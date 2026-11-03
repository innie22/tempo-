import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('urmodeFlow.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx1 = text.find('function renderAdjustmentStep3Proposal')
idx2 = text.find('function confirmAdjustmentPlan')
print(text[idx1:idx2+600])
