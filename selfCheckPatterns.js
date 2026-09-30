/**
 * TEMPO WELLBEING — SELF-CHECK PERSONAL PATTERN ENGINE (PHASE 4)
 * File: selfCheckPatterns.js
 *
 * Core Principles:
 * 1. Personal baseline comparison ONLY (compares recent window vs earlier personal window, NEVER universal thresholds).
 * 2. Conservative, descriptive, non-clinical. No universal scores, no mental health diagnosis, no crisis prediction.
 * 3. Per-tracker analysis only (zero correlation claims).
 * 4. Connects explicit Recovery Note linked reminders when elevating Something to Notice.
 * 5. Provides lightweight Dismiss and Remind Later state management.
 */

(function () {
    'use strict';

    // =========================================================================
    // CENTRALIZED CONFIGURATION (Never scattered throughout UI)
    // =========================================================================

    const PATTERN_CONFIG = {
        MIN_TOTAL_OBSERVATIONS: 3,     // Minimum observations needed to evaluate patterns
        RECENT_WINDOW_SIZE: 3,         // Size of recent observation window
        SCALE_DIFF_THRESHOLD: 0.7,     // Meaningful average difference for Scale (1-5)
        PERCENTAGE_DIFF_THRESHOLD: 15, // Meaningful average difference for Percentage (0-100%)
        YES_NO_FREQ_DIFF: 0.35,        // Increase in frequency of Yes for stress sign
        SNOOZE_HOURS: 24               // Cooldown duration for "Remind me later"
    };

    // =========================================================================
    // STORAGE & SNOOZE / DISMISS STATE
    // =========================================================================

    function getUserId() {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') {
            const uid = window.TempoAuth.getCurrentUserId();
            if (uid) return uid;
        }
        return 'local_user';
    }

    function getNoticeStateKey(trackerId) {
        const uid = getUserId();
        return `tempo_notice_state_${uid}_${trackerId}`;
    }

    function getNoticeState(trackerId) {
        try {
            const raw = localStorage.getItem(getNoticeStateKey(trackerId));
            if (raw) return JSON.parse(raw);
        } catch (e) {}
        return null;
    }

    function dismissNotice(trackerId) {
        try {
            const key = getNoticeStateKey(trackerId);
            const state = {
                status: 'dismissed',
                dismissed_at: new Date().toISOString()
            };
            localStorage.setItem(key, JSON.stringify(state));
            refreshRecoveryHome();
        } catch (e) {}
    }

    function snoozeNotice(trackerId) {
        try {
            const key = getNoticeStateKey(trackerId);
            const snoozedUntil = new Date(Date.now() + PATTERN_CONFIG.SNOOZE_HOURS * 3600 * 1000).toISOString();
            const state = {
                status: 'snoozed',
                snoozed_until: snoozedUntil
            };
            localStorage.setItem(key, JSON.stringify(state));
            refreshRecoveryHome();
        } catch (e) {}
    }

    function isNoticeSuppressed(trackerId) {
        const state = getNoticeState(trackerId);
        if (!state) return false;

        if (state.status === 'dismissed') return true;

        if (state.status === 'snoozed' && state.snoozed_until) {
            const until = new Date(state.snoozed_until).getTime();
            if (Date.now() < until) return true;
        }

        return false;
    }

    function refreshRecoveryHome() {
        if (window.TempoMode && typeof window.TempoMode.getMode === 'function') {
            if (window.TempoMode.getMode() === 'recovery') {
                window.TempoMode.renderRmodeHome();
            }
        }
    }

    // =========================================================================
    // OBSERVATION RETRIEVAL HELPER
    // =========================================================================

    function getChronologicalObservations(trackerId) {
        if (!window.TempoRecoverySelfCheck) return [];
        const checkins = window.TempoRecoverySelfCheck.getDailyCheckins() || [];
        // Sort ASC by date
        const sortedCheckins = [...checkins].sort((a, b) => (a.checkin_date || '').localeCompare(b.checkin_date || ''));

        const observations = [];
        sortedCheckins.forEach(chk => {
            const obsList = window.TempoRecoverySelfCheck.getObservationsForCheckin(chk.id);
            const obs = obsList.find(o => o.tracker_id === trackerId);
            if (obs && obs.status === 'answered' && obs.value !== null && obs.value !== undefined) {
                observations.push({
                    date: chk.checkin_date,
                    value: obs.value,
                    note: obs.note || '',
                    status: obs.status
                });
            }
        });

        return observations;
    }

    // =========================================================================
    // PATTERN ENGINE CORE
    // =========================================================================

    function analyzeTracker(tracker) {
        if (!tracker) return { status: 'invalid' };

        const obsList = getChronologicalObservations(tracker.id);

        if (obsList.length < PATTERN_CONFIG.MIN_TOTAL_OBSERVATIONS) {
            return {
                status: 'insufficient_history',
                count: obsList.length,
                tracker
            };
        }

        const recent = obsList.slice(-PATTERN_CONFIG.RECENT_WINDOW_SIZE);
        const earlier = obsList.slice(0, -PATTERN_CONFIG.RECENT_WINDOW_SIZE);

        // 1. NEUTRAL TRACKERS -> Raw descriptive history only, NEVER notice candidate
        if (tracker.category === 'neutral') {
            return buildNeutralDescriptive(tracker, obsList, recent);
        }

        // 2. SUPPORTIVE TRACKERS -> Descriptive positive history only, NEVER warning
        if (tracker.category === 'supportive') {
            return buildSupportiveDescriptive(tracker, obsList, recent);
        }

        // 3. STRESS SIGN TRACKERS
        return buildStressSignAnalysis(tracker, obsList, recent, earlier);
    }

    function buildNeutralDescriptive(tracker, obsList, recent) {
        if (tracker.check_method === 'scale') {
            const values = recent.map(o => Number(o.value)).filter(v => !isNaN(v));
            if (values.length > 0) {
                const min = Math.min(...values);
                const max = Math.max(...values);
                const rangeStr = (min === max) ? `${min}` : `${min}–${max}`;
                return {
                    status: 'descriptive_change',
                    tracker,
                    isConcerning: false,
                    noticeCandidate: false,
                    headline: tracker.name,
                    summary: `Recently ranged from ${rangeStr} / ${tracker.scale_max || 5}`
                };
            }
        } else if (tracker.check_method === 'quantity') {
            const latest = obsList[obsList.length - 1];
            return {
                status: 'descriptive_change',
                tracker,
                isConcerning: false,
                noticeCandidate: false,
                headline: tracker.name,
                summary: `Latest check-in: ${latest.value} ${tracker.quantity_unit || ''}`.trim()
            };
        }

        return {
            status: 'stable_or_no_clear_change',
            tracker,
            isConcerning: false,
            noticeCandidate: false,
            headline: tracker.name,
            summary: `Tracked on ${obsList.length} check-ins`
        };
    }

    function buildSupportiveDescriptive(tracker, obsList, recent) {
        if (tracker.check_method === 'yes_no') {
            const yesCount = recent.filter(o => o.value === true).length;
            if (yesCount > 0) {
                return {
                    status: 'descriptive_change',
                    tracker,
                    isConcerning: false,
                    noticeCandidate: false,
                    headline: tracker.name,
                    summary: `Marked on ${yesCount} recent check-ins`
                };
            }
        } else if (tracker.check_method === 'scale' || tracker.check_method === 'percentage') {
            const latest = obsList[obsList.length - 1];
            const displayVal = tracker.check_method === 'percentage' ? `${latest.value}%` : `${latest.value} / ${tracker.scale_max || 5}`;
            return {
                status: 'descriptive_change',
                tracker,
                isConcerning: false,
                noticeCandidate: false,
                headline: tracker.name,
                summary: `Latest check-in: ${displayVal}`
            };
        }

        return {
            status: 'stable_or_no_clear_change',
            tracker,
            isConcerning: false,
            noticeCandidate: false,
            headline: tracker.name,
            summary: `Tracked on ${obsList.length} check-ins`
        };
    }

    function buildStressSignAnalysis(tracker, obsList, recent, earlier) {
        // If user disabled pattern notices for this stress sign, keep it purely descriptive
        const patternNoticesEnabled = tracker.pattern_notices_enabled !== false;

        if (tracker.check_method === 'yes_no') {
            const recentYesCount = recent.filter(o => o.value === true).length;
            const recentFreq = recentYesCount / recent.length;

            const earlierYesCount = earlier.length > 0 ? earlier.filter(o => o.value === true).length : 0;
            const earlierFreq = earlier.length > 0 ? (earlierYesCount / earlier.length) : 0;

            const hasFrequencyIncrease = (recentFreq >= 0.5 && (recentFreq - earlierFreq >= PATTERN_CONFIG.YES_NO_FREQ_DIFF || earlier.length === 0));

            if (hasFrequencyIncrease) {
                const message = `${tracker.name} has been showing up more often in your recent check-ins.`;
                return {
                    status: 'notice_candidate',
                    tracker,
                    isConcerning: true,
                    noticeCandidate: patternNoticesEnabled,
                    headline: tracker.name,
                    summary: 'Showing up more often recently',
                    detailedNotice: message
                };
            }

            return {
                status: 'stable_or_no_clear_change',
                tracker,
                isConcerning: false,
                noticeCandidate: false,
                headline: tracker.name,
                summary: recentYesCount > 0 ? `Marked Yes on ${recentYesCount} of recent check-ins` : 'Not observed on recent check-ins'
            };
        }

        if (tracker.check_method === 'scale' || tracker.check_method === 'percentage') {
            const isScale = tracker.check_method === 'scale';
            const recentVals = recent.map(o => Number(o.value)).filter(v => !isNaN(v));
            const earlierVals = earlier.map(o => Number(o.value)).filter(v => !isNaN(v));

            const recentAvg = recentVals.reduce((a, b) => a + b, 0) / (recentVals.length || 1);
            const earlierAvg = earlierVals.length > 0
                ? (earlierVals.reduce((a, b) => a + b, 0) / earlierVals.length)
                : (isScale ? 2.5 : 50);

            const diffThreshold = isScale ? PATTERN_CONFIG.SCALE_DIFF_THRESHOLD : PATTERN_CONFIG.PERCENTAGE_DIFF_THRESHOLD;
            const diff = recentAvg - earlierAvg;

            let isElevated = false;
            if (tracker.direction === 'higher_concerning' && diff >= diffThreshold) {
                isElevated = true;
            } else if (tracker.direction === 'higher_better' && (-diff) >= diffThreshold) {
                isElevated = true;
            }

            if (isElevated) {
                const message = `Your recent ${tracker.name.toLowerCase()} check-ins have been higher than your earlier check-ins.`;
                return {
                    status: 'notice_candidate',
                    tracker,
                    isConcerning: true,
                    noticeCandidate: patternNoticesEnabled,
                    headline: tracker.name,
                    summary: 'Higher than earlier check-ins',
                    detailedNotice: message
                };
            }

            const latest = obsList[obsList.length - 1];
            const displayVal = isScale ? `${latest.value} / ${tracker.scale_max || 5}` : `${latest.value}%`;
            return {
                status: 'stable_or_no_clear_change',
                tracker,
                isConcerning: false,
                noticeCandidate: false,
                headline: tracker.name,
                summary: `Latest: ${displayVal}`
            };
        }

        // Quantity: never produces notice candidate
        const latest = obsList[obsList.length - 1];
        return {
            status: 'descriptive_change',
            tracker,
            isConcerning: false,
            noticeCandidate: false,
            headline: tracker.name,
            summary: `Latest: ${latest.value} ${tracker.quantity_unit || ''}`.trim()
        };
    }

    // =========================================================================
    // SOMETHING TO NOTICE & RECENTLY COMPILATION
    // =========================================================================

    function getActiveNotice() {
        if (!window.TempoRecoverySelfCheck) return null;
        const activeTrackers = window.TempoRecoverySelfCheck.getActiveTrackers() || [];

        for (const tracker of activeTrackers) {
            if (tracker.category !== 'stress_sign') continue;
            if (tracker.pattern_notices_enabled === false) continue;
            if (isNoticeSuppressed(tracker.id)) continue;

            const analysis = analyzeTracker(tracker);
            if (analysis.status === 'notice_candidate' && analysis.noticeCandidate) {
                // Find linked Recovery Note reminder if any
                let linkedNoteItem = null;
                if (tracker.linked_note_item_ids && tracker.linked_note_item_ids.length > 0 && window.TempoRecoveryNote) {
                    const allItems = window.TempoRecoveryNote.getItems() || [];
                    for (const id of tracker.linked_note_item_ids) {
                        const found = allItems.find(it => it.id === id);
                        if (found) {
                            linkedNoteItem = found;
                            break;
                        }
                    }
                }

                return {
                    trackerId: tracker.id,
                    trackerName: tracker.name,
                    message: analysis.detailedNotice,
                    linkedNoteItem: linkedNoteItem ? { text: linkedNoteItem.text, type: linkedNoteItem.type } : null
                };
            }
        }

        return null;
    }

    function getRecentlyObservations() {
        if (!window.TempoRecoverySelfCheck) return [];
        const activeTrackers = window.TempoRecoverySelfCheck.getActiveTrackers() || [];
        const results = [];

        activeTrackers.forEach(t => {
            const analysis = analyzeTracker(t);
            if (analysis.status === 'descriptive_change' || analysis.status === 'notice_candidate' || analysis.status === 'stable_or_no_clear_change') {
                const icon = t.category === 'stress_sign' ? '🔴' : (t.category === 'supportive' ? '🟢' : '🔵');
                results.push({
                    trackerId: t.id,
                    trackerName: t.name,
                    icon: icon,
                    summary: analysis.summary || t.name
                });
            }
        });

        // Limit to 2–3 concise observations for display
        return results.slice(0, 3);
    }

    // =========================================================================
    // EXPORTS
    // =========================================================================

    window.TempoSelfCheckPatterns = {
        CONFIG: PATTERN_CONFIG,
        analyzeTracker,
        getChronologicalObservations,
        getActiveNotice,
        getRecentlyObservations,
        dismissNotice,
        snoozeNotice,
        isNoticeSuppressed
    };

})();
