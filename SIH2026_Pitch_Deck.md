# SIH 2026 Presentation Deck (Problem Statement: SIH26180)

This is a comprehensive, slide-by-slide guide structured specifically for the Smart India Hackathon (SIH) format. You can copy this content directly into your PowerPoint / Canva design.

---

## Slide 1: Title Slide

**Project Title:** Canopy — AI-Powered Smart Farming Assistant
**Team Name:** [Your Team Name]
**Problem Statement Code:** SIH26180 (Hardware / Agriculture & Rural Development)
**Organization / Ministry:** Qualcomm Inc.

*(Visual suggestion: A clean, vibrant background showing a satellite scanning a farm polygon, with the Canopy UI overlaid)*

---

## Slide 2: The Problem

**Header:** The Crisis in Indian Agriculture
**Bullets:**

- **Delayed Intervention:** Farmers discover crop diseases, pest infestations, and nutrient deficiencies only *after* severe visible damage has occurred.
- **Climate Vulnerability:** Increasing frequency of droughts, heatwaves, and floods devastates yields without early climate-risk flagging.
- **Resource Inefficiency:** Generic irrigation and fertilization practices lead to wasted water, high input costs, and soil degradation.
- **The Gap:** Existing solutions require expensive lab tests or complex drone hardware unavailable to smallholder Indian farmers.

*(Visual suggestion: Split screen showing stressed crops vs. the SIH text describing agricultural risks in India)*

---

## Slide 3: Our Solution (The 'Canopy' Idea)

**Header:** Real-time On-Device Intelligence
**Bullets:**

- **Satellite & Edge Fusion:** We combine OSINT remote sensing (Sentinel-2 proxies, Open-Meteo) with edge-deployed Large Language Models to generate instant field diagnostics.
- **7-Metric Predictive Engine:** Automatically analyzes Mean NDVI, temperature, moisture, and sunlight to output predictions for:
  1. Stress Severity
  2. Crop Disease Risk (e.g., Fungal thresholds)
  3. Pest Pressure
  4. N-P-K Soil Health Deficiencies
  5. Irrigation Requirements
  6. Climate Resilience Flags (Drought/Heatwave)
  7. Overall Canopy Confidence
- **Accessible & Field-Deployable:** Operates as a highly-optimized, responsive dashboard bypassing the need for immediate localized physical hardware while retaining hardware-deployment readiness.

---

## Slide 4: Technology Stack

**Header:** Modern, Scalable, and Serverless
**Bullets/Diagram:**

- **Frontend / UI:** Vanilla JS Ecosystem seamlessly integrated with Leaflet.js rendering multi-layered topographic and satellite maps.
- **Computation / Edge:** Vercel Serverless Edge Architecture ensuring sub-second global delivery with zero cold-start bottlenecks.
- **Artificial Intelligence:** Google Gemini AI Native SDK (v2+) locked to rigid JSON-schema execution for deterministic, hallucination-free analytical payloads.
- **Data Layers:** Open-Meteo live endpoints and simulated Normalized Difference Vegetation Index (NDVI) models.
- **Security & Integrity:** DOMPurify for XSS-safe DOM injection and custom WebGL GPU-context recovery hooks.

---

## Slide 5: Key Use Cases

**Header:** Empowering the Agricultural Ecosystem
**Bullets:**

1. **The Smallholder Farmer:** Instantly select a farm plot on a mobile device and receive an immediate "Irrigate now" or "High pest risk alert" without requiring specialized knowledge.
2. **Agricultural Extension Workers (KVKs):** Monitor broad village-level canopies, identifying regional fungal outbreaks before they spread across borders.
3. **Agri-Financing & Policy Makers:** Track historical vegetation trends across seasons to validate insurance claims following heatwaves or unseasonal floods.

---

## Slide 6: Novelty & Showstoppers (SIH Mandatory)

**Header:** What sets Canopy apart?
**Bullets:**

- **Hardware-Ready Data Fusion:** While currently proxy-driven, the pipeline is engineered to instantly ingest real `CSI` (Capacitive Sensing) and IoT data streams out of the box using our MOONLIGHT Bayesian equations.
- **Structured LLM Overhaul:** We don't just dump AI prose. We force the LLM into a deterministic JSON constraint engine, guaranteeing 7 specific UI metrics every single time.
- **Limitations & Future Scalability:**
  - *Dependency:* Relies on stable satellite data proxy APIs (open-source currently).
  - *Mitigation:* We explicitly transparentize all AI values with `[AI Estimate]` UI badges to ensure farmers ground-truth serious findings.

---

## Speaker Notes / Pitch Tips for the Viva

1. **Drive the Narrative:** "Judges, we aren't just making a dashboard. We took the problem statement literally. SIH26180 asks for pest, disease, NPK, and water analysis. Our Gemini pipeline outputs exactly that, natively."
2. **Point out the Architecture:** Specifically mention that you fought through prompt engineering to force the AI to return *JSON code*, parsing it live on the edge, ensuring it actually looks like an application and not a chatbot.
3. **The WebGL Hook:** Throw in a technical flex. Mention that mapping apps often crash phones due to GPU memory leaks, but you wrote a custom WebGL context recovery hook to ensure the app is field-deployable on lower-end hardware without silent crashes.
