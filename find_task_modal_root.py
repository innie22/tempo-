import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'urmode-task-modal-root' in l:
        print(f"urmode-task-modal-root at {i+1}: {l.strip()}")
