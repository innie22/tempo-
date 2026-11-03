import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if l.strip().startswith('vi: {') or l.strip().startswith('en: {') or l.strip().startswith('const DICTIONARY'):
        print(f"{i+1}: {l.strip()}")
    if 'toolNotes' in l:
        print(f"toolNotes at {i+1}: {l.strip()}")
