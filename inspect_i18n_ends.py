import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Lines 575-595:")
for i in range(574, min(595, len(lines))):
    print(f"{i+1}: {repr(lines[i])}")

print("\nLines around 1140-1160:")
for i in range(1135, min(1160, len(lines))):
    print(f"{i+1}: {repr(lines[i])}")
