export default async function handler(req, res) {
    // Only allow POST
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        const body = req.body;
        const msg = (body.message || '').toLowerCase();

        let actions = [];
        let response_text = `I am AGRI-JARVIS. (Sample Baseline Mode). You said: ${body.message}. I am analyzing the telemetry...`;

        // Fast-path intent matching
        if (msg.includes("zoom in") || msg.includes("अंदर") || msg.includes("பெரிதாக்கு")) {
            response_text = "Zooming in on the map.";
            actions.push({ type: "zoom_map", level: 1 });
        } else if (msg.includes("high risk") || msg.includes("खतरा") || msg.includes("ஆபத்து")) {
            response_text = "Showing the highest risk fields in Sample Baseline Mode.";
            actions.push({ type: "filter_by_risk", level: "High" });
        } else if (msg.includes("ndvi")) {
            response_text = "nNDVI is a proxy index. In sample mode, we simulate it based on OSM tags and heuristics.";
        }

        return res.status(200).json({ text: response_text, actions: actions });
    } catch (error) {
        return res.status(500).json({ error: 'Failed to process request' });
    }
}
