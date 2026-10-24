# Requirements Specification: API-Driven Wildfire Event Detection

## 1. Introduction
This document outlines the functional and non-functional requirements for the `wildfire-detection-api` system. Requirements are prioritized using the MoSCoW method (Must have, Should have, Could have, Won't have) to guide development for Pre-Defense 2 and MVP delivery.

---

## 2. Functional Requirements (FR)

| ID | Feature / Module | Description | Priority | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **FR-01** | Data Ingestion Pipeline | Automated retrieval of active-fire CSV/JSON feeds from NASA FIRMS API. | **Must Have** | System successfully fetches daily thermal anomalies for specified bounding boxes without manual intervention. |
| **FR-02** | Spatial-Temporal Clustering | Group raw pixel detections into discrete fire events using DBSCAN. | **Must Have** | Clustered events correctly associate points based on proximity ($\epsilon$) and time windows ($t$). |
| **FR-03** | REST API Endpoints | Expose endpoints for active fires and clustered events (`GET /api/v1/wildfires`). | **Must Have** | Endpoints return valid GeoJSON FeatureCollection payloads with filtering query parameters. |
| **FR-04** | Client-Side Filtering | Dynamic map filters for date range, confidence threshold, and satellite source. | **Should Have** | User can adjust filters in the UI, and map markers update dynamically in real-time. |
| **FR-05** | Event Inspection Drawer | Detailed view showing brightness temperature, FRP, and acquisition metadata. | **Should Have** | Clicking a cluster marker opens a detailed sidebar panel with aggregated event metrics. |

---

## 3. Non-Functional Requirements (NFR)

| ID | Category | Description | Target Metric / Standard |
| :--- | :--- | :--- | :--- |
| **NFR-01** | Performance | API response time for fetching active regional fire events. | Under 500 ms for standard bounding box queries. |
| **NFR-02** | Reliability | Pipeline resilience against external NASA FIRMS API timeouts. | Graceful error handling with fallback caching. |
| **NFR-03** | Maintainability | Clean architecture separation (API routers, service layer, spatial database). | Modular codebase adhering to Python PEP 8 standards. |
| **NFR-04** | Security | Protection of sensitive credentials and database connection strings. | Strict use of `.env` configuration; zero secrets in Git. |

---

## 4. API Data Specification (GeoJSON Contract Draft)
The primary endpoint `GET /api/v1/wildfires/active` outputs a standard GeoJSON structure:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [71.4304, 51.1694]
      },
      "properties": {
        "cluster_id": "cls_001",
        "brightness": 325.4,
        "confidence": "high",
        "satellite": "VIIRS",
        "acquisition_date": "2026-10-23"
      }
    }
  ]
}