import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print("=== CHECKING YOUR WORKING PLAN IN MODE.JS ===")
for i, line in enumerate(lines):
    if 'your working plan' in line.lower() or 'yourworkingplan' in line.lower():
        print(f"L{i+1}: {line.strip()[:140]}")
