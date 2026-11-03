import os

# 1. Update i18n.js
with open('i18n.js', 'r', encoding='utf-8') as f:
    i18n_code = f.read()

vi_target = '                planUpdateNeededBadge: "PLAN CẦN ĐƯỢC CẬP NHẬT",'
vi_replacement = '''                workingPlanActiveBadge: "PLAN ĐANG HOẠT ĐỘNG",
                workingPlanActiveBody: "Bạn đã có một plan đang hoạt động. Hãy dành 2 phút tập thở để lấy lại sự tập trung, hoặc xem lại và tiếp tục kế hoạch hiện tại của bạn.",
                groundedStartBadge: "KHỞI ĐẦU ĐIỀM TĨNH",
                groundedStartTitle: "Dành một chút thời gian để lấy lại bình tĩnh?",
                groundedStartBody: "Những tình huống khẩn cấp sẽ nhẹ nhàng hơn rất nhiều khi bạn tạm dừng lại một chút. Bạn có muốn dành 2 phút tập thở để làm dịu thần kinh trước khi sắp xếp các task không?",
                buildMyPlanBtn: "Lên plan của tôi",
                groundedCheckpointBadge: "ĐIỂM DỪNG ĐIỀM TĨNH",
                areYouReadyTitle: "Bạn đã sẵn sàng chưa?",
                areYouReadyBody: "Bạn vừa dành thời gian để thở và lấy lại bình tĩnh. Bạn cảm thấy thế nào về việc bắt đầu với Kế hoạch Làm việc bây giờ?",
                areYouReadySub: "Nếu bạn vẫn cảm thấy quá tải, bạn có thể quay lại nghỉ ngơi thêm bất cứ lúc nào.",
                notYetReturnResetBtn: "Chưa, quay lại tập thở",
                yesImReadyBtn: "Có, tôi đã sẵn sàng →",
                planUpdateNeededBadge: "PLAN CẦN ĐƯỢC CẬP NHẬT",'''

assert vi_target in i18n_code, "vi_target not found in i18n.js"
i18n_code = i18n_code.replace(vi_target, vi_replacement, 1)

en_target = '                planUpdateNeededBadge: "PLAN UPDATE NEEDED",'
en_replacement = '''                workingPlanActiveBadge: "WORKING PLAN ACTIVE",
                workingPlanActiveBody: "You already have an active Working Plan saved. Take a 2-minute reset to ground your focus, or review and keep your existing plan.",
                groundedStartBadge: "GROUNDED START",
                groundedStartTitle: "Take a moment to reset?",
                groundedStartBody: "Urgent situations feel much lighter when you pause first. Would you like a 2-minute reset to calm your nervous system before organizing your tasks?",
                buildMyPlanBtn: "Build my plan",
                groundedCheckpointBadge: "GROUNDED CHECKPOINT",
                areYouReadyTitle: "Are you ready?",
                areYouReadyBody: "You took a moment to breathe and reset. How do you feel about moving into your Working Plan now?",
                areYouReadySub: "If you still feel overwhelmed, you can return to take another pause or rest anytime.",
                notYetReturnResetBtn: "Not yet, return to reset",
                yesImReadyBtn: "Yes, I'm ready →",
                planUpdateNeededBadge: "PLAN UPDATE NEEDED",'''

assert en_target in i18n_code, "en_target not found in i18n.js"
i18n_code = i18n_code.replace(en_target, en_replacement, 1)

i18n_code = i18n_code.replace('\r\n', '\n')
assert '\r' not in i18n_code, "CRLF found in i18n.js"

with open('i18n.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(i18n_code)
print("i18n.js updated successfully")


# 2. Update urmodeFlow.js
with open('urmodeFlow.js', 'r', encoding='utf-8') as f:
    flow_code = f.read()

target_reset_popup = """    function showResetPopup(forcedCase) {
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

        const primaryBtnFormatted = primaryBtnText.endsWith('→') ? primaryBtnText : (primaryBtnText + ' →');"""

refined_reset_popup = """    function showResetPopup(forcedCase) {
        const caseType = forcedCase || currentResetCase || determinePlanCase();
        currentResetCase = caseType;
        activeModalView = 'reset';

        const isVi = isViLocale();

        let badgeText = '';
        let titleText = '';
        let bodyText = '';
        let primaryBtnText = window.t
            ? window.t('workspace.yesTakeQuickResetBtn', {}, isVi ? 'Có, tôi muốn lấy lại bình tĩnh một chút →' : 'Yes, take a quick reset →')
            : (isVi ? 'Có, tôi muốn lấy lại bình tĩnh một chút →' : 'Yes, take a quick reset →');
        let secondaryBtnText = '';

        if (caseType === 'PLAN_NO_OVERDUE') {
            badgeText = window.t
                ? window.t('workspace.workingPlanActiveBadge', {}, isVi ? 'PLAN ĐANG HOẠT ĐỘNG' : 'WORKING PLAN ACTIVE')
                : (isVi ? 'PLAN ĐANG HOẠT ĐỘNG' : 'WORKING PLAN ACTIVE');
            titleText = window.t
                ? window.t('workspace.reviewAndResetWorkingPlanTitle', {}, isVi ? 'Xem lại và điều chỉnh plan của bạn' : 'Review and reset your Working Plan')
                : (isVi ? 'Xem lại và điều chỉnh plan của bạn' : 'Review and reset your Working Plan');
            bodyText = window.t
                ? window.t('workspace.workingPlanActiveBody', {}, isVi ? 'Bạn đã có một plan đang hoạt động. Hãy dành 2 phút tập thở để lấy lại sự tập trung, hoặc xem lại và tiếp tục kế hoạch hiện tại của bạn.' : 'You already have an active Working Plan saved. Take a 2-minute reset to ground your focus, or review and keep your existing plan.')
                : (isVi ? 'Bạn đã có một plan đang hoạt động. Hãy dành 2 phút tập thở để lấy lại sự tập trung, hoặc xem lại và tiếp tục kế hoạch hiện tại của bạn.' : 'You already have an active Working Plan saved. Take a 2-minute reset to ground your focus, or review and keep your existing plan.');
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
        } else {
            // NO_PLAN
            badgeText = window.t
                ? window.t('workspace.groundedStartBadge', {}, isVi ? 'KHỞI ĐẦU ĐIỀM TĨNH' : 'GROUNDED START')
                : (isVi ? 'KHỞI ĐẦU ĐIỀM TĨNH' : 'GROUNDED START');
            titleText = window.t
                ? window.t('workspace.groundedStartTitle', {}, isVi ? 'Dành một chút thời gian để lấy lại bình tĩnh?' : 'Take a moment to reset?')
                : (isVi ? 'Dành một chút thời gian để lấy lại bình tĩnh?' : 'Take a moment to reset?');
            bodyText = window.t
                ? window.t('workspace.groundedStartBody', {}, isVi ? 'Những tình huống khẩn cấp sẽ nhẹ nhàng hơn rất nhiều khi bạn tạm dừng lại một chút. Bạn có muốn dành 2 phút tập thở để làm dịu thần kinh trước khi sắp xếp các task không?' : 'Urgent situations feel much lighter when you pause first. Would you like a 2-minute reset to calm your nervous system before organizing your tasks?')
                : (isVi ? 'Những tình huống khẩn cấp sẽ nhẹ nhàng hơn rất nhiều khi bạn tạm dừng lại một chút. Bạn có muốn dành 2 phút tập thở để làm dịu thần kinh trước khi sắp xếp các task không?' : 'Urgent situations feel much lighter when you pause first. Would you like a 2-minute reset to calm your nervous system before organizing your tasks?');
            secondaryBtnText = window.t
                ? window.t('workspace.buildMyPlanBtn', {}, isVi ? 'Lên plan của tôi' : 'Build my plan')
                : (isVi ? 'Lên plan của tôi' : 'Build my plan');
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

        const primaryBtnFormatted = primaryBtnText.endsWith('→') ? primaryBtnText : (primaryBtnText + ' →');"""

assert target_reset_popup in flow_code, "target_reset_popup not found in urmodeFlow.js"
flow_code = flow_code.replace(target_reset_popup, refined_reset_popup, 1)

target_are_you_ready = """    function showAreYouReadyPopup() {
        activeModalView = 'are_you_ready';
        const caseType = determinePlanCase();

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-emerald-700 block">
                        GROUNDED CHECKPOINT
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        Are you ready?
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        aria-label="Close dialog"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <div class="py-3 text-center sm:text-left space-y-2">
                <p class="text-sm sm:text-base text-[#484541] leading-relaxed">
                    You took a moment to breathe and reset. How do you feel about moving into your Working Plan now?
                </p>
                <p class="text-xs text-[#8C8782]">
                    If you still feel overwhelmed, you can return to take another pause or rest anytime.
                </p>
            </div>

            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.showResetPopup()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                    Not yet, return to reset
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.handleAreYouReadyYes()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                    <span>Yes, I'm ready →</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }"""

refined_are_you_ready = """    function showAreYouReadyPopup() {
        activeModalView = 'are_you_ready';
        const caseType = determinePlanCase();
        const isVi = isViLocale();

        const badgeText = window.t
            ? window.t('workspace.groundedCheckpointBadge', {}, isVi ? 'ĐIỂM DỪNG ĐIỀM TĨNH' : 'GROUNDED CHECKPOINT')
            : (isVi ? 'ĐIỂM DỪNG ĐIỀM TĨNH' : 'GROUNDED CHECKPOINT');
        const titleText = window.t
            ? window.t('workspace.areYouReadyTitle', {}, isVi ? 'Bạn đã sẵn sàng chưa?' : 'Are you ready?')
            : (isVi ? 'Bạn đã sẵn sàng chưa?' : 'Are you ready?');
        const bodyText = window.t
            ? window.t('workspace.areYouReadyBody', {}, isVi ? 'Bạn vừa dành thời gian để thở và lấy lại bình tĩnh. Bạn cảm thấy thế nào về việc bắt đầu với Kế hoạch Làm việc bây giờ?' : 'You took a moment to breathe and reset. How do you feel about moving into your Working Plan now?')
            : (isVi ? 'Bạn vừa dành thời gian để thở và lấy lại bình tĩnh. Bạn cảm thấy thế nào về việc bắt đầu với Kế hoạch Làm việc bây giờ?' : 'You took a moment to breathe and reset. How do you feel about moving into your Working Plan now?');
        const subText = window.t
            ? window.t('workspace.areYouReadySub', {}, isVi ? 'Nếu bạn vẫn cảm thấy quá tải, bạn có thể quay lại nghỉ ngơi thêm bất cứ lúc nào.' : 'If you still feel overwhelmed, you can return to take another pause or rest anytime.')
            : (isVi ? 'Nếu bạn vẫn cảm thấy quá tải, bạn có thể quay lại nghỉ ngơi thêm bất cứ lúc nào.' : 'If you still feel overwhelmed, you can return to take another pause or rest anytime.');
        const notYetBtnText = window.t
            ? window.t('workspace.notYetReturnResetBtn', {}, isVi ? 'Chưa, quay lại tập thở' : 'Not yet, return to reset')
            : (isVi ? 'Chưa, quay lại tập thở' : 'Not yet, return to reset');
        const readyBtnText = window.t
            ? window.t('workspace.yesImReadyBtn', {}, isVi ? 'Có, tôi đã sẵn sàng →' : "Yes, I'm ready →")
            : (isVi ? 'Có, tôi đã sẵn sàng →' : "Yes, I'm ready →");
        const closeBtnText = window.t
            ? window.t('common.close', {}, isVi ? 'Đóng' : 'Close dialog')
            : (isVi ? 'Đóng' : 'Close dialog');

        const html = `
            <div class="flex items-start justify-between pb-3 border-b border-[#EAE4DF]/80 gap-4">
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-emerald-700 block">
                        ${badgeText}
                    </span>
                    <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-snug tracking-tight">
                        ${titleText}
                    </h2>
                </div>
                <button type="button" onclick="window.TempoUrmodeFlow.closeModal('dashboard')"
                        aria-label="${escapeHTML(closeBtnText)}"
                        class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF]/60 p-2 rounded-full transition-colors shrink-0 cursor-pointer"
                        title="${escapeHTML(closeBtnText)}">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <div class="py-3 text-center sm:text-left space-y-2">
                <p class="text-sm sm:text-base text-[#484541] leading-relaxed">
                    ${bodyText}
                </p>
                <p class="text-xs text-[#8C8782]">
                    ${subText}
                </p>
            </div>

            <div class="pt-4 border-t border-[#EAE4DF]/80 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="window.TempoUrmodeFlow.showResetPopup()"
                        class="w-full sm:w-auto px-5 py-2.5 rounded-2xl font-bold text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center justify-center transition cursor-pointer">
                    ${notYetBtnText}
                </button>
                <button type="button" onclick="window.TempoUrmodeFlow.handleAreYouReadyYes()"
                        class="w-full sm:w-auto btn-primary btn-terracotta px-6 py-2.5 rounded-2xl font-bold text-sm shadow-sm inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                    <span>${readyBtnText}</span>
                </button>
            </div>
        `;

        showModalContent(html);
    }"""

assert target_are_you_ready in flow_code, "target_are_you_ready not found in urmodeFlow.js"
flow_code = flow_code.replace(target_are_you_ready, refined_are_you_ready, 1)

# Language change listener support for are_you_ready
target_lang_listener = """            if (activeModalView === 'reset') {
                showResetPopup(currentResetCase);
            } else if (activeModalView === 'review_summary') {"""

refined_lang_listener = """            if (activeModalView === 'reset') {
                showResetPopup(currentResetCase);
            } else if (activeModalView === 'are_you_ready') {
                showAreYouReadyPopup();
            } else if (activeModalView === 'review_summary') {"""

assert target_lang_listener in flow_code, "target_lang_listener not found in urmodeFlow.js"
flow_code = flow_code.replace(target_lang_listener, refined_lang_listener, 1)

flow_code = flow_code.replace('\r\n', '\n')
assert '\r' not in flow_code, "CRLF found in urmodeFlow.js"

with open('urmodeFlow.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(flow_code)
print("urmodeFlow.js updated successfully")
