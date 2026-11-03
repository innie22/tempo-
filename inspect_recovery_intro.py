import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function renderRecoveryIntroBanner(')
if idx != -1:
    print(text[idx:idx+1500])
else:
    print("renderRecoveryIntroBanner NOT FOUND")
