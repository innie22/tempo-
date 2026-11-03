import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('learnSolve.js', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('function renderTipCalloutHTML(tipId)')
print(text[start:start+1000])
