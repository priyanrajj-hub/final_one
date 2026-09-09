# Review 1 - Methodology

This architecture leverages a two-pronged mechanism: the Ground Hardware and the Satellite Macro Screening.

- **Ground Hardware (Offline):** Utilizes an ESP32-S3 parsing local I2C/SPI streams from an FDC1004 (capacitive probe) and an INMP441 (MEMS mic). FreeRTOS pins the sensor polling to Core 0 while Core 1 performs local quantized ML inference without relying on internet availability.
- **Satellite Macro (Optional Context):** Utilizes NASA/Copernicus Sentinel-2 datasets. Because they typically lack NIR in the free drone/RGB tiers, we perform RGB regressions against true NDVI targets to establish an `nNDVI` proxy, then look for temporal shifts and LBP spatial anomalies. 
