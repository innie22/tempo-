import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('toolNotes.js', 'r', encoding='utf-8', newline='') as f:
    text = f.read()

end_idx = text.find("    // =========================================================================" + "\n    // 8. TOOL NOTES PAGE RENDERER")
start_idx = text.find("    function openCreateNoteModal(defaultType = 'day', defaultDate = null) {")

print("Target to replace starts with:")
print(repr(text[start_idx:start_idx+100]))
print("Target to replace ends with:")
print(repr(text[end_idx-100:end_idx]))
