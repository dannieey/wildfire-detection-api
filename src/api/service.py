"""Query layer over processed datasets (framework-independent, unit-tested)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.export import EVENT_PROPS, jsonable, load_outputs

CONF_RANK = {"low": 0, "nominal": 1, "high": 2}
PRIORITY_RANK = {"low": 0, "medium": 1, "high": 2}


class NotFound(KeyError):
    pass


@dataclass
class Filters:
    start: str | None = None
    end: str | None = None
    sensor: str | None = None  # VIIRS | MODIS
    region: str | None = None
    bbox: tuple[float, float, float, float] | None = None  # W,S,E,N
    min_confidence: str | None = None  # nominal | high (detections)
    min_priority: str | None = None  # medium | high (events)
    min_detections: int | None = None
    status: str | None = None  # active | inactive
    exclude_persistent: bool = False


def _ts(s: str | None, end: bool = False):
    if not s:
        return None
    t = pd.Timestamp(s)
    t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
    return t + pd.Timedelta(days=1) if end and len(s) == 10 else t


class DataStore:
    def __init__(self, processed_dir: Path):
        self.processed_dir = Path(processed_dir)
        self._cache: dict[str, tuple] = {}

    # ---------- datasets ----------
    def list_datasets(self) -> list[dict]:
        out = []
        if self.processed_dir.exists():
            for d in sorted(self.processed_dir.iterdir()):
                if (d / "meta.json").exists():
                    m = self._load(d.name)[2]
                    out.append({k: m.get(k) for k in ("dataset", "mode", "period_start", "period_end",
                                                      "n_detections", "n_events", "generated_at")})
        return out

    def _load(self, name: str):
        d = self.processed_dir / name
        if not (d / "meta.json").exists():
            raise NotFound(f"dataset '{name}' not found")
        mtime = (d / "meta.json").stat().st_mtime
        if name not in self._cache or self._cache[name][0] != mtime:
            self._cache[name] = (mtime, *load_outputs(d))
        return self._cache[name][1:]

    def reload(self, name: str) -> None:
        self._cache.pop(name, None)

    def meta(self, name: str) -> dict:
        return self._load(name)[2]

    def evaluation(self, name: str) -> dict:
        return self._load(name)[3]

    # ---------- filtering ----------
    def detections(self, name: str, f: Filters, event_id: str | None = None, include_noise=True) -> pd.DataFrame:
        det = self._load(name)[0]
        m = pd.Series(True, index=det.index)
        if (s := _ts(f.start)) is not None:
            m &= det["acq_datetime"] >= s
        if (e := _ts(f.end, end=True)) is not None:
            m &= det["acq_datetime"] < e
        if f.sensor:
            m &= det["sensor"].str.upper() == f.sensor.upper()
        if f.region:
            m &= det["region"] == f.region
        if f.bbox:
            w, so, ea, n = f.bbox
            m &= det["longitude"].between(w, ea) & det["latitude"].between(so, n)
        if f.min_confidence:
            m &= det["confidence_level"].map(CONF_RANK).fillna(-1) >= CONF_RANK[f.min_confidence]
        if event_id:
            m &= det["event_id"] == event_id
        if not include_noise:
            m &= det["event_id"].notna()
        return det[m]

    def events(self, name: str, f: Filters, sort: str = "-start_time", limit: int | None = None) -> pd.DataFrame:
        ev = self._load(name)[1]
        m = pd.Series(True, index=ev.index)
        if (s := _ts(f.start)) is not None:
            m &= ev["end_time"] >= s  # overlap with requested window
        if (e := _ts(f.end, end=True)) is not None:
            m &= ev["start_time"] < e
        if f.sensor:
            m &= ev["sensor"].str.upper() == f.sensor.upper()
        if f.region:
            m &= ev["region"] == f.region
        if f.bbox:
            w, so, ea, n = f.bbox
            m &= ev["centroid_lon"].between(w, ea) & ev["centroid_lat"].between(so, n)
        if f.min_priority:
            m &= ev["priority"].map(PRIORITY_RANK) >= PRIORITY_RANK[f.min_priority]
        if f.min_detections:
            m &= ev["n_detections"] >= f.min_detections
        if f.status:
            m &= ev["status"] == f.status
        if f.exclude_persistent:
            m &= ~ev["persistent_hotspot"].astype(bool)
        out = ev[m]
        col, asc = (sort[1:], False) if sort.startswith("-") else (sort, True)
        if col in out.columns:
            out = out.sort_values(col, ascending=asc, kind="stable")
        return out.head(limit) if limit else out

    def event_detail(self, name: str, event_id: str) -> dict:
        ev = self._load(name)[1]
        row = ev[ev["event_id"] == event_id]
        if row.empty:
            raise NotFound(f"event '{event_id}' not found")
        rec = row.iloc[0].to_dict()
        props = {k: jsonable(rec.get(k)) for k in EVENT_PROPS}
        props["hull"] = jsonable(rec.get("hull"))
        props["bbox"] = [rec["min_lon"], rec["min_lat"], rec["max_lon"], rec["max_lat"]]
        dets = self.detections(name, Filters(), event_id=event_id)
        props["daily"] = [
            {"date": d, "detections": int(len(g)), "sum_frp": jsonable(round(g["frp"].sum(), 2))}
            for d, g in dets.groupby("acq_date")
        ]
        return {"event": props, "detections": dets}

    # ---------- statistics ----------
    def summary(self, name: str, f: Filters) -> dict:
        det, ev = self.detections(name, f), self.events(name, f)
        latest = det["acq_datetime"].max() if len(det) else None
        return {
            "detected_events": int(len(ev)),
            "high_priority_events": int((ev["priority"] == "high").sum()),
            "active_events": int((ev["status"] == "active").sum()),
            "satellite_detections": int(len(det)),
            "isolated_detections": int(det["event_id"].isna().sum()),
            "latest_observation": jsonable(latest),
            "total_frp_mw": jsonable(round(float(det["frp"].sum()), 1)) if len(det) else 0.0,
            "by_sensor": {k: int(v) for k, v in det["sensor"].value_counts().items()},
        }

    def timeseries(self, name: str, f: Filters, freq: str = "D") -> list[dict]:
        det = self.detections(name, f)
        if det.empty:
            return []
        rule = {"D": "D", "W": "W-MON", "M": "MS"}[freq]
        local = det.set_index(det["acq_datetime"].dt.tz_convert(None))
        g = local.groupby([pd.Grouper(freq=rule), "sensor"])
        agg = g.agg(detections=("detection_id", "size"), sum_frp=("frp", "sum"),
                    events=("event_id", "nunique")).reset_index()
        return [
            {"period": r.acq_datetime.strftime("%Y-%m-%d"), "sensor": r.sensor, "detections": int(r.detections),
             "events": int(r.events), "sum_frp": round(float(r.sum_frp), 1)}
            for r in agg.itertuples() if r.detections > 0
        ]

    def by_region(self, name: str, f: Filters) -> list[dict]:
        det, ev = self.detections(name, f), self.events(name, f)
        d = det.groupby(det["region"].fillna("Unassigned")).agg(detections=("detection_id", "size"),
                                                                 sum_frp=("frp", "sum"))
        e = ev.groupby(ev["region"].fillna("Unassigned")).agg(
            events=("event_id", "size"), high_priority=("priority", lambda s: int((s == "high").sum())))
        t = d.join(e, how="outer").fillna(0).sort_values("detections", ascending=False)
        return [{"region": k, "detections": int(r.detections), "events": int(r.events),
                 "high_priority": int(r.high_priority), "sum_frp": round(float(r.sum_frp), 1)}
                for k, r in t.iterrows()]
