import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.rfind('window.TempoI18n =')
if idx == -1:
    idx = text.rfind('return {')
print(text[idx-50:idx+600])
