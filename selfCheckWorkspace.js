/**
 * Tempo Self-Check Tool Page
 * File: selfCheckWorkspace.js
 *
 * Implements the Tempo Self-check tool page matching the reference design:
 * - Left column: Weekly self-check summary, Today's self-check interactive card,
 *   My weekly report button, and My Recovery notice button.
 * - Right column: Your Tracking System with independently scrollable tracker cards,
 *   Add Tracking, Clear all with confirmation, Adjust edit popup, and View my full check popup.
 * - Context-aware navigation and persistence via window.TempoRecoverySelfCheck and window.TempoRecoveryNote.
 */

window.TempoSelfCheckWorkspace = (function () {
    'use strict';

    let showNoteInput = false;
    let selectedTrackerForHistory = null;
    let showClearConfirm = false;
    let showWeeklyReportModal = false;

    // Helper: Escape HTML
    function escapeHTML(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Helper: Get user ID
    function getUserId() {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') {
            return window.TempoAuth.getCurrentUserId() || 'local_user';
        }
        return 'local_user';
    }

    // Date Helpers
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
        const [y, m, d] = dateStr.split('-').map(Number);
        const dt = new Date(y, m - 1, d);
        dt.setDate(dt.getDate() + offsetDays);
        const ny = dt.getFullYear();
        const nm = String(dt.getMonth() + 1).padStart(2, '0');
        const nd = String(dt.getDate()).padStart(2, '0');
        return `${ny}-${nm}-${nd}`;
    }

    // Calculate current Monday through Sunday
    function getCurrentWeekDays() {
        const todayStr = getTodayDateStr();
        const [y, m, d] = todayStr.split('-').map(Number);
        const now = new Date(y, m - 1, d);
        
        // Sunday is 0, Monday is 1 ... Saturday is 6
        const day = now.getDay();
        const diffToMon = day === 0 ? -6 : 1 - day;
        const mon = new Date(now);
        mon.setDate(now.getDate() + diffToMon);

        const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        const days = [];

        for (let i = 0; i < 7; i++) {
            const dt = new Date(mon);
            dt.setDate(mon.getDate() + i);
            const dy = dt.getFullYear();
            const dm = String(dt.getMonth() + 1).padStart(2, '0');
            const dd = String(dt.getDate()).padStart(2, '0');
            const dateStr = `${dy}-${dm}-${dd}`;
            days.push({
                dateStr,
                dayLabel: dayLabels[i],
                dateObj: dt,
                isToday: (dateStr === todayStr),
                isPastOrToday: (dateStr <= todayStr)
            });
        }
        return days;
    }

    function getWeekDateRangeStr() {
        const days = getCurrentWeekDays();
        const mon = days[0].dateObj;
        const sun = days[6].dateObj;
        const monStr = mon.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        const sunStr = sun.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        return `${monStr} to ${sunStr}`;
    }

    // Seed initial trackers & check-ins if completely empty (matching reference screenshot)
    function seedDefaultsIfEmpty() {
        // Do not auto-seed trackers for users. Tracking items must only be created
        // through explicit setup flow or the "Add Tracking" interface.
        return;
    }

    function saveCustomCheckinForDate(dateStr, observations, note = '') {
        const uid = getUserId();
        const checkinsKey = `tempo_selfcheck_checkins_${uid}`;
        const obsKey = `tempo_selfcheck_observations_${uid}`;

        let checkins = [];
        let allObs = [];
        try {
            checkins = JSON.parse(localStorage.getItem(checkinsKey) || '[]');
            allObs = JSON.parse(localStorage.getItem(obsKey) || '[]');
        } catch (e) {}

        const chkId = 'chk_' + dateStr.replace(/-/g, '') + '_' + Math.random().toString(36).substr(2, 4);
        checkins = checkins.filter(c => c.checkin_date !== dateStr);
        checkins.push({
            id: chkId,
            user_id: uid,
            checkin_date: dateStr,
            overall_note: note,
            completed_at: new Date().toISOString(),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        });

        allObs = allObs.filter(o => o.checkin_id !== chkId);
        observations.forEach(o => {
            let trk = null;
            if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerById === 'function') {
                trk = window.TempoRecoverySelfCheck.getTrackerById(o.tracker_id);
            }
            let cfg = null;
            if (trk && window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerConfigForDate === 'function') {
                cfg = window.TempoRecoverySelfCheck.getTrackerConfigForDate(trk, dateStr);
            }
            const effMethod = o.check_method || (cfg && cfg.check_method) || (trk && trk.check_method) || 'yes_no';
            const effUnit = o.quantity_unit !== undefined ? o.quantity_unit : ((cfg && cfg.quantity_unit !== undefined) ? cfg.quantity_unit : ((trk && trk.quantity_unit) || ''));
            const effVer = o.config_version_id || (cfg && cfg.version_id) || null;

            allObs.push({
                id: o.id || ('obs_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4)),
                checkin_id: chkId,
                tracker_id: o.tracker_id,
                value: o.value,
                status: o.status || 'answered',
                check_method: effMethod,
                quantity_unit: effUnit,
                config_version_id: effVer,
                note: o.note ? o.note.trim() : '',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            });
        });

        try {
            localStorage.setItem(checkinsKey, JSON.stringify(checkins));
            localStorage.setItem(obsKey, JSON.stringify(allObs));
        } catch (e) {}
    }

    // Return today's observation for a tracker
    function getTodayObservation(trackerId) {
        const uid = getUserId();
        const todayStr = getTodayDateStr();
        const checkinsKey = `tempo_selfcheck_checkins_${uid}`;
        const obsKey = `tempo_selfcheck_observations_${uid}`;

        try {
            const rawChk = localStorage.getItem(checkinsKey) || (uid === 'local_user' ? localStorage.getItem('tempo_selfcheck_checkins') : null);
            const checkins = rawChk ? JSON.parse(rawChk) : [];
            const todayChk = checkins.find(c => c.checkin_date === todayStr);
            if (!todayChk) return null;

            const rawObs = localStorage.getItem(obsKey) || (uid === 'local_user' ? localStorage.getItem('tempo_selfcheck_observations') : null);
            const allObs = rawObs ? JSON.parse(rawObs) : [];
            return allObs.find(o => o.checkin_id === todayChk.id && o.tracker_id === trackerId) || null;
        } catch (e) {
            return null;
        }
    }

    // Save or update today's observation for a tracker
    function setTodayObservation(trackerId, value, status = 'answered') {
        const uid = getUserId();
        const todayStr = getTodayDateStr();
        const checkinsKey = `tempo_selfcheck_checkins_${uid}`;
        const obsKey = `tempo_selfcheck_observations_${uid}`;

        let checkins = [];
        let allObs = [];
        try {
            checkins = JSON.parse(localStorage.getItem(checkinsKey) || '[]');
            allObs = JSON.parse(localStorage.getItem(obsKey) || '[]');
        } catch (e) {}

        let todayChk = checkins.find(c => c.checkin_date === todayStr);
        if (!todayChk) {
            todayChk = {
                id: 'chk_' + todayStr.replace(/-/g, '') + '_' + Math.random().toString(36).substr(2, 4),
                user_id: uid,
                checkin_date: todayStr,
                overall_note: '',
                completed_at: new Date().toISOString(),
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            };
            checkins.push(todayChk);
            localStorage.setItem(checkinsKey, JSON.stringify(checkins));
        }

        let trk = null;
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerById === 'function') {
            trk = window.TempoRecoverySelfCheck.getTrackerById(trackerId);
        }
        let cfg = null;
        if (trk && window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerConfigForDate === 'function') {
            cfg = window.TempoRecoverySelfCheck.getTrackerConfigForDate(trk, todayStr);
        }
        const effMethod = (cfg && cfg.check_method) || (trk && trk.check_method) || 'yes_no';
        const effUnit = (cfg && cfg.quantity_unit !== undefined) ? cfg.quantity_unit : ((trk && trk.quantity_unit) || '');
        const effVer = (cfg && cfg.version_id) || null;

        const existingIdx = allObs.findIndex(o => o.checkin_id === todayChk.id && o.tracker_id === trackerId);
        if (existingIdx !== -1) {
            allObs[existingIdx].value = value;
            allObs[existingIdx].status = status;
            allObs[existingIdx].check_method = effMethod;
            allObs[existingIdx].quantity_unit = effUnit;
            allObs[existingIdx].config_version_id = effVer;
            allObs[existingIdx].updated_at = new Date().toISOString();
        } else {
            allObs.push({
                id: 'obs_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
                checkin_id: todayChk.id,
                tracker_id: trackerId,
                value: value,
                status: status,
                check_method: effMethod,
                quantity_unit: effUnit,
                config_version_id: effVer,
                note: '',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            });
        }

        try {
            localStorage.setItem(obsKey, JSON.stringify(allObs));
        } catch (e) {}

        // Notify recovery selfcheck core
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.refreshRecoveryHomeIfActive === 'function') {
            window.TempoRecoverySelfCheck.refreshRecoveryHomeIfActive();
        } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.get7DayHistory === 'function') {
            window.TempoRecoverySelfCheck.get7DayHistory();
        }

        if (status === 'answered') {
            if (window.TempoAlertSystem && typeof window.TempoAlertSystem.evaluateAndTriggerAlert === 'function') {
                setTimeout(() => {
                    window.TempoAlertSystem.evaluateAndTriggerAlert(trackerId);
                }, 50);
            }
        }
    }

    function getTodayNote() {
        const uid = getUserId();
        const todayStr = getTodayDateStr();
        const checkinsKey = `tempo_selfcheck_checkins_${uid}`;
        try {
            const rawChk = localStorage.getItem(checkinsKey) || (uid === 'local_user' ? localStorage.getItem('tempo_selfcheck_checkins') : null);
            const checkins = rawChk ? JSON.parse(rawChk) : [];
            const todayChk = checkins.find(c => c.checkin_date === todayStr);
            return todayChk ? (todayChk.overall_note || '') : '';
        } catch (e) {
            return '';
        }
    }

    function setTodayNote(noteText) {
        const uid = getUserId();
        const todayStr = getTodayDateStr();
        const checkinsKey = `tempo_selfcheck_checkins_${uid}`;
        try {
            let checkins = JSON.parse(localStorage.getItem(checkinsKey) || '[]');
            let todayChk = checkins.find(c => c.checkin_date === todayStr);
            if (!todayChk) {
                todayChk = {
                    id: 'chk_' + todayStr.replace(/-/g, '') + '_' + Math.random().toString(36).substr(2, 4),
                    user_id: uid,
                    checkin_date: todayStr,
                    overall_note: noteText,
                    completed_at: new Date().toISOString(),
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                };
                checkins.push(todayChk);
            } else {
                todayChk.overall_note = noteText;
                todayChk.updated_at = new Date().toISOString();
            }
            localStorage.setItem(checkinsKey, JSON.stringify(checkins));
        } catch (e) {}
    }

    // Get observation on specific date for a tracker
    function getObservationForDate(trackerId, dateStr) {
        if (!trackerId || !dateStr) return null;
        const todayStr = getTodayDateStr();
        if (dateStr > todayStr) return null; // Never return observations for future dates

        const uid = getUserId();
        const checkinsKey = `tempo_selfcheck_checkins_${uid}`;
        const obsKey = `tempo_selfcheck_observations_${uid}`;

        try {
            let checkins = [];
            let allObs = [];
            const rawChk = localStorage.getItem(checkinsKey) || localStorage.getItem('tempo_selfcheck_checkins');
            if (rawChk) checkins = JSON.parse(rawChk);
            const rawObs = localStorage.getItem(obsKey) || localStorage.getItem('tempo_selfcheck_observations');
            if (rawObs) allObs = JSON.parse(rawObs);

            const chk = checkins.find(c => c.checkin_date === dateStr);
            if (!chk) return null;

            return allObs.find(o => o.checkin_id === chk.id && o.tracker_id === trackerId) || null;
        } catch (e) {
            return null;
        }
    }

    // Calculate weekly summary metrics for a tracker
    function calculateTrackerWeeklySummary(tracker, weekDays) {
        let checkedCount = 0;
        let sum = 0;
        let countNumeric = 0;
        let goodCount = 0;
        let totalQty = 0;

        weekDays.forEach(day => {
            const obs = getObservationForDate(tracker.id, day.dateStr);
            if (obs && obs.status === 'answered' && obs.value !== null && obs.value !== undefined) {
                checkedCount++;
                const val = obs.value;
                if (typeof val === 'number') {
                    sum += val;
                    countNumeric++;
                    totalQty += val;
                } else if (typeof val === 'string') {
                    const num = parseFloat(val);
                    if (!isNaN(num)) {
                        sum += num;
                        countNumeric++;
                        totalQty += num;
                    }
                    if (val.toLowerCase() === 'good' || val.toLowerCase() === 'yes') {
                        goodCount++;
                    }
                }
            }
        });

        const nameLower = (tracker.name || '').toLowerCase();
        let metricLabel = '';
        let metricValue = '';

        if (tracker.check_method === 'percentage' || nameLower.includes('tension')) {
            const avg = countNumeric > 0 ? `${Math.round(sum / countNumeric)}%` : '0%';
            metricLabel = `Your average ${escapeHTML(nameLower)} level is`;
            metricValue = avg;
        } else if (tracker.check_method === 'yes_no' || nameLower.includes('sleep')) {
            metricLabel = `Nights of Quality Sleep`;
            metricValue = `${goodCount}`;
        } else if (tracker.check_method === 'quantity' || nameLower.includes('walk')) {
            const unit = tracker.quantity_unit || 'min';
            metricLabel = `Total logged this week`;
            metricValue = `${totalQty} ${unit}`;
        } else if (tracker.check_method === 'scale') {
            const avg = countNumeric > 0 ? `${(sum / countNumeric).toFixed(1)}/${tracker.scale_max || 5}` : `0/${tracker.scale_max || 5}`;
            metricLabel = `Average rating`;
            metricValue = avg;
        } else {
            metricLabel = `Your average ${escapeHTML(nameLower)} level is`;
            metricValue = countNumeric > 0 ? `${Math.round(sum / countNumeric)}%` : '0%';
        }

        const summaryHTML = `
            <div class="flex items-center justify-between text-xs sm:text-sm text-[#5B5550]">
                <span>${metricLabel}</span>
                <span class="font-bold text-sm text-[#37352F]">${metricValue}</span>
            </div>
        `;

        return { checkedCount, metricLabel, metricValue, summaryHTML };
    }

    // Format single day observation value for right column table
    function formatDayObservationValue(tracker, obs) {
        if (!obs || obs.status !== 'answered' || obs.value === null || obs.value === undefined) {
            // Unchecked / missed / future day: leave cell completely empty
            return '';
        }

        const val = obs.value;
        const method = obs.check_method || tracker.check_method;
        const nameLower = (tracker.name || '').toLowerCase();

        if (method === 'percentage' || nameLower.includes('tension')) {
            return `<span class="font-semibold text-xs text-[#37352F]">${parseInt(val, 10)}%</span>`;
        }

        if (method === 'yes_no' || method === 'options' || nameLower.includes('sleep')) {
            if (typeof val === 'string' && (val.toLowerCase() === 'good' || val.toLowerCase() === 'yes')) {
                return `<span class="font-semibold text-xs text-[#37352F]">Good</span>`;
            } else if (typeof val === 'string' && (val.toLowerCase() === 'not_good' || val.toLowerCase() === 'no')) {
                return `<span class="font-semibold text-xs text-[#7B7672]">No</span>`;
            }
            return `<span class="font-semibold text-xs text-[#37352F]">${escapeHTML(String(val))}</span>`;
        }

        if (method === 'quantity' || nameLower.includes('walk')) {
            if (val === 'no') {
                return `<span class="font-semibold text-xs text-[#7B7672]">No</span>`;
            }
            const numVal = parseFloat(val);
            if (!isNaN(numVal)) {
                const displayVal = Number.isInteger(numVal) ? numVal : Number(numVal.toFixed(2));
                return `<span class="font-semibold text-xs text-[#37352F]">${displayVal}</span>`;
            }
            return `<span class="font-semibold text-xs text-[#37352F]">${escapeHTML(String(val))}</span>`;
        }

        if (method === 'scale') {
            return `<span class="font-semibold text-xs text-[#37352F]">${escapeHTML(String(val))}</span>`;
        }

        return `<span class="font-semibold text-xs text-[#37352F]">${escapeHTML(String(val))}</span>`;
    }

    // Return to the active context's dashboard
    function returnHome() {
        document.body.style.backgroundColor = '';
        const mainEl = document.querySelector('main');
        if (mainEl) mainEl.style.backgroundColor = '';
        if (window.TempoMode && typeof window.TempoMode.returnToSourceContext === 'function') {
            window.TempoMode.returnToSourceContext();
        } else if (window.TempoMode && typeof window.TempoMode.navigateToActiveDashboard === 'function') {
            window.TempoMode.navigateToActiveDashboard();
        } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('today');
        }
    }

    function open() {
        if (window.TempoMode && typeof window.TempoMode.showStressCheckScreen === 'function') {
            window.TempoMode.showStressCheckScreen();
        } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('stress-check');
        } else {
            window.location.hash = '#stress-check';
        }
        render();
    }

    // Handlers for Today's Self-check interactions in Left Column
    function onTensionInput(val) {
        const valEl = document.getElementById('selfcheck-tension-val');
        if (valEl) valEl.textContent = `${val}%`;
    }

    function onTensionChange(val) {
        const trackers = window.TempoRecoverySelfCheck ? window.TempoRecoverySelfCheck.getActiveTrackers() : [];
        const tensionTrk = trackers.find(t => t.check_method === 'percentage' || t.name.toLowerCase().includes('tension'));
        if (tensionTrk) {
            setTodayObservation(tensionTrk.id, parseInt(val, 10) || 0, 'answered');
            render();
        }
    }

    function setSleepValue(choice) {
        const trackers = window.TempoRecoverySelfCheck ? window.TempoRecoverySelfCheck.getActiveTrackers() : [];
        const sleepTrk = trackers.find(t => t.check_method === 'yes_no' || t.name.toLowerCase().includes('sleep'));
        if (sleepTrk) {
            setTodayObservation(sleepTrk.id, choice, 'answered');
            render();
        }
    }

    // Quantity Tracking Method UI State & Controller
    const quantityChoiceState = {}; // trackerId -> 'yes' | 'no'
    const quantityDraftValues = {}; // trackerId -> string
    const quantityErrorState = {};  // trackerId -> string

    function setQuantityChoice(trackerId, choice) {
        if (!trackerId) return;
        quantityChoiceState[trackerId] = choice;
        delete quantityErrorState[trackerId];

        if (choice === 'no') {
            delete quantityDraftValues[trackerId];
            setTodayObservation(trackerId, 'no', 'answered');
            render();
        } else if (choice === 'yes') {
            const obs = getTodayObservation(trackerId);
            let existingNum = null;
            if (obs && obs.status === 'answered' && typeof obs.value === 'number') {
                existingNum = obs.value;
            } else if (obs && obs.status === 'answered' && typeof obs.value === 'string' && !isNaN(parseFloat(obs.value)) && obs.value !== 'no') {
                existingNum = parseFloat(obs.value);
            }

            if (existingNum !== null && !isNaN(existingNum)) {
                quantityDraftValues[trackerId] = String(existingNum);
                setTodayObservation(trackerId, existingNum, 'answered');
            } else {
                // Do not create a check-in record with a fabricated value when user has not entered a quantity!
                quantityDraftValues[trackerId] = '';
                setTodayObservation(trackerId, null, 'unanswered');
            }
            render();
            setTimeout(() => {
                const inp = document.getElementById(`selfcheck-qty-input-${trackerId}`);
                if (inp) inp.focus();
            }, 50);
        }
    }

    function onQuantityInput(trackerId, valStr) {
        if (!trackerId) return;
        quantityDraftValues[trackerId] = valStr;
        const trimmed = (valStr || '').trim();

        if (trimmed === '') {
            delete quantityErrorState[trackerId];
            setTodayObservation(trackerId, null, 'unanswered');
            const errEl = document.getElementById(`selfcheck-qty-error-${trackerId}`);
            if (errEl) errEl.remove();
            const inp = document.getElementById(`selfcheck-qty-input-${trackerId}`);
            if (inp) {
                inp.classList.remove('border-red-400');
                inp.classList.add('border-stone-300');
            }
            return;
        }

        const num = parseFloat(trimmed);
        if (isNaN(num) || num < 0 || !isFinite(num)) {
            quantityErrorState[trackerId] = 'Please enter a valid non-negative quantity.';
            // Do not save invalid/negative quantity as answered observation!
            setTodayObservation(trackerId, null, 'unanswered');
            const errEl = document.getElementById(`selfcheck-qty-error-${trackerId}`);
            if (errEl) {
                errEl.textContent = quantityErrorState[trackerId];
            } else {
                const container = document.querySelector(`[data-quantity-tracker-id="${trackerId}"]`);
                if (container) {
                    const p = document.createElement('p');
                    p.id = `selfcheck-qty-error-${trackerId}`;
                    p.className = 'text-[11px] text-red-600 font-medium pl-6';
                    p.textContent = quantityErrorState[trackerId];
                    container.appendChild(p);
                }
            }
            const inp = document.getElementById(`selfcheck-qty-input-${trackerId}`);
            if (inp) {
                inp.classList.add('border-red-400');
                inp.classList.remove('border-stone-300');
            }
        } else {
            delete quantityErrorState[trackerId];
            setTodayObservation(trackerId, num, 'answered');
            const errEl = document.getElementById(`selfcheck-qty-error-${trackerId}`);
            if (errEl) errEl.remove();
            const inp = document.getElementById(`selfcheck-qty-input-${trackerId}`);
            if (inp) {
                inp.classList.remove('border-red-400');
                inp.classList.add('border-stone-300');
            }
        }
    }

    function onQuantityChange(trackerId, valStr) {
        onQuantityInput(trackerId, valStr);
        render();
    }

    function setWalkChoice(choice) {
        const trackers = window.TempoRecoverySelfCheck ? window.TempoRecoverySelfCheck.getActiveTrackers() : [];
        const walkTrk = trackers.find(t => t.check_method === 'quantity' || t.name.toLowerCase().includes('walk'));
        if (walkTrk) {
            setQuantityChoice(walkTrk.id, choice);
        }
    }

    function setWalkMinutes(mins) {
        const trackers = window.TempoRecoverySelfCheck ? window.TempoRecoverySelfCheck.getActiveTrackers() : [];
        const walkTrk = trackers.find(t => t.check_method === 'quantity' || t.name.toLowerCase().includes('walk'));
        if (walkTrk) {
            onQuantityInput(walkTrk.id, String(mins));
            onQuantityChange(walkTrk.id, String(mins));
        }
    }

    function renderQuantityCheckinSection(tracker) {
        if (!tracker) return '';
        const obs = getTodayObservation(tracker.id);

        let choice = quantityChoiceState[tracker.id];
        let draftVal = quantityDraftValues[tracker.id];
        let errorMsg = quantityErrorState[tracker.id] || '';

        if (choice === undefined || choice === null) {
            if (obs && obs.status === 'answered' && obs.value !== null && obs.value !== undefined) {
                if (obs.value === 'no') {
                    choice = 'no';
                } else {
                    choice = 'yes';
                    if (draftVal === undefined) {
                        draftVal = String(obs.value);
                    }
                }
            } else {
                choice = null;
            }
        }

        const dotColor = tracker.type_color || (tracker.category === 'stress_sign' ? '#D48366' : (tracker.category === 'supportive' ? '#166545' : '#1E40AF'));
        const unit = tracker.quantity_unit || 'min';
        const isWalk = (tracker.name || '').toLowerCase().includes('walk');
        const questionText = isWalk ? 'Did you go for a walk today?' : `Did you log your ${escapeHTML((tracker.name || '').toLowerCase())} today?`;
        const radioName = isWalk ? 'selfcheck_walk_today' : `selfcheck_qty_${tracker.id}`;
        const inputId = `selfcheck-qty-input-${tracker.id}`;

        const isYesChecked = choice === 'yes';
        const isNoChecked = choice === 'no';
        const displayVal = draftVal !== undefined && draftVal !== null ? escapeHTML(String(draftVal)) : '';

        return `
            <div class="space-y-1.5" data-quantity-tracker-id="${tracker.id}">
                <div class="flex items-center space-x-2 text-sm font-bold text-[#37352F]">
                    <span class="w-2.5 h-2.5 rounded-full inline-block shrink-0" style="background-color: ${dotColor};"></span>
                    <span>${escapeHTML(tracker.name)}</span>
                </div>
                <p class="text-xs text-[#5B5550]">${questionText}</p>
                <div class="space-y-1.5 text-xs text-[#5B5550]">
                    <div class="flex items-center flex-wrap gap-2">
                        <label class="flex items-center space-x-2 cursor-pointer shrink-0">
                            <input type="radio" 
                                   name="${radioName}" 
                                   value="yes" 
                                   ${isYesChecked ? 'checked' : ''}
                                   onchange="window.TempoSelfCheckWorkspace.setQuantityChoice('${tracker.id}', 'yes')"
                                   class="accent-[#166545]">
                            <span>Yes</span>
                        </label>
                        ${isYesChecked ? `
                            <div class="inline-flex items-center space-x-1.5 pl-0.5">
                                <span class="text-stone-500 font-medium">For</span>
                                <input type="number" 
                                       id="${inputId}"
                                       data-tracker-id="${tracker.id}"
                                       step="any"
                                       min="0"
                                       placeholder="Enter quantity"
                                       value="${displayVal}"
                                       oninput="window.TempoSelfCheckWorkspace.onQuantityInput('${tracker.id}', this.value)"
                                       onchange="window.TempoSelfCheckWorkspace.onQuantityChange('${tracker.id}', this.value)"
                                       class="w-28 sm:w-32 px-2.5 py-1 bg-white border ${errorMsg ? 'border-red-400 focus:border-red-500' : 'border-stone-300 focus:border-[#4A6B5D]'} rounded-lg text-xs font-semibold text-[#202124] placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-[#4A6B5D]">
                                <span class="text-xs font-bold text-[#37352F]">${escapeHTML(unit)}</span>
                            </div>
                        ` : ''}
                    </div>
                    ${isYesChecked && errorMsg ? `<p id="selfcheck-qty-error-${tracker.id}" class="text-[11px] text-red-600 font-medium pl-6">${escapeHTML(errorMsg)}</p>` : ''}
                    <label class="flex items-center space-x-2 cursor-pointer">
                        <input type="radio" 
                               name="${radioName}" 
                               value="no" 
                               ${isNoChecked ? 'checked' : ''}
                               onchange="window.TempoSelfCheckWorkspace.setQuantityChoice('${tracker.id}', 'no')"
                               class="accent-[#166545]">
                        <span>No, i didn't</span>
                    </label>
                </div>
            </div>
        `;
    }

    function toggleNoteInput() {
        showNoteInput = !showNoteInput;
        const noteBox = document.getElementById('selfcheck-today-note-box');
        if (noteBox) {
            noteBox.classList.toggle('hidden', !showNoteInput);
            if (showNoteInput) {
                const txt = document.getElementById('selfcheck-today-note-textarea');
                if (txt) txt.focus();
            }
        }
    }

    function saveTodayNote() {
        const txt = document.getElementById('selfcheck-today-note-textarea');
        if (txt) {
            setTodayNote(txt.value.trim());
            showNoteInput = false;
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Note saved for today.");
            }
            render();
        }
    }

    // Modal Triggers
    function openWeeklyReport() {
        // Build and display weekly report modal
        const modal = document.getElementById('modal-selfcheck-weekly-report');
        if (!modal) return;

        const dateRangeEl = document.getElementById('selfcheck-weekly-report-dates');
        if (dateRangeEl) dateRangeEl.textContent = getWeekDateRangeStr();

        const contentEl = document.getElementById('selfcheck-weekly-report-content');
        if (contentEl) {
            const streak = window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.calculateStreak === 'function'
                ? window.TempoRecoverySelfCheck.calculateStreak()
                : 0;
            const trackers = window.TempoRecoverySelfCheck ? window.TempoRecoverySelfCheck.getActiveTrackers() : [];
            const days = getCurrentWeekDays();

            let summaryItemsHTML = trackers.map(t => {
                const s = calculateTrackerWeeklySummary(t, days);
                return `
                    <div class="p-3.5 rounded-2xl bg-stone-50 border border-stone-200 flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: ${t.category === 'stress_sign' ? '#D48366' : (t.category === 'supportive' ? '#166545' : '#1E40AF')};"></span>
                            <span class="font-bold text-xs sm:text-sm text-[#202124]">${escapeHTML(t.name)}</span>
                        </div>
                        <div class="text-right">
                            <span class="text-xs font-semibold text-[#5B5550]">Checked: ${s.checkedCount}/7 days</span>
                        </div>
                    </div>
                `;
            }).join('');

            contentEl.innerHTML = `
                <div class="space-y-4">
                    <div class="p-4 rounded-2xl bg-[#EDF7F1] border border-[#CDE9DA] flex items-center justify-between">
                        <div>
                            <span class="text-xs font-bold text-[#166545] uppercase tracking-wider block">CONSISTENCY</span>
                            <h4 class="font-heading text-lg font-extrabold text-[#202124]">${streak}-day check-in streak</h4>
                        </div>
                        <span class="text-2xl select-none">🌱</span>
                    </div>

                    <div class="space-y-2">
                        <h5 class="text-xs font-bold uppercase tracking-wider text-[#6F6B68]">Tracker Summary for this week</h5>
                        <div class="space-y-2">
                            ${summaryItemsHTML || '<p class="text-xs text-stone-500 italic">No active trackers.</p>'}
                        </div>
                    </div>
                </div>
            `;
        }

        modal.classList.remove('hidden');
    }

    function closeWeeklyReport() {
        const modal = document.getElementById('modal-selfcheck-weekly-report');
        if (modal) modal.classList.add('hidden');
    }

    function openRecoveryNotice() {
        // Specifically opens the Recovery Note popup/flow from Recovery Mode (NOT Tool Notes)
        if (window.TempoRecoveryNote && typeof window.TempoRecoveryNote.openViewModal === 'function') {
            window.TempoRecoveryNote.openViewModal();
        } else if (window.TempoRecoveryNote && typeof window.TempoRecoveryNote.openEditModal === 'function') {
            window.TempoRecoveryNote.openEditModal();
        }
    }

    function openAddTracking() {
        adjustDraftState = {
            mode: 'create',
            trackerId: null,
            trackerName: '',
            typeId: 'stress_sign',
            typeName: 'Sign of stress',
            typeColor: '#C34D2E',
            checkMethod: 'percentage',
            options: ['Yes', 'No'],
            scaleRange: '1-5',
            quantityUnit: 'minutes',
            alertEnabled: true,
            alertType: 'stress_sign',
            alertOperator: 'more_than',
            alertThreshold: 60,
            alertDays: 4,
            alertTargetOption: 'Yes',
            showNewTypeForm: false,
            newTypeError: '',
            selectedNewColor: '#C34D2E',
            nameError: '',
            isSaving: false
        };

        renderAdjustModal();
        const modal = document.getElementById('modal-selfcheck-adjust');
        if (modal) modal.classList.remove('hidden');
        setTimeout(() => {
            const inp = document.getElementById('adjust-tracker-name-input');
            if (inp) inp.focus();
        }, 50);
    }

    // =========================================================================
    // CUSTOM TRACKING TYPES & ALERT SYSTEM HELPERS
    // =========================================================================

    function getCustomTypes() {
        const uid = getUserId();
        const key = `tempo_selfcheck_custom_types_${uid}`;
        try {
            const raw = localStorage.getItem(key);
            if (raw) return JSON.parse(raw);
            if (uid === 'local_user') {
                const legacy = localStorage.getItem('tempo_selfcheck_custom_types');
                if (legacy) return JSON.parse(legacy);
            }
        } catch (e) {}
        return [];
    }

    function saveCustomType(name, color) {
        if (!name || !name.trim()) {
            return { error: 'Please enter a type name.' };
        }
        const cleanName = name.trim();
        const nameLower = cleanName.toLowerCase();

        // Disallow duplicating default names
        if (nameLower === 'sign of stress' || nameLower === 'supportive' || nameLower === 'general') {
            return { error: 'This is a default tracking type and cannot be duplicated.' };
        }

        const existing = getCustomTypes();
        if (existing.some(t => t.name.toLowerCase() === nameLower)) {
            return { error: 'A tracking type with this name already exists.' };
        }

        const newType = {
            id: 'type_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
            name: cleanName,
            color: color || '#859B8B',
            created_at: new Date().toISOString()
        };

        existing.push(newType);
        const uid = getUserId();
        const key = `tempo_selfcheck_custom_types_${uid}`;
        try {
            localStorage.setItem(key, JSON.stringify(existing));
            if (uid === 'local_user') {
                localStorage.setItem('tempo_selfcheck_custom_types', JSON.stringify(existing));
            }
        } catch (e) {}

        return { success: true, type: newType };
    }

    // Evaluate consecutive-day alert condition from actual persisted records
    function checkTrackerAlert(tracker) {
        if (window.TempoAlertSystem && typeof window.TempoAlertSystem.evaluateTrackerAlert === 'function') {
            return window.TempoAlertSystem.evaluateTrackerAlert(tracker);
        }
        if (!tracker || !tracker.alert_enabled || !tracker.alert_config) {
            return { triggered: false, consecutiveCount: 0 };
        }
        const cfg = tracker.alert_config;
        const requiredDays = parseInt(cfg.days, 10) || 1;
        if (requiredDays < 1) return { triggered: false, consecutiveCount: 0 };

        const todayStr = getTodayDateStr();
        let consecutiveMet = 0;

        for (let i = 0; i < requiredDays; i++) {
            const dStr = shiftDateStr(todayStr, -i);
            const obs = getObservationForDate(tracker.id, dStr);
            if (!obs || obs.status !== 'answered' || obs.value === null || obs.value === undefined) {
                return { triggered: false, consecutiveCount: consecutiveMet };
            }

            const val = obs.value;
            let dayMet = false;
            const method = tracker.check_method;

            if (method === 'percentage' || (tracker.name || '').toLowerCase().includes('tension')) {
                const num = parseFloat(val);
                const thresh = parseFloat(cfg.threshold);
                if (!isNaN(num) && !isNaN(thresh)) {
                    dayMet = (cfg.operator === 'less_than') ? (num < thresh) : (num > thresh);
                }
            } else if (method === 'options' || method === 'yes_no' || (tracker.name || '').toLowerCase().includes('sleep')) {
                if (cfg.target_option) {
                    dayMet = String(val).toLowerCase() === String(cfg.target_option).toLowerCase();
                }
            } else if (method === 'scale') {
                const num = parseFloat(val);
                const thresh = parseFloat(cfg.threshold);
                if (!isNaN(num) && !isNaN(thresh)) {
                    dayMet = (cfg.operator === 'less_than') ? (num < thresh) : (num > thresh);
                }
            } else if (method === 'quantity' || (tracker.name || '').toLowerCase().includes('walk')) {
                if (cfg.operator === 'didnt_do' || (cfg.target_option && String(cfg.target_option).toLowerCase().includes("didn't"))) {
                    dayMet = val === 'no' || val === 0 || String(val).toLowerCase().includes("didn't");
                } else {
                    const num = (val === 'no' || String(val).toLowerCase().includes("didn't")) ? 0 : parseFloat(val);
                    const thresh = parseFloat(cfg.threshold);
                    if (!isNaN(num) && !isNaN(thresh)) {
                        dayMet = (cfg.operator === 'less_than') ? (num < thresh) : (num > thresh);
                    }
                }
            }

            if (dayMet) {
                consecutiveMet++;
            } else {
                return { triggered: false, consecutiveCount: consecutiveMet };
            }
        }

        if (consecutiveMet >= requiredDays) {
            return { triggered: true, consecutiveCount: consecutiveMet };
        }
        return { triggered: false, consecutiveCount: consecutiveMet };
    }

    // =========================================================================
    // ADJUST TRACKING POPUP CONTROLLER & STATE
    // =========================================================================

    let adjustDraftState = null;

    function openAdjustTracker(trackerId) {
        let tracker = null;
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerById === 'function') {
            tracker = window.TempoRecoverySelfCheck.getTrackerById(trackerId);
        }
        if (!tracker && window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function') {
            const active = window.TempoRecoverySelfCheck.getActiveTrackers();
            tracker = active.find(t => t.id === trackerId);
        }
        if (!tracker) return;

        let defaultMethod = tracker.check_method || 'percentage';
        if (defaultMethod === 'yes_no') defaultMethod = 'options';

        let defaultOptions = tracker.options;
        if (!defaultOptions || !Array.isArray(defaultOptions) || defaultOptions.length === 0) {
            defaultOptions = (tracker.name || '').toLowerCase().includes('sleep') ? ['Good', 'Not good'] : ['Yes', 'No'];
        }

        const alertCfg = tracker.alert_config || {};

        adjustDraftState = {
            mode: 'edit',
            trackerId: tracker.id,
            trackerName: tracker.name || '',
            typeId: tracker.type_id || tracker.category || 'stress_sign',
            typeName: tracker.type_label || (tracker.category === 'supportive' ? 'Supportive' : 'Sign of stress'),
            typeColor: tracker.type_color || (tracker.category === 'supportive' ? '#859B8B' : '#C34D2E'),
            checkMethod: defaultMethod,
            options: [...defaultOptions],
            scaleRange: tracker.scale_range || (tracker.scale_max === 10 ? '1-10' : '1-5'),
            quantityUnit: tracker.quantity_unit || 'minutes',
            alertEnabled: tracker.alert_enabled !== undefined ? tracker.alert_enabled : true,
            alertType: alertCfg.alert_type || (tracker.category === 'supportive' ? 'supportive_reminder' : 'stress_sign'),
            alertOperator: alertCfg.operator || 'more_than',
            alertThreshold: alertCfg.threshold !== undefined ? alertCfg.threshold : (defaultMethod === 'scale' ? 3 : 60),
            alertDays: alertCfg.days || 4,
            alertTargetOption: alertCfg.target_option || defaultOptions[0] || 'Yes',
            showNewTypeForm: false,
            newTypeError: '',
            selectedNewColor: '#C34D2E',
            nameError: '',
            isSaving: false
        };

        renderAdjustModal();
        const modal = document.getElementById('modal-selfcheck-adjust');
        if (modal) modal.classList.remove('hidden');
    }

    function closeAdjustModal() {
        const modal = document.getElementById('modal-selfcheck-adjust');
        if (modal) modal.classList.add('hidden');
        adjustDraftState = null;
    }

    function setDraftTrackerName(name) {
        if (!adjustDraftState) return;
        adjustDraftState.trackerName = name;
        if (name && name.trim() && adjustDraftState.nameError) {
            adjustDraftState.nameError = '';
            const errEl = document.getElementById('adjust-name-error-msg');
            if (errEl) errEl.remove();
            const inp = document.getElementById('adjust-tracker-name-input');
            if (inp) {
                inp.classList.remove('border-red-400', 'focus:border-red-500', 'ring-1', 'ring-red-400');
                inp.classList.add('border-stone-300/80', 'focus:border-[#4A6B53]');
            }
        }
    }

    function setCustomObservation(trackerId, value) {
        setTodayObservation(trackerId, value, 'answered');
        render();
    }

    function setAdjustType(typeId, typeName, typeColor) {
        if (!adjustDraftState) return;
        adjustDraftState.typeId = typeId;
        adjustDraftState.typeName = typeName;
        adjustDraftState.typeColor = typeColor;
        renderAdjustModal();
    }

    function toggleCreateNewTypeForm(show = null) {
        if (!adjustDraftState) return;
        adjustDraftState.showNewTypeForm = (show !== null) ? show : !adjustDraftState.showNewTypeForm;
        adjustDraftState.newTypeError = '';
        renderAdjustModal();
    }

    function setNewTypeColor(color) {
        if (!adjustDraftState) return;
        const input = document.getElementById('adjust-new-type-input');
        if (input) adjustDraftState.newTypeName = input.value;
        adjustDraftState.selectedNewColor = color;
        renderAdjustModal();
    }

    function setDraftNewTypeName(name) {
        if (adjustDraftState) adjustDraftState.newTypeName = name;
    }

    function saveNewType() {
        if (!adjustDraftState) return;
        const input = document.getElementById('adjust-new-type-input');
        const name = (input && input.value.trim()) ? input.value.trim() : (adjustDraftState.newTypeName || '');
        const color = adjustDraftState.selectedNewColor || '#859B8B';

        const res = saveCustomType(name, color);
        if (res.error) {
            adjustDraftState.newTypeError = res.error;
            renderAdjustModal();
            return;
        }

        // Auto select newly created custom type
        adjustDraftState.typeId = res.type.id;
        adjustDraftState.typeName = res.type.name;
        adjustDraftState.typeColor = res.type.color;
        adjustDraftState.newTypeName = '';
        adjustDraftState.showNewTypeForm = false;
        adjustDraftState.newTypeError = '';
        renderAdjustModal();
    }

    function setAdjustMethod(method) {
        if (!adjustDraftState) return;
        readCurrentAlertInputs();
        adjustDraftState.checkMethod = method;
        if (method === 'scale' && (adjustDraftState.alertThreshold === 60 || adjustDraftState.alertThreshold > 10)) {
            adjustDraftState.alertThreshold = 3;
        } else if (method === 'percentage' && adjustDraftState.alertThreshold <= 10) {
            adjustDraftState.alertThreshold = 60;
        }
        renderAdjustModal();
    }

    function addAdjustOption() {
        if (!adjustDraftState) return;
        const input = document.getElementById('adjust-new-option-input');
        const opt = input ? input.value.trim() : '';
        if (opt && !adjustDraftState.options.includes(opt)) {
            adjustDraftState.options.push(opt);
            renderAdjustModal();
        }
    }

    function removeAdjustOption(opt) {
        if (!adjustDraftState || adjustDraftState.options.length <= 1) return;
        adjustDraftState.options = adjustDraftState.options.filter(o => o !== opt);
        if (adjustDraftState.alertTargetOption === opt) {
            adjustDraftState.alertTargetOption = adjustDraftState.options[0] || '';
        }
        renderAdjustModal();
    }

    function setAdjustScaleRange(range) {
        if (!adjustDraftState) return;
        adjustDraftState.scaleRange = range;
        renderAdjustModal();
    }

    function setAdjustQuantityUnit(unit) {
        if (!adjustDraftState) return;
        adjustDraftState.quantityUnit = unit ? unit.trim() : 'minutes';
        const unitLabel = document.getElementById('adjust-alert-unit-label');
        if (unitLabel) unitLabel.textContent = adjustDraftState.quantityUnit;
    }

    function toggleAdjustAlertSystem() {
        if (!adjustDraftState) return;
        readCurrentAlertInputs();
        adjustDraftState.alertEnabled = !adjustDraftState.alertEnabled;
        renderAdjustModal();
    }

    function onAlertOperatorChanged(val) {
        if (!adjustDraftState) return;
        readCurrentAlertInputs();
        adjustDraftState.alertOperator = val;
        renderAdjustModal();
    }

    function readCurrentAlertInputs() {
        if (!adjustDraftState) return;
        const typeEl = document.getElementById('adjust-alert-type');
        if (typeEl) adjustDraftState.alertType = typeEl.value;
        const opEl = document.getElementById('adjust-alert-operator');
        if (opEl) adjustDraftState.alertOperator = opEl.value;

        const threshEl = document.getElementById('adjust-alert-threshold');
        if (threshEl) adjustDraftState.alertThreshold = parseFloat(threshEl.value) || 0;

        const daysEl = document.getElementById('adjust-alert-days');
        if (daysEl) adjustDraftState.alertDays = parseInt(daysEl.value, 10) || 1;

        const targetEl = document.getElementById('adjust-alert-option-target');
        if (targetEl) adjustDraftState.alertTargetOption = targetEl.value;
    }

    function saveAdjustTracker() {
        if (!adjustDraftState) return;
        if (adjustDraftState.isSaving) return; // Prevent duplicate submissions

        readCurrentAlertInputs();

        // Read current name from input if present
        const nameInp = document.getElementById('adjust-tracker-name-input');
        const rawName = nameInp ? nameInp.value : (adjustDraftState.trackerName || '');
        const cleanName = rawName.trim();

        // Validate: Require a valid, non-empty tracking name before saving
        if (!cleanName) {
            adjustDraftState.nameError = 'Please enter a tracking name.';
            renderAdjustModal();
            const inp = document.getElementById('adjust-tracker-name-input');
            if (inp) inp.focus();
            return;
        }

        adjustDraftState.trackerName = cleanName;
        adjustDraftState.isSaving = true;

        const saveBtn = document.getElementById('adjust-save-submit-btn');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.classList.add('opacity-50', 'cursor-not-allowed');
        }

        const scaleMax = adjustDraftState.scaleRange === '1-10' ? 10 : 5;
        const alertConfig = {
            alert_type: adjustDraftState.alertType || (adjustDraftState.typeId === 'supportive' || adjustDraftState.typeName === 'Supportive' ? 'supportive_reminder' : 'stress_sign'),
            operator: adjustDraftState.alertOperator,
            threshold: adjustDraftState.alertThreshold,
            days: adjustDraftState.alertDays,
            target_option: adjustDraftState.alertTargetOption,
            unit: adjustDraftState.quantityUnit,
            scale_range: adjustDraftState.scaleRange
        };

        const trackerPayload = {
            name: cleanName,
            category: (adjustDraftState.typeId === 'stress_sign' || adjustDraftState.typeId === 'supportive') 
                ? adjustDraftState.typeId 
                : 'stress_sign',
            type_id: adjustDraftState.typeId,
            type_label: adjustDraftState.typeName,
            type_color: adjustDraftState.typeColor,
            check_method: adjustDraftState.checkMethod,
            options: adjustDraftState.options,
            scale_min: 1,
            scale_max: scaleMax,
            scale_range: adjustDraftState.scaleRange,
            quantity_unit: adjustDraftState.quantityUnit,
            alert_enabled: adjustDraftState.alertEnabled,
            alert_config: alertConfig
        };

        try {
            if (adjustDraftState.mode === 'create') {
                // If an active tracker with this name already exists, update it instead of creating a duplicate
                const existingActive = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function')
                    ? window.TempoRecoverySelfCheck.getActiveTrackers().find(t => (t.name || '').trim().toLowerCase() === cleanName.toLowerCase())
                    : null;

                if (existingActive) {
                    adjustDraftState.mode = 'edit';
                    adjustDraftState.trackerId = existingActive.id;
                }
            }

            if (adjustDraftState.mode === 'create') {
                let newTracker = null;
                if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.createTracker === 'function') {
                    newTracker = window.TempoRecoverySelfCheck.createTracker(trackerPayload);
                }
                if (newTracker && window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.updateTracker === 'function') {
                    window.TempoRecoverySelfCheck.updateTracker(newTracker.id, trackerPayload);
                }

                closeAdjustModal();
                render();

                if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                    window.TempoApp.showToast(`"${cleanName}" added to Your Tracking System.`);
                }
            } else {
                const trackerId = adjustDraftState.trackerId;
                if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.updateTracker === 'function') {
                    window.TempoRecoverySelfCheck.updateTracker(trackerId, trackerPayload);
                }

                closeAdjustModal();
                render();

                if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                    window.TempoApp.showToast(`"${cleanName}" updated successfully.`);
                }
            }
        } catch (err) {
            console.error("Error saving tracking configuration:", err);
            adjustDraftState.isSaving = false;
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            }
            adjustDraftState.nameError = err && err.message ? err.message : 'Failed to save tracker. Please try again.';
            renderAdjustModal();
        }
    }

    function renderAdjustModal() {
        const container = document.getElementById('selfcheck-adjust-modal-card');
        if (!container || !adjustDraftState) return;
        const draft = adjustDraftState;

        const customTypes = getCustomTypes();
        const customTypesHTML = customTypes.map(t => {
            const isSelected = draft.typeId === t.id;
            const style = isSelected 
                ? `background-color: ${t.color}; color: #ffffff;` 
                : `background-color: ${t.color}25; color: ${t.color}; border: 1px solid ${t.color}50;`;
            return `
                <button type="button" 
                        onclick="window.TempoSelfCheckWorkspace.setAdjustType('${t.id}', '${escapeHTML(t.name)}', '${t.color}')"
                        class="px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer shadow-2xs"
                        style="${style}">
                    ${escapeHTML(t.name)}
                </button>
            `;
        }).join('');

        // Preset colors for new type form
        const presetColors = ['#C34D2E', '#859B8B', '#2563EB', '#7C3AED', '#D97706', '#0D9488', '#EC4899', '#4B5563'];
        const colorButtonsHTML = presetColors.map(c => `
            <button type="button" 
                    onclick="window.TempoSelfCheckWorkspace.setNewTypeColor('${c}')"
                    class="w-6 h-6 rounded-full cursor-pointer transition transform ${draft.selectedNewColor === c ? 'scale-110 ring-2 ring-offset-1 ring-stone-600' : 'hover:scale-105'}"
                    style="background-color: ${c};" 
                    title="${c}">
            </button>
        `).join('');

        const newTypeFormHTML = draft.showNewTypeForm ? `
            <div class="mt-2.5 p-3.5 bg-white rounded-2xl border border-stone-200/80 space-y-2.5 shadow-2xs">
                <span class="text-[11px] font-bold text-[#5B5550] block">Create new type</span>
                <input type="text" id="adjust-new-type-input" placeholder="Type label (e.g. Physical, Habit)..." 
                       value="${escapeHTML(draft.newTypeName || '')}"
                       oninput="if(window.TempoSelfCheckWorkspace.setDraftNewTypeName) window.TempoSelfCheckWorkspace.setDraftNewTypeName(this.value)"
                       class="w-full px-3 py-1.5 text-xs rounded-xl border border-stone-300 focus:outline-none focus:border-[#4A6B53]">
                <div class="space-y-1">
                    <span class="text-[10px] text-stone-500 font-semibold block">Choose color:</span>
                    <div class="flex items-center space-x-2">
                        <div class="flex items-center space-x-1.5">${colorButtonsHTML}</div>
                        <input type="color" value="${draft.selectedNewColor}" 
                               onchange="window.TempoSelfCheckWorkspace.setNewTypeColor(this.value)"
                               class="w-6 h-6 rounded cursor-pointer border-0 p-0" title="Custom color picker">
                    </div>
                </div>
                ${draft.newTypeError ? `<p class="text-[11px] text-red-600 font-semibold">${escapeHTML(draft.newTypeError)}</p>` : ''}
                <div class="flex items-center space-x-2 pt-1">
                    <button type="button" onclick="window.TempoSelfCheckWorkspace.saveNewType()" 
                            class="px-3.5 py-1 rounded-xl text-xs font-bold bg-[#859B8B] hover:bg-[#748A7A] text-white transition">
                        Save type
                    </button>
                    <button type="button" onclick="window.TempoSelfCheckWorkspace.toggleCreateNewTypeForm(false)" 
                            class="px-2 py-1 text-xs text-stone-500 hover:text-stone-800 transition">
                        Cancel
                    </button>
                </div>
            </div>
        ` : '';

        // Method sub-config (options tag editor, scale selector, or quantity unit)
        let methodConfigHTML = '';
        if (draft.checkMethod === 'options') {
            methodConfigHTML = `
                <div class="p-2.5 bg-stone-100/70 rounded-xl space-y-1.5 mt-2 border border-stone-200/60">
                    <div class="flex items-center justify-between">
                        <span class="text-[11px] font-bold text-[#5B5550]">Configured options:</span>
                        <span class="text-[10px] text-stone-400">Click ✕ to remove</span>
                    </div>
                    <div class="flex flex-wrap gap-1.5 items-center">
                        ${draft.options.map(opt => `
                            <span class="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-lg text-xs font-semibold bg-white border border-stone-300 text-[#284132]">
                                <span>${escapeHTML(opt)}</span>
                                ${draft.options.length > 2 ? `<button type="button" onclick="window.TempoSelfCheckWorkspace.removeAdjustOption('${escapeHTML(opt)}')" class="text-stone-400 hover:text-red-500 ml-1">✕</button>` : ''}
                            </span>
                        `).join('')}
                    </div>
                    <div class="flex items-center space-x-2 pt-1">
                        <input type="text" id="adjust-new-option-input" placeholder="Add custom option (e.g. Maybe)..." 
                               class="px-2.5 py-1 rounded-lg border border-stone-300 text-xs w-48 bg-white focus:outline-none">
                        <button type="button" onclick="window.TempoSelfCheckWorkspace.addAdjustOption()" 
                                class="px-3 py-1 rounded-lg text-xs font-bold bg-[#859B8B] text-white hover:bg-[#748A7A] transition">
                            Add
                        </button>
                    </div>
                </div>
            `;
        } else if (draft.checkMethod === 'scale') {
            methodConfigHTML = `
                <div class="p-2.5 bg-stone-100/70 rounded-xl flex items-center space-x-3 mt-2 border border-stone-200/60">
                    <span class="text-[11px] font-bold text-[#5B5550]">Scale range:</span>
                    <button type="button" onclick="window.TempoSelfCheckWorkspace.setAdjustScaleRange('1-5')"
                            class="px-3 py-1 rounded-lg text-xs font-bold transition ${draft.scaleRange === '1-5' ? 'bg-[#859B8B] text-white shadow-2xs' : 'bg-white text-stone-700 border border-stone-300'}">
                        1 to 5
                    </button>
                    <button type="button" onclick="window.TempoSelfCheckWorkspace.setAdjustScaleRange('1-10')"
                            class="px-3 py-1 rounded-lg text-xs font-bold transition ${draft.scaleRange === '1-10' ? 'bg-[#859B8B] text-white shadow-2xs' : 'bg-white text-stone-700 border border-stone-300'}">
                        1 to 10
                    </button>
                </div>
            `;
        } else if (draft.checkMethod === 'quantity') {
            methodConfigHTML = `
                <div class="p-2.5 bg-stone-100/70 rounded-xl space-y-1.5 mt-2 border border-stone-200/60">
                    <span class="text-[11px] font-bold text-[#5B5550]">Measurement unit:</span>
                    <div class="flex flex-wrap gap-1.5 items-center">
                        ${['minutes', 'steps', 'times', 'hours', 'glasses', 'pages'].map(u => `
                            <button type="button" onclick="window.TempoSelfCheckWorkspace.setAdjustQuantityUnit('${u}')"
                                    class="px-2.5 py-0.5 rounded-lg text-xs font-semibold transition ${draft.quantityUnit === u ? 'bg-[#859B8B] text-white shadow-2xs' : 'bg-white text-stone-700 border border-stone-300 hover:bg-stone-50'}">
                                ${u}
                            </button>
                        `).join('')}
                    </div>
                    <div class="flex items-center space-x-2 pt-1">
                        <input type="text" id="adjust-custom-unit-input" placeholder="Custom unit (e.g. km, laps)..." 
                               value="${!['minutes', 'steps', 'times', 'hours', 'glasses', 'pages'].includes(draft.quantityUnit) ? draft.quantityUnit : ''}"
                               class="px-2.5 py-1 rounded-lg border border-stone-300 text-xs w-44 bg-white focus:outline-none"
                               oninput="window.TempoSelfCheckWorkspace.setAdjustQuantityUnit(this.value)">
                    </div>
                </div>
            `;
        }

        const alertTypeSelectorHTML = `
            <div class="flex items-center space-x-2 pt-1 pb-1.5">
                <span class="text-xs font-semibold text-[#5B5550]">Alert type:</span>
                <select id="adjust-alert-type" onchange="if(window.TempoSelfCheckWorkspace.readCurrentAlertInputs) window.TempoSelfCheckWorkspace.readCurrentAlertInputs()" class="px-2.5 py-1 text-xs rounded-xl border border-stone-300 bg-white font-bold text-[#284132] focus:outline-none">
                    <option value="stress_sign" ${draft.alertType === 'stress_sign' ? 'selected' : ''}>Sign of Stress</option>
                    <option value="supportive_reminder" ${draft.alertType === 'supportive_reminder' ? 'selected' : ''}>Supportive Reminder</option>
                </select>
            </div>
        `;

        // Method-specific Alert Controls matching screenshot design
        let alertControlsHTML = '';
        if (draft.checkMethod === 'percentage') {
            alertControlsHTML = `
                <div class="flex flex-wrap items-center gap-1.5 text-xs sm:text-sm text-[#284132] font-medium pt-1">
                    <select id="adjust-alert-operator" class="px-2.5 py-1.5 rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                        <option value="more_than" ${draft.alertOperator === 'more_than' ? 'selected' : ''}>More than</option>
                        <option value="less_than" ${draft.alertOperator === 'less_than' ? 'selected' : ''}>Less than</option>
                    </select>
                    <input type="number" id="adjust-alert-threshold" value="${draft.alertThreshold}" min="0" max="100" 
                           class="w-12 px-1.5 py-1.5 text-center rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                    <span>% for</span>
                    <input type="number" id="adjust-alert-days" value="${draft.alertDays}" min="1" max="30" 
                           class="w-10 px-1 py-1.5 text-center rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                    <span>days in a row.</span>
                </div>
            `;
        } else if (draft.checkMethod === 'options') {
            alertControlsHTML = `
                <div class="flex flex-wrap items-center gap-1.5 text-xs sm:text-sm text-[#284132] font-medium pt-1">
                    <span>Alert me when I select</span>
                    <select id="adjust-alert-option-target" class="px-2.5 py-1.5 rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                        ${draft.options.map(opt => `<option value="${escapeHTML(opt)}" ${opt === draft.alertTargetOption ? 'selected' : ''}>${escapeHTML(opt)}</option>`).join('')}
                    </select>
                    <span>for</span>
                    <input type="number" id="adjust-alert-days" value="${draft.alertDays}" min="1" max="30" 
                           class="w-10 px-1 py-1.5 text-center rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                    <span>days in a row.</span>
                </div>
            `;
        } else if (draft.checkMethod === 'scale') {
            const scaleMax = draft.scaleRange === '1-10' ? 10 : 5;
            const scaleNumbers = [];
            for (let i = 1; i <= scaleMax; i++) scaleNumbers.push(i);

            alertControlsHTML = `
                <div class="flex flex-wrap items-center gap-1.5 text-xs sm:text-sm text-[#284132] font-medium pt-1">
                    <select id="adjust-alert-operator" class="px-2.5 py-1.5 rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                        <option value="more_than" ${draft.alertOperator === 'more_than' ? 'selected' : ''}>More than</option>
                        <option value="less_than" ${draft.alertOperator === 'less_than' ? 'selected' : ''}>Less than</option>
                    </select>
                    <select id="adjust-alert-threshold" class="px-2 py-1.5 rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                        ${scaleNumbers.map(n => `<option value="${n}" ${n == draft.alertThreshold ? 'selected' : ''}>${n}</option>`).join('')}
                    </select>
                    <span>on a scale of ${draft.scaleRange} for</span>
                    <input type="number" id="adjust-alert-days" value="${draft.alertDays}" min="1" max="30" 
                           class="w-10 px-1 py-1.5 text-center rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                    <span>days in a row.</span>
                </div>
            `;
        } else if (draft.checkMethod === 'quantity') {
            const isDidntDo = draft.alertOperator === 'didnt_do';
            alertControlsHTML = `
                <div class="flex flex-wrap items-center gap-1.5 text-xs sm:text-sm text-[#284132] font-medium pt-1">
                    <select id="adjust-alert-operator" onchange="if(window.TempoSelfCheckWorkspace.onAlertOperatorChanged) window.TempoSelfCheckWorkspace.onAlertOperatorChanged(this.value)" class="px-2.5 py-1.5 rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                        <option value="more_than" ${draft.alertOperator === 'more_than' ? 'selected' : ''}>More than</option>
                        <option value="less_than" ${draft.alertOperator === 'less_than' ? 'selected' : ''}>Less than</option>
                        <option value="didnt_do" ${draft.alertOperator === 'didnt_do' ? 'selected' : ''}>Didn't do</option>
                    </select>
                    ${!isDidntDo ? `
                        <input type="number" id="adjust-alert-threshold" value="${draft.alertThreshold}" min="0" step="any" 
                               class="w-14 px-1.5 py-1.5 text-center rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                        <span id="adjust-alert-unit-label">${escapeHTML(draft.quantityUnit)}</span>
                    ` : ''}
                    <span>for</span>
                    <input type="number" id="adjust-alert-days" value="${draft.alertDays}" min="1" max="30" 
                           class="w-10 px-1 py-1.5 text-center rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                    <span>days in a row.</span>
                </div>
            `;
        }

        container.innerHTML = `
            <!-- Close Button -->
            <button type="button" 
                    onclick="window.TempoSelfCheckWorkspace.closeAdjustModal()" 
                    class="absolute top-4 right-4 text-[#9E9893] hover:text-[#37352F] text-base sm:text-lg transition cursor-pointer p-1 rounded-full hover:bg-stone-200/50" 
                    title="Close">
                ✕
            </button>

            <!-- 1. Heading & Editable Tracking Item Name -->
            <div class="space-y-1">
                <span class="text-xs sm:text-sm font-bold text-[#3B5441] tracking-tight block">Your Tracking Item</span>
                <div class="relative pt-0.5">
                    <input type="text" 
                           id="adjust-tracker-name-input" 
                           value="${escapeHTML(draft.trackerName || '')}" 
                           placeholder="Enter tracking name" 
                           maxlength="50"
                           class="w-full font-heading text-2xl sm:text-3xl font-extrabold text-[#284132] tracking-tight bg-white/70 hover:bg-white focus:bg-white rounded-2xl px-3.5 py-1.5 border ${draft.nameError ? 'border-red-400 focus:border-red-500 ring-1 ring-red-400' : 'border-stone-300/80 focus:border-[#4A6B53]'} focus:outline-none placeholder:text-stone-400 placeholder:font-normal placeholder:text-lg sm:placeholder:text-xl shadow-2xs transition"
                           oninput="if(window.TempoSelfCheckWorkspace.setDraftTrackerName) window.TempoSelfCheckWorkspace.setDraftTrackerName(this.value)" />
                    ${draft.nameError ? `<p id="adjust-name-error-msg" class="text-[11px] text-red-600 font-semibold mt-1 pl-1">${escapeHTML(draft.nameError)}</p>` : ''}
                </div>
            </div>

            <!-- 2. Type Section -->
            <div class="space-y-1.5 pt-2">
                <span class="text-xs sm:text-sm font-bold text-[#5B5550] block">Type:</span>
                <div class="flex flex-wrap items-center gap-2">
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.setAdjustType('stress_sign', 'Sign of stress', '#C34D2E')"
                            class="px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer shadow-2xs"
                            style="${draft.typeId === 'stress_sign' ? 'background-color: #C34D2E; color: #ffffff; box-shadow: 0 0 0 2px rgba(195,77,46,0.35);' : 'background-color: rgba(195,77,46,0.78); color: #ffffff;'}">
                        Sign of stress
                    </button>
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.setAdjustType('supportive', 'Supportive', '#859B8B')"
                            class="px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer shadow-2xs"
                            style="${draft.typeId === 'supportive' ? 'background-color: #859B8B; color: #ffffff; box-shadow: 0 0 0 2px rgba(133,155,139,0.35);' : 'background-color: rgba(133,155,139,0.78); color: #ffffff;'}">
                        Supportive
                    </button>
                    ${customTypesHTML}
                </div>
                <button type="button" 
                        onclick="window.TempoSelfCheckWorkspace.toggleCreateNewTypeForm()"
                        class="text-xs font-bold text-[#D48366] hover:underline transition cursor-pointer pt-0.5 block">
                    Create new type
                </button>
                ${newTypeFormHTML}
            </div>

            <!-- 3. Tracking Method Section -->
            <div class="space-y-1.5 pt-2">
                <span class="text-xs sm:text-sm font-bold text-[#5B5550] block">Tracking method:</span>
                <div class="grid grid-cols-4 gap-2 w-full">
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.setAdjustMethod('percentage')"
                            class="py-1.5 px-1 rounded-xl text-center text-xs sm:text-sm font-bold transition cursor-pointer shadow-2xs ${draft.checkMethod === 'percentage' ? 'bg-[#E2EAE4] border border-[#6B8B73] text-[#284132]' : 'bg-white border border-stone-300/80 text-[#3B5441] hover:bg-stone-50'}">
                        %
                    </button>
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.setAdjustMethod('options')"
                            class="py-1.5 px-1 rounded-xl text-center text-xs sm:text-sm font-bold transition cursor-pointer shadow-2xs ${draft.checkMethod === 'options' ? 'bg-[#E2EAE4] border border-[#6B8B73] text-[#284132]' : 'bg-white border border-stone-300/80 text-[#3B5441] hover:bg-stone-50'}">
                        Options
                    </button>
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.setAdjustMethod('scale')"
                            class="py-1.5 px-1 rounded-xl text-center text-xs sm:text-sm font-bold transition cursor-pointer shadow-2xs ${draft.checkMethod === 'scale' ? 'bg-[#E2EAE4] border border-[#6B8B73] text-[#284132]' : 'bg-white border border-stone-300/80 text-[#3B5441] hover:bg-stone-50'}">
                        Scale
                    </button>
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.setAdjustMethod('quantity')"
                            class="py-1.5 px-1 rounded-xl text-center text-xs sm:text-sm font-bold transition cursor-pointer shadow-2xs ${draft.checkMethod === 'quantity' ? 'bg-[#E2EAE4] border border-[#6B8B73] text-[#284132]' : 'bg-white border border-stone-300/80 text-[#3B5441] hover:bg-stone-50'}">
                        Quantity
                    </button>
                </div>
                ${methodConfigHTML}
            </div>

            <!-- 4. Alert System Section -->
            <div class="space-y-1.5 pt-2.5">
                <div class="flex items-center justify-between">
                    <span class="text-xs sm:text-sm font-bold text-[#5B5550]">Alert system</span>
                    <div class="flex items-center space-x-2">
                        <span class="text-xs font-semibold ${draft.alertEnabled ? 'text-[#37352F]' : 'text-stone-400'}">On</span>
                        <button type="button" 
                                onclick="window.TempoSelfCheckWorkspace.toggleAdjustAlertSystem()"
                                class="w-11 h-6 flex items-center rounded-full p-1 cursor-pointer transition ${draft.alertEnabled ? 'bg-[#859B8B] justify-end' : 'bg-stone-300 justify-start'}"
                                title="Toggle alert system">
                            <div class="bg-white w-4 h-4 rounded-full shadow-md"></div>
                        </button>
                        <span class="text-xs font-semibold ${!draft.alertEnabled ? 'text-[#37352F]' : 'text-stone-400'}">Off</span>
                    </div>
                </div>
                <p class="text-xs text-[#6F6B68]">Notice me if my checks are</p>
                <div id="adjust-alert-controls-container" class="${draft.alertEnabled ? '' : 'opacity-40 pointer-events-none'} transition">
                    ${alertTypeSelectorHTML}
                    ${alertControlsHTML}
                </div>
            </div>

            <!-- Bottom Actions -->
            <div class="flex items-center justify-end space-x-3 pt-4 border-t border-stone-200/60 mt-2">
                <button type="button" 
                        onclick="window.TempoSelfCheckWorkspace.closeAdjustModal()" 
                        class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-600 hover:text-stone-900 transition cursor-pointer">
                    Cancel
                </button>
                <button type="button" 
                        id="adjust-save-submit-btn"
                        onclick="window.TempoSelfCheckWorkspace.saveAdjustTracker()" 
                        class="px-5 py-2 rounded-xl text-xs font-bold bg-[#859B8B] hover:bg-[#728878] text-white transition cursor-pointer shadow-xs">
                    ${draft.mode === 'create' ? 'Add tracking' : 'Save changes'}
                </button>
            </div>
        `;
    }


    function promptClearAll() {
        const modal = document.getElementById('modal-selfcheck-clear-confirm');
        if (modal) modal.classList.remove('hidden');
    }

    function closeClearConfirm() {
        const modal = document.getElementById('modal-selfcheck-clear-confirm');
        if (modal) modal.classList.add('hidden');
    }

    function executeClearAll() {
        closeClearConfirm();
        if (window.TempoRecoverySelfCheck) {
            const active = window.TempoRecoverySelfCheck.getActiveTrackers ? window.TempoRecoverySelfCheck.getActiveTrackers() : [];
            active.forEach(t => {
                if (typeof window.TempoRecoverySelfCheck.archiveTracker === 'function') {
                    window.TempoRecoverySelfCheck.archiveTracker(t.id);
                }
            });
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("All active tracking items have been cleared.");
            }
            render();
        }
    }

    // Full Check Modal State & Month Selection Controller
    let fullCheckTrackerId = null;
    let fullCheckYear = new Date().getFullYear();
    let fullCheckMonth = new Date().getMonth(); // 0-indexed (0=Jan..11=Dec)

    function prevMonthFullCheck() {
        if (fullCheckMonth === 0) {
            fullCheckMonth = 11;
            fullCheckYear--;
        } else {
            fullCheckMonth--;
        }
        renderFullCheckModal(fullCheckTrackerId, fullCheckYear, fullCheckMonth);
    }

    function nextMonthFullCheck() {
        const now = new Date();
        if (fullCheckYear > now.getFullYear() || (fullCheckYear === now.getFullYear() && fullCheckMonth >= now.getMonth())) {
            return; // Disallow navigating into future months
        }
        if (fullCheckMonth === 11) {
            fullCheckMonth = 0;
            fullCheckYear++;
        } else {
            fullCheckMonth++;
        }
        renderFullCheckModal(fullCheckTrackerId, fullCheckYear, fullCheckMonth);
    }

    function jumpToCurrentMonthFullCheck() {
        const now = new Date();
        fullCheckYear = now.getFullYear();
        fullCheckMonth = now.getMonth();
        renderFullCheckModal(fullCheckTrackerId, fullCheckYear, fullCheckMonth);
    }

    function onFullCheckMonthChange(val) {
        const m = parseInt(val, 10);
        if (!isNaN(m) && m >= 0 && m <= 11) {
            const now = new Date();
            if (fullCheckYear === now.getFullYear() && m > now.getMonth()) {
                fullCheckMonth = now.getMonth();
            } else {
                fullCheckMonth = m;
            }
            renderFullCheckModal(fullCheckTrackerId, fullCheckYear, fullCheckMonth);
        }
    }

    function onFullCheckYearChange(val) {
        const y = parseInt(val, 10);
        if (!isNaN(y)) {
            const now = new Date();
            if (y > now.getFullYear()) {
                fullCheckYear = now.getFullYear();
            } else {
                fullCheckYear = y;
            }
            if (fullCheckYear === now.getFullYear() && fullCheckMonth > now.getMonth()) {
                fullCheckMonth = now.getMonth();
            }
            renderFullCheckModal(fullCheckTrackerId, fullCheckYear, fullCheckMonth);
        }
    }

    function renderFullCheckModal(trackerId, optionalYear, optionalMonth) {
        const container = document.getElementById('selfcheck-fullcheck-modal-card');
        if (!container) return;

        let tracker = null;
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerById === 'function') {
            tracker = window.TempoRecoverySelfCheck.getTrackerById(trackerId);
        }
        if (!tracker && window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function') {
            const active = window.TempoRecoverySelfCheck.getActiveTrackers();
            tracker = active.find(t => t.id === trackerId);
        }
        if (!tracker) {
            closeFullCheckPlaceholder();
            return;
        }

        fullCheckTrackerId = tracker.id;
        const now = new Date();
        const year = (typeof optionalYear === 'number') ? optionalYear : fullCheckYear;
        const month = (typeof optionalMonth === 'number') ? optionalMonth : fullCheckMonth;
        fullCheckYear = year;
        fullCheckMonth = month;
        const isCurrentMonth = (year === now.getFullYear() && month === now.getMonth());

        const dotColor = tracker.type_color || (tracker.category === 'stress_sign' ? '#D48366' : (tracker.category === 'supportive' ? '#166545' : '#1E40AF'));

        const monthNames = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];
        const monthName = monthNames[month];

        // Available years (2024 up to current year)
        const availableYears = [];
        const startYear = 2024;
        const currentYear = now.getFullYear();
        for (let y = startYear; y <= currentYear; y++) {
            availableYears.push(y);
        }

        // 7-column calendar starting Monday (Mon, Tue, Wed, Thus, Fri, Sat, Sun)
        const firstDay = new Date(year, month, 1);
        let startCol = firstDay.getDay() - 1; // 0=Mon, ..., 6=Sun
        if (startCol === -1) startCol = 6;

        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const daysInPrevMonth = new Date(year, month, 0).getDate();

        const cells = [];
        // Leading days from previous month
        for (let i = startCol - 1; i >= 0; i--) {
            const dayNum = daysInPrevMonth - i;
            const prevMonthIdx = month === 0 ? 11 : month - 1;
            const prevYear = month === 0 ? year - 1 : year;
            const dateStr = `${prevYear}-${String(prevMonthIdx + 1).padStart(2, '0')}-${String(dayNum).padStart(2, '0')}`;
            cells.push({
                dayNum,
                dateStr,
                isCurrentMonth: false,
                obs: null
            });
        }

        // Current month days
        for (let d = 1; d <= daysInMonth; d++) {
            const dStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            const obs = getObservationForDate(tracker.id, dStr);
            cells.push({
                dayNum: d,
                dateStr: dStr,
                isCurrentMonth: true,
                obs
            });
        }

        // Trailing days from next month to complete rows
        const totalCells = Math.ceil(cells.length / 7) * 7;
        const remaining = totalCells - cells.length;
        for (let d = 1; d <= remaining; d++) {
            const nextMonthIdx = month === 11 ? 0 : month + 1;
            const nextYear = month === 11 ? year + 1 : year;
            const dateStr = `${nextYear}-${String(nextMonthIdx + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            cells.push({
                dayNum: d,
                dateStr,
                isCurrentMonth: false,
                obs: null
            });
        }

        const dayCellsHTML = cells.map(cell => {
            let valText = '';
            if (cell.obs && cell.obs.status === 'answered' && cell.obs.value !== null && cell.obs.value !== undefined) {
                const val = cell.obs.value;
                let effMethod = cell.obs.check_method;
                let effUnit = cell.obs.quantity_unit;
                if (!effMethod) {
                    const cfg = (window.TempoRecoverySelfCheck && window.TempoRecoverySelfCheck.getTrackerConfigForDate)
                        ? window.TempoRecoverySelfCheck.getTrackerConfigForDate(tracker, cell.dateStr)
                        : null;
                    effMethod = cfg ? cfg.check_method : tracker.check_method;
                    if (effUnit === undefined && cfg) effUnit = cfg.quantity_unit;
                }
                if (effUnit === undefined) effUnit = tracker.quantity_unit || '';

                if (effMethod === 'percentage') {
                    valText = `${parseInt(val, 10)}%`;
                } else if (effMethod === 'yes_no' || effMethod === 'options') {
                    if (typeof val === 'string' && (val.toLowerCase() === 'good' || val.toLowerCase() === 'yes')) {
                        valText = 'Good';
                    } else if (typeof val === 'string' && (val.toLowerCase() === 'not_good' || val.toLowerCase() === 'no')) {
                        valText = 'No';
                    } else {
                        valText = String(val);
                    }
                } else if (effMethod === 'quantity') {
                    if (val === 'no') {
                        valText = 'No';
                    } else {
                        const numVal = parseFloat(val);
                        valText = !isNaN(numVal) ? (Number.isInteger(numVal) ? String(numVal) : String(Number(numVal.toFixed(2)))) : String(val);
                    }
                } else if (effMethod === 'scale') {
                    valText = String(val);
                } else {
                    valText = String(val);
                }
            }

            return `
                <div class="flex flex-col items-center justify-start text-center w-full min-h-[38px] sm:min-h-[40px]">
                    <div class="h-3.5 flex items-end justify-center text-center w-full shrink-0">
                        ${valText ? `<span class="font-bold text-[10px] sm:text-[11px] text-[#55785F] leading-none">${escapeHTML(valText)}</span>` : `<span class="invisible text-[10px] leading-none select-none" aria-hidden="true">&nbsp;</span>`}
                    </div>
                    <div class="h-5 flex items-center justify-center text-center w-full shrink-0">
                        <span class="text-xs sm:text-sm font-semibold select-none ${cell.isCurrentMonth ? 'text-[#37352F]' : 'text-[#BFB9B2]'}">${cell.dayNum}</span>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = `
            <!-- Close Button -->
            <button type="button" 
                    onclick="window.TempoSelfCheckWorkspace.closeFullCheckPlaceholder()" 
                    class="absolute top-4 right-4 text-[#9E9893] hover:text-[#37352F] text-base sm:text-lg transition cursor-pointer p-1 rounded-full hover:bg-stone-200/50" 
                    title="Close">
                ✕
            </button>

            <!-- 1. Small Heading -->
            <span class="text-xs sm:text-sm font-bold text-[#3B5441] tracking-tight block">Your full check</span>

            <!-- 2. Tracking Header: Dot + Name -->
            <div class="flex items-center space-x-2.5 sm:space-x-3 pt-1">
                <span class="w-5 h-5 sm:w-5.5 sm:h-5.5 rounded-full inline-block shrink-0 shadow-2xs" style="background-color: ${dotColor};"></span>
                <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#284132] tracking-tight truncate">${escapeHTML(tracker.name)}</h2>
            </div>

            <!-- 3. Current Month & Year Selector -->
            <div class="flex items-center justify-between pt-1.5 sm:pt-2 flex-wrap gap-2">
                <div class="flex items-center space-x-1.5">
                    <!-- Prev Month Arrow Button -->
                    <button type="button" 
                            id="fullcheck-prev-month-btn"
                            onclick="window.TempoSelfCheckWorkspace.prevMonthFullCheck()"
                            class="w-6 h-6 rounded-lg bg-stone-100 hover:bg-stone-200 text-[#5B5550] flex items-center justify-center transition cursor-pointer text-xs font-bold shadow-2xs" 
                            title="Previous month">
                        ‹
                    </button>

                    <!-- Month and Year Selectors -->
                    <div class="flex items-center space-x-1 bg-stone-50/80 px-2 py-0.5 rounded-lg border border-stone-200/60">
                        <select id="fullcheck-year-select" 
                                onchange="window.TempoSelfCheckWorkspace.onFullCheckYearChange(this.value)"
                                class="bg-transparent font-bold text-xs sm:text-sm text-[#C87D55] cursor-pointer focus:outline-none hover:opacity-80 py-0.5">
                            ${availableYears.map(y => `
                                <option value="${y}" ${y === year ? 'selected' : ''}>${y}</option>
                            `).join('')}
                        </select>
                        <span class="text-xs font-bold text-[#C87D55]">,</span>
                        <select id="fullcheck-month-select" 
                                onchange="window.TempoSelfCheckWorkspace.onFullCheckMonthChange(this.value)"
                                class="bg-transparent font-bold text-xs sm:text-sm text-[#C87D55] cursor-pointer focus:outline-none hover:opacity-80 py-0.5">
                            ${monthNames.map((m, idx) => {
                                const isFuture = (year === now.getFullYear() && idx > now.getMonth());
                                if (isFuture) return '';
                                return `<option value="${idx}" ${idx === month ? 'selected' : ''}>${m}</option>`;
                            }).join('')}
                        </select>
                    </div>

                    <!-- Next Month Arrow Button (Disabled on current month) -->
                    <button type="button" 
                            id="fullcheck-next-month-btn"
                            onclick="window.TempoSelfCheckWorkspace.nextMonthFullCheck()"
                            ${isCurrentMonth ? 'disabled title="Cannot navigate into future months"' : 'title="Next month"'}
                            class="w-6 h-6 rounded-lg flex items-center justify-center transition text-xs font-bold shadow-2xs ${isCurrentMonth ? 'bg-stone-100/50 text-stone-300 cursor-not-allowed' : 'bg-stone-100 hover:bg-stone-200 text-[#5B5550] cursor-pointer'}">
                        ›
                    </button>
                </div>

                <!-- Return to Current Month Pill (Only when not on current month) -->
                ${!isCurrentMonth ? `
                    <button type="button" 
                            id="fullcheck-return-current-btn"
                            onclick="window.TempoSelfCheckWorkspace.jumpToCurrentMonthFullCheck()"
                            class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA] hover:bg-[#DDF0E5] transition cursor-pointer shadow-2xs">
                        Current month
                    </button>
                ` : ''}
            </div>

            <!-- 4. Monthly Calendar with Seven Columns -->
            <div class="pt-2 sm:pt-2.5">
                <!-- Weekday Columns -->
                <div class="grid grid-cols-7 gap-1 text-center pt-2 pb-1.5 w-full">
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">Mon</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">Tue</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">Wed</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">Thus</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">Fri</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">Sat</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">Sun</span>
                </div>

                <!-- Calendar Days Grid -->
                <div class="grid grid-cols-7 gap-x-1 gap-y-1 sm:gap-y-1.5 text-center w-full">
                    ${dayCellsHTML}
                </div>
            </div>

            <!-- 5. Centered Monthly Overview Button -->
            <div class="flex justify-center pt-5 sm:pt-6">
                <button type="button" 
                        onclick="window.TempoSelfCheckWorkspace.onMonthlyOverviewClick('${tracker.id}')"
                        class="px-8 sm:px-10 py-2 sm:py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-[#859B8B] hover:bg-[#748A7A] text-white transition shadow-2xs cursor-pointer tracking-normal">
                    Monthly Overview
                </button>
            </div>
        `;
    }

    function openFullCheckPlaceholder(trackerId, year, month) {
        selectedTrackerForHistory = trackerId;
        fullCheckTrackerId = trackerId;
        const now = new Date();
        fullCheckYear = (typeof year === 'number') ? year : now.getFullYear();
        fullCheckMonth = (typeof month === 'number') ? month : now.getMonth();
        renderFullCheckModal(trackerId, fullCheckYear, fullCheckMonth);
        const modal = document.getElementById('modal-selfcheck-fullcheck');
        if (modal) modal.classList.remove('hidden');
    }

    function closeFullCheckPlaceholder() {
        const modal = document.getElementById('modal-selfcheck-fullcheck');
        if (modal) modal.classList.add('hidden');
        selectedTrackerForHistory = null;
    }

    // =========================================================================
    // MONTHLY OVERVIEW ANALYTICS CONTROLLER & RENDERERS
    // =========================================================================

    let monthlyOverviewTrackerId = null;
    let monthlyOverviewYear = new Date().getFullYear();
    let monthlyOverviewMonth = new Date().getMonth(); // 0-indexed (0=Jan..11=Dec)

    function openMonthlyOverview(trackerId, year, month) {
        if (!trackerId && selectedTrackerForHistory) {
            trackerId = selectedTrackerForHistory;
        }
        monthlyOverviewTrackerId = trackerId;
        const now = new Date();
        monthlyOverviewYear = (typeof year === 'number') ? year : now.getFullYear();
        monthlyOverviewMonth = (typeof month === 'number') ? month : now.getMonth();

        // Close full check calendar modal
        const fullCheckModal = document.getElementById('modal-selfcheck-fullcheck');
        if (fullCheckModal) fullCheckModal.classList.add('hidden');

        // Open monthly overview modal
        const overviewModal = document.getElementById('modal-selfcheck-monthly-overview');
        if (overviewModal) overviewModal.classList.remove('hidden');

        renderMonthlyOverview();
    }

    function closeMonthlyOverview(closeAll = false) {
        const overviewModal = document.getElementById('modal-selfcheck-monthly-overview');
        if (overviewModal) overviewModal.classList.add('hidden');

        if (!closeAll && monthlyOverviewTrackerId) {
            // Return to Full Check calendar preserving the month viewed in Monthly Overview
            openFullCheckPlaceholder(monthlyOverviewTrackerId, monthlyOverviewYear, monthlyOverviewMonth);
        } else {
            selectedTrackerForHistory = null;
            monthlyOverviewTrackerId = null;
        }
    }

    function prevMonthOverview() {
        if (monthlyOverviewMonth === 0) {
            monthlyOverviewMonth = 11;
            monthlyOverviewYear--;
        } else {
            monthlyOverviewMonth--;
        }
        renderMonthlyOverview();
    }

    function nextMonthOverview() {
        const now = new Date();
        if (monthlyOverviewYear > now.getFullYear() || (monthlyOverviewYear === now.getFullYear() && monthlyOverviewMonth >= now.getMonth())) {
            return;
        }
        if (monthlyOverviewMonth === 11) {
            monthlyOverviewMonth = 0;
            monthlyOverviewYear++;
        } else {
            monthlyOverviewMonth++;
        }
        renderMonthlyOverview();
    }

    function jumpToCurrentMonthOverview() {
        const now = new Date();
        monthlyOverviewYear = now.getFullYear();
        monthlyOverviewMonth = now.getMonth();
        renderMonthlyOverview();
    }

    function onMonthlyOverviewClick(trackerId) {
        openMonthlyOverview(trackerId, fullCheckYear, fullCheckMonth);
    }

    function renderMonthlyOverview() {
        const container = document.getElementById('selfcheck-monthly-overview-card');
        if (!container || !monthlyOverviewTrackerId) return;

        let tracker = null;
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerById === 'function') {
            tracker = window.TempoRecoverySelfCheck.getTrackerById(monthlyOverviewTrackerId);
        }
        if (!tracker && window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function') {
            const active = window.TempoRecoverySelfCheck.getActiveTrackers();
            tracker = active.find(t => t.id === monthlyOverviewTrackerId);
        }
        if (!tracker) return;

        const dotColor = tracker.type_color || (tracker.category === 'stress_sign' ? '#D48366' : (tracker.category === 'supportive' ? '#166545' : '#1E40AF'));

        const year = monthlyOverviewYear;
        const month = monthlyOverviewMonth;
        const now = new Date();
        const isCurrentMonthAndYear = (year === now.getFullYear() && month === now.getMonth());

        const monthNames = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];
        const monthName = monthNames[month];
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        // Query daily observations for this month
        const records = [];
        for (let d = 1; d <= daysInMonth; d++) {
            const dStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            const obs = getObservationForDate(tracker.id, dStr);
            let val = null;
            let hasValue = false;
            let effMethod = (obs && obs.check_method) || null;
            let effUnit = (obs && obs.quantity_unit !== undefined) ? obs.quantity_unit : null;
            if (!effMethod) {
                const cfg = (window.TempoRecoverySelfCheck && window.TempoRecoverySelfCheck.getTrackerConfigForDate)
                    ? window.TempoRecoverySelfCheck.getTrackerConfigForDate(tracker, dStr)
                    : null;
                effMethod = cfg ? cfg.check_method : tracker.check_method;
                if (effUnit === null && cfg) effUnit = cfg.quantity_unit;
            }
            if (effUnit === null) effUnit = tracker.quantity_unit || '';

            if (obs && obs.status === 'answered' && obs.value !== null && obs.value !== undefined) {
                val = obs.value;
                hasValue = true;
            }
            records.push({ day: d, dateStr: dStr, obs, val, hasValue, effectiveMethod: effMethod, effectiveUnit: effUnit });
        }

        const formatShortDate = (dStr) => {
            const [y, m, d] = dStr.split('-').map(Number);
            const dt = new Date(y, m - 1, d);
            return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        };

        const answeredRecords = records.filter(r => r.hasValue);
        const distinctMethods = Array.from(new Set(answeredRecords.map(r => r.effectiveMethod)));

        const method = tracker.check_method;
        const nameLower = (tracker.name || '').toLowerCase();
        let methodBadge = 'Percentage';
        if (method === 'options' || method === 'yes_no') methodBadge = 'Options';
        else if (method === 'scale') methodBadge = `Scale 1–${tracker.scale_max || 5}`;
        else if (method === 'quantity' || nameLower.includes('walk')) methodBadge = `Quantity (${tracker.quantity_unit || 'min'})`;

        // Generate Method Specific Analytics & Chart
        let analyticsHTML = '';

        if (distinctMethods.length <= 1) {
            const activeMethod = distinctMethods.length === 1 ? distinctMethods[0] : method;
            if (activeMethod === 'percentage') {
                analyticsHTML = renderPercentageMonthlyAnalytics(records, tracker, dotColor, monthName, year, daysInMonth, formatShortDate);
            } else if (activeMethod === 'options' || activeMethod === 'yes_no') {
                analyticsHTML = renderOptionsMonthlyAnalytics(records, tracker, dotColor, monthName, year, daysInMonth);
            } else if (activeMethod === 'scale') {
                analyticsHTML = renderScaleMonthlyAnalytics(records, tracker, dotColor, monthName, year, daysInMonth, formatShortDate);
            } else if (activeMethod === 'quantity') {
                analyticsHTML = renderQuantityMonthlyAnalytics(records, tracker, dotColor, monthName, year, daysInMonth, formatShortDate);
            } else {
                analyticsHTML = renderPercentageMonthlyAnalytics(records, tracker, dotColor, monthName, year, daysInMonth, formatShortDate);
            }
        } else {
            // Multi-method segmented rendering: never aggregate or compare incompatible values!
            const methodNames = {
                percentage: 'Percentage (%)',
                options: 'Options',
                yes_no: 'Options',
                scale: `Scale (1–${tracker.scale_max || 5})`,
                quantity: `Quantity (${tracker.quantity_unit || 'units'})`
            };

            let sectionsHTML = `
                <div class="mb-4 p-3.5 rounded-2xl bg-[#FBF7F2] border border-[#EBE2D8] flex items-start space-x-2.5 text-xs text-[#5B5550]">
                    <span class="text-base shrink-0">ℹ️</span>
                    <div>
                        <strong class="text-[#202124]">Multiple tracking methods used this month</strong>
                        <p class="pt-0.5 leading-relaxed">
                            This tracker switched methods during ${monthName} ${year}. To prevent incompatible comparisons or corrupted averages, records under each method are analyzed independently below.
                        </p>
                    </div>
                </div>
            `;

            distinctMethods.forEach(m => {
                const subset = records.map(r => r.effectiveMethod === m ? r : { ...r, hasValue: false, val: null });
                const subsetAnswered = records.filter(r => r.hasValue && r.effectiveMethod === m);
                const firstDay = subsetAnswered[0] ? subsetAnswered[0].day : '';
                const lastDay = subsetAnswered[subsetAnswered.length - 1] ? subsetAnswered[subsetAnswered.length - 1].day : '';
                const dateRangeText = (firstDay && lastDay) ? `(Day ${firstDay} – Day ${lastDay})` : '';

                let subAnalytics = '';
                if (m === 'percentage') {
                    subAnalytics = renderPercentageMonthlyAnalytics(subset, tracker, dotColor, monthName, year, daysInMonth, formatShortDate);
                } else if (m === 'options' || m === 'yes_no') {
                    subAnalytics = renderOptionsMonthlyAnalytics(subset, tracker, dotColor, monthName, year, daysInMonth);
                } else if (m === 'scale') {
                    subAnalytics = renderScaleMonthlyAnalytics(subset, tracker, dotColor, monthName, year, daysInMonth, formatShortDate);
                } else if (m === 'quantity') {
                    subAnalytics = renderQuantityMonthlyAnalytics(subset, tracker, dotColor, monthName, year, daysInMonth, formatShortDate);
                }

                sectionsHTML += `
                    <div class="mt-4 pt-3 border-t border-stone-200/80 space-y-2">
                        <div class="flex items-center space-x-2">
                            <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-[#E2EAE4] text-[#166545] border border-[#CDE9DA]">
                                ${methodNames[m] || m}
                            </span>
                            <span class="text-xs font-bold text-stone-600">${dateRangeText}</span>
                            <span class="text-xs text-stone-400">· ${subsetAnswered.length} record${subsetAnswered.length === 1 ? '' : 's'}</span>
                        </div>
                        ${subAnalytics}
                    </div>
                `;
            });

            analyticsHTML = sectionsHTML;
        }

        container.innerHTML = `
            <!-- Top Utility: Back to Calendar & Close -->
            <div class="flex items-center justify-between pb-3 border-b border-stone-200/70">
                <button type="button" 
                        onclick="window.TempoSelfCheckWorkspace.closeMonthlyOverview()" 
                        class="inline-flex items-center space-x-1.5 text-xs sm:text-sm font-bold text-[#4A6B5D] hover:text-[#166545] transition cursor-pointer"
                        title="Back to Calendar">
                    <span class="text-base leading-none">←</span>
                    <span>Back to calendar</span>
                </button>
                <button type="button" 
                        onclick="window.TempoSelfCheckWorkspace.closeMonthlyOverview(true)" 
                        class="text-[#9E9893] hover:text-[#37352F] text-base sm:text-lg transition cursor-pointer p-1 rounded-full hover:bg-stone-200/50" 
                        title="Close">
                    ✕
                </button>
            </div>

            <!-- Tracker Header & Month Navigator -->
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-3">
                <div>
                    <span class="text-xs font-bold text-[#3B5441] tracking-tight block">Monthly Overview</span>
                    <div class="flex items-center space-x-2.5 pt-0.5">
                        <span class="w-3.5 h-3.5 rounded-full inline-block shrink-0 shadow-2xs" style="background-color: ${dotColor};"></span>
                        <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#284132] tracking-tight">${escapeHTML(tracker.name)}</h2>
                        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#E2EAE4] text-[#284132] border border-[#6B8B73]/40">${methodBadge}</span>
                    </div>
                </div>

                <!-- Month Navigation Controls -->
                <div class="flex items-center space-x-1.5 sm:space-x-2">
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.prevMonthOverview()"
                            class="w-8 h-8 rounded-xl bg-white border border-stone-300 hover:bg-stone-50 text-stone-700 font-bold flex items-center justify-center transition cursor-pointer shadow-2xs"
                            title="Previous month">
                        ‹
                    </button>
                    <span class="text-xs sm:text-sm font-extrabold text-[#C87D55] px-2 min-w-[110px] sm:min-w-[130px] text-center select-none">${monthName} ${year}</span>
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.nextMonthOverview()"
                            class="w-8 h-8 rounded-xl bg-white border border-stone-300 hover:bg-stone-50 text-stone-700 font-bold flex items-center justify-center transition cursor-pointer shadow-2xs ${isCurrentMonthAndYear ? 'opacity-35 pointer-events-none' : ''}"
                            title="Next month">
                        ›
                    </button>
                    ${!isCurrentMonthAndYear ? `
                        <button type="button" 
                                onclick="window.TempoSelfCheckWorkspace.jumpToCurrentMonthOverview()"
                                class="px-2.5 py-1 rounded-xl bg-[#859B8B]/15 hover:bg-[#859B8B]/25 text-[#284132] text-[11px] font-bold transition cursor-pointer ml-1">
                            Current
                        </button>
                    ` : ''}
                </div>
            </div>

            <!-- Content Area: Cards + Dynamic Chart -->
            <div class="pt-2">
                ${analyticsHTML}
            </div>
        `;
    }

    function renderEmptyMonthlyState(tracker, monthName, year) {
        return `
            <div class="mt-4 p-8 sm:p-10 text-center rounded-2xl bg-white border border-dashed border-stone-300 space-y-3 shadow-2xs">
                <div class="w-12 h-12 mx-auto rounded-full bg-[#859B8B]/15 flex items-center justify-center text-[#4A6B5D] text-xl">
                    📅
                </div>
                <div class="space-y-1">
                    <h4 class="text-sm sm:text-base font-bold text-[#284132]">No check-in records for ${monthName} ${year}</h4>
                    <p class="text-xs text-[#6F6B68] max-w-sm mx-auto leading-relaxed">
                        There are no recorded check-ins for <strong>${escapeHTML(tracker.name)}</strong> during this month. Use the arrow buttons above to view other months.
                    </p>
                </div>
            </div>
        `;
    }

    function buildSvgLineChart(records, yMin, yMax, yTicks, trackerColor, unitSuffix = '', daysInMonth = 31) {
        const width = 560;
        const height = 180;
        const pad = { top: 15, right: 25, bottom: 25, left: 45 };
        const plotW = width - pad.left - pad.right;
        const plotH = height - pad.top - pad.bottom;

        // Group points into contiguous consecutive segments (gaps strictly preserved!)
        const segments = [];
        let curr = [];

        for (let i = 0; i < records.length; i++) {
            const r = records[i];
            const num = (r.hasValue && r.val !== 'no') ? parseFloat(r.val) : null;
            if (num !== null && !isNaN(num)) {
                const x = pad.left + ((r.day - 1) / Math.max(1, daysInMonth - 1)) * plotW;
                const y = pad.top + plotH - ((num - yMin) / Math.max(0.001, yMax - yMin)) * plotH;
                const pt = { day: r.day, dateStr: r.dateStr, num, x, y };

                if (curr.length > 0) {
                    const prev = curr[curr.length - 1];
                    if (r.day === prev.day + 1) {
                        curr.push(pt);
                    } else {
                        segments.push(curr);
                        curr = [pt];
                    }
                } else {
                    curr = [pt];
                }
            }
        }
        if (curr.length > 0) segments.push(curr);

        // Grid lines & Y axis ticks
        const yGridLines = yTicks.map(t => {
            const y = pad.top + plotH - ((t.val - yMin) / Math.max(0.001, yMax - yMin)) * plotH;
            return `
                <line x1="${pad.left}" y1="${y}" x2="${width - pad.right}" y2="${y}" stroke="#EAE4DF" stroke-width="1" stroke-dasharray="3,3" />
                <text x="${pad.left - 8}" y="${y + 3}" font-size="10" font-weight="600" fill="#787570" text-anchor="end">${escapeHTML(t.label)}</text>
            `;
        }).join('');

        // X axis ticks (Day 1, 5, 10, 15, 20, 25, daysInMonth)
        const xDays = [1, 5, 10, 15, 20, 25, daysInMonth].filter((v, idx, arr) => arr.indexOf(v) === idx && v <= daysInMonth);
        const xTicks = xDays.map(d => {
            const x = pad.left + ((d - 1) / Math.max(1, daysInMonth - 1)) * plotW;
            return `
                <line x1="${x}" y1="${height - pad.bottom}" x2="${x}" y2="${height - pad.bottom + 4}" stroke="#BFB9B2" stroke-width="1" />
                <text x="${x}" y="${height - pad.bottom + 16}" font-size="10" font-weight="600" fill="#787570" text-anchor="middle">${d}</text>
            `;
        }).join('');

        // Build path elements for each contiguous segment
        let pathsHTML = '';
        segments.forEach((seg, sIdx) => {
            if (seg.length > 1) {
                const dLine = seg.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
                const yBase = pad.top + plotH;
                const dArea = `${dLine} L ${seg[seg.length - 1].x.toFixed(1)} ${yBase} L ${seg[0].x.toFixed(1)} ${yBase} Z`;

                pathsHTML += `
                    <path d="${dArea}" fill="${trackerColor}" fill-opacity="0.12" />
                    <path d="${dLine}" fill="none" stroke="${trackerColor}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
                `;
            }
        });

        // Points
        let pointsHTML = '';
        segments.forEach(seg => {
            seg.forEach(p => {
                pointsHTML += `
                    <g class="cursor-pointer group">
                        <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4" fill="${trackerColor}" stroke="#ffffff" stroke-width="2" class="transition-transform group-hover:scale-125" />
                        <title>${p.dateStr}: ${p.num}${unitSuffix}</title>
                    </g>
                `;
            });
        });

        return `
            <div class="w-full overflow-x-auto">
                <svg viewBox="0 0 ${width} ${height}" class="w-full h-auto select-none" preserveAspectRatio="xMidYMid meet">
                    <!-- Axes & Grid -->
                    ${yGridLines}
                    <line x1="${pad.left}" y1="${height - pad.bottom}" x2="${width - pad.right}" y2="${height - pad.bottom}" stroke="#D1CAC3" stroke-width="1.2" />
                    ${xTicks}
                    <!-- Data Paths & Dots -->
                    ${pathsHTML}
                    ${pointsHTML}
                </svg>
            </div>
        `;
    }

    function renderPercentageMonthlyAnalytics(records, tracker, dotColor, monthName, year, daysInMonth, formatShortDate) {
        const valid = records.filter(r => r.hasValue && !isNaN(parseFloat(r.val)));
        if (valid.length === 0) return renderEmptyMonthlyState(tracker, monthName, year);

        const sum = valid.reduce((acc, r) => acc + parseFloat(r.val), 0);
        const avg = Math.round(sum / valid.length);
        const highest = valid.reduce((max, r) => parseFloat(r.val) > parseFloat(max.val) ? r : max, valid[0]);
        const lowest = valid.reduce((min, r) => parseFloat(r.val) < parseFloat(min.val) ? r : min, valid[0]);
        const count = valid.length;

        const yTicks = [
            { val: 0, label: '0%' },
            { val: 25, label: '25%' },
            { val: 50, label: '50%' },
            { val: 75, label: '75%' },
            { val: 100, label: '100%' }
        ];

        const chartSVG = buildSvgLineChart(records, 0, 100, yTicks, dotColor, '%', daysInMonth);

        return `
            <!-- Stats Cards Grid -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3 pt-3">
                <div class="bg-white/80 border border-stone-200/80 rounded-2xl p-3 shadow-2xs space-y-0.5">
                    <span class="text-[10px] sm:text-[11px] font-bold text-stone-500 uppercase tracking-wide block">Monthly Avg</span>
                    <span class="text-xl sm:text-2xl font-extrabold text-[#284132] block">${avg}%</span>
                    <span class="text-[10px] text-stone-400 font-medium block">from ${count} checks</span>
                </div>
                <div class="bg-white/80 border border-stone-200/80 rounded-2xl p-3 shadow-2xs space-y-0.5">
                    <span class="text-[10px] sm:text-[11px] font-bold text-stone-500 uppercase tracking-wide block">Highest</span>
                    <span class="text-xl sm:text-2xl font-extrabold text-[#284132] block">${parseFloat(highest.val)}%</span>
                    <span class="text-[10px] text-stone-400 font-medium block">${formatShortDate(highest.dateStr)}</span>
                </div>
                <div class="bg-white/80 border border-stone-200/80 rounded-2xl p-3 shadow-2xs space-y-0.5">
                    <span class="text-[10px] sm:text-[11px] font-bold text-stone-500 uppercase tracking-wide block">Lowest</span>
                    <span class="text-xl sm:text-2xl font-extrabold text-[#284132] block">${parseFloat(lowest.val)}%</span>
                    <span class="text-[10px] text-stone-400 font-medium block">${formatShortDate(lowest.dateStr)}</span>
                </div>
                <div class="bg-white/80 border border-stone-200/80 rounded-2xl p-3 shadow-2xs space-y-0.5">
                    <span class="text-[10px] sm:text-[11px] font-bold text-stone-500 uppercase tracking-wide block">Checked In</span>
                    <span class="text-xl sm:text-2xl font-extrabold text-[#284132] block">${count} <span class="text-xs text-stone-500 font-medium">/ ${daysInMonth}d</span></span>
                    <span class="text-[10px] text-stone-400 font-medium block">${Math.round((count / daysInMonth) * 100)}% active</span>
                </div>
            </div>

            <!-- Chart Container -->
            <div class="bg-white rounded-2xl border border-stone-200/80 p-4 shadow-2xs mt-3.5 space-y-2">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-bold text-[#284132]">Daily Tracking Trend (%)</span>
                    <span class="text-[10px] text-stone-400 font-medium">Gaps indicate unrecorded days</span>
                </div>
                ${chartSVG}
            </div>
        `;
    }

    function renderOptionsMonthlyAnalytics(records, tracker, dotColor, monthName, year, daysInMonth) {
        let optList = [];
        if (Array.isArray(tracker.options) && tracker.options.length > 0) {
            optList = [...tracker.options];
        } else if (tracker.check_method === 'yes_no') {
            optList = ['Good', 'Not good'];
        } else {
            optList = ['Yes', 'No'];
        }

        const counts = {};
        optList.forEach(o => counts[o] = 0);

        const valid = records.filter(r => r.hasValue);
        if (valid.length === 0) return renderEmptyMonthlyState(tracker, monthName, year);

        let total = 0;
        valid.forEach(r => {
            const v = String(r.val);
            const matched = optList.find(o => o.toLowerCase() === v.toLowerCase());
            if (matched) {
                counts[matched]++;
                total++;
            } else {
                counts[v] = (counts[v] || 0) + 1;
                total++;
                if (!optList.includes(v)) optList.push(v);
            }
        });

        let topOpt = null;
        let topCount = 0;
        optList.forEach(o => {
            if (counts[o] > topCount) {
                topCount = counts[o];
                topOpt = o;
            }
        });

        const palette = ['#166545', '#D48366', '#2563EB', '#7C3AED', '#D97706', '#0D9488'];

        // Stacked proportional distribution bar
        const stackedBarHTML = optList.map((o, idx) => {
            const cnt = counts[o] || 0;
            const pct = total > 0 ? (cnt / total) * 100 : 0;
            if (pct <= 0) return '';
            const c = palette[idx % palette.length];
            return `<div style="width: ${pct}%; background-color: ${c};" class="h-full transition-all" title="${escapeHTML(o)}: ${cnt} (${Math.round(pct)}%)"></div>`;
        }).join('');

        // Bars list
        const maxCnt = Math.max(1, ...optList.map(o => counts[o] || 0));
        const barsHTML = optList.map((o, idx) => {
            const cnt = counts[o] || 0;
            const pctOfTotal = total > 0 ? Math.round((cnt / total) * 100) : 0;
            const barWidth = Math.round((cnt / maxCnt) * 100);
            const c = palette[idx % palette.length];

            return `
                <div class="space-y-1">
                    <div class="flex items-center justify-between text-xs">
                        <span class="font-bold text-[#37352F] flex items-center space-x-1.5">
                            <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: ${c};"></span>
                            <span>${escapeHTML(o)}</span>
                        </span>
                        <span class="font-semibold text-stone-600">${cnt} times (${pctOfTotal}%)</span>
                    </div>
                    <div class="w-full h-3 rounded-full bg-stone-100 overflow-hidden">
                        <div class="h-full rounded-full transition-all" style="width: ${barWidth}%; background-color: ${c};"></div>
                    </div>
                </div>
            `;
        }).join('');

        return `
            <!-- Stats Cards Grid -->
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-2.5 sm:gap-3 pt-3">
                <div class="bg-white/80 border border-stone-200/80 rounded-2xl p-3 shadow-2xs space-y-0.5">
                    <span class="text-[10px] sm:text-[11px] font-bold text-stone-500 uppercase tracking-wide block">Total Check-ins</span>
                    <span class="text-xl sm:text-2xl font-extrabold text-[#284132] block">${total}</span>
                    <span class="text-[10px] text-stone-400 font-medium block">in ${monthName}</span>
                </div>
                <div class="bg-white/80 border border-stone-200/80 rounded-2xl p-3 shadow-2xs space-y-0.5">
                    <span class="text-[10px] sm:text-[11px] font-bold text-stone-500 uppercase tracking-wide block">Top Selection</span>
                    <span class="text-xl sm:text-2xl font-extrabold text-[#284132] block truncate">${topOpt || 'None'}</span>
                    <span class="text-[10px] text-stone-400 font-medium block">${topCount} times (${total > 0 ? Math.round((topCount / total) * 100) : 0}%)</span>
                </div>
                <div class="bg-white/80 border border-stone-200/80 rounded-2xl p-3 shadow-2xs space-y-0.5 col-span-2 sm:col-span-1">
                    <span class="text-[10px] sm:text-[11px] font-bold text-stone-500 uppercase tracking-wide block">Active Days</span>
                    <span class="text-xl sm:text-2xl font-extrabold text-[#284132] block">${total} <span class="text-xs text-stone-500 font-medium">/ ${daysInMonth}d</span></span>
                    <span class="text-[10px] text-stone-400 font-medium block">${Math.round((total / daysInMonth) * 100)}% consistency</span>
                </div>
            </div>

            <!-- Distribution & Bar Chart -->
            <div class="bg-white rounded-2xl border border-stone-200/80 p-4 sm:p-5 shadow-2xs mt-3.5 space-y-4">
                <div>
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-xs font-bold text-[#284132]">Selection Distribution</span>
                        <span class="text-[10px] text-stone-400 font-medium">${total} recorded selections</span>
                    </div>
                    <div class="w-full h-3.5 rounded-full overflow-hidden flex bg-stone-100">
                        ${stackedBarHTML}
                    </div>
                </div>

                <div class="space-y-3 pt-2 border-t border-stone-100">
                    <span class="text-xs font-bold text-[#284132] block">Option Frequencies</span>
                    ${barsHTML}
                </div>
            </div>
        `;
    }

    function renderScaleMonthlyAnalytics(records, tracker, dotColor, monthName, year, daysInMonth, formatShortDate) {
        const valid = records.filter(r => r.hasValue && !isNaN(parseFloat(r.val)));
        if (valid.length === 0) return renderEmptyMonthlyState(tracker, monthName, year);

        const scaleMax = tracker.scale_max || 5;
        const sum = valid.reduce((acc, r) => acc + parseFloat(r.val), 0);
        const avg = (sum / valid.length).toFixed(1);
        const highest = valid.reduce((max, r) => parseFloat(r.val) > parseFloat(max.val) ? r : max, valid[0]);
        const lowest = valid.reduce((min, r) => parseFloat(r.val) < parseFloat(min.val) ? r : min, valid[0]);
        const count = valid.length;

        const yTicks = [];
        for (let i = 1; i <= scaleMax; i++) {
            yTicks.push({ val: i, label: String(i) });
        }

        const chartSVG = buildSvgLineChart(records, 1, scaleMax, yTicks, dotColor, `/${scaleMax}`, daysInMonth);

        return `
            <!-- Stats Cards Grid -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3 pt-3">
                <div class="bg-white/80 border border-stone-200/80 rounded-2xl p-3 shadow-2xs space-y-0.5">
                    <span class="text-[10px] sm:text-[11px] font-bold text-stone-500 uppercase tracking-wide block">Avg Score</span>
                    <span class="text-xl sm:text-2xl font-extrabold text-[#284132] block">${avg} <span class="text-xs text-stone-500 font-medium">/ ${scaleMax}</span></span>
                    <span class="text-[10px] text-stone-400 font-medium block">from ${count} checks</span>
                </div>
                <div class="bg-white/80 border border-stone-200/80 rounded-2xl p-3 shadow-2xs space-y-0.5">
                    <span class="text-[10px] sm:text-[11px] font-bold text-stone-500 uppercase tracking-wide block">Highest</span>
                    <span class="text-xl sm:text-2xl font-extrabold text-[#284132] block">${parseFloat(highest.val)} <span class="text-xs text-stone-500 font-medium">/ ${scaleMax}</span></span>
                    <span class="text-[10px] text-stone-400 font-medium block">${formatShortDate(highest.dateStr)}</span>
                </div>
                <div class="bg-white/80 border border-stone-200/80 rounded-2xl p-3 shadow-2xs space-y-0.5">
                    <span class="text-[10px] sm:text-[11px] font-bold text-stone-500 uppercase tracking-wide block">Lowest</span>
                    <span class="text-xl sm:text-2xl font-extrabold text-[#284132] block">${parseFloat(lowest.val)} <span class="text-xs text-stone-500 font-medium">/ ${scaleMax}</span></span>
                    <span class="text-[10px] text-stone-400 font-medium block">${formatShortDate(lowest.dateStr)}</span>
                </div>
                <div class="bg-white/80 border border-stone-200/80 rounded-2xl p-3 shadow-2xs space-y-0.5">
                    <span class="text-[10px] sm:text-[11px] font-bold text-stone-500 uppercase tracking-wide block">Checked In</span>
                    <span class="text-xl sm:text-2xl font-extrabold text-[#284132] block">${count} <span class="text-xs text-stone-500 font-medium">/ ${daysInMonth}d</span></span>
                    <span class="text-[10px] text-stone-400 font-medium block">${Math.round((count / daysInMonth) * 100)}% active</span>
                </div>
            </div>

            <!-- Chart Container -->
            <div class="bg-white rounded-2xl border border-stone-200/80 p-4 shadow-2xs mt-3.5 space-y-2">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-bold text-[#284132]">Daily Scale Ratings (1–${scaleMax})</span>
                    <span class="text-[10px] text-stone-400 font-medium">Gaps indicate unrecorded days</span>
                </div>
                ${chartSVG}
            </div>
        `;
    }

    function renderQuantityMonthlyAnalytics(records, tracker, dotColor, monthName, year, daysInMonth, formatShortDate) {
        const valid = records.filter(r => r.hasValue && r.val !== 'no' && !isNaN(parseFloat(r.val)));
        if (valid.length === 0) return renderEmptyMonthlyState(tracker, monthName, year);

        const unit = tracker.quantity_unit || 'min';
        const total = valid.reduce((acc, r) => acc + parseFloat(r.val), 0);
        const avgNum = total / valid.length;
        const avg = Number.isInteger(avgNum) ? avgNum : Number(avgNum.toFixed(1));
        const displayTotal = Number.isInteger(total) ? total : Number(total.toFixed(2));
        const highest = valid.reduce((max, r) => parseFloat(r.val) > parseFloat(max.val) ? r : max, valid[0]);
        const lowest = valid.reduce((min, r) => parseFloat(r.val) < parseFloat(min.val) ? r : min, valid[0]);
        const count = valid.length;

        const maxVal = parseFloat(highest.val);
        const yMax = Math.max(10, Math.ceil(maxVal * 1.25));
        const step = Math.ceil(yMax / 4);
        const yTicks = [
            { val: 0, label: '0' },
            { val: step, label: String(step) },
            { val: step * 2, label: String(step * 2) },
            { val: step * 3, label: String(step * 3) },
            { val: step * 4, label: String(step * 4) }
        ];

        const chartSVG = buildSvgLineChart(records, 0, step * 4, yTicks, dotColor, ` ${unit}`, daysInMonth);

        return `
            <!-- Stats Cards Grid -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3 pt-3">
                <div class="bg-white/80 border border-stone-200/80 rounded-2xl p-3 shadow-2xs space-y-0.5">
                    <span class="text-[10px] sm:text-[11px] font-bold text-stone-500 uppercase tracking-wide block">Total Logged</span>
                    <span class="text-xl sm:text-2xl font-extrabold text-[#284132] block truncate">${displayTotal} <span class="text-xs text-stone-500 font-medium">${escapeHTML(unit)}</span></span>
                    <span class="text-[10px] text-stone-400 font-medium block">in ${monthName}</span>
                </div>
                <div class="bg-white/80 border border-stone-200/80 rounded-2xl p-3 shadow-2xs space-y-0.5">
                    <span class="text-[10px] sm:text-[11px] font-bold text-stone-500 uppercase tracking-wide block">Daily Avg</span>
                    <span class="text-xl sm:text-2xl font-extrabold text-[#284132] block truncate">${avg} <span class="text-xs text-stone-500 font-medium">${escapeHTML(unit)}</span></span>
                    <span class="text-[10px] text-stone-400 font-medium block">on active days</span>
                </div>
                <div class="bg-white/80 border border-stone-200/80 rounded-2xl p-3 shadow-2xs space-y-0.5">
                    <span class="text-[10px] sm:text-[11px] font-bold text-stone-500 uppercase tracking-wide block">Highest Day</span>
                    <span class="text-xl sm:text-2xl font-extrabold text-[#284132] block truncate">${parseFloat(highest.val)} <span class="text-xs text-stone-500 font-medium">${escapeHTML(unit)}</span></span>
                    <span class="text-[10px] text-stone-400 font-medium block">${formatShortDate(highest.dateStr)}</span>
                </div>
                <div class="bg-white/80 border border-stone-200/80 rounded-2xl p-3 shadow-2xs space-y-0.5">
                    <span class="text-[10px] sm:text-[11px] font-bold text-stone-500 uppercase tracking-wide block">Checked In</span>
                    <span class="text-xl sm:text-2xl font-extrabold text-[#284132] block">${count} <span class="text-xs text-stone-500 font-medium">/ ${daysInMonth}d</span></span>
                    <span class="text-[10px] text-stone-400 font-medium block">${Math.round((count / daysInMonth) * 100)}% active</span>
                </div>
            </div>

            <!-- Chart Container -->
            <div class="bg-white rounded-2xl border border-stone-200/80 p-4 shadow-2xs mt-3.5 space-y-2">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-bold text-[#284132]">Daily Quantities (${escapeHTML(unit)})</span>
                    <span class="text-[10px] text-stone-400 font-medium">Gaps indicate unrecorded days</span>
                </div>
                ${chartSVG}
            </div>
        `;
    }

    // Main Render Function
    function render() {
        const root = document.getElementById('self-check-workspace-root');
        if (!root) return;

        // Ensure soft sage-green background matching reference screenshot
        document.body.style.backgroundColor = '#E6EDE7';
        const mainEl = document.querySelector('main');
        if (mainEl) mainEl.style.backgroundColor = '#E6EDE7';

        // Auto-seed defaults if storage is empty
        seedDefaultsIfEmpty();

        const weekDays = getCurrentWeekDays();
        const weekDateRangeStr = getWeekDateRangeStr();
        const activeTrackers = window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function'
            ? window.TempoRecoverySelfCheck.getActiveTrackers()
            : [];

        const streak = window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.calculateStreak === 'function'
            ? window.TempoRecoverySelfCheck.calculateStreak()
            : 0;

        // Resolve today's observation values for Left Card
        const tensionTrk = activeTrackers.find(t => t.check_method === 'percentage' || t.name.toLowerCase().includes('tension'));
        const sleepTrk = activeTrackers.find(t => t.check_method === 'yes_no' || t.name.toLowerCase().includes('sleep'));
        const walkTrk = activeTrackers.find(t => t.check_method === 'quantity' || t.name.toLowerCase().includes('walk'));

        let tensionVal = 0;
        let hasTensionAnswered = false;
        if (tensionTrk) {
            const obs = getTodayObservation(tensionTrk.id);
            if (obs && obs.value !== undefined && obs.value !== null && obs.status === 'answered') {
                tensionVal = parseInt(obs.value, 10);
                hasTensionAnswered = true;
            }
        }

        let sleepVal = null;
        if (sleepTrk) {
            const obs = getTodayObservation(sleepTrk.id);
            if (obs && obs.value !== undefined && obs.value !== null && obs.status === 'answered') {
                sleepVal = String(obs.value).toLowerCase();
            }
        }

        // Quantity tracking items handled dynamically via renderQuantityCheckinSection

        // Count checked-in items today
        let answeredTodayCount = 0;
        activeTrackers.forEach(t => {
            const obs = getTodayObservation(t.id);
            if (obs && obs.status === 'answered' && obs.value !== null && obs.value !== undefined) {
                answeredTodayCount++;
            }
        });

        const todayNote = getTodayNote();

        // Build Right Column Tracker Cards HTML
        let rightColumnItemsHTML = '';
        if (activeTrackers.length === 0) {
            rightColumnItemsHTML = `
                <div class="p-8 sm:p-10 text-center rounded-3xl border-2 border-dashed border-[#8E9F92]/40 bg-white/40 space-y-3 my-2" data-tempo-ui="selfcheck-empty-state">
                    <h3 class="font-heading text-lg font-bold text-[#1B4332]">No tracking items yet</h3>
                    <p class="text-xs sm:text-sm text-[#5B5550] max-w-sm mx-auto leading-relaxed">Add a tracking item to start recording your daily check-ins.</p>
                    <div class="pt-2">
                        <button type="button" 
                                onclick="window.TempoSelfCheckWorkspace.openAddTracking()"
                                class="px-4 py-2 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shadow-2xs inline-flex items-center space-x-1.5">
                            <span>+ Add Tracking</span>
                        </button>
                    </div>
                </div>
            `;
        } else {
            rightColumnItemsHTML = activeTrackers.map(t => {
                const summary = calculateTrackerWeeklySummary(t, weekDays);
                const dotColor = t.type_color || (t.category === 'stress_sign' ? '#D48366' : (t.category === 'supportive' ? '#166545' : '#1E40AF'));
                const alertStatus = checkTrackerAlert(t);

                // Generate 7-day values in consistent 7-column grid
                const dayCellsHTML = weekDays.map(d => {
                    const obs = getObservationForDate(t.id, d.dateStr);
                    const formattedVal = formatDayObservationValue(t, obs);
                    return `
                        <div class="flex flex-col items-center text-center justify-end w-full">
                            <div class="h-6 flex items-center justify-center text-xs w-full text-center font-semibold text-[#37352F]">
                                ${formattedVal}
                            </div>
                            <span class="text-xs font-bold text-[#5B5550] select-none text-center w-full mt-1.5">${d.dayLabel}</span>
                        </div>
                    `;
                }).join('');

                return `
                    <div class="space-y-3 pb-6 border-b border-stone-300/60 last:border-0" data-tracker-id="${t.id}">
                        <!-- Item Header: Colored Dot + Name + Adjust button -->
                        <div class="flex items-center justify-between w-full">
                            <div class="flex items-center space-x-2.5 min-w-0">
                                <span class="w-2.5 h-2.5 rounded-full shrink-0 inline-block" style="background-color: ${dotColor};"></span>
                                <h3 class="font-bold text-base sm:text-lg text-[#37352F] tracking-tight truncate">${escapeHTML(t.name)}</h3>
                                ${alertStatus.triggered ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FFE9DC] text-[#C34D2E] border border-[#FFD2BA] whitespace-nowrap">Alert</span>` : ''}
                            </div>
                            <button type="button" 
                                    onclick="window.TempoSelfCheckWorkspace.openAdjustTracker('${t.id}')"
                                    class="px-3.5 py-1 rounded-xl text-xs font-bold bg-[#8E9F92] hover:bg-[#7D8F81] text-white transition cursor-pointer shadow-2xs shrink-0">
                                Adjust
                            </button>
                        </div>

                        <!-- 7-Day Values & Days Grid (equal column widths, values directly centered above weekday labels) -->
                        <div class="grid grid-cols-7 gap-1 text-center py-1 w-full">
                            ${dayCellsHTML}
                        </div>

                        <!-- Summary Section: Average Row + Right-Aligned View Full Check Row -->
                        <div class="pt-2 text-xs sm:text-sm text-[#5B5550] space-y-2">
                            <!-- Row 1: Average Label on Left, Average Value on Right -->
                            <div class="flex items-center justify-between text-xs sm:text-sm text-[#5B5550]">
                                <span class="font-medium text-[#5B5550] leading-snug">${summary.metricLabel}</span>
                                <span class="font-bold text-xs sm:text-sm text-[#37352F] text-right whitespace-nowrap">${summary.metricValue}</span>
                            </div>

                            <!-- Row 2: View my full check Button Aligned to Right Edge -->
                            <div class="flex justify-end pt-0.5">
                                <button type="button" 
                                        onclick="window.TempoSelfCheckWorkspace.openFullCheckPlaceholder('${t.id}')"
                                        class="px-3.5 sm:px-4 py-1.5 rounded-full text-xs font-semibold bg-white/90 hover:bg-white border border-[#99A99D] text-[#202124] transition shadow-2xs cursor-pointer whitespace-nowrap">
                                    View my full check
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Other custom trackers in Left Card (if any beyond Tension, Sleep, Walk)
        const customTrackers = activeTrackers.filter(t => t !== tensionTrk && t !== sleepTrk && t !== walkTrk);
        let customTrackersHTML = '';
        if (customTrackers.length > 0) {
            customTrackersHTML = customTrackers.map(t => {
                if (t.check_method === 'quantity') {
                    return `<div class="pt-2 border-t border-stone-100">${renderQuantityCheckinSection(t)}</div>`;
                }
                const obs = getTodayObservation(t.id);
                const dotColor = t.type_color || (t.category === 'stress_sign' ? '#D48366' : (t.category === 'supportive' ? '#166545' : '#1E40AF'));
                const isAnswered = obs && obs.status === 'answered' && obs.value !== null && obs.value !== undefined;
                const obsVal = isAnswered ? obs.value : null;

                let checkinInputHTML = '';
                if (t.check_method === 'options') {
                    const opts = (t.options && Array.isArray(t.options) && t.options.length > 0) ? t.options : ['Yes', 'No'];
                    checkinInputHTML = `
                        <div class="flex flex-wrap gap-1.5 pt-0.5">
                            ${opts.map(opt => `
                                <button type="button" 
                                        onclick="window.TempoSelfCheckWorkspace.setCustomObservation('${t.id}', '${escapeHTML(opt)}')"
                                        class="px-3 py-1 rounded-xl text-xs font-semibold border transition cursor-pointer ${String(obsVal) === String(opt) ? 'bg-[#EDF7F1] border-[#166545] text-[#166545] font-bold shadow-2xs' : 'bg-white border-stone-200 text-[#5B5550] hover:bg-stone-50'}">
                                    ${escapeHTML(opt)}
                                </button>
                            `).join('')}
                        </div>
                    `;
                } else if (t.check_method === 'scale') {
                    const max = t.scale_max || (t.scale_range === '1-10' ? 10 : 5);
                    const numbers = [];
                    for (let n = 1; n <= max; n++) numbers.push(n);
                    checkinInputHTML = `
                        <div class="flex items-center space-x-1 pt-0.5 overflow-x-auto pb-0.5">
                            ${numbers.map(num => `
                                <button type="button" 
                                        onclick="window.TempoSelfCheckWorkspace.setCustomObservation('${t.id}', ${num})"
                                        class="w-7 h-7 rounded-xl text-xs font-bold border transition cursor-pointer flex items-center justify-center shrink-0 ${Number(obsVal) === num ? 'bg-[#166545] text-white border-[#166545] shadow-2xs' : 'bg-white border-stone-200 text-[#5B5550] hover:bg-stone-50'}">
                                    ${num}
                                </button>
                            `).join('')}
                        </div>
                    `;
                } else if (t.check_method === 'percentage') {
                    const pctVal = isAnswered ? parseInt(obsVal, 10) : 0;
                    checkinInputHTML = `
                        <div class="space-y-1 pt-0.5">
                            <div class="flex items-center justify-between text-xs">
                                <span class="text-stone-400">Current:</span>
                                <span class="font-bold text-[#37352F]" id="custom-pct-val-${t.id}">${isAnswered ? `${pctVal}%` : '0%'}</span>
                            </div>
                            <input type="range" min="0" max="100" value="${pctVal}" 
                                   oninput="const el = document.getElementById('custom-pct-val-${t.id}'); if (el) el.textContent = this.value + '%';"
                                   onchange="window.TempoSelfCheckWorkspace.setCustomObservation('${t.id}', parseInt(this.value, 10))"
                                   class="w-full accent-[#4A6B5D] cursor-pointer">
                        </div>
                    `;
                } else {
                    checkinInputHTML = `
                        <div class="text-xs text-[#5B5550]">
                            <span>Status: ${isAnswered ? 'Checked in' : 'Pending'}</span>
                        </div>
                    `;
                }

                return `
                    <div class="space-y-1.5 pt-2 border-t border-stone-100" data-custom-tracker-id="${t.id}">
                        <div class="flex items-center space-x-2 text-sm font-bold text-[#37352F]">
                            <span class="w-2.5 h-2.5 rounded-full inline-block shrink-0" style="background-color: ${dotColor};"></span>
                            <span>${escapeHTML(t.name)}</span>
                        </div>
                        ${checkinInputHTML}
                    </div>
                `;
            }).join('');
        }

        // Master Layout HTML matching reference screenshot
        root.innerHTML = `
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 space-y-6">
                <!-- Top Utility Bar: Return Home & Centered Title -->
                <div class="relative flex items-center justify-between pb-2">
                    <!-- Top Left: ← Return Home -->
                    <div class="shrink-0">
                        <button type="button" 
                                id="btn-self-check-return-home"
                                data-tempo-action="return-home"
                                onclick="window.TempoSelfCheckWorkspace.returnHome()" 
                                class="inline-flex items-center space-x-1.5 text-xs sm:text-sm font-semibold text-[#4A6B5D] hover:text-[#166545] transition cursor-pointer" 
                                title="Return Home">
                            <span class="text-base leading-none">←</span>
                            <span>Return Home</span>
                        </button>
                    </div>

                    <!-- Centered Title -->
                    <div class="absolute left-1/2 -translate-x-1/2 text-center pointer-events-none">
                        <h1 class="font-heading text-2xl sm:text-3xl md:text-4xl font-extrabold text-[#234E3B] tracking-tight">
                            Tempo Self-check
                        </h1>
                    </div>

                    <!-- Spacer for layout symmetry -->
                    <div class="w-24 shrink-0"></div>
                </div>

                <!-- Two-Column Main Content -->
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-10 items-start">
                    <!-- LEFT COLUMN (col-span-5): Summary Card + Action Buttons -->
                    <div class="lg:col-span-5 space-y-4 lg:sticky lg:top-20">
                        <!-- Card: Today's self-check -->
                        <div class="bg-[#FEFAF4] rounded-3xl p-6 sm:p-7 shadow-xs border border-white/80 space-y-4">
                            <!-- Category, Title, Streak -->
                            <div class="space-y-1">
                                <span class="text-xs sm:text-sm font-extrabold text-[#4A6B5D] uppercase tracking-wide block">Your daily check-in</span>
                                <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#37352F] tracking-tight leading-snug">Today’s self-check</h2>
                                <p class="text-xs italic text-[#787570] font-medium">${streak}-day streak</p>
                            </div>

                            <!-- Interactive Trackers -->
                            <div class="space-y-3.5 pt-1">
                                ${activeTrackers.length === 0 ? `
                                    <div class="py-5 text-center space-y-1.5 text-stone-500">
                                        <p class="text-xs font-semibold text-[#5B5550]">No tracking items yet</p>
                                        <p class="text-[11px] text-[#787570]">Add a tracking item to start recording your daily check-ins.</p>
                                    </div>
                                ` : `
                                    <!-- Tension -->
                                    ${tensionTrk ? `
                                        <div class="space-y-1.5">
                                            <div class="flex items-center space-x-2 text-sm font-bold text-[#37352F]">
                                                <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: ${tensionTrk.type_color || '#D48366'};"></span>
                                                <span>${escapeHTML(tensionTrk.name || 'Tension')}</span>
                                            </div>
                                            <div class="space-y-1">
                                                <input type="range" min="0" max="100" value="${hasTensionAnswered ? tensionVal : 0}"
                                                       class="selfcheck-tension-slider"
                                                       oninput="window.TempoSelfCheckWorkspace.onTensionInput(this.value)"
                                                       onchange="window.TempoSelfCheckWorkspace.onTensionChange(this.value)">
                                                <div class="text-center text-xs font-bold text-[#5B5550]">
                                                    <span id="selfcheck-tension-val">${hasTensionAnswered ? tensionVal + '%' : '0%'}</span>
                                                </div>
                                            </div>
                                        </div>
                                    ` : ''}

                                    <!-- Sleep -->
                                    ${sleepTrk ? `
                                        <div class="space-y-1.5">
                                            <div class="flex items-center space-x-2 text-sm font-bold text-[#37352F]">
                                                <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: ${sleepTrk.type_color || '#166545'};"></span>
                                                <span>${escapeHTML(sleepTrk.name || 'Sleep')}</span>
                                            </div>
                                            <p class="text-xs text-[#5B5550]">How was your sleep last night?</p>
                                            <div class="flex items-center space-x-3 pt-0.5">
                                                <button type="button" 
                                                        onclick="window.TempoSelfCheckWorkspace.setSleepValue('good')"
                                                        class="px-5 py-1.5 rounded-xl text-xs font-semibold border transition cursor-pointer ${sleepVal === 'good' ? 'bg-[#EDF7F1] border-[#166545] text-[#166545] font-bold shadow-2xs' : 'bg-white border-stone-200 text-[#5B5550] hover:bg-stone-50'}">
                                                    Good
                                                </button>
                                                <button type="button" 
                                                        onclick="window.TempoSelfCheckWorkspace.setSleepValue('not_good')"
                                                        class="px-5 py-1.5 rounded-xl text-xs font-semibold border transition cursor-pointer ${sleepVal === 'not_good' ? 'bg-[#FCEEE8] border-[#D48366] text-[#B83D08] font-bold shadow-2xs' : 'bg-white border-stone-200 text-[#5B5550] hover:bg-stone-50'}">
                                                    Not good
                                                </button>
                                            </div>
                                        </div>
                                    ` : ''}

                                    <!-- Quantity Tracker: Walk -->
                                    ${walkTrk ? renderQuantityCheckinSection(walkTrk) : ''}

                                    <!-- Any Custom Trackers -->
                                    ${customTrackersHTML}
                                `}

                                <!-- Create a note for today -->
                                <div class="pt-2">
                                    <button type="button" 
                                            onclick="window.TempoSelfCheckWorkspace.toggleNoteInput()"
                                            class="text-xs font-semibold text-[#D05A3F] hover:underline transition cursor-pointer flex items-center space-x-1">
                                        <span>Create a note for today</span>
                                    </button>
                                    <div id="selfcheck-today-note-box" class="${showNoteInput ? '' : 'hidden'} pt-2 space-y-2">
                                        <textarea id="selfcheck-today-note-textarea" 
                                                  rows="2" 
                                                  placeholder="How are you feeling today?" 
                                                  class="w-full p-2.5 text-xs rounded-xl border border-stone-200 focus:outline-none focus:border-[#4A6B5D] bg-white resize-none">${escapeHTML(todayNote)}</textarea>
                                        <div class="flex justify-end space-x-2">
                                            <button type="button" onclick="window.TempoSelfCheckWorkspace.saveTodayNote()" 
                                                    class="px-3 py-1 rounded-lg text-xs font-bold bg-[#7B9688] text-white hover:bg-[#6D8475] transition cursor-pointer">
                                                Save note
                                            </button>
                                        </div>
                                    </div>
                                </div>

                                <!-- Status line -->
                                <p class="text-xs text-[#5B5550] pt-1">
                                    You checked in on ${answeredTodayCount} of ${activeTrackers.length} things.
                                </p>
                            </div>
                        </div>

                        <!-- Bottom Buttons: My weekly report & My Recovery notice -->
                        <div class="grid grid-cols-2 gap-3 sm:gap-4 pt-1">
                            <!-- My weekly report -->
                            <button type="button" 
                                    onclick="window.TempoSelfCheckWorkspace.openWeeklyReport()"
                                    class="p-4 sm:p-5 rounded-2xl bg-[#E8EFF3] hover:bg-[#DEE7EC] border border-[#D0DDE5] text-left transition cursor-pointer shadow-2xs flex flex-col justify-center space-y-1">
                                <span class="text-sm sm:text-base font-extrabold text-[#202124] block leading-tight">My weekly report</span>
                                <span class="text-[11px] sm:text-xs text-[#6F6B68] font-medium block">${weekDateRangeStr}</span>
                            </button>

                            <!-- My Recovery notice -->
                            <button type="button" 
                                    onclick="window.TempoSelfCheckWorkspace.openRecoveryNotice()"
                                    class="p-4 sm:p-5 rounded-2xl bg-[#7E9685] hover:bg-[#728A79] text-white text-center transition cursor-pointer shadow-xs flex items-center justify-center">
                                <span class="text-sm sm:text-base font-extrabold block leading-tight">My Recovery notice</span>
                            </button>
                        </div>
                    </div>

                    <!-- RIGHT COLUMN (col-span-7): Your Tracking System (Independently Scrollable) -->
                    <div class="lg:col-span-7 flex flex-col space-y-4">
                        <!-- Header: Title + Add Tracking + Clear all -->
                        <div class="flex items-center justify-between gap-3 pb-1">
                            <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#1B4332]">
                                Your Tracking System
                            </h2>
                            <div class="flex items-center space-x-2">
                                <button type="button" 
                                        onclick="window.TempoSelfCheckWorkspace.openAddTracking()"
                                        class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shadow-2xs">
                                    Add Tracking
                                </button>
                                <button type="button" 
                                        onclick="window.TempoSelfCheckWorkspace.promptClearAll()"
                                        class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#C8322B] hover:bg-[#B32B25] text-white transition cursor-pointer shadow-2xs">
                                    Clear all
                                </button>
                            </div>
                        </div>

                        <!-- Independently Scrollable Container -->
                        <div class="selfcheck-custom-scroll overflow-y-auto max-h-[calc(100vh-210px)] min-h-[380px] pr-2 space-y-6 overscroll-contain">
                            ${rightColumnItemsHTML}
                        </div>
                    </div>
                </div>
            </div>

            <!-- MODAL: Full Check Monthly Popup (matches reference UI) -->
            <div id="modal-selfcheck-fullcheck" 
                 class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-4 hidden" 
                 role="dialog" 
                 aria-modal="true"
                 onclick="if (event.target === this) window.TempoSelfCheckWorkspace.closeFullCheckPlaceholder()">
                <div id="selfcheck-fullcheck-modal-card" 
                     class="max-w-[420px] w-full p-6 sm:p-7 bg-[#FEFAF4] rounded-3xl shadow-2xl relative border border-[#EAE4DF]/80 max-h-[92vh] overflow-y-auto">
                    <!-- Rendered dynamically by renderFullCheckModal -->
                </div>
            </div>

            <!-- MODAL: Adjust Tracking Configuration (matches reference UI) -->
            <div id="modal-selfcheck-adjust" 
                 class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-4 hidden" 
                 role="dialog" 
                 aria-modal="true"
                 onclick="if (event.target === this) window.TempoSelfCheckWorkspace.closeAdjustModal()">
                <div id="selfcheck-adjust-modal-card" 
                     class="max-w-[390px] sm:max-w-[420px] w-full p-6 sm:p-7 bg-[#FEFAF4] rounded-3xl shadow-2xl relative border border-[#EAE4DF]/80 max-h-[92vh] overflow-y-auto"
                     style="background-color: #FEFAF4;">
                    <!-- Rendered dynamically by renderAdjustModal -->
                </div>
            </div>

            <!-- MODAL: Monthly Overview Analytics (matches reference UI) -->
            <div id="modal-selfcheck-monthly-overview" 
                 class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-4 hidden" 
                 role="dialog" 
                 aria-modal="true"
                 onclick="if (event.target === this) window.TempoSelfCheckWorkspace.closeMonthlyOverview()">
                <div id="selfcheck-monthly-overview-card" 
                     class="max-w-2xl w-full p-6 sm:p-7 rounded-3xl shadow-2xl relative border border-[#EAE4DF]/80 max-h-[92vh] overflow-y-auto"
                     style="background-color: #FEFAF4;">
                    <!-- Rendered dynamically by renderMonthlyOverview -->
                </div>
            </div>

            <!-- MODAL: Clear All Confirmation -->
            <div id="modal-selfcheck-clear-confirm" class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-4 hidden" role="dialog" aria-modal="true">
                <div class="tempo-card max-w-md w-full p-6 space-y-5 bg-white rounded-3xl shadow-2xl relative border border-[#EAE4DF]">
                    <div class="space-y-2">
                        <h3 class="font-heading text-lg font-bold text-[#202124]">Clear all tracking items?</h3>
                        <p class="text-xs text-[#6F6B68] leading-relaxed">
                            This will remove active items from your tracking system. Your past check-in history will be preserved safely.
                        </p>
                    </div>
                    <div class="flex items-center justify-end space-x-3 pt-2">
                        <button type="button" onclick="window.TempoSelfCheckWorkspace.closeClearConfirm()" 
                                class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-600 hover:text-stone-900 transition cursor-pointer">
                            Cancel
                        </button>
                        <button type="button" onclick="window.TempoSelfCheckWorkspace.executeClearAll()" 
                                class="px-4 py-2 rounded-xl text-xs font-bold bg-[#C8322B] hover:bg-[#B32B25] text-white transition cursor-pointer shadow-xs">
                            Clear all
                        </button>
                    </div>
                </div>
            </div>

            <!-- MODAL: Weekly Report Popup -->
            <div id="modal-selfcheck-weekly-report" class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-4 hidden" role="dialog" aria-modal="true">
                <div class="tempo-card max-w-xl w-full p-6 sm:p-8 space-y-6 bg-white rounded-3xl shadow-2xl relative border border-[#EAE4DF] max-h-[90vh] overflow-y-auto">
                    <button type="button" onclick="window.TempoSelfCheckWorkspace.closeWeeklyReport()" 
                            class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer" title="Close">✕</button>
                    <div class="space-y-1">
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#4A6B5D]">WEEKLY SUMMARY</span>
                        <h3 class="font-heading text-2xl font-extrabold text-[#202124]">My Weekly Report</h3>
                        <p id="selfcheck-weekly-report-dates" class="text-xs text-[#6F6B68] font-medium"></p>
                    </div>
                    <div id="selfcheck-weekly-report-content" class="space-y-4"></div>
                    <div class="flex justify-between items-center pt-3 border-t border-stone-100">
                        <button type="button" onclick="if (window.TempoWeeklyReview && typeof window.TempoWeeklyReview.open === 'function') { window.TempoSelfCheckWorkspace.closeWeeklyReport(); window.TempoWeeklyReview.open(); }" 
                                class="text-xs font-bold text-[#166545] hover:underline transition cursor-pointer">
                            Open full weekly reflection →
                        </button>
                        <button type="button" onclick="window.TempoSelfCheckWorkspace.closeWeeklyReport()" 
                                class="px-5 py-2 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shadow-xs">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    return {
        open,
        render,
        returnHome,
        onTensionInput,
        onTensionChange,
        setSleepValue,
        setQuantityChoice,
        onQuantityInput,
        onQuantityChange,
        renderQuantityCheckinSection,
        setWalkChoice,
        setWalkMinutes,
        toggleNoteInput,
        saveTodayNote,
        openWeeklyReport,
        closeWeeklyReport,
        openRecoveryNotice,
        openAddTracking,
        openAdjustTracker,
        closeAdjustModal,
        renderAdjustModal,
        setDraftTrackerName,
        setCustomObservation,
        setAdjustType,
        toggleCreateNewTypeForm,
        setNewTypeColor,
        setDraftNewTypeName,
        saveNewType,
        setAdjustMethod,
        addAdjustOption,
        removeAdjustOption,
        setAdjustScaleRange,
        setAdjustQuantityUnit,
        toggleAdjustAlertSystem,
        onAlertOperatorChanged,
        saveAdjustTracker,
        checkTrackerAlert,
        getCustomTypes,
        saveCustomType,
        promptClearAll,
        closeClearConfirm,
        executeClearAll,
        openFullCheckPlaceholder,
        closeFullCheckPlaceholder,
        renderFullCheckModal,
        prevMonthFullCheck,
        nextMonthFullCheck,
        jumpToCurrentMonthFullCheck,
        onFullCheckMonthChange,
        onFullCheckYearChange,
        onMonthlyOverviewClick,
        openMonthlyOverview,
        closeMonthlyOverview,
        prevMonthOverview,
        nextMonthOverview,
        jumpToCurrentMonthOverview,
        renderMonthlyOverview,
        saveCustomCheckinForDate,
        getTodayObservation,
        setTodayObservation
    };
})();
