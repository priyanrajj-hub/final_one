from algorithm.crop_inference import infer_crop_type

def test_osm_tag_shortcircuit():
    tags = {'crop': 'chickpea'}
    res = infer_crop_type(tags, 20.0, 75.0)
    assert res['best_guess'] == "Chickpea (OSM Confirmed)"
    assert res['confidence'] == 100.0

def test_sugarcane_spectral_signature():
    # High average NDVI, low variance
    ndvi_history = [0.70, 0.72, 0.68, 0.75, 0.74, 0.71]*2 # 12 months
    res = infer_crop_type({}, 12.0, 78.0, ndvi_history=ndvi_history, geom_area=8.0)
    # With area > 5.0 and signature matching, Sugarcane should win.
    assert "Sugarcane" in res['best_guess']
    # Max confidence limit is 85 with NDVI
    assert res['confidence'] <= 85.0

def test_rice_paddy_signature():
    # Low start (flooded), high peak
    ndvi_history = [-0.1, 0.1, 0.4, 0.7, 0.8, 0.75, 0.4, 0.2]
    # Given in Punjab (25-33 lat) in Rabi, Wheat is normally dominant, 
    # but Rice signature should strongly boost Rice Paddy.
    res = infer_crop_type({}, 28.0, 75.0, ndvi_history=ndvi_history)
    assert "Rice Paddy" in res['best_guess']

def test_ambiguous_without_ndvi():
    # No tags, no ndvi, relying solely on geo priors
    res = infer_crop_type({}, 28.0, 75.0) # North India
    assert res['confidence'] <= 65.0
    assert len(res['shortlist']) >= 2
