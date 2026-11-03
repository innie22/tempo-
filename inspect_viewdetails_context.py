import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

print("vi lines 627-635:")
for i in range(626, 636):
    print(f"  {repr(lines[i])}")

print("en lines 1243-1252:")
for i in range(1242, 1252):
    print(f"  {repr(lines[i])}")
