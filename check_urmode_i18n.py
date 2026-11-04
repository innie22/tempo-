import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('urmodeFlow.js', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('function openQuickTaskModal()')
print(text[start:start+2500])
