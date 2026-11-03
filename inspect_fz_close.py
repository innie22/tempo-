import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('focusZone.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function close() {')
print(text[idx:idx+1200])
