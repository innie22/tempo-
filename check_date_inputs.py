import os, re

files = [f for f in os.listdir('.') if f.endswith('.js') or f.endswith('.html')]
for f in files:
    content = open(f, 'r', encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'<input[^>]*type=["\']date["\'][^>]*>', content):
        print(f + ' -> ' + m.group(0)[:120])
