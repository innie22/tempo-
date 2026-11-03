# -*- coding: utf-8 -*-
with open(r'scratch\test_all_tool_notes.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace document.querySelectorAll('[data-day-note-id]') with document.querySelectorAll('#tool-notes-root [data-day-note-id]')
text = text.replace("document.querySelectorAll('[data-day-note-id]')", "document.querySelectorAll('#tool-notes-root [data-day-note-id]')")
text = text.replace("document.querySelectorAll('[data-task-note-id]')", "document.querySelectorAll('#tool-notes-root [data-task-note-id]')")

with open(r'scratch\test_all_tool_notes.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print("Updated selector scoping in test script.")
