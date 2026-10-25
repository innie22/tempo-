/**
 * TEMPO WELLBEING — UCHECK: PHQ-9 (PATIENT HEALTH QUESTIONNAIRE-9)
 * File: phq9Assessment.js
 *
 * Implements the PHQ-9 Depression Self-Assessment under UCheck -> Depression Assessment:
 * 1. Test Introduction (Name, 2-week instructions, 9 questions, ~3-5 mins, non-diagnostic disclaimer).
 * 2. 9 Questions with exact Vietnamese text and 4 response options (0-3).
 * 3. Step-by-step navigation with selected state, back navigation, and required-answer validation.
 * 4. Immediate SOS flow triggered upon confirming Q9 > 0 (1, 2, or 3) with foreground crisis modal,
 *    compassionate Vietnamese wording, verified resources (HOPE 0865 044 400, 115, trusted contact),
 *    and answer-preserving continuation. Single trigger invariant per test attempt.
 * 5. Optional functional-impact question (does NOT contribute to total score).
 * 6. Scoring: Sum of Q1-Q9 (0-27) with severity bands (Tối thiểu, Nhẹ, Trung bình, Trung bình–nặng, Nặng).
 * 7. Results view with non-diagnostic disclaimer, supportive next steps, and return to UCheck.
 * 8. User-scoped persistence under tempo_phq9_history_${uid}.
 */

(function () {
    'use strict';

    // =========================================================================
    // CONSTANTS & QUESTION DATA
    // =========================================================================

    const PHQ9_QUESTIONS = [
        {
            id: 1,
            text: 'Ít hứng thú hoặc ít cảm thấy vui vẻ khi làm việc gì đó.'
        },
        {
            id: 2,
            text: 'Cảm thấy buồn bã, chán nản hoặc tuyệt vọng.'
        },
        {
            id: 3,
            text: 'Khó đi vào giấc ngủ, ngủ không ngon, hoặc ngủ quá nhiều.'
        },
        {
            id: 4,
            text: 'Cảm thấy mệt mỏi hoặc thiếu năng lượng.'
        },
        {
            id: 5,
            text: 'Chán ăn hoặc ăn quá nhiều.'
        },
        {
            id: 6,
            text: 'Cảm thấy tồi tệ về bản thân — cảm thấy mình là người thất bại hoặc đã khiến bản thân hay gia đình thất vọng.'
        },
        {
            id: 7,
            text: 'Gặp khó khăn trong việc tập trung vào những việc như đọc báo hoặc xem tivi.'
        },
        {
            id: 8,
            text: 'Di chuyển hoặc nói chậm đến mức người khác có thể nhận thấy; hoặc ngược lại, cảm thấy bồn chồn, đứng ngồi không yên và vận động nhiều hơn bình thường.'
        },
        {
            id: 9,
            text: 'Nghĩ rằng mình sẽ tốt hơn nếu không còn sống, hoặc nghĩ đến việc làm tổn thương bản thân theo cách nào đó.'
        }
    ];

    const PHQ9_OPTIONS = [
        { value: 0, label: '0 — Không hề' },
        { value: 1, label: '1 — Một vài ngày' },
        { value: 2, label: '2 — Hơn một nửa số ngày' },
        { value: 3, label: '3 — Gần như mỗi ngày' }
    ];

    const IMPACT_QUESTION = {
        text: 'Những vấn đề trên đã gây khó khăn như thế nào cho bạn trong công việc, việc nhà hoặc khi giao tiếp với người khác?',
        options: [
            'Không gây khó khăn',
            'Hơi khó khăn',
            'Rất khó khăn',
            'Cực kỳ khó khăn'
        ]
    };

    const SEVERITY_BANDS = [
        {
            min: 0,
            max: 4,
            key: 'minimal',
            label: 'Tối thiểu',
            badgeBg: '#EAF0EB',
            badgeText: '#4A6B5D',
            badgeBorder: '#BACAD0',
            description: 'Kết quả phản ánh mức độ triệu chứng tối thiểu hoặc không đáng kể trong 2 tuần qua.',
            nextSteps: 'Tiếp tục duy trì nhịp sống tích cực, chế độ sinh hoạt điều độ và các thói quen chăm sóc sức khỏe tinh thần hiện tại của bạn.'
        },
        {
            min: 5,
            max: 9,
            key: 'mild',
            label: 'Nhẹ',
            badgeBg: '#FEF3C7',
            badgeText: '#92400E',
            badgeBorder: '#FDE68A',
            description: 'Kết quả phản ánh mức độ triệu chứng nhẹ trong 2 tuần qua.',
            nextSteps: 'Nên chú ý cân bằng giữa học tập, công việc và nghỉ ngơi; vận động thể chất nhẹ nhàng; thực hành thư giãn và theo dõi cảm xúc hàng ngày.'
        },
        {
            min: 10,
            max: 14,
            key: 'moderate',
            label: 'Trung bình',
            badgeBg: '#FED7AA',
            badgeText: '#9A3412',
            badgeBorder: '#FDBA74',
            description: 'Kết quả phản ánh các triệu chứng ở mức trung bình trong 2 tuần qua.',
            nextSteps: 'Nên cân nhắc chia sẻ cảm xúc với người thân, bạn bè tin cậy hoặc tìm kiếm sự tham vấn từ chuyên viên tâm lý / bác sĩ để có hướng hỗ trợ phù hợp.'
        },
        {
            min: 15,
            max: 19,
            key: 'moderately_severe',
            label: 'Trung bình–nặng',
            badgeBg: '#FFEDD5',
            badgeText: '#C2410C',
            badgeBorder: '#FDBA74',
            description: 'Kết quả phản ánh các triệu chứng đang ảnh hưởng đáng kể đến đời sống và cảm xúc của bạn trong 2 tuần qua.',
            nextSteps: 'Khuyến nghị bạn sớm liên hệ với chuyên gia tâm lý hoặc bác sĩ chuyên khoa sức khỏe tâm thần để được đánh giá toàn diện và đồng hành điều trị kịp thời.'
        },
        {
            min: 20,
            max: 27,
            key: 'severe',
            label: 'Nặng',
            badgeBg: '#FEE2E2',
            badgeText: '#D92D20',
            badgeBorder: '#FCA5A5',
            description: 'Kết quả phản ánh mức độ triệu chứng nặng đang tác động sâu sắc đến sức khỏe và các hoạt động thường ngày.',
            nextSteps: 'Rất khuyến khích bạn sớm liên hệ cơ sở y tế chuyên khoa hoặc chuyên gia tâm lý để nhận được sự chăm sóc y tế và can thiệp hỗ trợ chuyên sâu.'
        }
    ];

    // =========================================================================
    // STATE MODEL FOR CURRENT TEST SESSION
    // =========================================================================

    let testState = {
        currentStep: 'intro', // 'intro' | 'question' | 'impact' | 'results'
        currentQuestionIndex: 0, // 0 to 8
        answers: [null, null, null, null, null, null, null, null, null],
        impactAnswer: null,
        hasTriggeredQ9SosForCurrentAttempt: false,
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
        return `tempo_phq9_history_${uid}`;
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
    // SCORING & SEVERITY CALCULATION
    // =========================================================================

    function calculateTotalScore(answers) {
        let total = 0;
        for (let i = 0; i < 9; i++) {
            const val = answers[i];
            if (typeof val === 'number') {
                total += val;
            }
        }
        return total;
    }

    function getSeverityBand(score) {
        for (const band of SEVERITY_BANDS) {
            if (score >= band.min && score <= band.max) {
                return band;
            }
        }
        return SEVERITY_BANDS[0];
    }

    // =========================================================================
    // DOM MOUNTING & DIALOG MANAGEMENT
    // =========================================================================

    function ensureModalsMounted() {
        // 1. Main PHQ-9 Test Modal
        if (!document.getElementById('modal-phq9-test')) {
            const modalEl = document.createElement('div');
            modalEl.id = 'modal-phq9-test';
            modalEl.className = 'fixed inset-0 z-[95] flex items-center justify-center modal-backdrop p-3 sm:p-4 hidden';
            modalEl.style.zIndex = '95';
            modalEl.setAttribute('role', 'dialog');
            modalEl.setAttribute('aria-modal', 'true');
            modalEl.innerHTML = `
                <div id="phq9-modal-card" 
                     class="tempo-card max-w-2xl w-full p-6 sm:p-8 space-y-6 rounded-3xl shadow-2xl relative border border-[#EAE4DF]/80 max-h-[94vh] overflow-y-auto"
                     style="background-color: #FEFAF4;">
                    <!-- Dynamically populated by renderModalContent() -->
                </div>
            `;
            document.body.appendChild(modalEl);
        }

        // 2. Foreground SOS Popup Modal
        if (!document.getElementById('modal-phq9-sos')) {
            const sosEl = document.createElement('div');
            sosEl.id = 'modal-phq9-sos';
            sosEl.className = 'fixed inset-0 z-[110] flex items-center justify-center modal-backdrop p-3 sm:p-4 hidden';
            sosEl.style.zIndex = '110';
            sosEl.setAttribute('role', 'dialog');
            sosEl.setAttribute('aria-modal', 'true');
            sosEl.innerHTML = `
                <div id="phq9-sos-card" 
                     class="tempo-card max-w-lg w-full p-6 sm:p-7 space-y-5 rounded-3xl shadow-2xl relative border border-[#EAE4DF] max-h-[92vh] overflow-y-auto"
                     style="background-color: #FEFAF4;">
                    <!-- Dynamically populated by renderSosModalContent() -->
                </div>
            `;
            document.body.appendChild(sosEl);
        }
    }

    // =========================================================================
    // TEST LIFECYCLE & NAVIGATION CONTROLLER
    // =========================================================================

    function openTestModal() {
        ensureModalsMounted();

        // Fresh test attempt initialization
        testState = {
            currentStep: 'intro',
            currentQuestionIndex: 0,
            answers: [null, null, null, null, null, null, null, null, null],
            impactAnswer: null,
            hasTriggeredQ9SosForCurrentAttempt: false,
            completedResult: null
        };

        renderModalContent();
        const modal = document.getElementById('modal-phq9-test');
        if (modal) modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    function closeTestModal(confirmIfInProgress = false) {
        if (confirmIfInProgress && testState.currentStep === 'question') {
            const hasAnyAnswer = testState.answers.some(a => a !== null);
            if (hasAnyAnswer) {
                const ok = window.confirm("Bạn có chắc chắn muốn rời khỏi bài tự kiểm tra không? Các câu trả lời chưa hoàn thành sẽ không được lưu.");
                if (!ok) return;
            }
        }

        const modal = document.getElementById('modal-phq9-test');
        if (modal) modal.classList.add('hidden');
        closeSosModal();
        document.body.classList.remove('overflow-hidden');
    }

    function startTest() {
        testState.currentStep = 'question';
        testState.currentQuestionIndex = 0;
        renderModalContent();
    }

    function selectAnswer(value) {
        const qIdx = testState.currentQuestionIndex;
        testState.answers[qIdx] = value;
        renderModalContent();
    }

    function handleNextQuestion() {
        const qIdx = testState.currentQuestionIndex;
        const currentAns = testState.answers[qIdx];

        if (currentAns === null) {
            return; // Required question must be answered
        }

        // Question 9: Check for immediate SOS flow
        if (qIdx === 8) {
            if (currentAns > 0 && !testState.hasTriggeredQ9SosForCurrentAttempt) {
                testState.hasTriggeredQ9SosForCurrentAttempt = true;
                openSosModal();
                return;
            }
            // Advance to supplementary functional-impact question
            testState.currentStep = 'impact';
            renderModalContent();
            return;
        }

        // Q1 through Q8: Advance to next question
        testState.currentQuestionIndex = qIdx + 1;
        renderModalContent();
    }

    function handlePrevQuestion() {
        if (testState.currentStep === 'impact') {
            testState.currentStep = 'question';
            testState.currentQuestionIndex = 8;
            renderModalContent();
            return;
        }

        if (testState.currentStep === 'question' && testState.currentQuestionIndex > 0) {
            testState.currentQuestionIndex -= 1;
            renderModalContent();
        }
    }

    function selectImpactAnswer(optionText) {
        testState.impactAnswer = optionText;
        renderModalContent();
    }

    function submitAssessment() {
        // Compute total score from Q1 to Q9 only
        const total = calculateTotalScore(testState.answers);
        const severity = getSeverityBand(total);

        const resultRecord = {
            id: 'phq9_' + Date.now(),
            testId: 'phq-9',
            testName: 'PHQ-9 — Depression Self-Assessment',
            completedAt: new Date().toISOString(),
            score: total,
            maxScore: 27,
            severityKey: severity.key,
            severityLabel: severity.label,
            answers: [...testState.answers],
            impactAnswer: testState.impactAnswer || null,
            triggeredSos: testState.hasTriggeredQ9SosForCurrentAttempt
        };

        testState.completedResult = resultRecord;
        testState.currentStep = 'results';

        // Persist result safely
        saveCompletedResult(resultRecord);

        // Update UCheck category UI if visible
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
    // SOS CRITICAL FLOW (QUESTION 9 TRIGGER)
    // =========================================================================

    function openSosModal() {
        ensureModalsMounted();
        const card = document.getElementById('phq9-sos-card');
        const modal = document.getElementById('modal-phq9-sos');
        if (!card || !modal) return;

        card.innerHTML = `
            <!-- Close icon button -->
            <button type="button" 
                    onclick="window.TempoPHQ9.dismissSosModal()" 
                    class="absolute top-5 right-5 w-8 h-8 rounded-full flex items-center justify-center text-[#8C8681] hover:text-[#202124] hover:bg-stone-200/50 text-base transition cursor-pointer" 
                    title="Đóng">✕</button>

            <!-- Top Tag with Semantic Warning Red (#D92D20) -->
            <div class="flex items-center space-x-2">
                <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: #D92D20;"></span>
                <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#D92D20]">HỖ TRỢ KHẨN CẤP &amp; AN TOÀN</span>
            </div>

            <!-- Compassionate Title & Inquiries -->
            <div class="space-y-2">
                <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124] tracking-tight leading-snug">
                    Bạn có đang an toàn ở thời điểm hiện tại không?
                </h3>
                <p class="text-xs sm:text-sm text-[#5B5550] leading-relaxed">
                    Ở câu hỏi số 9, bạn vừa chia sẻ về những suy nghĩ liên quan đến việc làm tổn thương bản thân hoặc cái chết. Chúng mình muốn dừng lại một chút để hỏi thăm và chắc chắn rằng bạn đang được an toàn.
                </p>
                <p class="text-xs sm:text-sm text-[#5B5550] leading-relaxed">
                    Bạn không cần phải tự mình gánh chịu những cảm xúc nặng nề này. Luôn có sự hỗ trợ lắng nghe sẵn sàng dành cho bạn bất cứ lúc nào.
                </p>
            </div>

            <!-- Crisis Support Resources List -->
            <div class="space-y-2.5 pt-1">
                <!-- HOPE Hotline Card -->
                <div class="bg-white rounded-2xl border border-stone-200/80 p-3.5 sm:p-4 space-y-2 shadow-2xs">
                    <div class="flex items-center justify-between">
                        <div class="space-y-0.5">
                            <span class="text-xs font-bold text-[#202124] flex items-center space-x-1.5">
                                <span>📞</span>
                                <span>Đường dây nóng HOPE</span>
                            </span>
                            <p class="text-[11px] text-[#6F6B68]">Hỗ trợ tâm lý &amp; phòng ngừa tự tử (Miễn phí, bảo mật 24/7)</p>
                        </div>
                        <a href="tel:0865044400" 
                           class="px-3.5 py-2 rounded-xl text-xs font-bold bg-[#829B87] hover:bg-[#728A77] text-white shadow-xs transition cursor-pointer whitespace-nowrap">
                            Gọi 0865 044 400
                        </a>
                    </div>
                </div>

                <!-- Emergency Medical 115 Card -->
                <div class="bg-white rounded-2xl border border-stone-200/80 p-3.5 sm:p-4 space-y-2 shadow-2xs">
                    <div class="flex items-center justify-between">
                        <div class="space-y-0.5">
                            <span class="text-xs font-bold text-[#D92D20] flex items-center space-x-1.5">
                                <span>🚨</span>
                                <span>Cấp cứu y tế khẩn cấp 115</span>
                            </span>
                            <p class="text-[11px] text-[#6F6B68]">Nếu bạn hoặc ai đó đang trong tình huống nguy hiểm trước mắt</p>
                        </div>
                        <a href="tel:115" 
                           class="px-3.5 py-2 rounded-xl text-xs font-bold bg-white text-[#D92D20] border border-[#D92D20] hover:bg-red-50 shadow-xs transition cursor-pointer whitespace-nowrap">
                            Gọi 115
                        </a>
                    </div>
                </div>

                <!-- Trusted Person Contact Template Card -->
                <div class="bg-white rounded-2xl border border-stone-200/80 p-3.5 sm:p-4 space-y-2 shadow-2xs">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-[#202124] flex items-center space-x-1.5">
                            <span>💬</span>
                            <span>Nhắn tin cho người thân / bạn bè tin cậy</span>
                        </span>
                        <button type="button" 
                                onclick="window.TempoPHQ9.copyTrustedMessage()" 
                                class="text-xs font-bold text-[#4A6B5D] hover:underline cursor-pointer">
                            Sao chép mẫu tin
                        </button>
                    </div>
                    <div class="text-xs text-[#5B5550] bg-[#F9F7F5] rounded-xl px-3 py-2 border border-stone-200/60 italic">
                        "Hey, mình đang trải qua một khoảng thời gian rất khó khăn và thấy hơi quá tải. Bạn có thể trò chuyện hoặc ngồi cùng mình một lát được không?"
                    </div>
                </div>
            </div>

            <!-- Bottom Actions: Continue test safely without losing answers -->
            <div class="pt-3 border-t border-stone-200/80 flex flex-col sm:flex-row items-center justify-between gap-2.5">
                <span class="text-[11px] text-stone-400 text-center sm:text-left">
                    Câu trả lời của bạn đã được ghi nhận an toàn.
                </span>
                <button type="button" 
                        id="btn-phq9-sos-continue"
                        onclick="window.TempoPHQ9.dismissSosModal()" 
                        class="w-full sm:w-auto px-5 py-2.5 rounded-xl text-xs font-bold bg-[#829B87] hover:bg-[#728A77] text-white shadow-xs transition cursor-pointer text-center">
                    Tôi hiện an toàn, tiếp tục bài kiểm tra
                </button>
            </div>
        `;

        modal.classList.remove('hidden');
    }

    function closeSosModal() {
        const modal = document.getElementById('modal-phq9-sos');
        if (modal) modal.classList.add('hidden');
    }

    function dismissSosModal() {
        closeSosModal();
        // Advance to supplementary impact question without losing any answers
        testState.currentStep = 'impact';
        renderModalContent();
    }

    function copyTrustedMessage() {
        const msg = "Hey, mình đang trải qua một khoảng thời gian rất khó khăn và thấy hơi quá tải. Bạn có thể trò chuyện hoặc ngồi cùng mình một lát được không?";
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(msg);
        }
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("Đã sao chép mẫu tin nhắn! Bạn có thể gửi cho người thân hoặc bạn bè.");
        } else {
            alert("Đã sao chép mẫu tin nhắn: " + msg);
        }
    }

    // =========================================================================
    // MODAL VIEW RENDERERS (INTRO, QUESTION, IMPACT, RESULTS)
    // =========================================================================

    function renderModalContent() {
        const card = document.getElementById('phq9-modal-card');
        if (!card) return;

        switch (testState.currentStep) {
            case 'intro':
                card.innerHTML = renderIntroHTML();
                break;
            case 'question':
                card.innerHTML = renderQuestionHTML();
                break;
            case 'impact':
                card.innerHTML = renderImpactHTML();
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
            const dt = new Date(latest.completedAt).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
            prevResultNotice = `
                <div class="p-3.5 bg-[#F4F7F5] rounded-2xl border border-[#CDE9DA] text-xs text-[#284132] flex items-center justify-between">
                    <span>Lần làm gần nhất: <strong>${latest.score} / 27 (${escapeHTML(latest.severityLabel)})</strong> vào ngày ${dt}</span>
                    <span class="text-[11px] font-bold text-[#4A6B5D]">Lịch sử lưu an toàn</span>
                </div>
            `;
        }

        return `
            <!-- Top Close Button -->
            <button type="button" 
                    onclick="window.TempoPHQ9.closeTestModal(false)" 
                    class="absolute top-5 right-5 w-8 h-8 rounded-full flex items-center justify-center text-[#8C8681] hover:text-[#202124] hover:bg-stone-200/50 text-base transition cursor-pointer" 
                    title="Đóng">✕</button>

            <!-- Navigation Breadcrumb -->
            <div class="flex items-center space-x-2 text-xs font-bold text-[#829B87] uppercase tracking-wider">
                <span>UCheck</span>
                <span>•</span>
                <span>Depression Assessment</span>
            </div>

            <!-- Test Title & Header -->
            <div class="space-y-2">
                <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                    PHQ-9 — Depression Self-Assessment
                </h2>
                <p class="text-xs sm:text-sm text-[#5B5550] leading-relaxed">
                    Thang đo tiêu chuẩn quốc tế giúp sàng lọc và đánh giá mức độ các dấu hiệu trầm cảm dựa trên trải nghiệm thực tế của bạn trong <strong>2 tuần vừa qua</strong>.
                </p>
            </div>

            ${prevResultNotice}

            <!-- Key Information Cards -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <div class="bg-white rounded-2xl border border-stone-200/80 p-4 space-y-1 shadow-2xs">
                    <span class="text-xs font-bold text-[#202124] flex items-center space-x-1.5">
                        <span>📝</span>
                        <span>Số lượng câu hỏi</span>
                    </span>
                    <p class="text-xs text-[#5B5550]">9 câu hỏi tự đánh giá + 1 câu hỏi bổ sung tùy chọn.</p>
                </div>
                <div class="bg-white rounded-2xl border border-stone-200/80 p-4 space-y-1 shadow-2xs">
                    <span class="text-xs font-bold text-[#202124] flex items-center space-x-1.5">
                        <span>⏱️</span>
                        <span>Thời gian ước tính</span>
                    </span>
                    <p class="text-xs text-[#5B5550]">Khoảng 3–5 phút để hoàn thành.</p>
                </div>
            </div>

            <!-- Disclaimer Notice -->
            <div class="p-4 bg-stone-50 rounded-2xl border border-stone-200/70 text-xs text-[#6F6B68] leading-relaxed">
                ℹ️ <strong>Lưu ý quan trọng:</strong> Bài tự kiểm tra này được thiết kế nhằm mục đích phản ánh cá nhân và sàng lọc sớm. Kết quả <strong>không phải là một chẩn đoán y khoa</strong> và không thay thế cho việc đánh giá chuyên sâu của bác sĩ hoặc chuyên gia tâm lý có chứng chỉ hành nghề.
            </div>

            <!-- Bottom Action Buttons -->
            <div class="pt-4 border-t border-stone-200/80 flex items-center justify-between">
                <button type="button" 
                        onclick="window.TempoPHQ9.closeTestModal(false)" 
                        class="px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-600 hover:text-stone-900 transition cursor-pointer">
                    Quay lại UCheck
                </button>
                <button type="button" 
                        id="btn-phq9-start-test"
                        onclick="window.TempoPHQ9.startTest()" 
                        class="px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#829B87] hover:bg-[#728A77] text-white shadow-xs transition cursor-pointer">
                    Bắt đầu làm bài →
                </button>
            </div>
        `;
    }

    function renderQuestionHTML() {
        const qIdx = testState.currentQuestionIndex;
        const q = PHQ9_QUESTIONS[qIdx];
        const selectedVal = testState.answers[qIdx];
        const isAnswered = selectedVal !== null && selectedVal !== undefined;
        const progressPct = Math.round(((qIdx + 1) / 9) * 100);

        return `
            <!-- Top Controls: Question Counter & Exit -->
            <div class="flex items-center justify-between text-xs">
                <div class="flex items-center space-x-2">
                    <span class="font-extrabold text-[#4A6B5D] text-xs uppercase tracking-wider">Câu hỏi ${qIdx + 1} / 9</span>
                    <span class="text-stone-400">•</span>
                    <span class="text-stone-500 font-medium">Trải nghiệm trong 2 tuần qua</span>
                </div>
                <button type="button" 
                        onclick="window.TempoPHQ9.closeTestModal(true)" 
                        class="text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer" 
                        title="Đóng bài kiểm tra">Thoát</button>
            </div>

            <!-- Progress Bar -->
            <div class="w-full bg-stone-200/80 h-2 rounded-full overflow-hidden">
                <div class="bg-[#829B87] h-full transition-all duration-300 rounded-full" style="width: ${progressPct}%;"></div>
            </div>

            <!-- Question Statement -->
            <div class="space-y-1.5 py-1">
                <span class="text-xs text-stone-400 font-semibold uppercase tracking-wider">Trong 2 tuần vừa qua, bạn có thường xuyên bị:</span>
                <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124] leading-snug">
                    ${escapeHTML(q.text)}
                </h3>
            </div>

            <!-- 4 Response Options -->
            <div class="space-y-2.5 pt-1">
                ${PHQ9_OPTIONS.map(opt => {
                    const isSelected = selectedVal === opt.value;
                    return `
                        <div onclick="window.TempoPHQ9.selectAnswer(${opt.value})" 
                             class="p-4 rounded-2xl border transition cursor-pointer flex items-center justify-between select-none ${
                                 isSelected 
                                     ? 'bg-[#EAF0EB] border-2 border-[#4A6B5D] text-[#284132] font-bold shadow-xs' 
                                     : 'bg-white border-stone-200 hover:border-stone-400 text-[#484541] hover:bg-stone-50/70'
                             }">
                            <span class="text-xs sm:text-sm">${escapeHTML(opt.label)}</span>
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
                        onclick="window.TempoPHQ9.handlePrevQuestion()" 
                        class="px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition cursor-pointer ${
                            qIdx === 0 
                                ? 'opacity-30 pointer-events-none text-stone-400' 
                                : 'text-stone-600 hover:text-stone-900 bg-white border border-stone-200'
                        }">
                    ← Quay lại
                </button>
                <button type="button" 
                        id="btn-phq9-next-question"
                        onclick="window.TempoPHQ9.handleNextQuestion()" 
                        class="px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold shadow-xs transition cursor-pointer ${
                            isAnswered 
                                ? 'bg-[#829B87] hover:bg-[#728A77] text-white' 
                                : 'bg-stone-300 text-stone-500 opacity-60 cursor-not-allowed pointer-events-none'
                        }">
                    ${qIdx === 8 ? 'Tiếp tục →' : 'Câu tiếp theo →'}
                </button>
            </div>
        `;
    }

    function renderImpactHTML() {
        const selectedVal = testState.impactAnswer;

        return `
            <!-- Top Controls -->
            <div class="flex items-center justify-between text-xs">
                <div class="flex items-center space-x-2">
                    <span class="font-extrabold text-[#829B87] text-xs uppercase tracking-wider">Câu hỏi bổ sung (Tùy chọn)</span>
                    <span class="text-stone-400">•</span>
                    <span class="text-stone-500 font-medium">Không tính vào điểm số</span>
                </div>
                <button type="button" 
                        onclick="window.TempoPHQ9.closeTestModal(true)" 
                        class="text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">Thoát</button>
            </div>

            <!-- Header and Question Statement -->
            <div class="space-y-1.5 py-1">
                <span class="text-xs text-stone-400 font-semibold uppercase tracking-wider">Đánh giá mức độ ảnh hưởng chức năng:</span>
                <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124] leading-snug">
                    ${escapeHTML(IMPACT_QUESTION.text)}
                </h3>
                <p class="text-xs text-stone-500 leading-relaxed">
                    Câu hỏi này giúp bạn nhìn nhận thêm về mức độ tác động của các triệu chứng đến cuộc sống thường ngày. Bạn có thể chọn câu trả lời phù hợp nhất hoặc bấm bỏ qua.
                </p>
            </div>

            <!-- 4 Options -->
            <div class="space-y-2.5 pt-1">
                ${IMPACT_QUESTION.options.map(opt => {
                    const isSelected = selectedVal === opt;
                    return `
                        <div onclick="window.TempoPHQ9.selectImpactAnswer('${escapeHTML(opt)}')" 
                             class="p-4 rounded-2xl border transition cursor-pointer flex items-center justify-between select-none ${
                                 isSelected 
                                     ? 'bg-[#EAF0EB] border-2 border-[#4A6B5D] text-[#284132] font-bold shadow-xs' 
                                     : 'bg-white border-stone-200 hover:border-stone-400 text-[#484541] hover:bg-stone-50/70'
                             }">
                            <span class="text-xs sm:text-sm">${escapeHTML(opt)}</span>
                            <div class="w-5 h-5 rounded-full border flex items-center justify-center shrink-0 ${
                                isSelected ? 'border-[#4A6B5D] bg-[#4A6B5D] text-white' : 'border-stone-300 bg-white'
                            }">
                                ${isSelected ? '✓' : ''}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>

            <!-- Bottom Actions -->
            <div class="pt-4 border-t border-stone-200/80 flex items-center justify-between">
                <button type="button" 
                        onclick="window.TempoPHQ9.handlePrevQuestion()" 
                        class="px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-600 hover:text-stone-900 bg-white border border-stone-200 transition cursor-pointer">
                    ← Quay lại câu 9
                </button>
                <div class="flex items-center space-x-2">
                    <button type="button" 
                            onclick="window.TempoPHQ9.submitAssessment()" 
                            class="px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ${selectedVal ? 'Bỏ chọn & Hoàn thành' : 'Bỏ qua câu này'}
                    </button>
                    <button type="button" 
                            id="btn-phq9-submit"
                            onclick="window.TempoPHQ9.submitAssessment()" 
                            class="px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#829B87] hover:bg-[#728A77] text-white shadow-xs transition cursor-pointer">
                        Xem kết quả →
                    </button>
                </div>
            </div>
        `;
    }

    function renderResultsHTML() {
        const res = testState.completedResult || getLatestResult();
        if (!res) return renderIntroHTML();

        const score = res.score;
        const severity = getSeverityBand(score);
        const q9Answer = res.answers[8];
        const isQ9Positive = q9Answer > 0;

        return `
            <!-- Top Exit Button -->
            <button type="button" 
                    onclick="window.TempoPHQ9.closeTestModal(false)" 
                    class="absolute top-5 right-5 w-8 h-8 rounded-full flex items-center justify-center text-[#8C8681] hover:text-[#202124] hover:bg-stone-200/50 text-base transition cursor-pointer" 
                    title="Đóng">✕</button>

            <!-- Header Badge -->
            <div class="flex items-center space-x-2 text-xs font-bold text-[#829B87] uppercase tracking-wider">
                <span>Kết quả tự đánh giá</span>
                <span>•</span>
                <span>PHQ-9</span>
            </div>

            <div class="space-y-1">
                <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                    Kết quả sàng lọc mức độ trầm cảm
                </h2>
                <p class="text-xs sm:text-sm text-[#5B5550]">
                    Dựa trên các câu trả lời cho trải nghiệm trong 2 tuần vừa qua của bạn.
                </p>
            </div>

            <!-- Score & Severity Card -->
            <div class="p-5 sm:p-6 rounded-3xl border border-stone-200/80 bg-white space-y-4 shadow-2xs">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-stone-200/60">
                    <div>
                        <span class="text-xs text-stone-400 font-semibold uppercase tracking-wider">Tổng điểm PHQ-9</span>
                        <div class="flex items-baseline space-x-2 pt-0.5">
                            <span class="font-heading text-3xl sm:text-4xl font-extrabold text-[#202124]">${score}</span>
                            <span class="text-sm font-bold text-stone-400">/ 27 điểm</span>
                        </div>
                    </div>
                    <div>
                        <span class="text-xs text-stone-400 font-semibold uppercase tracking-wider">Mức độ sàng lọc</span>
                        <div class="pt-1">
                            <span class="inline-block px-3.5 py-1.5 rounded-full text-xs font-extrabold border"
                                  style="background-color: ${severity.badgeBg}; color: ${severity.badgeText}; border-color: ${severity.badgeBorder};">
                                ${escapeHTML(severity.label)}
                            </span>
                        </div>
                    </div>
                </div>

                <div class="space-y-1.5">
                    <h4 class="text-xs font-bold text-[#202124] uppercase tracking-wider">Ý nghĩa kết quả</h4>
                    <p class="text-xs sm:text-sm text-[#5B5550] leading-relaxed">
                        ${escapeHTML(severity.description)}
                    </p>
                </div>

                ${res.impactAnswer ? `
                    <div class="pt-2 text-xs text-[#484541] bg-[#F9F7F5] rounded-xl px-3 py-2 border border-stone-200/60">
                        <strong>Mức độ ảnh hưởng sinh hoạt:</strong> ${escapeHTML(res.impactAnswer)}
                    </div>
                ` : ''}
            </div>

            <!-- Ongoing Crisis Notice if Q9 was positive -->
            ${isQ9Positive ? `
                <div class="p-4 rounded-2xl bg-[#FFF5F5] border border-[#FCA5A5] space-y-2">
                    <div class="flex items-center space-x-2 text-[#D92D20]">
                        <span class="text-base">⚠️</span>
                        <h4 class="text-xs font-extrabold uppercase tracking-wider">Nhắc nhở an toàn quan trọng</h4>
                    </div>
                    <p class="text-xs text-[#5B5550] leading-relaxed">
                        Bạn đã ghi nhận có những suy nghĩ về cái chết hoặc làm tổn thương bản thân ở câu hỏi số 9. Nếu bạn đang cảm thấy quá tải hoặc không an toàn, xin hãy liên hệ ngay với đường dây nóng <strong>HOPE (0865 044 400)</strong> hoặc <strong>Cấp cứu 115</strong>. Luôn có sự hỗ trợ lắng nghe sẵn sàng dành cho bạn.
                    </p>
                </div>
            ` : ''}

            <!-- Supportive Next Steps -->
            <div class="bg-[#F4F7F5] rounded-2xl border border-[#CDE9DA] p-4 sm:p-5 space-y-2 shadow-2xs">
                <span class="text-xs font-bold text-[#202124] flex items-center space-x-1.5">
                    <span>🌱</span>
                    <span>Gợi ý bước tiếp theo dành cho bạn</span>
                </span>
                <p class="text-xs sm:text-sm text-[#384F43] leading-relaxed">
                    ${escapeHTML(severity.nextSteps)}
                </p>
            </div>

            <!-- Non-diagnostic Disclaimer -->
            <div class="text-[11px] text-stone-400 italic leading-relaxed text-center px-2">
                Thông báo: Kết quả này phản ánh tần suất các dấu hiệu bạn báo cáo trong 2 tuần qua theo thang đo PHQ-9. Đây là công cụ sàng lọc tự đánh giá và không phải là chẩn đoán y tế chuyên nghiệp hay kế hoạch điều trị.
            </div>

            <!-- Bottom Actions -->
            <div class="pt-4 border-t border-stone-200/80 flex flex-col sm:flex-row items-center justify-between gap-3">
                <button type="button" 
                        onclick="window.TempoPHQ9.startTest()" 
                        class="w-full sm:w-auto px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-600 hover:text-stone-900 bg-white border border-stone-200 transition cursor-pointer text-center">
                    Làm lại bài kiểm tra
                </button>
                <button type="button" 
                        onclick="window.TempoPHQ9.returnToUCheck()" 
                        class="w-full sm:w-auto px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#829B87] hover:bg-[#728A77] text-white shadow-xs transition cursor-pointer text-center">
                    Quay lại UCheck →
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

    window.TempoPHQ9 = {
        PHQ9_QUESTIONS,
        PHQ9_OPTIONS,
        IMPACT_QUESTION,
        SEVERITY_BANDS,
        calculateTotalScore,
        getSeverityBand,
        getLatestResult,
        saveCompletedResult,
        openTestModal,
        closeTestModal,
        startTest,
        selectAnswer,
        handleNextQuestion,
        handlePrevQuestion,
        selectImpactAnswer,
        submitAssessment,
        openSosModal,
        closeSosModal,
        dismissSosModal,
        copyTrustedMessage,
        returnToUCheck,
        // State getter for inspection & testing
        getTestState: () => Object.assign({}, testState, {
            answers: [...testState.answers]
        }),
        // Helper to set arbitrary state for testing
        _setTestState: (partial) => {
            Object.assign(testState, partial);
            renderModalContent();
        }
    };

})();
