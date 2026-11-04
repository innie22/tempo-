with open('planWorkspace.js', 'rb') as f:
    content = f.read()

assert b'\r\n' not in content, 'File has CRLF!'

old_fit_modal = b"""        if (activeModal === 'fit-task-prompt' && pendingAddedTask) {
            return `
                <div class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">"""

new_fit_modal = b"""        if (activeModal === 'fit-task-prompt' && pendingAddedTask) {
            return `
                <div id="fit-task-modal" data-modal-type="fit-task-prompt" class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">"""

assert old_fit_modal in content, "old_fit_modal not found"
content = content.replace(old_fit_modal, new_fit_modal)

with open('planWorkspace.js', 'wb') as f:
    f.write(content)

print("Added id and data-modal-type to fit-task-modal!")
