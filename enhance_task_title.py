with open('planWorkspace.js', 'rb') as f:
    content = f.read()

assert b'\r\n' not in content, 'File has CRLF!'

# 1. Update updateTaskName
old_fn = b"""    function updateTaskName(taskId, newName) {
        if (!newName || !newName.trim()) return;
        const plan = getActivePlan();
        if (!plan) return;

        let task = null;
        const pt = plan.plannedTasks.find(item => item.task && item.task.id === taskId);
        if (pt) task = pt.task;
        if (!task && plan.unarrangedTasks) {
            task = plan.unarrangedTasks.find(t => t.id === taskId);
        }
        if (!task) return;

        task.name = newName.trim();

        // Sync with shared tasks array
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getTasks === 'function') {
            const raw = window.TempoEmergencyFlow.getTasks();
            const shared = raw.find(t => t.id === taskId);
            if (shared) shared.name = task.name;
        }

        persistPlan(plan);
        render();
    }"""

new_fn = b"""    function updateTaskName(taskId, newName) {
        if (!newName || !newName.trim()) return;
        const plan = getActivePlan();
        if (!plan) return;

        const trimmed = newName.trim();
        let found = false;

        if (Array.isArray(plan.tasks)) {
            const t = plan.tasks.find(item => item && item.id === taskId);
            if (t) {
                t.name = trimmed;
                found = true;
            }
        }

        if (Array.isArray(plan.plannedTasks)) {
            plan.plannedTasks.forEach(pt => {
                if (pt && pt.task && pt.task.id === taskId) {
                    pt.task.name = trimmed;
                    found = true;
                }
            });
        }

        if (Array.isArray(plan.unarrangedTasks)) {
            plan.unarrangedTasks.forEach(u => {
                const ut = (u && u.task) ? u.task : u;
                if (ut && ut.id === taskId) {
                    ut.name = trimmed;
                    found = true;
                }
            });
        }

        if (!found) return;

        // Sync with shared tasks array
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getTasks === 'function') {
            const raw = window.TempoEmergencyFlow.getTasks();
            const shared = raw.find(t => t && t.id === taskId);
            if (shared) shared.name = trimmed;
        }

        persistPlan(plan);
        render();
    }"""

assert old_fn in content, "old_fn not found in planWorkspace.js"
content = content.replace(old_fn, new_fn)

# 2. Add id="pw-task-detail-title"
old_heading = b"""                                            <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] truncate ${selectedTask.completed ? 'line-through text-stone-400' : ''}">
                                                ${escapeHTML(selectedTask.name)}
                                            </h2>"""

new_heading = b"""                                            <h2 id="pw-task-detail-title" class="font-heading text-xl sm:text-2xl font-bold text-[#202124] truncate ${selectedTask.completed ? 'line-through text-stone-400' : ''}">
                                                ${escapeHTML(selectedTask.name)}
                                            </h2>"""

assert old_heading in content, "old_heading not found in planWorkspace.js"
content = content.replace(old_heading, new_heading)

with open('planWorkspace.js', 'wb') as f:
    f.write(content)

print("Applied updateTaskName & pw-task-detail-title enhancements successfully!")
