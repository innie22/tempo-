import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('toolNotes.js', 'r', encoding='utf-8', newline='') as f:
    text = f.read()

start_idx = text.find("    function openCreateNoteModal(defaultType = 'day', defaultDate = null) {")
end_idx = text.find("    function renderDayNotesListHTML(dayNotes) {")

print("start_idx:", start_idx)
print("end_idx:", end_idx)
print("block length:", end_idx - start_idx)
print("End of block:")
print(repr(text[end_idx-100:end_idx]))
