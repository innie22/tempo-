import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'plan-workspace' in l or 'plan' in l.lower():
        if any(k in l for k in ['case', 'route', 'tabId', 'navigateTo', 'render']):
            print(f"app.js line {i+1}: {l.strip()}")
