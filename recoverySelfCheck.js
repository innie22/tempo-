/**
 * TEMPO WELLBEING — RECOVERY MODE: USER-DEFINED SELF-CHECK CORE (PHASE 2)
 * File: recoverySelfCheck.js
 *
 * Architecture:
 * 1. User-Defined Trackers Model (Categories: stress_sign, supportive, neutral; Check Methods: yes_no, scale, percentage, quantity)
 * 2. Daily Check-in & Observation Model (strict unanswered, skipped, answered states; no midpoint defaults)
 * 3. Daily Check-in Streak & 7-Day Calendar Indicator (consecutive completed days, no punitive messaging)
 * 4. Recovery Home Card State Provider (State 1: No trackers, State 2: Active trackers, State 3: Checked in today)
 * 5. Manage Trackers, Daily Check-in Form, View/Edit Today Check-in Modals
 * 6. Dual Persistence: Synchronous local storage mirror + additive Supabase client sync
 */

(function () {
    'use strict';

    // =========================================================================
    // CONSTANTS & DEFINITIONS
    // =========================================================================

    const CATEGORIES = {
        STRESS_SIGN: 'stress_sign',
        SUPPORTIVE: 'supportive',
        NEUTRAL: 'neutral'
    };

    const CATEGORY_META = {
        stress_sign: {
            id: 'stress_sign',
            label: 'Sign of stress',
            pluralLabel: 'Signs of stress',
            icon: '🔴',
            color: '#B83D08',
            bgColor: '#FFE9DC',
            borderColor: '#FFD2BA'
        },
        supportive: {
            id: 'supportive',
            label: 'Supportive',
            pluralLabel: 'Supportive habits',
            icon: '🟢',
            color: '#166545',
            bgColor: '#EDF7F1',
            borderColor: '#CDE9DA'
        },
        neutral: {
            id: 'neutral',
            label: 'General',
            pluralLabel: 'General',
            icon: '🔵',
            color: '#1E40AF',
            bgColor: '#DBEAFE',
            borderColor: '#BFDBFE'
        }
    };

    const CHECK_METHODS = {
        YES_NO: 'yes_no',
        SCALE: 'scale',
        PERCENTAGE: 'percentage',
        QUANTITY: 'quantity'
    };

    const CHECK_METHOD_LABELS = {
        yes_no: 'Yes / No',
        scale: 'Scale 1–5',
        percentage: 'Percentage',
        quantity: 'Quantity'
    };

    const SUGGESTIONS = [
        { name: 'Trouble focusing', category: 'stress_sign', check_method: 'yes_no', direction: 'higher_concerning' },
        { name: 'Tension', category: 'stress_sign', check_method: 'percentage', direction: 'higher_concerning' },
        { name: 'Feeling overwhelmed', category: 'stress_sign', check_method: 'scale', scale_min: 1, scale_max: 5, scale_min_label: 'Low', scale_max_label: 'Very high', direction: 'higher_concerning' },
        { name: 'Energy', category: 'neutral', check_method: 'scale', scale_min: 1, scale_max: 5, scale_min_label: 'Drained', scale_max_label: 'Energized', direction: 'higher_better' },
        { name: 'Sleep quality', category: 'supportive', check_method: 'scale', scale_min: 1, scale_max: 5, scale_min_label: 'Poor', scale_max_label: 'Restful', direction: 'higher_better' },
        { name: 'Went outside', category: 'supportive', check_method: 'yes_no', direction: 'higher_better' },
        { name: 'Took a real break', category: 'supportive', check_method: 'yes_no', direction: 'higher_better' },
        { name: 'Water', category: 'neutral', check_method: 'quantity', quantity_unit: 'glasses', direction: 'higher_better' },
        { name: 'Journaling', category: 'supportive', check_method: 'yes_no', direction: 'higher_better' }
    ];

    // =========================================================================
    // STORAGE HELPERS (LOCALSTORAGE + SUPABASE)
    // =========================================================================

    function getUserId() {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') {
            const uid = window.TempoAuth.getCurrentUserId();
            if (uid) return uid;
        }
        return 'local_user';
    }

    function getStorageKey(type) {
        const uid = getUserId();
        return `tempo_selfcheck_${type}_${uid}`;
    }

    function loadFromStorage(type, fallback = []) {
        try {
            const key = getStorageKey(type);
            const raw = localStorage.getItem(key);
            if (raw) return JSON.parse(raw);

            // Only check legacy non-scoped key for default local_user to avoid cross-account leak
            const uid = getUserId();
            if (uid === 'local_user') {
                const legacyKey = `tempo_selfcheck_${type}`;
                const legacyRaw = localStorage.getItem(legacyKey);
                if (legacyRaw) return JSON.parse(legacyRaw);
            }
        } catch (e) {
            console.warn(`[SelfCheck] Error loading ${type} from storage:`, e);
        }
        return fallback;
    }

    function saveToStorage(type, data) {
        try {
            const key = getStorageKey(type);
            localStorage.setItem(key, JSON.stringify(data));
        } catch (e) {
            console.warn(`[SelfCheck] Error saving ${type} to storage:`, e);
        }
    }

    function getSupabaseClient() {
        if (window.TempoSupabase && typeof window.TempoSupabase.getClient === 'function') {
            return window.TempoSupabase.getClient();
        }
        return null;
    }

    // =========================================================================
    // DATE UTILITIES
    // =========================================================================

    function getTodayDateStr() {
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

    function formatHumanDate(dateStr) {
        if (!dateStr) return '';
        const today = getTodayDateStr();
        const yesterday = shiftDateStr(today, -1);
        if (dateStr === today) return 'Today';
        if (dateStr === yesterday) return 'Yesterday';

        try {
            const [y, m, d] = dateStr.split('-').map(Number);
            const dt = new Date(y, m - 1, d);
            return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        } catch (e) {
            return dateStr;
        }
    }

    // =========================================================================
    // TRACKERS API
    // =========================================================================

    function getCanonicalTrackerKey(tracker) {
        if (!tracker) return '';
        const nameLower = (tracker.name || '').trim().toLowerCase();
        if (nameLower.includes('tension')) {
            return 'stress_sign::tension';
        }
        const cat = (tracker.category || CATEGORIES.STRESS_SIGN).toLowerCase();
        return `${cat}::${nameLower}`;
    }

    function consolidateDuplicateTrackers(trackers) {
        if (!Array.isArray(trackers) || trackers.length === 0) return [];

        const uid = getUserId();
        const activeTrackers = trackers.filter(t => !t.is_archived);
        const groups = new Map();

        // Group active trackers by canonical concept key
        activeTrackers.forEach(t => {
            const key = getCanonicalTrackerKey(t);
            if (!groups.has(key)) {
                groups.set(key, []);
            }
            groups.get(key).push(t);
        });

        let hasMutations = false;
        const supersededIds = new Set();
        const idReplacements = new Map(); // oldId -> authoritativeId

        groups.forEach((groupTrackers, key) => {
            if (groupTrackers.length > 1) {
                hasMutations = true;
                // Determine authoritative tracker:
                // 1. If it's Tension, prefer one with check_method === 'percentage'
                // 2. Otherwise prefer the one with the latest updated_at or created_at
                let authoritative = groupTrackers[0];
                for (let i = 1; i < groupTrackers.length; i++) {
                    const candidate = groupTrackers[i];
                    if (key === 'stress_sign::tension') {
                        if (candidate.check_method === 'percentage' && authoritative.check_method !== 'percentage') {
                            authoritative = candidate;
                            continue;
                        }
                    }
                    const candTime = candidate.updated_at || candidate.created_at || '';
                    const authTime = authoritative.updated_at || authoritative.created_at || '';
                    if (candTime > authTime) {
                        authoritative = candidate;
                    }
                }

                // If authoritative is Tension, ensure check_method is 'percentage'
                if (key === 'stress_sign::tension' && authoritative.check_method !== 'percentage') {
                    authoritative.check_method = 'percentage';
                    authoritative.updated_at = new Date().toISOString();
                }

                if (!Array.isArray(authoritative.alias_ids)) {
                    authoritative.alias_ids = [];
                }

                groupTrackers.forEach(t => {
                    if (t.id !== authoritative.id) {
                        t.is_archived = true;
                        t.archived_at = t.archived_at || new Date().toISOString();
                        t.updated_at = new Date().toISOString();
                        supersededIds.add(t.id);
                        idReplacements.set(t.id, authoritative.id);
                        if (!authoritative.alias_ids.includes(t.id)) {
                            authoritative.alias_ids.push(t.id);
                        }
                        if (Array.isArray(t.alias_ids)) {
                            t.alias_ids.forEach(aid => {
                                if (!authoritative.alias_ids.includes(aid)) authoritative.alias_ids.push(aid);
                                idReplacements.set(aid, authoritative.id);
                            });
                        }
                    }
                });
            } else if (groupTrackers.length === 1 && key === 'stress_sign::tension') {
                const singleTension = groupTrackers[0];
                if (singleTension.check_method !== 'percentage') {
                    singleTension.check_method = 'percentage';
                    singleTension.updated_at = new Date().toISOString();
                    hasMutations = true;
                }
            }
        });

        if (hasMutations) {
            saveToStorage('trackers', trackers);

            // Re-point observations with superseded tracker_ids to authoritative tracker_id
            if (idReplacements.size > 0) {
                try {
                    const obsKey = getStorageKey('observations');
                    const rawObs = localStorage.getItem(obsKey);
                    if (rawObs) {
                        const allObs = JSON.parse(rawObs);
                        let obsChanged = false;
                        allObs.forEach(o => {
                            if (o && o.tracker_id && idReplacements.has(o.tracker_id)) {
                                o.tracker_id = idReplacements.get(o.tracker_id);
                                obsChanged = true;
                            }
                        });
                        if (obsChanged) {
                            localStorage.setItem(obsKey, JSON.stringify(allObs));
                            if (uid === 'local_user') {
                                localStorage.setItem('tempo_selfcheck_observations', JSON.stringify(allObs));
                            }
                        }
                    }
                } catch (e) {
                    console.warn('[SelfCheck] Error migrating duplicate observations:', e);
                }

                // If Supabase is active, sync archived state
                supersededIds.forEach(id => {
                    const trk = trackers.find(t => t.id === id);
                    if (trk) syncTrackerToSupabase(trk, 'update');
                });
            }
        }

        return trackers;
    }

    function getTrackers(includeArchived = false) {
        const rawTrackers = loadFromStorage('trackers', []);
        const trackers = consolidateDuplicateTrackers(rawTrackers);
        if (includeArchived) return trackers;
        return trackers.filter(t => !t.is_archived);
    }

    function getActiveTrackers() {
        return getTrackers(false);
    }

    function getTrackerById(id) {
        const trackers = loadFromStorage('trackers', []);
        return trackers.find(t => t.id === id) || null;
    }

    function getTrackerConfigForDate(tracker, dateStr) {
        if (!tracker) return null;
        const versions = Array.isArray(tracker.config_versions) ? tracker.config_versions : [];
        if (versions.length === 0) {
            return {
                check_method: tracker.check_method,
                quantity_unit: tracker.quantity_unit,
                options: tracker.options,
                scale_min: tracker.scale_min,
                scale_max: tracker.scale_max,
                scale_range: tracker.scale_range,
                type_id: tracker.type_id,
                type_label: tracker.type_label,
                type_color: tracker.type_color,
                alert_enabled: tracker.alert_enabled,
                alert_config: tracker.alert_config
            };
        }
        const sorted = [...versions].sort((a, b) => (a.effective_from || '').localeCompare(b.effective_from || ''));
        const match = sorted.find(v => {
            const fromOk = !v.effective_from || v.effective_from <= dateStr;
            const toOk = !v.effective_to || dateStr < v.effective_to;
            return fromOk && toOk;
        });
        if (match) return match;
        if (sorted.length > 0 && dateStr < (sorted[0].effective_from || '')) return sorted[0];
        return sorted[sorted.length - 1];
    }

    // =========================================================================
    // SETUP MANAGEMENT & ARCHIVAL API
    // =========================================================================

    function saveSetups(setups) {
        saveToStorage('setups', setups);
        try {
            const uid = getUserId();
            localStorage.setItem(`tempo_recovery_setups_${uid}`, JSON.stringify(setups));
        } catch (e) {}
    }

    function getSetups() {
        const uid = getUserId();
        let setups = loadFromStorage('setups', []);
        if (setups.length === 0) {
            try {
                const raw = localStorage.getItem(`tempo_recovery_setups_${uid}`);
                if (raw) setups = JSON.parse(raw);
            } catch (e) {}
        }
        if (setups.length === 0) {
            const isCompleted = localStorage.getItem(`tempo_recovery_setup_status_${uid}`) === 'completed';
            const activeTrackers = getActiveTrackers();
            if (isCompleted && activeTrackers.length > 0) {
                const initialSetup = {
                    id: 'setup_default_' + uid,
                    user_id: uid,
                    name: 'Initial Setup',
                    status: 'active',
                    created_at: activeTrackers[0].created_at || new Date().toISOString(),
                    archived_at: null,
                    tracker_ids: activeTrackers.map(t => t.id)
                };
                setups.push(initialSetup);
                saveSetups(setups);
            }
        }
        return setups;
    }

    function getActiveSetup() {
        const setups = getSetups();
        return setups.find(s => s.status === 'active') || null;
    }

    function archiveCurrentSetup() {
        const activeTrackers = getActiveTrackers();
        const setups = getSetups();
        const todayDateStr = getTodayDateStr();

        let activeSetup = setups.find(s => s.status === 'active');
        if (!activeSetup) {
            activeSetup = {
                id: 'setup_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
                user_id: getUserId(),
                name: `Setup (${formatHumanDate(todayDateStr)})`,
                status: 'active',
                created_at: new Date().toISOString(),
                archived_at: null,
                tracker_ids: activeTrackers.map(t => t.id)
            };
            setups.push(activeSetup);
        }

        activeSetup.status = 'archived';
        activeSetup.archived_at = new Date().toISOString();
        activeSetup.trackers_snapshot = activeTrackers.map(t => ({ ...t }));
        activeSetup.recovery_note = (window.TempoRecoveryNote && typeof window.TempoRecoveryNote.getItems === 'function')
            ? window.TempoRecoveryNote.getItems()
            : [];

        // Archive all currently active trackers so they do not appear in the new daily checkin flow
        const allTrackers = loadFromStorage('trackers', []);
        allTrackers.forEach(t => {
            if (activeTrackers.some(act => act.id === t.id)) {
                t.is_archived = true;
                t.archived_at = new Date().toISOString();
                t.updated_at = new Date().toISOString();
            }
        });
        saveToStorage('trackers', allTrackers);
        saveSetups(setups);

        return activeSetup;
    }

    function createActiveSetup(name, trackerIds = []) {
        const setups = getSetups();
        setups.forEach(s => {
            if (s.status === 'active') {
                s.status = 'archived';
                s.archived_at = new Date().toISOString();
            }
        });

        const newSetup = {
            id: 'setup_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
            user_id: getUserId(),
            name: name || 'Active Setup',
            status: 'active',
            created_at: new Date().toISOString(),
            archived_at: null,
            tracker_ids: trackerIds
        };
        setups.push(newSetup);
        saveSetups(setups);
        return newSetup;
    }

    function updateActiveSetup(data) {
        const setups = getSetups();
        let active = setups.find(s => s.status === 'active');
        if (!active) {
            active = createActiveSetup('Active Setup', data.tracker_ids || []);
        } else {
            if (data.name) active.name = data.name;
            if (Array.isArray(data.tracker_ids)) active.tracker_ids = data.tracker_ids;
            if (data.metadata) active.metadata = { ...(active.metadata || {}), ...data.metadata };
            active.updated_at = new Date().toISOString();
            saveSetups(setups);
        }
        return active;
    }

    function createTracker(data) {
        if (!data || !data.name || !data.name.trim()) {
            throw new Error("Tracker name is required.");
        }

        const rawTrackers = loadFromStorage('trackers', []);
        const trackers = consolidateDuplicateTrackers(rawTrackers);
        const cleanName = data.name.trim();
        const cleanCategory = data.category || CATEGORIES.STRESS_SIGN;
        const targetCanonicalKey = getCanonicalTrackerKey({ name: cleanName, category: cleanCategory });

        // Check if an active tracker with this canonical concept already exists
        const existingActive = trackers.find(t => !t.is_archived && getCanonicalTrackerKey(t) === targetCanonicalKey);
        if (existingActive) {
            // Update existing active tracker rather than inserting duplicate
            return updateTracker(existingActive.id, data);
        }

        // Check if an archived tracker with this canonical concept exists
        const existingArchived = trackers.find(t => t.is_archived && getCanonicalTrackerKey(t) === targetCanonicalKey);
        if (existingArchived) {
            // Reactivate existing tracker, preserving past observation history
            existingArchived.is_archived = false;
            delete existingArchived.archived_at;
            existingArchived.updated_at = new Date().toISOString();
            saveToStorage('trackers', trackers);
            return updateTracker(existingArchived.id, data);
        }

        const todayDateStr = getTodayDateStr();
        const isTension = cleanName.toLowerCase().includes('tension');
        const effMethod = isTension ? 'percentage' : (data.check_method || CHECK_METHODS.YES_NO);

        const initialVersion = {
            version_id: 'cfg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
            effective_from: todayDateStr,
            effective_to: null,
            check_method: effMethod,
            options: data.options !== undefined ? data.options : null,
            quantity_unit: data.quantity_unit ? data.quantity_unit.trim() : '',
            scale_min: data.scale_min !== undefined ? Number(data.scale_min) : 1,
            scale_max: data.scale_max !== undefined ? Number(data.scale_max) : 5,
            scale_range: data.scale_range !== undefined ? data.scale_range : null,
            type_id: data.type_id !== undefined ? data.type_id : null,
            type_label: data.type_label !== undefined ? data.type_label : null,
            type_color: data.type_color !== undefined ? data.type_color : null,
            alert_enabled: data.alert_enabled !== undefined ? Boolean(data.alert_enabled) : false,
            alert_config: data.alert_config !== undefined ? data.alert_config : null,
            created_at: new Date().toISOString()
        };

        const newTracker = {
            id: 'trk_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
            user_id: getUserId(),
            name: cleanName,
            category: cleanCategory,
            check_method: effMethod,
            scale_min: data.scale_min !== undefined ? Number(data.scale_min) : 1,
            scale_max: data.scale_max !== undefined ? Number(data.scale_max) : 5,
            scale_min_label: data.scale_min_label || 'Very low',
            scale_max_label: data.scale_max_label || 'Very high',
            quantity_unit: data.quantity_unit ? data.quantity_unit.trim() : '',
            direction: data.direction || 'neutral',
            pattern_notices_enabled: Boolean(data.pattern_notices_enabled),
            linked_note_item_ids: Array.isArray(data.linked_note_item_ids) ? data.linked_note_item_ids : [],
            is_archived: false,
            type_id: data.type_id !== undefined ? data.type_id : null,
            type_label: data.type_label !== undefined ? data.type_label : null,
            type_color: data.type_color !== undefined ? data.type_color : null,
            options: data.options !== undefined ? data.options : null,
            scale_range: data.scale_range !== undefined ? data.scale_range : null,
            alert_enabled: data.alert_enabled !== undefined ? Boolean(data.alert_enabled) : false,
            alert_config: data.alert_config !== undefined ? data.alert_config : null,
            config_versions: [initialVersion],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };

        trackers.push(newTracker);
        saveToStorage('trackers', trackers);

        // Async sync to Supabase if connected
        syncTrackerToSupabase(newTracker, 'insert');

        refreshRecoveryHomeIfActive();
        return newTracker;
    }

    function updateTracker(id, data) {
        const trackers = loadFromStorage('trackers', []);
        const idx = trackers.findIndex(t => t.id === id);
        if (idx === -1) throw new Error("Tracker not found.");

        const existing = trackers[idx];
        const todayDateStr = getTodayDateStr();
        let configVersions = Array.isArray(existing.config_versions) ? [...existing.config_versions] : [];
        if (configVersions.length === 0) {
            configVersions.push({
                version_id: 'cfg_init_' + existing.id,
                effective_from: (existing.created_at ? existing.created_at.slice(0, 10) : todayDateStr),
                effective_to: null,
                check_method: existing.check_method || CHECK_METHODS.YES_NO,
                options: existing.options !== undefined ? existing.options : null,
                quantity_unit: existing.quantity_unit ? existing.quantity_unit : '',
                scale_min: existing.scale_min !== undefined ? existing.scale_min : 1,
                scale_max: existing.scale_max !== undefined ? existing.scale_max : 5,
                scale_range: existing.scale_range !== undefined ? existing.scale_range : null,
                type_id: existing.type_id !== undefined ? existing.type_id : null,
                type_label: existing.type_label !== undefined ? existing.type_label : null,
                type_color: existing.type_color !== undefined ? existing.type_color : null,
                alert_enabled: existing.alert_enabled !== undefined ? Boolean(existing.alert_enabled) : false,
                alert_config: existing.alert_config !== undefined ? existing.alert_config : null,
                created_at: existing.created_at || new Date().toISOString()
            });
        }

        const methodChanged = data.check_method && data.check_method !== existing.check_method;
        const unitChanged = data.quantity_unit !== undefined && data.quantity_unit.trim() !== (existing.quantity_unit || '').trim();
        const optionsChanged = data.options !== undefined && JSON.stringify(data.options) !== JSON.stringify(existing.options);
        const scaleChanged = data.scale_range !== undefined && data.scale_range !== existing.scale_range;

        if (methodChanged || unitChanged || optionsChanged || scaleChanged) {
            // Close previous version effective_to as of todayDateStr
            const currentActiveIdx = configVersions.findIndex(v => v.effective_to === null);
            if (currentActiveIdx !== -1) {
                configVersions[currentActiveIdx].effective_to = todayDateStr;
            }
            // Add new active version
            const newVersion = {
                version_id: 'cfg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
                effective_from: todayDateStr,
                effective_to: null,
                check_method: data.check_method || existing.check_method,
                options: data.options !== undefined ? data.options : existing.options,
                quantity_unit: data.quantity_unit !== undefined ? data.quantity_unit.trim() : existing.quantity_unit,
                scale_min: data.scale_min !== undefined ? Number(data.scale_min) : existing.scale_min,
                scale_max: data.scale_max !== undefined ? Number(data.scale_max) : existing.scale_max,
                scale_range: data.scale_range !== undefined ? data.scale_range : existing.scale_range,
                type_id: data.type_id !== undefined ? data.type_id : existing.type_id,
                type_label: data.type_label !== undefined ? data.type_label : existing.type_label,
                type_color: data.type_color !== undefined ? data.type_color : existing.type_color,
                alert_enabled: data.alert_enabled !== undefined ? Boolean(data.alert_enabled) : existing.alert_enabled,
                alert_config: data.alert_config !== undefined ? data.alert_config : existing.alert_config,
                created_at: new Date().toISOString()
            };
            configVersions.push(newVersion);
        }

        const updated = {
            ...existing,
            name: data.name !== undefined ? data.name.trim() : existing.name,
            category: data.category || existing.category,
            check_method: data.check_method || existing.check_method,
            scale_min: data.scale_min !== undefined ? Number(data.scale_min) : existing.scale_min,
            scale_max: data.scale_max !== undefined ? Number(data.scale_max) : existing.scale_max,
            scale_min_label: data.scale_min_label !== undefined ? data.scale_min_label : existing.scale_min_label,
            scale_max_label: data.scale_max_label !== undefined ? data.scale_max_label : existing.scale_max_label,
            quantity_unit: data.quantity_unit !== undefined ? data.quantity_unit.trim() : existing.quantity_unit,
            direction: data.direction || existing.direction,
            pattern_notices_enabled: data.pattern_notices_enabled !== undefined ? Boolean(data.pattern_notices_enabled) : existing.pattern_notices_enabled,
            linked_note_item_ids: data.linked_note_item_ids !== undefined ? (Array.isArray(data.linked_note_item_ids) ? data.linked_note_item_ids : []) : (existing.linked_note_item_ids || []),
            is_archived: data.is_archived !== undefined ? Boolean(data.is_archived) : existing.is_archived,
            type_id: data.type_id !== undefined ? data.type_id : existing.type_id,
            type_label: data.type_label !== undefined ? data.type_label : existing.type_label,
            type_color: data.type_color !== undefined ? data.type_color : existing.type_color,
            options: data.options !== undefined ? data.options : existing.options,
            scale_range: data.scale_range !== undefined ? data.scale_range : existing.scale_range,
            alert_enabled: data.alert_enabled !== undefined ? Boolean(data.alert_enabled) : existing.alert_enabled,
            alert_config: data.alert_config !== undefined ? data.alert_config : existing.alert_config,
            config_versions: configVersions,
            updated_at: new Date().toISOString()
        };

        trackers[idx] = updated;
        saveToStorage('trackers', trackers);

        syncTrackerToSupabase(updated, 'update');
        refreshRecoveryHomeIfActive();
        return updated;
    }

    function archiveTracker(id) {
        return updateTracker(id, { is_archived: true });
    }

    async function syncTrackerToSupabase(tracker, action) {
        const sb = getSupabaseClient();
        if (!sb || !window.TempoAuth || !window.TempoAuth.getCurrentUserId()) return;
        try {
            const uid = window.TempoAuth.getCurrentUserId();
            const payload = {
                id: tracker.id.startsWith('trk_') ? undefined : tracker.id,
                user_id: uid,
                name: tracker.name,
                category: tracker.category,
                check_method: tracker.check_method,
                scale_min: tracker.scale_min,
                scale_max: tracker.scale_max,
                scale_min_label: tracker.scale_min_label,
                scale_max_label: tracker.scale_max_label,
                quantity_unit: tracker.quantity_unit,
                direction: tracker.direction,
                pattern_notices_enabled: tracker.pattern_notices_enabled,
                linked_note_item_ids: tracker.linked_note_item_ids || [],
                is_archived: tracker.is_archived,
                updated_at: tracker.updated_at
            };
            if (action === 'insert') {
                await sb.from('self_check_trackers').upsert([payload]);
            } else {
                await sb.from('self_check_trackers').update(payload).eq('id', tracker.id);
            }
        } catch (e) {
            console.warn("[SelfCheck] Supabase tracker sync notice (safe local fallback active):", e);
        }
    }

    // =========================================================================
    // DAILY CHECK-INS & OBSERVATIONS API
    // =========================================================================

    function getDailyCheckins() {
        const checkins = loadFromStorage('checkins', []);
        return checkins.sort((a, b) => (b.checkin_date || '').localeCompare(a.checkin_date || ''));
    }

    function getTodayCheckin() {
        const todayStr = getTodayDateStr();
        const checkins = getDailyCheckins();
        return checkins.find(c => c.checkin_date === todayStr) || null;
    }

    function getObservationsForCheckin(checkinId) {
        if (!checkinId) return [];
        const allObs = loadFromStorage('observations', []);
        return allObs.filter(o => o.checkin_id === checkinId);
    }

    function saveTodayCheckin({ observations, overall_note }) {
        const todayStr = getTodayDateStr();
        const checkins = loadFromStorage('checkins', []);
        let existing = checkins.find(c => c.checkin_date === todayStr);

        let checkinRecord;
        if (existing) {
            existing.overall_note = overall_note || '';
            existing.completed_at = new Date().toISOString();
            existing.updated_at = new Date().toISOString();
            checkinRecord = existing;
        } else {
            checkinRecord = {
                id: 'chk_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
                user_id: getUserId(),
                checkin_date: todayStr,
                overall_note: overall_note || '',
                completed_at: new Date().toISOString(),
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            };
            checkins.push(checkinRecord);
        }

        saveToStorage('checkins', checkins);

        // Update observations
        const allObs = loadFromStorage('observations', []);
        const otherObs = allObs.filter(o => o.checkin_id !== checkinRecord.id);

        const newObsList = (observations || []).map(obs => {
            const trk = getTrackerById(obs.tracker_id);
            const cfg = trk ? getTrackerConfigForDate(trk, checkinRecord.checkin_date) : null;
            return {
                id: obs.id || ('obs_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6)),
                checkin_id: checkinRecord.id,
                tracker_id: obs.tracker_id,
                status: obs.status || 'unanswered', // 'unanswered', 'skipped', 'answered'
                value: obs.value !== undefined ? obs.value : null,
                check_method: obs.check_method || (cfg ? cfg.check_method : (trk ? trk.check_method : 'yes_no')),
                quantity_unit: obs.quantity_unit !== undefined ? obs.quantity_unit : (cfg ? cfg.quantity_unit : (trk ? trk.quantity_unit : '')),
                config_version_id: obs.config_version_id || (cfg ? cfg.version_id : null),
                note: obs.note ? obs.note.trim() : '',
                created_at: obs.created_at || new Date().toISOString(),
                updated_at: new Date().toISOString()
            };
        });

        saveToStorage('observations', [...otherObs, ...newObsList]);

        // Background sync to Supabase
        syncCheckinToSupabase(checkinRecord, newObsList);

        refreshRecoveryHomeIfActive();
        return { checkin: checkinRecord, observations: newObsList };
    }

    async function syncCheckinToSupabase(checkin, observations) {
        const sb = getSupabaseClient();
        if (!sb || !window.TempoAuth || !window.TempoAuth.getCurrentUserId()) return;
        try {
            const uid = window.TempoAuth.getCurrentUserId();
            await sb.from('self_check_daily_checkins').upsert([{
                id: checkin.id.startsWith('chk_') ? undefined : checkin.id,
                user_id: uid,
                checkin_date: checkin.checkin_date,
                overall_note: checkin.overall_note,
                completed_at: checkin.completed_at,
                updated_at: checkin.updated_at
            }]);
        } catch (e) {
            console.warn("[SelfCheck] Supabase checkin sync notice (safe local fallback active):", e);
        }
    }

    // =========================================================================
    // STREAK & 7-DAY CALENDAR INDICATOR
    // =========================================================================

    /**
     * Determines if a calendar date has an actual, valid check-in record.
     * Never counts future dates or dates without check-in records.
     */
    function hasValidCheckinForDate(dateStr) {
        if (!dateStr) return false;
        const todayStr = getTodayDateStr();
        if (dateStr > todayStr) return false;

        const checkins = getDailyCheckins();
        const chk = checkins.find(c => c.checkin_date === dateStr);
        if (!chk) return false;

        const obs = getObservationsForCheckin(chk.id);
        const hasAnsweredObs = obs.some(o => o.status === 'answered' && o.value !== null && o.value !== undefined);
        if (hasAnsweredObs) return true;

        if (chk.overall_note && chk.overall_note.trim().length > 0) return true;
        if (chk.completed_at && obs.length > 0) return true;

        return false;
    }

    function calculateStreak() {
        const checkins = getDailyCheckins();
        if (!checkins || checkins.length === 0) return 0;

        const todayStr = getTodayDateStr();
        const yesterdayStr = shiftDateStr(todayStr, -1);

        let streak = 0;
        let startDate = null;

        if (hasValidCheckinForDate(todayStr)) {
            // Checked in today -> streak starts today
            startDate = todayStr;
        } else if (hasValidCheckinForDate(yesterdayStr)) {
            // Not checked today yet, but checked yesterday -> streak remains intact until today ends!
            startDate = yesterdayStr;
        } else {
            // Missed yesterday and today -> streak is broken
            return 0;
        }

        let currDate = startDate;
        while (hasValidCheckinForDate(currDate)) {
            streak++;
            currDate = shiftDateStr(currDate, -1);
        }

        return streak;
    }

    function get7DayHistory() {
        const todayStr = getTodayDateStr();
        const history = [];
        // Past 6 days + today = 7 days
        for (let i = 6; i >= 0; i--) {
            const dateStr = shiftDateStr(todayStr, -i);
            const [y, m, d] = dateStr.split('-').map(Number);
            const dt = new Date(y, m - 1, d);
            const dayLabel = dt.toLocaleDateString('en-US', { weekday: 'narrow' }) || 'D';
            const isChecked = hasValidCheckinForDate(dateStr);
            const isToday = (dateStr === todayStr);

            let status = 'empty';
            if (isChecked) {
                status = 'done';
            } else if (isToday) {
                status = 'pending';
            }

            history.push({
                dateStr,
                dayLabel,
                isChecked,
                isToday,
                status
            });
        }

        return history;
    }

    // =========================================================================
    // RECOVERY HOME INTEGRATION (PROVIDES STATE TO mode.js)
    // =========================================================================

    function getState() {
        const activeTrackers = getActiveTrackers();
        if (activeTrackers.length === 0) {
            return { type: 'STATE_A' };
        }

        const todayCheckin = getTodayCheckin();
        const streak = calculateStreak();
        const history = get7DayHistory();
        const days = history.map(h => h.dayLabel);
        const dayStatus = history.map(h => h.status);

        if (!todayCheckin) {
            return {
                type: 'STATE_B',
                streak: streak,
                trackersCount: activeTrackers.length,
                days: days,
                dayStatus: dayStatus,
                trackersPreview: activeTrackers.slice(0, 3).map(t => t.name)
            };
        }

        // State C: Checked in today
        const observations = getObservationsForCheckin(todayCheckin.id);
        const activeIds = new Set(activeTrackers.map(t => t.id));
        const answeredCount = observations.filter(o => activeIds.has(o.tracker_id) && o.status === 'answered').length;

        return {
            type: 'STATE_C',
            streak: streak,
            checkedCount: answeredCount,
            totalCount: activeTrackers.length,
            days: days,
            dayStatus: dayStatus
        };
    }

    function getRecentlyState() {
        const checkins = getDailyCheckins();
        if (checkins.length >= 1) {
            return { type: 'NOT_ENOUGH' };
        }
        return { type: 'EMPTY' };
    }

    function refreshRecoveryHomeIfActive() {
        if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
            window.TempoMode.renderActiveModeHome();
        } else if (window.TempoMode && typeof window.TempoMode.getMode === 'function') {
            if (window.TempoMode.getMode() === 'recovery') {
                window.TempoMode.renderRmodeHome();
            }
        }
        if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.render === 'function') {
            const scScreen = document.getElementById('screen-stress-check');
            if (scScreen && !scScreen.classList.contains('hidden')) {
                window.TempoSelfCheckWorkspace.render();
            }
        }
    }

    // =========================================================================
    // MODAL SHELLS & CONTROLLERS
    // =========================================================================

    function ensureModalsMounted() {
        if (document.getElementById('tempo-selfcheck-container')) return;

        const container = document.createElement('div');
        container.id = 'tempo-selfcheck-container';
        container.className = 'relative z-[70]';
        container.style.zIndex = '70';
        container.innerHTML = `
            <!-- MODAL 1: MANAGE SELF-CHECK -->
            <div id="modal-selfcheck-manage" class="fixed inset-0 z-[70] flex items-center justify-center modal-backdrop p-4 hidden" style="z-index: 70;" role="dialog" aria-modal="true">
                <div class="tempo-card max-w-xl w-full p-6 sm:p-8 space-y-6 bg-white rounded-3xl shadow-2xl relative border border-[#EAE4DF] max-h-[90vh] overflow-y-auto">
                    <button type="button" onclick="window.TempoRecoverySelfCheck.closeManage()" class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer" title="Close">✕</button>

                    <div class="space-y-1">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#166545] inline-block"></span>
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">SELF-CHECK</span>
                        </div>
                        <h3 class="font-heading text-2xl font-extrabold text-[#202124]">Things I'm keeping track of</h3>
                        <p class="text-xs text-[#6F6B68]">Create a check-in that fits you. You can change or archive items anytime.</p>
                    </div>

                    <!-- Suggestions Chips -->
                    <div class="space-y-2 pt-1 border-t border-stone-100">
                        <span class="text-[11px] font-bold text-stone-500 uppercase tracking-wide">Suggestions</span>
                        <div id="selfcheck-manage-suggestions" class="flex flex-wrap gap-2"></div>
                    </div>

                    <!-- Active Trackers Grouped List -->
                    <div id="selfcheck-manage-list" class="space-y-4 pt-1"></div>

                    <!-- Footer Actions -->
                    <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                        <button type="button" onclick="window.TempoRecoverySelfCheck.openTrackerModal()" class="btn-primary px-4 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                            <span>+ Add tracker</span>
                        </button>
                        <button type="button" onclick="window.TempoRecoverySelfCheck.closeManage()" class="px-4 py-2 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition cursor-pointer">
                            Done
                        </button>
                    </div>
                </div>
            </div>

            <!-- MODAL 2: ADD / EDIT TRACKER -->
            <div id="modal-selfcheck-tracker-edit" class="fixed inset-0 z-[80] flex items-center justify-center modal-backdrop p-4 hidden" style="z-index: 80;" role="dialog" aria-modal="true">
                <div class="tempo-card max-w-lg w-full p-6 sm:p-8 space-y-6 bg-white rounded-3xl shadow-2xl relative border border-[#EAE4DF] max-h-[90vh] overflow-y-auto">
                    <button type="button" onclick="window.TempoRecoverySelfCheck.closeTrackerModal()" class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer" title="Close">✕</button>

                    <div class="space-y-1">
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">TRACKER CONFIGURATION</span>
                        <h3 id="selfcheck-tracker-modal-title" class="font-heading text-2xl font-extrabold text-[#202124]">Add something to track</h3>
                    </div>

                    <form id="form-selfcheck-tracker" onsubmit="window.TempoRecoverySelfCheck.handleTrackerFormSubmit(event)" class="space-y-5">
                        <input type="hidden" id="tracker-edit-id" value="">

                        <!-- Name -->
                        <div class="space-y-1.5">
                            <label for="tracker-input-name" class="block text-xs font-bold uppercase tracking-wider text-[#202124]">Name</label>
                            <input type="text" id="tracker-input-name" required placeholder="e.g. Trouble focusing, Sleep quality, Water..."
                                   class="w-full px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:border-[#166545] focus:ring-1 focus:ring-[#166545] text-sm text-[#202124]">
                        </div>

                        <!-- Category -->
                        <div class="space-y-1.5">
                            <label class="block text-xs font-bold uppercase tracking-wider text-[#202124]">Category</label>
                            <div class="grid grid-cols-3 gap-2">
                                <label class="cursor-pointer border border-stone-200 rounded-xl p-3 text-center flex flex-col items-center space-y-1 hover:border-[#FF6B2C] has-[:checked]:border-[#B83D08] has-[:checked]:bg-[#FFE9DC]/40 transition">
                                    <input type="radio" name="tracker_category" value="stress_sign" checked onchange="window.TempoRecoverySelfCheck.onCategoryChanged()" class="sr-only">
                                    <span class="text-base">🔴</span>
                                    <span class="text-xs font-bold text-[#202124]">Sign of stress</span>
                                </label>
                                <label class="cursor-pointer border border-stone-200 rounded-xl p-3 text-center flex flex-col items-center space-y-1 hover:border-[#166545] has-[:checked]:border-[#166545] has-[:checked]:bg-[#EDF7F1] transition">
                                    <input type="radio" name="tracker_category" value="supportive" onchange="window.TempoRecoverySelfCheck.onCategoryChanged()" class="sr-only">
                                    <span class="text-base">🟢</span>
                                    <span class="text-xs font-bold text-[#202124]">Supportive</span>
                                </label>
                                <label class="cursor-pointer border border-stone-200 rounded-xl p-3 text-center flex flex-col items-center space-y-1 hover:border-[#1E40AF] has-[:checked]:border-[#1E40AF] has-[:checked]:bg-[#DBEAFE]/40 transition">
                                    <input type="radio" name="tracker_category" value="neutral" onchange="window.TempoRecoverySelfCheck.onCategoryChanged()" class="sr-only">
                                    <span class="text-base">🔵</span>
                                    <span class="text-xs font-bold text-[#202124]">General</span>
                                </label>
                            </div>
                        </div>

                        <!-- Check Method -->
                        <div class="space-y-1.5">
                            <label class="block text-xs font-bold uppercase tracking-wider text-[#202124]">Check With</label>
                            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                                <label class="cursor-pointer border border-stone-200 rounded-xl p-2.5 text-center flex flex-col items-center space-y-0.5 has-[:checked]:border-[#166545] has-[:checked]:bg-[#EDF7F1] transition">
                                    <input type="radio" name="tracker_method" value="yes_no" checked onchange="window.TempoRecoverySelfCheck.onMethodChanged()" class="sr-only">
                                    <span class="text-xs font-bold text-[#202124]">Yes / No</span>
                                </label>
                                <label class="cursor-pointer border border-stone-200 rounded-xl p-2.5 text-center flex flex-col items-center space-y-0.5 has-[:checked]:border-[#166545] has-[:checked]:bg-[#EDF7F1] transition">
                                    <input type="radio" name="tracker_method" value="scale" onchange="window.TempoRecoverySelfCheck.onMethodChanged()" class="sr-only">
                                    <span class="text-xs font-bold text-[#202124]">Scale</span>
                                </label>
                                <label class="cursor-pointer border border-stone-200 rounded-xl p-2.5 text-center flex flex-col items-center space-y-0.5 has-[:checked]:border-[#166545] has-[:checked]:bg-[#EDF7F1] transition">
                                    <input type="radio" name="tracker_method" value="percentage" onchange="window.TempoRecoverySelfCheck.onMethodChanged()" class="sr-only">
                                    <span class="text-xs font-bold text-[#202124]">Percentage</span>
                                </label>
                                <label class="cursor-pointer border border-stone-200 rounded-xl p-2.5 text-center flex flex-col items-center space-y-0.5 has-[:checked]:border-[#166545] has-[:checked]:bg-[#EDF7F1] transition">
                                    <input type="radio" name="tracker_method" value="quantity" onchange="window.TempoRecoverySelfCheck.onMethodChanged()" class="sr-only">
                                    <span class="text-xs font-bold text-[#202124]">Quantity</span>
                                </label>
                            </div>
                        </div>

                        <!-- Method-Specific Config Panels -->
                        <div id="tracker-config-scale" class="space-y-3 p-4 bg-stone-50 rounded-2xl border border-stone-200 hidden">
                            <div class="grid grid-cols-2 gap-3">
                                <div>
                                    <label class="block text-[11px] font-bold text-[#6F6B68]">Scale Range</label>
                                    <div class="flex items-center space-x-2 pt-1">
                                        <input type="number" id="tracker-scale-min" value="1" min="0" max="10" class="w-16 px-2.5 py-1.5 rounded-lg border border-stone-300 text-xs">
                                        <span class="text-xs text-stone-400">to</span>
                                        <input type="number" id="tracker-scale-max" value="5" min="2" max="10" class="w-16 px-2.5 py-1.5 rounded-lg border border-stone-300 text-xs">
                                    </div>
                                </div>
                                <div>
                                    <label class="block text-[11px] font-bold text-[#6F6B68]">Labels</label>
                                    <div class="space-y-1 pt-1">
                                        <input type="text" id="tracker-scale-min-label" placeholder="Min (Very low)" value="Very low" class="w-full px-2.5 py-1 rounded-lg border border-stone-300 text-xs">
                                        <input type="text" id="tracker-scale-max-label" placeholder="Max (Very high)" value="Very high" class="w-full px-2.5 py-1 rounded-lg border border-stone-300 text-xs">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div id="tracker-config-quantity" class="space-y-2 p-4 bg-stone-50 rounded-2xl border border-stone-200 hidden">
                            <label for="tracker-quantity-unit" class="block text-[11px] font-bold text-[#6F6B68]">Unit of measurement</label>
                            <input type="text" id="tracker-quantity-unit" placeholder="e.g. glasses, hours, cups, minutes, pages..." class="w-full px-3 py-2 rounded-xl border border-stone-300 text-xs text-[#202124]">
                        </div>

                        <!-- Direction Setting (for scale and percentage) -->
                        <div id="tracker-config-direction" class="space-y-1.5 p-4 bg-stone-50 rounded-2xl border border-stone-200 hidden">
                            <label class="block text-[11px] font-bold text-[#6F6B68]">Higher values mean:</label>
                            <div class="space-y-1">
                                <label class="flex items-center space-x-2 cursor-pointer text-xs text-[#202124]">
                                    <input type="radio" name="tracker_direction" value="higher_concerning" checked>
                                    <span>This sign feels stronger</span>
                                </label>
                                <label class="flex items-center space-x-2 cursor-pointer text-xs text-[#202124]">
                                    <input type="radio" name="tracker_direction" value="higher_better">
                                    <span>I'm doing better</span>
                                </label>
                                <label class="flex items-center space-x-2 cursor-pointer text-xs text-[#202124]">
                                    <input type="radio" name="tracker_direction" value="neutral">
                                    <span>Just track it</span>
                                </label>
                            </div>
                        </div>

                        <!-- Pattern Notices Setting (stress signs only) -->
                        <div id="tracker-config-patterns" class="p-4 bg-[#FFFBF7] rounded-2xl border border-[#FFD2BA] space-y-1">
                            <label class="flex items-start space-x-2.5 cursor-pointer">
                                <input type="checkbox" id="tracker-pattern-notices" checked class="mt-0.5 rounded text-[#B83D08] focus:ring-[#B83D08]">
                                <div>
                                    <span class="text-xs font-bold text-[#202124]">Help me notice patterns</span>
                                    <p class="text-[11px] text-[#6F6B68]">Keep track of when this stress sign shows up so you can spot trends over time.</p>
                                </div>
                            </label>
                        </div>

                        <!-- Recovery Note Item Linking (Optional, max 3) -->
                        <div id="tracker-config-note-linking" class="space-y-2 p-4 bg-stone-50 rounded-2xl border border-stone-200">
                            <div class="flex items-center justify-between">
                                <label class="block text-[11px] font-bold text-[#6F6B68] uppercase tracking-wider">
                                    Link to Recovery Note reminder
                                </label>
                                <span class="text-[10px] text-stone-400 font-medium">Optional · Max 3</span>
                            </div>
                            <p class="text-[11px] text-[#6F6B68]">
                                If this sign shows up more often, Tempo can gently remind you what you wanted to remember.
                            </p>
                            <div id="tracker-note-links-container" class="space-y-1.5 pt-1">
                                <!-- Populated dynamically from TempoRecoveryNote.getItems() -->
                            </div>
                        </div>

                        <!-- Buttons -->
                        <div class="pt-4 border-t border-stone-100 flex items-center justify-end space-x-3">
                            <button type="button" onclick="window.TempoRecoverySelfCheck.closeTrackerModal()" class="px-4 py-2.5 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition cursor-pointer">
                                Cancel
                            </button>
                            <button type="submit" class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer">
                                Save tracker
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- MODAL 3: DAILY SELF-CHECK / EDIT TRACKING FORM -->
            <div id="modal-selfcheck-daily" 
                 class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-4 hidden" 
                 role="dialog" 
                 aria-modal="true"
                 onclick="if (event.target === this) window.TempoRecoverySelfCheck.closeDailyCheckin()">
                <div class="tempo-card max-w-xl w-full p-6 sm:p-8 space-y-6 rounded-3xl shadow-2xl relative border border-[#EAE4DF]/80 max-h-[92vh] overflow-y-auto"
                     style="background-color: #FEFAF4;">
                    <button type="button" onclick="window.TempoRecoverySelfCheck.closeDailyCheckin()" 
                            class="absolute top-5 right-5 w-8 h-8 rounded-full flex items-center justify-center text-[#8C8681] hover:text-[#37352F] hover:bg-stone-200/50 text-base transition cursor-pointer" 
                            title="Close">✕</button>

                    <div class="space-y-1">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#4A6B5D] inline-block"></span>
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#4A6B5D]">YOUR DAILY CHECK-IN</span>
                        </div>
                        <h3 id="selfcheck-daily-modal-title" class="font-heading text-2xl font-extrabold text-[#37352F] tracking-tight">How have things been today?</h3>
                        <p id="selfcheck-daily-modal-subtitle" class="text-xs text-[#7B7672]">Check in with whatever feels useful. You don't have to answer everything.</p>
                    </div>

                    <!-- Daily Trackers List -->
                    <div id="selfcheck-daily-trackers-container" class="space-y-4"></div>

                    <!-- Overall Daily Note -->
                    <div class="space-y-2 pt-2 border-t border-stone-200/80">
                        <label for="selfcheck-overall-note" class="block text-xs font-bold text-[#37352F]">
                            Anything else you want to remember about today? <span class="text-stone-400 font-normal">(Optional)</span>
                        </label>
                        <textarea id="selfcheck-overall-note" rows="2" placeholder="Add an optional note about today..."
                                  class="w-full px-4 py-2.5 rounded-xl border border-stone-300 focus:outline-none focus:border-[#4A6B5D] text-xs text-[#37352F] bg-white resize-none shadow-2xs"></textarea>
                    </div>

                    <!-- Finish CTA -->
                    <div class="pt-4 border-t border-stone-200/80 flex items-center justify-between">
                        <button type="button" onclick="window.TempoRecoverySelfCheck.closeDailyCheckin()" class="px-4 py-2.5 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#37352F] hover:bg-stone-200/50 transition cursor-pointer">
                            Close
                        </button>
                        <button type="button" id="btn-selfcheck-finish" onclick="window.TempoRecoverySelfCheck.finishDailyCheckin()"
                                class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-[#7B9688] hover:bg-[#6D8475] text-white shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                            <span id="btn-selfcheck-finish-text">Finish check-in</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- MODAL 4: VIEW TODAY'S CHECK-IN -->
            <div id="modal-selfcheck-view" 
                 class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-4 hidden" 
                 role="dialog" 
                 aria-modal="true"
                 onclick="if (event.target === this) window.TempoRecoverySelfCheck.closeViewToday()">
                <div class="tempo-card max-w-lg w-full p-6 sm:p-8 space-y-6 bg-white rounded-3xl shadow-2xl relative border border-[#EAE4DF] max-h-[90vh] overflow-y-auto">
                    <button type="button" onclick="window.TempoRecoverySelfCheck.closeViewToday()" class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer" title="Close">✕</button>

                    <div class="space-y-1">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full bg-[#166545] inline-block"></span>
                                <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">SELF-CHECK</span>
                            </div>
                            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA]">
                                ✓ Checked in today
                            </span>
                        </div>
                        <h3 class="font-heading text-2xl font-extrabold text-[#202124]">Today's check-in</h3>
                        <p id="selfcheck-view-summary" class="text-xs text-[#6F6B68]"></p>
                    </div>

                    <div id="selfcheck-view-content" class="space-y-4"></div>

                    <div id="selfcheck-view-overall-note" class="p-3 bg-stone-50 rounded-2xl border border-stone-200 hidden space-y-1">
                        <span class="text-[11px] font-bold text-stone-500 uppercase tracking-wide">Daily Note</span>
                        <p id="selfcheck-view-overall-text" class="text-xs text-[#202124] italic"></p>
                    </div>

                    <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                        <button type="button" onclick="window.TempoRecoverySelfCheck.openDailyCheckin(true)"
                                class="text-xs font-bold text-[#4A6B5D] hover:text-[#3B5441] transition cursor-pointer">
                            Edit check-in
                        </button>
                        <button type="button" onclick="window.TempoRecoverySelfCheck.closeViewToday()"
                                class="px-4 py-2 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition cursor-pointer">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(container);
    }

    // =========================================================================
    // MODAL 1: MANAGE CONTROLLER
    // =========================================================================

    function openManage() {
        if (!window.TempoAuth || !window.TempoAuth.getCurrentUser()) {
            if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                window.TempoMode.openStrack('manage');
            }
            return;
        }
        ensureModalsMounted();
        renderManageView();
        const modal = document.getElementById('modal-selfcheck-manage');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
        }
    }

    function closeManage() {
        const modal = document.getElementById('modal-selfcheck-manage');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    function renderManageView() {
        const listEl = document.getElementById('selfcheck-manage-list');
        const suggEl = document.getElementById('selfcheck-manage-suggestions');
        if (!listEl) return;

        // Render Suggestions Chips
        if (suggEl) {
            suggEl.innerHTML = SUGGESTIONS.map(s => `
                <button type="button" onclick="window.TempoRecoverySelfCheck.useSuggestion('${escapeHTML(s.name)}')"
                        class="px-3 py-1.5 rounded-xl border border-stone-200 hover:border-[#166545] hover:bg-[#EDF7F1] text-xs font-medium text-[#202124] transition cursor-pointer flex items-center space-x-1.5">
                    <span>${s.category === 'stress_sign' ? '🔴' : (s.category === 'supportive' ? '🟢' : '🔵')}</span>
                    <span>${escapeHTML(s.name)}</span>
                </button>
            `).join('');
        }

        const activeTrackers = getActiveTrackers();
        if (activeTrackers.length === 0) {
            listEl.innerHTML = `
                <div class="p-6 text-center rounded-2xl border border-dashed border-stone-200 space-y-2">
                    <p class="text-sm font-semibold text-[#202124]">No trackers set up yet.</p>
                    <p class="text-xs text-[#6F6B68]">Add your first tracker or choose from the suggestions above.</p>
                </div>
            `;
            return;
        }

        const groups = [
            { category: CATEGORIES.STRESS_SIGN, meta: CATEGORY_META.stress_sign },
            { category: CATEGORIES.SUPPORTIVE, meta: CATEGORY_META.supportive },
            { category: CATEGORIES.NEUTRAL, meta: CATEGORY_META.neutral }
        ];

        let html = '';
        groups.forEach(g => {
            const groupTrackers = activeTrackers.filter(t => t.category === g.category);
            if (groupTrackers.length === 0) return;

            html += `
                <div class="space-y-2">
                    <div class="flex items-center space-x-1.5 text-xs font-bold text-[#202124]">
                        <span>${g.meta.icon}</span>
                        <span>${escapeHTML(g.meta.pluralLabel)}</span>
                        <span class="text-stone-400 font-normal">(${groupTrackers.length})</span>
                    </div>
                    <div class="space-y-1.5">
                        ${groupTrackers.map(t => {
                            let methodLabel = CHECK_METHOD_LABELS[t.check_method] || t.check_method;
                            if (t.check_method === 'scale') methodLabel = `Scale ${t.scale_min || 1}–${t.scale_max || 5}`;
                            if (t.check_method === 'quantity' && t.quantity_unit) methodLabel = `Quantity (${t.quantity_unit})`;

                            return `
                                <div class="p-3 rounded-2xl border border-stone-200 hover:border-stone-300 flex items-center justify-between transition">
                                    <div class="space-y-0.5">
                                        <h4 class="text-xs sm:text-sm font-bold text-[#202124]">${escapeHTML(t.name)}</h4>
                                        <span class="text-[11px] text-[#6F6B68] font-medium">${escapeHTML(methodLabel)}</span>
                                    </div>
                                    <div class="flex items-center space-x-2 text-xs font-semibold">
                                        <button type="button" onclick="window.TempoRecoverySelfCheck.openTrackerModal('${t.id}')"
                                                class="px-2.5 py-1 rounded-lg text-[#166545] hover:bg-[#EDF7F1] transition cursor-pointer">
                                            Edit
                                        </button>
                                        <button type="button" onclick="window.TempoRecoverySelfCheck.handleArchiveTracker('${t.id}')"
                                                class="px-2.5 py-1 rounded-lg text-stone-500 hover:text-stone-800 hover:bg-stone-100 transition cursor-pointer">
                                            Archive
                                        </button>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        });

        listEl.innerHTML = html;
    }

    function useSuggestion(name) {
        const s = SUGGESTIONS.find(item => item.name === name);
        if (s) {
            openTrackerModal(null, s);
        } else {
            openTrackerModal(null, { name });
        }
    }

    function handleArchiveTracker(id) {
        archiveTracker(id);
        renderManageView();
        if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.onTrackerArchived === 'function') {
            window.TempoRecoverySetup.onTrackerArchived(id);
        }
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("Tracker archived.");
        }
    }

    // =========================================================================
    // MODAL 2: ADD / EDIT TRACKER CONTROLLER
    // =========================================================================

    function openTrackerModal(trackerId = null, prefill = null) {
        if (trackerId && window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.openAdjustTracker === 'function') {
            window.TempoSelfCheckWorkspace.openAdjustTracker(trackerId);
            return;
        }
        ensureModalsMounted();
        const modal = document.getElementById('modal-selfcheck-tracker-edit');
        const form = document.getElementById('form-selfcheck-tracker');
        const titleEl = document.getElementById('selfcheck-tracker-modal-title');
        const idInput = document.getElementById('tracker-edit-id');
        const nameInput = document.getElementById('tracker-input-name');

        if (!modal || !form) return;
        form.reset();

        if (trackerId) {
            const tracker = getTrackerById(trackerId);
            if (!tracker) return;
            idInput.value = tracker.id;
            titleEl.textContent = 'Edit tracker';
            nameInput.value = tracker.name;

            // Category radio
            const catRadio = form.querySelector(`input[name="tracker_category"][value="${tracker.category}"]`);
            if (catRadio) catRadio.checked = true;

            // Method radio
            const methodRadio = form.querySelector(`input[name="tracker_method"][value="${tracker.check_method}"]`);
            if (methodRadio) methodRadio.checked = true;

            // Scale config
            document.getElementById('tracker-scale-min').value = tracker.scale_min || 1;
            document.getElementById('tracker-scale-max').value = tracker.scale_max || 5;
            document.getElementById('tracker-scale-min-label').value = tracker.scale_min_label || 'Very low';
            document.getElementById('tracker-scale-max-label').value = tracker.scale_max_label || 'Very high';

            // Quantity config
            document.getElementById('tracker-quantity-unit').value = tracker.quantity_unit || '';

            // Direction
            const dirRadio = form.querySelector(`input[name="tracker_direction"][value="${tracker.direction || 'neutral'}"]`);
            if (dirRadio) dirRadio.checked = true;

            // Pattern notices
            document.getElementById('tracker-pattern-notices').checked = Boolean(tracker.pattern_notices_enabled);

            // Recovery Note linking
            renderNoteLinkingSelector(tracker.linked_note_item_ids || []);
        } else {
            idInput.value = '';
            titleEl.textContent = 'Add something to track';
            renderNoteLinkingSelector([]);
            if (prefill) {
                nameInput.value = prefill.name || '';
                if (prefill.category) {
                    const r = form.querySelector(`input[name="tracker_category"][value="${prefill.category}"]`);
                    if (r) r.checked = true;
                }
                if (prefill.check_method) {
                    const m = form.querySelector(`input[name="tracker_method"][value="${prefill.check_method}"]`);
                    if (m) m.checked = true;
                }
                if (prefill.scale_min !== undefined) {
                    document.getElementById('tracker-scale-min').value = prefill.scale_min;
                }
                if (prefill.scale_max !== undefined) {
                    document.getElementById('tracker-scale-max').value = prefill.scale_max;
                }
                if (prefill.scale_min_label) {
                    document.getElementById('tracker-scale-min-label').value = prefill.scale_min_label;
                }
                if (prefill.scale_max_label) {
                    document.getElementById('tracker-scale-max-label').value = prefill.scale_max_label;
                }
                if (prefill.quantity_unit) {
                    document.getElementById('tracker-quantity-unit').value = prefill.quantity_unit;
                }
                if (prefill.direction) {
                    const d = form.querySelector(`input[name="tracker_direction"][value="${prefill.direction}"]`);
                    if (d) d.checked = true;
                }
                if (prefill.pattern_notices_enabled !== undefined) {
                    document.getElementById('tracker-pattern-notices').checked = Boolean(prefill.pattern_notices_enabled);
                }
            } else {
                nameInput.value = '';
                form.querySelector(`input[name="tracker_category"][value="stress_sign"]`).checked = true;
                form.querySelector(`input[name="tracker_method"][value="yes_no"]`).checked = true;
                document.getElementById('tracker-scale-min').value = 1;
                document.getElementById('tracker-scale-max').value = 5;
                document.getElementById('tracker-scale-min-label').value = 'Very low';
                document.getElementById('tracker-scale-max-label').value = 'Very high';
                document.getElementById('tracker-quantity-unit').value = '';
                form.querySelector(`input[name="tracker_direction"][value="higher_concerning"]`).checked = true;
                document.getElementById('tracker-pattern-notices').checked = true;
            }
        }

        onCategoryChanged();
        onMethodChanged();

        modal.classList.remove('hidden');
        nameInput.focus();
    }

    function renderNoteLinkingSelector(selectedIds = []) {
        const container = document.getElementById('tracker-note-links-container');
        if (!container) return;

        const noteItems = (window.TempoRecoveryNote && typeof window.TempoRecoveryNote.getItems === 'function')
            ? window.TempoRecoveryNote.getItems()
            : [];

        if (noteItems.length === 0) {
            container.innerHTML = `
                <p class="text-xs text-stone-400 italic">No Recovery Note items written yet. Write items in your Recovery Note to link them here.</p>
            `;
            return;
        }

        const idSet = new Set(selectedIds || []);
        container.innerHTML = noteItems.map(item => {
            const isChecked = idSet.has(item.id);
            return `
                <label class="flex items-start space-x-2 text-xs text-[#202124] p-1.5 rounded-lg hover:bg-white cursor-pointer transition">
                    <input type="checkbox" name="tracker_linked_note" value="${item.id}" ${isChecked ? 'checked' : ''}
                           onchange="window.TempoRecoverySelfCheck.onNoteLinkChanged(this)"
                           class="mt-0.5 rounded text-[#166545] focus:ring-[#166545]">
                    <span class="leading-tight select-none">${escapeHTML(item.text)}</span>
                </label>
            `;
        }).join('');
    }

    function onNoteLinkChanged(checkbox) {
        const checked = document.querySelectorAll('input[name="tracker_linked_note"]:checked');
        if (checked.length > 3) {
            checkbox.checked = false;
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("You can link up to 3 Recovery Note reminders.");
            }
        }
    }

    function closeTrackerModal() {
        const modal = document.getElementById('modal-selfcheck-tracker-edit');
        if (modal) modal.classList.add('hidden');
    }

    function onCategoryChanged() {
        const form = document.getElementById('form-selfcheck-tracker');
        if (!form) return;
        const cat = form.querySelector('input[name="tracker_category"]:checked')?.value;
        const patternBox = document.getElementById('tracker-config-patterns');
        if (patternBox) {
            patternBox.style.display = (cat === 'stress_sign') ? 'block' : 'none';
        }
    }

    function onMethodChanged() {
        const form = document.getElementById('form-selfcheck-tracker');
        if (!form) return;
        const method = form.querySelector('input[name="tracker_method"]:checked')?.value;
        const scaleBox = document.getElementById('tracker-config-scale');
        const quantityBox = document.getElementById('tracker-config-quantity');
        const directionBox = document.getElementById('tracker-config-direction');

        if (scaleBox) scaleBox.classList.toggle('hidden', method !== 'scale');
        if (quantityBox) quantityBox.classList.toggle('hidden', method !== 'quantity');
        if (directionBox) directionBox.classList.toggle('hidden', method !== 'scale' && method !== 'percentage');
    }

    function handleTrackerFormSubmit(event) {
        event.preventDefault();
        const form = document.getElementById('form-selfcheck-tracker');
        if (!form) return;

        const id = document.getElementById('tracker-edit-id').value;
        const name = document.getElementById('tracker-input-name').value.trim();
        const category = form.querySelector('input[name="tracker_category"]:checked')?.value || 'stress_sign';
        const check_method = form.querySelector('input[name="tracker_method"]:checked')?.value || 'yes_no';
        const direction = form.querySelector('input[name="tracker_direction"]:checked')?.value || 'neutral';
        const pattern_notices_enabled = document.getElementById('tracker-pattern-notices')?.checked || false;

        const linkedBoxes = form.querySelectorAll('input[name="tracker_linked_note"]:checked');
        const linked_note_item_ids = Array.from(linkedBoxes).map(cb => cb.value);

        const scale_min = Number(document.getElementById('tracker-scale-min').value) || 1;
        const scale_max = Number(document.getElementById('tracker-scale-max').value) || 5;
        const scale_min_label = document.getElementById('tracker-scale-min-label').value.trim() || 'Very low';
        const scale_max_label = document.getElementById('tracker-scale-max-label').value.trim() || 'Very high';
        const quantity_unit = document.getElementById('tracker-quantity-unit').value.trim();

        const payload = {
            name,
            category,
            check_method,
            direction,
            pattern_notices_enabled: category === 'stress_sign' ? pattern_notices_enabled : false,
            linked_note_item_ids,
            scale_min,
            scale_max,
            scale_min_label,
            scale_max_label,
            quantity_unit
        };

        let savedTracker;
        if (id) {
            savedTracker = updateTracker(id, payload);
        } else {
            savedTracker = createTracker(payload);
        }

        closeTrackerModal();
        renderManageView();

        if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.onTrackerSaved === 'function') {
            window.TempoRecoverySetup.onTrackerSaved(savedTracker);
        }

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(id ? "Tracker updated." : "Tracker added.");
        }
    }

    // =========================================================================
    // MODAL 3: DAILY SELF-CHECK CONTROLLER
    // =========================================================================

    // Current in-memory draft for the active daily check-in modal
    let activeDailyDraft = null;

    function openDailyCheckin(isEditMode = false) {
        if (!window.TempoAuth || !window.TempoAuth.getCurrentUser()) {
            if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                window.TempoMode.openStrack('checkin', { isEdit: isEditMode });
            }
            return;
        }
        ensureModalsMounted();
        const activeTrackers = getActiveTrackers();
        if (activeTrackers.length === 0) {
            // No active trackers -> open manage/setup
            openManage();
            return;
        }

        // Cleanly close View Today modal so it does not sit behind or cover the daily checkin modal
        closeViewToday();
        closeManage();

        const todayCheckin = getTodayCheckin();
        const existingObs = todayCheckin ? getObservationsForCheckin(todayCheckin.id) : [];
        const existingObsMap = new Map(existingObs.map(o => [o.tracker_id, o]));

        // Build draft observations for active trackers
        const draftObs = {};
        activeTrackers.forEach(t => {
            const existing = existingObsMap.get(t.id);
            if (existing) {
                draftObs[t.id] = {
                    id: existing.id,
                    tracker_id: t.id,
                    status: existing.status, // 'unanswered', 'skipped', 'answered'
                    value: existing.value,
                    note: existing.note || '',
                    noteExpanded: Boolean(existing.note)
                };
            } else {
                draftObs[t.id] = {
                    id: null,
                    tracker_id: t.id,
                    status: 'unanswered',
                    value: null,
                    note: '',
                    noteExpanded: false
                };
            }
        });

        activeDailyDraft = {
            isEditMode,
            checkinId: todayCheckin ? todayCheckin.id : null,
            overallNote: todayCheckin ? (todayCheckin.overall_note || '') : '',
            observations: draftObs
        };

        renderDailyForm();

        const modal = document.getElementById('modal-selfcheck-daily');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
        }
    }

    function closeDailyCheckin() {
        const modal = document.getElementById('modal-selfcheck-daily');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
        activeDailyDraft = null;
    }

    function renderDailyForm() {
        if (!activeDailyDraft) return;
        const container = document.getElementById('selfcheck-daily-trackers-container');
        const overallInput = document.getElementById('selfcheck-overall-note');
        if (!container) return;

        const titleEl = document.getElementById('selfcheck-daily-modal-title');
        const subtitleEl = document.getElementById('selfcheck-daily-modal-subtitle');
        if (titleEl) {
            titleEl.textContent = activeDailyDraft.isEditMode ? "Edit today's check-in" : "How have things been today?";
        }
        if (subtitleEl) {
            subtitleEl.textContent = activeDailyDraft.isEditMode 
                ? "Update your entries for today. Changes will be saved to your tracking history."
                : "Check in with whatever feels useful. You don't have to answer everything.";
        }

        if (overallInput) {
            overallInput.value = activeDailyDraft.overallNote || '';
        }

        const activeTrackers = getActiveTrackers();
        const groups = [
            { category: CATEGORIES.STRESS_SIGN, meta: CATEGORY_META.stress_sign },
            { category: CATEGORIES.SUPPORTIVE, meta: CATEGORY_META.supportive },
            { category: CATEGORIES.NEUTRAL, meta: CATEGORY_META.neutral }
        ];

        let html = '';
        groups.forEach(g => {
            const groupTrackers = activeTrackers.filter(t => t.category === g.category);
            if (groupTrackers.length === 0) return;

            html += `
                <div class="space-y-3">
                    <div class="flex items-center space-x-1.5 text-xs font-bold text-[#484541] uppercase tracking-wide">
                        <span>${g.meta.icon}</span>
                        <span>${escapeHTML(g.meta.pluralLabel)}</span>
                    </div>
                    <div class="space-y-2.5">
                        ${groupTrackers.map(t => renderDailyTrackerCard(t, activeDailyDraft.observations[t.id])).join('')}
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
        updateDailyFinishButton();
    }

    function renderDailyTrackerCard(tracker, obsState) {
        const status = obsState.status; // 'unanswered', 'skipped', 'answered'
        const val = obsState.value;
        const note = obsState.note || '';
        const noteExpanded = obsState.noteExpanded || Boolean(note);
        const dotColor = tracker.type_color || (tracker.category === 'stress_sign' ? '#D48366' : (tracker.category === 'supportive' ? '#166545' : '#1E40AF'));

        let controlsHtml = '';

        if (tracker.check_method === CHECK_METHODS.YES_NO || tracker.check_method === 'options') {
            let opts = tracker.options;
            if (!opts || !Array.isArray(opts) || opts.length === 0) {
                opts = tracker.check_method === 'options' ? ['Good', 'Not good'] : ['Yes', 'No'];
            }
            const isSkip = status === 'skipped';
            const optButtons = opts.map(opt => {
                const isSelected = status === 'answered' && (
                    val === opt || 
                    (opt === 'Yes' && (val === true || val === 'yes' || val === 'Yes')) || 
                    (opt === 'No' && (val === false || val === 'no' || val === 'No'))
                );
                return `
                    <button type="button" onclick="window.TempoRecoverySelfCheck.setDailyOption('${tracker.id}', '${escapeHTML(opt)}')"
                            class="px-4 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer border ${isSelected ? 'bg-[#7B9688] text-white border-[#7B9688] shadow-2xs' : 'bg-white text-[#37352F] border-stone-300/80 hover:border-[#7B9688] hover:bg-[#F4F7F5] shadow-2xs'}">
                        ${escapeHTML(opt)}
                    </button>
                `;
            }).join('');

            controlsHtml = `
                <div class="flex items-center flex-wrap gap-2">
                    ${optButtons}
                    <button type="button" onclick="window.TempoRecoverySelfCheck.setDailySkip('${tracker.id}')"
                            class="px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer border ${isSkip ? 'bg-stone-200 text-stone-800 border-stone-400 font-bold' : 'bg-transparent text-stone-400 hover:text-stone-700 border-transparent'}">
                        Skip
                    </button>
                </div>
            `;
        } else if (tracker.check_method === CHECK_METHODS.SCALE) {
            const min = tracker.scale_min || 1;
            const max = tracker.scale_max || (tracker.scale_range === '1-10' ? 10 : 5);
            const isSkip = status === 'skipped';

            const buttons = [];
            for (let i = min; i <= max; i++) {
                const isSelected = status === 'answered' && Number(val) === i;
                buttons.push(`
                    <button type="button" onclick="window.TempoRecoverySelfCheck.setDailyScale('${tracker.id}', ${i})"
                            class="w-8 h-8 sm:w-9 sm:h-9 rounded-xl text-xs font-bold transition cursor-pointer border flex items-center justify-center shadow-2xs ${isSelected ? 'bg-[#7B9688] text-white border-[#7B9688]' : 'bg-white text-[#37352F] border-stone-300/80 hover:border-[#7B9688] hover:bg-[#F4F7F5]'}">
                        ${i}
                    </button>
                `);
            }

            controlsHtml = `
                <div class="space-y-1.5">
                    <div class="flex items-center flex-wrap gap-1.5">
                        <div class="flex items-center space-x-1.5 overflow-x-auto pb-0.5">${buttons.join('')}</div>
                        <button type="button" onclick="window.TempoRecoverySelfCheck.setDailySkip('${tracker.id}')"
                                class="px-2.5 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer border ${isSkip ? 'bg-stone-200 text-stone-800 border-stone-400 font-bold' : 'bg-transparent text-stone-400 hover:text-stone-700 border-transparent'}">
                            Skip
                        </button>
                    </div>
                    <div class="flex justify-between text-[10px] text-stone-400 max-w-[200px] px-1 font-medium">
                        <span>${escapeHTML(tracker.scale_min_label || 'Min')}</span>
                        <span>${escapeHTML(tracker.scale_max_label || 'Max')}</span>
                    </div>
                </div>
            `;
        } else if (tracker.check_method === CHECK_METHODS.PERCENTAGE) {
            const isSkip = status === 'skipped';
            const isAnswered = status === 'answered' && val !== null;
            const displayVal = isAnswered ? `${val}%` : '-- %';

            controlsHtml = `
                <div class="space-y-1.5">
                    <div class="flex items-center space-x-3">
                        <input type="range" min="0" max="100" step="1" value="${isAnswered ? val : 50}"
                               oninput="window.TempoRecoverySelfCheck.setDailyPercentage('${tracker.id}', this.value)"
                               class="w-40 sm:w-48 accent-[#4A6B5D] cursor-pointer">
                        <span class="text-xs font-extrabold text-[#37352F] w-12 text-center py-1 px-1.5 rounded-lg bg-stone-100 border border-stone-200/80">${displayVal}</span>
                        <button type="button" onclick="window.TempoRecoverySelfCheck.setDailySkip('${tracker.id}')"
                                class="px-2.5 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer border ${isSkip ? 'bg-stone-200 text-stone-800 border-stone-400 font-bold' : 'bg-transparent text-stone-400 hover:text-stone-700 border-transparent'}">
                            Skip
                        </button>
                    </div>
                    ${!isAnswered && !isSkip ? '<p class="text-[10px] text-stone-400 italic font-medium">Drag slider to set percentage</p>' : ''}
                </div>
            `;
        } else if (tracker.check_method === CHECK_METHODS.QUANTITY) {
            const isSkip = status === 'skipped';
            const isAnswered = status === 'answered' && val !== null;
            const unit = tracker.quantity_unit || 'min';

            controlsHtml = `
                <div class="flex items-center flex-wrap gap-2">
                    <input type="number" min="0" step="any" placeholder="Enter quantity" value="${isAnswered ? val : ''}"
                           oninput="window.TempoRecoverySelfCheck.setDailyQuantity('${tracker.id}', this.value)"
                           class="w-32 px-3 py-1.5 rounded-xl border border-stone-300 focus:outline-none focus:border-[#4A6B5D] text-xs font-semibold text-[#37352F] bg-white shadow-2xs">
                    <span class="text-xs font-bold text-[#5B5550]">${escapeHTML(unit)}</span>
                    <button type="button" onclick="window.TempoRecoverySelfCheck.setDailySkip('${tracker.id}')"
                            class="px-2.5 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer border ${isSkip ? 'bg-stone-200 text-stone-800 border-stone-400 font-bold' : 'bg-transparent text-stone-400 hover:text-stone-700 border-transparent'}">
                        Skip
                    </button>
                </div>
            `;
        }

        // Note UI
        let noteHtml = '';
        if (noteExpanded) {
            noteHtml = `
                <div class="pt-1.5">
                    <input type="text" placeholder="Add a note for this..." value="${escapeHTML(note)}"
                           oninput="window.TempoRecoverySelfCheck.setDailyNote('${tracker.id}', this.value)"
                           class="w-full px-3 py-1.5 rounded-xl border border-stone-300 focus:outline-none focus:border-[#4A6B5D] text-xs text-[#37352F] bg-white shadow-2xs">
                </div>
            `;
        } else {
            noteHtml = `
                <button type="button" onclick="window.TempoRecoverySelfCheck.toggleDailyNoteExpanded('${tracker.id}')"
                        class="text-[11px] font-semibold text-stone-500 hover:text-[#4A6B5D] transition cursor-pointer">
                    + Add a note
                </button>
            `;
        }

        return `
            <div class="p-4 rounded-2xl border border-stone-200/80 bg-white space-y-3 shadow-2xs">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2 text-sm font-bold text-[#37352F] truncate min-w-0">
                        <span class="w-2.5 h-2.5 rounded-full inline-block shrink-0" style="background-color: ${dotColor};"></span>
                        <span class="truncate">${escapeHTML(tracker.name)}</span>
                    </div>
                    ${status === 'answered' ? '<span class="text-[10px] font-bold text-[#166545] bg-[#EDF7F1] px-2.5 py-0.5 rounded-full border border-[#CDE9DA]">Answered</span>' : (status === 'skipped' ? '<span class="text-[10px] font-semibold text-[#8C8681] bg-stone-100 px-2.5 py-0.5 rounded-full">Skipped</span>' : '<span class="text-[10px] font-medium text-stone-400">Unanswered</span>')}
                </div>
                ${controlsHtml}
                ${noteHtml}
            </div>
        `;
    }

    function setDailyYesNo(trackerId, boolVal) {
        if (!activeDailyDraft || !activeDailyDraft.observations[trackerId]) return;
        const obs = activeDailyDraft.observations[trackerId];
        if (obs.status === 'answered' && obs.value === boolVal) {
            // Deselect -> back to unanswered
            obs.status = 'unanswered';
            obs.value = null;
        } else {
            obs.status = 'answered';
            obs.value = boolVal;
        }
        renderDailyForm();
    }

    function setDailyScale(trackerId, numVal) {
        if (!activeDailyDraft || !activeDailyDraft.observations[trackerId]) return;
        const obs = activeDailyDraft.observations[trackerId];
        if (obs.status === 'answered' && Number(obs.value) === numVal) {
            // Deselect -> back to unanswered
            obs.status = 'unanswered';
            obs.value = null;
        } else {
            obs.status = 'answered';
            obs.value = numVal;
        }
        renderDailyForm();
    }

    function setDailyPercentage(trackerId, strVal) {
        if (!activeDailyDraft || !activeDailyDraft.observations[trackerId]) return;
        const obs = activeDailyDraft.observations[trackerId];
        obs.status = 'answered';
        obs.value = Number(strVal);
        renderDailyForm();
    }

    function setDailyQuantity(trackerId, strVal) {
        if (!activeDailyDraft || !activeDailyDraft.observations[trackerId]) return;
        const obs = activeDailyDraft.observations[trackerId];
        if (strVal === '' || strVal === null) {
            obs.status = 'unanswered';
            obs.value = null;
        } else {
            obs.status = 'answered';
            obs.value = Number(strVal);
        }
        updateDailyFinishButton();
    }

    function setDailySkip(trackerId) {
        if (!activeDailyDraft || !activeDailyDraft.observations[trackerId]) return;
        const obs = activeDailyDraft.observations[trackerId];
        if (obs.status === 'skipped') {
            obs.status = 'unanswered';
            obs.value = null;
        } else {
            obs.status = 'skipped';
            obs.value = null;
        }
        renderDailyForm();
    }

    function toggleDailyNoteExpanded(trackerId) {
        if (!activeDailyDraft || !activeDailyDraft.observations[trackerId]) return;
        activeDailyDraft.observations[trackerId].noteExpanded = true;
        renderDailyForm();
    }

    function setDailyNote(trackerId, text) {
        if (!activeDailyDraft || !activeDailyDraft.observations[trackerId]) return;
        activeDailyDraft.observations[trackerId].note = text;
    }

    function setDailyOption(trackerId, optionVal) {
        if (!activeDailyDraft || !activeDailyDraft.observations[trackerId]) return;
        const obs = activeDailyDraft.observations[trackerId];
        const trk = getTrackerById(trackerId);
        const isBool = trk && trk.check_method === CHECK_METHODS.YES_NO;
        const targetVal = isBool ? (optionVal === 'Yes' || optionVal === true) : optionVal;

        if (obs.status === 'answered' && (obs.value === targetVal || (isBool && Boolean(obs.value) === Boolean(targetVal)))) {
            obs.status = 'unanswered';
            obs.value = null;
        } else {
            obs.status = 'answered';
            obs.value = targetVal;
        }
        renderDailyForm();
    }

    function updateDailyFinishButton() {
        if (!activeDailyDraft) return;
        const btnTextEl = document.getElementById('btn-selfcheck-finish-text');
        if (!btnTextEl) return;

        const activeTrackers = getActiveTrackers();
        const obsList = Object.values(activeDailyDraft.observations);
        const answeredCount = obsList.filter(o => o.status === 'answered').length;
        const actionWord = activeDailyDraft.isEditMode ? "Save changes" : "Finish check-in";

        if (answeredCount > 0) {
            btnTextEl.textContent = `${actionWord} · ${answeredCount} of ${activeTrackers.length} answered`;
        } else {
            btnTextEl.textContent = actionWord;
        }
    }

    function finishDailyCheckin() {
        if (!activeDailyDraft) return;
        const overallInput = document.getElementById('selfcheck-overall-note');
        const overallNote = overallInput ? overallInput.value.trim() : '';

        const observationsToSave = Object.values(activeDailyDraft.observations);

        try {
            saveTodayCheckin({
                observations: observationsToSave,
                overall_note: overallNote
            });

            closeDailyCheckin();
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("✓ Check-in saved for today.");
            }
            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.onDailyCheckinFinished === 'function') {
                window.TempoRecoverySetup.onDailyCheckinFinished();
            }

            if (window.TempoAlertSystem && typeof window.TempoAlertSystem.evaluateAnsweredTrackers === 'function') {
                const answeredTrackerIds = observationsToSave.filter(o => o.status === 'answered').map(o => o.tracker_id);
                window.TempoAlertSystem.evaluateAnsweredTrackers(answeredTrackerIds);
            }
        } catch (e) {
            console.error("Failed to save check-in:", e);
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Could not save check-in. Please try again.");
            }
        }
    }

    // =========================================================================
    // MODAL 4: VIEW TODAY'S CHECK-IN CONTROLLER
    // =========================================================================

    function openViewToday() {
        if (!window.TempoAuth || !window.TempoAuth.getCurrentUser()) {
            if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                window.TempoMode.openStrack('view');
            }
            return;
        }
        ensureModalsMounted();
        const todayCheckin = getTodayCheckin();
        const activeTrackers = getActiveTrackers();
        const modal = document.getElementById('modal-selfcheck-view');
        const summaryEl = document.getElementById('selfcheck-view-summary');
        const contentEl = document.getElementById('selfcheck-view-content');
        const overallBox = document.getElementById('selfcheck-view-overall-note');
        const overallText = document.getElementById('selfcheck-view-overall-text');

        if (!modal || !contentEl) return;

        const observations = todayCheckin ? getObservationsForCheckin(todayCheckin.id) : [];
        const obsMap = new Map(observations.map(o => [o.tracker_id, o]));
        const answeredCount = observations.filter(o => o.status === 'answered').length;

        if (summaryEl) {
            summaryEl.textContent = `You checked in on ${answeredCount} of ${activeTrackers.length} things today.`;
        }

        if (todayCheckin && todayCheckin.overall_note) {
            overallBox.classList.remove('hidden');
            overallText.textContent = `"${todayCheckin.overall_note}"`;
        } else {
            overallBox.classList.add('hidden');
        }

        let html = '';
        activeTrackers.forEach(t => {
            const obs = obsMap.get(t.id);
            const status = obs ? obs.status : 'unanswered';
            let valueDisplay = '';

            if (status === 'answered') {
                if (t.check_method === 'yes_no') {
                    valueDisplay = `<span class="font-bold text-[#166545]">${obs.value ? 'Yes' : 'No'}</span>`;
                } else if (t.check_method === 'scale') {
                    valueDisplay = `<span class="font-bold text-[#166545]">${obs.value} of ${t.scale_max || 5}</span>`;
                } else if (t.check_method === 'percentage') {
                    valueDisplay = `<span class="font-bold text-[#166545]">${obs.value}%</span>`;
                } else if (t.check_method === 'quantity') {
                    valueDisplay = `<span class="font-bold text-[#166545]">${obs.value} ${escapeHTML(t.quantity_unit || '')}</span>`;
                } else {
                    valueDisplay = `<span class="font-bold text-[#166545]">${escapeHTML(String(obs.value))}</span>`;
                }
            } else if (status === 'skipped') {
                valueDisplay = `<span class="text-stone-400 italic">Skipped today</span>`;
            } else {
                valueDisplay = `<span class="text-stone-400 italic">Not answered</span>`;
            }

            const noteHtml = (obs && obs.note) ? `<p class="text-[11px] text-stone-500 italic pt-1">Note: "${escapeHTML(obs.note)}"</p>` : '';

            html += `
                <div class="p-3.5 rounded-2xl border border-stone-200 bg-stone-50/50 flex flex-col space-y-1">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-[#202124]">${escapeHTML(t.name)}</span>
                        <div class="text-xs">${valueDisplay}</div>
                    </div>
                    ${noteHtml}
                </div>
            `;
        });

        contentEl.innerHTML = html;
        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    function closeViewToday() {
        const modal = document.getElementById('modal-selfcheck-view');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    // =========================================================================
    // ACTION DISPATCHER (WIRED TO mode.js)
    // =========================================================================

    function handleAction(action) {
        if (action === 'checkin') {
            openDailyCheckin(false);
        } else if (action === 'manage') {
            openManage();
        } else if (action === 'view') {
            openViewToday();
        } else if (action === 'edit') {
            openDailyCheckin(true);
        } else if (action === 'history') {
            if (window.TempoSelfCheckHistory && typeof window.TempoSelfCheckHistory.open === 'function') {
                window.TempoSelfCheckHistory.open();
            }
        }
    }

    function openSetup() {
        if (!window.TempoAuth || !window.TempoAuth.getCurrentUser()) {
            if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                window.TempoMode.openStrack('setup');
            }
            return;
        }
        openManage();
    }

    // =========================================================================
    // UTILITIES
    // =========================================================================

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
    // INITIALIZATION & GLOBAL EXPORT
    // =========================================================================

    function init() {
        ensureModalsMounted();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.TempoRecoverySelfCheck = {
        init,
        CATEGORIES,
        CHECK_METHODS,
        // Trackers API
        getTrackers,
        getActiveTrackers,
        getTrackerById,
        createTracker,
        updateTracker,
        archiveTracker,
        // Check-ins API
        getDailyCheckins,
        getTodayCheckin,
        getObservationsForCheckin,
        saveTodayCheckin,
        // Dates
        getTodayDateStr,
        shiftDateStr,
        // Streak & History
        hasValidCheckinForDate,
        calculateStreak,
        get7DayHistory,
        // Recovery Home State Provider
        getState,
        getRecentlyState,
        // Handlers & Modal Openers
        handleAction,
        openSetup,
        openManage,
        closeManage,
        openTrackerModal,
        closeTrackerModal,
        onCategoryChanged,
        onMethodChanged,
        onNoteLinkChanged,
        handleTrackerFormSubmit,
        handleArchiveTracker,
        useSuggestion,
        // Setup Management & Configuration Versions
        getSetups,
        getActiveSetup,
        archiveCurrentSetup,
        createActiveSetup,
        updateActiveSetup,
        getTrackerConfigForDate,
        openDailyCheckin,
        closeDailyCheckin,
        setDailyYesNo,
        setDailyOption,
        setDailyScale,
        setDailyPercentage,
        setDailyQuantity,
        setDailySkip,
        toggleDailyNoteExpanded,
        setDailyNote,
        finishDailyCheckin,
        openViewToday,
        closeViewToday
    };

})();
