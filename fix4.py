with open('index.html', 'r', encoding='utf-8') as f:
    t = f.read()

t = t.replace('const timeoutId = setTimeout(() => controller.abort(), 35000);', 
    'console.log("GEMINI_TIMEOUT_MS =", 35000);\n            const timeoutId = setTimeout(() => controller.abort(), 35000);')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(t)
