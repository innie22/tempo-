import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'i18n.js' in l or 'toolNotes.js' in l:
        print(f"{i+1}: {repr(l.strip())}")
