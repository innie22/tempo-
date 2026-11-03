import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'toolNotes:' in l:
        print(f"toolNotes: found at line {i+1}")
        for j in range(i, min(i+25, len(lines))):
            print(f"  {lines[j]}", end='')
