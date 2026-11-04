with open('mode.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'openquicktaskmodal' in line.lower():
        print(f"openQuickTaskModal at {i+1}: {line.strip()}")
    if 'execute my task' in line.lower():
        print(f"execute my task at {i+1}: {line.strip()}")
    if 'tạo task' in line.lower() or 'create a new task' in line.lower() or 'execute an urgent task' in line.lower():
        print(f"related at {i+1}: {line.strip()}")
