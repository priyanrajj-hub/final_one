with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's cleanly replace the entire block from gemRes.json() to the end of the try block
start_marker = 'const gemData = await gemRes.json();'
end_marker = '} else {'
start_idx = text.find(start_marker)

if start_idx != -1:
    end_idx = text.find(end_marker, start_idx)
    old_block = text[start_idx:end_idx]
    
    new_block = '''const gemData = await gemRes.json();
                                console.log("[CANOPY AI INSIGHT] Successful response:", gemData);
                                console.log("[CANOPY AI INSIGHT] RAW STRUCTURE:", JSON.stringify(gemData, null, 2));

                                if (gemData && (gemData.text || gemData.candidates)) {
                                    insight = gemData.text ? gemData.text : gemData.candidates[0].content.parts[0].text;
                                    window._canopyDebug.geminiSuccess++;
                                    insight = insight.replace(/<[^>]*>/g, '');
                                    insight += ' <em style="font-size:11px; color:#8a7a63;"><br/><br/>[Source: Gemini AI analysis. NPK/Pest levels are AI-estimated reasoning based on telemetry patterns and are NOT direct sensor measurements. Requires hardware validation.]</em>';
                                } else if (gemData.error) {
                                    console.error("[CANOPY AI INSIGHT] API returned error block:", gemData.error);
                                    insight = "AI insight unavailable — " + (gemData.error.message || "Unknown API error");
                                    throw new Error(insight);
                                } else {
                                    const errMsg = "Cannot process response structure, expected 'text' parameter.";
                                    console.error("[CANOPY AI INSIGHT] PARSING ERROR:", errMsg, "Raw data:", gemData);
                                    throw new Error(errMsg);
                                }
                            '''
    text = text.replace(old_block, new_block)
else:
    print("FATAL: Could not find start block!")

# Also, update the geminiPayload to satisfy Fix #2
old_prompt = 'you are the Canopy AI Agricultural Analyst. I just scanned a farm polygon using OSINT proxies. The Mean NDVI is ${ndvi.toFixed(3)}. In exactly 2 plain-text sentences (no markdown, no HTML tags, no bold/italic formatting), give a professional vegetation health diagnosis for this NDVI value. State specifically whether the crop is healthy or stressed, and name the most likely risk factor. DO NOT use any markup or formatting characters.'

# Find the payload and replace
payload_start = text.find('const geminiPayload = {')
if payload_start != -1:
    payload_end = text.find('};', payload_start) + 2
    
    new_payload = '''const geminiPayload = {
                            "contents": [{ "parts": [{ "text": `You are the Canopy AI Agricultural Analyst. I just scanned a farm polygon using OSINT proxies. The Mean NDVI is ${ndvi.toFixed(3)}. Provide a professional vegetation diagnosis estimating 1) Crop health/stress severity, 2) The most likely dominant risk factor or pest risk based on the data, and 3) An estimated reasoning of general NPK soil health. Write exactly 2-3 concise plain-text sentences. DO NOT use markdown, HTML tags, or formatting characters.` }] }]
                        };'''
    text = text[:payload_start] + new_payload + text[payload_end:]

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(text)

