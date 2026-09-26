export default function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(200).json({ status: 'ok', message: 'Send POST with text and availableHours' });
    }

    const { text = '', availableHours = 4 } = req.body || {};
    const lower = text.toLowerCase();
    const tasks = [];

    const taskPatterns = [
        { regex: /marketing report/i, title: 'Marketing Report', deadline: 'Tomorrow, 9:00 AM', effort: 2.0, priority: 95 },
        { regex: /\b(?<!marketing\s)report\b/i, title: 'Academic Report', deadline: 'Tomorrow morning', effort: 2.5, priority: 90 },
        { regex: /presentation|slides/i, title: 'Research Presentation Slides', deadline: 'Friday, 2:00 PM', effort: 1.5, priority: 75 },
        { regex: /exam|test|quiz|midterm/i, title: 'Exam Preparation Review', deadline: 'In 3 days', effort: 2.0, priority: 70 },
        { regex: /lab|code|coding/i, title: 'Programming Lab Assignment', deadline: 'Tonight, 11:59 PM', effort: 1.5, priority: 88 },
        { regex: /essay|paper/i, title: 'Course Essay Draft', deadline: 'In 2 days', effort: 3.0, priority: 80 },
        { regex: /reading|readings/i, title: 'Course Reading Chapters', deadline: 'This weekend', effort: 1.0, priority: 50 }
    ];

    const matchedTitles = new Set();
    for (const pattern of taskPatterns) {
        if (pattern.regex.test(lower) && !matchedTitles.has(pattern.title)) {
            tasks.push({
                id: `task-${tasks.length + 1}`,
                title: pattern.title,
                deadline: pattern.deadline,
                estimatedHours: pattern.effort,
                priorityScore: pattern.priority,
                status: 'pending'
            });
            matchedTitles.add(pattern.title);
        }
    }

    if (tasks.length === 0) {
        const cleanSnippet = text.trim() ? text.trim().substring(0, 50) + '...' : 'Immediate Academic Task';
        tasks.push({
            id: 'task-1',
            title: cleanSnippet,
            deadline: 'Upcoming deadline',
            estimatedHours: Math.min(availableHours, 2.0),
            priorityScore: 85,
            status: 'pending'
        });
    }

    tasks.sort((a, b) => b.priorityScore - a.priorityScore);
    const topTask = tasks[0];

    let oneAction = `Draft 3 concrete bullet points for the next section of ${topTask.title}`;
    let oneActionMicro = "Open your notes and read the assignment prompt once with a highlighter";
    let rationale = "Starting with a bite-sized draft creates forward momentum without triggering perfectionism.";

    if (topTask.title.toLowerCase().includes('marketing') || topTask.title.toLowerCase().includes('report')) {
        oneAction = "Write down the 3 core section headings and bullet points for Section 2";
        oneActionMicro = "Just open the document and type 3 bullet points for paragraph 1";
        rationale = "This has the earliest deadline (tomorrow morning). Outlining the next section removes 70% of writing hesitation.";
    } else if (topTask.title.toLowerCase().includes('presentation') || topTask.title.toLowerCase().includes('slide')) {
        oneAction = "Create blank slide outline with 5 slide titles (Title, Problem, Method, Findings, Conclusion)";
        oneActionMicro = "Open your slide app and title Slide 1 and Slide 2";
        rationale = "Structuring the 5 headers gives you an instant roadmap without needing finished bullet points.";
    } else if (topTask.title.toLowerCase().includes('lab') || topTask.title.toLowerCase().includes('code')) {
        oneAction = "Isolate the failing function and write out input/output test cases on paper";
        oneActionMicro = "Add a single print/log statement to verify where the variable changes";
        rationale = "Debugging in code while stressed causes loops. Writing test cases grounds the logic immediately.";
    }

    return res.status(200).json({
        success: true,
        summary: `Detected ${tasks.length} main academic priorities across ~${availableHours} hours available.`,
        availableHours: Number(availableHours),
        tasks,
        topTask,
        oneNextAction: oneAction,
        oneNextActionMicro: oneActionMicro,
        rationale,
        targetMinutes: 25,
        recommendedBreakMinutes: 5
    });
}
