import { z } from "zod";
import * as turf from "@turf/turf";

// ─────────────────────────────────────────────
// 1. Zod Validation Schemas
// ─────────────────────────────────────────────
const PolgonSchema = z.object({
    type: z.literal("Polygon"),
    coordinates: z.array(z.array(z.tuple([z.number(), z.number()]))).min(1),
});

const RequestSchema = z.object({
    polygon: PolgonSchema,
    language: z.string().optional().default("English"),
});

// ESA Worldcover 2021 Dictionary
const WORLDCOVER_CLASSES = {
    10: { name: "Tree cover", veg: true },
    20: { name: "Shrubland", veg: true },
    30: { name: "Grassland", veg: true },
    40: { name: "Cropland", veg: true },
    50: { name: "Built-up", veg: false },
    60: { name: "Bare/sparse vegetation", veg: false },
    70: { name: "Snow and ice", veg: false },
    80: { name: "Permanent water bodies", veg: false },
    90: { name: "Herbaceous wetland", veg: true },
    95: { name: "Mangroves", veg: true },
    100: { name: "Moss and lichen", veg: true },
};

// ─────────────────────────────────────────────
// 2. Base Interfaces & Modules
// ─────────────────────────────────────────────

/** Helper to wrap a source fetch with a timeout and uniform error formatting */
async function fetchSource(name, fetchFn, timeoutMs = 15000) {
    try {
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), timeoutMs);
        const result = await Promise.race([
            fetchFn(ctrl.signal),
            new Promise((_, r) => setTimeout(() => r(new Error(`Timeout after ${timeoutMs}ms`)), timeoutMs))
        ]);
        clearTimeout(t);
        return { name, status: "ok", data: result };
    } catch (err) {
        return { name, status: "unavailable", reason: err.message };
    }
}

// ─────────────────────────────────────────────
// Vercel Serverless Handler (Streaming NDJSON)
// ─────────────────────────────────────────────
export default async function handler(req, res) {
    res.setHeader("Access-Control-Allow-Origin", "*");
    if (req.method !== "POST") return res.status(405).json({ error: "POST only" });

    res.setHeader("Content-Type", "application/x-ndjson");
    res.setHeader("Cache-Control", "no-cache, no-transform");

    const writeChunk = (type, payload) => {
        res.write(JSON.stringify({ type, timestamp: new Date().toISOString(), payload }) + "\n");
    };

    try {
        // 1. Validation
        let body = typeof req.body === "string" ? JSON.parse(req.body) : req.body;

        // Support legacy "lat/lon" payloads by converting them into a tiny synthetic polygon if needed,
        // though the new UI should just send a real polygon GeoJSON.
        if (!body.polygon && body.lat && body.lon) {
            body.polygon = turf.buffer(turf.point([body.lon, body.lat]), 0.05, { units: 'kilometers' }).geometry;
        }

        const parsed = RequestSchema.safeParse(body);
        if (!parsed.success) {
            res.end(JSON.stringify({ type: "error", error: "Invalid payload", details: parsed.error.issues }));
            return;
        }

        const poly = turf.polygon(parsed.data.polygon.coordinates);
        const areaSqMeters = turf.area(poly);

        if (areaSqMeters > 500000) {
            res.end(JSON.stringify({ type: "error", error: "Polygon exceeds 50ha max area constraint." }));
            return;
        }

        writeChunk("info", {
            message: "Request validated successfully",
            area_m2: areaSqMeters,
            warnings: areaSqMeters < 100 ? ["Polygon < 100 m²; results will be highly mixed."] : []
        });

        // ─────────────────────────────────────────────
        // 2. Parallel Source Fetching Starts Here
        // ─────────────────────────────────────────────
        writeChunk("info", { message: "Initiating Earth Observation queries via Microsoft Planetary Computer STAC..." });

        const getSASToken = async (c) => {
            const res = await fetch(`https://planetarycomputer.microsoft.com/api/sas/v1/token/${c}`);
            return (await res.json()).token;
        };

        // Helper: fetch MS Planetary Computer STAC
        const searchSTAC = async (collection, bbox, maxCloud = 100) => {
            const body = { collections: [collection], bbox, limit: 1 };
            if (maxCloud < 100) body.query = { "eo:cloud_cover": { lt: maxCloud } };
            const res = await fetch("https://planetarycomputer.microsoft.com/api/stac/v1/search", {
                method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body)
            });
            if (!res.ok) throw new Error("STAC Search failed: " + res.status);
            const data = await res.json();
            return data.features || [];
        };

        const bbox = turf.bbox(poly);

        // -- Land Cover Gate (ESA WorldCover)
        const runLandCover = async () => {
            const features = await searchSTAC("esa-worldcover", bbox);
            if (!features.length) throw new Error("No WorldCover data found");
            const mapUrl = features[0].assets.map.href;

            let urlWithSAS = mapUrl;
            try { urlWithSAS += "?" + await getSASToken("esa-worldcover"); } catch (e) { /* fallback anonymous */ }

            // Fetch just the window covering our BBOX
            const { fromUrl } = await import("geotiff");
            const tiff = await fromUrl(urlWithSAS);
            const image = await tiff.getImage();
            // ESA Worldcover is unprojected Lat/Lon (EPSG:4326) which matches GeoJSON BBOX exactly.
            const rasters = await image.readRasters({ window: image.getBoundingBox(), bbox });

            const pixels = rasters[0];
            let counts = {};
            let total = 0; let vegCount = 0;

            for (let i = 0; i < pixels.length; i++) {
                const val = pixels[i];
                if (val === 0) continue; // NoData
                const clName = WORLDCOVER_CLASSES[val]?.name || "Unknown";
                counts[clName] = (counts[clName] || 0) + 1;
                if (WORLDCOVER_CLASSES[val]?.veg) vegCount++;
                total++;
            }

            if (total === 0) throw new Error("Polygon fell in NoData region");

            let fractions = {};
            for (const [k, v] of Object.entries(counts)) fractions[k] = Math.round((v / total) * 100) / 100;

            return {
                classes: fractions,
                vegetated_fraction: Math.round((vegCount / total) * 100) / 100,
                pixel_count: total,
                source: "ESA WorldCover (MPC)", date: "2021"
            };
        };

        const runNDVI = async () => {
            const features = await searchSTAC("sentinel-2-l2a", bbox, 20);
            if (!features.length) throw new Error("No usable Sentinel-2 scenes in window");
            const item = features[0];

            let token = "";
            try { token = "?" + await getSASToken("sentinel-2-l2a"); } catch (e) { }

            const { fromUrl } = await import("geotiff");

            const readAsset = async (assetKey) => {
                const h = item.assets[assetKey].href + token;
                const tiff = await fromUrl(h);
                const image = await tiff.getImage();

                // Transform bbox to image grid. For simplicity given we might not have full projection 
                // bounds, geotiff.js readRasters supports bounding boxes if we provide the image's coordinate window.
                // BoundingBox [minX, minY, maxX, maxY] is expected in the image's native CRS. 
                // Better: use boundingBox provided by the STAC item's proj extension.
                const stacBbox = item.bbox || item.properties['proj:bbox'];
                if (!stacBbox) return { data: (await image.readRasters())[0], width: image.getWidth() }; // fallback read whole (might be huge, usually 10k x 10k, but let's assume it works or we window later)

                // To ensure we don't blow up memory, rely on geotiff's internal windowing
                return { data: (await image.readRasters({ window: image.getBoundingBox(), bbox }))[0], width: image.getWidth() };
            };

            try {
                const [b4, b8, scl] = await Promise.all([
                    readAsset("B04"), readAsset("B08"), readAsset("SCL")
                ]);

                let ndviSum = 0; let validCount = 0; let totalMask = 0;
                const b4Vals = b4.data; const b8Vals = b8.data; const sclVals = scl.data;
                const len = Math.min(b4Vals.length, b8Vals.length, sclVals.length);

                // SCL Classes: 0: NoData, 1: Satur, 2: Dark, 3: CloudShadow, 4: Veg, 5: NotVeg, 6: Water, 7: Unclass, 8: CloudMed, 9: CloudHigh, 10: Cirrus, 11: Snow
                // Valid for NDVI: 4 (Veg), 5 (NotVeg), 6 (Water, mostly non veg but observable), 7, 1 (Satur, maybe), 2
                const invalidSCL = new Set([0, 1, 3, 8, 9, 10, 11]);

                for (let i = 0; i < len; i++) {
                    if (invalidSCL.has(sclVals[i])) continue; // Masked out
                    totalMask++;
                    const red = b4Vals[i]; const nir = b8Vals[i];
                    if (red === 0 && nir === 0) continue;
                    const ndvi = (nir - red) / (nir + red);
                    if (ndvi >= -1 && ndvi <= 1) {
                        ndviSum += ndvi;
                        validCount++;
                    }
                }

                if (validCount === 0) throw new Error("Entire polygon is obscured by clouds/shadows in standard SCL.");

                return {
                    ndvi: Math.round((ndviSum / validCount) * 1000) / 1000,
                    valid_pixels: validCount,
                    cloud_obfuscation_pct: Math.round((1 - (totalMask / len)) * 100),
                    source: "Sentinel-2 L2A (MPC)", date: item.properties.datetime
                };
            } catch (e) {
                return { status: "unavailable", reason: "GeoTIFF processing failed: " + e.message };
            }
        };

        // -- Phase 4: MODIS Anomaly (ORNL DAAC)
        const runMODIS = async () => {
            const center = turf.center(poly).geometry.coordinates;
            const [lon, lat] = center;
            const url = `https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset?latitude=${lat}&longitude=${lon}&band=250m_16_days_NDVI&startDate=A2015001&endDate=A2024001&kmAboveBelow=0&kmLeftRight=0`;
            const res = await fetch(url);
            if (!res.ok) throw new Error("MODIS DAAC Error: " + res.status);
            const data = await res.json();
            const vals = data.subset[0].data.filter(v => v > -2000).map(v => v * data.scale);
            if (!vals.length) throw new Error("No valid MODIS history");

            const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
            const std = Math.sqrt(vals.map(x => Math.pow(x - mean, 2)).reduce((a, b) => a + b) / vals.length) || 0.05;

            return {
                historical_mean_ndvi: Math.round(mean * 1000) / 1000,
                std,
                z_score: null, // to be calculated if S2 is present
                source: "NASA MODIS MOD13Q1 (ORNL DAAC)", date: "2015-2023"
            };
        };

        // -- Phase 5: Weather & Soil (Open-Meteo)
        const runWeather = async () => {
            const [lon, lat] = turf.center(poly).geometry.coordinates;
            const params = "temperature_2m,relative_humidity_2m,soil_moisture_0_to_7cm,et0_fao_evapotranspiration,precipitation";
            const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=${params}&past_days=30`;
            const res = await fetch(url);
            if (!res.ok) throw new Error("Open-Meteo Error: " + res.status);
            const w = await res.json();

            const pastPrecip = w.hourly?.precipitation?.reduce((a, b) => a + (b || 0), 0) || 0;
            const pastET0 = w.hourly?.et0_fao_evapotranspiration?.reduce((a, b) => a + (b || 0), 0) || 1;
            const precipDeficit = pastPrecip - pastET0;

            return {
                temperature: w.current.temperature_2m,
                soil_moisture: w.current.soil_moisture_0_to_7cm,
                precip_deficit_30d: Math.round(precipDeficit * 10) / 10,
                source: "Open-Meteo (ERA5-Land / DWD)", date: w.current.time
            };
        };

        const results = await Promise.allSettled([
            fetchSource("land_cover", runLandCover, 15000),
            fetchSource("ndvi", runNDVI, 15000),
            fetchSource("modis", runMODIS, 10000),
            fetchSource("weather", runWeather, 10000)
        ]);

        const landCover = results[0].value;
        const ndvi = results[1].value;
        const modis = results[2].value;
        const weather = results[3].value;

        writeChunk("land_cover", landCover);
        writeChunk("ndvi", ndvi);
        writeChunk("modis", modis);
        writeChunk("weather", weather);

        // Gate: Abort if < 30% vegetation, UNLESS live NDVI verifies it is actually green (e.g. overriding misclassified water bodies)
        if (landCover.status === "ok" && landCover.data.vegetated_fraction < 0.3) {
            if (ndvi.status === "ok" && ndvi.data.ndvi > 0.2) {
                writeChunk("info", { message: "WorldCover indicates non-vegetation, but live NDVI reveals green canopy. Proceeding." });
            } else {
                writeChunk("info", { message: "Vegetated fraction extremely low and no green NDVI detected. Terminating agricultural metrics pipeline." });
                res.end();
                return;
            }
        }

        // ─────────────────────────────────────────────
        // 3. Phase 6: Deterministic Score Engine
        // ─────────────────────────────────────────────
        let baseScore = 50;
        let risks = [];
        let componentsUsed = [];

        // Determine S2 NDVI relative anomaly if both exist
        let s2_anomaly_pct = null;
        if (ndvi.status === "ok" && modis.status === "ok") {
            const z = (ndvi.data.ndvi - modis.data.historical_mean_ndvi) / modis.data.std;
            modis.data.z_score = Math.round(z * 100) / 100;
            s2_anomaly_pct = (ndvi.data.ndvi / modis.data.historical_mean_ndvi) * 100;
            writeChunk("modis", modis); // rewrite with z_score

            // Score primarily controlled by anomaly if present
            baseScore = Math.max(10, Math.min(100, s2_anomaly_pct > 120 ? 95 : s2_anomaly_pct < 80 ? 30 : 60 + (z * 15)));
            componentsUsed.push("Sentinel-MODIS Anomaly");
            if (z < -1.5) risks.push(`Critical vegetation deficit: NDVI is ${Math.round(z * 10) / 10} standard deviations below historical norm.`);
        } else if (ndvi.status === "ok") {
            baseScore = Math.round(ndvi.data.ndvi * 100);
            componentsUsed.push("Raw Sentinel-2 NDVI");
        }

        if (weather.status === "ok") {
            const w = weather.data;
            if (w.soil_moisture < 0.15) { baseScore -= 10; risks.push(`Low root-zone moisture (${w.soil_moisture} m³/m³).`); }
            if (w.precip_deficit_30d < -50) { baseScore -= 5; risks.push(`Severe 30-day precipitation deficit vs ET0 (${w.precip_deficit_30d} mm).`); }
            if (w.temperature > 35) { baseScore -= 8; risks.push(`High heat stress detected (${w.temperature}°C).`); }
            componentsUsed.push("Weather/Soil Sensors");
        }

        if (risks.length === 0) risks.push("No elevated risks detected from measurement data.");

        baseScore = Math.max(0, Math.min(100, Math.round(baseScore)));

        let confidence = (ndvi.status === "ok" && weather.status === "ok") ? "High" : "Medium";
        if (ndvi.status !== "ok") confidence = "Low";

        writeChunk("score", {
            healthScore: baseScore,
            status: baseScore > 75 ? "Healthy" : baseScore > 50 ? "Stable" : baseScore > 30 ? "Marginal" : "Critical",
            confidence,
            range: `±${confidence === "High" ? 5 : 15}`,
            risks,
            components_used: componentsUsed
        });

        // ─────────────────────────────────────────────
        // 4. Finalize Stream
        // ─────────────────────────────────────────────
        writeChunk("complete", { status: "Done" });
        res.end();

    } catch (err) {
        writeChunk("error", { error: "Internal Server Error", message: err.message });
        res.end();
    }
}
