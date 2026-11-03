import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'recently' in line.lower() or 'gần đây' in line.lower():
            print(f'{idx}: {line.strip()[:100]}')
