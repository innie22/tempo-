import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

assert '\r\n' not in content, "CRLF found in mode.js!"

# 1. Update getUrmodeTaskData
task_data_target = """        if (!matchedTask && mockTasks[sTaskId]) {
            matchedTask = mockTasks[sTaskId];
        }

        if (matchedTask) {"""

task_data_replacement = """        if (!matchedTask && mockTasks[sTaskId]) {
            matchedTask = mockTasks[sTaskId];
        }

        if (!matchedTask && window.TempoToolNotes && typeof window.TempoToolNotes.getAvailableTasks === 'function') {
            const avail = window.TempoToolNotes.getAvailableTasks();
            const found = avail.find(t => t && String(t.id) === sTaskId);
            if (found) {
                matchedTask = found;
            }
        }

        if (matchedTask) {"""

assert task_data_target in content, "task_data_target not found!"
content = content.replace(task_data_target, task_data_replacement, 1)

# 2. Update closeUrmodeTaskDetailModal and renderUrmodeTaskDetailModalDOM
modal_dom_target = """    function closeUrmodeTaskDetailModal() {
        activeUrmodeDetailTaskId = null;
        isUrmodeDetailEditingTitle = false;
        isUrmodeDetailEditingDeadline = false;
        isUrmodeDetailEditingNote = false;
        isUrmodeDetailLabelMenuOpen = false;
        isUrmodeDetailAddingSubtask = false;
        editingUrmodeSubtaskId = null;
        renderUrmodeTaskDetailModalDOM();
    }

    function isUrmodeTaskDetailModalOpen() {
        return Boolean(activeUrmodeDetailTaskId);
    }

    function renderUrmodeTaskDetailModalDOM() {
        const root = document.getElementById('urmode-task-modal-root');
        if (root) {
            root.innerHTML = renderUrmodeTaskDetailModalHTML();
        }
    }"""

modal_dom_replacement = """    function closeUrmodeTaskDetailModal() {
        activeUrmodeDetailTaskId = null;
        isUrmodeDetailEditingTitle = false;
        isUrmodeDetailEditingDeadline = false;
        isUrmodeDetailEditingNote = false;
        isUrmodeDetailLabelMenuOpen = false;
        isUrmodeDetailAddingSubtask = false;
        editingUrmodeSubtaskId = null;
        const globalRoot = document.getElementById('urmode-task-modal-global-root');
        if (globalRoot) {
            globalRoot.innerHTML = '';
        }
        renderUrmodeTaskDetailModalDOM();
    }

    function isUrmodeTaskDetailModalOpen() {
        return Boolean(activeUrmodeDetailTaskId);
    }

    function renderUrmodeTaskDetailModalDOM() {
        let root = document.getElementById('urmode-task-modal-root');
        if (!root || root.closest('.hidden')) {
            let globalRoot = document.getElementById('urmode-task-modal-global-root');
            if (!globalRoot) {
                globalRoot = document.createElement('div');
                globalRoot.id = 'urmode-task-modal-global-root';
                document.body.appendChild(globalRoot);
            }
            globalRoot.innerHTML = renderUrmodeTaskDetailModalHTML();
            return;
        }
        root.innerHTML = renderUrmodeTaskDetailModalHTML();
    }"""

assert modal_dom_target in content, "modal_dom_target not found!"
content = content.replace(modal_dom_target, modal_dom_replacement, 1)

assert '\r' not in content, "CRLF introduced into mode.js!"

with open('mode.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print(f"Updated mode.js successfully! Total LF lines: {content.count(chr(10))}")
