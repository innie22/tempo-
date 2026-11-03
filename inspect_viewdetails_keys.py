import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'viewDetails: "Xem chi tiết' in l:
        print(f"vi at line {i+1}: {l.strip()}")
    if 'viewDetails: "View details' in l:
        print(f"en at line {i+1}: {l.strip()}")
