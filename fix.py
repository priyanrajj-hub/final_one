with open('index.html', 'r', encoding='utf-8') as f:
    t = f.read()
t = t.replace(r'\u26a0', '⚠')
t = t.replace('controller.abort(), 12000', 'controller.abort(), 28000')
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(t)
