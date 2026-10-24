# Verification, Risk Management, and Supervisor Feedback

## 1. Verification and Evaluation Plan
To demonstrate the successful achievement of the project aim—evaluating whether an integrated lightweight workflow improves wildfire event identification—the following verification strategy and metrics will be applied:

### Evaluation Metrics
- **Spatial Accuracy (Cluster Agreement):** Percentage of detected spatial clusters matching a benchmark reference event set.
- **Processing Latency:** Time taken by the API pipeline to fetch, parse, cluster, and serve daily global/regional thermal anomaly feeds.
- **User Efficiency (Reduction in Manual Inspection):** Comparing the time required by an operator to review raw unclustered point detections versus clustered event summaries.

### Baseline Solution for Comparison
- **Unclustered Baseline:** Raw point-detection feed from NASA FIRMS without spatiotemporal aggregation or filtering. Evaluation will measure how much clustering reduces cognitive load and redundant visual inspection.

---

## 2. Project Risk Management & Dependencies

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **RS-01** | NASA FIRMS API rate limits or downtime during peak fire seasons. | Medium | High | Implement local caching of recent query responses and graceful error handling with fallback data. |
| **RS-02** | High computational overhead during spatial clustering of dense thermal points. | Medium | Medium | Optimize spatial indexing using PostGIS R-Trees and bound geographic filter areas. |
| **RS-03** | Frontend map rendering performance bottlenecks with large datasets. | Low | Medium | Utilize client-side marker clustering and viewport culling in Mapbox GL. |
| **RS-04** | Schedule delays due to synchronization between backend and frontend tasks. | Low | High | Maintain modular REST API contracts (GeoJSON) early to decouple frontend/backend development. |

---

## 3. Supervisor Feedback & Revisions Log
*This section records feedback received from the project supervisor during preliminary checkpoints and the planned responses.*

- **Feedback 1 (Scope & Objectives):** Ensure the distinction between thermal anomaly detection and machine learning prediction is clearly maintained.
  - **Action Taken:** Refined project scope to focus strictly on API ingestion, spatiotemporal event clustering, and interactive web visualization without expanding into predictive forecasting models.
- **Feedback 2 (Evaluation Rigor):** Define clear criteria for comparing clustered events against raw point feeds.
  - **Action Taken:** Established a comparative verification plan evaluating event-level agreement and reduction in manual review effort (incorporated into the verification plan above).