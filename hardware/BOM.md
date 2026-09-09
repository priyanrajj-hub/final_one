# Bill of Materials (BOM) - AGRISENSE Sensor Node

| Component | Quantity | Purpose | Approx. Cost (INR) |
| --- | --- | --- | --- |
| **ESP32-S3 WROOM-1** | 1 | Main dual-core microcontroller (Wifi/BLE), handles DSP and ML inference. | ₹400 |
| **FDC1004 Capacitive Sensor** | 1 | Leaf dielectric permittivity for water stress. | ₹250 |
| **INMP441 MEMS Microphone** | 1 | Acoustic sensing for pest/insect chewing sounds. | ₹150 |
| **NPK Soil Sensor (RS485/Modbus)** | 1 | Ground truth nutrient (N/P/K) monitoring. | ₹350 |
| **OV2640 Camera Module** | 1 | Low-cost RGB image capture for localized visual checks. | ₹200 |
| **Solar Panel (5V/1W) + TP4056** | 1 | Power harvesting and charging circuit. | ₹100 |
| **18650 Li-Ion Battery (2000mAh)** | 1 | Energy storage for continuous offline operation. | ₹90 |
| **Miscellaneous (PCB, Wires, passives)** | 1 | Interconnects and structural base. | ₹50 |
| **Total Estimated Cost** | | | **~₹1600** |

*Note: The target cost was ~₹1,500. This estimate is slightly above target (~₹1,600) due to adding the solar charging module for true field deployment autonomy. Bulk PCB ordering would bring this down.*
