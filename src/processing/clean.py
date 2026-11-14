"""Validation and cleaning with an auditable data-quality report.

Every rule records how many rows it removed, so the Methods/Results sections of
the paper can report a full data-flow table (raw -> retained).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import pandas as pd

FIRE_TYPE_LABELS = {
    0: "presumed vegetation fire",
    1: "active volcano",
    2: "other static land source",
    3: "offshore",
}


@dataclass
class CleaningConfig:
    bbox: tuple[float, float, float, float] | None = (46.4, 40.5, 87.4, 55.5)  # W,S,E,N
    keep_types: tuple[int, ...] = (0,)  # vegetation fires only; NRT data (no type) is kept
    drop_low_confidence: bool = True
    start: str | None = None  # inclusive, YYYY-MM-DD
    end: str | None = None  # inclusive, YYYY-MM-DD


@dataclass
class QualityReport:
    raw_rows: int = 0
    steps: list[dict] = field(default_factory=list)
    type_counts: dict = field(default_factory=dict)
    confidence_counts: dict = field(default_factory=dict)
    retained_rows: int = 0

    def log(self, rule: str, before: int, after: int) -> None:
        self.steps.append({"rule": rule, "removed": before - after, "remaining": after})

    @property
    def retention_pct(self) -> float:
        return round(100 * self.retained_rows / self.raw_rows, 2) if self.raw_rows else 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["retention_pct"] = self.retention_pct
        return d


def clean_detections(df: pd.DataFrame, cfg: CleaningConfig | None = None) -> tuple[pd.DataFrame, QualityReport]:
    cfg = cfg or CleaningConfig()
    rep = QualityReport(raw_rows=len(df))
    rep.type_counts = {
        FIRE_TYPE_LABELS.get(int(k), str(k)) if pd.notna(k) else "not provided (NRT)": int(v)
        for k, v in df["type"].value_counts(dropna=False).items()
    }
    rep.confidence_counts = {
        str(k): int(v) for k, v in df["confidence_level"].fillna("missing").value_counts().items()
    }

    def step(rule: str, mask: pd.Series) -> None:
        nonlocal df
        before = len(df)
        df = df[mask.fillna(False)]
        rep.log(rule, before, len(df))

    step("missing coordinates or timestamp", df[["latitude", "longitude", "acq_datetime"]].notna().all(axis=1))
    step("impossible coordinates", df["latitude"].between(-90, 90) & df["longitude"].between(-180, 180))
    if cfg.bbox:
        w, s, e, n = cfg.bbox
        step("outside study bounding box", df["longitude"].between(w, e) & df["latitude"].between(s, n))
    if cfg.start:
        step("before study period", df["acq_datetime"] >= pd.Timestamp(cfg.start, tz="UTC"))
    if cfg.end:
        step("after study period", df["acq_datetime"] < pd.Timestamp(cfg.end, tz="UTC") + pd.Timedelta(days=1))

    before = len(df)
    df = df.drop_duplicates(subset=["latitude", "longitude", "acq_datetime", "sensor", "satellite"])
    rep.log("exact duplicates", before, len(df))

    if cfg.keep_types:
        step(
            f"non-vegetation source type (kept types {list(cfg.keep_types)})",
            df["type"].isna() | df["type"].isin(cfg.keep_types),
        )
    if cfg.drop_low_confidence:
        step("low confidence", df["confidence_level"] != "low")

    df = df.sort_values(["acq_datetime", "sensor"]).reset_index(drop=True)
    prefix = df["sensor"].str[0]  # V / M
    df["detection_id"] = prefix + "-" + df.index.astype(str).str.zfill(7)
    rep.retained_rows = len(df)
    return df, rep
