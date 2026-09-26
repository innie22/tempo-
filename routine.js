/**
 * Tempo Routine & Habit Tracker
 * Supports students in building gentle, sustainable stress-management habits
 * with flexible, non-judgmental progress tracking and a zero-pressure "Rest Day" mode.
 */

window.TempoRoutine = (function() {
    let habits = [];
    let routineBlocks = [];
    let isGentleDayActive = false;
    let isHabitRestDay = false;

    const dayLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

    function init() {
        loadData();
        bindEvents();
        renderHabits();
        renderRoutine();
        renderDashboardHabitsMini();
    }

    function loadData() {
        // Load Habits from LocalStorage or seed data
        const savedHabits = localStorage.getItem('tempo_habits');
        if (savedHabits) {
            try {
                habits = JSON.parse(savedHabits);
            } catch (e) {
                habits = [...(window.TEMPO_DATA.habits || [])];
            }
        } else {
            habits = [...(window.TEMPO_DATA.habits || [])];
        }

        // Load Routine Blocks from LocalStorage or seed data
        const savedRoutine = localStorage.getItem('tempo_routine');
        if (savedRoutine) {
            try {
                routineBlocks = JSON.parse(savedRoutine);
            } catch (e) {
                routineBlocks = [...(window.TEMPO_DATA.routine || [])];
            }
        } else {
            routineBlocks = [...(window.TEMPO_DATA.routine || [])];
        }

        // Load Rest Day State
        isHabitRestDay = localStorage.getItem('tempo_habit_rest_day') === 'true';
    }

    function bindEvents() {
        // Gentle Day Mode (Routine Blocks)
        const gentleToggle = document.getElementById('toggle-gentle-day');
        if (gentleToggle) {
            gentleToggle.addEventListener('change', (e) => {
                isGentleDayActive = e.target.checked;
                renderRoutine();
                if (isGentleDayActive) {
                    window.TempoApp.showToast("Gentle Day Mode active. Non-essential schedule expectations suspended.");
                } else {
                    window.TempoApp.showToast("Standard daily schedule restored.");
                }
            });
        }

        // Habit Rest Day Toggle
        const restDayBtn = document.getElementById('btn-toggle-habit-rest');
        if (restDayBtn) {
            restDayBtn.addEventListener('click', toggleHabitRestDay);
        }

        // Routine Generation Wizard
        const buildRoutineBtn = document.getElementById('btn-generate-routine');
        if (buildRoutineBtn) {
            buildRoutineBtn.addEventListener('click', handleGenerateRoutine);
        }

        // Add Routine Block Button
        const addBlockBtn = document.getElementById('btn-add-routine-block');
        if (addBlockBtn) {
            addBlockBtn.addEventListener('click', openAddBlockModal);
        }

        // Habit Creation & Preset Modal Buttons
        const openAddHabitBtn = document.getElementById('btn-open-add-habit');
        if (openAddHabitBtn) {
            openAddHabitBtn.addEventListener('click', openAddHabitModal);
        }

        const closeAddHabitBtn = document.getElementById('btn-close-add-habit-modal');
        if (closeAddHabitBtn) {
            closeAddHabitBtn.addEventListener('click', closeAddHabitModal);
        }

        const formAddHabit = document.getElementById('form-add-habit');
        if (formAddHabit) {
            formAddHabit.addEventListener('submit', handleAddCustomHabit);
        }
    }

    // =========================================================================
    // HABITS TRACKER LOGIC (US01)
    // =========================================================================

    function renderHabits() {
        const container = document.getElementById('habits-list-container');
        if (!container) return;

        // Render Progress Bar & Messages
        updateHabitsProgressUI();

        if (habits.length === 0) {
            container.innerHTML = `
                <div class="p-8 text-center bg-white border border-gray-200 rounded-2xl space-y-3">
                    <p class="text-sm text-gray-500">You don't have any scheduled habits yet.</p>
                    <button onclick="window.TempoRoutine.openAddHabitModal()" class="btn-sage px-4 py-2 rounded-xl text-xs font-semibold">
                        + Add Your First Gentle Habit
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = habits.map(habit => {
            const isCompleted = habit.isDone && !isHabitRestDay;
            const categoryBadge = getCategoryBadge(habit.category);
            const timeBadge = habit.timeOfDay ? `<span class="text-[10px] text-gray-400 font-medium px-2 py-0.5 bg-gray-100 rounded-full">${habit.timeOfDay}</span>` : '';

            // Render 7-day momentum dots (non-judgmental consistency view)
            const historyDots = renderMomentumDots(habit.history || [true, true, false, true, true, false, false]);

            return `
                <div class="tempo-card p-4 md:p-5 transition-all duration-200 ${
                    isHabitRestDay 
                        ? 'bg-blue-50/40 border-blue-200' 
                        : (isCompleted ? 'bg-emerald-50/60 border-emerald-300 shadow-sm' : 'bg-white border-gray-200 hover:border-gray-300')
                }">
                    <div class="flex items-start justify-between gap-3">
                        <div class="flex items-start space-x-3.5 flex-1">
                            <!-- Large Accessible Checkbox -->
                            <div class="pt-0.5">
                                <input type="checkbox" id="chk-${habit.id}" ${isCompleted ? 'checked' : ''} ${isHabitRestDay ? 'disabled' : ''}
                                    onchange="window.TempoRoutine.toggleHabitDone('${habit.id}')"
                                    class="w-5 h-5 text-emerald-700 rounded-lg border-gray-300 focus:ring-emerald-500 cursor-pointer disabled:opacity-40 transition">
                            </div>

                            <div class="space-y-1 flex-1">
                                <div class="flex flex-wrap items-center gap-2">
                                    <h4 class="text-sm font-semibold ${isCompleted ? 'line-through text-gray-400' : 'text-gray-900'}">
                                        ${habit.title}
                                    </h4>
                                    ${categoryBadge}
                                    ${timeBadge}
                                    ${isCompleted ? '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">✓ Cared for today</span>' : ''}
                                    ${isHabitRestDay ? '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800">Resting</span>' : ''}
                                </div>
                                <p class="text-xs text-gray-500 leading-relaxed max-w-xl">
                                    ${habit.whyItHelps || 'Supports daily nervous system resilience.'}
                                </p>
                            </div>
                        </div>

                        <!-- Right Actions: Momentum & Delete -->
                        <div class="flex flex-col items-end space-y-2 shrink-0">
                            <!-- 7-Day Momentum Dots -->
                            <div class="flex items-center space-x-1" title="Last 7 days practice">
                                ${historyDots}
                            </div>
                            <button onclick="window.TempoRoutine.deleteHabit('${habit.id}')" 
                                class="text-gray-300 hover:text-red-500 text-xs p-1 transition" title="Remove habit">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderMomentumDots(history) {
        return history.map((val, idx) => {
            const dayName = dayLabels[idx % dayLabels.length];
            let dotColor = 'bg-stone-200 text-stone-400';
            if (val === true) {
                dotColor = 'bg-emerald-600 text-white font-bold';
            } else if (val === 'rest') {
                dotColor = 'bg-blue-300 text-blue-800';
            }
            return `
                <span class="w-4 h-4 rounded-full text-[9px] flex items-center justify-center ${dotColor}" title="Day ${idx + 1}">
                    ${dayName}
                </span>
            `;
        }).join('');
    }

    function updateHabitsProgressUI() {
        const total = habits.length;
        const completed = habits.filter(h => h.isDone).length;
        const percent = total > 0 ? Math.round((completed / total) * 100) : 0;

        const countEl = document.getElementById('habit-progress-counter');
        const barEl = document.getElementById('habit-progress-bar');
        const messageEl = document.getElementById('habit-encouragement-message');
        const restBtn = document.getElementById('btn-toggle-habit-rest');

        if (countEl) {
            countEl.textContent = isHabitRestDay 
                ? 'Mindful Rest Day active' 
                : `${completed} of ${total} gentle habits explored today`;
        }

        if (barEl) {
            barEl.style.width = isHabitRestDay ? '100%' : `${percent}%`;
            barEl.className = isHabitRestDay 
                ? 'h-2 rounded-full transition-all duration-500 bg-blue-500' 
                : 'h-2 rounded-full transition-all duration-500 bg-emerald-600';
        }

        if (messageEl) {
            if (isHabitRestDay) {
                messageEl.textContent = "Rest is not a failure of discipline; it is how your brain consolidates learning and restores emotional capacity.";
            } else if (completed === 0) {
                messageEl.textContent = "No pressure to complete everything. Starting with even one 2-minute micro-habit gives your nervous system a calm anchor.";
            } else if (completed < total) {
                messageEl.textContent = "Every small action grounds your focus and helps buffer academic pressure.";
            } else {
                messageEl.textContent = "You've given yourself full support today. Take a deep breath and acknowledge your effort.";
            }
        }

        if (restBtn) {
            if (isHabitRestDay) {
                restBtn.className = "px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-300 shadow-sm transition flex items-center space-x-1";
                restBtn.innerHTML = `<span>🧘 Resting Today (Active)</span>`;
            } else {
                restBtn.className = "px-3.5 py-1.5 rounded-xl text-xs font-medium bg-stone-100 hover:bg-stone-200 text-stone-700 border border-stone-200 transition flex items-center space-x-1";
                restBtn.innerHTML = `<span>🧘 Take a Rest Day</span>`;
            }
        }
    }

    function toggleHabitDone(id) {
        if (isHabitRestDay) return;

        const habit = habits.find(h => h.id === id);
        if (habit) {
            habit.isDone = !habit.isDone;

            // Update last day in history
            if (!habit.history) habit.history = [true, true, true, false, true, false, false];
            habit.history[habit.history.length - 1] = habit.isDone;

            saveHabits();
            renderHabits();
            renderDashboardHabitsMini();

            if (habit.isDone) {
                window.TempoApp.showToast(`✓ "${habit.title}" completed. One small step for your wellbeing!`);
                const allDone = habits.every(h => h.isDone);
                if (allDone) {
                    window.TempoApp.triggerConfetti();
                    window.TempoApp.showToast("All habits explored today! Remarkable self-care.");
                }
            }
        }
    }

    function toggleHabitRestDay() {
        isHabitRestDay = !isHabitRestDay;
        localStorage.setItem('tempo_habit_rest_day', isHabitRestDay.toString());
        renderHabits();
        renderDashboardHabitsMini();

        if (isHabitRestDay) {
            window.TempoApp.showToast("Mindful Rest Day activated. Take time to breathe without task pressure.");
        } else {
            window.TempoApp.showToast("Active habit cadence resumed.");
        }
    }

    function getCategoryBadge(category) {
        switch (category) {
            case 'Physical':
                return '<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-100 text-sky-800">Physical</span>';
            case 'Mental / Calm':
                return '<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">Calm Reset</span>';
            case 'Focus':
                return '<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-100 text-indigo-800">Focus</span>';
            case 'Recovery':
                return '<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-800">Recovery</span>';
            case 'Sleep':
                return '<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-100 text-purple-800">Sleep Anchor</span>';
            default:
                return '<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-gray-100 text-gray-700">Habit</span>';
        }
    }

    // =========================================================================
    // HABIT MODAL & PRESETS DRAWER
    // =========================================================================

    function openAddHabitModal() {
        const modal = document.getElementById('add-habit-modal');
        if (!modal) return;

        // Render Pre-curated Habit Library Presets
        const presetsList = document.getElementById('habit-presets-grid');
        const presets = window.TEMPO_DATA.habitPresets || [];

        if (presetsList) {
            presetsList.innerHTML = presets.map((p, idx) => `
                <div class="p-3 bg-stone-50 border border-stone-200 rounded-xl flex items-center justify-between hover:border-emerald-300 transition">
                    <div class="space-y-0.5 pr-2">
                        <div class="flex items-center space-x-2">
                            <h5 class="text-xs font-bold text-gray-900">${p.title}</h5>
                            ${getCategoryBadge(p.category)}
                        </div>
                        <p class="text-[11px] text-gray-500">${p.whyItHelps}</p>
                    </div>
                    <button type="button" onclick="window.TempoRoutine.addPresetHabit(${idx})" 
                        class="px-2.5 py-1 bg-white border border-gray-300 hover:border-emerald-600 hover:text-emerald-700 text-gray-700 rounded-lg text-xs font-semibold shrink-0 transition">
                        + Add
                    </button>
                </div>
            `).join('');
        }

        modal.classList.remove('hidden');
    }

    function closeAddHabitModal() {
        const modal = document.getElementById('add-habit-modal');
        if (modal) modal.classList.add('hidden');
    }

    function addPresetHabit(index) {
        const presets = window.TEMPO_DATA.habitPresets || [];
        const preset = presets[index];
        if (!preset) return;

        habits.push({
            id: `hab-pre-${Date.now()}`,
            title: preset.title,
            whyItHelps: preset.whyItHelps,
            category: preset.category,
            timeOfDay: preset.timeOfDay,
            isDone: false,
            history: [false, true, true, false, false, false, false]
        });

        saveHabits();
        renderHabits();
        renderDashboardHabitsMini();
        closeAddHabitModal();
        window.TempoApp.showToast(`Added "${preset.title}" to your routine habits!`);
    }

    function handleAddCustomHabit(e) {
        e.preventDefault();
        const title = document.getElementById('input-habit-title').value.trim();
        const why = document.getElementById('input-habit-why').value.trim();
        const category = document.getElementById('select-habit-category').value;
        const timeOfDay = document.getElementById('select-habit-time').value;

        if (!title) {
            window.TempoApp.showToast("Please enter a title for your habit.");
            return;
        }

        habits.push({
            id: `hab-cust-${Date.now()}`,
            title: title,
            whyItHelps: why || 'Supports daily calm and cognitive clarity.',
            category: category,
            timeOfDay: timeOfDay,
            isDone: false,
            history: [false, false, false, false, false, false, false]
        });

        saveHabits();
        renderHabits();
        renderDashboardHabitsMini();
        closeAddHabitModal();
        e.target.reset();
        window.TempoApp.showToast("Custom gentle habit added!");
    }

    function deleteHabit(id) {
        if (confirm("Remove this habit from your routine?")) {
            habits = habits.filter(h => h.id !== id);
            saveHabits();
            renderHabits();
            renderDashboardHabitsMini();
            window.TempoApp.showToast("Habit removed.");
        }
    }

    function saveHabits() {
        localStorage.setItem('tempo_habits', JSON.stringify(habits));
    }

    // =========================================================================
    // DASHBOARD MINI-WIDGET SYNC
    // =========================================================================

    function renderDashboardHabitsMini() {
        const container = document.getElementById('dashboard-habits-mini-list');
        if (!container) return;

        const total = habits.length;
        const completed = habits.filter(h => h.isDone).length;

        const countLabel = document.getElementById('dashboard-habit-count-label');
        if (countLabel) {
            countLabel.textContent = isHabitRestDay 
                ? 'Rest Day' 
                : `${completed}/${total} done`;
        }

        container.innerHTML = habits.slice(0, 3).map(h => `
            <div class="flex items-center justify-between text-xs py-1.5 border-b border-gray-100 last:border-none">
                <div class="flex items-center space-x-2">
                    <input type="checkbox" ${h.isDone && !isHabitRestDay ? 'checked' : ''} ${isHabitRestDay ? 'disabled' : ''}
                        onchange="window.TempoRoutine.toggleHabitDone('${h.id}')"
                        class="w-4 h-4 text-emerald-700 rounded border-gray-300 focus:ring-emerald-500 cursor-pointer">
                    <span class="${h.isDone && !isHabitRestDay ? 'line-through text-gray-400' : 'text-gray-800 font-medium'} truncate max-w-[180px]">
                        ${h.title}
                    </span>
                </div>
                ${getCategoryBadge(h.category)}
            </div>
        `).join('');
    }

    // =========================================================================
    // TIME-BLOCKED SCHEDULE BLOCKS LOGIC
    // =========================================================================

    function renderRoutine() {
        const listEl = document.getElementById('routine-blocks-list');
        const dashboardListEl = document.getElementById('dashboard-routine-list');

        const activeList = isGentleDayActive 
            ? routineBlocks.filter(b => b.tag === 'Sleep' || b.tag === 'Recovery' || b.id === 'rt-1')
            : routineBlocks;

        const html = activeList.map(block => {
            const tagBadge = getTagBadge(block.tag);
            return `
                <div class="p-3.5 bg-white border border-gray-200 rounded-xl flex items-center justify-between transition hover:border-gray-300">
                    <div class="flex items-center space-x-3.5">
                        <input type="checkbox" ${block.isDone ? 'checked' : ''} 
                            onchange="window.TempoRoutine.toggleBlockDone('${block.id}')"
                            class="w-5 h-5 text-emerald-700 rounded border-gray-300 focus:ring-emerald-500 cursor-pointer">
                        <div>
                            <span class="text-xs font-semibold text-gray-500 block">${block.time}</span>
                            <h4 class="text-sm font-medium ${block.isDone ? 'line-through text-gray-400' : 'text-gray-900'}">${block.title}</h4>
                        </div>
                    </div>
                    <div>
                        ${tagBadge}
                    </div>
                </div>
            `;
        }).join('');

        if (listEl) listEl.innerHTML = html;
        if (dashboardListEl) dashboardListEl.innerHTML = html;

        // Update progress count
        const total = activeList.length;
        const completed = activeList.filter(b => b.isDone).length;
        const progressEl = document.getElementById('routine-progress-counter');
        if (progressEl) {
            progressEl.textContent = `${completed} of ${total} activities completed`;
        }
    }

    function getTagBadge(tag) {
        if (tag === 'Focus') {
            return `<span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">Focus Block</span>`;
        } else if (tag === 'Recovery') {
            return `<span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">Recharge</span>`;
        } else {
            return `<span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">Sleep Anchor</span>`;
        }
    }

    function toggleBlockDone(id) {
        const block = routineBlocks.find(b => b.id === id);
        if (block) {
            block.isDone = !block.isDone;
            saveRoutine();
            renderRoutine();
            if (block.isDone) {
                window.TempoApp.showToast("Block marked as complete. Well done!");
            }
        }
    }

    function handleGenerateRoutine() {
        const focusWindow = document.getElementById('select-focus-window').value;
        const sleepTime = document.getElementById('input-sleep-time').value || "11:00 PM";
        const recoveryChoice = document.getElementById('select-recovery-choice').value;

        routineBlocks = [
            {
                id: 'rt-gen-1',
                time: focusWindow === 'morning' ? '09:30 - 10:30 AM' : '02:00 - 03:00 PM',
                title: 'Primary Priority: Deep Focus Window',
                tag: 'Focus',
                tagColor: 'sage',
                isDone: false,
                isFlexible: false
            },
            {
                id: 'rt-gen-2',
                time: '01:00 - 01:30 PM',
                title: `Recovery Anchor: ${recoveryChoice}`,
                tag: 'Recovery',
                tagColor: 'blue',
                isDone: false,
                isFlexible: true
            },
            {
                id: 'rt-gen-3',
                time: focusWindow === 'morning' ? '03:30 - 04:30 PM' : '07:30 - 08:30 PM',
                title: 'Secondary Priority: Gentle Review & Organization',
                tag: 'Focus',
                tagColor: 'sage',
                isDone: false,
                isFlexible: false
            },
            {
                id: 'rt-gen-4',
                time: '09:00 - 09:45 PM',
                title: `Wind-down & Sleep Anchor (Target: ${sleepTime})`,
                tag: 'Sleep',
                tagColor: 'amber',
                isDone: false,
                isFlexible: true
            }
        ];

        saveRoutine();
        renderRoutine();
        window.TempoApp.showToast("New personalized routine created!");
    }

    function openAddBlockModal() {
        const title = prompt("Enter activity title (e.g., Chemistry Flashcards or 15-min Walk):");
        if (!title) return;
        const time = prompt("Enter time window (e.g., 4:00 - 4:45 PM):", "4:00 - 4:45 PM");

        routineBlocks.push({
            id: 'rt-custom-' + Date.now(),
            time: time || 'Flexible',
            title: title,
            tag: 'Focus',
            tagColor: 'sage',
            isDone: false,
            isFlexible: true
        });

        saveRoutine();
        renderRoutine();
        window.TempoApp.showToast("Custom routine block added.");
    }

    function saveRoutine() {
        localStorage.setItem('tempo_routine', JSON.stringify(routineBlocks));
    }

    return {
        init,
        toggleHabitDone,
        toggleHabitRestDay,
        openAddHabitModal,
        closeAddHabitModal,
        addPresetHabit,
        deleteHabit,
        toggleBlockDone
    };
})();
