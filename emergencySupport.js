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

    // Configurable Institution & Regional Support Information
    const supportConfig = {
        institutionName: 'University Wellbeing Network',
        crisisLine: {
            title: '988 Suicide & Crisis Lifeline',
            phone: '988',
            actionText: 'Call or Text 988',
            availability: '24/7 • Free • Confidential',
            details: 'Trained crisis counselors available nationwide by phone or text.'
        },
        crisisText: {
            title: 'Crisis Text Line',
            action: 'Text HOME to 741741',
            availability: '24/7 • Free • Confidential',
            details: 'Connect with a volunteer crisis counselor via SMS anytime.'
        },
        campusSupport: {
            title: 'Campus Urgent Wellbeing Center',
            phone: '(555) 019-2831',
            location: 'Student Health Center, Room 204',
            operatingHours: 'Mon–Fri: 9:00 AM – 5:00 PM',
            isOnlineNow: false, // Realistic check
            offlineNotice: 'The campus support team is currently offline (Operating hours: Mon–Fri 9am–5pm). For urgent safety situations, please connect directly with 24/7 immediate support services below.'
        },
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
            copyTrustedBtn.addEventListener('click', () => {
                navigator.clipboard.writeText(supportConfig.trustedPersonTemplate);
                window.TempoApp.showToast("Message copied! You can paste and send it to a friend or family member.");
            });
        }
    }

    function openModal() {
        const modal = document.getElementById('progressive-emergency-modal');
        if (!modal) return;

        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');

        // Reset to Step 1: Initial Check-In
        goToStep('checkin');
    }

    function closeModal() {
        if (isSafetyMode) {
            if (!confirm("You are currently in Safety Support. Are you sure you want to exit? Remember, 988 is available 24/7.")) {
                return;
            }
        }
        stopBreathing();
        const modal = document.getElementById('progressive-emergency-modal');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
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
            // Also notify user gently
            goToStep('grounding');
            // Auto open human drawer in safety mode if selfharm
            if (choice === 'selfharm') {
                openHumanDrawer();
            }
        } else if (choice === 'notsure') {
            isSafetyMode = true;
            goToStep('grounding');
        } else {
            // Overwhelmed or panicking
            isSafetyMode = false;
            currentGroundingIndex = 0;
            goToStep('grounding');
        }
    }

    // STEP 3: GROUNDING ACTIVITIES
    function renderGroundingActivity(index) {
        currentGroundingIndex = index;
        const container = document.getElementById('grounding-activity-content');
        if (!container) return;

        if (index === 0) {
            // Activity 1: Notice your surroundings
            container.innerHTML = `
                <div class="space-y-4">
                    <div class="p-5 bg-[#FFF9F4] border border-[#FFD2BA] rounded-2xl space-y-3">
                        <span class="text-xs font-bold text-[#B83D08] uppercase tracking-wider">Grounding 1 of 3 • Sensory Anchoring</span>
                        <h4 class="font-heading text-lg font-bold text-gray-900">Notice Your Surroundings</h4>
                        <p class="text-sm text-gray-700 leading-relaxed">
                            "Put both feet flat on the floor if you can. Feel the solid ground underneath you.<br>
                            Look around the room slowly, and name 3 things you can see right now."
                        </p>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2">
                            <input type="text" placeholder="1. Item I see..." class="p-2.5 text-xs bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-[#FF6B2C] focus:border-[#FF6B2C]">
                            <input type="text" placeholder="2. Item I see..." class="p-2.5 text-xs bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-[#FF6B2C] focus:border-[#FF6B2C]">
                            <input type="text" placeholder="3. Item I see..." class="p-2.5 text-xs bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-[#FF6B2C] focus:border-[#FF6B2C]">
                        </div>
                    </div>

                    <div class="flex items-center justify-between pt-2">
                        <button onclick="window.TempoEmergencySupport.nextGrounding()" class="text-xs text-gray-500 hover:text-gray-800 font-medium underline">
                            Try another grounding exercise →
                        </button>
                        <button onclick="window.TempoEmergencySupport.goToStep('safety_checkin')" class="btn-primary px-6 py-2.5 rounded-xl text-xs font-bold shadow-sm">
                            I completed this (Next step)
                        </button>
                    </div>
                </div>
            `;
        } else if (index === 1) {
            // Activity 2: Slow down breathing
            container.innerHTML = `
                <div class="space-y-5 text-center">
                    <div class="space-y-1">
                        <span class="text-xs font-bold text-[#B83D08] uppercase tracking-wider">Grounding 2 of 3 • Paced Respiration</span>
                        <h4 class="font-heading text-lg font-bold text-gray-900">Slow Down Your Breathing</h4>
                        <p class="text-xs text-gray-600 max-w-md mx-auto">
                            Follow the expanding circle. Inhale gently through your nose, pause, and exhale slowly.
                        </p>
                    </div>

                    <div class="h-44 flex items-center justify-center">
                        <div id="grounding-breathing-circle" class="w-28 h-28 rounded-full bg-[#FFE9DC]/60 border-2 border-[#FF6B2C]/50 flex flex-col items-center justify-center transition-all duration-1000">
                            <span id="grounding-breath-phase" class="text-xs font-semibold text-[#202124]">Inhale</span>
                            <span id="grounding-breath-count" class="text-xs font-bold text-[#FF6B2C] mt-0.5">4s</span>
                        </div>
                    </div>

                    <div class="flex items-center justify-between pt-2">
                        <button onclick="window.TempoEmergencySupport.nextGrounding()" class="text-xs text-gray-500 hover:text-gray-800 font-medium underline">
                            Try another grounding exercise →
                        </button>
                        <button onclick="window.TempoEmergencySupport.goToStep('safety_checkin')" class="btn-primary px-6 py-2.5 rounded-xl text-xs font-bold shadow-sm">
                            I feel ready to check in
                        </button>
                    </div>
                </div>
            `;
            startGroundingBreathing();
        } else {
            // Activity 3: Move toward safety
            container.innerHTML = `
                <div class="space-y-4">
                    <div class="p-5 bg-amber-50/70 border border-amber-200 rounded-2xl space-y-3">
                        <span class="text-xs font-bold text-amber-900 uppercase tracking-wider">Grounding 3 of 3 • Physical Safety & Connection</span>
                        <h4 class="font-heading text-lg font-bold text-gray-900">Move Toward Space & Safety</h4>
                        <p class="text-sm text-gray-700 leading-relaxed">
                            Take a moment to protect your immediate environment:
                        </p>
                        <ul class="text-xs text-gray-700 space-y-2 list-disc list-inside">
                            <li>Move to a room or space where other people are present (living room, hallway, library).</li>
                            <li>Send a short message to a trusted friend, roommate, or family member.</li>
                            <li>Create physical distance from anything you might use to hurt yourself.</li>
                        </ul>
                    </div>

                    <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2">
                        <button onclick="window.TempoEmergencySupport.openHumanDrawer()" class="p-3 bg-stone-100 hover:bg-stone-200 text-stone-800 rounded-xl text-xs font-semibold text-center transition">
                            💬 Contact Someone I Trust
                        </button>
                        <button onclick="window.TempoEmergencySupport.openHumanDrawer()" class="p-3 bg-amber-100 hover:bg-amber-200 text-amber-900 rounded-xl text-xs font-semibold text-center transition">
                            📞 Immediate Human Help
                        </button>
                        <button onclick="window.TempoEmergencySupport.goToStep('safety_checkin')" class="btn-primary p-3 rounded-xl text-xs font-bold text-center transition">
                            Check In on How I Feel
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

    // STEP 4: QUICK SAFETY CHECK-IN
    function handleSafetyCheckin(feeling) {
        if (feeling === 'unsafe') {
            // STEP 5A: User still does not feel safe
            isSafetyMode = true;
            goToStep('still_unsafe');
        } else if (feeling === 'distressed_calmer') {
            // Still distressed but a little calmer
            goToStep('calmer_options');
        } else {
            // Feels calmer now
            goToStep('calmer_options');
        }
    }

    // STEP 6: UNDERSTAND THE PROBLEM
    function handleAnalyzeProblem() {
        const input = document.getElementById('emergency-problem-text');
        const text = input ? input.value.trim() : '';

        if (!text) {
            window.TempoApp.showToast("Please write a few words about what is feeling difficult.");
            return;
        }

        // Extract practical non-clinical stressors
        const lower = text.toLowerCase();
        const detectedFactors = [];

        if (lower.includes('deadline') || lower.includes('due') || lower.includes('tomorrow') || lower.includes('report')) {
            detectedFactors.push({ title: 'Clustered Academic Deadlines', tip: 'Multiple deliverables competing for working memory.' });
        }
        if (lower.includes('sleep') || lower.includes('tired') || lower.includes('exhausted') || lower.includes('night')) {
            detectedFactors.push({ title: 'Physical Sleep Debt', tip: 'Brain fatigue makes initiation feel 3x heavier.' });
        }
        if (lower.includes('start') || lower.includes('freeze') || lower.includes('stuck') || lower.includes('blank')) {
            detectedFactors.push({ title: 'Task Initiation Freeze', tip: 'Perfectionism or threat perception causing avoidance.' });
        }
        if (lower.includes('alone') || lower.includes('isolate') || lower.includes('nobody')) {
            detectedFactors.push({ title: 'Feeling Isolated', tip: 'Holding stress in secret magnifies cognitive burden.' });
        }

        if (detectedFactors.length === 0) {
            detectedFactors.push({ title: 'Immediate Academic Pressure', tip: 'High volume of work in a short timeframe.' });
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
        let oneAction = "Open your next assignment and write down only the three section headings you need.";
        let estimatedTime = "5 minutes";

        if (rawText.toLowerCase().includes('report') || rawText.toLowerCase().includes('marketing')) {
            oneAction = "Open your Marketing Report document and type 3 rough bullet points for Section 2.";
            estimatedTime = "5 minutes";
        } else if (rawText.toLowerCase().includes('slides') || rawText.toLowerCase().includes('presentation')) {
            oneAction = "Create blank slide presentation and title Slide 1, Slide 2, and Slide 3.";
            estimatedTime = "4 minutes";
        }

        document.getElementById('emergency-solved-action').textContent = oneAction;
        document.getElementById('emergency-solved-time').textContent = `Estimated time: ${estimatedTime} • Low pressure`;
    }

    function launchImmediateMicroAction() {
        closeModal();
        // Pre-fill triage input and launch gentle focus timer
        const actionText = document.getElementById('emergency-solved-action').textContent;
        window.TempoApp.navigateTo('emergency');
        window.TempoApp.showToast("Starting with your 5-minute micro-action. You've got this.");
        
        // Launch focus mode with this micro step
        if (window.TempoTriage) {
            setTimeout(() => {
                window.TempoTriage.launchFocusMode();
            }, 500);
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

    function openSOS() {
        openModal();
        isSafetyMode = true;
        goToStep('checkin');
        openHumanDrawer();
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
        toggleHumanDrawer
    };
})();
