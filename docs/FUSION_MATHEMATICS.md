# MOONLIGHT Fusion Engine: Mathematical Architecture

## Overview

The MOONLIGHT (Multi-Modal Oscillation-Optical fusion with Nocturnal-drift correction) algorithm is the core technical differentiator of the AGRISENSE platform. It deliberately abandons single-sensor heuristics in favor of a dynamically weighted exponential fusion model that correlates macro-level satellite trends with micro-level IoT readings.

## 1. Parameters & Vector Scaling

The model fuses five independent sensor inputs into a unified Crop Stress Index (CSI).
To prevent dimensional collision, all disparate variables are mathematically transformed into a generic `[0, 1]` stress space (where `0` = Optimal Health, `1` = Critical Stress).

- **$C$ (Capacitive Water Stress):** Captured via FDC1004. Scaled 0 to 1 directly natively from dielectric divergence.
- **$A$ (Acoustic Pest Signature):** Captured via INMP441 + FFT analysis. Spectral density in the 4-6kHz pest-chewing band normalized.
- **$N_{stress}$ (Sentinel-2 NDVI Trend):**
  A raw temporal slope (e.g. $\Delta NDVI / \Delta t$) is unbounded. We apply an inverse sigmoidal transform to map it tightly to the generic bounds without clipping:
  $$ N_{stress} = \frac{1}{1 + e^{-k \times N_{slope}}} $$
  *(where $k = -50.0$, driving negative slopes towards $1.0$ and positive slopes to $0.0$.)*
- **$R$ (Rainfall Deficit):** Normalized millimeter-deficit against a 5-year spatial climate mean.
- **$K$ (NPK Deviation):** Electrochemical probe drift translated as absolute percentage deviation from crop-specific ideal norms.

## 2. Dynamic Reliability Weighting

Instead of static weights (e.g., $w_N = 0.25$), MOONLIGHT queries metadata attributes (like cloud cover, thermal noise, and irrigation schedules) at execution time to degrade the weight of compromised sensors:

- $w_N = (1 - cloud\_fraction)^2$
- $w_C = 1 - \frac{|\Delta T|}{T_{max}}$
- $w_A$ degrades based on ambient background `noise_sigma`.
- $w_R$ zeroes out exactly to `0.0` if an active `irrigation_flag` is thrown.

## 3. The Fusion Equation

The raw instant CSI is the weighted mean of the scaled vectors:
$$ CSI_{raw} = \frac{\sum (w_i \cdot x_i)}{\sum w_i} $$

To prevent false-positive alarms from momentary sensor spikes (e.g. bird noise triggering the acoustic sensor), the raw CSI is passed through an Exponential Smoothing filter parameterized by $\tau$ (the recovery time constant):
$$ CSI_t = \lambda \cdot CSI_{raw} + (1 - \lambda) \cdot CSI_{t-1} $$
Where $\lambda = 1 - e^{-\Delta t / \tau}$.

## 4. Derived Interpretability

A purely numerical $CSI$ value risks confusing end-users. A secondary explicit mapping function evaluates the unweighted vectors (e.g., $if N_{stress} > 0.6 \text{ and } A > 0.5$) to append plain-language clinical diagnoses (e.g. *"NDVI temporal degradation correlates with pest signature -> Requires intervention"*).
