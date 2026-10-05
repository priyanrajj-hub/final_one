const { Pool } = require('@neondatabase/serverless');

const pool = new Pool({ connectionString: process.env.DATABASE_URL });

export default async function handler(req, res) {
    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    try {
        const { place_id, start_date, end_date } = req.query;

        const client = await pool.connect();

        try {
            // Build dynamic filters
            let conditionStr = "1=1";
            let params = [];
            let paramIdx = 1;

            if (place_id) {
                conditionStr += ` AND v.place_id = $${paramIdx}`;
                params.push(place_id);
                paramIdx++;
            }
            if (start_date) {
                conditionStr += ` AND v.local_date >= $${paramIdx}`;
                params.push(start_date);
                paramIdx++;
            }
            if (end_date) {
                conditionStr += ` AND v.local_date <= $${paramIdx}`;
                params.push(end_date);
                paramIdx++;
            }

            // Stream visits joined with observations and labels
            const query = `
                SELECT 
                    v.visit_id, v.place_id, v.local_date, v.local_time, v.visit_number_for_place,
                    o.ndvi, o.temperature_c, o.humidity_pct, o.capacitive_pf, o.acoustic_val,
                    l.label_type, l.label_value
                FROM visits v
                LEFT JOIN observations o ON v.visit_id = o.visit_id
                LEFT JOIN labels l ON v.visit_id = l.visit_id
                WHERE ${conditionStr}
                ORDER BY v.visit_timestamp_utc ASC
            `;

            const dbResult = await client.query(query, params);
            const rows = dbResult.rows;

            if (rows.length === 0) {
                return res.status(404).send("No visits found for the specified filters.");
            }

            // Extract CSV headers natively
            const headers = Object.keys(rows[0]);

            // Map JSON responses into raw CSV arrays
            const csvText = [
                headers.join(','),
                ...rows.map(row => headers.map(fieldName => {
                    let val = row[fieldName];
                    if (val === null || val === undefined) return '';
                    if (typeof val === 'string' && val.includes(',')) return `"${val}"`;
                    return val;
                }).join(','))
            ].join('\n');

            res.setHeader('Content-Type', 'text/csv');
            res.setHeader('Content-Disposition', 'attachment; filename="canopy_telemetry_export.csv"');
            return res.status(200).send(csvText);

        } finally {
            client.release();
        }

    } catch (err) {
        console.error("Neon DB Export Error:", err);
        return res.status(500).json({ error: "Failed to allocate SQL export pipeline: " + err.message });
    }
}
