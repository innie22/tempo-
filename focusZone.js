/**
 * Tempo Focus Zone MVP
 * 
 * Core Concept:
 * Task → one next action → focused work → contained break → return or finish → task state updates.
 * 
 * Concepts:
 * - TASK: shared Tempo task object (never duplicated)
 * - FOCUS SESSION: one period where the user enters Focus Zone to work
 * - FOCUS BLOCK: one timed focus period inside a session (e.g. 45m / 25m / 50m / custom)
 * - BREAK: a timed recovery period between focus blocks (e.g. 15m / 5m / 10m / custom)
 */

window.TempoFocusZone = (function() {
    // -------------------------------------------------------------------------
    // SESSION STATE
    // -------------------------------------------------------------------------
    let session = {
        isOpen: false,
        phase: 'setup', // 'quick_entry' | 'setup' | 'focus' | 'paused' | 'block_complete' | 'finish_confirm' | 'subtasks_all_done' | 'break' | 'break_game' | 'break_move' | 'break_just' | 'break_ended' | 'return_transition' | 'task_finished_early' | 'last_task_today' | 'pre_break_orientation' | 'finish_early_orient' | 'today_complete' | 'review_tomorrow' | 'round_grace' | 'change_rhythm' | 'rhythm_updated'
        
        // Task reference (shared, not owned)
        taskId: null,
        taskName: 'Independent Focus Session',
        nextAction: 'Begin focused preliminary work block.',
        subtasks: [],
        
        // Timer settings
        focusDurationSeconds: 45 * 60,
        breakDurationSeconds: 15 * 60,
        focusSecondsRemaining: 45 * 60,
        breakSecondsRemaining: 15 * 60,
        focusElapsedSeconds: 0,
        
        // Timer loop handles
        timerInterval: null,
        breakInterval: null,
        isTimerRunning: false,
        isBreakRunning: false,
        
        // Break properties
        hasUsedBreakExtension: false,
        isFinishingAllowedGameRound: false,
        breakActivityType: 'other', // 'round_game' | 'non_round_game' | 'other'
        isPostDayBreak: false,
        selectedMoveOption: null,
        
        // Styling & Atmosphere
        background: 'cream', // 'cream' | 'sunset' | 'sky' | 'night'
        soundType: 'none',   // 'none' | 'rain' | 'cafe' | 'music'
        soundVolume: 0.5,
        isSoundMuted: false,
        
        // Memory game state
        gameState: null
    };

    // Rhythm modal configuration state
    let rhythmModalState = {
        selectedPreset: '45_15', // '25_5' | '45_15' | '50_10' | 'custom'
        customFocus: 35,
        customBreak: 10
    };

    // Helper: Load saved Focus Rhythm
    function loadSavedRhythm() {
        try {
            const raw = localStorage.getItem('tempo_focus_rhythm');
            if (raw) {
                const data = JSON.parse(raw);
                if (data && data.focusDurationSeconds && data.breakDurationSeconds) {
                    session.focusDurationSeconds = data.focusDurationSeconds;
                    session.breakDurationSeconds = data.breakDurationSeconds;
                    return true;
                }
            }
        } catch (e) {}
        return false;
    }

    // Helper: Resolve shared Emergency Plan and tasks for Today and Tomorrow
    function getPlanContext() {
        let plan = null;
        if (window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            plan = window.TempoPlanStore.getActivePlan('emergency');
        }
        if (!plan && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            plan = window.TempoEmergencyFlow.getConfirmedPlan();
        }

        const now = new Date();
        const todayStr = now.toISOString().split('T')[0];
        const tomorrowDate = new Date(now);
        tomorrowDate.setDate(tomorrowDate.getDate() + 1);
        const tomorrowStr = tomorrowDate.toISOString().split('T')[0];

        const plannedTasks = (plan && Array.isArray(plan.plannedTasks)) ? plan.plannedTasks : [];

        let todayItems = plannedTasks.filter(pt => {
            if (!pt || !pt.task) return false;
            if (pt.dayDate === todayStr) return true;
            if (pt.dayLabel && pt.dayLabel.toUpperCase() === 'TODAY') return true;
            return false;
        });

        const tomorrowItems = plannedTasks.filter(pt => {
            if (!pt || !pt.task) return false;
            if (pt.dayDate === tomorrowStr) return true;
            if (pt.dayLabel && pt.dayLabel.toUpperCase() === 'TOMORROW') return true;
            return false;
        });

        // Fallback: If no explicit dates match today/tomorrow, treat all uncompleted planned tasks as today
        if (todayItems.length === 0 && tomorrowItems.length === 0 && plannedTasks.length > 0) {
            todayItems = plannedTasks.filter(pt => pt && pt.task);
        }

        const todayUnfinished = todayItems.filter(pt => pt.task && !pt.task.completed);
        const tomorrowUnfinished = tomorrowItems.filter(pt => pt.task && !pt.task.completed);

        return {
            plan,
            todayStr,
            tomorrowStr,
            plannedTasks,
            todayItems,
            todayUnfinished,
            tomorrowItems,
            tomorrowUnfinished
        };
    }

    // Helper: 12H time formatting (e.g. 08:30 -> 8:30 AM, 20:30 -> 8:30 PM)
    function formatTime12H(timeStr) {
        if (!timeStr) return '';
        if (timeStr.includes('AM') || timeStr.includes('PM')) return timeStr;
        const parts = timeStr.split(':');
        if (parts.length < 2) return timeStr;
        let h = parseInt(parts[0], 10);
        const m = parts[1].padStart(2, '0');
        const ampm = h >= 12 ? 'PM' : 'AM';
        h = h % 12;
        if (h === 0) h = 12;
        return `${h}:${m} ${ampm}`;
    }

    // Helper: Duration friendly formatting (e.g. 165 -> 2h45)
    function formatMinutesFriendly(mins) {
        if (!mins || mins <= 0) return '0m';
        const h = Math.floor(mins / 60);
        const m = mins % 60;
        if (h > 0 && m > 0) return `${h}h${m.toString().padStart(2, '0')}`;
        if (h > 0) return `${h}h`;
        return `${m}m`;
    }

    // Helper: Check if a time string is in the future today
    function isTimeInFuture(timeStr) {
        if (!timeStr) return false;
        try {
            let h = 0, m = 0;
            if (timeStr.includes('AM') || timeStr.includes('PM')) {
                const parts = timeStr.split(' ');
                const timeParts = parts[0].split(':');
                h = parseInt(timeParts[0], 10);
                m = parseInt(timeParts[1], 10);
                if (parts[1].toUpperCase() === 'PM' && h < 12) h += 12;
                if (parts[1].toUpperCase() === 'AM' && h === 12) h = 0;
            } else {
                const parts = timeStr.split(':');
                h = parseInt(parts[0], 10);
                m = parseInt(parts[1], 10);
            }
            const now = new Date();
            const taskTime = new Date();
            taskTime.setHours(h, m, 0, 0);
            return taskTime.getTime() > now.getTime();
        } catch (e) {
            return false;
        }
    }

    // Navigation helpers
    function navigateHomeAndClose() {
        close();
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('today');
        } else {
            window.location.hash = '#today';
        }
    }

    function viewTodaysPlanAndClose() {
        close();
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('plan-workspace');
        } else {
            window.location.hash = '#plan-workspace';
        }
    }

    // Web Audio Synthesizer state
    let audioCtx = null;
    let masterGain = null;
    let activeAudioSource = null;
    let synthInterval = null;

    // -------------------------------------------------------------------------
    // INITIALIZATION & PUBLIC API
    // -------------------------------------------------------------------------
    function init() {
        restoreSessionFromStorage();
        bindGlobalKeybindings();

        // Bridge for existing Tempo call-sites
        if (window.TempoTriage) {
            window.TempoTriage.launchFocusMode = function(initialPhase = 'focus', taskTitle = null) {
                if (taskTitle) {
                    open({ taskName: taskTitle });
                } else {
                    openQuickEntry();
                }
            };
        }
    }

    function bindGlobalKeybindings() {
        window.addEventListener('keydown', (e) => {
            if (!session.isOpen) return;

            // Spacebar toggles pause/resume when in active focus and not typing in an input
            if (e.code === 'Space' && (session.phase === 'focus' || session.phase === 'paused')) {
                const targetTag = e.target.tagName.toLowerCase();
                if (targetTag !== 'input' && targetTag !== 'textarea') {
                    e.preventDefault();
                    if (session.phase === 'focus') pauseFocusTimer();
                    else if (session.phase === 'paused') resumeFocusTimer();
                }
            }

            // Esc prompts finish confirmation during focus
            if (e.key === 'Escape') {
                if (session.phase === 'focus' || session.phase === 'paused') {
                    confirmFinishEarly();
                } else if (session.phase === 'setup' || session.phase === 'quick_entry') {
                    close();
                }
            }
        });
    }

    function getRoot() {
        let root = document.getElementById('tempo-focus-zone-root');
        if (!root) {
            root = document.createElement('div');
            root.id = 'tempo-focus-zone-root';
            root.className = 'fixed inset-0 z-50 flex flex-col hidden transition-colors duration-300';
            document.body.appendChild(root);
        }
        return root;
    }

    /**
     * Entry Point A: Task-Based Entry
     * Used by Emergency Mode "Do now", task details, etc.
     */
    function open(options = {}) {
        const root = getRoot();

        // Reset runtime intervals
        stopFocusTimer();
        stopBreakTimer();
        stopAudio();

        session.isOpen = true;
        session.isStandaloneBreak = false;
        session.hasUsedBreakExtension = false;
        session.isFinishingAllowedGameRound = false;
        session.breakActivityType = 'other';
        session.isPostDayBreak = false;
        session.focusElapsedSeconds = 0;

        // Restore saved focus rhythm preference if present
        loadSavedRhythm();

        // Resolve shared task reference
        if (options.taskId) {
            session.taskId = options.taskId;
            resolveSharedTaskData(options.taskId);
        } else if (options.taskName) {
            session.taskId = null;
            session.taskName = options.taskName;
            session.nextAction = options.nextAction || '';
            session.subtasks = [];
        } else {
            session.taskId = null;
            session.taskName = 'No task selected';
            session.nextAction = '';
            session.subtasks = [];
        }

        session.focusSecondsRemaining = session.focusDurationSeconds;
        session.breakSecondsRemaining = session.breakDurationSeconds;

        session.phase = 'setup';

        root.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');

        saveSessionToStorage();
        render();
    }

    /**
     * Entry Point B: Quick Tool Entry
     * Asks: "What are you working on?" -> [Choose an existing task] or [Focus without a task]
     */
    function openQuickEntry() {
        const root = getRoot();

        stopFocusTimer();
        stopBreakTimer();
        stopAudio();

        session.isOpen = true;
        session.isStandaloneBreak = false;
        session.phase = 'quick_entry';
        session.taskId = null;
        session.taskName = 'Independent Focus Session';
        session.nextAction = 'Focus with intentional breaks.';
        session.subtasks = [];
        session.hasUsedBreakExtension = false;
        session.isFinishingAllowedGameRound = false;
        session.breakActivityType = 'other';
        session.isPostDayBreak = false;
        session.focusElapsedSeconds = 0;

        loadSavedRhythm();

        session.focusSecondsRemaining = session.focusDurationSeconds;
        session.breakSecondsRemaining = session.breakDurationSeconds;

        root.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');

        render();
    }

    function close() {
        stopFocusTimer();
        stopBreakTimer();
        stopAudio();

        session.isOpen = false;
        session.isStandaloneBreak = false;
        session.phase = 'setup';

        const root = getRoot();
        if (root) root.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
        document.title = 'Tempo - Student Wellbeing';

        clearSessionStorage();

        // Refresh Emode home if active so progress reflects
        if (window.TempoMode && window.TempoMode.getMode() === 'emergency') {
            window.TempoMode.renderEmodeHome();
        }
    }

    function resolveSharedTaskData(taskId) {
        let task = null;

        // Try Emergency Plan tasks
        if (window.TempoEmergencyFlow) {
            const confirmedPlan = window.TempoEmergencyFlow.getConfirmedPlan();
            if (confirmedPlan && confirmedPlan.plannedTasks) {
                const item = confirmedPlan.plannedTasks.find(pt => pt.task.id === taskId);
                if (item) task = item.task;
            }

            if (!task) {
                const allTasks = window.TempoEmergencyFlow.getTasks();
                task = allTasks.find(t => t.id === taskId);
            }
        }

        if (task) {
            session.taskName = task.name;
            session.subtasks = task.subtasks || [];
            
            // Surface first unfinished subtask
            const firstIncomplete = session.subtasks.find(s => !s.completed);
            if (firstIncomplete) {
                session.nextAction = firstIncomplete.title;
            } else if (session.subtasks.length > 0) {
                session.nextAction = session.subtasks[0].title;
            } else {
                session.nextAction = 'Begin focused preliminary work block.';
            }
        } else {
            session.taskName = 'Planned Academic Task';
            session.nextAction = 'Begin first concrete step.';
            session.subtasks = [];
        }
    }

    function focusWithoutTask() {
        session.taskId = null;
        session.taskName = 'Independent Focus Session';
        session.nextAction = '';
        session.subtasks = [];
        saveSessionToStorage();
        render();
    }

    // -------------------------------------------------------------------------
    // RHYTHM SELECTION & SETUP
    // -------------------------------------------------------------------------
    function selectRhythm(focusMin, breakMin) {
        session.focusDurationSeconds = focusMin * 60;
        session.breakDurationSeconds = breakMin * 60;
        session.focusSecondsRemaining = focusMin * 60;
        session.breakSecondsRemaining = breakMin * 60;
        render();
    }

    function setCustomRhythm() {
        const focusInput = document.getElementById('fz-custom-focus');
        const breakInput = document.getElementById('fz-custom-break');

        const focusVal = focusInput ? parseInt(focusInput.value, 10) : 45;
        const breakVal = breakInput ? parseInt(breakInput.value, 10) : 15;

        if (isNaN(focusVal) || focusVal <= 0 || isNaN(breakVal) || breakVal <= 0) {
            if (window.TempoApp) {
                window.TempoApp.showToast("Please enter valid focus and break durations greater than 0.");
            }
            return;
        }

        session.focusDurationSeconds = focusVal * 60;
        session.breakDurationSeconds = breakVal * 60;
        session.focusSecondsRemaining = focusVal * 60;
        session.breakSecondsRemaining = breakVal * 60;
        render();
    }

    function startFocusSession() {
        // Mark task in progress if supported by shared task architecture
        if (session.taskId && window.TempoEmergencyFlow && window.TempoEmergencyFlow.setTaskInProgress) {
            window.TempoEmergencyFlow.setTaskInProgress(session.taskId, true);
        }

        session.phase = 'focus';
        session.focusSecondsRemaining = session.focusDurationSeconds;
        session.focusElapsedSeconds = 0;
        session.isPostDayBreak = false;

        startFocusTimer();
        startAudio();
        saveSessionToStorage();
        render();
    }

    // -------------------------------------------------------------------------
    // FOCUS TIMER ENGINE
    // -------------------------------------------------------------------------
    function startFocusTimer() {
        stopFocusTimer();
        session.isTimerRunning = true;

        session.timerInterval = setInterval(() => {
            if (session.focusSecondsRemaining > 0) {
                session.focusSecondsRemaining--;
                session.focusElapsedSeconds++;
                updateTimerDisplayDirectly();
            } else {
                handleFocusBlockComplete();
            }
        }, 1000);

        updateTimerDisplayDirectly();
    }

    function pauseFocusTimer() {
        stopFocusTimer();
        session.phase = 'paused';
        saveSessionToStorage();
        render();
    }

    function resumeFocusTimer() {
        session.phase = 'focus';
        startFocusTimer();
        saveSessionToStorage();
        render();
    }

    function stopFocusTimer() {
        if (session.timerInterval) {
            clearInterval(session.timerInterval);
            session.timerInterval = null;
        }
        session.isTimerRunning = false;
    }

    function updateTimerDisplayDirectly() {
        const timerEl = document.getElementById('fz-clock-display');
        const mins = Math.floor(session.focusSecondsRemaining / 60);
        const secs = session.focusSecondsRemaining % 60;
        const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

        if (timerEl) {
            timerEl.textContent = timeStr;
        }

        const ringEl = document.getElementById('fz-timer-circle');
        if (ringEl && session.focusDurationSeconds > 0) {
            const circumference = 691.15;
            const progress = session.focusSecondsRemaining / session.focusDurationSeconds;
            ringEl.style.strokeDashoffset = (circumference * (1 - progress)).toString();
        }

        document.title = `(${timeStr}) Focus • ${session.taskName || 'Tempo'}`;
    }

    function handleFocusBlockComplete() {
        stopFocusTimer();
        stopAudio();
        playNotificationChime();

        session.phase = 'block_complete';
        saveSessionToStorage();
        render();
    }

    // -------------------------------------------------------------------------
    // SUBTASK & NEXT ACTION HANDLERS
    // -------------------------------------------------------------------------
    function completeActiveSubtask() {
        if (!session.taskId || session.subtasks.length === 0) return;

        // Find current first uncompleted subtask
        const activeSubtask = session.subtasks.find(s => !s.completed);
        if (activeSubtask) {
            activeSubtask.completed = true;

            // Sync to persistence store
            if (window.TempoPlanStore) {
                window.TempoPlanStore.updateSubtaskState(session.taskId, activeSubtask.id, { completed: true });
            }

            // Supportive feedback (no confetti)
            if (window.TempoApp) {
                window.TempoApp.showToast(`Completed: "${activeSubtask.title}"`);
            }

            // Find next uncompleted subtask
            const nextIncomplete = session.subtasks.find(s => !s.completed);
            if (nextIncomplete) {
                session.nextAction = nextIncomplete.title;
                render();
            } else {
                // All subtasks done! Prompt confirmation without auto-completing parent task
                session.phase = 'subtasks_all_done';
                render();
            }
        }
    }

    function handleSubtasksAllDoneChoice(isTaskComplete) {
        if (isTaskComplete) {
            finishActiveTaskEarly();
        } else {
            // Task not yet complete: return to active focus countdown
            session.nextAction = 'Wrap up final details and review.';
            session.phase = 'focus';
            render();
        }
    }

    // -------------------------------------------------------------------------
    // FINISH EARLY & COMPLETION CHOICES
    // -------------------------------------------------------------------------
    function confirmFinishEarly() {
        stopFocusTimer();
        session.phase = 'finish_confirm';
        render();
    }

    function handleFinishChoice(choice) {
        if (choice === 'keep_focusing') {
            session.phase = 'focus';
            startFocusTimer();
            render();
            return;
        }

        if (choice === 'mark_done') {
            finishActiveTaskEarly();
            return;
        }

        if (choice === 'stop_here') {
            finishFocusEarly();
            return;
        }
    }

    function markSharedTaskComplete(targetTaskId = null) {
        const idToMark = targetTaskId || session.taskId;
        if (!idToMark) return;

        if (window.TempoEmergencyFlow) {
            const tasks = (typeof window.TempoEmergencyFlow.getTasks === 'function') ? window.TempoEmergencyFlow.getTasks() : [];
            let task = tasks.find(t => t && t.id === idToMark);
            if (!task && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
                const plan = window.TempoEmergencyFlow.getConfirmedPlan();
                const item = plan?.plannedTasks?.find(pt => pt.task && pt.task.id === idToMark);
                if (item) task = item.task;
            }

            if (task) {
                task.completed = true;
                task.isInProgress = false;
            }
        }

        if (window.TempoPlanStore && typeof window.TempoPlanStore.updateTaskState === 'function') {
            window.TempoPlanStore.updateTaskState(idToMark, { completed: true, isInProgress: false });
        }

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(`Task completed! Great job following through.`);
        }
    }

    // -------------------------------------------------------------------------
    // GOAL A: TASK FINISHED BEFORE FOCUS BLOCK ENDS
    // -------------------------------------------------------------------------
    function finishActiveTaskEarly() {
        stopFocusTimer();
        const ctx = getPlanContext();

        if (!session.taskId) {
            confirmFinishEarly();
            return;
        }

        // Check if there are other unfinished tasks planned for TODAY
        const otherUnfinishedToday = ctx.todayUnfinished.filter(pt => pt.task.id !== session.taskId);

        if (otherUnfinishedToday.length > 0) {
            session.phase = 'task_finished_early';
        } else {
            session.phase = 'last_task_today';
        }
        saveSessionToStorage();
        render();
    }

    function continueWithNextTask() {
        if (session.taskId) {
            markSharedTaskComplete(session.taskId);
        }

        const ctx = getPlanContext();
        // Resolve next unfinished task from today's plan in execution order
        const nextItem = ctx.todayItems.find(pt => pt.task && pt.task.id !== session.taskId && !pt.task.completed);
        if (nextItem && nextItem.task) {
            session.taskId = nextItem.task.id;
            session.taskName = nextItem.task.name;
            session.subtasks = nextItem.task.subtasks || [];
            const firstIncomplete = session.subtasks.find(s => !s.completed);
            session.nextAction = firstIncomplete ? firstIncomplete.title : (session.subtasks.length > 0 ? session.subtasks[0].title : 'Begin focused preliminary work block.');

            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setTaskInProgress === 'function') {
                window.TempoEmergencyFlow.setTaskInProgress(nextItem.task.id, true);
            }
            if (window.TempoPlanStore && typeof window.TempoPlanStore.updateTaskState === 'function') {
                window.TempoPlanStore.updateTaskState(nextItem.task.id, { isInProgress: true });
            }
        }

        // Invariant: Preserve the EXACT remaining timer in current block (do NOT reset)
        session.phase = 'focus';
        startFocusTimer();
        saveSessionToStorage();
        render();
    }

    function markDoneAndTakeBreak() {
        if (session.taskId) {
            markSharedTaskComplete(session.taskId);
        }
        stopFocusTimer();
        session.phase = 'pre_break_orientation';
        saveSessionToStorage();
        render();
    }

    function finishFocusEarly() {
        stopFocusTimer();
        stopBreakTimer();
        const ctx = getPlanContext();

        // Check if unfinished tasks remain today
        const unfinishedToday = ctx.todayItems.filter(pt => pt.task && !pt.task.completed);

        if (unfinishedToday.length > 0) {
            session.phase = 'finish_early_orient';
            saveSessionToStorage();
            render();
        } else {
            close();
        }
    }

    function markLastTaskCompleted() {
        if (session.taskId) {
            markSharedTaskComplete(session.taskId);
        }
        stopFocusTimer();
        session.taskId = null;
        session.phase = 'today_complete';
        saveSessionToStorage();
        render();
    }

    function startPostDayBreak() {
        startBreakPeriod(true);
    }

    function openReviewTomorrow() {
        session.phase = 'review_tomorrow';
        saveSessionToStorage();
        render();
    }

    function startTomorrowTaskEarly(taskId) {
        session.taskId = taskId;
        resolveSharedTaskData(taskId);
        readyForNextFocusBlock();
    }

    // -------------------------------------------------------------------------
    // BREAK ENGINE & PARENT BREAK TIMER
    // -------------------------------------------------------------------------
    function openStandaloneBreak() {
        const root = getRoot();
        stopFocusTimer();
        stopBreakTimer();
        stopAudio();

        loadSavedRhythm();

        session.isOpen = true;
        session.isStandaloneBreak = true;
        session.taskId = null;
        session.taskName = 'Recovery Break';
        session.nextAction = '';
        session.subtasks = [];
        session.phase = 'break';
        session.hasUsedBreakExtension = false;
        session.isFinishingAllowedGameRound = false;
        session.isPostDayBreak = false;
        session.breakActivityType = 'other';
        session.breakSecondsRemaining = session.breakDurationSeconds;

        root.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');

        startBreakTimer();
        render();
    }

    function startBreakPeriod(isPostDay = false) {
        const root = getRoot();
        session.isOpen = true;
        root.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');

        stopFocusTimer();
        session.phase = 'break';
        session.breakSecondsRemaining = session.breakDurationSeconds;
        session.hasUsedBreakExtension = false;
        session.isFinishingAllowedGameRound = false;
        session.isPostDayBreak = !!isPostDay;

        startBreakTimer();
        saveSessionToStorage();
        render();
    }

    function startBreakTimer() {
        stopBreakTimer();
        session.isBreakRunning = true;

        session.breakInterval = setInterval(() => {
            if (session.breakSecondsRemaining > 0) {
                session.breakSecondsRemaining--;
                updateBreakDisplayDirectly();
            } else {
                handleBreakEnd();
            }
        }, 1000);

        updateBreakDisplayDirectly();
    }

    function stopBreakTimer() {
        if (session.breakInterval) {
            clearInterval(session.breakInterval);
            session.breakInterval = null;
        }
        session.isBreakRunning = false;
    }

    function updateBreakDisplayDirectly() {
        const breakClock = document.getElementById('fz-break-clock');
        const mins = Math.floor(session.breakSecondsRemaining / 60);
        const secs = session.breakSecondsRemaining % 60;
        const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

        if (breakClock) {
            breakClock.textContent = timeStr;
        }

        const ringEl = document.getElementById('fz-break-circle');
        if (ringEl && session.breakDurationSeconds > 0) {
            const circumference = 439.82;
            const progress = session.breakSecondsRemaining / session.breakDurationSeconds;
            ringEl.style.strokeDashoffset = (circumference * (1 - progress)).toString();
        }

        const badgeEl = document.getElementById('fz-break-badge');
        if (badgeEl) {
            badgeEl.textContent = `Break: ${timeStr}`;
        }

        document.title = `(${timeStr}) Break • Tempo`;
    }

    function handleBreakEnd() {
        stopBreakTimer();
        playNotificationChime();

        // If user is currently playing Gentle Match and is allowed to finish the current round
        if (session.phase === 'break_game' && session.isFinishingAllowedGameRound) {
            return;
        }

        session.phase = 'break_ended';
        saveSessionToStorage();
        render();
    }

    function selectBreakActivity(activity) {
        if (activity === 'game' || activity === 'round_game') {
            session.breakActivityType = 'round_game';
            initGentleMatch();
            session.phase = 'break_game';
        } else if (activity === 'non_round_game') {
            session.breakActivityType = 'non_round_game';
            session.phase = 'break';
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Enjoy your open-ended game time.");
            }
        } else if (activity === 'stress') {
            session.breakActivityType = 'other';
            if (window.TempoStressRelief) {
                window.TempoStressRelief.openModal();
            }
            session.phase = 'break';
        } else if (activity === 'move') {
            session.breakActivityType = 'other';
            session.selectedMoveOption = null;
            session.phase = 'break_move';
        } else if (activity === 'just') {
            session.breakActivityType = 'other';
            session.phase = 'break_just';
        } else {
            session.breakActivityType = 'other';
            session.phase = 'break';
        }
        render();
    }

    function returnToBreakHub() {
        session.phase = 'break';
        render();
    }

    function extendBreak5Minutes() {
        if (session.hasUsedBreakExtension) return;

        session.hasUsedBreakExtension = true;
        session.breakSecondsRemaining += (5 * 60);
        session.phase = 'break';

        startBreakTimer();
        saveSessionToStorage();
        render();

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("Added 5 extra minutes to your break.");
        }
    }

    function startRoundGrace() {
        if (session.hasUsedBreakExtension) return;

        session.hasUsedBreakExtension = true;
        session.phase = 'round_grace';
        saveSessionToStorage();
        render();
    }

    function confirmRoundDone() {
        session.phase = 'return_transition';
        saveSessionToStorage();
        render();
    }

    function endBreakEarly() {
        stopBreakTimer();
        if (session.isStandaloneBreak) {
            close();
            return;
        }
        session.phase = 'return_transition';
        saveSessionToStorage();
        render();
    }

    function readyForNextFocusBlock() {
        const ctx = getPlanContext();
        // Resolve next unfinished task from today in execution order
        const nextItem = ctx.todayItems.find(pt => pt.task && !pt.task.completed);
        if (nextItem && nextItem.task) {
            session.taskId = nextItem.task.id;
            session.taskName = nextItem.task.name;
            session.subtasks = nextItem.task.subtasks || [];
            const firstIncomplete = session.subtasks.find(s => !s.completed);
            session.nextAction = firstIncomplete ? firstIncomplete.title : (session.subtasks.length > 0 ? session.subtasks[0].title : 'Begin focused preliminary work block.');

            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setTaskInProgress === 'function') {
                window.TempoEmergencyFlow.setTaskInProgress(nextItem.task.id, true);
            }
            if (window.TempoPlanStore && typeof window.TempoPlanStore.updateTaskState === 'function') {
                window.TempoPlanStore.updateTaskState(nextItem.task.id, { isInProgress: true });
            }
        }

        session.phase = 'focus';
        session.focusSecondsRemaining = session.focusDurationSeconds;
        session.breakSecondsRemaining = session.breakDurationSeconds;
        session.focusElapsedSeconds = 0;
        session.hasUsedBreakExtension = false;
        session.isPostDayBreak = false;

        startFocusTimer();
        startAudio();
        saveSessionToStorage();
        render();
    }

    // -------------------------------------------------------------------------
    // GOAL C: CHANGE FOCUS RHYTHM (POST-BREAK CHECKPOINT)
    // -------------------------------------------------------------------------
    function openChangeRhythmModal() {
        const fMin = Math.round(session.focusDurationSeconds / 60);
        const bMin = Math.round(session.breakDurationSeconds / 60);
        if (fMin === 25 && bMin === 5) {
            rhythmModalState.selectedPreset = '25_5';
        } else if (fMin === 45 && bMin === 15) {
            rhythmModalState.selectedPreset = '45_15';
        } else if (fMin === 50 && bMin === 10) {
            rhythmModalState.selectedPreset = '50_10';
        } else {
            rhythmModalState.selectedPreset = 'custom';
            rhythmModalState.customFocus = fMin;
            rhythmModalState.customBreak = bMin;
        }
        session.phase = 'change_rhythm';
        saveSessionToStorage();
        render();
    }

    function selectRhythmChoice(choice) {
        rhythmModalState.selectedPreset = choice;
        render();
    }

    function cancelChangeRhythm() {
        session.phase = 'return_transition';
        saveSessionToStorage();
        render();
    }

    function saveRhythmFromModal() {
        let fMin = 45;
        let bMin = 15;

        if (rhythmModalState.selectedPreset === '25_5') {
            fMin = 25;
            bMin = 5;
        } else if (rhythmModalState.selectedPreset === '45_15') {
            fMin = 45;
            bMin = 15;
        } else if (rhythmModalState.selectedPreset === '50_10') {
            fMin = 50;
            bMin = 10;
        } else if (rhythmModalState.selectedPreset === 'custom') {
            const focusInput = document.getElementById('fz-modal-custom-focus');
            const breakInput = document.getElementById('fz-modal-custom-break');
            const parsedFocus = focusInput ? parseInt(focusInput.value, 10) : rhythmModalState.customFocus;
            const parsedBreak = breakInput ? parseInt(breakInput.value, 10) : rhythmModalState.customBreak;

            if (isNaN(parsedFocus) || parsedFocus <= 0 || isNaN(parsedBreak) || parsedBreak <= 0) {
                if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                    window.TempoApp.showToast("Please enter valid focus and break durations greater than 0.");
                }
                return;
            }
            fMin = parsedFocus;
            bMin = parsedBreak;
            rhythmModalState.customFocus = fMin;
            rhythmModalState.customBreak = bMin;
        }

        // Apply strictly to future focus blocks (not mutating current running block)
        session.focusDurationSeconds = fMin * 60;
        session.breakDurationSeconds = bMin * 60;

        // Persist rhythm preference across blocks and sessions
        try {
            localStorage.setItem('tempo_focus_rhythm', JSON.stringify({
                focusDurationSeconds: session.focusDurationSeconds,
                breakDurationSeconds: session.breakDurationSeconds
            }));
        } catch (e) {}

        session.phase = 'rhythm_updated';
        saveSessionToStorage();
        render();
    }

    // -------------------------------------------------------------------------
    // MINI-GAME: GENTLE MATCH (MVP BOUNDED BREAK GAME)
    // -------------------------------------------------------------------------
    function initGentleMatch() {
        const symbols = ['🌿', '🍵', '☁️', '🌸', '🕯️', '🌙'];
        const deck = [...symbols, ...symbols];

        // Shuffle deck
        for (let i = deck.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [deck[i], deck[j]] = [deck[j], deck[i]];
        }

        session.gameState = {
            cards: deck.map((symbol, id) => ({
                id,
                symbol,
                isFlipped: false,
                isMatched: false
            })),
            flippedIndices: [],
            isProcessing: false,
            isCompleted: false
        };
    }

    function handleCardClick(index) {
        const game = session.gameState;
        if (!game || game.isProcessing) return;

        const card = game.cards[index];
        if (card.isMatched || card.isFlipped) return;

        // Flip card
        card.isFlipped = true;
        game.flippedIndices.push(index);

        if (game.flippedIndices.length === 2) {
            const idx1 = game.flippedIndices[0];
            const idx2 = game.flippedIndices[1];
            const card1 = game.cards[idx1];
            const card2 = game.cards[idx2];

            if (card1.symbol === card2.symbol) {
                // Matched!
                card1.isMatched = true;
                card2.isMatched = true;
                game.flippedIndices = [];

                // Check if all cards matched
                const allMatched = game.cards.every(c => c.isMatched);
                if (allMatched) {
                    game.isCompleted = true;

                    // If break ended while finishing this allowed round, enforce transition
                    if (session.breakSecondsRemaining <= 0) {
                        setTimeout(() => {
                            session.phase = 'break_ended';
                            render();
                        }, 1200);
                        return;
                    }
                }
                render();
            } else {
                // Mismatch: flip back after brief pause
                game.isProcessing = true;
                render();
                setTimeout(() => {
                    card1.isFlipped = false;
                    card2.isFlipped = false;
                    game.flippedIndices = [];
                    game.isProcessing = false;
                    render();
                }, 750);
            }
        } else {
            render();
        }
    }

    function allowFinishCurrentGameRound() {
        session.isFinishingAllowedGameRound = true;
        session.phase = 'break_game';
        render();
    }

    // -------------------------------------------------------------------------
    // ATMOSPHERE & BUILT-IN BACKGROUNDS
    // -------------------------------------------------------------------------
    function setBackground(bgKey) {
        if (!['cream', 'sunset', 'sky', 'night'].includes(bgKey)) return;
        session.background = bgKey;
        saveSessionToStorage();
        render();
    }

    function getBackgroundStyles() {
        const isFocusOrPaused = session.phase === 'focus' || session.phase === 'paused';
        const activeBg = isFocusOrPaused ? session.background : 'cream';

        switch (activeBg) {
            case 'sunset':
                return {
                    name: 'sunset',
                    containerClass: 'fz-bg-sunset text-[#202124]',
                    cardClass: 'bg-white/85 backdrop-blur-md border border-white/60 shadow-lg text-[#202124]',
                    pillClass: 'bg-white/80 backdrop-blur-md border border-white/60 text-[#202124]',
                    controlBarClass: 'fz-control-bar text-[#202124]',
                    accentColor: '#FF6B2C',
                    subtextColor: 'text-stone-700',
                    isDark: false
                };
            case 'sky':
                return {
                    name: 'sky',
                    containerClass: 'fz-bg-sky text-[#0F172A]',
                    cardClass: 'bg-white/85 backdrop-blur-md border border-white/60 shadow-lg text-[#0F172A]',
                    pillClass: 'bg-white/80 backdrop-blur-md border border-white/60 text-[#0F172A]',
                    controlBarClass: 'fz-control-bar text-[#0F172A]',
                    accentColor: '#0284C7',
                    subtextColor: 'text-slate-600',
                    isDark: false
                };
            case 'night':
                return {
                    name: 'night',
                    containerClass: 'fz-bg-night text-[#F8FAFC]',
                    cardClass: 'bg-slate-900/80 backdrop-blur-md border border-slate-700/60 shadow-2xl text-white',
                    pillClass: 'bg-slate-800/80 backdrop-blur-md border border-slate-700/60 text-white',
                    controlBarClass: 'fz-control-bar text-[#F8FAFC]',
                    accentColor: '#FF6B2C',
                    subtextColor: 'text-stone-400',
                    isDark: true
                };
            case 'cream':
            default:
                return {
                    name: 'cream',
                    containerClass: 'fz-bg-cream text-[#202124]',
                    cardClass: 'bg-white border border-[#EAE4DF] shadow-xs text-[#202124]',
                    pillClass: 'bg-white border border-[#EAE4DF] text-[#202124]',
                    controlBarClass: 'fz-control-bar text-[#202124]',
                    accentColor: '#FF6B2C',
                    subtextColor: 'text-[#6F6B68]',
                    isDark: false
                };
        }
    }

    function renderAtmosphereArtwork(style) {
        if (session.phase !== 'focus' && session.phase !== 'paused') {
            return '';
        }

        if (session.background === 'sunset') {
            return `
                <div class="fz-glowing-sun" aria-hidden="true"></div>
                <svg class="fz-mountain-silhouette" viewBox="0 0 1440 240" fill="none" preserveAspectRatio="none" aria-hidden="true">
                    <path d="M0,170 C280,105 480,140 760,165 C1040,190 1220,120 1440,150 L1440,240 L0,240 Z" fill="#4A2840" opacity="0.6"/>
                    <path d="M0,190 C200,145 520,205 840,160 C1160,115 1320,170 1440,185 L1440,240 L0,240 Z" fill="#2F172C" opacity="0.85"/>
                    <path d="M0,205 C340,170 640,225 980,185 C1220,155 1360,195 1440,205 L1440,240 L0,240 Z" fill="#1D0B1B"/>
                </svg>
            `;
        }

        if (session.background === 'sky') {
            return `
                <svg class="fz-mountain-silhouette" viewBox="0 0 1440 240" fill="none" preserveAspectRatio="none" aria-hidden="true">
                    <path d="M0,170 C280,110 480,140 760,165 C1040,190 1220,125 1440,150 L1440,240 L0,240 Z" fill="#94A3B8" opacity="0.45"/>
                    <path d="M0,190 C200,145 520,205 840,160 C1160,120 1320,170 1440,185 L1440,240 L0,240 Z" fill="#64748B" opacity="0.75"/>
                    <path d="M0,205 C340,170 640,225 980,185 C1220,155 1360,195 1440,205 L1440,240 L0,240 Z" fill="#334155"/>
                </svg>
            `;
        }

        if (session.background === 'night') {
            return `
                <div class="absolute top-10 right-1/4 w-8 h-8 rounded-full border-2 border-amber-100/30 opacity-70 pointer-events-none" aria-hidden="true"></div>
                <svg class="fz-mountain-silhouette" viewBox="0 0 1440 240" fill="none" preserveAspectRatio="none" aria-hidden="true">
                    <path d="M0,170 C280,110 480,140 760,165 C1040,190 1220,125 1440,150 L1440,240 L0,240 Z" fill="#1E293B" opacity="0.5"/>
                    <path d="M0,190 C200,145 520,205 840,160 C1160,120 1320,170 1440,185 L1440,240 L0,240 Z" fill="#0F172A" opacity="0.8"/>
                    <path d="M0,205 C340,170 640,225 980,185 C1220,155 1360,195 1440,205 L1440,240 L0,240 Z" fill="#050811"/>
                </svg>
            `;
        }

        return '';
    }

    // -------------------------------------------------------------------------
    // BUILT-IN SOUND SYNTHESIZER (100% Offline Web Audio)
    // -------------------------------------------------------------------------
    function initAudioContext() {
        if (!audioCtx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            audioCtx = new AudioContext();
            masterGain = audioCtx.createGain();
            masterGain.gain.setValueAtTime(session.isSoundMuted ? 0 : session.soundVolume * 0.08, audioCtx.currentTime);
            masterGain.connect(audioCtx.destination);
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
    }

    function setSound(type) {
        session.soundType = type;
        saveSessionToStorage();
        if (session.isTimerRunning) {
            startAudio();
        }
        render();
    }

    function setVolume(val, shouldRender = false) {
        session.soundVolume = parseFloat(val);
        session.isSoundMuted = false;
        if (masterGain && audioCtx) {
            masterGain.gain.setValueAtTime(session.soundVolume * 0.08, audioCtx.currentTime);
        }
        saveSessionToStorage();
        if (shouldRender) {
            render();
        }
    }

    function toggleMute() {
        session.isSoundMuted = !session.isSoundMuted;
        if (masterGain && audioCtx) {
            masterGain.gain.setValueAtTime(session.isSoundMuted ? 0 : session.soundVolume * 0.08, audioCtx.currentTime);
        }
        render();
    }

    function startAudio() {
        if (session.soundType === 'none') {
            stopAudio();
            return;
        }

        try {
            initAudioContext();
            stopAudio();

            if (session.soundType === 'rain') {
                // Gentle continuous rain via brown/pink filtered noise buffer
                const bufferSize = audioCtx.sampleRate * 2;
                const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
                const data = buffer.getChannelData(0);
                let last = 0;
                for (let i = 0; i < bufferSize; i++) {
                    const white = Math.random() * 2 - 1;
                    data[i] = (last + (0.02 * white)) / 1.02;
                    last = data[i];
                    data[i] *= 3.5;
                }
                const source = audioCtx.createBufferSource();
                source.buffer = buffer;
                source.loop = true;

                const filter = audioCtx.createBiquadFilter();
                filter.type = 'lowpass';
                filter.frequency.setValueAtTime(650, audioCtx.currentTime);

                source.connect(filter);
                filter.connect(masterGain);
                source.start();
                activeAudioSource = source;

            } else if (session.soundType === 'cafe') {
                // Warm ambient cafe tone via filtered band noise + low resonant hum
                const bufferSize = audioCtx.sampleRate * 2;
                const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
                const data = buffer.getChannelData(0);
                for (let i = 0; i < bufferSize; i++) {
                    data[i] = (Math.random() * 2 - 1) * 0.4;
                }
                const source = audioCtx.createBufferSource();
                source.buffer = buffer;
                source.loop = true;

                const filter = audioCtx.createBiquadFilter();
                filter.type = 'bandpass';
                filter.frequency.setValueAtTime(320, audioCtx.currentTime);
                filter.Q.setValueAtTime(1.2, audioCtx.currentTime);

                source.connect(filter);
                filter.connect(masterGain);
                source.start();
                activeAudioSource = source;

            } else if (session.soundType === 'music') {
                // Soft focus music via slow ambient pentatonic drone
                const chordNotes = [261.63, 329.63, 392.00, 523.25]; // C4, E4, G4, C5
                const osc = audioCtx.createOscillator();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(chordNotes[0], audioCtx.currentTime);

                const filter = audioCtx.createBiquadFilter();
                filter.type = 'lowpass';
                filter.frequency.setValueAtTime(450, audioCtx.currentTime);

                osc.connect(filter);
                filter.connect(masterGain);
                osc.start();
                activeAudioSource = osc;

                // Cycle gentle harmony
                let noteIndex = 0;
                synthInterval = setInterval(() => {
                    if (!audioCtx || session.soundType !== 'music') {
                        clearInterval(synthInterval);
                        return;
                    }
                    noteIndex = (noteIndex + 1) % chordNotes.length;
                    osc.frequency.setTargetAtTime(chordNotes[noteIndex], audioCtx.currentTime, 1.2);
                }, 4000);
            }
        } catch (e) {
            console.log("Audio synthesis notice:", e);
        }
    }

    function stopAudio() {
        if (synthInterval) {
            clearInterval(synthInterval);
            synthInterval = null;
        }
        if (activeAudioSource) {
            try {
                activeAudioSource.stop();
                activeAudioSource.disconnect();
            } catch (e) {}
            activeAudioSource = null;
        }
    }

    function playNotificationChime() {
        try {
            initAudioContext();
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();

            osc.type = 'sine';
            osc.frequency.setValueAtTime(523.25, audioCtx.currentTime); // C5
            osc.frequency.exponentialRampToValueAtTime(659.25, audioCtx.currentTime + 0.3); // E5

            gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.9);

            osc.connect(gain);
            gain.connect(audioCtx.destination);

            osc.start();
            osc.stop(audioCtx.currentTime + 1.0);
        } catch (e) {}
    }

    // -------------------------------------------------------------------------
    // LOCAL SESSION PERSISTENCE (Safe refresh recovery)
    // -------------------------------------------------------------------------
    function saveSessionToStorage() {
        try {
            const data = {
                phase: session.phase,
                taskId: session.taskId,
                taskName: session.taskName,
                nextAction: session.nextAction,
                focusDurationSeconds: session.focusDurationSeconds,
                breakDurationSeconds: session.breakDurationSeconds,
                focusSecondsRemaining: session.focusSecondsRemaining,
                breakSecondsRemaining: session.breakSecondsRemaining,
                hasUsedBreakExtension: session.hasUsedBreakExtension,
                breakActivityType: session.breakActivityType,
                isPostDayBreak: session.isPostDayBreak,
                background: session.background,
                soundType: session.soundType,
                soundVolume: session.soundVolume,
                timestamp: Date.now()
            };
            localStorage.setItem('tempo_focus_session', JSON.stringify(data));
        } catch (e) {}
    }

    function restoreSessionFromStorage() {
        try {
            const raw = localStorage.getItem('tempo_focus_session');
            if (!raw) return;
            const data = JSON.parse(raw);
            if (!data) return;

            // Only restore if saved less than 3 hours ago
            if (Date.now() - data.timestamp < 3 * 60 * 60 * 1000) {
                session.taskId = data.taskId;
                session.taskName = data.taskName || 'Independent Focus Session';
                session.nextAction = data.nextAction || 'Single focus objective.';
                session.focusDurationSeconds = data.focusDurationSeconds || 45 * 60;
                session.breakDurationSeconds = data.breakDurationSeconds || 15 * 60;
                session.focusSecondsRemaining = data.focusSecondsRemaining || 45 * 60;
                session.breakSecondsRemaining = data.breakSecondsRemaining || 15 * 60;
                session.hasUsedBreakExtension = !!data.hasUsedBreakExtension;
                session.breakActivityType = data.breakActivityType || 'other';
                session.isPostDayBreak = !!data.isPostDayBreak;
                session.background = data.background || 'cream';
                session.soundType = data.soundType || 'none';
                session.soundVolume = data.soundVolume || 0.5;

                // Restore non-active screen conservatively so timer does not run in background
                if (data.phase === 'focus' || data.phase === 'paused') {
                    session.phase = 'paused';
                }
            } else {
                clearSessionStorage();
            }
        } catch (e) {}
    }

    function clearSessionStorage() {
        try {
            localStorage.removeItem('tempo_focus_session');
        } catch (e) {}
    }

    // -------------------------------------------------------------------------
    // MAIN RENDER DISPATCHER
    // -------------------------------------------------------------------------
    function render() {
        const root = getRoot();
        if (!root || !session.isOpen) return;

        const style = getBackgroundStyles();
        root.className = `fixed inset-0 z-50 flex flex-col p-4 sm:p-6 overflow-y-auto ${style.containerClass} transition-colors duration-500`;

        let contentHtml = '';
        switch (session.phase) {
            case 'quick_entry':
                contentHtml = renderQuickEntry(style);
                break;
            case 'setup':
                contentHtml = renderSetup(style);
                break;
            case 'focus':
                contentHtml = renderActiveFocus(style);
                break;
            case 'paused':
                contentHtml = renderFocusPaused(style);
                break;
            case 'finish_confirm':
                contentHtml = renderFinishConfirm(style);
                break;
            case 'task_finished_early':
                contentHtml = renderTaskFinishedEarly(style);
                break;
            case 'last_task_today':
                contentHtml = renderLastTaskToday(style);
                break;
            case 'pre_break_orientation':
                contentHtml = renderPreBreakOrientation(style);
                break;
            case 'finish_early_orient':
                contentHtml = renderFinishEarlyOrient(style);
                break;
            case 'today_complete':
                contentHtml = renderTodayComplete(style);
                break;
            case 'review_tomorrow':
                contentHtml = renderReviewTomorrow(style);
                break;
            case 'subtasks_all_done':
                contentHtml = renderSubtasksAllDone(style);
                break;
            case 'block_complete':
                contentHtml = renderBlockComplete(style);
                break;
            case 'break':
                contentHtml = renderBreakHub(style);
                break;
            case 'break_game':
                contentHtml = renderGentleMatch(style);
                break;
            case 'break_move':
                contentHtml = renderMoveALittle(style);
                break;
            case 'break_just':
                contentHtml = renderJustTakeABreak(style);
                break;
            case 'break_ended':
                contentHtml = renderBreakEnded(style);
                break;
            case 'round_grace':
                contentHtml = renderRoundGrace(style);
                break;
            case 'change_rhythm':
                contentHtml = renderChangeRhythm(style);
                break;
            case 'rhythm_updated':
                contentHtml = renderRhythmUpdated(style);
                break;
            case 'return_transition':
                contentHtml = renderReturnTransition(style);
                break;
            default:
                contentHtml = renderSetup(style);
                break;
        }

        root.innerHTML = `
            ${renderAtmosphereArtwork(style)}
            <div class="relative z-10 w-full flex flex-col flex-1 min-h-full">
                ${renderTopBar(style)}
                <div class="flex-1 flex items-center justify-center py-4 sm:py-6 w-full max-w-2xl mx-auto">
                    ${contentHtml}
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // TOP NAVIGATION & ATMOSPHERE BAR (Always accessible SOS)
    // -------------------------------------------------------------------------
    function renderTopBar(style) {
        let navButtonHtml = '';
        if (session.phase === 'setup' || session.phase === 'quick_entry') {
            navButtonHtml = `
                <button type="button" onclick="window.TempoFocusZone.close()" 
                        class="text-xs font-semibold ${style.isDark ? 'text-stone-300 hover:text-white' : 'text-stone-600 hover:text-stone-900'} transition flex items-center space-x-1.5 px-2 py-1 rounded-lg">
                    <span>←</span>
                    <span>Back</span>
                </button>
            `;
        } else if (session.phase === 'focus' || session.phase === 'paused') {
            navButtonHtml = `
                <button type="button" onclick="window.TempoFocusZone.handleExitClick()" 
                        class="text-xs font-semibold ${style.isDark ? 'text-stone-300 hover:text-white' : 'text-stone-600 hover:text-stone-900'} transition flex items-center space-x-1.5 px-2 py-1 rounded-lg">
                    <span>←</span>
                    <span>Exit Focus</span>
                </button>
            `;
        } else if (session.phase.startsWith('break')) {
            navButtonHtml = `
                <button type="button" onclick="window.TempoFocusZone.handleExitClick()" 
                        class="text-xs font-semibold text-stone-600 hover:text-stone-900 transition flex items-center space-x-1.5 px-2 py-1 rounded-lg">
                    <span>←</span>
                    <span>Exit Focus</span>
                </button>
            `;
        } else {
            navButtonHtml = `
                <button type="button" onclick="window.TempoFocusZone.close()" 
                        class="text-xs font-semibold text-stone-600 hover:text-stone-900 transition flex items-center space-x-1.5 px-2 py-1 rounded-lg">
                    <span>←</span>
                    <span>Exit</span>
                </button>
            `;
        }

        return `
            <div class="w-full max-w-4xl mx-auto flex items-center justify-between gap-3 text-xs shrink-0 select-none pb-2">
                <!-- Left: Brand Logo & Navigation Action -->
                <div class="flex items-center space-x-4">
                    <div class="flex items-center space-x-2">
                        <span class="font-heading font-extrabold text-lg tracking-tight ${style.isDark ? 'text-white' : 'text-[#202124]'}">Tempo</span>
                        <span class="w-2.5 h-2.5 rounded-full bg-[#FF6B2C]"></span>
                    </div>
                    ${navButtonHtml}
                </div>

                <!-- Right: Safety SOS & User Avatar -->
                <div class="flex items-center space-x-3">
                    <!-- Standard Safety SOS Button -->
                    <button type="button" onclick="window.TempoEmergencySupport.openSOS()" 
                            class="btn-sos px-3.5 py-1.5 rounded-full font-bold flex items-center space-x-1 shadow-xs transition hover:brightness-105 active:scale-95" 
                            title="Emergency Safety Support">
                        <span>⚡</span>
                        <span>SOS</span>
                    </button>
                    <!-- User Avatar -->
                    <div class="w-8 h-8 rounded-full bg-[#FFD2BA] text-[#B83D08] font-bold text-xs flex items-center justify-center border border-white/60 shadow-xs" title="Logged in as Student">
                        L
                    </div>
                </div>
            </div>
        `;
    }

    function handleExitClick() {
        if (session.phase === 'focus' || session.phase === 'paused') {
            confirmFinishEarly();
        } else if (session.phase === 'break' || session.phase === 'break_game' || session.phase === 'break_move' || session.phase === 'break_just') {
            const leave = confirm("Exit Focus Session during break?");
            if (leave) close();
        } else {
            close();
        }
    }

    // -------------------------------------------------------------------------
    // VIEW 1: QUICK TOOL ENTRY CHOICE
    // -------------------------------------------------------------------------
    function renderQuickEntry(style) {
        // Collect existing shared tasks
        const availableTasks = [];
        if (window.TempoEmergencyFlow) {
            const confirmedPlan = window.TempoEmergencyFlow.getConfirmedPlan();
            if (confirmedPlan && confirmedPlan.plannedTasks) {
                confirmedPlan.plannedTasks.forEach(pt => {
                    if (pt.task && !pt.task.completed) {
                        availableTasks.push(pt.task);
                    }
                });
            }
            if (availableTasks.length === 0) {
                const rawTasks = window.TempoEmergencyFlow.getTasks();
                rawTasks.forEach(t => {
                    if (!t.completed && !availableTasks.some(existing => existing.id === t.id)) {
                        availableTasks.push(t);
                    }
                });
            }
        }

        return `
            <div class="tempo-card w-full max-w-lg p-6 sm:p-8 space-y-6 rounded-3xl ${style.cardClass} text-center">
                <div class="space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">FOCUS ZONE</span>
                    <h3 class="font-heading text-2xl font-bold text-[#202124]">What are you working on?</h3>
                    <p class="text-xs text-[#6F6B68]">
                        Work on a specific task from your plan, or start an independent timed focus block.
                    </p>
                </div>

                <div class="space-y-3 pt-2 text-left">
                    ${availableTasks.length > 0 ? `
                        <div class="space-y-2">
                            <span class="text-[11px] font-bold text-stone-500 uppercase tracking-wider">Choose a planned task:</span>
                            <div class="max-h-48 overflow-y-auto space-y-2 pr-1">
                                ${availableTasks.map(t => `
                                    <button type="button" onclick="window.TempoFocusZone.open({ taskId: '${t.id}' })"
                                            class="w-full p-3.5 rounded-2xl border border-stone-200 hover:border-[#FF6B2C] bg-white hover:bg-[#FFF9F4] transition flex items-center justify-between group">
                                        <div class="min-w-0 pr-2">
                                            <h4 class="text-xs font-bold text-[#202124] group-hover:text-[#FF6B2C] truncate">${escapeHTML(t.name)}</h4>
                                            <p class="text-[11px] text-[#6F6B68]">${t.durationLabel ? `~${t.durationLabel}` : 'Time not estimated'}</p>
                                        </div>
                                        <span class="text-xs text-[#FF6B2C] font-bold group-hover:translate-x-1 transition-transform">Start →</span>
                                    </button>
                                `).join('')}
                            </div>
                        </div>

                        <div class="relative flex py-1 items-center">
                            <div class="flex-grow border-t border-gray-200"></div>
                            <span class="flex-shrink mx-3 text-[11px] text-gray-400 font-semibold uppercase">Or</span>
                            <div class="flex-grow border-t border-gray-200"></div>
                        </div>
                    ` : ''}

                    <button type="button" onclick="window.TempoFocusZone.open({ taskName: 'Independent Focus Session' })"
                            class="w-full p-4 rounded-2xl border-2 border-dashed border-stone-300 hover:border-[#FF6B2C] bg-stone-50 hover:bg-white text-center transition group">
                        <span class="text-sm font-bold text-[#202124] group-hover:text-[#FF6B2C] block">Focus without a task</span>
                        <span class="text-xs text-[#6F6B68]">Use the full focus and break timer without modifying any task.</span>
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // VIEW 2: SETUP SCREEN (Panel 1 in Mockup)
    // -------------------------------------------------------------------------
    function renderSetup(style) {
        const is4515 = session.focusDurationSeconds === 45 * 60 && session.breakDurationSeconds === 15 * 60;
        const is255 = session.focusDurationSeconds === 25 * 60 && session.breakDurationSeconds === 5 * 60;
        const is5010 = session.focusDurationSeconds === 50 * 60 && session.breakDurationSeconds === 10 * 60;
        const isCustom = !is4515 && !is255 && !is5010;

        return `
            <div class="tempo-card w-full max-w-lg p-6 sm:p-8 space-y-6 rounded-3xl ${style.cardClass} text-center">
                <div class="space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C] block">FOCUS ZONE</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        ${session.taskId ? escapeHTML(session.taskName) : 'No task selected'}
                    </h2>
                </div>

                <!-- Compact Task Card with Orange Icon & Edit Button -->
                <div class="p-3.5 sm:p-4 rounded-2xl bg-white border border-[#EAE4DF] flex items-center justify-between text-left shadow-xs">
                    <div class="flex items-center space-x-3 min-w-0 pr-2">
                        <div class="w-10 h-10 rounded-xl bg-[#FFE9DC] text-[#FF6B2C] flex items-center justify-center text-lg shrink-0">
                            📋
                        </div>
                        <div class="min-w-0">
                            ${session.taskId ? `
                                <h4 class="text-xs font-bold text-[#202124] truncate">${escapeHTML(session.taskName)}</h4>
                                <p class="text-[11px] text-[#6F6B68] truncate">Next: ${escapeHTML(session.nextAction)}</p>
                            ` : `
                                <h4 class="text-xs font-bold text-[#202124] truncate">NO TASK</h4>
                                <p class="text-[11px] text-[#6F6B68] truncate">Just give yourself some focused time</p>
                            `}
                        </div>
                    </div>
                    <div class="flex items-center space-x-2 shrink-0">
                        <button type="button" onclick="window.TempoFocusZone.openQuickEntry()" class="text-xs font-bold text-[#FF6B2C] hover:underline px-2 py-1">
                            ${session.taskId ? 'Edit' : 'Choose a task'}
                        </button>
                        ${session.taskId ? `
                            <button type="button" onclick="window.TempoFocusZone.focusWithoutTask()" class="text-xs font-bold text-stone-500 hover:text-stone-800 px-2 py-1 border border-stone-200 rounded-lg hover:bg-stone-50 transition">
                                Focus without a task
                            </button>
                        ` : ''}
                    </div>
                </div>

                <!-- Focus Rhythm Selector (4 Horizontal Chips) -->
                <div class="space-y-2 text-left">
                    <label class="block text-xs font-bold text-[#202124]">Focus rhythm</label>
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                        <button type="button" onclick="window.TempoFocusZone.selectRhythm(45, 15)"
                                class="p-3 rounded-2xl border text-left transition relative ${is4515 ? 'border-2 border-[#FF6B2C] bg-[#FFF8F2] text-[#202124] shadow-xs' : 'border-stone-200 bg-white hover:border-stone-300 text-stone-700'}">
                            ${is4515 ? '<span class="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-[#FF6B2C]"></span>' : ''}
                            <div class="text-sm font-extrabold">45 / 15</div>
                            <div class="text-[10px] text-stone-500 font-medium mt-0.5">Recommended</div>
                        </button>
                        <button type="button" onclick="window.TempoFocusZone.selectRhythm(25, 5)"
                                class="p-3 rounded-2xl border text-left transition relative ${is255 ? 'border-2 border-[#FF6B2C] bg-[#FFF8F2] text-[#202124] shadow-xs' : 'border-stone-200 bg-white hover:border-stone-300 text-stone-700'}">
                            ${is255 ? '<span class="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-[#FF6B2C]"></span>' : ''}
                            <div class="text-sm font-extrabold">25 / 5</div>
                            <div class="text-[10px] text-stone-500 font-medium mt-0.5">Pomodoro</div>
                        </button>
                        <button type="button" onclick="window.TempoFocusZone.selectRhythm(50, 10)"
                                class="p-3 rounded-2xl border text-left transition relative ${is5010 ? 'border-2 border-[#FF6B2C] bg-[#FFF8F2] text-[#202124] shadow-xs' : 'border-stone-200 bg-white hover:border-stone-300 text-stone-700'}">
                            ${is5010 ? '<span class="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-[#FF6B2C]"></span>' : ''}
                            <div class="text-sm font-extrabold">50 / 10</div>
                            <div class="text-[10px] text-stone-500 font-medium mt-0.5">Deep work</div>
                        </button>
                        <button type="button" onclick="window.TempoFocusZone.selectRhythm(60, 15)"
                                class="p-3 rounded-2xl border text-left transition relative ${isCustom ? 'border-2 border-[#FF6B2C] bg-[#FFF8F2] text-[#202124] shadow-xs' : 'border-stone-200 bg-white hover:border-stone-300 text-stone-700'}">
                            ${isCustom ? '<span class="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-[#FF6B2C]"></span>' : ''}
                            <div class="text-sm font-extrabold">Custom</div>
                            <div class="text-[10px] text-stone-500 font-medium mt-0.5">Set your own</div>
                        </button>
                    </div>

                    ${isCustom ? `
                        <div class="p-3.5 bg-stone-50 border border-stone-200 rounded-2xl flex items-center gap-3 text-xs mt-2">
                            <div class="flex-1">
                                <label class="text-[10px] uppercase font-bold text-stone-500 block">Focus (mins):</label>
                                <input id="fz-custom-focus" type="number" min="1" max="180" 
                                       value="${Math.round(session.focusDurationSeconds / 60)}"
                                       class="w-full px-2.5 py-1.5 text-xs border border-stone-300 rounded-lg text-center font-bold bg-white focus:outline-none focus:ring-1 focus:ring-[#FF6B2C]">
                            </div>
                            <div class="flex-1">
                                <label class="text-[10px] uppercase font-bold text-stone-500 block">Break (mins):</label>
                                <input id="fz-custom-break" type="number" min="1" max="60" 
                                       value="${Math.round(session.breakDurationSeconds / 60)}"
                                       class="w-full px-2.5 py-1.5 text-xs border border-stone-300 rounded-lg text-center font-bold bg-white focus:outline-none focus:ring-1 focus:ring-[#FF6B2C]">
                            </div>
                            <button type="button" onclick="window.TempoFocusZone.setCustomRhythm()"
                                    class="btn-primary px-4 py-2 rounded-xl text-xs font-bold mt-3 shrink-0">
                                Apply
                            </button>
                        </div>
                    ` : ''}
                </div>

                <!-- Visual Atmosphere Selector (4 Swatches with Checkmark) -->
                <div class="space-y-2 text-left">
                    <label class="block text-xs font-bold text-[#202124]">Visual atmosphere</label>
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                        <!-- Warm Cream -->
                        <button type="button" onclick="window.TempoFocusZone.setBackground('cream')"
                                class="p-2.5 rounded-2xl border text-left transition ${session.background === 'cream' ? 'border-2 border-[#FF6B2C] bg-[#FFF8F2] shadow-xs' : 'border-stone-200 bg-white hover:border-stone-300'}">
                            <div class="fz-swatch fz-swatch-cream">
                                ${session.background === 'cream' ? '<span class="absolute top-1.5 right-1.5 w-4 h-4 rounded-full bg-[#FF6B2C] text-white text-[9px] flex items-center justify-center font-bold shadow-2xs">✓</span>' : ''}
                            </div>
                            <div class="text-xs font-bold text-[#202124]">Warm Cream</div>
                        </button>

                        <!-- Soft Sunset -->
                        <button type="button" onclick="window.TempoFocusZone.setBackground('sunset')"
                                class="p-2.5 rounded-2xl border text-left transition ${session.background === 'sunset' ? 'border-2 border-[#FF6B2C] bg-[#FFF8F2] shadow-xs' : 'border-stone-200 bg-white hover:border-stone-300'}">
                            <div class="fz-swatch fz-swatch-sunset">
                                ${session.background === 'sunset' ? '<span class="absolute top-1.5 right-1.5 w-4 h-4 rounded-full bg-[#FF6B2C] text-white text-[9px] flex items-center justify-center font-bold shadow-2xs">✓</span>' : ''}
                            </div>
                            <div class="text-xs font-bold text-[#202124]">Soft Sunset</div>
                        </button>

                        <!-- Quiet Sky -->
                        <button type="button" onclick="window.TempoFocusZone.setBackground('sky')"
                                class="p-2.5 rounded-2xl border text-left transition ${session.background === 'sky' ? 'border-2 border-[#FF6B2C] bg-[#FFF8F2] shadow-xs' : 'border-stone-200 bg-white hover:border-stone-300'}">
                            <div class="fz-swatch fz-swatch-sky">
                                ${session.background === 'sky' ? '<span class="absolute top-1.5 right-1.5 w-4 h-4 rounded-full bg-[#FF6B2C] text-white text-[9px] flex items-center justify-center font-bold shadow-2xs">✓</span>' : ''}
                            </div>
                            <div class="text-xs font-bold text-[#202124]">Quiet Sky</div>
                        </button>

                        <!-- Night Focus -->
                        <button type="button" onclick="window.TempoFocusZone.setBackground('night')"
                                class="p-2.5 rounded-2xl border text-left transition ${session.background === 'night' ? 'border-2 border-[#FF6B2C] bg-[#FFF8F2] shadow-xs' : 'border-stone-200 bg-white hover:border-stone-300'}">
                            <div class="fz-swatch fz-swatch-night">
                                ${session.background === 'night' ? '<span class="absolute top-1.5 right-1.5 w-4 h-4 rounded-full bg-[#FF6B2C] text-white text-[9px] flex items-center justify-center font-bold shadow-2xs">✓</span>' : ''}
                            </div>
                            <div class="text-xs font-bold text-[#202124]">Night Focus</div>
                        </button>
                    </div>
                </div>

                <!-- Background Sound & Volume Selector -->
                <div class="space-y-2 text-left">
                    <label class="block text-xs font-bold text-[#202124]">Background sound</label>
                    <div class="flex flex-wrap items-center gap-2">
                        <button type="button" onclick="window.TempoFocusZone.setSound('none')"
                                class="px-3.5 py-2 rounded-xl text-xs font-bold transition ${session.soundType === 'none' ? 'bg-[#202124] text-white shadow-xs' : 'bg-white border border-stone-200 text-stone-700 hover:bg-stone-50'}">
                            None
                        </button>
                        <button type="button" onclick="window.TempoFocusZone.setSound('rain')"
                                class="px-3.5 py-2 rounded-xl text-xs font-bold transition ${session.soundType === 'rain' ? 'bg-[#202124] text-white shadow-xs' : 'bg-white border border-stone-200 text-stone-700 hover:bg-stone-50'}">
                            🌧 Rain
                        </button>
                        <button type="button" onclick="window.TempoFocusZone.setSound('cafe')"
                                class="px-3.5 py-2 rounded-xl text-xs font-bold transition ${session.soundType === 'cafe' ? 'bg-[#202124] text-white shadow-xs' : 'bg-white border border-stone-200 text-stone-700 hover:bg-stone-50'}">
                            ☕ Café
                        </button>
                        <button type="button" onclick="window.TempoFocusZone.setSound('music')"
                                class="px-3.5 py-2 rounded-xl text-xs font-bold transition ${session.soundType === 'music' ? 'bg-[#202124] text-white shadow-xs' : 'bg-white border border-stone-200 text-stone-700 hover:bg-stone-50'}">
                            🎵 Soft Focus
                        </button>
                    </div>

                    ${session.soundType !== 'none' ? `
                        <div class="flex items-center space-x-3 pt-2">
                            <span class="text-[11px] font-semibold text-stone-500">Volume</span>
                            <input type="range" min="0" max="100" value="${Math.round(session.soundVolume * 100)}"
                                   oninput="window.TempoFocusZone.setVolume(this.value / 100, false)"
                                   onchange="window.TempoFocusZone.setVolume(this.value / 100, true)"
                                   class="flex-1 h-1.5 cursor-pointer">
                            <span class="text-[11px] font-mono font-bold text-stone-600">${Math.round(session.soundVolume * 100)}%</span>
                        </div>
                    ` : ''}
                </div>

                <!-- Start Focusing CTA -->
                <div class="pt-2">
                    <button type="button" onclick="window.TempoFocusZone.startFocusSession()"
                            class="btn-primary w-full py-4 rounded-2xl font-bold text-sm shadow-md transition flex items-center justify-center space-x-2">
                        <span>Start focusing (${Math.round(session.focusDurationSeconds / 60)} min)</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // VIEW 3: ACTIVE FOCUS COUNTDOWN SCREEN (Panel 2 in Mockup)
    // -------------------------------------------------------------------------
    function renderActiveFocus(style) {
        const mins = Math.floor(session.focusSecondsRemaining / 60);
        const secs = session.focusSecondsRemaining % 60;
        const timeDisplay = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

        const circumference = 691.15;
        const progress = session.focusDurationSeconds > 0 ? (session.focusSecondsRemaining / session.focusDurationSeconds) : 1;
        const progressOffset = circumference * (1 - progress);

        return `
            <div class="w-full max-w-xl mx-auto flex flex-col items-center justify-center space-y-5 text-center">
                <!-- Task Header -->
                <div class="space-y-1">
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold ${style.isDark ? 'text-white' : 'text-[#202124]'} tracking-tight">
                        ${session.taskId ? escapeHTML(session.taskName) : 'Independent Focus Session'}
                    </h2>
                </div>

                <!-- Next Action Pill with Immediate Done Checkmark -->
                ${session.taskId ? `
                    <div class="flex flex-col items-center gap-2">
                        <div class="inline-flex items-center gap-2.5 px-4 py-2 rounded-full ${style.pillClass} shadow-xs max-w-md mx-auto">
                            <span class="text-xs font-bold ${style.isDark ? 'text-stone-300' : 'text-stone-700'} truncate">
                                Next: ${escapeHTML(session.nextAction)}
                            </span>
                            ${session.subtasks.length > 0 ? `
                                <button type="button" onclick="window.TempoFocusZone.completeActiveSubtask()" 
                                        class="w-5 h-5 rounded-full bg-emerald-500 hover:bg-emerald-600 text-white flex items-center justify-center text-xs font-bold shrink-0 transition shadow-2xs"
                                        title="Mark step done">
                                    ✓
                                </button>
                            ` : ''}
                        </div>
                        <button type="button" onclick="window.TempoFocusZone.finishActiveTaskEarly()"
                                class="px-3.5 py-1 rounded-full text-xs font-bold border border-stone-200 hover:border-[#FF6B2C] bg-white/90 hover:bg-white text-stone-700 hover:text-[#FF6B2C] shadow-2xs transition">
                            Finish task
                        </button>
                    </div>
                ` : `
                    <div class="inline-flex items-center gap-2.5 px-4 py-2 rounded-full ${style.pillClass} shadow-xs max-w-md mx-auto">
                        <span class="text-xs font-medium ${style.isDark ? 'text-stone-300' : 'text-stone-600'}">
                            Just giving yourself some focused time
                        </span>
                    </div>
                `}

                <!-- Large Circular Progress Ring -->
                <div class="relative w-64 h-64 sm:w-72 sm:h-72 mx-auto my-2 flex items-center justify-center select-none">
                    <svg class="w-full h-full" viewBox="0 0 260 260">
                        <circle class="fz-timer-circle-bg" cx="130" cy="130" r="110" stroke-width="6"/>
                        <circle id="fz-timer-circle" class="fz-timer-circle-fg" cx="130" cy="130" r="110" stroke-width="7"
                                stroke-dasharray="691.15" stroke-dashoffset="${progressOffset}"/>
                    </svg>
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                        <div id="fz-clock-display" class="font-mono text-5xl sm:text-6xl font-black tracking-tight ${style.isDark ? 'text-white' : 'text-[#202124]'}">
                            ${timeDisplay}
                        </div>
                        <span class="text-[11px] font-extrabold uppercase tracking-widest ${style.isDark ? 'text-stone-400' : 'text-stone-500'} mt-2">
                            FOCUS TIME
                        </span>
                    </div>
                </div>

                <!-- Pause Button -->
                <div>
                    <button type="button" onclick="window.TempoFocusZone.pauseFocusTimer()"
                            class="px-8 py-2.5 rounded-full bg-white hover:bg-stone-50 text-[#202124] font-bold text-xs sm:text-sm shadow-md border border-stone-200/80 transition flex items-center space-x-2">
                        <span>⏸</span>
                        <span>Pause</span>
                    </button>
                </div>

                <!-- Floating Translucent Control Bar -->
                <div class="fz-control-bar inline-flex items-center gap-3 px-4 py-2 rounded-2xl shadow-lg text-xs font-medium mt-4">
                    <!-- Sound Selector -->
                    <div class="flex items-center space-x-1.5">
                        <select onchange="window.TempoFocusZone.setSound(this.value)"
                                class="text-xs font-bold bg-transparent border-0 focus:outline-none cursor-pointer ${style.isDark ? 'text-white' : 'text-stone-800'}">
                            <option value="none" ${session.soundType === 'none' ? 'selected' : ''} class="text-stone-900">🔇 Sound Off</option>
                            <option value="rain" ${session.soundType === 'rain' ? 'selected' : ''} class="text-stone-900">🌧️ Gentle Rain</option>
                            <option value="cafe" ${session.soundType === 'cafe' ? 'selected' : ''} class="text-stone-900">☕ Café Ambience</option>
                            <option value="music" ${session.soundType === 'music' ? 'selected' : ''} class="text-stone-900">🎵 Soft Focus Tone</option>
                        </select>
                    </div>

                    <!-- Volume Slider -->
                    <div class="flex items-center space-x-2 border-l ${style.isDark ? 'border-white/20' : 'border-stone-300/70'} pl-3">
                        <span class="text-[10px] font-semibold uppercase tracking-wider ${style.isDark ? 'text-stone-400' : 'text-stone-500'}">Vol</span>
                        <input type="range" min="0" max="100" value="${Math.round(session.soundVolume * 100)}"
                               oninput="window.TempoFocusZone.setVolume(this.value / 100, false)"
                               onchange="window.TempoFocusZone.setVolume(this.value / 100, true)"
                               class="w-16 h-1 cursor-pointer">
                    </div>

                    <!-- Atmosphere Switcher -->
                    <div class="flex items-center space-x-1.5 border-l ${style.isDark ? 'border-white/20' : 'border-stone-300/70'} pl-3">
                        <select onchange="window.TempoFocusZone.setBackground(this.value)"
                                class="text-xs font-bold bg-transparent border-0 focus:outline-none cursor-pointer ${style.isDark ? 'text-white' : 'text-stone-800'}">
                            <option value="cream" ${session.background === 'cream' ? 'selected' : ''} class="text-stone-900">☀️ Cream</option>
                            <option value="sunset" ${session.background === 'sunset' ? 'selected' : ''} class="text-stone-900">🌅 Sunset</option>
                            <option value="sky" ${session.background === 'sky' ? 'selected' : ''} class="text-stone-900">🌤️ Sky</option>
                            <option value="night" ${session.background === 'night' ? 'selected' : ''} class="text-stone-900">🌙 Night</option>
                        </select>
                    </div>
                </div>

                <!-- Bottom Card: Need a moment? Quick Stress Relief + Finish session -->
                <div class="w-full max-w-md mx-auto px-4 py-2.5 rounded-2xl ${style.isDark ? 'bg-slate-800/80 border border-slate-700/60' : 'bg-white/80 border border-white/70'} backdrop-blur-md shadow-xs flex items-center justify-between text-xs mt-2">
                    <div class="flex items-center space-x-2">
                        <span class="${style.isDark ? 'text-stone-300' : 'text-stone-700'}">🌿 Need a moment?</span>
                        <button type="button" onclick="window.TempoStressRelief.openModal()"
                                class="px-2.5 py-1 rounded-xl bg-white hover:bg-stone-50 border border-stone-200 text-[#FF6B2C] font-bold shadow-2xs transition">
                            Quick Stress Relief
                        </button>
                    </div>
                    <button type="button" onclick="window.TempoFocusZone.confirmFinishEarly()"
                            class="text-xs ${style.isDark ? 'text-stone-400 hover:text-stone-200' : 'text-stone-500 hover:text-stone-800'} underline">
                        Finish session
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // VIEW 4: PAUSED SCREEN (Panel 3 in Mockup)
    // -------------------------------------------------------------------------
    function renderFocusPaused(style) {
        const mins = Math.floor(session.focusSecondsRemaining / 60);
        const secs = session.focusSecondsRemaining % 60;
        const timeDisplay = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

        return `
            <div class="w-full max-w-md mx-auto flex flex-col items-center justify-center space-y-6 text-center">
                <!-- Circular Ring with Pause Icon -->
                <div class="relative w-56 h-56 sm:w-60 sm:h-60 mx-auto flex items-center justify-center select-none">
                    <svg class="w-full h-full" viewBox="0 0 240 240">
                        <circle class="fz-timer-circle-bg" cx="120" cy="120" r="100" stroke-width="5"/>
                    </svg>
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                        <div class="w-14 h-14 rounded-full ${style.isDark ? 'bg-slate-800 text-stone-200' : 'bg-white text-stone-700'} flex items-center justify-center text-xl font-black shadow-sm mb-2">
                            ⏸
                        </div>
                        <h3 class="font-heading text-xl font-bold ${style.isDark ? 'text-white' : 'text-[#202124]'}">
                            Focus paused
                        </h3>
                        <p class="text-xs ${style.isDark ? 'text-stone-400' : 'text-stone-500'} mt-0.5">
                            Your timer is saved.
                        </p>
                        <div class="font-mono text-2xl font-bold ${style.isDark ? 'text-stone-300' : 'text-stone-700'} mt-1">
                            ${timeDisplay}
                        </div>
                    </div>
                </div>

                <!-- Action Buttons: Resume & Finish -->
                <div class="flex flex-col sm:flex-row items-center gap-3 w-full max-w-xs">
                    <button type="button" onclick="window.TempoFocusZone.resumeFocusTimer()"
                            class="btn-primary w-full py-3 rounded-2xl font-bold text-sm shadow-md transition flex items-center justify-center space-x-1.5">
                        <span>▶</span>
                        <span>Resume</span>
                    </button>
                    ${session.taskId ? `
                        <button type="button" onclick="window.TempoFocusZone.finishActiveTaskEarly()"
                                class="w-full py-3 rounded-2xl bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 text-emerald-900 font-bold text-sm shadow-sm transition">
                            Finish task
                        </button>
                    ` : ''}
                    <button type="button" onclick="window.TempoFocusZone.confirmFinishEarly()"
                            class="w-full py-3 rounded-2xl ${style.isDark ? 'bg-slate-800 hover:bg-slate-700 text-white' : 'bg-stone-800 hover:bg-stone-900 text-white'} font-bold text-sm shadow-sm transition">
                        Finish session
                    </button>
                </div>

                <!-- Floating Translucent Control Bar -->
                <div class="fz-control-bar inline-flex items-center gap-3 px-4 py-2 rounded-2xl shadow-lg text-xs font-medium">
                    <!-- Sound Selector -->
                    <div class="flex items-center space-x-1.5">
                        <select onchange="window.TempoFocusZone.setSound(this.value)"
                                class="text-xs font-bold bg-transparent border-0 focus:outline-none cursor-pointer ${style.isDark ? 'text-white' : 'text-stone-800'}">
                            <option value="none" ${session.soundType === 'none' ? 'selected' : ''} class="text-stone-900">🔇 Sound Off</option>
                            <option value="rain" ${session.soundType === 'rain' ? 'selected' : ''} class="text-stone-900">🌧️ Gentle Rain</option>
                            <option value="cafe" ${session.soundType === 'cafe' ? 'selected' : ''} class="text-stone-900">☕ Café Ambience</option>
                            <option value="music" ${session.soundType === 'music' ? 'selected' : ''} class="text-stone-900">🎵 Soft Focus Tone</option>
                        </select>
                    </div>

                    <!-- Volume Slider -->
                    <div class="flex items-center space-x-2 border-l ${style.isDark ? 'border-white/20' : 'border-stone-300/70'} pl-3">
                        <span class="text-[10px] font-semibold uppercase tracking-wider ${style.isDark ? 'text-stone-400' : 'text-stone-500'}">Vol</span>
                        <input type="range" min="0" max="100" value="${Math.round(session.soundVolume * 100)}"
                               oninput="window.TempoFocusZone.setVolume(this.value / 100, false)"
                               onchange="window.TempoFocusZone.setVolume(this.value / 100, true)"
                               class="w-16 h-1 cursor-pointer">
                    </div>

                    <!-- Atmosphere Switcher -->
                    <div class="flex items-center space-x-1.5 border-l ${style.isDark ? 'border-white/20' : 'border-stone-300/70'} pl-3">
                        <select onchange="window.TempoFocusZone.setBackground(this.value)"
                                class="text-xs font-bold bg-transparent border-0 focus:outline-none cursor-pointer ${style.isDark ? 'text-white' : 'text-stone-800'}">
                            <option value="cream" ${session.background === 'cream' ? 'selected' : ''} class="text-stone-900">☀️ Cream</option>
                            <option value="sunset" ${session.background === 'sunset' ? 'selected' : ''} class="text-stone-900">🌅 Sunset</option>
                            <option value="sky" ${session.background === 'sky' ? 'selected' : ''} class="text-stone-900">🌤️ Sky</option>
                            <option value="night" ${session.background === 'night' ? 'selected' : ''} class="text-stone-900">🌙 Night</option>
                        </select>
                    </div>
                </div>

                <!-- Bottom Card: Need a moment? Quick Stress Relief -->
                <div class="w-full max-w-xs mx-auto px-4 py-2.5 rounded-2xl ${style.isDark ? 'bg-slate-800/80 border border-slate-700/60' : 'bg-white/80 border border-white/70'} backdrop-blur-md shadow-xs flex items-center justify-between text-xs">
                    <span class="${style.isDark ? 'text-stone-300' : 'text-stone-700'}">🌿 Need a moment?</span>
                    <button type="button" onclick="window.TempoStressRelief.openModal()"
                            class="px-2.5 py-1 rounded-xl bg-white hover:bg-stone-50 border border-stone-200 text-[#FF6B2C] font-bold shadow-2xs transition">
                        Quick Stress Relief
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // VIEW 5: FINISH EARLY CONFIRMATION
    // -------------------------------------------------------------------------
    function renderFinishConfirm(style) {
        if (!session.taskId) {
            // No-task session: simply confirm ending
            return `
                <div class="tempo-card w-full max-w-sm p-6 sm:p-8 text-center space-y-5 rounded-3xl ${style.cardClass}">
                    <h3 class="font-heading text-xl font-bold text-[#202124]">End this focus session?</h3>
                    <p class="text-xs text-[#6F6B68]">You focused for ~${Math.max(1, Math.round(session.focusElapsedSeconds / 60))} minutes.</p>
                    <div class="space-y-2 pt-2">
                        <button type="button" onclick="window.TempoFocusZone.handleFinishChoice('stop_here')"
                                class="btn-primary w-full py-3 rounded-2xl font-bold text-xs shadow-sm">
                            End session
                        </button>
                        <button type="button" onclick="window.TempoFocusZone.handleFinishChoice('keep_focusing')"
                                class="w-full py-2.5 rounded-2xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50">
                            Keep focusing
                        </button>
                    </div>
                </div>
            `;
        }

        return `
            <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">FINISH SESSION</span>
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Did you finish the task?</h3>
                    <p class="text-xs text-[#6F6B68] max-w-xs mx-auto">
                        <strong>${escapeHTML(session.taskName)}</strong>
                    </p>
                </div>

                <div class="space-y-2.5 pt-2">
                    <button type="button" onclick="window.TempoFocusZone.handleFinishChoice('mark_done')"
                            class="w-full p-3.5 rounded-2xl bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 text-emerald-900 font-bold text-xs transition text-left flex items-center justify-between group">
                        <div>
                            <span>✓ Yes, mark task as done</span>
                            <p class="text-[11px] font-normal text-emerald-700">All planned work for this task is complete.</p>
                        </div>
                        <span class="group-hover:translate-x-1 transition-transform">→</span>
                    </button>

                    <button type="button" onclick="window.TempoFocusZone.handleFinishChoice('stop_here')"
                            class="w-full p-3.5 rounded-2xl bg-stone-50 hover:bg-stone-100 border border-stone-200 text-stone-800 font-semibold text-xs transition text-left flex items-center justify-between group">
                        <div>
                            <span>No, I'm stopping here</span>
                            <p class="text-[11px] font-normal text-stone-500">Keep task in progress. I will return to it later.</p>
                        </div>
                        <span class="group-hover:translate-x-1 transition-transform">→</span>
                    </button>

                    <button type="button" onclick="window.TempoFocusZone.handleFinishChoice('keep_focusing')"
                            class="w-full py-2.5 text-xs text-[#6F6B68] hover:text-[#202124] underline">
                        Keep focusing
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // VIEW 6: ALL SUBTASKS COMPLETED CHECKPOINT
    // -------------------------------------------------------------------------
    function renderSubtasksAllDone(style) {
        return `
            <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                <div class="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto text-xl font-bold">
                    ✓
                </div>
                <div class="space-y-1">
                    <h3 class="font-heading text-xl font-bold text-[#202124]">All action steps are done!</h3>
                    <p class="text-xs text-[#6F6B68]">Is the whole task finished?</p>
                </div>

                <div class="pt-2 flex flex-col gap-2.5">
                    <button type="button" onclick="window.TempoFocusZone.handleSubtasksAllDoneChoice(true)"
                            class="btn-primary w-full py-3.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm transition">
                        Yes, mark task done →
                    </button>
                    <button type="button" onclick="window.TempoFocusZone.handleSubtasksAllDoneChoice(false)"
                            class="w-full py-2.5 rounded-2xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                        Not yet, keep working
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // VIEW 7: FOCUS BLOCK COMPLETE (00:00)
    // -------------------------------------------------------------------------
    function renderBlockComplete(style) {
        const plannedMin = Math.round(session.focusDurationSeconds / 60);

        if (!session.taskId) {
            return `
                <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-6 rounded-3xl ${style.cardClass} text-center">
                    <div class="w-14 h-14 rounded-2xl bg-[#FFE9DC] text-[#FF6B2C] flex items-center justify-center mx-auto text-2xl font-bold">
                        🎉
                    </div>
                    <div class="space-y-1">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">BLOCK COMPLETE</span>
                        <h3 class="font-heading text-2xl font-bold text-[#202124]">You focused for ${plannedMin} minutes!</h3>
                        <p class="text-xs text-[#6F6B68]">Step away and take your contained recovery break.</p>
                    </div>

                    <div class="pt-2 flex flex-col gap-2.5">
                        <button type="button" onclick="window.TempoFocusZone.startBreakPeriod()"
                                class="btn-primary w-full py-3.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm transition">
                            Take a ${Math.round(session.breakDurationSeconds / 60)} min break →
                        </button>
                        <button type="button" onclick="window.TempoFocusZone.close()"
                                class="w-full py-2.5 rounded-2xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                            Finish session for now
                        </button>
                    </div>
                </div>
            `;
        }

        return `
            <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                <div class="w-14 h-14 rounded-2xl bg-[#FFE9DC] text-[#FF6B2C] flex items-center justify-center mx-auto text-2xl font-bold">
                    🎯
                </div>
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">FOCUS BLOCK COMPLETE</span>
                    <h3 class="font-heading text-2xl font-bold text-[#202124]">You focused for ${plannedMin} minutes.</h3>
                    <p class="text-xs text-[#6F6B68]">How is "${escapeHTML(session.taskName)}" going?</p>
                </div>

                <div class="space-y-2 pt-2 text-left">
                    <button type="button" onclick="window.TempoFocusZone.handleFinishChoice('mark_done')"
                            class="w-full p-3.5 rounded-2xl bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 text-emerald-900 font-bold text-xs transition flex items-center justify-between group">
                        <div>
                            <span>✓ I finished the task</span>
                            <p class="text-[11px] font-normal text-emerald-700">Completed all work. Mark done in plan.</p>
                        </div>
                        <span class="group-hover:translate-x-1 transition-transform">→</span>
                    </button>

                    <button type="button" onclick="window.TempoFocusZone.startBreakPeriod()"
                            class="btn-primary w-full p-3.5 rounded-2xl text-xs font-bold transition flex items-center justify-between group shadow-sm">
                        <div>
                            <span>I'm still working on it</span>
                            <p class="text-[11px] font-normal text-white/80">Take a ${Math.round(session.breakDurationSeconds / 60)}m recovery break before the next block.</p>
                        </div>
                        <span class="group-hover:translate-x-1 transition-transform">Break →</span>
                    </button>

                    <button type="button" onclick="window.TempoFocusZone.close()"
                            class="w-full p-3 rounded-2xl border border-stone-200 hover:bg-stone-50 text-stone-700 font-semibold text-xs text-center transition">
                        I'm stopping for now
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // VIEW 8: BREAK HUB (Panel 4 in Mockup)
    // -------------------------------------------------------------------------
    function renderBreakHub(style) {
        const mins = Math.floor(session.breakSecondsRemaining / 60);
        const secs = session.breakSecondsRemaining % 60;
        const timeDisplay = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

        const circumference = 439.82;
        const progress = session.breakDurationSeconds > 0 ? (session.breakSecondsRemaining / session.breakDurationSeconds) : 1;
        const breakOffset = circumference * (1 - progress);

        return `
            <div class="tempo-card relative w-full max-w-xl p-6 sm:p-8 space-y-6 rounded-3xl ${style.cardClass} text-center">
                ${session.isStandaloneBreak ? `
                    <button type="button" onclick="window.TempoFocusZone.close()"
                            class="absolute top-4 right-4 text-stone-400 hover:text-stone-700 p-2 rounded-full hover:bg-stone-100 transition"
                            title="Close break">
                        ✕
                    </button>
                ` : ''}

                <!-- Title & Intro -->
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-emerald-700 block">${session.isStandaloneBreak ? 'TEMPO BREAK' : 'RECOVERY BREAK'}</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124]">${session.isStandaloneBreak ? 'Take a Break' : 'Break'}</h2>
                    <p class="text-xs text-[#6F6B68] max-w-sm mx-auto">
                        ${session.isStandaloneBreak ? 'Take a few minutes to rest, stretch, or breathe.' : 'Nice. One focus block done. Take a few minutes away from the task.'}
                    </p>
                </div>

                <!-- Circular Timer Ring for Break -->
                <div class="relative w-44 h-44 sm:w-48 sm:h-48 mx-auto flex items-center justify-center select-none">
                    <svg class="w-full h-full" viewBox="0 0 180 180">
                        <circle class="fz-timer-circle-bg" cx="90" cy="90" r="70" stroke-width="5"/>
                        <circle id="fz-break-circle" class="fz-break-circle-fg" cx="90" cy="90" r="70" stroke-width="6"
                                stroke-dasharray="439.82" stroke-dashoffset="${breakOffset}"/>
                    </svg>
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                        <div id="fz-break-clock" class="font-mono text-3xl sm:text-4xl font-extrabold text-emerald-700">
                            ${timeDisplay}
                        </div>
                        <span class="text-[10px] font-extrabold uppercase tracking-widest text-stone-400 mt-1">
                            BREAK LEFT
                        </span>
                    </div>
                </div>

                <!-- What feels good right now? (4 Cards in a Row / 2x2 Grid) -->
                <div class="w-full space-y-3 text-left">
                    <h4 class="text-xs font-bold text-center text-stone-600 uppercase tracking-wider">
                        What feels good right now?
                    </h4>
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                        <!-- Card 1: Gentle Match -->
                        <button type="button" onclick="window.TempoFocusZone.selectBreakActivity('game')"
                                class="p-3.5 rounded-2xl border border-stone-200 hover:border-[#FF6B2C] bg-white hover:bg-[#FFF9F4] transition text-left space-y-1 shadow-2xs group">
                            <div class="text-2xl">🎮</div>
                            <div>
                                <div class="text-xs font-bold text-[#202124] group-hover:text-[#FF6B2C]">Play something</div>
                                <div class="text-[11px] font-semibold text-stone-500">Gentle Match</div>
                            </div>
                            <p class="text-[10px] text-[#6F6B68] leading-tight">Low-pressure memory puzzle.</p>
                        </button>

                        <!-- Card 2: Quick Stress Relief -->
                        <button type="button" onclick="window.TempoFocusZone.selectBreakActivity('stress')"
                                class="p-3.5 rounded-2xl border border-stone-200 hover:border-[#FF6B2C] bg-white hover:bg-[#FFF9F4] transition text-left space-y-1 shadow-2xs group">
                            <div class="text-2xl">🌿</div>
                            <div>
                                <div class="text-xs font-bold text-[#202124] group-hover:text-[#FF6B2C]">Reset my head</div>
                                <div class="text-[11px] font-semibold text-stone-500">Quick Stress Relief</div>
                            </div>
                            <p class="text-[10px] text-[#6F6B68] leading-tight">Calming micro-actions.</p>
                        </button>

                        <!-- Card 3: Move a little -->
                        <button type="button" onclick="window.TempoFocusZone.selectBreakActivity('move')"
                                class="p-3.5 rounded-2xl border border-stone-200 hover:border-[#FF6B2C] bg-white hover:bg-[#FFF9F4] transition text-left space-y-1 shadow-2xs group">
                            <div class="text-2xl">🚶</div>
                            <div>
                                <div class="text-xs font-bold text-[#202124] group-hover:text-[#FF6B2C]">Move a little</div>
                                <div class="text-[11px] font-semibold text-stone-500">Short activities</div>
                            </div>
                            <p class="text-[10px] text-[#6F6B68] leading-tight">Simple stretches or 3m walk.</p>
                        </button>

                        <!-- Card 4: Just take a break -->
                        <button type="button" onclick="window.TempoFocusZone.selectBreakActivity('just')"
                                class="p-3.5 rounded-2xl border border-stone-200 hover:border-[#FF6B2C] bg-white hover:bg-[#FFF9F4] transition text-left space-y-1 shadow-2xs group">
                            <div class="text-2xl">☕</div>
                            <div>
                                <div class="text-xs font-bold text-[#202124] group-hover:text-[#FF6B2C]">Just take a break</div>
                                <div class="text-[11px] font-semibold text-stone-500">No activity needed</div>
                            </div>
                            <p class="text-[10px] text-[#6F6B68] leading-tight">Zero requirements. Rest screen.</p>
                        </button>
                    </div>
                </div>

                <!-- Ready to Focus CTA -->
                <div class="pt-2">
                    ${session.isStandaloneBreak ? `
                        <button type="button" onclick="window.TempoFocusZone.close()"
                                class="btn-primary px-8 py-3.5 rounded-2xl font-bold text-xs sm:text-sm shadow-md transition">
                            Finish break & return →
                        </button>
                    ` : `
                        <button type="button" onclick="window.TempoFocusZone.endBreakEarly()"
                                class="btn-primary px-8 py-3.5 rounded-2xl font-bold text-xs sm:text-sm shadow-md transition">
                            I'm ready to focus →
                        </button>
                    `}
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // VIEW 9: GENTLE MATCH MINI-GAME (Panel 5 in Mockup)
    // -------------------------------------------------------------------------
    function renderGentleMatch(style) {
        const game = session.gameState;
        if (!game) return '';

        const mins = Math.floor(session.breakSecondsRemaining / 60);
        const secs = session.breakSecondsRemaining % 60;
        const timeDisplay = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

        return `
            <div class="tempo-card w-full max-w-lg p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                <!-- Header with Running Break Time Badge -->
                <div class="flex items-center justify-between pb-3 border-b border-stone-200/80">
                    <button type="button" onclick="window.TempoFocusZone.returnToBreakHub()"
                            class="text-xs font-semibold text-stone-600 hover:text-stone-900 flex items-center space-x-1.5 transition">
                        <span>←</span>
                        <span>Back to break options</span>
                    </button>
                    <span id="fz-break-badge" class="text-xs font-mono font-bold text-emerald-800 bg-emerald-100/80 border border-emerald-200 px-3 py-1 rounded-full">
                        Break: ${timeDisplay}
                    </span>
                </div>

                <div class="space-y-0.5 pt-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Gentle Match</h3>
                    <p class="text-xs text-[#6F6B68]">Find all matching pairs at your own pace. A calm game for a calmer you.</p>
                </div>

                <!-- 4x3 Matching Grid (Zero performance pressure, no scores/XP) -->
                <div class="grid grid-cols-4 gap-2.5 sm:gap-3 max-w-xs sm:max-w-sm mx-auto py-2">
                    ${game.cards.map((card, idx) => `
                        <button type="button" 
                                onclick="window.TempoFocusZone.handleCardClick(${idx})"
                                class="w-16 h-16 sm:w-18 sm:h-18 rounded-2xl flex items-center justify-center text-2xl font-bold transition-all duration-200 select-none ${
                                    card.isMatched 
                                        ? 'bg-emerald-50 text-emerald-700 border-2 border-emerald-300 opacity-70 cursor-default'
                                        : (card.isFlipped 
                                            ? 'bg-[#FFE9DC] text-[#FF6B2C] border-2 border-[#FF6B2C] shadow-xs'
                                            : 'bg-white hover:bg-stone-50 border-2 border-stone-200 text-stone-300 hover:border-stone-300 cursor-pointer shadow-2xs')
                                }">
                            ${card.isFlipped || card.isMatched ? card.symbol : '•'}
                        </button>
                    `).join('')}
                </div>

                <!-- Completion Status -->
                ${game.isCompleted ? `
                    <div class="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl space-y-2">
                        <span class="text-xs font-bold text-emerald-900 block">✨ All pairs matched. Take a slow breath.</span>
                        <div class="flex items-center justify-center gap-2">
                            <button type="button" onclick="window.TempoFocusZone.returnToBreakHub()"
                                    class="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-bold transition shadow-xs">
                                Back to break
                            </button>
                            ${session.breakSecondsRemaining > 0 ? `
                                <button type="button" onclick="window.TempoFocusZone.initGentleMatch(); window.TempoFocusZone.render();"
                                        class="px-3.5 py-2 rounded-xl border border-emerald-300 bg-white text-emerald-900 text-xs font-semibold hover:bg-emerald-50 transition">
                                    Another round
                                </button>
                            ` : ''}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // VIEW 10: MOVE A LITTLE GUIDE
    // -------------------------------------------------------------------------
    function renderMoveALittle(style) {
        const mins = Math.floor(session.breakSecondsRemaining / 60);
        const secs = session.breakSecondsRemaining % 60;
        const timeDisplay = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

        return `
            <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                    <button type="button" onclick="window.TempoFocusZone.returnToBreakHub()"
                            class="text-xs font-semibold text-stone-500 hover:text-stone-800 flex items-center space-x-1">
                        <span>←</span>
                        <span>Back to break options</span>
                    </button>
                    <span id="fz-break-badge" class="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full">
                        Break: ${timeDisplay}
                    </span>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl font-bold text-[#202124]">Move a little</h3>
                    <p class="text-xs text-[#6F6B68]">Gentle micro-movements to release physical tension.</p>
                </div>

                <div class="space-y-2 text-left pt-2">
                    <div class="p-3.5 bg-stone-50 border border-stone-200 rounded-xl space-y-1">
                        <div class="flex items-center justify-between text-xs font-bold text-stone-800">
                            <span>🚶 Walk around</span>
                            <span class="text-stone-400 font-normal">~3 mins</span>
                        </div>
                        <p class="text-[11px] text-stone-600">Step away from your desk. Walk through the room or corridor to circulate blood flow.</p>
                    </div>

                    <div class="p-3.5 bg-stone-50 border border-stone-200 rounded-xl space-y-1">
                        <div class="flex items-center justify-between text-xs font-bold text-stone-800">
                            <span>🧘 Shoulder & neck stretch</span>
                            <span class="text-stone-400 font-normal">~2 mins</span>
                        </div>
                        <p class="text-[11px] text-stone-600">Roll your shoulders backward 5 times. Gently tilt your ear toward your shoulder for 15 seconds.</p>
                    </div>

                    <div class="p-3.5 bg-stone-50 border border-stone-200 rounded-xl space-y-1">
                        <div class="flex items-center justify-between text-xs font-bold text-stone-800">
                            <span>👀 Look at distant horizon</span>
                            <span class="text-stone-400 font-normal">~1 min</span>
                        </div>
                        <p class="text-[11px] text-stone-600">Look out of a window at an object 20 feet away to relax your optic nerves.</p>
                    </div>

                    <div class="p-3.5 bg-stone-50 border border-stone-200 rounded-xl space-y-1">
                        <div class="flex items-center justify-between text-xs font-bold text-stone-800">
                            <span>💧 Drink some water</span>
                            <span class="text-stone-400 font-normal">~1 min</span>
                        </div>
                        <p class="text-[11px] text-stone-600">Hydrate your brain and take 3 deep belly breaths before returning.</p>
                    </div>
                </div>

                <div class="pt-2">
                    <button type="button" onclick="window.TempoFocusZone.returnToBreakHub()"
                            class="w-full py-2.5 rounded-xl border border-stone-300 text-xs font-semibold text-stone-700 hover:bg-stone-50 transition">
                        Done with movement
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // VIEW 11: JUST TAKE A BREAK (Zero-performance rest)
    // -------------------------------------------------------------------------
    function renderJustTakeABreak(style) {
        const mins = Math.floor(session.breakSecondsRemaining / 60);
        const secs = session.breakSecondsRemaining % 60;
        const timeDisplay = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

        return `
            <div class="tempo-card w-full max-w-md p-8 sm:p-10 space-y-6 rounded-3xl ${style.cardClass} text-center">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-emerald-700">REST & RESTORE</span>
                    <h3 class="font-heading text-2xl font-bold text-[#202124]">Just resting.</h3>
                    <p class="text-xs text-[#6F6B68] max-w-xs mx-auto leading-relaxed">
                        No tasks. No tracking. Close your eyes, lean back, or let your mind wander freely.
                    </p>
                </div>

                <div class="py-4">
                    <div class="font-mono text-5xl font-extrabold text-emerald-700">
                        ${timeDisplay}
                    </div>
                    <span class="text-[11px] text-stone-400 block mt-1">Remaining restful break</span>
                </div>

                <div class="pt-2 flex flex-col gap-2.5">
                    ${session.isStandaloneBreak ? `
                        <button type="button" onclick="window.TempoFocusZone.close()"
                                class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs shadow-xs transition">
                            Finish break & return →
                        </button>
                    ` : `
                        <button type="button" onclick="window.TempoFocusZone.endBreakEarly()"
                                class="px-5 py-2.5 rounded-xl border border-stone-300 hover:bg-stone-50 text-xs font-bold text-stone-800 transition">
                            I'm ready to focus →
                        </button>
                    `}
                    <button type="button" onclick="window.TempoFocusZone.returnToBreakHub()"
                            class="text-xs text-stone-500 hover:text-stone-800 underline">
                        Back to break options
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // VIEW 12: BREAK ENDED (Context-Aware Extension)
    // -------------------------------------------------------------------------
    function renderBreakEnded(style) {
        const isRoundGame = session.breakActivityType === 'round_game';

        if (session.isStandaloneBreak) {
            return `
                <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                    <div class="w-14 h-14 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-700 flex items-center justify-center mx-auto text-2xl shadow-xs">
                        🌿
                    </div>
                    <div class="space-y-1">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-emerald-700 block">BREAK COMPLETE</span>
                        <h3 class="font-heading text-2xl font-bold text-[#202124]">
                            Break time is up 🌿
                        </h3>
                        <p class="text-xs text-[#6F6B68]">
                            Take this refreshed momentum back into your day.
                        </p>
                    </div>

                    <div class="space-y-2.5 pt-2">
                        <button type="button" onclick="window.TempoFocusZone.close()"
                                class="btn-primary w-full py-3.5 rounded-2xl font-bold text-sm shadow-md transition flex items-center justify-center space-x-1.5">
                            <span>✓</span>
                            <span>Finish break & return</span>
                        </button>

                        ${!session.hasUsedBreakExtension && !isRoundGame ? `
                            <button type="button" onclick="window.TempoFocusZone.extendBreak5Minutes()"
                                    class="w-full p-3.5 rounded-2xl bg-[#FFF8F2] border border-[#FFD2BA] hover:bg-[#FFE9DC] text-[#B83D08] text-xs font-semibold transition flex items-center justify-between shadow-2xs group">
                                <span>I need 5 more minutes</span>
                                <span class="text-[#FF6B2C] group-hover:translate-x-1 transition-transform">→</span>
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        return `
            <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                <div class="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 text-amber-700 flex items-center justify-center mx-auto text-2xl shadow-xs">
                    🌅
                </div>
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C] block">BREAK OVER</span>
                    <h3 class="font-heading text-2xl font-bold text-[#202124]">
                        ${session.hasUsedBreakExtension ? 'Your extra 5 minutes are up.' : 'Break time is up 🌿'}
                    </h3>
                    <p class="text-xs text-[#6F6B68]">
                        ${session.hasUsedBreakExtension ? 'Ready to return to your work?' : 'Ready to get back?'}
                    </p>
                </div>

                <div class="space-y-2.5 pt-2">
                    <!-- Primary CTA -->
                    <button type="button" onclick="window.TempoFocusZone.endBreakEarly()"
                            class="btn-primary w-full py-3.5 rounded-2xl font-bold text-sm shadow-md transition flex items-center justify-center space-x-1.5">
                        <span>▶</span>
                        <span>Return to Focus</span>
                    </button>

                    ${!session.hasUsedBreakExtension && isRoundGame ? `
                        <button type="button" onclick="window.TempoFocusZone.startRoundGrace()"
                                class="w-full p-3.5 rounded-2xl bg-white border border-stone-200 hover:border-stone-300 text-stone-700 text-xs font-semibold transition flex items-center justify-between shadow-2xs group">
                            <span>Let me finish this round</span>
                            <span class="text-stone-400 group-hover:translate-x-1 transition-transform">→</span>
                        </button>
                    ` : ''}

                    ${!session.hasUsedBreakExtension && !isRoundGame ? `
                        <button type="button" onclick="window.TempoFocusZone.extendBreak5Minutes()"
                                class="w-full p-3.5 rounded-2xl bg-[#FFF8F2] border border-[#FFD2BA] hover:bg-[#FFE9DC] text-[#B83D08] text-xs font-semibold transition flex items-center justify-between shadow-2xs group">
                            <span>I need 5 more minutes</span>
                            <span class="text-[#FF6B2C] group-hover:translate-x-1 transition-transform">→</span>
                        </button>
                    ` : ''}

                    <button type="button" onclick="window.TempoFocusZone.finishFocusEarly()"
                            class="w-full py-2 text-xs text-stone-500 hover:text-stone-800 underline">
                        Finish focus for now
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // VIEW 13: POST-BREAK CHECKPOINT (Sections 23, 33, 34, 35)
    // -------------------------------------------------------------------------
    function renderReturnTransition(style) {
        if (session.isStandaloneBreak) {
            return `
                <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                    <div class="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto text-xl font-bold">
                        🌿
                    </div>
                    <div class="space-y-1">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-emerald-700 block">RECHARGED</span>
                        <h3 class="font-heading text-2xl font-bold text-[#202124]">Break complete 🌿</h3>
                        <p class="text-xs text-[#6F6B68]">Take this refreshed momentum back into your day.</p>
                    </div>
                    <div class="pt-2">
                        <button type="button" onclick="window.TempoFocusZone.close()"
                                class="btn-primary w-full py-3.5 rounded-2xl font-bold text-xs sm:text-sm shadow-md transition">
                            Finish break & return →
                        </button>
                    </div>
                </div>
            `;
        }
        const ctx = getPlanContext();
        const isTodayComplete = session.isPostDayBreak || ctx.todayUnfinished.length === 0;

        if (isTodayComplete) {
            const tomorrowFirstItem = ctx.tomorrowItems.length > 0 ? ctx.tomorrowItems[0] : null;

            return `
                <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                    <div class="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto text-xl font-bold">
                        🌿
                    </div>
                    <div class="space-y-1">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-emerald-700 block">RECHARGED</span>
                        <h3 class="font-heading text-2xl font-bold text-[#202124]">Break complete 🌿</h3>
                        <p class="text-xs text-[#6F6B68]">You're done with today's plan.</p>
                    </div>

                    ${tomorrowFirstItem ? `
                        <div class="p-4 bg-stone-50 border border-stone-200 rounded-2xl text-left space-y-1">
                            <span class="text-[10px] font-bold uppercase tracking-wider text-stone-500 block">Tomorrow starts with:</span>
                            <h4 class="text-sm font-bold text-[#202124]">${escapeHTML(tomorrowFirstItem.task.name)}</h4>
                            ${tomorrowFirstItem.scheduledStartTime ? `
                                <div class="text-xs text-stone-600 pt-0.5 font-medium">${formatTime12H(tomorrowFirstItem.scheduledStartTime)}</div>
                            ` : ''}
                        </div>
                        <p class="text-xs text-stone-500">
                            If you feel like getting ahead, you can start now — but you don't have to.
                        </p>
                    ` : ''}

                    <div class="space-y-2 pt-2">
                        ${tomorrowFirstItem ? `
                            <button type="button" onclick="window.TempoFocusZone.openReviewTomorrow()"
                                    class="btn-primary w-full py-3.5 rounded-2xl font-bold text-xs sm:text-sm shadow-md transition">
                                Review tomorrow
                            </button>
                            <button type="button" onclick="window.TempoFocusZone.startTomorrowTaskEarly('${tomorrowFirstItem.task.id}')"
                                    class="w-full py-2.5 rounded-2xl border border-stone-200 text-xs font-semibold text-stone-700 hover:bg-stone-50 transition">
                                Start a task now
                            </button>
                        ` : ''}
                        <button type="button" onclick="window.TempoFocusZone.close()"
                                class="w-full py-2 text-xs text-stone-500 hover:text-stone-800 underline">
                            Done
                        </button>
                    </div>
                </div>
            `;
        }

        // Another task remains today
        const nextItem = ctx.todayItems.find(pt => pt.task && !pt.task.completed);
        const nextTask = nextItem ? nextItem.task : { name: session.taskName, durationLabel: '' };
        const plannedStartStr = nextItem && nextItem.scheduledStartTime ? formatTime12H(nextItem.scheduledStartTime) : '';
        const isFutureTask = nextItem && nextItem.scheduledStartTime && isTimeInFuture(nextItem.scheduledStartTime);
        const focusMin = Math.round(session.focusDurationSeconds / 60);
        const breakMin = Math.round(session.breakDurationSeconds / 60);

        if (isFutureTask && plannedStartStr) {
            return `
                <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                    <div class="space-y-1">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-emerald-700 block">RECHARGED</span>
                        <h3 class="font-heading text-2xl font-bold text-[#202124]">Break complete 🌿</h3>
                        <p class="text-xs text-[#6F6B68]">
                            Your next task is planned for <strong>${escapeHTML(plannedStartStr)}</strong>.
                        </p>
                    </div>

                    <div class="p-4 bg-[#FFF8F2] border border-[#FFD2BA] rounded-2xl text-left space-y-1">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-[#B83D08] block">Next task</span>
                        <h4 class="text-sm font-bold text-[#202124]">${escapeHTML(nextTask.name)}</h4>
                        ${nextTask.durationLabel ? `
                            <div class="flex items-center justify-between text-xs text-stone-600 pt-1">
                                <span>Estimate</span>
                                <span class="font-semibold text-stone-800">${escapeHTML(nextTask.durationLabel)} focused work</span>
                            </div>
                        ` : ''}
                    </div>

                    <p class="text-xs text-stone-500">
                        If you're ready, you can start now — or come back when it's time.
                    </p>

                    <div class="space-y-2 pt-2">
                        <button type="button" onclick="window.TempoFocusZone.readyForNextFocusBlock()"
                                class="btn-primary w-full py-3.5 rounded-2xl font-bold text-xs sm:text-sm shadow-md transition flex items-center justify-center space-x-1.5">
                            <span>Start now</span>
                            <span>→</span>
                        </button>
                        <button type="button" onclick="window.TempoFocusZone.openChangeRhythmModal()"
                                class="w-full py-2.5 rounded-2xl border border-stone-200 text-xs font-semibold text-stone-700 hover:bg-stone-50 transition">
                            Change focus rhythm
                        </button>
                        <button type="button" onclick="window.TempoFocusZone.finishFocusEarly()"
                                class="w-full py-2 text-xs text-stone-500 hover:text-stone-800 underline">
                            I'll start at ${escapeHTML(plannedStartStr)}
                        </button>
                    </div>
                </div>
            `;
        }

        return `
            <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-emerald-700 block">RECHARGED</span>
                    <h3 class="font-heading text-2xl font-bold text-[#202124]">Break complete 🌿</h3>
                </div>

                <div class="p-4 bg-[#FFF8F2] border border-[#FFD2BA] rounded-2xl text-left space-y-2">
                    <div>
                        <span class="text-[10px] font-bold uppercase tracking-wider text-[#B83D08] block">UP NEXT</span>
                        <h4 class="text-sm font-bold text-[#202124]">${escapeHTML(nextTask.name)}</h4>
                    </div>
                    ${plannedStartStr ? `
                        <div class="flex items-center justify-between text-xs text-stone-600 border-t border-stone-200/60 pt-1.5">
                            <span>Planned start</span>
                            <span class="font-semibold text-stone-800">${escapeHTML(plannedStartStr)}</span>
                        </div>
                    ` : ''}
                    ${nextTask.durationLabel ? `
                        <div class="flex items-center justify-between text-xs text-stone-600 border-t border-stone-200/60 pt-1.5">
                            <span>Estimate</span>
                            <span class="font-semibold text-stone-800">${escapeHTML(nextTask.durationLabel)} focused work</span>
                        </div>
                    ` : ''}
                    <div class="flex items-center justify-between text-xs text-stone-600 border-t border-stone-200/60 pt-1.5">
                        <span>Current rhythm</span>
                        <span class="font-semibold text-stone-800">${focusMin} min focus · ${breakMin} min break</span>
                    </div>
                </div>

                <div class="space-y-2 pt-2">
                    <button type="button" onclick="window.TempoFocusZone.readyForNextFocusBlock()"
                            class="btn-primary w-full py-3.5 rounded-2xl font-bold text-xs sm:text-sm shadow-md transition flex items-center justify-center space-x-1.5">
                        <span>Start next focus</span>
                        <span>→</span>
                    </button>
                    <button type="button" onclick="window.TempoFocusZone.openChangeRhythmModal()"
                            class="w-full py-2.5 rounded-2xl border border-stone-200 text-xs font-semibold text-stone-700 hover:bg-stone-50 transition">
                        Change focus rhythm
                    </button>
                    <button type="button" onclick="window.TempoFocusZone.finishFocusEarly()"
                            class="w-full py-2 text-xs text-stone-500 hover:text-stone-800 underline">
                        Finish focus for now
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // NEW RENDER VIEWS (GOALS A, B, C)
    // -------------------------------------------------------------------------

    // View 14: Task finished with time remaining in current block (Section 3)
    function renderTaskFinishedEarly(style) {
        const mins = Math.floor(session.focusSecondsRemaining / 60);
        const secs = session.focusSecondsRemaining % 60;
        const timeDisplay = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

        return `
            <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                <div class="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto text-xl font-bold">
                    ✓
                </div>
                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">${escapeHTML(session.taskName)} complete ✓</h3>
                    <p class="text-xs text-[#6F6B68]">
                        You still have <strong>${timeDisplay}</strong> in this focus block.
                    </p>
                    <p class="text-xs text-stone-500 font-medium">What would you like to do?</p>
                </div>

                <div class="space-y-2.5 pt-2 text-left">
                    <button type="button" onclick="window.TempoFocusZone.continueWithNextTask()"
                            class="btn-primary w-full p-3.5 rounded-2xl text-xs font-bold transition flex items-center justify-between shadow-sm group">
                        <div>
                            <span class="block text-white font-extrabold">Continue with next task</span>
                            <span class="text-[11px] font-normal text-white/80">Keep this timer running with your next planned task today.</span>
                        </div>
                        <span class="text-white group-hover:translate-x-1 transition-transform font-bold">→</span>
                    </button>

                    <button type="button" onclick="window.TempoFocusZone.markDoneAndTakeBreak()"
                            class="w-full p-3.5 rounded-2xl bg-white border border-stone-200 hover:border-stone-300 text-stone-800 text-xs font-semibold transition flex items-center justify-between shadow-2xs group hover:bg-stone-50">
                        <div>
                            <span class="block font-bold">Mark as done and take a break</span>
                            <span class="text-[11px] font-normal text-stone-500">End this block now and recharge with a contained break.</span>
                        </div>
                        <span class="text-stone-400 group-hover:translate-x-1 transition-transform">→</span>
                    </button>

                    <button type="button" onclick="window.TempoFocusZone.finishFocusEarly()"
                            class="w-full py-2.5 text-xs text-stone-500 hover:text-stone-800 underline text-center">
                        Finish focus early
                    </button>
                </div>
            </div>
        `;
    }

    // View 15: Last task of today completed (Section 8)
    function renderLastTaskToday(style) {
        return `
            <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                <div class="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto text-xl font-bold">
                    🌿
                </div>
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C] block">FINAL TASK FOR TODAY</span>
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">You're at the end of today's plan.</h3>
                    <p class="text-xs text-[#6F6B68]">
                        "${escapeHTML(session.taskName)}" is the last unfinished task scheduled for today.
                    </p>
                </div>

                <div class="space-y-2.5 pt-2">
                    <button type="button" onclick="window.TempoFocusZone.markLastTaskCompleted()"
                            class="btn-primary w-full py-3.5 rounded-2xl font-bold text-xs sm:text-sm shadow-md transition flex items-center justify-center space-x-1.5">
                        <span>✓</span>
                        <span>Mark as completed</span>
                    </button>
                    <button type="button" onclick="window.TempoFocusZone.finishFocusEarly()"
                            class="w-full py-2.5 rounded-2xl border border-stone-200 text-xs font-semibold text-stone-700 hover:bg-stone-50 transition">
                        Finish focus early
                    </button>
                </div>
            </div>
        `;
    }

    // View 16: Pre-break orientation before entering break (Section 5 & 6)
    function renderPreBreakOrientation(style) {
        const ctx = getPlanContext();
        const nextItem = ctx.todayItems.find(pt => pt.task && pt.task.id !== session.taskId && !pt.task.completed);
        const nextTaskName = nextItem ? nextItem.task.name : 'Next planned task';
        const plannedStartStr = nextItem && nextItem.scheduledStartTime ? formatTime12H(nextItem.scheduledStartTime) : '';
        const isFuture = nextItem && nextItem.scheduledStartTime && isTimeInFuture(nextItem.scheduledStartTime);

        return `
            <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                <div class="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto text-xl font-bold">
                    ✓
                </div>
                <div class="space-y-1">
                    <h3 class="font-heading text-xl font-bold text-[#202124]">Nice work — task is done ✓</h3>
                    <p class="text-xs text-[#6F6B68]">Take your break first. We'll remind you what comes next afterward.</p>
                </div>

                <div class="p-4 bg-[#FFF8F2] border border-[#FFD2BA] rounded-2xl text-left space-y-1">
                    ${isFuture && plannedStartStr ? `
                        <span class="text-[10px] font-bold uppercase tracking-wider text-[#B83D08] block">Your next task:</span>
                        <h4 class="text-sm font-bold text-[#202124]">${escapeHTML(nextTaskName)}</h4>
                        <div class="flex items-center justify-between text-xs text-stone-600 pt-1">
                            <span>Planned start</span>
                            <span class="font-bold text-stone-800">${escapeHTML(plannedStartStr)}</span>
                        </div>
                    ` : `
                        <span class="text-[10px] font-bold uppercase tracking-wider text-[#B83D08] block">Your next task is ready when you are.</span>
                        <h4 class="text-sm font-bold text-[#202124]">${escapeHTML(nextTaskName)}</h4>
                        ${plannedStartStr ? `
                            <div class="flex items-center justify-between text-xs text-stone-600 pt-1">
                                <span>Planned for</span>
                                <span class="font-bold text-stone-800">${escapeHTML(plannedStartStr)}</span>
                            </div>
                        ` : ''}
                    `}
                </div>

                <div class="space-y-2 pt-1">
                    <button type="button" onclick="window.TempoFocusZone.startBreakPeriod()"
                            class="btn-primary w-full py-3.5 rounded-2xl font-bold text-xs sm:text-sm shadow-md transition">
                        Start break (${Math.round(session.breakDurationSeconds / 60)}m) →
                    </button>
                    <button type="button" onclick="window.TempoFocusZone.finishFocusEarly()"
                            class="w-full py-2 text-xs text-stone-500 hover:text-stone-800 underline">
                        Finish for now
                    </button>
                </div>
            </div>
        `;
    }

    // View 17: Finish Early Orientation reminder (Section 7)
    function renderFinishEarlyOrient(style) {
        const ctx = getPlanContext();
        const todayUnfinishedList = ctx.todayItems.filter(pt => pt.task && !pt.task.completed);
        const nextItem = todayUnfinishedList.length > 0 ? todayUnfinishedList[0] : null;
        let nextPlannedText = '';
        if (nextItem) {
            const timeStr = nextItem.scheduledStartTime ? ` · ${formatTime12H(nextItem.scheduledStartTime)}` : '';
            nextPlannedText = `${nextItem.task.name}${timeStr}`;
        }

        return `
            <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C] block">SESSION PAUSED</span>
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Focus finished for now.</h3>
                    <p class="text-xs text-[#6F6B68]">You still have work planned for today:</p>
                </div>

                <div class="space-y-2 text-left py-1">
                    ${todayUnfinishedList.map(item => `
                        <div class="p-3 bg-stone-50 border border-stone-200 rounded-xl flex items-center justify-between text-xs">
                            <span class="font-bold text-[#202124] truncate pr-2">• ${escapeHTML(item.task.name)}</span>
                            <span class="text-[11px] font-medium ${item.task.isInProgress ? 'text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200' : 'text-stone-500'} shrink-0">
                                ${item.task.isInProgress ? 'in progress' : 'not started'}
                            </span>
                        </div>
                    `).join('')}
                </div>

                ${nextPlannedText ? `
                    <div class="p-3 bg-[#FFF9F4] border border-[#FFE4D4] rounded-xl text-left text-xs">
                        <span class="text-[10px] font-bold uppercase text-[#B83D08] block">Next planned</span>
                        <span class="font-semibold text-stone-800">${escapeHTML(nextPlannedText)}</span>
                    </div>
                ` : `
                    <p class="text-xs text-stone-500">
                        You still have tasks planned for today. Continue whenever you're ready.
                    </p>
                `}

                <div class="space-y-2 pt-2">
                    <button type="button" onclick="window.TempoFocusZone.navigateHomeAndClose()"
                            class="btn-primary w-full py-3 rounded-2xl font-bold text-xs sm:text-sm shadow-md transition">
                        Return to Home
                    </button>
                    <button type="button" onclick="window.TempoFocusZone.viewTodaysPlanAndClose()"
                            class="w-full py-2.5 rounded-2xl border border-stone-200 text-xs font-semibold text-stone-700 hover:bg-stone-50 transition">
                        View today's plan
                    </button>
                </div>
            </div>
        `;
    }

    // View 18: Today's Plan Complete (Section 9)
    function renderTodayComplete(style) {
        const ctx = getPlanContext();
        let tomorrowSummary = null;
        if (ctx.tomorrowItems.length > 0) {
            const count = ctx.tomorrowItems.length;
            const totalMins = ctx.tomorrowItems.reduce((acc, pt) => acc + (pt.task.estimateMinutes || pt.allocatedMinutes || 45), 0);
            tomorrowSummary = {
                taskCountStr: `${count} task${count > 1 ? 's' : ''}`,
                durationStr: formatMinutesFriendly(totalMins)
            };
        }

        return `
            <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                <div class="w-14 h-14 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto text-2xl font-bold shadow-xs">
                    🌿
                </div>
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-emerald-700 block">DAY COMPLETE</span>
                    <h3 class="font-heading text-2xl font-extrabold text-[#202124]">Today's plan is complete ✓</h3>
                    <p class="text-xs text-[#6F6B68]">
                        You made it through everything you planned for today.
                    </p>
                </div>

                ${tomorrowSummary ? `
                    <div class="p-4 bg-stone-50 border border-stone-200 rounded-2xl text-left space-y-1.5">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-stone-500 block">Tomorrow</span>
                        <div class="text-xs font-bold text-stone-800">
                            ${escapeHTML(tomorrowSummary.taskCountStr)} · ~${escapeHTML(tomorrowSummary.durationStr)} focused work
                        </div>
                        <p class="text-[11px] text-stone-600">Would you like to take a quick look at tomorrow's plan?</p>
                    </div>
                ` : ''}

                <div class="space-y-2 pt-2">
                    <button type="button" onclick="window.TempoFocusZone.startPostDayBreak()"
                            class="btn-primary w-full py-3.5 rounded-2xl font-bold text-xs sm:text-sm shadow-md transition flex items-center justify-center space-x-1.5">
                        <span>Take a break (${Math.round(session.breakDurationSeconds / 60)}m)</span>
                        <span>→</span>
                    </button>

                    ${tomorrowSummary ? `
                        <button type="button" onclick="window.TempoFocusZone.openReviewTomorrow()"
                                class="w-full py-2.5 rounded-2xl border border-stone-200 text-xs font-semibold text-stone-700 hover:bg-stone-50 transition">
                            Review tomorrow's plan
                        </button>
                    ` : ''}

                    <button type="button" onclick="window.TempoFocusZone.close()"
                            class="w-full py-2 text-xs text-stone-500 hover:text-stone-800 underline">
                        Done for today
                    </button>
                </div>
            </div>
        `;
    }

    // View 19: Preview Tomorrow's Plan (Section 11)
    function renderReviewTomorrow(style) {
        const ctx = getPlanContext();

        return `
            <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C] block">PREVIEW</span>
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Tomorrow's Plan</h3>
                </div>

                <div class="space-y-2 text-left py-1 max-h-56 overflow-y-auto pr-1">
                    ${ctx.tomorrowItems.map(item => `
                        <div class="p-3 bg-stone-50 border border-stone-200 rounded-xl space-y-0.5">
                            <div class="flex items-center justify-between text-xs font-bold text-[#202124]">
                                <span class="truncate pr-2">${escapeHTML(item.task.name)}</span>
                                <span class="text-[10px] font-bold text-[#FF6B2C] uppercase shrink-0">${item.planPositionBadge || 'SCHEDULED'}</span>
                            </div>
                            <div class="text-[11px] text-stone-500">
                                ${item.scheduledStartTime ? `${formatTime12H(item.scheduledStartTime)}${item.scheduledEndTime ? '–' + formatTime12H(item.scheduledEndTime) : ''}` : 'Time flexible'}
                                ${item.task.durationLabel ? ` · ~${item.task.durationLabel}` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>

                <div class="space-y-2 pt-2">
                    <button type="button" onclick="window.TempoFocusZone.viewTodaysPlanAndClose()"
                            class="btn-primary w-full py-3 rounded-2xl font-bold text-xs sm:text-sm shadow-md transition">
                        View / Edit Tomorrow's Plan
                    </button>
                    <button type="button" onclick="window.TempoFocusZone.close()"
                            class="w-full py-2 text-xs text-stone-500 hover:text-stone-800 underline">
                        Done
                    </button>
                </div>
            </div>
        `;
    }

    // View 20: Round completion grace state (Section 16)
    function renderRoundGrace(style) {
        return `
            <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                <div class="w-14 h-14 rounded-2xl bg-purple-100 text-purple-700 flex items-center justify-center mx-auto text-2xl shadow-xs">
                    🎮
                </div>
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-purple-700 block">ROUND IN PROGRESS</span>
                    <h3 class="font-heading text-2xl font-bold text-[#202124]">Finish your round 🎮</h3>
                    <p class="text-xs text-[#6F6B68]">
                        Wrap up the round you're already in. Take your time to finish this match.
                    </p>
                </div>

                <div class="pt-4">
                    <button type="button" onclick="window.TempoFocusZone.confirmRoundDone()"
                            class="btn-primary w-full py-3.5 rounded-2xl font-bold text-xs sm:text-sm shadow-md transition flex items-center justify-center space-x-1.5">
                        <span>✓</span>
                        <span>I'm done</span>
                    </button>
                </div>
            </div>
        `;
    }

    // View 21: Change Focus Rhythm Modal (Section 25)
    function renderChangeRhythm(style) {
        const selectedPreset = rhythmModalState.selectedPreset;
        const customFocusVal = rhythmModalState.customFocus;
        const customBreakVal = rhythmModalState.customBreak;

        return `
            <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C] block">PACING</span>
                    <h3 class="font-heading text-2xl font-bold text-[#202124]">Change focus rhythm</h3>
                    <p class="text-xs text-[#6F6B68]">Find a pace that works better for you.</p>
                </div>

                <div class="space-y-2 text-left pt-1">
                    <label class="p-3.5 rounded-2xl border ${selectedPreset === '25_5' ? 'border-2 border-[#FF6B2C] bg-[#FFF8F2]' : 'border-stone-200 bg-white hover:border-stone-300'} flex items-center justify-between cursor-pointer transition">
                        <div class="flex items-center space-x-3">
                            <input type="radio" name="fz_rhythm_choice" value="25_5" ${selectedPreset === '25_5' ? 'checked' : ''} onchange="window.TempoFocusZone.selectRhythmChoice('25_5')" class="text-[#FF6B2C] focus:ring-[#FF6B2C]">
                            <div>
                                <span class="text-xs font-bold text-[#202124] block">25 min focus · 5 min break</span>
                                <span class="text-[10px] text-stone-500">Pomodoro cadence</span>
                            </div>
                        </div>
                    </label>

                    <label class="p-3.5 rounded-2xl border ${selectedPreset === '45_15' ? 'border-2 border-[#FF6B2C] bg-[#FFF8F2]' : 'border-stone-200 bg-white hover:border-stone-300'} flex items-center justify-between cursor-pointer transition">
                        <div class="flex items-center space-x-3">
                            <input type="radio" name="fz_rhythm_choice" value="45_15" ${selectedPreset === '45_15' ? 'checked' : ''} onchange="window.TempoFocusZone.selectRhythmChoice('45_15')" class="text-[#FF6B2C] focus:ring-[#FF6B2C]">
                            <div>
                                <span class="text-xs font-bold text-[#202124] block">45 min focus · 15 min break</span>
                                <span class="text-[10px] text-stone-500">Tempo default cadence</span>
                            </div>
                        </div>
                    </label>

                    <label class="p-3.5 rounded-2xl border ${selectedPreset === '50_10' ? 'border-2 border-[#FF6B2C] bg-[#FFF8F2]' : 'border-stone-200 bg-white hover:border-stone-300'} flex items-center justify-between cursor-pointer transition">
                        <div class="flex items-center space-x-3">
                            <input type="radio" name="fz_rhythm_choice" value="50_10" ${selectedPreset === '50_10' ? 'checked' : ''} onchange="window.TempoFocusZone.selectRhythmChoice('50_10')" class="text-[#FF6B2C] focus:ring-[#FF6B2C]">
                            <div>
                                <span class="text-xs font-bold text-[#202124] block">50 min focus · 10 min break</span>
                                <span class="text-[10px] text-stone-500">Deep work blocks</span>
                            </div>
                        </div>
                    </label>

                    <label class="p-3.5 rounded-2xl border ${selectedPreset === 'custom' ? 'border-2 border-[#FF6B2C] bg-[#FFF8F2]' : 'border-stone-200 bg-white hover:border-stone-300'} flex items-center justify-between cursor-pointer transition">
                        <div class="flex items-center space-x-3">
                            <input type="radio" name="fz_rhythm_choice" value="custom" ${selectedPreset === 'custom' ? 'checked' : ''} onchange="window.TempoFocusZone.selectRhythmChoice('custom')" class="text-[#FF6B2C] focus:ring-[#FF6B2C]">
                            <div>
                                <span class="text-xs font-bold text-[#202124] block">Custom</span>
                                <span class="text-[10px] text-stone-500">Set your own focus and break durations</span>
                            </div>
                        </div>
                    </label>

                    ${selectedPreset === 'custom' ? `
                        <div class="p-3.5 bg-stone-50 border border-stone-200 rounded-2xl flex items-center gap-3 text-xs mt-2">
                            <div class="flex-1">
                                <label class="text-[10px] uppercase font-bold text-stone-500 block">Focus</label>
                                <div class="flex items-center gap-1.5 mt-0.5">
                                    <input id="fz-modal-custom-focus" type="number" min="1" max="180" 
                                           value="${customFocusVal}"
                                           class="w-full px-2.5 py-1.5 text-xs border border-stone-300 rounded-lg text-center font-bold bg-white focus:outline-none focus:ring-1 focus:ring-[#FF6B2C]">
                                    <span class="text-stone-500 font-medium">min</span>
                                </div>
                            </div>
                            <div class="flex-1">
                                <label class="text-[10px] uppercase font-bold text-stone-500 block">Break</label>
                                <div class="flex items-center gap-1.5 mt-0.5">
                                    <input id="fz-modal-custom-break" type="number" min="1" max="60" 
                                           value="${customBreakVal}"
                                           class="w-full px-2.5 py-1.5 text-xs border border-stone-300 rounded-lg text-center font-bold bg-white focus:outline-none focus:ring-1 focus:ring-[#FF6B2C]">
                                    <span class="text-stone-500 font-medium">min</span>
                                </div>
                            </div>
                        </div>
                    ` : ''}
                </div>

                <div class="flex items-center gap-3 pt-2">
                    <button type="button" onclick="window.TempoFocusZone.cancelChangeRhythm()"
                            class="w-1/2 py-3 rounded-2xl border border-stone-200 text-xs font-semibold text-stone-700 hover:bg-stone-50 transition">
                        Cancel
                    </button>
                    <button type="button" onclick="window.TempoFocusZone.saveRhythmFromModal()"
                            class="btn-primary w-1/2 py-3 rounded-2xl font-bold text-xs shadow-sm transition">
                        Save rhythm
                    </button>
                </div>
            </div>
        `;
    }

    // View 22: Focus Rhythm Updated Confirmation (Section 27 & 31)
    function renderRhythmUpdated(style) {
        const ctx = getPlanContext();
        const nextItem = ctx.todayItems.find(pt => pt.task && !pt.task.completed);
        const nextTask = nextItem ? nextItem.task : null;
        const focusMin = Math.round(session.focusDurationSeconds / 60);
        const breakMin = Math.round(session.breakDurationSeconds / 60);

        return `
            <div class="tempo-card w-full max-w-md p-6 sm:p-8 space-y-5 rounded-3xl ${style.cardClass} text-center">
                <div class="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto text-xl font-bold">
                    ✓
                </div>
                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Focus rhythm updated ✓</h3>
                    <p class="text-xs font-bold text-[#FF6B2C]">
                        ${focusMin} min focus · ${breakMin} min break
                    </p>
                    <p class="text-xs text-[#6F6B68] pt-1">
                        This changes how your work and breaks are paced. Your task estimates and current plan stay the same.
                    </p>
                </div>

                ${nextTask ? `
                    <div class="p-4 bg-[#FFF8F2] border border-[#FFD2BA] rounded-2xl text-left space-y-1">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-[#B83D08] block">UP NEXT</span>
                        <h4 class="text-sm font-bold text-[#202124]">${escapeHTML(nextTask.name)}</h4>
                        ${nextTask.durationLabel ? `
                            <div class="flex items-center justify-between text-xs text-stone-600 pt-1">
                                <span>Estimate</span>
                                <span class="font-semibold text-stone-800">${escapeHTML(nextTask.durationLabel)} focused work</span>
                            </div>
                        ` : ''}
                    </div>
                ` : ''}

                <div class="space-y-2 pt-2">
                    <button type="button" onclick="window.TempoFocusZone.readyForNextFocusBlock()"
                            class="btn-primary w-full py-3.5 rounded-2xl font-bold text-xs sm:text-sm shadow-md transition flex items-center justify-center space-x-1.5">
                        <span>Start ${focusMin}-min focus</span>
                        <span>→</span>
                    </button>
                    <button type="button" onclick="window.TempoFocusZone.finishFocusEarly()"
                            class="w-full py-2 text-xs text-stone-500 hover:text-stone-800 underline">
                        Finish focus for now
                    </button>
                </div>
            </div>
        `;
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

    return {
        init,
        open,
        openQuickEntry,
        openStandaloneBreak,
        focusWithoutTask,
        close,
        selectRhythm,
        setCustomRhythm,
        startFocusSession,
        pauseFocusTimer,
        resumeFocusTimer,
        confirmFinishEarly,
        handleFinishChoice,
        completeActiveSubtask,
        handleSubtasksAllDoneChoice,
        finishActiveTaskEarly,
        continueWithNextTask,
        markDoneAndTakeBreak,
        finishFocusEarly,
        markLastTaskCompleted,
        startPostDayBreak,
        openReviewTomorrow,
        startTomorrowTaskEarly,
        startBreakPeriod,
        selectBreakActivity,
        returnToBreakHub,
        extendBreak5Minutes,
        startRoundGrace,
        confirmRoundDone,
        endBreakEarly,
        readyForNextFocusBlock,
        openChangeRhythmModal,
        selectRhythmChoice,
        cancelChangeRhythm,
        saveRhythmFromModal,
        navigateHomeAndClose,
        viewTodaysPlanAndClose,
        handleCardClick,
        initGentleMatch,
        allowFinishCurrentGameRound,
        setBackground,
        setSound,
        setVolume,
        toggleMute,
        handleExitClick,
        render,
        getSessionState: () => ({ ...session }),
        _setSessionForTesting: (patch) => {
            if (patch && typeof patch === 'object') {
                Object.assign(session, patch);
            }
        },
        getPlanContext
    };
})();

// Auto-initialize if DOM is ready
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            if (window.TempoFocusZone) window.TempoFocusZone.init();
        });
    } else {
        if (window.TempoFocusZone) window.TempoFocusZone.init();
    }
}
