import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'renderRecentlyCard' in line or 'recently' in line.lower() and 'card' in line.lower():
            print(f'{idx}: {line.strip()[:100]}')
