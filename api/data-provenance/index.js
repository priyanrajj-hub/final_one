module.exports = async function (req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    try {
        const body = req.body || {};

        // This endpoint dynamically evaluates the provenance state based on what the upstream calls returned

        let ndvi_provenance = "Modeled (OSINT/RGB Pipeline)";
        if (body.ndvi_source === "sentinel2_spectral") {
            ndvi_provenance = "Live Spectral (ESA Sentinel-2 L2A)";
        }

        let crop_provenance = "Modeled (Generic Geo-Heuristics)";
        if (body.crop_source && body.crop_source.includes("OSM")) {
            crop_provenance = "Live Extraction (OpenStreetMap Tags)";
        }

        const provenance = {
            "NDVI_Vegetation_Index": ndvi_provenance,
            "Crop_Classification": crop_provenance,
            "Weather_Telemetry": "Live Measurement (Open-Meteo)",
            "Acoustic_Pest_Sensing": "Simulated Input (Hardware Disconnected)",
            "Capacitive_Water_Stress": "Simulated Input (Hardware Disconnected)",
            "NPK_Soil_Probe": "Simulated Input (Hardware Disconnected)",
            "Fusion_Decision_Engine": "Live Execution (MOONLIGHT Model Python Runtime)"
        };

        return res.status(200).json(provenance);
    } catch (err) {
        return res.status(500).json({ error: 'Provenance resolution failure', details: err.message });
    }
};
