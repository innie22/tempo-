import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('planWorkspace.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== activeModal assignments in planWorkspace.js ===")
for i, line in enumerate(lines):
    if re.search(r'activeModal\s*=', line):
        print(f"L{i+1}: {line.strip()[:100]}")
