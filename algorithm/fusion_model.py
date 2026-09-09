import math
import numpy as np
import sys
import os
from skimage import feature
from collections import deque
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from algorithm.weather_service import get_precipitation_deficit
from GlobalPlantHealth.backend.sentinel_service import get_punjab_image_patch

def moonlight_fusion(C, A, N_trend_raw, R_deficit, K_dev, meta, prev_csi, dt, tau, threshold):
    """
    MOONLIGHT: Multi-Modal Oscillation-Optical fusion with Nocturnal-drift correction
    
    EXTENDED MODIFICATIONS (Task 2):
    - Replaced 'N' (NDVI Texture spatial variance) with 'N_trend_raw' (Temporal NDVI Trend slope).
      *Calibration Fix:* N_trend_raw is continuous (e.g., -0.1 to +0.1 per day). We map it onto a [0, 1] 
      stress scale (N_stress) using an inverse sigmoidal transform to ensure w_N remains calibrated 
      to the same [0, 1] magnitude space that the texture anomalies used to occupy.
    - Added 'K' (NPK Soil Deviation), weighted by npk_reliability based on probe constraints.
    - Added rule-based 'fusion_explanation' generator dynamically checking the dominant stress vectors.
    """
    EPS = 1e-6
    
    # --- 1. Signal Normalization ---
    # Convert N_trend_raw (e.g., -0.05 slope implies degradation) into N_stress [0, 1]
    # Negative trend strongly approaches 1.0 (stressed), Positive/Zero trend approaches 0.0 (healthy).
    k_slope = -50.0  # Steepness of transition
    N = 1.0 / (1.0 + math.exp(-k_slope * N_trend_raw))
    
    # R (Rainfall Deficit) - previously assumed already scaled [0,1], kept identical.
    R = min(max(R_deficit, 0.0), 1.0)
    
    # --- 2. Live Reliability Weights from Metadata ---
    w_C = 1.0 - min(abs(meta.get('delta_T', 0)) / meta.get('T_max', 20.0), 1.0)
    w_A = 1.0 - min(meta.get('noise_sigma', 0) / meta.get('noise_sigma_max', 10.0), 1.0)
    w_N = (1.0 - meta.get('cloud_frac', 0.0)) ** 2
    w_R = 0.0 if meta.get('irrigation_flag', False) else 1.0
    w_K = meta.get('npk_reliability', 0.8) # Constant or derived from calibration timestamp
    
    weights = [w_C, w_A, w_N, w_R, w_K]
    signals = [C, A, N, R, K_dev]

    # --- 3. Weighted Aggregation with Fallback ---
    total_w = sum(weights)
    if total_w < EPS:
        csi_raw = prev_csi if prev_csi is not None else 0.0
    else:
        csi_raw = sum(w * x for w, x in zip(weights, signals)) / total_w

    # --- 4. Exponential Temporal Smoothing ---
    lam = 1 - math.exp(-dt / tau) if tau > 0 else 1.0
    csi = csi_raw if prev_csi is None else lam * csi_raw + (1 - lam) * prev_csi

    # --- 5. Confidence Decomposition ---
    mean_w = sum(weights) / len(weights)
    var_w = sum((w - mean_w) ** 2 for w in weights) / len(weights)
    confidence = max(weights) / (var_w + 1)

    # --- 6. Lead-Time Estimate ---
    lead_time = None
    if prev_csi is not None and dt > 0:
        slope = (csi - prev_csi) / dt
        if slope > EPS:
            lead_time = (threshold - csi) / slope

    # --- 7. Explainability Logic (Fusion Explanation) ---
    explanation = []
    if N > 0.6: explanation.append("NDVI temporal degradation detected")
    elif N < 0.3: explanation.append("NDVI stable")
    
    if A > 0.5: explanation.append(f"Acoustic pest signature detected (High confidence: {w_A:.2f})")
    
    if C > 0.6 and R > 0.6: explanation.append("Severe correlated water-stress (Capacitive drop + Rain deficit)")
    elif C > 0.6: explanation.append("Capacitive water stress elevated")
    
    if K_dev > 0.5: explanation.append("Significant NPK deviation from optimal range")
    
    base_text = " | ".join(explanation) if explanation else "Overall canopy baseline is healthy."
    if A > 0.5 and N > 0.6:
        base_text = "CRITICAL: NDVI degradation strongly correlates with pest presence — early intervention required."

    return {
        "csi": round(csi, 4),
        "confidence": round(confidence, 4),
        "fusion_explanation": base_text,
        "weights": {"capacitive": round(w_C, 3), "acoustic": round(w_A, 3), "ndvi_trend": round(w_N, 3), "rainfall": round(w_R, 3), "npk": round(w_K, 3)},
        "lead_time_hours": round(lead_time, 1) if lead_time else None,
        "label": "ESTIMATED (linear trend) — not a forecast model"
    }

class AgrisenseFusionModel:
    def __init__(self, history_size=5):
        self.history = deque(maxlen=history_size)
    
    def rgb_to_nndvi(self, rgb_array):
        r, g, b = rgb_array[0], rgb_array[1], rgb_array[2] 
        exg = 2 * g - r - b 
        return np.clip(exg / 255.0, -1, 1)

    def texture_anomaly_layer(self, image_patch):
        if len(image_patch.shape) == 3:
            gray = np.dot(image_patch[...,:3], [0.2989, 0.5870, 0.1140])
        else:
            gray = image_patch
        radius = 1
        n_points = 8 * radius
        lbp = feature.local_binary_pattern(gray, n_points, radius, method="uniform")
        anomalies = np.sum(lbp >= n_points)
        total_pixels = lbp.shape[0] * lbp.shape[1]
        return min(anomalies / float(total_pixels) * 5.0, 1.0) 

    def predict_field_risk(self, rgb_patch=None, invoke_apis=False, prev_csi=0.2):
        if invoke_apis or rgb_patch is None:
            rgb_patch = get_punjab_image_patch()
            weather_data = get_precipitation_deficit()
        else:
            weather_data = {"deficit_mm": 0.0, "status": "SYNTHETIC_TEST"}

        base_nndvi = self.rgb_to_nndvi(np.mean(rgb_patch, axis=(0,1)))
        self.history.append(base_nndvi)
        
        # C (Capacitive), A (Acoustic), N_trend_raw (NDVI Trend), R (Rainfall), K_dev (NPK Deviation)
        C = 0.4 # Proxy ground-truth baseline
        A = 0.2 # Proxy acoustic pest score
        
        if len(self.history) >= 2:
            N_trend_raw = (self.history[-1] - self.history[0]) / len(self.history)
        else:
            N_trend_raw = -0.02 # Synthetic slight degradation baseline

        R = min(max(weather_data['deficit_mm'] / 50.0, 0.0), 1.0)
        K_dev = 0.15 # Synthetic NPK deviation (e.g., Nitrogen slightly depleted)
        
        # Meta for dynamic weighting
        meta = {
            'delta_T': 2.5, 'T_max': 20.0,       # C fail bounds
            'noise_sigma': 2.0, 'noise_sigma_max': 10.0, # A fail bounds
            'cloud_frac': 0.15,                 # N fail bounds
            'irrigation_flag': False,           # R fail bounds
            'npk_reliability': 0.8              # K reliability weight
        }
        
        result = moonlight_fusion(C, A, N_trend_raw, R, K_dev, meta, prev_csi=prev_csi, dt=24.0, tau=48.0, threshold=0.7)
        # Append nNDVI_raw and status to output payload
        result['nNDVI_raw'] = base_nndvi
        result['data_status'] = weather_data.get('status', 'PROXY')
        return result

if __name__ == "__main__":
    fusion = AgrisenseFusionModel()
    print("--- Testing Live Api MOONLIGHT Fusion ---")
    print(fusion.predict_field_risk(invoke_apis=True))
