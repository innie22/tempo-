import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('learnSolve.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function openModal(')
print(text[idx:idx+1200])
