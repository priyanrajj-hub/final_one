import sys
import os
import math
import numpy as np

# Mocking the missing GlobalPlantHealth modules so test_fusion can import fusion_model independently
class MockSentinelService:
    @staticmethod
    def get_punjab_image_patch():
        return np.ones((10, 10, 3))
sys.modules['GlobalPlantHealth'] = type('MockModule', (), {})
sys.modules['GlobalPlantHealth.backend'] = type('MockModule', (), {})
sys.modules['GlobalPlantHealth.backend.sentinel_service'] = MockSentinelService

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from algorithm.fusion_model import moonlight_fusion

base_meta = {
    'delta_T': 1.0, 'T_max': 20.0,
    'noise_sigma': 1.0, 'noise_sigma_max': 10.0,
    'cloud_frac': 0.1,
    'irrigation_flag': False,
    'npk_reliability': 0.8
}

def test_signal_calibration_preservation():
    """
    Test to ensure the new N_trend_raw parameter logic does not wildly break 
    CSI score expectations compared to the old N_texture logic.
    Old logic assumed N in [0, 1]. New logic calculates N via inverse sigmoid.
    """
    print("\n--- Test: Calibration Preservation (Texture vs Trend) ---")
    
    # Old model equivalent: If texture anomaly was 0.8 (high stress)
    # New model: If trend is highly negative (e.g., -0.05), N should internally map to ~ 0.92
    
    res_healthy = moonlight_fusion(0.1, 0.1, 0.05, 0.1, 0.1, base_meta, None, 24.0, 48.0, 0.7)
    res_stressed = moonlight_fusion(0.1, 0.1, -0.05, 0.1, 0.1, base_meta, None, 24.0, 48.0, 0.7)
    
    print(f"Healthy Trend (+0.05) CSI: {res_healthy['csi']} | Exp N weight internal behavior stable")
    print(f"Degraded Trend (-0.05) CSI: {res_stressed['csi']} | Exp N weight internal behavior stable")
    
    assert res_healthy['csi'] < 0.15, f"Healthy trend should result in base CSI. Got {res_healthy['csi']}"
    assert res_stressed['csi'] > 0.22, f"Degraded trend should spike the CSI significantly higher. Got {res_stressed['csi']}"

def test_all_healthy():
    print("\n--- Test: All Healthy ---")
    res = moonlight_fusion(
        C=0.1, A=0.1, N_trend_raw=0.02, R_deficit=0.0, K_dev=0.05, 
        meta=base_meta, prev_csi=0.1, dt=24.0, tau=48.0, threshold=0.7
    )
    print(f"Result CSI: {res['csi']} | Explanation: {res['fusion_explanation']}")
    assert res['csi'] < 0.2

def test_pest_only():
    print("\n--- Test: Pest Only (Acoustic Spike) ---")
    res = moonlight_fusion(
        C=0.1, A=0.8, N_trend_raw=-0.01, R_deficit=0.0, K_dev=0.1, 
        meta=base_meta, prev_csi=0.2, dt=24.0, tau=48.0, threshold=0.7
    )
    print(f"Result CSI: {res['csi']} | Explanation: {res['fusion_explanation']}")
    assert "pest" in res['fusion_explanation'].lower()

def test_water_stress_only():
    print("\n--- Test: Water Stress (Capacitive + Rainfall Deficit) ---")
    res = moonlight_fusion(
        C=0.9, A=0.1, N_trend_raw=-0.02, R_deficit=0.8, K_dev=0.1, 
        meta=base_meta, prev_csi=0.4, dt=24.0, tau=48.0, threshold=0.7
    )
    print(f"Result CSI: {res['csi']} | Explanation: {res['fusion_explanation']}")
    assert "water-stress" in res['fusion_explanation']

def test_combined_stress():
    print("\n--- Test: Combined Critical Stress (Pest + NDVI Drop) ---")
    res = moonlight_fusion(
        C=0.5, A=0.9, N_trend_raw=-0.08, R_deficit=0.4, K_dev=0.4, 
        meta=base_meta, prev_csi=0.5, dt=24.0, tau=48.0, threshold=0.7
    )
    print(f"Result CSI: {res['csi']} | Explanation: {res['fusion_explanation']}")
    assert "CRITICAL" in res['fusion_explanation']

if __name__ == "__main__":
    test_signal_calibration_preservation()
    test_all_healthy()
    test_pest_only()
    test_water_stress_only()
    test_combined_stress()
    print("\nAll synthetic fusion logic tests passed!")
