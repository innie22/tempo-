import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('app.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'function\s+navigateTo', text)]
for m in matches:
    lno = text.count('\n', 0, m) + 1
    print(f"navigateTo at line {lno}")
