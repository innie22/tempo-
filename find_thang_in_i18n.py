import sys
sys.stdout.reconfigure(encoding='utf-8')

content = open('i18n.js', encoding='utf-8').read()
for idx, line in enumerate(content.splitlines()):
    if 'tháng' in line.lower():
        print(f'{idx+1}: {line.strip()[:100]}')
