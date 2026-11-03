import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('communityPosts.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update INITIAL_TIPS
old_initial_tips = '''    // Reference 2: Tips (Solve) Situations
    const INITIAL_TIPS = [
        {
            id: 'deadline_pileup',
            title: 'The 5-Minute Starter Rule for Paralyzing Deadlines',
            usage: 'Try it when you have a lot to do that makes you not want to do anything at all'
        },
        {
            id: 'presentation_dread',
            title: 'Presentation anxiety',
            usage: 'Try it when you have a presentation ahead and you feel anxious about it'
        },
        {
            id: 'brain_fog_reset',
            title: 'Brain Fog Reset & Mental Momentum',
            usage: 'Try it when mental fatigue blocks focus and simple tasks feel impossible'
        },
        {
            id: 'exam_panic_surge',
            title: 'Exam panic & physiological sigh reset',
            usage: 'Try it when sudden panic spikes right before or during a major test'
        },
        {
            id: 'email_paralysis',
            title: 'Professor extension email template',
            usage: 'Try it when severe stress requires requesting an urgent assignment extension'
        },
        {
            id: 'sleep_runaway',
            title: 'Racing night thoughts wind-down',
            usage: 'Try it when academic worries keep you awake well past 2 AM'
        }
    ];'''

new_initial_tips = '''    // Reference 2: Tips (Solve) Situations
    const INITIAL_TIPS = [
        {
            id: 'deadline_pileup',
            title: 'The 5-Minute Starter Rule for Paralyzing Deadlines',
            usage: 'Try it when you have a lot to do that makes you not want to do anything at all.'
        },
        {
            id: 'presentation_dread',
            title: 'Presentation anxiety',
            usage: 'Try it when you have a presentation ahead and you feel anxious about it.'
        },
        {
            id: 'brain_fog_reset',
            title: 'Brain Fog Reset & Mental Momentum',
            usage: 'Try it when mental fatigue blocks focus and simple tasks feel impossible.'
        },
        {
            id: 'exam_panic_surge',
            title: 'Exam panic & physiological sigh reset',
            usage: 'Try it when sudden panic spikes right before or during a major test.'
        },
        {
            id: 'email_paralysis',
            title: 'Professor extension email template',
            usage: 'Try it when severe stress requires requesting an urgent assignment extension.'
        },
        {
            id: 'sleep_runaway',
            title: 'Racing night thoughts wind-down',
            usage: 'Try it when academic worries keep you awake well past 2 AM.'
        },
        {
            id: 'falling_behind',
            title: 'Falling behind / not keeping up',
            usage: 'Struggling to keep pace with lecture material, required readings, or lab work.'
        },
        {
            id: 'teamwork',
            title: 'Teamwork problems',
            usage: 'Unbalanced workload, unresponsive group members, or communication friction.'
        },
        {
            id: 'grades',
            title: 'Grades didn’t go as expected',
            usage: 'Coping with academic disappointment and extracting constructive next steps.'
        }
    ];'''

# 2. Update updateCommunityStaticUI and add updateTipsToolbar and getTipDisplay
old_static_ui = '''    function updateCommunityStaticUI() {
        updateReturnButton();
        updateCommunitySidebar();
        updatePostsToolbar();
    }'''

new_static_ui = '''    function updateTipsToolbar() {
        const isVi = isViLocale();
        const searchInput = document.getElementById('tips-search-input');
        if (searchInput) {
            searchInput.placeholder = isVi ? 'Tìm kiếm...' : 'Search...';
        }
    }

    function getTipDisplay(item) {
        const isVi = isViLocale();
        if (window.TempoI18n && typeof window.TempoI18n.t === 'function') {
            const locTitle = window.TempoI18n.t(`community.tips.items.${item.id}.title`);
            const locUsage = window.TempoI18n.t(`community.tips.items.${item.id}.usage`);
            if (locTitle && locTitle !== `community.tips.items.${item.id}.title`) {
                return {
                    title: locTitle,
                    usage: locUsage || item.usage
                };
            }
        }
        const tipsTranslations = {
            deadline_pileup: {
                vi: {
                    title: 'Quy tắc bắt đầu 5 phút khi deadline khiến bạn tê liệt',
                    usage: 'Thử áp dụng khi bạn có quá nhiều việc phải làm đến mức không biết bắt đầu từ đâu.'
                },
                en: {
                    title: 'The 5-Minute Starter Rule for Paralyzing Deadlines',
                    usage: 'Try it when you have a lot to do that makes you not want to do anything at all.'
                }
            },
            presentation_dread: {
                vi: {
                    title: 'Lo lắng khi thuyết trình',
                    usage: 'Áp dụng khi bạn sắp có một buổi thuyết trình và cảm thấy lo lắng về điều đó.'
                },
                en: {
                    title: 'Presentation anxiety',
                    usage: 'Try it when you have a presentation ahead and you feel anxious about it.'
                }
            },
            brain_fog_reset: {
                vi: {
                    title: 'Xua tan sương mù tinh thần và lấy lại đà tập trung',
                    usage: 'Thử áp dụng khi sự mệt mỏi về tinh thần khiến bạn khó tập trung và ngay cả những việc đơn giản cũng trở nên khó khăn.'
                },
                en: {
                    title: 'Brain Fog Reset & Mental Momentum',
                    usage: 'Try it when mental fatigue blocks focus and simple tasks feel impossible.'
                }
            },
            exam_panic_surge: {
                vi: {
                    title: 'Giảm hoảng loạn trước kỳ thi bằng kỹ thuật thở dài sinh lý',
                    usage: 'Áp dụng khi bạn đột nhiên cảm thấy hoảng loạn ngay trước hoặc trong một bài kiểm tra quan trọng.'
                },
                en: {
                    title: 'Exam panic & physiological sigh reset',
                    usage: 'Try it when sudden panic spikes right before or during a major test.'
                }
            },
            email_paralysis: {
                vi: {
                    title: 'Mẫu email xin gia hạn deadline với giảng viên',
                    usage: 'Sử dụng khi bạn đang chịu áp lực lớn và cần xin gia hạn deadline bài tập một cách khẩn cấp.'
                },
                en: {
                    title: 'Professor extension email template',
                    usage: 'Try it when severe stress requires requesting an urgent assignment extension.'
                }
            },
            sleep_runaway: {
                vi: {
                    title: 'Thư giãn khi những suy nghĩ cứ tiếp diễn vào ban đêm',
                    usage: 'Thử áp dụng khi những lo lắng về học tập khiến bạn trằn trọc và không thể ngủ dù đã qua 2 giờ sáng.'
                },
                en: {
                    title: 'Racing night thoughts wind-down',
                    usage: 'Try it when academic worries keep you awake well past 2 AM.'
                }
            },
            falling_behind: {
                vi: {
                    title: 'Cảm thấy bị tụt lại phía sau trong học tập',
                    usage: 'Khi bạn gặp khó khăn trong việc theo kịp bài giảng, tài liệu đọc bắt buộc hoặc các bài thực hành.'
                },
                en: {
                    title: 'Falling behind / not keeping up',
                    usage: 'Struggling to keep pace with lecture material, required readings, or lab work.'
                }
            },
            teamwork: {
                vi: {
                    title: 'Khó khăn khi làm việc nhóm',
                    usage: 'Khi khối lượng công việc không được phân chia đồng đều, thành viên nhóm thiếu phản hồi hoặc giao tiếp gặp nhiều trở ngại.'
                },
                en: {
                    title: 'Teamwork problems',
                    usage: 'Unbalanced workload, unresponsive group members, or communication friction.'
                }
            },
            teamwork_problems: {
                vi: {
                    title: 'Khó khăn khi làm việc nhóm',
                    usage: 'Khi khối lượng công việc không được phân chia đồng đều, thành viên nhóm thiếu phản hồi hoặc giao tiếp gặp nhiều trở ngại.'
                },
                en: {
                    title: 'Teamwork problems',
                    usage: 'Unbalanced workload, unresponsive group members, or communication friction.'
                }
            },
            grades: {
                vi: {
                    title: 'Kết quả học tập không như mong đợi',
                    usage: 'Khi bạn cảm thấy thất vọng về kết quả học tập và cần tìm ra những bước tiếp theo mang tính xây dựng.'
                },
                en: {
                    title: 'Grades didn’t go as expected',
                    usage: 'Coping with academic disappointment and extracting constructive next steps.'
                }
            },
            grades_disappointment: {
                vi: {
                    title: 'Kết quả học tập không như mong đợi',
                    usage: 'Khi bạn cảm thấy thất vọng về kết quả học tập và cần tìm ra những bước tiếp theo mang tính xây dựng.'
                },
                en: {
                    title: 'Grades didn’t go as expected',
                    usage: 'Coping with academic disappointment and extracting constructive next steps.'
                }
            }
        };

        const t = tipsTranslations[item.id];
        if (t) {
            const loc = isVi ? t.vi : t.en;
            return {
                title: loc.title || item.title,
                usage: loc.usage || item.usage
            };
        }
        return {
            title: item.title,
            usage: item.usage
        };
    }

    function updateCommunityStaticUI() {
        updateReturnButton();
        updateCommunitySidebar();
        updatePostsToolbar();
        updateTipsToolbar();
    }'''

# 3. Update renderTips and openTipDetail
old_render_tips = '''    function renderTips() {
        const container = document.getElementById('tips-cards-grid');
        const emptyState = document.getElementById('tips-empty-state');
        if (!container) return;

        let filtered = [...tips];

        // Also merge situations from TempoLearnSolve if not present
        if (window.TempoLearnSolve && typeof window.TempoLearnSolve.getSituations === 'function') {
            const extra = window.TempoLearnSolve.getSituations();
            extra.forEach(s => {
                if (!filtered.some(f => f.id === s.id)) {
                    filtered.push({
                        id: s.id,
                        title: s.title,
                        usage: s.shortDescription || 'Actionable coping guide'
                    });
                }
            });
        }

        if (currentTipsSearch) {
            const q = currentTipsSearch.toLowerCase();
            filtered = filtered.filter(t => (t.title || '').toLowerCase().includes(q) || (t.usage || '').toLowerCase().includes(q));
        }

        if (filtered.length === 0) {
            container.innerHTML = '';
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }

        if (emptyState) emptyState.classList.add('hidden');

        container.innerHTML = filtered.map(item => {
            return `
                <div class="h-full bg-[#FFFDFB] border-2 border-[#ECA689] rounded-3xl p-5 sm:p-6 shadow-xs flex flex-col justify-between space-y-3 min-h-[190px] transition hover:shadow-xs">
                    <div class="space-y-2">
                        <h3 class="font-heading text-[13.5px] sm:text-[14px] font-bold text-[#4A4541] leading-snug">
                            ${escapeHtml(item.title)}
                        </h3>
                        <p class="text-xs sm:text-[12.5px] text-[#6E6964] leading-relaxed">
                            <strong class="text-[#DE8662] font-bold">Usage:</strong> ${escapeHtml(item.usage)}
                        </p>
                    </div>

                    <div>
                        <button type="button" 
                                onclick="window.TempoCommunity.openTipDetail('${escapeHtml(item.id)}')"
                                class="text-[#DE8662] font-bold text-xs sm:text-[13px] flex items-center space-x-1 hover:underline cursor-pointer">
                            <span>See more</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    function openTipDetail(id) {
        if (window.TempoLearnSolve && typeof window.TempoLearnSolve.openSituationModal === 'function') {
            window.TempoLearnSolve.openSituationModal(id);
        } else if (window.TempoLearnSolve && typeof window.TempoLearnSolve.openModal === 'function') {
            window.TempoLearnSolve.openModal(id);
        } else if (window.TempoApp) {
            window.TempoApp.showToast("Opening solution guide...");
        }
    }'''

new_render_tips = '''    function renderTips() {
        const container = document.getElementById('tips-cards-grid');
        const emptyState = document.getElementById('tips-empty-state');
        if (!container) return;

        updateTipsToolbar();

        const isVi = isViLocale();
        const usageLabel = isVi ? 'Cách sử dụng:' : 'Usage:';
        const seeMoreText = isVi ? 'Xem thêm' : 'See more';

        let filtered = [...tips];

        if (currentTipsSearch) {
            const q = currentTipsSearch.toLowerCase();
            filtered = filtered.filter(t => {
                const disp = getTipDisplay(t);
                return (disp.title || '').toLowerCase().includes(q) || 
                       (disp.usage || '').toLowerCase().includes(q) ||
                       (t.title || '').toLowerCase().includes(q) || 
                       (t.usage || '').toLowerCase().includes(q);
            });
        }

        if (filtered.length === 0) {
            container.innerHTML = '';
            if (emptyState) {
                emptyState.classList.remove('hidden');
                const emptyTitle = emptyState.querySelector('h3');
                if (emptyTitle) emptyTitle.textContent = isVi ? 'Không tìm thấy giải pháp phù hợp' : 'No matching solutions found';
                const emptyDesc = emptyState.querySelector('p');
                if (emptyDesc) emptyDesc.textContent = isVi ? 'Hãy thử tìm kiếm bằng các từ khóa khác.' : 'Try searching with different terms.';
                const emptyBtn = emptyState.querySelector('button');
                if (emptyBtn) emptyBtn.textContent = isVi ? 'Đặt lại tìm kiếm' : 'Reset Search';
            }
            return;
        }

        if (emptyState) emptyState.classList.add('hidden');

        container.innerHTML = filtered.map(item => {
            const disp = getTipDisplay(item);
            return `
                <div class="h-full bg-[#FFFDFB] border-2 border-[#ECA689] rounded-3xl p-5 sm:p-6 shadow-xs flex flex-col justify-between space-y-3 min-h-[190px] transition hover:shadow-xs" data-tip-id="${escapeHtml(item.id)}">
                    <div class="space-y-2">
                        <h3 class="font-heading text-[13.5px] sm:text-[14px] font-bold text-[#4A4541] leading-snug">
                            ${escapeHtml(disp.title)}
                        </h3>
                        <p class="text-xs sm:text-[12.5px] text-[#6E6964] leading-relaxed">
                            <strong class="text-[#DE8662] font-bold">${escapeHtml(usageLabel)}</strong> ${escapeHtml(disp.usage)}
                        </p>
                    </div>

                    <div>
                        <button type="button" 
                                onclick="window.TempoCommunity.openTipDetail('${escapeHtml(item.id)}')"
                                class="text-[#DE8662] font-bold text-xs sm:text-[13px] flex items-center space-x-1 hover:underline cursor-pointer">
                            <span>${escapeHtml(seeMoreText)}</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    function openTipDetail(id) {
        let mappedId = id;
        if (id === 'presentation_dread') mappedId = 'presentation_anxiety';
        else if (id === 'brain_fog_reset') mappedId = 'cant_focus';
        else if (id === 'teamwork_problems') mappedId = 'teamwork';
        else if (id === 'grades_disappointment') mappedId = 'grades';

        if (window.TempoLearnSolve && typeof window.TempoLearnSolve.openSituationModal === 'function') {
            window.TempoLearnSolve.openSituationModal(mappedId);
        } else if (window.TempoLearnSolve && typeof window.TempoLearnSolve.openModal === 'function') {
            window.TempoLearnSolve.openModal(mappedId);
        } else if (window.TempoApp) {
            window.TempoApp.showToast("Opening solution guide...");
        }
    }'''

# 4. Update onLanguageChange to re-render tips if tips panel is visible
old_lang_change = '''            const postsPanel = document.getElementById('community-panel-posts');
            if (postsPanel && !postsPanel.classList.contains('hidden')) {
                renderCommunityPosts();
            }'''

new_lang_change = '''            const postsPanel = document.getElementById('community-panel-posts');
            if (postsPanel && !postsPanel.classList.contains('hidden')) {
                renderCommunityPosts();
            }
            const tipsPanel = document.getElementById('community-panel-tips');
            if (tipsPanel && !tipsPanel.classList.contains('hidden')) {
                renderTips();
            }'''

# 5. Update exported public API
old_exports = '''        updatePostsToolbar,
        updateCommunityStaticUI,'''

new_exports = '''        updatePostsToolbar,
        updateTipsToolbar,
        updateCommunityStaticUI,
        getTipDisplay,'''

assert old_initial_tips.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_initial_tips not found"
assert old_static_ui.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_static_ui not found"
assert old_render_tips.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_render_tips not found"
assert old_lang_change.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_lang_change not found"
assert old_exports.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_exports not found"

content_norm = content.replace('\r\n', '\n')
content_norm = content_norm.replace(old_initial_tips.replace('\r\n', '\n'), new_initial_tips.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_static_ui.replace('\r\n', '\n'), new_static_ui.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_render_tips.replace('\r\n', '\n'), new_render_tips.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_lang_change.replace('\r\n', '\n'), new_lang_change.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_exports.replace('\r\n', '\n'), new_exports.replace('\r\n', '\n'))

content_crlf = content_norm.replace('\n', '\r\n')

with open('communityPosts.js', 'wb') as f:
    f.write(content_crlf.encode('utf-8'))

print("communityPosts.js updated successfully with Tips localization (strict CRLF).")
