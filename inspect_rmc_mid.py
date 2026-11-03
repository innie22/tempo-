import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/render_modal_content_dump.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(130, 260):
    print(f"{i+1:3d}: {lines[i].rstrip()}")
