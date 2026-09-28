/**
 * Tempo Emergency Triage & Focus Engine
 * Implements acute stabilization, AI parsing, the ONE Next Action,
 * 25-min gentle focus timer with Web Audio ambient sounds, and post-session pulse check.
 */

window.TempoTriage = (function() {
    let activePlan = null;
    let timerInterval = null;
    let timerSecondsLeft = 25 * 60;
    let isTimerRunning = false;
    let currentTaskTitle = "Immediate Focus Step";
    let ambientAudioContext = null;
    let ambientGainNode = null;
    let currentAmbientType = 'rain'; // 'rain' | 'forest' | 'white' | 'none'
    let isAmbientPlaying = false;

    // Preset Scenarios for quick 1-click user testing
    const samplePrompts = {
        marketing: "I have a Marketing report due tomorrow at 9 AM and I have only finished the introduction. I also have a research presentation on Friday and I haven't started the slides. I have around four hours tonight but I don't know what to do first.",
        exams: "I have two midterm exams on Monday and Tuesday (Calculus & Psychology). I am 4 chapters behind on readings, my sleep has been terrible, and looking at the syllabus makes me freeze up. I have about 3 hours this afternoon.",
        coding: "My Computer Science project is due tonight at 11:59 PM. My algorithm passes test 1 and 2 but fails test 3 with a segmentation fault. I feel exhausted, frustrated, and terrified of failing the course."
    };

    function init() {
        bindEvents();
    }

    function bindEvents() {
        const analyzeBtn = document.getElementById('btn-analyze-emergency');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', handleAnalyze);
        }

        // Quick Scenario Chip Buttons
        document.querySelectorAll('.sample-chip').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const key = e.currentTarget.dataset.scenario;
                const textarea = document.getElementById('emergency-brain-dump');
                if (textarea && samplePrompts[key]) {
                    textarea.value = samplePrompts[key];
                    window.TempoApp.showToast("Sample scenario loaded. Click 'Analyze & Create Calm Plan' below.");
                }
            });
        });

        // Focus Timer Buttons
        const startFocusBtn = document.getElementById('btn-start-focus');
        if (startFocusBtn) {
            startFocusBtn.addEventListener('click', launchFocusMode);
        }

        const timerToggleBtn = document.getElementById('btn-timer-toggle');
        if (timerToggleBtn) {
            timerToggleBtn.addEventListener('click', toggleTimer);
        }

        const timerDoneEarlyBtn = document.getElementById('btn-timer-done-early');
        if (timerDoneEarlyBtn) {
            timerDoneEarlyBtn.addEventListener('click', completeFocusSession);
        }

        const timerExitBtn = document.getElementById('btn-exit-focus');
        if (timerExitBtn) {
            timerExitBtn.addEventListener('click', exitFocusMode);
        }

        // Ambient Sound Controls
        const ambientToggle = document.getElementById('btn-toggle-ambient');
        if (ambientToggle) {
            ambientToggle.addEventListener('click', toggleAmbientSound);
        }

        const ambientSelect = document.getElementById('select-ambient-sound');
        if (ambientSelect) {
            ambientSelect.addEventListener('change', (e) => {
                currentAmbientType = e.target.value;
                if (isAmbientPlaying) {
                    stopAmbientSound();
                    startAmbientSound(currentAmbientType);
                }
            });
        }

        // Micro-step decomposition button
        const smallerStepBtn = document.getElementById('btn-smaller-step');
        if (smallerStepBtn) {
            smallerStepBtn.addEventListener('click', toggleEvenSmallerStep);
        }
    }

    async function handleAnalyze() {
        const textarea = document.getElementById('emergency-brain-dump');
        const text = textarea ? textarea.value.trim() : '';
        const hoursSelect = document.getElementById('emergency-hours-select');
        const availableHours = hoursSelect ? parseFloat(hoursSelect.value) : 4;

        if (!text) {
            window.TempoApp.showToast("Please dump a few words about what is on your plate first.");
            return;
        }

        const analyzeBtn = document.getElementById('btn-analyze-emergency');
        const originalHtml = analyzeBtn.innerHTML;
        analyzeBtn.innerHTML = `
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Triage in Progress...
        `;
        analyzeBtn.disabled = true;

        try {
            // Try server API first, fallback to robust client-side heuristics
            let planData;
            try {
                const response = await fetch('/api/ai/parse-triage', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, availableHours })
                });
                if (response.ok) {
                    planData = await response.json();
                }
            } catch (err) {
                console.log("Using client-side fallback triage engine:", err);
            }

            if (!planData) {
                planData = clientSideTriageParse(text, availableHours);
            }

            activePlan = planData;
            renderTriagePlan(planData);
            window.TempoApp.showToast("Triage plan created. Notice your ONE next action.");

            // Scroll gently to plan
            const planSection = document.getElementById('emergency-plan-results');
            if (planSection) {
                planSection.scrollIntoView({ behavior: 'smooth' });
            }

        } catch (error) {
            console.error("Triage error:", error);
            window.TempoApp.showToast("Error analyzing tasks. Please try again.");
        } finally {
            analyzeBtn.innerHTML = originalHtml;
            analyzeBtn.disabled = false;
        }
    }

    function clientSideTriageParse(text, availableHours) {
        const lower = text.toLowerCase();
        let tasks = [];

        if (lower.includes('marketing') || lower.includes('report')) {
            tasks.push({
                id: 't-1',
                title: 'Marketing Report Final Draft',
                deadline: 'Tomorrow, 9:00 AM',
                estimatedHours: 2.5,
                priorityScore: 96,
                isUrgent: true
            });
        }
        if (lower.includes('presentation') || lower.includes('slide')) {
            tasks.push({
                id: 't-2',
                title: 'Research Presentation Slide Outline',
                deadline: 'Friday, 2:00 PM',
                estimatedHours: 1.5,
                priorityScore: 78,
                isUrgent: false
            });
        }
        if (lower.includes('exam') || lower.includes('midterm') || lower.includes('calculus')) {
            tasks.push({
                id: 't-3',
                title: 'Exam Key Concept Review (Chapters 1-3)',
                deadline: 'Monday Morning',
                estimatedHours: 2.0,
                priorityScore: 75,
                isUrgent: false
            });
        }
        if (lower.includes('code') || lower.includes('lab') || lower.includes('program')) {
            tasks.push({
                id: 't-4',
                title: 'Lab Debugging: Test Case 3',
                deadline: 'Tonight, 11:59 PM',
                estimatedHours: 1.5,
                priorityScore: 92,
                isUrgent: true
            });
        }

        if (tasks.length === 0) {
            tasks.push({
                id: 't-custom',
                title: text.substring(0, 50) + (text.length > 50 ? '...' : ''),
                deadline: 'Immediate Deadline',
                estimatedHours: Math.min(availableHours, 2.0),
                priorityScore: 88,
                isUrgent: true
            });
        }

        tasks.sort((a, b) => b.priorityScore - a.priorityScore);
        const topTask = tasks[0];

        let oneAction = `Write 3 bullet points for the opening section of ${topTask.title}`;
        let oneMicro = `Open the document and write 1 rough sentence. No formatting.`;
        let rationale = `This task has the closest deadline constraint. Taking 1 small step releases the panic response.`;

        if (topTask.title.includes('Marketing') || topTask.title.includes('Report')) {
            oneAction = "Draft the 3 core section headings and 2 bullet points for Section 2";
            oneMicro = "Open the Google Doc and type: Heading 2: Analysis";
            rationale = "Due tomorrow at 9:00 AM. Setting up headings eliminates 70% of writing friction without demanding full prose.";
        } else if (topTask.title.includes('Lab') || topTask.title.includes('Debug')) {
            oneAction = "Isolate failing function and write out inputs and expected outputs on scratch paper";
            oneMicro = "Add one console.log statement to inspect the input value";
            rationale = "Writing on paper grounds your working memory when code debugging feels chaotic.";
        }

        return {
            success: true,
            availableHours,
            tasks,
            topTask,
            oneNextAction: oneAction,
            oneNextActionMicro: oneMicro,
            rationale,
            targetMinutes: 25
        };
    }

    function renderTriagePlan(plan) {
        const container = document.getElementById('emergency-plan-results');
        if (!container) return;

        container.classList.remove('hidden');

        // Populate ONE Next Action
        document.getElementById('one-action-title').textContent = plan.oneNextAction;
        document.getElementById('one-action-context').textContent = `Target: 25 minutes | Task: ${plan.topTask.title} (${plan.topTask.deadline})`;
        document.getElementById('one-action-rationale').textContent = plan.rationale;
        
        currentTaskTitle = plan.oneNextAction;

        // Populate Task Breakdown List
        const taskListEl = document.getElementById('triage-task-list');
        taskListEl.innerHTML = '';
        plan.tasks.forEach((t, idx) => {
            const isTop = idx === 0;
            const li = document.createElement('div');
            li.className = `p-4 rounded-xl border flex items-center justify-between ${
                isTop ? 'bg-[#FFF9F4] border-[#FFD2BA]' : 'bg-white border-[#E8E4E1]'
            }`;
            li.innerHTML = `
                <div class="flex items-center space-x-3">
                    <span class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        isTop ? 'bg-[#FF6B2C] text-white' : 'bg-[#F3F1EF] text-[#6F6B68]'
                    }">${idx + 1}</span>
                    <div>
                        <h4 class="font-medium text-[#202124]">${t.title}</h4>
                        <p class="text-xs text-[#6F6B68]">Deadline: <span class="font-medium text-[#B83D08]">${t.deadline}</span> • Est: ~${t.estimatedHours} hrs</p>
                    </div>
                </div>
                <div class="text-right">
                    <span class="inline-block text-xs font-semibold px-2.5 py-1 rounded-full ${
                        isTop ? 'bg-[#FFE9DC] text-[#B83D08]' : 'bg-[#F3F1EF] text-[#6F6B68]'
                    }">${isTop ? 'Focus First' : 'Can Wait'}</span>
                </div>
            `;
            taskListEl.appendChild(li);
        });

        // Time Budget Indicator
        const totalEstHours = plan.tasks.reduce((sum, t) => sum + t.estimatedHours, 0);
        document.getElementById('triage-budget-summary').textContent = 
            `You have ~${plan.availableHours} hours available tonight. Total estimated workload is ~${totalEstHours} hours.`;
    }

    function toggleEvenSmallerStep() {
        if (!activePlan) return;
        const titleEl = document.getElementById('one-action-title');
        const btn = document.getElementById('btn-smaller-step');

        if (btn.dataset.mode === 'micro') {
            titleEl.textContent = activePlan.oneNextAction;
            btn.dataset.mode = 'standard';
            btn.innerHTML = `<span>🤏 Make it even smaller (5 mins)</span>`;
            currentTaskTitle = activePlan.oneNextAction;
        } else {
            titleEl.textContent = activePlan.oneNextActionMicro;
            btn.dataset.mode = 'micro';
            btn.innerHTML = `<span>↺ Back to 25-minute step</span>`;
            currentTaskTitle = activePlan.oneNextActionMicro;
            window.TempoApp.showToast("Step simplified to a 5-minute activation hurdle!");
        }
    }

    function launchFocusMode() {
        const focusModal = document.getElementById('focus-session-modal');
        if (!focusModal) return;

        focusModal.classList.remove('hidden');
        document.getElementById('focus-task-name').textContent = currentTaskTitle;

        // Reset timer to 25 minutes
        timerSecondsLeft = 25 * 60;
        updateTimerDisplay();
        startTimer();

        // Start ambient sound if selected
        if (currentAmbientType !== 'none') {
            startAmbientSound(currentAmbientType);
        }
    }

    function updateTimerDisplay() {
        const mins = Math.floor(timerSecondsLeft / 60);
        const secs = timerSecondsLeft % 60;
        const display = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        
        const timerEl = document.getElementById('focus-timer-clock');
        if (timerEl) timerEl.textContent = display;

        // Document title update
        if (isTimerRunning) {
            document.title = `(${display}) Focus - Tempo`;
        } else {
            document.title = `Tempo - Student Wellbeing`;
        }
    }

    function startTimer() {
        if (timerInterval) clearInterval(timerInterval);
        isTimerRunning = true;
        const toggleBtn = document.getElementById('btn-timer-toggle');
        if (toggleBtn) {
            toggleBtn.innerHTML = `
                <svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg> Pause
            `;
        }

        timerInterval = setInterval(() => {
            if (timerSecondsLeft > 0) {
                timerSecondsLeft--;
                updateTimerDisplay();
            } else {
                completeFocusSession();
            }
        }, 1000);
    }

    function toggleTimer() {
        if (isTimerRunning) {
            clearInterval(timerInterval);
            isTimerRunning = false;
            const toggleBtn = document.getElementById('btn-timer-toggle');
            if (toggleBtn) {
                toggleBtn.innerHTML = `
                    <svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg> Resume
                `;
            }
        } else {
            startTimer();
        }
    }

    function completeFocusSession() {
        clearInterval(timerInterval);
        isTimerRunning = false;
        stopAmbientSound();

        // Hide focus modal
        const focusModal = document.getElementById('focus-session-modal');
        if (focusModal) focusModal.classList.add('hidden');

        // Open Emotional Pulse Check Modal
        openPulseCheckModal();
    }

    function exitFocusMode() {
        if (confirm("Are you sure you want to pause your focus session?")) {
            clearInterval(timerInterval);
            isTimerRunning = false;
            stopAmbientSound();
            const focusModal = document.getElementById('focus-session-modal');
            if (focusModal) focusModal.classList.add('hidden');
            document.title = "Tempo - Student Wellbeing";
        }
    }

    function openPulseCheckModal() {
        const pulseModal = document.getElementById('pulse-check-modal');
        if (pulseModal) pulseModal.classList.remove('hidden');

        // Bind pulse options
        document.querySelectorAll('.pulse-option-btn').forEach(btn => {
            btn.onclick = () => {
                const feel = btn.dataset.feel;
                handlePulseSelection(feel);
            };
        });
    }

    function handlePulseSelection(feeling) {
        const pulseModal = document.getElementById('pulse-check-modal');
        if (pulseModal) pulseModal.classList.add('hidden');

        if (feeling === 'lighter') {
            window.TempoApp.triggerConfetti();
            window.TempoApp.showToast("Great job! You broke through the freeze response.");
            // Mark step complete in UI and offer step 2
            const actionCard = document.getElementById('one-action-card');
            if (actionCard) {
                actionCard.innerHTML = `
                    <div class="p-6 bg-[#FFF9F4] rounded-2xl border border-[#FFD2BA] text-center space-y-4">
                        <div class="w-12 h-12 bg-[#FFE9DC] text-[#FF6B2C] rounded-full flex items-center justify-center mx-auto text-xl font-bold">✓</div>
                        <h3 class="text-xl font-bold text-[#202124]">Step 1 Complete!</h3>
                        <p class="text-sm text-[#6F6B68] max-w-md mx-auto">You've unlocked momentum. You can either take a 5-minute breather or continue to the next part of the report.</p>
                        <div class="flex justify-center space-x-3 pt-2">
                            <button onclick="window.TempoApp.navigateTo('routine')" class="btn-primary px-5 py-2.5 rounded-xl text-sm font-bold shadow-sm">Save to Today's Routine</button>
                            <button onclick="window.TempoApp.navigateTo('today')" class="btn-secondary px-5 py-2.5 rounded-xl text-sm font-medium">Back to Dashboard</button>
                        </div>
                    </div>
                `;
            }
        } else if (feeling === 'same') {
            window.TempoApp.showToast("Progress isn't always linear. Take a 5-minute break and drink water.");
            window.TempoApp.navigateTo('today');
        } else {
            // Still overwhelmed: Open Progressive Emergency Support
            if (window.TempoEmergencySupport) {
                window.TempoEmergencySupport.openModal();
            } else {
                openBoxBreathingModal();
            }
        }
    }

    function openBoxBreathingModal() {
        const modal = document.getElementById('box-breathing-modal');
        if (!modal) return;
        modal.classList.remove('hidden');

        const circle = document.getElementById('breathing-animated-circle');
        const text = document.getElementById('breathing-phase-text');
        const count = document.getElementById('breathing-count-text');

        if (circle) circle.classList.add('breathing-circle-active');

        let phaseIndex = 0;
        const phases = [
            { label: 'Inhale gently through nose', seconds: 4 },
            { label: 'Hold breath softly', seconds: 4 },
            { label: 'Exhale slowly through mouth', seconds: 4 },
            { label: 'Rest before next breath', seconds: 4 }
        ];

        let sec = 4;
        const breathInterval = setInterval(() => {
            if (modal.classList.contains('hidden')) {
                clearInterval(breathInterval);
                return;
            }
            if (sec > 1) {
                sec--;
            } else {
                phaseIndex = (phaseIndex + 1) % phases.length;
                sec = phases[phaseIndex].seconds;
            }
            if (text) text.textContent = phases[phaseIndex].label;
            if (count) count.textContent = `${sec}s`;
        }, 1000);

        const closeBtn = document.getElementById('btn-close-breathing');
        if (closeBtn) {
            closeBtn.onclick = () => {
                clearInterval(breathInterval);
                modal.classList.add('hidden');
                if (circle) circle.classList.remove('breathing-circle-active');
            };
        }

        const supportBtn = document.getElementById('btn-breathing-ask-support');
        if (supportBtn) {
            supportBtn.onclick = () => {
                clearInterval(breathInterval);
                modal.classList.add('hidden');
                window.TempoApp.navigateTo('support');
            };
        }
    }

    // Web Audio Synthesizer for Offline Ambient Sounds
    function startAmbientSound(type) {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!ambientAudioContext) {
                ambientAudioContext = new AudioContext();
            }
            if (ambientAudioContext.state === 'suspended') {
                ambientAudioContext.resume();
            }

            ambientGainNode = ambientAudioContext.createGain();
            ambientGainNode.gain.setValueAtTime(0.04, ambientAudioContext.currentTime);
            ambientGainNode.connect(ambientAudioContext.destination);

            // Generate synthetic soothing noise buffer
            const bufferSize = ambientAudioContext.sampleRate * 2;
            const noiseBuffer = ambientAudioContext.createBuffer(1, bufferSize, ambientAudioContext.sampleRate);
            const output = noiseBuffer.getChannelData(0);
            let lastOut = 0.0;

            for (let i = 0; i < bufferSize; i++) {
                const white = Math.random() * 2 - 1;
                // Brown/Pink noise filter for rain or soft wind
                output[i] = (lastOut + (0.02 * white)) / 1.02;
                lastOut = output[i];
                output[i] *= 3.5;
            }

            const whiteNoise = ambientAudioContext.createBufferSource();
            whiteNoise.buffer = noiseBuffer;
            whiteNoise.loop = true;

            const filter = ambientAudioContext.createBiquadFilter();
            filter.type = type === 'rain' ? 'lowpass' : 'bandpass';
            filter.frequency.setValueAtTime(type === 'rain' ? 800 : 450, ambientAudioContext.currentTime);

            whiteNoise.connect(filter);
            filter.connect(ambientGainNode);
            whiteNoise.start(0);

            ambientAudioContext._activeSource = whiteNoise;
            isAmbientPlaying = true;
            updateAmbientIcon(true);
        } catch (e) {
            console.log("Web Audio not supported or blocked by browser:", e);
        }
    }

    function stopAmbientSound() {
        if (ambientAudioContext && ambientAudioContext._activeSource) {
            try {
                ambientAudioContext._activeSource.stop();
                ambientAudioContext._activeSource.disconnect();
                ambientAudioContext._activeSource = null;
            } catch (e) {}
        }
        isAmbientPlaying = false;
        updateAmbientIcon(false);
    }

    function toggleAmbientSound() {
        if (isAmbientPlaying) {
            stopAmbientSound();
            window.TempoApp.showToast("Ambient audio muted.");
        } else {
            startAmbientSound(currentAmbientType);
            window.TempoApp.showToast(`Ambient audio playing: ${currentAmbientType}`);
        }
    }

    function updateAmbientIcon(playing) {
        const waves = document.getElementById('sound-waves-indicator');
        const label = document.getElementById('sound-toggle-label');
        if (waves) {
            waves.style.display = playing ? 'flex' : 'none';
        }
        if (label) {
            label.textContent = playing ? 'Sound: On' : 'Sound: Off';
        }
    }

    return {
        init,
        launchFocusMode,
        handleAnalyze
    };
})();
