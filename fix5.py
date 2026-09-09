import re

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Add the console log exactly before the AbortController is created
text = re.sub(
    r'(const controller = new AbortController\(\);)',
    r'console.log("GEMINI_TIMEOUT_MS =", 35000);\n            \1',
    text
)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(text)
