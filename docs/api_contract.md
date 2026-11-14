# PyroScope API contract (backend ↔ frontend)

Base URL (dev): `http://127.0.0.1:8000` — the Vite dev server proxies `/api` there, so the
frontend just calls `/api/v1/...`. Interactive docs: `http://127.0.0.1:8000/docs`.

All endpoints accept `dataset` (default `kz_2025`; `live` after a refresh). Dates are UTC `YYYY-MM-DD`,
`end` is inclusive. Common filters: `start`, `end`, `sensor` (`VIIRS`|`MODIS`), `region`, `bbox=w,s,e,n`.

| Method | Path | Purpose (UI element) |
|---|---|---|
| GET | `/api/v1/health` | Backend status badge |
| GET | `/api/v1/datasets` | Dataset switcher (2025 archive / live) |
| GET | `/api/v1/meta` | Period, sensors, region list (filter dropdowns), data-quality report |
| GET | `/api/v1/stats/summary` | KPI tiles: detected events, high priority, satellite detections, latest observation |
| GET | `/api/v1/events` | Map event layer + event queue. Extra: `min_priority`, `min_detections`, `status`, `exclude_persistent`, `geometry=point\|hull`, `sort=-max_frp`, `limit` |
| GET | `/api/v1/events/{event_id}` | Event drawer: summary, hull, daily breakdown, member detections |
| GET | `/api/v1/detections` | Raw-points layer (unclustered baseline). Extra: `min_confidence`, `include_noise`, `limit` → returns `total`, `truncated` |
| GET | `/api/v1/stats/timeseries?freq=D\|W\|M` | Analytics chart: detections / events / FRP per period and sensor |
| GET | `/api/v1/stats/regions` | Analytics: per-oblast table/choropleth |
| GET | `/api/v1/evaluation` | Methodology page: H1/H2 test results, sensitivity grid, cleaning steps |
| GET | `/api/v1/export/events.csv` / `.geojson` | "Export" button |
| POST | `/api/v1/refresh?days=3` | "Refresh" button: pulls FIRMS NRT data into dataset `live` (202, runs in background) |
| GET | `/api/v1/refresh/status` | Poll after refresh |

## Event feature (`/api/v1/events`)
```json
{
  "type": "Feature",
  "id": "VIIRS-000012",
  "geometry": {"type": "Point", "coordinates": [82.61, 49.90]},
  "properties": {
    "event_id": "VIIRS-000012", "sensor": "VIIRS", "n_detections": 60,
    "start_time": "2025-07-01T02:14:00+00:00", "end_time": "2025-07-04T20:31:00+00:00",
    "duration_hours": 90.3, "n_overpass_days": 4, "centroid_lat": 49.9, "centroid_lon": 82.61,
    "area_km2": 6.2, "max_extent_km": 4.1, "max_frp": 120.5, "sum_frp": 1810.2, "mean_frp": 30.2,
    "mean_brightness_k": 335.1, "share_high_confidence": 0.48, "n_day": 30, "n_night": 30,
    "region": "East Kazakhstan Region", "priority": "high", "status": "inactive",
    "persistent_hotspot": false
  }
}
```

## Detection feature (`/api/v1/detections`)
`properties`: `detection_id, event_id (null = isolated), sensor, satellite, acq_datetime, acq_date,
brightness_k, brightness2_k, frp, confidence_level (low|nominal|high), confidence_raw, daynight, region`.

## Wording rule for the UI
Show "candidate event" / "thermal anomaly", never "confirmed fire". All UI text in English
(screenshots go into the paper and slides).
