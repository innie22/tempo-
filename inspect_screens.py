import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('app.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('// Hide all screen containers')
if idx == -1:
    idx = text.find('screen-')
print(text[idx-50:idx+1500])
