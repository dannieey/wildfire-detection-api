# Project Proposal: API-Driven Interactive Wildfire Event Detection Using MODIS/VIIRS

## 1. Project Title
API-Driven Interactive Wildfire Event Detection Using MODIS/VIIRS

## 2. Team Members & Roles
- **Danel Li** – Backend & Infrastructure Engineer (API ingestion pipelines, database architecture, spatial clustering algorithms)
- **Ramina Kuzhentayeva** – Frontend & UI/UX Developer (Interactive web mapping interface, client-side filtering controls, design system)

## 3. Supervisor
- **Supervisor:** Department of Information Technology, Astana IT University

## 4. Problem Statement
Wildfire monitoring heavily relies on satellite remote sensing to cover remote geographic regions, utilizing established sensors such as MODIS and VIIRS. However, raw satellite detections represent thermal anomalies—which can include false alarms, hot smoke, or agricultural burning—and are typically distributed as separate, raw data feeds rather than an integrated monitoring workflow. The core problem is the lack of a unified, lightweight architecture that continuously acquires API data, processes anomalies, clusters related points into coherent fire events, and presents them in an interactive map interface.

## 5. Target Users
- Researchers and environmental monitoring personnel who need to inspect satellite fire detections, reduce manual point-by-point inspection, and understand thermal anomalies as coherent fire events.

## 6. Aim and Objectives
### Aim
To evaluate whether integrating near-real-time MODIS/VIIRS thermal anomaly retrieval with automated spatiotemporal clustering improves the identification and interactive interpretation of coherent wildfire events in a lightweight monitoring workflow.

### Objectives
1. Identify satellite observations and metadata required for event-level wildfire analysis (location, acquisition time, confidence, brightness attributes).
2. Develop a lightweight API-driven pipeline for retrieving and preprocessing near-real-time MODIS/VIIRS thermal anomalies.
3. Implement spatiotemporal clustering to aggregate related satellite detections into coherent wildfire events.
4. Compare clustered event representations with unclustered point detections using predefined criteria.
5. Assess the feasibility of presenting resulting wildfire events through an interactive web map.

## 7. Expected Outcomes
- An automated backend ingestion and spatial clustering pipeline.
- A functional web-based interactive mapping interface for exploratory wildfire analysis.
- A comparative evaluation demonstrating how clustered event workflows improve interpretability over raw unclustered points.

## 8. Project Scope
### In-Scope
- Automated retrieval of MODIS and VIIRS active-fire observations via NASA FIRMS APIs.
- Database storage with spatial indexing (PostGIS / MongoDB).
- Spatiotemporal clustering (DBSCAN/HDBSCAN based on spatial distance and time windows).
- Web-based interactive visualization using Mapbox/Leaflet with date, confidence, and satellite filters.

### Out-of-Scope
- Developing core satellite sensor algorithms or atmospheric correction models.
- Long-term machine learning predictive modeling for future fire risk occurrence (focus is strictly on near-real-time detection and event aggregation).