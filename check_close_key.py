import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(1060, 1100):
    if 'close' in lines[i].lower():
        print(f'{i+1}: {lines[i].strip()}')
