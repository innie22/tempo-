import sys, os, re

sys.stdout.reconfigure(encoding='utf-8')

print("=== SEARCHING FOR WEEKLY REVIEW / REPORT ===")
pattern = re.compile(r'weekly(?:review|report)', re.I)

matches = []
for root, dirs, files in os.walk('.'):
    if 'node_modules' in root or '.git' in root or 'scratch' in root:
        continue
    for f in files:
        if f.endswith('.js') or f.endswith('.html'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as fl:
                for line_num, line in enumerate(fl, 1):
                    if pattern.search(line):
                        matches.append((path, line_num, line.strip()))

for p, l, line in matches[:40]:
    print(f"{p}:{l} -> {line[:120]}")
