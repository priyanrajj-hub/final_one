# Canopy: Global Vegetation Health Monitor

[![Vercel Deploy](https://img.shields.io/badge/Vercel-Deployed-success)](https://smart-plant-health-monitoring-using-solar-images.vercel.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*Companion Hardware Research Repo:* [Review-2 Repository (Microwave Dielectric Leaf Sensing)](https://github.com/priyanrajj-hub/review2)

Canopy is a browser-based vegetation monitoring dashboard that combines OpenStreetMap land-use classification with real-time weather data to estimate crop health indicators.

## ⚠️ Data Source Transparency

| Feature | Data Source | Status |
| --------- | ----------- | -------- |
| **NDVI Spectral Base** | Sentinel-2 L2A via CDSE API | **Pending User Credentials** — gracefully falls back to OSINT/RGB proxy array when CDSE OAuth is uninitialized or masked by clouds. |
| **Multi-Modal Fusion** | MOONLIGHT Decision Engine | **Live Execution** — Fuses satellite NDVI slope dynamically with simulated acoustics/capacitive inputs on the backend. |
| **Crop Inference** | OSM Specific Tags + Geo-Heuristics | **Live** — Queries OpenStreetMap for exact crop, with strict fallback to coordinate-bounded planting schedules (Kharif/Rabi). |
| **Weather Telemetry** | Open-Meteo Historic + Live | **Live** — Live macro-environmental tracking for localized polygons. |
| **Acoustic Pest / Capacitive / NPK Limits** | Node Simulation | **Hardware Disabled** — The software fusion engine is mathematical and live, but ground IoT parameters are fed via test vectors for web demonstration purposes. |
| **AI Narrative** | Gemini 1.5 Flash structured JSON | **Live** |

### What Would Make NDVI Real?

To get actual satellite-derived NDVI, you need credentials for one of:

- **Sentinel Hub** (ESA Copernicus) — free tier available, requires OAuth2 flow
- **NASA MODIS/VIIRS** (AppEEARS API) — free, but data is coarse
- **Google Earth Engine** — free for research, requires approved account

## 🚀 Roadmap / Future Improvements

- **Authenticated Sentinel Hub Access:** Replace the current OSINT NDVI fallback logic with live Sentinel Hub REST API integration. This requires adding a valid `SENTINEL_HUB_SECRET` to the Vercel backend and handling ESA OAuth2 token renewal logic.
- **Historical Time-Series Fetch:** Rather than simulating the 7-day NDVI trend, fetch true historical multispectral arrays through the Sentinel Hub Statistical API.

## 🏗 Architecture

```
User draws polygon on Leaflet map
        ↓
┌───────────────────────────────────┐
│  3 parallel API calls (browser)  │
├──────────┬──────────┬─────────────┤
│ Overpass │Open-Meteo│ Rain Archive│
│ (OSM tags)│(weather) │ (baseline)  │
└────┬─────┴────┬─────┴──────┬──────┘
     ↓          ↓            ↓
  NDVI proxy  Live temp   Deficit %
     ↓          humidity     ↓
  Rule engine merges all signals
     ↓
  Gemini API (if key) or rule fallback
     ↓
  UI renders with source labels
```

## 🛠️ Running Locally

```bash
# Install dependencies
npm install

# Start local server
node server.js

# Note: The frontend explicitly relies on standard web technologies
# (Leaflet, Chart.js) and does not require complex build steps.
```

## 🧪 Smoke Testing

Run the included smoke test to verify API routes and external fetch stability:

```bash
node test_smoke.js
```
