import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('toolNotes.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'function getAvailableTasks' in l:
        print(f"getAvailableTasks at {i+1}:")
        for j in range(i, min(i+45, len(lines))):
            print(f"  {lines[j]}", end='')
        break
