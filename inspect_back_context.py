import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for target in [730, 1469]:
    print(f"Around line {target}:")
    for j in range(max(0, target-15), min(len(lines), target+5)):
        print(f"  {j+1}: {lines[j]}", end='')
