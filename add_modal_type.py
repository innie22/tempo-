with open('planWorkspace.js', 'rb') as f:
    content = f.read()

assert b'\r\n' not in content, 'File has CRLF!'

content = content.replace(
    b'<div id="add-task-modal" class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4" onclick="if (event.target === this) window.TempoPlanWorkspace.closeAddTaskModal();" role="dialog" aria-modal="true">',
    b'<div id="add-task-modal" data-modal-type="add-task" class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4" onclick="if (event.target === this) window.TempoPlanWorkspace.closeAddTaskModal();" role="dialog" aria-modal="true">'
)

content = content.replace(
    b'<div id="reschedule-modal" class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4" onclick="if (event.target === this) window.TempoPlanWorkspace.closeRescheduleModal();" role="dialog" aria-modal="true">',
    b'<div id="reschedule-modal" data-modal-type="reschedule" class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4" onclick="if (event.target === this) window.TempoPlanWorkspace.closeRescheduleModal();" role="dialog" aria-modal="true">'
)

content = content.replace(
    b'<div id="add-available-time-modal"\n                     class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4"',
    b'<div id="add-available-time-modal"\n                     data-modal-type="add-available-time"\n                     class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4"'
)

content = content.replace(
    b'<div id="adjust-availability-modal" class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4" onclick="if (event.target === this) window.TempoPlanWorkspace.closeAdjustAvailabilityModal();" role="dialog" aria-modal="true">',
    b'<div id="adjust-availability-modal" data-modal-type="adjust-availability" class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4" onclick="if (event.target === this) window.TempoPlanWorkspace.closeAdjustAvailabilityModal();" role="dialog" aria-modal="true">'
)

with open('planWorkspace.js', 'wb') as f:
    f.write(content)

print('Updated modal tags with data-modal-type!')
