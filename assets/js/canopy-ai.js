/*  canopy-ai.js  -  AI analysis, safe rendering, CSV export/import for Canopy
 *  Load once:  <script src="canopy-ai.js"></script>
 *  After your telemetry is fetched:  CanopyAI.run({ lat, lon, ndvi, temperature, sunlightHours, uvIndex, humidity, cropType, cropConfidence, areaHa })
 */
(function () {
    "use strict";
    const HISTORY_KEY = "canopy.history.v1";
    const COLS = ["timestamp", "lat", "lon", "cropType", "cropConfidence", "areaHa", "ndvi", "temperature", "humidity", "uvIndex", "sunlightHours",
        "healthScore", "status", "confidence", "summary", "risks", "recommendations", "nextChecks", "engine"];
    const cfg = { panel: null, allowLocalFallback: true, fetchTelemetry: null };
    let history = [];
    try { history = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"); } catch (_) { }
    const save = () => { try { localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(-500))); } catch (_) { } };

    /* ---- null-safe DOM helpers: fixes "Cannot set properties of null (setting 'textContent')" ---- */
    const $ = (s, r) => (r || document).querySelector(s);
    function setText(target, value) {
        const el = typeof target === "string" ? document.getElementById(target) || $(target) : target;
        if (!el) { console.warn("[Canopy] missing element:", target); return false; }
        el.textContent = value == null || value === "" ? "\u2014" : String(value);
        return true;
    }
    function h(tag, attrs, ...kids) {
        const e = document.createElement(tag);
        for (const [k, v] of Object.entries(attrs || {})) k === "class" ? (e.className = v) : e.setAttribute(k, v);
        kids.flat().forEach((c) => e.append(c && c.nodeType ? c : document.createTextNode(c == null ? "" : String(c))));
        return e;
    }

    /* ---- styles (matches the dark brown / green Canopy look) ---- */
    const css = `
  #canopy-ai-card{font:13px/1.5 ui-monospace,Menlo,Consolas,monospace;color:#e9e2d4;background:#1d1611;border:1px solid #3e5a2c;border-radius:6px;padding:16px;margin:16px 0}
  #canopy-ai-card.floating{position:fixed;left:16px;bottom:16px;width:min(420px,calc(100vw - 32px));max-height:70vh;overflow:auto;z-index:9999;box-shadow:0 8px 30px #000a}
  #canopy-ai-card h4{margin:0 0 8px;font:600 12px/1.2 system-ui,sans-serif;letter-spacing:.06em;color:#9fd07a}
  .cai-score{display:flex;gap:14px;align-items:center;margin-bottom:10px}
  .cai-ring{--p:0;width:64px;height:64px;border-radius:50%;display:grid;place-items:center;background:conic-gradient(var(--c,#7bbf4a) calc(var(--p)*1%),#3a2f26 0);flex:none}
  .cai-ring span{width:50px;height:50px;border-radius:50%;background:#1d1611;display:grid;place-items:center;font:700 18px system-ui}
  .cai-status{font:700 16px system-ui}.cai-meta{opacity:.65;font-size:11px}
  #canopy-ai-card ul{margin:4px 0 10px;padding-left:18px}#canopy-ai-card li{margin:2px 0}
  #canopy-ai-card h5{margin:10px 0 2px;font:600 11px system-ui;opacity:.75;letter-spacing:.05em}
  .cai-bar{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px;border-top:1px solid #3a2f26;padding-top:10px}
  .cai-bar button{font:12px ui-monospace,monospace;color:#e9e2d4;background:#2a2019;border:1px solid #5a4a3a;border-radius:4px;padding:6px 10px;cursor:pointer}
  .cai-bar button:hover,.cai-bar button:focus-visible{border-color:#9fd07a;outline:none}
  .cai-warn{color:#f0b35a}.cai-err{color:#f08a7a}
  .cai-load{opacity:.7;font-style:italic}
  @media (prefers-reduced-motion:no-preference){.cai-load{animation:caipulse 1.4s ease-in-out infinite}@keyframes caipulse{50%{opacity:.35}}}`;
    document.head.append(h("style", {}, css));

    /* ---- card ---- */
    function card() {
        let c = document.getElementById("canopy-ai-card");
        if (c) return c;
        c = h("section", { id: "canopy-ai-card", "aria-live": "polite" });
        const host = cfg.panel && $(cfg.panel);
        if (host) host.append(c); else { c.classList.add("floating"); document.body.append(c); }
        return c;
    }
    const scoreColor = (s) => (s >= 75 ? "#7bbf4a" : s >= 55 ? "#d8c14a" : s >= 35 ? "#e08e3c" : "#d95a4a");

    function toolbar() {
        const file = h("input", { type: "file", accept: ".csv,text/csv", hidden: "" });
        file.addEventListener("change", async () => { if (file.files[0]) await importCSV(file.files[0]); file.value = ""; });
        return h("div", { class: "cai-bar" },
            h("button", { type: "button", onclick: "" }, "Export all data (CSV)"),
            h("button", { type: "button" }, "Import parcels (CSV)"),
            h("button", { type: "button" }, "Download CSV template"),
            h("button", { type: "button" }, "Clear history"),
            file);
    }
    function wireToolbar(c) {
        const b = c.querySelectorAll(".cai-bar button");
        b[0].onclick = exportCSV;
        b[1].onclick = () => c.querySelector("input[type=file]").click();
        b[2].onclick = downloadTemplate;
        b[3].onclick = () => { if (confirm("Delete all saved parcel analyses on this device?")) { history = []; save(); note("History cleared."); } };
    }
    function note(msg, cls) {
        const c = card(); let n = c.querySelector(".cai-note");
        if (!n) { n = h("div", { class: "cai-note cai-meta" }); c.querySelector(".cai-bar")?.before(n) || c.append(n); }
        n.className = "cai-note cai-meta " + (cls || ""); n.textContent = msg;
    }

    function render(p, r, engine, model) {
        const c = card(); c.replaceChildren();
        const s = Math.max(0, Math.min(100, Math.round(+r.healthScore || 0)));
        const ring = h("div", { class: "cai-ring" }, h("span", {}, s));
        ring.style.setProperty("--p", s); ring.style.setProperty("--c", scoreColor(s));
        const list = (title, arr) => (arr && arr.length) ? [h("h5", {}, title), h("ul", {}, arr.map((x) => h("li", {}, x)))] : [];
        c.append(
            h("h4", {}, "CANOPY AI INSIGHT"),
            h("div", { class: "cai-score" }, ring, h("div", {},
                h("div", { class: "cai-status" }, r.status || "\u2014"),
                h("div", { class: "cai-meta" }, `Confidence: ${r.confidence || "\u2014"} \u00b7 ${engine === "gemini" ? "Gemini (" + model + ")" : "Rule-based (Gemini unavailable)"}`))),
            h("p", {}, r.summary || ""),
            ...list("RISKS", r.risks), ...list("RECOMMENDATIONS", r.recommendations), ...list("NEXT CHECKS", r.nextChecks),
            toolbar());
        wireToolbar(c);
        // if (engine !== "gemini") note("Gemini could not be reached; this report is computed from thresholds, not by the AI model.", "cai-warn");
    }

    /* ---- main entry ---- */
    async function run(parcel) {
        const p = Object.assign({ timestamp: new Date().toISOString() }, parcel);
        const c = card(); c.replaceChildren(h("h4", {}, "CANOPY AI INSIGHT"), h("div", { class: "cai-load" }, "Fetching real satellite data\u2026"));
        let report = {
            healthScore: null, status: "Pending", confidence: "Pending",
            summary: "Analyzing data streams...", risks: [], recommendations: [], nextChecks: []
        };
        let engine = "eo", model = "Planetary Computer", errMsg = "";

        try {
            const ctrl = new AbortController();
            const res = await fetch("/api/analyze", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify(p), signal: ctrl.signal
            });

            if (!res.ok) throw new Error("HTTP " + res.status);

            // NDJSON Stream Reader
            const reader = res.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";
            let evidence = {};

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop(); // keep remainder

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const chunk = JSON.parse(line);
                        // Progressive render logic based on chunk type
                        if (chunk.type === "info") {
                            report.summary = "Resolved polygon. Area: " + Math.round(chunk.payload?.area_m2 || 0) + " m²";
                        } else if (chunk.type === "land_cover") {
                            report.summary = `Confirmed Land Cover: ${Math.round((chunk.payload?.vegetated_fraction || 0) * 100)}% Vegetation`;
                            evidence.landCover = chunk.payload;
                        } else if (chunk.type === "ndvi") {
                            report.summary = "Extracted true Sentinel-2 NDVI...";
                            evidence.ndvi = chunk.payload;
                        } else if (chunk.type === "weather" || chunk.type === "modis") {
                            evidence[chunk.type] = chunk.payload;
                        } else if (chunk.type === "score") {
                            // Adopt the deterministic score
                            Object.assign(report, chunk.payload);
                            report.summary = "Formulating AI narrative...";
                        } else if (chunk.type === "error") {
                            throw new Error(chunk.error + (chunk.message ? ": " + chunk.message : ""));
                        }
                        // Render progress
                        render(p, report, engine, model);
                    } catch (err) {
                        console.warn("Stream parse error:", err);
                    }
                }
            }

            // After stream finishes, if we gathered evidence and didn't abort/fail, invoke Gemini
            if (report.healthScore !== null) {
                const gemRes = await fetch("/api/gemini", {
                    method: "POST", headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ ...p, evidence })
                });
                const gemData = await gemRes.json();
                if (gemData.ok && gemData.report) {
                    // Update ONLY the narrative fields
                    report.summary = gemData.report.summary || report.summary;
                    report.risks = gemData.report.risks || report.risks;
                    report.recommendations = gemData.report.recommendations || report.recommendations;
                    report.nextChecks = gemData.report.nextChecks || report.nextChecks;
                    model = gemData.model;
                    engine = "gemini + eo";
                }
            }
        } catch (e) {
            console.error("[CANOPY AI ERROR]", e); errMsg = e.message;
            report = {
                healthScore: null, status: "Data unavailable", confidence: "None",
                summary: `Data unavailable (reason: ${errMsg})`,
                risks: [], recommendations: [], nextChecks: []
            };
            engine = "failed";
        }

        const rec = Object.assign({}, p, report, { engine });
        history.push(rec); save();
        if (engine !== 'failed') render(p, report, engine, model);
        return rec;
    }

    /* ---- CSV ---- */
    const safe = (v) => {
        let s = Array.isArray(v) ? v.join(" | ") : v == null ? "" : String(v);
        if (/^[=+\-@\t\r]/.test(s)) s = "'" + s; // blocks spreadsheet formula injection
        return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    };
    const toCSV = (rows) => [COLS.join(",")].concat(rows.map((r) => COLS.map((k) => safe(r[k])).join(","))).join("\r\n");
    function download(name, text) {
        const a = h("a", { href: URL.createObjectURL(new Blob(["\ufeff" + text], { type: "text/csv;charset=utf-8" })), download: name });
        document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    }
    function exportCSV() {
        if (!history.length) return note("Nothing to export yet. Analyse a parcel first.", "cai-warn");
        download(`canopy-parcels-${new Date().toISOString().slice(0, 10)}.csv`, toCSV(history)); note(`Exported ${history.length} parcels.`);
    }
    function downloadTemplate() {
        download("canopy-import-template.csv", "lat,lon,cropType,ndvi,temperature,humidity,uvIndex,sunlightHours\r\n10.9049,76.8999,Coconut,0.72,26.4,74,8.1,10.1\r\n");
    }
    function parseCSV(text) {
        const rows = []; let row = [], cur = "", q = false;
        for (let i = 0; i < text.length; i++) {
            const ch = text[i];
            if (q) { if (ch === '"') { if (text[i + 1] === '"') { cur += '"'; i++; } else q = false; } else cur += ch; }
            else if (ch === '"') q = true;
            else if (ch === ",") { row.push(cur); cur = ""; }
            else if (ch === "\n" || ch === "\r") { if (ch === "\r" && text[i + 1] === "\n") i++; row.push(cur); cur = ""; if (row.some((x) => x.trim())) rows.push(row); row = []; }
            else cur += ch;
        }
        row.push(cur); if (row.some((x) => x.trim())) rows.push(row);
        return rows;
    }
    async function weather(lat, lon) {
        try {
            const u = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m&daily=uv_index_max,sunshine_duration&timezone=auto&forecast_days=1`;
            const d = await (await fetch(u)).json();
            return {
                temperature: d.current?.temperature_2m, humidity: d.current?.relative_humidity_2m,
                uvIndex: d.daily?.uv_index_max?.[0], sunlightHours: d.daily?.sunshine_duration?.[0] != null ? +(d.daily.sunshine_duration[0] / 3600).toFixed(1) : null
            };
        } catch (_) { return {}; }
    }
    async function importCSV(file) {
        const rows = parseCSV((await file.text()).replace(/^\ufeff/, ""));
        if (rows.length < 2) return note("CSV needs a header row and at least one data row.", "cai-err");
        const head = rows[0].map((x) => x.trim());
        const li = head.findIndex((x) => /^lat/i.test(x)), oi = head.findIndex((x) => /^(lon|lng)/i.test(x));
        if (li < 0 || oi < 0) return note("CSV must contain lat and lon columns. Use the template.", "cai-err");
        const data = rows.slice(1, 101); // cap at 100 parcels per import
        let done = 0;
        for (const r of data) {
            const p = {}; head.forEach((k, i) => { if (r[i] !== undefined && r[i].trim() !== "") p[k] = r[i].trim(); });
            p.lat = parseFloat(r[li]); p.lon = parseFloat(r[oi]);
            if (!isFinite(p.lat) || !isFinite(p.lon) || Math.abs(p.lat) > 90 || Math.abs(p.lon) > 180) continue;
            const extra = cfg.fetchTelemetry ? await cfg.fetchTelemetry(p.lat, p.lon) : (p.temperature ? {} : await weather(p.lat, p.lon));
            await run(Object.assign(extra || {}, p));
            note(`Imported ${++done}/${data.length}\u2026`);
        }
        note(`Import finished: ${done} parcels analysed. Use Export to download everything.`);
    }

    window.CanopyAI = { init(o) { Object.assign(cfg, o || {}); }, run, setText, exportCSV, importCSV, history: () => history.slice() };
})();
