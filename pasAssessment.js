/**
 * TEMPO WELLBEING — UCHECK: PERCEPTION OF ACADEMIC STRESS SCALE (PAS)
 * File: pasAssessment.js
 *
 * Implements the 18-item PAS assessment under UCheck -> Stress Assessments:
 * 1. Instrument Source & Attribution:
 *    - Authors: Dalia Bedewy and Adel Gabriel (2015)
 *    - Publication: Bedewy, D., & Gabriel, A. (2015). Examining perceptions of academic stress and its sources
 *      among university students: The Perception of Academic Stress Scale. Health Psychology Open, 2(2).
 *    - DOI: https://doi.org/10.1177/2055102915596714
 *    - License: Creative Commons Attribution–NonCommercial 3.0 Unported (CC BY-NC 3.0)
 *      https://creativecommons.org/licenses/by-nc/3.0/
 *    - Unofficial Vietnamese translation for research and self-reflection. Not clinically validated for Vietnamese university students.
 *    - Neither Tempo nor this translation is endorsed by the original authors.
 * 2. 18 Items:
 *    - Q1–Q5: positive statements (confidence, decision-making, available time). Reverse-scored: 6 - response.
 *    - Q6–Q18: statements addressing criticism, academic concerns, expectations, workload, competition, examinations, employment.
 * 3. 5-point Likert scale (1 to 5):
 *    - 1: Hoàn toàn không đồng ý (Strongly disagree)
 *    - 2: Không đồng ý (Disagree)
 *    - 3: Trung lập / Không đồng ý cũng không phản đối (Neither agree nor disagree)
 *    - 4: Đồng ý (Agree)
 *    - 5: Hoàn toàn đồng ý (Strongly agree)
 * 4. Scoring Engine:
 *    - Total range: 18 to 90. Average item rating: 1.0 to 5.0.
 *    - Centralized scoring logic. No invented clinical cutoffs or diagnostic labels.
 * 5. Descriptive Pressure Pattern Analysis:
 *    - Explicitly labeled as descriptive interpretations rather than validated subscale scores.
 * 6. Tailored Support Recommendations:
 *    - Focus Zone for workload/deadlines, Breathing for exam pressure, Academic support for expectations.
 *    - Non-prescriptive, user-chosen actions.
 * 7. User-scoped persistence under tempo_pas_history_${uid}.
 */

(function () {
    'use strict';

    // =========================================================================
    // INSTRUMENT ATTRIBUTION & METADATA
    // =========================================================================

    const ATTRIBUTION_INFO = {
        instrumentName: 'Perception of Academic Stress Scale (PAS)',
        instrumentNameVi: 'Thang đo Nhận thức Căng thẳng Học tập (PAS)',
        version: '1.0.0',
        scoringVersion: 'bedewy_gabriel_2015_normalized_v1',
        authors: 'Dalia Bedewy & Adel Gabriel (2015)',
        citation: 'Bedewy, D., & Gabriel, A. (2015). Examining perceptions of academic stress and its sources among university students: The Perception of Academic Stress Scale. Health Psychology Open, 2(2).',
        doi: 'https://doi.org/10.1177/2055102915596714',
        license: 'Creative Commons Attribution–NonCommercial 3.0 Unported (CC BY-NC 3.0)',
        licenseUrl: 'https://creativecommons.org/licenses/by-nc/3.0/',
        estimatedMinutes: 5,
        disclaimerVi: 'Bản dịch tiếng Việt mang tính chất tham khảo thực nghiệm, chưa được chuẩn hóa riêng cho sinh viên Việt Nam. Công cụ tự đánh giá không thay thế cho chẩn đoán y khoa hay tâm thần học chuyên nghiệp. Tempo và bản dịch này không được tài trợ hay chứng thực bởi các tác giả gốc.'
    };

    // =========================================================================
    // 18 QUESTION CONFIGURATION (CENTRALIZED & EDITABLE)
    // =========================================================================

    const PAS_QUESTIONS = [
        {
            id: 1,
            text: 'Tôi tự tin rằng mình sẽ là một sinh viên thành công.',
            textEn: 'I am confident that I will be a successful student.',
            isReverse: true,
            domain: 'academic_confidence',
            domainLabel: 'Sự tự tin học tập'
        },
        {
            id: 2,
            text: 'Tôi tự tin rằng mình sẽ thành công trong sự nghiệp tương lai.',
            textEn: 'I am confident that I will be successful in my future career.',
            isReverse: true,
            domain: 'academic_confidence',
            domainLabel: 'Sự tự tin học tập'
        },
        {
            id: 3,
            text: 'Tôi có thể đưa ra các quyết định trong học tập một cách dễ dàng.',
            textEn: 'I can make academic decisions easily.',
            isReverse: true,
            domain: 'academic_confidence',
            domainLabel: 'Sự tự tin học tập'
        },
        {
            id: 4,
            text: 'Thời gian dành cho các lớp học và việc học tập là đủ.',
            textEn: 'The time allocated to classes and academic work is enough.',
            isReverse: true,
            domain: 'time_restraints',
            domainLabel: 'Thời gian & Nghỉ ngơi'
        },
        {
            id: 5,
            text: 'Tôi có đủ thời gian để nghỉ ngơi, thư giãn sau giờ học và làm việc.',
            textEn: 'I have enough time to relax after work.',
            isReverse: true,
            domain: 'time_restraints',
            domainLabel: 'Thời gian & Nghỉ ngơi'
        },
        {
            id: 6,
            text: 'Giảng viên khắt khe hoặc hay chỉ trích kết quả học tập của tôi.',
            textEn: 'My teachers are critical of my academic performance.',
            isReverse: false,
            domain: 'expectations_eval',
            domainLabel: 'Kỳ vọng & Đánh giá'
        },
        {
            id: 7,
            text: 'Tôi lo sợ mình sẽ bị trượt hoặc rớt môn trong năm học này.',
            textEn: 'I fear failing courses this year.',
            isReverse: false,
            domain: 'examinations',
            domainLabel: 'Áp lực thi cử'
        },
        {
            id: 8,
            text: 'Tôi nghĩ rằng sự lo lắng về thi cử là một điểm yếu trong tính cách của mình.',
            textEn: 'I think that my worry about examinations is a weakness of character.',
            isReverse: false,
            domain: 'examinations',
            domainLabel: 'Áp lực thi cử'
        },
        {
            id: 9,
            text: 'Giảng viên đặt những kỳ vọng thiếu thực tế đối với tôi.',
            textEn: 'Teachers have unrealistic expectations of me.',
            isReverse: false,
            domain: 'expectations_eval',
            domainLabel: 'Kỳ vọng & Đánh giá'
        },
        {
            id: 10,
            text: 'Khối lượng chương trình học (workload) là quá tải.',
            textEn: 'The size of the curriculum (workload) is excessive.',
            isReverse: false,
            domain: 'workload_assignments',
            domainLabel: 'Khối lượng học tập'
        },
        {
            id: 11,
            text: 'Tôi cảm thấy khối lượng bài tập và tiểu luận được giao là quá nhiều.',
            textEn: 'I believe that the amount of work assignment is too much.',
            isReverse: false,
            domain: 'workload_assignments',
            domainLabel: 'Khối lượng học tập'
        },
        {
            id: 12,
            text: 'Tôi không thể theo kịp bài học nếu lỡ bị chậm trễ hoặc tụt lại phía sau.',
            textEn: 'I am unable to catch up if getting behind the work.',
            isReverse: false,
            domain: 'workload_assignments',
            domainLabel: 'Khối lượng học tập'
        },
        {
            id: 13,
            text: 'Kỳ vọng thiếu thực tế từ cha mẹ tạo áp lực lớn cho tôi.',
            textEn: 'The unrealistic expectations of my parents stress me out.',
            isReverse: false,
            domain: 'expectations_eval',
            domainLabel: 'Kỳ vọng & Đánh giá'
        },
        {
            id: 14,
            text: 'Sự cạnh tranh điểm số với bạn bè cùng khóa diễn ra khá căng thẳng.',
            textEn: 'Competition with my peers for grades is quite intense.',
            isReverse: false,
            domain: 'expectations_eval',
            domainLabel: 'Kỳ vọng & Đánh giá'
        },
        {
            id: 15,
            text: 'Các câu hỏi trong đề thi thường quá khó.',
            textEn: 'The examination questions are usually difficult.',
            isReverse: false,
            domain: 'examinations',
            domainLabel: 'Áp lực thi cử'
        },
        {
            id: 16,
            text: 'Thời gian làm bài thi quá ngắn để hoàn thành đầy đủ câu trả lời.',
            textEn: 'Examination time is short to complete the answers.',
            isReverse: false,
            domain: 'examinations',
            domainLabel: 'Áp lực thi cử'
        },
        {
            id: 17,
            text: 'Các kỳ thi luôn tạo ra mức độ căng thẳng rất cao đối với tôi.',
            textEn: 'Examination times are very stressful to me.',
            isReverse: false,
            domain: 'examinations',
            domainLabel: 'Áp lực thi cử'
        },
        {
            id: 18,
            text: 'Ngay cả khi thi đỗ, tôi vẫn lo lắng về khả năng tìm kiếm việc làm sau này.',
            textEn: 'Even if I pass my exams, I am worried about getting a job.',
            isReverse: false,
            domain: 'career_outlook',
            domainLabel: 'Định hướng tương lai & Việc làm'
        }
    ];

    const PAS_OPTIONS = [
        {
            value: 1,
            label: 'Hoàn toàn không đồng ý',
            labelEn: 'Strongly disagree'
        },
        {
            value: 2,
            label: 'Không đồng ý',
            labelEn: 'Disagree'
        },
        {
            value: 3,
            label: 'Trung lập / Không đồng ý cũng không phản đối',
            labelEn: 'Neither agree nor disagree'
        },
        {
            value: 4,
            label: 'Đồng ý',
            labelEn: 'Agree'
        },
        {
            value: 5,
            label: 'Hoàn toàn đồng ý',
            labelEn: 'Strongly agree'
        }
    ];

    // =========================================================================
    // STATE MODEL FOR CURRENT TEST ATTEMPT
    // =========================================================================

    let testState = {
        currentStep: 'intro', // 'intro' | 'question' | 'results'
        currentQuestionIndex: 0, // 0 to 17
        answers: new Array(18).fill(null), // 18 raw responses (1–5)
        validationError: '',
        isSubmitting: false,
        completedResult: null,
        callerMode: 'unclear'
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
        return `tempo_pas_history_${uid}`;
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
     * Calculates normalized item score for a given question index and raw response.
     * Items 1–5: reverse-scored using `6 - response`.
     * Items 6–18: retain the original response score (1–5).
     */
    function calculateItemScore(questionNumber, rawValue) {
        if (typeof rawValue !== 'number' || rawValue < 1 || rawValue > 5) {
            return 0;
        }
        if (questionNumber >= 1 && questionNumber <= 5) {
            return 6 - rawValue;
        }
        return rawValue;
    }

    /**
     * Calculates the final total PAS score across all 18 items.
     * Range: 18 to 90.
     */
    function calculateTotalScore(answers) {
        if (!Array.isArray(answers)) return 0;
        let total = 0;
        for (let i = 0; i < 18; i++) {
            const raw = answers[i];
            total += calculateItemScore(i + 1, raw);
        }
        return total;
    }

    /**
     * Computes descriptive patterns across pressure areas.
     * Clearly identified as Tempo descriptive interpretations, NOT validated clinical subscales.
     */
    function computeDescriptivePatterns(answers) {
        if (!Array.isArray(answers) || answers.length !== 18) return [];

        const normalizedScores = answers.map((val, idx) => calculateItemScore(idx + 1, val));

        const groups = [
            {
                key: 'workload',
                title: 'Khối lượng học tập & Bài tập',
                titleEn: 'Curriculum & Workload',
                items: [10, 11, 12],
                description: 'Cảm giác quá tải trước khối lượng giáo trình, bài tập và áp lực bắt kịp tiến độ.',
                actionHint: 'Chia nhỏ nhiệm vụ lớn thành các bước khả thi và ưu tiên hạn chót trong Focus Zone.'
            },
            {
                key: 'examinations',
                title: 'Áp lực thi cử & Đánh giá',
                titleEn: 'Examinations & Performance',
                items: [7, 8, 15, 16, 17],
                description: 'Lo âu trước độ khó của đề thi, áp lực thời gian làm bài và nỗi sợ rớt môn.',
                actionHint: 'Thực hành các kỹ thuật thở hộp giải tỏa căng thẳng trước kỳ thi và xây dựng lộ trình ôn tập cuốn chiếu.'
            },
            {
                key: 'expectations',
                title: 'Kỳ vọng & Môi trường cạnh tranh',
                titleEn: 'Expectations & Competition',
                items: [6, 9, 13, 14],
                description: 'Áp lực từ sự chỉ trích, kỳ vọng của cha mẹ, giảng viên hoặc sự ganh đua điểm số giữa bạn bè.',
                actionHint: 'Làm rõ các kỳ vọng thực tế trong tầm kiểm soát và phân biệt mục tiêu cá nhân với áp lực từ bên ngoài.'
            },
            {
                key: 'confidence',
                title: 'Sự tự tin & Ra quyết định',
                titleEn: 'Academic Confidence',
                items: [1, 2, 3],
                description: 'Mức độ tự tin vào khả năng học tập, sự nghiệp tương lai và việc đưa ra quyết định học thuật.',
                actionHint: 'Chọn một nhiệm vụ nhỏ có thể hoàn thành ngay hôm nay để củng cố cảm giác thành tựu và tìm kiếm sự đồng hành.'
            },
            {
                key: 'time_restraints',
                title: 'Thời gian & Thư giãn',
                titleEn: 'Time Restraints & Rest',
                items: [4, 5],
                description: 'Sự thiếu hụt thời gian dành cho các lớp học hoặc không đủ thời gian nghỉ ngơi sau giờ học.',
                actionHint: 'Bảo vệ các khoảng nghỉ phục hồi ngắn (Recovery Anchor) và điều chỉnh giờ ngủ đều đặn.'
            },
            {
                key: 'career',
                title: 'Định hướng tương lai & Việc làm',
                titleEn: 'Career & Employment Concerns',
                items: [18],
                description: 'Lo lắng về triển vọng việc làm và cơ hội nghề nghiệp sau khi tốt nghiệp.',
                actionHint: 'Tham khảo ý kiến cố vấn hướng nghiệp và từng bước chuẩn bị các kỹ năng thực tế thay vì gánh nặng quá sớm.'
            }
        ];

        return groups.map(g => {
            const groupScores = g.items.map(itemNum => normalizedScores[itemNum - 1]);
            const avg = groupScores.reduce((a, b) => a + b, 0) / groupScores.length;
            return {
                key: g.key,
                title: g.title,
                titleEn: g.titleEn,
                items: g.items,
                avgScore: parseFloat(avg.toFixed(1)),
                isProminent: avg >= 3.5,
                description: g.description,
                actionHint: g.actionHint
            };
        });
    }

    // =========================================================================
    // DOM MOUNTING & DIALOG MANAGEMENT
    // =========================================================================

    function ensureModalMounted() {
        if (!document.getElementById('modal-pas-test')) {
            const modalEl = document.createElement('div');
            modalEl.id = 'modal-pas-test';
            modalEl.className = 'fixed inset-0 z-[95] flex items-center justify-center modal-backdrop p-3 sm:p-4 hidden';
            modalEl.style.zIndex = '95';
            modalEl.setAttribute('role', 'dialog');
            modalEl.setAttribute('aria-modal', 'true');
            modalEl.innerHTML = `
                <div id="pas-modal-card" 
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

    function openTestModal(options) {
        ensureModalMounted();

        // Record caller mode if available
        let caller = 'unclear';
        if (options && options.callerMode) {
            caller = options.callerMode;
        } else if (window.TempoMode && typeof window.TempoMode.getMode === 'function') {
            const m = window.TempoMode.getMode();
            if (m) caller = m;
        }

        // Fresh test attempt initialization
        testState = {
            currentStep: 'intro',
            currentQuestionIndex: 0,
            answers: new Array(18).fill(null),
            validationError: '',
            isSubmitting: false,
            completedResult: null,
            callerMode: caller
        };

        renderModalContent();
        const modal = document.getElementById('modal-pas-test');
        if (modal) modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    function closeTestModal(confirmIfInProgress = false) {
        if (confirmIfInProgress && testState.currentStep === 'question') {
            const hasAnyAnswer = testState.answers.some(a => a !== null);
            if (hasAnyAnswer) {
                const ok = window.confirm("Bạn có chắc chắn muốn rời bài đánh giá? Các câu trả lời chưa hoàn thành sẽ không được lưu.");
                if (!ok) return;
            }
        }

        const modal = document.getElementById('modal-pas-test');
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
            testState.validationError = 'Vui lòng chọn một mức độ phản hồi trước khi tiếp tục.';
            renderModalContent();
            return;
        }

        testState.validationError = '';

        if (qIdx === 17) {
            // Last question (index 17 of 18): submit assessment
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

        // Verify all 18 questions are answered
        const unansweredIdx = testState.answers.findIndex(a => a === null || a === undefined);
        if (unansweredIdx !== -1) {
            testState.currentQuestionIndex = unansweredIdx;
            testState.validationError = `Câu hỏi ${unansweredIdx + 1} chưa được trả lời. Vui lòng phản hồi để tiếp tục.`;
            renderModalContent();
            return;
        }

        testState.isSubmitting = true;

        const totalScore = calculateTotalScore(testState.answers);
        const itemScores = testState.answers.map((raw, idx) => calculateItemScore(idx + 1, raw));
        const patterns = computeDescriptivePatterns(testState.answers);

        const resultRecord = {
            id: 'pas_' + Date.now(),
            testId: 'pas',
            testName: 'PAS — Perception of Academic Stress Scale',
            version: ATTRIBUTION_INFO.version,
            scoringVersion: ATTRIBUTION_INFO.scoringVersion,
            completedAt: new Date().toISOString(),
            status: 'completed',
            score: totalScore,
            maxScore: 90,
            minScore: 18,
            averageItemScore: parseFloat((totalScore / 18).toFixed(2)),
            answers: [...testState.answers],
            itemScores: itemScores,
            descriptivePatterns: patterns
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
            window.TempoExploreAssessments.selectCategory('stress');
        }
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('explore-mental-health-tests', 'stress');
        } else {
            window.location.hash = '#explore-mental-health-tests?category=stress';
        }
    }

    function openFocusZone() {
        closeTestModal(false);
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('focus-zone');
        } else {
            window.location.hash = '#focus-zone';
        }
    }

    function openStressRelief() {
        closeTestModal(false);
        if (window.TempoStressRelief && typeof window.TempoStressRelief.openModal === 'function') {
            window.TempoStressRelief.openModal('breathing');
        }
    }

    // =========================================================================
    // MODAL VIEW RENDERERS (INTRO, QUESTION, RESULTS)
    // =========================================================================

    function renderModalContent() {
        const card = document.getElementById('pas-modal-card');
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
            const dt = new Date(latest.completedAt).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
            prevResultNotice = `
                <div class="p-3.5 bg-[#F4F7F5] rounded-2xl border border-[#CDE9DA] text-xs text-[#284132] flex items-center justify-between">
                    <span>📋 Lần làm gần nhất: <strong>${latest.score} / 90 (Trung bình ${(latest.score / 18).toFixed(1)} / 5.0)</strong> • Ngày ${dt}</span>
                    <span class="text-[11px] font-bold text-[#4A6B5D]">Lịch sử an toàn</span>
                </div>
            `;
        }

        return `
            <!-- Top Close Button -->
            <button type="button" 
                    onclick="window.TempoPAS.closeTestModal(false)" 
                    class="absolute top-5 right-5 w-8 h-8 rounded-full flex items-center justify-center text-[#8C8681] hover:text-[#202124] hover:bg-stone-200/50 text-base transition cursor-pointer" 
                    title="Close">✕</button>

            <!-- Navigation Breadcrumb -->
            <div class="flex items-center space-x-2 text-xs font-bold text-[#829B87] uppercase tracking-wider">
                <span>UCheck</span>
                <span>•</span>
                <span>Stress Assessments</span>
            </div>

            <!-- Test Title & Header -->
            <div class="space-y-1.5">
                <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                    Academic Stress Check (PAS)
                </h2>
                <p class="text-sm font-semibold text-[#829B87]">
                    Perception of Academic Stress Scale • Bedewy &amp; Gabriel (2015)
                </p>
                <p class="text-xs sm:text-sm text-[#5B5550] leading-relaxed pt-1">
                    Thang đo tự đánh giá giúp sinh viên đại học nhận diện mức độ căng thẳng học tập và khám phá các nguồn áp lực tiềm ẩn từ khối lượng học, kỳ vọng và thi cử.
                </p>
            </div>

            ${prevResultNotice}

            <!-- Test Key Details -->
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div class="bg-white rounded-2xl border border-stone-200/80 p-3.5 space-y-1 shadow-2xs">
                    <span class="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Số câu hỏi</span>
                    <p class="text-sm font-bold text-[#202124]">18 câu hỏi</p>
                </div>
                <div class="bg-white rounded-2xl border border-stone-200/80 p-3.5 space-y-1 shadow-2xs">
                    <span class="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Thời gian ước tính</span>
                    <p class="text-sm font-bold text-[#202124]">~5 phút</p>
                </div>
                <div class="bg-white rounded-2xl border border-stone-200/80 p-3.5 space-y-1 shadow-2xs">
                    <span class="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Thang điểm</span>
                    <p class="text-sm font-bold text-[#202124]">18 – 90 (Likert 1–5)</p>
                </div>
            </div>

            <!-- Important Limitation & Disclaimer Notice -->
            <div class="p-4 bg-stone-50 rounded-2xl border border-stone-200/70 text-xs text-[#6F6B68] leading-relaxed space-y-1.5">
                <div class="font-bold text-[#202124] flex items-center space-x-1.5">
                    <span>ℹ️</span>
                    <span>Lưu ý quan trọng &amp; Giới hạn công cụ:</span>
                </div>
                <p>
                    Đây là công cụ tự báo cáo (self-report) nhằm nâng cao nhận thức cá nhân về các nguồn gây căng thẳng học tập. Thang đo <strong>không phải công cụ chẩn đoán y khoa</strong> và không thay thế cho đánh giá chuyên môn từ chuyên gia y tế hoặc tâm lý.
                </p>
                <p class="text-[11px] text-stone-500 italic">
                    ${escapeHTML(ATTRIBUTION_INFO.disclaimerVi)}
                </p>
            </div>

            <!-- Scientific Attribution & License Box -->
            <div class="p-3.5 bg-white rounded-2xl border border-stone-200/80 text-[11px] text-stone-500 leading-relaxed space-y-1">
                <div class="font-semibold text-stone-700">Nguồn trích dẫn gốc &amp; Giấy phép bản quyền:</div>
                <p>
                    Bedewy, D., &amp; Gabriel, A. (2015). <em>Examining perceptions of academic stress and its sources among university students: The Perception of Academic Stress Scale.</em> Health Psychology Open, 2(2). 
                    <a href="${ATTRIBUTION_INFO.doi}" target="_blank" rel="noopener noreferrer" class="text-[#4A6B5D] hover:underline font-medium">DOI: 10.1177/2055102915596714</a>
                </p>
                <p>
                    Phát hành theo giấy phép <a href="${ATTRIBUTION_INFO.licenseUrl}" target="_blank" rel="noopener noreferrer" class="text-[#4A6B5D] hover:underline font-medium">${ATTRIBUTION_INFO.license}</a>.
                </p>
            </div>

            <!-- Bottom Actions -->
            <div class="pt-4 border-t border-stone-200/80 flex items-center justify-between">
                <button type="button" 
                        onclick="window.TempoPAS.closeTestModal(false)" 
                        class="px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-600 hover:text-stone-900 transition cursor-pointer">
                    Quay lại UCheck
                </button>
                <button type="button" 
                        id="btn-pas-start-test"
                        onclick="window.TempoPAS.startTest()" 
                        class="px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#829B87] hover:bg-[#728A77] text-white shadow-xs transition cursor-pointer">
                    Bắt đầu làm bài →
                </button>
            </div>
        `;
    }

    function renderQuestionHTML() {
        const qIdx = testState.currentQuestionIndex;
        const q = PAS_QUESTIONS[qIdx];
        const selectedVal = testState.answers[qIdx];
        const isAnswered = selectedVal !== null && selectedVal !== undefined;
        const progressPct = Math.round(((qIdx + 1) / 18) * 100);

        return `
            <!-- Top Controls: Question Counter & Exit -->
            <div class="flex items-center justify-between text-xs">
                <div class="flex items-center space-x-2">
                    <span class="font-extrabold text-[#4A6B5D] text-xs uppercase tracking-wider">Câu hỏi ${qIdx + 1} / 18</span>
                    <span class="text-stone-400">•</span>
                    <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-[#EAF0EB] text-[#384F43] border border-[#CDE9DA]">
                        ${escapeHTML(q.domainLabel)}
                    </span>
                </div>
                <button type="button" 
                        onclick="window.TempoPAS.closeTestModal(true)" 
                        class="text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer" 
                        title="Rời bài đánh giá">Thoát</button>
            </div>

            <!-- Progress Bar -->
            <div class="w-full bg-stone-200/80 h-2 rounded-full overflow-hidden">
                <div class="bg-[#829B87] h-full transition-all duration-300 rounded-full" style="width: ${progressPct}%;"></div>
            </div>

            <!-- Question Statement -->
            <div class="space-y-1.5 py-1">
                <span class="text-xs text-stone-400 font-semibold uppercase tracking-wider">Hãy cho biết mức độ đồng ý của bạn:</span>
                <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124] leading-snug">
                    ${escapeHTML(q.text)}
                </h3>
                <p class="text-xs text-stone-400 italic">
                    Original item: “${escapeHTML(q.textEn)}”
                </p>
            </div>

            <!-- Validation Feedback (if triggered) -->
            ${testState.validationError ? `
                <div class="p-3 bg-red-50 border border-red-200 rounded-xl text-xs font-semibold text-[#D92D20] flex items-center space-x-2">
                    <span>⚠️</span>
                    <span>${escapeHTML(testState.validationError)}</span>
                </div>
            ` : ''}

            <!-- 5 Likert Response Options -->
            <div class="space-y-2 pt-1">
                ${PAS_OPTIONS.map(opt => {
                    const isSelected = selectedVal === opt.value;
                    return `
                        <div onclick="window.TempoPAS.selectAnswer(${opt.value})" 
                             class="p-3 sm:p-3.5 rounded-2xl border transition cursor-pointer flex items-center justify-between select-none ${
                                 isSelected 
                                     ? 'bg-[#EAF0EB] border-2 border-[#4A6B5D] text-[#284132] font-bold shadow-xs' 
                                     : 'bg-white border-stone-200 hover:border-stone-400 text-[#484541] hover:bg-stone-50/70'
                             }">
                            <div class="space-y-0.5 pr-2">
                                <div class="text-xs sm:text-sm font-semibold">
                                    <span class="font-bold text-stone-400 mr-1.5">${opt.value} —</span>
                                    <span>${escapeHTML(opt.label)}</span>
                                </div>
                                <div class="text-[11px] text-stone-400 italic">
                                    ${escapeHTML(opt.labelEn)}
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
                        onclick="window.TempoPAS.handlePrevQuestion()" 
                        class="px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition cursor-pointer ${
                            qIdx === 0 
                                ? 'opacity-30 pointer-events-none text-stone-400' 
                                : 'text-stone-600 hover:text-stone-900 bg-white border border-stone-200'
                        }">
                    ← Quay lại
                </button>
                <button type="button" 
                        id="btn-pas-next-question"
                        onclick="window.TempoPAS.handleNextQuestion()" 
                        class="px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold shadow-xs transition cursor-pointer ${
                            isAnswered 
                                ? 'bg-[#829B87] hover:bg-[#728A77] text-white' 
                                : 'bg-stone-300 text-stone-500 opacity-60 cursor-not-allowed'
                        }">
                    ${qIdx === 17 ? 'Hoàn thành bài đánh giá' : 'Câu tiếp theo →'}
                </button>
            </div>
        `;
    }

    function renderResultsHTML() {
        const res = testState.completedResult || getLatestResult();
        if (!res) return renderIntroHTML();

        const score = res.score;
        const avgItem = (score / 18).toFixed(1);
        const patterns = res.descriptivePatterns || computeDescriptivePatterns(res.answers);
        const prominentPatterns = patterns.filter(p => p.isProminent);

        return `
            <!-- Top Exit Button -->
            <button type="button" 
                    onclick="window.TempoPAS.closeTestModal(false)" 
                    class="absolute top-5 right-5 w-8 h-8 rounded-full flex items-center justify-center text-[#8C8681] hover:text-[#202124] hover:bg-stone-200/50 text-base transition cursor-pointer" 
                    title="Close">✕</button>

            <!-- Header Badge -->
            <div class="flex items-center space-x-2 text-xs font-bold text-[#829B87] uppercase tracking-wider">
                <span>Kết quả tự đánh giá</span>
                <span>•</span>
                <span>Academic Stress Check (PAS)</span>
            </div>

            <div class="space-y-1">
                <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                    Kết Quả Đánh Giá Căng Thẳng Học Tập
                </h2>
                <p class="text-xs sm:text-sm text-[#5B5550]">
                    Dựa trên 18 câu trả lời phản ánh trải nghiệm học tập và nhận thức áp lực hiện tại của bạn.
                </p>
            </div>

            <!-- Score Summary Card -->
            <div class="p-5 sm:p-6 rounded-3xl border border-stone-200/80 bg-white space-y-4 shadow-2xs">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-stone-200/60">
                    <div>
                        <span class="text-xs text-stone-400 font-semibold uppercase tracking-wider">Tổng điểm chuẩn hóa</span>
                        <div class="flex items-baseline space-x-2 pt-0.5">
                            <span class="font-heading text-3xl sm:text-4xl font-extrabold text-[#202124]">${score}</span>
                            <span class="text-sm font-bold text-stone-400">/ 90 điểm</span>
                        </div>
                    </div>
                    <div>
                        <span class="text-xs text-stone-400 font-semibold uppercase tracking-wider">Mức trung bình câu</span>
                        <div class="pt-1">
                            <span class="inline-block px-3.5 py-1.5 rounded-full text-xs font-extrabold bg-[#EAF0EB] text-[#384F43] border border-[#CDE9DA]">
                                ${avgItem} / 5.0
                            </span>
                        </div>
                    </div>
                </div>

                <div class="space-y-1.5">
                    <h4 class="text-xs font-bold text-[#202124] uppercase tracking-wider">Ý nghĩa của điểm số:</h4>
                    <p class="text-xs sm:text-sm text-[#5B5550] leading-relaxed">
                        Thang đo PAS đo lường mức độ cảm nhận chủ quan của bạn trước các yếu tố gây căng thẳng trong môi trường đại học. Nghiên cứu gốc của Bedewy &amp; Gabriel (2015) <strong>không thiết lập các ngưỡng phân loại lâm sàng</strong> (như nhẹ, vừa hay nặng) và điểm số này <strong>không cấu thành một chẩn đoán y khoa</strong>. Điểm số mang tính chất phản chiếu mức độ áp lực bạn đang tự cảm nhận.
                    </p>
                </div>
            </div>

            <!-- Descriptive Pressure Areas (Explicitly noted as descriptive interpretations, NOT validated subscales) -->
            <div class="space-y-3">
                <div class="space-y-0.5">
                    <h4 class="text-xs font-bold text-[#202124] uppercase tracking-wider flex items-center space-x-1.5">
                        <span>🔍</span>
                        <span>Diễn giải mô tả các nguồn áp lực nổi bật</span>
                    </h4>
                    <p class="text-[11px] text-stone-500 italic">
                        *Lưu ý phân tích: Các nhóm chủ đề dưới đây là diễn giải mô tả do Tempo thiết kế nhằm giúp bạn nhận diện các khía cạnh tạo nhiều áp lực, không phải các thang đo thành phần (subscales) đã được chuẩn hóa lâm sàng độc lập.
                    </p>
                </div>

                <div class="grid grid-cols-1 gap-2.5">
                    ${patterns.map(p => {
                        const isHigh = p.avgScore >= 3.5;
                        return `
                            <div class="p-3.5 rounded-2xl border transition ${
                                isHigh 
                                    ? 'bg-[#FEFAF4] border-[#E8D9CF]' 
                                    : 'bg-stone-50/70 border-stone-200/60'
                            }">
                                <div class="flex items-center justify-between pb-1">
                                    <div class="space-y-0.5">
                                        <div class="text-xs font-bold text-[#202124]">
                                            ${escapeHTML(p.title)}
                                        </div>
                                        <div class="text-[11px] text-stone-400">
                                            ${escapeHTML(p.titleEn)}
                                        </div>
                                    </div>
                                    <span class="px-2.5 py-1 rounded-full text-[11px] font-bold ${
                                        isHigh 
                                            ? 'bg-[#FFEDD5] text-[#C2410C] border border-[#FED7AA]' 
                                            : 'bg-white text-stone-600 border border-stone-200'
                                    }">
                                        ${p.avgScore} / 5.0
                                    </span>
                                </div>
                                <p class="text-xs text-[#5B5550] leading-relaxed pt-1">
                                    ${escapeHTML(p.description)}
                                </p>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>

            <!-- Tailored Next Steps within Tempo (Non-prescriptive, User chooses) -->
            <div class="bg-[#F4F7F5] rounded-3xl border border-[#CDE9DA] p-5 space-y-3.5 shadow-2xs">
                <div class="space-y-1">
                    <span class="text-xs font-bold text-[#284132] flex items-center space-x-1.5">
                        <span>🌱</span>
                        <span>Gợi ý hành động tiếp theo trong Tempo (Tùy chọn)</span>
                    </span>
                    <p class="text-xs text-[#4A6B5D] leading-relaxed">
                        Các khuyến nghị thực hành dưới đây do Tempo thiết kế để bạn tự chăm sóc bản thân, không phải kết luận trực tiếp từ thang đo PAS. Bạn có thể tự do lựa chọn thực hiện khi phù hợp.
                    </p>
                </div>

                <div class="space-y-2.5">
                    <!-- 1. Workload / Deadlines Suggestion -->
                    <div class="p-3.5 bg-white rounded-2xl border border-stone-200/80 space-y-2">
                        <div class="text-xs font-bold text-[#202124]">
                            🎯 Nếu khối lượng bài vở hoặc hạn chót đang dồn dập:
                        </div>
                        <p class="text-xs text-[#5B5550] leading-relaxed">
                            Hãy chia nhỏ công việc thành từng phần việc 25 phút có thể quản lý được và ưu tiên danh sách deadline sắp tới trong Focus Zone.
                        </p>
                        <div>
                            <button type="button" 
                                    onclick="window.TempoPAS.openFocusZone()" 
                                    class="px-4 py-2 rounded-xl text-xs font-bold bg-[#829B87] hover:bg-[#728A77] text-white shadow-xs transition cursor-pointer">
                                Mở Focus Zone →
                            </button>
                        </div>
                    </div>

                    <!-- 2. Exam Tension / Physical Reset Suggestion -->
                    <div class="p-3.5 bg-white rounded-2xl border border-stone-200/80 space-y-2">
                        <div class="text-xs font-bold text-[#202124]">
                            🫁 Nếu căng thẳng vì thi cử hoặc nhịp học dồn dập:
                        </div>
                        <p class="text-xs text-[#5B5550] leading-relaxed">
                            Thực hành 3 phút thở hộp hoặc thả lỏng vai và hàm để giúp hệ thần kinh lấy lại sự cân bằng trước khi bắt đầu ôn tập.
                        </p>
                        <div>
                            <button type="button" 
                                    onclick="window.TempoPAS.openStressRelief()" 
                                    class="px-4 py-2 rounded-xl text-xs font-bold bg-stone-100 hover:bg-stone-200 text-[#202124] border border-stone-200 transition cursor-pointer">
                                Thử bài tập thở hộp →
                            </button>
                        </div>
                    </div>

                    <!-- 3. Academic Expectations Support -->
                    <div class="p-3.5 bg-white rounded-2xl border border-stone-200/80 space-y-1">
                        <div class="text-xs font-bold text-[#202124]">
                            💬 Về kỳ vọng học tập &amp; áp lực cạnh tranh:
                        </div>
                        <p class="text-xs text-[#5B5550] leading-relaxed">
                            Xác định những yếu tố trong tầm kiểm soát của bạn, trao đổi với giảng viên bộ môn hoặc bạn học tin cậy để làm rõ các tiêu chí đánh giá thay vì giữ lo âu một mình.
                        </p>
                    </div>
                </div>
            </div>

            <!-- Mandatory Attribution & Screening Disclaimer -->
            <div class="p-4 bg-stone-50 rounded-2xl border border-stone-200/70 text-xs text-[#6F6B68] leading-relaxed space-y-1">
                <div>
                    ℹ️ <strong>Tuyên bố miễn trừ trách nhiệm:</strong> ${escapeHTML(ATTRIBUTION_INFO.disclaimerVi)}
                </div>
                <div class="text-[11px] text-stone-500 pt-1">
                    Công cụ: <em>Perception of Academic Stress Scale (PAS)</em> • Dalia Bedewy &amp; Adel Gabriel (2015) • Health Psychology Open • Giấy phép CC BY-NC 3.0.
                </div>
            </div>

            <!-- Bottom Actions -->
            <div class="pt-4 border-t border-stone-200/80 flex flex-col sm:flex-row items-center justify-between gap-3">
                <button type="button" 
                        onclick="window.TempoPAS.startTest()" 
                        class="w-full sm:w-auto px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-600 hover:text-stone-900 bg-white border border-stone-200 transition cursor-pointer text-center">
                    Làm lại bài đánh giá
                </button>
                <button type="button" 
                        onclick="window.TempoPAS.returnToUCheck()" 
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

    window.TempoPAS = {
        ATTRIBUTION_INFO,
        PAS_QUESTIONS,
        PAS_OPTIONS,
        calculateItemScore,
        calculateTotalScore,
        computeDescriptivePatterns,
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
        openFocusZone,
        openStressRelief,
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
