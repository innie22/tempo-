/**
 * Tempo Shared Ecosystem — Phase 2: Learn & Solve Library
 * 
 * Reusable shared component providing two distinct content experiences:
 * 1. 🧩 SOLVE A SITUATION: Practical, situation-driven guidance organized by life/study taxonomy
 * 2. 🧠 LEARN ABOUT STRESS: Foundational, non-diagnostic stress education concepts
 * 3. 💡 TEMPO TIPS: Centralized, reusable micro-content callouts
 * 
 * Core principles:
 * - One shared feature with two content experiences
 * - Reusable content modal with in-modal history navigation stack
 * - Natural cross-linking between Learn <-> Solve <-> Tempo Tools <-> Modes
 * - Strict non-diagnostic, non-clinical, non-evaluative boundaries
 * - Does not auto-switch modes; preserves existing auth/pendingMode gating
 * - Does not auto-trigger SOS
 */

window.TempoLearnSolve = (function() {
    'use strict';

    // =========================================================================
    // 1. REUSABLE MICRO-CONTENT: TEMPO TIPS
    // =========================================================================
    const TEMPO_TIPS = {
        startSmall: {
            id: 'startSmall',
            title: 'Start Smaller Than You Think',
            text: 'Having trouble starting? Lower the bar. Commit to just 5 minutes or writing a single sentence. Overcoming initial friction is all that matters.'
        },
        goodEnoughBeforePerfect: {
            id: 'goodEnoughBeforePerfect',
            title: 'Good Enough Before Perfect',
            text: "Stuck aiming for perfection? Aim for 'good enough to submit' first. Revision is always easier than creating from a blank page."
        },
        containTheWorry: {
            id: 'containTheWorry',
            title: 'Contain the Worry Loop',
            text: 'Thoughts looping about a conflict or worry? Write down the core issue, schedule a specific time tomorrow to address it, and gently park it for now.'
        },
        interruptTheLoop: {
            id: 'interruptTheLoop',
            title: 'Interrupt Just One Link',
            text: "Caught in a stress loop? You don't have to fix everything today. Change just one link — like sleeping an extra hour or doing one 5-minute reset."
        },
        selfCheckSigns: {
            id: 'selfCheckSigns',
            title: 'Notice Early Signals',
            text: "Notice your body's early stress signals? Tracking repeated signs in Self-check helps you catch overload before exhaustion sets in."
        },
        breathingBeforeAction: {
            id: 'breathingBeforeAction',
            title: 'Calm the Adrenaline Surge',
            text: "Heart racing before speaking or presenting? Two minutes of box breathing directly activates your body's calming parasympathetic reflex."
        },
        pauseBeforeSnack: {
            id: 'pauseBeforeSnack',
            title: 'Create a 60-Second Pause',
            text: 'Reaching for food when stressed? Pause for 60 seconds with a glass of water to notice if your body needs fuel, rest, or emotional relief.'
        },
        stabilizeOneThing: {
            id: 'stabilizeOneThing',
            title: 'Anchor Just One Routine',
            text: "Routine feeling chaotic? Don't overhaul your whole life at once. Anchor just one simple habit — like a fixed wake-up time or drinking a glass of water each morning."
        }
    };

    // =========================================================================
    // 2. SOLVE TAXONOMY & SITUATIONS
    // =========================================================================
    const SOLVE_CATEGORIES = [
        { key: 'study', label: 'Study', icon: '📚' },
        { key: 'future', label: 'Myself & Future', icon: '💭' },
        { key: 'work', label: 'Work & Activities', icon: '💼' },
        { key: 'relationships', label: 'Relationships', icon: '🤝' },
        { key: 'life', label: 'Life', icon: '🌿' }
    ];

    const SOLVE_SITUATIONS = [
        // --- 📚 Study ---
        {
            id: 'deadline_pileup',
            category: 'study',
            type: 'solve',
            badge: '📚 Study · Situation',
            icon: '⏰',
            title: 'Deadline pile-up',
            shortDescription: 'Multiple deadlines crowding together, making it hard to know where to begin.',
            context: 'When multiple assignments, problem sets, or reports cluster in the same week, your brain easily treats the entire workload as an imminent, single threat. This triggers a freeze response where starting anything feels futile.',
            steps: [
                {
                    heading: 'Lower friction with the 5-Minute Rule',
                    detail: 'Do not commit to finishing the entire assignment right now. Commit only to working on the most approachable task for 300 seconds. Overcoming inertia is the only goal of minute one.'
                },
                {
                    heading: 'Triage into three concrete buckets',
                    detail: 'Bucket 1: Must submit today. Bucket 2: Can be negotiated, postponed with an email, or completed with a passing standard. Bucket 3: Tasks to handle once immediate pressure clears.'
                },
                {
                    heading: 'Protect single-task focus blocks',
                    detail: 'Tab switching wastes cognitive energy. Close all other project files and protect one 45-minute focus session on your single highest-priority task.'
                }
            ],
            tipId: 'startSmall',
            relatedLearnIds: ['stress_loop'],
            relatedTool: { id: 'focus_zone', label: 'Open Focus Zone', action: 'focus_zone' },
            relatedMode: { mode: 'emergency', label: 'Go to Urgent Mode' }
        },
        {
            id: 'falling_behind',
            category: 'study',
            type: 'solve',
            badge: '📚 Study · Situation',
            icon: '📖',
            title: 'Falling behind / not keeping up',
            shortDescription: 'Struggling to keep pace with lecture material, required readings, or lab work.',
            context: 'Falling behind can happen gradually until a syllabus checkpoint makes the gap feel alarming. How you respond depends on how close the assessment is.',
            caseDistinctions: [
                {
                    caseTitle: 'Case A: Exam is close and I don’t understand the material',
                    items: [
                        'Triage high-yield concepts: Stop attempting to read textbook chapters sequentially from page 1. Focus on syllabus weightings, lecture summary slides, and past exam themes.',
                        'Seek immediate peer or TA guidance: Bring 1–2 specific problem questions to office hours or ask a classmate to explain core formulas.',
                        'Focus on passing essentials: Master fundamental concepts that guarantee baseline points before tackling difficult edge cases.'
                    ]
                },
                {
                    caseTitle: 'Case B: Mid-semester and I’m starting to lose track',
                    items: [
                        'Conduct a calm audit: List missing lectures and unread modules without self-criticism. An honest inventory reduces imagined dread.',
                        'Schedule catch-up blocks incrementally: Add one dedicated 45-minute catch-up sprint per day rather than burning out on an unsustainable all-nighter.',
                        'Reach out early: Contact your course coordinator or TA to ask which foundational modules are most vital for upcoming topics.'
                    ]
                }
            ],
            tipId: 'goodEnoughBeforePerfect',
            relatedLearnIds: ['academic_burnout'],
            relatedTool: { id: 'focus_zone', label: 'Open Focus Zone', action: 'focus_zone' },
            relatedMode: { mode: 'emergency', label: 'Go to Urgent Mode' }
        },
        {
            id: 'teamwork',
            category: 'study',
            type: 'solve',
            badge: '📚 Study · Situation',
            icon: '👥',
            title: 'Teamwork problems',
            shortDescription: 'Unbalanced workload, unresponsive group members, or communication friction.',
            context: 'Group projects are a major source of university stress because your grade is tied to others whose communication styles and accountability differ from your own.',
            caseDistinctions: [
                {
                    caseTitle: 'Case A: Deadline is already close',
                    items: [
                        'Define the Minimum Viable Submission: Convene a quick standup to clarify what essential parts must be submitted to earn credit.',
                        'Divide remaining work with hard cutoffs: Assign discrete sections with firm submission times so one missing piece does not stall the entire project.',
                        'Notify your instructor with documentation: If a team member has completely disappeared, send a factual, respectful email detailing completed components and seeking guidance.'
                    ]
                },
                {
                    caseTitle: 'Case B: Problem noticed early in the semester',
                    items: [
                        'Establish explicit milestone dates: Agree on draft deadlines at least 48 hours before the final due date to allow room for editing.',
                        'Clarify individual ownership: Ensure every team member has specific deliverables rather than vague shared responsibilities.',
                        'Schedule brief weekly checkpoints: A 10-minute weekly check-in surfaces blockers before resentment builds.'
                    ]
                }
            ],
            tipId: 'containTheWorry',
            relatedLearnIds: ['what_is_stress'],
            relatedTool: { id: 'quick_relief', label: 'Open Quick Relief', action: 'quick_relief' }
        },
        {
            id: 'grades',
            category: 'study',
            type: 'solve',
            badge: '📚 Study · Situation',
            icon: '📊',
            title: 'Grades didn’t go as expected',
            shortDescription: 'Coping with academic disappointment and extracting constructive next steps.',
            context: 'A disappointing grade often triggers acute feelings of inadequacy, making you question your intelligence, major, or future trajectory.',
            steps: [
                {
                    heading: 'Take a 24-hour emotional cooling pause',
                    detail: 'Avoid firing off an emotional email to your professor immediately. Allow physiological stress hormones to subside so you can review feedback objectively.'
                },
                {
                    heading: 'Separate academic execution from self-worth',
                    detail: 'A grade evaluates your preparation strategy and execution on one specific day. It is an evaluation of an artifact, not an assessment of your human value or potential.'
                },
                {
                    heading: 'Review specific criteria and rubric notes',
                    detail: 'Analyze where marks were lost: conceptual misunderstandings, exam pacing, or formatting. Concrete gaps are solvable problems.'
                },
                {
                    heading: 'Schedule an office hours feedback conversation',
                    detail: 'Approach instructors with a learning mindset: "I want to improve on the next paper. Could you help me understand how to strengthen my analytical arguments?"'
                }
            ],
            tipId: 'goodEnoughBeforePerfect',
            relatedLearnIds: ['recovery'],
            relatedTool: { id: 'breathing', label: 'Start Breathing', action: 'breathing' },
            relatedMode: { mode: 'recovery', label: 'Go to Recovery Mode' }
        },
        {
            id: 'presentation_anxiety',
            category: 'study',
            type: 'solve',
            badge: '📚 Study · Situation',
            icon: '🎤',
            title: 'Presentation anxiety',
            shortDescription: 'Intense nervousness, racing heartbeat, or dread before speaking in front of peers.',
            context: 'Speaking before an audience activates our evolutionary fear of social rejection, releasing adrenaline that causes rapid breathing, trembling, and mental fog.',
            steps: [
                {
                    heading: 'Reset physiology with extended exhales',
                    detail: 'When your exhale is longer than your inhale (e.g. 4 seconds in, 6 seconds out), the vagus nerve triggers parasympathetic slowing of your heart rate.'
                },
                {
                    heading: 'Over-learn the opening two minutes',
                    detail: 'Anxiety peaks in the first 120 seconds of speaking and naturally subsides as habituation kicks in. Rehearse your first 2 minutes until they are automatic.'
                },
                {
                    heading: 'Reframe physical arousal as readiness',
                    detail: 'A rapid pulse is your body preparing oxygen and glucose to help you focus, not proof that you are going to freeze or fail.'
                }
            ],
            tipId: 'breathingBeforeAction',
            relatedLearnIds: ['stress_signs'],
            relatedTool: { id: 'breathing', label: 'Start Breathing', action: 'breathing' }
        },
        {
            id: 'cant_focus',
            category: 'study',
            type: 'solve',
            badge: '📚 Study · Situation',
            icon: '🧠',
            title: 'Can’t focus / can’t get started',
            shortDescription: 'Staring at a blank screen, experiencing brain fog, or feeling paralyzed by inertia.',
            context: 'When mental fatigue is high or an assignment feels too ambiguous, executive function stumbles. The brain seeks instant dopamine from phone notifications instead.',
            steps: [
                {
                    heading: 'Strip sensory distractions',
                    detail: 'Place your phone in another room or inside your bag. Close all irrelevant browser tabs. Visual clutter competes directly for working memory.'
                },
                {
                    heading: 'Pick a trivial mechanical micro-task',
                    detail: 'Instead of "write the introduction", start by pasting the assignment rubric into the document, creating title headers, or formatting citations.'
                },
                {
                    heading: 'Work in bounded rhythm sprints',
                    detail: 'Tell yourself you only need to work until the next short break. Knowing rest is guaranteed removes internal resistance to starting.'
                }
            ],
            tipId: 'startSmall',
            relatedLearnIds: ['stress_loop'],
            relatedTool: { id: 'focus_zone', label: 'Open Focus Zone', action: 'focus_zone' }
        },

        // --- 💭 Myself & Future ---
        {
            id: 'future_uncertainty',
            category: 'future',
            type: 'solve',
            badge: '💭 Myself & Future · Situation',
            icon: '🧭',
            title: 'Unsure about direction / future',
            shortDescription: 'Worrying about career choices, major selection, or feeling behind peers.',
            context: 'University often fosters an unspoken expectation that you must have a 10-year career trajectory locked down, creating chronic background anxiety.',
            steps: [
                {
                    heading: 'Shrink the question',
                    detail: 'You do not need to resolve your entire life today. Shrink the question from "What is my lifelong career?" to "What is the single next course or skill I want to explore next term?"'
                },
                {
                    heading: 'Distinguish "I don’t know yet" from "I must know now"',
                    detail: 'Not knowing is normal and healthy during academic exploration. Ask yourself: does an irreversible decision actually need to be made before Friday?'
                },
                {
                    heading: 'Gather low-stakes information when decisions arise',
                    detail: 'Instead of ruminating in isolation, schedule a casual 15-minute coffee chat with an alumnus, visit career advising, or skim entry-level job descriptions.'
                }
            ],
            tipId: 'startSmall',
            relatedLearnIds: ['what_is_stress'],
            relatedMode: { mode: 'unclear', label: 'Go to Unclear Mode' }
        },
        {
            id: 'not_good_enough',
            category: 'future',
            type: 'solve',
            badge: '💭 Myself & Future · Situation',
            icon: '🪞',
            title: 'Feeling "not good enough"',
            shortDescription: 'Persistent self-doubt, imposter syndrome, and feeling like an academic fraud.',
            context: 'Imposter syndrome convinces us that our achievements are mere luck, while any temporary struggle is definitive proof of inadequacy.',
            steps: [
                {
                    heading: 'Check the concrete evidence',
                    detail: 'Separate emotional reasoning from objective facts. You met admission standards, completed prerequisite coursework, and earned your place here. Feelings are real, but they are not facts.'
                },
                {
                    heading: 'Ask for specific, objective feedback',
                    detail: 'Instead of seeking general reassurance ("Am I doing okay?"), ask for targeted feedback on specific work ("How can I sharpen my thesis statement?"). Specific critique is actionable.'
                },
                {
                    heading: 'Choose one concrete craft area to improve',
                    detail: 'Replace global self-judgments ("I am bad at university") with concrete skills ("I want to practice time budgeting during 50-minute exams").'
                }
            ],
            tipId: 'goodEnoughBeforePerfect',
            relatedLearnIds: ['academic_burnout'],
            relatedTool: { id: 'quick_relief', label: 'Open Quick Relief', action: 'quick_relief' }
        },
        {
            id: 'expectations_pressure',
            category: 'future',
            type: 'solve',
            badge: '💭 Myself & Future · Situation',
            icon: '⚖️',
            title: 'Pressure from expectations of myself',
            shortDescription: 'Perfectionism, harsh internal standards, and fear of disappointing yourself.',
            context: 'High personal standards can drive growth, but when infected by perfectionism, any human mistake triggers severe self-criticism.',
            steps: [
                {
                    heading: 'Distinguish high standards from punitive perfectionism',
                    detail: 'Healthy standards strive for quality while accepting human limitations. Perfectionism demands flawless output under every circumstance and punishes rest.'
                },
                {
                    heading: 'Aim for sufficiency first ("Good enough before perfect")',
                    detail: 'Strive for an 80% draft that is completed in reasonable time rather than chasing a mythical 100% that drains your health.'
                },
                {
                    heading: 'Enforce an unconditional stopping boundary',
                    detail: 'Diminishing returns set in late at night. Set a firm hour where studying ends, giving your brain permission to transition into recovery.'
                }
            ],
            tipId: 'goodEnoughBeforePerfect',
            relatedLearnIds: ['recovery'],
            relatedMode: { mode: 'recovery', label: 'Go to Recovery Mode' }
        },
        {
            id: 'comparing_others',
            category: 'future',
            type: 'solve',
            badge: '💭 Myself & Future · Situation',
            icon: '👥',
            title: 'Comparing myself with other people',
            shortDescription: 'Feeling inadequate when observing peers’ internships, grades, or active social lives.',
            context: 'Campus life constantly puts classmates on display looking competent and poised, triggering immediate comparison traps.',
            steps: [
                {
                    heading: 'Notice the comparison asymmetry',
                    detail: 'You are comparing your full, messy internal reality (doubts, fatigue, confusion) to other people’s curated public highlight reels.'
                },
                {
                    heading: 'Pause triggering social feeds',
                    detail: 'If scrolling LinkedIn or Instagram consistently leaves you feeling deficient, introduce a deliberate 7-day social media detox.'
                },
                {
                    heading: 'Re-anchor on your own starting baseline',
                    detail: 'Measure your progress strictly against where you were at the beginning of the semester, not against someone else’s trajectory.'
                }
            ],
            tipId: 'containTheWorry',
            relatedLearnIds: ['stress_signs'],
            relatedTool: { id: 'quick_relief', label: 'Open Quick Relief', action: 'quick_relief' }
        },

        // --- 💼 Work & Activities ---
        {
            id: 'too_many_responsibilities',
            category: 'work',
            type: 'solve',
            badge: '💼 Work & Activities · Situation',
            icon: '🎒',
            title: 'Too many responsibilities at once',
            shortDescription: 'Overloaded with study, part-time jobs, student clubs, and personal obligations.',
            context: 'Overload is frequently framed as a personal time-management flaw. In reality, some weekly commitments simply cannot mathematically fit into 168 hours.',
            steps: [
                {
                    heading: 'Create a single unified commitment inventory',
                    detail: 'Write down every obligation across classes, shifts, clubs, and personal life on one master sheet to see total weekly hour requirements.'
                },
                {
                    heading: 'Acknowledge mathematics over sheer willpower',
                    detail: 'If your required commitments add up to 80 hours a week outside of sleep and travel, better productivity cannot solve the deficit. Workload must be adjusted.'
                },
                {
                    heading: 'Proactively negotiate, adjust, or postpone',
                    detail: 'Step back temporarily from voluntary roles, speak to your workplace about temporary shift reductions, or request coursework extensions before you reach exhaustion.'
                }
            ],
            tipId: 'goodEnoughBeforePerfect',
            relatedLearnIds: ['academic_burnout'],
            relatedTool: { id: 'focus_zone', label: 'Open Focus Zone', action: 'focus_zone' },
            relatedMode: { mode: 'emergency', label: 'Go to Urgent Mode' }
        },

        // --- 🤝 Relationships ---
        {
            id: 'relationship_conflict',
            category: 'relationships',
            type: 'solve',
            badge: '🤝 Relationships · Situation',
            icon: '⚡',
            title: 'Conflict with someone important',
            shortDescription: 'Friction with a roommate, partner, friend, or family member draining mental energy.',
            context: 'Interpersonal discord activates deep social threat circuits, making it difficult to concentrate on academic work while arguments loop in your mind.',
            steps: [
                {
                    heading: 'Contain the problem boundary',
                    detail: 'Acknowledge that the conflict hurts, but consciously set an intentional boundary so it does not derail your entire study day.'
                },
                {
                    heading: 'Write down the core issues and park them',
                    detail: 'Write what you want to say in a private draft to get thoughts out of your head, then agree on a specific time to talk rather than exchanging reactive texts.'
                },
                {
                    heading: 'Redirect focus to tasks with clear boundaries',
                    detail: 'Engage in an activity with an unambiguous start and finish (e.g. solving 5 specific problem sets or taking a brisk walk) to break the mental rumination.'
                },
                {
                    heading: 'Talk to a trusted neutral person if thoughts loop',
                    detail: 'If conversations continue replaying endlessly, speak to a trusted friend or campus peer advisor to gain perspective.'
                }
            ],
            tipId: 'containTheWorry',
            relatedLearnIds: ['stress_signs'],
            relatedTool: { id: 'breathing', label: 'Start Breathing', action: 'breathing' }
        },
        {
            id: 'loneliness',
            category: 'relationships',
            type: 'solve',
            badge: '🤝 Relationships · Situation',
            icon: '🍂',
            title: 'Loneliness / feeling disconnected',
            shortDescription: 'Feeling isolated on campus, lacking belonging, or having no one to turn to.',
            context: 'Loneliness is exceptionally common among university students yet seldom discussed openly. It easily generates a false sense that everyone else belongs while you do not.',
            steps: [
                {
                    heading: 'Keep small, low-pressure connections',
                    detail: 'You do not need to plunge into large social gatherings. Send a short text to check in on an acquaintance, say hello to your barista, or study in a shared campus library.'
                },
                {
                    heading: 'Distinguish facts from catastrophic assumptions',
                    detail: '"I ate dinner alone tonight" is an objective fact. "Nobody cares about me" is an anxious assumption. Keep them separate.'
                },
                {
                    heading: 'Step away from passive social-media checking',
                    detail: 'Endlessly watching other people’s social stories when feeling lonely reinforces perceived exclusion and elevates sadness.'
                },
                {
                    heading: 'Notice when isolation impacts basic routines',
                    detail: 'If loneliness leads to skipping meals or staying in bed all day, treat it as a clear signal to connect with campus wellbeing resources.'
                }
            ],
            tipId: 'startSmall',
            relatedLearnIds: ['support_seeking'],
            relatedTool: { id: 'quick_relief', label: 'Open Quick Relief', action: 'quick_relief' }
        },

        // --- 🌿 Life ---
        {
            id: 'disrupted_routine',
            category: 'life',
            type: 'solve',
            badge: '🌿 Life · Situation',
            icon: '🔄',
            title: 'Daily routine has been disrupted for a while',
            shortDescription: 'Sleep schedule inverted, meals irregular, and everyday habits falling apart.',
            context: 'During heavy academic periods, daily self-care routines are often the first casualty. A disrupted routine is a common consequence of acute overload, not a personal failing.',
            steps: [
                {
                    heading: 'Stabilize ONE single anchor first',
                    detail: 'Do not attempt to overhaul your sleep, nutrition, exercise, and room cleaning all at once. Choose one anchor — like a consistent wake-up time or drinking a glass of water each morning.'
                },
                {
                    heading: 'Notice repeated changes without self-criticism',
                    detail: 'View routine changes as diagnostic feedback that your body is carrying too much stress, not as a character flaw.'
                },
                {
                    heading: 'Track patterns in Self-check',
                    detail: 'Use Recovery Self-check to quietly log sleep and energy patterns over time, identifying what simple adjustments help you decompress.'
                },
                {
                    heading: 'Consider additional support if daily functioning drops',
                    detail: 'If maintaining basic nutrition or hygiene continues to deteriorate across multiple weeks, reach out to campus wellbeing coordinators for support.'
                }
            ],
            tipId: 'stabilizeOneThing',
            relatedLearnIds: ['recovery'],
            relatedTool: { id: 'self_check', label: 'Open Self-check', action: 'self_check' },
            relatedMode: { mode: 'recovery', label: 'Go to Recovery Mode' }
        }
    ];

    // =========================================================================
    // 3. LEARN ABOUT STRESS TOPICS
    // =========================================================================
    function isViLocale() {
        if (window.TempoI18n && typeof window.TempoI18n.getLanguage === 'function') {
            return window.TempoI18n.getLanguage() === 'vi';
        }
        if (window.TempoI18n && typeof window.TempoI18n.getCurrentLanguage === 'function') {
            return window.TempoI18n.getCurrentLanguage() === 'vi';
        }
        return (localStorage.getItem('tempo_language') || localStorage.getItem('tempo_locale') || 'vi') === 'vi';
    }

    const TEMPO_TIPS_VI = {
        startSmall: {
            title: 'Bắt đầu nhỏ hơn bạn nghĩ',
            text: 'Gặp khó khăn khi bắt đầu? Hãy hạ thấp tiêu chuẩn. Cam kết chỉ làm trong 5 phút hoặc viết một câu duy nhất. Vượt qua sức ỳ ban đầu là tất cả những gì quan trọng.'
        },
        goodEnoughBeforePerfect: {
            title: 'Đủ tốt trước khi hoàn hảo',
            text: "Bị mắc kẹt vì muốn mọi thứ phải hoàn hảo? Hãy nhắm đến mức 'đủ tốt để nộp' trước. Chỉnh sửa luôn dễ dàng hơn nhiều so với việc bắt đầu từ một trang giấy trắng."
        },
        containTheWorry: {
            title: 'Khoanh vùng vòng lặp lo âu',
            text: 'Suy nghĩ cứ xoay quanh một mối lo hay mâu thuẫn? Hãy viết vấn đề cốt lõi ra giấy, lên lịch một giờ cụ thể vào ngày mai để giải quyết, và nhẹ nhàng gác nó lại lúc này.'
        },
        interruptTheLoop: {
            title: 'Ngắt chỉ một mắt xích',
            text: 'Bị kẹt trong vòng lặp căng thẳng? Bạn không cần phải sửa chữa mọi thứ ngay hôm nay. Chỉ cần thay đổi một mắt xích duy nhất — như ngủ thêm 1 tiếng hoặc thư giãn 5 phút.'
        },
        selfCheckSigns: {
            title: 'Nhận biết tín hiệu sớm',
            text: 'Nhận ra các dấu hiệu căng thẳng sớm của cơ thể? Theo dõi các dấu hiệu lặp lại trong Self-check giúp bạn phát hiện quá tải trước khi kiệt sức ập đến.'
        },
        breathingBeforeAction: {
            title: 'Làm dịu cơn tăng adrenaline',
            text: 'Tim đập nhanh trước khi phát biểu hoặc thuyết trình? Hai phút thở hộp sẽ kích hoạt trực tiếp phản xạ phó giao cảm giúp cơ thể bạn dịu lại.'
        },
        pauseBeforeSnack: {
            title: 'Tạo khoảng dừng 60 giây',
            text: 'Tìm đến đồ ăn khi căng thẳng? Hãy dừng lại 60 giây cùng một ly nước để nhận biết cơ thể bạn đang cần nạp năng lượng, cần nghỉ ngơi, hay cần xoa dịu cảm xúc.'
        },
        stabilizeOneThing: {
            title: 'Neo giữ một thói quen duy nhất',
            text: 'Sinh hoạt cảm thấy hỗn loạn? Đừng cố gắng thay đổi toàn bộ cuộc sống cùng lúc. Hãy neo giữ một thói quen đơn giản — như giờ thức dậy cố định hoặc uống một ly nước mỗi sáng.'
        }
    };

    const SOLVE_SITUATIONS_TITLES_VI = {
        deadline_pileup: 'Dồn dập deadline',
        falling_behind: 'Bị tụt lại phía sau',
        cant_focus: 'Không thể tập trung',
        perfectionism_paralysis: 'Tê liệt vì cầu toàn',
        disrupted_routine: 'Xáo trộn sinh hoạt',
        grades: 'Áp lực điểm số',
        too_many_responsibilities: 'Quá nhiều trách nhiệm',
        loneliness: 'Cảm giác cô đơn',
        teamwork_conflict: 'Mâu thuẫn bài tập nhóm',
        exam_anxiety: 'Lo âu trước kỳ thi'
    };

    const LEARN_TOPICS_VI = {
        what_is_stress: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Stress là gì?',
            shortDescription: 'Căng thẳng là trạng thái lo lắng hoặc áp lực tinh thần xuất phát từ một tình huống khó khăn. Đây là phản ứng tự nhiên của con người, giúp chúng ta đối mặt với những thử thách và mối đe dọa trong cuộc sống. Mỗi người đều trải qua căng thẳng ở một mức độ nhất định.',
            contentParagraphs: [
                'Stress không phải là bệnh lý, sự yếu đuối cá nhân hay khiếm khuyết tính cách. Đây là cơ chế sinh lý tiến hóa giúp tâm trí và cơ thể bạn chuẩn bị sẵn sàng đối mặt với thử thách và thích ứng với các yêu cầu.',
                'Khi bạn đối mặt với deadline căng thẳng, câu hỏi thi bất ngờ hoặc xung đột trong giao tiếp, não bộ sẽ kích hoạt hệ thần kinh giao cảm và trục HPA, giải phóng các hormone như adrenaline và cortisol. Tim bạn đập nhanh hơn, nhịp thở tăng lên và sự chú ý tập trung dồn vào nhiệm vụ trước mắt.',
                'Ở mức độ vừa phải và kiểm soát được, căng thẳng cấp tính rất hữu ích: nó huy động năng lượng, mài sắc sự tập trung và nâng cao trạng thái sẵn sàng. Mối lo ngại chỉ phát sinh khi căng thẳng trở nên quá mức, kéo dài liên tục hoặc thiếu cơ hội phục hồi phù hợp.'
            ],
            relatedToolLabel: 'Mở Giải tỏa nhanh'
        },
        stress_problem: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Khi nào căng thẳng trở thành vấn đề?',
            shortDescription: 'Sự khác biệt giữa chu kỳ căng thẳng lành mạnh và tình trạng quá tải mãn tính không dứt.',
            contentParagraphs: [
                'Trong điều kiện lành mạnh, căng thẳng diễn ra theo một chu kỳ tự nhiên: Áp lực → Căng thẳng → Hoàn thành → Nghỉ ngơi → Phục hồi. Khi điểm gây áp lực được giải quyết, hệ thần kinh sẽ tự điều hòa giảm xuống và trở về mức cân bằng ban đầu.',
                'Trong đời sống sinh viên, căng thẳng thường trở thành một vòng lặp không ngừng nghỉ: Deadline → Căng thẳng → Deadline tiếp theo → Căng thẳng → Dự án nhóm → Căng thẳng → Thi cử... Không có khoảng dừng để phục hồi, hệ thần kinh luôn ở trạng thái báo động cao liên tục.',
                'Điều quan trọng là thời gian kéo dài và việc thiếu phục hồi cũng đáng lo ngại tương đương với cường độ căng thẳng tức thời. Khi căng thẳng tiếp diễn mà không được giải tỏa, nó dần bào mòn 5 khía cạnh sinh hoạt hàng ngày:'
            ],
            descriptiveList: [
                { title: 'Giấc ngủ', detail: 'Khó đi vào giấc ngủ, hay giật mình thức giấc giữa đêm hoặc thức dậy cảm thấy không sảng khoái.' },
                { title: 'Khả năng tập trung', detail: 'Trí nhớ làm việc suy giảm, khiến việc đọc tài liệu và giải quyết bài toán cảm thấy khó gấp đôi.' },
                { title: 'Cảm xúc', detail: 'Dễ cáu gắt hơn, đột ngột rơi nước mắt hoặc cảm thấy tê liệt, mất cảm xúc.' },
                { title: 'Năng lượng', detail: 'Sự kiệt sức sâu sắc về thể chất và tinh thần mà cà phê liên tục cũng không thể bù đắp.' },
                { title: 'Thói quen hằng ngày', detail: 'Các bữa ăn đều đặn, vệ sinh cá nhân và việc giữ gọn gàng không gian sống bắt đầu bị bỏ bê.' }
            ],
            relatedToolLabel: 'Mở Giải tỏa nhanh',
            relatedModeLabel: 'Vào Chế độ phục hồi'
        },
        stress_signs: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Cách căng thẳng biểu hiện ra ngoài',
            shortDescription: '4 nhóm dấu hiệu căng thẳng: Suy nghĩ, Cảm xúc, Cơ thể và Hành vi.',
            contentParagraphs: [
                'Căng thẳng không đơn thuần là một trải nghiệm trong suy nghĩ. Nó biểu hiện qua 4 khía cạnh gắn kết chặt chẽ trong đời sống hàng ngày của bạn:',
                'Những dấu hiệu lặp đi lặp lại có thể trở thành tín hiệu cảnh báo sớm của riêng bạn. Nếu nhận thấy bản thân bỏ bữa sáng hay nghiến chặt quai hàm, việc chăm sóc những dấu hiệu đó sớm sẽ giúp bạn điều chỉnh trước khi chạm ngưỡng kiệt sức.'
            ],
            fourGroups: [
                {
                    name: '🧠 Suy nghĩ',
                    items: ['Khó tập trung', 'Suy nghĩ chạy đua liên tục không dứt', 'Khó đưa ra quyết định', 'Thường xuyên trống rỗng đầu óc']
                },
                {
                    name: '💭 Cảm xúc',
                    items: ['Lo lắng dai dẳng', 'Dễ cáu gắt / gắt gỏng với bạn bè', 'Cảm giác buồn bã hoặc bất an', 'Cảm thấy choáng ngợp trước những việc nhỏ nhặt']
                },
                {
                    name: '💤 Cơ thể',
                    items: ['Mệt mỏi mãn tính', 'Khó đi vào giấc ngủ', 'Đau đầu do căng thẳng', 'Căng cứng cơ vùng cổ và vai']
                },
                {
                    name: '🔄 Hành vi & Sinh hoạt',
                    items: ['Trì hoãn các hành động đơn giản', 'Thu mình khỏi bạn bè và các mối quan hệ', 'Ăn uống thất thường / chán ăn', 'Bỏ bê các thói quen sinh hoạt hằng ngày']
                }
            ],
            relatedToolLabel: 'Mở Self-check'
        },
        stress_loop: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Vòng lặp căng thẳng ở sinh viên',
            shortDescription: 'Cách những deadline dồn dập kích hoạt trạng thái tê liệt tinh thần, tạo ra các vòng lặp né tránh làm tăng thêm mức độ căng thẳng.',
            contentParagraphs: [
                'Căng thẳng thường xuyên giữ chân sinh viên trong những vòng lặp hành vi tự củng cố. Khối lượng công việc nặng nề gây lo lắng, dẫn đến việc thức khuya cày bài. Thiếu ngủ gây mệt mỏi, làm suy giảm khả năng tập trung vào ngày hôm sau, khiến tốc độ hoàn thành công việc chậm lại và sinh ra thêm nhiều căng thẳng hơn nữa.'
            ],
            loopNodes: [
                { label: 'Dồn dập deadline', icon: '⏰' },
                { label: 'Căng thẳng / Hoảng loạn', icon: '⚡' },
                { label: 'Thức khuya làm bài', icon: '🌙' },
                { label: 'Mệt mỏi & khó tập trung', icon: '😴' },
                { label: 'Tiến độ chậm lại', icon: '⏳' },
                { label: 'Căng thẳng tăng thêm', icon: '💥' }
            ],
            keyTakeaway: 'Bạn không cần phải thay đổi tất cả mọi thứ cùng một lúc. Nhận diện vòng lặp và ngắt quãng nó chỉ tại MỘT mắt xích (ví dụ: đi ngủ đúng giờ hoặc đi bộ 10 phút) sẽ bẻ gãy đà tích tụ căng thẳng.',
            relatedToolLabel: 'Mở Giải tỏa nhanh',
            relatedModeLabel: 'Vào Chế độ phục hồi'
        },
        recovery: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Phục hồi là một phần của quản lý căng thẳng',
            shortDescription: 'Tại sao căng thẳng không kết thúc ngay khi deadline vừa qua, và tại sao phục hồi lại thiết yếu.',
            contentParagraphs: [
                'Bạn đã bao giờ nộp xong một bài tập lớn hoặc hoàn thành kỳ thi cuối kỳ, chỉ để cảm thấy cạn kiệt năng lượng, dễ cáu gắt, hoặc bị cảm lạnh ngay sau đó chưa?',
                'Việc kết thúc tình huống gây căng thẳng không đồng nghĩa với phản ứng căng thẳng của cơ thể sẽ tắt đi như một công tắc đèn. Lượng cortisol và adrenaline tăng cao cần thời gian để chuyển hóa hết, và hệ thần kinh tự chủ của bạn đòi hỏi sự nghỉ ngơi có chủ đích để tái lập trạng thái cân bằng nội môi.',
                'Phục hồi không phải là lãng phí thời gian, lười biếng hay trì hoãn. Đó là một quá trình sinh học và tâm lý chủ động, nơi các kết nối thần kinh được củng cố, khả năng phục hồi cảm xúc được tái tạo và sự sáng suốt tinh thần quay trở lại.',
                'Chế độ phục hồi trong Tempo được thiết kế chuyên biệt cho giai đoạn này: mang lại cho bạn không gian để sống chậm lại, check-in với chính mình và nhận ra điều gì thực sự hữu ích.'
            ],
            relatedToolLabel: 'Bắt đầu Tập thở',
            relatedModeLabel: 'Vào Chế độ phục hồi'
        },
        academic_burnout: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Kiệt sức học đường (Academic burnout)',
            shortDescription: 'Hiểu về tình trạng kiệt quệ kéo dài, thái độ tiêu cực và suy giảm hiệu quả học tập.',
            contentParagraphs: [
                'Kiệt sức học đường không phải là sự mệt mỏi thông thường sau một đêm thức khuya. Đó là trạng thái cạn kiệt thể chất và cảm xúc mãn tính do áp lực học tập kéo dài mà thiếu cơ hội phục hồi thích đáng.',
                'Các nghiên cứu thường mô tả kiệt sức học đường qua 3 khía cạnh rõ rệt:'
            ],
            burnoutDimensions: [
                {
                    icon: '🪫',
                    name: 'Kiệt quệ',
                    detail: 'Trạng thái mệt mỏi mãn tính về thể chất, nhận thức và cảm xúc, nơi giấc ngủ thông thường không còn giúp bạn hồi phục năng lượng.'
                },
                {
                    icon: '📚',
                    name: 'Xa lánh & Hoài nghi',
                    detail: 'Hình thành thái độ thờ ơ, hoài nghi hoặc chán chường đối với bài vở, giảng viên và các mục tiêu học tập từng rất quan trọng với bạn.'
                },
                {
                    icon: '📉',
                    name: 'Cảm giác suy giảm hiệu quả',
                    detail: 'Cảm giác dai dẳng rằng nỗ lực của mình là vô nghĩa, bản thân làm việc không hiệu quả và không có thành tựu nào thực sự đáng kể.'
                }
            ],
            nonDiagnosticNote: 'Bạn không cần phải phân định rạch ròi liệu mình "chỉ đang căng thẳng" hay "đã bị kiệt sức" trước khi bắt đầu quan tâm đến sức khỏe tinh thần của mình. Nhận ra các dấu hiệu này là lời nhắc bạn tạm dừng, điều chỉnh khối lượng công việc và tìm kiếm sự hỗ trợ.',
            relatedModeLabel: 'Vào Chế độ phục hồi'
        },
        stress_eating: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Ăn uống do căng thẳng',
            shortDescription: 'Ăn uống do căng thẳng, hay còn gọi là ăn uống theo cảm xúc, là việc sử dụng thức ăn để cải thiện cảm xúc hoặc khiến bản thân cảm thấy dễ chịu hơn, thay vì đáp ứng nhu cầu đói về mặt thể chất.',
            contentParagraphs: [
                'Tìm đến thức ăn khi căng thẳng là một phản xạ sinh lý và cảm xúc hoàn toàn dễ hiểu. Khi căng thẳng mãn tính, cortisol kích thích cảm giác thèm các loại tinh bột giàu năng lượng, trong khi việc ăn uống kích hoạt giải phóng dopamine tạm thời giúp xoa dịu nỗi bất an cảm xúc.',
                'Dưới đây là cách tiếp cận thấu hiểu, không tự phán xét đối với việc ăn uống do căng thẳng:'
            ],
            steps: [
                {
                    heading: 'Kiểm tra xem bạn đang đói, căng thẳng hay cả hai',
                    detail: 'Nếu bạn thực sự đói về mặt thể chất, cơ thể bạn cần dinh dưỡng. Hãy thưởng thức một bữa ăn đàng hoàng mà không tự trách mình.'
                },
                {
                    heading: 'Tạo khoảng dừng ngắn 60 giây',
                    detail: 'Uống một cốc nước, hít thở sâu 5 nhịp hoặc rời khỏi bàn học trong một phút. Khoảng dừng ngắn tạo ra không gian để bạn nhận biết cảm xúc thực sự của mình.'
                },
                {
                    heading: 'Không phán xét đạo đức hay xem đó là thất bại',
                    detail: 'Nếu bạn vẫn chọn ăn, hãy đối xử với bản thân bằng sự dịu dàng. Ép buộc ăn kiêng và cảm giác tội lỗi chỉ tạo ra thêm căng thẳng, tiếp thêm nhiên liệu cho chính vòng lặp mà bạn đang muốn thoát ra.'
                },
                {
                    heading: 'Quay lại nhiệm vụ khi tâm trí đã lắng dịu',
                    detail: 'Khi bạn đã cảm thấy vững vàng và tĩnh tâm hơn một chút, hãy quay lại công việc với một bước đầu tiên thật nhỏ.'
                }
            ],
            relatedToolLabel: 'Mở Giải tỏa nhanh'
        },
        what_do_i_need: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Tôi cần gì khi bị căng thẳng?',
            shortDescription: 'Kết nối trải nghiệm căng thẳng hiện tại của bạn với không gian phù hợp trong Tempo.',
            contentParagraphs: [
                'Căng thẳng biểu hiện theo nhiều cách khác nhau, và điều bạn cần phụ thuộc vào trạng thái bạn đang trải qua ngay lúc này:'
            ],
            routingOptions: [
                {
                    condition: 'Quá choáng ngợp hoặc hoảng loạn không thể nghĩ thông suốt?',
                    actionText: 'Hãy xoa dịu hệ thần kinh trước tiên với Giải tỏa nhanh hoặc Tập thở hộp 2 phút.',
                    btnLabel: 'Mở Giải tỏa nhanh',
                    actionKey: 'quick_relief'
                },
                {
                    condition: 'Biết chính xác tình huống nào đang gây ra căng thẳng?',
                    actionText: 'Khám phá mục Giải quyết tình huống để nhận kế hoạch hành động từng bước thực tế.',
                    btnLabel: 'Khám phá Tình huống',
                    actionKey: 'switch_to_solve'
                },
                {
                    condition: 'Vấn đề đã qua đi nhưng bạn vẫn cảm thấy chưa ổn?',
                    actionText: 'Vào Chế độ phục hồi để giải tỏa áp lực, theo dõi thể trạng mỗi ngày và nghỉ ngơi.',
                    btnLabel: 'Vào Chế độ phục hồi',
                    actionKey: 'mode_recovery'
                },
                {
                    condition: 'Thấy có gì đó bất ổn nhưng không rõ lý do cụ thể?',
                    actionText: 'Sử dụng Chế độ mơ hồ để check-in và suy ngẫm theo hướng dẫn nhẹ nhàng.',
                    btnLabel: 'Vào Chế độ mơ hồ',
                    actionKey: 'mode_unclear'
                },
                {
                    condition: 'Có một vấn đề cấp bách cần giải quyết dứt điểm ngay?',
                    actionText: 'Vào Chế độ khẩn cấp để phân loại các task gấp và tạo timeline khả thi.',
                    btnLabel: 'Vào Chế độ khẩn cấp',
                    actionKey: 'mode_emergency'
                }
            ],
            relatedToolLabel: 'Mở Giải tỏa nhanh',
            relatedModeLabel: 'Vào Chế độ khẩn cấp'
        },
        support_seeking: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Khi nào tôi nên tìm kiếm thêm sự hỗ trợ?',
            shortDescription: 'Các chỉ số mô tả cho thấy việc tìm kiếm thêm hỗ trợ phù hợp là rất đáng cân nhắc.',
            contentParagraphs: [
                'Các công cụ tự quản lý và chiến lược cá nhân rất có giá trị, nhưng những thử thách ở đại học không phải là điều bạn bắt buộc phải vượt qua trong sự đơn độc hoàn toàn.',
                'Các dấu hiệu mô tả cho thấy sự hỗ trợ bổ sung có thể rất đáng để bạn cân nhắc:'
            ],
            descriptiveList: [
                { title: 'Căng thẳng kéo dài không thuyên giảm', detail: 'Căng thẳng dai dẳng qua nhiều tuần và những ngày cuối tuần nghỉ ngơi bình thường cũng không giúp xoa dịu.' },
                { title: 'Ảnh hưởng đến sức khỏe thể chất', detail: 'Chất lượng ăn uống, giấc ngủ hoặc mức năng lượng mỗi ngày bị xáo trộn rõ rệt và liên tục.' },
                { title: 'Hiệu quả sinh hoạt suy giảm', detail: 'Việc học tập, lên lớp hoặc các công việc thường nhật cảm thấy ngày càng khó duy trì.' },
                { title: 'Các cách quen thuộc không còn hiệu quả', detail: 'Những phương pháp và thói quen trước đây từng giúp bạn ứng phó nay dường như không còn tác dụng.' }
            ],
            supportConclusion: 'Liên hệ với điều phối viên chăm sóc sức khỏe tinh thần trong trường, cố vấn học tập hoặc các bạn tư vấn đồng đẳng là một dấu hiệu chủ động bảo vệ bản thân. (Lưu ý: Đối với các tình huống khẩn cấp về an toàn tức thời, nút SOS toàn cầu của Tempo luôn sẵn sàng bất cứ lúc nào).',
            relatedToolLabel: 'Khám phá các lựa chọn hỗ trợ'
        }
    };

    function getTopicDisplay(item) {
        if (!item) return item;
        const isVi = isViLocale();
        if (!isVi) return item;
        const viData = LEARN_TOPICS_VI[item.id];
        if (!viData) {
            if (SOLVE_SITUATIONS_TITLES_VI[item.id]) {
                return {
                    ...item,
                    title: SOLVE_SITUATIONS_TITLES_VI[item.id]
                };
            }
            return item;
        }
        return {
            ...item,
            title: viData.title || item.title,
            badge: viData.badge || (item.type === 'solve' ? '🧩 Tình huống & Giải pháp' : '🧠 Giáo dục Căng thẳng · Chủ đề'),
            shortDescription: viData.shortDescription || item.shortDescription,
            context: viData.context || item.context,
            contentParagraphs: viData.contentParagraphs || item.contentParagraphs,
            descriptiveList: viData.descriptiveList || item.descriptiveList,
            fourGroups: viData.fourGroups || item.fourGroups,
            loopNodes: viData.loopNodes || item.loopNodes,
            keyTakeaway: viData.keyTakeaway || item.keyTakeaway,
            burnoutDimensions: viData.burnoutDimensions || item.burnoutDimensions,
            nonDiagnosticNote: viData.nonDiagnosticNote || item.nonDiagnosticNote,
            steps: viData.steps || item.steps,
            routingOptions: viData.routingOptions || item.routingOptions,
            supportConclusion: viData.supportConclusion || item.supportConclusion,
            relatedTool: item.relatedTool ? {
                ...item.relatedTool,
                label: viData.relatedToolLabel || item.relatedTool.label
            } : null,
            relatedMode: item.relatedMode ? {
                ...item.relatedMode,
                label: viData.relatedModeLabel || item.relatedMode.label
            } : null
        };
    }

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
        const isVi = isViLocale();
        const tipDisplay = (isVi && TEMPO_TIPS_VI[tipId]) ? TEMPO_TIPS_VI[tipId] : tip;
        return `
            <div class="tempo-tip-callout p-4 sm:p-5 rounded-2xl bg-[#FFF8F3] border border-[#FFD2BA] space-y-1.5 shadow-2xs text-left">
                <div class="flex items-center space-x-1.5 text-[10px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">
                    <span>💡</span>
                    <span>TEMPO TIP</span>
                </div>
                <h5 class="text-xs sm:text-sm font-bold text-[#202124] leading-snug">${escapeHTML(tipDisplay.title)}</h5>
                <p class="text-xs text-[#6F6B68] leading-relaxed">${escapeHTML(tipDisplay.text)}</p>
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

    function getItemById(id) {
        const sit = SOLVE_SITUATIONS.find(s => s.id === id);
        if (sit) return sit;
        return LEARN_TOPICS.find(t => t.id === id);
    }

    function openModal(itemId) {
        if (!itemId) {
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('learn');
            }
            return;
        }
        ensureModalMounted();

        // If newly opened from outside, reset stack
        if (modalNavStack.length === 0 || modalNavStack[modalNavStack.length - 1] !== itemId) {
            modalNavStack.push(itemId);
        }

        renderModalContent();

        const modal = document.getElementById('tempo-learn-solve-modal');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
            const card = document.getElementById('tempo-learn-solve-modal-card');
            if (card) card.scrollTop = 0;
        }
    }

    function goBackModal() {
        if (modalNavStack.length > 1) {
            modalNavStack.pop();
            renderModalContent();
            const card = document.getElementById('tempo-learn-solve-modal-card');
            if (card) card.scrollTop = 0;
        }
    }

    function closeModal() {
        const modal = document.getElementById('tempo-learn-solve-modal');
        if (modal) {
            modal.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        }
        modalNavStack = [];
    }

    function renderModalContent() {
        const card = document.getElementById('tempo-learn-solve-modal-card');
        if (!card) return;

        const currentId = modalNavStack[modalNavStack.length - 1];
        const rawItem = getItemById(currentId);
        if (!rawItem) {
            closeModal();
            return;
        }

        const isVi = isViLocale();
        const item = getTopicDisplay(rawItem);

        const hasBack = modalNavStack.length > 1;
        const prevId = hasBack ? modalNavStack[modalNavStack.length - 2] : null;
        const rawPrevItem = prevId ? getItemById(prevId) : null;
        const prevItem = rawPrevItem ? getTopicDisplay(rawPrevItem) : null;

        // 1. Header with Back button + Badge + Close button
        let headerHTML = `
            <div class="flex items-center justify-between pb-3 border-b border-stone-100 gap-3">
                <div class="flex items-center space-x-2">
                    ${hasBack ? `
                        <button type="button" onclick="window.TempoLearnSolve.goBackModal()"
                                class="inline-flex items-center space-x-1 text-xs font-bold text-stone-500 hover:text-stone-900 transition cursor-pointer mr-1">
                            <span>←</span>
                            <span>${prevItem ? escapeHTML(prevItem.title) : (isVi ? 'Quay lại' : 'Back')}</span>
                        </button>
                        <span class="text-stone-300">|</span>
                    ` : ''}
                    <span class="text-xs font-extrabold uppercase tracking-wider ${item.type === 'solve' ? 'text-[#FF6B2C]' : 'text-[#7E22CE]'}">
                        ${escapeHTML(item.badge)}
                    </span>
                </div>
                <button type="button" onclick="window.TempoLearnSolve.closeModal()"
                        aria-label="${isVi ? 'Đóng cửa sổ' : 'Close dialog'}"
                        class="text-stone-400 hover:text-stone-800 p-1.5 rounded-xl transition cursor-pointer text-base">
                    ✕
                </button>
            </div>
        `;

        // 2. Title & Context
        let titleContextHTML = `
            <div class="space-y-1.5 text-left">
                <div class="flex items-center space-x-2">
                    <span class="text-2xl">${item.icon}</span>
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124] leading-snug">
                        ${escapeHTML(item.title)}
                    </h3>
                </div>
                ${item.shortDescription ? `
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        ${escapeHTML(item.shortDescription)}
                    </p>
                ` : ''}
            </div>
        `;

        // 3. Body Content
        let bodyHTML = '';

        // If context paragraph
        if (item.context) {
            bodyHTML += `
                <div class="p-4 rounded-2xl bg-stone-50 border border-stone-200/80 text-xs sm:text-sm text-[#474543] leading-relaxed">
                    ${escapeHTML(item.context)}
                </div>
            `;
        }

        // If general paragraphs (Learn topics)
        if (item.contentParagraphs && item.contentParagraphs.length > 0) {
            bodyHTML += `
                <div class="space-y-3 text-xs sm:text-sm text-[#474543] leading-relaxed">
                    ${item.contentParagraphs.map(p => `<p>${escapeHTML(p)}</p>`).join('')}
                </div>
            `;
        }

        // If steps
        if (item.steps && item.steps.length > 0) {
            bodyHTML += `
                <div class="space-y-3 pt-2">
                    <span class="text-xs font-extrabold uppercase tracking-wider text-stone-500">${isVi ? 'CÁC BƯỚC THỰC HIỆN' : 'ACTION STEPS'}</span>
                    <div class="space-y-2.5">
                        ${item.steps.map((s, idx) => `
                            <div class="p-4 rounded-2xl border border-stone-200 bg-white space-y-1 shadow-2xs">
                                <div class="flex items-center space-x-2">
                                    <span class="w-5 h-5 rounded-full bg-[#FFE9DC] text-[#B83D08] text-[11px] font-extrabold flex items-center justify-center shrink-0">
                                        ${idx + 1}
                                    </span>
                                    <h5 class="text-xs sm:text-sm font-bold text-[#202124]">
                                        ${escapeHTML(s.heading)}
                                    </h5>
                                </div>
                                <p class="text-xs text-[#6F6B68] leading-relaxed pl-7">
                                    ${escapeHTML(s.detail)}
                                </p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // If case distinctions (e.g. Falling Behind, Teamwork)
        if (item.caseDistinctions && item.caseDistinctions.length > 0) {
            bodyHTML += `
                <div class="space-y-3.5 pt-2">
                    <span class="text-xs font-extrabold uppercase tracking-wider text-stone-500">${isVi ? 'CÁC BỐI CẢNH / TÌNH HUỐNG KHÁC NHAU' : 'DIFFERENT CONTEXTS / CASES'}</span>
                    <div class="space-y-3">
                        ${item.caseDistinctions.map(c => `
                            <div class="p-4 sm:p-5 rounded-2xl border border-[#FFD2BA] bg-[#FFF9F5] space-y-2.5 shadow-2xs">
                                <h5 class="text-xs sm:text-sm font-extrabold text-[#B83D08] flex items-center space-x-1.5">
                                    <span>👉</span>
                                    <span>${escapeHTML(c.caseTitle)}</span>
                                </h5>
                                <ul class="space-y-1.5 text-xs text-[#474543] pl-1">
                                    ${c.items.map(it => `
                                        <li class="flex items-start space-x-2 leading-relaxed">
                                            <span class="text-[#FF6B2C] font-bold">•</span>
                                            <span>${escapeHTML(it)}</span>
                                        </li>
                                    `).join('')}
                                </ul>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // If descriptive list (e.g. 5 areas of stress problem)
        if (item.descriptiveList && item.descriptiveList.length > 0) {
            bodyHTML += `
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2">
                    ${item.descriptiveList.map(dl => `
                        <div class="p-3.5 rounded-xl border border-stone-200 bg-stone-50/60 space-y-0.5">
                            <h6 class="text-xs font-bold text-[#202124]">${escapeHTML(dl.title)}</h6>
                            <p class="text-xs text-[#6F6B68] leading-relaxed">${escapeHTML(dl.detail)}</p>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // If 4 groups (Thoughts, Emotions, Body, Behavior)
        if (item.fourGroups && item.fourGroups.length > 0) {
            bodyHTML += `
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                    ${item.fourGroups.map(grp => `
                        <div class="p-4 rounded-2xl border border-stone-200 bg-stone-50 space-y-2">
                            <h6 class="text-xs font-extrabold text-[#202124] uppercase tracking-wide">${escapeHTML(grp.name)}</h6>
                            <ul class="space-y-1 text-xs text-[#474543]">
                                ${grp.items.map(it => `
                                    <li class="flex items-center space-x-1.5">
                                        <span class="text-[#FF6B2C] font-bold">·</span>
                                        <span>${escapeHTML(it)}</span>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // If Visual Loop diagram (The stress loop)
        if (item.hasVisualLoop && item.loopNodes) {
            bodyHTML += `
                <div class="p-5 rounded-3xl border-2 border-[#FFD2BA] bg-gradient-to-br from-[#FFF9F5] to-white space-y-3.5 shadow-2xs">
                    <span class="text-[10px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">${isVi ? 'VÒNG LẶP CĂNG THẲNG TRỰC QUAN' : 'VISUAL STRESS CYCLE'}</span>
                    <div class="flex flex-wrap items-center justify-center gap-2 text-center py-2">
                        ${item.loopNodes.map((n, i) => `
                            <div class="px-3 py-1.5 rounded-xl bg-white border border-[#FFD2BA] shadow-2xs text-xs font-bold text-[#202124] flex items-center space-x-1">
                                <span>${n.icon}</span>
                                <span>${escapeHTML(n.label)}</span>
                            </div>
                            ${i < item.loopNodes.length - 1 ? `<span class="text-[#FF6B2C] font-bold">→</span>` : `<span class="text-stone-300 font-bold">↺</span>`}
                        `).join('')}
                    </div>
                    ${item.keyTakeaway ? `
                        <div class="p-3 rounded-xl bg-white/90 border border-stone-200 text-xs text-[#474543] leading-relaxed">
                            <strong class="text-[#202124]">${isVi ? 'Điểm mấu chốt:' : 'Key Insight:'}</strong> ${escapeHTML(item.keyTakeaway)}
                        </div>
                    ` : ''}
                </div>
            `;
        }

        // If Burnout dimensions
        if (item.burnoutDimensions && item.burnoutDimensions.length > 0) {
            bodyHTML += `
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-2">
                    ${item.burnoutDimensions.map(d => `
                        <div class="p-4 rounded-2xl border border-purple-200 bg-purple-50/50 space-y-1.5 text-left">
                            <div class="text-lg">${d.icon}</div>
                            <h6 class="text-xs font-bold text-[#202124]">${escapeHTML(d.name)}</h6>
                            <p class="text-[11px] text-[#6F6B68] leading-relaxed">${escapeHTML(d.detail)}</p>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // If Non-diagnostic note
        if (item.nonDiagnosticNote) {
            bodyHTML += `
                <div class="p-3.5 rounded-xl bg-stone-50 border border-stone-200 text-xs text-stone-600 leading-relaxed italic">
                    ${escapeHTML(item.nonDiagnosticNote)}
                </div>
            `;
        }

        // If Routing options (What do I need when I'm stressed?)
        if (item.routingOptions && item.routingOptions.length > 0) {
            bodyHTML += `
                <div class="space-y-2.5 pt-2">
                    <span class="text-xs font-extrabold uppercase tracking-wider text-stone-500">${isVi ? 'TÌM BƯỚC TIẾP THEO CỦA BẠN' : 'FINDING YOUR NEXT STEP'}</span>
                    <div class="space-y-2">
                        ${item.routingOptions.map(ro => `
                            <div class="p-3.5 sm:p-4 rounded-2xl border border-stone-200 bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs">
                                <div class="space-y-0.5">
                                    <h6 class="text-xs font-bold text-[#202124]">${escapeHTML(ro.condition)}</h6>
                                    <p class="text-xs text-[#6F6B68] leading-relaxed">${escapeHTML(ro.actionText)}</p>
                                </div>
                                <button type="button" onclick="window.TempoLearnSolve.handleRoutingAction('${ro.actionKey}')"
                                        class="btn-primary px-3.5 py-1.5 rounded-xl text-xs font-bold shadow-2xs shrink-0 cursor-pointer">
                                    ${escapeHTML(ro.btnLabel)} →
                                </button>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // If Support conclusion
        if (item.supportConclusion) {
            bodyHTML += `
                <div class="p-4 rounded-2xl bg-[#EDF7F1] border border-[#CDE9DA] text-xs text-[#166545] leading-relaxed">
                    ${escapeHTML(item.supportConclusion)}
                </div>
            `;
        }

        // Embedded Reusable Tempo Tip
        if (item.tipId) {
            bodyHTML += renderTipCalloutHTML(item.tipId);
        }

        // 4. Related Links & Cross-Linking Section
        let relatedHTML = '';
        const hasRelatedLearn = item.relatedLearnIds && item.relatedLearnIds.length > 0;
        const hasRelatedSolve = item.relatedSolveIds && item.relatedSolveIds.length > 0;
        const hasRelatedTool = Boolean(item.relatedTool);
        const hasRelatedMode = Boolean(item.relatedMode);

        if (hasRelatedLearn || hasRelatedSolve || hasRelatedTool || hasRelatedMode) {
            relatedHTML += `
                <div class="pt-4 border-t border-stone-100 space-y-3">
                    <span class="text-xs font-extrabold uppercase tracking-wider text-stone-400">
                        ${isVi ? 'HƯỚNG DẪN &amp; HÀNH ĐỘNG LIÊN QUAN' : 'RELATED GUIDES &amp; ACTIONS'}
                    </span>
                    <div class="flex flex-wrap items-center gap-2">
                        ${hasRelatedLearn ? item.relatedLearnIds.map(rid => {
                            const rItem = getItemById(rid);
                            if (!rItem) return '';
                            const disp = getTopicDisplay(rItem);
                            return `
                                <button type="button" onclick="window.TempoLearnSolve.openModal('${rItem.id}')"
                                        class="px-3 py-1.5 rounded-xl bg-purple-50 text-[#7E22CE] border border-purple-200 text-xs font-bold hover:bg-purple-100 transition cursor-pointer flex items-center space-x-1">
                                    <span>🧠</span>
                                    <span>${escapeHTML(disp.title)} →</span>
                                </button>
                            `;
                        }).join('') : ''}

                        ${hasRelatedSolve ? item.relatedSolveIds.map(rid => {
                            const rItem = getItemById(rid);
                            if (!rItem) return '';
                            const disp = getTopicDisplay(rItem);
                            return `
                                <button type="button" onclick="window.TempoLearnSolve.openModal('${rItem.id}')"
                                        class="px-3 py-1.5 rounded-xl bg-[#FFF5EC] text-[#B83D08] border border-[#FFD2BA] text-xs font-bold hover:bg-[#FFE9DC] transition cursor-pointer flex items-center space-x-1">
                                    <span>🧩</span>
                                    <span>${escapeHTML(disp.title)} →</span>
                                </button>
                            `;
                        }).join('') : ''}

                        ${hasRelatedTool ? `
                            <button type="button" onclick="window.TempoLearnSolve.handleToolAction('${item.relatedTool.action}')"
                                    class="px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold hover:bg-emerald-100 transition cursor-pointer flex items-center space-x-1">
                                <span>🛠️</span>
                                <span>${escapeHTML(item.relatedTool.label)}</span>
                            </button>
                        ` : ''}

                        ${hasRelatedMode ? `
                            <button type="button" onclick="window.TempoLearnSolve.handleModeAction('${item.relatedMode.mode}')"
                                    class="px-3 py-1.5 rounded-xl bg-[#FFE9DC] text-[#B83D08] border border-[#FFD2BA] text-xs font-bold hover:bg-[#FFD2BA] transition cursor-pointer flex items-center space-x-1">
                                <span>⚡</span>
                                <span>${escapeHTML(item.relatedMode.label)}</span>
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        // Assemble Modal Card
        card.innerHTML = `
            ${headerHTML}
            ${titleContextHTML}
            <div class="space-y-4">
                ${bodyHTML}
            </div>
            ${relatedHTML}
            <div class="pt-3 border-t border-stone-100 flex items-center justify-end">
                <button type="button" onclick="window.TempoLearnSolve.closeModal()"
                        class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                    ${isVi ? 'Đóng' : 'Close'}
                </button>
            </div>
        `;
    }

    // =========================================================================
    // 8. PUBLIC TOOL & MODE CROSS-LINK ACTIONS
    // =========================================================================
    function handleToolAction(toolAction) {
        closeModal();
        if (toolAction === 'focus_zone') {
            if (window.TempoFocusZone && typeof window.TempoFocusZone.openQuickEntry === 'function') {
                window.TempoFocusZone.openQuickEntry();
            } else if (window.TempoTriage && typeof window.TempoTriage.launchFocusMode === 'function') {
                window.TempoTriage.launchFocusMode();
            }
        } else if (toolAction === 'quick_relief') {
            if (window.TempoStressRelief && typeof window.TempoStressRelief.openModal === 'function') {
                window.TempoStressRelief.openModal();
            } else if (window.TempoTriage && typeof window.TempoTriage.openBoxBreathingModal === 'function') {
                window.TempoTriage.openBoxBreathingModal();
            }
        } else if (toolAction === 'breathing') {
            if (window.TempoStressRelief && typeof window.TempoStressRelief.openBreathing === 'function') {
                window.TempoStressRelief.openBreathing();
            } else if (window.TempoTriage && typeof window.TempoTriage.openBoxBreathingModal === 'function') {
                window.TempoTriage.openBoxBreathingModal();
            }
        } else if (toolAction === 'self_check') {
            if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                window.TempoMode.openStrack('checkin');
            } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openDailyCheckin === 'function') {
                window.TempoRecoverySelfCheck.openDailyCheckin();
            } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('strack');
            }
        } else if (toolAction === 'support_page') {
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('support');
            }
        }
    }

    function handleModeAction(modeKey) {
        closeModal();
        if (window.TempoMode && typeof window.TempoMode.requestMode === 'function') {
            window.TempoMode.requestMode(modeKey);
        }
    }

    function handleRoutingAction(actionKey) {
        closeModal();
        if (actionKey === 'quick_relief') {
            handleToolAction('quick_relief');
        } else if (actionKey === 'switch_to_solve') {
            selectTab('solve');
        } else if (actionKey === 'mode_recovery') {
            handleModeAction('recovery');
        } else if (actionKey === 'mode_unclear') {
            handleModeAction('unclear');
        } else if (actionKey === 'mode_emergency') {
            handleModeAction('emergency');
        }
    }

    // =========================================================================
    // 9. CONTROLLER API
    // =========================================================================
    function selectTab(tabKey) {
        if (tabKey !== 'solve' && tabKey !== 'learn') return;
        activeTab = tabKey;
        updateDOM();
    }

    function selectCategory(catKey) {
        activeCategory = catKey;
        activeTab = 'solve';
        updateDOM();
    }

    function updateDOM() {
        const sections = document.querySelectorAll('#tempo-learn-solve-section, .tempo-learn-solve-section');
        if (sections && sections.length > 0) {
            sections.forEach(target => {
                if (target && target.parentNode) {
                    const temp = document.createElement('div');
                    temp.innerHTML = renderSectionHTML();
                    const newSection = temp.firstElementChild;
                    if (newSection) {
                        target.parentNode.replaceChild(newSection, target);
                    }
                }
            });
            return;
        }

        const containers = document.querySelectorAll('.tempo-learn-solve-container, #tempo-learn-solve-section-container, #dmode-learn-solve-container, #emode-learn-solve-container, #rmode-learn-solve-container, #hub-learn-solve-container');
        if (containers && containers.length > 0) {
            containers.forEach(c => {
                c.innerHTML = renderSectionHTML();
            });
            return;
        }
    }

    function renderSection(containerId) {
        const el = document.getElementById(containerId);
        if (el) {
            el.innerHTML = renderSectionHTML();
        }
    }

    function init() {
        ensureModalMounted();
        if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
            window.TempoI18n.onLanguageChange(() => {
                const modal = document.getElementById('tempo-learn-solve-modal');
                if (modal && !modal.classList.contains('hidden') && modalNavStack.length > 0) {
                    renderModalContent();
                }
                updateDOM();
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    return {
        init,
        renderSectionHTML,
        renderSection,
        selectTab,
        selectCategory,
        openModal,
        openTopic: (id) => openModal(id === 'theStressLoop' ? 'stress_loop' : id),
        closeModal,
        goBackModal,
        handleToolAction,
        handleModeAction,
        handleRoutingAction,
        // Data accessors
        getTips: () => TEMPO_TIPS,
        getCategories: () => SOLVE_CATEGORIES,
        getSituations: () => SOLVE_SITUATIONS,
        getTopics: () => LEARN_TOPICS,
        getActiveTab: () => activeTab,
        getActiveCategory: () => activeCategory,
        getNavStack: () => [...modalNavStack],
        isViLocale,
        getTopicDisplay
    };
})();
