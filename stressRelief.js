/**
 * Tempo Quick Stress Relief & Breathing Reusable System
 * 
 * Reusable system callable from:
 * - Homepage Quick Tools (Breathing & Quick Stress Relief)
 * - Emergency Mode Reset Flow
 * - Future Focus Zone stress pauses
 * 
 * Flow:
 * Library / Direct Entry -> Method Detail -> Timed Session -> Checkpoint Panel
 * Checkpoint actions:
 * - I'm ready -> return to caller context (Emergency Reality Check or Home)
 * - Do this again / Keep breathing -> repeat method
 * - Try something else -> return to Method Library
 */

window.TempoStressRelief = (function() {
    // 8 Core Stress-Relief Methods
    const METHODS = [
        {
            id: 'breathing',
            icon: '🫁',
            title: 'Box Breathing',
            summary: 'Follow a steady 4-count rhythm to calm your nervous system.',
            durationLabel: '3 min',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: true,
            steps: [
                'Inhale gently through your nose for 4 seconds.',
                'Hold the air softly in your lungs for 4 seconds.',
                'Exhale slowly and completely through your mouth for 4 seconds.',
                'Rest empty for 4 seconds before your next breath.'
            ]
        },
        {
            id: 'release-tension',
            icon: '💆',
            title: 'Release Tension',
            summary: 'Relax your jaw, shoulders, and hands.',
            durationLabel: '2–3 min',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: false,
            steps: [
                'Notice your teeth or jaw. Let your mouth part slightly and drop your tongue.',
                'Gently raise your shoulders toward your ears on a slow inhale.',
                'Exhale firmly, letting your shoulders drop completely loose.',
                'Open and unclench your fingers, resting your hands flat and heavy.'
            ]
        },
        {
            id: 'short-stretch',
            icon: '🧘',
            title: 'Short Stretch',
            summary: 'Gently release tight neck, spine, and chest muscles.',
            durationLabel: '3 min',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: false,
            steps: [
                'Sit tall. Slowly tilt your right ear to your right shoulder for 3 breaths.',
                'Switch and tilt your left ear to your left shoulder for 3 breaths.',
                'Interlace fingers behind your head and gently lean back to open your chest.',
                'Exhale and round your upper back softly, tucking your chin lightly.'
            ]
        },
        {
            id: 'sensory-grounding',
            icon: '👁️',
            title: 'Sensory Grounding',
            summary: 'Anchor your attention with 5-4-3-2-1 room observation.',
            durationLabel: '3 min',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: false,
            steps: [
                'Look around: Name 5 distinct things you can see right now.',
                'Feel your body: Name 4 physical sensations (feet on floor, sweater on arms).',
                'Listen closely: Name 3 subtle sounds in your surroundings.',
                'Notice 2 textures or scents nearby, then take 1 slow grounding breath.'
            ]
        },
        {
            id: 'step-away',
            icon: '🚪',
            title: 'Step Away from Screen',
            summary: 'Rest your optic nerves and step completely away from devices.',
            durationLabel: '5 min',
            defaultDuration: 5,
            filterDuration: 5,
            isBreathing: false,
            steps: [
                'Close your laptop lid and turn your phone face down.',
                'Stand up and walk away from your workspace entirely.',
                'Look out of a window or across a room at the furthest possible point.',
                'Let your gaze rest gently in the distance without focusing on small details.'
            ]
        },
        {
            id: 'short-walk',
            icon: '🚶',
            title: 'Short Walk',
            summary: 'Walk a hallway or corridor to metabolize physical stress.',
            durationLabel: '5 min',
            defaultDuration: 5,
            filterDuration: 5,
            isBreathing: false,
            steps: [
                'Leave your current room without taking your phone.',
                'Walk down the corridor, hallway, or courtyard at a comfortable pace.',
                'Notice the rhythmic feeling of your heels and feet contacting the ground.',
                'Let your arms swing naturally and keep your breathing unhurried.'
            ]
        },
        {
            id: 'write-worries',
            icon: '📝',
            title: 'Write Down Worries',
            summary: 'Offload one specific unresolved worry onto a note.',
            durationLabel: '3 min',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: false,
            steps: [
                'Grab a scrap of paper or sticky note.',
                'Write in one sentence: "What is the single thing worrying me most right now?"',
                'Ask yourself: "Can I solve this in the next 15 minutes?"',
                'If not, write: "I am parking this until later." Fold the note and set it aside.'
            ]
        },
        {
            id: 'get-water',
            icon: '💧',
            title: 'Get Some Water',
            summary: 'Drink a glass of cool water slowly and mindfully.',
            durationLabel: '1–2 min',
            defaultDuration: 1,
            filterDuration: 1,
            isBreathing: false,
            steps: [
                'Walk to the nearest sink, tap, or water dispenser.',
                'Pour a glass of cool or room-temperature water.',
                'Take 3 slow, intentional sips, feeling the cool temperature.',
                'Take one long exhale before returning to your seat.'
            ]
        }
    ];

    // State Variables
    let activeContext = 'home'; // 'home' | 'emergency'
    let onReadyCallback = null;
    let activeMethod = METHODS[0]; // defaults to Breathing
    let selectedDuration = 3; // minutes
    let currentFilter = 'all'; // 'all' | '1' | '3' | '5' | '10'

    // Timer and Interval References
    let sessionTimer = null;
    let sessionRemainingSeconds = 180;
    let sessionIsPaused = false;
    let breathingInterval = null;
    let breathingPhaseIndex = 0;
    let breathingPhaseSeconds = 4;

    const BREATHING_PHASES = [
        { label: 'Breathe in gently', count: 4, scale: 1.35 },
        { label: 'Hold softly', count: 4, scale: 1.35 },
        { label: 'Breathe out slowly', count: 4, scale: 0.85 },
        { label: 'Rest before next breath', count: 4, scale: 0.85 }
    ];

    function init() {
        bindEvents();
    }

    function bindEvents() {
        const closeBtn = document.getElementById('btn-close-stress-relief');
        if (closeBtn) {
            closeBtn.addEventListener('click', closeModal);
        }

        // Close on backdrop click
        const modal = document.getElementById('modal-quick-stress-relief');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    closeModal();
                }
            });
        }

        // Close on Escape key
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal && !modal.classList.contains('hidden')) {
                closeModal();
            }
        });
    }

    /**
     * Open Breathing directly (used by Emergency Mode Reset & Quick Tools Breathing)
     */
    function openBreathing(options = {}) {
        activeContext = options.context || 'home';
        onReadyCallback = options.onReady || null;
        activeMethod = METHODS.find(m => m.id === 'breathing') || METHODS[0];
        selectedDuration = 3;

        stopAllTimers();
        openModalWrapper();
        renderBreathingSetup();
    }

    /**
     * Open Method Library (used by Homepage Quick Tools & "Try something else")
     */
    function openLibrary(options = {}) {
        activeContext = options.context || activeContext || 'home';
        if (options.onReady) {
            onReadyCallback = options.onReady;
        }

        stopAllTimers();
        openModalWrapper();
        renderLibrary();
    }

    /**
     * Backwards-compatible alias for Quick Tools
     */
    function openModal(defaultFilter = 'all') {
        currentFilter = defaultFilter;
        openLibrary({ context: 'home' });
    }

    function openModalWrapper() {
        const modal = document.getElementById('modal-quick-stress-relief');
        if (!modal) return;
        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    function closeModal() {
        stopAllTimers();
        const modal = document.getElementById('modal-quick-stress-relief');
        if (modal) {
            modal.classList.add('hidden');
        }
        document.body.classList.remove('overflow-hidden');
    }

    function stopAllTimers() {
        if (sessionTimer) {
            clearInterval(sessionTimer);
            sessionTimer = null;
        }
        if (breathingInterval) {
            clearInterval(breathingInterval);
            breathingInterval = null;
        }
        sessionIsPaused = false;
    }

    // =========================================================================
    // VIEW 1: METHOD LIBRARY VIEW
    // =========================================================================
    function renderLibrary() {
        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        const filters = [
            { key: 'all', label: 'All Durations' },
            { key: '1', label: '⚡ 1 min' },
            { key: '3', label: '🌿 3 min' },
            { key: '5', label: '🚶 5 min' }
        ];

        const filtered = currentFilter === 'all'
            ? METHODS
            : METHODS.filter(m => String(m.filterDuration) === currentFilter);

        container.innerHTML = `
            <div class="space-y-6">
                <!-- Header -->
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">QUICK STRESS RELIEF</span>
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Choose a grounding method</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">Pick something small to try. A few minutes is enough to signal your nervous system.</p>
                </div>

                <!-- Duration Filter Pills -->
                <div class="flex flex-wrap items-center gap-2">
                    ${filters.map(f => `
                        <button onclick="window.TempoStressRelief.setFilter('${f.key}')" 
                                class="px-3.5 py-1.5 rounded-full text-xs font-semibold transition ${
                                    currentFilter === f.key 
                                        ? 'bg-[#FF6B2C] text-white shadow-sm' 
                                        : 'bg-[#F3F1EF] text-[#6F6B68] hover:text-[#202124] hover:bg-stone-200'
                                }">
                            ${f.label}
                        </button>
                    `).join('')}
                </div>

                <!-- Cards Grid -->
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-1">
                    ${filtered.map(m => `
                        <div onclick="window.TempoStressRelief.selectMethod('${m.id}')"
                             tabindex="0"
                             role="button"
                             onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();window.TempoStressRelief.selectMethod('${m.id}');}"
                             class="p-4 bg-white border border-[#EAE4DF] hover:border-[#FF6B2C] rounded-2xl cursor-pointer transition hover:shadow-sm space-y-2 group flex flex-col justify-between">
                            <div class="space-y-2">
                                <div class="flex items-center justify-between">
                                    <span class="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FFE9DC] text-[#B83D08]">
                                        <span>${m.durationLabel}</span>
                                    </span>
                                    <span class="text-lg">${m.icon}</span>
                                </div>
                                <h4 class="font-heading text-sm font-bold text-[#202124] group-hover:text-[#FF6B2C] transition">
                                    ${m.title}
                                </h4>
                                <p class="text-xs text-[#6F6B68] leading-relaxed line-clamp-2">
                                    ${m.summary}
                                </p>
                            </div>
                            <div class="pt-2 flex items-center justify-between text-xs text-[#FF6B2C] font-bold border-t border-stone-100">
                                <span>Start this action</span>
                                <span class="group-hover:translate-x-1 transition-transform">→</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    function setFilter(filterKey) {
        currentFilter = filterKey;
        renderLibrary();
    }

    function selectMethod(methodId) {
        const method = METHODS.find(m => m.id === methodId);
        if (!method) return;
        activeMethod = method;

        if (method.isBreathing) {
            renderBreathingSetup();
        } else {
            renderMethodDetail(method);
        }
    }

    // =========================================================================
    // VIEW 2: BREATHING SETUP VIEW (Default for Reset)
    // =========================================================================
    function renderBreathingSetup() {
        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        selectedDuration = 3;

        container.innerHTML = `
            <div class="space-y-6 max-w-lg mx-auto py-2">
                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">BREATHING</span>
                    <h3 class="font-heading text-2xl font-bold text-[#202124]">Box Breathing Reset</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">Take a few minutes and follow the rhythm.</p>
                </div>

                <!-- Explanation Box -->
                <div class="p-4 bg-[#FFF8F2] border border-[#FFD2BA]/60 rounded-2xl text-xs text-[#6F6B68] leading-relaxed space-y-2">
                    <p class="font-semibold text-[#202124]">How it works:</p>
                    <p>Inhale (4s) • Hold (4s) • Exhale (4s) • Rest (4s). This equal cadence helps your heart rate and nervous system downshift naturally.</p>
                </div>

                <!-- Duration Picker -->
                <div class="space-y-3 pt-1">
                    <label class="block text-xs font-bold uppercase tracking-wider text-[#202124] text-center">
                        Select Duration:
                    </label>
                    <div class="flex items-center justify-center gap-2.5">
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(1)" id="dur-btn-1" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50">
                            1 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(3)" id="dur-btn-3" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition bg-[#FF6B2C] text-white border border-[#FF6B2C] shadow-sm">
                            3 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(5)" id="dur-btn-5" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50">
                            5 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice('custom')" id="dur-btn-custom" 
                                class="px-3.5 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50">
                            Custom
                        </button>
                    </div>

                    <!-- Custom Duration Input (hidden by default) -->
                    <div id="custom-duration-box" class="hidden text-center pt-2">
                        <label for="custom-duration-input" class="text-xs text-[#6F6B68] mr-2">Minutes:</label>
                        <input id="custom-duration-input" type="number" min="1" max="20" value="4" 
                               onchange="window.TempoStressRelief.handleCustomDurationChange(this.value)"
                               class="w-16 px-2.5 py-1 text-xs border border-gray-300 rounded-lg text-center font-bold">
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
                    <button onclick="window.TempoStressRelief.startBreathingSession()" 
                            class="btn-primary w-full sm:w-auto px-8 py-3 rounded-xl font-bold text-sm shadow-md flex items-center justify-center space-x-2">
                        <span>Start Breathing →</span>
                    </button>
                    <button onclick="window.TempoStressRelief.renderLibrary()" 
                            class="w-full sm:w-auto px-5 py-3 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                        View Other Methods
                    </button>
                </div>
            </div>
        `;
    }

    function setDurationChoice(val) {
        const customBox = document.getElementById('custom-duration-box');
        ['1', '3', '5', 'custom'].forEach(k => {
            const btn = document.getElementById(`dur-btn-${k}`);
            if (btn) {
                if (String(val) === k) {
                    btn.className = 'px-4 py-2 rounded-xl text-xs font-bold transition bg-[#FF6B2C] text-white border border-[#FF6B2C] shadow-sm';
                } else {
                    btn.className = 'px-4 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50';
                }
            }
        });

        if (val === 'custom') {
            if (customBox) customBox.classList.remove('hidden');
            const customInput = document.getElementById('custom-duration-input');
            selectedDuration = customInput ? parseInt(customInput.value, 10) || 4 : 4;
        } else {
            if (customBox) customBox.classList.add('hidden');
            selectedDuration = parseInt(val, 10);
        }
    }

    function handleCustomDurationChange(val) {
        const parsed = parseInt(val, 10);
        if (parsed && parsed >= 1 && parsed <= 30) {
            selectedDuration = parsed;
        }
    }

    // =========================================================================
    // VIEW 3: ACTIVE BREATHING SESSION
    // =========================================================================
    function startBreathingSession() {
        stopAllTimers();
        sessionRemainingSeconds = selectedDuration * 60;
        sessionIsPaused = false;
        breathingPhaseIndex = 0;
        breathingPhaseSeconds = 4;

        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        container.innerHTML = `
            <div class="space-y-6 max-w-sm mx-auto text-center py-2">
                <!-- Header -->
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">BREATHING</span>
                    <h3 class="font-heading text-xl font-bold text-[#202124]">Box Breathing Reset</h3>
                    <p id="breathing-time-remaining" class="text-xs font-bold text-[#6F6B68]">
                        ${formatMinutesSeconds(sessionRemainingSeconds)} remaining
                    </p>
                </div>

                <!-- Animated Breathing Circle -->
                <div class="h-48 flex items-center justify-center relative">
                    <div id="active-breathing-circle" 
                         class="w-32 h-32 rounded-full bg-[#FFE9DC]/70 border-2 border-[#FF6B2C]/60 flex flex-col items-center justify-center transition-all duration-1000 ease-in-out shadow-sm">
                        <span id="active-breathing-phase" class="text-xs font-bold text-[#202124] px-4 text-center leading-snug">
                            Breathe in gently
                        </span>
                        <span id="active-breathing-count" class="text-sm font-extrabold text-[#FF6B2C] mt-1">
                            4s
                        </span>
                    </div>
                </div>

                <!-- Session Controls -->
                <div class="space-y-3 pt-2">
                    <div class="flex items-center justify-center gap-3">
                        <button id="btn-breathing-pause" onclick="window.TempoStressRelief.togglePauseResume()" 
                                class="px-5 py-2.5 rounded-xl border border-gray-300 hover:border-gray-400 text-xs font-bold text-gray-700 bg-white hover:bg-stone-50 transition shadow-sm">
                            ⏸ Pause
                        </button>
                        <button onclick="window.TempoStressRelief.endSessionEarly()" 
                                class="px-5 py-2.5 rounded-xl border border-transparent text-xs font-medium text-gray-500 hover:text-gray-800 hover:bg-stone-100 transition">
                            Finish Early
                        </button>
                    </div>
                </div>
            </div>
        `;

        updateBreathingDisplay();

        // 1-second interval driving both the breathing phases and session total countdown
        breathingInterval = setInterval(() => {
            if (sessionIsPaused) return;

            // Decrement session remaining
            if (sessionRemainingSeconds > 0) {
                sessionRemainingSeconds--;
                const timeEl = document.getElementById('breathing-time-remaining');
                if (timeEl) {
                    timeEl.textContent = `${formatMinutesSeconds(sessionRemainingSeconds)} remaining`;
                }
            } else {
                // Session finished!
                stopAllTimers();
                renderCheckpoint();
                return;
            }

            // Decrement current breathing phase count
            if (breathingPhaseSeconds > 1) {
                breathingPhaseSeconds--;
            } else {
                breathingPhaseIndex = (breathingPhaseIndex + 1) % BREATHING_PHASES.length;
                breathingPhaseSeconds = BREATHING_PHASES[breathingPhaseIndex].count;
            }

            updateBreathingDisplay();
        }, 1000);
    }

    function updateBreathingDisplay() {
        const circle = document.getElementById('active-breathing-circle');
        const phaseEl = document.getElementById('active-breathing-phase');
        const countEl = document.getElementById('active-breathing-count');

        const currentPhase = BREATHING_PHASES[breathingPhaseIndex];
        if (phaseEl) phaseEl.textContent = currentPhase.label;
        if (countEl) countEl.textContent = `${breathingPhaseSeconds}s`;

        if (circle) {
            circle.style.transform = `scale(${currentPhase.scale})`;
            circle.style.borderColor = breathingPhaseIndex % 2 === 0 ? '#FF6B2C' : '#FF9E79';
        }
    }

    // =========================================================================
    // VIEW 4: METHOD DETAIL VIEW (Non-breathing methods)
    // =========================================================================
    function renderMethodDetail(method) {
        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        selectedDuration = method.defaultDuration || 3;

        container.innerHTML = `
            <div class="space-y-6 max-w-lg mx-auto py-2">
                <!-- Back Link -->
                <button onclick="window.TempoStressRelief.renderLibrary()" 
                        class="text-xs font-semibold text-[#6F6B68] hover:text-[#202124] flex items-center space-x-1 transition">
                    <span>←</span>
                    <span>Back to all methods</span>
                </button>

                <!-- Method Header -->
                <div class="space-y-1.5 border-b border-gray-100 pb-4">
                    <div class="flex items-center space-x-2">
                        <span class="text-2xl">${method.icon}</span>
                        <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#FFE9DC] text-[#B83D08]">
                            ${method.durationLabel}
                        </span>
                    </div>
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">${method.title}</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">${method.summary}</p>
                </div>

                <!-- Step-by-Step Instructions -->
                <div class="space-y-2.5">
                    <h4 class="text-xs font-bold uppercase tracking-wider text-[#202124]">Simple Instructions:</h4>
                    <ol class="space-y-2">
                        ${method.steps.map((s, idx) => `
                            <li class="flex items-start space-x-3 p-3 bg-[#FFF8F2] border border-[#FFD2BA]/60 rounded-xl text-xs text-[#202124]">
                                <span class="w-5 h-5 rounded-full bg-[#FF6B2C] text-white flex items-center justify-center font-bold text-[11px] shrink-0 mt-0.5">
                                    ${idx + 1}
                                </span>
                                <span class="leading-relaxed">${s}</span>
                            </li>
                        `).join('')}
                    </ol>
                </div>

                <!-- Duration Picker -->
                <div class="space-y-3 pt-2">
                    <label class="block text-xs font-bold uppercase tracking-wider text-[#202124] text-center">
                        How long?
                    </label>
                    <div class="flex items-center justify-center gap-2.5">
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(1)" id="dur-btn-1" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 1 ? 'bg-[#FF6B2C] text-white border border-[#FF6B2C]' : 'border border-gray-200 text-gray-700 hover:bg-stone-50'}">
                            1 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(3)" id="dur-btn-3" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 3 ? 'bg-[#FF6B2C] text-white border border-[#FF6B2C]' : 'border border-gray-200 text-gray-700 hover:bg-stone-50'}">
                            3 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(5)" id="dur-btn-5" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 5 ? 'bg-[#FF6B2C] text-white border border-[#FF6B2C]' : 'border border-gray-200 text-gray-700 hover:bg-stone-50'}">
                            5 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice('custom')" id="dur-btn-custom" 
                                class="px-3.5 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50">
                            Custom
                        </button>
                    </div>

                    <div id="custom-duration-box" class="hidden text-center pt-2">
                        <label for="custom-duration-input" class="text-xs text-[#6F6B68] mr-2">Minutes:</label>
                        <input id="custom-duration-input" type="number" min="1" max="20" value="${selectedDuration}" 
                               onchange="window.TempoStressRelief.handleCustomDurationChange(this.value)"
                               class="w-16 px-2.5 py-1 text-xs border border-gray-300 rounded-lg text-center font-bold">
                    </div>
                </div>

                <!-- Action Button -->
                <div class="pt-2 flex justify-center">
                    <button onclick="window.TempoStressRelief.startTimedSession()" 
                            class="btn-primary w-full sm:w-auto px-8 py-3 rounded-xl font-bold text-sm shadow-md flex items-center justify-center space-x-2">
                        <span>Start →</span>
                    </button>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // VIEW 5: ACTIVE TIMED SESSION (Non-breathing methods)
    // =========================================================================
    function startTimedSession() {
        stopAllTimers();
        sessionRemainingSeconds = selectedDuration * 60;
        sessionIsPaused = false;

        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        container.innerHTML = `
            <div class="space-y-6 max-w-md mx-auto text-center py-2">
                <!-- Header -->
                <div class="space-y-1">
                    <span class="text-3xl">${activeMethod.icon}</span>
                    <h3 class="font-heading text-xl font-bold text-[#202124]">${activeMethod.title}</h3>
                    <p class="text-xs text-[#6F6B68]">${activeMethod.summary}</p>
                </div>

                <!-- Countdown Clock Display -->
                <div class="py-6 px-8 bg-[#FFF8F2] border border-[#FFD2BA]/60 rounded-3xl inline-block shadow-sm">
                    <span id="timed-session-clock" class="font-heading text-4xl sm:text-5xl font-extrabold text-[#FF6B2C] tracking-tight">
                        ${formatMinutesSeconds(sessionRemainingSeconds)}
                    </span>
                    <p class="text-[11px] font-bold text-[#6F6B68] uppercase tracking-wider mt-1">Remaining Time</p>
                </div>

                <!-- Steps Quick Reminder -->
                <div class="text-left bg-white p-4 rounded-2xl border border-gray-200 text-xs space-y-2">
                    <p class="font-bold text-gray-800 uppercase tracking-wider text-[10px]">Follow along at your own pace:</p>
                    <ul class="space-y-1.5 text-[#6F6B68]">
                        ${activeMethod.steps.map(s => `<li>• ${s}</li>`).join('')}
                    </ul>
                </div>

                <!-- Session Controls -->
                <div class="flex items-center justify-center gap-3 pt-2">
                    <button id="btn-timed-pause" onclick="window.TempoStressRelief.togglePauseResume()" 
                            class="px-5 py-2.5 rounded-xl border border-gray-300 hover:border-gray-400 text-xs font-bold text-gray-700 bg-white hover:bg-stone-50 transition shadow-sm">
                        ⏸ Pause
                    </button>
                    <button onclick="window.TempoStressRelief.endSessionEarly()" 
                            class="px-5 py-2.5 rounded-xl border border-transparent text-xs font-medium text-gray-500 hover:text-gray-800 hover:bg-stone-100 transition">
                        Finish Early
                    </button>
                </div>
            </div>
        `;

        sessionTimer = setInterval(() => {
            if (sessionIsPaused) return;

            if (sessionRemainingSeconds > 0) {
                sessionRemainingSeconds--;
                const clockEl = document.getElementById('timed-session-clock');
                if (clockEl) {
                    clockEl.textContent = formatMinutesSeconds(sessionRemainingSeconds);
                }
            } else {
                stopAllTimers();
                renderCheckpoint();
            }
        }, 1000);
    }

    // =========================================================================
    // PAUSE / RESUME CONTROL
    // =========================================================================
    function togglePauseResume() {
        sessionIsPaused = !sessionIsPaused;
        const btnBreathing = document.getElementById('btn-breathing-pause');
        const btnTimed = document.getElementById('btn-timed-pause');
        const circle = document.getElementById('active-breathing-circle');

        const btnText = sessionIsPaused ? '▶ Resume' : '⏸ Pause';
        if (btnBreathing) btnBreathing.textContent = btnText;
        if (btnTimed) btnTimed.textContent = btnText;

        if (circle) {
            if (sessionIsPaused) {
                circle.style.transition = 'none';
            } else {
                circle.style.transition = 'all 1000ms ease-in-out';
            }
        }
    }

    function endSessionEarly() {
        stopAllTimers();
        renderCheckpoint();
    }

    // =========================================================================
    // VIEW 6: CHECKPOINT PANEL (How are you feeling now?)
    // =========================================================================
    function renderCheckpoint() {
        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        const isBreathing = activeMethod && activeMethod.isBreathing;
        const repeatActionText = isBreathing ? 'Keep breathing' : 'Do this again';

        container.innerHTML = `
            <div class="space-y-6 max-w-md mx-auto text-center py-4">
                <div class="w-14 h-14 rounded-2xl bg-emerald-50 text-emerald-600 border border-emerald-100 flex items-center justify-center mx-auto text-2xl shadow-sm">
                    ✨
                </div>

                <div class="space-y-1.5">
                    <h3 class="font-heading text-2xl font-bold text-[#202124]">How are you feeling now?</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">Take a breath and check in with your mind and body.</p>
                </div>

                <!-- Checkpoint 3 Action Buttons -->
                <div class="space-y-3 pt-2">
                    <!-- 1. Primary: I'm ready -->
                    <button onclick="window.TempoStressRelief.handleReady()" 
                            class="btn-primary w-full py-3.5 rounded-xl font-bold text-sm shadow-md flex items-center justify-center space-x-2 transition">
                        <span>I'm ready →</span>
                    </button>

                    <!-- 2. Secondary: Repeat -->
                    <button onclick="window.TempoStressRelief.handleRepeat()" 
                            class="w-full py-3 rounded-xl border border-gray-200 text-xs sm:text-sm font-semibold text-gray-700 bg-white hover:bg-stone-50 transition">
                        ${repeatActionText}
                    </button>

                    <!-- 3. Tertiary: Try something else -->
                    <button onclick="window.TempoStressRelief.renderLibrary()" 
                            class="w-full py-2.5 text-xs text-[#FF6B2C] hover:text-[#E8591C] font-semibold underline transition">
                        Try something else
                    </button>
                </div>
            </div>
        `;
    }

    function handleReady() {
        closeModal();

        if (activeContext === 'emergency') {
            if (window.TempoEmergencyFlow) {
                window.TempoEmergencyFlow.goToStage('reality-check');
            }
            if (typeof onReadyCallback === 'function') {
                onReadyCallback();
            }
        } else {
            if (window.TempoApp) {
                window.TempoApp.showToast("Nicely done. Take your grounded energy into your next step.");
            }
        }
    }

    function handleRepeat() {
        if (activeMethod && activeMethod.isBreathing) {
            renderBreathingSetup();
        } else if (activeMethod) {
            renderMethodDetail(activeMethod);
        } else {
            renderBreathingSetup();
        }
    }

    function formatMinutesSeconds(totalSec) {
        const mins = Math.floor(totalSec / 60);
        const secs = totalSec % 60;
        return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }

    return {
        init,
        openBreathing,
        openLibrary,
        openModal,
        closeModal,
        renderLibrary,
        setFilter,
        selectMethod,
        renderBreathingSetup,
        setDurationChoice,
        handleCustomDurationChange,
        startBreathingSession,
        renderMethodDetail,
        startTimedSession,
        togglePauseResume,
        endSessionEarly,
        renderCheckpoint,
        handleReady,
        handleRepeat
    };
})();
