const { Client } = require('pg');

module.exports = async (req, res) => {
    // Standard Node.js Vercel Function
    const geminiKey = process.env.GEMINI_API_KEY;
    const sentinelKey = process.env.SENTINEL_HUB_SECRET;
    const databaseUrl = process.env.DATABASE_URL;

    let dbConfigured = !!databaseUrl;
    let dbStatus = dbConfigured ? "healthy" : "missing_credentials";

    if (dbConfigured) {
        const client = new Client({
            connectionString: databaseUrl,
            ssl: { rejectUnauthorized: false } // Required for most managed DBs
        });
        try {
            await client.connect();
            await client.query('SELECT 1');
            await client.end();
            dbStatus = "healthy";
        } catch (error) {
            console.error("Database health check failed:", error);
            dbStatus = "connection_error";
        }
    }

    res.status(200).json({
        status: 'online',
        timestamp: new Date().toISOString(),
        integrations: {
            gemini_api: {
                configured: !!geminiKey,
                status: geminiKey ? "healthy" : "missing_credentials"
            },
            sentinel_api: {
                configured: !!sentinelKey,
                status: sentinelKey ? "healthy" : "missing_credentials"
            },
            database: {
                configured: dbConfigured,
                status: dbStatus
            }
        }
    });
};
