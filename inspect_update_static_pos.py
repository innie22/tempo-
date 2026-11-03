import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

for i, l in enumerate(lines, 1):
    if 'function updateStaticHtml()' in l:
        for j in range(i-1, i+30):
            print(f"{j+1}: {repr(lines[j])}")
        break
