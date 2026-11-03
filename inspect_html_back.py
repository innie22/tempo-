import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

for i in range(583, 595):
    print(f"{i+1}: {repr(lines[i])}")
