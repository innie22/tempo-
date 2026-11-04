import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('planWorkspace.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(2942, 2955):
    print(f"L{i+1}: {repr(lines[i])}")
