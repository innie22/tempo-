import re

with open('index.html', 'r', encoding='utf-8') as f:
    c = f.read()

matches = re.findall(r'id=["\']([^"\']*modal[^"\']*)["\']', c, re.IGNORECASE)
for m in sorted(set(matches)):
    print(m)
