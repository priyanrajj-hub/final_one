with open('index.html', 'r', encoding='utf-8') as f:
    t = f.read()

t = t.replace('const timeoutId = setTimeout(() => controller.abort(), 28000);', 
    'console.log("GEMINI_TIMEOUT_MS =", 28000);\n            const timeoutId = setTimeout(() => controller.abort(), 28000);')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(t)
