/**
 * Tempo Unclear Mode (Umode) Phase 1: Entry + Clarity Check-in
 * 
 * Unclear Mode is a secondary, transitional Tempo mode designed for:
 * "Something feels off, but I don't clearly know why or what I need."
 * 
 * Lifecycle:
 * LOOK AROUND (Stage 1: What's on my mind)
 * -> NARROW DOWN (Stage 2: What feels heaviest & feelings)
 * -> NOTICE IMPACT (Stage 3: What have I noticed & impact level)
 * -> IDENTIFY WHAT I NEED (Stage 4: Broad needs & primary need)
 * -> COMPLETION (Stage 5: Things are a little clearer)
 * 
 * Core Product Principle:
 * "Things are a little clearer than when I started."
 * Not a clinical assessment, no diagnosis, no scoring, no Unclear plan.
 */

window.TempoUnclearMode = (function() {
    'use strict';

    // =========================================================================
    // CONSTANTS & VOCABULARIES
    // =========================================================================

    const LIFE_AREAS = [
        {
            key: 'study',
            title: 'Study',
            icon: '📚',
            items: [
                'Deadlines / assignments',
                'Grades / academic results',
                'Projects / teamwork',
                'Presentations / exams',
                'Struggling to keep up'
            ]
        },
        {
            key: 'work',
            title: 'Work & activities',
            icon: '💼',
            items: [
                'Work / internship',
                'Clubs / other commitments',
                'Too many things at once',
                'Not enough time for myself'
            ]
        },
        {
            key: 'future',
            title: 'Myself & the future',
            icon: '💭',
            items: [
                'Expectations I have for myself',
                "Worrying I'm not good enough",
                "Unsure whether I'm going in the right direction",
                'Worrying about the future'
            ]
        },
        {
            key: 'relationships',
            title: 'Relationships',
            icon: '🤝',
            items: [
                'Family',
                'Friends',
                'Romantic relationships',
                'Feeling lonely / disconnected'
            ]
        },
        {
            key: 'life',
            title: 'Life',
            icon: '🌿',
            items: [
                'Finances',
                'Health / daily routine',
                'Recent changes',
                'Not enough time to rest'
            ]
        }
    ];

    const FEELINGS = [
        'Anxious',
        'Tired',
        'Sad',
        'Irritable',
        'Pressured',
        'Hard to focus'
    ];

    const NOTICED_CATEGORIES = [
        {
            key: 'eating_rest',
            title: 'Eating & rest',
            icon: '🥣',
            items: [
                'Harder to sleep / staying up later than usual',
                'Sleeping more but still tired',
                'Eating more or less than usual'
            ]
        },
        {
            key: 'study_work',
            title: 'Study & work',
            icon: '📚',
            items: [
                'Sitting down but struggling to start',
                'Harder to focus',
                'Procrastinating more than usual'
            ]
        },
        {
            key: 'emotions',
            title: 'Emotions',
            icon: '💭',
            items: [
                'More irritable than usual',
                'Worrying / overthinking more',
                'Feeling low more often'
            ]
        },
        {
            key: 'everyday_life',
            title: 'Everyday life',
            icon: '🌿',
            items: [
                'Less interested in seeing or talking to people',
                'Less interested in things I usually enjoy',
                'Letting some everyday things slide'
            ]
        }
    ];

    const IMPACT_OPTIONS = [
        { key: 'little', label: 'A little' },
        { key: 'quite_a_bit', label: 'Quite a bit' },
        { key: 'a_lot', label: 'A lot' }
    ];

    const BROAD_NEEDS = [
        {
            key: 'room',
            title: 'I need some room',
            shortLabel: 'Some room',
            icon: '🌿',
            badgeBg: '#EDF7F1',
            badgeColor: '#166545',
            badgeBorder: '#CDE9DA',
            items: [
                'Pause work for a while',
                'Sleep / rest',
                'Do something that helps me unwind'
            ]
        },
        {
            key: 'handle',
            title: 'I need to deal with something',
            shortLabel: 'Deal with something',
            icon: '🧩',
            badgeBg: '#FFF4EC',
            badgeColor: '#FF6B2C',
            badgeBorder: '#FFD2BA',
            items: [
                "Handle something that's worrying me",
                'Reduce or move something if possible',
                'Break down something that feels messy'
            ]
        },
        {
            key: 'support',
            title: 'I need some support',
            shortLabel: 'Some support',
            icon: '🤝',
            badgeBg: '#EDF5FF',
            badgeColor: '#1D4ED8',
            badgeBorder: '#BFDBFE',
            items: [
                'Talk to someone I trust',
                'Ask someone for help with something',
                'I mostly need someone to listen'
            ]
        },
        {
            key: 'self_directed',
            title: 'I think I know what I want to do',
            shortLabel: 'I know what to do',
            icon: '🎯',
            badgeBg: '#FAF5FF',
            badgeColor: '#7E22CE',
            badgeBorder: '#E9D5FF',
            items: [
                'I understand things a little better and want to take it from here.'
            ]
        }
    ];

    // =========================================================================
    // STATE & DRAFT PERSISTENCE
    // =========================================================================

    let currentDraft = null;
    let viewState = 'home'; // 'home' | 'checkin'
    let activeCustomInputs = {}; // Category-keyed tracking for open input boxes

    function getUserId() {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') {
            const uid = window.TempoAuth.getCurrentUserId();
            if (uid) return uid;
        }
        return 'local_user';
    }

    function getStorageKey(type) {
        const uid = getUserId();
        return `tempo_unclear_${type}_${uid}`;
    }

    function getVersionsKey() {
        const uid = getUserId();
        return `tempo_ucheck_versions_${uid}`;
    }

    function loadAllVersions() {
        try {
            const key = getVersionsKey();
            const raw = localStorage.getItem(key);
            if (raw) {
                const parsed = JSON.parse(raw);
                if (Array.isArray(parsed)) return parsed;
            }
        } catch (e) {
            console.warn('[TempoUnclearMode] Error loading versions:', e);
        }

        // Migrate from history and draft if versions array is not yet present
        const versions = [];
        const hist = loadCompletedHistory();
        if (Array.isArray(hist) && hist.length > 0) {
            hist.forEach((h, idx) => {
                if (!h.version) h.version = hist.length - idx;
                versions.push(h);
            });
        }
        try {
            const uid = getUserId();
            const rawDraft = localStorage.getItem(getStorageKey('draft')) || localStorage.getItem('tempo_unclear_draft');
            if (rawDraft) {
                const parsed = JSON.parse(rawDraft);
                if (parsed && parsed.status === 'in_progress' && !versions.some(v => v.id === parsed.id)) {
                    parsed.version = (versions[0]?.version || 0) + 1;
                    versions.unshift(parsed);
                }
            }
        } catch (e) {}

        return versions;
    }

    function saveAllVersions(versions) {
        try {
            const key = getVersionsKey();
            localStorage.setItem(key, JSON.stringify(versions.slice(0, 50)));
        } catch (e) {
            console.warn('[TempoUnclearMode] Error saving versions:', e);
        }
    }

    function getIncompleteVersions() {
        return loadAllVersions().filter(v => v && v.status === 'in_progress');
    }

    function getCompletedVersions() {
        return loadAllVersions().filter(v => v && v.status === 'completed');
    }

    function loadDraft() {
        if (currentDraft && currentDraft.status === 'in_progress') {
            return currentDraft;
        }
        const incomplete = getIncompleteVersions();
        if (incomplete.length > 0) {
            currentDraft = incomplete[0];
            return currentDraft;
        }
        try {
            const key = getStorageKey('draft');
            const raw = localStorage.getItem(key) || localStorage.getItem('tempo_unclear_draft');
            if (raw) {
                const parsed = JSON.parse(raw);
                if (parsed && parsed.status === 'in_progress') {
                    currentDraft = parsed;
                    return currentDraft;
                }
            }
        } catch (e) {}
        currentDraft = null;
        return null;
    }

    function saveDraft() {
        if (!currentDraft) return;
        currentDraft.updated_at = new Date().toISOString();
        const versions = loadAllVersions();
        const idx = versions.findIndex(v => v.id === currentDraft.id);
        if (idx >= 0) {
            versions[idx] = currentDraft;
        } else {
            versions.unshift(currentDraft);
        }
        saveAllVersions(versions);
        try {
            const key = getStorageKey('draft');
            localStorage.setItem(key, JSON.stringify(currentDraft));
        } catch (e) {
            console.warn('[TempoUnclearMode] Error saving draft:', e);
        }
    }

    function clearDraft() {
        currentDraft = null;
        try {
            const key = getStorageKey('draft');
            localStorage.removeItem(key);
            localStorage.removeItem('tempo_unclear_draft');
            const uid = getUserId();
            sessionStorage.removeItem(`tempo_unclear_in_flow_${uid}`);
        } catch (e) {}
    }

    function saveCompletedHistory(checkInRecord) {
        try {
            checkInRecord.status = 'completed';
            checkInRecord.completed_at = checkInRecord.completed_at || new Date().toISOString();

            const versions = loadAllVersions();
            const idx = versions.findIndex(v => v.id === checkInRecord.id);
            if (idx >= 0) {
                versions[idx] = checkInRecord;
            } else {
                versions.unshift(checkInRecord);
            }
            saveAllVersions(versions);

            const key = getStorageKey('history');
            const raw = localStorage.getItem(key);
            const history = raw ? JSON.parse(raw) : [];
            const hIdx = history.findIndex(h => h.id === checkInRecord.id);
            if (hIdx >= 0) {
                history[hIdx] = checkInRecord;
            } else {
                history.unshift(checkInRecord);
            }
            localStorage.setItem(key, JSON.stringify(history.slice(0, 30)));
        } catch (e) {
            console.warn('[TempoUnclearMode] Error saving history:', e);
        }
    }

    function loadCompletedHistory() {
        try {
            const key = getStorageKey('history');
            const raw = localStorage.getItem(key);
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            return [];
        }
    }

    function createNewDraft(versionNum = 1) {
        const uid = getUserId();
        return {
            id: 'uc_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
            user_id: uid,
            version: versionNum,
            parent_version_id: null,
            status: 'in_progress',
            current_stage: 1, // 1 to 5 (5 is completion)
            concerns: [],
            custom_concerns: [], // [{ category, text }]
            top_concerns: [], // max 2 string names
            feelings_by_concern: {}, // { [concernName]: ['Anxious', ...] }
            custom_feelings_by_concern: {}, // { [concernName]: 'string' }
            noticed_changes: [],
            custom_changes: [],
            impact_level: '', // 'little' | 'quite_a_bit' | 'a_lot'
            needs: [], // keys e.g. ['room', 'handle']
            need_details: {}, // { [needKey]: ['sub-item', ...] }
            custom_need: '',
            primary_need: '', // 'room' | 'handle' | 'support' | 'self_directed' | 'custom'
            chosen_direction: '',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            completed_at: null
        };
    }

    // =========================================================================
    // MAIN ENTRY CONTROLLER & ROUTER
    // =========================================================================

    function renderHome() {
        const container = document.getElementById('umode-home-content');
        if (!container) return;

        // Check if session was currently in check-in flow
        const uid = getUserId();
        const isInFlow = sessionStorage.getItem(`tempo_unclear_in_flow_${uid}`) === 'true';

        loadDraft();

        if (isInFlow && currentDraft && currentDraft.status === 'in_progress') {
            viewState = 'checkin';
            renderCheckinFlow(container);
        } else {
            viewState = 'home';
            renderHomeView(container);
        }
    }

    // =========================================================================
    // VIEW 1: UNCLEAR MODE HOME (COMPACT ENTRY SCREEN)
    // =========================================================================

    function renderHomeView(container) {
        // Dynamic greeting name from auth profile or default to Innie
        const profile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
        let userName = 'Innie';
        if (profile) {
            const nameCandidate = profile.preferred_name || profile.display_name || profile.first_name;
            if (nameCandidate && typeof nameCandidate === 'string' && nameCandidate.trim().length >= 1) {
                userName = nameCandidate.trim().charAt(0).toUpperCase() + nameCandidate.trim().slice(1);
            }
        }

        const incompleteDrafts = getIncompleteVersions();
        const hasUnfinishedDraft = incompleteDrafts.length > 0;
        const draft = incompleteDrafts[0] || null;
        const history = loadCompletedHistory();
        const lastCheckin = history.length > 0 ? history[0] : null;

        container.innerHTML = `
            <div id="unclear-home-view" class="space-y-6">
                <!-- Top Navigation Row: Return Home + Unclear Pill + ((SOS)) I don't feel safe -->
                <div class="flex items-center justify-between gap-4 pb-1">
                    <!-- Left: Return Home & Unclear Mode pill -->
                    <div class="flex items-center space-x-3">
                        <button type="button" 
                                onclick="window.TempoUnclearMode.returnToHome()"
                                class="px-5 py-2 rounded-full text-xs sm:text-sm font-bold text-[#5B5550] hover:text-[#202124] bg-white/90 hover:bg-white border border-[#E8D9CF] transition shadow-2xs flex items-center space-x-1.5 cursor-pointer"
                                title="Return Home">
                            <span>←</span>
                            <span>Return Home</span>
                        </button>

                        <div id="home-mode-selector-wrapper" class="relative inline-block text-left">
                            <button id="btn-home-mode-selector" 
                                    type="button" 
                                    onclick="window.TempoMode.toggleModeDropdown(event)" 
                                    class="px-7 py-2 rounded-full text-xs sm:text-sm font-extrabold bg-[#FFF6EF] text-[#C2785C] hover:bg-[#FDEBD0] border border-[#E2B7A0] transition flex items-center space-x-1 shadow-2xs cursor-pointer"
                                    aria-haspopup="true"
                                    aria-expanded="false"
                                    title="Switch Tempo Mode">
                                <span>Unclear</span>
                            </button>
                            <div id="home-mode-selector-dropdown" class="hidden absolute left-0 mt-2 w-72 sm:w-80 bg-white rounded-2xl shadow-xl border border-[#EAE4DF] z-50 overflow-hidden" role="menu"></div>
                        </div>
                    </div>

                    <!-- Right: ((SOS)) I don't feel safe -->
                    <button type="button"
                            onclick="window.TempoEmergencySupport.openSOS()"
                            class="px-5 sm:px-6 py-2 rounded-full text-xs sm:text-sm font-extrabold text-white bg-[#BD3022] hover:bg-[#A9271A] transition shadow-xs flex items-center space-x-2 cursor-pointer"
                            title="I don't feel safe">
                        <span class="tracking-widest font-black">((sos))</span>
                        <span>I don’t feel safe</span>
                    </button>
                </div>

                <!-- Main Content Area: Two-Column Layout -->
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
                    <!-- Left card: Welcome and Tempo Test -->
                    <div data-card="welcome-tempo-test" class="lg:col-span-7 flex flex-col justify-between bg-[#FEFAF4] border border-[#F2ECE4] rounded-[28px] p-6 sm:p-8 md:p-10 shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
                        <div class="space-y-3">
                            <div class="text-xl sm:text-2xl font-extrabold text-[#C2785C] flex items-center space-x-2">
                                <span>👋</span>
                                <span>Hi ${escapeHTML(userName)},</span>
                            </div>
                            <h2 class="font-heading text-2xl sm:text-3xl lg:text-4xl font-extrabold text-[#46413C] tracking-tight leading-tight">
                                Not sure where to start?
                            </h2>
                            <h3 class="font-heading text-2xl sm:text-3xl lg:text-4xl font-extrabold text-[#46413C] tracking-tight leading-tight">
                                Let’s figure it out together.
                            </h3>
                            <p class="italic text-sm sm:text-base text-[#6F6B68] leading-relaxed pt-1">
                                Let’s try a few quick check-ins to understand what you need.
                            </p>
                        </div>

                        <div class="pt-8">
                            <div class="flex flex-wrap items-center gap-3.5">
                                <button type="button"
                                        onclick="window.TempoUnclearMode.startNewCheckIn()"
                                        class="bg-[#829B87] hover:bg-[#728A77] text-white font-bold text-sm sm:text-base px-6 py-3 rounded-2xl shadow-xs transition hover:opacity-95 cursor-pointer">
                                    Do Tempo Test
                                </button>
                                <button type="button"
                                        onclick="window.TempoApp.navigateTo('my-test-results')"
                                        class="bg-white hover:bg-stone-50 border border-[#C5BCB3] hover:border-stone-400 text-[#5B5550] font-bold text-sm sm:text-base px-6 py-3 rounded-2xl shadow-xs transition cursor-pointer">
                                    View my results
                                </button>
                            </div>

                            ${hasUnfinishedDraft ? `
                                <div class="pt-3">
                                    <button type="button" onclick="window.TempoUnclearMode.resumeDraft('${draft.id}')"
                                            class="text-xs font-semibold text-[#FF6B2C] hover:text-[#B83D08] flex items-center space-x-1.5 transition cursor-pointer">
                                        <span>Continue where I left off</span>
                                        <span>→</span>
                                        <span class="text-stone-400 font-normal">(${draft.current_stage} of 4 steps)</span>
                                    </button>
                                </div>
                            ` : (lastCheckin && lastCheckin.completed_at ? `
                                <div class="pt-3 text-[11px] text-stone-400 flex items-center space-x-2">
                                    <span>Last check-in: ${new Date(lastCheckin.completed_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                                    <button type="button" onclick="window.TempoUnclearMode.viewCompletedCheckIn('${lastCheckin.id}')" class="text-stone-500 hover:underline">
                                        View reflection →
                                    </button>
                                </div>
                            ` : '')}
                        </div>
                    </div>

                    <!-- Right card: Explore Mental Health Tests -->
                    <div data-card="explore-assessments" class="lg:col-span-5 flex flex-col justify-between bg-[#829B87] border border-[#728A77] rounded-[28px] p-6 sm:p-8 md:p-10 shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
                        <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-snug mb-6">
                            Explore Mental<br />Health Tests
                        </h2>
                        <div class="space-y-3 w-full">
                            <button type="button"
                                    onclick="window.TempoApp.navigateTo('explore-mental-health-tests', 'depression')"
                                    class="w-full bg-white hover:bg-[#FAF9F5] text-left font-bold text-sm sm:text-base text-[#46413C] hover:text-[#202124] py-3.5 px-5 rounded-2xl shadow-xs transition cursor-pointer block">
                                Depression Assessments
                            </button>
                            <button type="button"
                                    onclick="window.TempoApp.navigateTo('explore-mental-health-tests', 'stress')"
                                    class="w-full bg-white hover:bg-[#FAF9F5] text-left font-bold text-sm sm:text-base text-[#46413C] hover:text-[#202124] py-3.5 px-5 rounded-2xl shadow-xs transition cursor-pointer block">
                                Stress Assessments
                            </button>
                            <button type="button"
                                    onclick="window.TempoApp.navigateTo('explore-mental-health-tests', 'anxiety')"
                                    class="w-full bg-white hover:bg-[#FAF9F5] text-left font-bold text-sm sm:text-base text-[#46413C] hover:text-[#202124] py-3.5 px-5 rounded-2xl shadow-xs transition cursor-pointer block">
                                Anxiety Assessments
                            </button>
                            <button type="button"
                                    onclick="window.TempoApp.navigateTo('explore-mental-health-tests', 'other')"
                                    class="w-full bg-white hover:bg-[#FAF9F5] text-left font-bold text-sm sm:text-base text-[#46413C] hover:text-[#202124] py-3.5 px-5 rounded-2xl shadow-xs transition cursor-pointer block">
                                Other Assessments
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Bottom Tool Cards: Quick Relief, Learn & Solve, Tempo break -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
                    <!-- 1. Quick Relief -->
                    <div data-card="quick-relief"
                         onclick="if (window.TempoStressRelief && window.TempoStressRelief.openModal) { window.TempoStressRelief.openModal('unclear'); } else if (window.TempoTriage && window.TempoTriage.openQuickReliefModal) { window.TempoTriage.openQuickReliefModal(); }"
                         class="bg-[#D9E7E0] border border-[#BACAD0] rounded-[24px] overflow-hidden p-5 sm:p-6 flex items-center justify-between min-h-[160px] shadow-[0_4px_10px_-2px_rgba(75,55,40,0.05),0_10px_20px_-4px_rgba(75,55,40,0.08)] hover:shadow-md transition cursor-pointer group select-none relative"
                         title="Quick Relief">
                        <div class="flex-1 min-w-0 pr-2">
                            <h3 class="text-xl sm:text-2xl font-extrabold text-[#4A6356] mb-1 group-hover:text-[#384F43] transition">
                                Quick Relief
                            </h3>
                            <p class="text-xs sm:text-sm text-[#5C7568] leading-snug">
                                Quick ways to ease stress and feel better.
                            </p>
                        </div>
                        <img src="assets/quick-relief-mascot-transparent.png" alt="Quick Relief Mascot" class="h-20 sm:h-24 w-auto object-contain shrink-0 select-none pointer-events-none group-hover:scale-105 transition-transform" />
                    </div>

                    <!-- 2. Learn & Solve -->
                    <div data-card="learn-solve"
                         onclick="if (window.TempoApp) { window.TempoApp.navigateTo('learn'); } else { window.location.hash = '#learn'; }"
                         class="bg-[#FBEDD9] border border-[#DFCFC0] rounded-[24px] overflow-hidden p-5 sm:p-6 flex items-center justify-between min-h-[160px] shadow-[0_4px_10px_-2px_rgba(75,55,40,0.05),0_10px_20px_-4px_rgba(75,55,40,0.08)] hover:shadow-md transition cursor-pointer group select-none relative"
                         title="Learn & Solve">
                        <div class="flex-1 min-w-0 pr-2">
                            <h3 class="text-xl sm:text-2xl font-extrabold text-[#6D583F] mb-1 group-hover:text-[#5B4833] transition">
                                Learn &amp; Solve
                            </h3>
                            <p class="text-xs sm:text-sm text-[#7D6B54] leading-snug">
                                Tips and tools to help you cope.
                            </p>
                        </div>
                        <img src="assets/learn-solve-mascot.png" alt="Learn & Solve Mascot" class="h-20 sm:h-24 w-auto object-contain shrink-0 select-none pointer-events-none group-hover:scale-105 transition-transform" />
                    </div>

                    <!-- 3. Tempo break -->
                    <div data-card="tempo-break"
                         onclick="if (window.TempoTools && typeof window.TempoTools.openBreak === 'function') { window.TempoTools.openBreak(); } else if (window.TempoFocusZone) { window.TempoFocusZone.openQuickEntry(); }"
                         class="bg-[#D3DFE4] border border-[#BACAD0] rounded-[24px] overflow-hidden p-5 sm:p-6 flex items-center justify-between min-h-[160px] shadow-[0_4px_10px_-2px_rgba(75,55,40,0.05),0_10px_20px_-4px_rgba(75,55,40,0.08)] hover:shadow-md transition cursor-pointer group select-none relative"
                         title="Tempo break">
                        <div class="flex-1 min-w-0 pr-2">
                            <h3 class="text-xl sm:text-2xl font-extrabold text-[#3D4E56] mb-1 group-hover:text-[#2A373E] transition">
                                Tempo break
                            </h3>
                            <p class="text-xs sm:text-sm text-[#5B6C74] leading-snug">
                                Take a break with fun activities to unwind.
                            </p>
                        </div>
                        <img src="assets/tempo-break-mascot.png" alt="Tempo break Mascot" class="h-20 sm:h-24 w-auto object-contain shrink-0 select-none pointer-events-none group-hover:scale-105 transition-transform" />
                    </div>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // VIEW 2: CLARITY CHECK-IN ORCHESTRATOR
    // =========================================================================

    function startNewCheckIn() {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUser === 'function' && !window.TempoAuth.getCurrentUser()) {
            if (window.TempoMode && typeof window.TempoMode.openUcheck === 'function') {
                window.TempoMode.openUcheck({ startNew: true });
                return;
            }
        }

        const versions = loadAllVersions();
        const maxV = versions.reduce((m, v) => Math.max(m, (v && typeof v.version === 'number') ? v.version : 0), 0);
        const newVersionNum = maxV + 1;

        currentDraft = createNewDraft(newVersionNum);
        versions.unshift(currentDraft);
        saveAllVersions(versions);
        saveDraft();

        const uid = getUserId();
        sessionStorage.setItem(`tempo_unclear_in_flow_${uid}`, 'true');
        viewState = 'checkin';
        renderHome();
    }

    function adjustCompletedCheckIn(checkInId) {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUser === 'function' && !window.TempoAuth.getCurrentUser()) {
            if (window.TempoMode && typeof window.TempoMode.openUcheck === 'function') {
                window.TempoMode.openUcheck({ adjustVersionId: checkInId });
                return;
            }
        }

        const versions = loadAllVersions();
        let base = null;
        if (checkInId) {
            base = versions.find(v => v.id === checkInId);
        }
        if (!base) {
            const completed = versions.filter(v => v.status === 'completed');
            base = completed[0] || null;
        }
        if (!base) {
            startNewCheckIn();
            return;
        }

        const maxV = versions.reduce((m, v) => Math.max(m, (v && typeof v.version === 'number') ? v.version : 0), 0);
        const newVersionNum = maxV + 1;

        // V1 -> Adjust -> V2 copied from V1, V1 remains unchanged in versions storage
        const newDraft = {
            id: 'uc_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
            user_id: getUserId(),
            version: newVersionNum,
            parent_version_id: base.id,
            status: 'in_progress',
            current_stage: 1,
            concerns: Array.isArray(base.concerns) ? [...base.concerns] : [],
            custom_concerns: Array.isArray(base.custom_concerns) ? JSON.parse(JSON.stringify(base.custom_concerns)) : [],
            top_concerns: Array.isArray(base.top_concerns) ? [...base.top_concerns] : [],
            feelings_by_concern: base.feelings_by_concern ? JSON.parse(JSON.stringify(base.feelings_by_concern)) : {},
            custom_feelings_by_concern: base.custom_feelings_by_concern ? JSON.parse(JSON.stringify(base.custom_feelings_by_concern)) : {},
            noticed_changes: Array.isArray(base.noticed_changes) ? [...base.noticed_changes] : [],
            custom_changes: Array.isArray(base.custom_changes) ? JSON.parse(JSON.stringify(base.custom_changes)) : [],
            impact_level: base.impact_level || '',
            needs: Array.isArray(base.needs) ? [...base.needs] : [],
            need_details: base.need_details ? JSON.parse(JSON.stringify(base.need_details)) : {},
            custom_need: base.custom_need || '',
            primary_need: base.primary_need || '',
            chosen_direction: '',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            completed_at: null
        };

        versions.unshift(newDraft);
        saveAllVersions(versions);

        currentDraft = newDraft;
        saveDraft();

        const uid = getUserId();
        sessionStorage.setItem(`tempo_unclear_in_flow_${uid}`, 'true');
        viewState = 'checkin';
        renderHome();
    }

    function resumeDraft(checkInId) {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUser === 'function' && !window.TempoAuth.getCurrentUser()) {
            if (window.TempoMode && typeof window.TempoMode.openUcheck === 'function') {
                window.TempoMode.openUcheck({ resumeDraftId: checkInId });
                return;
            }
        }

        const incomplete = getIncompleteVersions();
        if (checkInId) {
            currentDraft = incomplete.find(v => v.id === checkInId) || null;
        }
        if (!currentDraft && incomplete.length > 0) {
            currentDraft = incomplete[0];
        }
        if (!currentDraft) {
            startNewCheckIn();
            return;
        }

        const uid = getUserId();
        sessionStorage.setItem(`tempo_unclear_in_flow_${uid}`, 'true');
        viewState = 'checkin';
        renderHome();
    }

    function resetFlowState() {
        const uid = getUserId();
        try {
            sessionStorage.removeItem(`tempo_unclear_in_flow_${uid}`);
        } catch (e) {}
        viewState = 'home';
    }

    function returnToHome() {
        const uid = getUserId();
        sessionStorage.removeItem(`tempo_unclear_in_flow_${uid}`);
        if (window.TempoMode && typeof window.TempoMode.returnToSourceContext === 'function') {
            window.TempoMode.returnToSourceContext();
        } else if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
            window.TempoMode.setMode('default');
        } else {
            viewState = 'home';
            renderHome();
        }
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('today');
        }
    }

    function goToStage(stageNum) {
        if (!currentDraft) currentDraft = createNewDraft();
        currentDraft.current_stage = stageNum;
        saveDraft();
        renderHome();
    }

    function goBack() {
        if (!currentDraft || currentDraft.current_stage <= 1) {
            const currentMode = window.TempoMode ? window.TempoMode.getMode() : null;
            if (currentMode === 'unclear') {
                const uid = getUserId();
                sessionStorage.removeItem(`tempo_unclear_in_flow_${uid}`);
                viewState = 'home';
                renderHome();
                return;
            }
            returnToHome();
            return;
        }
        goToStage(currentDraft.current_stage - 1);
    }

    function chooseDirection(directionKey, optionalNextStep) {
        if (!currentDraft) loadDraft();
        if (!currentDraft) {
            returnToHome();
            return;
        }

        const nextStepInput = document.getElementById('unclear-next-step-input');
        const nextStepVal = optionalNextStep || (nextStepInput ? nextStepInput.value.trim() : '');

        currentDraft.chosen_direction = directionKey;
        if (nextStepVal) {
            currentDraft.next_step = nextStepVal;
        }
        currentDraft.status = 'completed';
        currentDraft.completed_at = new Date().toISOString();
        saveCompletedHistory(currentDraft);
        clearDraft();

        if (directionKey === 'urgent') {
            if (window.TempoMode && typeof window.TempoMode.transitionContext === 'function') {
                window.TempoMode.transitionContext('emergency');
            } else if (window.TempoMode) {
                window.TempoMode.setMode('emergency');
            }
        } else if (directionKey === 'recovery') {
            if (window.TempoMode && typeof window.TempoMode.transitionContext === 'function') {
                window.TempoMode.transitionContext('recovery');
            } else if (window.TempoMode) {
                window.TempoMode.setMode('recovery');
            }
        } else if (directionKey === 'default') {
            if (window.TempoMode && typeof window.TempoMode.transitionContext === 'function') {
                window.TempoMode.transitionContext(null);
            } else if (window.TempoMode) {
                window.TempoMode.setMode('default');
            }
        } else if (directionKey === 'support') {
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('support');
            }
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast('Connecting to student wellbeing support.');
            }
        } else if (directionKey === 'unclear') {
            const uid = getUserId();
            sessionStorage.removeItem(`tempo_unclear_in_flow_${uid}`);
            viewState = 'home';
            renderHome();
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast('✓ Clarity check-in complete. You are in Unclear Mode.');
            }
        }
    }

    function finishCheckIn() {
        chooseDirection('unclear');
    }

    function viewCompletedCheckIn(checkInId) {
        const history = loadCompletedHistory();
        const found = history.find(h => h.id === checkInId);
        if (found) {
            currentDraft = found;
            viewState = 'checkin';
            renderHome();
        }
    }

    function renderCheckinFlow(container) {
        if (!currentDraft) {
            currentDraft = createNewDraft();
            saveDraft();
        }

        const stage = currentDraft.current_stage || 1;

        // Render Completion Screen if Stage 5
        if (stage >= 5) {
            renderStage5Completion(container);
            return;
        }

        container.innerHTML = `
            <div class="max-w-3xl mx-auto space-y-6">
                <!-- Check-in Header Utility Bar: Back Button + Step Progress Indicator -->
                <div class="flex items-center justify-between pb-1">
                    <button type="button" onclick="window.TempoUnclearMode.goBack()"
                            class="inline-flex items-center space-x-1.5 text-xs font-bold text-stone-500 hover:text-stone-900 transition cursor-pointer">
                        <span>←</span>
                        <span>Back</span>
                    </button>

                    <!-- 4-step Progress Indicator with connected track -->
                    <div class="flex items-center">
                        ${[1, 2, 3, 4].map((s, idx) => {
                            const isActive = s === stage;
                            const isPast = s < stage;
                            const dotHtml = `
                                <span class="w-2.5 h-2.5 rounded-full transition-all duration-300 ${
                                    isActive
                                        ? 'bg-[#FF6B2C] ring-4 ring-[#FFE9DC]'
                                        : isPast
                                        ? 'bg-[#FF6B2C]'
                                        : 'bg-stone-200'
                                }"></span>
                            `;
                            const lineHtml = idx < 3 ? `
                                <span class="w-6 sm:w-10 h-0.5 transition-all duration-300 ${
                                    s < stage ? 'bg-[#FF6B2C]' : 'bg-stone-200'
                                }"></span>
                            ` : '';
                            return dotHtml + lineHtml;
                        }).join('')}
                    </div>

                    <span class="text-xs font-bold text-[#6F6B68]">
                        ${stage} of 4
                    </span>
                </div>

                <!-- Check-in Dynamic Stage Screen -->
                <div id="unclear-stage-body" class="space-y-6"></div>
            </div>
        `;

        const body = document.getElementById('unclear-stage-body');
        if (!body) return;

        if (stage === 1) renderStage1(body);
        else if (stage === 2) renderStage2(body);
        else if (stage === 3) renderStage3(body);
        else if (stage === 4) renderStage4(body);
    }

    // =========================================================================
    // STAGE 1: WHAT'S BEEN ON MY MIND LATELY?
    // =========================================================================

    function renderStage1(container) {
        const selectedConcerns = new Set(currentDraft.concerns || []);
        const customConcerns = currentDraft.custom_concerns || [];

        container.innerHTML = `
            <div class="space-y-6">
                <!-- Title & Context -->
                <div class="space-y-1">
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        What's been on your mind lately?
                    </h2>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        Sometimes it's hard to point to one reason you feel off. Start with what's been taking up more space than usual.
                    </p>
                </div>

                <!-- 5 Life Areas Grid -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    ${LIFE_AREAS.map(area => {
                        const areaCustoms = customConcerns.filter(c => c.category === area.key);
                        const isInputOpen = activeCustomInputs[area.key] || false;

                        return `
                            <div class="p-5 rounded-3xl border border-[#EAE4DF] bg-white space-y-3.5 shadow-2xs">
                                <!-- Area Header -->
                                <div class="flex items-center space-x-2 text-xs font-extrabold uppercase tracking-wider text-[#202124]">
                                    <span>${area.icon}</span>
                                    <span>${escapeHTML(area.title)}</span>
                                </div>

                                <!-- Predefined Concern Items -->
                                <div class="space-y-1.5">
                                    ${area.items.map(item => {
                                        const isChecked = selectedConcerns.has(item);
                                        return `
                                            <label class="flex items-center space-x-2.5 p-2 rounded-xl border transition cursor-pointer select-none ${
                                                isChecked
                                                    ? 'border-[#FF6B2C] bg-[#FFF8F4] text-[#202124]'
                                                    : 'border-transparent hover:bg-stone-50 text-[#474543]'
                                            }">
                                                <input type="checkbox" 
                                                       ${isChecked ? 'checked' : ''} 
                                                       onchange="window.TempoUnclearMode.toggleConcern('${escapeHTML(item)}')"
                                                       class="w-4 h-4 rounded text-[#FF6B2C] focus:ring-[#FF6B2C] accent-[#FF6B2C]">
                                                <span class="text-xs sm:text-sm font-medium leading-snug">${escapeHTML(item)}</span>
                                            </label>
                                        `;
                                    }).join('')}

                                    <!-- Custom Concerns for this category -->
                                    ${areaCustoms.map(customItem => {
                                        const isChecked = selectedConcerns.has(customItem.text);
                                        return `
                                            <label class="flex items-center space-x-2.5 p-2 rounded-xl border transition cursor-pointer select-none ${
                                                isChecked
                                                    ? 'border-[#FF6B2C] bg-[#FFF8F4] text-[#202124]'
                                                    : 'border-transparent hover:bg-stone-50 text-[#474543]'
                                            }">
                                                <input type="checkbox" 
                                                       ${isChecked ? 'checked' : ''} 
                                                       onchange="window.TempoUnclearMode.toggleConcern('${escapeHTML(customItem.text)}')"
                                                       class="w-4 h-4 rounded text-[#FF6B2C] focus:ring-[#FF6B2C] accent-[#FF6B2C]">
                                                <span class="text-xs sm:text-sm font-medium leading-snug">${escapeHTML(customItem.text)}</span>
                                                <span class="text-[10px] text-stone-400 italic ml-auto">(Added by you)</span>
                                            </label>
                                        `;
                                    }).join('')}
                                </div>

                                <!-- Add Custom Concern Button or Input -->
                                <div class="pt-1">
                                    ${isInputOpen ? `
                                        <div class="flex items-center space-x-2 pt-1">
                                            <input type="text" id="custom-input-${area.key}" placeholder="Add something you noticed..."
                                                   onkeydown="if (event.key === 'Enter') { window.TempoUnclearMode.submitCustomConcern('${area.key}'); }"
                                                   class="w-full px-3 py-1.5 rounded-xl border border-stone-200 text-xs focus:outline-none focus:border-[#FF6B2C] focus:ring-1 focus:ring-[#FF6B2C]">
                                            <button type="button" onclick="window.TempoUnclearMode.submitCustomConcern('${area.key}')"
                                                    class="btn-primary px-3 py-1.5 rounded-xl text-xs font-bold shrink-0 transition cursor-pointer">
                                                Add
                                            </button>
                                            <button type="button" onclick="window.TempoUnclearMode.toggleCustomInput('${area.key}', false)"
                                                    class="px-2.5 py-1.5 rounded-xl text-xs text-stone-500 hover:text-stone-800 transition cursor-pointer">
                                                ✕
                                            </button>
                                        </div>
                                    ` : `
                                        <button type="button" onclick="window.TempoUnclearMode.toggleCustomInput('${area.key}', true)"
                                                class="text-xs font-semibold text-stone-400 hover:text-[#FF6B2C] transition cursor-pointer flex items-center space-x-1">
                                            <span>+ Add my own</span>
                                        </button>
                                    `}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>

                <!-- Footer Navigation -->
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <span class="text-xs text-[#6F6B68]">
                        ${selectedConcerns.size > 0 ? `${selectedConcerns.size} selected` : 'Choose whatever feels relevant'}
                    </span>
                    <button type="button" onclick="window.TempoUnclearMode.submitStage1()"
                            ${selectedConcerns.size === 0 ? 'disabled' : ''}
                            class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed">
                        <span>Continue</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;

        // Focus open custom input if any
        Object.keys(activeCustomInputs).forEach(k => {
            if (activeCustomInputs[k]) {
                const el = document.getElementById(`custom-input-${k}`);
                if (el) el.focus();
            }
        });
    }

    function toggleConcern(concernText) {
        if (!currentDraft) return;
        const set = new Set(currentDraft.concerns || []);
        if (set.has(concernText)) {
            set.delete(concernText);
            // Also clean from top_concerns if deselected
            currentDraft.top_concerns = (currentDraft.top_concerns || []).filter(c => c !== concernText);
            delete currentDraft.feelings_by_concern[concernText];
        } else {
            set.add(concernText);
        }
        currentDraft.concerns = Array.from(set);
        saveDraft();
        renderHome();
    }

    function toggleCustomInput(categoryKey, isOpen) {
        activeCustomInputs[categoryKey] = isOpen;
        renderHome();
    }

    function submitCustomConcern(categoryKey, optionalText) {
        let text = (typeof optionalText === 'string') ? optionalText.trim() : '';
        if (!text) {
            const input = document.getElementById(`custom-input-${categoryKey}`);
            if (input) text = input.value.trim();
        }
        if (!text) {
            toggleCustomInput(categoryKey, false);
            return;
        }

        if (!currentDraft.custom_concerns) currentDraft.custom_concerns = [];
        if (!currentDraft.concerns) currentDraft.concerns = [];

        // Avoid exact duplicate
        if (!currentDraft.concerns.includes(text)) {
            currentDraft.custom_concerns.push({ category: categoryKey, text });
            currentDraft.concerns.push(text);
        }

        activeCustomInputs[categoryKey] = false;
        saveDraft();
        renderHome();
    }

    function submitStage1() {
        if (!currentDraft || !currentDraft.concerns || currentDraft.concerns.length === 0) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast('Please select at least one thing that has been taking up space.');
            }
            return;
        }
        goToStage(2);
    }

    // =========================================================================
    // STAGE 2: WHAT FEELS HEAVIEST RIGHT NOW? (MAX 2) + FEELINGS
    // =========================================================================

    function renderStage2(container) {
        const availableConcerns = currentDraft.concerns || [];
        const topConcerns = currentDraft.top_concerns || [];
        const feelingsByConcern = currentDraft.feelings_by_concern || {};
        const customFeelings = currentDraft.custom_feelings_by_concern || {};

        container.innerHTML = `
            <div class="space-y-6">
                <!-- Title & Context -->
                <div class="space-y-1">
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        What feels heaviest right now?
                    </h2>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        You may have a few things taking up space. You don't need to untangle everything at once. Choose up to 2 that seem to be taking the most thought or energy.
                    </p>
                </div>

                <!-- Top Concerns Selection Chips (Max 2) -->
                <div class="space-y-2">
                    <span class="text-xs font-bold uppercase tracking-wider text-stone-500">
                        Select up to 2:
                    </span>
                    <div class="flex flex-wrap gap-2.5">
                        ${availableConcerns.map(concern => {
                            const isSelected = topConcerns.includes(concern);
                            return `
                                <button type="button" 
                                        onclick="window.TempoUnclearMode.toggleTopConcern('${escapeHTML(concern)}')"
                                        class="px-4 py-2.5 rounded-2xl border text-xs sm:text-sm font-semibold transition cursor-pointer flex items-center space-x-2 ${
                                            isSelected
                                                ? 'bg-[#FFE9DC] border-[#FF6B2C] text-[#B83D08] font-bold shadow-2xs'
                                                : 'bg-white border-stone-200 text-[#202124] hover:border-stone-300'
                                        }">
                                    <span>${isSelected ? '✓' : '○'}</span>
                                    <span>${escapeHTML(concern)}</span>
                                </button>
                            `;
                        }).join('')}
                    </div>
                </div>

                <!-- Feelings for Each Selected Top Concern -->
                ${topConcerns.length > 0 ? `
                    <div class="space-y-4 pt-2">
                        <span class="text-xs font-bold uppercase tracking-wider text-stone-500">
                            How has this been making you feel?
                        </span>
                        ${topConcerns.map(concern => {
                            const concernFeelings = new Set(feelingsByConcern[concern] || []);
                            const customVal = customFeelings[concern] || '';
                            const isCustomOpen = activeCustomInputs[`feeling_${concern}`] || false;

                            return `
                                <div class="p-5 rounded-3xl border border-[#EAE4DF] bg-white space-y-3.5 shadow-2xs">
                                    <div class="flex items-center justify-between">
                                        <h4 class="text-sm font-bold text-[#202124]">${escapeHTML(concern)}</h4>
                                        <button type="button" onclick="window.TempoUnclearMode.toggleTopConcern('${escapeHTML(concern)}')"
                                                class="text-xs text-stone-400 hover:text-stone-700 transition cursor-pointer" title="Remove">✕</button>
                                    </div>
                                    <p class="text-xs text-[#6F6B68]">Select any feelings that apply:</p>

                                    <!-- Feeling Chips -->
                                    <div class="flex flex-wrap gap-2">
                                        ${FEELINGS.map(f => {
                                            const isChecked = concernFeelings.has(f);
                                            return `
                                                <button type="button" 
                                                        onclick="window.TempoUnclearMode.toggleFeeling('${escapeHTML(concern)}', '${escapeHTML(f)}')"
                                                        class="px-3.5 py-1.5 rounded-xl border text-xs font-semibold transition cursor-pointer flex items-center space-x-1.5 ${
                                                            isChecked
                                                                ? 'bg-[#FFE9DC] border-[#FF6B2C] text-[#B83D08] font-bold shadow-2xs'
                                                                : 'bg-stone-50 border-stone-200 text-stone-700 hover:bg-stone-100'
                                                        }">
                                                    <span>${escapeHTML(f)}</span>
                                                    ${isChecked ? '<span>✓</span>' : ''}
                                                </button>
                                            `;
                                        }).join('')}

                                        <!-- Custom Feeling Input -->
                                        ${isCustomOpen ? `
                                            <div class="inline-flex items-center space-x-1.5">
                                                <input type="text" id="custom-feeling-${escapeHTML(concern)}" value="${escapeHTML(customVal)}"
                                                       placeholder="Feeling..."
                                                       onkeydown="if (event.key === 'Enter') { window.TempoUnclearMode.submitCustomFeeling('${escapeHTML(concern)}'); }"
                                                       class="w-32 px-3 py-1.5 rounded-xl border border-stone-200 text-xs focus:outline-none focus:border-[#FF6B2C]">
                                                <button type="button" onclick="window.TempoUnclearMode.submitCustomFeeling('${escapeHTML(concern)}')"
                                                        class="btn-primary px-2.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer">
                                                    ✓
                                                </button>
                                            </div>
                                        ` : `
                                            <button type="button" onclick="window.TempoUnclearMode.toggleCustomFeelingInput('${escapeHTML(concern)}', true)"
                                                    class="px-3.5 py-1.5 rounded-xl border border-dashed border-stone-300 text-xs font-semibold text-stone-500 hover:text-[#FF6B2C] hover:border-[#FF6B2C] transition cursor-pointer">
                                                ${customVal ? `+ ${escapeHTML(customVal)}` : '+ Something else'}
                                            </button>
                                        `}
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                ` : `
                    <div class="p-6 rounded-3xl border border-dashed border-stone-200 text-center text-xs text-[#6F6B68]">
                        Select up to 2 concerns above to reflect on how they've been feeling.
                    </div>
                `}

                <!-- Footer Navigation -->
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoUnclearMode.goBack()"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ← Back
                    </button>
                    <button type="button" onclick="window.TempoUnclearMode.submitStage2()"
                            ${topConcerns.length === 0 ? 'disabled' : ''}
                            class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed">
                        <span>Continue</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    function toggleTopConcern(concernText) {
        if (!currentDraft) return;
        let top = currentDraft.top_concerns || [];
        if (top.includes(concernText)) {
            top = top.filter(c => c !== concernText);
            delete currentDraft.feelings_by_concern[concernText];
        } else {
            if (top.length >= 2) {
                if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                    window.TempoApp.showToast('Choose up to 2 that feel heaviest right now. You can uncheck one to pick another.');
                }
                return;
            }
            top.push(concernText);
            if (!currentDraft.feelings_by_concern) currentDraft.feelings_by_concern = {};
            if (!currentDraft.feelings_by_concern[concernText]) currentDraft.feelings_by_concern[concernText] = [];
        }
        currentDraft.top_concerns = top;
        saveDraft();
        renderHome();
    }

    function toggleFeeling(concernText, feelingText) {
        if (!currentDraft) return;
        if (!currentDraft.feelings_by_concern) currentDraft.feelings_by_concern = {};
        let list = currentDraft.feelings_by_concern[concernText] || [];
        if (list.includes(feelingText)) {
            list = list.filter(f => f !== feelingText);
        } else {
            list.push(feelingText);
        }
        currentDraft.feelings_by_concern[concernText] = list;
        saveDraft();
        renderHome();
    }

    function toggleCustomFeelingInput(concernText, isOpen) {
        activeCustomInputs[`feeling_${concernText}`] = isOpen;
        renderHome();
    }

    function submitCustomFeeling(concernText, optionalText) {
        let text = (typeof optionalText === 'string') ? optionalText.trim() : '';
        if (!text) {
            const input = document.getElementById(`custom-feeling-${concernText}`);
            if (input) text = input.value.trim();
        }
        if (!currentDraft.custom_feelings_by_concern) currentDraft.custom_feelings_by_concern = {};
        if (text) {
            currentDraft.custom_feelings_by_concern[concernText] = text;
        } else {
            delete currentDraft.custom_feelings_by_concern[concernText];
        }
        activeCustomInputs[`feeling_${concernText}`] = false;
        saveDraft();
        renderHome();
    }

    function submitStage2() {
        if (!currentDraft || !currentDraft.top_concerns || currentDraft.top_concerns.length === 0) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast('Please choose at least 1 thing that feels heaviest right now.');
            }
            return;
        }
        goToStage(3);
    }

    // =========================================================================
    // STAGE 3: WHAT HAVE I NOTICED? + IMPACT
    // =========================================================================

    function renderStage3(container) {
        const selectedNoticed = new Set(currentDraft.noticed_changes || []);
        const customChanges = currentDraft.custom_changes || [];
        const impact = currentDraft.impact_level || '';
        const isCustomOpen = activeCustomInputs['noticed_custom'] || false;

        container.innerHTML = `
            <div class="space-y-6">
                <!-- Title & Context -->
                <div class="space-y-1">
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        What have you noticed lately?
                    </h2>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        Things that weigh on us can sometimes show up in ordinary parts of the day. See if anything has felt different from usual.
                    </p>
                </div>

                <!-- 4 Noticed Categories Grid -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    ${NOTICED_CATEGORIES.map(cat => {
                        return `
                            <div class="p-5 rounded-3xl border border-[#EAE4DF] bg-white space-y-3 shadow-2xs">
                                <div class="flex items-center space-x-2 text-xs font-extrabold uppercase tracking-wider text-[#202124]">
                                    <span>${cat.icon}</span>
                                    <span>${escapeHTML(cat.title)}</span>
                                </div>
                                <div class="space-y-1.5">
                                    ${cat.items.map(item => {
                                        const isChecked = selectedNoticed.has(item);
                                        return `
                                            <label class="flex items-center space-x-2.5 p-2 rounded-xl border transition cursor-pointer select-none ${
                                                isChecked
                                                    ? 'border-[#FF6B2C] bg-[#FFF8F4] text-[#202124]'
                                                    : 'border-transparent hover:bg-stone-50 text-[#474543]'
                                            }">
                                                <input type="checkbox" 
                                                       ${isChecked ? 'checked' : ''} 
                                                       onchange="window.TempoUnclearMode.toggleNoticedChange('${escapeHTML(item)}')"
                                                       class="w-4 h-4 rounded text-[#FF6B2C] focus:ring-[#FF6B2C] accent-[#FF6B2C]">
                                                <span class="text-xs sm:text-sm font-medium leading-snug">${escapeHTML(item)}</span>
                                            </label>
                                        `;
                                    }).join('')}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>

                <!-- Custom Noticed Changes Section -->
                <div class="p-4 rounded-2xl border border-stone-200 bg-stone-50/60 space-y-2">
                    <div class="flex items-center justify-between text-xs font-bold text-stone-700">
                        <span>Anything else you've noticed? <span class="text-stone-400 font-normal">(Optional)</span></span>
                        ${!isCustomOpen ? `
                            <button type="button" onclick="window.TempoUnclearMode.toggleCustomNoticedInput(true)"
                                    class="text-xs font-bold text-[#FF6B2C] hover:underline cursor-pointer">
                                + Add my own
                            </button>
                        ` : ''}
                    </div>

                    ${customChanges.length > 0 ? `
                        <div class="flex flex-wrap gap-2 pt-1">
                            ${customChanges.map(changeText => `
                                <span class="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white border border-[#FFD2BA] text-xs font-semibold text-[#202124]">
                                    <span>${escapeHTML(changeText)}</span>
                                    <button type="button" onclick="window.TempoUnclearMode.removeCustomNoticed('${escapeHTML(changeText)}')"
                                            class="text-stone-400 hover:text-red-500 font-bold ml-1 transition cursor-pointer">✕</button>
                                </span>
                            `).join('')}
                        </div>
                    ` : ''}

                    ${isCustomOpen ? `
                        <div class="flex items-center space-x-2 pt-1">
                            <input type="text" id="custom-noticed-input" placeholder="e.g. Taking longer to reply to messages..."
                                   onkeydown="if (event.key === 'Enter') { window.TempoUnclearMode.submitCustomNoticed(); }"
                                   class="w-full px-3 py-1.5 rounded-xl border border-stone-200 text-xs focus:outline-none focus:border-[#FF6B2C]">
                            <button type="button" onclick="window.TempoUnclearMode.submitCustomNoticed()"
                                    class="btn-primary px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer shrink-0">
                                Add
                            </button>
                            <button type="button" onclick="window.TempoUnclearMode.toggleCustomNoticedInput(false)"
                                    class="px-2.5 py-1.5 rounded-xl text-xs text-stone-500 hover:text-stone-800 transition cursor-pointer">
                                ✕
                            </button>
                        </div>
                    ` : ''}
                </div>

                <!-- Impact Question at the Bottom of Stage 3 -->
                <div class="p-6 rounded-3xl border border-[#FFD2BA] bg-gradient-to-br from-white to-[#FFF9F5] space-y-3.5 shadow-2xs">
                    <div class="space-y-1">
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">IMPACT</span>
                        <h4 class="font-heading text-sm sm:text-base font-extrabold text-[#202124]">
                            Overall, how much has this been affecting your everyday life?
                        </h4>
                    </div>

                    <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                        ${IMPACT_OPTIONS.map(opt => {
                            const isSelected = impact === opt.key;
                            return `
                                <button type="button" 
                                        onclick="window.TempoUnclearMode.setImpactLevel('${opt.key}')"
                                        class="p-3.5 rounded-2xl border text-xs sm:text-sm font-semibold transition cursor-pointer text-center flex items-center justify-center space-x-2 ${
                                            isSelected
                                                ? 'bg-[#FFE9DC] border-[#FF6B2C] text-[#B83D08] font-bold shadow-2xs'
                                                : 'bg-white border-stone-200 text-[#202124] hover:border-stone-300'
                                        }">
                                    <span>${isSelected ? '●' : '○'}</span>
                                    <span>${escapeHTML(opt.label)}</span>
                                </button>
                            `;
                        }).join('')}
                    </div>
                </div>

                <!-- Footer Navigation -->
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoUnclearMode.goBack()"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ← Back
                    </button>
                    <button type="button" onclick="window.TempoUnclearMode.submitStage3()"
                            ${!impact ? 'disabled' : ''}
                            class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed">
                        <span>Continue</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;

        if (isCustomOpen) {
            const el = document.getElementById('custom-noticed-input');
            if (el) el.focus();
        }
    }

    function toggleNoticedChange(changeText) {
        if (!currentDraft) return;
        const set = new Set(currentDraft.noticed_changes || []);
        if (set.has(changeText)) set.delete(changeText);
        else set.add(changeText);
        currentDraft.noticed_changes = Array.from(set);
        saveDraft();
        renderHome();
    }

    function toggleCustomNoticedInput(isOpen) {
        activeCustomInputs['noticed_custom'] = isOpen;
        renderHome();
    }

    function submitCustomNoticed(optionalText) {
        let text = (typeof optionalText === 'string') ? optionalText.trim() : '';
        if (!text) {
            const input = document.getElementById('custom-noticed-input');
            if (input) text = input.value.trim();
        }
        if (!text) {
            toggleCustomNoticedInput(false);
            return;
        }

        if (!currentDraft.custom_changes) currentDraft.custom_changes = [];
        if (!currentDraft.custom_changes.includes(text)) {
            currentDraft.custom_changes.push(text);
        }
        activeCustomInputs['noticed_custom'] = false;
        saveDraft();
        renderHome();
    }

    function removeCustomNoticed(changeText) {
        if (!currentDraft || !currentDraft.custom_changes) return;
        currentDraft.custom_changes = currentDraft.custom_changes.filter(c => c !== changeText);
        saveDraft();
        renderHome();
    }

    function setImpactLevel(levelKey) {
        if (!currentDraft) return;
        currentDraft.impact_level = levelKey;
        saveDraft();
        renderHome();
    }

    function submitStage3() {
        if (!currentDraft || !currentDraft.impact_level) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast('Please select how much this has been affecting your everyday life.');
            }
            return;
        }
        goToStage(4);
    }

    // =========================================================================
    // STAGE 4: WHAT DO I NEED RIGHT NOW? (BROAD NEEDS + PRIMARY NEED)
    // =========================================================================

    function renderStage4(container) {
        const selectedNeeds = new Set(currentDraft.needs || []);
        const needDetails = currentDraft.need_details || {};
        const customNeed = currentDraft.custom_need || '';
        const primaryNeed = currentDraft.primary_need || '';

        container.innerHTML = `
            <div class="space-y-6">
                <!-- Title & Context -->
                <div class="space-y-1">
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        What would help most right now?
                    </h2>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        You don't have to solve everything today. What feels like it would make things a little easier from here?
                    </p>
                </div>

                <!-- 4 Broad Need Cards Grid -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    ${BROAD_NEEDS.map(bn => {
                        const isCardActive = selectedNeeds.has(bn.key);
                        const selectedSub = new Set(needDetails[bn.key] || []);

                        return `
                            <div class="p-5 rounded-3xl border transition space-y-3.5 shadow-2xs ${
                                isCardActive
                                    ? 'border-[#FF6B2C] bg-white ring-1 ring-[#FFD2BA]'
                                    : 'border-[#EAE4DF] bg-white'
                            }">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center space-x-2 text-xs font-extrabold uppercase tracking-wider text-[#202124]">
                                        <span>${bn.icon}</span>
                                        <span>${escapeHTML(bn.title)}</span>
                                    </div>
                                    <button type="button" 
                                            onclick="window.TempoUnclearMode.toggleBroadNeed('${bn.key}')"
                                            class="text-xs font-bold px-2.5 py-1 rounded-xl transition cursor-pointer ${
                                                isCardActive
                                                    ? 'bg-[#FFE9DC] text-[#B83D08]'
                                                    : 'text-stone-400 hover:text-stone-700'
                                            }">
                                        ${isCardActive ? 'Selected ✓' : '+ Select'}
                                    </button>
                                </div>

                                <div class="space-y-1.5 pt-1">
                                    ${bn.items.map(subItem => {
                                        const isSubChecked = selectedSub.has(subItem);
                                        return `
                                            <label class="flex items-center space-x-2.5 p-2 rounded-xl border transition cursor-pointer select-none ${
                                                isSubChecked
                                                    ? 'border-[#FF6B2C] bg-[#FFF8F4] text-[#202124]'
                                                    : 'border-transparent hover:bg-stone-50 text-[#474543]'
                                            }">
                                                <input type="checkbox" 
                                                       ${isSubChecked ? 'checked' : ''} 
                                                       onchange="window.TempoUnclearMode.toggleNeedDetail('${bn.key}', '${escapeHTML(subItem)}')"
                                                       class="w-4 h-4 rounded text-[#FF6B2C] focus:ring-[#FF6B2C] accent-[#FF6B2C]">
                                                <span class="text-xs sm:text-sm font-medium leading-snug">${escapeHTML(subItem)}</span>
                                            </label>
                                        `;
                                    }).join('')}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>

                <!-- Something Else / Custom Need -->
                <div class="p-5 rounded-3xl border border-[#EAE4DF] bg-white space-y-2.5 shadow-2xs">
                    <div class="flex items-center space-x-2 text-xs font-extrabold uppercase tracking-wider text-[#202124]">
                        <span>💛</span>
                        <span>Something else</span>
                    </div>
                    <input type="text" id="custom-need-input" value="${escapeHTML(customNeed)}"
                           placeholder="Write what you need right now (optional)..."
                           oninput="window.TempoUnclearMode.setCustomNeed(this.value)"
                           class="w-full px-4 py-2.5 rounded-xl border border-stone-200 text-xs sm:text-sm focus:outline-none focus:border-[#FF6B2C] focus:ring-1 focus:ring-[#FF6B2C]">
                </div>

                <!-- Primary Need Single-Choice Selection -->
                ${selectedNeeds.size > 0 || customNeed ? `
                    <div class="p-6 rounded-3xl border border-[#FFD2BA] bg-gradient-to-br from-white to-[#FFF9F5] space-y-3.5 shadow-2xs">
                        <div class="space-y-1">
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">PRIMARY NEED</span>
                            <h4 class="font-heading text-sm sm:text-base font-extrabold text-[#202124]">
                                Which feels most useful to start with?
                            </h4>
                            <p class="text-xs text-[#6F6B68]">
                                Choose one to focus on first. You can still explore the others later.
                            </p>
                        </div>

                        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 pt-1">
                            ${Array.from(selectedNeeds).map(needKey => {
                                const bn = BROAD_NEEDS.find(n => n.key === needKey);
                                if (!bn) return '';
                                const isSelected = primaryNeed === needKey;
                                return `
                                    <button type="button" 
                                            onclick="window.TempoUnclearMode.setPrimaryNeed('${needKey}')"
                                            class="p-3.5 rounded-2xl border text-xs sm:text-sm font-semibold transition cursor-pointer text-center flex items-center justify-center space-x-2 ${
                                                isSelected
                                                    ? 'bg-[#FFE9DC] border-[#FF6B2C] text-[#B83D08] font-bold shadow-2xs'
                                                    : 'bg-white border-stone-200 text-[#202124] hover:border-stone-300'
                                            }">
                                        <span>${isSelected ? '●' : '○'}</span>
                                        <span>${escapeHTML(bn.shortLabel)}</span>
                                    </button>
                                `;
                            }).join('')}

                            ${customNeed ? `
                                <button type="button" 
                                        onclick="window.TempoUnclearMode.setPrimaryNeed('custom')"
                                        class="p-3.5 rounded-2xl border text-xs sm:text-sm font-semibold transition cursor-pointer text-center flex items-center justify-center space-x-2 ${
                                            primaryNeed === 'custom'
                                                ? 'bg-[#FFE9DC] border-[#FF6B2C] text-[#B83D08] font-bold shadow-2xs'
                                                : 'bg-white border-stone-200 text-[#202124] hover:border-stone-300'
                                        }">
                                    <span>${primaryNeed === 'custom' ? '●' : '○'}</span>
                                    <span>Something else</span>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                ` : ''}

                <!-- Footer Navigation -->
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoUnclearMode.goBack()"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ← Back
                    </button>
                    <button type="button" onclick="window.TempoUnclearMode.submitStage4()"
                            ${(!primaryNeed && selectedNeeds.size === 0 && !customNeed) ? 'disabled' : ''}
                            class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed">
                        <span>Continue</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    function toggleBroadNeed(needKey) {
        if (!currentDraft) return;
        const set = new Set(currentDraft.needs || []);
        if (set.has(needKey)) {
            set.delete(needKey);
            delete currentDraft.need_details[needKey];
            if (currentDraft.primary_need === needKey) {
                currentDraft.primary_need = set.size > 0 ? Array.from(set)[0] : '';
            }
        } else {
            set.add(needKey);
            if (!currentDraft.primary_need) {
                currentDraft.primary_need = needKey;
            }
        }
        currentDraft.needs = Array.from(set);
        saveDraft();
        renderHome();
    }

    function toggleNeedDetail(needKey, detailText) {
        if (!currentDraft) return;
        if (!currentDraft.needs) currentDraft.needs = [];
        if (!currentDraft.needs.includes(needKey)) {
            currentDraft.needs.push(needKey);
            if (!currentDraft.primary_need) {
                currentDraft.primary_need = needKey;
            }
        }

        if (!currentDraft.need_details) currentDraft.need_details = {};
        let list = currentDraft.need_details[needKey] || [];
        if (list.includes(detailText)) {
            list = list.filter(d => d !== detailText);
        } else {
            list.push(detailText);
        }
        currentDraft.need_details[needKey] = list;
        saveDraft();
        renderHome();
    }

    function setCustomNeed(text) {
        if (!currentDraft) return;
        currentDraft.custom_need = text;
        if (text && !currentDraft.primary_need) {
            currentDraft.primary_need = 'custom';
        }
        saveDraft();
        renderHome();
    }

    function setPrimaryNeed(needKey) {
        if (!currentDraft) return;
        currentDraft.primary_need = needKey;
        saveDraft();
        renderHome();
    }

    function submitStage4() {
        if (!currentDraft) return;
        const hasNeeds = (currentDraft.needs && currentDraft.needs.length > 0) || currentDraft.custom_need;
        if (!hasNeeds) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast('Please select what feels like it would help most right now.');
            }
            return;
        }

        // If only 1 need selected and primary not yet explicitly picked, auto-assign
        if (!currentDraft.primary_need) {
            if (currentDraft.needs && currentDraft.needs.length > 0) {
                currentDraft.primary_need = currentDraft.needs[0];
            } else if (currentDraft.custom_need) {
                currentDraft.primary_need = 'custom';
            }
        }

        goToStage(5);
    }

    // =========================================================================
    // STAGE 5: FINAL RESULT — REFLECTION SUMMARY + NEXT DIRECTIONS (PHASE 2)
    // =========================================================================

    function getDirectionDefinitions() {
        return {
            urgent: {
                key: 'urgent',
                badge: '⚡ Urgent Mode',
                title: '⚡ Handle what needs attention',
                description: "If there's something concrete that needs sorting out, Urgent Mode can help you decide what comes first and make a workable plan.",
                cta: 'Go to Urgent Mode →',
                secondaryTitle: '⚡ Urgent Mode',
                secondaryDesc: 'If something needs concrete sorting out and a workable plan.'
            },
            recovery: {
                key: 'recovery',
                badge: '🌱 Recovery Mode',
                title: '🌱 Give yourself some room',
                description: 'Recovery Mode gives you space to slow things down, check in with yourself, and notice what helps over time.',
                cta: 'Go to Recovery Mode →',
                secondaryTitle: '🌱 Recovery Mode',
                secondaryDesc: 'If you need space to slow things down and decompress.'
            },
            default: {
                key: 'default',
                badge: '○ Return to Tempo',
                title: '○ Take it from here',
                description: 'You understand things a little better and want to work on what comes next in your own way. Your usual Tempo space and tools are still here.',
                cta: 'Return to Tempo →',
                secondaryTitle: '○ Return to Tempo',
                secondaryDesc: 'Return to your normal exploratory workspace and tools.'
            },
            support: {
                key: 'support',
                badge: '🤝 Support options',
                title: '🤝 Get some support',
                description: "You don't have to work through everything alone. Connect with campus wellbeing coordinators or explore peer experiences.",
                cta: 'Explore support options →',
                secondaryTitle: '🤝 Support options',
                secondaryDesc: 'Connect with campus wellbeing coordinators or peer resources.'
            }
        };
    }

    function getFeaturedKey(draft) {
        if (!draft) return 'custom';
        const p = draft.primary_need;
        if (p === 'handle') return 'urgent';
        if (p === 'room') return 'recovery';
        if (p === 'self_directed') return 'default';
        if (p === 'support') return 'support';
        return 'custom';
    }

    function renderSummaryTopConcerns(draft) {
        const top = draft.top_concerns || [];
        const allConcerns = draft.concerns || [];
        const displayed = top.length > 0 ? top : (allConcerns.length > 0 ? allConcerns.slice(0, 3) : []);
        if (displayed.length === 0) return '';

        return `
            <div class="space-y-2">
                <span class="text-[11px] font-extrabold uppercase tracking-wider text-stone-400">
                    WHAT'S BEEN WEIGHING ON YOU
                </span>
                <div class="flex flex-wrap gap-2">
                    ${displayed.map(c => `
                        <span class="px-3.5 py-1.5 rounded-xl bg-[#FFF5EF] border border-[#FFD2BA] text-xs font-semibold text-[#B83D08]">
                            ${escapeHTML(c)}
                        </span>
                    `).join('')}
                </div>
            </div>
        `;
    }

    function renderSummaryNoticed(draft) {
        const feelings = [];
        const fByC = draft.feelings_by_concern || {};
        Object.values(fByC).forEach(arr => {
            if (Array.isArray(arr)) feelings.push(...arr);
        });
        const cFeelings = draft.custom_feelings_by_concern || {};
        Object.values(cFeelings).forEach(txt => {
            if (txt) feelings.push(txt);
        });
        const uniqueFeelings = Array.from(new Set(feelings));

        const noticed = draft.noticed_changes || [];
        const customChanges = draft.custom_changes || [];
        const allNoticed = [...noticed, ...customChanges];

        if (uniqueFeelings.length === 0 && allNoticed.length === 0) return '';

        return `
            <div class="space-y-2 pt-2 border-t border-stone-100">
                <span class="text-[11px] font-extrabold uppercase tracking-wider text-stone-400">
                    WHAT YOU'VE NOTICED
                </span>
                <div class="space-y-2">
                    ${uniqueFeelings.length > 0 ? `
                        <div class="flex flex-wrap gap-1.5 items-center">
                            <span class="text-xs text-[#6F6B68] mr-1">Feelings:</span>
                            ${uniqueFeelings.map(f => `
                                <span class="px-2.5 py-1 rounded-lg bg-stone-100 text-stone-800 text-xs font-medium">
                                    ${escapeHTML(f)}
                                </span>
                            `).join('')}
                        </div>
                    ` : ''}
                    ${allNoticed.length > 0 ? `
                        <div class="flex flex-wrap gap-1.5 items-center">
                            <span class="text-xs text-[#6F6B68] mr-1">Day-to-day:</span>
                            ${allNoticed.map(n => `
                                <span class="px-2.5 py-1 rounded-lg bg-stone-100 text-stone-800 text-xs font-medium">
                                    ${escapeHTML(n)}
                                </span>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    function renderSummaryImpact(draft) {
        if (!draft || !draft.impact_level) return '';
        const map = {
            'little': 'A little',
            'quite_a_bit': 'Quite a bit',
            'a_lot': 'A lot'
        };
        const label = map[draft.impact_level] || draft.impact_level;

        return `
            <div class="space-y-1 pt-2 border-t border-stone-100">
                <span class="text-[11px] font-extrabold uppercase tracking-wider text-stone-400">
                    EVERYDAY IMPACT
                </span>
                <p class="text-xs sm:text-sm font-semibold text-[#202124]">
                    ${escapeHTML(label)}
                </p>
            </div>
        `;
    }

    function renderSummaryNeeds(draft) {
        const needs = draft.needs || [];
        const customNeed = draft.custom_need || '';
        const primaryNeed = draft.primary_need || '';

        const broadMap = {
            'room': 'Some room',
            'handle': 'Deal with something',
            'support': 'Some support',
            'self_directed': 'I know what to do'
        };

        const needLabels = [];
        needs.forEach(k => {
            if (broadMap[k]) needLabels.push(broadMap[k]);
        });
        if (customNeed) needLabels.push(customNeed);

        if (needLabels.length === 0 && !primaryNeed) return '';

        let primaryLabel = '';
        if (primaryNeed === 'custom') {
            primaryLabel = customNeed || 'Something else';
        } else if (broadMap[primaryNeed]) {
            primaryLabel = broadMap[primaryNeed];
        }

        return `
            <div class="space-y-2 pt-2 border-t border-stone-100">
                <span class="text-[11px] font-extrabold uppercase tracking-wider text-stone-400">
                    WHAT YOU SAID YOU NEED
                </span>
                <div class="flex flex-wrap gap-2">
                    ${needLabels.map(nl => `
                        <span class="px-3 py-1 rounded-xl bg-stone-50 border border-stone-200 text-xs font-medium text-stone-700">
                            ${escapeHTML(nl)}
                        </span>
                    `).join('')}
                </div>
                ${primaryLabel ? `
                    <div class="pt-1 flex items-center space-x-2 text-xs">
                        <span class="text-stone-400 font-semibold uppercase text-[10px] tracking-wider">MOST USEFUL TO START WITH:</span>
                        <span class="font-bold text-[#FF6B2C] bg-[#FFE9DC] px-2.5 py-0.5 rounded-lg">${escapeHTML(primaryLabel)}</span>
                    </div>
                ` : ''}
            </div>
        `;
    }

    function renderStage5Completion(container) {
        if (!currentDraft) loadDraft();
        const draft = currentDraft || {};
        const defs = getDirectionDefinitions();
        const featuredKey = getFeaturedKey(draft);

        // Determine secondary options
        let secondaryKeys = [];
        if (featuredKey === 'urgent') {
            secondaryKeys = ['recovery', 'default'];
            if (draft.needs && draft.needs.includes('support')) secondaryKeys.push('support');
        } else if (featuredKey === 'recovery') {
            secondaryKeys = ['urgent', 'default'];
            if (draft.needs && draft.needs.includes('support')) secondaryKeys.push('support');
        } else if (featuredKey === 'default') {
            secondaryKeys = ['recovery', 'urgent'];
            if (draft.needs && draft.needs.includes('support')) secondaryKeys.push('support');
        } else if (featuredKey === 'support') {
            secondaryKeys = ['default', 'recovery', 'urgent'];
        } else {
            secondaryKeys = ['urgent', 'recovery', 'default'];
            if (draft.needs && draft.needs.includes('support')) secondaryKeys.push('support');
        }

        const topConcernsHTML = renderSummaryTopConcerns(draft);
        const noticedHTML = renderSummaryNoticed(draft);
        const impactHTML = renderSummaryImpact(draft);
        const needsHTML = renderSummaryNeeds(draft);

        const featuredDef = defs[featuredKey];
        const isCompleted = draft.status === 'completed';

        container.innerHTML = `
            <div class="max-w-2xl mx-auto space-y-6">
                <!-- Check-in Header Utility Bar: Back Button + Status -->
                <div class="flex items-center justify-between pb-1">
                    ${isCompleted ? `
                        <button type="button" onclick="window.TempoUnclearMode.returnToHome()"
                                class="inline-flex items-center space-x-1.5 text-xs font-bold text-stone-500 hover:text-stone-900 transition cursor-pointer">
                            <span>←</span>
                            <span>Return Home</span>
                        </button>
                    ` : `
                        <button type="button" onclick="window.TempoUnclearMode.goBack()"
                                class="inline-flex items-center space-x-1.5 text-xs font-bold text-stone-500 hover:text-stone-900 transition cursor-pointer">
                            <span>←</span>
                            <span>Back to edit needs</span>
                        </button>
                    `}
                    <div class="inline-flex items-center space-x-1.5 text-xs font-bold text-[#166545] bg-[#EDF7F1] px-3 py-1 rounded-full border border-[#CDE9DA]">
                        <span>✓</span>
                        <span>Things are a little clearer</span>
                    </div>
                </div>

                <!-- Title & Context -->
                <div class="space-y-1.5 text-left">
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        Here's what you noticed
                    </h2>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        You don't need to have everything figured out. Here's what's been coming up for you — and a few places you can go from here.
                    </p>
                </div>

                <!-- Structured Reflection Summary Card -->
                <div class="tempo-card p-6 sm:p-7 rounded-3xl bg-white border border-[#EAE4DF] space-y-5 shadow-2xs text-left">
                    <div class="flex items-center space-x-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-[#FF6B2C] inline-block"></span>
                        <span class="text-xs font-extrabold uppercase tracking-wider text-[#202124]">
                            YOUR REFLECTION SUMMARY
                        </span>
                    </div>

                    ${topConcernsHTML}
                    ${noticedHTML}
                    ${impactHTML}
                    ${needsHTML}
                </div>

                <!-- Next Direction Section -->
                <div class="space-y-3 pt-2 text-left">
                    <div class="space-y-1">
                        <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#202124]">
                            What feels right from here?
                        </h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                            You can start with what feels most useful right now. You can always change direction later.
                        </p>
                    </div>

                    <!-- Featured Direction Card (Order & Emphasis Based on Primary Need) -->
                    ${featuredKey !== 'custom' && featuredDef ? `
                        <div class="p-6 sm:p-7 rounded-3xl border-2 border-[#FFD2BA] bg-gradient-to-br from-[#FFF9F5] to-white space-y-4 shadow-2xs">
                            <div class="space-y-1.5">
                                <div class="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-[#FFE9DC] text-[#B83D08] text-[10px] font-extrabold uppercase tracking-wider">
                                    <span>★</span>
                                    <span>Based on what you said you need first</span>
                                </div>
                                <h4 class="font-heading text-lg sm:text-xl font-extrabold text-[#202124]">
                                    ${featuredDef.title}
                                </h4>
                                <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed max-w-xl">
                                    ${featuredDef.description}
                                </p>
                            </div>

                            ${featuredKey === 'default' ? `
                                <div class="pt-1 max-w-md space-y-1.5">
                                    <label for="unclear-next-step-input" class="block text-[11px] font-bold uppercase tracking-wider text-stone-500">
                                        One thing I want to do next <span class="text-stone-400 font-normal lowercase">(optional)</span>
                                    </label>
                                    <input type="text" id="unclear-next-step-input" placeholder="e.g. Finish the outline, then stop for tonight"
                                           class="w-full px-3.5 py-2 rounded-xl border border-stone-200 text-xs sm:text-sm focus:outline-none focus:border-[#FF6B2C] focus:ring-1 focus:ring-[#FF6B2C]">
                                </div>
                            ` : ''}

                            <div class="pt-2">
                                <button type="button" onclick="window.TempoUnclearMode.chooseDirection('${featuredDef.key}')"
                                        class="btn-primary px-6 py-3 rounded-2xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer inline-flex items-center space-x-2">
                                    <span>${featuredDef.cta}</span>
                                </button>
                            </div>
                        </div>
                    ` : `
                        <!-- Custom Need Featured Card -->
                        <div class="p-6 sm:p-7 rounded-3xl border-2 border-[#FFD2BA] bg-gradient-to-br from-[#FFF9F5] to-white space-y-3.5 shadow-2xs">
                            <div class="space-y-1">
                                <span class="text-[10px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">BASED ON WHAT YOU SAID YOU NEED FIRST</span>
                                <h4 class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">
                                    ○ Choose what feels useful
                                </h4>
                                <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                                    You know more about what you need than Tempo does. Choose where you'd like to go from here.
                                </p>
                            </div>
                        </div>
                    `}

                    <!-- Secondary Directions Grid -->
                    ${secondaryKeys.length > 0 ? `
                        <div class="space-y-2.5 pt-2">
                            <span class="text-xs font-bold text-stone-500 uppercase tracking-wider">
                                Other directions you can explore:
                            </span>
                            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                                ${secondaryKeys.map(k => {
                                    const d = defs[k];
                                    if (!d) return '';
                                    return `
                                        <div class="p-4 sm:p-5 rounded-2xl border border-[#EAE4DF] bg-white space-y-3 flex flex-col justify-between hover:border-stone-300 transition shadow-2xs">
                                            <div class="space-y-1">
                                                <h5 class="font-heading text-xs sm:text-sm font-bold text-[#202124]">
                                                    ${escapeHTML(d.secondaryTitle)}
                                                </h5>
                                                <p class="text-[11px] sm:text-xs text-[#6F6B68] leading-relaxed">
                                                    ${escapeHTML(d.secondaryDesc)}
                                                </p>
                                            </div>
                                            <div class="pt-1">
                                                <button type="button" onclick="window.TempoUnclearMode.chooseDirection('${d.key}')"
                                                        class="text-xs font-bold text-[#FF6B2C] hover:text-[#B83D08] flex items-center space-x-1 transition cursor-pointer">
                                                    <span>${escapeHTML(d.cta)}</span>
                                                </button>
                                            </div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- Bottom Navigation: Return Home or Options -->
                    <div class="pt-5 border-t border-stone-100 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
                        <div class="flex items-center space-x-3">
                            ${isCompleted ? `
                                <button type="button" onclick="window.TempoUnclearMode.returnToHome()"
                                        class="text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                                    ← Return Home
                                </button>
                            ` : `
                                <button type="button" onclick="window.TempoUnclearMode.goBack()"
                                        class="text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                                    ← Back to edit needs
                                </button>
                            `}
                            <button type="button" onclick="window.TempoUnclearMode.startNewCheckIn()"
                                    class="text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                                Take another check
                            </button>
                        </div>
                        <button type="button" onclick="window.TempoUnclearMode.chooseDirection('unclear')"
                                class="text-xs font-semibold text-stone-500 hover:text-[#FF6B2C] transition cursor-pointer">
                            Stay in Unclear Mode for now →
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // INITIALIZATION & EXPORTS
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

    function init() {
        loadDraft();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    return {
        init,
        renderHome,
        startNewCheckIn,
        resumeDraft,
        resetFlowState,
        returnToHome,
        goToStage,
        goBack,
        finishCheckIn,
        chooseDirection,
        viewCompletedCheckIn,
        // Stage 1
        toggleConcern,
        toggleCustomInput,
        submitCustomConcern,
        submitStage1,
        // Stage 2
        toggleTopConcern,
        toggleFeeling,
        toggleCustomFeelingInput,
        submitCustomFeeling,
        submitStage2,
        // Stage 3
        toggleNoticedChange,
        toggleCustomNoticedInput,
        submitCustomNoticed,
        removeCustomNoticed,
        setImpactLevel,
        submitStage3,
        // Stage 4
        toggleBroadNeed,
        toggleNeedDetail,
        setCustomNeed,
        setPrimaryNeed,
        submitStage4,
        // Utilities
        getDraft: () => currentDraft,
        getCurrentDraft: () => currentDraft,
        getHistory: () => loadCompletedHistory(),
        clearDraft,
        adjustCompletedCheckIn,
        getVersions: loadAllVersions,
        getIncompleteVersions,
        getCompletedVersions
    };

})();
