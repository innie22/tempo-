import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('recoverySetup.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'function renderReturningHub' in line:
        print('=== renderReturningHub ===')
        print(''.join(lines[i:i+90]))
        break
