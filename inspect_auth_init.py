import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('auth.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('async function init(')
if idx == -1:
    idx = text.find('function init(')
print(text[idx:idx+1500])
