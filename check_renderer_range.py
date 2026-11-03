import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('toolNotes.js', 'r', encoding='utf-8') as f:
    text = f.read()

start_marker = "    // =========================================================================\n    // 8. TOOL NOTES PAGE RENDERER (Full Workspace)\n    // ========================================================================="
end_marker = "    // Escape key listener for closing modals\n    if (typeof window !== 'undefined') {"

start_pos = text.find(start_marker)
end_pos = text.find(end_marker)

print("start_pos:", start_pos)
print("end_pos:", end_pos)
print("Total length of section:", end_pos - start_pos)
