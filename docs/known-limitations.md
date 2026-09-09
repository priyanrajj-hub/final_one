# Canopy Platform: Known Limitations & Demo Status

This document explicitly designates which features in the Canopy platform are currently functioning in a **Sample Baseline Mode** versus fully integrated production components. This protects the academic integrity of the project during presentation.

## 1. Sentinel-2 / Copernicus Integration

- **Status:** Pending OAuth credentialing.
- **Limitation:** The platform requires an active Sentinel Hub API key to pull live Level-2A imagery and compute programmatic NDVI.
- **Demo Fallback:** The application currently renders a statically computed NDVI array (e.g., `0.35`) against the Leaflet map bounds for demonstration purposes. The UI is explicitly marked as running in `Sample Baseline Mode`.
- **Validation Route:** See `/docs/validation/ndvi_log.json` for the empirical testing protocol verifying our baseline NDVI bounds against Copernicus EO Browser exports.

## 2. Google Maps 360 / Street View Integration

- **Status:** Pending Billing/Quota Configuration.
- **Limitation:** Full Google Street View capability requires an authorized Maps JavaScript API key restricted to the Vercel domain. Furthermore, agricultural parcels typically lack Street View camera coverage.
- **Demo Fallback:** The application defaults to the `Pannellum` open-source library to render a static 360° demonstration equirectangular projection to mimic the UI/UX architecture.

## 3. Gemini Edge Insight (AI Diagnostic)

- **Status:** Integrated via Vercel Edge (`/api/gemini`).
- **Limitation:** Live access requires the `GEMINI_API_KEY` to be configured in Vercel's Environment Variables.
- **Demo Fallback:** The frontend dynamically queries `/api/health` on load. If the key is missing, the dashboard intelligently suppresses the module, displaying `AI analysis not yet configured`.

## 4. TensorFlow.js Crop Classification (PlantVillage)

- **Status:** Validated Pipeline, End-to-End ImageNet stripped.
- **Limitation:** MobileNetV2 requires structural fine-tuning specific to PlantVillage tensors via an explicit `model.json` compilation structure which exceeds current repository storage limitations.
- **Demo Fallback:** Arbitrary image uploads are disabled. The UI exposes three hardcoded test cases representing 100% verified outputs against benchmarked image classes (`Tomato___Early_blight`, `Apple___Apple_scab`, `Corn_(maize)___healthy`).

## 5. Agronomic Rule-Engine Citations

- **Status:** Explicit thresholds pending literature-review consolidation.
- **Limitation:** The deterministic rule-engine thresholds (e.g., Humidity >65%) are functionally operative but temporarily instantiated using conservative approximations.
- **Demo Fallback:** The UI explicitly denotes these modules as `(Rule-Based)` rather than machine-learning, guaranteeing mathematical transparency over hallucinated AI claims.
