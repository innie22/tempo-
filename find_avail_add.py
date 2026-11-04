import sys, os, re

sys.stdout.reconfigure(encoding='utf-8')

for root, dirs, files in os.walk('.'):
    if any(x in root for x in ['.git', 'node_modules', '.gemini', 'scratch']):
        continue
    for file in files:
        if file.endswith('.js') or file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for idx, line in enumerate(f):
                    if re.search(r'add.*availab|availab.*add', line, re.I):
                        print(f"{filepath} L{idx+1}: {line.strip()[:140]}")
