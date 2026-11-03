import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('planStore.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('async function saveActivePlan')
print(text[idx+150:idx+650])
