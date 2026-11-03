import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'screen-plan' in l or 'plan-mount' in l:
        print(f"index.html line {i+1}: {l.strip()}")
