/**
 * TEMPO WELLBEING — SELF-CHECK HISTORY & TRACKER DETAIL (PHASE 4)
 * File: selfCheckHistory.js
 *
 * Architecture:
 * 1. Self-check History Modal (#modal-selfcheck-history)
 * 2. Tabs: [ Check-ins ] (fully functional) and [ Weekly Reviews ] (Phase 5 placeholder)
 * 3. Monthly Check-in Calendar with Month Navigation and Selected Day Detail
 * 4. Your Trackers List with last recorded observation
 * 5. Tracker Detail View with method-specific visual history (SVG line charts for Scale, % & Quantity; list for Yes/No)
 * 6. Dynamic Recently Card on Recovery Home (States 1, 2, 3, and 4: Something to Notice)
 */

(function () {
    'use strict';

    // Calendar state
    let currentCalYear = new Date().getFullYear();
    let currentCalMonth = new Date().getMonth(); // 0-indexed
    let selectedDateStr = getTodayISOString();

    // Active tab in history modal ('checkins' | 'weekly_reviews')
    let activeTab = 'checkins';

    // Active view in history modal ('overview' | 'tracker_detail')
    let currentHistoryView = 'overview';
    let selectedTrackerId = null;

    function getTodayISOString() {
        const now = new Date();
        const y = now.getFullYear();
        const m = String(now.getMonth() + 1).padStart(2, '0');
        const d = String(now.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    }

    function formatDisplayDate(dateStr) {
        if (!dateStr) return '';
        try {
            const [y, m, d] = dateStr.split('-').map(Number);
            const dt = new Date(y, m - 1, d);
            return dt.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
        } catch (e) {
            return dateStr;
        }
    }

    // =========================================================================
    // MODAL SHELL MOUNTING
    // =========================================================================

    function ensureModalMounted() {
        if (document.getElementById('modal-selfcheck-history')) return;

        const modal = document.createElement('div');
        modal.id = 'modal-selfcheck-history';
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-3 sm:p-4 hidden';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.innerHTML = `
            <div class="tempo-card max-w-2xl w-full p-6 sm:p-8 space-y-6 bg-white rounded-3xl shadow-2xl relative border border-[#EAE4DF] max-h-[92vh] overflow-y-auto">
                <button type="button" onclick="window.TempoSelfCheckHistory.close()"
                        class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer" title="Close">✕</button>
                <div id="selfcheck-history-content"></div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    function open(trackerId = null) {
        ensureModalMounted();
        if (trackerId) {
            currentHistoryView = 'tracker_detail';
            selectedTrackerId = trackerId;
        } else {
            currentHistoryView = 'overview';
            selectedTrackerId = null;
        }

        renderHistoryModal();
        const modal = document.getElementById('modal-selfcheck-history');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
        }
    }

    function close() {
        const modal = document.getElementById('modal-selfcheck-history');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    // =========================================================================
    // MODAL VIEW ROUTER
    // =========================================================================

    function renderHistoryModal() {
        const container = document.getElementById('selfcheck-history-content');
        if (!container) return;

        if (currentHistoryView === 'tracker_detail' && selectedTrackerId) {
            renderTrackerDetailView(container, selectedTrackerId);
        } else {
            renderOverviewView(container);
        }
    }

    // =========================================================================
    // OVERVIEW VIEW: TABS + CALENDAR + DAY DETAIL + TRACKERS
    // =========================================================================

    function renderOverviewView(container) {
        const streak = window.TempoRecoverySelfCheck ? window.TempoRecoverySelfCheck.calculateStreak() : 0;
        const todayCheckin = window.TempoRecoverySelfCheck ? window.TempoRecoverySelfCheck.getTodayCheckin() : null;

        container.innerHTML = `
            <div class="space-y-6">
                <!-- Header -->
                <div class="space-y-1.5">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#166545] inline-block"></span>
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">SELF-CHECK</span>
                        </div>
                        <span class="text-xs font-semibold text-[#6F6B68]">${streak} day check-in streak</span>
                    </div>
                    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                        <div>
                            <h3 class="font-heading text-2xl font-extrabold text-[#202124]">Your Check-ins</h3>
                            <p class="text-xs text-[#6F6B68]">A look back at what you've been noticing over time.</p>
                        </div>
                        <div>
                            ${todayCheckin ? `
                                <span class="inline-flex items-center space-x-1 px-3 py-1.5 rounded-full bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA] text-xs font-bold">
                                    <span>✓</span>
                                    <span>Checked in today</span>
                                </span>
                            ` : `
                                <button type="button" onclick="window.TempoSelfCheckHistory.launchCheckin()"
                                        class="btn-primary px-4 py-2 rounded-xl font-bold text-xs shadow-xs transition cursor-pointer">
                                    Check in today →
                                </button>
                            `}
                        </div>
                    </div>
                </div>

                <!-- Tabs: [ Check-ins ] and [ Weekly Reviews ] -->
                <div class="flex border-b border-stone-200 gap-6">
                    <button type="button" onclick="window.TempoSelfCheckHistory.switchTab('checkins')"
                            class="pb-2.5 text-xs font-bold transition cursor-pointer border-b-2 ${activeTab === 'checkins' ? 'border-[#166545] text-[#166545]' : 'border-transparent text-stone-400 hover:text-stone-700'}">
                        Check-ins
                    </button>
                    <button type="button" onclick="window.TempoSelfCheckHistory.switchTab('weekly_reviews')"
                            class="pb-2.5 text-xs font-bold transition cursor-pointer border-b-2 ${activeTab === 'weekly_reviews' ? 'border-[#166545] text-[#166545]' : 'border-transparent text-stone-400 hover:text-stone-700'}">
                        Weekly Reviews
                    </button>
                </div>

                <!-- Tab Content -->
                ${activeTab === 'weekly_reviews' ? renderWeeklyReviewsTabContent() : renderCheckinsTabContent()}
            </div>
        `;
    }

    function switchTab(tab) {
        activeTab = tab;
        renderHistoryModal();
    }

    function renderWeeklyReviewsTabContent() {
        if (window.TempoWeeklyReview && typeof window.TempoWeeklyReview.renderHistoryTabContent === 'function') {
            return window.TempoWeeklyReview.renderHistoryTabContent();
        }
        return renderWeeklyReviewsTabPlaceholder();
    }

    function renderWeeklyReviewsTabPlaceholder() {
        return `
            <div class="p-8 text-center rounded-3xl border border-stone-200 bg-stone-50/50 space-y-3">
                <div class="w-10 h-10 rounded-2xl bg-[#EDF7F1] text-[#166545] flex items-center justify-center text-lg font-bold mx-auto shadow-xs">
                    📅
                </div>
                <div class="space-y-1 max-w-sm mx-auto">
                    <h4 class="font-heading text-base font-bold text-[#202124]">Weekly Reviews</h4>
                    <p class="text-xs text-[#6F6B68] leading-relaxed">
                        Your weekly reflections will appear here once you've looked back at a week with Tempo.
                    </p>
                </div>
            </div>
        `;
    }

    function renderCheckinsTabContent() {
        return `
            <div class="space-y-6">
                <!-- Calendar Section -->
                <div class="p-4 sm:p-5 rounded-3xl border border-stone-200 bg-white space-y-4 shadow-2xs">
                    ${renderCalendarHeader()}
                    ${renderCalendarGrid()}
                </div>

                <!-- Selected Day Observation Detail Panel -->
                <div id="selfcheck-day-detail-panel" class="p-5 rounded-3xl border border-stone-200 bg-stone-50/50 space-y-3">
                    ${renderSelectedDayDetail()}
                </div>

                <!-- Your Trackers Section -->
                <div class="space-y-3 pt-2">
                    <h4 class="text-xs font-extrabold uppercase tracking-wider text-stone-500">Your Trackers</h4>
                    ${renderYourTrackersList()}
                </div>
            </div>
        `;
    }

    // =========================================================================
    // CALENDAR CONTROLLER
    // =========================================================================

    function renderCalendarHeader() {
        const monthNames = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];

        return `
            <div class="flex items-center justify-between">
                <h4 class="font-heading text-base font-bold text-[#202124]">
                    ${monthNames[currentCalMonth]} ${currentCalYear}
                </h4>
                <div class="flex items-center space-x-1.5 text-xs">
                    <button type="button" onclick="window.TempoSelfCheckHistory.prevMonth()"
                            class="w-7 h-7 rounded-lg border border-stone-200 hover:bg-stone-100 flex items-center justify-center font-bold text-stone-600 transition cursor-pointer">
                        ‹
                    </button>
                    <button type="button" onclick="window.TempoSelfCheckHistory.nextMonth()"
                            class="w-7 h-7 rounded-lg border border-stone-200 hover:bg-stone-100 flex items-center justify-center font-bold text-stone-600 transition cursor-pointer">
                        ›
                    </button>
                </div>
            </div>
        `;
    }

    function renderCalendarGrid() {
        // Collect completed check-in dates
        const checkins = window.TempoRecoverySelfCheck ? window.TempoRecoverySelfCheck.getDailyCheckins() : [];
        const checkinDates = new Set(checkins.map(c => c.checkin_date));

        const todayStr = getTodayISOString();

        // First day of month
        const firstDay = new Date(currentCalYear, currentCalMonth, 1);
        let startDayIndex = firstDay.getDay() - 1; // 0 = Mon, 6 = Sun
        if (startDayIndex === -1) startDayIndex = 6;

        // Days in month
        const daysInMonth = new Date(currentCalYear, currentCalMonth + 1, 0).getDate();

        const weekdays = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

        const cells = [];
        // Blank cells before month start
        for (let i = 0; i < startDayIndex; i++) {
            cells.push(`<div class="h-10"></div>`);
        }

        // Days of month
        for (let day = 1; day <= daysInMonth; day++) {
            const mStr = String(currentCalMonth + 1).padStart(2, '0');
            const dStr = String(day).padStart(2, '0');
            const dateStr = `${currentCalYear}-${mStr}-${dStr}`;

            const isCompleted = checkinDates.has(dateStr);
            const isToday = (dateStr === todayStr);
            const isSelected = (dateStr === selectedDateStr);

            let cellClass = 'w-9 h-9 sm:w-10 sm:h-10 rounded-2xl flex flex-col items-center justify-center text-xs font-semibold transition cursor-pointer relative ';
            if (isSelected) {
                cellClass += 'ring-2 ring-[#166545] font-bold ';
            }

            let badgeHtml = '';
            if (isCompleted) {
                badgeHtml = `<span class="text-[10px] text-[#166545] font-extrabold">✓</span>`;
                cellClass += 'bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA] ';
            } else {
                cellClass += 'text-stone-700 hover:bg-stone-100 border border-transparent ';
            }

            if (isToday) {
                badgeHtml += `<span class="w-1 h-1 rounded-full bg-[#166545] absolute bottom-1"></span>`;
            }

            cells.push(`
                <button type="button" onclick="window.TempoSelfCheckHistory.selectDate('${dateStr}')"
                        class="${cellClass}" title="${dateStr}">
                    <span>${day}</span>
                    ${badgeHtml}
                </button>
            `);
        }

        return `
            <div class="space-y-1">
                <div class="grid grid-cols-7 text-center text-[10px] font-bold uppercase tracking-wider text-stone-400 pb-1">
                    ${weekdays.map(w => `<div>${w}</div>`).join('')}
                </div>
                <div class="grid grid-cols-7 gap-1 place-items-center">
                    ${cells.join('')}
                </div>
            </div>
        `;
    }

    function prevMonth() {
        currentCalMonth--;
        if (currentCalMonth < 0) {
            currentCalMonth = 11;
            currentCalYear--;
        }
        renderHistoryModal();
    }

    function nextMonth() {
        currentCalMonth++;
        if (currentCalMonth > 11) {
            currentCalMonth = 0;
            currentCalYear++;
        }
        renderHistoryModal();
    }

    function selectDate(dateStr) {
        selectedDateStr = dateStr;
        const panel = document.getElementById('selfcheck-day-detail-panel');
        if (panel) {
            panel.innerHTML = renderSelectedDayDetail();
        }
        // Also re-render calendar grid to update selection ring
        renderHistoryModal();
    }

    // =========================================================================
    // DAY OBSERVATION DETAIL PANEL
    // =========================================================================

    function renderSelectedDayDetail() {
        const dateStr = selectedDateStr;
        const checkins = window.TempoRecoverySelfCheck ? window.TempoRecoverySelfCheck.getDailyCheckins() : [];
        const checkin = checkins.find(c => c.checkin_date === dateStr);

        const formattedDate = formatDisplayDate(dateStr);

        if (!checkin) {
            return `
                <div class="space-y-1">
                    <span class="text-[11px] font-bold uppercase tracking-wider text-stone-400">${formattedDate}</span>
                    <h5 class="text-xs font-bold text-[#202124]">No check-in</h5>
                    <p class="text-xs text-[#6F6B68]">You didn't finish a Self-check on this day.</p>
                </div>
            `;
        }

        const observations = window.TempoRecoverySelfCheck.getObservationsForCheckin(checkin.id);
        const activeTrackers = window.TempoRecoverySelfCheck.getActiveTrackers();
        const allTrackers = window.TempoRecoverySelfCheck.getTrackers(true); // include archived so past observations remain readable
        const trackerMap = new Map(allTrackers.map(t => [t.id, t]));

        const groups = [
            { category: 'stress_sign', label: 'Signs of stress', icon: '🔴' },
            { category: 'supportive', label: 'Supportive', icon: '🟢' },
            { category: 'neutral', label: 'General', icon: '🔵' }
        ];

        let obsHtml = '';
        groups.forEach(g => {
            const groupObs = observations.filter(o => {
                const trk = trackerMap.get(o.tracker_id);
                return trk && trk.category === g.category;
            });

            if (groupObs.length === 0) return;

            obsHtml += `
                <div class="space-y-2">
                    <span class="text-[11px] font-bold text-stone-500 uppercase tracking-wide flex items-center space-x-1">
                        <span>${g.icon}</span>
                        <span>${g.label}</span>
                    </span>
                    <div class="space-y-1.5">
                        ${groupObs.map(o => {
                            const trk = trackerMap.get(o.tracker_id);
                            const name = trk ? trk.name : 'Tracker';
                            let valueDisplay = '';

                            if (o.status === 'answered') {
                                if (trk && trk.check_method === 'yes_no') {
                                    valueDisplay = `<span class="font-bold text-[#166545]">${o.value ? 'Yes' : 'No'}</span>`;
                                } else if (trk && trk.check_method === 'scale') {
                                    valueDisplay = `<span class="font-bold text-[#166545]">${o.value} / ${trk.scale_max || 5}</span>`;
                                } else if (trk && trk.check_method === 'percentage') {
                                    valueDisplay = `<span class="font-bold text-[#166545]">${o.value}%</span>`;
                                } else if (trk && trk.check_method === 'quantity') {
                                    valueDisplay = `<span class="font-bold text-[#166545]">${o.value} ${escapeHTML(trk.quantity_unit || '')}</span>`;
                                } else {
                                    valueDisplay = `<span class="font-bold text-[#166545]">${o.value}</span>`;
                                }
                            } else if (o.status === 'skipped') {
                                valueDisplay = `<span class="text-stone-400 italic">Skipped</span>`;
                            } else {
                                valueDisplay = `<span class="text-stone-400 italic">Not answered</span>`;
                            }

                            const noteHtml = o.note ? `<p class="text-[11px] text-stone-500 italic pt-0.5">"${escapeHTML(o.note)}"</p>` : '';

                            return `
                                <div class="p-3 rounded-2xl bg-white border border-stone-200 flex flex-col space-y-0.5">
                                    <div class="flex items-center justify-between text-xs">
                                        <span class="font-bold text-[#202124]">${escapeHTML(name)}</span>
                                        <div>${valueDisplay}</div>
                                    </div>
                                    ${noteHtml}
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        });

        const overallNoteHtml = checkin.overall_note ? `
            <div class="p-3 rounded-2xl bg-white border border-stone-200 space-y-1">
                <span class="text-[10px] font-bold text-stone-400 uppercase tracking-wider">Overall Daily Note</span>
                <p class="text-xs text-[#202124] italic">"${escapeHTML(checkin.overall_note)}"</p>
            </div>
        ` : '';

        return `
            <div class="space-y-3">
                <div class="flex items-center justify-between border-b border-stone-200/80 pb-2">
                    <span class="text-xs font-bold text-[#202124]">${formattedDate}</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA]">
                        ✓ Completed Check-in
                    </span>
                </div>
                ${obsHtml || '<p class="text-xs text-stone-400">No observations recorded.</p>'}
                ${overallNoteHtml}
            </div>
        `;
    }

    // =========================================================================
    // YOUR TRACKERS LIST (IN HISTORY)
    // =========================================================================

    function renderYourTrackersList() {
        if (!window.TempoRecoverySelfCheck) return '';
        const activeTrackers = window.TempoRecoverySelfCheck.getActiveTrackers();
        if (activeTrackers.length === 0) {
            return `<p class="text-xs text-stone-400">No active trackers configured.</p>`;
        }

        const groups = [
            { category: 'stress_sign', label: 'Signs of stress', icon: '🔴' },
            { category: 'supportive', label: 'Supportive', icon: '🟢' },
            { category: 'neutral', label: 'General', icon: '🔵' }
        ];

        let html = '';
        groups.forEach(g => {
            const trks = activeTrackers.filter(t => t.category === g.category);
            if (trks.length === 0) return;

            html += `
                <div class="space-y-2">
                    <span class="text-[11px] font-bold text-stone-500 uppercase tracking-wide flex items-center space-x-1">
                        <span>${g.icon}</span>
                        <span>${g.label}</span>
                    </span>
                    <div class="space-y-2">
                        ${trks.map(t => {
                            const obsList = window.TempoSelfCheckPatterns
                                ? window.TempoSelfCheckPatterns.getChronologicalObservations(t.id)
                                : [];
                            const latest = obsList.length > 0 ? obsList[obsList.length - 1] : null;

                            let lastObsText = 'No check-ins yet';
                            if (latest) {
                                let valStr = latest.value;
                                if (t.check_method === 'yes_no') valStr = latest.value ? 'Yes' : 'No';
                                else if (t.check_method === 'scale') valStr = `${latest.value} / ${t.scale_max || 5}`;
                                else if (t.check_method === 'percentage') valStr = `${latest.value}%`;
                                else if (t.check_method === 'quantity') valStr = `${latest.value} ${t.quantity_unit || ''}`.trim();

                                lastObsText = `Last: ${valStr} · ${formatDisplayDate(latest.date)}`;
                            }

                            return `
                                <div class="p-3.5 rounded-2xl bg-white border border-stone-200 flex items-center justify-between shadow-2xs hover:border-stone-300 transition">
                                    <div class="space-y-0.5">
                                        <h5 class="text-xs font-bold text-[#202124]">${escapeHTML(t.name)}</h5>
                                        <p class="text-[11px] text-stone-400">${escapeHTML(lastObsText)}</p>
                                    </div>
                                    <button type="button" onclick="window.TempoSelfCheckHistory.openTrackerDetail('${t.id}')"
                                            class="text-xs font-bold text-[#166545] hover:text-[#0E4A32] transition cursor-pointer flex items-center space-x-1">
                                        <span>View history</span>
                                        <span>→</span>
                                    </button>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        });

        return html;
    }

    // =========================================================================
    // TRACKER DETAIL VIEW (OCCURRENCE LIST OR SVG RAW CHART)
    // =========================================================================

    function openTrackerDetail(trackerId) {
        currentHistoryView = 'tracker_detail';
        selectedTrackerId = trackerId;
        renderHistoryModal();
    }

    function closeTrackerDetail() {
        currentHistoryView = 'overview';
        selectedTrackerId = null;
        renderHistoryModal();
    }

    function renderTrackerDetailView(container, trackerId) {
        const tracker = window.TempoRecoverySelfCheck ? window.TempoRecoverySelfCheck.getTrackerById(trackerId) : null;
        if (!tracker) {
            closeTrackerDetail();
            return;
        }

        const obsList = window.TempoSelfCheckPatterns
            ? window.TempoSelfCheckPatterns.getChronologicalObservations(tracker.id)
            : [];

        // Linked recovery note snippet
        let linkedNoteHtml = '';
        if (tracker.linked_note_item_ids && tracker.linked_note_item_ids.length > 0 && window.TempoRecoveryNote) {
            const allNotes = window.TempoRecoveryNote.getItems();
            const linked = allNotes.find(n => tracker.linked_note_item_ids.includes(n.id));
            if (linked) {
                linkedNoteHtml = `
                    <div class="p-4 rounded-2xl bg-[#FFFBF7] border border-[#FFD2BA] space-y-1">
                        <div class="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-[#FF6B2C]">
                            <span>FROM YOUR RECOVERY NOTE</span>
                            <button type="button" onclick="window.TempoRecoverySelfCheck.openTrackerModal('${tracker.id}')" class="underline hover:text-[#B83D08]">
                                Edit link
                            </button>
                        </div>
                        <p class="text-xs text-[#202124] italic font-medium">"${escapeHTML(linked.text)}"</p>
                    </div>
                `;
            }
        }

        container.innerHTML = `
            <div class="space-y-6">
                <!-- Top Nav & Header -->
                <div class="space-y-3">
                    <button type="button" onclick="window.TempoSelfCheckHistory.closeTrackerDetail()"
                            class="text-xs font-semibold text-[#166545] hover:text-[#0E4A32] transition cursor-pointer flex items-center space-x-1">
                        <span>← Back to check-ins</span>
                    </button>
                    <div class="flex items-center justify-between">
                        <div class="space-y-1">
                            <div class="flex items-center space-x-2">
                                <span>${tracker.category === 'stress_sign' ? '🔴' : (tracker.category === 'supportive' ? '🟢' : '🔵')}</span>
                                <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">${escapeHTML(tracker.name)}</h3>
                            </div>
                            <span class="text-xs text-[#6F6B68]">
                                ${tracker.category === 'stress_sign' ? 'Sign of stress' : (tracker.category === 'supportive' ? 'Supportive' : 'General')} · ${tracker.check_method}
                            </span>
                        </div>
                        <button type="button" onclick="window.TempoRecoverySelfCheck.openTrackerModal('${tracker.id}')"
                                class="btn-primary px-3.5 py-1.5 rounded-xl text-xs font-bold shadow-xs transition cursor-pointer">
                            Edit tracker
                        </button>
                    </div>
                </div>

                ${linkedNoteHtml}

                <!-- Visual History Presentation by Method -->
                <div class="p-5 rounded-3xl border border-stone-200 bg-white space-y-4 shadow-2xs">
                    <h4 class="text-xs font-extrabold uppercase tracking-wider text-stone-500">History Over Time</h4>
                    ${renderMethodSpecificHistory(tracker, obsList)}
                </div>
            </div>
        `;
    }

    function renderMethodSpecificHistory(tracker, obsList) {
        if (obsList.length === 0) {
            return `<p class="text-xs text-stone-400 italic">No check-ins recorded yet for this tracker.</p>`;
        }

        // 1. YES / NO: Occurrence table/list (NEVER misleading continuous line chart)
        if (tracker.check_method === 'yes_no') {
            return `
                <div class="space-y-2">
                    <div class="divide-y divide-stone-100 border border-stone-200 rounded-2xl overflow-hidden">
                        ${[...obsList].reverse().map(o => `
                            <div class="p-3 flex items-center justify-between text-xs bg-white">
                                <span class="font-medium text-stone-600">${formatDisplayDate(o.date)}</span>
                                <div class="flex items-center space-x-2">
                                    <span class="font-bold ${o.value ? 'text-[#B83D08]' : 'text-stone-400'}">${o.value ? 'Yes' : 'No'}</span>
                                    ${o.note ? `<span class="text-[11px] text-stone-400 italic">("${escapeHTML(o.note)}")</span>` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // 2. SCALE / PERCENTAGE / QUANTITY: Lightweight SVG Chart + Table
        const isPercentage = tracker.check_method === 'percentage';
        const isScale = tracker.check_method === 'scale';
        const isQuantity = tracker.check_method === 'quantity';

        const maxY = isPercentage ? 100 : (isScale ? (tracker.scale_max || 5) : Math.max(...obsList.map(o => Number(o.value) || 1), 5));
        const minY = isPercentage ? 0 : (isScale ? (tracker.scale_min || 1) : 0);

        const width = 450;
        const height = 140;
        const pad = 24;

        const points = obsList.map((o, idx) => {
            const x = pad + (idx / Math.max(obsList.length - 1, 1)) * (width - 2 * pad);
            const val = Number(o.value) || 0;
            const normY = (val - minY) / Math.max(maxY - minY, 1);
            const y = height - pad - normY * (height - 2 * pad);
            return { x, y, val, date: o.date };
        });

        const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');

        return `
            <div class="space-y-4">
                <!-- SVG Chart -->
                <div class="w-full overflow-x-auto">
                    <svg viewBox="0 0 ${width} ${height}" class="w-full max-w-full h-auto">
                        <!-- Horizontal baseline ticks -->
                        <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="#EAE4DF" stroke-width="1" />
                        <line x1="${pad}" y1="${pad}" x2="${width - pad}" y2="${pad}" stroke="#EAE4DF" stroke-dasharray="3 3" stroke-width="1" />
                        
                        <!-- Axis Labels -->
                        <text x="${pad - 4}" y="${height - pad + 3}" font-size="9" fill="#A8A29E" text-anchor="end">${minY}</text>
                        <text x="${pad - 4}" y="${pad + 3}" font-size="9" fill="#A8A29E" text-anchor="end">${maxY}</text>

                        <!-- Line path -->
                        <path d="${pathD}" fill="none" stroke="#166545" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />

                        <!-- Data Dots -->
                        ${points.map(p => `
                            <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4" fill="#166545" stroke="#ffffff" stroke-width="2" />
                        `).join('')}
                    </svg>
                </div>

                <!-- History Records List -->
                <div class="divide-y divide-stone-100 border border-stone-200 rounded-2xl overflow-hidden max-h-48 overflow-y-auto">
                    ${[...obsList].reverse().map(o => {
                        let displayVal = `${o.value}`;
                        if (isPercentage) displayVal = `${o.value}%`;
                        else if (isScale) displayVal = `${o.value} / ${tracker.scale_max || 5}`;
                        else if (isQuantity) displayVal = `${o.value} ${tracker.quantity_unit || ''}`.trim();

                        return `
                            <div class="p-3 flex items-center justify-between text-xs bg-white">
                                <span class="font-medium text-stone-600">${formatDisplayDate(o.date)}</span>
                                <div class="flex items-center space-x-2">
                                    <span class="font-bold text-[#166545]">${displayVal}</span>
                                    ${o.note ? `<span class="text-[11px] text-stone-400 italic">("${escapeHTML(o.note)}")</span>` : ''}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

    function launchCheckin() {
        close();
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openDailyCheckin === 'function') {
            window.TempoRecoverySelfCheck.openDailyCheckin(false);
        }
    }

    // =========================================================================
    // RECENTLY CARD ON RECOVERY HOME (STATES 1, 2, 3, AND 4: SOMETHING TO NOTICE)
    // =========================================================================

    function renderRecentlyCard() {
        const checkins = window.TempoRecoverySelfCheck ? window.TempoRecoverySelfCheck.getDailyCheckins() : [];
        const checkinCount = checkins.length;

        // STATE 1: NO HISTORY (0 check-ins)
        if (checkinCount === 0) {
            return `
                <div class="recovery-card-recently bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-4 shadow-xs flex flex-col justify-between h-full">
                    <div class="space-y-3">
                        <div class="flex items-center space-x-2">
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#6F6B68]">RECENTLY</span>
                        </div>
                        <h4 class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">Nothing here yet.</h4>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                            Once you start checking in, this space can help you look back at what you've been noticing over time.
                        </p>
                    </div>
                    <div class="pt-4 border-t border-stone-100 text-[11px] text-[#6F6B68]">
                        <span>Nothing needs to be recorded until you're ready.</span>
                    </div>
                </div>
            `;
        }

        // STATE 2: INSUFFICIENT HISTORY (1–2 check-ins)
        if (checkinCount < 3) {
            return `
                <div class="recovery-card-recently bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-4 shadow-xs flex flex-col justify-between h-full">
                    <div class="space-y-3">
                        <div class="flex items-center space-x-2">
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#6F6B68]">RECENTLY</span>
                        </div>
                        <h4 class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">You're just getting started.</h4>
                        <p class="text-xs text-[#6F6B68] leading-relaxed">
                            There's not enough history to compare yet. Keep checking in and your patterns will show up here.
                        </p>
                    </div>
                    <div class="pt-3 border-t border-stone-100">
                        <button type="button" onclick="window.TempoSelfCheckHistory.open()"
                                class="text-xs font-bold text-[#166545] hover:text-[#0E4A32] transition cursor-pointer flex items-center space-x-1">
                            <span>View history</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>
            `;
        }

        // Check for active notice candidate
        const activeNotice = window.TempoSelfCheckPatterns ? window.TempoSelfCheckPatterns.getActiveNotice() : null;

        // STATE 4: SOMETHING TO NOTICE (Warm peach/soft sand card)
        if (activeNotice) {
            const linkedReminder = activeNotice.linkedNoteItem
                ? `<div class="p-3 bg-white/70 rounded-2xl border border-[#FFD2BA]/70 space-y-0.5">
                     <span class="text-[10px] font-bold text-[#B83D08] uppercase tracking-wider">You wanted to remember</span>
                     <p class="text-xs text-[#202124] italic font-medium">"${escapeHTML(activeNotice.linkedNoteItem.text)}"</p>
                   </div>`
                : '';

            return `
                <div class="recovery-card-something-notice bg-gradient-to-br from-[#FFFBF7] to-[#FFF5EC] border-2 border-[#FFD2BA] rounded-3xl p-6 space-y-4 shadow-xs">
                    <div class="flex items-center space-x-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-[#B83D08] inline-block animate-pulse"></span>
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#B83D08]">
                            SOMETHING TO NOTICE
                        </span>
                    </div>

                    <div class="space-y-1.5">
                        <h4 class="font-heading text-base font-extrabold text-[#202124]">
                            ${escapeHTML(activeNotice.message)}
                        </h4>
                    </div>

                    ${linkedReminder}

                    <!-- Actions -->
                    <div class="pt-2 flex flex-wrap items-center gap-2.5">
                        <button type="button" onclick="window.TempoStressRelief ? window.TempoStressRelief.openModal() : null"
                                class="btn-primary px-3.5 py-2 rounded-xl text-xs font-bold shadow-xs transition cursor-pointer">
                            Quick Relief →
                        </button>
                        ${activeNotice.linkedNoteItem ? `
                            <button type="button" onclick="window.TempoRecoveryNote ? window.TempoRecoveryNote.openViewModal() : null"
                                    class="px-3.5 py-2 rounded-xl bg-white border border-[#FFD2BA] text-xs font-bold text-[#B83D08] hover:bg-[#FFF5EC] transition cursor-pointer">
                                View Recovery Note
                            </button>
                        ` : `
                            <button type="button" onclick="window.TempoSelfCheckHistory.open('${activeNotice.trackerId}')"
                                    class="px-3.5 py-2 rounded-xl bg-white border border-[#FFD2BA] text-xs font-bold text-[#B83D08] hover:bg-[#FFF5EC] transition cursor-pointer">
                                View history
                            </button>
                        `}
                    </div>

                    <!-- Cooldown Controls -->
                    <div class="pt-2 flex items-center space-x-3 text-xs text-stone-400">
                        <button type="button" onclick="window.TempoSelfCheckPatterns.snoozeNotice('${activeNotice.trackerId}')"
                                class="hover:text-stone-700 transition cursor-pointer">
                            Remind me later
                        </button>
                        <span>·</span>
                        <button type="button" onclick="window.TempoSelfCheckPatterns.dismissNotice('${activeNotice.trackerId}')"
                                class="hover:text-stone-700 transition cursor-pointer">
                            Dismiss
                        </button>
                    </div>
                </div>
            `;
        }

        // STATE 3: NORMAL HISTORY (2–3 concise descriptive observations)
        const observations = window.TempoSelfCheckPatterns ? window.TempoSelfCheckPatterns.getRecentlyObservations() : [];

        return `
            <div class="recovery-card-recently bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-4 shadow-xs flex flex-col justify-between h-full">
                <div class="space-y-3">
                    <div class="flex items-center space-x-2">
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#6F6B68]">RECENTLY</span>
                    </div>
                    <div class="space-y-2.5">
                        ${observations.length > 0 ? observations.map(obs => `
                            <div class="space-y-0.5">
                                <h5 class="text-xs font-bold text-[#202124] flex items-center space-x-1.5">
                                    <span>${obs.icon}</span>
                                    <span>${escapeHTML(obs.trackerName)}</span>
                                </h5>
                                <p class="text-xs text-[#6F6B68] pl-4">${escapeHTML(obs.summary)}</p>
                            </div>
                        `).join('') : `
                            <p class="text-xs text-[#6F6B68]">Patterns are tracking steadily.</p>
                        `}
                    </div>
                </div>
                <div class="pt-3 border-t border-stone-100">
                    <button type="button" onclick="window.TempoSelfCheckHistory.open()"
                            class="text-xs font-bold text-[#166545] hover:text-[#0E4A32] transition cursor-pointer flex items-center space-x-1">
                        <span>View history</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
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

    function init() {
        ensureModalMounted();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.TempoSelfCheckHistory = {
        init,
        open,
        close,
        switchTab,
        prevMonth,
        nextMonth,
        selectDate,
        openTrackerDetail,
        closeTrackerDetail,
        launchCheckin,
        renderRecentlyCard
    };

})();
