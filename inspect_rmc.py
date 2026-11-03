import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/render_modal_content_dump.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(50, len(lines), 30):
    print(f"--- Lines {i+1} to {min(i+30, len(lines))} ---")
    for j in range(i, min(i+30, len(lines))):
        print(f"{j+1:3d}: {lines[j].rstrip()}")
