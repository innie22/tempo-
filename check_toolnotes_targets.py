import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('toolNotes.js', 'r', encoding='utf-8', newline='') as f:
    text = f.read()

assert '\r\n' not in text, "CRLF found in toolNotes.js!"

# Check if target blocks exist exactly
target_header = """    // Active modal state
    let activeModalNoteId = null;"""

print("target_header in text:", target_header in text)

target_close = """    function closeModal() {
        const root = document.getElementById('tool-notes-modal-root');
        if (root) root.innerHTML = '';
        activeModalNoteId = null;
    }"""

print("target_close in text:", target_close in text)

target_modal_start = "    function openCreateNoteModal(defaultType = 'day', defaultDate = null) {"
print("target_modal_start in text:", target_modal_start in text)
