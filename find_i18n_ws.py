import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'workspace:' in line or 'workspace :' in line:
        print(f"L{i+1}: {line.strip()}")
