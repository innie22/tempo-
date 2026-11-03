import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

print("Total lines:", len(lines))
for i in range(1140, min(1200, len(lines))):
    print(f"{i+1}: {repr(lines[i][:60])}")
