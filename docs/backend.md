# Backend: data pipeline and API

## 1. Setup
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # add FIRMS_MAP_KEY only if you need live data
pytest                                                  # all tests should pass
```

## 2. Get the data (NASA FIRMS, Kazakhstan, 2025)
From <https://firms.modaps.eosdis.nasa.gov/country/> download the yearly country files for Kazakhstan and put
the CSVs into `data/raw/`:

| Sensor | File |
|---|---|
| VIIRS NOAA-20 (JPSS-1) | `viirs-jpss1_2025_Kazakhstan.csv` |
| VIIRS Suomi NPP | `viirs-snpp_2025_Kazakhstan.csv` |
| MODIS (Terra+Aqua, C6.1) | `modis_2025_Kazakhstan.csv` |

Optional: oblast boundaries for the `region` field — geoBoundaries KAZ ADM1 (simplified GeoJSON, CC BY 4.0),
saved as `data/reference/kaz_adm1.geojson`. With this file, points outside the national border are removed
and every event gets a region.

## 3. Run the pipeline
```bash
python -m src.pipeline --name kz_2025 \
  --viirs data/raw/viirs-jpss1_2025_Kazakhstan.csv data/raw/viirs-snpp_2025_Kazakhstan.csv \
  --modis data/raw/modis_2025_Kazakhstan.csv --sensitivity
```
Outputs in `data/processed/kz_2025/`: `detections.csv/.geojson`, `events.csv/.geojson`, `meta.json`
(period, timing, data-quality report per rule), `evaluation.json` (H1, H2), `sensitivity_viirs.csv`.

Live data (last 1–5 days, needs `FIRMS_MAP_KEY`): `python -m src.pipeline --name live --fetch-nrt --days 3`
or the `POST /api/v1/refresh` endpoint.

Development without real data: `python scripts/make_synthetic.py data/raw/synthetic` then run the pipeline
with `--name kz_2025` on those two files (synthetic — never report as results).

## 4. Run the API
```bash
uvicorn src.api.app:app --reload --port 8000     # docs: http://127.0.0.1:8000/docs
cd frontend && npm install && npm run dev        # Vite proxies /api to :8000
```
Contract: `docs/api_contract.md`.

## 5. Method summary (for the paper)
1. **Unified schema** for VIIRS (`bright_ti4`, l/n/h confidence) and MODIS (`brightness`, 0–100 %
   confidence → low <30 ≤ nominal <80 ≤ high).
2. **Cleaning**, each rule logged: missing coordinates/time, impossible coordinates, study bbox, exact
   duplicates, FIRMS `type` ≠ 0 (static sources such as gas flares, volcanoes, offshore), low confidence.
3. **Spatiotemporal DBSCAN**: neighbours if great-circle distance ≤ `eps_km` (3 km) AND |Δt| ≤ `eps_days`
   (2 days); `min_samples`=2; run per sensor. `eps_days=None` = spatial-only baseline (Assignment 3).
4. **Event summaries**: time span, centroid, convex hull and area, FRP stats, day/night counts, region,
   rule-based priority (high: max FRP ≥100 MW or ≥50 detections or ≥25 km²; medium: max FRP ≥30 MW or
   ≥10 detections), status (active if last detection ≤48 h ago), persistent-hotspot flag (≥30 days,
   ≤2 km extent).
5. **Evaluation**
   - H1: VIIRS events vs isolated VIIRS detections, confirmed by MODIS within 3 km / ±1 day →
     χ² test (2×2), odds ratio, Cramér's V; size-bin χ² as secondary analysis.
   - H2: spatiotemporal vs spatial-only event durations → one-sided Mann–Whitney U; plus share of events
     longer than 7 days.
   - Data reduction: review items (events + isolated) vs raw detections.
   - Sensitivity: `eps_km` ∈ {1,2,3,5} × `eps_days` ∈ {1,2,3}.
