import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
for m in re.finditer(r'cards:\s*\{', text):
    start = max(0, m.start() - 300)
    end = min(len(text), m.end() + 200)
    print(f"Match cards at {m.start()}:\n", text[start:end])
    print("="*40)
