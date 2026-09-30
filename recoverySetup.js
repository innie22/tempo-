/**
 * TEMPO WELLBEING — RECOVERY MODE: RECOVERY ENTRY & SETUP FLOW (PHASE 3)
 * File: recoverySetup.js
 *
 * Architecture:
 * 1. First-time Recovery entry check (Welcome -> Setup or direct Home entry)
 * 2. 7-Stage Calm Recovery Setup Flow:
 *    Stage 1: Welcome ("Start my recovery check-in" vs "I'll explore first")
 *    Stage 2: Looking Back (Mind, Body, Behavior, Emotions chips + custom)
 *    Stage 3: What Helped (Body, Rest, Support, Boundaries chips + custom)
 *    Stage 4: Recovery Note (Warning signs, Helpers, Reminders, Support contacts)
 *    Stage 5: Build My Self-check (Reuses Phase 2 tracker system with reflection suggestions)
 *    Stage 6: First Self-check (Reuses Phase 2 Daily Check-in form & streak engine)
 *    Stage 7: Recovery Check-in Complete + Contextual Academic Next Step
 * 3. Draft preservation across stages & navigation
 * 4. Absolute rule: NEVER creates a "Recovery Plan" entity.
 */

(function () {
    'use strict';

    // =========================================================================
    // REFLECTION SUGGESTIONS DATA (STAGES 2 & 3)
    // =========================================================================

    const LOOKING_BACK_GROUPS = [
        {
            category: 'mind',
            label: 'Mind',
            items: [
                'Trouble focusing',
                'Thoughts kept racing',
                'Hard to switch off',
                'Felt mentally overloaded'
            ]
        },
        {
            category: 'body',
            label: 'Body',
            items: [
                'Felt tired',
                'Trouble sleeping',
                'Tension',
                'Low energy'
            ]
        },
        {
            category: 'behavior',
            label: 'Behavior',
            items: [
                'Put things off',
                'Worked for too long without stopping',
                'Stayed up later than usual',
                'Pulled away from things I normally do'
            ]
        },
        {
            category: 'emotions',
            label: 'Emotions',
            items: [
                'Felt overwhelmed',
                'Felt irritable',
                'Felt anxious',
                'Felt emotionally drained'
            ]
        }
    ];

    const WHAT_HELPED_GROUPS = [
        {
            category: 'body',
            label: 'Body',
            items: [
                'Eating something',
                'Drinking water',
                'Going outside',
                'Moving around for a while'
            ]
        },
        {
            category: 'rest',
            label: 'Rest',
            items: [
                'Taking a real break',
                'Sleeping',
                'Doing something unrelated to work',
                'Spending time somewhere quiet'
            ]
        },
        {
            category: 'support',
            label: 'Support',
            items: [
                'Talking to someone I trust',
                'Being around other people',
                'Asking someone for help'
            ]
        },
        {
            category: 'boundaries',
            label: 'Boundaries',
            items: [
                'Stopping work for the day',
                'Saying no to something',
                'Reducing what I was trying to finish',
                'Giving myself more time'
            ]
        }
    ];

    const GENTLE_REMINDER_SUGGESTIONS = [
        "I don't have to solve everything at once.",
        "Taking a real break is allowed.",
        "One next step is enough.",
        "I can slow things down before deciding what comes next."
    ];

    // =========================================================================
    // STATE & PERSISTENCE
    // =========================================================================

    function getUserId() {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') {
            const uid = window.TempoAuth.getCurrentUserId();
            if (uid) return uid;
        }
        return 'local_user';
    }

    function isIntroSeen() {
        const uid = getUserId();
        return localStorage.getItem(`tempo_recovery_intro_seen_${uid}`) === 'true';
    }

    function markIntroSeen() {
        const uid = getUserId();
        localStorage.setItem(`tempo_recovery_intro_seen_${uid}`, 'true');
    }

    function isSetupCompleted() {
        const uid = getUserId();
        return localStorage.getItem(`tempo_recovery_setup_status_${uid}`) === 'completed';
    }

    function markSetupCompleted() {
        const uid = getUserId();
        localStorage.setItem(`tempo_recovery_setup_status_${uid}`, 'completed');
        markIntroSeen();
    }

    function resetSetupState() {
        const uid = getUserId();
        localStorage.removeItem(`tempo_recovery_setup_status_${uid}`);
        localStorage.removeItem(`tempo_recovery_intro_seen_${uid}`);
        localStorage.removeItem(`tempo_recovery_setup_draft_${uid}`);
    }

    // In-memory setup session draft
    let setupDraft = {
        currentStage: 1,
        lookingBackSelections: [], // array of string names
        lookingBackCustom: [],
        whatHelpedSelections: [], // array of string names
        whatHelpedCustom: [],
        noteWarningSigns: [],
        noteHelpers: [],
        noteReminders: [],
        noteSupportPeople: [],
        selectedTrackerIds: []
    };

    function saveDraftToStorage() {
        try {
            const uid = getUserId();
            localStorage.setItem(`tempo_recovery_setup_draft_${uid}`, JSON.stringify(setupDraft));
        } catch (e) {}
    }

    function loadDraftFromStorage() {
        try {
            const uid = getUserId();
            const raw = localStorage.getItem(`tempo_recovery_setup_draft_${uid}`);
            if (raw) {
                const parsed = JSON.parse(raw);
                setupDraft = { ...setupDraft, ...parsed };
                if (!Array.isArray(setupDraft.selectedTrackerIds)) {
                    setupDraft.selectedTrackerIds = [];
                }
            }
        } catch (e) {}
    }

    // Determine if first-time Recovery visitor (Case 1 vs Case 2 & 3)
    function shouldShowFirstTimeWelcome() {
        if (isIntroSeen() || isSetupCompleted()) return false;
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function') {
            const trackers = window.TempoRecoverySelfCheck.getActiveTrackers();
            // If setup draft is in progress, allow it to continue
            if (setupDraft && setupDraft.currentStage > 1) {
                return true;
            }
            if (trackers.length > 0) {
                // User already has meaningful trackers -> Case 2: do not force setup
                return false;
            }
        }
        return true;
    }

    // =========================================================================
    // MODAL SHELL & NAVIGATION
    // =========================================================================

    function ensureModalMounted() {
        if (document.getElementById('modal-recovery-setup')) return;

        const modal = document.createElement('div');
        modal.id = 'modal-recovery-setup';
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-3 sm:p-4 hidden';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.innerHTML = `
            <div class="tempo-card max-w-2xl w-full p-6 sm:p-8 space-y-6 bg-white rounded-3xl shadow-2xl relative border border-[#EAE4DF] max-h-[92vh] overflow-y-auto">
                <button type="button" onclick="window.TempoRecoverySetup.exploreFirst()"
                        class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer" title="Exit">✕</button>
                <div id="recovery-setup-stage-container"></div>
            </div>
        `;
        document.body.appendChild(containerPlanConfirmModal());
        document.body.appendChild(modal);
    }

    function containerPlanConfirmModal() {
        const el = document.createElement('div');
        el.id = 'modal-recovery-plan-confirm';
        el.className = 'fixed inset-0 z-[60] flex items-center justify-center modal-backdrop p-4 hidden';
        el.innerHTML = `
            <div class="tempo-card max-w-md w-full p-6 space-y-5 bg-white rounded-3xl shadow-2xl relative border border-[#FFD2BA]">
                <div class="space-y-1 text-center">
                    <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">CREATE A PLAN</span>
                    <h3 class="font-heading text-xl font-extrabold text-[#202124]">Switch to Urgent Mode?</h3>
                    <p class="text-xs text-[#6F6B68] leading-relaxed">
                        Tempo's Urgent Plan helps when several tasks or deadlines need sorting out. Would you like to switch to Urgent Mode and create one?
                    </p>
                </div>
                <div class="pt-2 flex flex-col sm:flex-row items-center justify-center gap-2.5">
                    <button type="button" onclick="window.TempoRecoverySetup.confirmSwitchToUrgentPlan()"
                            class="btn-primary w-full sm:w-auto px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer">
                        Switch & create a plan →
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.closePlanConfirmModal()"
                            class="w-full sm:w-auto px-4 py-2.5 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition cursor-pointer">
                        Not now
                    </button>
                </div>
            </div>
        `;
        return el;
    }

    function open(stage = 1) {
        ensureModalMounted();
        loadDraftFromStorage();
        goToStage(stage);

        const modal = document.getElementById('modal-recovery-setup');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
            try {
                const uid = getUserId();
                sessionStorage.setItem(`tempo_recovery_setup_open_${uid}`, 'true');
            } catch (e) {}
        }
    }

    function close() {
        const modal = document.getElementById('modal-recovery-setup');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
        try {
            const uid = getUserId();
            sessionStorage.removeItem(`tempo_recovery_setup_open_${uid}`);
        } catch (e) {}
    }

    function exploreFirst() {
        markIntroSeen();
        close();
        if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
            window.TempoMode.renderRmodeHome();
        }
    }

    function goToStage(stageNum) {
        setupDraft.currentStage = stageNum;
        saveDraftToStorage();

        const container = document.getElementById('recovery-setup-stage-container');
        if (!container) return;

        if (stageNum === 1) renderStage1Welcome(container);
        else if (stageNum === 2) renderStage2LookingBack(container);
        else if (stageNum === 3) renderStage3WhatHelped(container);
        else if (stageNum === 4) renderStage4RecoveryNote(container);
        else if (stageNum === 5) renderStage5BuildSelfCheck(container);
        else if (stageNum === 6) renderStage6FirstSelfCheck(container);
        else if (stageNum === 7) renderStage7Complete(container);
    }

    // =========================================================================
    // STAGE 1: WELCOME
    // =========================================================================

    function renderStage1Welcome(container) {
        container.innerHTML = `
            <div class="space-y-6 text-center py-4">
                <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA] text-xs font-extrabold uppercase tracking-wider">
                    <span>🌱</span>
                    <span>RECOVERY MODE</span>
                </div>

                <div class="space-y-3 max-w-lg mx-auto">
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        Give yourself some space to recover.
                    </h2>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        Things may have slowed down, but you might still be carrying some of the stress.
                    </p>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        Recovery Mode gives you some space to slow down, look back, and notice what might help from here.
                    </p>
                </div>

                <div class="pt-4 flex flex-col items-center space-y-3 max-w-xs mx-auto">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(2)"
                            class="btn-primary w-full px-6 py-3 rounded-xl font-bold text-sm shadow-xs inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                        <span>Start my recovery check-in</span>
                        <span>→</span>
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.exploreFirst()"
                            class="text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition cursor-pointer">
                        I'll explore first
                    </button>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // STAGE 2: LOOKING BACK
    // =========================================================================

    function renderStage2LookingBack(container) {
        container.innerHTML = `
            <div class="space-y-5">
                <div class="flex items-center justify-between text-xs text-[#6F6B68]">
                    <span class="font-bold uppercase tracking-wider text-[#166545]">STEP 1 OF 5 · REFLECTION</span>
                    <span>Looking Back</span>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">What did you notice in yourself?</h3>
                    <p class="text-xs text-[#6F6B68]">
                        Think about the period you've just been through. Choose anything that feels familiar.
                    </p>
                </div>

                <!-- Reflection Chips Grouped -->
                <div class="space-y-4 pt-1">
                    ${LOOKING_BACK_GROUPS.map(g => `
                        <div class="space-y-2">
                            <span class="text-[11px] font-bold uppercase tracking-wider text-stone-500">${g.label}</span>
                            <div class="flex flex-wrap gap-2">
                                ${g.items.map(item => {
                                    const isSelected = setupDraft.lookingBackSelections.includes(item);
                                    return `
                                        <button type="button" onclick="window.TempoRecoverySetup.toggleLookingBack('${escapeHTML(item)}')"
                                                class="px-3.5 py-2 rounded-xl text-xs font-medium transition cursor-pointer border ${isSelected ? 'bg-[#FFE9DC] text-[#B83D08] border-[#FFD2BA] font-bold shadow-xs' : 'bg-white text-[#202124] border-stone-200 hover:border-stone-300'}">
                                            ${isSelected ? '✓ ' : ''}${escapeHTML(item)}
                                        </button>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    `).join('')}

                    ${setupDraft.lookingBackCustom.length > 0 ? `
                        <div class="space-y-2">
                            <span class="text-[11px] font-bold uppercase tracking-wider text-stone-500">Custom</span>
                            <div class="flex flex-wrap gap-2">
                                ${setupDraft.lookingBackCustom.map(item => `
                                    <button type="button" onclick="window.TempoRecoverySetup.toggleLookingBack('${escapeHTML(item)}')"
                                            class="px-3.5 py-2 rounded-xl text-xs font-bold transition cursor-pointer border bg-[#FFE9DC] text-[#B83D08] border-[#FFD2BA] shadow-xs">
                                        ✓ ${escapeHTML(item)}
                                    </button>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- Add Custom Input -->
                    <div class="pt-2 flex items-center space-x-2">
                        <input type="text" id="input-custom-looking-back" placeholder="Add something you noticed..."
                               class="flex-1 px-3 py-2 rounded-xl border border-stone-200 text-xs text-[#202124] focus:outline-none focus:border-[#166545]">
                        <button type="button" onclick="window.TempoRecoverySetup.addCustomLookingBack()"
                                class="px-3 py-2 rounded-xl bg-stone-100 hover:bg-stone-200 text-xs font-bold text-[#202124] transition cursor-pointer">
                            + Add
                        </button>
                    </div>
                </div>

                <!-- Footer Nav -->
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(1)"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ← Back
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(3)"
                            class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                        <span>Continue</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    function toggleLookingBack(item) {
        const idx = setupDraft.lookingBackSelections.indexOf(item);
        if (idx === -1) {
            setupDraft.lookingBackSelections.push(item);
        } else {
            setupDraft.lookingBackSelections.splice(idx, 1);
        }
        renderStage2LookingBack(document.getElementById('recovery-setup-stage-container'));
    }

    function addCustomLookingBack() {
        const input = document.getElementById('input-custom-looking-back');
        if (!input || !input.value.trim()) return;
        const text = input.value.trim();
        if (!setupDraft.lookingBackCustom.includes(text)) {
            setupDraft.lookingBackCustom.push(text);
        }
        if (!setupDraft.lookingBackSelections.includes(text)) {
            setupDraft.lookingBackSelections.push(text);
        }
        renderStage2LookingBack(document.getElementById('recovery-setup-stage-container'));
    }

    // =========================================================================
    // STAGE 3: WHAT HELPED
    // =========================================================================

    function renderStage3WhatHelped(container) {
        container.innerHTML = `
            <div class="space-y-5">
                <div class="flex items-center justify-between text-xs text-[#6F6B68]">
                    <span class="font-bold uppercase tracking-wider text-[#166545]">STEP 2 OF 5 · REFLECTION</span>
                    <span>What Helped</span>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">What seemed to make things a little easier?</h3>
                    <p class="text-xs text-[#6F6B68]">
                        Choose anything that felt helpful, even if it only helped a little.
                    </p>
                </div>

                <!-- Reflection Chips Grouped -->
                <div class="space-y-4 pt-1">
                    ${WHAT_HELPED_GROUPS.map(g => `
                        <div class="space-y-2">
                            <span class="text-[11px] font-bold uppercase tracking-wider text-stone-500">${g.label}</span>
                            <div class="flex flex-wrap gap-2">
                                ${g.items.map(item => {
                                    const isSelected = setupDraft.whatHelpedSelections.includes(item);
                                    return `
                                        <button type="button" onclick="window.TempoRecoverySetup.toggleWhatHelped('${escapeHTML(item)}')"
                                                class="px-3.5 py-2 rounded-xl text-xs font-medium transition cursor-pointer border ${isSelected ? 'bg-[#EDF7F1] text-[#166545] border-[#CDE9DA] font-bold shadow-xs' : 'bg-white text-[#202124] border-stone-200 hover:border-stone-300'}">
                                            ${isSelected ? '✓ ' : ''}${escapeHTML(item)}
                                        </button>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    `).join('')}

                    ${setupDraft.whatHelpedCustom.length > 0 ? `
                        <div class="space-y-2">
                            <span class="text-[11px] font-bold uppercase tracking-wider text-stone-500">Custom</span>
                            <div class="flex flex-wrap gap-2">
                                ${setupDraft.whatHelpedCustom.map(item => `
                                    <button type="button" onclick="window.TempoRecoverySetup.toggleWhatHelped('${escapeHTML(item)}')"
                                            class="px-3.5 py-2 rounded-xl text-xs font-bold transition cursor-pointer border bg-[#EDF7F1] text-[#166545] border-[#CDE9DA] shadow-xs">
                                        ✓ ${escapeHTML(item)}
                                    </button>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- Add Custom Input -->
                    <div class="pt-2 flex items-center space-x-2">
                        <input type="text" id="input-custom-what-helped" placeholder="Add something that helped you..."
                               class="flex-1 px-3 py-2 rounded-xl border border-stone-200 text-xs text-[#202124] focus:outline-none focus:border-[#166545]">
                        <button type="button" onclick="window.TempoRecoverySetup.addCustomWhatHelped()"
                                class="px-3 py-2 rounded-xl bg-stone-100 hover:bg-stone-200 text-xs font-bold text-[#202124] transition cursor-pointer">
                            + Add
                        </button>
                    </div>
                </div>

                <!-- Footer Nav -->
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(2)"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ← Back
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(4)"
                            class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                        <span>Continue</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    function toggleWhatHelped(item) {
        const idx = setupDraft.whatHelpedSelections.indexOf(item);
        if (idx === -1) {
            setupDraft.whatHelpedSelections.push(item);
        } else {
            setupDraft.whatHelpedSelections.splice(idx, 1);
        }
        renderStage3WhatHelped(document.getElementById('recovery-setup-stage-container'));
    }

    function addCustomWhatHelped() {
        const input = document.getElementById('input-custom-what-helped');
        if (!input || !input.value.trim()) return;
        const text = input.value.trim();
        if (!setupDraft.whatHelpedCustom.includes(text)) {
            setupDraft.whatHelpedCustom.push(text);
        }
        if (!setupDraft.whatHelpedSelections.includes(text)) {
            setupDraft.whatHelpedSelections.push(text);
        }
        renderStage3WhatHelped(document.getElementById('recovery-setup-stage-container'));
    }

    // =========================================================================
    // STAGE 4: RECOVERY NOTE
    // =========================================================================

    function renderStage4RecoveryNote(container) {
        // Suggested warning signs from Looking Back
        const candidateWarningSigns = setupDraft.lookingBackSelections.length > 0
            ? setupDraft.lookingBackSelections
            : ['Trouble focusing', 'Hard to switch off', 'Sleeping later than usual'];

        // Suggested helpers from What Helped
        const candidateHelpers = setupDraft.whatHelpedSelections.length > 0
            ? setupDraft.whatHelpedSelections
            : ['Going outside', 'Taking a real break', 'Drinking water'];

        container.innerHTML = `
            <div class="space-y-5">
                <div class="flex items-center justify-between text-xs text-[#6F6B68]">
                    <span class="font-bold uppercase tracking-wider text-[#FF6B2C]">STEP 3 OF 5 · RECOVERY NOTE (OPTIONAL)</span>
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(5)"
                            class="text-xs text-stone-400 hover:text-stone-700 transition cursor-pointer">
                        Skip this step
                    </button>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">Create your Recovery Note</h3>
                    <p class="text-xs text-[#6F6B68]">
                        Keep a few things you'd like Tempo to remind you of when things feel heavy.
                    </p>
                </div>

                <div class="space-y-5 pt-1">
                    <!-- SECTION 1: WARNING SIGNS -->
                    <div class="p-4 rounded-2xl bg-stone-50 border border-stone-200 space-y-2.5">
                        <span class="text-xs font-extrabold uppercase tracking-wider text-[#B83D08]">
                            1. When I start getting overwhelmed...
                        </span>
                        <p class="text-[11px] text-stone-500">Suggested from what you noticed:</p>
                        <div class="space-y-1.5" id="note-warning-signs-list">
                            ${candidateWarningSigns.map(item => {
                                const isChecked = setupDraft.noteWarningSigns.includes(item);
                                return `
                                    <label class="flex items-center space-x-2.5 text-xs text-[#202124] cursor-pointer">
                                        <input type="checkbox" onchange="window.TempoRecoverySetup.toggleNoteItem('warning_sign', '${escapeHTML(item)}')"
                                               ${isChecked ? 'checked' : ''} class="rounded text-[#B83D08] focus:ring-[#B83D08]">
                                        <span>${escapeHTML(item)}</span>
                                    </label>
                                `;
                            }).join('')}
                        </div>
                        <div class="flex items-center space-x-2 pt-1">
                            <input type="text" id="input-note-custom-sign" placeholder="+ Add my own warning sign..."
                                   class="flex-1 px-3 py-1.5 rounded-xl border border-stone-200 text-xs text-[#202124] focus:outline-none focus:border-[#B83D08]">
                            <button type="button" onclick="window.TempoRecoverySetup.addCustomNoteItem('warning_sign')"
                                    class="px-3 py-1.5 rounded-xl bg-white border border-stone-300 text-xs font-bold text-stone-700 transition cursor-pointer">
                                Add
                            </button>
                        </div>
                    </div>

                    <!-- SECTION 2: HELPERS -->
                    <div class="p-4 rounded-2xl bg-stone-50 border border-stone-200 space-y-2.5">
                        <span class="text-xs font-extrabold uppercase tracking-wider text-[#166545]">
                            2. Things that seem to help...
                        </span>
                        <p class="text-[11px] text-stone-500">Suggested from what helped you:</p>
                        <div class="space-y-1.5" id="note-helpers-list">
                            ${candidateHelpers.map(item => {
                                const isChecked = setupDraft.noteHelpers.includes(item);
                                return `
                                    <label class="flex items-center space-x-2.5 text-xs text-[#202124] cursor-pointer">
                                        <input type="checkbox" onchange="window.TempoRecoverySetup.toggleNoteItem('helper', '${escapeHTML(item)}')"
                                               ${isChecked ? 'checked' : ''} class="rounded text-[#166545] focus:ring-[#166545]">
                                        <span>${escapeHTML(item)}</span>
                                    </label>
                                `;
                            }).join('')}
                        </div>
                        <div class="flex items-center space-x-2 pt-1">
                            <input type="text" id="input-note-custom-helper" placeholder="+ Add my own helpful thing..."
                                   class="flex-1 px-3 py-1.5 rounded-xl border border-stone-200 text-xs text-[#202124] focus:outline-none focus:border-[#166545]">
                            <button type="button" onclick="window.TempoRecoverySetup.addCustomNoteItem('helper')"
                                    class="px-3 py-1.5 rounded-xl bg-white border border-stone-300 text-xs font-bold text-stone-700 transition cursor-pointer">
                                Add
                            </button>
                        </div>
                    </div>

                    <!-- SECTION 3: REMINDERS -->
                    <div class="p-4 rounded-2xl bg-stone-50 border border-stone-200 space-y-2.5">
                        <span class="text-xs font-extrabold uppercase tracking-wider text-[#1E40AF]">
                            3. What I want to remind myself...
                        </span>
                        <div class="space-y-1.5">
                            ${GENTLE_REMINDER_SUGGESTIONS.map(rem => {
                                const isChecked = setupDraft.noteReminders.includes(rem);
                                return `
                                    <label class="flex items-center space-x-2.5 text-xs text-[#202124] cursor-pointer">
                                        <input type="checkbox" onchange="window.TempoRecoverySetup.toggleNoteItem('reminder', '${escapeHTML(rem)}')"
                                               ${isChecked ? 'checked' : ''} class="rounded text-[#1E40AF] focus:ring-[#1E40AF]">
                                        <span>"${escapeHTML(rem)}"</span>
                                    </label>
                                `;
                            }).join('')}
                        </div>
                        <div class="flex items-center space-x-2 pt-1">
                            <input type="text" id="input-note-custom-reminder" placeholder="+ Write my own reminder..."
                                   class="flex-1 px-3 py-1.5 rounded-xl border border-stone-200 text-xs text-[#202124] focus:outline-none focus:border-[#1E40AF]">
                            <button type="button" onclick="window.TempoRecoverySetup.addCustomNoteItem('reminder')"
                                    class="px-3 py-1.5 rounded-xl bg-white border border-stone-300 text-xs font-bold text-stone-700 transition cursor-pointer">
                                Add
                            </button>
                        </div>
                    </div>

                    <!-- SECTION 4: SUPPORT PEOPLE -->
                    <div class="p-4 rounded-2xl bg-stone-50 border border-stone-200 space-y-2.5">
                        <span class="text-xs font-extrabold uppercase tracking-wider text-[#7C3AED]">
                            4. People I can reach out to...
                        </span>
                        <p class="text-[11px] text-stone-500">Add someone you may want to reach out to when things feel like a lot:</p>
                        ${setupDraft.noteSupportPeople.length > 0 ? `
                            <div class="space-y-1">
                                ${setupDraft.noteSupportPeople.map((p, idx) => `
                                    <div class="flex items-center justify-between p-2 rounded-xl bg-white border border-stone-200 text-xs">
                                        <span class="font-bold text-[#202124]">${escapeHTML(p.name)} <span class="text-stone-400 font-normal">(${escapeHTML(p.relationship || 'Support')})</span></span>
                                        <button type="button" onclick="window.TempoRecoverySetup.removeSupportPerson(${idx})" class="text-stone-400 hover:text-red-600 font-bold">✕</button>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                            <input type="text" id="input-setup-person-name" placeholder="Name (e.g. Nhung)"
                                   class="px-3 py-1.5 rounded-xl border border-stone-200 text-xs text-[#202124] focus:outline-none focus:border-[#7C3AED]">
                            <div class="flex items-center space-x-2">
                                <input type="text" id="input-setup-person-rel" placeholder="Relationship (e.g. Friend)"
                                       class="flex-1 px-3 py-1.5 rounded-xl border border-stone-200 text-xs text-[#202124] focus:outline-none focus:border-[#7C3AED]">
                                <button type="button" onclick="window.TempoRecoverySetup.addSupportPersonFromSetup()"
                                        class="px-3 py-1.5 rounded-xl bg-white border border-stone-300 text-xs font-bold text-stone-700 transition cursor-pointer">
                                    + Add
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Footer Nav -->
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(3)"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ← Back
                    </button>
                    <div class="flex items-center space-x-3">
                        <button type="button" onclick="window.TempoRecoverySetup.goToStage(5)"
                                class="text-xs font-semibold text-stone-400 hover:text-stone-700 transition cursor-pointer">
                            Skip for now
                        </button>
                        <button type="button" onclick="window.TempoRecoverySetup.saveNoteAndContinue()"
                                class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                            <span>Continue</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function toggleNoteItem(type, text) {
        let list;
        if (type === 'warning_sign') list = setupDraft.noteWarningSigns;
        else if (type === 'helper') list = setupDraft.noteHelpers;
        else if (type === 'reminder') list = setupDraft.noteReminders;
        if (!list) return;

        const idx = list.indexOf(text);
        if (idx === -1) list.push(text);
        else list.splice(idx, 1);
    }

    function addCustomNoteItem(type) {
        let inputId, list;
        if (type === 'warning_sign') { inputId = 'input-note-custom-sign'; list = setupDraft.noteWarningSigns; }
        else if (type === 'helper') { inputId = 'input-note-custom-helper'; list = setupDraft.noteHelpers; }
        else if (type === 'reminder') { inputId = 'input-note-custom-reminder'; list = setupDraft.noteReminders; }

        const input = document.getElementById(inputId);
        if (!input || !input.value.trim() || !list) return;

        const val = input.value.trim();
        if (!list.includes(val)) list.push(val);
        input.value = '';
        renderStage4RecoveryNote(document.getElementById('recovery-setup-stage-container'));
    }

    function addSupportPersonFromSetup() {
        const nameInput = document.getElementById('input-setup-person-name');
        const relInput = document.getElementById('input-setup-person-rel');
        if (!nameInput || !nameInput.value.trim()) return;

        setupDraft.noteSupportPeople.push({
            name: nameInput.value.trim(),
            relationship: relInput ? relInput.value.trim() : ''
        });

        nameInput.value = '';
        if (relInput) relInput.value = '';
        renderStage4RecoveryNote(document.getElementById('recovery-setup-stage-container'));
    }

    function removeSupportPerson(idx) {
        setupDraft.noteSupportPeople.splice(idx, 1);
        renderStage4RecoveryNote(document.getElementById('recovery-setup-stage-container'));
    }

    function saveNoteAndContinue() {
        // Collect items into Recovery Note
        if (window.TempoRecoveryNote && typeof window.TempoRecoveryNote.setNoteItems === 'function') {
            const items = [];
            setupDraft.noteWarningSigns.forEach(text => items.push({ type: 'warning_sign', text, source: 'reflection' }));
            setupDraft.noteHelpers.forEach(text => items.push({ type: 'helper', text, source: 'reflection' }));
            setupDraft.noteReminders.forEach(text => items.push({ type: 'reminder', text, source: 'suggestion' }));
            setupDraft.noteSupportPeople.forEach(p => items.push({ type: 'support_person', text: p.name, metadata: { relationship: p.relationship }, source: 'custom' }));

            if (items.length > 0) {
                window.TempoRecoveryNote.setNoteItems(items);
            }
        }
        goToStage(5);
    }

    // =========================================================================
    // STAGE 5: BUILD MY SELF-CHECK (REUSES PHASE 2 TRACKERS)
    // =========================================================================

    // Cache for candidate suggestions in Stage 5 so methods can look up full configuration
    let candidateSuggestionsCache = [];

    function addSuggestedTracker(name) {
        if (!name || typeof name !== 'string') return;
        const trimmed = name.trim();
        if (!trimmed) return;

        if (!window.TempoRecoverySelfCheck || typeof window.TempoRecoverySelfCheck.createTracker !== 'function') return;

        // Check if already active to prevent duplicates
        const activeTrackers = window.TempoRecoverySelfCheck.getActiveTrackers ? window.TempoRecoverySelfCheck.getActiveTrackers() : [];
        const existing = activeTrackers.find(t => t.name.toLowerCase() === trimmed.toLowerCase());
        if (existing) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast(`"${trimmed}" is already in your Self-check.`);
            }
            return;
        }

        // Find suggestion template in cache or standard suggestions
        let tmpl = candidateSuggestionsCache.find(s => s.name.toLowerCase() === trimmed.toLowerCase());
        if (!tmpl) {
            tmpl = {
                name: trimmed,
                category: 'stress_sign',
                check_method: 'yes_no',
                direction: 'higher_concerning',
                pattern_notices_enabled: true
            };
        }

        const payload = {
            name: tmpl.name,
            category: tmpl.category || 'stress_sign',
            check_method: tmpl.check_method || 'yes_no',
            direction: tmpl.direction || (tmpl.category === 'supportive' ? 'higher_better' : 'higher_concerning'),
            quantity_unit: tmpl.quantity_unit || '',
            scale_min: tmpl.scale_min !== undefined ? tmpl.scale_min : 1,
            scale_max: tmpl.scale_max !== undefined ? tmpl.scale_max : 5,
            scale_min_label: tmpl.scale_min_label || 'Very low',
            scale_max_label: tmpl.scale_max_label || 'Very high',
            pattern_notices_enabled: Boolean(tmpl.pattern_notices_enabled)
        };

        const newTracker = window.TempoRecoverySelfCheck.createTracker(payload);
        onTrackerSaved(newTracker);

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(`✓ Added "${tmpl.name}" to Self-check.`);
        }
    }

    function removeTrackerFromSetup(id) {
        if (!window.TempoRecoverySelfCheck || typeof window.TempoRecoverySelfCheck.archiveTracker !== 'function') return;
        window.TempoRecoverySelfCheck.archiveTracker(id);
        onTrackerArchived(id);
    }

    function onTrackerSaved(savedTracker) {
        if (!savedTracker || !savedTracker.id) return;
        if (!setupDraft.selectedTrackerIds) setupDraft.selectedTrackerIds = [];
        if (!setupDraft.selectedTrackerIds.includes(savedTracker.id)) {
            setupDraft.selectedTrackerIds.push(savedTracker.id);
        }
        saveDraftToStorage();

        const container = document.getElementById('recovery-setup-stage-container');
        if (container) {
            if (setupDraft.currentStage === 5) {
                renderStage5BuildSelfCheck(container);
            } else if (setupDraft.currentStage === 6) {
                renderStage6FirstSelfCheck(container);
            }
        }
    }

    function onTrackerArchived(trackerId) {
        if (setupDraft.selectedTrackerIds) {
            setupDraft.selectedTrackerIds = setupDraft.selectedTrackerIds.filter(id => id !== trackerId);
            saveDraftToStorage();
        }
        const container = document.getElementById('recovery-setup-stage-container');
        if (container && setupDraft.currentStage === 5) {
            renderStage5BuildSelfCheck(container);
        }
    }

    function openAddTrackerPrefill(name, category, check_method) {
        if (!name) return;
        const trimmed = name.trim();
        const activeTrackers = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function')
            ? window.TempoRecoverySelfCheck.getActiveTrackers()
            : [];
        if (activeTrackers.some(t => t.name.toLowerCase() === trimmed.toLowerCase())) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast(`"${trimmed}" is already in your Self-check.`);
            }
            return;
        }

        // Add tracker directly using template configuration
        addSuggestedTracker(name);
    }

    function renderStage5BuildSelfCheck(container) {
        const activeTrackers = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function')
            ? window.TempoRecoverySelfCheck.getActiveTrackers()
            : [];

        // Build candidate suggestions from Stage 2 & Stage 3 reflections and standard suggestions
        candidateSuggestionsCache = [];
        const seenNames = new Set();

        (setupDraft.lookingBackSelections || []).forEach(name => {
            const trimmed = name.trim();
            if (trimmed && !seenNames.has(trimmed.toLowerCase())) {
                seenNames.add(trimmed.toLowerCase());
                candidateSuggestionsCache.push({
                    name: trimmed,
                    category: 'stress_sign',
                    check_method: 'yes_no',
                    direction: 'higher_concerning',
                    pattern_notices_enabled: true
                });
            }
        });

        (setupDraft.whatHelpedSelections || []).forEach(name => {
            const trimmed = name.trim();
            if (trimmed && !seenNames.has(trimmed.toLowerCase())) {
                seenNames.add(trimmed.toLowerCase());
                candidateSuggestionsCache.push({
                    name: trimmed,
                    category: 'supportive',
                    check_method: 'yes_no',
                    direction: 'higher_better',
                    pattern_notices_enabled: false
                });
            }
        });

        // Add standard helpful suggestions if not already added by reflection
        const standardSuggestions = [
            { name: 'Trouble focusing', category: 'stress_sign', check_method: 'yes_no', direction: 'higher_concerning', pattern_notices_enabled: true },
            { name: 'Feeling overwhelmed', category: 'stress_sign', check_method: 'scale', scale_min: 1, scale_max: 5, scale_min_label: 'Low', scale_max_label: 'Very high', direction: 'higher_concerning', pattern_notices_enabled: true },
            { name: 'Sleep quality', category: 'supportive', check_method: 'scale', scale_min: 1, scale_max: 5, scale_min_label: 'Poor', scale_max_label: 'Restful', direction: 'higher_better', pattern_notices_enabled: false },
            { name: 'Took a real break', category: 'supportive', check_method: 'yes_no', direction: 'higher_better', pattern_notices_enabled: false },
            { name: 'Water', category: 'neutral', check_method: 'quantity', quantity_unit: 'glasses', direction: 'higher_better', pattern_notices_enabled: false },
            { name: 'Went outside', category: 'supportive', check_method: 'yes_no', direction: 'higher_better', pattern_notices_enabled: false }
        ];

        standardSuggestions.forEach(s => {
            if (!seenNames.has(s.name.toLowerCase())) {
                seenNames.add(s.name.toLowerCase());
                candidateSuggestionsCache.push(s);
            }
        });

        container.innerHTML = `
            <div class="space-y-5">
                <div class="flex items-center justify-between text-xs text-[#6F6B68]">
                    <span class="font-bold uppercase tracking-wider text-[#166545]">STEP 4 OF 5 · SELF-CHECK</span>
                    <span>Build My Self-check</span>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                        ${activeTrackers.length > 0 ? "Your Self-check" : "What would you like to keep track of?"}
                    </h3>
                    <p class="text-xs text-[#6F6B68]">
                        ${activeTrackers.length > 0 ? `You're currently keeping track of ${activeTrackers.length} thing${activeTrackers.length === 1 ? '' : 's'}. You can add more from what you noticed or continue.` : "Choose a few things that feel useful to check in with. Suggested items are completely optional."}
                    </p>
                </div>

                <!-- Existing Active Trackers Display -->
                ${activeTrackers.length > 0 ? `
                    <div class="p-4 rounded-2xl bg-[#EDF7F1]/60 border border-[#CDE9DA] space-y-2.5">
                        <div class="flex items-center justify-between text-xs font-bold text-[#166545]">
                            <span id="setup-active-trackers-count">Active Trackers (${activeTrackers.length})</span>
                            <button type="button" onclick="window.TempoRecoverySelfCheck.openManage()" class="text-xs font-bold underline hover:text-[#0E4A32] cursor-pointer">
                                Manage trackers
                            </button>
                        </div>
                        <div class="flex flex-wrap gap-2 pt-1" id="setup-active-trackers-list">
                            ${activeTrackers.map(t => `
                                <span class="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white border border-[#CDE9DA] text-xs font-semibold text-[#202124] shadow-2xs">
                                    <span>${t.category === 'stress_sign' ? '🔴' : (t.category === 'supportive' ? '🟢' : '🔵')}</span>
                                    <span>${escapeHTML(t.name)}</span>
                                    <button type="button" onclick="window.TempoRecoverySetup.removeTrackerFromSetup('${t.id}')"
                                            class="text-stone-400 hover:text-red-500 font-bold ml-1 transition cursor-pointer" title="Remove">✕</button>
                                </span>
                            `).join('')}
                        </div>
                    </div>
                ` : `
                    <div class="p-4 rounded-2xl bg-stone-50 border border-stone-200 text-center text-xs text-[#6F6B68]">
                        No trackers added yet. Pick from the suggestions below or add a custom one. (Self-check is optional)
                    </div>
                `}

                <!-- Suggestions to Add -->
                <div class="space-y-2.5 pt-1">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-extrabold uppercase tracking-wider text-stone-500">
                            Suggested things to track:
                        </span>
                        <span class="text-[11px] text-stone-400">Suggestions are optional</span>
                    </div>
                    <div class="space-y-2 max-h-[36vh] overflow-y-auto pr-1">
                        ${candidateSuggestionsCache.slice(0, 6).map(s => {
                            const isAdded = activeTrackers.some(t => t.name.toLowerCase() === s.name.toLowerCase());
                            return `
                                <div class="p-3 rounded-2xl border ${isAdded ? 'border-[#CDE9DA] bg-[#F7FCF9]' : 'border-stone-200 bg-white'} flex items-center justify-between shadow-2xs transition">
                                    <div class="flex items-center space-x-2.5">
                                        <span class="text-base">${s.category === 'stress_sign' ? '🔴' : (s.category === 'supportive' ? '🟢' : '🔵')}</span>
                                        <div>
                                            <div class="flex items-center space-x-2">
                                                <h4 class="text-xs font-bold text-[#202124]">${escapeHTML(s.name)}</h4>
                                                ${isAdded ? '<span class="text-[10px] font-bold text-[#166545] bg-[#EDF7F1] px-1.5 py-0.5 rounded-full border border-[#CDE9DA]">In Self-check</span>' : ''}
                                            </div>
                                            <span class="text-[10px] text-stone-400">
                                                ${s.category === 'stress_sign' ? 'Sign of stress' : (s.category === 'supportive' ? 'Supportive habit' : 'General')} · ${s.check_method === 'scale' ? 'Scale 1–5' : (s.check_method === 'quantity' ? `Quantity (${s.quantity_unit || 'units'})` : 'Yes / No')}
                                            </span>
                                        </div>
                                    </div>
                                    ${isAdded ? `
                                        <span class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA] inline-flex items-center space-x-1">
                                            <span>✓ Added</span>
                                        </span>
                                    ` : `
                                        <button type="button" onclick="window.TempoRecoverySetup.addSuggestedTracker('${escapeHTML(s.name)}')"
                                                class="btn-primary px-3.5 py-1.5 rounded-xl text-xs font-bold shadow-xs transition cursor-pointer hover:opacity-95">
                                            + Add
                                        </button>
                                    `}
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>

                <!-- Custom Add Button -->
                <div class="pt-1 flex items-center space-x-3">
                    <button type="button" onclick="window.TempoRecoverySelfCheck.openTrackerModal()"
                            class="px-4 py-2 rounded-xl border border-stone-300 hover:border-stone-400 text-xs font-bold text-[#202124] transition cursor-pointer flex items-center space-x-1.5">
                        <span>+ Add custom tracker</span>
                    </button>
                </div>

                <!-- Footer Nav -->
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(4)"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ← Back
                    </button>
                    <div class="flex items-center space-x-3">
                        <button type="button" onclick="window.TempoRecoverySetup.goToStage(6)"
                                class="text-xs font-semibold text-stone-400 hover:text-stone-700 transition cursor-pointer">
                            ${activeTrackers.length === 0 ? 'Skip for now' : 'Continue'}
                        </button>
                        <button type="button" onclick="window.TempoRecoverySetup.goToStage(6)"
                                class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                            <span>Continue</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // STAGE 6: FIRST SELF-CHECK (REUSES PHASE 2 DAILY SELF-CHECK)
    // =========================================================================

    function renderStage6FirstSelfCheck(container) {
        const activeTrackers = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function')
            ? window.TempoRecoverySelfCheck.getActiveTrackers()
            : [];

        if (activeTrackers.length === 0) {
            // Case: No trackers configured (Valid: zero trackers)
            container.innerHTML = `
                <div class="space-y-6 text-center py-4">
                    <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-stone-100 text-stone-600 border border-stone-200 text-xs font-extrabold uppercase tracking-wider">
                        <span>SELF-CHECK</span>
                    </div>

                    <div class="space-y-2 max-w-md mx-auto">
                        <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                            You haven't set anything up to check in with yet.
                        </h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                            That's completely fine. You can create your Self-check anytime from Recovery Home.
                        </p>
                    </div>

                    <div class="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
                        <button type="button" onclick="window.TempoRecoverySetup.goToStage(5)"
                                class="px-4 py-2.5 rounded-xl border border-stone-300 hover:border-stone-400 text-xs font-bold text-[#202124] transition cursor-pointer">
                            + Set up Self-check
                        </button>
                        <button type="button" onclick="window.TempoRecoverySetup.goToStage(7)"
                                class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer">
                            Continue →
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        const todayCheckin = window.TempoRecoverySelfCheck.getTodayCheckin();
        if (todayCheckin) {
            // Already checked in today
            const obs = window.TempoRecoverySelfCheck.getObservationsForCheckin(todayCheckin.id);
            const answeredCount = obs.filter(o => o.status === 'answered').length;

            container.innerHTML = `
                <div class="space-y-6 text-center py-4">
                    <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA] text-xs font-bold">
                        <span>✓ Checked in today</span>
                    </div>

                    <div class="space-y-2 max-w-md mx-auto">
                        <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                            You've already checked in today
                        </h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68]">
                            You checked in on ${answeredCount} of ${activeTrackers.length} things.
                        </p>
                    </div>

                    <div class="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
                        <button type="button" onclick="window.TempoRecoverySelfCheck.openViewToday()"
                                class="px-4 py-2 rounded-xl text-xs font-bold text-[#166545] hover:bg-[#EDF7F1] transition cursor-pointer">
                            View today's check-in
                        </button>
                        <button type="button" onclick="window.TempoRecoverySetup.goToStage(7)"
                                class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer">
                            Continue →
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        // Render questionnaire review and check-in launch
        container.innerHTML = `
            <div class="space-y-5">
                <div class="flex items-center justify-between text-xs text-[#6F6B68]">
                    <span class="font-bold uppercase tracking-wider text-[#166545]">STEP 5 OF 5 · FIRST CHECK-IN</span>
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(7)"
                            class="text-xs text-stone-400 hover:text-stone-700 transition cursor-pointer">
                        Skip for today
                    </button>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">How have things been today?</h3>
                    <p class="text-xs text-[#6F6B68]">Check in with whatever feels useful. You don't have to answer everything.</p>
                </div>

                <!-- Your Active Trackers in Questionnaire -->
                <div class="space-y-2 pt-1">
                    <span class="text-xs font-extrabold uppercase tracking-wider text-stone-500">
                        Things you're checking in on (${activeTrackers.length}):
                    </span>
                    <div class="space-y-2 max-h-[32vh] overflow-y-auto pr-1" id="setup-stage6-trackers-list">
                        ${activeTrackers.map(t => `
                            <div class="p-3.5 rounded-2xl border border-stone-200 bg-white flex items-center justify-between shadow-2xs">
                                <div class="flex items-center space-x-2.5">
                                    <span class="text-base">${t.category === 'stress_sign' ? '🔴' : (t.category === 'supportive' ? '🟢' : '🔵')}</span>
                                    <div>
                                        <h4 class="text-xs font-bold text-[#202124]">${escapeHTML(t.name)}</h4>
                                        <span class="text-[10px] text-stone-400">
                                            ${t.category === 'stress_sign' ? 'Sign of stress' : (t.category === 'supportive' ? 'Supportive habit' : 'General')} · ${t.check_method === 'scale' ? 'Scale 1–5' : (t.check_method === 'quantity' ? `Quantity (${t.quantity_unit || 'units'})` : 'Yes / No')}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Check-in CTA card -->
                <div class="p-5 text-center rounded-2xl border border-[#CDE9DA] bg-[#EDF7F1]/40 space-y-3">
                    <p class="text-xs text-[#6F6B68]">
                        Your trackers are ready. Start your first daily check-in now:
                    </p>
                    <div class="flex items-center justify-center gap-3">
                        <button type="button" onclick="window.TempoRecoverySetup.launchFirstDailyCheckin()"
                                class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                            <span>Check in now</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>

                <!-- Footer Nav -->
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(5)"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ← Back to trackers
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(7)"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        Skip for today / Continue →
                    </button>
                </div>
            </div>
        `;
    }

    function launchFirstDailyCheckin() {
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openDailyCheckin === 'function') {
            window.TempoRecoverySelfCheck.openDailyCheckin(false);
            // Advance setup background stage to 7 so when daily checkin finishes, stage 7 is ready!
            goToStage(7);
        }
    }

    // =========================================================================
    // STAGE 7: RECOVERY CHECK-IN COMPLETE + CONTEXTUAL PLAN NEXT STEP
    // =========================================================================

    function renderStage7Complete(container) {
        // Evaluate academic plan context:
        // Case A: Plan exists and has tasks scheduled for today
        // Case B: Plan exists, but no tasks scheduled for today
        // Case C: No plan exists
        const planContext = evaluatePlanContext();

        let planHtml = '';
        if (planContext.type === 'CASE_A') {
            planHtml = `
                <div class="p-4 rounded-2xl bg-white border border-[#FFD2BA] space-y-2 text-left shadow-2xs">
                    <span class="text-[10px] font-extrabold uppercase tracking-wider text-[#B83D08]">WHEN YOU'RE READY</span>
                    <h4 class="font-heading text-sm font-bold text-[#202124]">Your plan for today is still here.</h4>
                    <p class="text-xs text-[#6F6B68]">You have ${planContext.taskCount} planned tasks for today whenever you feel ready to review them.</p>
                    <button type="button" onclick="window.TempoRecoverySetup.viewPlanForToday()"
                            class="text-xs font-bold text-[#B83D08] hover:text-[#9A3412] transition cursor-pointer pt-1 flex items-center space-x-1">
                        <span>View your plan for today</span>
                        <span>→</span>
                    </button>
                </div>
            `;
        } else if (planContext.type === 'CASE_B') {
            planHtml = `
                <div class="p-4 rounded-2xl bg-white border border-stone-200 space-y-2 text-left shadow-2xs">
                    <span class="text-[10px] font-extrabold uppercase tracking-wider text-stone-500">YOUR CURRENT PLAN</span>
                    <h4 class="font-heading text-sm font-bold text-[#202124]">Your existing plan is still here.</h4>
                    <p class="text-xs text-[#6F6B68]">No tasks are scheduled for today. Your existing plan is ready whenever you want to review it.</p>
                    <button type="button" onclick="window.TempoRecoverySetup.viewPlan()"
                            class="text-xs font-bold text-[#166545] hover:text-[#0E4A32] transition cursor-pointer pt-1 flex items-center space-x-1">
                        <span>View your plan</span>
                        <span>→</span>
                    </button>
                </div>
            `;
        } else {
            // Case C: No plan exists
            planHtml = `
                <div class="p-4 rounded-2xl bg-white border border-stone-200 space-y-2 text-left shadow-2xs">
                    <span class="text-[10px] font-extrabold uppercase tracking-wider text-stone-500">WHEN YOU'RE READY</span>
                    <h4 class="font-heading text-sm font-bold text-[#202124]">Need to organize academic deadlines?</h4>
                    <p class="text-xs text-[#6F6B68]">If you have things to work through, Tempo's Urgent Mode can help you make a structured plan.</p>
                    <button type="button" onclick="window.TempoRecoverySetup.promptCreatePlan()"
                            class="text-xs font-bold text-[#FF6B2C] hover:text-[#E05316] transition cursor-pointer pt-1 flex items-center space-x-1">
                        <span>Create your plan</span>
                        <span>→</span>
                    </button>
                </div>
            `;
        }

        container.innerHTML = `
            <div class="space-y-6 text-center py-4">
                <div class="w-12 h-12 rounded-2xl bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA] flex items-center justify-center text-xl font-bold mx-auto shadow-xs">
                    ✓
                </div>

                <div class="space-y-2 max-w-md mx-auto">
                    <span class="text-xs font-extrabold uppercase tracking-wider text-[#166545]">
                        ✓ RECOVERY CHECK-IN COMPLETE
                    </span>
                    <h3 class="font-heading text-2xl font-extrabold text-[#202124]">
                        You've taken some time to slow down.
                    </h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        You looked back, noticed what might help, and set up your personal space. Take things at your own pace from here.
                    </p>
                </div>

                <!-- Primary Action: Return to Recovery Home -->
                <div class="pt-2 max-w-xs mx-auto">
                    <button type="button" onclick="window.TempoRecoverySetup.finishAndReturnHome()"
                            class="btn-primary w-full px-6 py-3 rounded-xl font-bold text-sm shadow-xs inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                        <span>Back to Dashboard</span>
                        <span>→</span>
                    </button>
                </div>

                <!-- Contextual Plan Section -->
                <div class="pt-4 border-t border-stone-100 max-w-md mx-auto">
                    ${planHtml}
                </div>
            </div>
        `;
    }

    function evaluatePlanContext() {
        const storePlan = window.TempoPlanStore && window.TempoPlanStore.getActivePlan
            ? window.TempoPlanStore.getActivePlan('emergency')
            : null;
        const confirmedPlan = (storePlan && storePlan.plannedTasks && storePlan.plannedTasks.length > 0)
            ? storePlan
            : ((window.TempoEmergencyFlow && window.TempoEmergencyFlow.getConfirmedPlan) ? window.TempoEmergencyFlow.getConfirmedPlan() : null);

        if (!confirmedPlan || !confirmedPlan.plannedTasks || confirmedPlan.plannedTasks.length === 0) {
            return { type: 'CASE_C' };
        }

        // Check if there are tasks for today
        const todayStr = (function () {
            const now = new Date();
            return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
        })();

        const todayTasks = confirmedPlan.plannedTasks.filter(pt => pt.day === todayStr && !pt.task?.completed);
        if (todayTasks.length > 0) {
            return { type: 'CASE_A', taskCount: todayTasks.length };
        }

        return { type: 'CASE_B' };
    }

    function finishAndReturnHome() {
        markSetupCompleted();
        close();
        if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
            window.TempoMode.renderRmodeHome();
        }
    }

    function viewPlanForToday() {
        markSetupCompleted();
        close();
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.open === 'function') {
            window.TempoPlanWorkspace.open();
        } else if (window.TempoApp) {
            window.TempoApp.navigateTo('today');
        }
    }

    function viewPlan() {
        markSetupCompleted();
        close();
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.open === 'function') {
            window.TempoPlanWorkspace.open();
        } else if (window.TempoApp) {
            window.TempoApp.navigateTo('today');
        }
    }

    function promptCreatePlan() {
        const modal = document.getElementById('modal-recovery-plan-confirm');
        if (modal) modal.classList.remove('hidden');
    }

    function closePlanConfirmModal() {
        const modal = document.getElementById('modal-recovery-plan-confirm');
        if (modal) modal.classList.add('hidden');
    }

    function confirmSwitchToUrgentPlan() {
        closePlanConfirmModal();
        markSetupCompleted();
        close();
        if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
            window.TempoMode.setMode('emergency');
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.openPlanningFlow === 'function') {
                window.TempoEmergencyFlow.openPlanningFlow();
            }
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

    function onDailyCheckinFinished() {
        const modal = document.getElementById('modal-recovery-setup');
        if (modal && !modal.classList.contains('hidden')) {
            goToStage(7);
        }
    }

    function init() {
        ensureModalMounted();
        loadDraftFromStorage();
        try {
            const uid = getUserId();
            const wasOpen = sessionStorage.getItem(`tempo_recovery_setup_open_${uid}`) === 'true';
            if (wasOpen && !isSetupCompleted()) {
                open(setupDraft.currentStage || 1);
            }
        } catch (e) {}
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.TempoRecoverySetup = {
        init,
        isIntroSeen,
        markIntroSeen,
        isSetupCompleted,
        markSetupCompleted,
        resetSetupState,
        shouldShowFirstTimeWelcome,
        open,
        close,
        exploreFirst,
        goToStage,
        toggleLookingBack,
        addCustomLookingBack,
        toggleWhatHelped,
        addCustomWhatHelped,
        toggleNoteItem,
        addCustomNoteItem,
        addSupportPersonFromSetup,
        removeSupportPerson,
        saveNoteAndContinue,
        addSuggestedTracker,
        removeTrackerFromSetup,
        onTrackerSaved,
        onTrackerArchived,
        openAddTrackerPrefill,
        launchFirstDailyCheckin,
        onDailyCheckinFinished,
        finishAndReturnHome,
        viewPlanForToday,
        viewPlan,
        promptCreatePlan,
        closePlanConfirmModal,
        confirmSwitchToUrgentPlan
    };

})();
