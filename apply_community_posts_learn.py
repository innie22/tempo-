import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('communityPosts.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update updateCommunitySidebar
old_sidebar = '''        const tabLabels = {
            announcement: isVi ? 'Thông báo' : 'Announcement',
            tips: 'Tips',
            learn: 'Learn',
            posts: isVi ? 'Bài viết' : 'Posts',
            messages: isVi ? 'Tin nhắn riêng' : 'Direct Message'
        };'''

new_sidebar = '''        const tabLabels = {
            announcement: isVi ? 'Thông báo' : 'Announcement',
            tips: 'Tips',
            learn: isVi ? 'Kiến thức' : 'Learn',
            posts: isVi ? 'Bài viết' : 'Posts',
            messages: isVi ? 'Tin nhắn riêng' : 'Direct Message'
        };'''

# 2. Add updateLearnToolbar and getLearnDisplay
old_static_ui = '''    function updateCommunityStaticUI() {
        updateReturnButton();
        updateCommunitySidebar();
        updatePostsToolbar();
        updateTipsToolbar();
    }'''

new_static_ui = '''    function updateLearnToolbar() {
        const isVi = isViLocale();
        const searchInput = document.getElementById('learn-search-input');
        if (searchInput) searchInput.placeholder = isVi ? 'Tìm kiếm...' : 'Search...';
    }

    function getLearnDisplay(item) {
        const isVi = isViLocale();
        if (window.TempoI18n && typeof window.TempoI18n.t === 'function') {
            const locTitle = window.TempoI18n.t(`community.learn.cards.${item.id}.title`);
            const locSummary = window.TempoI18n.t(`community.learn.cards.${item.id}.summary`);
            if (locTitle && locTitle !== `community.learn.cards.${item.id}.title`) {
                return {
                    title: locTitle,
                    summary: locSummary || item.summary
                };
            }
        }
        const learnTranslations = {
            what_is_stress: {
                vi: {
                    title: 'Stress là gì?',
                    summary: 'Căng thẳng là trạng thái lo lắng hoặc áp lực tinh thần xuất phát từ một tình huống khó khăn. Đây là phản ứng tự nhiên của con người, giúp chúng ta đối mặt với những thử thách và mối đe dọa trong cuộc sống. Mỗi người đều trải qua căng thẳng ở một mức độ nhất định.'
                },
                en: {
                    title: 'What is stress?',
                    summary: 'Stress is a state of worry or mental tension caused by a difficult situation. Stress is a natural human response that prompts us to address challenges and threats in our lives. Everyone experiences stress to some degree.'
                }
            },
            stress_eating: {
                vi: {
                    title: 'Ăn uống do căng thẳng',
                    summary: 'Ăn uống do căng thẳng, hay còn gọi là ăn uống theo cảm xúc, là việc sử dụng thức ăn để cải thiện cảm xúc hoặc khiến bản thân cảm thấy dễ chịu hơn, thay vì đáp ứng nhu cầu đói về mặt thể chất.'
                },
                en: {
                    title: 'Stress eating',
                    summary: 'Stress eating, or emotional eating, is using food to make yourself feel better—eating to satisfy emotional needs, rather than to satisfy physical hunger.'
                }
            },
            stress_loop: {
                vi: {
                    title: 'Vòng lặp căng thẳng ở sinh viên',
                    summary: 'Cách những deadline dồn dập kích hoạt trạng thái tê liệt tinh thần, tạo ra các vòng lặp né tránh làm tăng thêm mức độ căng thẳng.'
                },
                en: {
                    title: 'The Student Stress Loop',
                    summary: 'How acute deadlines trigger mental paralysis, creating avoidance loops that multiply stress levels.'
                }
            }
        };
        const t = learnTranslations[item.id];
        if (t) {
            const loc = isVi ? t.vi : t.en;
            return {
                title: loc.title || item.title,
                summary: loc.summary || item.summary
            };
        }
        return {
            title: item.title,
            summary: item.summary
        };
    }

    function updateCommunityStaticUI() {
        updateReturnButton();
        updateCommunitySidebar();
        updatePostsToolbar();
        updateTipsToolbar();
        updateLearnToolbar();
    }'''

# 3. Update renderLearn
old_render_learn = '''    function renderLearn() {
        const container = document.getElementById('learn-cards-grid');
        const emptyState = document.getElementById('learn-empty-state');
        if (!container) return;

        let filtered = [...learn];
        if (currentLearnSearch) {
            const q = currentLearnSearch.toLowerCase();
            filtered = filtered.filter(l => (l.title || '').toLowerCase().includes(q) || (l.summary || '').toLowerCase().includes(q));
        }

        if (filtered.length === 0) {
            container.innerHTML = '';
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }

        if (emptyState) emptyState.classList.add('hidden');

        container.innerHTML = filtered.map(item => {
            return `
                <div class="bg-[#FFFDFB] border-2 border-[#ECA689] rounded-3xl p-5 sm:p-6 shadow-xs flex flex-col md:flex-row items-center justify-between gap-5">
                    <!-- Left Side: Text -->
                    <div class="flex-1 space-y-2">
                        <h3 class="font-heading text-[16px] sm:text-[18px] font-bold text-[#4A4541]">
                            ${escapeHtml(item.title)}
                        </h3>
                        <p class="text-xs sm:text-[13px] text-[#6E6964] leading-relaxed">
                            ${escapeHtml(item.summary)}
                        </p>
                        <div>
                            <button type="button" 
                                    onclick="window.TempoCommunity.openLearnDetail('${escapeHtml(item.id)}')"
                                    class="text-[#DE8662] font-bold text-xs sm:text-[13px] hover:underline inline-flex items-center space-x-1 cursor-pointer">
                                <span>See more</span>
                                <span>→</span>
                            </button>
                        </div>
                    </div>

                    <!-- Right Side: Illustration / Photo -->
                    <div class="w-full md:w-64 h-36 sm:h-40 overflow-hidden rounded-2xl bg-stone-50 flex items-center justify-center shrink-0">
                        <img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.title)}" class="w-full h-full object-cover">
                    </div>
                </div>
            `;
        }).join('');
    }'''

new_render_learn = '''    function renderLearn() {
        const container = document.getElementById('learn-cards-grid');
        const emptyState = document.getElementById('learn-empty-state');
        if (!container) return;

        updateLearnToolbar();

        const isVi = isViLocale();
        const seeMoreText = isVi ? 'Xem thêm' : 'See more';

        let filtered = [...learn];
        if (currentLearnSearch) {
            const q = currentLearnSearch.toLowerCase();
            filtered = filtered.filter(l => {
                const disp = getLearnDisplay(l);
                return (disp.title || '').toLowerCase().includes(q) || 
                       (disp.summary || '').toLowerCase().includes(q) ||
                       (l.title || '').toLowerCase().includes(q) || 
                       (l.summary || '').toLowerCase().includes(q);
            });
        }

        if (filtered.length === 0) {
            container.innerHTML = '';
            if (emptyState) {
                emptyState.classList.remove('hidden');
                const emptyTitle = emptyState.querySelector('h3');
                if (emptyTitle) emptyTitle.textContent = isVi ? 'Không tìm thấy chủ đề kiến thức nào' : 'No educational topics found';
                const emptyDesc = emptyState.querySelector('p');
                if (emptyDesc) emptyDesc.textContent = isVi ? 'Hãy thử tìm kiếm với từ khóa khác hoặc đặt lại tìm kiếm.' : 'Try searching with a broader keyword or clearing your search.';
                const emptyBtn = emptyState.querySelector('button');
                if (emptyBtn) emptyBtn.textContent = isVi ? 'Đặt lại tìm kiếm' : 'Reset Search';
            }
            return;
        }

        if (emptyState) emptyState.classList.add('hidden');

        container.innerHTML = filtered.map(item => {
            const disp = getLearnDisplay(item);
            return `
                <div class="bg-[#FFFDFB] border-2 border-[#ECA689] rounded-3xl p-5 sm:p-6 shadow-xs flex flex-col md:flex-row items-center justify-between gap-5" data-learn-id="${escapeHtml(item.id)}">
                    <!-- Left Side: Text -->
                    <div class="flex-1 space-y-2">
                        <h3 class="font-heading text-[16px] sm:text-[18px] font-bold text-[#4A4541]">
                            ${escapeHtml(disp.title)}
                        </h3>
                        <p class="text-xs sm:text-[13px] text-[#6E6964] leading-relaxed">
                            ${escapeHtml(disp.summary)}
                        </p>
                        <div>
                            <button type="button" 
                                    onclick="window.TempoCommunity.openLearnDetail('${escapeHtml(item.id)}')"
                                    class="text-[#DE8662] font-bold text-xs sm:text-[13px] hover:underline inline-flex items-center space-x-1 cursor-pointer">
                                <span>${escapeHtml(seeMoreText)}</span>
                                <span>→</span>
                            </button>
                        </div>
                    </div>

                    <!-- Right Side: Illustration / Photo -->
                    <div class="w-full md:w-64 h-36 sm:h-40 overflow-hidden rounded-2xl bg-stone-50 flex items-center justify-center shrink-0">
                        <img src="${escapeHtml(item.image)}" alt="${escapeHtml(disp.title)}" class="w-full h-full object-cover">
                    </div>
                </div>
            `;
        }).join('');
    }'''

# 4. Update onLanguageChange
old_lang_change = '''            const tipsPanel = document.getElementById('community-panel-tips');
            if (tipsPanel && !tipsPanel.classList.contains('hidden')) {
                renderTips();
            }'''

new_lang_change = '''            const tipsPanel = document.getElementById('community-panel-tips');
            if (tipsPanel && !tipsPanel.classList.contains('hidden')) {
                renderTips();
            }
            const learnPanel = document.getElementById('community-panel-learn');
            if (learnPanel && !learnPanel.classList.contains('hidden')) {
                renderLearn();
            }'''

# 5. Update public exports
old_exports = '''        updatePostsToolbar,
        updateTipsToolbar,
        updateCommunityStaticUI,
        getTipDisplay,'''

new_exports = '''        updatePostsToolbar,
        updateTipsToolbar,
        updateLearnToolbar,
        updateCommunityStaticUI,
        getTipDisplay,
        getLearnDisplay,'''

content_norm = content.replace('\r\n', '\n')
assert old_sidebar.replace('\r\n', '\n') in content_norm, "old_sidebar not found"
assert old_static_ui.replace('\r\n', '\n') in content_norm, "old_static_ui not found"
assert old_render_learn.replace('\r\n', '\n') in content_norm, "old_render_learn not found"
assert old_lang_change.replace('\r\n', '\n') in content_norm, "old_lang_change not found"
assert old_exports.replace('\r\n', '\n') in content_norm, "old_exports not found"

content_norm = content_norm.replace(old_sidebar.replace('\r\n', '\n'), new_sidebar.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_static_ui.replace('\r\n', '\n'), new_static_ui.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_render_learn.replace('\r\n', '\n'), new_render_learn.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_lang_change.replace('\r\n', '\n'), new_lang_change.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_exports.replace('\r\n', '\n'), new_exports.replace('\r\n', '\n'))

content_crlf = content_norm.replace('\n', '\r\n')
with open('communityPosts.js', 'wb') as f:
    f.write(content_crlf.encode('utf-8'))

print("Updated communityPosts.js with Learn localization (CRLF).")
