import re

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the payload matching
pattern = r'if \(gemData && gemData\.candidates\) \{[\s\S]*?\} else if \(gemData\.error\) \{[\s\S]*?throw new Error\(insight\);\n\s*\}'

replacement = '''console.log("[CANOPY AI INSIGHT] RAW STRUCTURE:", JSON.stringify(gemData, null, 2));
                                if (gemData && (gemData.text || gemData.candidates)) {
                                    // Support both modern flattened payload (.text) and legacy array traversal (.candidates)
                                    insight = gemData.text ? gemData.text : gemData.candidates[0].content.parts[0].text;
                                    window._canopyDebug.geminiSuccess++;
                                    // Strip any accidental HTML tags from LLM output
                                    insight = insight.replace(/<[^>]*>/g, '');
                                    insight += ' <em style="font-size:11px; color:#8a7a63;">[Source: Gemini AI analysis]</em>';
                                } else if (gemData.error) {
                                    console.error("[CANOPY AI INSIGHT] API returned error block:", gemData.error);
                                    insight = "AI insight unavailable — " + (gemData.error.message || "Unknown API error");
                                    throw new Error(insight);
                                } else {
                                    const errMsg = "Cannot process response structure, expected 'text' parameter.";
                                    console.error("[CANOPY AI INSIGHT] PARSING ERROR:", errMsg, "Raw data:", gemData);
                                    throw new Error(errMsg);
                                }'''

text = re.sub(pattern, replacement, text)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(text)
