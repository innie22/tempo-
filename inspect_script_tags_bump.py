import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if any(k in l for k in ['i18n.js', 'toolNotes.js', 'mode.js']):
        print(f"{i+1}: {repr(l.strip())}")
