import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from algorithm.tests.test_crop_inference import (
    test_osm_tag_shortcircuit, test_sugarcane_spectral_signature,
    test_rice_paddy_signature, test_ambiguous_without_ndvi
)

print("Running tests...")
test_osm_tag_shortcircuit()
test_sugarcane_spectral_signature()
test_rice_paddy_signature()
test_ambiguous_without_ndvi()
print("All tests passed.")
