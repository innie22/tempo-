import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('mode.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(''.join(lines[3530:3562]))
