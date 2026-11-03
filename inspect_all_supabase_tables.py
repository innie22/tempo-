import sys, os, re

sys.stdout.reconfigure(encoding='utf-8')

print("=== SEARCHING ALL SUPABASE TABLES USED IN REPOSITORY ===")
pattern = re.compile(r'supabase\s*\.\s*from\(\s*[\'"]([^\'"]+)[\'"]\s*\)')

tables_found = {}
for root, dirs, files in os.walk('.'):
    if 'node_modules' in root or '.git' in root or 'scratch' in root:
        continue
    for f in files:
        if f.endswith('.js'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as fl:
                for line_num, line in enumerate(fl, 1):
                    for match in pattern.finditer(line):
                        tbl = match.group(1)
                        if tbl not in tables_found:
                            tables_found[tbl] = []
                        tables_found[tbl].append((path, line_num))

for tbl, locs in sorted(tables_found.items()):
    print(f"Table '{tbl}': {len(locs)} occurrences across {len(set(p for p, _ in locs))} file(s)")
    for p, l in locs[:3]:
        print(f"   {p}:{l}")
