/**
 * Tempo Tool Notes
 * File: toolNotes.js
 *
 * Dedicated storage and manager for Tool Notes and Task-associated notes.
 * Integrates with Working Plan task cards, Tool Notes screen, and Focus Zone.
 */

window.TempoToolNotes = (function () {
    'use strict';

    function getUserId() {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') {
            const uid = window.TempoAuth.getCurrentUserId();
            if (uid) return uid;
        }
        return 'local_user';
    }

    function getStorageKey() {
        const uid = getUserId();
        return `tempo_tool_notes_${uid}`;
    }

    function loadNotes() {
        try {
            const key = getStorageKey();
            const raw = localStorage.getItem(key);
            if (raw) {
                const parsed = JSON.parse(raw);
                if (Array.isArray(parsed)) return parsed;
            }

            // Fallback to non-uid key
            const fallback = localStorage.getItem('tempo_tool_notes');
            if (fallback) {
                const parsed = JSON.parse(fallback);
                if (Array.isArray(parsed)) return parsed;
            }
        } catch (e) {
            console.warn("[TempoToolNotes] Error loading notes:", e);
        }
        return [];
    }

    function saveNotes(notes) {
        try {
            const key = getStorageKey();
            localStorage.setItem(key, JSON.stringify(notes));
            localStorage.setItem('tempo_tool_notes', JSON.stringify(notes));
        } catch (e) {
            console.warn("[TempoToolNotes] Error saving notes:", e);
        }
    }

    function getNotes() {
        return loadNotes();
    }

    function getNoteForTask(taskId) {
        if (!taskId) return null;
        const sId = String(taskId);
        const notes = loadNotes();
        return notes.find(n => String(n.taskId) === sId) || null;
    }

    function saveTaskNote(taskId, taskName, text) {
        if (!taskId) return null;
        const sId = String(taskId);
        const trimmed = (text || '').trim();

        const notes = loadNotes();
        const existingIdx = notes.findIndex(n => String(n.taskId) === sId);

        let savedNote = null;

        if (!trimmed) {
            // If empty text, remove note
            if (existingIdx !== -1) {
                notes.splice(existingIdx, 1);
                saveNotes(notes);
            }
            syncTaskInPlans(sId, '');
        } else {
            const now = new Date().toISOString();
            if (existingIdx !== -1) {
                notes[existingIdx].text = trimmed;
                notes[existingIdx].content = trimmed;
                notes[existingIdx].taskName = taskName || notes[existingIdx].taskName || 'Academic Task';
                notes[existingIdx].title = `Note for ${notes[existingIdx].taskName}`;
                notes[existingIdx].updatedAt = now;
                savedNote = notes[existingIdx];
            } else {
                savedNote = {
                    id: 'tool_note_task_' + sId,
                    taskId: sId,
                    taskName: taskName || 'Academic Task',
                    title: `Note for ${taskName || 'Academic Task'}`,
                    text: trimmed,
                    content: trimmed,
                    createdAt: now,
                    updatedAt: now,
                    category: 'task'
                };
                notes.unshift(savedNote);
            }
            saveNotes(notes);
            syncTaskInPlans(sId, trimmed);
        }

        // Notify active views
        renderToolNotesPage();

        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
        }

        if (window.TempoFocusZone && typeof window.TempoFocusZone.render === 'function') {
            window.TempoFocusZone.render();
        }

        return savedNote;
    }

    function deleteTaskNote(taskId) {
        if (!taskId) return;
        const sId = String(taskId);
        const notes = loadNotes();
        const idx = notes.findIndex(n => String(n.taskId) === sId);
        if (idx !== -1) {
            notes.splice(idx, 1);
            saveNotes(notes);
        }
        syncTaskInPlans(sId, '');

        renderToolNotesPage();

        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
        }

        if (window.TempoFocusZone && typeof window.TempoFocusZone.render === 'function') {
            window.TempoFocusZone.render();
        }
    }

    function syncTaskInPlans(taskId, noteText) {
        // 1. Sync in TempoEmergencyFlow
        if (window.TempoEmergencyFlow) {
            const confirmedPlan = typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function' ? window.TempoEmergencyFlow.getConfirmedPlan() : null;
            if (confirmedPlan && Array.isArray(confirmedPlan.plannedTasks)) {
                const pt = confirmedPlan.plannedTasks.find(item => item.task && String(item.task.id) === String(taskId));
                if (pt && pt.task) {
                    pt.task.note = noteText;
                    pt.task.description = noteText;
                }
            }
            if (typeof window.TempoEmergencyFlow.getTasks === 'function') {
                const tasks = window.TempoEmergencyFlow.getTasks();
                const t = tasks.find(item => String(item.id) === String(taskId));
                if (t) {
                    t.note = noteText;
                    t.description = noteText;
                }
            }
        }

        // 2. Sync in TempoPlanStore
        if (window.TempoPlanStore) {
            const activePlan = typeof window.TempoPlanStore.getActivePlan === 'function' ? window.TempoPlanStore.getActivePlan('emergency') : null;
            if (activePlan && Array.isArray(activePlan.plannedTasks)) {
                const pt = activePlan.plannedTasks.find(item => item.task && String(item.task.id) === String(taskId));
                if (pt && pt.task) {
                    pt.task.note = noteText;
                    pt.task.description = noteText;
                }
                if (typeof window.TempoPlanStore.saveActivePlan === 'function') {
                    window.TempoPlanStore.saveActivePlan('emergency', activePlan);
                }
            }
        }
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

    function renderToolNotesPage() {
        const screen = document.getElementById('screen-tool-notes');
        if (!screen) return;

        let notesContainer = document.getElementById('tool-notes-task-list-container');
        if (!notesContainer) {
            notesContainer = document.createElement('div');
            notesContainer.id = 'tool-notes-task-list-container';
            notesContainer.className = 'max-w-2xl mx-auto space-y-4 pt-6';
            screen.appendChild(notesContainer);
        }

        const notes = loadNotes();

        if (notes.length === 0) {
            notesContainer.innerHTML = `
                <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-8 text-center space-y-3 shadow-xs">
                    <div class="w-12 h-12 mx-auto rounded-2xl bg-amber-50 text-amber-700 flex items-center justify-center text-xl">
                        📝
                    </div>
                    <div class="space-y-1">
                        <h3 class="font-heading text-lg font-bold text-[#202124]">No task notes yet</h3>
                        <p class="text-xs text-[#6F6B68] max-w-sm mx-auto">
                            When you create notes on your Working Plan task cards, they will be preserved and accessible here.
                        </p>
                    </div>
                </div>
            `;
            return;
        }

        notesContainer.innerHTML = `
            <div class="space-y-3">
                <div class="flex items-center justify-between px-1">
                    <h3 class="font-heading text-base sm:text-lg font-bold text-[#202124]">
                        Task Notes (${notes.length})
                    </h3>
                    <span class="text-xs text-[#6F6B68]">Saved from your Working Plan</span>
                </div>
                <div class="space-y-3">
                    ${notes.map(note => {
                        const dateStr = note.updatedAt ? new Date(note.updatedAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';
                        return `
                            <div class="bg-white border border-[#EAE4DF] rounded-2xl p-5 space-y-3 shadow-xs hover:border-[#D99E87] transition" data-tool-note-id="${note.id}">
                                <div class="flex items-center justify-between gap-3">
                                    <div class="flex items-center space-x-2 min-w-0">
                                        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 shrink-0">
                                            Task Note
                                        </span>
                                        <h4 class="font-heading text-sm sm:text-base font-bold text-[#202124] truncate">
                                            ${escapeHTML(note.taskName || 'Academic Task')}
                                        </h4>
                                    </div>
                                    <div class="text-[11px] text-[#8C827A] shrink-0">
                                        ${dateStr}
                                    </div>
                                </div>
                                <p class="text-xs sm:text-sm text-[#4A4540] whitespace-pre-wrap leading-relaxed bg-[#FAF7F4] p-3 rounded-xl border border-stone-100">
                                    ${escapeHTML(note.text)}
                                </p>
                                <div class="flex items-center justify-end space-x-3 pt-1 text-xs">
                                    <button type="button"
                                            onclick="window.TempoToolNotes.deleteTaskNote('${note.taskId}')"
                                            class="text-rose-600 hover:text-rose-800 font-semibold cursor-pointer">
                                        Delete
                                    </button>
                                    <button type="button"
                                            onclick="window.TempoApp.navigateTo('plan-workspace'); if (window.TempoPlanWorkspace && window.TempoPlanWorkspace.selectTask) { window.TempoPlanWorkspace.selectTask('${note.taskId}'); setTimeout(() => window.TempoPlanWorkspace.openNoteEditor('${note.taskId}'), 150); }"
                                            class="text-[#D99E87] hover:underline font-bold cursor-pointer">
                                        Edit in Plan →
                                    </button>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

    function init() {
        renderToolNotesPage();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 50);
    }

    return {
        getNotes,
        getNoteForTask,
        saveTaskNote,
        deleteTaskNote,
        renderToolNotesPage
    };
})();
