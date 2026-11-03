# -*- coding: utf-8 -*-
import re

with open('mode.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Verify LF
assert '\r' not in content, 'mode.js has carriage returns before modification'

replacement_code = '''    function formatNoteTime(note) {
        if (!note) return '';
        if (note.time) return note.time;
        const iso = note.createdAt || note.updatedAt;
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

    function getUmodeDayNotesForToday(targetDate) {
        const today = targetDate || (typeof getTodayISOString === 'function' ? getTodayISOString() : new Date().toISOString().slice(0, 10));
        const allNotes = [];
        const seenIds = new Set();

        function addCandidate(n) {
            if (!n) return;
            // Strictly exclude task notes
            if (n.taskId || n.category === 'task' || n.type === 'task') return;
            // Must be day note or general note without task association
            const isDay = n.category === 'day' || n.type === 'day' || (!n.taskId && n.category !== 'task' && n.type !== 'task');
            if (!isDay) return;

            // Check date match strictly against targetDate
            let nDate = '';
            if (n.date && typeof n.date === 'string') {
                nDate = n.date.slice(0, 10);
            } else if (n.createdAt && typeof n.createdAt === 'string') {
                nDate = n.createdAt.slice(0, 10);
            } else if (n.updatedAt && typeof n.updatedAt === 'string') {
                nDate = n.updatedAt.slice(0, 10);
            }
            if (nDate !== today) return;

            const noteId = String(n.id || (n.text ? n.text.slice(0, 30) : Math.random()));
            if (!seenIds.has(noteId)) {
                seenIds.add(noteId);
                allNotes.push(n);
            }
        }

        // 1. First source: window.TempoToolNotes.getDayNotes(today)
        if (typeof window !== 'undefined' && window.TempoToolNotes && typeof window.TempoToolNotes.getDayNotes === 'function') {
            try {
                const tnNotes = window.TempoToolNotes.getDayNotes(today) || [];
                if (Array.isArray(tnNotes)) {
                    tnNotes.forEach(addCandidate);
                }
            } catch (e) {}
        }

        // 2. Second source: localStorage keys
        try {
            let uid = 'local_user';
            if (typeof window !== 'undefined' && window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') {
                const u = window.TempoAuth.getCurrentUserId();
                if (u) uid = u;
            } else if (typeof window !== 'undefined' && window.TempoAuth && typeof window.TempoAuth.getUser === 'function') {
                const u = window.TempoAuth.getUser();
                if (u && u.id) uid = u.id;
            }

            const keysToCheck = [
                `tempo_day_notes_${uid}`,
                'tempo_day_notes',
                `tempo_tool_notes_${uid}`,
                'tempo_tool_notes'
            ];

            for (const k of keysToCheck) {
                const raw = localStorage.getItem(k);
                if (!raw) continue;
                try {
                    const parsed = JSON.parse(raw);
                    if (Array.isArray(parsed)) {
                        parsed.forEach(addCandidate);
                    }
                } catch (err) {}
            }
        } catch (e) {}

        // Sort latest first
        allNotes.sort((a, b) => {
            const timeA = new Date(a.createdAt || a.updatedAt || a.date || 0).getTime();
            const timeB = new Date(b.createdAt || b.updatedAt || b.date || 0).getTime();
            return timeB - timeA;
        });

        return allNotes;
    }

    function renderEmodeCreateNotesCard(ctx) {
        const todayStr = (ctx && ctx.todayStr) || (typeof getTodayISOString === 'function' ? getTodayISOString() : new Date().toISOString().slice(0, 10));
        const dayNotes = getUmodeDayNotesForToday(todayStr);

        let notesListHTML = '';
        if (!dayNotes || dayNotes.length === 0) {
            notesListHTML = `
                <div class="h-full min-h-[78px] flex flex-col items-center justify-center text-center px-3 py-2 bg-[#FCF5F0]/70 border border-dashed border-[#E8D5CA] rounded-2xl select-none" data-tempo-ui="notes-empty-state">
                    <span class="text-base text-[#B87561] mb-0.5">📝</span>
                    <p class="text-xs font-semibold text-[#8C7D75]">No notes for today yet.</p>
                </div>
            `;
        } else {
            notesListHTML = `
                <div class="overflow-y-auto max-h-[96px] space-y-1.5 pr-1 text-left custom-scrollbar" data-tempo-ui="notes-scroll-list" style="max-height: 96px; overflow-y: auto;">
                    ${dayNotes.map(n => {
                        const noteText = escapeHTML(n.text || n.content || n.note || '');
                        const timeStr = formatNoteTime(n);
                        const safeId = escapeHTML(String(n.id || ''));
                        return `
                            <div onclick="if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('notes'); } else { window.location.hash = '#notes'; }"
                                 class="bg-white/90 hover:bg-white border border-[#EBDCD3] hover:border-[#D9C4B7] rounded-xl px-2.5 py-1.5 transition text-xs shadow-2xs group cursor-pointer" 
                                 data-day-note-id="${safeId}"
                                 title="View note in notes manager">
                                <div class="flex items-center justify-between gap-1 mb-0.5">
                                    <span class="text-[10px] font-bold uppercase tracking-wider text-[#B87561] flex items-center gap-1">
                                        <span>📝</span>
                                        <span>Day Note</span>
                                    </span>
                                    ${timeStr ? `<span class="text-[10px] text-[#9E9087] font-medium">${escapeHTML(timeStr)}</span>` : ''}
                                </div>
                                <p class="text-[11.5px] text-[#484541] font-medium leading-snug line-clamp-2 break-words">
                                    ${noteText}
                                </p>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }

        return `
            <div class="w-full min-h-[122px] max-h-[122px] h-[122px] bg-[#F9E8E2] border border-[#E8D5CA] rounded-3xl p-3.5 sm:p-4 shadow-xs flex flex-row items-center justify-between box-border relative overflow-hidden" 
                 data-tempo-ui="urmode-create-notes" 
                 style="width: 100%; height: 122px; min-height: 122px; max-height: 122px; box-sizing: border-box; overflow: hidden;">
                <!-- Left: Title & View Button -->
                <div class="flex flex-col justify-between shrink-0 space-y-2 pr-3 sm:pr-4 border-r border-[#E8D5CA]/70" data-tempo-ui="notes-text-block" style="min-width: 120px; max-width: 135px;">
                    <h3 class="text-lg sm:text-xl font-bold text-[#554741] leading-tight tracking-tight">
                        Create Notes
                    </h3>
                    <div>
                        <button type="button"
                                onclick="if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('notes'); } else { window.location.hash = '#notes'; }"
                                class="px-3 py-1.5 rounded-xl font-bold text-xs bg-[#C88E7D] hover:bg-[#B97F6E] text-white shadow-2xs transition cursor-pointer inline-flex items-center justify-center whitespace-nowrap">
                            View my notes
                        </button>
                    </div>
                </div>

                <!-- Right: Today's Day Notes List (Scrollable) -->
                <div class="flex-1 min-w-0 pl-3 sm:pl-4 h-full flex flex-col justify-center" data-tempo-ui="notes-list-container">
                    ${notesListHTML}
                </div>
            </div>
        `;
    }

    function refreshNotesCardIfPresent() {
        const cardEl = document.querySelector('[data-tempo-ui="urmode-create-notes"]');
        if (!cardEl) return;
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = renderEmodeCreateNotesCard().trim();
        const newCard = tempDiv.firstElementChild;
        if (newCard) {
            cardEl.replaceWith(newCard);
        }
    }'''

target_regex = r'    function renderEmodeCreateNotesCard\(\) \{[\s\S]*?    \}\n\n    function renderLowerCreateNotesCard'

match = re.search(target_regex, content)
assert match is not None, 'Could not find renderEmodeCreateNotesCard() definition to replace'

new_content = content[:match.start()] + replacement_code + '\n\n    function renderLowerCreateNotesCard' + content[match.end():]

# Also ensure TempoMode return object exports renderEmodeCreateNotesCard, refreshNotesCardIfPresent, getUmodeDayNotesForToday
export_target = 'syncUmodeCreateNotesAlignment,\n        EPLAN_STATES'
export_replacement = '''syncUmodeCreateNotesAlignment,
        renderEmodeCreateNotesCard,
        refreshNotesCardIfPresent,
        getUmodeDayNotesForToday,
        EPLAN_STATES'''

assert export_target in new_content, 'Could not find export target in new_content'
new_content = new_content.replace(export_target, export_replacement, 1)

# Also ensure note event listeners are registered alongside selfcheck listeners
listener_target = '''window.addEventListener('storage', function(e) {
    if (e && e.key && e.key.includes('tempo_selfcheck')) {
        if (window.TempoMode && typeof window.TempoMode.refreshStreakCardIfPresent === 'function') {
            window.TempoMode.refreshStreakCardIfPresent();
        }
    }
});'''

listener_replacement = '''window.addEventListener('storage', function(e) {
    if (e && e.key && e.key.includes('tempo_selfcheck')) {
        if (window.TempoMode && typeof window.TempoMode.refreshStreakCardIfPresent === 'function') {
            window.TempoMode.refreshStreakCardIfPresent();
        }
    }
});

window.addEventListener('tempo:note-updated', function() {
    if (window.TempoMode && typeof window.TempoMode.refreshNotesCardIfPresent === 'function') {
        window.TempoMode.refreshNotesCardIfPresent();
    }
});

window.addEventListener('storage', function(e) {
    if (e && e.key && (e.key.includes('note') || e.key.includes('Note'))) {
        if (window.TempoMode && typeof window.TempoMode.refreshNotesCardIfPresent === 'function') {
            window.TempoMode.refreshNotesCardIfPresent();
        }
    }
});'''

assert listener_target in new_content, 'Could not find listener target in new_content'
new_content = new_content.replace(listener_target, listener_replacement, 1)

# Enforce LF
new_content = new_content.replace('\r\n', '\n')
assert '\r' not in new_content, 'New content has carriage returns'

with open('mode.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(new_content)

print('Successfully updated mode.js with Daily Notes preview and reactive listeners.')
