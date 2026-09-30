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

    function loadDraft() {
        try {
            const uid = getUserId();
            const key = getStorageKey('draft');
            const raw = localStorage.getItem(key) || localStorage.getItem('tempo_unclear_draft');
            if (raw) {
                const parsed = JSON.parse(raw);
                if (parsed && parsed.status === 'in_progress') {
                    currentDraft = parsed;
                    return currentDraft;
                }
            }
        } catch (e) {
            console.warn('[TempoUnclearMode] Error loading draft:', e);
        }
        currentDraft = null;
        return null;
    }

    function saveDraft() {
        if (!currentDraft) return;
        currentDraft.updated_at = new Date().toISOString();
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
            const key = getStorageKey('history');
            const raw = localStorage.getItem(key);
            const history = raw ? JSON.parse(raw) : [];
            history.unshift(checkInRecord);
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

    function createNewDraft() {
        const uid = getUserId();
        return {
            id: 'uc_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
            user_id: uid,
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
        const todayObj = new Date();
        const formattedDate = todayObj.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric'
        });

        // Greeting
        const profile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
        let greetingText = 'Hi there 👋';
        if (profile) {
            const nameCandidate = profile.preferred_name || profile.display_name || profile.first_name;
            if (nameCandidate && typeof nameCandidate === 'string' && nameCandidate.trim().length >= 2 && nameCandidate.trim().length <= 14) {
                const clean = nameCandidate.trim().charAt(0).toUpperCase() + nameCandidate.trim().slice(1);
                greetingText = `Hi, ${clean} 👋`;
            }
        }

        const draft = loadDraft();
        const hasUnfinishedDraft = Boolean(draft && draft.status === 'in_progress' && draft.current_stage >= 1);
        const history = loadCompletedHistory();
        const lastCheckin = history.length > 0 ? history[0] : null;

        container.innerHTML = `
            <div id="unclear-home-view" class="space-y-6">
                <!-- Top Utility Row: Mode Selector + Current Date -->
                <div class="relative pb-1">
                    <div class="flex items-center justify-between gap-4">
                        <!-- Anchored Mode Selector Dropdown -->
                        <div id="home-mode-selector-wrapper" class="relative inline-block text-left">
                            <button id="btn-home-mode-selector" 
                                    type="button" 
                                    onclick="window.TempoMode.toggleModeDropdown(event)" 
                                    class="px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#FEF7EC] text-[#9A5B13] hover:bg-[#FDEBD0] border border-[#FDE5BE] transition flex items-center space-x-1.5 shadow-xs cursor-pointer"
                                    aria-haspopup="true"
                                    aria-expanded="false"
                                    title="Switch Tempo Mode">
                                <span>🧭</span>
                                <span class="font-extrabold">Unclear Mode</span>
                                <span class="text-[10px] ml-0.5 opacity-80">▾</span>
                            </button>
                            <div id="home-mode-selector-dropdown" class="hidden absolute left-0 mt-2 w-72 sm:w-80 bg-white rounded-2xl shadow-xl border border-[#EAE4DF] z-50 overflow-hidden" role="menu"></div>
                        </div>

                        <!-- Date Display -->
                        <div class="text-xs font-semibold text-[#8E8A85]">
                            ${escapeHTML(formattedDate)}
                        </div>
                    </div>
                </div>

                <!-- Primary Entry Card (Mode = Context, Not Hero) -->
                <div class="relative overflow-hidden rounded-3xl border border-[#FDE5BE] bg-gradient-to-br from-white via-[#FFFAF5] to-[#FFF3E8] p-6 sm:p-8 md:p-10 shadow-xs">
                    <div class="max-w-xl space-y-4 relative z-10">
                        <p class="text-xs sm:text-sm font-bold text-[#FF6B2C] tracking-wide">
                            ${escapeHTML(greetingText)}
                        </p>
                        <h2 class="font-heading text-2xl sm:text-3xl md:text-4xl font-extrabold text-[#202124] tracking-tight leading-tight">
                            Something feels off?
                        </h2>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed max-w-md">
                            You don't need to know why yet. Take a quick look at what's been going on lately, and what you might need from here.
                        </p>
                        <div class="pt-2 flex flex-col items-start gap-2.5">
                            <button type="button" onclick="window.TempoUnclearMode.startNewCheckIn()"
                                    class="btn-primary px-6 py-3 rounded-2xl text-xs sm:text-sm font-bold shadow-xs transition cursor-pointer flex items-center space-x-2 hover:opacity-95">
                                <span>Check in with myself</span>
                                <span>→</span>
                            </button>
                            ${hasUnfinishedDraft ? `
                                <button type="button" onclick="window.TempoUnclearMode.resumeDraft()"
                                        class="text-xs font-semibold text-[#FF6B2C] hover:text-[#B83D08] flex items-center space-x-1.5 transition cursor-pointer pt-1">
                                    <span>Continue where I left off</span>
                                    <span>→</span>
                                    <span class="text-stone-400 font-normal">(${draft.current_stage} of 4 steps)</span>
                                </button>
                            ` : (lastCheckin && lastCheckin.completed_at ? `
                                <div class="pt-1 flex items-center space-x-2 text-[11px] text-stone-400">
                                    <span>Last check-in: ${new Date(lastCheckin.completed_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                                    <button type="button" onclick="window.TempoUnclearMode.viewCompletedCheckIn('${lastCheckin.id}')"
                                            class="text-[#FF6B2C] hover:underline font-semibold cursor-pointer">
                                        View reflection →
                                    </button>
                                </div>
                            ` : '')}
                        </div>
                    </div>

                    <!-- Subtle Decorative Signpost Motif (Understated, non-intrusive) -->
                    <div class="hidden sm:block absolute right-8 top-1/2 -translate-y-1/2 opacity-75 pointer-events-none select-none">
                        <svg width="140" height="150" viewBox="0 0 140 150" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <rect x="62" y="15" width="16" height="125" rx="8" fill="#FFD2BA" fill-opacity="0.45" />
                            <!-- Signpost 1 (Right) -->
                            <path d="M40 38H115L128 50L115 62H40V38Z" fill="#FFE9DC" fill-opacity="0.8" />
                            <path d="M40 38H115L128 50L115 62H40" stroke="#FFD2BA" stroke-width="2" />
                            <!-- Signpost 2 (Left) -->
                            <path d="M100 78H25L12 90L25 102H100V78Z" fill="#FFE9DC" fill-opacity="0.65" />
                            <path d="M100 78H25L12 90L25 102H100" stroke="#FFD2BA" stroke-width="2" />
                        </svg>
                    </div>
                </div>

                <!-- Secondary Support Utilities: Quick Relief & Focus Zone -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <!-- Quick Relief Card -->
                    <div class="rounded-3xl border border-[#EAE4DF] bg-white p-5 sm:p-6 space-y-4 shadow-2xs flex flex-col justify-between hover:border-[#FFD2BA] transition">
                        <div class="space-y-2.5">
                            <div class="w-10 h-10 rounded-2xl bg-[#FFE9DC] text-[#B83D08] flex items-center justify-center text-lg font-bold shadow-xs">
                                ⚡
                            </div>
                            <div>
                                <h3 class="text-sm font-bold text-[#202124]">Quick Relief</h3>
                                <p class="text-xs text-[#6F6B68] mt-0.5 leading-relaxed">Take a short break to feel a bit calmer right now.</p>
                            </div>
                        </div>
                        <div>
                            <button type="button" onclick="if (window.TempoStressRelief) { window.TempoStressRelief.openModal(); } else if (window.TempoTriage) { window.TempoTriage.openBoxBreathingModal(); }"
                                    class="text-xs font-bold text-[#FF6B2C] hover:text-[#B83D08] flex items-center space-x-1 transition cursor-pointer">
                                <span>Open Quick Relief</span>
                                <span>→</span>
                            </button>
                        </div>
                    </div>

                    <!-- Focus Zone Card -->
                    <div class="rounded-3xl border border-[#EAE4DF] bg-white p-5 sm:p-6 space-y-4 shadow-2xs flex flex-col justify-between hover:border-[#FFD2BA] transition">
                        <div class="space-y-2.5">
                            <div class="w-10 h-10 rounded-2xl bg-[#FFE9DC] text-[#FF6B2C] flex items-center justify-center text-lg font-bold shadow-xs">
                                🎯
                            </div>
                            <div>
                                <h3 class="text-sm font-bold text-[#202124]">Focus Zone</h3>
                                <p class="text-xs text-[#6F6B68] mt-0.5 leading-relaxed">Work on your own flow with a timer and simple tools.</p>
                            </div>
                        </div>
                        <div>
                            <button type="button" onclick="if (window.TempoFocusZone && typeof window.TempoFocusZone.openQuickEntry === 'function') { window.TempoFocusZone.openQuickEntry(); } else if (window.TempoFocusZone && typeof window.TempoFocusZone.open === 'function') { window.TempoFocusZone.open(); } else if (window.TempoTriage) { window.TempoTriage.launchFocusMode(); }"
                                    class="text-xs font-bold text-[#FF6B2C] hover:text-[#B83D08] flex items-center space-x-1 transition cursor-pointer">
                                <span>Open Focus Zone</span>
                                <span>→</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // VIEW 2: CLARITY CHECK-IN ORCHESTRATOR
    // =========================================================================

    function startNewCheckIn() {
        currentDraft = createNewDraft();
        saveDraft();
        const uid = getUserId();
        sessionStorage.setItem(`tempo_unclear_in_flow_${uid}`, 'true');
        viewState = 'checkin';
        renderHome();
    }

    function resumeDraft() {
        if (!currentDraft) loadDraft();
        if (!currentDraft) {
            startNewCheckIn();
            return;
        }
        const uid = getUserId();
        sessionStorage.setItem(`tempo_unclear_in_flow_${uid}`, 'true');
        viewState = 'checkin';
        renderHome();
    }

    function returnToHome() {
        const uid = getUserId();
        sessionStorage.removeItem(`tempo_unclear_in_flow_${uid}`);
        viewState = 'home';
        renderHome();
    }

    function goToStage(stageNum) {
        if (!currentDraft) currentDraft = createNewDraft();
        currentDraft.current_stage = stageNum;
        saveDraft();
        renderHome();
    }

    function goBack() {
        if (!currentDraft) {
            returnToHome();
            return;
        }
        if (currentDraft.current_stage <= 1) {
            returnToHome();
        } else {
            goToStage(currentDraft.current_stage - 1);
        }
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
            if (window.TempoMode) {
                window.TempoMode.setMode('emergency');
            }
        } else if (directionKey === 'recovery') {
            if (window.TempoMode) {
                window.TempoMode.setMode('recovery');
            }
        } else if (directionKey === 'default') {
            if (window.TempoMode) {
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
            returnToHome();
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
                            <span>Back to Unclear Mode</span>
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

                    <!-- Bottom Navigation: Stay in Unclear Mode -->
                    <div class="pt-5 border-t border-stone-100 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
                        ${isCompleted ? `
                            <button type="button" onclick="window.TempoUnclearMode.returnToHome()"
                                    class="text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                                ← Back to Unclear Mode
                            </button>
                        ` : `
                            <button type="button" onclick="window.TempoUnclearMode.goBack()"
                                    class="text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                                ← Back to edit needs
                            </button>
                        `}
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
        clearDraft
    };

})();
