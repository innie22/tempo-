import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('toolNotes.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

assert '\r\n' not in content, "CRLF found in toolNotes.js!"

modal_target = """    function openNoteDetailModal(noteId) {
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
                                ${isTask ? `📌 ${escapeHTML(note.taskName || (isViLocale() ? 'Công việc Học tập' : 'Study Task'))}` : `📅 ${escapeHTML(formattedDate)}`}
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
                        <span class="text-xs font-bold uppercase tracking-wider text-[#8C827A]">${escapeHTML(t('toolNotes.fullContent', isViLocale() ? 'Nội dung đầy đủ' : 'Full Content'))}</span>
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
                            <span>🗑️ ${escapeHTML(t('toolNotes.delete', isViLocale() ? 'Xóa' : 'Delete'))}</span>
                        </button>
                        <div class="flex items-center space-x-2">
                            <button type="button"
                                    onclick="window.TempoToolNotes.closeModal()"
                                    class="px-4 py-2 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] hover:bg-stone-100 transition cursor-pointer">
                                ${escapeHTML(t('toolNotes.close', isViLocale() ? 'Đóng' : 'Close'))}
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
    }"""

modal_replacement = """    function openNoteDetailModal(noteId) {
        if (!noteId) return;
        const note = getNoteById(noteId);
        if (!note) return;

        // Clean up previous listeners if switching modals
        if (typeof activeModalCleanup === 'function') {
            try { activeModalCleanup(); } catch (e) {}
            activeModalCleanup = null;
        }

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
                <div class="bg-white border border-[#EAE4DF] rounded-3xl max-w-lg w-full p-6 sm:p-7 shadow-xl space-y-4 animate-in fade-in zoom-in-95 relative text-left" 
                     role="dialog" 
                     aria-modal="true"
                     aria-labelledby="note-detail-title">
                    
                    <!-- Header -->
                    <div class="flex items-start justify-between gap-3 pb-3 border-b border-stone-100">
                        <div class="space-y-1 min-w-0">
                            <div class="flex items-center space-x-2">
                                <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold ${isTask ? 'bg-[#FEF3C7] text-[#92400E]' : 'bg-[#F9E8E2] text-[#B87561]'} uppercase tracking-wider">
                                    ${isTask ? `📋 ${escapeHTML(t('toolNotes.tabTaskNote', isViLocale() ? 'Note theo task' : 'Task Note'))}` : `📝 ${escapeHTML(t('toolNotes.tabDayNote', isViLocale() ? 'Note theo ngày' : 'Day Note'))}`}
                                </span>
                                ${timeStr ? `<span class="text-xs text-[#8C827A] font-medium">${escapeHTML(timeStr)}</span>` : ''}
                            </div>
                            <h3 id="note-detail-title" class="font-heading text-lg sm:text-xl font-bold text-[#202124] truncate">
                                ${isTask ? `📌 ${escapeHTML(note.taskName || (isViLocale() ? 'Công việc Học tập' : 'Study Task'))}` : `📅 ${escapeHTML(formattedDate)}`}
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
                        <span class="text-xs font-bold uppercase tracking-wider text-[#8C827A]">${escapeHTML(t('toolNotes.fullContent', isViLocale() ? 'Nội dung đầy đủ' : 'Full Content'))}</span>
                        <div class="bg-[#FAF7F4] border border-stone-200/70 rounded-2xl p-4 max-h-[340px] overflow-y-auto custom-scrollbar">
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

                    <!-- Feedback message (e.g. for unavailable task) -->
                    <div id="note-detail-feedback" class="text-xs font-semibold text-rose-600 min-h-[16px]"></div>

                    <!-- Footer Actions -->
                    <div class="flex items-center justify-between pt-3 border-t border-stone-100 flex-wrap gap-2">
                        <button type="button"
                                onclick="window.TempoToolNotes.confirmDeleteNote('${escapeHTML(String(note.id))}')"
                                class="px-4 py-2 rounded-xl text-xs font-bold text-rose-600 hover:text-white hover:bg-rose-600 border border-rose-200 hover:border-rose-600 transition cursor-pointer inline-flex items-center gap-1.5">
                            <span>🗑️ ${escapeHTML(t('toolNotes.delete', isViLocale() ? 'Xóa' : 'Delete'))}</span>
                        </button>
                        <div class="flex items-center space-x-2">
                            <button type="button"
                                    onclick="window.TempoToolNotes.closeModal()"
                                    class="px-4 py-2 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] hover:bg-stone-100 transition cursor-pointer">
                                ${escapeHTML(t('toolNotes.close', isViLocale() ? 'Đóng' : 'Close'))}
                            </button>
                            ${isTask ? `
                                <button type="button"
                                        id="btn-note-view-task"
                                        onclick="window.TempoToolNotes.viewAssociatedTask('${escapeHTML(String(note.taskId || ''))}')"
                                        class="px-4 py-2 rounded-xl text-xs font-bold bg-[#FEF3C7] hover:bg-[#FDE68A] text-[#92400E] border border-[#FCD34D] transition cursor-pointer inline-flex items-center gap-1.5">
                                    <span>📌 ${escapeHTML(t('toolNotes.viewTask', isViLocale() ? 'Xem task' : 'View Task'))}</span>
                                </button>
                            ` : ''}
                            <button type="button"
                                    onclick="window.TempoToolNotes.openNoteEditModal('${escapeHTML(String(note.id))}')"
                                    class="px-5 py-2 rounded-xl font-bold text-xs bg-[#C88E7D] hover:bg-[#B97F6E] text-white shadow-2xs transition cursor-pointer inline-flex items-center gap-1.5">
                                <span>✏️ ${escapeHTML(t('toolNotes.editNote', isViLocale() ? 'Chỉnh sửa Ghi chú' : 'Edit Note'))}</span>
                            </button>
                        </div>
                    </div>

                </div>
            </div>
        `;

        // Subscribe to dynamic language changes while modal is open
        const unsubscribeLang = window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function'
            ? window.TempoI18n.onLanguageChange(() => {
                if (activeModalNoteId === String(note.id)) {
                    openNoteDetailModal(note.id);
                }
            })
            : null;

        activeModalCleanup = () => {
            if (typeof unsubscribeLang === 'function') {
                try { unsubscribeLang(); } catch (e) {}
            }
        };
    }

    function viewAssociatedTask(taskId) {
        if (!taskId) {
            showTaskUnavailableFeedback();
            return;
        }

        const sTaskId = String(taskId);

        // 1. Check if task exists in any active data source
        let taskData = null;
        if (window.TempoMode && typeof window.TempoMode.getUrmodeTaskData === 'function') {
            const res = window.TempoMode.getUrmodeTaskData(sTaskId);
            if (res && res.task) {
                taskData = res.task;
            }
        }

        if (!taskData && typeof getAvailableTasks === 'function') {
            const avail = getAvailableTasks();
            const found = avail.find(t => t && String(t.id) === sTaskId);
            if (found) {
                taskData = found;
            }
        }

        if (!taskData) {
            showTaskUnavailableFeedback();
            return;
        }

        // Close note detail modal so user can view task modal cleanly
        closeModal();

        // Open existing Task Detail Modal
        if (window.TempoMode && typeof window.TempoMode.openUrmodeTaskDetailModal === 'function') {
            window.TempoMode.openUrmodeTaskDetailModal(sTaskId);
        } else if (window.TempoMode && typeof window.TempoMode.openRmodeTaskDetailModal === 'function') {
            window.TempoMode.openRmodeTaskDetailModal(sTaskId);
        }
    }

    function showTaskUnavailableFeedback() {
        const fb = document.getElementById('note-detail-feedback');
        const msg = t('toolNotes.taskUnavailable', isViLocale() ? 'Task này hiện không còn tồn tại.' : 'This task is no longer available.');
        if (fb) {
            fb.innerText = msg;
        } else {
            alert(msg);
        }
    }"""

assert modal_target in content, "modal_target not found in toolNotes.js!"
content = content.replace(modal_target, modal_replacement, 1)

# Export viewAssociatedTask
export_target = """        getTodayLocalDateStr,
        formatDisplayDate
    };"""

export_replacement = """        getTodayLocalDateStr,
        formatDisplayDate,
        viewAssociatedTask
    };"""

assert export_target in content, "export_target not found in toolNotes.js!"
content = content.replace(export_target, export_replacement, 1)

assert '\r' not in content, "CRLF found in toolNotes.js after update!"

with open('toolNotes.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print(f"Updated toolNotes.js successfully! Total LF lines: {content.count(chr(10))}")
