/**
 * TEMPO WELLBEING — UCHECK: CES-D (CENTER FOR EPIDEMIOLOGIC STUDIES DEPRESSION SCALE)
 * File: cesdAssessment.js
 *
 * Implements the 20-item CES-D self-assessment under UCheck -> Depression Assessment:
 * 1. Test Information & Introduction:
 *    - Name: CES-D (Center for Epidemiologic Studies Depression Scale)
 *    - Category: Depression Assessment
 *    - 20 items, reference period: The past week (Tuần vừa qua)
 *    - Score range: 0–60
 *    - Purpose: Self-assessment of the frequency of depressive symptoms (screening tool, not diagnostic).
 *    - Vietnamese introduction working copy:
 *      "Dưới đây là danh sách những cảm xúc hoặc trạng thái mà bạn có thể đã trải qua. Hãy cho biết bạn đã cảm thấy như vậy thường xuyên đến mức nào trong tuần vừa qua."
 * 2. 4 Response Options (0 to 3) with working copy and reference periods:
 *    - 0: Hiếm khi hoặc không bao giờ (< 1 ngày)
 *    - 1: Một vài lần (1–2 ngày)
 *    - 2: Thỉnh thoảng hoặc ở mức độ vừa phải (3–4 ngày)
 *    - 3: Hầu hết hoặc toàn bộ thời gian (5–7 ngày)
 * 3. 20 Items in exact original order.
 * 4. Exact reverse-scoring for positive items 4, 8, 12, 16:
 *    - 0 -> 3, 1 -> 2, 2 -> 1, 3 -> 0.
 * 5. Exactly 2 Screening Interpretation Bands:
 *    - Score 0–15: Below the commonly used screening threshold (0–15)
 *    - Score 16–60: At or above the commonly used screening threshold (16–60)
 *    - Screening threshold = 16 (screening cutoff, not diagnostic).
 *    - Disclaimer displayed:
 *      "CES-D là công cụ sàng lọc triệu chứng, không phải công cụ chẩn đoán trầm cảm. Kết quả không thay thế cho đánh giá của chuyên gia. Ngưỡng điểm này chưa được xác nhận riêng cho sinh viên Việt Nam trong cấu hình hiện tại."
 * 6. Sequential 1-at-a-time navigation, answer preservation on Back/Forward, validation feedback.
 * 7. English UI conventions for shared chrome and navigation; Vietnamese working copy for clinical questions/items.
 * 8. User-scoped persistence under tempo_cesd_history_${uid}.
 */

(function () {
    'use strict';

    // =========================================================================
    // CONSTANTS & QUESTION DATA
    // =========================================================================

    // 1-based question numbers that are positive statements and must be reverse-scored
    const REVERSE_ITEMS = [4, 8, 12, 16];

    const CESD_QUESTIONS = [
        {
            id: 1,
            text: 'Tôi bị làm phiền bởi những điều mà bình thường không khiến tôi bận tâm.',
            isReverse: false
        },
        {
            id: 2,
            text: 'Tôi không muốn ăn; tôi ăn không ngon miệng.',
            isReverse: false
        },
        {
            id: 3,
            text: 'Tôi cảm thấy mình không thể thoát khỏi tâm trạng buồn bã, ngay cả khi có sự giúp đỡ từ gia đình hoặc bạn bè.',
            isReverse: false
        },
        {
            id: 4,
            text: 'Tôi cảm thấy mình cũng tốt như những người khác.',
            isReverse: true
        },
        {
            id: 5,
            text: 'Tôi gặp khó khăn trong việc tập trung vào những gì mình đang làm.',
            isReverse: false
        },
        {
            id: 6,
            text: 'Tôi cảm thấy chán nản, buồn bã.',
            isReverse: false
        },
        {
            id: 7,
            text: 'Tôi cảm thấy mọi việc mình làm đều đòi hỏi rất nhiều nỗ lực.',
            isReverse: false
        },
        {
            id: 8,
            text: 'Tôi cảm thấy hy vọng về tương lai.',
            isReverse: true
        },
        {
            id: 9,
            text: 'Tôi nghĩ rằng cuộc đời mình đã là một thất bại.',
            isReverse: false
        },
        {
            id: 10,
            text: 'Tôi cảm thấy sợ hãi.',
            isReverse: false
        },
        {
            id: 11,
            text: 'Tôi ngủ không yên giấc.',
            isReverse: false
        },
        {
            id: 12,
            text: 'Tôi cảm thấy hạnh phúc.',
            isReverse: true
        },
        {
            id: 13,
            text: 'Tôi nói ít hơn bình thường.',
            isReverse: false
        },
        {
            id: 14,
            text: 'Tôi cảm thấy cô đơn.',
            isReverse: false
        },
        {
            id: 15,
            text: 'Mọi người không thân thiện với tôi.',
            isReverse: false
        },
        {
            id: 16,
            text: 'Tôi tận hưởng cuộc sống.',
            isReverse: true
        },
        {
            id: 17,
            text: 'Tôi có những lúc bật khóc.',
            isReverse: false
        },
        {
            id: 18,
            text: 'Tôi cảm thấy buồn.',
            isReverse: false
        },
        {
            id: 19,
            text: 'Tôi cảm thấy mọi người không thích mình.',
            isReverse: false
        },
        {
            id: 20,
            text: 'Tôi cảm thấy mình không thể bắt đầu làm bất cứ việc gì.',
            isReverse: false
        }
    ];

    const CESD_OPTIONS = [
        {
            value: 0,
            label: 'Hiếm khi hoặc không bao giờ',
            period: 'Dưới 1 ngày'
        },
        {
            value: 1,
            label: 'Một vài lần',
            period: '1–2 ngày'
        },
        {
            value: 2,
            label: 'Thỉnh thoảng hoặc ở mức độ vừa phải',
            period: '3–4 ngày'
        },
        {
            value: 3,
            label: 'Hầu hết hoặc toàn bộ thời gian',
            period: '5–7 ngày'
        }
    ];

    const SCREENING_BANDS = {
        below_threshold: {
            key: 'below_threshold',
            min: 0,
            max: 15,
            title: 'Below the commonly used screening threshold',
            titleVi: 'Dưới ngưỡng sàng lọc thường dùng',
            badgeBg: '#EAF0EB',
            badgeText: '#4A6B5D',
            badgeBorder: '#BACAD0',
            descriptionVi: 'Điểm số của bạn nằm dưới ngưỡng sàng lọc thường dùng. Điều này không có nghĩa là bạn hoàn toàn không gặp khó khăn về sức khỏe tinh thần.',
            nextSteps: 'Tiếp tục theo dõi sức khỏe tinh thần và duy trì các thói quen chăm sóc bản thân hàng ngày. Nếu bạn bắt đầu cảm thấy căng thẳng hoặc mệt mỏi, hãy dành thời gian nghỉ ngơi và chia sẻ với người thân.'
        },
        at_or_above_threshold: {
            key: 'at_or_above_threshold',
            min: 16,
            max: 60,
            title: 'At or above the commonly used screening threshold',
            titleVi: 'Đạt hoặc vượt ngưỡng sàng lọc thường dùng',
            badgeBg: '#FEF3C7',
            badgeText: '#92400E',
            badgeBorder: '#FDE68A',
            descriptionVi: 'Điểm số của bạn đạt hoặc vượt ngưỡng sàng lọc thường dùng. Bạn có thể cân nhắc trao đổi với chuyên gia sức khỏe tinh thần để được đánh giá thêm.',
            nextSteps: 'Điểm số này cho thấy bạn đang trải qua các triệu chứng trầm cảm với tần suất cao hơn mức thông thường. Việc tìm kiếm sự hỗ trợ từ chuyên viên tâm lý hoặc bác sĩ có thể giúp bạn hiểu rõ hơn và có kế hoạch hỗ trợ phù hợp.'
        }
    };

    const DISCLAIMER_TEXT = 'CES-D là công cụ sàng lọc triệu chứng, không phải công cụ chẩn đoán trầm cảm. Kết quả không thay thế cho đánh giá của chuyên gia. Ngưỡng điểm này chưa được xác nhận riêng cho sinh viên Việt Nam trong cấu hình hiện tại.';

    // =========================================================================
    // STATE MODEL FOR CURRENT TEST ATTEMPT
    // =========================================================================

    let testState = {
        currentStep: 'intro', // 'intro' | 'question' | 'results'
        currentQuestionIndex: 0, // 0 to 19
        answers: new Array(20).fill(null), // 20 raw answers
        validationError: '',
        isSubmitting: false,
        completedResult: null
    };

    // =========================================================================
    // USER PERSISTENCE HELPERS
    // =========================================================================

    function getUserId() {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') {
            const uid = window.TempoAuth.getCurrentUserId();
            if (uid) return uid;
        }
        return 'local_user';
    }

    function getStorageKey() {
        const uid = getUserId();
        return `tempo_cesd_history_${uid}`;
    }

    function saveCompletedResult(resultData) {
        const key = getStorageKey();
        let history = [];
        try {
            history = JSON.parse(localStorage.getItem(key) || '[]');
        } catch (e) {}

        history.unshift(resultData);
        if (history.length > 30) history = history.slice(0, 30);
        localStorage.setItem(key, JSON.stringify(history));

        // Sync to general assessment history
        const uid = getUserId();
        const generalKey = `tempo_assessment_history_${uid}`;
        let generalHistory = [];
        try {
            generalHistory = JSON.parse(localStorage.getItem(generalKey) || '[]');
        } catch (e) {}
        generalHistory.unshift(resultData);
        if (generalHistory.length > 50) generalHistory = generalHistory.slice(0, 50);
        localStorage.setItem(generalKey, JSON.stringify(generalHistory));
    }

    function getLatestResult() {
        const key = getStorageKey();
        try {
            const history = JSON.parse(localStorage.getItem(key) || '[]');
            return history.length > 0 ? history[0] : null;
        } catch (e) {
            return null;
        }
    }

    // =========================================================================
    // SCORING LOGIC (TESTABLE & REUSABLE)
    // =========================================================================

    /**
     * Calculates the CES-D item score for a given question index and raw response.
     * Questions 4, 8, 12, 16 are reverse-scored: 0 -> 3, 1 -> 2, 2 -> 1, 3 -> 0.
     * All other questions retain their raw response score (0-3).
     */
    function calculateItemScore(questionNumber, rawValue) {
        if (typeof rawValue !== 'number' || rawValue < 0 || rawValue > 3) {
            return 0;
        }
        if (REVERSE_ITEMS.includes(questionNumber)) {
            return 3 - rawValue;
        }
        return rawValue;
    }

    /**
     * Calculates the final total CES-D score across all 20 items.
     * Returns an integer between 0 and 60.
     */
    function calculateTotalScore(answers) {
        if (!Array.isArray(answers)) return 0;
        let total = 0;
        for (let i = 0; i < 20; i++) {
            const raw = answers[i];
            const qNum = i + 1;
            total += calculateItemScore(qNum, raw);
        }
        return total;
    }

    /**
     * Determines the screening interpretation band (0-15 vs 16-60).
     */
    function getInterpretationBand(score) {
        if (score >= 16) {
            return SCREENING_BANDS.at_or_above_threshold;
        }
        return SCREENING_BANDS.below_threshold;
    }

    // =========================================================================
    // DOM MOUNTING & DIALOG MANAGEMENT
    // =========================================================================

    function ensureModalMounted() {
        if (!document.getElementById('modal-cesd-test')) {
            const modalEl = document.createElement('div');
            modalEl.id = 'modal-cesd-test';
            modalEl.className = 'fixed inset-0 z-[95] flex items-center justify-center modal-backdrop p-3 sm:p-4 hidden';
            modalEl.style.zIndex = '95';
            modalEl.setAttribute('role', 'dialog');
            modalEl.setAttribute('aria-modal', 'true');
            modalEl.innerHTML = `
                <div id="cesd-modal-card" 
                     class="tempo-card max-w-2xl w-full p-6 sm:p-8 space-y-6 rounded-3xl shadow-2xl relative border border-[#EAE4DF]/80 max-h-[94vh] overflow-y-auto"
                     style="background-color: #FEFAF4;">
                    <!-- Dynamically populated by renderModalContent() -->
                </div>
            `;
            document.body.appendChild(modalEl);
        }
    }

    // =========================================================================
    // TEST CONTROLLER & LIFECYCLE
    // =========================================================================

    function openTestModal() {
        ensureModalMounted();

        // Fresh test attempt initialization
        testState = {
            currentStep: 'intro',
            currentQuestionIndex: 0,
            answers: new Array(20).fill(null),
            validationError: '',
            isSubmitting: false,
            completedResult: null
        };

        renderModalContent();
        const modal = document.getElementById('modal-cesd-test');
        if (modal) modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    function closeTestModal(confirmIfInProgress = false) {
        if (confirmIfInProgress && testState.currentStep === 'question') {
            const hasAnyAnswer = testState.answers.some(a => a !== null);
            if (hasAnyAnswer) {
                const ok = window.confirm("Are you sure you want to leave the assessment? Your unsaved progress will be lost.");
                if (!ok) return;
            }
        }

        const modal = document.getElementById('modal-cesd-test');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    function startTest() {
        testState.currentStep = 'question';
        testState.currentQuestionIndex = 0;
        testState.validationError = '';
        renderModalContent();
    }

    function selectAnswer(val) {
        const qIdx = testState.currentQuestionIndex;
        testState.answers[qIdx] = val;
        testState.validationError = '';
        renderModalContent();
    }

    function handleNextQuestion() {
        const qIdx = testState.currentQuestionIndex;
        const currentAns = testState.answers[qIdx];

        if (currentAns === null || currentAns === undefined) {
            testState.validationError = 'Please select an answer before continuing.';
            renderModalContent();
            return;
        }

        testState.validationError = '';

        if (qIdx === 19) {
            // Last question: submit assessment
            submitAssessment();
            return;
        }

        testState.currentQuestionIndex = qIdx + 1;
        renderModalContent();
    }

    function handlePrevQuestion() {
        testState.validationError = '';
        if (testState.currentStep === 'question' && testState.currentQuestionIndex > 0) {
            testState.currentQuestionIndex -= 1;
            renderModalContent();
        }
    }

    function submitAssessment() {
        if (testState.isSubmitting) return;

        // Verify all 20 questions are answered exactly once
        const unansweredIdx = testState.answers.findIndex(a => a === null || a === undefined);
        if (unansweredIdx !== -1) {
            testState.currentQuestionIndex = unansweredIdx;
            testState.validationError = `Question ${unansweredIdx + 1} has not been answered yet. Please provide a response.`;
            renderModalContent();
            return;
        }

        testState.isSubmitting = true;

        const totalScore = calculateTotalScore(testState.answers);
        const band = getInterpretationBand(totalScore);

        // Calculate item-by-item scored breakdown
        const itemScores = testState.answers.map((raw, idx) => calculateItemScore(idx + 1, raw));

        const resultRecord = {
            id: 'cesd_' + Date.now(),
            testId: 'ces-d',
            testName: 'CES-D — Center for Epidemiologic Studies Depression Scale',
            completedAt: new Date().toISOString(),
            score: totalScore,
            maxScore: 60,
            interpretationKey: band.key,
            interpretationTitle: band.title,
            interpretationTitleVi: band.titleVi,
            answers: [...testState.answers],
            itemScores: itemScores
        };

        testState.completedResult = resultRecord;
        testState.currentStep = 'results';
        testState.isSubmitting = false;

        saveCompletedResult(resultRecord);

        // Refresh UCheck category UI if visible
        if (window.TempoExploreAssessments && typeof window.TempoExploreAssessments.render === 'function') {
            window.TempoExploreAssessments.render();
        }

        renderModalContent();
    }

    function returnToUCheck() {
        closeTestModal(false);
        if (window.TempoExploreAssessments && typeof window.TempoExploreAssessments.selectCategory === 'function') {
            window.TempoExploreAssessments.selectCategory('depression');
        }
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('explore-mental-health-tests', 'depression');
        } else {
            window.location.hash = '#explore-mental-health-tests?category=depression';
        }
    }

    // =========================================================================
    // MODAL VIEW RENDERERS (INTRO, QUESTION, RESULTS)
    // =========================================================================

    function renderModalContent() {
        const card = document.getElementById('cesd-modal-card');
        if (!card) return;

        switch (testState.currentStep) {
            case 'intro':
                card.innerHTML = renderIntroHTML();
                break;
            case 'question':
                card.innerHTML = renderQuestionHTML();
                break;
            case 'results':
                card.innerHTML = renderResultsHTML();
                break;
            default:
                card.innerHTML = renderIntroHTML();
        }
    }

    function renderIntroHTML() {
        const latest = getLatestResult();
        let prevResultNotice = '';
        if (latest) {
            const dt = new Date(latest.completedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            prevResultNotice = `
                <div class="p-3.5 bg-[#F4F7F5] rounded-2xl border border-[#CDE9DA] text-xs text-[#284132] flex items-center justify-between">
                    <span>Latest assessment: <strong>${latest.score} / 60 (${escapeHTML(latest.interpretationTitleVi)})</strong> on ${dt}</span>
                    <span class="text-[11px] font-bold text-[#4A6B5D]">Saved History</span>
                </div>
            `;
        }

        return `
            <!-- Top Close Button -->
            <button type="button" 
                    onclick="window.TempoCESD.closeTestModal(false)" 
                    class="absolute top-5 right-5 w-8 h-8 rounded-full flex items-center justify-center text-[#8C8681] hover:text-[#202124] hover:bg-stone-200/50 text-base transition cursor-pointer" 
                    title="Close">✕</button>

            <!-- Navigation Breadcrumb -->
            <div class="flex items-center space-x-2 text-xs font-bold text-[#829B87] uppercase tracking-wider">
                <span>UCheck</span>
                <span>•</span>
                <span>Depression Assessment</span>
            </div>

            <!-- Test Title & Header -->
            <div class="space-y-1.5">
                <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                    CES-D
                </h2>
                <p class="text-sm font-semibold text-[#829B87]">
                    Center for Epidemiologic Studies Depression Scale
                </p>
                <p class="text-xs sm:text-sm text-[#5B5550] leading-relaxed pt-1">
                    Self-assessment of the frequency of depressive symptoms.
                </p>
            </div>

            ${prevResultNotice}

            <!-- Vietnamese Working Introduction Notice -->
            <div class="p-4 bg-white rounded-2xl border border-stone-200/80 space-y-2 shadow-2xs">
                <span class="text-xs font-bold text-[#202124] flex items-center space-x-1.5">
                    <span>📋</span>
                    <span>Hướng dẫn làm bài (Working Copy)</span>
                </span>
                <p class="text-xs sm:text-sm text-[#484541] italic leading-relaxed">
                    “Dưới đây là danh sách những cảm xúc hoặc trạng thái mà bạn có thể đã trải qua. Hãy cho biết bạn đã cảm thấy như vậy thường xuyên đến mức nào trong tuần vừa qua.”
                </p>
            </div>

            <!-- Test Key Details -->
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div class="bg-white rounded-2xl border border-stone-200/80 p-3.5 space-y-1 shadow-2xs">
                    <span class="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Questions</span>
                    <p class="text-sm font-bold text-[#202124]">20 items</p>
                </div>
                <div class="bg-white rounded-2xl border border-stone-200/80 p-3.5 space-y-1 shadow-2xs">
                    <span class="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Reference Period</span>
                    <p class="text-sm font-bold text-[#202124]">The past week</p>
                </div>
                <div class="bg-white rounded-2xl border border-stone-200/80 p-3.5 space-y-1 shadow-2xs">
                    <span class="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Score Range</span>
                    <p class="text-sm font-bold text-[#202124]">0 – 60</p>
                </div>
            </div>

            <!-- Important Screening Limitation Disclaimer -->
            <div class="p-4 bg-stone-50 rounded-2xl border border-stone-200/70 text-xs text-[#6F6B68] leading-relaxed">
                ℹ️ <strong>Important Limitation:</strong> This is a self-assessment screening tool designed for personal reflection. It is <strong>not a diagnostic instrument</strong> and does not substitute for a professional clinical evaluation.
            </div>

            <!-- Bottom Actions -->
            <div class="pt-4 border-t border-stone-200/80 flex items-center justify-between">
                <button type="button" 
                        onclick="window.TempoCESD.closeTestModal(false)" 
                        class="px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-600 hover:text-stone-900 transition cursor-pointer">
                    Back to UCheck
                </button>
                <button type="button" 
                        id="btn-cesd-start-test"
                        onclick="window.TempoCESD.startTest()" 
                        class="px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#829B87] hover:bg-[#728A77] text-white shadow-xs transition cursor-pointer">
                    Start Assessment →
                </button>
            </div>
        `;
    }

    function renderQuestionHTML() {
        const qIdx = testState.currentQuestionIndex;
        const q = CESD_QUESTIONS[qIdx];
        const selectedVal = testState.answers[qIdx];
        const isAnswered = selectedVal !== null && selectedVal !== undefined;
        const progressPct = Math.round(((qIdx + 1) / 20) * 100);

        return `
            <!-- Top Controls: Question Counter & Exit -->
            <div class="flex items-center justify-between text-xs">
                <div class="flex items-center space-x-2">
                    <span class="font-extrabold text-[#4A6B5D] text-xs uppercase tracking-wider">Question ${qIdx + 1} of 20</span>
                    <span class="text-stone-400">•</span>
                    <span class="text-stone-500 font-medium">The past week</span>
                </div>
                <button type="button" 
                        onclick="window.TempoCESD.closeTestModal(true)" 
                        class="text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer" 
                        title="Exit assessment">Exit</button>
            </div>

            <!-- Progress Bar -->
            <div class="w-full bg-stone-200/80 h-2 rounded-full overflow-hidden">
                <div class="bg-[#829B87] h-full transition-all duration-300 rounded-full" style="width: ${progressPct}%;"></div>
            </div>

            <!-- Question Statement -->
            <div class="space-y-1.5 py-1">
                <span class="text-xs text-stone-400 font-semibold uppercase tracking-wider">Trong tuần vừa qua:</span>
                <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124] leading-snug">
                    ${escapeHTML(q.text)}
                </h3>
            </div>

            <!-- Validation Feedback (if triggered) -->
            ${testState.validationError ? `
                <div class="p-3 bg-red-50 border border-red-200 rounded-xl text-xs font-semibold text-[#D92D20] flex items-center space-x-2">
                    <span>⚠️</span>
                    <span>${escapeHTML(testState.validationError)}</span>
                </div>
            ` : ''}

            <!-- 4 Response Options -->
            <div class="space-y-2.5 pt-1">
                ${CESD_OPTIONS.map(opt => {
                    const isSelected = selectedVal === opt.value;
                    return `
                        <div onclick="window.TempoCESD.selectAnswer(${opt.value})" 
                             class="p-3.5 sm:p-4 rounded-2xl border transition cursor-pointer flex items-center justify-between select-none ${
                                 isSelected 
                                     ? 'bg-[#EAF0EB] border-2 border-[#4A6B5D] text-[#284132] font-bold shadow-xs' 
                                     : 'bg-white border-stone-200 hover:border-stone-400 text-[#484541] hover:bg-stone-50/70'
                             }">
                            <div class="space-y-0.5 pr-2">
                                <div class="text-xs sm:text-sm font-semibold">
                                    <span class="font-bold text-stone-400 mr-1.5">${opt.value} —</span>
                                    <span>${escapeHTML(opt.label)}</span>
                                </div>
                                <div class="text-[11px] text-stone-500">
                                    Khoảng thời gian: <span class="font-medium text-stone-700">${escapeHTML(opt.period)}</span>
                                </div>
                            </div>
                            <div class="w-5 h-5 rounded-full border flex items-center justify-center shrink-0 ${
                                isSelected ? 'border-[#4A6B5D] bg-[#4A6B5D] text-white' : 'border-stone-300 bg-white'
                            }">
                                ${isSelected ? '✓' : ''}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>

            <!-- Bottom Navigation Controls -->
            <div class="pt-4 border-t border-stone-200/80 flex items-center justify-between">
                <button type="button" 
                        onclick="window.TempoCESD.handlePrevQuestion()" 
                        class="px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition cursor-pointer ${
                            qIdx === 0 
                                ? 'opacity-30 pointer-events-none text-stone-400' 
                                : 'text-stone-600 hover:text-stone-900 bg-white border border-stone-200'
                        }">
                    ← Back
                </button>
                <button type="button" 
                        id="btn-cesd-next-question"
                        onclick="window.TempoCESD.handleNextQuestion()" 
                        class="px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold shadow-xs transition cursor-pointer ${
                            isAnswered 
                                ? 'bg-[#829B87] hover:bg-[#728A77] text-white' 
                                : 'bg-stone-300 text-stone-500 opacity-60 cursor-not-allowed'
                        }">
                    ${qIdx === 19 ? 'Submit Assessment' : 'Next Question →'}
                </button>
            </div>
        `;
    }

    function renderResultsHTML() {
        const res = testState.completedResult || getLatestResult();
        if (!res) return renderIntroHTML();

        const score = res.score;
        const band = getInterpretationBand(score);

        return `
            <!-- Top Exit Button -->
            <button type="button" 
                    onclick="window.TempoCESD.closeTestModal(false)" 
                    class="absolute top-5 right-5 w-8 h-8 rounded-full flex items-center justify-center text-[#8C8681] hover:text-[#202124] hover:bg-stone-200/50 text-base transition cursor-pointer" 
                    title="Close">✕</button>

            <!-- Header Badge -->
            <div class="flex items-center space-x-2 text-xs font-bold text-[#829B87] uppercase tracking-wider">
                <span>Assessment Results</span>
                <span>•</span>
                <span>CES-D</span>
            </div>

            <div class="space-y-1">
                <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                    CES-D Assessment Results
                </h2>
                <p class="text-xs sm:text-sm text-[#5B5550]">
                    Center for Epidemiologic Studies Depression Scale • Based on your responses for the past week.
                </p>
            </div>

            <!-- Score & Interpretation Card -->
            <div class="p-5 sm:p-6 rounded-3xl border border-stone-200/80 bg-white space-y-4 shadow-2xs">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-stone-200/60">
                    <div>
                        <span class="text-xs text-stone-400 font-semibold uppercase tracking-wider">Total Score</span>
                        <div class="flex items-baseline space-x-2 pt-0.5">
                            <span class="font-heading text-3xl sm:text-4xl font-extrabold text-[#202124]">${score}</span>
                            <span class="text-sm font-bold text-stone-400">/ 60 points</span>
                        </div>
                    </div>
                    <div>
                        <span class="text-xs text-stone-400 font-semibold uppercase tracking-wider">Screening Band</span>
                        <div class="pt-1">
                            <span class="inline-block px-3.5 py-1.5 rounded-full text-xs font-extrabold border"
                                  style="background-color: ${band.badgeBg}; color: ${band.badgeText}; border-color: ${band.badgeBorder};">
                                ${escapeHTML(band.titleVi)}
                            </span>
                        </div>
                    </div>
                </div>

                <div class="space-y-1.5">
                    <h4 class="text-xs font-bold text-[#202124] uppercase tracking-wider">Screening Interpretation</h4>
                    <p class="text-xs sm:text-sm text-[#5B5550] leading-relaxed">
                        ${escapeHTML(band.descriptionVi)}
                    </p>
                </div>
            </div>

            <!-- Supportive Next Steps -->
            <div class="bg-[#F4F7F5] rounded-2xl border border-[#CDE9DA] p-4 sm:p-5 space-y-2 shadow-2xs">
                <span class="text-xs font-bold text-[#202124] flex items-center space-x-1.5">
                    <span>🌱</span>
                    <span>Supportive Next Steps</span>
                </span>
                <p class="text-xs sm:text-sm text-[#384F43] leading-relaxed">
                    ${escapeHTML(band.nextSteps)}
                </p>
            </div>

            <!-- Mandatory Screening Disclaimer -->
            <div class="p-4 bg-stone-50 rounded-2xl border border-stone-200/70 text-xs text-[#6F6B68] leading-relaxed">
                ℹ️ <strong>Screening Disclaimer:</strong> ${escapeHTML(DISCLAIMER_TEXT)}
            </div>

            <!-- Bottom Actions -->
            <div class="pt-4 border-t border-stone-200/80 flex flex-col sm:flex-row items-center justify-between gap-3">
                <button type="button" 
                        onclick="window.TempoCESD.startTest()" 
                        class="w-full sm:w-auto px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-600 hover:text-stone-900 bg-white border border-stone-200 transition cursor-pointer text-center">
                    Retake Assessment
                </button>
                <button type="button" 
                        onclick="window.TempoCESD.returnToUCheck()" 
                        class="w-full sm:w-auto px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#829B87] hover:bg-[#728A77] text-white shadow-xs transition cursor-pointer text-center">
                    Return to UCheck →
                </button>
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

    // =========================================================================
    // EXPORTS
    // =========================================================================

    window.TempoCESD = {
        CESD_QUESTIONS,
        CESD_OPTIONS,
        REVERSE_ITEMS,
        SCREENING_BANDS,
        DISCLAIMER_TEXT,
        calculateItemScore,
        calculateTotalScore,
        getInterpretationBand,
        getLatestResult,
        saveCompletedResult,
        openTestModal,
        closeTestModal,
        startTest,
        selectAnswer,
        handleNextQuestion,
        handlePrevQuestion,
        submitAssessment,
        returnToUCheck,
        // State getters & test helpers
        getTestState: () => Object.assign({}, testState, {
            answers: [...testState.answers]
        }),
        _setTestState: (partial) => {
            Object.assign(testState, partial);
            renderModalContent();
        }
    };

})();
