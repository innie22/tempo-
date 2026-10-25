/**
 * TEMPO WELLBEING — UCHECK: GAD-7 (GENERALIZED ANXIETY DISORDER-7)
 * File: gad7Assessment.js
 *
 * Implements the 7-item GAD-7 self-assessment under UCheck -> Anxiety Assessment:
 * 1. Test Information & Introduction:
 *    - Name: GAD-7
 *    - Full Name: Generalized Anxiety Disorder-7
 *    - Category: Anxiety Assessment
 *    - 7 items, reference period: The past two weeks (2 tuần vừa qua)
 *    - Score range: 0–21
 *    - Purpose: Screening for anxiety symptoms (screening tool, not diagnostic instrument).
 *    - Vietnamese introduction working copy:
 *      "Trong 2 tuần vừa qua, bạn thường xuyên bị làm phiền bởi những vấn đề sau đây ở mức độ nào?"
 * 2. 4 Response Options (0 to 3) for every question:
 *    - 0: Không hề
 *    - 1: Một vài ngày
 *    - 2: Hơn một nửa số ngày
 *    - 3: Gần như mỗi ngày
 * 3. 7 Questions in exact original order.
 * 4. Standard Scoring Logic:
 *    - Each item receives 0, 1, 2, or 3 points.
 *    - Sum the seven item scores (range: 0–21).
 *    - No reverse-scoring. No multiplication or transformation factor.
 * 5. Exactly 4 Screening Interpretation Bands:
 *    - 0–4: Minimal (Tối thiểu)
 *    - 5–9: Mild (Nhẹ)
 *    - 10–14: Moderate (Trung bình)
 *    - 15–21: Severe (Nặng)
 *    - Screening cutoff = 10 (commonly used threshold for considering further assessment).
 *    - Supportive, non-diagnostic result explanation:
 *      Scores 0–9: "Kết quả của bạn nằm trong khoảng điểm từ tối thiểu đến nhẹ trên thang sàng lọc này. Điểm số không phản ánh toàn bộ sức khỏe tinh thần của bạn."
 *      Scores 10–21: "Kết quả của bạn cho thấy các triệu chứng lo âu có thể cần được đánh giá thêm. Bạn có thể cân nhắc trao đổi với chuyên gia sức khỏe tinh thần để được hỗ trợ phù hợp."
 *    - Mandatory disclaimer on results screen:
 *      "GAD-7 là công cụ sàng lọc triệu chứng, không phải công cụ chẩn đoán. Kết quả không thay thế cho đánh giá của chuyên gia."
 * 6. Safety & UX:
 *    - Does NOT interpret score as diagnosis.
 *    - Does NOT trigger Tempo SOS flow solely because of GAD-7 total score.
 *    - No invented crisis hotlines or phone numbers.
 *    - Sequential 1-at-a-time navigation, answer preservation on Back/Forward, validation feedback.
 * 7. English UI conventions for shared chrome and navigation; Vietnamese working copy for clinical questionnaire items.
 * 8. User-scoped persistence under tempo_gad7_history_${uid}.
 */

(function () {
    'use strict';

    // =========================================================================
    // CONSTANTS & QUESTION DATA
    // =========================================================================

    const GAD7_QUESTIONS = [
        {
            id: 1,
            text: 'Cảm thấy lo lắng, bồn chồn hoặc căng thẳng.'
        },
        {
            id: 2,
            text: 'Không thể ngừng lo lắng hoặc không kiểm soát được sự lo lắng.'
        },
        {
            id: 3,
            text: 'Lo lắng quá nhiều về nhiều vấn đề khác nhau.'
        },
        {
            id: 4,
            text: 'Khó thư giãn.'
        },
        {
            id: 5,
            text: 'Bồn chồn đến mức khó có thể ngồi yên.'
        },
        {
            id: 6,
            text: 'Dễ trở nên khó chịu hoặc cáu kỉnh.'
        },
        {
            id: 7,
            text: 'Cảm thấy sợ hãi như thể điều gì đó khủng khiếp có thể xảy ra.'
        }
    ];

    const GAD7_OPTIONS = [
        {
            value: 0,
            label: 'Không hề'
        },
        {
            value: 1,
            label: 'Một vài ngày'
        },
        {
            value: 2,
            label: 'Hơn một nửa số ngày'
        },
        {
            value: 3,
            label: 'Gần như mỗi ngày'
        }
    ];

    const INTERPRETATION_BANDS = {
        minimal: {
            key: 'minimal',
            min: 0,
            max: 4,
            title: 'Minimal',
            titleVi: 'Tối thiểu',
            badgeBg: '#EAF0EB',
            badgeText: '#4A6B5D',
            badgeBorder: '#BACAD0',
            descriptionVi: 'Kết quả của bạn nằm trong khoảng điểm từ tối thiểu đến nhẹ trên thang sàng lọc này. Điểm số không phản ánh toàn bộ sức khỏe tinh thần của bạn.',
            nextSteps: 'Duy trì các thói quen chăm sóc bản thân lành mạnh như ngủ đủ giấc, vận động nhẹ nhàng và thực hành thư giãn khi cần thiết.'
        },
        mild: {
            key: 'mild',
            min: 5,
            max: 9,
            title: 'Mild',
            titleVi: 'Nhẹ',
            badgeBg: '#FEF3C7',
            badgeText: '#92400E',
            badgeBorder: '#FDE68A',
            descriptionVi: 'Kết quả của bạn nằm trong khoảng điểm từ tối thiểu đến nhẹ trên thang sàng lọc này. Điểm số không phản ánh toàn bộ sức khỏe tinh thần của bạn.',
            nextSteps: 'Chú ý đến các yếu tố gây căng thẳng trong sinh hoạt hoặc học tập. Bạn có thể áp dụng các kỹ thuật hít thở sâu, ghi chép nhật ký cảm xúc và dành thời gian nghỉ ngơi hợp lý.'
        },
        moderate: {
            key: 'moderate',
            min: 10,
            max: 14,
            title: 'Moderate',
            titleVi: 'Trung bình',
            badgeBg: '#FFEDD5',
            badgeText: '#C2410C',
            badgeBorder: '#FED7AA',
            descriptionVi: 'Kết quả của bạn cho thấy các triệu chứng lo âu có thể cần được đánh giá thêm. Bạn có thể cân nhắc trao đổi với chuyên gia sức khỏe tinh thần để được hỗ trợ phù hợp.',
            nextSteps: 'Điểm số đạt ngưỡng sàng lọc thông thường (≥ 10). Bạn có thể cân nhắc chia sẻ với chuyên viên tâm lý hoặc cố vấn sức khỏe tinh thần để tìm hiểu nguyên nhân và tiếp cận các chiến lược điều hòa cảm xúc hiệu quả.'
        },
        severe: {
            key: 'severe',
            min: 15,
            max: 21,
            title: 'Severe',
            titleVi: 'Nặng',
            badgeBg: '#FEE2E2',
            badgeText: '#D92D20',
            badgeBorder: '#FCA5A5',
            descriptionVi: 'Kết quả của bạn cho thấy các triệu chứng lo âu có thể cần được đánh giá thêm. Bạn có thể cân nhắc trao đổi với chuyên gia sức khỏe tinh thần để được hỗ trợ phù hợp.',
            nextSteps: 'Các triệu chứng lo âu đang ảnh hưởng đáng kể đến trạng thái hàng ngày. Việc trao đổi sớm với chuyên gia y tế hoặc tâm lý chuyên nghiệp sẽ hỗ trợ bạn có kế hoạch can thiệp an toàn và phù hợp.'
        }
    };

    const DISCLAIMER_TEXT = 'GAD-7 là công cụ sàng lọc triệu chứng, không phải công cụ chẩn đoán. Kết quả không thay thế cho đánh giá của chuyên gia.';

    // =========================================================================
    // STATE MODEL FOR CURRENT TEST ATTEMPT
    // =========================================================================

    let testState = {
        currentStep: 'intro', // 'intro' | 'question' | 'results'
        currentQuestionIndex: 0, // 0 to 6
        answers: new Array(7).fill(null), // 7 raw answers
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
        return `tempo_gad7_history_${uid}`;
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
     * Calculates the GAD-7 item score for a given question index and raw response.
     * Each item receives 0, 1, 2, or 3 points.
     * No items are reverse-scored.
     */
    function calculateItemScore(questionNumber, rawValue) {
        if (typeof rawValue !== 'number' || rawValue < 0 || rawValue > 3) {
            return 0;
        }
        return rawValue;
    }

    /**
     * Calculates the final total GAD-7 score across all 7 items.
     * Returns an integer between 0 and 21.
     * Does not multiply or transform the sum.
     */
    function calculateTotalScore(answers) {
        if (!Array.isArray(answers)) return 0;
        let total = 0;
        for (let i = 0; i < 7; i++) {
            const raw = answers[i];
            total += calculateItemScore(i + 1, raw);
        }
        return total;
    }

    /**
     * Determines the screening interpretation band:
     * 0–4: Minimal
     * 5–9: Mild
     * 10–14: Moderate
     * 15–21: Severe
     */
    function getInterpretationBand(score) {
        if (score >= 15) return INTERPRETATION_BANDS.severe;
        if (score >= 10) return INTERPRETATION_BANDS.moderate;
        if (score >= 5) return INTERPRETATION_BANDS.mild;
        return INTERPRETATION_BANDS.minimal;
    }

    // =========================================================================
    // DOM MOUNTING & DIALOG MANAGEMENT
    // =========================================================================

    function ensureModalMounted() {
        if (!document.getElementById('modal-gad7-test')) {
            const modalEl = document.createElement('div');
            modalEl.id = 'modal-gad7-test';
            modalEl.className = 'fixed inset-0 z-[95] flex items-center justify-center modal-backdrop p-3 sm:p-4 hidden';
            modalEl.style.zIndex = '95';
            modalEl.setAttribute('role', 'dialog');
            modalEl.setAttribute('aria-modal', 'true');
            modalEl.innerHTML = `
                <div id="gad7-modal-card" 
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
            answers: new Array(7).fill(null),
            validationError: '',
            isSubmitting: false,
            completedResult: null
        };

        renderModalContent();
        const modal = document.getElementById('modal-gad7-test');
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

        const modal = document.getElementById('modal-gad7-test');
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

        if (qIdx === 6) {
            // Last question (index 6 of 7): submit assessment
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

        // Verify all 7 questions are answered
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
            id: 'gad7_' + Date.now(),
            testId: 'gad-7',
            testName: 'GAD-7 — Generalized Anxiety Disorder-7',
            completedAt: new Date().toISOString(),
            score: totalScore,
            maxScore: 21,
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
            window.TempoExploreAssessments.selectCategory('anxiety');
        }
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('explore-mental-health-tests', 'anxiety');
        } else {
            window.location.hash = '#explore-mental-health-tests?category=anxiety';
        }
    }

    // =========================================================================
    // MODAL VIEW RENDERERS (INTRO, QUESTION, RESULTS)
    // =========================================================================

    function renderModalContent() {
        const card = document.getElementById('gad7-modal-card');
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
                    <span>Latest assessment: <strong>${latest.score} / 21 (${escapeHTML(latest.interpretationTitleVi)})</strong> on ${dt}</span>
                    <span class="text-[11px] font-bold text-[#4A6B5D]">Saved History</span>
                </div>
            `;
        }

        return `
            <!-- Top Close Button -->
            <button type="button" 
                    onclick="window.TempoGAD7.closeTestModal(false)" 
                    class="absolute top-5 right-5 w-8 h-8 rounded-full flex items-center justify-center text-[#8C8681] hover:text-[#202124] hover:bg-stone-200/50 text-base transition cursor-pointer" 
                    title="Close">✕</button>

            <!-- Navigation Breadcrumb -->
            <div class="flex items-center space-x-2 text-xs font-bold text-[#829B87] uppercase tracking-wider">
                <span>UCheck</span>
                <span>•</span>
                <span>Anxiety Assessment</span>
            </div>

            <!-- Test Title & Header -->
            <div class="space-y-1.5">
                <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                    GAD-7
                </h2>
                <p class="text-sm font-semibold text-[#829B87]">
                    Generalized Anxiety Disorder-7
                </p>
                <p class="text-xs sm:text-sm text-[#5B5550] leading-relaxed pt-1">
                    Screening tool for generalized anxiety symptoms. Designed for personal reflection and symptom tracking.
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
                    “Trong 2 tuần vừa qua, bạn thường xuyên bị làm phiền bởi những vấn đề sau đây ở mức độ nào?”
                </p>
            </div>

            <!-- Test Key Details -->
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div class="bg-white rounded-2xl border border-stone-200/80 p-3.5 space-y-1 shadow-2xs">
                    <span class="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Questions</span>
                    <p class="text-sm font-bold text-[#202124]">7 items</p>
                </div>
                <div class="bg-white rounded-2xl border border-stone-200/80 p-3.5 space-y-1 shadow-2xs">
                    <span class="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Reference Period</span>
                    <p class="text-sm font-bold text-[#202124]">The past two weeks</p>
                </div>
                <div class="bg-white rounded-2xl border border-stone-200/80 p-3.5 space-y-1 shadow-2xs">
                    <span class="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Score Range</span>
                    <p class="text-sm font-bold text-[#202124]">0 – 21</p>
                </div>
            </div>

            <!-- Important Screening Limitation Disclaimer -->
            <div class="p-4 bg-stone-50 rounded-2xl border border-stone-200/70 text-xs text-[#6F6B68] leading-relaxed">
                ℹ️ <strong>Important Limitation:</strong> GAD-7 is a self-assessment screening tool, <strong>not a diagnostic instrument</strong>. It helps identify anxiety symptoms and does not substitute for a professional clinical evaluation.
            </div>

            <!-- Bottom Actions -->
            <div class="pt-4 border-t border-stone-200/80 flex items-center justify-between">
                <button type="button" 
                        onclick="window.TempoGAD7.closeTestModal(false)" 
                        class="px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-600 hover:text-stone-900 transition cursor-pointer">
                    Back to UCheck
                </button>
                <button type="button" 
                        id="btn-gad7-start-test"
                        onclick="window.TempoGAD7.startTest()" 
                        class="px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#829B87] hover:bg-[#728A77] text-white shadow-xs transition cursor-pointer">
                    Start Assessment →
                </button>
            </div>
        `;
    }

    function renderQuestionHTML() {
        const qIdx = testState.currentQuestionIndex;
        const q = GAD7_QUESTIONS[qIdx];
        const selectedVal = testState.answers[qIdx];
        const isAnswered = selectedVal !== null && selectedVal !== undefined;
        const progressPct = Math.round(((qIdx + 1) / 7) * 100);

        return `
            <!-- Top Controls: Question Counter & Exit -->
            <div class="flex items-center justify-between text-xs">
                <div class="flex items-center space-x-2">
                    <span class="font-extrabold text-[#4A6B5D] text-xs uppercase tracking-wider">Question ${qIdx + 1} of 7</span>
                    <span class="text-stone-400">•</span>
                    <span class="text-stone-500 font-medium">The past two weeks</span>
                </div>
                <button type="button" 
                        onclick="window.TempoGAD7.closeTestModal(true)" 
                        class="text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer" 
                        title="Exit assessment">Exit</button>
            </div>

            <!-- Progress Bar -->
            <div class="w-full bg-stone-200/80 h-2 rounded-full overflow-hidden">
                <div class="bg-[#829B87] h-full transition-all duration-300 rounded-full" style="width: ${progressPct}%;"></div>
            </div>

            <!-- Question Statement -->
            <div class="space-y-1.5 py-1">
                <span class="text-xs text-stone-400 font-semibold uppercase tracking-wider">Trong 2 tuần vừa qua:</span>
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
                ${GAD7_OPTIONS.map(opt => {
                    const isSelected = selectedVal === opt.value;
                    return `
                        <div onclick="window.TempoGAD7.selectAnswer(${opt.value})" 
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
                        onclick="window.TempoGAD7.handlePrevQuestion()" 
                        class="px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition cursor-pointer ${
                            qIdx === 0 
                                ? 'opacity-30 pointer-events-none text-stone-400' 
                                : 'text-stone-600 hover:text-stone-900 bg-white border border-stone-200'
                        }">
                    ← Back
                </button>
                <button type="button" 
                        id="btn-gad7-next-question"
                        onclick="window.TempoGAD7.handleNextQuestion()" 
                        class="px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold shadow-xs transition cursor-pointer ${
                            isAnswered 
                                ? 'bg-[#829B87] hover:bg-[#728A77] text-white' 
                                : 'bg-stone-300 text-stone-500 opacity-60 cursor-not-allowed'
                        }">
                    ${qIdx === 6 ? 'Submit Assessment' : 'Next Question →'}
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
                    onclick="window.TempoGAD7.closeTestModal(false)" 
                    class="absolute top-5 right-5 w-8 h-8 rounded-full flex items-center justify-center text-[#8C8681] hover:text-[#202124] hover:bg-stone-200/50 text-base transition cursor-pointer" 
                    title="Close">✕</button>

            <!-- Header Badge -->
            <div class="flex items-center space-x-2 text-xs font-bold text-[#829B87] uppercase tracking-wider">
                <span>Assessment Results</span>
                <span>•</span>
                <span>GAD-7</span>
            </div>

            <div class="space-y-1">
                <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                    GAD-7 Assessment Results
                </h2>
                <p class="text-xs sm:text-sm text-[#5B5550]">
                    Generalized Anxiety Disorder-7 • Based on your responses for the past two weeks.
                </p>
            </div>

            <!-- Score & Interpretation Card -->
            <div class="p-5 sm:p-6 rounded-3xl border border-stone-200/80 bg-white space-y-4 shadow-2xs">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-stone-200/60">
                    <div>
                        <span class="text-xs text-stone-400 font-semibold uppercase tracking-wider">Total Score</span>
                        <div class="flex items-baseline space-x-2 pt-0.5">
                            <span class="font-heading text-3xl sm:text-4xl font-extrabold text-[#202124]">${score}</span>
                            <span class="text-sm font-bold text-stone-400">/ 21 points</span>
                        </div>
                    </div>
                    <div>
                        <span class="text-xs text-stone-400 font-semibold uppercase tracking-wider">Screening Band</span>
                        <div class="pt-1">
                            <span class="inline-block px-3.5 py-1.5 rounded-full text-xs font-extrabold border"
                                  style="background-color: ${band.badgeBg}; color: ${band.badgeText}; border-color: ${band.badgeBorder};">
                                ${escapeHTML(band.title)} (${escapeHTML(band.titleVi)})
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
                        onclick="window.TempoGAD7.startTest()" 
                        class="w-full sm:w-auto px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-600 hover:text-stone-900 bg-white border border-stone-200 transition cursor-pointer text-center">
                    Retake Assessment
                </button>
                <button type="button" 
                        onclick="window.TempoGAD7.returnToUCheck()" 
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

    window.TempoGAD7 = {
        GAD7_QUESTIONS,
        GAD7_OPTIONS,
        INTERPRETATION_BANDS,
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
