/**
 * TEMPO WELLBEING — WEEKLY REVIEW (PHASE 5)
 * File: weeklyReview.js
 *
 * Architecture:
 * 1. Tempo-level journey recap (independent of modes, survives mode switches).
 * 2. Strict separation:
 *    - Derived Weekly Recap: dynamically derived from authoritative source data (check-ins, tasks, patterns).
 *    - User Weekly Reflection: persistent, user-authored (comparison, differences, note).
 * 3. Week definition: Monday → Sunday. A completed week becomes reviewable once Sunday ends.
 * 4. Readiness:
 *    - Evaluates most recent completed week.
 *    - Gracefully adapts to sparse data.
 *    - "Maybe later" dismisses Home card for the session without deleting review opportunity.
 * 5. Stepped Review Flow:
 *    Step 1: Your Week
 *    Step 2: Things You Got Through
 *    Step 3: Your Check-ins
 *    Step 4: Things Tempo Noticed
 *    Step 5: Looking Back (with last-week continuity)
 *    Step 6: Finish (calm reflection of user's answer)
 * 6. History Integration:
 *    - Fully populates the [ Weekly Reviews ] tab in the Self-check/History modal.
 *    - Past reviews viewable and editable without creating duplicates.
 */

(function () {
    'use strict';

    const COMPARISON_OPTIONS = [
        { value: 'much_harder', label: 'Much harder', icon: '↘' },
        { value: 'little_harder', label: 'A little harder', icon: '↘' },
        { value: 'same', label: 'About the same', icon: '→' },
        { value: 'little_better', label: 'A little better', icon: '↗' },
        { value: 'much_better', label: 'Much better', icon: '↗' },
        { value: 'unsure', label: "I'm not sure", icon: '·' }
    ];

    const DIFFERENCE_SUGGESTIONS = [
        "I feel less overwhelmed",
        "I feel more in control",
        "I have more energy",
        "It's easier to focus",
        "I'm resting better",
        "Things still feel heavy",
        "I'm more overwhelmed"
    ];

    // Current active review in-memory state
    let activeFlowState = null;

    // =========================================================================
    // USER & STORAGE HELPERS
    // =========================================================================

    function getUserId() {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') {
            const uid = window.TempoAuth.getCurrentUserId();
            if (uid) return uid;
        }
        return 'local_user';
    }

    function getStorageKey() {
        const uid = getUserId();
        return `tempo_weekly_reflections_${uid}`;
    }

    function getDismissKey(weekStart) {
        const uid = getUserId();
        return `tempo_weekly_review_dismissed_${uid}_${weekStart}`;
    }

    function loadReflections() {
        try {
            const key = getStorageKey();
            const raw = localStorage.getItem(key);
            if (raw) return JSON.parse(raw);
        } catch (e) {
            console.warn("[WeeklyReview] Error reading reflections:", e);
        }
        return [];
    }

    function saveReflections(list) {
        try {
            const key = getStorageKey();
            localStorage.setItem(key, JSON.stringify(list));
        } catch (e) {
            console.warn("[WeeklyReview] Error saving reflections:", e);
        }
    }

    function getReflectionForWeek(weekStart) {
        const list = loadReflections();
        return list.find(r => r.week_start === weekStart) || null;
    }

    function getPreviousReflection(weekStart) {
        try {
            const [y, m, d] = weekStart.split('-').map(Number);
            const dt = new Date(y, m - 1, d);
            dt.setDate(dt.getDate() - 7);
            const prevStart = toISODate(dt);
            return getReflectionForWeek(prevStart);
        } catch (e) {
            return null;
        }
    }

    function saveUserReflection(payload) {
        const list = loadReflections();
        const existingIdx = list.findIndex(r => r.week_start === payload.week_start);

        let savedRecord;
        const nowIso = new Date().toISOString();

        if (existingIdx !== -1) {
            // Update in place — NEVER duplicate for the same week
            savedRecord = {
                ...list[existingIdx],
                comparison: payload.comparison !== undefined ? payload.comparison : list[existingIdx].comparison,
                difference_items: payload.difference_items !== undefined ? payload.difference_items : (list[existingIdx].difference_items || []),
                custom_difference_items: payload.custom_difference_items !== undefined ? payload.custom_difference_items : (list[existingIdx].custom_difference_items || []),
                user_note: payload.user_note !== undefined ? payload.user_note : (list[existingIdx].user_note || ''),
                reviewed_at: nowIso,
                updated_at: nowIso
            };
            list[existingIdx] = savedRecord;
        } else {
            savedRecord = {
                id: 'wref_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
                user_id: getUserId(),
                week_start: payload.week_start,
                week_end: payload.week_end,
                comparison: payload.comparison || null,
                difference_items: payload.difference_items || [],
                custom_difference_items: payload.custom_difference_items || [],
                user_note: payload.user_note || '',
                reviewed_at: nowIso,
                created_at: nowIso,
                updated_at: nowIso
            };
            list.push(savedRecord);
        }

        saveReflections(list);

        // Async sync to Supabase if connected
        syncReflectionToSupabase(savedRecord);

        // Notify mode or UI to re-render
        if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
            if (window.TempoMode.getMode() === 'recovery') {
                window.TempoMode.renderRmodeHome();
            }
        }

        return savedRecord;
    }

    async function syncReflectionToSupabase(record) {
        if (!window.TempoSupabase || typeof window.TempoSupabase.getClient !== 'function') return;
        const sb = window.TempoSupabase.getClient();
        if (!sb || !window.TempoAuth || !window.TempoAuth.getCurrentUserId()) return;

        try {
            const uid = window.TempoAuth.getCurrentUserId();
            await sb.from('weekly_reflections').upsert([{
                id: record.id.startsWith('wref_') ? undefined : record.id,
                user_id: uid,
                week_start: record.week_start,
                week_end: record.week_end,
                comparison: record.comparison,
                difference_items: record.difference_items || [],
                custom_difference_items: record.custom_difference_items || [],
                user_note: record.user_note,
                reviewed_at: record.reviewed_at,
                updated_at: record.updated_at
            }], { onConflict: 'user_id,week_start' });
        } catch (e) {
            console.warn("[WeeklyReview] Supabase sync notice (safe local fallback active):", e);
        }
    }

    function isNoticeDismissed(weekStart) {
        try {
            return localStorage.getItem(getDismissKey(weekStart)) === 'true';
        } catch (e) {
            return false;
        }
    }

    function snoozeOrDismissNotice(weekStart) {
        try {
            localStorage.setItem(getDismissKey(weekStart), 'true');
        } catch (e) {}
        if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
            window.TempoMode.renderRmodeHome();
        }
    }

    // =========================================================================
    // CALENDAR & WEEK CALCULATION UTILITIES
    // =========================================================================

    function toISODate(d) {
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
    }

    function getMondayOfDate(d) {
        const date = new Date(d.getFullYear(), d.getMonth(), d.getDate());
        const day = date.getDay(); // 0 is Sunday, 1 is Monday
        const diff = (day === 0 ? -6 : 1) - day;
        date.setDate(date.getDate() + diff);
        return date;
    }

    function formatWeekRange(startStr, endStr) {
        if (!startStr || !endStr) return '';
        try {
            const [sy, sm, sd] = startStr.split('-').map(Number);
            const [ey, em, ed] = endStr.split('-').map(Number);
            const sDate = new Date(sy, sm - 1, sd);
            const eDate = new Date(ey, em - 1, ed);

            const startPart = sDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            const endPart = eDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            return `${startPart} – ${endPart}`;
        } catch (e) {
            return `${startStr} – ${endStr}`;
        }
    }

    /**
     * Returns an array of past COMPLETED weeks (Monday -> Sunday).
     * The current unfinished week is NOT included.
     */
    function getCompletedWeeks(count = 4) {
        const now = new Date();
        const currentMonday = getMondayOfDate(now);

        const weeks = [];
        for (let i = 1; i <= count; i++) {
            const m = new Date(currentMonday);
            m.setDate(m.getDate() - (i * 7));
            const s = new Date(m);
            s.setDate(s.getDate() + 6);

            const startStr = toISODate(m);
            const endStr = toISODate(s);
            weeks.push({
                start: startStr,
                end: endStr,
                dateRange: formatWeekRange(startStr, endStr)
            });
        }
        return weeks;
    }

    function getLatestEligibleWeek() {
        const completed = getCompletedWeeks(1);
        return completed.length > 0 ? completed[0] : null;
    }

    function isReady() {
        const latest = getLatestEligibleWeek();
        if (!latest) return false;

        // If already reviewed, do NOT show the large ready card on Home
        const existing = getReflectionForWeek(latest.start);
        if (existing) return false;

        // If user dismissed/snoozed "Maybe later" for this week, suppress the Home card
        if (isNoticeDismissed(latest.start)) return false;

        return true;
    }

    // =========================================================================
    // AUTHORITATIVE DERIVED RECAP ENGINE
    // =========================================================================

    function deriveRecap(weekStart, weekEnd) {
        // 1. CHECK-INS & DAYS
        const allCheckins = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getDailyCheckins === 'function')
            ? window.TempoRecoverySelfCheck.getDailyCheckins()
            : [];

        const weekCheckins = allCheckins.filter(c => c.checkin_date >= weekStart && c.checkin_date <= weekEnd);
        const checkinDateSet = new Set(weekCheckins.map(c => c.checkin_date));
        const checkinCount = weekCheckins.length;

        // Generate 7-day row
        const dayNames = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
        const dayDots = [];
        const [sy, sm, sd] = weekStart.split('-').map(Number);
        for (let i = 0; i < 7; i++) {
            const dt = new Date(sy, sm - 1, sd + i);
            const iso = toISODate(dt);
            dayDots.push({
                dayLabel: dayNames[i],
                dateStr: iso,
                hasCheckin: checkinDateSet.has(iso)
            });
        }

        // Tracker summaries for the week
        const allTrackers = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackers === 'function')
            ? window.TempoRecoverySelfCheck.getTrackers(true)
            : [];

        const trackerSummaries = [];
        allTrackers.forEach(trk => {
            const obsForTracker = [];
            weekCheckins.forEach(chk => {
                const obsList = window.TempoRecoverySelfCheck.getObservationsForCheckin(chk.id);
                const match = obsList.find(o => o.tracker_id === trk.id && o.status === 'answered' && o.value !== null && o.value !== undefined);
                if (match) obsForTracker.push(match);
            });

            if (obsForTracker.length === 0) return;

            let summaryText = '';
            if (trk.check_method === 'yes_no') {
                const yesCount = obsForTracker.filter(o => o.value === true).length;
                if (trk.category === 'stress_sign') {
                    summaryText = `Showed up on ${yesCount} check-in${yesCount === 1 ? '' : 's'}`;
                } else {
                    summaryText = `Marked Yes on ${yesCount} check-in${yesCount === 1 ? '' : 's'}`;
                }
            } else if (trk.check_method === 'scale') {
                const values = obsForTracker.map(o => Number(o.value)).filter(v => !isNaN(v));
                if (values.length > 0) {
                    const min = Math.min(...values);
                    const max = Math.max(...values);
                    const rangeStr = (min === max) ? `${min}` : `${min}–${max}`;
                    summaryText = `Ranged from ${rangeStr} / ${trk.scale_max || 5}`;
                }
            } else if (trk.check_method === 'percentage') {
                const values = obsForTracker.map(o => Number(o.value)).filter(v => !isNaN(v));
                if (values.length > 0) {
                    const min = Math.min(...values);
                    const max = Math.max(...values);
                    const rangeStr = (min === max) ? `${min}%` : `${min}–${max}%`;
                    summaryText = `Recent values ranged from ${rangeStr}`;
                }
            } else if (trk.check_method === 'quantity') {
                const values = obsForTracker.map(o => Number(o.value)).filter(v => !isNaN(v));
                if (values.length > 0) {
                    const min = Math.min(...values);
                    const max = Math.max(...values);
                    const unit = trk.quantity_unit ? ` ${trk.quantity_unit}` : '';
                    const rangeStr = (min === max) ? `${min}${unit}` : `${min}–${max}${unit}`;
                    summaryText = `Recorded between ${rangeStr}`;
                }
            }

            if (summaryText) {
                const icon = trk.category === 'stress_sign' ? '🔴' : (trk.category === 'supportive' ? '🟢' : '🔵');
                trackerSummaries.push({
                    trackerId: trk.id,
                    name: trk.name,
                    category: trk.category,
                    icon,
                    summary: summaryText,
                    count: obsForTracker.length
                });
            }
        });

        // Limit to 3–5 representative summaries
        const selectedTrackerSummaries = trackerSummaries.slice(0, 5);

        // 2. SHARED TASKS
        let completedTasks = [];
        let carryoverTasks = [];
        let hasUrgentPlan = false;

        let plan = (window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function')
            ? window.TempoPlanStore.getActivePlan('emergency')
            : null;

        if (!plan && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            plan = window.TempoEmergencyFlow.getConfirmedPlan();
        }

        if (!plan) {
            try {
                const keys = [
                    'tempo_store_active_emergency_local_user',
                    'tempo_store_active_emergency_guest',
                    'tempo_emergency_confirmed_plan'
                ];
                for (const k of keys) {
                    const raw = localStorage.getItem(k);
                    if (raw) {
                        plan = JSON.parse(raw);
                        break;
                    }
                }
            } catch (e) {}
        }

        if (plan && Array.isArray(plan.plannedTasks)) {
            hasUrgentPlan = true;
            plan.plannedTasks.forEach(pt => {
                if (!pt || !pt.task) return;
                const task = pt.task;
                const taskDate = pt.dayDate || pt.date || '';

                // Completed during target week
                if (task.completed) {
                    let compDate = task.completedAt || task.completed_at || task.updated_at || taskDate;
                    if (compDate && typeof compDate === 'string' && compDate.includes('T')) {
                        compDate = compDate.split('T')[0];
                    }
                    if (compDate >= weekStart && compDate <= weekEnd) {
                        completedTasks.push({
                            id: task.id,
                            name: task.name,
                            completedDate: compDate
                        });
                    }
                } else {
                    // Carryover / in progress
                    if (taskDate >= weekStart && taskDate <= weekEnd) {
                        carryoverTasks.push({
                            id: task.id,
                            name: task.name
                        });
                    }
                }
            });
        }

        // 3. THINGS TEMPO NOTICED (REUSES PHASE 4 ENGINE)
        let noticePattern = null;
        let linkedRecoveryNoteItem = null;

        if (window.TempoSelfCheckPatterns && typeof window.TempoSelfCheckPatterns.analyzeTracker === 'function') {
            for (const trk of allTrackers) {
                if (trk.category !== 'stress_sign') continue;
                const analysis = window.TempoSelfCheckPatterns.analyzeTracker(trk);
                if (analysis && (analysis.status === 'notice_candidate' || analysis.status === 'descriptive_change') && analysis.detailedNotice) {
                    noticePattern = {
                        trackerName: trk.name,
                        message: analysis.detailedNotice
                    };

                    if (trk.linked_note_item_ids && trk.linked_note_item_ids.length > 0 && window.TempoRecoveryNote) {
                        const allNotes = window.TempoRecoveryNote.getItems() || [];
                        const found = allNotes.find(it => trk.linked_note_item_ids.includes(it.id));
                        if (found) {
                            linkedRecoveryNoteItem = found;
                        }
                    }
                    break;
                }
            }
        }

        const hasMeaningfulData = checkinCount > 0 || completedTasks.length > 0;

        return {
            weekStart,
            weekEnd,
            dateRange: formatWeekRange(weekStart, weekEnd),
            checkinCount,
            dayDots,
            trackerSummaries: selectedTrackerSummaries,
            completedTasks,
            carryoverTasks,
            hasUrgentPlan,
            noticePattern,
            linkedRecoveryNoteItem,
            hasMeaningfulData
        };
    }

    // =========================================================================
    // MODAL SHELL MOUNTING & CONTROLLER
    // =========================================================================

    function ensureModalMounted() {
        if (document.getElementById('modal-weekly-review')) return;

        const modal = document.createElement('div');
        modal.id = 'modal-weekly-review';
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-3 sm:p-4 hidden';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.innerHTML = `
            <div class="tempo-card max-w-2xl w-full p-6 sm:p-8 space-y-6 bg-white rounded-3xl shadow-2xl relative border border-[#EAE4DF] max-h-[92vh] overflow-y-auto">
                <button type="button" onclick="window.TempoWeeklyReview.close()"
                        class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer" title="Close">✕</button>
                <div id="weekly-review-modal-content"></div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    function open(weekStart = null, isEditMode = false) {
        ensureModalMounted();

        // Default to latest eligible completed week if not specified
        const targetWeek = weekStart ? { start: weekStart, end: calculateWeekEnd(weekStart) } : getLatestEligibleWeek();
        if (!targetWeek) {
            if (window.TempoApp) window.TempoApp.showToast("No completed weeks available for review yet.");
            return;
        }

        const existingReflection = getReflectionForWeek(targetWeek.start);
        const recap = deriveRecap(targetWeek.start, targetWeek.end);

        // If existing and not explicitly editing, show the past review view
        if (existingReflection && !isEditMode) {
            renderPastReviewView(targetWeek.start);
            showModal();
            return;
        }

        // Initialize active review flow state
        activeFlowState = {
            step: 1, // 1 to 6
            weekStart: targetWeek.start,
            weekEnd: targetWeek.end,
            recap,
            isEditMode: !!isEditMode,
            draft: {
                comparison: existingReflection ? existingReflection.comparison : null,
                difference_items: existingReflection ? [...(existingReflection.difference_items || [])] : [],
                custom_difference_items: existingReflection ? [...(existingReflection.custom_difference_items || [])] : [],
                user_note: existingReflection ? (existingReflection.user_note || '') : ''
            }
        };

        renderStep();
        showModal();
    }

    function calculateWeekEnd(startStr) {
        const [y, m, d] = startStr.split('-').map(Number);
        const end = new Date(y, m - 1, d + 6);
        return toISODate(end);
    }

    function showModal() {
        const modal = document.getElementById('modal-weekly-review');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
        }
    }

    function close() {
        const modal = document.getElementById('modal-weekly-review');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
        activeFlowState = null;
    }

    function goToStep(stepNum) {
        if (!activeFlowState) return;
        activeFlowState.step = Math.max(1, Math.min(6, stepNum));
        renderStep();
    }

    // =========================================================================
    // STEPPED FLOW VIEWS (STEPS 1 TO 6)
    // =========================================================================

    function renderStep() {
        const container = document.getElementById('weekly-review-modal-content');
        if (!container || !activeFlowState) return;

        const { step, recap } = activeFlowState;

        switch (step) {
            case 1:
                renderStep1YourWeek(container, recap);
                break;
            case 2:
                renderStep2Tasks(container, recap);
                break;
            case 3:
                renderStep3Checkins(container, recap);
                break;
            case 4:
                renderStep4Noticed(container, recap);
                break;
            case 5:
                renderStep5LookingBack(container, recap);
                break;
            case 6:
                renderStep6Finish(container, recap);
                break;
            default:
                renderStep1YourWeek(container, recap);
        }
    }

    function renderProgressIndicator(currentStep, totalSteps = 6) {
        return `
            <div class="flex items-center space-x-1.5 pb-2">
                ${Array.from({ length: totalSteps }).map((_, i) => `
                    <div class="h-1 rounded-full flex-1 transition-all ${i + 1 <= currentStep ? 'bg-[#166545]' : 'bg-stone-200'}"></div>
                `).join('')}
            </div>
        `;
    }

    // STEP 1: YOUR WEEK
    function renderStep1YourWeek(container, recap) {
        container.innerHTML = `
            <div class="space-y-6">
                ${renderProgressIndicator(1)}

                <div class="space-y-1.5">
                    <div class="flex items-center space-x-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-[#166545] inline-block"></span>
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">YOUR WEEK</span>
                    </div>
                    <h3 class="font-heading text-2xl font-extrabold text-[#202124]">${escapeHTML(recap.dateRange)}</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">A quick look back at the week you just moved through.</p>
                </div>

                ${!recap.hasMeaningfulData ? `
                    <div class="p-6 rounded-2xl border border-stone-200 bg-stone-50/60 space-y-2 text-center">
                        <h4 class="text-xs font-bold uppercase tracking-wider text-stone-500">Not much to look back on yet</h4>
                        <p class="text-xs text-[#6F6B68]">There isn't much Tempo activity recorded from this week to recap. You can still add your reflection.</p>
                    </div>
                ` : `
                    <div class="grid grid-cols-2 gap-4">
                        <div class="p-5 rounded-2xl border border-stone-200 bg-white space-y-1">
                            <span class="font-heading text-3xl font-extrabold text-[#202124]">${recap.checkinCount}</span>
                            <p class="text-xs text-[#6F6B68] font-medium">check-in day${recap.checkinCount === 1 ? '' : 's'}</p>
                        </div>
                        <div class="p-5 rounded-2xl border border-stone-200 bg-white space-y-1">
                            <span class="font-heading text-3xl font-extrabold text-[#202124]">${recap.completedTasks.length}</span>
                            <p class="text-xs text-[#6F6B68] font-medium">task${recap.completedTasks.length === 1 ? '' : 's'} completed</p>
                        </div>
                    </div>
                `}

                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoWeeklyReview.close()"
                            class="px-4 py-2.5 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition cursor-pointer">
                        Leave for now
                    </button>
                    <button type="button" onclick="window.TempoWeeklyReview.goToStep(2)"
                            class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer flex items-center space-x-1.5">
                        <span>Things you got through</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    // STEP 2: THINGS YOU GOT THROUGH
    function renderStep2Tasks(container, recap) {
        container.innerHTML = `
            <div class="space-y-6">
                ${renderProgressIndicator(2)}

                <div class="space-y-1.5">
                    <div class="flex items-center space-x-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-[#166545] inline-block"></span>
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">THINGS YOU GOT THROUGH</span>
                    </div>
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">A few things you moved forward</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">Quiet steps that added up over the week.</p>
                </div>

                ${recap.hasUrgentPlan ? `
                    <div class="p-4 rounded-2xl bg-[#FFFBF7] border border-[#FFD2BA] space-y-1">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-[#B83D08]">Busy part of the week</span>
                        <p class="text-xs text-[#202124]">You used an Urgent Plan to work through a cluster of tasks and deadlines.</p>
                    </div>
                ` : ''}

                <div class="space-y-2">
                    ${recap.completedTasks.length > 0 ? `
                        <div class="space-y-1.5">
                            ${recap.completedTasks.map(t => `
                                <div class="p-3 rounded-2xl bg-white border border-stone-200 flex items-center justify-between">
                                    <div class="flex items-center space-x-2.5">
                                        <span class="text-xs font-bold text-[#166545]">✓</span>
                                        <span class="text-xs sm:text-sm font-semibold text-[#202124]">${escapeHTML(t.name)}</span>
                                    </div>
                                    ${t.completedDate ? `<span class="text-[11px] text-stone-400">${escapeHTML(formatDisplayShortDate(t.completedDate))}</span>` : ''}
                                </div>
                            `).join('')}
                        </div>
                    ` : `
                        <div class="p-5 rounded-2xl border border-dashed border-stone-200 text-center">
                            <p class="text-xs text-[#6F6B68]">No tasks recorded as completed in Tempo during this week.</p>
                        </div>
                    `}
                </div>

                ${recap.carryoverTasks.length > 0 ? `
                    <div class="space-y-2 pt-2 border-t border-stone-100">
                        <div class="space-y-0.5">
                            <span class="text-[11px] font-bold text-stone-500 uppercase tracking-wide">Still in progress</span>
                            <p class="text-[11px] text-[#6F6B68]">Some things are still moving with you into the next week.</p>
                        </div>
                        <div class="space-y-1">
                            ${recap.carryoverTasks.map(t => `
                                <div class="p-2.5 rounded-xl bg-stone-50 border border-stone-200 text-xs text-[#202124]">
                                    • ${escapeHTML(t.name)}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoWeeklyReview.goToStep(1)"
                            class="px-4 py-2.5 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition cursor-pointer">
                        ← Back
                    </button>
                    <button type="button" onclick="window.TempoWeeklyReview.goToStep(3)"
                            class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer flex items-center space-x-1.5">
                        <span>Your check-ins</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    // STEP 3: YOUR CHECK-INS
    function renderStep3Checkins(container, recap) {
        container.innerHTML = `
            <div class="space-y-6">
                ${renderProgressIndicator(3)}

                <div class="space-y-1.5">
                    <div class="flex items-center space-x-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-[#166545] inline-block"></span>
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">YOUR CHECK-INS</span>
                    </div>
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">Here's what you recorded</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">A factual look at what showed up in your daily Self-checks.</p>
                </div>

                <!-- 7-Day Dots Row -->
                <div class="p-4 rounded-2xl border border-stone-200 bg-stone-50/50 flex items-center justify-around">
                    ${recap.dayDots.map(d => `
                        <div class="flex flex-col items-center space-y-1">
                            <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${d.hasCheckin ? 'bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA]' : 'border border-stone-200 text-stone-300'}">
                                ${d.hasCheckin ? '✓' : '·'}
                            </div>
                            <span class="text-[10px] text-stone-500 font-semibold">${d.dayLabel}</span>
                        </div>
                    `).join('')}
                </div>

                <!-- Tracker Summaries -->
                <div class="space-y-2">
                    ${recap.trackerSummaries.length > 0 ? `
                        <div class="space-y-2">
                            ${recap.trackerSummaries.map(s => `
                                <div class="p-3.5 rounded-2xl bg-white border border-stone-200 flex items-center justify-between">
                                    <div class="space-y-0.5">
                                        <h5 class="text-xs font-bold text-[#202124] flex items-center space-x-1.5">
                                            <span>${s.icon}</span>
                                            <span>${escapeHTML(s.name)}</span>
                                        </h5>
                                        <p class="text-xs text-[#6F6B68] pl-4">${escapeHTML(s.summary)}</p>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : `
                        <div class="p-5 rounded-2xl border border-dashed border-stone-200 text-center">
                            <p class="text-xs text-[#6F6B68]">No completed Self-checks recorded during this week.</p>
                        </div>
                    `}
                </div>

                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoWeeklyReview.goToStep(2)"
                            class="px-4 py-2.5 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition cursor-pointer">
                        ← Back
                    </button>
                    <button type="button" onclick="window.TempoWeeklyReview.goToStep(4)"
                            class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer flex items-center space-x-1.5">
                        <span>Things Tempo noticed</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    // STEP 4: THINGS TEMPO NOTICED
    function renderStep4Noticed(container, recap) {
        container.innerHTML = `
            <div class="space-y-6">
                ${renderProgressIndicator(4)}

                <div class="space-y-1.5">
                    <div class="flex items-center space-x-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-[#166545] inline-block"></span>
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">THINGS TEMPO NOTICED</span>
                    </div>
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">Patterns from your records</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">Descriptive patterns comparing your recent check-ins against your earlier personal baseline.</p>
                </div>

                ${recap.noticePattern ? `
                    <div class="p-5 rounded-3xl bg-[#FFFBF7] border border-[#FFD2BA] space-y-3">
                        <div class="space-y-1">
                            <h4 class="font-heading text-sm sm:text-base font-bold text-[#202124]">
                                ${escapeHTML(recap.noticePattern.message)}
                            </h4>
                        </div>

                        ${recap.linkedRecoveryNoteItem ? `
                            <div class="p-3 bg-white/80 rounded-2xl border border-[#FFD2BA] space-y-0.5">
                                <span class="text-[10px] font-bold text-[#B83D08] uppercase tracking-wider">FROM YOUR RECOVERY NOTE</span>
                                <p class="text-xs text-[#202124] italic font-medium">"${escapeHTML(recap.linkedRecoveryNoteItem.text)}"</p>
                            </div>
                        ` : ''}
                    </div>
                ` : `
                    <div class="p-6 rounded-3xl border border-stone-200 bg-stone-50/50 space-y-1 text-center">
                        <h4 class="text-xs font-bold uppercase tracking-wider text-stone-500">Steady patterns</h4>
                        <p class="text-xs text-[#6F6B68] leading-relaxed">
                            There isn't a clear pattern to call out yet. That's okay — your check-ins simply stay as an honest record of the week.
                        </p>
                    </div>
                `}

                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoWeeklyReview.goToStep(3)"
                            class="px-4 py-2.5 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition cursor-pointer">
                        ← Back
                    </button>
                    <button type="button" onclick="window.TempoWeeklyReview.goToStep(5)"
                            class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer flex items-center space-x-1.5">
                        <span>Looking back</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    // STEP 5: LOOKING BACK (USER SELF-REFLECTION)
    function renderStep5LookingBack(container, recap) {
        const draft = activeFlowState.draft;
        const prevReflection = getPreviousReflection(recap.weekStart);

        let continuityHtml = '';
        if (prevReflection && prevReflection.comparison) {
            const prevOpt = COMPARISON_OPTIONS.find(o => o.value === prevReflection.comparison);
            const prevLabel = prevOpt ? prevOpt.label : prevReflection.comparison;
            continuityHtml = `
                <div class="p-3.5 rounded-2xl bg-stone-50 border border-stone-200 space-y-1">
                    <span class="text-[10px] font-bold uppercase tracking-wider text-stone-500">LAST WEEK</span>
                    <p class="text-xs text-[#202124]">You described yourself as: <strong>${escapeHTML(prevLabel)}</strong></p>
                    ${prevReflection.user_note ? `<p class="text-xs text-[#6F6B68] italic font-medium">You wanted to remember: "${escapeHTML(prevReflection.user_note)}"</p>` : ''}
                </div>
            `;
        }

        container.innerHTML = `
            <div class="space-y-6">
                ${renderProgressIndicator(5)}

                <div class="space-y-1.5">
                    <div class="flex items-center space-x-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-[#166545] inline-block"></span>
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">LOOKING BACK</span>
                    </div>
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">How does this week feel?</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">Take a breath. Only you decide how this week felt for you.</p>
                </div>

                ${continuityHtml}

                <!-- Question 1: Comparison -->
                <div class="space-y-2.5">
                    <label class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                        Compared with one week ago, how do you feel right now?
                    </label>
                    <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        ${COMPARISON_OPTIONS.map(opt => `
                            <label class="cursor-pointer border border-stone-200 rounded-xl p-3 text-center flex flex-col items-center space-y-1 hover:border-[#166545] has-[:checked]:border-[#166545] has-[:checked]:bg-[#EDF7F1] transition">
                                <input type="radio" name="reflection_comparison" value="${opt.value}" ${draft.comparison === opt.value ? 'checked' : ''}
                                       onchange="window.TempoWeeklyReview.setDraftComparison('${opt.value}')" class="sr-only">
                                <span class="text-base">${opt.icon}</span>
                                <span class="text-xs font-bold text-[#202124]">${escapeHTML(opt.label)}</span>
                            </label>
                        `).join('')}
                    </div>
                </div>

                <!-- Question 2: What feels different (Multi-select) -->
                <div class="space-y-2 pt-2 border-t border-stone-100">
                    <div class="space-y-0.5">
                        <label class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                            What feels different? <span class="text-[10px] text-stone-400 font-normal lowercase">(optional · select anything that fits)</span>
                        </label>
                    </div>
                    <div class="space-y-1.5" id="weekly-difference-items-list">
                        ${DIFFERENCE_SUGGESTIONS.map(s => {
                            const isChecked = draft.difference_items.includes(s);
                            return `
                                <label class="flex items-center space-x-2.5 text-xs text-[#202124] p-2 rounded-xl hover:bg-stone-50 cursor-pointer transition">
                                    <input type="checkbox" value="${escapeHTML(s)}" ${isChecked ? 'checked' : ''}
                                           onchange="window.TempoWeeklyReview.toggleDifferenceItem('${escapeHTML(s)}')"
                                           class="rounded text-[#166545] focus:ring-[#166545]">
                                    <span>${escapeHTML(s)}</span>
                                </label>
                            `;
                        }).join('')}
                        ${draft.custom_difference_items.map(s => `
                            <label class="flex items-center space-x-2.5 text-xs text-[#202124] p-2 rounded-xl bg-[#EDF7F1]/50 border border-[#CDE9DA] cursor-pointer">
                                <input type="checkbox" value="${escapeHTML(s)}" checked
                                       onchange="window.TempoWeeklyReview.toggleCustomDifferenceItem('${escapeHTML(s)}')"
                                       class="rounded text-[#166545] focus:ring-[#166545]">
                                <span class="font-medium">${escapeHTML(s)}</span>
                            </label>
                        `).join('')}
                    </div>

                    <!-- Custom item add -->
                    <div class="pt-1 flex items-center space-x-2">
                        <input type="text" id="input-custom-difference" placeholder="+ Add something that feels different..."
                               class="flex-1 px-3 py-2 text-xs rounded-xl border border-stone-200 focus:outline-none focus:border-[#166545]">
                        <button type="button" onclick="window.TempoWeeklyReview.addCustomDifference()"
                                class="px-3 py-2 text-xs font-bold text-[#166545] bg-[#EDF7F1] rounded-xl hover:bg-[#DDF0E5] transition cursor-pointer">
                            Add
                        </button>
                    </div>
                </div>

                <!-- Question 3: User Note -->
                <div class="space-y-1.5 pt-2 border-t border-stone-100">
                    <label for="input-weekly-note" class="block text-xs font-bold uppercase tracking-wider text-[#202124]">
                        Anything you want to remember about this week? <span class="text-[10px] text-stone-400 font-normal lowercase">(optional)</span>
                    </label>
                    <textarea id="input-weekly-note" rows="2" placeholder="e.g. Taking Friday afternoon slower helped a lot..."
                              oninput="window.TempoWeeklyReview.setDraftNote(this.value)"
                              class="w-full px-3.5 py-2.5 text-xs sm:text-sm rounded-xl border border-stone-200 focus:outline-none focus:border-[#166545] text-[#202124] resize-none">${escapeHTML(draft.user_note)}</textarea>
                </div>

                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoWeeklyReview.goToStep(4)"
                            class="px-4 py-2.5 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition cursor-pointer">
                        ← Back
                    </button>
                    <button type="button" onclick="window.TempoWeeklyReview.finishReview()"
                            class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer flex items-center space-x-1.5">
                        <span>Finish review</span>
                        <span>✓</span>
                    </button>
                </div>
            </div>
        `;
    }

    // STEP 6: FINISH
    function renderStep6Finish(container, recap) {
        const draft = activeFlowState.draft;
        const opt = COMPARISON_OPTIONS.find(o => o.value === draft.comparison);

        let answerContent = '';
        if (opt) {
            if (opt.value === 'little_better' || opt.value === 'much_better') {
                answerContent = `
                    <div class="space-y-1">
                        <span class="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Compared with one week ago, you described yourself as</span>
                        <div class="text-base sm:text-lg font-extrabold text-[#166545] flex items-center justify-center space-x-1">
                            <span>${opt.icon}</span>
                            <span>${escapeHTML(opt.label)}</span>
                        </div>
                    </div>
                `;
            } else if (opt.value === 'little_harder' || opt.value === 'much_harder') {
                answerContent = `
                    <div class="space-y-2">
                        <span class="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Compared with one week ago, you described things as feeling</span>
                        <div class="text-base sm:text-lg font-extrabold text-[#B83D08] flex items-center justify-center space-x-1">
                            <span>${opt.icon}</span>
                            <span>${escapeHTML(opt.label)}</span>
                        </div>
                        <p class="text-xs text-[#6F6B68] max-w-sm mx-auto">You don't have to solve the whole week from here. Take things one step at a time.</p>
                        <div class="pt-1">
                            <button type="button" onclick="window.TempoStressRelief ? window.TempoStressRelief.openModal() : null"
                                    class="px-3.5 py-1.5 rounded-xl text-xs font-bold text-[#B83D08] bg-[#FFE9DC] hover:bg-[#FFD2BA] transition cursor-pointer">
                                Quick Relief →
                            </button>
                        </div>
                    </div>
                `;
            } else if (opt.value === 'unsure') {
                answerContent = `
                    <div class="space-y-1">
                        <p class="text-xs text-[#6F6B68] max-w-sm mx-auto">
                            You don't have to put a label on the week. Your review will still be here if you want to look back later.
                        </p>
                    </div>
                `;
            } else {
                answerContent = `
                    <div class="space-y-1">
                        <span class="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Compared with one week ago, you described yourself as</span>
                        <div class="text-base sm:text-lg font-extrabold text-[#202124]">
                            ${escapeHTML(opt.label)}
                        </div>
                    </div>
                `;
            }
        }

        container.innerHTML = `
            <div class="space-y-6 text-center py-2">
                ${renderProgressIndicator(6)}

                <div class="w-12 h-12 rounded-3xl bg-[#EDF7F1] text-[#166545] flex items-center justify-center text-xl font-bold mx-auto shadow-xs">
                    🌱
                </div>

                <div class="space-y-2">
                    <h3 class="font-heading text-2xl font-extrabold text-[#202124]">Week reviewed</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68] max-w-md mx-auto leading-relaxed">
                        You've taken a look back at the week. Keep what feels useful. Leave the rest here.
                    </p>
                </div>

                ${answerContent}

                <div class="pt-4 border-t border-stone-100 flex items-center justify-center">
                    <button type="button" onclick="window.TempoWeeklyReview.close()"
                            class="btn-primary px-8 py-3 rounded-xl font-bold text-xs sm:text-sm shadow-md transition cursor-pointer">
                        Back to Dashboard →
                    </button>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // PAST REVIEW READ-ONLY VIEW WITH EDIT OPTION
    // =========================================================================

    function renderPastReviewView(weekStart) {
        const container = document.getElementById('weekly-review-modal-content');
        if (!container) return;

        const reflection = getReflectionForWeek(weekStart);
        const weekEnd = calculateWeekEnd(weekStart);
        const recap = deriveRecap(weekStart, weekEnd);

        let opt = null;
        if (reflection && reflection.comparison) {
            opt = COMPARISON_OPTIONS.find(o => o.value === reflection.comparison);
        }

        container.innerHTML = `
            <div class="space-y-6">
                <!-- Header -->
                <div class="space-y-1.5 border-b border-stone-200/80 pb-3">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#166545] inline-block"></span>
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">WEEKLY REVIEW</span>
                        </div>
                        <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA]">
                            ✓ Reviewed
                        </span>
                    </div>
                    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                        <h3 class="font-heading text-2xl font-extrabold text-[#202124]">${escapeHTML(recap.dateRange)}</h3>
                        <button type="button" onclick="window.TempoWeeklyReview.open('${weekStart}', true)"
                                class="px-3.5 py-1.5 rounded-xl border border-stone-200 hover:border-stone-300 text-xs font-semibold text-[#166545] hover:bg-[#EDF7F1] transition cursor-pointer self-start sm:self-auto">
                            Edit reflection
                        </button>
                    </div>
                </div>

                <!-- Factual Recap Stats -->
                <div class="grid grid-cols-2 gap-3">
                    <div class="p-4 rounded-2xl bg-stone-50 border border-stone-200">
                        <span class="font-heading text-2xl font-extrabold text-[#202124]">${recap.checkinCount}</span>
                        <p class="text-xs text-[#6F6B68]">check-in day${recap.checkinCount === 1 ? '' : 's'}</p>
                    </div>
                    <div class="p-4 rounded-2xl bg-stone-50 border border-stone-200">
                        <span class="font-heading text-2xl font-extrabold text-[#202124]">${recap.completedTasks.length}</span>
                        <p class="text-xs text-[#6F6B68]">task${recap.completedTasks.length === 1 ? '' : 's'} completed</p>
                    </div>
                </div>

                <!-- User Reflection Section -->
                <div class="p-5 rounded-3xl bg-white border border-[#EAE4DF] space-y-4 shadow-2xs">
                    <span class="text-[10px] font-extrabold uppercase tracking-wider text-[#166545]">YOUR REFLECTION</span>

                    <div class="space-y-1">
                        <span class="text-xs text-stone-400 font-medium">Compared with one week ago:</span>
                        <h4 class="text-sm font-bold text-[#202124]">
                            ${opt ? `${opt.icon} ${escapeHTML(opt.label)}` : (reflection?.comparison ? escapeHTML(reflection.comparison) : 'No comparison recorded')}
                        </h4>
                    </div>

                    ${(reflection?.difference_items?.length > 0 || reflection?.custom_difference_items?.length > 0) ? `
                        <div class="space-y-1 pt-1 border-t border-stone-100">
                            <span class="text-xs text-stone-400 font-medium">What felt different:</span>
                            <ul class="text-xs text-[#202124] space-y-1 pt-0.5 list-disc pl-4">
                                ${(reflection.difference_items || []).map(it => `<li>${escapeHTML(it)}</li>`).join('')}
                                ${(reflection.custom_difference_items || []).map(it => `<li>${escapeHTML(it)}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}

                    ${reflection?.user_note ? `
                        <div class="space-y-1 pt-1 border-t border-stone-100">
                            <span class="text-xs text-stone-400 font-medium">You wanted to remember:</span>
                            <p class="text-xs text-[#202124] italic">"${escapeHTML(reflection.user_note)}"</p>
                        </div>
                    ` : ''}
                </div>

                <!-- Actions -->
                <div class="pt-2 flex items-center justify-between">
                    <button type="button" onclick="window.TempoWeeklyReview.close()"
                            class="px-4 py-2.5 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition cursor-pointer">
                        Close
                    </button>
                    <button type="button" onclick="window.TempoWeeklyReview.open('${weekStart}', true)"
                            class="btn-primary px-5 py-2 rounded-xl text-xs font-bold shadow-xs transition cursor-pointer">
                        Edit reflection
                    </button>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // DRAFT INTERACTION HANDLERS
    // =========================================================================

    function setDraftComparison(val) {
        if (!activeFlowState) return;
        activeFlowState.draft.comparison = val;
    }

    function toggleDifferenceItem(item) {
        if (!activeFlowState) return;
        const list = activeFlowState.draft.difference_items;
        const idx = list.indexOf(item);
        if (idx === -1) list.push(item);
        else list.splice(idx, 1);
    }

    function toggleCustomDifferenceItem(item) {
        if (!activeFlowState) return;
        const list = activeFlowState.draft.custom_difference_items;
        const idx = list.indexOf(item);
        if (idx !== -1) list.splice(idx, 1);
        renderStep();
    }

    function addCustomDifference() {
        if (!activeFlowState) return;
        const input = document.getElementById('input-custom-difference');
        if (!input) return;
        const val = input.value.trim();
        if (!val) return;
        if (!activeFlowState.draft.custom_difference_items.includes(val)) {
            activeFlowState.draft.custom_difference_items.push(val);
        }
        input.value = '';
        renderStep();
    }

    function setDraftNote(val) {
        if (!activeFlowState) return;
        activeFlowState.draft.user_note = val;
    }

    function finishReview() {
        if (!activeFlowState) return;
        const { weekStart, weekEnd, draft } = activeFlowState;

        // Persist reflection
        saveUserReflection({
            week_start: weekStart,
            week_end: weekEnd,
            comparison: draft.comparison,
            difference_items: draft.difference_items,
            custom_difference_items: draft.custom_difference_items,
            user_note: draft.user_note
        });

        // Advance to Step 6 (Finish)
        activeFlowState.step = 6;
        renderStep();

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("✓ Weekly review saved.");
        }
    }

    // =========================================================================
    // HISTORY TAB CONTENT RENDERER (WIRED TO selfCheckHistory.js)
    // =========================================================================

    function renderHistoryTabContent() {
        const completedWeeks = getCompletedWeeks(4);
        if (completedWeeks.length === 0) {
            return `
                <div class="p-8 text-center rounded-3xl border border-stone-200 bg-stone-50/50 space-y-2">
                    <p class="text-xs text-[#6F6B68]">No completed weeks to display yet.</p>
                </div>
            `;
        }

        return `
            <div class="space-y-4">
                <div class="space-y-1">
                    <h4 class="text-xs font-extrabold uppercase tracking-wider text-stone-500">Weekly Reviews</h4>
                    <p class="text-xs text-[#6F6B68]">A look back at each completed week and how you described things feeling.</p>
                </div>

                <div class="space-y-3">
                    ${completedWeeks.map(wk => {
                        const reflection = getReflectionForWeek(wk.start);
                        const recap = deriveRecap(wk.start, wk.end);

                        let reflectionLabel = 'No reflection added';
                        if (reflection && reflection.comparison) {
                            const opt = COMPARISON_OPTIONS.find(o => o.value === reflection.comparison);
                            reflectionLabel = opt ? opt.label : reflection.comparison;
                        }

                        const isReviewed = Boolean(reflection);

                        return `
                            <div class="p-4 sm:p-5 rounded-2xl bg-white border border-stone-200 hover:border-stone-300 transition flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs">
                                <div class="space-y-1">
                                    <div class="flex items-center space-x-2">
                                        <h5 class="text-sm font-bold text-[#202124]">${escapeHTML(wk.dateRange)}</h5>
                                        ${isReviewed ? `
                                            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA]">
                                                ✓ Reviewed
                                            </span>
                                        ` : `
                                            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                                                Ready to review
                                            </span>
                                        `}
                                    </div>
                                    <p class="text-xs text-[#6F6B68]">
                                        ${recap.checkinCount} check-in day${recap.checkinCount === 1 ? '' : 's'} · ${recap.completedTasks.length} task${recap.completedTasks.length === 1 ? '' : 's'} completed
                                    </p>
                                    ${isReviewed ? `
                                        <p class="text-xs text-stone-700 font-medium">
                                            You described yourself as: <span class="font-bold text-[#166545]">${escapeHTML(reflectionLabel)}</span>
                                        </p>
                                    ` : ''}
                                </div>
                                <div class="shrink-0">
                                    ${isReviewed ? `
                                        <button type="button" onclick="window.TempoWeeklyReview.open('${wk.start}', false)"
                                                class="px-4 py-2 rounded-xl border border-stone-200 hover:border-stone-300 text-xs font-bold text-[#166545] hover:bg-[#EDF7F1] transition cursor-pointer">
                                            View review →
                                        </button>
                                    ` : `
                                        <button type="button" onclick="window.TempoWeeklyReview.open('${wk.start}', true)"
                                                class="btn-primary px-4 py-2 rounded-xl text-xs font-bold shadow-xs transition cursor-pointer">
                                            Review →
                                        </button>
                                    `}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

    // =========================================================================
    // UTILITIES
    // =========================================================================

    function formatDisplayShortDate(dateStr) {
        if (!dateStr) return '';
        try {
            const [y, m, d] = dateStr.split('-').map(Number);
            const dt = new Date(y, m - 1, d);
            return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        } catch (e) {
            return dateStr;
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

    function init() {
        ensureModalMounted();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Global Export
    window.TempoWeeklyReview = {
        init,
        isReady,
        getLatestEligibleWeek,
        getCompletedWeeks,
        deriveRecap,
        getReflectionForWeek,
        loadReflections,
        saveUserReflection,
        snoozeOrDismissNotice,
        isNoticeDismissed,
        open,
        close,
        goToStep,
        setDraftComparison,
        toggleDifferenceItem,
        toggleCustomDifferenceItem,
        addCustomDifference,
        setDraftNote,
        finishReview,
        renderHistoryTabContent
    };

})();
