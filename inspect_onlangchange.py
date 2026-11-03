import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

for i in range(1199, min(1230, len(lines))):
    print(f"{i+1}: {repr(lines[i][:60])}")
