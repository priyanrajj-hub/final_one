const { Pool } = require('@neondatabase/serverless');

// Vercel serverless environment pooled connection string
const pool = new Pool({ connectionString: process.env.DATABASE_URL });

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    try {
        const payload = req.body;
        const {
            polygon_geojson,
            centroid_lat,
            centroid_lon,
            area_hectares,
            ndvi,
            ndvi_source,
            weather
        } = payload;

        if (!polygon_geojson || centroid_lat === undefined || centroid_lon === undefined) {
            return res.status(400).json({ error: "Missing required spatial polygon telemetry." });
        }

        // Connect to neon proxy pool
        const client = await pool.connect();

        try {
            // Geographic Place Matcher (~30m radius approximation in decimal degrees without PostGIS)
            // 30 meters is roughly 0.00027 degrees.
            const distanceThreshold = 0.00027;

            // Search for existing place
            let placeResult = await client.query(`
                SELECT place_id FROM places 
                WHERE SQRT(POWER(centroid_lat - $1, 2) + POWER(centroid_lon - $2, 2)) < $3
                LIMIT 1
            `, [centroid_lat, centroid_lon, distanceThreshold]);

            let place_id;
            let isNewPlace = false;
            let currentVisitCount = 0;

            if (placeResult.rows.length > 0) {
                place_id = placeResult.rows[0].place_id;

                const updateRes = await client.query(`
                    UPDATE places 
                    SET visit_count = visit_count + 1, last_visit_utc = now() 
                    WHERE place_id = $1 
                    RETURNING visit_count
                `, [place_id]);
                currentVisitCount = updateRes.rows[0].visit_count;
            } else {
                isNewPlace = true;
                const crypto = require('crypto');
                place_id = crypto.randomUUID();

                await client.query(`
                    INSERT INTO places (place_id, centroid_lat, centroid_lon, polygon_geojson, area_hectares, visit_count)
                    VALUES ($1, $2, $3, $4, $5, 1)
                `, [place_id, centroid_lat, centroid_lon, JSON.stringify(polygon_geojson), area_hectares || 0]);
                currentVisitCount = 1;
            }

            // Insert Visit
            const visitResult = await client.query(`
                INSERT INTO visits (place_id, visit_number_for_place, local_date, local_time)
                VALUES ($1, $2, CURRENT_DATE, CURRENT_TIME)
                RETURNING visit_id
            `, [place_id, currentVisitCount]);

            const visit_id = visitResult.rows[0].visit_id;

            // Generate strict schema fallback provenance map
            const provenance = {
                ndvi: ndvi_source || 'unavailable',
                weather: weather ? (weather.source || 'unavailable') : 'unavailable',
                hardware: 'not_connected'
            };

            // Insert matching Observations structure (ensuring strictly truthy physical tracking)
            await client.query(`
                INSERT INTO observations (
                    visit_id, place_id, 
                    ndvi, ndvi_source, 
                    temperature_c, humidity_pct, 
                    weather_source, sensor_source, provenance
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            `, [
                visit_id,
                place_id,
                ndvi || null,
                ndvi_source || 'unavailable',
                weather?.temperature_c || null,
                weather?.humidity_pct || null,
                weather?.source || 'unavailable',
                'not_connected',
                JSON.stringify(provenance)
            ]);

            return res.status(200).json({
                success: true,
                place_id,
                visit_id,
                visit_count: currentVisitCount,
                message: `Visit #${currentVisitCount} logged successfully to Neon telemetry.`
            });

        } finally {
            // MUST release pooled connection securely in serverless edges
            client.release();
        }

    } catch (err) {
        console.error("Neon DB Logging Fatal Error:", err);
        return res.status(500).json({ error: "Failed to allocate SQL visit logging: " + err.message });
    }
}
