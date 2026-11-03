import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('urmodeFlow.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('window.TempoPlanStore.saveActivePlan')
print(text[idx-50:idx+400])
