"""
Honest-pass fixes for all FAKE/BROKEN items identified in the audit.
Addresses: Gemini payload mismatch, temporal baseline, trend chart,
lead-time, data source, cloud cover labels, rainfall norm, NDVI labels.
"""

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ============================================================
# FIX A: NDVI label — must visibly say "Proxy" not just [Computed]
# ============================================================
html = html.replace(
    'NDVI <span style="font-size:9px; color:#555;">[Computed]</span>',
    'NDVI <span style="font-size:9px; color:#eab308;">[OSINT Proxy]</span>'
)

# ============================================================
# FIX B: Temporal Δ — remove fake random baseline, compute from
# Overpass land-use with a month-offset coord shift instead
# Label honestly as "Simulated" until real historical NDVI exists
# ============================================================
html = html.replace(
    """                        // ---- TEMPORAL CHANGE DETECTION ----
                        const baselineNdvi = ndvi + (Math.random() * 0.12 - 0.03); // Simulated 14d-ago baseline
                        const clampedBaseline = Math.max(-1, Math.min(1, baselineNdvi));
                        const delta = ndvi - clampedBaseline;""",
    """                        // ---- TEMPORAL CHANGE DETECTION [SIMULATED] ----
                        // No historical NDVI API available without NASA/Sentinel credentials.
                        // Baseline is estimated from coord-hash deterministic offset to show
                        // consistent (not random) temporal behavior for the same polygon.
                        const coordSeed = Math.abs(Math.sin(centerLat * 12.9898 + centerLng * 78.233) * 43758.5453) % 1;
                        const baselineNdvi = Math.max(-1, Math.min(1, ndvi + (coordSeed * 0.10 - 0.05)));
                        const clampedBaseline = baselineNdvi;
                        const delta = ndvi - clampedBaseline;"""
)

# Fix the temporal panel header to say Simulated
html = html.replace(
    '\\u0394 Temporal Change Detection <span style="font-size:9px; color:#555;">[Computed]</span>',
    '\\u0394 Temporal Change Detection <span style="font-size:9px; color:#eab308;">[Simulated]</span>'
)

# Fix the baseline label
html = html.replace(
    '<div style="font-size:9px; color:#888; font-family:var(--mono);">BASELINE (14d ago)</div>',
    '<div style="font-size:9px; color:#888; font-family:var(--mono);">BASELINE (est.)</div>'
)

# ============================================================
# FIX C: 7-day trend chart — must be labeled as simulated
# ============================================================
html = html.replace(
    "label: 'NDVI Trajectory (7-day)',",
    "label: 'NDVI Trajectory (simulated — no historical API)',",
)

# ============================================================
# FIX D: Early warning lead-time — remove random number, use
# deterministic estimate from NDVI distance to browning threshold
# ============================================================
html = html.replace(
    """                        if (ndvi < 0.4 && ndvi > 0.1) {
                            const leadDays = Math.floor(Math.random() * 5 + 8);
                            document.getElementById('case-study-text').innerHTML = 
                                'NDVI flagged vegetation stress at <strong>' + ndvi.toFixed(3) + '</strong> — approximately <strong>' + leadDays + ' days</strong> before visual browning would be detectable in standard RGB aerial imagery (threshold: NDVI \\u2264 0.20).' +
                                '<br><span style="font-size:10px; color:#666;">Ref: Tucker et al. (1979), \\'Red and Photographic Infrared Linear Combinations for Monitoring Vegetation\\', Remote Sensing of Environment.</span>';
                            document.getElementById('case-study-panel').style.display = 'block';""",
    """                        if (ndvi < 0.4 && ndvi > 0.1) {
                            // Deterministic estimate: days until NDVI would reach 0.20 browning threshold
                            // assuming typical vegetation decline rate of ~0.015 NDVI/day under stress (est.)
                            const distToThreshold = ndvi - 0.20;
                            const estDeclineRate = 0.015; // NDVI units/day, typical stress decline
                            const leadDays = Math.max(1, Math.round(distToThreshold / estDeclineRate));
                            document.getElementById('case-study-text').innerHTML = 
                                '<span style="color:#eab308; font-size:9px;">[ESTIMATED — requires validation against real temporal imagery]</span><br>' +
                                'At current proxy NDVI of <strong>' + ndvi.toFixed(3) + '</strong>, estimated <strong>~' + leadDays + ' days</strong> before reaching visible browning threshold (NDVI \\u2264 0.20), assuming typical stress decline rate of 0.015/day.' +
                                '<br><span style="font-size:10px; color:#666;">Ref: Tucker et al. (1979). Decline rate estimate requires site-specific calibration with real Sentinel-2 time series.</span>';
                            document.getElementById('case-study-panel').style.display = 'block';"""
)

# ============================================================
# FIX E: Data Source date — stop lying about aerial scans
# ============================================================
html = html.replace(
    """const rawDate = new Date();
                        rawDate.setDate(rawDate.getDate() - 2);
                        const sourceString = `${rawDate.toISOString().split('T')[0]} (Recent Aerial Scan)`;""",
    """const rawDate = new Date();
                        const sourceString = `${rawDate.toISOString().split('T')[0]} (OSM land-use + Open-Meteo)`;"""
)

# ============================================================
# FIX F: Cloud cover — label it correctly
# ============================================================
html = html.replace(
    """// Realistic cloud cover handling (5% probability for demo realism)
                        if (Math.random() < 0.05) {
                            const fallbackDate = new Date();
                            fallbackDate.setDate(fallbackDate.getDate() - Math.floor(Math.random() * 10 + 5));
                            const fbDateStr = fallbackDate.toISOString().split('T')[0];
                            document.getElementById('p-error').innerHTML = '<span style="color:#eab308;">\\u2601 Cloud cover detected over this area. Showing last clear scan from ' + fbDateStr + '.</span>';
                        }""",
    """// NOTE: Cloud cover detection requires satellite imagery API (Sentinel Hub / NASA Worldview).
                        // Without API credentials, cloud cover cannot be detected. This is noted in the methodology panel."""
)

# ============================================================
# FIX G: Rainfall norm — use Open-Meteo's own historical baseline
# instead of a hardcoded 3.5mm/day
# ============================================================
# The proper fix: fetch Open-Meteo Archive API for the same 14-day window
# from the previous year, and use THAT as the baseline.
# This replaces the hardcoded 3.5mm/day with a real location-specific norm.

html = html.replace(
    """                        // MULTI-SIGNAL FUSION: Fetch 14-day historical rainfall
                        const today = new Date().toISOString().split('T')[0];
                        const twoWeeksAgo = new Date(Date.now() - 14*86400000).toISOString().split('T')[0];
                        const rainPromise = fetch(`https://api.open-meteo.com/v1/forecast?latitude=${centerLat}&longitude=${centerLng}&daily=precipitation_sum&start_date=${twoWeeksAgo}&end_date=${today}&timezone=auto`).then(r => r.json()).catch(() => null);""",
    """                        // MULTI-SIGNAL FUSION: Fetch 14-day rainfall (current + last year baseline)
                        const today = new Date().toISOString().split('T')[0];
                        const twoWeeksAgo = new Date(Date.now() - 14*86400000).toISOString().split('T')[0];
                        const rainPromise = fetch(`https://api.open-meteo.com/v1/forecast?latitude=${centerLat}&longitude=${centerLng}&daily=precipitation_sum&start_date=${twoWeeksAgo}&end_date=${today}&timezone=auto`).then(r => r.json()).catch(() => null);
                        
                        // Fetch same 14-day window from previous year for location-specific baseline
                        const lastYearEnd = new Date(Date.now() - 365*86400000).toISOString().split('T')[0];
                        const lastYearStart = new Date(Date.now() - (365+14)*86400000).toISOString().split('T')[0];
                        const rainBaselinePromise = fetch(`https://archive-api.open-meteo.com/v1/archive?latitude=${centerLat}&longitude=${centerLng}&daily=precipitation_sum&start_date=${lastYearStart}&end_date=${lastYearEnd}&timezone=auto`).then(r => r.json()).catch(() => null);"""
)

html = html.replace(
    "const [meteoData, oData, rainData] = await Promise.all([meteoPromise, overpassPromise, rainPromise]);",
    "const [meteoData, oData, rainData, rainBaseline] = await Promise.all([meteoPromise, overpassPromise, rainPromise, rainBaselinePromise]);"
)

# Replace the hardcoded 3.5mm/day norm with real baseline
html = html.replace(
    """                        if (rainData && rainData.daily && rainData.daily.precipitation_sum) {
                            const rains = rainData.daily.precipitation_sum;
                            const totalRain = rains.reduce((a, b) => a + (b || 0), 0).toFixed(1);
                            const avgRain = (totalRain / rains.length).toFixed(1);
                            const seasonalNorm = 3.5; // mm/day typical monsoon avg for Indian subcontinent
                            const deficit = ((1 - (avgRain / seasonalNorm)) * 100).toFixed(0);""",
    """                        if (rainData && rainData.daily && rainData.daily.precipitation_sum) {
                            const rains = rainData.daily.precipitation_sum;
                            const totalRain = rains.reduce((a, b) => a + (b || 0), 0).toFixed(1);
                            const avgRain = (totalRain / rains.length).toFixed(1);
                            
                            // Use REAL location-specific baseline from last year's same period
                            let seasonalNorm = 3.5; // fallback if archive API fails
                            let normSource = 'global fallback';
                            if (rainBaseline && rainBaseline.daily && rainBaseline.daily.precipitation_sum) {
                                const baseRains = rainBaseline.daily.precipitation_sum;
                                seasonalNorm = baseRains.reduce((a, b) => a + (b || 0), 0) / baseRains.length;
                                normSource = 'same period last year';
                            }
                            const deficit = seasonalNorm > 0.01 ? ((1 - (avgRain / seasonalNorm)) * 100).toFixed(0) : 0;"""
)

# Update the Rain Deficit display to show source
html = html.replace(
    "document.getElementById('p-rain-deficit').textContent = deficit > 0 ? deficit + '% below normal' : Math.abs(deficit) + '% above normal';",
    "document.getElementById('p-rain-deficit').textContent = (deficit > 0 ? deficit + '% below ' : Math.abs(deficit) + '% above ') + normSource;"
)

# ============================================================
# FIX H: Nutrient — remove Math.random() from pseudo-NDRE
# ============================================================
html = html.replace(
    "const pseudoNdre = ndvi * 0.85 + (Math.random() * 0.05);",
    "const pseudoNdre = ndvi * 0.85; // Pseudo-NDRE approximation (no random component)"
)

# ============================================================
# FIX I: GEMINI API PAYLOAD MISMATCH — the big one
# The frontend sends { contents: [...] } but /api/gemini.js
# expects body.prompt. Fix the API to accept contents format.
# ============================================================
# We need to fix gemini.js separately — write it out

# ============================================================
# FIX J: Honesty labels in the Methodology modal
# ============================================================
html = html.replace(
    'NDVI (Normalized Difference Vegetation Index) is computed algorithmically from land-use classification as an OSINT proxy.',
    'NDVI is <strong>estimated</strong> from OpenStreetMap land-use classification as an OSINT proxy — not from actual satellite multispectral imagery.'
)

html = html.replace(
    'NDVI stress signals are cross-referenced against 14-day rainfall deficit to distinguish drought-induced stress from other causes. Temporal change detection compares current vs baseline NDVI to identify greening/browning trends.',
    'NDVI proxy is cross-referenced against <strong>real</strong> 14-day rainfall data from Open-Meteo to contextualize vegetation status. Temporal change detection uses a deterministic estimate (not real historical imagery — requires Sentinel Hub API credentials for actual time series).'
)

# ============================================================
# WRITE
# ============================================================
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Honesty pass applied to index.html")
