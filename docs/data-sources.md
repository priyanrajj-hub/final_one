# Integration Note: Data Sources & Methodology

## SATELLITE/MACRO LAYER

This project leverages simulated remote sensing due to the unavailability of live Sentinel-2 API credentials in this demo workspace.

### Data Sources

* **Satellite RGB Imagery (Simulated):** Normally retrieved from NASA Earthdata / Copernicus Hub (Sentinel-2 L2A). The RGB (Bends 4, 3, 2) imagery serves as input.
* **Vegetation Index Ground Truth:** When training the nNDVI model, True NDVI (using Band 8 NIR) is used as the target variable for the neural network.
* **Texture Priors:** Models are pre-trained leveraging PlantVillage datasets to identify repeating necrotic lesion textures.

### ALGORITHM NOVELTY & LIMITATIONS

* **Limitation:** True NDVI requires NIR light. Standard satellite RGB fails to provide this.
* **Novelty:** We train a regression model to estimate an NDVI-proxy (nNDVI) solely from RGB. While this heuristic is founded on existing research (e.g., RGB-only Vegetation Indices), the novelty of our approach relies in **Temporal Fusing**. We do not rely statically on nNDVI. We utilize a rolling temporal-change layer to flag sudden onset anomalies which standard absolute thresholds might miss.

[Note to Judges]: The live API ingestion is disabled to maintain stability in this demo environment. The data displayed is a static, realistic sample derived from the methodologies described above.
