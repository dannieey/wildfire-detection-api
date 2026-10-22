# Literature Review: Interactive Wildfire Event Detection Using Satellite APIs

## 1. Introduction and Search Strategy
This literature review establishes the scientific and technical foundation for the `wildfire-detection-api` project. The reviewed literature covers four core domains:
1. Remote sensing baselines (MODIS and VIIRS active-fire algorithms).
2. Distinction between raw thermal anomalies and verified fire events.
3. Machine learning applications in wildfire prediction and monitoring.
4. Spatiotemporal event aggregation and operational monitoring frameworks.

### Search Strategy & Databases
Searches were conducted via ScienceDirect, Scopus, Web of Science, IEEE Xplore, Google Scholar, and NASA FIRMS / Earthdata. Boolean queries combined concepts such as wildfire detection, remote sensing sensors (MODIS, VIIRS, FIRMS), thermal anomalies, spatial-temporal analysis, and API-driven systems.
- **Inclusion Criteria:** Peer-reviewed studies on satellite fire algorithms, ML fire prediction, spatial event aggregation, and operational monitoring.
- **Exclusion Criteria:** Non-peer-reviewed news, duplicate studies, and non-computational ecological studies.

---

## 2. Structured Literature Synthesis

### 2.1 Remote Sensing Foundation (MODIS & VIIRS)
The operational baseline for satellite active-fire detection relies heavily on spaceborne sensors. Giglio et al. (2016) detailed the Collection 6 MODIS active fire detection algorithm, which provides a long-term historical record and global operational active-fire products. Complementing MODIS, Schroeder et al. (2014) and Csiszar et al. (2014) introduced the VIIRS 375 m active fire detection data product, significantly improving spatial resolution and enhancing the mapping of smaller fires while reducing omission errors.

### 2.2 Thermal Anomalies vs. Confirmed Fires
Satellite observations primarily detect thermal contrast and radiative energy rather than visually verified fires. NASA FIRMS guidelines and Schroeder et al. (2014) highlight inherent commission errors, cloud obstruction, and sensor limitations. This establishes the necessity of applying confidence filtering, metadata evaluation, and contextual preprocessing before raw data can be interpreted reliably.

### 2.3 Machine Learning and Computational Approaches
Computational methods play a major role in modern wildfire analysis. Sayad et al. (2019) and Jain et al. (2020) demonstrated that machine learning approaches can effectively model fire occurrence and environmental features using remote sensing data. However, while predictive modeling is robust, interpretability and operational pipeline complexity remain challenges, supporting the need for a focused, lightweight detection and event-aggregation workflow.

### 2.4 Pixel Detections to Coherent Fire Events
Transforming fragmented, pixel-level thermal anomalies into discrete, manageable events is a critical software challenge. Recent frameworks, such as the FireCluster approach by Chen et al. (2026), utilize spatiotemporal clustering algorithms to group multi-sensor detections into coherent wildfire events, reducing noise and improving spatial interpretation.

### 2.5 Operational Systems and Multi-Source Intelligence
Large-scale operational platforms, such as the European Forest Fire Information System (EFFIS) reviewed by San-Miguel-Ayanz et al. (2012), along with multimodal architectures by Joshi et al. (2026), demonstrate that integrating thermal hotspots with spatial context significantly enhances monitoring workflows and decision-support capabilities.

---

## 3. Literature Matrix Summary

| Author(s) & Year | Core Focus / Domain | Key Contribution | Relevance to Project |
| :--- | :--- | :--- | :--- |
| **Giglio et al. (2016)** | MODIS Collection 6 | Details active fire detection algorithm and global products. | Provides historical baseline and algorithmic context for MODIS feeds. |
| **Schroeder et al. (2014)** | VIIRS 375 m Product | Evaluates high-resolution active fire data product performance. | Justifies using VIIRS 375 m for improved spatial precision over legacy pixels. |
| **Csiszar et al. (2014)** | Suomi NPP VIIRS | Assesses initial product status and spatial capabilities. | Validates satellite data reliability for operational tracking. |
| **Jain et al. (2020)** | ML in Wildfire Science | Comprehensive review of machine learning applications. | Frames computational approaches, supporting structured workflow design. |
| **Sayad et al. (2019)** | Predictive Modeling | Evaluates datasets and ML approaches for wildfire prediction. | Compares prediction paradigms against direct anomaly detection workflows. |
| **San-Miguel-Ayanz et al. (2012)** | EFFIS Operational System | Comprehensive monitoring of wildfires across Europe. | Demonstrates value of structured operational monitoring frameworks. |
| **Chen et al. (2026)** | FireCluster Algorithm | Multi-source active fire data clustering for event identification. | Direct methodological precedent for spatiotemporal clustering implementation. |
| **Joshi et al. (2026)** | Multimodal Risk & Detection | Satellite imagery and climate data early detection workflows. | Highlights the importance of interactive web visualization and API ingestion. |
| **Kang et al. (2023)** | Deep Learning Monitoring | Adaptable models considering environmental conditions. | Emphasizes the need to preserve observation metadata (acquisition time, brightness). |
| **Phelps & Woolford (2021)** | Fire Occurrence Prediction | Compares statistical and ML methods for wildland fires. | Helps differentiate active event detection from long-term risk forecasting. |

---

## 4. Identified Research Gap
While satellite fire detection and ML risk modeling are well-established in scientific literature, existing solutions are often fragmented, highly complex, or lack modular accessibility. 

**Research Gap:** There is insufficient investigation of an accessible, API-driven, interactive wildfire monitoring workflow that combines near-real-time thermal anomaly retrieval, automated spatiotemporal event clustering, and user-oriented web visualization within a single lightweight system. This project directly addresses this gap through engineered software integration.