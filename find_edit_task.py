import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('planWorkspace.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'edit\s*task', text, re.I)]
print(f"Matches for 'edit task' in planWorkspace.js: {len(matches)}")
for idx in matches:
    start = max(0, idx - 100)
    end = min(len(text), idx + 100)
    print(text[start:end].replace('\n', ' '))
    print('-'*50)
