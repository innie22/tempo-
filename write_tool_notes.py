# -*- coding: utf-8 -*-

js_content = '''/**
 * Tempo Tool Notes
 * File: toolNotes.js
 *
 * Dedicated storage and manager for Tool Notes (Day Notes & Task Notes).
 * Integrates with Working Plan task cards, Tool Notes screen, URmode dashboard, and Focus Zone.
 */

window.TempoToolNotes = (function () {
    'use strict';

    // State for Note Creation Form on Tool Notes Page
    let currentCreationType = 'day'; // 'day' | 'task'
    let isSavingNote = false;

    // Active modal state
    let activeModalNoteId = null;

    // =========================================================================
    // 1. USER & STORAGE HELPERS
    // =========================================================================

    function getUserId() {
        if (typeof window !== 'undefined' && window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') {
            const uid = window.TempoAuth.getCurrentUserId();
            if (uid) return uid;
        }
        if (typeof window !== 'undefined' && window.TempoAuth && typeof window.TempoAuth.getUser === 'function') {
            const u = window.TempoAuth.getUser();
            if (u && u.id) return u.id;
        }
        try {
            const raw = localStorage.getItem('tempo_local_dev_user');
            if (raw) {
                const parsed = JSON.parse(raw);
                if (parsed && parsed.id) return parsed.id;
            }
        } catch (e) {}
        return 'local_user';
    }

    function getStorageKey() {
        const uid = getUserId();
        return `tempo_tool_notes_${uid}`;
    }

    function getSupabaseClient() {
        if (typeof window !== 'undefined' && window.TempoSupabase && typeof window.TempoSupabase.getClient === 'function') {
            return window.TempoSupabase.getClient();
        }
        return null;
    }

    // =========================================================================
    // 2. DATA PERSISTENCE & DUAL SYNC (LocalStorage + Supabase)
    // =========================================================================

    function loadNotes() {
        const uid = getUserId();
        const seenIds = new Set();
        const result = [];

        function addRaw(list) {
            if (!Array.isArray(list)) return;
            list.forEach(n => {
                if (!n) return;
                const noteId = String(n.id || (n.taskId ? 'task_' + n.taskId : Math.random().toString(36).substr(2)));
                if (!seenIds.has(noteId)) {
                    seenIds.add(noteId);
                    const isTask = !!(n.taskId || n.category === 'task' || n.type === 'task');
                    result.push({
                        id: noteId,
                        type: isTask ? 'task' : 'day',
                        category: isTask ? 'task' : 'day',
                        date: n.date || (n.createdAt ? getLocalDateStr(n.createdAt) : getTodayLocalDateStr()),
                        taskId: n.taskId ? String(n.taskId) : null,
                        taskName: n.taskName || (n.taskId ? `Task #${n.taskId}` : null),
                        title: n.title || (isTask ? `Note for ${n.taskName || 'Task'}` : `Day Note - ${n.date || getTodayLocalDateStr()}`),
                        text: (n.text || n.content || '').trim(),
                        content: (n.text || n.content || '').trim(),
                        user_id: n.user_id || uid,
                        createdAt: n.createdAt || new Date().toISOString(),
                        updatedAt: n.updatedAt || new Date().toISOString()
                    });
                }
            });
        }

        try {
            // Priority 1: User-scoped tool notes
            const rawUser = localStorage.getItem(`tempo_tool_notes_${uid}`);
            if (rawUser) addRaw(JSON.parse(rawUser));

            // Priority 2: User-scoped day notes
            const rawDay = localStorage.getItem(`tempo_day_notes_${uid}`);
            if (rawDay) addRaw(JSON.parse(rawDay));

            // Priority 3: Fallback keys
            const rawFallback = localStorage.getItem('tempo_tool_notes');
            if (rawFallback) addRaw(JSON.parse(rawFallback));
        } catch (e) {
            console.warn("[TempoToolNotes] Error loading notes:", e);
        }

        // Sort latest first
        result.sort((a, b) => {
            const timeA = new Date(a.updatedAt || a.createdAt || 0).getTime();
            const timeB = new Date(b.updatedAt || b.createdAt || 0).getTime();
            return timeB - timeA;
        });

        return result;
    }

    function saveNotes(notes) {
        const uid = getUserId();
        try {
            const key = `tempo_tool_notes_${uid}`;
            localStorage.setItem(key, JSON.stringify(notes));
            localStorage.setItem('tempo_tool_notes', JSON.stringify(notes));

            // Keep tempo_day_notes synchronized
            const dayNotes = notes.filter(n => !(n.taskId || n.category === 'task' || n.type === 'task'));
            localStorage.setItem(`tempo_day_notes_${uid}`, JSON.stringify(dayNotes));
            localStorage.setItem('tempo_day_notes', JSON.stringify(dayNotes));
        } catch (e) {
            console.warn("[TempoToolNotes] Error saving notes:", e);
        }
    }

    async function syncNoteToSupabase(note, action = 'upsert') {
        const sb = getSupabaseClient();
        if (!sb) return;
        try {
            const uid = getUserId();
            if (action === 'delete') {
                await sb.from('tool_notes').delete().eq('id', note.id);
            } else {
                const payload = {
                    id: note.id,
                    user_id: uid === 'local_user' ? null : uid,
                    type: note.type,
                    category: note.category,
                    date: note.date,
                    task_id: note.taskId,
                    task_name: note.taskName,
                    title: note.title,
                    content: note.text || note.content || '',
                    text: note.text || note.content || '',
                    updated_at: note.updatedAt || new Date().toISOString()
                };
                await sb.from('tool_notes').upsert(payload);
            }
        } catch (e) {
            console.warn("[TempoToolNotes] Supabase sync notice (local storage preserved):", e);
        }
    }

    // =========================================================================
    // 3. DATE & TIME UTILITIES
    // =========================================================================

    function getTodayLocalDateStr() {
        const now = new Date();
        const y = now.getFullYear();
        const m = String(now.getMonth() + 1).padStart(2, '0');
        const d = String(now.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    }

    function getLocalDateStr(d) {
        if (!d) return '';
        try {
            if (typeof d === 'string' && d.length === 10 && d.includes('-') && !d.includes('T')) {
                return d;
            }
            const dateObj = new Date(d);
            if (!isNaN(dateObj.getTime())) {
                const y = dateObj.getFullYear();
                const m = String(dateObj.getMonth() + 1).padStart(2, '0');
                const day = String(dateObj.getDate()).padStart(2, '0');
                return `${y}-${m}-${day}`;
            }
        } catch (e) {}
        if (typeof d === 'string') {
            if (d.includes('T')) return d.split('T')[0];
            return d.substring(0, 10);
        }
        return '';
    }

    function formatDisplayDate(dateStr) {
        if (!dateStr) return 'Unspecified Date';
        const today = getTodayLocalDateStr();
        const now = new Date();
        const yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayStr = getLocalDateStr(yesterday);

        let parsed;
        try {
            const parts = dateStr.split('-');
            if (parts.length === 3) {
                parsed = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
            } else {
                parsed = new Date(dateStr);
            }
        } catch (e) {
            parsed = new Date(dateStr);
        }

        const dateFormatted = !isNaN(parsed.getTime())
            ? parsed.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
            : dateStr;

        if (dateStr === today) {
            return `Today • ${dateFormatted}`;
        }
        if (dateStr === yesterdayStr) {
            return `Yesterday • ${dateFormatted}`;
        }
        return dateFormatted;
    }

    function formatNoteTime(note) {
        if (!note) return '';
        if (note.time) return note.time;
        const iso = note.updatedAt || note.createdAt;
        if (iso) {
            try {
                const d = new Date(iso);
                if (!isNaN(d.getTime())) {
                    let hours = d.getHours();
                    const minutes = String(d.getMinutes()).padStart(2, '0');
                    const ampm = hours >= 12 ? 'PM' : 'AM';
                    hours = hours % 12;
                    hours = hours ? hours : 12;
                    return `${hours}:${minutes} ${ampm}`;
                }
            } catch (e) {}
        }
        return '';
    }

    function escapeHTML(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // =========================================================================
    // 4. TASK AGGREGATION & PLAN SYNCHRONIZATION
    // =========================================================================

    function getAvailableTasks() {
        const uid = getUserId();
        const tasksMap = new Map();

        // 1. From TempoEmergencyFlow getTasks()
        if (typeof window !== 'undefined' && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getTasks === 'function') {
            try {
                const efTasks = window.TempoEmergencyFlow.getTasks() || [];
                efTasks.forEach(t => {
                    if (t && t.id) {
                        tasksMap.set(String(t.id), {
                            id: String(t.id),
                            name: t.name || t.title || `Task ${t.id}`,
                            deadlineDate: t.deadlineDate || t.deadline || null,
                            priority: t.priorityCategory || t.importance || null,
                            completed: !!t.completed
                        });
                    }
                });
            } catch (e) {}
        }

        // 2. From confirmedPlan plannedTasks
        if (typeof window !== 'undefined' && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            try {
                const plan = window.TempoEmergencyFlow.getConfirmedPlan();
                if (plan && Array.isArray(plan.plannedTasks)) {
                    plan.plannedTasks.forEach(pt => {
                        const t = pt.task || pt;
                        if (t && t.id && !tasksMap.has(String(t.id))) {
                            tasksMap.set(String(t.id), {
                                id: String(t.id),
                                name: t.name || t.title || `Task ${t.id}`,
                                deadlineDate: t.deadlineDate || pt.dayDate || null,
                                priority: t.priorityCategory || null,
                                completed: !!t.completed
                            });
                        }
                    });
                }
            } catch (e) {}
        }

        // 3. From PlanStore active plan
        if (typeof window !== 'undefined' && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            try {
                const plan = window.TempoPlanStore.getActivePlan('emergency');
                if (plan && Array.isArray(plan.plannedTasks)) {
                    plan.plannedTasks.forEach(pt => {
                        const t = pt.task || pt;
                        if (t && t.id && !tasksMap.has(String(t.id))) {
                            tasksMap.set(String(t.id), {
                                id: String(t.id),
                                name: t.name || t.title || `Task ${t.id}`,
                                deadlineDate: t.deadlineDate || pt.dayDate || null,
                                priority: t.priorityCategory || null,
                                completed: !!t.completed
                            });
                        }
                    });
                }
            } catch (e) {}
        }

        // 4. From LocalStorage tempo_tasks_${uid}
        try {
            const rawTasks = localStorage.getItem(`tempo_tasks_${uid}`);
            if (rawTasks) {
                const parsed = JSON.parse(rawTasks);
                if (Array.isArray(parsed)) {
                    parsed.forEach(t => {
                        if (t && t.id && !tasksMap.has(String(t.id))) {
                            tasksMap.set(String(t.id), {
                                id: String(t.id),
                                name: t.name || t.title || `Task ${t.id}`,
                                deadlineDate: t.deadlineDate || null,
                                priority: t.priorityCategory || null,
                                completed: !!t.completed
                            });
                        }
                    });
                }
            }
        } catch (e) {}

        return Array.from(tasksMap.values());
    }

    function syncTaskInPlans(taskId, noteText) {
        if (!taskId) return;
        const sId = String(taskId);

        // 1. Sync in TempoEmergencyFlow
        if (typeof window !== 'undefined' && window.TempoEmergencyFlow) {
            const confirmedPlan = typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function' ? window.TempoEmergencyFlow.getConfirmedPlan() : null;
            if (confirmedPlan && Array.isArray(confirmedPlan.plannedTasks)) {
                const pt = confirmedPlan.plannedTasks.find(item => item.task && String(item.task.id) === sId);
                if (pt && pt.task) {
                    pt.task.note = noteText;
                    pt.task.description = noteText;
                }
            }
            if (typeof window.TempoEmergencyFlow.getTasks === 'function') {
                const tasks = window.TempoEmergencyFlow.getTasks();
                const t = tasks.find(item => String(item.id) === sId);
                if (t) {
                    t.note = noteText;
                    t.description = noteText;
                }
            }
        }

        // 2. Sync in TempoPlanStore
        if (typeof window !== 'undefined' && window.TempoPlanStore) {
            const activePlan = typeof window.TempoPlanStore.getActivePlan === 'function' ? window.TempoPlanStore.getActivePlan('emergency') : null;
            if (activePlan && Array.isArray(activePlan.plannedTasks)) {
                const pt = activePlan.plannedTasks.find(item => item.task && String(item.task.id) === sId);
                if (pt && pt.task) {
                    pt.task.note = noteText;
                    pt.task.description = noteText;
                }
                if (typeof window.TempoPlanStore.saveActivePlan === 'function') {
                    window.TempoPlanStore.saveActivePlan('emergency', activePlan);
                }
            }
        }

        // 3. Refresh Plan Workspace & Focus Zone if open
        if (typeof window !== 'undefined' && window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
        }
        if (typeof window !== 'undefined' && window.TempoFocusZone && typeof window.TempoFocusZone.render === 'function') {
            window.TempoFocusZone.render();
        }
    }

    // =========================================================================
    // 5. NOTE OPERATIONS (CRUD)
    // =========================================================================

    function getNotes() {
        return loadNotes();
    }

    function getDayNotes(dateStr) {
        const notes = loadNotes();
        return notes.filter(n => {
            const isTask = !!(n.taskId || n.category === 'task' || n.type === 'task');
            if (isTask) return false;
            if (dateStr) {
                return (n.date && String(n.date).slice(0, 10) === dateStr) ||
                       (n.createdAt && getLocalDateStr(n.createdAt) === dateStr);
            }
            return true;
        });
    }

    function getTaskNotes() {
        const notes = loadNotes();
        return notes.filter(n => !!(n.taskId || n.category === 'task' || n.type === 'task'));
    }

    function getNoteById(noteId) {
        if (!noteId) return null;
        const notes = loadNotes();
        return notes.find(n => String(n.id) === String(noteId)) || null;
    }

    function saveDayNote(text, dateStr, existingNoteId) {
        const trimmed = (text || '').trim();
        if (!trimmed) return null;

        const targetDate = dateStr ? getLocalDateStr(dateStr) : getTodayLocalDateStr();
        const now = new Date();
        const nowIso = now.toISOString();
        const notes = loadNotes();
        const uid = getUserId();

        let savedNote = null;

        if (existingNoteId) {
            const idx = notes.findIndex(n => String(n.id) === String(existingNoteId));
            if (idx !== -1) {
                notes[idx].text = trimmed;
                notes[idx].content = trimmed;
                notes[idx].date = targetDate;
                notes[idx].title = `Day Note - ${targetDate}`;
                notes[idx].updatedAt = nowIso;
                savedNote = notes[idx];
            }
        }

        if (!savedNote) {
            savedNote = {
                id: 'day_note_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
                type: 'day',
                category: 'day',
                date: targetDate,
                text: trimmed,
                content: trimmed,
                title: `Day Note - ${targetDate}`,
                user_id: uid,
                createdAt: nowIso,
                updatedAt: nowIso
            };
            notes.unshift(savedNote);
        }

        saveNotes(notes);
        syncNoteToSupabase(savedNote, 'upsert');

        if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('tempo:note-updated', { detail: { note: savedNote, type: 'day' } }));
        }

        renderToolNotesPage();

        if (typeof window !== 'undefined' && window.TempoMode && typeof window.TempoMode.refreshNotesCardIfPresent === 'function') {
            window.TempoMode.refreshNotesCardIfPresent();
        }

        return savedNote;
    }

    function saveTaskNote(taskId, taskName, text, existingNoteId) {
        const trimmed = (text || '').trim();
        const sId = taskId ? String(taskId) : null;
        if (!sId || !trimmed) return null;

        const now = new Date();
        const nowIso = now.toISOString();
        const notes = loadNotes();
        const uid = getUserId();

        let savedNote = null;

        if (existingNoteId) {
            const idx = notes.findIndex(n => String(n.id) === String(existingNoteId));
            if (idx !== -1) {
                notes[idx].taskId = sId;
                notes[idx].taskName = taskName || notes[idx].taskName || 'Academic Task';
                notes[idx].title = `Note for ${notes[idx].taskName}`;
                notes[idx].text = trimmed;
                notes[idx].content = trimmed;
                notes[idx].updatedAt = nowIso;
                savedNote = notes[idx];
            }
        }

        if (!savedNote) {
            const existingTaskNoteIdx = notes.findIndex(n => String(n.taskId) === sId);
            if (existingTaskNoteIdx !== -1) {
                notes[existingTaskNoteIdx].text = trimmed;
                notes[existingTaskNoteIdx].content = trimmed;
                notes[existingTaskNoteIdx].taskName = taskName || notes[existingTaskNoteIdx].taskName || 'Academic Task';
                notes[existingTaskNoteIdx].title = `Note for ${notes[existingTaskNoteIdx].taskName}`;
                notes[existingTaskNoteIdx].updatedAt = nowIso;
                savedNote = notes[existingTaskNoteIdx];
            } else {
                savedNote = {
                    id: 'tool_note_task_' + sId + '_' + Date.now().toString(36),
                    taskId: sId,
                    taskName: taskName || 'Academic Task',
                    title: `Note for ${taskName || 'Academic Task'}`,
                    type: 'task',
                    category: 'task',
                    date: getTodayLocalDateStr(),
                    text: trimmed,
                    content: trimmed,
                    user_id: uid,
                    createdAt: nowIso,
                    updatedAt: nowIso
                };
                notes.unshift(savedNote);
            }
        }

        saveNotes(notes);
        syncTaskInPlans(sId, trimmed);
        syncNoteToSupabase(savedNote, 'upsert');

        if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('tempo:note-updated', { detail: { note: savedNote, type: 'task' } }));
        }

        renderToolNotesPage();

        if (typeof window !== 'undefined' && window.TempoMode && typeof window.TempoMode.refreshNotesCardIfPresent === 'function') {
            window.TempoMode.refreshNotesCardIfPresent();
        }

        return savedNote;
    }

    function updateNote(noteId, updates) {
        if (!noteId || !updates) return null;
        const notes = loadNotes();
        const idx = notes.findIndex(n => String(n.id) === String(noteId));
        if (idx === -1) return null;

        const nowIso = new Date().toISOString();
        const n = notes[idx];

        if (typeof updates.text === 'string') {
            n.text = updates.text.trim();
            n.content = n.text;
        }
        if (typeof updates.date === 'string') {
            n.date = getLocalDateStr(updates.date);
            if (n.type === 'day') {
                n.title = `Day Note - ${n.date}`;
            }
        }
        if (updates.taskId) {
            n.taskId = String(updates.taskId);
            if (updates.taskName) n.taskName = updates.taskName;
            n.title = `Note for ${n.taskName || 'Academic Task'}`;
            syncTaskInPlans(n.taskId, n.text);
        }
        n.updatedAt = nowIso;

        saveNotes(notes);
        syncNoteToSupabase(n, 'upsert');

        if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('tempo:note-updated', { detail: { note: n, action: 'update' } }));
        }

        renderToolNotesPage();

        if (typeof window !== 'undefined' && window.TempoMode && typeof window.TempoMode.refreshNotesCardIfPresent === 'function') {
            window.TempoMode.refreshNotesCardIfPresent();
        }

        return n;
    }

    function deleteNote(noteId) {
        if (!noteId) return;
        const sId = String(noteId);
        const notes = loadNotes();
        const noteToDelete = notes.find(n => String(n.id) === sId);
        const filtered = notes.filter(n => String(n.id) !== sId);
        saveNotes(filtered);

        if (noteToDelete) {
            if (noteToDelete.taskId) {
                syncTaskInPlans(noteToDelete.taskId, '');
            }
            syncNoteToSupabase(noteToDelete, 'delete');
        }

        if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('tempo:note-updated', { detail: { noteId: sId, action: 'delete' } }));
        }

        renderToolNotesPage();

        if (typeof window !== 'undefined' && window.TempoMode && typeof window.TempoMode.refreshNotesCardIfPresent === 'function') {
            window.TempoMode.refreshNotesCardIfPresent();
        }
    }

    function deleteDayNote(noteId) {
        deleteNote(noteId);
    }

    function deleteTaskNote(taskId) {
        if (!taskId) return;
        const notes = loadNotes();
        const note = notes.find(n => String(n.taskId) === String(taskId));
        if (note) {
            deleteNote(note.id);
        }
    }

    // =========================================================================
    // 6. UI CREATION FORM HANDLERS
    // =========================================================================

    function setCreationType(type) {
        currentCreationType = (type === 'task') ? 'task' : 'day';

        const pillDay = document.getElementById('pill-type-day');
        const pillTask = document.getElementById('pill-type-task');
        const groupDate = document.getElementById('form-group-day-date');
        const groupTask = document.getElementById('form-group-task-select');
        const textarea = document.getElementById('textarea-note-content');

        if (pillDay && pillTask) {
            if (currentCreationType === 'day') {
                pillDay.className = "px-4 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer bg-[#C88E7D] text-white shadow-2xs";
                pillTask.className = "px-4 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer text-[#6F6B68] hover:text-[#202124]";
            } else {
                pillTask.className = "px-4 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer bg-[#C88E7D] text-white shadow-2xs";
                pillDay.className = "px-4 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer text-[#6F6B68] hover:text-[#202124]";
            }
        }

        if (groupDate) {
            groupDate.className = currentCreationType === 'day' ? 'block space-y-1.5' : 'hidden';
        }
        if (groupTask) {
            groupTask.className = currentCreationType === 'task' ? 'block space-y-1.5' : 'hidden';
        }
        if (textarea) {
            textarea.placeholder = currentCreationType === 'day'
                ? 'Write reflections, reminders, or general observations for the day...'
                : 'Write notes, research links, outlines, or next action steps for this task...';
        }

        const feedback = document.getElementById('create-note-feedback');
        if (feedback) feedback.innerHTML = '';
    }

    function handleCreateFormSubmit() {
        if (isSavingNote) return;

        const textarea = document.getElementById('textarea-note-content');
        const content = textarea ? textarea.value.trim() : '';
        const feedback = document.getElementById('create-note-feedback');
        const submitBtn = document.getElementById('btn-save-note-submit');

        if (!content) {
            if (feedback) {
                feedback.innerHTML = `<span class="text-rose-600 font-bold">⚠️ Please enter some note content before saving.</span>`;
            }
            if (textarea) textarea.focus();
            return;
        }

        if (currentCreationType === 'day') {
            const dateInput = document.getElementById('input-note-date');
            const dateVal = dateInput ? dateInput.value.trim() : getTodayLocalDateStr();
            if (!dateVal) {
                if (feedback) {
                    feedback.innerHTML = `<span class="text-rose-600 font-bold">⚠️ Please select a valid date.</span>`;
                }
                return;
            }

            isSavingNote = true;
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.classList.add('opacity-70', 'cursor-not-allowed');
                submitBtn.innerHTML = `<span>Saving...</span>`;
            }

            try {
                saveDayNote(content, dateVal);
                if (textarea) textarea.value = '';
                if (feedback) {
                    feedback.innerHTML = `<span class="text-emerald-700 font-bold">✓ Day Note saved successfully!</span>`;
                }
                setTimeout(() => {
                    if (feedback) feedback.innerHTML = '';
                }, 2500);
            } catch (err) {
                if (feedback) {
                    feedback.innerHTML = `<span class="text-rose-600 font-bold">❌ Error saving note: ${escapeHTML(err.message)}</span>`;
                }
            } finally {
                isSavingNote = false;
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('opacity-70', 'cursor-not-allowed');
                    submitBtn.innerHTML = `<span>Save Note</span>`;
                }
            }
        } else {
            const taskSelect = document.getElementById('select-note-task');
            const taskId = taskSelect ? taskSelect.value.trim() : '';
            if (!taskId) {
                if (feedback) {
                    feedback.innerHTML = `<span class="text-rose-600 font-bold">⚠️ Please select an associated task.</span>`;
                }
                return;
            }
            const taskName = taskSelect.options[taskSelect.selectedIndex]?.text || 'Academic Task';

            isSavingNote = true;
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.classList.add('opacity-70', 'cursor-not-allowed');
                submitBtn.innerHTML = `<span>Saving...</span>`;
            }

            try {
                saveTaskNote(taskId, taskName, content);
                if (textarea) textarea.value = '';
                if (feedback) {
                    feedback.innerHTML = `<span class="text-emerald-700 font-bold">✓ Task Note saved successfully!</span>`;
                }
                setTimeout(() => {
                    if (feedback) feedback.innerHTML = '';
                }, 2500);
            } catch (err) {
                if (feedback) {
                    feedback.innerHTML = `<span class="text-rose-600 font-bold">❌ Error saving task note: ${escapeHTML(err.message)}</span>`;
                }
            } finally {
                isSavingNote = false;
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('opacity-70', 'cursor-not-allowed');
                    submitBtn.innerHTML = `<span>Save Note</span>`;
                }
            }
        }
    }

    function resetCreateForm() {
        const textarea = document.getElementById('textarea-note-content');
        if (textarea) textarea.value = '';
        const feedback = document.getElementById('create-note-feedback');
        if (feedback) feedback.innerHTML = '';
    }

    // =========================================================================
    // 7. MODALS & POPUPS (Detail, Edit, and Create Popups)
    // =========================================================================

    function getOrCreateModalRoot() {
        let root = document.getElementById('tool-notes-modal-root');
        if (!root) {
            root = document.createElement('div');
            root.id = 'tool-notes-modal-root';
            document.body.appendChild(root);
        }
        return root;
    }

    function closeModal() {
        const root = document.getElementById('tool-notes-modal-root');
        if (root) root.innerHTML = '';
        activeModalNoteId = null;
    }

    function openNoteDetailModal(noteId) {
        if (!noteId) return;
        const note = getNoteById(noteId);
        if (!note) return;

        activeModalNoteId = String(note.id);
        const root = getOrCreateModalRoot();
        const isTask = note.type === 'task' || !!note.taskId;

        const formattedDate = formatDisplayDate(note.date);
        const timeStr = formatNoteTime(note);
        const noteText = escapeHTML(note.text || note.content || '');

        root.innerHTML = `
            <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs transition-opacity" 
                 id="note-detail-backdrop"
                 onclick="if (event.target === this) window.TempoToolNotes.closeModal();">
                <div class="bg-white border border-[#EAE4DF] rounded-3xl max-w-lg w-full p-6 sm:p-7 shadow-xl space-y-5 animate-in fade-in zoom-in-95 relative" 
                     role="dialog" 
                     aria-modal="true"
                     aria-labelledby="note-detail-title">
                    
                    <!-- Header -->
                    <div class="flex items-start justify-between gap-3 pb-3 border-b border-stone-100">
                        <div class="space-y-1 min-w-0">
                            <div class="flex items-center space-x-2">
                                <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold ${isTask ? 'bg-[#FEF3C7] text-[#92400E]' : 'bg-[#F9E8E2] text-[#B87561]'} uppercase tracking-wider">
                                    ${isTask ? '📋 Task Note' : '📝 Day Note'}
                                </span>
                                ${timeStr ? `<span class="text-xs text-[#8C827A] font-medium">${escapeHTML(timeStr)}</span>` : ''}
                            </div>
                            <h3 id="note-detail-title" class="font-heading text-lg sm:text-xl font-bold text-[#202124] truncate">
                                ${isTask ? `📌 ${escapeHTML(note.taskName || 'Academic Task')}` : `📅 ${escapeHTML(formattedDate)}`}
                            </h3>
                        </div>
                        <button type="button" 
                                onclick="window.TempoToolNotes.closeModal()"
                                class="text-stone-400 hover:text-stone-700 w-8 h-8 rounded-full flex items-center justify-center hover:bg-stone-100 transition cursor-pointer shrink-0"
                                aria-label="Close note popup">
                            ✕
                        </button>
                    </div>

                    <!-- Complete Note Content (Untruncated) -->
                    <div class="space-y-2">
                        <span class="text-xs font-bold uppercase tracking-wider text-[#8C827A]">Full Content</span>
                        <div class="bg-[#FAF7F4] border border-stone-200/70 rounded-2xl p-4 max-h-[360px] overflow-y-auto custom-scrollbar">
                            <p class="whitespace-pre-wrap text-xs sm:text-sm text-[#332F2C] leading-relaxed break-words font-medium">
                                ${noteText}
                            </p>
                        </div>
                    </div>

                    <!-- Timestamps -->
                    <div class="flex items-center justify-between text-[11px] text-[#8C827A] pt-1">
                        <span>Created: ${note.createdAt ? new Date(note.createdAt).toLocaleDateString() : 'N/A'}</span>
                        <span>Updated: ${note.updatedAt ? new Date(note.updatedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A'}</span>
                    </div>

                    <!-- Footer Actions -->
                    <div class="flex items-center justify-between pt-3 border-t border-stone-100">
                        <button type="button"
                                onclick="window.TempoToolNotes.confirmDeleteNote('${escapeHTML(String(note.id))}')"
                                class="px-4 py-2 rounded-xl text-xs font-bold text-rose-600 hover:text-white hover:bg-rose-600 border border-rose-200 hover:border-rose-600 transition cursor-pointer inline-flex items-center gap-1.5">
                            <span>🗑️ Delete</span>
                        </button>
                        <div class="flex items-center space-x-2">
                            <button type="button"
                                    onclick="window.TempoToolNotes.closeModal()"
                                    class="px-4 py-2 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] hover:bg-stone-100 transition cursor-pointer">
                                Close
                            </button>
                            <button type="button"
                                    onclick="window.TempoToolNotes.openNoteEditModal('${escapeHTML(String(note.id))}')"
                                    class="px-5 py-2 rounded-xl font-bold text-xs bg-[#C88E7D] hover:bg-[#B97F6E] text-white shadow-2xs transition cursor-pointer inline-flex items-center gap-1.5">
                                <span>✏️ Edit Note</span>
                            </button>
                        </div>
                    </div>

                </div>
            </div>
        `;
    }

    function confirmDeleteNote(noteId) {
        if (!noteId) return;
        const note = getNoteById(noteId);
        if (!note) return;

        const isTask = note.type === 'task' || !!note.taskId;
        const confirmMsg = isTask 
            ? `Are you sure you want to delete this task note for "${note.taskName || 'Academic Task'}"?` 
            : `Are you sure you want to delete this day note for ${note.date || 'today'}?`;

        if (window.confirm(confirmMsg)) {
            deleteNote(noteId);
            closeModal();
        }
    }

    function openNoteEditModal(noteId) {
        if (!noteId) return;
        const note = getNoteById(noteId);
        if (!note) return;

        const root = getOrCreateModalRoot();
        const isTask = note.type === 'task' || !!note.taskId;
        const availableTasks = getAvailableTasks();
        const noteDate = note.date || getTodayLocalDateStr();

        root.innerHTML = `
            <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs transition-opacity" 
                 id="note-edit-backdrop"
                 onclick="if (event.target === this) window.TempoToolNotes.closeModal();">
                <div class="bg-white border border-[#EAE4DF] rounded-3xl max-w-lg w-full p-6 sm:p-7 shadow-xl space-y-4 animate-in fade-in zoom-in-95 relative" 
                     role="dialog" 
                     aria-modal="true">
                    
                    <!-- Header -->
                    <div class="flex items-center justify-between pb-3 border-b border-stone-100">
                        <div class="flex items-center space-x-2">
                            <span class="text-lg">✏️</span>
                            <h3 class="font-heading text-lg font-bold text-[#202124]">Edit Note</h3>
                        </div>
                        <button type="button" 
                                onclick="window.TempoToolNotes.closeModal()"
                                class="text-stone-400 hover:text-stone-700 w-8 h-8 rounded-full flex items-center justify-center hover:bg-stone-100 transition cursor-pointer">
                            ✕
                        </button>
                    </div>

                    <!-- Edit Form -->
                    <form onsubmit="event.preventDefault(); window.TempoToolNotes.handleSaveEditSubmit('${escapeHTML(String(note.id))}');" class="space-y-4">
                        ${!isTask ? `
                            <div class="space-y-1.5">
                                <label for="edit-note-date" class="block text-xs font-bold text-[#554741]">Calendar Date</label>
                                <input type="date" 
                                       id="edit-note-date" 
                                       value="${escapeHTML(noteDate)}"
                                       class="w-full px-3.5 py-2 text-xs sm:text-sm rounded-xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white" />
                            </div>
                        ` : `
                            <div class="space-y-1.5">
                                <label for="edit-note-task" class="block text-xs font-bold text-[#554741]">Associated Academic Task</label>
                                <select id="edit-note-task" 
                                        class="w-full px-3.5 py-2 text-xs sm:text-sm rounded-xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white">
                                    ${availableTasks.length === 0 ? `
                                        <option value="${escapeHTML(note.taskId || 'current')}" selected>${escapeHTML(note.taskName || 'Current Task')}</option>
                                    ` : availableTasks.map(t => `
                                        <option value="${escapeHTML(t.id)}" ${String(t.id) === String(note.taskId) ? 'selected' : ''}>${escapeHTML(t.name)}${t.deadlineDate ? ` (Due ${t.deadlineDate})` : ''}</option>
                                    `).join('')}
                                </select>
                            </div>
                        `}

                        <div class="space-y-1.5">
                            <label for="edit-note-content" class="block text-xs font-bold text-[#554741]">Note Content</label>
                            <textarea id="edit-note-content" 
                                      rows="4" 
                                      class="w-full p-3.5 text-xs sm:text-sm rounded-2xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white resize-y min-h-[110px] leading-relaxed">${escapeHTML(note.text || note.content || '')}</textarea>
                        </div>

                        <div id="edit-note-feedback" class="text-xs font-semibold text-rose-600 min-h-[16px]"></div>

                        <div class="flex items-center justify-end space-x-2 pt-2 border-t border-stone-100">
                            <button type="button" 
                                    onclick="window.TempoToolNotes.openNoteDetailModal('${escapeHTML(String(note.id))}')"
                                    class="px-4 py-2 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] hover:bg-stone-100 transition cursor-pointer">
                                Back to Details
                            </button>
                            <button type="submit" 
                                    class="px-5 py-2 rounded-xl font-bold text-xs bg-[#C88E7D] hover:bg-[#B97F6E] text-white shadow-2xs transition cursor-pointer">
                                Save Changes
                            </button>
                        </div>
                    </form>

                </div>
            </div>
        `;
    }

    function handleSaveEditSubmit(noteId) {
        if (!noteId) return;
        const note = getNoteById(noteId);
        if (!note) return;

        const isTask = note.type === 'task' || !!note.taskId;
        const textarea = document.getElementById('edit-note-content');
        const content = textarea ? textarea.value.trim() : '';
        const feedback = document.getElementById('edit-note-feedback');

        if (!content) {
            if (feedback) feedback.innerText = 'Please enter note content.';
            return;
        }

        const updates = { text: content };

        if (!isTask) {
            const dateInput = document.getElementById('edit-note-date');
            if (dateInput && dateInput.value) {
                updates.date = dateInput.value.trim();
            }
        } else {
            const taskSelect = document.getElementById('edit-note-task');
            if (taskSelect && taskSelect.value) {
                updates.taskId = taskSelect.value.trim();
                updates.taskName = taskSelect.options[taskSelect.selectedIndex]?.text || note.taskName;
            }
        }

        updateNote(noteId, updates);
        openNoteDetailModal(noteId);
    }

    function openCreateNoteModal(defaultType = 'day', defaultDate = null) {
        const root = getOrCreateModalRoot();
        const availableTasks = getAvailableTasks();
        const initialDate = defaultDate ? getLocalDateStr(defaultDate) : getTodayLocalDateStr();
        let selectedType = defaultType === 'task' ? 'task' : 'day';

        function renderModalBody() {
            root.innerHTML = `
                <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs transition-opacity" 
                     id="note-create-backdrop"
                     onclick="if (event.target === this) window.TempoToolNotes.closeModal();">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl max-w-lg w-full p-6 sm:p-7 shadow-xl space-y-4 animate-in fade-in zoom-in-95 relative" 
                         role="dialog" 
                         aria-modal="true">
                        
                        <!-- Header -->
                        <div class="flex items-center justify-between pb-3 border-b border-stone-100">
                            <div class="flex items-center space-x-2">
                                <span class="text-xl">✏️</span>
                                <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124]">Create a Note</h3>
                            </div>
                            <button type="button" 
                                    onclick="window.TempoToolNotes.closeModal()"
                                    class="text-stone-400 hover:text-stone-700 w-8 h-8 rounded-full flex items-center justify-center hover:bg-stone-100 transition cursor-pointer">
                                ✕
                            </button>
                        </div>

                        <!-- Type Selector Pills -->
                        <div class="flex items-center justify-center">
                            <div class="inline-flex p-1 bg-[#FAF7F4] border border-[#EAE4DF] rounded-2xl space-x-1">
                                <button type="button" 
                                        id="modal-pill-day"
                                        class="px-4 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${selectedType === 'day' ? 'bg-[#C88E7D] text-white shadow-2xs' : 'text-[#6F6B68] hover:text-[#202124]'}">
                                    📝 Day Note
                                </button>
                                <button type="button" 
                                        id="modal-pill-task"
                                        class="px-4 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${selectedType === 'task' ? 'bg-[#C88E7D] text-white shadow-2xs' : 'text-[#6F6B68] hover:text-[#202124]'}">
                                    📋 Task Note
                                </button>
                            </div>
                        </div>

                        <!-- Form -->
                        <form id="modal-create-note-form" class="space-y-4">
                            <!-- Day Note Date Field -->
                            <div id="modal-group-date" class="${selectedType === 'day' ? 'block' : 'hidden'} space-y-1.5">
                                <label for="modal-input-date" class="block text-xs font-bold text-[#554741]">Calendar Date</label>
                                <input type="date" 
                                       id="modal-input-date" 
                                       value="${escapeHTML(initialDate)}"
                                       class="w-full px-3.5 py-2 text-xs sm:text-sm rounded-xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white" />
                                <p class="text-[11px] text-[#8C827A]">Prefilled with today's date. You can change it if creating for another day.</p>
                            </div>

                            <!-- Task Note Selector Field -->
                            <div id="modal-group-task" class="${selectedType === 'task' ? 'block' : 'hidden'} space-y-1.5">
                                <label for="modal-select-task" class="block text-xs font-bold text-[#554741]">Associated Academic Task</label>
                                <select id="modal-select-task" 
                                        class="w-full px-3.5 py-2 text-xs sm:text-sm rounded-xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white">
                                    <option value="" disabled selected>-- Select a task from your plan --</option>
                                    ${availableTasks.length === 0 ? `
                                        <option value="" disabled>No active tasks in your plan</option>
                                    ` : availableTasks.map(t => `
                                        <option value="${escapeHTML(t.id)}">${escapeHTML(t.name)}${t.deadlineDate ? ` (Due ${t.deadlineDate})` : ''}</option>
                                    `).join('')}
                                </select>
                            </div>

                            <!-- Note Content Textarea -->
                            <div class="space-y-1.5">
                                <label for="modal-textarea-content" class="block text-xs font-bold text-[#554741]">Note Content</label>
                                <textarea id="modal-textarea-content" 
                                          rows="3" 
                                          placeholder="${selectedType === 'day' ? 'Write reflections, reminders, or general observations for the day...' : 'Write research notes, outlines, or next action steps for this task...'}"
                                          class="w-full p-3.5 text-xs sm:text-sm rounded-2xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white resize-y min-h-[90px]"></textarea>
                            </div>

                            <div id="modal-create-feedback" class="text-xs font-semibold text-rose-600 min-h-[16px]"></div>

                            <!-- Actions -->
                            <div class="flex items-center justify-end space-x-2 pt-2 border-t border-stone-100">
                                <button type="button" 
                                        onclick="window.TempoToolNotes.closeModal()"
                                        class="px-4 py-2 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] hover:bg-stone-100 transition cursor-pointer">
                                    Cancel
                                </button>
                                <button type="submit" 
                                        id="modal-btn-submit"
                                        class="px-5 py-2 rounded-xl font-bold text-xs bg-[#C88E7D] hover:bg-[#B97F6E] text-white shadow-2xs transition cursor-pointer">
                                    Save Note
                                </button>
                            </div>
                        </form>

                    </div>
                </div>
            `;

            // Attach pill click events
            const pDay = document.getElementById('modal-pill-day');
            const pTask = document.getElementById('modal-pill-task');
            if (pDay) pDay.onclick = () => { selectedType = 'day'; renderModalBody(); };
            if (pTask) pTask.onclick = () => { selectedType = 'task'; renderModalBody(); };

            // Attach form submission
            const form = document.getElementById('modal-create-note-form');
            if (form) {
                form.onsubmit = (e) => {
                    e.preventDefault();
                    const ta = document.getElementById('modal-textarea-content');
                    const textVal = ta ? ta.value.trim() : '';
                    const fb = document.getElementById('modal-create-feedback');
                    if (!textVal) {
                        if (fb) fb.innerText = 'Please enter note content.';
                        if (ta) ta.focus();
                        return;
                    }

                    if (selectedType === 'day') {
                        const dInput = document.getElementById('modal-input-date');
                        const dVal = dInput ? dInput.value.trim() : getTodayLocalDateStr();
                        if (!dVal) {
                            if (fb) fb.innerText = 'Please select a date.';
                            return;
                        }
                        saveDayNote(textVal, dVal);
                    } else {
                        const tSelect = document.getElementById('modal-select-task');
                        const tId = tSelect ? tSelect.value.trim() : '';
                        if (!tId) {
                            if (fb) fb.innerText = 'Please select an associated task.';
                            return;
                        }
                        const tName = tSelect.options[tSelect.selectedIndex]?.text || 'Academic Task';
                        saveTaskNote(tId, tName, textVal);
                    }
                    closeModal();
                };
            }
        }

        renderModalBody();
    }

    // =========================================================================
    // 8. TOOL NOTES PAGE RENDERER (Full Workspace)
    // =========================================================================

    function renderDayNotesListHTML(dayNotes) {
        if (!dayNotes || dayNotes.length === 0) {
            return `
                <div class="py-12 px-4 text-center space-y-3 bg-[#FAF7F4] border border-dashed border-stone-200 rounded-2xl" data-tempo-ui="day-notes-empty">
                    <div class="w-10 h-10 mx-auto rounded-xl bg-[#F9E8E2] text-[#B87561] flex items-center justify-center text-lg shadow-2xs">📝</div>
                    <div class="space-y-1">
                        <h4 class="font-heading text-sm font-bold text-[#202124]">No day notes yet.</h4>
                        <p class="text-xs text-[#6F6B68] max-w-xs mx-auto">Track thoughts, energy levels, or gentle reflections for any day.</p>
                    </div>
                    <button type="button" 
                            onclick="window.TempoToolNotes.setCreationType('day'); const ta = document.getElementById('textarea-note-content'); if (ta) { ta.scrollIntoView({ behavior: 'smooth', block: 'center' }); ta.focus(); }" 
                            class="px-3.5 py-1.5 rounded-xl font-bold text-xs bg-[#C88E7D] hover:bg-[#B97F6E] text-white shadow-2xs transition cursor-pointer">
                        + Add a Day Note
                    </button>
                </div>
            `;
        }

        // Group notes by date
        const groups = {};
        dayNotes.forEach(n => {
            const d = n.date || (n.createdAt ? getLocalDateStr(n.createdAt) : 'Other');
            if (!groups[d]) groups[d] = [];
            groups[d].push(n);
        });

        const sortedDates = Object.keys(groups).sort((a, b) => b.localeCompare(a));

        return sortedDates.map(dateKey => {
            const dateNotes = groups[dateKey];
            const headerLabel = formatDisplayDate(dateKey);

            return `
                <div class="space-y-2" data-date-group="${escapeHTML(dateKey)}">
                    <!-- Date Header -->
                    <div class="flex items-center space-x-2 text-xs font-bold text-[#554741] sticky top-0 bg-white/95 backdrop-blur-2xs py-1 z-10 border-b border-stone-100">
                        <span class="text-[#B87561]">📅</span>
                        <span>${escapeHTML(headerLabel)}</span>
                        <span class="text-[10px] text-[#8C827A] font-medium">(${dateNotes.length})</span>
                    </div>

                    <!-- Cards in this group -->
                    <div class="space-y-2">
                        ${dateNotes.map(n => {
                            const timeStr = formatNoteTime(n);
                            const textPreview = escapeHTML(n.text || n.content || '');
                            const safeId = escapeHTML(String(n.id));

                            return `
                                <div onclick="window.TempoToolNotes.openNoteDetailModal('${safeId}')"
                                     class="bg-[#FEFAF8] hover:bg-white border border-[#EBDCD3] hover:border-[#C88E7D] rounded-2xl p-3.5 space-y-2 shadow-2xs hover:shadow-xs transition cursor-pointer group"
                                     data-day-note-id="${safeId}"
                                     title="Click to view full note details">
                                    <div class="flex items-center justify-between gap-2">
                                        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#F9E8E2] text-[#B87561] shrink-0 uppercase tracking-wider">
                                            Day Note
                                        </span>
                                        ${timeStr ? `<span class="text-[11px] text-[#8C827A] font-medium">${escapeHTML(timeStr)}</span>` : ''}
                                    </div>
                                    <p class="text-xs sm:text-[13px] text-[#4A4540] font-medium leading-relaxed line-clamp-2 break-words group-hover:text-[#202124] transition-colors">
                                        ${textPreview}
                                    </p>
                                    <div class="flex items-center justify-between pt-1 text-[11px] text-[#8C827A] border-t border-stone-100/70">
                                        <span class="group-hover:text-[#C88E7D] transition-colors font-medium">View details →</span>
                                        <span class="text-[10px] text-stone-400">Click to expand</span>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderTaskNotesListHTML(taskNotes) {
        if (!taskNotes || taskNotes.length === 0) {
            return `
                <div class="py-12 px-4 text-center space-y-3 bg-[#FAF7F4] border border-dashed border-stone-200 rounded-2xl" data-tempo-ui="task-notes-empty">
                    <div class="w-10 h-10 mx-auto rounded-xl bg-[#FEF3C7] text-[#92400E] flex items-center justify-center text-lg shadow-2xs">📋</div>
                    <div class="space-y-1">
                        <h4 class="font-heading text-sm font-bold text-[#202124]">No task notes yet.</h4>
                        <p class="text-xs text-[#6F6B68] max-w-xs mx-auto">Attach specific research notes, formulas, or steps to your working plan tasks.</p>
                    </div>
                    <button type="button" 
                            onclick="window.TempoToolNotes.setCreationType('task'); const ta = document.getElementById('textarea-note-content'); if (ta) { ta.scrollIntoView({ behavior: 'smooth', block: 'center' }); ta.focus(); }" 
                            class="px-3.5 py-1.5 rounded-xl font-bold text-xs bg-[#C88E7D] hover:bg-[#B97F6E] text-white shadow-2xs transition cursor-pointer">
                        + Add a Task Note
                    </button>
                </div>
            `;
        }

        return taskNotes.map(n => {
            const timeStr = formatNoteTime(n);
            const textPreview = escapeHTML(n.text || n.content || '');
            const safeId = escapeHTML(String(n.id));
            const taskTitle = escapeHTML(n.taskName || 'Academic Task');

            return `
                <div onclick="window.TempoToolNotes.openNoteDetailModal('${safeId}')"
                     class="bg-[#FEFAF8] hover:bg-white border border-[#EBDCD3] hover:border-[#C88E7D] rounded-2xl p-3.5 space-y-2 shadow-2xs hover:shadow-xs transition cursor-pointer group"
                     data-task-note-id="${safeId}"
                     title="Click to view full task note details">
                    <div class="flex items-center justify-between gap-2">
                        <div class="flex items-center space-x-1.5 min-w-0">
                            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FEF3C7] text-[#92400E] shrink-0 uppercase tracking-wider">
                                Task Note
                            </span>
                            <span class="text-xs font-bold text-[#202124] truncate flex items-center gap-1">
                                <span>📌</span>
                                <span class="truncate">${taskTitle}</span>
                            </span>
                        </div>
                        ${timeStr ? `<span class="text-[11px] text-[#8C827A] font-medium shrink-0">${escapeHTML(timeStr)}</span>` : ''}
                    </div>
                    <p class="text-xs sm:text-[13px] text-[#4A4540] font-medium leading-relaxed line-clamp-2 break-words group-hover:text-[#202124] transition-colors">
                        ${textPreview}
                    </p>
                    <div class="flex items-center justify-between pt-1 text-[11px] text-[#8C827A] border-t border-stone-100/70">
                        <span class="group-hover:text-[#C88E7D] transition-colors font-medium">View details →</span>
                        <span class="text-[10px] text-stone-400">Click to expand</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderToolNotesPage() {
        const root = document.getElementById('tool-notes-root');
        if (!root) return;

        const notes = loadNotes();
        const dayNotes = notes.filter(n => !(n.taskId || n.category === 'task' || n.type === 'task'));
        const taskNotes = notes.filter(n => !!(n.taskId || n.category === 'task' || n.type === 'task'));
        const availableTasks = getAvailableTasks();
        const todayStr = getTodayLocalDateStr();

        root.innerHTML = `
            <!-- Navigation Return Bar -->
            <div class="flex items-center justify-between pb-3">
                <button type="button" 
                        id="btn-tool-notes-back" 
                        onclick="if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') window.TempoApp.navigateTo('today'); else window.location.hash = '#today';"
                        class="inline-flex items-center space-x-1.5 text-xs sm:text-sm font-semibold text-[#6F6B68] hover:text-[#202124] transition cursor-pointer">
                    <span>← Back to Dashboard</span>
                </button>
            </div>

            <!-- Page Title -->
            <div class="space-y-1 pb-4">
                <div class="flex items-center space-x-2">
                    <span class="text-2xl sm:text-3xl">📝</span>
                    <h1 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">Tool Notes</h1>
                </div>
                <p class="text-xs sm:text-sm text-[#6F6B68]">
                    A calm, dedicated space to keep your daily reflections and academic task notes organized.
                </p>
            </div>

            <!-- 1. Dedicated Note Creation Section -->
            <div class="bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:p-6 shadow-xs space-y-4 mb-6" data-tempo-ui="tool-notes-create-section">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-stone-100">
                    <div class="flex items-center space-x-2">
                        <span class="text-lg">✏️</span>
                        <h2 class="font-heading text-base sm:text-lg font-bold text-[#202124]">Create a Note</h2>
                    </div>
                    <!-- Type Selector Pills -->
                    <div class="inline-flex p-1 bg-[#FAF7F4] border border-[#EAE4DF] rounded-2xl space-x-1" role="tablist">
                        <button type="button" 
                                id="pill-type-day"
                                onclick="window.TempoToolNotes.setCreationType('day')"
                                class="px-4 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${currentCreationType === 'day' ? 'bg-[#C88E7D] text-white shadow-2xs' : 'text-[#6F6B68] hover:text-[#202124]'}">
                            📝 Day Note
                        </button>
                        <button type="button" 
                                id="pill-type-task"
                                onclick="window.TempoToolNotes.setCreationType('task')"
                                class="px-4 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${currentCreationType === 'task' ? 'bg-[#C88E7D] text-white shadow-2xs' : 'text-[#6F6B68] hover:text-[#202124]'}">
                            📋 Task Note
                        </button>
                    </div>
                </div>

                <!-- Form -->
                <form id="tool-notes-create-form" onsubmit="event.preventDefault(); window.TempoToolNotes.handleCreateFormSubmit();" class="space-y-4">
                    <!-- Day Note Date Field -->
                    <div id="form-group-day-date" class="${currentCreationType === 'day' ? 'block' : 'hidden'} space-y-1.5">
                        <label for="input-note-date" class="block text-xs font-bold text-[#554741]">
                            Calendar Date
                        </label>
                        <div class="flex items-center gap-2 max-w-xs">
                            <input type="date" 
                                   id="input-note-date" 
                                   value="${escapeHTML(todayStr)}"
                                   class="w-full px-3.5 py-2 text-xs sm:text-sm rounded-xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white transition" />
                        </div>
                        <p class="text-[11px] text-[#8C827A]">Defaults to today's local date. You can select another date if needed.</p>
                    </div>

                    <!-- Task Note Selector Field -->
                    <div id="form-group-task-select" class="${currentCreationType === 'task' ? 'block' : 'hidden'} space-y-1.5">
                        <label for="select-note-task" class="block text-xs font-bold text-[#554741]">
                            Associated Academic Task
                        </label>
                        <select id="select-note-task" 
                                class="w-full max-w-md px-3.5 py-2 text-xs sm:text-sm rounded-xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white transition">
                            <option value="" disabled selected>-- Select a task from your plan --</option>
                            ${availableTasks.length === 0 ? `
                                <option value="" disabled>No active tasks in your plan yet</option>
                            ` : availableTasks.map(t => `
                                <option value="${escapeHTML(t.id)}">${escapeHTML(t.name)}${t.deadlineDate ? ` (Due ${t.deadlineDate})` : ''}</option>
                            `).join('')}
                        </select>
                        <p class="text-[11px] text-[#8C827A]">Populated from your working plan and current tasks.</p>
                    </div>

                    <!-- Note Textarea -->
                    <div class="space-y-1.5">
                        <label for="textarea-note-content" class="block text-xs font-bold text-[#554741]">
                            Note Content
                        </label>
                        <textarea id="textarea-note-content" 
                                  rows="3" 
                                  placeholder="${currentCreationType === 'day' ? 'Write reflections, reminders, or general observations for the day...' : 'Write notes, research links, outlines, or next action steps for this task...'}"
                                  class="w-full p-3.5 text-xs sm:text-sm rounded-2xl border border-stone-200 focus:outline-none focus:border-[#C88E7D] bg-[#FEFAF8] focus:bg-white resize-y min-h-[90px] transition placeholder:text-stone-400"></textarea>
                    </div>

                    <!-- Feedback & Actions -->
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
                        <div id="create-note-feedback" class="text-xs font-medium text-stone-500 min-h-[20px]"></div>
                        <div class="flex items-center space-x-2.5 self-end sm:self-auto">
                            <button type="button" 
                                    onclick="window.TempoToolNotes.resetCreateForm()"
                                    class="px-4 py-2 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] hover:bg-[#FAF7F4] transition cursor-pointer">
                                Cancel
                            </button>
                            <button type="submit" 
                                    id="btn-save-note-submit"
                                    class="px-5 py-2 rounded-xl font-bold text-xs bg-[#C88E7D] hover:bg-[#B97F6E] text-white shadow-2xs transition cursor-pointer inline-flex items-center gap-1.5">
                                <span>Save Note</span>
                            </button>
                        </div>
                    </div>
                </form>
            </div>

            <!-- 2. Two-Column Notes Display -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start" data-tempo-ui="tool-notes-two-columns">
                <!-- LEFT PANEL: Day Notes -->
                <div class="bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:p-6 shadow-xs space-y-4" data-tempo-ui="tool-notes-day-panel">
                    <div class="flex items-center justify-between pb-2 border-b border-stone-100">
                        <div class="flex items-center space-x-2">
                            <span class="text-lg">📝</span>
                            <h3 class="font-heading text-base sm:text-lg font-bold text-[#202124]">
                                Day Notes
                            </h3>
                            <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-[#F9E8E2] text-[#B87561]" id="day-notes-count-badge">
                                ${dayNotes.length}
                            </span>
                        </div>
                        <span class="text-xs text-[#8C827A]">Grouped by date</span>
                    </div>

                    <!-- Scrollable List of Day Notes -->
                    <div class="overflow-y-auto max-h-[580px] space-y-4 pr-1.5 custom-scrollbar" data-tempo-ui="day-notes-scroll-container">
                        ${renderDayNotesListHTML(dayNotes)}
                    </div>
                </div>

                <!-- RIGHT PANEL: Task Notes -->
                <div class="bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:p-6 shadow-xs space-y-4" data-tempo-ui="tool-notes-task-panel">
                    <div class="flex items-center justify-between pb-2 border-b border-stone-100">
                        <div class="flex items-center space-x-2">
                            <span class="text-lg">📋</span>
                            <h3 class="font-heading text-base sm:text-lg font-bold text-[#202124]">
                                Task Notes
                            </h3>
                            <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-[#FEF3C7] text-[#92400E]" id="task-notes-count-badge">
                                ${taskNotes.length}
                            </span>
                        </div>
                        <span class="text-xs text-[#8C827A]">Attached to tasks</span>
                    </div>

                    <!-- Scrollable List of Task Notes -->
                    <div class="overflow-y-auto max-h-[580px] space-y-3 pr-1.5 custom-scrollbar" data-tempo-ui="task-notes-scroll-container">
                        ${renderTaskNotesListHTML(taskNotes)}
                    </div>
                </div>
            </div>
        `;
    }

    // Escape key listener for closing modals
    if (typeof window !== 'undefined') {
        window.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                closeModal();
            }
        });
    }

    function init() {
        renderToolNotesPage();
    }

    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
        } else {
            setTimeout(init, 50);
        }
    }

    return {
        getNotes,
        getNoteById,
        getNoteForTask: (taskId) => {
            if (!taskId) return null;
            const notes = loadNotes();
            return notes.find(n => String(n.taskId) === String(taskId)) || null;
        },
        saveTaskNote,
        deleteTaskNote,
        saveDayNote,
        deleteDayNote,
        updateNote,
        deleteNote,
        confirmDeleteNote,
        getDayNotes,
        getTaskNotes,
        getAvailableTasks,
        setCreationType,
        handleCreateFormSubmit,
        resetCreateForm,
        openNoteDetailModal,
        openNoteEditModal,
        handleSaveEditSubmit,
        openCreateNoteModal,
        closeModal,
        renderToolNotesPage,
        getTodayLocalDateStr,
        formatDisplayDate
    };
})();
'''

# Enforce pure LF
js_content = js_content.replace('\r\n', '\n')
assert '\r' not in js_content, "Found CRLF in js_content"

with open('toolNotes.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(js_content)

print("toolNotes.js successfully written with pure LF.")
