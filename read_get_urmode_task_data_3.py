import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(8670, 8740):
    print(f"{i+1}: {lines[i]}", end='')
