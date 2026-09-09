with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the payload directly using slicing
start_str = 'const geminiPayload = {'
payload_start = text.find(start_str)

if payload_start != -1:
    payload_end = text.find('};', payload_start) + 2
    
    new_payload = '''const geminiPayload = {
                            "contents": [{ "parts": [{ "text": `You are the Canopy AI Agricultural Analyst. I just scanned a farm polygon using OSINT proxies. The Mean NDVI is ${ndvi.toFixed(3)}. Provide a professional vegetation diagnosis. You MUST strictly use explicit hedging language (like 'estimated', 'likely', or 'based on vegetation patterns') when guessing pest risks or general NPK soil health, to ensure they are visually distinguished as AI estimates and not physical sensor measurements. Write exactly 2-3 concise plain-text sentences. DO NOT use markdown, HTML tags, or formatting characters.` }] }]
                        };'''
    text = text[:payload_start] + new_payload + text[payload_end:]

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(text)
