import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('toolNotes.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'openNoteDetailModal' in l or 'expand' in l.lower():
        print(f"{i+1}: {l.strip()}")
