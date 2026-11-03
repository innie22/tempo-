# -*- coding: utf-8 -*-
with open(r'scratch\test_all_tool_notes.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("root.querySelector('.bg-\\\\[\\\\#FAF7F4\\\\] p')", "root.querySelector('p.whitespace-pre-wrap')")
text = text.replace("root.querySelector('.bg-\\[\\#FAF7F4\\] p')", "root.querySelector('p.whitespace-pre-wrap')")

with open(r'scratch\test_all_tool_notes.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print("Replaced querySelector with p.whitespace-pre-wrap.")
