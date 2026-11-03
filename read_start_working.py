import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('urmodeFlow.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function showStartWorkingPopup()')
print(text[idx+1800:idx+3500])
