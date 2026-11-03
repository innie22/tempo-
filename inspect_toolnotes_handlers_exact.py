import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('toolNotes.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(670, 725):
    print(f"{i+1}: {repr(lines[i])}")
