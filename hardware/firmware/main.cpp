#include <Arduino.h>
#include <Wire.h>
#include "FDC1004.h"

// Task handles for FreeRTOS dual-core split
TaskHandle_t SensorTask;
TaskHandle_t MLInferenceTask;
SemaphoreHandle_t i2cMutex;

// Global sensor variables protected by mutex
float latestCapacitance = 0.0;
float latestAcousticFreq = 0.0; // derived from MEMS
float latestNPK[3] = {0,0,0};

FDC1004 fdc;

void sensor_read_task(void * parameter) {
  for(;;) {
    if (xSemaphoreTake(i2cMutex, portMAX_DELAY)) {
      // 1. Read Capacitive (Water Stress)
      fdc.triggerSingleMeasurement(FDC1004_100HZ, FDC1004_CH1);
      delay(15);
      uint16_t value[2];
      if (fdc.readMeasurement(FDC1004_CH1, value) == 0) {
        latestCapacitance = fdc.getCapacitance(value);
      }
      
      // 2. Read NPK via simulated Modbus/Serial placeholder
      // latestNPK = read_modbus_npk();
      
      // 3. Update Acoustic baseline from MEMS (I2S DMA buffering logic not shown for brevity)
      
      xSemaphoreGive(i2cMutex);
    }
    vTaskDelay(2000 / portTICK_PERIOD_MS); // Sample every 2 seconds
  }
}

void ml_inference_task(void * parameter) {
  for(;;) {
    float currentCap, currentAc, currentN, currentP, currentK;
    
    // Copy safely
    if (xSemaphoreTake(i2cMutex, portMAX_DELAY)) {
      currentCap = latestCapacitance;
      currentAc = latestAcousticFreq;
      currentN = latestNPK[0];
      currentP = latestNPK[1];
      currentK = latestNPK[2];
      xSemaphoreGive(i2cMutex);
    }

    // TFLite Micro invocation placeholder
    // float risk_score = invoke_tflite_model(currentCap, currentAc, currentN, currentP, currentK);
    float risk_score = (currentCap < 1.0) ? 0.8 : 0.2; // naive heuristic fallback
    
    Serial.printf("Offline ML Inference -> Risk Score: %.2f\n", risk_score);
    if(risk_score > 0.75) {
      Serial.println("ALERT: Local offline threshold exceeded. Disease/Pest or extreme drought detected!");
    }
    
    vTaskDelay(5000 / portTICK_PERIOD_MS);
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  
  i2cMutex = xSemaphoreCreateMutex();
  
  // Pin to Core 0 for Sensor IO
  xTaskCreatePinnedToCore(sensor_read_task, "SensorTask", 4096, NULL, 1, &SensorTask, 0);
  // Pin to Core 1 for ML Inference
  xTaskCreatePinnedToCore(ml_inference_task, "MLTask", 8192, NULL, 1, &MLInferenceTask, 1);
}

void loop() {
  // FreeRTOS handles execution
  vTaskDelete(NULL);
}
