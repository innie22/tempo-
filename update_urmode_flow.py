import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('urmodeFlow.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

# 1. Update closeModal to reset currentResetCase
target_close = '''        activeModalView = null;
        isSubmitting = false;'''

replacement_close = '''        activeModalView = null;
        currentResetCase = null;
        isSubmitting = false;'''

# 2. Update showResetPopup
target_popup = '''    // -------------------------------------------------------------------------
    // 1. RESET POPUP (On Explicit Entry)
    // -------------------------------------------------------------------------

    function showResetPopup() {
        const caseType = determinePlanCase();
        activeModalView = 'reset';

        let badgeText = 'GROUNDED START';
        let titleText = 'Take a moment to reset?';
        let bodyText = "Urgent situations feel much lighter when you pause first. Would you like a 2-minute reset to calm your nervous system before organizing your tasks?";
        let primaryBtnText = 'Yes, take a quick reset';
        let secondaryBtnText = 'Build my plan';

        if (caseType === 'PLAN_NO_OVERDUE') {
            badgeText = 'WORKING PLAN ACTIVE';
            titleText = 'Review and reset your Working Plan';
            bodyText = 'You already have an active Working Plan saved. Take a 2-minute reset to ground your focus, or review and keep your existing plan.';
            secondaryBtnText = 'Review your plan';
        } else if (caseType === 'PLAN_WITH_OVERDUE') {
            badgeText = 'PLAN UPDATE NEEDED';
            titleText = 'Review and reset your Working Plan';
            bodyText = 'You have tasks with overdue deadlines that need your attention. Take a quick reset to calm down, or review your tasks and adjust your schedule.';
            secondaryBtnText = 'Review your plan';
        }

        const html = `
            <!-- Header -->
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${badgeText}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${titleText}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.handleResetClose()"
                        aria-label="Close dialog"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="Close and stay in Urmode">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Mascot & Body Row -->
            <div class="flex flex-col sm:flex-row items-center sm:items-start gap-4 py-2">
                <div class="w-20 h-20 rounded-2xl bg-[#FFE9DC] flex items-center justify-center shrink-0 shadow-xs">
                    <img src="assets/practice-breathing-mascot.png" alt="Reset Breathing" class="w-16 h-16 object-contain pointer-events-none select-none" />
                </div>
                <div class="space-y-2 text-center sm:text-left">
                    <p class="text-sm sm:text-base text-[#484541] leading-relaxed">
                        ${bodyText}
                    </p>
                    <div class="text-xs text-[#8C8782] flex items-center justify-center sm:justify-start gap-2 pt-1">
                        <span>🌱 2 min box breathing</span>
                        <span>•</span>
                        <span>Grounds focus</span>
                        <span>•</span>
                        <span>No rush</span>
                    </div>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.handleResetNoOrPlan()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                    ${secondaryBtnText}
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.handleResetYes()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                    <span>${primaryBtnText} →</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }'''

replacement_popup = '''    // -------------------------------------------------------------------------
    // 1. RESET POPUP (On Explicit Entry)
    // -------------------------------------------------------------------------

    let currentResetCase = null;

    function showResetPopup(forcedCase) {
        const caseType = forcedCase || currentResetCase || determinePlanCase();
        currentResetCase = caseType;
        activeModalView = 'reset';

        const isVi = isViLocale();

        let badgeText = 'GROUNDED START';
        let titleText = 'Take a moment to reset?';
        let bodyText = "Urgent situations feel much lighter when you pause first. Would you like a 2-minute reset to calm your nervous system before organizing your tasks?";
        let primaryBtnText = isVi ? 'Có, tôi muốn lấy lại bình tĩnh một chút →' : 'Yes, take a quick reset →';
        let secondaryBtnText = 'Build my plan';

        if (caseType === 'PLAN_NO_OVERDUE') {
            badgeText = 'WORKING PLAN ACTIVE';
            titleText = window.t
                ? window.t('workspace.reviewAndResetWorkingPlanTitle', {}, isVi ? 'Xem lại và điều chỉnh plan của bạn' : 'Review and reset your Working Plan')
                : (isVi ? 'Xem lại và điều chỉnh plan của bạn' : 'Review and reset your Working Plan');
            bodyText = 'You already have an active Working Plan saved. Take a 2-minute reset to ground your focus, or review and keep your existing plan.';
            secondaryBtnText = window.t
                ? window.t('workspace.reviewYourPlanBtn', {}, isVi ? 'Xem lại plan' : 'Review your plan')
                : (isVi ? 'Xem lại plan' : 'Review your plan');
        } else if (caseType === 'PLAN_WITH_OVERDUE') {
            badgeText = window.t
                ? window.t('workspace.planUpdateNeededBadge', {}, isVi ? 'PLAN CẦN ĐƯỢC CẬP NHẬT' : 'PLAN UPDATE NEEDED')
                : (isVi ? 'PLAN CẦN ĐƯỢC CẬP NHẬT' : 'PLAN UPDATE NEEDED');
            titleText = window.t
                ? window.t('workspace.reviewAndResetWorkingPlanTitle', {}, isVi ? 'Xem lại và điều chỉnh plan của bạn' : 'Review and reset your Working Plan')
                : (isVi ? 'Xem lại và điều chỉnh plan của bạn' : 'Review and reset your Working Plan');
            bodyText = window.t
                ? window.t('workspace.planUpdateNeededBody', {}, isVi ? 'Bạn có một số task đã quá deadline cần được xem lại. Hãy dành chút thời gian để lấy lại bình tĩnh, hoặc xem lại các task và điều chỉnh lịch trình của mình nhé.' : 'You have tasks with overdue deadlines that need your attention. Take a quick reset to calm down, or review your tasks and adjust your schedule.')
                : (isVi ? 'Bạn có một số task đã quá deadline cần được xem lại. Hãy dành chút thời gian để lấy lại bình tĩnh, hoặc xem lại các task và điều chỉnh lịch trình của mình nhé.' : 'You have tasks with overdue deadlines that need your attention. Take a quick reset to calm down, or review your tasks and adjust your schedule.');
            secondaryBtnText = window.t
                ? window.t('workspace.reviewYourPlanBtn', {}, isVi ? 'Xem lại plan' : 'Review your plan')
                : (isVi ? 'Xem lại plan' : 'Review your plan');
            primaryBtnText = window.t
                ? window.t('workspace.yesTakeQuickResetBtn', {}, isVi ? 'Có, tôi muốn lấy lại bình tĩnh một chút →' : 'Yes, take a quick reset →')
                : (isVi ? 'Có, tôi muốn lấy lại bình tĩnh một chút →' : 'Yes, take a quick reset →');
        }

        const featureBoxBreathing = window.t
            ? window.t('workspace.boxBreathingFeature', {}, isVi ? 'Tập thở trong 2 phút' : '2 min box breathing')
            : (isVi ? 'Tập thở trong 2 phút' : '2 min box breathing');
        const featureGroundsFocus = window.t
            ? window.t('workspace.groundsFocusFeature', {}, isVi ? 'Giúp bạn lấy lại sự tập trung' : 'Grounds focus')
            : (isVi ? 'Giúp bạn lấy lại sự tập trung' : 'Grounds focus');
        const featureNoRush = window.t
            ? window.t('workspace.noRushFeature', {}, isVi ? 'Không cần vội' : 'No rush')
            : (isVi ? 'Không cần vội' : 'No rush');

        const primaryBtnFormatted = primaryBtnText.endsWith('→') ? primaryBtnText : (primaryBtnText + ' →');

        const html = `
            <!-- Header -->
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#D79277] block">
                        ${badgeText}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${titleText}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.handleResetClose()"
                        aria-label="${window.t ? window.t('common.close', {}, isVi ? 'Đóng' : 'Close dialog') : (isVi ? 'Đóng' : 'Close dialog')}"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="${window.t ? window.t('common.close', {}, isVi ? 'Đóng' : 'Close dialog') : (isVi ? 'Đóng' : 'Close dialog')}">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Mascot & Body Row -->
            <div class="flex flex-col sm:flex-row items-center sm:items-start gap-4 py-2">
                <div class="w-20 h-20 rounded-2xl bg-[#FFE9DC] flex items-center justify-center shrink-0 shadow-xs">
                    <img src="assets/practice-breathing-mascot.png" alt="Reset Breathing" class="w-16 h-16 object-contain pointer-events-none select-none" />
                </div>
                <div class="space-y-2 text-center sm:text-left">
                    <p class="text-sm sm:text-base text-[#484541] leading-relaxed">
                        ${bodyText}
                    </p>
                    <div class="text-xs text-[#8C8782] flex items-center justify-center sm:justify-start gap-2 pt-1">
                        <span>🌱 ${featureBoxBreathing}</span>
                        <span>•</span>
                        <span>${featureGroundsFocus}</span>
                        <span>•</span>
                        <span>${featureNoRush}</span>
                    </div>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.handleResetNoOrPlan()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                    ${secondaryBtnText}
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.handleResetYes()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                    <span>${primaryBtnFormatted}</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }'''

# 3. Update onLanguageChange
target_lang_change = '''    if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
        window.TempoI18n.onLanguageChange(() => {
            if (activeModalView === 'adjust_keep') {'''

replacement_lang_change = '''    if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
        window.TempoI18n.onLanguageChange(() => {
            if (activeModalView === 'reset') {
                showResetPopup(currentResetCase);
            } else if (activeModalView === 'adjust_keep') {'''

if target_close not in content:
    print('ERROR: target_close not found')
    sys.exit(1)

if target_popup not in content:
    print('ERROR: target_popup not found')
    sys.exit(1)

if target_lang_change not in content:
    print('ERROR: target_lang_change not found')
    sys.exit(1)

content = content.replace(target_close, replacement_close, 1)
content = content.replace(target_popup, replacement_popup, 1)
content = content.replace(target_lang_change, replacement_lang_change, 1)

with open('urmodeFlow.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print('Successfully updated urmodeFlow.js')
