"""PyroScope REST API (FastAPI).

Run:  uvicorn src.api.app:app --reload --port 8000
Docs: http://127.0.0.1:8000/docs  (interactive Swagger UI for the frontend developer)
"""
from __future__ import annotations

import io
import logging
import os
from typing import Literal, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from src.api.service import DataStore, Filters, NotFound
from src.core.config import settings
from src.export import detections_geojson, events_geojson, jsonable

log = logging.getLogger("api")
DEFAULT_DATASET = os.getenv("DEFAULT_DATASET", "kz_2025")

app = FastAPI(
    title="PyroScope API",
    version="1.0.0",
    description="Candidate wildfire events built from NASA FIRMS MODIS/VIIRS thermal-anomaly detections "
    "(Kazakhstan). Events are algorithmic candidates, not confirmed incidents.",
)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET", "POST"],
                   allow_headers=["*"])
store = DataStore(settings.processed_dir)
_refresh_state = {"running": False, "last_error": None, "last_result": None}


def _filters(start, end, sensor, region, bbox, min_confidence=None, min_priority=None, min_detections=None,
             status=None, exclude_persistent=False) -> Filters:
    box = None
    if bbox:
        try:
            box = tuple(float(x) for x in bbox.split(","))
            assert len(box) == 4
        except (ValueError, AssertionError):
            raise HTTPException(422, "bbox must be 'west,south,east,north'")
    return Filters(start, end, sensor, region, box, min_confidence, min_priority, min_detections, status,
                   exclude_persistent)


def _ds(dataset: Optional[str]) -> str:
    return dataset or DEFAULT_DATASET


@app.exception_handler(NotFound)
async def _nf(_, exc: NotFound):
    return JSONResponse(status_code=404, content={"detail": str(exc).strip("'\"")})


# Common query parameters --------------------------------------------------
Q_DS = Query(None, description="Dataset name, e.g. kz_2025 or live")
Q_START = Query(None, description="YYYY-MM-DD (UTC)")
Q_END = Query(None, description="YYYY-MM-DD inclusive (UTC)")
Q_SENSOR = Query(None, pattern="^(VIIRS|MODIS)$")
Q_BBOX = Query(None, description="west,south,east,north")


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "datasets": [d["dataset"] for d in store.list_datasets()],
            "default_dataset": DEFAULT_DATASET, "firms_key_configured": bool(settings.firms_map_key)}


@app.get("/api/v1/datasets")
def datasets():
    return store.list_datasets()


@app.get("/api/v1/meta")
def meta(dataset: Optional[str] = Q_DS):
    return store.meta(_ds(dataset))


@app.get("/api/v1/events")
def events(
    dataset: Optional[str] = Q_DS, start: Optional[str] = Q_START, end: Optional[str] = Q_END,
    sensor: Optional[str] = Q_SENSOR, region: Optional[str] = None, bbox: Optional[str] = Q_BBOX,
    min_priority: Optional[Literal["low", "medium", "high"]] = None, min_detections: Optional[int] = Query(None, ge=1),
    status: Optional[Literal["active", "inactive"]] = None, exclude_persistent: bool = False,
    geometry: Literal["point", "hull"] = "point",
    sort: str = Query("-start_time", description="field, prefix '-' for descending (e.g. -max_frp)"),
    limit: Optional[int] = Query(None, ge=1, le=20000),
):
    """Candidate events as a GeoJSON FeatureCollection (centroids or convex hulls)."""
    f = _filters(start, end, sensor, region, bbox, None, min_priority, min_detections, status, exclude_persistent)
    return events_geojson(store.events(_ds(dataset), f, sort=sort, limit=limit), geometry=geometry)


@app.get("/api/v1/events/{event_id}")
def event_detail(event_id: str, dataset: Optional[str] = Q_DS):
    """One event: summary, hull, daily breakdown and its detections (GeoJSON)."""
    d = store.event_detail(_ds(dataset), event_id)
    return {"event": d["event"], "detections": detections_geojson(d["detections"])}


@app.get("/api/v1/detections")
def detections(
    dataset: Optional[str] = Q_DS, start: Optional[str] = Q_START, end: Optional[str] = Q_END,
    sensor: Optional[str] = Q_SENSOR, region: Optional[str] = None, bbox: Optional[str] = Q_BBOX,
    min_confidence: Optional[Literal["nominal", "high"]] = None, include_noise: bool = True,
    limit: int = Query(50000, ge=1, le=200000),
):
    """Raw (cleaned) detections - the unclustered baseline layer."""
    f = _filters(start, end, sensor, region, bbox, min_confidence)
    det = store.detections(_ds(dataset), f, include_noise=include_noise)
    fc = detections_geojson(det.head(limit))
    fc["total"], fc["truncated"] = int(len(det)), bool(len(det) > limit)
    return fc


@app.get("/api/v1/stats/summary")
def stats_summary(dataset: Optional[str] = Q_DS, start: Optional[str] = Q_START, end: Optional[str] = Q_END,
                  sensor: Optional[str] = Q_SENSOR, region: Optional[str] = None, bbox: Optional[str] = Q_BBOX):
    """KPI tiles: events, high priority, detections, latest observation."""
    return store.summary(_ds(dataset), _filters(start, end, sensor, region, bbox))


@app.get("/api/v1/stats/timeseries")
def stats_timeseries(dataset: Optional[str] = Q_DS, start: Optional[str] = Q_START, end: Optional[str] = Q_END,
                     sensor: Optional[str] = Q_SENSOR, region: Optional[str] = None,
                     freq: Literal["D", "W", "M"] = "D"):
    return store.timeseries(_ds(dataset), _filters(start, end, sensor, region, None), freq)


@app.get("/api/v1/stats/regions")
def stats_regions(dataset: Optional[str] = Q_DS, start: Optional[str] = Q_START, end: Optional[str] = Q_END,
                  sensor: Optional[str] = Q_SENSOR):
    return store.by_region(_ds(dataset), _filters(start, end, sensor, None, None))


@app.get("/api/v1/evaluation")
def evaluation(dataset: Optional[str] = Q_DS):
    """Hypothesis tests (H1 cross-sensor, H2 temporal vs spatial), sensitivity grid, data quality."""
    ds = _ds(dataset)
    return {"evaluation": store.evaluation(ds), "quality": store.meta(ds).get("quality")}


@app.get("/api/v1/export/events.{fmt}")
def export_events(fmt: Literal["csv", "geojson"], dataset: Optional[str] = Q_DS, start: Optional[str] = Q_START,
                  end: Optional[str] = Q_END, sensor: Optional[str] = Q_SENSOR, region: Optional[str] = None,
                  min_priority: Optional[Literal["low", "medium", "high"]] = None):
    ev = store.events(_ds(dataset), _filters(start, end, sensor, region, None, None, min_priority))
    if fmt == "geojson":
        return JSONResponse(events_geojson(ev, geometry="hull"),
                            headers={"Content-Disposition": "attachment; filename=pyroscope_events.geojson"})
    buf = io.StringIO()
    ev.drop(columns=["hull"]).to_csv(buf, index=False)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=pyroscope_events.csv"})


def _do_refresh(days: int) -> None:
    from src.ingestion.firms_client import download_nrt
    from src.pipeline import run

    try:
        paths = download_nrt(settings.raw_dir / "live", day_range=days)
        viirs = [str(p) for p in paths if "modis" not in p.name]
        modis = [str(p) for p in paths if "modis" in p.name]
        if not paths:
            raise RuntimeError("No FIRMS sources could be downloaded.")
        _refresh_state["last_result"] = jsonable(run("live", viirs, modis, live=True))
        _refresh_state["last_error"] = None
        store.reload("live")
    except Exception as err:  # noqa: BLE001 - reported to the client
        log.exception("refresh failed")
        _refresh_state["last_error"] = str(err)
    finally:
        _refresh_state["running"] = False


@app.post("/api/v1/refresh", status_code=202)
def refresh(background: BackgroundTasks, days: int = Query(3, ge=1, le=5)):
    """Fetch the latest NRT data from FIRMS and rebuild the 'live' dataset (needs FIRMS_MAP_KEY)."""
    if not settings.firms_map_key:
        raise HTTPException(503, "FIRMS_MAP_KEY is not configured on the server.")
    if _refresh_state["running"]:
        return {"status": "already running"}
    _refresh_state["running"] = True
    background.add_task(_do_refresh, days)
    return {"status": "started", "dataset": "live"}


@app.get("/api/v1/refresh/status")
def refresh_status():
    return _refresh_state
