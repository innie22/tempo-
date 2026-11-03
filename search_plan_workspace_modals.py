import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('planWorkspace.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if any(k in l for k in ['openTask', 'taskDetail', 'task-detail', 'TaskModal', 'openDetail']):
        print(f"{i+1}: {l.strip()}")
