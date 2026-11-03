import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

for i, l in enumerate(lines, 1):
    if 'mode.js' in l:
        print(f"{i}: {l.strip()}")
