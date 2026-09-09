module.exports = async function (req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    try {
        const { lat, lng } = req.body;

        if (!lat || !lng) {
            return res.status(400).json({ error: 'Missing coordinates (lat, lng)' });
        }

        const bbox = `${lat - 0.005},${lng - 0.005},${lat + 0.005},${lng + 0.005}`;
        const queryData = `[out:json];(node(${bbox})["landuse"];way(${bbox})["landuse"];node(${bbox})["crop"];way(${bbox})["crop"];node(${bbox})["produce"];way(${bbox})["produce"];);out;`;
        const overpassQuery = `https://overpass-api.de/api/interpreter?data=${encodeURIComponent(queryData)}`;

        const fetchWithRetry = async (url, options, retries = 1, timeoutMs = 8000) => {
            for (let i = 0; i <= retries; i++) {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
                try {
                    const response = await fetch(url, { ...options, signal: controller.signal });
                    clearTimeout(timeoutId);
                    if (!response.ok) throw new Error(`Overpass API responded with status: ${response.status}`);
                    return await response.json();
                } catch (err) {
                    clearTimeout(timeoutId);
                    if (i === retries) throw err;
                    console.warn(`[OSM Lookup] Attempt ${i + 1} failed, retrying...`, err.message);
                }
            }
        };

        const data = await fetchWithRetry(overpassQuery, {
            headers: {
                'User-Agent': 'SmartPlantHealthMonitoring/1.0 (Research Hackathon SIH26180)'
            }
        });

        return res.status(200).json(data);
    } catch (err) {
        console.error("OSM Lookup Proxy Error:", err);
        // Clean fallback response instead of 502 per Fix 3
        return res.status(200).json({ elements: [], fallback_triggered: true });
    }
};
