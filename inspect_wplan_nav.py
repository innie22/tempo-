import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('app.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('const isWplan =')
print(text[idx:idx+1500])
