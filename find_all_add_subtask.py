import os, glob, re, sys
sys.stdout.reconfigure(encoding='utf-8')

for root, dirs, files in os.walk('.'):
    if any(p in root for p in ['.git', 'scratch', 'node_modules']):
        continue
    for file in files:
        if file.endswith(('.js', '.html')):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                for idx, line in enumerate(lines):
                    if re.search(r'add.*subtask', line, re.I):
                        print(f"{path}:{idx+1}: {line.strip()[:140]}")
