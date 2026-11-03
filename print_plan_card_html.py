import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/rmode_plan_dump.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(220, min(350, len(lines))):
    print(f"{i+1:3d}: {lines[i].rstrip()}")
