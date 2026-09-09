import math
from datetime import datetime

def infer_crop_type(tags, lat, lng, ndvi_history=None, geom_area=None):
    """
    Infers the likely crop type based on OSM tags, Sentinel-2 spectral signatures (NDVI),
    geographical region, and field geometry.
    
    Returns a dict with: 'best_guess' (string), 'confidence' (float), and 'shortlist' (list of dicts).
    """
    # 1. Non-Agricultural Check (Highest Priority)
    if tags:
        # Check for non-crop OSM tags
        landuse = tags.get('landuse', '').lower()
        natural = tags.get('natural', '').lower()
        building = tags.get('building', '')
        
        if landuse in ['residential', 'commercial', 'industrial', 'retail'] or \
           natural in ['wood', 'tree', 'scrub', 'water'] or \
           tags.get('leisure') == 'park' or building:
            return {
                "best_guess": "Non-Agricultural / Mixed Vegetation (Not cropland)",
                "confidence": 100.0,
                "shortlist": []
            }

    # 2. OSM Crop Tags
    if tags:
        explicit_crop = tags.get('crop') or tags.get('produce')
        if explicit_crop:
            formatted = explicit_crop.capitalize() + " (OSM Confirmed)"
            return {
                "best_guess": formatted,
                "confidence": 100.0,
                "shortlist": [{"crop": formatted, "prob": 100.0}]
            }

    ranked_crops = {}
    total_score = 0.0
    
    # helper to add/multiply score
    def add_score(crop, prob_weight):
        nonlocal total_score
        ranked_crops[crop] = ranked_crops.get(crop, 0.0) + prob_weight
        total_score += prob_weight

    # 2. Spectral Signature (NDVI Phenology)
    # Different crops have distinguishable growth curves.
    has_ndvi = False
    if ndvi_history and isinstance(ndvi_history, list) and len(ndvi_history) > 0:
        has_ndvi = True
        # Extract basic phenology metrics
        avg_ndvi = sum(ndvi_history) / len(ndvi_history)
        max_ndvi = max(ndvi_history)
        min_ndvi = min(ndvi_history)
        variance = max_ndvi - min_ndvi
        
        # Sugarcane: holds high NDVI year-round (low variance, high average)
        if avg_ndvi > 0.65 and variance < 0.2:
            add_score("Sugarcane", 40.0)
        
        # Paddy Rice: distinctive flooded start (low/negative NDVI) rapidly spiking to >0.7
        # assuming ndvi_history is ordered chronologically
        if min_ndvi < 0.2 and max_ndvi >= 0.65 and variance > 0.5:
            add_score("Rice Paddy", 35.0)
            
        # Short cycle Row Crops: Moderate peak, quick senescence
        if 0.4 <= max_ndvi <= 0.75 and variance > 0.3:
            add_score("Wheat", 20.0)
            add_score("Soybean", 15.0)
            add_score("Maize / Corn", 15.0)
            
        # Orchards: stable moderate-high NDVI, not as dense as sugarcane
        if 0.45 < avg_ndvi < 0.65 and variance < 0.15:
            add_score("Orchard / Fruit Trees", 25.0)

    # 3. Geo-Spatial Region & Season Prior
    month = datetime.now().month
    season = "rabi" if not (6 <= month <= 10) else "kharif"

    if 25 < lat < 33 and 72 < lng < 80:
        # North India (Punjab/Haryana)
        if season == "rabi":
            add_score("Wheat", 40.0)
            add_score("Mustard", 20.0)
        else:
            add_score("Rice Paddy", 50.0)
            add_score("Cotton", 10.0)
    elif 8 < lat < 15 and 74 < lng < 81:
        # South India
        add_score("Rice Paddy", 30.0)
        add_score("Sugarcane", 20.0)
        add_score("Orchard / Fruit Trees", 15.0)
    elif 18 < lat < 24 and 72 < lng < 80:
        # Central/West India
        if season == "kharif":
            add_score("Cotton", 35.0)
            add_score("Soybean", 30.0)
        else:
            add_score("Wheat", 25.0)
        add_score("Sugarcane", 15.0)
    else:
        # Generic Farmland
        add_score("Mixed Vegetables", 20.0)
        add_score("Row Crop", 15.0)

    # 4. Geometry heuristic (Area in hectares)
    if geom_area is not None and geom_area > 0:
        if geom_area > 5.0:
            add_score("Sugarcane", 10.0)
            add_score("Cotton", 10.0)
        elif geom_area < 0.5:
            add_score("Mixed Vegetables", 15.0)
            
    # Compile results
    if total_score == 0:
        return {
            "best_guess": "Unknown Crop (Inferred)", 
            "confidence": 10.0, 
            "shortlist": [{"crop": "Mixed Row Crops", "prob": 10.0}]
        }

    # Normalize scores and sort
    sorted_crops = sorted([(c, (s/total_score) * 100) for c, s in ranked_crops.items()], key=lambda x: x[1], reverse=True)
    best_c, best_p = sorted_crops[0]
    
    # Cap confidence depending on data quality
    max_confidence_limit = 85.0 if has_ndvi else 65.0
    final_conf = min(best_p, max_confidence_limit)
    
    # Signal Logging via Vercel Stdout (Diagnostic)
    print(f"[CROP INFERENCE DIAGNOSTICS] Location: {lat},{lng} | Area: {geom_area} | NDVI Available: {has_ndvi}")
    if has_ndvi:
        print(f"  > NDVI Stats -> Avg: {avg_ndvi:.3f}, Max: {max_ndvi:.3f}, Min: {min_ndvi:.3f}, Var: {variance:.3f}")
    print(f"  > Geo Season: {season}")
    print(f"  > Computed Baseline Probabilities: {ranked_crops}")
    
    shortlist = [{"crop": c, "prob": round(p, 1)} for c, p in sorted_crops[:5]]

    # Confidence Thresholding: If best probability is too low (< 45% or lacks strong single signal), drop to uncertain
    if final_conf < 45.0:
        print(f"  > Low confidence ({final_conf:.1f}%). Triggering Uncertainty Fallback.")
        return {
            "best_guess": "Uncertain — please confirm",
            "confidence": round(final_conf, 1),
            "shortlist": shortlist
        }

    return {
        "best_guess": f"{best_c} (Inferred)",
        "confidence": round(final_conf, 1),
        "shortlist": shortlist
    }
