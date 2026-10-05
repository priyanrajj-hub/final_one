export default async function handler(req, res) {
    const { x, y, z } = req.query;
    if (!x || !y || !z) return res.status(400).json({ error: "Missing xyz params" });

    // Use environment variable fallback prioritizing the newly provided Planet Key
    const PLANET_KEY = process.env.PLANET_API_KEY || "PLAK755889448c664e4698de15b8272505a6";

    // We bind to one of Planet's standard global monthly visual mosaics
    const mosaicName = "global_monthly_2023_01_mosaic";
    const url = `https://tiles.planet.com/basemaps/v1/planet-tiles/${mosaicName}/gmap/${z}/${x}/${y}.png?api_key=${PLANET_KEY}`;

    try {
        const response = await fetch(url);

        // If Planet denies the request due to unprovisioned API keys or region locks,
        // we can gracefully let the frontend fall back (e.g. standard 404 transparent tile).
        if (!response.ok) {
            return res.status(response.status).json({ error: "Upstream Planet Labs error", details: response.statusText });
        }

        const arrayBuffer = await response.arrayBuffer();

        res.setHeader("Content-Type", "image/png");
        res.setHeader("Access-Control-Allow-Origin", "*");
        res.setHeader("Cache-Control", "public, s-maxage=86400"); // Cache heavily to save API quota

        // Return raw png buffer
        return res.status(200).send(Buffer.from(arrayBuffer));
    } catch (err) {
        console.error("Planet Proxy Error:", err);
        return res.status(500).json({ error: "Failed to proxy Planet tile" });
    }
}
