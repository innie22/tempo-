import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('planStore.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.rfind('return {')
print(text[idx:])
