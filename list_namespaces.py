import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if idx > 25 and idx < 1000 and line.startswith('            ') and line.endswith('{\n'):
            print(f'{idx}: {line.strip()}')
