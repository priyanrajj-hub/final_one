# Review 1 - Literature Survey

This survey assesses the state-of-the-art in both proximal inductive sensing and regional macro-level indices.

1. **Afzal et al. (2017):** Established foundational frameworks for dielectric evaluations of leaf tissue, proving standard capacitive probes can intercept internal VWC (volumetric water content) shifts long before chlorotic stress causes visual cues.
2. **Nolf et al. (2015):** Studied hydraulic constraints and early water stress tracking using xylem acoustic emissions. We adapt this principle to our low-cost MEMS microphone array finding cavitation pops.
3. **Hughes & Salathé (2015):** The original open-source dataset evaluation underlying PlantVillage. It provides the image baseline we utilize for pre-training our Local Binary Pattern texture anomalies for necrotic spotting.
4. **Anitha et al. (2025):** Evaluated modern RF/XGB methodologies with Conformal Prediction architectures on embedded scale systems.

Our architecture heavily builds upon these works. We do not claim original discovery of LBP or nNDVI proxies, but rather the unique temporal fusion of these metrics on ultra-low-cost (ESP32-S3) edge processors combined with macro satellite screening.
