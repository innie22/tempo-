import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('toolNotes.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'renderToolNotesPage' in l or '8. TOOL NOTES PAGE RENDERER' in l or 'renderDayNotesListHTML' in l or 'renderTaskNotesListHTML' in l:
        print(f"{i+1}: {l.strip()}")
