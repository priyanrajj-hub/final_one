export default async function handler(req, res) {
    const { x, y, z } = req.query;
    if (!x || !y || !z) return res.status(400).json({ error: "Missing xyz params" });

    try {
        const url = `https://mt1.google.com/vt/lyrs=s&x=${x}&y=${y}&z=${z}`;
        const response = await fetch(url);
        if (!response.ok) {
            return res.status(response.status).json({ error: "Upstream Google Maps error" });
        }

        const arrayBuffer = await response.arrayBuffer();

        res.setHeader("Content-Type", "image/jpeg");
        res.setHeader("Access-Control-Allow-Origin", "*");
        res.setHeader("Cache-Control", "public, s-maxage=86400"); // cache heavily

        // Return raw jpeg buffer
        return res.status(200).send(Buffer.from(arrayBuffer));
    } catch (err) {
        console.error("Proxy Tile Error:", err);
        return res.status(500).json({ error: "Failed to proxy tile" });
    }
}
