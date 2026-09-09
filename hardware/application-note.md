# Application Note: AGRISENSE Ground Node

## Problem Addressed

Standard satellite-based vegetation index (NDVI) monitoring suffers from temporal limits (cloud cover, 5-day revisit times) and struggles to detect acute, immediate stress (e.g. flash drought or rapid pest infestation onset) before significant chlorophyll degradation happens.

## Deployment Scenario

The AGRISENSE Ground Node is an ultra-low-cost (~$18 / ₹1,500) device meant for smallholder farmers.

- **Power**: It leverages a 5V/1W solar panel charging an 18650 cell, enabling true offline autonomy.
- **Computation**: It boasts on-device intelligence via a TinyML (Quantized TFLite Micro) model deployed directly on the ESP32-S3.
- **Sensing Modalities**: Fusing capacitive dielectric sensing (water stress), acoustic monitoring via MEMS (pest attack), and NPK probes.

## Offline/Real-Time Architecture (SIH26180 Specific)

Because agricultural fields in rural areas lack consistent broadband, this node runs completely offline. The local ML classifier fuses sensor inputs and triggers a local alert (via status LED or short-range LoRa broadcast) independently of any cloud infrastructure, strongly satisfying the "field-deployable" and "on-device intelligence" requirements.

This node acts as the "ground truth" and real-time core. The SATELLITE/MACRO layer is completely optional and complementary—providing regional-scale prioritization when internet is available.
