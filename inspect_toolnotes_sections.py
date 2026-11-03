import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('toolNotes.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Lines 815-825:")
for i in range(814, 825):
    print(f"{i+1}: {lines[i]}", end='')

print("\nLines 1040-1055:")
for i in range(1040, 1055):
    print(f"{i+1}: {lines[i]}", end='')
