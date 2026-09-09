import re

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update the Gemini Payload Prompt
old_payload = '''const geminiPayload = {
                            "contents": [{ "parts": [{ "text": `You are the Canopy AI Agricultural Analyst. I just scanned a farm polygon using OSINT proxies. The Mean NDVI is ${ndvi.toFixed(3)}. Provide a professional vegetation diagnosis. You MUST strictly use explicit hedging language (like 'estimated', 'likely', or 'based on vegetation patterns') when guessing pest risks or general NPK soil health, to ensure they are visually distinguished as AI estimates and not physical sensor measurements. Write exactly 2-3 concise plain-text sentences. DO NOT use markdown, HTML tags, or formatting characters.` }] }]
                        };'''

new_payload = '''const geminiPayload = {
                            "contents": [{ "parts": [{ "text": `You are the Canopy AI Agricultural Analyst. I just scanned a farm polygon using OSINT proxies. The Mean NDVI is ${ndvi.toFixed(3)}. Return your analysis STRICTLY as a JSON object with the following exact keys, and DO NOT wrap it in markdown code blocks: {"summary": "one sentence overview", "stress_severity": "Low | Moderate | High | Critical", "likely_crop_disease_or_pest_risk": "short estimated risk description", "npk_soil_health_estimate": "short estimated description", "confidence_caveat": "AI-estimated reasoning based on telemetry, not direct physical sensor measurement."}. You MUST use explicit hedging language ('estimated', 'likely', 'potential') in the risk and NPK fields.` }] }]
                        };'''

if old_payload in text:
    text = text.replace(old_payload, new_payload)

# 2. Update the string parsing and Insight UI rendering logic
# We need to replace the content inside the "if (gemData && (gemData.text || gemData.candidates)) {" block
old_parse_block = '''insight = gemData.text ? gemData.text : gemData.candidates[0].content.parts[0].text;
                                    window._canopyDebug.geminiSuccess++;
                                    insight = insight.replace(/<[^>]*>/g, '');
                                    insight += ' <em style="font-size:11px; color:#8a7a63;"><br/><br/>[Source: Gemini AI analysis. NPK/Pest levels are AI-estimated reasoning based on telemetry patterns and are NOT direct sensor measurements. Requires hardware validation.]</em>';
                                    console.log("SETTING_INSIGHT_TEXT =", insight);'''

new_parse_block = '''let rawString = gemData.text ? gemData.text : gemData.candidates[0].content.parts[0].text;
                                    window._canopyDebug.geminiSuccess++;
                                    
                                    try {
                                        rawString = rawString.trim().replace(/^```json/, '').replace(/```$/, '').trim();
                                        const j = JSON.parse(rawString);
                                        insight = `
                                            <div style="margin-bottom:12px; line-height:1.4;">${j.summary}</div>
                                            
                                            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; padding-bottom:6px; margin-bottom:6px;">
                                                <span style="color:#aaa; font-size:12px;">STRESS SEVERITY</span>
                                                <div style="text-align:right;">
                                                    <strong style="color:var(--stress-300); font-size:13px;">${j.stress_severity}</strong> 
                                                    <span style="font-size:9px; color:#8a7a63; display:block;">[AI Estimate]</span>
                                                </div>
                                            </div>

                                            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; padding-bottom:6px; margin-bottom:6px;">
                                                <span style="color:#aaa; font-size:12px;">PEST RISK</span>
                                                <div style="text-align:right;">
                                                    <strong style="color:var(--stress-300); font-size:12px;">${j.likely_crop_disease_or_pest_risk}</strong> 
                                                    <span style="font-size:9px; color:#8a7a63; display:block;">[AI Estimate]</span>
                                                </div>
                                            </div>

                                            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; padding-bottom:6px; margin-bottom:12px;">
                                                <span style="color:#aaa; font-size:12px;">NPK SOIL HEALTH</span>
                                                <div style="text-align:right;">
                                                    <strong style="color:var(--stress-300); font-size:12px;">${j.npk_soil_health_estimate}</strong> 
                                                    <span style="font-size:9px; color:#8a7a63; display:block;">[AI Estimate]</span>
                                                </div>
                                            </div>

                                            <div style="font-size:10px; color:#666; text-align:center; padding-top:6px; font-style:italic;">
                                                ${j.confidence_caveat}
                                            </div>
                                        `;
                                        console.log("SETTING_INSIGHT_TEXT =", "JSON Structured Injection Active");
                                    } catch(parseErr) {
                                        console.error("[CANOPY AI INSIGHT] JSON Parse Error. Falling back to prose:", parseErr);
                                        insight = rawString + '<br><br><span style="font-size:10px; color:#8a7a63;">[AI Estimate - Failed to parse structured JSON]</span>';
                                    }
'''

if old_parse_block in text:
    text = text.replace(old_parse_block, new_parse_block)

# 3. Increase sanitize allowed tags for divs/styling
old_dompurify = "document.getElementById('p-insight').innerHTML = typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(insight, { ALLOWED_TAGS: ['em', 'strong', 'span', 'br'], ALLOWED_ATTR: ['style'] }) : insight;"
new_dompurify = "document.getElementById('p-insight').innerHTML = typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(insight, { ALLOWED_TAGS: ['em', 'strong', 'span', 'br', 'div'], ALLOWED_ATTR: ['style'] }) : insight;"

if old_dompurify in text:
    text = text.replace(old_dompurify, new_dompurify)

# 4. Bind the webglcontextlost hook
webgl_hook = '''// Initialize visual rendering array
        try {
            const world = Globe()
                (document.getElementById('globe-viz'))'''

new_webgl_hook = '''// Context loss recovery hook for memory pressure
        const globeContainer = document.getElementById('globe-viz');
        globeContainer.addEventListener('webglcontextlost', (e) => {
            e.preventDefault();
            console.error("WebGL Context Lost due to memory pressure.");
            globeContainer.innerHTML = '<div style="display:flex; height:100%; align-items:center; justify-content:center; color:#ef4444; font-family:monospace; font-size:14px; background:#000;">[WARNING] 3D Globe Context Lost! GPU memory exhausted.<br><br>Please hard-refresh (Ctrl+F5) to restore rendering pipeline.</div>';
        });

        // Initialize visual rendering array
        try {
            const world = Globe()
                (document.getElementById('globe-viz'))'''

if webgl_hook in text:
    text = text.replace(webgl_hook, new_webgl_hook)


with open('index.html', 'w', encoding='utf-8') as f:
    f.write(text)
