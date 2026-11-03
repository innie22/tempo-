with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    c = f.read()

assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated before patch"

if 'selfCheckWorkspace:' not in c:
    target_vi = '            toolNotes: {'
    replace_vi = """            selfCheckWorkspace: {
                title: "T\u1ef1 ki\u1ec3m tra Tempo",
                returnUrgent: "Quay l\u1ea1i Ch\u1ebf \u0111\u1ed9 kh\u1ea9n c\u1ea5p",
                returnRecovery: "Quay l\u1ea1i Ch\u1ebf \u0111\u1ed9 ph\u1ee5c h\u1ed3i",
                returnUnclear: "Quay l\u1ea1i Ch\u1ebf \u0111\u1ed9 m\u01a1 h\u1ed3",
                returnHome: "Quay l\u1ea1i trang ch\u1ee7",
                returnUrgentWithArrow: "\u2190 Quay l\u1ea1i Ch\u1ebf \u0111\u1ed9 kh\u1ea9n c\u1ea5p",
                dailyCheckinUpper: "CHECK-IN H\u1eb0NG NG\u00c0Y",
                todaysCheckin: "Check-in h\u00f4m nay",
                streakDays: "Chu\u1ed7i {count} ng\u00e0y",
                sleepQuestion: "B\u1ea1n ng\u1ee7 th\u1ebf n\u00e0o v\u00e0o t\u1ed1i qua?",
                good: "T\u1ed1t",
                notGood: "Ch\u01b0a t\u1ed1t",
                walkQuestion: "H\u00f4m nay b\u1ea1n c\u00f3 \u0111i b\u1ed9 kh\u00f4ng?",
                yes: "C\u00f3",
                noIdidnt: "Kh\u00f4ng",
                createNoteForToday: "T\u1ea1o ghi ch\u00fa h\u00f4m nay",
                checkedInCount: "B\u1ea1n \u0111\u00e3 check-in {completed}/{total} m\u1ee5c h\u00f4m nay.",
                yourTrackingSystem: "H\u1ec7 th\u1ed1ng tracking c\u1ee7a b\u1ea1n",
                addTracking: "Th\u00eam tracking",
                clearAll: "X\u00f3a t\u1ea5t c\u1ea3",
                adjust: "Ch\u1ec9nh s\u1eeda",
                tension: "C\u0103ng th\u1eb3ng",
                sleep: "Gi\u1ea5c ng\u1ee7",
                walk: "\u0110i b\u1ed9",
                avgTensionLevel: "M\u1ee9c \u0111\u1ed9 c\u0103ng th\u1eb3ng trung b\u00ecnh c\u1ee7a b\u1ea1n l\u00e0",
                nightsQualitySleep: "S\u1ed1 \u0111\u00eam ng\u1ee7 ngon",
                totalLoggedThisWeek: "T\u1ed5ng ghi nh\u1eadn tu\u1ea7n n\u00e0y",
                avgRating: "\u0110\u00e1nh gi\u00e1 trung b\u00ecnh",
                viewMyFullCheck: "Xem full-check",
                myWeeklyReport: "B\u00e1o c\u00e1o tu\u1ea7n c\u1ee7a t\u00f4i",
                myRecoveryNotice: "L\u1eddi nh\u1eafn ph\u1ee5c h\u1ed3i",
                mon: "Th\u1ee9 2",
                tue: "Th\u1ee9 3",
                wed: "Th\u1ee9 4",
                thu: "Th\u1ee9 5",
                fri: "Th\u1ee9 6",
                sat: "Th\u1ee9 7",
                sun: "Ch\u1ee7 nh\u1eadt",
                emptyTitle: "Ch\u01b0a c\u00f3 m\u1ee5c theo d\u00f5i n\u00e0o",
                emptyDesc: "Th\u00eam m\u1ee5c theo d\u00f5i \u0111\u1ec3 b\u1eaft \u0111\u1ea7u ghi nh\u1eadn check-in h\u1eb1ng ng\u00e0y."
            },
            toolNotes: {""".replace('\n', '\r\n')
    assert target_vi in c, "target_vi not found"
    c = c.replace(target_vi, replace_vi, 1)

    target_en = '        en: {\r\n            common: {'
    replace_en = """        en: {
            selfCheckWorkspace: {
                title: "Tempo Self-check",
                returnUrgent: "Return to Urgent Mode",
                returnRecovery: "Return to Recovery Mode",
                returnUnclear: "Return to Unclear Mode",
                returnHome: "Return Home",
                returnUrgentWithArrow: "Return to Urgent Mode",
                dailyCheckinUpper: "YOUR DAILY CHECK-IN",
                todaysCheckin: "Today's Check-in",
                streakDays: "{count}-day streak",
                sleepQuestion: "How was your sleep last night?",
                good: "Good",
                notGood: "Not good",
                walkQuestion: "Did you go for a walk today?",
                yes: "Yes",
                noIdidnt: "No, I didn't",
                createNoteForToday: "Create a note for today",
                checkedInCount: "You checked in on {completed} of {total} things.",
                yourTrackingSystem: "Your Tracking System",
                addTracking: "Add Tracking",
                clearAll: "Clear all",
                adjust: "Adjust",
                tension: "Tension",
                sleep: "Sleep",
                walk: "Walk",
                avgTensionLevel: "Your average tension level is",
                nightsQualitySleep: "Nights of Quality Sleep",
                totalLoggedThisWeek: "Total logged this week",
                avgRating: "Average rating",
                viewMyFullCheck: "View my full check",
                myWeeklyReport: "My weekly report",
                myRecoveryNotice: "My Recovery notice",
                mon: "Mon",
                tue: "Tue",
                wed: "Wed",
                thu: "Thu",
                fri: "Fri",
                sat: "Sat",
                sun: "Sun",
                emptyTitle: "No tracking items yet",
                emptyDesc: "Add a tracking item to start recording your daily check-ins."
            },
            common: {""".replace('\n', '\r\n')
    assert target_en in c, "target_en not found"
    c = c.replace(target_en, replace_en, 1)

    assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated after patch"
    with open('i18n.js', 'w', encoding='utf-8', newline='') as f:
        f.write(c)
    print("selfCheckWorkspace keys added successfully to i18n.js!")
else:
    print("selfCheckWorkspace already in i18n.js")
