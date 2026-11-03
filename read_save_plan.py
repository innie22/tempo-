import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('urmodeFlow.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function saveAdjustmentPlan')
print(text[idx:idx+1500])
