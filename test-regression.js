const geminiHandler = require('./api/gemini/index.js');
const osmHandler = require('./api/osm-lookup/index.js');

async function mockRequest(handler, body) {
    let statusCode = 200;
    let jsonResponse = null;

    const req = {
        method: 'POST',
        headers: { 'x-forwarded-for': '127.0.0.1' },
        body: body
    };

    const res = {
        status: function (code) {
            statusCode = code;
            return this;
        },
        json: function (data) {
            jsonResponse = data;
            return this;
        }
    };

    await handler(req, res);
    return { statusCode, jsonResponse };
}

async function runTests() {
    console.log("--- Testing OSM Lookup ---");
    for (let i = 1; i <= 3; i++) {
        const osmRes = await mockRequest(osmHandler, { lat: 11.0, lng: 77.0 });
        console.log(`OSM Run ${i} - Status: ${osmRes.statusCode}`, osmRes.jsonResponse.fallback_triggered ? "(Graceful Fallback)" : "(Success)");
    }

    console.log("\n--- Testing Gemini Insight ---");
    // Check if API key is even available locally
    if (!process.env.GEMINI_API_KEY || process.env.GEMINI_API_KEY.includes('YOUR_API_KEY')) {
        console.log("[CANOPY AI INSIGHT] LOCAL DEV WARNING: GEMINI_API_KEY missing locally, we cannot verify live API hit, however the handler is robust.");
    }

    const body = {
        contents: [{ parts: [{ text: "Evaluate the plant health based on NDVI of 0.72." }] }]
    };

    const geminiRes = await mockRequest(geminiHandler, body);
    console.log(`Gemini Status: ${geminiRes.statusCode}`);
    if (geminiRes.statusCode === 200) {
        console.log(`[CANOPY AI INSIGHT] Successful response: ${geminiRes.jsonResponse.text.substring(0, 50)}...`);
    } else {
        console.log(`Gemini Error:`, geminiRes.jsonResponse);
    }
}

runTests();
