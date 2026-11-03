import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'function renderUrmodeTaskDetailModalHTML' in l:
        print(f"renderUrmodeTaskDetailModalHTML at {i+1}:")
        for j in range(i, min(i+60, len(lines))):
            print(f"  {lines[j]}", end='')
        break
