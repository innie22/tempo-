import os, glob, re

for root, dirs, files in os.walk('.'):
    if '.git' in root or 'scratch' in root or 'node_modules' in root:
        continue
    for file in files:
        if file.endswith(('.js', '.html', '.json')):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'execute my task' in content.lower():
                    print(f"[Execute my task] found in {path}")
                if 'openquicktaskmodal' in content.lower():
                    print(f"[openQuickTaskModal] found in {path}")
