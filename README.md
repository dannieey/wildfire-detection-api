# API-Driven Interactive Wildfire Event Detection Using MODIS/VIIRS

## Brief Description
This repository contains the project documentation, system architecture, and source code for an API-driven interactive wildfire and thermal anomaly early detection system. The project focuses on transforming raw, fragmented satellite thermal anomaly data feeds from MODIS and VIIRS sensors into structured, spatiotemporally clustered wildfire events presented through an interactive web visualization workflow.

---

## Problem Statement, Target Users, and Expected Outcomes

### Problem Statement
Satellite remote sensing using MODIS and VIIRS sensors provides vital global active-fire observations. However, raw satellite detections represent unverified thermal anomalies—which can include false alarms, hot smoke, or agricultural burning—rather than coherent, verified fire events. Furthermore, they are typically distributed as raw data feeds rather than integrated monitoring workflows. There is a lack of lightweight, accessible architectures that continuously retrieve API data, process anomalies, cluster related points into discrete fire events, and present them in an interactive map interface.

### Target Users
- Environmental researchers and data analysts requiring structured satellite data for event-level analysis.
- Monitoring personnel and operators who need to inspect active fire locations efficiently without manually parsing thousands of raw, unclustered satellite data points.

### Expected Outcomes
1. An automated API-driven retrieval pipeline for near-real-time MODIS and VIIRS thermal anomaly observations.
2. A spatiotemporal clustering algorithm that aggregates individual pixel detections into coherent, meaningful wildfire events.
3. An interactive web mapping interface designed to improve event identification, reduce manual inspection effort, and enhance overall interpretability compared to unclustered point displays.

---

## Team Members, Responsibilities, and Supervisor

- **Danel Li** (Group: SE-2406) — Lead Backend Engineer & Systems Architect:System architecture design, RESTful API pipeline development (FastAPI), spatial database modeling (PostgreSQL + PostGIS), core data ingestion from NASA FIRMS APIs, and server-side spatiotemporal clustering pipeline (DBSCAN/HDBSCAN)
- **Ramina Kuzhentayeva** (Group: SE-2406) — Lead Frontend Engineer & Algorithm Specialist:Web GIS architecture, Figma design system, Mapbox GL JS integration, implementation of client-side spatial filtering algorithms, bounding-box spatial queries optimization, and geospatial data transformation logic for dynamic map rendering and multi-parameter anomaly filtering.
- **Supervisor:** Alshynov Shynggys

---

## Project Scope and Current Development Status

### Project Scope
- **Included:** Integration of NASA FIRMS / MODIS and VIIRS APIs, backend data preprocessing, implementation of spatiotemporal clustering algorithms, comparative evaluation against unclustered baselines, and a prototype interactive web map.
- **Excluded:** Building proprietary satellite hardware, training original low-level sensor classification neural networks, or handling real-time firefighting resource dispatch.

### Current Development Status
- **Phase:** Analysis, Architecture Design, and Planning (Pre-Defense 1 preparation).
- **Completed Deliverables:** Project proposal, literature review (12+ sources), existing systems and technology comparisons, requirements specification, architectural diagrams, and verification plan.
- **Next Steps:** Setting up the core backend retrieval scripts and implementing initial clustering logic.

---

## Selected Technologies

- **Backend Language:** Python (chosen for rich geospatial data libraries and API integrations).
- **Geospatial & Data Processing:** Pandas, GeoPandas, Shapely.
- **Satellite Data Sources:** NASA FIRMS / MODIS (Collection 6) & VIIRS (375 m) APIs.
- **Database & Storage:** PostgreSQL / PostGIS (planned for spatial data management).
- **Frontend & Visualization:** Interactive web map interface (framework to be finalized during prototyping).
- **Version Control & Project Management:** Git, GitHub, YouTrack.

---

## Links and Documentation

---

## Setup, Execution, and Testing Instructions

*(This section will be updated as runnable code modules become available during development).*

### Prerequisites
- Python 3.10+
- Git

### Installation
```bash
# Clone the repository
git clone [https://github.com/dannieey/wildfire-detection-api.git](https://github.com/dannieey/wildfire-detection-api.git)
cd wildfire-detection-api

# Install dependencies (coming soon)
# pip install -r requirements.txt