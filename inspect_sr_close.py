import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('stressRelief.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function closeModal')
print(text[idx:idx+1000])
