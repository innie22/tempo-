/**
 * Explore Mental Health Tests Controller
 * Manages category tabs and assessment views for the 4 assessment categories:
 * - Depression Assessment ('depression') -> PHQ-9 & CES-D
 * - Stress Assessments ('stress')
 * - Anxiety Assessments ('anxiety')
 * - Other Assessments ('other')
 */
window.TempoExploreAssessments = (function() {
    const CATEGORIES = {
        depression: {
            id: 'depression',
            title: 'Depression Assessment',
            icon: '🌧️',
            summary: 'Evaluations for low mood, persistent fatigue, and depressive signals.',
            note: 'Standardized depression assessment tools are available below.'
        },
        stress: {
            id: 'stress',
            title: 'Stress Assessments',
            icon: '⚡',
            summary: 'Evaluations for acute academic stress, overwhelm, and cognitive fatigue.',
            note: 'Targeted stress evaluation tools are being prepared for this section.'
        },
        anxiety: {
            id: 'anxiety',
            title: 'Anxiety Assessments',
            icon: '🌀',
            summary: 'Evaluations for worry, bodily tension, nervousness, and panic symptoms.',
            note: 'Validated anxiety assessment tools are being prepared for this section.'
        },
        other: {
            id: 'other',
            title: 'Other Assessments',
            icon: '🌱',
            summary: 'Evaluations for sleep quality, daily rhythm balance, and general wellbeing.',
            note: 'Holistic wellbeing assessments are being prepared for this section.'
        }
    };

    let activeCategory = 'depression';

    function getActiveCategory() {
        return activeCategory;
    }

    function selectCategory(catKey, pushHash = true) {
        const key = (catKey && CATEGORIES[catKey.toLowerCase()]) ? catKey.toLowerCase() : 'depression';
        activeCategory = key;

        if (pushHash) {
            window.location.hash = `#explore-mental-health-tests?category=${key}`;
        }

        render();
    }

    function openPHQ9() {
        if (window.TempoPHQ9 && typeof window.TempoPHQ9.openTestModal === 'function') {
            window.TempoPHQ9.openTestModal();
        }
    }

    function openCESD() {
        if (window.TempoCESD && typeof window.TempoCESD.openTestModal === 'function') {
            window.TempoCESD.openTestModal();
        }
    }

    function openGAD7() {
        if (window.TempoGAD7 && typeof window.TempoGAD7.openTestModal === 'function') {
            window.TempoGAD7.openTestModal();
        }
    }

    function openPAS() {
        if (window.TempoPAS && typeof window.TempoPAS.openTestModal === 'function') {
            window.TempoPAS.openTestModal();
        }
    }

    function render() {
        const data = CATEGORIES[activeCategory] || CATEGORIES.depression;

        // Update nav button states
        document.querySelectorAll('.explore-cat-btn').forEach(btn => {
            const cat = btn.getAttribute('data-cat');
            if (cat === activeCategory) {
                btn.className = 'explore-cat-btn py-2.5 px-3 rounded-xl text-xs sm:text-sm font-bold text-center transition cursor-pointer bg-[#829B87] text-white shadow-xs';
            } else {
                btn.className = 'explore-cat-btn py-2.5 px-3 rounded-xl text-xs sm:text-sm font-bold text-center transition cursor-pointer bg-stone-50 hover:bg-stone-100 text-[#4A4540]';
            }
        });

        // Update detail card
        const contentBox = document.getElementById('explore-category-content');
        if (!contentBox) return;

        // Specialized rendering for Depression Assessment: Displays PHQ-9 & CES-D cards
        if (activeCategory === 'depression') {
            // 1. PHQ-9 Latest Result
            const latestPHQ9 = (window.TempoPHQ9 && typeof window.TempoPHQ9.getLatestResult === 'function')
                ? window.TempoPHQ9.getLatestResult()
                : null;

            let historyPHQ9HTML = '';
            if (latestPHQ9) {
                const dt = new Date(latestPHQ9.completedAt).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
                historyPHQ9HTML = `
                    <div class="mt-4 p-3.5 bg-[#F4F7F5] rounded-2xl border border-[#CDE9DA] text-xs text-[#284132] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div class="flex items-center space-x-2">
                            <span>📋</span>
                            <span>Lần làm gần nhất: <strong>${latestPHQ9.score} / 27 (${escapeHTML(latestPHQ9.severityLabel)})</strong> • Ngày ${dt}</span>
                        </div>
                        <span class="text-[11px] font-bold text-[#4A6B5D] shrink-0">Lịch sử an toàn</span>
                    </div>
                `;
            }

            // 2. CES-D Latest Result
            const latestCESD = (window.TempoCESD && typeof window.TempoCESD.getLatestResult === 'function')
                ? window.TempoCESD.getLatestResult()
                : null;

            let historyCESDHTML = '';
            if (latestCESD) {
                const dt = new Date(latestCESD.completedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                historyCESDHTML = `
                    <div class="mt-4 p-3.5 bg-[#F4F7F5] rounded-2xl border border-[#CDE9DA] text-xs text-[#284132] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div class="flex items-center space-x-2">
                            <span>📋</span>
                            <span>Latest assessment: <strong>${latestCESD.score} / 60 (${escapeHTML(latestCESD.interpretationTitleVi)})</strong> • ${dt}</span>
                        </div>
                        <span class="text-[11px] font-bold text-[#4A6B5D] shrink-0">Saved History</span>
                    </div>
                `;
            }

            contentBox.innerHTML = `
                <div class="w-16 h-16 rounded-2xl bg-[#EAF0EB] text-[#4A6356] border border-[#BACAD0] flex items-center justify-center mx-auto text-2xl shadow-xs">
                    ${data.icon}
                </div>
                <div class="space-y-1">
                    <span class="text-xs font-bold uppercase tracking-wider text-[#829B87]">Selected Category</span>
                    <h2 class="text-xl sm:text-2xl font-extrabold text-[#202124]">${data.title}</h2>
                    <p class="text-sm text-[#6F6B68] max-w-md mx-auto leading-relaxed pt-1">
                        ${data.summary}
                    </p>
                </div>

                <!-- Assessments List Container -->
                <div class="grid grid-cols-1 gap-5 pt-3 max-w-2xl mx-auto text-left">
                    <!-- 1. PHQ-9 Assessment Item Card -->
                    <div class="bg-[#FEFAF4] border border-[#EAE4DF] hover:border-[#829B87] transition rounded-3xl p-6 shadow-xs space-y-4">
                        <div class="space-y-2">
                            <div class="flex flex-wrap items-center gap-2">
                                <span class="px-2.5 py-1 rounded-full text-[11px] font-extrabold bg-[#EAF0EB] text-[#4A6B5D] border border-[#BACAD0]">
                                    Tiêu chuẩn quốc tế
                                </span>
                                <span class="text-xs text-stone-500 font-semibold">• 9 câu hỏi</span>
                                <span class="text-xs text-stone-500 font-semibold">• ~3–5 phút</span>
                            </div>
                            <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#202124]">
                                PHQ-9 — Depression Self-Assessment
                            </h3>
                            <p class="text-xs sm:text-sm text-[#5B5550] leading-relaxed">
                                Thang đo tự đánh giá tiêu chuẩn giúp sàng lọc và đánh giá mức độ các dấu hiệu trầm cảm trong 2 tuần qua. Kết quả tự đánh giá mang tính chất phản ánh cá nhân, không thay thế chẩn đoán y khoa chuyên nghiệp.
                            </p>
                        </div>

                        ${historyPHQ9HTML}

                        <div class="pt-3 border-t border-[#EAE4DF] flex items-center justify-between">
                            <span class="text-xs text-stone-500 italic">Bảo mật &amp; riêng tư</span>
                            <button type="button" 
                                    id="btn-start-phq9"
                                    onclick="window.TempoExploreAssessments.openPHQ9()"
                                    class="px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#829B87] hover:bg-[#728A77] text-white shadow-xs transition cursor-pointer">
                                ${latestPHQ9 ? 'Làm lại bài kiểm tra' : 'Bắt đầu làm bài →'}
                            </button>
                        </div>
                    </div>

                    <!-- 2. CES-D Assessment Item Card -->
                    <div class="bg-[#FEFAF4] border border-[#EAE4DF] hover:border-[#829B87] transition rounded-3xl p-6 shadow-xs space-y-4">
                        <div class="space-y-2">
                            <div class="flex flex-wrap items-center gap-2">
                                <span class="px-2.5 py-1 rounded-full text-[11px] font-extrabold bg-[#EAF0EB] text-[#4A6B5D] border border-[#BACAD0]">
                                    Epidemiologic Scale
                                </span>
                                <span class="text-xs text-stone-500 font-semibold">• 20 items</span>
                                <span class="text-xs text-stone-500 font-semibold">• The past week</span>
                                <span class="text-xs text-stone-500 font-semibold">• Score range: 0–60</span>
                            </div>
                            <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#202124]">
                                CES-D — Center for Epidemiologic Studies Depression Scale
                            </h3>
                            <p class="text-xs sm:text-sm text-[#5B5550] leading-relaxed">
                                Self-assessment of the frequency of depressive symptoms over the past week. A widely utilized screening tool for personal reflection; not a diagnostic instrument.
                            </p>
                        </div>

                        ${historyCESDHTML}

                        <div class="pt-3 border-t border-[#EAE4DF] flex items-center justify-between">
                            <span class="text-xs text-stone-500 italic">Private &amp; Confidential</span>
                            <button type="button" 
                                    id="btn-start-cesd"
                                    onclick="window.TempoExploreAssessments.openCESD()"
                                    class="px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#829B87] hover:bg-[#728A77] text-white shadow-xs transition cursor-pointer">
                                ${latestCESD ? 'Retake Assessment' : 'Start Assessment →'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
            return;
        }

        // Specialized rendering for Anxiety Assessment: Displays GAD-7 card
        if (activeCategory === 'anxiety') {
            const latestGAD7 = (window.TempoGAD7 && typeof window.TempoGAD7.getLatestResult === 'function')
                ? window.TempoGAD7.getLatestResult()
                : null;

            let historyGAD7HTML = '';
            if (latestGAD7) {
                const dt = new Date(latestGAD7.completedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                historyGAD7HTML = `
                    <div class="mt-4 p-3.5 bg-[#F4F7F5] rounded-2xl border border-[#CDE9DA] text-xs text-[#284132] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div class="flex items-center space-x-2">
                            <span>📋</span>
                            <span>Latest assessment: <strong>${latestGAD7.score} / 21 (${escapeHTML(latestGAD7.interpretationTitleVi)})</strong> • ${dt}</span>
                        </div>
                        <span class="text-[11px] font-bold text-[#4A6B5D] shrink-0">Saved History</span>
                    </div>
                `;
            }

            contentBox.innerHTML = `
                <div class="w-16 h-16 rounded-2xl bg-[#EAF0EB] text-[#4A6356] border border-[#BACAD0] flex items-center justify-center mx-auto text-2xl shadow-xs">
                    ${data.icon}
                </div>
                <div class="space-y-1">
                    <span class="text-xs font-bold uppercase tracking-wider text-[#829B87]">Selected Category</span>
                    <h2 class="text-xl sm:text-2xl font-extrabold text-[#202124]">${data.title}</h2>
                    <p class="text-sm text-[#6F6B68] max-w-md mx-auto leading-relaxed pt-1">
                        ${data.summary}
                    </p>
                </div>

                <!-- Assessments List Container -->
                <div class="grid grid-cols-1 gap-5 pt-3 max-w-2xl mx-auto text-left">
                    <!-- GAD-7 Assessment Item Card -->
                    <div class="bg-[#FEFAF4] border border-[#EAE4DF] hover:border-[#829B87] transition rounded-3xl p-6 shadow-xs space-y-4">
                        <div class="space-y-2">
                            <div class="flex flex-wrap items-center gap-2">
                                <span class="px-2.5 py-1 rounded-full text-[11px] font-extrabold bg-[#EAF0EB] text-[#4A6B5D] border border-[#BACAD0]">
                                    Standardized Screening
                                </span>
                                <span class="text-xs text-stone-500 font-semibold">• 7 items</span>
                                <span class="text-xs text-stone-500 font-semibold">• The past two weeks</span>
                                <span class="text-xs text-stone-500 font-semibold">• Score range: 0–21</span>
                            </div>
                            <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#202124]">
                                GAD-7 — Generalized Anxiety Disorder-7
                            </h3>
                            <p class="text-xs sm:text-sm text-[#5B5550] leading-relaxed">
                                Standardized self-assessment for screening generalized anxiety symptoms over the past two weeks. Designed for personal reflection; not a diagnostic instrument.
                            </p>
                        </div>

                        ${historyGAD7HTML}

                        <div class="pt-3 border-t border-[#EAE4DF] flex items-center justify-between">
                            <span class="text-xs text-stone-500 italic">Private &amp; Confidential</span>
                            <button type="button" 
                                    id="btn-start-gad7"
                                    onclick="window.TempoExploreAssessments.openGAD7()"
                                    class="px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#829B87] hover:bg-[#728A77] text-white shadow-xs transition cursor-pointer">
                                ${latestGAD7 ? 'Retake Assessment' : 'Start Assessment →'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
            return;
        }

        // Specialized rendering for Stress Assessments: Displays Academic Stress Check (PAS) card
        if (activeCategory === 'stress') {
            const latestPAS = (window.TempoPAS && typeof window.TempoPAS.getLatestResult === 'function')
                ? window.TempoPAS.getLatestResult()
                : null;

            let historyPASHTML = '';
            if (latestPAS) {
                const dt = new Date(latestPAS.completedAt).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
                historyPASHTML = `
                    <div class="mt-4 p-3.5 bg-[#F4F7F5] rounded-2xl border border-[#CDE9DA] text-xs text-[#284132] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div class="flex items-center space-x-2">
                            <span>📋</span>
                            <span>Lần làm gần nhất: <strong>${latestPAS.score} / 90 (Trung bình ${(latestPAS.score / 18).toFixed(1)} / 5.0)</strong> • Ngày ${dt}</span>
                        </div>
                        <span class="text-[11px] font-bold text-[#4A6B5D] shrink-0">Lịch sử an toàn</span>
                    </div>
                `;
            }

            contentBox.innerHTML = `
                <div class="w-16 h-16 rounded-2xl bg-[#EAF0EB] text-[#4A6356] border border-[#BACAD0] flex items-center justify-center mx-auto text-2xl shadow-xs">
                    ${data.icon}
                </div>
                <div class="space-y-1">
                    <span class="text-xs font-bold uppercase tracking-wider text-[#829B87]">Selected Category</span>
                    <h2 class="text-xl sm:text-2xl font-extrabold text-[#202124]">${data.title}</h2>
                    <p class="text-sm text-[#6F6B68] max-w-md mx-auto leading-relaxed pt-1">
                        ${data.summary}
                    </p>
                </div>

                <!-- Assessments List Container -->
                <div class="grid grid-cols-1 gap-5 pt-3 max-w-2xl mx-auto text-left">
                    <!-- PAS Assessment Item Card -->
                    <div class="bg-[#FEFAF4] border border-[#EAE4DF] hover:border-[#829B87] transition rounded-3xl p-6 shadow-xs space-y-4">
                        <div class="space-y-2">
                            <div class="flex flex-wrap items-center gap-2">
                                <span class="px-2.5 py-1 rounded-full text-[11px] font-extrabold bg-[#EAF0EB] text-[#4A6B5D] border border-[#BACAD0]">
                                    Academic Stress Scale
                                </span>
                                <span class="text-xs text-stone-500 font-semibold">• 18 câu hỏi</span>
                                <span class="text-xs text-stone-500 font-semibold">• ~5 phút</span>
                                <span class="text-xs text-stone-500 font-semibold">• Thang điểm: 18–90</span>
                            </div>
                            <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#202124]">
                                Academic Stress Check (PAS)
                            </h3>
                            <p class="text-xs font-semibold text-[#829B87]">
                                Perception of Academic Stress Scale • Bedewy &amp; Gabriel (2015)
                            </p>
                            <p class="text-xs sm:text-sm text-[#5B5550] leading-relaxed">
                                Thang đo 18 câu hỏi giúp sinh viên đại học nhận diện mức độ căng thẳng học tập và các nguồn áp lực từ khối lượng học, kỳ vọng và thi cử. Công cụ tự đánh giá phản ánh cá nhân, không phải chẩn đoán y khoa.
                            </p>
                            <div class="text-[11px] text-stone-400 italic">
                                Nghiên cứu gốc: Dalia Bedewy &amp; Adel Gabriel (2015), Health Psychology Open. Giấy phép CC BY-NC 3.0.
                            </div>
                        </div>

                        ${historyPASHTML}

                        <div class="pt-3 border-t border-[#EAE4DF] flex items-center justify-between">
                            <span class="text-xs text-stone-500 italic">Bảo mật &amp; riêng tư</span>
                            <button type="button" 
                                    id="btn-start-pas"
                                    onclick="window.TempoExploreAssessments.openPAS()"
                                    class="px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#829B87] hover:bg-[#728A77] text-white shadow-xs transition cursor-pointer">
                                ${latestPAS ? 'Làm lại bài kiểm tra' : 'Bắt đầu làm bài →'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
            return;
        }

        // Default placeholder detail card for other categories (other)
        contentBox.innerHTML = `
            <div class="w-16 h-16 rounded-2xl bg-[#EAF0EB] text-[#4A6356] border border-[#BACAD0] flex items-center justify-center mx-auto text-2xl shadow-xs">
                ${data.icon}
            </div>
            <div class="space-y-1">
                <span class="text-xs font-bold uppercase tracking-wider text-[#829B87]">Selected Category</span>
                <h2 class="text-xl sm:text-2xl font-extrabold text-[#202124]">${data.title}</h2>
                <p class="text-sm text-[#6F6B68] max-w-md mx-auto leading-relaxed pt-1">
                    ${data.summary}
                </p>
            </div>
            <div class="pt-2 text-xs text-stone-500 bg-stone-50 rounded-2xl p-4 max-w-lg mx-auto border border-stone-200/60">
                ℹ️ ${data.note}
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

    return {
        CATEGORIES,
        getActiveCategory,
        selectCategory,
        openPHQ9,
        openCESD,
        openGAD7,
        openPAS,
        render
    };
})();
