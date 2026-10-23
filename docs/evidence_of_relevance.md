# Evidence of Relevance and User Research

## 1. Domain Context & Practical Need
Operational wildfire management requires timely and accurate spatial intelligence. While spaceborne sensors like MODIS Collection 6 (Giglio et al., 2016) and VIIRS 375 m (Schroeder et al., 2014) provide global coverage, monitoring personnel face significant cognitive and operational friction. Raw data streams consist of thousands of isolated thermal points daily, containing commission errors, cloud artifacts, and agricultural burns.

## 2. Evidence from Domain Analysis & Stakeholder Insights
Based on stakeholder discussions and workflow observations in environmental monitoring:
- **High Volume Fatigue:** Monitoring staff are overwhelmed by raw point notifications, making manual filtering for true cluster events inefficient.
- **Need for Event-Level Abstraction:** End-users do not inherently care about individual 375m pixels; they require aggregated boundaries, timestamps, and confidence metrics representing a single "fire event."
- **Accessibility Barrier:** Existing institutional tools are often heavy, proprietary, or lack modular API-driven architectures suitable for rapid regional deployment.

## 3. Distinguishing Empirical Findings from Assumptions
- **Empirical Findings (Verified via Literature & Data Specs):** NASA FIRMS provides open access to near-real-time CSV/JSON feeds; VIIRS 375 m significantly improves spatial precision over legacy 1 km MODIS pixels (Schroeder et al., 2014); spatial proximity and temporal continuity strongly correlate with single combustion sources.
- **Project Assumptions:** A lightweight web application combining automated retrieval and client-side visualization can adequately streamline manual inspection without requiring enterprise-grade cloud clusters.