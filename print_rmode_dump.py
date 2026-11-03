import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/rmode_home_dump.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines[:120], 1):
    print(f"{i:3d}: {l.rstrip()}")
