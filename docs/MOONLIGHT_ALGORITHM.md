# MOONLIGHT: A Multi-Modal, Confidence-Weighted Fusion Algorithm for Early Crop Stress Detection

**M**ulti-modal **O**scillation-**O**ptical fusion with **N**octurnal-drift correction for **L**ocalized **I**ndex of **G**round-truth and satellite **H**ealth **T**riage

**Author:** Priyanraj — Team Meta Monkey, SIH26180
**System:** AGRISENSE Field Intelligence Platform
**Status:** Original formulation, unpublished. Validation pending real hardware/imagery data (see §8, Limitations).

---

## Abstract

Existing plant-stress detection systems typically rely on a single modality — either ground-level sensing (capacitive, acoustic) or remote sensing (NDVI-class vegetation indices) — evaluated independently, with no principled way to combine them when they disagree. This paper proposes **MOONLIGHT**, a confidence-weighted Bayesian fusion algorithm that combines four heterogeneous signal streams — capacitive dielectric water-stress sensing, acoustic emission-rate cavitation/pest detection, satellite-derived NDVI-texture (LBP) anomaly scoring, and rainfall-deficit correlation — into a single calibrated **Crop Stress Index (CSI)** with an accompanying, decomposable confidence score. Unlike naive weighted averaging, MOONLIGHT treats each modality's *reliability* as a function of its own internal signal quality (e.g., cloud cover reduces satellite confidence; humidity swings reduce capacitive confidence) rather than a fixed constant, and propagates that reliability into the final index rather than hiding it. We present the mathematical formulation, pseudocode, computational complexity, and — honestly — the validation this method still requires before any claim of accuracy can be made.

---

## 1. Motivation and Novelty Claim

Three sensing traditions exist in isolation in the literature this project draws on:

1. **Capacitive/dielectric leaf water-status sensing** (Afzal et al., 2017) — measures water content via electrical capacitance, but is known to drift with ambient temperature and humidity.
2. **Acoustic emission analysis** (Nolf et al., 2015) — detects xylem cavitation events via acoustic emission rate, correlating with drought stress, but is noisy in windy or high-ambient-noise field conditions.
3. **Satellite vegetation indices** (Rouse et al., 1974) and **texture anomaly detection** (Ojala et al., 2002) — detect regional stress via reflectance and surface-texture change, but suffer from cloud contamination, coarse revisit intervals, and canopy-level (not plant-level) resolution.

Each of these has a well-documented **failure mode that is orthogonal to the others**: cloud cover doesn't affect capacitance; sensor drift doesn't affect satellite imagery; wind noise doesn't affect NDVI. This is the actual, defensible novelty claim: **MOONLIGHT is not a new sensor or a new index — it is a fusion architecture that explicitly models when each existing method should be trusted, and downweights it automatically when its own failure mode is active**, rather than fusing all sources with fixed or manually-tuned weights (the common approach in prior multi-sensor agri-fusion work).

This is a modest, honest, and checkable claim — appropriate for a jury that will ask "what's actually new here?"

---

## 2. Signal Definitions

Let each field-plot $p$ at time $t$ produce four raw modality scores, each independently normalized to $[0,1]$ where 1 = maximum stress:

| Symbol | Modality | Source | Failure mode |
| --- | --- | --- | --- |
| $C_t$ | Capacitive water-stress score | FDC1004, ground node | Temperature/humidity drift |
| $A_t$ | Acoustic stress score | INMP441 emission-rate | Wind/ambient noise |
| $N_t$ | NDVI-texture anomaly score | Sentinel-2 L2A + LBP | Cloud cover, coarse revisit |
| $R_t$ | Rainfall-deficit correlation score | Open-Meteo 14-day fusion | Irrigation confounds (false positive when irrigated) |

Each modality also produces a **self-reported reliability** $w_i(t) \in [0,1]$ — not a static weight, but a live signal-quality estimate computed *from the modality's own metadata*:

$$
w_C(t) = 1 - \left|\frac{\Delta T_t}{T_{max}}\right|, \qquad
w_A(t) = 1 - \frac{\sigma_{noise}(t)}{\sigma_{noise}^{max}}, \qquad
w_N(t) = (1 - \text{cloud\_frac}(t))^2, \qquad
w_R(t) = 1 - \mathbb{1}[\text{irrigation\_flag}(t)]
$$

This is the core mechanism: **reliability is derived from observable metadata already present in each pipeline** (temperature delta from the calibration baseline, RMS noise floor, cloud-mask fraction from Sentinel-2's SCL band, and an irrigation-event flag), not from a hand-tuned constant. This is what makes the fusion "confidence-weighted" rather than "averaged."

---

## 3. The Fusion Equation

### 3.1 Weighted stress aggregation

$$
\text{CSI}_{raw}(t) = \frac{\sum_{i \in \{C,A,N,R\}} w_i(t) \cdot x_i(t)}{\sum_{i \in \{C,A,N,R\}} w_i(t) + \epsilon}
$$

where $x_i(t) \in \{C_t, A_t, N_t, R_t\}$ and $\epsilon$ is a small constant preventing division by zero when all modalities report near-zero reliability (e.g., total cloud cover *and* a dead ground node — the correct behavior here is to fall back to the last known good CSI, not to output a meaningless zero).

### 3.2 Temporal smoothing (exponential decay)

A single noisy timestep should not cause a stress alert. MOONLIGHT applies exponential decay smoothing with a half-life tuned to the fastest-onset failure mode this system targets (rapid-onset pest chewing, per the acoustic literature, can manifest within 24–48h):

$$
\text{CSI}(t) = \lambda \cdot \text{CSI}_{raw}(t) + (1-\lambda) \cdot \text{CSI}(t-1), \qquad \lambda = 1 - e^{-\Delta t / \tau}
$$

with $\tau$ (the decay time constant) set per-crop based on known stress-onset speed — this is a tunable, documented parameter, not a magic number.

### 3.3 Confidence decomposition

The headline number a farmer or judge sees should never be presented without its confidence, and that confidence should be *explainable*, not a black box:

$$
\text{Confidence}(t) = \frac{\max_i w_i(t)}{\text{Var}(w_1, w_2, w_3, w_4) + 1}
$$

This rewards both (a) at least one highly reliable modality being active, and (b) *agreement* among modalities' reliabilities — if three sensors are confident and one is degraded, confidence stays high; if all four are marginal and disagree, confidence correctly collapses. This decomposition is exactly what should populate the "confidence score breakdown on hover" UI feature already planned for the dashboard — this gives that feature a real formula to compute, instead of a random number.

### 3.4 Early-warning lead-time estimate

$$
\text{LeadTime}(t) = \frac{\text{CSI}_{threshold} - \text{CSI}(t)}{\frac{d(\text{CSI})}{dt}}, \quad \text{valid only if } \frac{d(\text{CSI})}{dt} > 0
$$

This is a **linear extrapolation**, not a predictive model — it should be labeled in the UI exactly as that ("estimated at current trend rate," not "AI-predicted"), because that is what it honestly is. Overclaiming this as a machine-learned forecast would be exactly the kind of dishonesty this whole project has been trying to eliminate.

---

## 4. Pseudocode

```python
def moonlight_fusion(C, A, N, R, meta, prev_csi, dt, tau, threshold):
    EPS = 1e-6
    # 1. Compute live reliability weights from metadata
    w_C = 1 - min(abs(meta['delta_T']) / meta['T_max'], 1.0)
    w_A = 1 - min(meta['noise_sigma'] / meta['noise_sigma_max'], 1.0)
    w_N = (1 - meta['cloud_frac']) ** 2
    w_R = 0.0 if meta['irrigation_flag'] else 1.0
    
    weights = [w_C, w_A, w_N, w_R]
    signals = [C, A, N, R]

    # 2. Weighted aggregation with fallback
    total_w = sum(weights)
    if total_w < EPS:
        csi_raw = prev_csi if prev_csi is not None else 0.0
    else:
        csi_raw = sum(w * x for w, x in zip(weights, signals)) / total_w

    # 3. Exponential temporal smoothing
    import math
    lam = 1 - math.exp(-dt / tau)
    csi = csi_raw if prev_csi is None else lam * csi_raw + (1 - lam) * prev_csi

    # 4. Confidence decomposition
    mean_w = sum(weights) / len(weights)
    var_w = sum((w - mean_w) ** 2 for w in weights) / len(weights)
    confidence = max(weights) / (var_w + 1)

    # 5. Lead-time estimate
    lead_time = None
    if prev_csi is not None and dt > 0:
        slope = (csi - prev_csi) / dt
        if slope > EPS:
            lead_time = (threshold - csi) / slope

    return {
        "csi": round(csi, 4),
        "confidence": round(confidence, 4),
        "weights": {"capacitive": w_C, "acoustic": w_A, "ndvi_texture": w_N, "rainfall": w_R},
        "lead_time_hours": lead_time,
        "label": "ESTIMATED (linear trend) — not a forecast model"
    }
```

**Complexity:** $O(1)$ per plot per timestep.

---

## 5. Why This Is Defensible Under Cross-Examination

- **"Why not just train an ML model to learn the weights?"** Because you have no labeled training data yet, and a closed-form, interpretable formula that degrades gracefully and can be explained on a whiteboard is more defensible *at this stage* than an uninterpretable model trained on synthetic data.
- **"How did you choose $\tau$ and the threshold?"** Currently as documented, tunable constants informed by literature-reported stress-onset windows.
- **"What happens when all four modalities disagree completely?"** The confidence score explicitly collapses via the variance term.

---

## 8. Limitations

This algorithm is a **mathematical formulation, not yet a validated result.** Do not present it as "tested" or "accurate" until the following are true:

1. No real accuracy numbers exist yet.
2. It depends on the underlying signals being real. Fusing four proxy signals produces a more sophisticated proxy, not a real measurement.
3. Irrigation-flag detection currently assumes an external flag exists.
