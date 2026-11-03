# -*- coding: utf-8 -*-
with open(r'scratch\test_all_tool_notes.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace document.querySelector('[data-day-note-id]') with document.querySelector('#tool-notes-root [data-day-note-id]')
text = text.replace("const dayCard = document.querySelector('[data-day-note-id]');", "const dayCard = document.querySelector('#tool-notes-root [data-day-note-id]');")

with open(r'scratch\test_all_tool_notes.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print("Updated dayCard click selector.")
