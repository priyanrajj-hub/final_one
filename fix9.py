import re

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# First fallback injection block
text = re.sub(
    r'(document\.getElementById\(\'p-insight\'\)\.innerHTML = (DOMPurify\.sanitize\(insight.*?\) : insight);)',
    r'console.log("SETTING_INSIGHT_TEXT =", insight);\n                                \1',
    text
)

# Secondary DOMPurify else block injection
text = re.sub(
    r'(document\.getElementById\(\'p-insight\'\)\.innerHTML = insight;)',
    r'console.log("SETTING_INSIGHT_TEXT =", insight);\n                                \1',
    text
)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(text)
