import re

with open('urmodeFlow.js', 'r', encoding='utf-8') as f:
    text = f.read()

print("--- adjust-due matches ---")
for m in re.finditer(r'.{0,60}adjust-due[^\s"\'>]+.{0,60}', text):
    print(m.group(0).strip())

print("\n--- adjust-new-task-due matches ---")
for m in re.finditer(r'.{0,60}adjust-new-task-due.{0,60}', text):
    print(m.group(0).strip())
