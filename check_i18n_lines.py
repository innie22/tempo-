import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('i18n.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("VI urgent:")
print(''.join(lines[182:195]))

print("VI recovery:")
print(''.join(lines[500:515]))
