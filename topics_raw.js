const LEARN_TOPICS = [
        {
            id: 'what_is_stress',
            type: 'learn',
            badge: '🧠 Stress Education · Topic',
            icon: '⚡',
            title: 'What is stress?',
            shortDescription: 'A normal response to pressure, change, or demands requiring adaptation.',
            contentParagraphs: [
                'Stress is not a disease, personal weakness, or character flaw. It is an evolutionary physiological mechanism evolved to prepare your mind and body to meet challenges and adapt to demands.',
                'When you encounter a challenging deadline, an unexpected exam question, or interpersonal friction, your brain activates the sympathetic nervous system and the HPA axis, releasing hormones like adrenaline and cortisol. Your heart beats faster, breathing rate increases, and attention narrows onto the immediate task.',
                'At a moderate, manageable level, acute stress is helpful: it mobilizes energy, sharpens focus, and enhances readiness. The concern is when stress becomes excessive, continuous, or lacks adequate opportunity for recovery.'
            ],
            tipId: 'interruptTheLoop',
            relatedSolveIds: ['cant_focus'],
            relatedTool: { id: 'quick_relief', label: 'Open Quick Relief', action: 'quick_relief' }
        },
        {
            id: 'stress_problem',
            type: 'learn',
            badge: '🧠 Stress Education · Topic',
            icon: '📉',
            title: 'When does stress become a problem?',
            shortDescription: 'The difference between healthy stress cycles and chronic unremitting overload.',
            contentParagraphs: [
                'In healthy circumstances, stress follows a natural cycle: Pressure → Stress → Completion → Rest → Recovery. Once the pressure point is resolved, the nervous system down-regulates and returns to its resting baseline.',
                'In university life, stress often becomes an unrelenting loop: Deadline → Stress → Another Deadline → Stress → Group Project → Stress → Exam... Without pauses for recovery, the nervous system remains on continuous high alert.',
                'Crucially, duration and lack of recovery matter just as much as acute intensity. When stress continues without relief, it gradually erodes five everyday areas:'
            ],
            descriptiveList: [
                { title: 'Sleep', detail: 'Difficulty falling asleep, frequent waking, or waking up feeling unrefreshed.' },
                { title: 'Concentration', detail: 'Working memory degrades, making reading and problem-solving feel twice as hard.' },
                { title: 'Emotions', detail: 'Heightened irritability, sudden tearfulness, or emotional numbness.' },
                { title: 'Energy', detail: 'Deep physical and mental fatigue that persistent coffee consumption cannot fix.' },
                { title: 'Everyday routines', detail: 'Regular meals, personal hygiene, and tidy living spaces begin to slip.' }
            ],
            tipId: 'selfCheckSigns',
            relatedSolveIds: ['deadline_pileup'],
            relatedTool: { id: 'quick_relief', label: 'Open Quick Relief', action: 'quick_relief' },
            relatedMode: { mode: 'recovery', label: 'Go to Recovery Mode' }
        },
        {
            id: 'stress_signs',
            type: 'learn',
            badge: '🧠 Stress Education · Topic',
            icon: '🔍',
            title: 'How stress can show up',
            shortDescription: 'The 4 groups of stress signs: Thoughts, Emotions, Body, and Behavior.',
            contentParagraphs: [
                'Stress is not merely an intellectual experience. It distributes itself across four interconnected domains of your daily life:',
                'Repeated signs can become your personal early detection signals. If you notice yourself skipping breakfast or clenching your jaw, treating those signs early helps you adjust before reaching exhaustion.'
            ],
            fourGroups: [
                {
                    name: '🧠 Thoughts',
                    items: ['Difficulty concentrating', 'Thoughts racing continuously', 'Difficulty making decisions', 'Frequent mind-blanking']
                },
                {
                    name: '💭 Emotions',
                    items: ['Persistent worry', 'Irritability / snapping at friends', 'Feelings of sadness or dread', 'Feeling overwhelmed by minor tasks']
                },
                {
                    name: '💤 Body',
                    items: ['Chronic tiredness', 'Difficulty falling asleep', 'Tension headaches', 'Muscle tightness in neck/shoulders']
                },
                {
                    name: '🔄 Behavior & daily life',
                    items: ['Procrastinating on simple actions', 'Withdrawing from social circles', 'Irregular eating / appetite loss', 'Letting daily routines slide']
                }
            ],
            tipId: 'selfCheckSigns',
            relatedSolveIds: ['disrupted_routine'],
            relatedTool: { id: 'self_check', label: 'Open Self-check', action: 'self_check' }
        },
        {
            id: 'stress_loop',
            type: 'learn',
            badge: '🧠 Stress Education · Topic',
            icon: '🔁',
            title: 'The stress loop',
            shortDescription: 'How stress feeds on itself, and how interrupting one link breaks the chain.',
            contentParagraphs: [
                'Stress frequently traps students in self-reinforcing behavioral loops. A heavy workload causes worry, leading to late-night cramming. Lack of sleep causes fatigue, which impairs cognitive focus the next day, slowing down work output and generating even more stress.'
            ],
            hasVisualLoop: true,
            loopNodes: [
                { label: 'Deadline pile-up', icon: '⏰' },
                { label: 'Stress / Panic', icon: '⚡' },
                { label: 'Stay up late to work', icon: '🌙' },
                { label: 'Tired & hard to focus', icon: '😴' },
                { label: 'Work slows down', icon: '⏳' },
                { label: 'More stress', icon: '💥' }
            ],
            keyTakeaway: 'You do not need to change everything all at once. Recognizing the loop and interrupting it at just ONE point (e.g. going to sleep on time or taking one 10-minute walk) breaks the compounding momentum.',
            tipId: 'interruptTheLoop',
            relatedSolveIds: ['deadline_pileup'],
            relatedTool: { id: 'quick_relief', label: 'Open Quick Relief', action: 'quick_relief' },
            relatedMode: { mode: 'recovery', label: 'Go to Recovery Mode' }
        },
        {
            id: 'recovery',
            type: 'learn',
            badge: '🧠 Stress Education · Topic',
            icon: '🌱',
            title: 'Recovery is part of stress management',
            shortDescription: 'Why stress does not end the moment a deadline passes, and why recovery is essential.',
            contentParagraphs: [
                'Have you ever submitted a major assignment or finished your last final exam, only to feel drained, irritable, or catch a cold immediately after?',
                'Finishing the stressful event does not mean your body’s stress response turns off like a light switch. Elevated cortisol and adrenaline take time to metabolize, and your autonomic nervous system requires deliberate rest to re-establish homeostatic balance.',
                'Recovery is not wasted time, laziness, or procrastination. It is an active biological and psychological process where neural connections solidify, emotional resilience restores, and cognitive clarity returns.',
                'Recovery Mode in Tempo is designed specifically for this phase: giving you space to slow things down, check in with yourself, and notice what truly helps.'
            ],
            tipId: 'stabilizeOneThing',
            relatedSolveIds: ['grades'],
            relatedTool: { id: 'breathing', label: 'Start Breathing', action: 'breathing' },
            relatedMode: { mode: 'recovery', label: 'Go to Recovery Mode' }
        },
        {
            id: 'academic_burnout',
            type: 'learn',
            badge: '🧠 Stress Education · Topic',
            icon: '🪫',
            title: 'Academic burnout',
            shortDescription: 'Understanding prolonged exhaustion, cynicism, and reduced efficacy.',
            contentParagraphs: [
                'Academic burnout is not ordinary tiredness after a late night. It is a state of chronic physical and emotional depletion brought on by prolonged academic pressure without adequate recovery opportunity.',
                'Research generally describes academic burnout through three distinct dimensions:'
            ],
            burnoutDimensions: [
                {
                    icon: '🪫',
                    name: 'Exhaustion',
                    detail: 'A chronic state of physical, cognitive, and emotional fatigue where normal sleep no longer restores your energy.'
                },
                {
                    icon: '📚',
                    name: 'Disengagement & Cynicism',
                    detail: 'Developing a detached, cynical, or resentful attitude toward coursework, professors, and academic goals that used to matter to you.'
                },
                {
                    icon: '📉',
                    name: 'Reduced Sense of Efficacy',
                    detail: 'A persistent feeling that your efforts are pointless, you are ineffective, and nothing you accomplish truly counts.'
                }
            ],
            nonDiagnosticNote: 'You do not need to determine whether you are "just stressed" or "already burned out" before paying attention to your wellbeing. Recognizing these signs is an invitation to pause, adjust your workload, and seek support.',
            tipId: 'goodEnoughBeforePerfect',
            relatedSolveIds: ['too_many_responsibilities'],
            relatedMode: { mode: 'recovery', label: 'Go to Recovery Mode' }
        },
        {
            id: 'stress_eating',
            type: 'learn',
            badge: '🧠 Stress Education · Topic',
            icon: '🥣',
            title: 'Stress eating',
            shortDescription: 'A compassionate, non-shaming approach to eating when stressed.',
            contentParagraphs: [
                'Reaching for food when stressed is a completely understandable physiological and emotional reflex. Under chronic stress, cortisol stimulates cravings for energy-dense carbohydrates, while eating triggers a temporary dopamine release that temporarily soothes emotional distress.',
                'Here is a compassionate, non-shaming way to handle stress eating:'
            ],
            steps: [
                {
                    heading: 'Check if you are hungry, stressed, or both',
                    detail: 'If you are physically hungry, your body needs nourishment. Eat a proper meal without self-criticism.'
                },
                {
                    heading: 'Create a brief 60-second pause',
                    detail: 'Drink a glass of water, take five deep breaths, or step away from your desk for one minute. A short pause creates space to notice what you are really feeling.'
                },
                {
                    heading: 'No moral judgment or failure mindset',
                    detail: 'If you still choose to eat, treat yourself with kindness. Food restriction and guilt only create more stress, fueling the exact loop you are trying to break.'
                },
                {
                    heading: 'Return to the stressor when settled',
                    detail: 'Once you feel slightly more grounded, return to your work with a smaller first step.'
                }
            ],
            tipId: 'pauseBeforeSnack',
            relatedSolveIds: ['disrupted_routine'],
            relatedTool: { id: 'quick_relief', label: 'Open Quick Relief', action: 'quick_relief' }
        },
        {
            id: 'what_do_i_need',
            type: 'learn',
            badge: '🧠 Stress Education · Topic',
            icon: '🧭',
            title: 'What do I need when I’m stressed?',
            shortDescription: 'Matching your current stress experience to the right Tempo space.',
            contentParagraphs: [
                'Stress manifests in different ways, and what you need depends on where you find yourself right now:'
            ],
            routingOptions: [
                {
                    condition: 'Too overwhelmed or panicking to think clearly?',
                    actionText: 'Settle your nervous system first with Quick Stress Relief or 2-minute Box Breathing.',
                    btnLabel: 'Open Quick Relief',
                    actionKey: 'quick_relief'
                },
                {
                    condition: 'Know exactly what situation is causing stress?',
                    actionText: 'Browse Solve a Situation for tactical, realistic step-by-step action plans.',
                    btnLabel: 'Explore Situations',
                    actionKey: 'switch_to_solve'
                },
                {
                    condition: 'Problem has passed but you still don’t feel okay?',
                    actionText: 'Enter Recovery Mode to decompress, track your daily baseline, and rest.',
                    btnLabel: 'Go to Recovery Mode',
                    actionKey: 'mode_recovery'
                },
                {
                    condition: 'Something feels off but you don’t clearly know why?',
                    actionText: 'Use Unclear Mode for a calm, guided reflection check-in to narrow it down.',
                    btnLabel: 'Go to Unclear Mode',
                    actionKey: 'mode_unclear'
                },
                {
                    condition: 'There is a pressing problem that needs concrete handling now?',
                    actionText: 'Enter Urgent Mode to triage urgent tasks and build a workable timeline.',
                    btnLabel: 'Go to Urgent Mode',
                    actionKey: 'mode_emergency'
                }
            ],
            tipId: 'startSmall',
            relatedTool: { id: 'quick_relief', label: 'Open Quick Relief', action: 'quick_relief' },
            relatedMode: { mode: 'emergency', label: 'Go to Urgent Mode' }
        },
        {
            id: 'support_seeking',
            type: 'learn',
            badge: '🧠 Stress Education · Topic',
            icon: '🤝',
            title: 'When should I seek more support?',
            shortDescription: 'Descriptive indicators that additional appropriate support is worth considering.',
            contentParagraphs: [
                'Self-management tools and personal strategies are valuable, but university challenges are not meant to be navigated in total isolation.',
                'Descriptive signs that additional support may be worth considering:'
            ],
            descriptiveList: [
                { title: 'Stress continues unrelieved', detail: 'Stress persists across multiple weeks and normal restful weekends do not relieve it.' },
                { title: 'Physical health impacts', detail: 'Eating, sleep quality, or daily energy levels are consistently and clearly disrupted.' },
                { title: 'Declining daily functioning', detail: 'Studying, attending lectures, or everyday tasks feel increasingly difficult to sustain.' },
                { title: 'Usual approaches stop working', detail: 'Techniques and habits that previously helped you cope no longer seem effective.' }
            ],
            supportConclusion: 'Reaching out to campus wellbeing coordinators, academic advisors, or peer counselors is a proactive sign of self-advocacy. (Note: For immediate safety emergencies, Tempo’s global SOS remains accessible at all times).',
            tipId: 'containTheWorry',
            relatedSolveIds: ['loneliness'],
            relatedTool: { id: 'support_page', label: 'Explore Support Options', action: 'support_page' }
        }
    ];

    // =========================================================================
    // 4. COMPONENT STATE & NAVIGATION STACK
    // =========================================================================
    let activeTab = 'solve'; // 'solve' | 'learn'
    let activeCategory = 'study'; // 'study' | 'future' | 'work' | 'relationships' | 'life'
    let modalNavStack = []; // ['item_id_1', 'item_id_2']

    // =========================================================================
    // 5. HELPER RENDERING FUNCTIONS
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

    function renderTipCalloutHTML(tipId) {
        const tip = TEMPO_TIPS[tipId];
        if (!tip) return '';
        return `
            <div class="tempo-tip-callout p-4 sm:p-5 rounded-2xl bg-[#FFF8F3] border border-[#FFD2BA] space-y-1.5 shadow-2xs text-left">
                <div class="flex items-center space-x-1.5 text-[10px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">
                    <span>💡</span>
                    <span>TEMPO TIP</span>
                </div>
                <h5 class="text-xs sm:text-sm font-bold text-[#202124] leading-snug">${escapeHTML(tip.title)}</h5>
                <p class="text-xs text-[#6F6B68] leading-relaxed">${escapeHTML(tip.text)}</p>
            </div>
        `;
    }

    // =========================================================================
    // 6. SHARED SECTION HTML GENERATOR
    // =========================================================================
    function renderSectionHTML() {
        const isSolve = activeTab === 'solve';
        const isLearn = activeTab === 'learn';

        return `
            <div id="tempo-learn-solve-section" class="space-y-6 pt-2">
                <!-- Section Header -->
                <div class="space-y-1 text-left">
                    <div class="flex items-center space-x-2">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">LIBRARY &amp; GUIDES</span>
                    </div>
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124] tracking-tight">
                        Learn &amp; Solve
                    </h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed max-w-xl">
                        Sometimes you need a practical way forward. Sometimes you just want to understand what's happening.
                    </p>
                </div>

                <!-- Primary Two Cards (Interactive Selectors) -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <!-- Card 1: Solve a Situation -->
                    <div onclick="window.TempoLearnSolve.selectTab('solve')"
                         role="button"
                         tabindex="0"
                         onkeydown="if(event.key==='Enter'||event.key===' '){window.TempoLearnSolve.selectTab('solve');}"
                         class="p-6 rounded-3xl border-2 transition cursor-pointer flex flex-col justify-between space-y-4 shadow-2xs text-left ${
                             isSolve
                                 ? 'border-[#FF6B2C] bg-gradient-to-br from-white to-[#FFF9F5] ring-2 ring-[#FFD2BA]'
                                 : 'border-[#EAE4DF] bg-white hover:border-[#FFD2BA]'
                         }">
                        <div class="space-y-2">
                            <div class="w-10 h-10 rounded-2xl bg-[#FFE9DC] text-[#B83D08] flex items-center justify-center text-lg font-bold shadow-xs">
                                🧩
                            </div>
                            <h4 class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">
                                Solve a Situation
                            </h4>
                            <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                                Something specific is stressing you out? Find realistic, actionable steps close to what you're dealing with.
                            </p>
                        </div>
                        <div class="pt-2 flex items-center justify-between">
                            <span class="text-xs font-bold ${isSolve ? 'text-[#B83D08]' : 'text-[#FF6B2C]'} flex items-center space-x-1">
                                <span>${isSolve ? 'Exploring situations' : 'Explore situations'}</span>
                                <span>→</span>
                            </span>
                            ${isSolve ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-[#FFE9DC] text-[#B83D08]">ACTIVE</span>` : ''}
                        </div>
                    </div>

                    <!-- Card 2: Learn about Stress -->
                    <div onclick="window.TempoLearnSolve.selectTab('learn')"
                         role="button"
                         tabindex="0"
                         onkeydown="if(event.key==='Enter'||event.key===' '){window.TempoLearnSolve.selectTab('learn');}"
                         class="p-6 rounded-3xl border-2 transition cursor-pointer flex flex-col justify-between space-y-4 shadow-2xs text-left ${
                             isLearn
                                 ? 'border-[#7E22CE] bg-gradient-to-br from-white to-[#FAF5FF] ring-2 ring-[#E9D5FF]'
                                 : 'border-[#EAE4DF] bg-white hover:border-[#E9D5FF]'
                         }">
                        <div class="space-y-2">
                            <div class="w-10 h-10 rounded-2xl bg-[#FAF5FF] text-[#7E22CE] flex items-center justify-center text-lg font-bold shadow-xs">
                                🧠
                            </div>
                            <h4 class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">
                                Learn about Stress
                            </h4>
                            <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                                Understand stress, how it can show up, the stress loop, and what to notice over time.
                            </p>
                        </div>
                        <div class="pt-2 flex items-center justify-between">
                            <span class="text-xs font-bold ${isLearn ? 'text-[#7E22CE]' : 'text-[#9333EA]'} flex items-center space-x-1">
                                <span>${isLearn ? 'Browsing topics' : 'Start learning'}</span>
                                <span>→</span>
                            </span>
                            ${isLearn ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-[#FAF5FF] text-[#7E22CE]">ACTIVE</span>` : ''}
                        </div>
                    </div>
                </div>

                <!-- Sub-options Container -->
                <div id="learn-solve-subcontent" class="space-y-5 pt-1">
                    ${isSolve ? renderSolveSubcontentHTML() : renderLearnSubcontentHTML()}
                </div>
            </div>
        `;
    }

    // --- SOLVE SUB-CONTENT ---
    function renderSolveSubcontentHTML() {
        const catObj = SOLVE_CATEGORIES.find(c => c.key === activeCategory) || SOLVE_CATEGORIES[0];
        const situations = SOLVE_SITUATIONS.filter(s => s.category === activeCategory);

        return `
            <div class="space-y-4">
                <!-- Category Controls -->
                <div class="flex items-center justify-between flex-wrap gap-2 pt-2 border-t border-stone-100">
                    <span class="text-xs font-bold text-stone-500 uppercase tracking-wider">CHOOSE A LIFE AREA:</span>
                    <div class="flex flex-wrap gap-2" role="tablist">
                        ${SOLVE_CATEGORIES.map(cat => {
                            const isSelected = activeCategory === cat.key;
                            return `
                                <button type="button"
                                        role="tab"
                                        aria-selected="${isSelected}"
                                        onclick="window.TempoLearnSolve.selectCategory('${cat.key}')"
                                        class="px-3.5 py-1.5 rounded-full text-xs font-semibold transition cursor-pointer flex items-center space-x-1.5 ${
                                            isSelected
                                                ? 'bg-[#FF6B2C] text-white shadow-xs'
                                                : 'bg-stone-100 text-stone-600 hover:bg-stone-200 hover:text-stone-900'
                                        }">
                                    <span>${cat.icon}</span>
                                    <span>${escapeHTML(cat.label)}</span>
                                </button>
                            `;
                        }).join('')}
                    </div>
                </div>

                <!-- Situations Subcards Grid -->
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5 pt-1">
                    ${situations.map(sit => {
                        return `
                            <div onclick="window.TempoLearnSolve.openModal('${sit.id}')"
                                 role="button"
                                 tabindex="0"
                                 onkeydown="if(event.key==='Enter'||event.key===' '){window.TempoLearnSolve.openModal('${sit.id}');}"
                                 class="p-4 sm:p-5 rounded-2xl border border-[#EAE4DF] bg-white hover:border-[#FF6B2C] hover:shadow-xs transition cursor-pointer flex flex-col justify-between space-y-3 text-left">
                                <div class="space-y-1.5">
                                    <div class="flex items-center space-x-2">
                                        <span class="text-base">${sit.icon}</span>
                                        <h5 class="font-heading text-xs sm:text-sm font-bold text-[#202124] leading-snug">
                                            ${escapeHTML(sit.title)}
                                        </h5>
                                    </div>
                                    <p class="text-xs text-[#6F6B68] leading-relaxed line-clamp-2">
                                        ${escapeHTML(sit.shortDescription)}
                                    </p>
                                </div>
                                <div class="pt-1 flex items-center justify-between text-xs font-bold text-[#FF6B2C]">
                                    <span>View solution</span>
                                    <span>→</span>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

    // --- LEARN SUB-CONTENT ---
    function renderLearnSubcontentHTML() {
        return `
            <div class="space-y-4">
                <div class="pt-2 border-t border-stone-100 flex items-center justify-between">
                    <span class="text-xs font-bold text-stone-500 uppercase tracking-wider">STRESS EDUCATION TOPICS:</span>
                    <span class="text-xs text-stone-400 font-medium">9 essential topics</span>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5 pt-1">
                    ${LEARN_TOPICS.map(top => {
                        return `
                            <div onclick="window.TempoLearnSolve.openModal('${top.id}')"
                                 role="button"
                                 tabindex="0"
                                 onkeydown="if(event.key==='Enter'||event.key===' '){window.TempoLearnSolve.openModal('${top.id}');}"
                                 class="p-4 sm:p-5 rounded-2xl border border-[#EAE4DF] bg-white hover:border-[#7E22CE] hover:shadow-xs transition cursor-pointer flex flex-col justify-between space-y-3 text-left">
                                <div class="space-y-1.5">
                                    <div class="flex items-center space-x-2">
                                        <span class="text-base">${top.icon}</span>
                                        <h5 class="font-heading text-xs sm:text-sm font-bold text-[#202124] leading-snug">
                                            ${escapeHTML(top.title)}
                                        </h5>
                                    </div>
                                    <p class="text-xs text-[#6F6B68] leading-relaxed line-clamp-2">
                                        ${escapeHTML(top.shortDescription)}
                                    </p>
                                </div>
                                <div class="pt-1 flex items-center justify-between text-xs font-bold text-[#7E22CE]">
                                    <span>Start topic</span>
                                    <span>→</span>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

    // =========================================================================
    // 7. CONTENT MODAL SYSTEM & NAVIGATION STACK
    // =========================================================================
    function ensureModalMounted() {
        if (document.getElementById('tempo-learn-solve-modal')) return;

        const modalDiv = document.createElement('div');
        modalDiv.id = 'tempo-learn-solve-modal';
        modalDiv.className = 'fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-3 sm:p-6 overflow-y-auto hidden';
        modalDiv.setAttribute('role', 'dialog');
        modalDiv.setAttribute('aria-modal', 'true');
        modalDiv.innerHTML = `
            <div id="tempo-learn-solve-modal-card" class="tempo-card max-w-2xl w-full my-auto bg-white rounded-3xl p-6 sm:p-8 space-y-6 relative shadow-2xl border border-[#EAE4DF] text-left max-h-[90vh] overflow-y-auto">
                <!-- Modal Body will be dynamically rendered -->
            </div>
        `;
        document.body.appendChild(modalDiv);

        // Click outside backdrop to close
        modalDiv.addEventListener('click', (e) => {
            if (e.target === modalDiv) {
                closeModal();
            }
        });

        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !modalDiv.classList.contains('hidden')) {
                closeModal();
            }
        });
    }

    