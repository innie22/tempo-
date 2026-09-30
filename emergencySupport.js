/**
 * Tempo Progressive Emergency & Crisis Support Engine
 * Implements a progressive crisis-support flow where AI provides immediate grounding
 * and emotional stabilization while human/emergency support options remain accessible at all times.
 * STRICT POLICY: No medical/mental-health diagnoses. AI is never a replacement for professional help.
 */

window.TempoEmergencySupport = (function() {
    // State
    let currentStep = 'checkin'; // 'checkin' | 'grounding' | 'safety_checkin' | 'still_unsafe' | 'calmer_options' | 'understand_problem' | 'problem_solving'
    let selectedNeed = null;     // 'overwhelmed' | 'crisis' | 'selfharm' | 'notsure'
    let isSafetyMode = false;
    let currentGroundingIndex = 0; // 0: surroundings, 1: slow breathing, 2: move toward safety
    let breathingInterval = null;

    // Configurable Support Information (Centralized per Tempo Handbook)
    const supportConfig = {
        emergencyMedical: {
            title: 'Emergency Medical Support',
            phone: '115',
            callHref: 'tel:115',
            details: "If you're at immediate risk of hurting yourself or you're in immediate danger."
        },
        crisisHotline: {
            title: 'HOPE — Suicide Prevention Hotline',
            phone: '0865 044 400',
            callHref: 'tel:0865044400',
            details: "If you're in crisis, having thoughts of hurting yourself, or need someone to support you right now."
        },
        waitingGuidance: [
            'Stay with someone you trust.',
            'Move somewhere safer.',
            'Create distance from anything that could hurt you.'
        ],
        closingReassurance: "You don't need to solve everything right now. For now, just focus on staying safe.",
        trustedPersonTemplate: "Hey, I'm having a really difficult time right now and feeling overwhelmed. Are you free to talk or sit with me for a few minutes?"
    };

    function init() {
        bindEvents();
    }

    function bindEvents() {
        // Universal trigger buttons
        document.querySelectorAll('.btn-open-emergency-support, .btn-urgent, .btn-open-crisis-helpline').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                openModal();
            });
        });

        // Close Modal
        const closeBtn = document.getElementById('btn-close-emergency-flow');
        if (closeBtn) {
            closeBtn.addEventListener('click', closeModal);
        }

        // Persistent Human Support Drawer Toggle
        const toggleHumanBtn = document.getElementById('btn-toggle-human-drawer');
        if (toggleHumanBtn) {
            toggleHumanBtn.addEventListener('click', toggleHumanDrawer);
        }
        const closeDrawerBtn = document.getElementById('btn-close-human-drawer');
        if (closeDrawerBtn) {
            closeDrawerBtn.addEventListener('click', closeHumanDrawer);
        }

        // Copy trusted contact message
        const copyTrustedBtn = document.getElementById('btn-copy-trusted-msg');
        if (copyTrustedBtn) {
            copyTrustedBtn.addEventListener('click', copyTrustedMessage);
        }
    }

    function copyTrustedMessage() {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(supportConfig.trustedPersonTemplate);
        }
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("Message copied! You can paste and send it to a friend or family member.");
        }
    }

    function submitOfflineMessage(source = 'drawer') {
        const contactInput = document.getElementById(source === 'drawer' ? 'drawer-offline-contact' : 'step5a-offline-contact');
        const msgInput = document.getElementById(source === 'drawer' ? 'drawer-offline-message' : 'step5a-offline-message');
        const successEl = document.getElementById(source === 'drawer' ? 'drawer-offline-success' : 'step5a-offline-success');

        const message = msgInput ? msgInput.value.trim() : '';
        const contact = contactInput ? contactInput.value.trim() : 'Anonymous Student';

        if (!message) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Please enter a message before sending.");
            }
            return;
        }

        const offlineEntry = {
            id: 'offline-' + Date.now(),
            contact: contact || 'Anonymous Student',
            message: message,
            timestamp: new Date().toISOString()
        };

        try {
            const existing = JSON.parse(localStorage.getItem('tempo_offline_messages') || '[]');
            existing.push(offlineEntry);
            localStorage.setItem('tempo_offline_messages', JSON.stringify(existing));
        } catch (e) {
            console.warn("Storage warning:", e);
        }

        if (msgInput) msgInput.value = '';
        if (successEl) successEl.classList.remove('hidden');

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("Message received for office hours. For immediate help, call 115 or HOPE (0865 044 400).");
        }
    }

    function openModal() {
        const modal = document.getElementById('progressive-emergency-modal');
        if (!modal) return;

        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');

        // Always close human drawer when opening modal fresh
        closeHumanDrawer();

        // Reset to Step 1: Initial Check-In
        isSafetyMode = false;
        goToStep('checkin');
    }

    function closeModal(force = false) {
        if (!force && isSafetyMode) {
            if (typeof window.confirm === 'function' && !window.confirm("You are currently in Safety Support. Are you sure you want to exit? Remember, 115 and HOPE (0865 044 400) are available.")) {
                return;
            }
        }
        stopBreathing();
        const modal = document.getElementById('progressive-emergency-modal');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
        closeHumanDrawer();
    }

    function goToStep(step) {
        currentStep = step;
        stopBreathing();

        // Hide all step panels
        document.querySelectorAll('.emergency-flow-step').forEach(panel => {
            panel.classList.add('hidden');
        });

        const activePanel = document.getElementById(`emergency-step-${step}`);
        if (activePanel) {
            activePanel.classList.remove('hidden');
        }

        // Update Safety Mode banner & header
        const safetyBanner = document.getElementById('emergency-safety-banner');
        if (safetyBanner) {
            if (isSafetyMode) {
                safetyBanner.classList.remove('hidden');
            } else {
                safetyBanner.classList.add('hidden');
            }
        }

        // Trigger specific step initializers
        if (step === 'grounding') {
            renderGroundingActivity(currentGroundingIndex);
        }
    }

    // STEP 1: INITIAL CHECK-IN HANDLERS
    function handleInitialCheckin(choice) {
        selectedNeed = choice;

        if (choice === 'crisis' || choice === 'selfharm') {
            // Immediate Safety Mode
            isSafetyMode = true;
            if (choice === 'selfharm') {
                currentGroundingIndex = 2; // Move toward safety grounding
            } else {
                currentGroundingIndex = 0;
            }
            goToStep('grounding');
        } else if (choice === 'notsure') {
            isSafetyMode = false;
            currentGroundingIndex = 0;
            goToStep('grounding');
        } else {
            // Overwhelmed or panicking
            isSafetyMode = false;
            currentGroundingIndex = 0;
            goToStep('grounding');
        }
    }

    // STEP 3: GROUNDING ACTIVITIES (ONE ACTIVITY AT A TIME)
    function renderGroundingActivity(index) {
        currentGroundingIndex = index;
        const container = document.getElementById('grounding-activity-content');
        if (!container) return;

        if (index === 0) {
            // Grounding Activity 1: Notice your surroundings
            container.innerHTML = `
                <div class="space-y-4">
                    <div class="p-5 bg-[#FFF9F4] border border-[#FFD2BA] rounded-2xl space-y-3">
                        <span class="text-xs font-bold text-[#B83D08] uppercase tracking-wider">Grounding 1 of 3 • Notice Your Surroundings</span>
                        <h4 class="font-heading text-lg font-bold text-gray-900">Notice Your Surroundings</h4>
                        <div class="space-y-1.5 text-sm text-gray-700 leading-relaxed">
                            <p class="font-medium">"Put both feet on the floor if you can."</p>
                            <p class="text-xs text-gray-600">"Look around and name 3 things you can see."</p>
                        </div>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2">
                            <input type="text" placeholder="1. Item I see..." class="p-2.5 text-xs bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-[#FF6B2C] focus:border-[#FF6B2C]">
                            <input type="text" placeholder="2. Item I see..." class="p-2.5 text-xs bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-[#FF6B2C] focus:border-[#FF6B2C]">
                            <input type="text" placeholder="3. Item I see..." class="p-2.5 text-xs bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-[#FF6B2C] focus:border-[#FF6B2C]">
                        </div>
                    </div>

                    <div class="flex items-center justify-between pt-2">
                        <button type="button" onclick="window.TempoEmergencySupport.nextGrounding()" class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                            Try something else
                        </button>
                        <button type="button" onclick="window.TempoEmergencySupport.goToStep('safety_checkin')" class="btn-primary px-6 py-2.5 rounded-xl text-xs font-bold shadow-sm">
                            Done
                        </button>
                    </div>
                </div>
            `;
        } else if (index === 1) {
            // Grounding Activity 2: Slow down (Visually paced respiration)
            container.innerHTML = `
                <div class="space-y-5 text-center">
                    <div class="space-y-1">
                        <span class="text-xs font-bold text-[#B83D08] uppercase tracking-wider">Grounding 2 of 3 • Slow Down</span>
                        <h4 class="font-heading text-lg font-bold text-gray-900">Slow Down Your Breathing</h4>
                        <p class="text-xs text-gray-600 max-w-md mx-auto">
                            Follow the expanding circle. Inhale gently through your nose, pause, and exhale slowly.
                        </p>
                    </div>

                    <div class="h-44 flex items-center justify-center">
                        <div id="grounding-breathing-circle" class="w-28 h-28 rounded-full bg-[#FFE9DC]/60 border-2 border-[#FF6B2C]/50 flex flex-col items-center justify-center transition-all duration-1000 shadow-sm">
                            <span id="grounding-breath-phase" class="text-xs font-semibold text-[#202124]">Inhale gently</span>
                            <span id="grounding-breath-count" class="text-xs font-bold text-[#FF6B2C] mt-0.5">4s</span>
                        </div>
                    </div>

                    <div class="flex items-center justify-between pt-2">
                        <button type="button" onclick="window.TempoEmergencySupport.nextGrounding()" class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                            Try something else
                        </button>
                        <button type="button" onclick="window.TempoEmergencySupport.goToStep('safety_checkin')" class="btn-primary px-6 py-2.5 rounded-xl text-xs font-bold shadow-sm">
                            Done
                        </button>
                    </div>
                </div>
            `;
            startGroundingBreathing();
        } else {
            // Grounding Activity 3: Move toward safety
            container.innerHTML = `
                <div class="space-y-4">
                    <div class="p-5 bg-amber-50/70 border border-amber-200 rounded-2xl space-y-3">
                        <span class="text-xs font-bold text-amber-900 uppercase tracking-wider">Grounding 3 of 3 • Move Toward Safety</span>
                        <h4 class="font-heading text-lg font-bold text-gray-900">Move Toward Space & Safety</h4>
                        <p class="text-sm text-gray-700 leading-relaxed font-medium">
                            While you're waiting for support:
                        </p>
                        <ul class="text-xs text-gray-700 space-y-1.5 list-disc list-inside font-medium">
                            <li>Stay with someone you trust.</li>
                            <li>Move somewhere safer.</li>
                            <li>Create distance from anything that could hurt you.</li>
                        </ul>
                        <div class="pt-2 border-t border-amber-200/70 text-xs text-amber-900 space-y-0.5">
                            <p class="font-semibold">You don't need to solve everything right now.</p>
                            <p>For now, just focus on staying safe.</p>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                        <button type="button" onclick="window.TempoEmergencySupport.copyTrustedMessage()" class="p-3 bg-stone-100 hover:bg-stone-200 text-stone-800 rounded-xl text-xs font-semibold text-center transition flex items-center justify-center space-x-1.5">
                            <span>💬</span>
                            <span>Contact someone I trust</span>
                        </button>
                        <button type="button" onclick="window.TempoEmergencySupport.openHumanDrawer()" class="p-3 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold text-center transition flex items-center justify-center space-x-1.5 shadow-sm" title="Get immediate help">
                            <span>📞</span>
                            <span>Get support now →</span>
                        </button>
                    </div>

                    <div class="flex items-center justify-between pt-2">
                        <button type="button" onclick="window.TempoEmergencySupport.nextGrounding()" class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                            Continue grounding
                        </button>
                        <button type="button" onclick="window.TempoEmergencySupport.goToStep('safety_checkin')" class="btn-primary px-6 py-2.5 rounded-xl text-xs font-bold shadow-sm">
                            Done
                        </button>
                    </div>
                </div>
            `;
        }
    }

    function nextGrounding() {
        stopBreathing();
        currentGroundingIndex = (currentGroundingIndex + 1) % 3;
        renderGroundingActivity(currentGroundingIndex);
    }

    function startGroundingBreathing() {
        const circle = document.getElementById('grounding-breathing-circle');
        const phaseText = document.getElementById('grounding-breath-phase');
        const countText = document.getElementById('grounding-breath-count');

        if (circle) circle.classList.add('breathing-circle-active');

        const phases = [
            { label: 'Inhale gently', sec: 4 },
            { label: 'Hold softly', sec: 4 },
            { label: 'Exhale slowly', sec: 4 },
            { label: 'Rest', sec: 4 }
        ];

        let pIdx = 0;
        let s = 4;

        breathingInterval = setInterval(() => {
            if (s > 1) {
                s--;
            } else {
                pIdx = (pIdx + 1) % phases.length;
                s = phases[pIdx].sec;
            }
            if (phaseText) phaseText.textContent = phases[pIdx].label;
            if (countText) countText.textContent = `${s}s`;
        }, 1000);
    }

    function stopBreathing() {
        if (breathingInterval) {
            clearInterval(breathingInterval);
            breathingInterval = null;
        }
    }

    // STEP 4: QUICK SAFETY CHECK-IN (NO NUMERICAL SCORE)
    function handleSafetyCheckin(feeling) {
        if (feeling === 'unsafe') {
            // STEP 5A: User still does not feel safe
            isSafetyMode = true;
            goToStep('still_unsafe');
        } else if (feeling === 'distressed_calmer') {
            // STEP 5B: Still distressed but a little calmer
            isSafetyMode = false;
            goToStep('calmer_options');
        } else {
            // STEP 5B: Feels calmer now
            isSafetyMode = false;
            goToStep('calmer_options');
        }
    }

    // STEP 6: UNDERSTAND THE PROBLEM (NATURAL LANGUAGE - NO MEDICAL DIAGNOSIS)
    function handleAnalyzeProblem() {
        const input = document.getElementById('emergency-problem-text');
        const text = input ? input.value.trim() : '';

        if (!text) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Please describe what is feeling difficult in a few words.");
            }
            return;
        }

        // Extract practical, non-clinical stressors
        const lower = text.toLowerCase();
        const detectedFactors = [];

        if (lower.includes('deadline') || lower.includes('due') || lower.includes('tomorrow') || lower.includes('report') || lower.includes('exam') || lower.includes('paper')) {
            detectedFactors.push({ 
                title: 'Deadline Overload & Academic Workload', 
                tip: 'Multiple impending tasks competing for active cognitive bandwidth.' 
            });
        }
        if (lower.includes('sleep') || lower.includes('tired') || lower.includes('exhaust') || lower.includes('night') || lower.includes('drained')) {
            detectedFactors.push({ 
                title: 'Physical Sleep Debt', 
                tip: 'Physical depletion significantly increases perceived difficulty and cognitive friction.' 
            });
        }
        if (lower.includes('start') || lower.includes('freeze') || lower.includes('stuck') || lower.includes('blank') || lower.includes('procrastinat')) {
            detectedFactors.push({ 
                title: 'Task Initiation Freeze', 
                tip: 'Initial friction creates an avoidance loop. Breaking the activation threshold is key.' 
            });
        }
        if (lower.includes('alone') || lower.includes('isolate') || lower.includes('nobody') || lower.includes('secret') || lower.includes('help')) {
            detectedFactors.push({ 
                title: 'Carrying Stress Alone', 
                tip: 'Carrying academic panic in isolation magnifies emotional distress.' 
            });
        }
        if (lower.includes('fight') || lower.includes('roommate') || lower.includes('argue') || lower.includes('friend') || lower.includes('family') || lower.includes('conflict')) {
            detectedFactors.push({ 
                title: 'Interpersonal Conflict', 
                tip: 'Relational tension drawing attention away from study focus.' 
            });
        }

        if (detectedFactors.length === 0) {
            detectedFactors.push({ 
                title: 'Immediate Task Pressure', 
                tip: 'High concentration of pending obligations creating cognitive overload.' 
            });
        }

        renderProblemAnalysis(text, detectedFactors);
        goToStep('problem_solving');
    }

    function renderProblemAnalysis(rawText, factors) {
        const container = document.getElementById('problem-factors-list');
        if (container) {
            container.innerHTML = factors.map(f => `
                <div class="p-3 bg-stone-50 border border-stone-200 rounded-xl space-y-1">
                    <span class="text-xs font-bold text-gray-900">${f.title}</span>
                    <p class="text-[11px] text-gray-600">${f.tip}</p>
                </div>
            `).join('');
        }

        // Bridge to ONE Next Action
        let oneAction = "Open your Marketing report and list the three sections you still need to complete.";
        let estimatedTime = "5 minutes";

        const lower = rawText.toLowerCase();
        if (lower.includes('slide') || lower.includes('presentation')) {
            oneAction = "Open your presentation software and title Slide 1, Slide 2, and Slide 3 with rough bullet headers.";
            estimatedTime = "4 minutes";
        } else if (lower.includes('math') || lower.includes('problem') || lower.includes('pset')) {
            oneAction = "Read Problem 1 only and write down the two known variables given in the prompt.";
            estimatedTime = "5 minutes";
        } else if (lower.includes('email') || lower.includes('professor') || lower.includes('extension')) {
            oneAction = "Draft a 2-sentence email to request a 24-hour extension on your upcoming submission.";
            estimatedTime = "3 minutes";
        } else if (lower.includes('read') || lower.includes('chapter')) {
            oneAction = "Open the assigned reading and read just the section headers and conclusion paragraph.";
            estimatedTime = "5 minutes";
        }

        const actionEl = document.getElementById('emergency-solved-action');
        const timeEl = document.getElementById('emergency-solved-time');
        if (actionEl) actionEl.textContent = oneAction;
        if (timeEl) timeEl.textContent = `Estimated time: ${estimatedTime} • Low pressure`;
    }

    function launchImmediateMicroAction() {
        const actionEl = document.getElementById('emergency-solved-action');
        const actionText = actionEl ? actionEl.textContent : "Open your document and list 3 rough section headers.";

        closeModal(true);

        // Connect directly into Focus Zone
        if (window.TempoFocusZone) {
            window.TempoFocusZone.open({
                taskName: 'Immediate Micro Step',
                nextAction: actionText
            });
        } else if (window.TempoTriage) {
            window.TempoTriage.launchFocusMode();
        }

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("Starting with your 5-minute micro-action. You've got this.");
        }
    }

    // HUMAN SUPPORT DRAWER CONTROLS
    function openHumanDrawer() {
        const drawer = document.getElementById('human-support-drawer');
        if (drawer) {
            drawer.classList.remove('hidden');
        }
    }

    function closeHumanDrawer() {
        const drawer = document.getElementById('human-support-drawer');
        if (drawer) {
            drawer.classList.add('hidden');
        }
    }

    function toggleHumanDrawer() {
        const drawer = document.getElementById('human-support-drawer');
        if (drawer) {
            if (drawer.classList.contains('hidden')) {
                openHumanDrawer();
            } else {
                closeHumanDrawer();
            }
        }
    }

    // Entry point when clicking SOS in top nav or headers
    // CRITICAL: Opens calm Step 1 Initial Check-In (does NOT auto-pop hotline drawer)
    function openSOS() {
        openModal();
        isSafetyMode = true; // Sets safety mode header/banner ready
        goToStep('checkin');
        // Do NOT call openHumanDrawer()!
    }

    return {
        init,
        openModal,
        closeModal,
        openSOS,
        goToStep,
        handleInitialCheckin,
        nextGrounding,
        handleSafetyCheckin,
        handleAnalyzeProblem,
        launchImmediateMicroAction,
        openHumanDrawer,
        closeHumanDrawer,
        toggleHumanDrawer,
        copyTrustedMessage,
        submitOfflineMessage
    };
})();
