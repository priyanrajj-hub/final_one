# SIH2026 Pitch: The AGRISENSE Novelty Argument

When evaluating AGRISENSE against traditional "Smart Farming" submissions, focus on the following genuine, structurally distinct engineering choices that separate it from typical Arduino-based MVPs:

### 1. Rejection of Single-Sensor Blindspots (MOONLIGHT Engine)

Standard projects trigger irrigation on a single soil-moisture reading. AGRISENSE mathematically acknowledges that *sensors lie*. Our MOONLIGHT fusion algorithm dynamically degrades the weight of our capacitive water sensor if the ambient temperature suggests thermal drift, and entirely drops satellite NDVI from the equation if CDSE Copernicus APIs report high cloud cover in the polygon. It is a robust, fault-tolerant mathematical model (see `docs/FUSION_MATHEMATICS.md`), not a naive `if/else` gateway.

### 2. Spectral NDVI Integration (Not RGB Proxies)

We integrate the actual European Space Agency Copernicus Data Space Ecosystem (CDSE) API to fetch genuine Level-2A Band 4 (Red) and Band 8 (NIR) satellite patches for user-drawn polygons. **We calculate true physical NDVI**, completely abandoning the unscientific, highly unstable "RGB approximation" method used by most hackathon projects.

### 3. Backend Model Segregation & Transparency

We explicitly separated inference, routing, and UI. Our geographical/OSM crop-inference heuristics are fully encapsulated inside testable Python backend modules covered by CI regression tests. Furthermore, we maintain a dedicated `api/data-provenance` transparency pipeline that tells the UI *exactly* which metrics are mathematically simulated for the demo versus which are streaming live from the web (Satellites/Weather models).

### 4. Mathematical Scale Normalization

We built an inverse-sigmoidal scaling function that mathematically projects the unbounded temporal slope of an NDVI trend line directly onto the exact same `[0, 1]` risk curve used by IoT LBP texture readings. This enforces absolute mathematical stability for the fusion architecture.
