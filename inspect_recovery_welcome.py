import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('recoverySetup.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print('=== Lines 280 to 450 ===')
print(''.join(lines[280:450]))
