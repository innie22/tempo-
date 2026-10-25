/**
 * TEMPO WELLBEING — CONFIGURABLE ALERT SYSTEM
 * File: tempoAlertSystem.js
 *
 * Implements two distinct alert types:
 * 1. Sign of Stress (alerts for persistent patterns indicating stress, with Recovery Note helpers & self-check test referrals)
 * 2. Supportive Reminder (gentle, encouraging reminders for uncompleted habits with small steps & Recovery Note ideas)
 *
 * Consecutive Sequence & Notification Rules:
 * - Counter increments only on actual check-in satisfying the item's configured condition.
 * - Missing check-ins or failed conditions strictly break the consecutive sequence.
 * - Alerts trigger only after successful check-in reaches duration N.
 * - Consecutive sequences deliver at most one notification per qualifying sequence (no daily duplicates).
 * - When a sequence breaks, counter and notification state reset so a new qualifying sequence can trigger normally.
 * - Scoped persistence under tempo_selfcheck_alerts_${uid}.
 */

(function () {
    'use strict';

    const ALERT_TYPES = {
        STRESS_SIGN: 'stress_sign',
        SUPPORTIVE_REMINDER: 'supportive_reminder'
    };

    // =========================================================================
    // STORAGE & PERSISTENCE
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
        return `tempo_selfcheck_alerts_${uid}`;
    }

    function loadNotifications() {
        try {
            const raw = localStorage.getItem(getStorageKey());
            if (raw) return JSON.parse(raw);
        } catch (e) {
            console.warn("[TempoAlertSystem] Error loading notifications:", e);
        }
        return {};
    }

    function saveNotifications(data) {
        try {
            localStorage.setItem(getStorageKey(), JSON.stringify(data));
        } catch (e) {
            console.warn("[TempoAlertSystem] Error saving notifications:", e);
        }
    }

    function recordNotificationDelivered(trackerId, info) {
        const notifs = loadNotifications();
        notifs[trackerId] = {
            sequenceStartDate: info.sequenceStartDate,
            deliveredAt: info.deliveredAt || new Date().toISOString(),
            consecutiveCount: info.consecutiveCount,
            alertType: info.alertType,
            dismissed: Boolean(info.dismissed)
        };
        saveNotifications(notifs);
    }

    function clearNotificationIfActive(trackerId) {
        const notifs = loadNotifications();
        if (notifs[trackerId]) {
            delete notifs[trackerId];
            saveNotifications(notifs);
        }
    }

    // =========================================================================
    // DATE UTILITIES
    // =========================================================================

    function getTodayDateStr() {
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTodayDateStr === 'function') {
            return window.TempoRecoverySelfCheck.getTodayDateStr();
        }
        const now = new Date();
        const y = now.getFullYear();
        const m = String(now.getMonth() + 1).padStart(2, '0');
        const d = String(now.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    }

    function shiftDateStr(dateStr, offsetDays) {
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.shiftDateStr === 'function') {
            return window.TempoRecoverySelfCheck.shiftDateStr(dateStr, offsetDays);
        }
        const [y, m, d] = dateStr.split('-').map(Number);
        const dt = new Date(y, m - 1, d);
        dt.setDate(dt.getDate() + offsetDays);
        const ny = dt.getFullYear();
        const nm = String(dt.getMonth() + 1).padStart(2, '0');
        const nd = String(dt.getDate()).padStart(2, '0');
        return `${ny}-${nm}-${nd}`;
    }

    // =========================================================================
    // OBSERVATION FETCHER
    // =========================================================================

    function getObservationForTrackerAndDate(trackerId, dateStr) {
        const uid = getUserId();
        const checkinsKey = `tempo_selfcheck_checkins_${uid}`;
        const obsKey = `tempo_selfcheck_observations_${uid}`;

        let checkins = [];
        let allObs = [];
        try {
            checkins = JSON.parse(localStorage.getItem(checkinsKey) || '[]');
            allObs = JSON.parse(localStorage.getItem(obsKey) || '[]');
        } catch (e) {
            return null;
        }

        // Also fallback to legacy non-scoped key if local_user
        if (checkins.length === 0 && uid === 'local_user') {
            try {
                checkins = JSON.parse(localStorage.getItem('tempo_selfcheck_checkins') || '[]');
                allObs = JSON.parse(localStorage.getItem('tempo_selfcheck_observations') || '[]');
            } catch (e) {}
        }

        const chk = checkins.find(c => c.checkin_date === dateStr);
        if (!chk) return null;

        return allObs.find(o => o.checkin_id === chk.id && o.tracker_id === trackerId) || null;
    }

    // =========================================================================
    // CONDITION EVALUATION
    // =========================================================================

    function isTrackerConditionMet(tracker, obs) {
        if (!obs || obs.status !== 'answered' || obs.value === null || obs.value === undefined) {
            return false;
        }

        const cfg = tracker.alert_config;
        if (!cfg) return false;

        const val = obs.value;
        const method = obs.check_method || tracker.check_method || 'yes_no';
        const nameLower = (tracker.name || '').toLowerCase();

        if (method === 'percentage' || nameLower.includes('tension')) {
            const num = parseFloat(val);
            const thresh = parseFloat(cfg.threshold);
            if (isNaN(num) || isNaN(thresh)) return false;
            // Strict semantics: 70% does not qualify if condition is > 70%
            return (cfg.operator === 'less_than') ? (num < thresh) : (num > thresh);
        }

        if (method === 'scale') {
            const num = parseFloat(val);
            const thresh = parseFloat(cfg.threshold);
            if (isNaN(num) || isNaN(thresh)) return false;
            return (cfg.operator === 'less_than') ? (num < thresh) : (num > thresh);
        }

        if (method === 'quantity' || nameLower.includes('walk')) {
            // Check for explicit "Didn't do" condition
            const isDidntDoCondition = cfg.operator === 'didnt_do' ||
                                       (cfg.target_option && String(cfg.target_option).toLowerCase().includes("didn't")) ||
                                       (cfg.target_option && String(cfg.target_option).toLowerCase() === 'no');

            if (isDidntDoCondition) {
                return val === 'no' || val === 0 || val === '0' || String(val).toLowerCase().includes("didn't");
            }

            // Numeric quantity comparison
            const num = (val === 'no' || String(val).toLowerCase().includes("didn't")) ? 0 : parseFloat(val);
            const thresh = parseFloat(cfg.threshold);
            if (isNaN(num) || isNaN(thresh)) return false;
            return (cfg.operator === 'less_than') ? (num < thresh) : (num > thresh);
        }

        if (method === 'options' || method === 'yes_no' || nameLower.includes('sleep')) {
            const target = cfg.target_option;
            if (!target) return false;
            const targetLower = String(target).toLowerCase();
            const valLower = String(val).toLowerCase();

            if (valLower === targetLower) return true;
            if (targetLower === 'yes' && (val === true || valLower === 'yes')) return true;
            if (targetLower === 'no' && (val === false || valLower === 'no')) return true;
            return false;
        }

        return false;
    }

    function getTrackerAlertType(tracker) {
        if (tracker && tracker.alert_config && tracker.alert_config.alert_type) {
            return tracker.alert_config.alert_type;
        }
        if (tracker && tracker.category === 'stress_sign') {
            return ALERT_TYPES.STRESS_SIGN;
        }
        if (tracker && tracker.category === 'supportive') {
            return ALERT_TYPES.SUPPORTIVE_REMINDER;
        }
        if (tracker && tracker.direction === 'higher_concerning') {
            return ALERT_TYPES.STRESS_SIGN;
        }
        return ALERT_TYPES.SUPPORTIVE_REMINDER;
    }

    function getConditionDescription(tracker, cfg) {
        if (!cfg) return 'your configured condition';
        const method = tracker.check_method;
        const nameLower = (tracker.name || '').toLowerCase();

        if (method === 'percentage' || nameLower.includes('tension')) {
            return `${cfg.operator === 'less_than' ? 'below' : 'above'} ${cfg.threshold}%`;
        }
        if (method === 'scale') {
            return `${cfg.operator === 'less_than' ? 'below' : 'above'} ${cfg.threshold}`;
        }
        if (method === 'quantity' || nameLower.includes('walk')) {
            if (cfg.operator === 'didnt_do' || (cfg.target_option && String(cfg.target_option).toLowerCase().includes("didn't"))) {
                return 'uncompleted ("Didn\'t do")';
            }
            return `${cfg.operator === 'less_than' ? 'below' : 'above'} ${cfg.threshold} ${tracker.quantity_unit || 'min'}`;
        }
        if (cfg.target_option) {
            return `at "${cfg.target_option}"`;
        }
        return 'at your alert threshold';
    }

    // =========================================================================
    // CONSECUTIVE COUNTER & EVALUATION API
    // =========================================================================

    function evaluateTrackerAlert(tracker, referenceDateStr = null) {
        if (!tracker || !tracker.alert_enabled || !tracker.alert_config) {
            return { triggered: false, consecutiveCount: 0 };
        }

        const cfg = tracker.alert_config;
        const requiredDays = parseInt(cfg.days, 10) || 1;
        if (requiredDays < 1) return { triggered: false, consecutiveCount: 0 };

        const todayStr = referenceDateStr || getTodayDateStr();
        let consecutiveMet = 0;
        let currentDay = todayStr;

        // Traverse backwards day-by-day from todayStr
        // Gaps in daily check-in records strictly break the consecutive sequence
        while (true) {
            const obs = getObservationForTrackerAndDate(tracker.id, currentDay);
            if (!obs || obs.status !== 'answered') {
                break;
            }
            if (isTrackerConditionMet(tracker, obs)) {
                consecutiveMet++;
                currentDay = shiftDateStr(currentDay, -1);
            } else {
                break;
            }
        }

        const alertType = getTrackerAlertType(tracker);

        if (consecutiveMet === 0) {
            // Consecutive sequence is broken: clear previous notification state so a future sequence triggers cleanly
            clearNotificationIfActive(tracker.id);
            return { triggered: false, consecutiveCount: 0, alertType };
        }

        // Start date of the unbroken sequence
        const sequenceStartDate = shiftDateStr(todayStr, -(consecutiveMet - 1));

        if (consecutiveMet < requiredDays) {
            return {
                triggered: false,
                consecutiveCount: consecutiveMet,
                requiredDays: requiredDays,
                sequenceStartDate: sequenceStartDate,
                alertType: alertType
            };
        }

        // Check if this notification milestone has already been delivered for this sequence
        const notifs = loadNotifications();
        const existing = notifs[tracker.id];

        if (existing && existing.sequenceStartDate === sequenceStartDate) {
            // Already delivered for this sequence! Do not show duplicate alerts on subsequent qualifying days
            return {
                triggered: false,
                alreadyDelivered: true,
                consecutiveCount: consecutiveMet,
                requiredDays: requiredDays,
                sequenceStartDate: sequenceStartDate,
                alertType: alertType
            };
        }

        // Milestone reached for a new sequence!
        return {
            triggered: true,
            consecutiveCount: consecutiveMet,
            requiredDays: requiredDays,
            sequenceStartDate: sequenceStartDate,
            alertType: alertType,
            tracker: tracker,
            conditionDescription: getConditionDescription(tracker, cfg)
        };
    }

    // Evaluate an item and trigger the alert popup immediately after check-in save
    function evaluateAndTriggerAlert(trackerId) {
        let tracker = null;
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerById === 'function') {
            tracker = window.TempoRecoverySelfCheck.getTrackerById(trackerId);
        }
        if (!tracker && window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.getActiveTrackers === 'function') {
            const list = window.TempoSelfCheckWorkspace.getActiveTrackers();
            tracker = list.find(t => t.id === trackerId);
        }
        if (!tracker) return null;

        const result = evaluateTrackerAlert(tracker);
        if (result.triggered) {
            // Mark milestone delivered for this sequence
            recordNotificationDelivered(tracker.id, {
                sequenceStartDate: result.sequenceStartDate,
                deliveredAt: new Date().toISOString(),
                consecutiveCount: result.consecutiveCount,
                alertType: result.alertType,
                dismissed: false
            });

            // Open alert popup in foreground
            openAlertModal(result);
            return result;
        }
        return result;
    }

    // Evaluate a list of tracker IDs (e.g. after finishDailyCheckin)
    function evaluateAnsweredTrackers(trackerIds) {
        if (!Array.isArray(trackerIds) || trackerIds.length === 0) return;
        for (const id of trackerIds) {
            const res = evaluateAndTriggerAlert(id);
            if (res && res.triggered) {
                // Show the first triggered alert immediately
                break;
            }
        }
    }

    // =========================================================================
    // MODAL SHELL & RENDERING
    // =========================================================================

    function ensureAlertModalMounted() {
        if (document.getElementById('modal-tempo-alert')) return;

        const container = document.createElement('div');
        container.id = 'modal-tempo-alert';
        container.className = 'fixed inset-0 z-[90] flex items-center justify-center modal-backdrop p-4 hidden';
        container.style.zIndex = '90';
        container.setAttribute('role', 'dialog');
        container.setAttribute('aria-modal', 'true');
        container.onclick = function (e) {
            if (e.target === this) dismissAlert();
        };

        container.innerHTML = `
            <div id="tempo-alert-modal-card" 
                 class="tempo-card max-w-lg w-full p-6 sm:p-7 space-y-5 rounded-3xl shadow-2xl relative border border-[#EAE4DF]/80 max-h-[92vh] overflow-y-auto"
                 style="background-color: #FEFAF4;">
                <!-- Populated dynamically by openAlertModal -->
            </div>
        `;
        document.body.appendChild(container);
    }

    function openAlertModal(alertData) {
        ensureAlertModalMounted();

        // Close any daily checkin or view modals to prevent overlapping dialogs
        if (window.TempoRecoverySelfCheck) {
            if (typeof window.TempoRecoverySelfCheck.closeDailyCheckin === 'function') {
                window.TempoRecoverySelfCheck.closeDailyCheckin();
            }
            if (typeof window.TempoRecoverySelfCheck.closeViewToday === 'function') {
                window.TempoRecoverySelfCheck.closeViewToday();
            }
        }

        const modal = document.getElementById('modal-tempo-alert');
        const card = document.getElementById('tempo-alert-modal-card');
        if (!modal || !card) return;

        card.innerHTML = renderAlertModalHTML(alertData);
        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    function closeAlertModal() {
        const modal = document.getElementById('modal-tempo-alert');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    function dismissAlert() {
        closeAlertModal();
    }

    function renderAlertModalHTML(alertData) {
        const trk = alertData.tracker || {};
        const trkName = trk.name || 'tracker';
        const consecutiveCount = alertData.consecutiveCount || alertData.requiredDays || 4;
        const conditionDesc = alertData.conditionDescription || 'above your configured threshold';
        const isStressSign = alertData.alertType === ALERT_TYPES.STRESS_SIGN;

        // Fetch actual Recovery Note items
        const noteItems = (window.TempoRecoveryNote && typeof window.TempoRecoveryNote.getItems === 'function')
            ? window.TempoRecoveryNote.getItems()
            : [];

        if (isStressSign) {
            // A. SIGN OF STRESS POPUP
            const relevantItems = noteItems.filter(item => item.type === 'helper' || item.type === 'reminder' || item.type === 'support_person');

            let recoveryNoteSectionHTML = '';
            if (relevantItems.length > 0) {
                recoveryNoteSectionHTML = `
                    <div class="bg-white rounded-2xl border border-stone-200/80 p-4 space-y-2.5 shadow-2xs">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold text-[#37352F] flex items-center space-x-1.5">
                                <span>📝</span>
                                <span>From your Recovery Note</span>
                            </span>
                            <button type="button" 
                                    onclick="window.TempoAlertSystem.handleOpenRecoveryNote()" 
                                    class="text-xs font-bold text-[#4A6B5D] hover:underline cursor-pointer">
                                Open full note →
                            </button>
                        </div>
                        <div class="space-y-1.5 pt-1">
                            ${relevantItems.slice(0, 3).map(it => `
                                <div class="text-xs text-[#484541] flex items-start space-x-2 bg-[#F9F7F5] rounded-xl px-3 py-2 border border-stone-200/60">
                                    <span class="font-bold text-[#4A6B5D] shrink-0">•</span>
                                    <span>${escapeHTML(it.content || it.name || '')}${it.metadata && it.metadata.relationship ? ` <em class="text-stone-400 font-normal">(${escapeHTML(it.metadata.relationship)})</em>` : ''}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            } else {
                recoveryNoteSectionHTML = `
                    <div class="bg-white rounded-2xl border border-stone-200/80 p-4 space-y-2 shadow-2xs">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold text-[#37352F] flex items-center space-x-1.5">
                                <span>📝</span>
                                <span>Recovery Note</span>
                            </span>
                        </div>
                        <p class="text-xs text-stone-400 italic">No coping strategies or helpers saved in your Recovery Note yet.</p>
                        <button type="button" 
                                onclick="window.TempoAlertSystem.handleCreateRecoveryNote()" 
                                class="text-xs font-bold text-[#4A6B5D] hover:underline cursor-pointer block pt-0.5">
                            + Add helpers to your Recovery Note
                        </button>
                    </div>
                `;
            }

            return `
                <!-- Close Button -->
                <button type="button" 
                        onclick="window.TempoAlertSystem.dismissAlert()" 
                        class="absolute top-5 right-5 w-8 h-8 rounded-full flex items-center justify-center text-[#8C8681] hover:text-[#37352F] hover:bg-stone-200/50 text-base transition cursor-pointer" 
                        title="Dismiss">✕</button>

                <!-- Top Category Tag with Semantic Warning Red (#D92D20) -->
                <div class="flex items-center space-x-2">
                    <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: #D92D20;"></span>
                    <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#D92D20]">SIGN OF STRESS ALERT</span>
                </div>

                <!-- Title & Supportive Message -->
                <div class="space-y-1.5">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#37352F] tracking-tight leading-snug">
                        You've been experiencing ongoing pressure
                    </h3>
                    <p class="text-xs sm:text-sm text-[#5B5550] leading-relaxed">
                        Your recent check-ins show that your <strong>${escapeHTML(trkName)}</strong> has remained ${escapeHTML(conditionDesc)} for <strong>${consecutiveCount} consecutive days</strong>. This may be a sign that you are experiencing a prolonged period of stress.
                    </p>
                </div>

                <!-- Action A: Recovery Note -->
                ${recoveryNoteSectionHTML}

                <!-- Action B: Explore Self-check Tests -->
                <div class="bg-[#F4F7F5] rounded-2xl border border-[#CDE9DA]/70 p-4 space-y-2 shadow-2xs">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-[#202124] flex items-center space-x-1.5">
                            <span>🔍</span>
                            <span>Explore Self-check Tests</span>
                        </span>
                    </div>
                    <p class="text-xs text-[#5B5550]">
                        Consider checking in with an informational evaluation to reflect on your stress and fatigue levels:
                    </p>
                    <div class="flex flex-wrap gap-2 pt-1">
                        <button type="button" 
                                onclick="window.TempoAlertSystem.handleOpenTest('stress')" 
                                class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-white text-[#166545] border border-[#7B9688] hover:bg-[#EDF7F1] transition cursor-pointer shadow-2xs">
                            ⚡ Stress Assessment
                        </button>
                        <button type="button" 
                                onclick="window.TempoAlertSystem.handleOpenTest('anxiety')" 
                                class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-white text-[#166545] border border-[#7B9688] hover:bg-[#EDF7F1] transition cursor-pointer shadow-2xs">
                            🌀 Anxiety Assessment
                        </button>
                    </div>
                    <p class="text-[10px] text-stone-400 italic pt-0.5">
                        Note: Informational self-check results are for your personal reflection and not a clinical diagnosis.
                    </p>
                </div>

                <!-- Footer: Dismissal CTA -->
                <div class="flex items-center justify-between pt-3 border-t border-stone-200/80">
                    <span class="text-[11px] text-stone-400">Check-in recorded safely.</span>
                    <button type="button" 
                            onclick="window.TempoAlertSystem.dismissAlert()" 
                            class="px-5 py-2 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white shadow-xs transition cursor-pointer">
                        Dismiss
                    </button>
                </div>
            `;
        } else {
            // B. SUPPORTIVE REMINDER POPUP
            const reminderItems = noteItems.filter(item => item.type === 'helper' || item.type === 'reminder');

            let helperPreviewHTML = '';
            if (reminderItems.length > 0) {
                helperPreviewHTML = `
                    <div class="bg-white rounded-2xl border border-stone-200/80 p-4 space-y-2 shadow-2xs">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold text-[#37352F] flex items-center space-x-1.5">
                                <span>🌱</span>
                                <span>Ideas from your Recovery Note</span>
                            </span>
                            <button type="button" 
                                    onclick="window.TempoAlertSystem.handleOpenRecoveryNote()" 
                                    class="text-xs font-bold text-[#4A6B5D] hover:underline cursor-pointer">
                                Open note →
                            </button>
                        </div>
                        <div class="space-y-1 pt-1">
                            ${reminderItems.slice(0, 2).map(it => `
                                <div class="text-xs text-[#484541] flex items-start space-x-2 bg-[#F9F7F5] rounded-xl px-3 py-1.5 border border-stone-200/60">
                                    <span class="font-bold text-[#4A6B5D] shrink-0">•</span>
                                    <span>${escapeHTML(it.content || '')}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            return `
                <!-- Close Button -->
                <button type="button" 
                        onclick="window.TempoAlertSystem.dismissAlert()" 
                        class="absolute top-5 right-5 w-8 h-8 rounded-full flex items-center justify-center text-[#8C8681] hover:text-[#37352F] hover:bg-stone-200/50 text-base transition cursor-pointer" 
                        title="Dismiss">✕</button>

                <!-- Top Category Tag with Supportive Green (#4A6B5D) -->
                <div class="flex items-center space-x-2">
                    <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: #4A6B5D;"></span>
                    <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#4A6B5D]">SUPPORTIVE REMINDER</span>
                </div>

                <!-- Title & Encouraging Message -->
                <div class="space-y-1.5">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#37352F] tracking-tight leading-snug">
                        Let's start again with a small step
                    </h3>
                    <p class="text-xs sm:text-sm text-[#5B5550] leading-relaxed">
                        You haven't completed your configured <strong>${escapeHTML(trkName)}</strong> activity for <strong>${consecutiveCount} consecutive days</strong>. Would you like to try a small, manageable step today?
                    </p>
                </div>

                <!-- Ideas from Recovery Note (if available) -->
                ${helperPreviewHTML}

                <!-- Actions: Return to Tracking or Dismiss -->
                <div class="flex items-center justify-between pt-3 border-t border-stone-200/80">
                    <button type="button" 
                            onclick="window.TempoAlertSystem.handleReturnToTracking('${trk.id}')" 
                            class="px-4 py-2 rounded-xl text-xs font-bold bg-white border border-[#7B9688] text-[#4A6B5D] hover:bg-[#F4F7F5] shadow-xs transition cursor-pointer">
                        View ${escapeHTML(trkName)} tracking
                    </button>
                    <button type="button" 
                            onclick="window.TempoAlertSystem.dismissAlert()" 
                            class="px-5 py-2 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white shadow-xs transition cursor-pointer">
                        Dismiss
                    </button>
                </div>
            `;
        }
    }

    // =========================================================================
    // ACTION HANDLERS
    // =========================================================================

    function handleOpenRecoveryNote() {
        dismissAlert();
        if (window.TempoRecoveryNote && typeof window.TempoRecoveryNote.openViewModal === 'function') {
            window.TempoRecoveryNote.openViewModal();
        }
    }

    function handleCreateRecoveryNote() {
        dismissAlert();
        if (window.TempoRecoveryNote && typeof window.TempoRecoveryNote.openEditModal === 'function') {
            window.TempoRecoveryNote.openEditModal();
        }
    }

    function handleOpenTest(categoryKey) {
        dismissAlert();
        if (window.TempoExploreAssessments && typeof window.TempoExploreAssessments.selectCategory === 'function') {
            window.TempoExploreAssessments.selectCategory(categoryKey);
        }
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('explore-mental-health-tests');
        } else {
            window.location.hash = '#explore-mental-health-tests';
        }
    }

    function handleReturnToTracking(trackerId) {
        dismissAlert();
        if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
            window.TempoMode.openStrack('open', { sourceContext: 'recovery' });
        } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('stress-check');
        } else {
            window.location.hash = '#stress-check';
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

    // =========================================================================
    // EXPORTS
    // =========================================================================

    window.TempoAlertSystem = {
        ALERT_TYPES,
        evaluateTrackerAlert,
        evaluateAndTriggerAlert,
        evaluateAnsweredTrackers,
        openAlertModal,
        closeAlertModal,
        dismissAlert,
        handleOpenRecoveryNote,
        handleCreateRecoveryNote,
        handleOpenTest,
        handleReturnToTracking,
        loadNotifications,
        saveNotifications,
        clearNotificationIfActive
    };

})();
