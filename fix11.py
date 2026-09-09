import re

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update Payload
new_payload = '''const geminiPayload = {
                            "contents": [{ "parts": [{ "text": `You are the Canopy AI Agricultural Analyst. I just scanned a farm polygon using OSINT proxies. The Mean NDVI is ${ndvi.toFixed(3)}. Return your analysis STRICTLY as a JSON object with the following exact keys, and DO NOT wrap it in markdown code blocks:
{
  "summary": "one sentence overview of overall crop canopy health",
  "stress_severity": "Low | Moderate | High | Critical",
  "crop_disease_risk": "estimated disease risk with likely disease type if inferable from NDVI/weather pattern (e.g. fungal risk under high humidity)",
  "pest_risk": "estimated pest pressure level and likely pest category if inferable (e.g. sap-sucking pests favored by current temperature/humidity)",
  "nutrient_deficiency_estimate": "estimated N-P-K deficiency signals inferable from canopy density/color patterns — name which nutrient is most likely limiting if any signal suggests it",
  "irrigation_recommendation": "estimated water need based on current NDVI, rainfall deficit, and temperature — e.g. 'irrigate within 2-3 days' or 'no immediate action needed'",
  "climate_risk_flag": "flag drought/heat-wave/flood risk specifically if current weather data (temperature, rainfall deficit, humidity) crosses recognizable thresholds",
  "confidence_caveat": "AI-estimated reasoning based on satellite/weather telemetry, not direct sensor or lab measurement — requires ground validation"
}` }] }]
                        };'''

text = re.sub(r'const geminiPayload = \{[\s\S]*?\};', new_payload, text, count=1)

# 2. Update Parse logic
new_parse = r'''if (gemData && (gemData.text || gemData.candidates)) {
                                    let rawString = gemData.text ? gemData.text : gemData.candidates[0].content.parts[0].text;
                                    window._canopyDebug.geminiSuccess++;
                                    
                                    try {
                                        let cleanStr = rawString.replace(/^```(json)?/, '').replace(/```$/, '').trim();
                                        const j = JSON.parse(cleanStr);
                                        
                                        insight = `
                                            <div style="margin-bottom:12px; line-height:1.4;">${j.summary}</div>
                                            
                                            <div style="color:var(--leaf-500); font-weight:bold; font-size:12px; border-bottom:1px solid #333; padding-bottom:6px; margin-bottom:8px; margin-top:15px; letter-spacing:1px;">
                                                > FIELD DIAGNOSTIC ESTIMATE
                                            </div>

                                            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #222; padding-bottom:6px; margin-bottom:6px;">
                                                <span style="color:#aaa; font-size:11px;">STRESS SEVERITY</span>
                                                <div style="text-align:right;">
                                                    <strong style="color:var(--stress-300); font-size:12px;">${j.stress_severity}</strong> 
                                                    <span style="font-size:9px; color:#8a7a63; display:block;">[AI Estimate]</span>
                                                </div>
                                            </div>

                                            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #222; padding-bottom:6px; margin-bottom:6px;">
                                                <span style="color:#aaa; font-size:11px;">CROP DISEASE RISK</span>
                                                <div style="text-align:right;">
                                                    <strong style="color:var(--stress-300); font-size:12px;">${j.crop_disease_risk}</strong> 
                                                    <span style="font-size:9px; color:#8a7a63; display:block;">[AI Estimate]</span>
                                                </div>
                                            </div>

                                            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #222; padding-bottom:6px; margin-bottom:6px;">
                                                <span style="color:#aaa; font-size:11px;">PEST RISK</span>
                                                <div style="text-align:right;">
                                                    <strong style="color:var(--stress-300); font-size:12px;">${j.pest_risk}</strong> 
                                                    <span style="font-size:9px; color:#8a7a63; display:block;">[AI Estimate]</span>
                                                </div>
                                            </div>

                                            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #222; padding-bottom:6px; margin-bottom:6px;">
                                                <span style="color:#aaa; font-size:11px;">NUTRIENT DEFICIENCY</span>
                                                <div style="text-align:right;">
                                                    <strong style="color:var(--stress-300); font-size:12px;">${j.nutrient_deficiency_estimate}</strong> 
                                                    <span style="font-size:9px; color:#8a7a63; display:block;">[AI Estimate]</span>
                                                </div>
                                            </div>
                                            
                                            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #222; padding-bottom:6px; margin-bottom:6px;">
                                                <span style="color:#aaa; font-size:11px;">IRRIGATION RECOMMENDATION</span>
                                                <div style="text-align:right;">
                                                    <strong style="color:var(--stress-300); font-size:12px;">${j.irrigation_recommendation}</strong> 
                                                    <span style="font-size:9px; color:#8a7a63; display:block;">[AI Estimate]</span>
                                                </div>
                                            </div>
                                            
                                            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #222; padding-bottom:6px; margin-bottom:12px;">
                                                <span style="color:#aaa; font-size:11px;">CLIMATE RISK FLAG</span>
                                                <div style="text-align:right;">
                                                    <strong style="color:var(--stress-300); font-size:12px;">${j.climate_risk_flag}</strong> 
                                                    <span style="font-size:9px; color:#8a7a63; display:block;">[AI Estimate]</span>
                                                </div>
                                            </div>

                                            <div style="font-size:10px; color:#666; text-align:center; padding-top:6px; font-style:italic;">
                                                ${j.confidence_caveat}
                                            </div>
                                        `;
                                        console.log("SETTING_INSIGHT_TEXT =", "JSON Structure Parse Success!");
                                    } catch(parseErr) {
                                        console.error("[CANOPY AI INSIGHT] JSON Parse Error. Falling back to prose:", parseErr);
                                        insight = rawString.replace(/<[^>]*>/g, '') + '<br><br><span style="font-size:10px; color:#8a7a63;">[AI Estimate - Failed to parse structured JSON]</span>';
                                        console.log("SETTING_INSIGHT_TEXT =", insight);
                                    }
                                } else if (gemData.error) {'''

text = re.sub(r'if \(gemData && \(gemData\.text \|\| gemData\.candidates\)\) \{[\s\S]*?\} else if \(gemData\.error\) \{', new_parse, text, count=1)


# 3. Add global unhandled context hook OR attach it to document.addEventListener("webglcontextlost") if globe doesn't natively expose it.
new_webgl = r'''document.addEventListener("webglcontextlost", function(e) {
            e.preventDefault();
            console.error("WebGL Context Lost triggered document-wide.");
            let globeContainer = document.getElementById('panorama');
            if (!globeContainer) globeContainer = document.body;
            const marker = document.createElement("div");
            marker.style = "position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:999999;background:rgba(20,0,0,0.9);color:#ef4444;padding:20px;border-radius:10px;font-family:monospace;border:2px solid #ef4444;text-align:center;";
            marker.innerHTML = "<strong>[WARNING] 3D Renderer Context Lost!</strong><br><br>GPU memory exhausted. This is normal over extended telemetry monitoring.<br>Please hard-refresh (Ctrl+F5) to restart the visualization pipeline.";
            document.body.appendChild(marker);
        }, true);
        '''
        
if 'webglcontextlost' not in text:
    text = re.sub(r'(<script>)', r'\1\n        ' + new_webgl, text, count=1)


with open('index.html', 'w', encoding='utf-8') as f:
    f.write(text)
