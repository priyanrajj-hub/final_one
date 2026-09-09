module.exports = async (req, res) => {
    try {
        const apiKey = process.env.GEMINI_API_KEY;

        if (!apiKey || apiKey === '' || (typeof apiKey === 'string' && apiKey.includes('YOUR_API_KEY'))) {
            return res.status(403).json({ error: "Missing/Invalid API Key in Vercel environment." });
        }

        const apiUrl = `https://generativelanguage.googleapis.com/v1/models?key=${apiKey}`;

        const rawResponse = await fetch(apiUrl);
        const rawText = await rawResponse.text();

        if (!rawResponse.ok) {
            return res.status(rawResponse.status).json({
                error: `HTTP Error ${rawResponse.status} while fetching ListModels`,
                details: rawText
            });
        }

        const jsonResponse = JSON.parse(rawText);

        // Filter for models supporting generateContent
        const validModels = (jsonResponse.models || []).filter(m =>
            m.supportedGenerationMethods && m.supportedGenerationMethods.includes('generateContent')
        );

        return res.status(200).json({
            allModelsCount: (jsonResponse.models || []).length,
            validModelsCount: validModels.length,
            validModels: validModels.map(m => m.name),
            rawModelList: jsonResponse.models
        });

    } catch (e) {
        return res.status(500).json({ error: "Proxy Exception: " + e.message });
    }
};
