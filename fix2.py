with open('index.html', 'r', encoding='utf-8') as f:
    t = f.read()

t = t.replace(r'\u2197', '↗')
t = t.replace(r'\u25b2', '▲')
t = t.replace(r'\u25cf', '●')
t = t.replace(r'\u2014', '—')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(t)
