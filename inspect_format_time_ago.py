import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    text = f.read()

idx = text.find('function formatTimeAgo(')
print(text[idx:idx+1500])
