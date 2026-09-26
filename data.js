/**
 * Default Seed Data for Tempo Wellbeing
 * Provides realistic pre-populated data for immediate user testing.
 */

window.TEMPO_DATA = {
    // Initial routine blocks for "Today's Gentle Cadence"
    routine: [
        {
            id: 'rt-1',
            time: '10:00 - 10:45 AM',
            title: 'Deep Focus: Marketing Report Intro & Outline',
            tag: 'Focus',
            tagColor: 'sage',
            isDone: true,
            isFlexible: false
        },
        {
            id: 'rt-2',
            time: '12:30 - 01:15 PM',
            title: 'Recovery Anchor: Walk outside & Hydration',
            tag: 'Recovery',
            tagColor: 'blue',
            isDone: true,
            isFlexible: true
        },
        {
            id: 'rt-3',
            time: '03:00 - 03:45 PM',
            title: 'Gentle Focus: Research Presentation Slide Titles',
            tag: 'Focus',
            tagColor: 'sage',
            isDone: false,
            isFlexible: false
        },
        {
            id: 'rt-4',
            time: '05:30 - 06:00 PM',
            title: 'Decompression: Light stretching & screen break',
            tag: 'Recovery',
            tagColor: 'blue',
            isDone: false,
            isFlexible: true
        },
        {
            id: 'rt-5',
            time: '09:30 - 10:15 PM',
            title: 'Sleep Wind-Down: No screens, reading fiction',
            tag: 'Sleep',
            tagColor: 'amber',
            isDone: false,
            isFlexible: true
        }
    ],

    // Stress-Management Habits for Routine Tracker (Non-punitive, supportive)
    habits: [
        {
            id: 'hab-1',
            title: 'Morning Hydration Anchor',
            whyItHelps: 'Rehydrates brain cells to reduce mental fatigue before caffeine.',
            category: 'Physical',
            timeOfDay: 'Morning',
            isDone: true,
            history: [true, true, true, false, true, true, true]
        },
        {
            id: 'hab-2',
            title: '2-Minute Box Breathing Reset',
            whyItHelps: 'Activates parasympathetic nervous system to lower heart rate.',
            category: 'Mental / Calm',
            timeOfDay: 'Anytime',
            isDone: true,
            history: [true, false, true, true, true, false, true]
        },
        {
            id: 'hab-3',
            title: 'One 25-Min Single-Task Focus Block',
            whyItHelps: 'Protects working memory by eliminating frantic tab switching.',
            category: 'Focus',
            timeOfDay: 'Afternoon',
            isDone: false,
            history: [true, true, false, true, true, true, false]
        },
        {
            id: 'hab-4',
            title: '10-Minute Screen-Free Outdoor Walk',
            whyItHelps: 'Optic flow and natural light reset eye strain and mental exhaustion.',
            category: 'Recovery',
            timeOfDay: 'Afternoon',
            isDone: false,
            history: [false, true, true, true, false, true, false]
        },
        {
            id: 'hab-5',
            title: 'Bedtime Paper Brain Dump (5 mins)',
            whyItHelps: 'Offloads unfinished academic loops from memory before sleep.',
            category: 'Sleep',
            timeOfDay: 'Evening',
            isDone: false,
            history: [true, true, true, true, false, true, false]
        }
    ],

    // Curated Stress-Relief Habit Library presets for 1-click addition
    habitPresets: [
        {
            title: '5-Minute Natural Sunlight Exposure',
            whyItHelps: 'Calibrates circadian rhythm and morning alertness.',
            category: 'Physical',
            timeOfDay: 'Morning'
        },
        {
            title: 'Cold Water Wrist Splash',
            whyItHelps: 'Triggers the dive reflex to instantly de-escalate anxiety surges.',
            category: 'Mental / Calm',
            timeOfDay: 'Anytime'
        },
        {
            title: 'Single-Tab Writing Sprint (15 mins)',
            whyItHelps: 'Lowers friction for starting stubborn essays or lab reports.',
            category: 'Focus',
            timeOfDay: 'Morning'
        },
        {
            title: '30-Minute Screen Curfew Before Bed',
            whyItHelps: 'Prevents blue light from suppressing natural melatonin production.',
            category: 'Sleep',
            timeOfDay: 'Evening'
        },
        {
            title: 'Self-Compassion Check-in (1 min)',
            whyItHelps: 'Reminds yourself that your worth is not measured by semester grades.',
            category: 'Recovery',
            timeOfDay: 'Evening'
        }
    ],

    // Knowledge Hub "Learn & Solve" Articles
    articles: [
        {
            id: 'art-1',
            category: 'urgent',
            categoryLabel: 'Urgent / Can’t Start',
            title: 'The 5-Minute Starter Rule for Paralyzing Deadlines',
            readTime: '3 min read',
            summary: 'When multiple deadlines trigger a freeze response, your brain views the entire assignment as a physical threat. Here is how to deactivate the alarm.',
            keyTakeaways: [
                'Do not commit to finishing the assignment; commit only to working for exactly 300 seconds.',
                'The goal of minute 1–5 is not quality; it is purely overcoming kinetic friction.',
                'Give yourself full permission to stop after 5 minutes. Over 80% of students choose to continue once started.'
            ],
            steps: [
                'Open the blank document and type 3 messy bullet points.',
                'Turn off all browser tabs except the immediate rubric.',
                'Set a 5-minute timer on your phone and place it screen-down.'
            ],
            quote: 'Action creates emotional traction. You do not need to feel ready to take a micro-step.'
        },
        {
            id: 'art-2',
            category: 'communication',
            categoryLabel: 'Asking for Help',
            title: 'How to Ask a Professor for an Extension (With Email Template)',
            readTime: '4 min read',
            summary: 'Most professors want to help when approached respectfully and proactively. Here is how to ask without shame or over-explaining.',
            keyTakeaways: [
                'Reach out at least 24 hours before the deadline whenever possible.',
                'Take ownership, propose a realistic alternative date, and show work in progress.',
                'Never send a panicked apology; send a clear, dignified professional request.'
            ],
            template: `Subject: Course [Course Code] - Extension Request for [Assignment Title]

Dear Professor [Last Name],

I am writing regarding the upcoming [Assignment Title] due on [Original Date]. Due to an unexpected cluster of academic commitments and health challenges this week, I am currently behind schedule.

I have already drafted the initial outline and research citations [attach or mention briefly]. To submit work that genuinely reflects course expectations, I respectfully request an extension until [Proposed Date & Time, e.g., Sunday at 5:00 PM].

Thank you very much for your time and understanding.

Sincerely,
[Your Name]
[Student ID]`,
            steps: [
                'Choose a concrete new deadline that gives you breathing room (48-72 hours).',
                'Copy and customize the template above with your details.',
                'Attach your rough notes or draft to demonstrate honest effort.'
            ],
            quote: 'Advocating for your academic capacity is a sign of maturity, not failure.'
        },
        {
            id: 'art-3',
            category: 'sleep',
            categoryLabel: 'Sleep & Worry',
            title: 'How to Sleep When Your Brain Won’t Stop Calculating Deadlines',
            readTime: '3 min read',
            summary: 'Lying in bed mentally calculating hours until your alarm is the quickest way to stay awake. Learn the physical cognitive offloading protocol.',
            keyTakeaways: [
                'Brain dump onto physical paper before turning off the lights—digital screens keep dopamine active.',
                'Adopt the "Cognitive Shuffle" technique to scramble anxious planning circuits.',
                'Acknowledge that 6 hours of imperfect rest is 10x better for your GPA than pulling an all-nighter.'
            ],
            steps: [
                'Keep a notepad by your bed; write down the single first task for tomorrow morning.',
                'Use the 4-7-8 breathing cadence: Inhale 4s, Hold 7s, Exhale slowly 8s.',
                'Keep bedroom temperature cool (around 18-20°C / 65-68°F).'
            ],
            quote: 'Sleep is not a reward you earn after finishing work; it is the biological prerequisite for thinking.'
        },
        {
            id: 'art-4',
            category: 'focus',
            categoryLabel: 'Focus & Brain Fog',
            title: 'The 20-20 Cognitive Reset for Severe Brain Fog',
            readTime: '2 min read',
            summary: 'When you have been staring at the same paragraph for 20 minutes without processing words, your prefrontal cortex is depleted.',
            keyTakeaways: [
                'Brain fog is metabolic depletion, not lack of willpower.',
                'Change your physical sensory field: stand up, drink cold water, look at an object 20 feet away.',
                'Switch from abstract synthesis (writing an argument) to mechanical execution (formatting citations, downloading sources).'
            ],
            steps: [
                'Step away from all screens for 3 full minutes.',
                'Drink a full glass of water and stretch your shoulders and neck.',
                'Resume with a mechanical low-cognitive task for 10 minutes.'
            ],
            quote: 'When your brain refuses to sprint, give it permission to take a slow, steady walk.'
        },
        {
            id: 'art-5',
            category: 'urgent',
            categoryLabel: 'Perfectionism & Overwhelm',
            title: 'Overcoming the "All-or-Nothing" Perfectionism Trap',
            readTime: '3 min read',
            summary: 'Perfectionism is not high standards; it is fear in a fancy suit. Learn how the "Draft Zero" mindset unlocks paralyzed work.',
            keyTakeaways: [
                'A mediocre completed paper can be improved; a blank page cannot be graded.',
                'Embrace "Draft Zero": write sentence fragments, slang, and placeholders like [INSERT FACT HERE].',
                'Lowering the bar from "outstanding" to "acceptable" is the secret to starting.'
            ],
            steps: [
                'Explicitly give yourself permission to write the ugliest first draft possible.',
                'Set a rule: No backspacing or editing during the first 15 minutes of drafting.',
                'Remember that 75% submitted is infinitely better than 0% unsubmitted.'
            ],
            quote: 'Done is better than perfect, because done allows you to sleep.'
        }
    ],

    // Admin / Advisor Micro-Tips
    tips: [
        {
            id: 'tip-1',
            author: 'Dr. Elena Vance',
            role: 'Campus Wellbeing Advisor',
            title: 'The "Two-Task Horizon" Technique',
            category: 'Prioritization',
            readMinutes: 2,
            content: 'When looking at a list of 10 items, your brain freezes. Pick only 2 tasks for the morning. Hide the remaining 8 in a drawer or closed browser window until 1:00 PM. Narrowing your horizon restores your sense of control.',
            publishedAt: 'Yesterday',
            isPublished: true
        },
        {
            id: 'tip-2',
            author: 'Dr. Elena Vance',
            role: 'Campus Wellbeing Advisor',
            title: 'Emergency De-escalation: The Physical Reset',
            category: 'Stress Relief',
            readMinutes: 1,
            content: 'If panic hits your chest right now: Run cold tap water over your wrists for 30 seconds. This triggers the mammalian dive reflex, immediately dropping your elevated heart rate and grounding your nervous system.',
            publishedAt: '3 days ago',
            isPublished: true
        },
        {
            id: 'tip-3',
            author: 'Marcus Reed',
            role: 'Peer Academic Mentor',
            title: 'How to Break Down a 10-Page Research Paper',
            category: 'Study Habits',
            readMinutes: 2,
            content: 'A 10-page paper is simply 8 small essays of 350 words each. Treat each section heading as its own independent mini-assignment with its own micro-break.',
            publishedAt: '5 days ago',
            isPublished: true
        }
    ],

    // Seeded Student Support Conversations
    supportTickets: [
        {
            id: 'TCK-2041',
            studentName: 'Alex Rivera',
            studentEmail: 'a.rivera@university.edu',
            category: 'Deadline Cluster & Triage',
            urgency: 'High (Struggling today)',
            status: 'Awaiting Advisor',
            subject: 'Overwhelmed by 3 overlapping finals and need guidance on requesting delay',
            createdAt: '25 minutes ago',
            messages: [
                {
                    id: 'msg-1',
                    sender: 'student',
                    senderName: 'Alex Rivera',
                    text: 'Hello. I have a marketing report due tomorrow, slides due Friday, and an exam next Monday. I had a severe migraine yesterday and lost 8 hours of study time. I don’t know whether to ask for an extension or try to pull an all-nighter. I am feeling really anxious and paralyzed.',
                    timestamp: '25m ago'
                }
            ]
        },
        {
            id: 'TCK-1988',
            studentName: 'Jordan Taylor',
            studentEmail: 'j.taylor@university.edu',
            category: 'Sleep & Burnout',
            urgency: 'Medium',
            status: 'Advisor Replied',
            subject: 'Cannot sleep because of exam thoughts',
            createdAt: 'Yesterday',
            messages: [
                {
                    id: 'msg-2',
                    sender: 'student',
                    senderName: 'Jordan Taylor',
                    text: 'I haven’t slept more than 3 hours a night for the past 4 days. Every time I close my eyes my mind repeats chemistry formulas. What can I do?',
                    timestamp: 'Yesterday at 3:15 PM'
                },
                {
                    id: 'msg-3',
                    sender: 'admin',
                    senderName: 'Dr. Elena Vance (Wellbeing Advisor)',
                    text: 'Hi Jordan. First, please know that this is a very common stress response when your nervous system is on hyper-alert. Tonight, please try the Cognitive Shuffle technique from our Knowledge Hub, and avoid doing any work in your bed. I have also reserved a 15-minute virtual check-in tomorrow at 2:00 PM if you would like to talk it through.',
                    timestamp: 'Yesterday at 4:40 PM'
                }
            ]
        }
    ],

    // Last completed stress test baseline
    lastStressTest: {
        overallScore: 38,
        rating: 'Strained Pressure',
        completedAt: '2 days ago',
        dimensions: {
            perceivedStress: 7,
            deadlinePressure: 9,
            sleepQuality: 4,
            concentration: 5,
            exhaustion: 7,
            burnoutSigns: 6
        }
    }
};
