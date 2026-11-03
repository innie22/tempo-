import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('recoverySetup.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function exploreFirst(')
print(text[idx:idx+600])
