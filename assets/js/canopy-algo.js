/**
 * CANOPY AI ADVANCED ALGORITHMS: Bayesian Fusion Engine
 * Implements a Gaussian Naive Bayes fusion matrix to evaluate Crop Stress Index (CSI)
 * based on cross-correlated multi-modal telemetry (NDVI, Temp, Humidity, Rain).
 */

class CanopyBayesianEngine {
    constructor() {
        // Optimal environmental priors for generic C3/C4 crops
        this.priors = {
            temperature: { m: 24.5, s: 6.0 }, // Mean 24.5C, StdDev 6C
            humidity: { m: 65.0, s: 15.0 },
            ndvi: { m: 0.75, s: 0.15 },
            rainDeficit: { m: 0.0, s: 2.0 } // 0mm deficit is optimal
        };
    }

    // Gaussian Probability Density Function
    gaussianPdf(x, mean, stdDev) {
        if (stdDev === 0) return 0;
        const variance = Math.pow(stdDev, 2);
        const exp = Math.exp(-Math.pow(x - mean, 2) / (2 * variance));
        return (1 / Math.sqrt(2 * Math.PI * variance)) * exp;
    }

    normalizeProbability(val, mean, stdDev) {
        const p = this.gaussianPdf(val, mean, stdDev);
        const maxP = this.gaussianPdf(mean, mean, stdDev); // peak probability (optimal)
        return p / maxP; // returns 0.0 to 1.0 (1.0 = perfectly healthy feature)
    }

    /**
     * Compute the unified Crop Stress Index (CSI).
     * Returns: { csi: [0-100], confidence: [0-100], factors: {} }
     */
    computeFusionCSI(telemetry) {
        let pTemp = 1.0, pHum = 1.0, pNdvi = 1.0, pRain = 1.0;
        let c_temp = 0, c_hum = 0, c_ndvi = 0, c_rain = 0;

        if (telemetry.temperature !== undefined) {
            pTemp = this.normalizeProbability(telemetry.temperature, this.priors.temperature.m, this.priors.temperature.s);
            c_temp = 1;
        }
        if (telemetry.humidity !== undefined) {
            pHum = this.normalizeProbability(telemetry.humidity, this.priors.humidity.m, this.priors.humidity.s);
            c_hum = 1;
        }
        if (telemetry.ndvi !== undefined) {
            pNdvi = this.normalizeProbability(telemetry.ndvi, this.priors.ndvi.m, this.priors.ndvi.s);
            c_ndvi = (telemetry.ndvi < 0.2) ? 2 : 1; // Double weight for very low NDVI (critical stress)
        }
        if (telemetry.rainDeficit !== undefined) {
            pRain = this.normalizeProbability(telemetry.rainDeficit, this.priors.rainDeficit.m, this.priors.rainDeficit.s);
            c_rain = 1;
        }

        // Weighted Bayesian Log-Likelihood Fusion
        // Stress increases as joint probability of perfect health decreases
        const totalWeight = c_temp + c_hum + c_ndvi + c_rain;
        if (totalWeight === 0) return { csi: null, confidence: 0 };

        const weightedHealthProb = (
            (pTemp * c_temp) +
            (pHum * c_hum) +
            (pNdvi * c_ndvi) +
            (pRain * c_rain)
        ) / totalWeight;

        // CSI is the inverse of health probability
        const csi = (1.0 - weightedHealthProb) * 100;

        // Confidence scales based on the number of available active telemetry vectors
        const confidence = (totalWeight / 5.0) * 100; // max possible weight is 5

        return {
            csi: Math.min(100, Math.max(0, csi)),
            healthScore: Math.round(weightedHealthProb * 100),
            confidence: Math.round(confidence),
            factors: { pTemp, pHum, pNdvi, pRain }
        };
    }
}

window.CanopyBayesianEngine = CanopyBayesianEngine;
