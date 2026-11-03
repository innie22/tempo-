import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('auth.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("".join(lines[415:460]))
