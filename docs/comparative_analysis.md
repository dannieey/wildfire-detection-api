# Comparative Analysis: Existing Systems and Technology Stack

## 1. Existing Systems Comparison
To justify the necessity of the `wildfire-detection-api` project, existing wildfire monitoring solutions were evaluated against 8 core comparison criteria:
1. **Real-Time Data Ingestion:** Automated retrieval via satellite APIs.
2. **Spatial Precision:** High-resolution sensor support (e.g., VIIRS 375 m).
3. **Automated Clustering:** Aggregating raw thermal anomalies into discrete events.
4. **Interactive Web Mapping:** Visual interface for end-user inspection.
5. **Open/Modular API:** Extensible architecture for external integrations.
6. **Low Operational Overhead:** Lightweight infrastructure without heavy enterprise licensing.
7. **Custom Filtering:** User-defined date, confidence, and sensor filters.
8. **Open Access:** Accessibility for academic and research utilization.

### Comparison Table
| Criteria | EFFIS (EU) | NASA FIRMS Map | Global Forest Watch | Custom Desktop GIS | **Our Proposed System** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Real-Time Ingestion** | Yes | Yes | Partial | No (Manual) | **Yes (Automated API)** |
| **High Spatial Precision** | Moderate | Yes (VIIRS) | Moderate | Depends on data | **Yes (VIIRS 375 m)** |
| **Automated Clustering** | Yes (Complex) | No (Raw points) | Regional | No | **Yes (Spatiotemporal)** |
| **Interactive Mapping** | Yes | Yes | Yes | Desktop-based | **Yes (Web Leaflet/Mapbox)** |
| **Open / Modular API** | Restricted | Restricted | Partial | No | **Yes (FastAPI REST)** |
| **Low Overhead** | No (Heavy) | N/A (View-only) | No | No (Heavy setup) | **Yes (Lightweight)** |
| **Custom Filtering** | Preset | Basic | Preset | High (Manual) | **Yes (Dynamic params)** |
| **Open Access** | Institutional | Public View | Public View | Requires license | **Yes (Open source)** |

**Justification:** While platforms like EFFIS and NASA FIRMS provide powerful monitoring, they either act as closed institutional systems or display raw unclustered points without providing a lightweight, customizable API-driven workflow for localized event analysis.

---

## 2. Technology Stack Comparison & Justification
To ensure optimal performance, maintainability, and feasibility within a semester timeframe, alternatives were evaluated across three key architectural decisions:

### Decision 1: Server Platform / Backend Framework
- **Alternatives:** Node.js (Express), Go (Fiber), **Python (FastAPI — Selected)**.
- **Justification:** FastAPI provides native asynchronous support, automatic interactive documentation (Swagger UI), and seamless integration with spatial and data-science libraries (GeoPandas, Shapely), which is crucial for handling geographic data pipelines.

### Decision 2: Spatial Database / Data Storage
- **Alternatives:** MongoDB (Document store), PostgreSQL without extension, **PostgreSQL with PostGIS extension (Selected)**.
- **Justification:** PostGIS provides robust spatial indexing (R-Tree), native geometric/geographical data types, and high-performance spatial query execution required for clustering thermal anomalies.

### Decision 3: Spatiotemporal Clustering Method
- **Alternatives:** K-Means (Requires pre-defined cluster count), Grid-based binning, **DBSCAN / HDBSCAN (Selected)**.
- **Justification:** DBSCAN handles arbitrary cluster shapes, effectively identifies noise (false thermal anomalies), and groups points based on spatial distance epsilon and temporal windows without requiring prior knowledge of the cluster count.