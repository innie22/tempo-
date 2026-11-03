/**
 * Tempo Community Module
 * Pixel-accurate reproduction of the 5 user-supplied reference screenshots:
 * Reference 1 — Announcement
 * Reference 2 — Tips (Solve)
 * Reference 3 — Learn
 * Reference 4 — Posts
 * Reference 5 — Direct Message
 *
 * Polished for:
 * 1. Robust flex search bar layout (zero overlap)
 * 2. Reduced typography by ~5px across hierarchy
 * 3. Empty states for Direct Message (no fabricated conversations or fake messages)
 * 4. Chat Requests exact symbol integration & accept/decline request management
 * 5. Posts sidebar navigation always returning to canonical newsfeed
 */

window.TempoCommunity = (function() {
    'use strict';

    function isViLocale() {
        return !window.TempoI18n || typeof window.TempoI18n.getLanguage !== 'function' || window.TempoI18n.getLanguage() === 'vi';
    }

    // =========================================================================
    // 1. DATASETS & CONTENT
    // =========================================================================

    // Reference 1: Official Announcements
    const INITIAL_ANNOUNCEMENTS = [
        {
            id: 'ann-1',
            title: 'Self-check update v2.1',
            summary: 'In this version, users are allowed to customize the tracking items by type, method, and also set up an alert for each of them.',
            content: 'In this version, users are allowed to customize the tracking items by type, method, and also set up an alert for each of them. Daily check-in alerts help you detect early stress signals and sustain positive habits.',
            coverImage: 'assets/announcement_selfcheck_v21.png',
            publishedAt: 'Today',
            author: 'Tempo Product Team',
            actionLabel: 'Try it now',
            actionRoute: 'stress-check'
        },
        {
            id: 'ann-2',
            title: 'Version update: v2.1',
            summary: 'We have updated the newest version of Tempo, please check it out.',
            content: 'We have updated the newest version of Tempo, please check it out. Recovery Mode dashboard, Quick Relief exercises, and Learn & Solve resources have all been refined for peak clarity and ease of use.',
            coverImage: 'assets/announcement_rmode_v21.png',
            publishedAt: 'Recently',
            author: 'Tempo Product Team',
            actionLabel: 'Try it now',
            actionRoute: 'recovery-mode'
        }
    ];

    // Reference 2: Tips (Solve) Situations
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
    ];

    // Reference 3: Learn Stress Topics
    const INITIAL_LEARN = [
        {
            id: 'what_is_stress',
            title: 'What is stress?',
            summary: 'Stress is a state of worry or mental tension caused by a difficult situation. Stress is a natural human response that prompts us to address challenges and threats in our lives. Everyone experiences stress to some degree.',
            image: 'assets/what_is_stress_scribble.svg'
        },
        {
            id: 'stress_eating',
            title: 'Stress eating',
            summary: 'Stress eating, or emotional eating, is using food to make yourself feel better—eating to satisfy emotional needs, rather than to satisfy physical hunger.',
            image: 'assets/stress_eating_donut.jpg'
        },
        {
            id: 'stress_loop',
            title: 'The Student Stress Loop',
            summary: 'How acute deadlines trigger mental paralysis, creating avoidance loops that multiply stress levels.',
            image: 'assets/practice-breathing-mascot.png'
        }
    ];

    // Reference 4: Community Posts Feed
    const INITIAL_POSTS = [
        {
            id: 'post-1',
            authorId: 'user-fpt-bakhi',
            authorName: 'FPT Bá khí',
            authorHandle: '@fpt_bakhi',
            timeAgo: '2 hours ago',
            avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=120&h=120&q=80',
            content: 'How to survive 4 projects in just 2 weeks without destroying my mental health? Urgent situation, please give me some tips. Thank you all.',
            tags: [
                { label: 'mental health', bg: 'bg-[#E8F0F5]', text: 'text-[#4A728A]' },
                { label: 'Deadline', bg: 'bg-[#FCEFE8]', text: 'text-[#DE8662]' }
            ],
            likes: 29,
            commentsCount: 5,
            isLiked: false,
            isBookmarked: false,
            layout: 'two-column',
            comments: [
                {
                    id: 'c-1',
                    author: 'NNN',
                    time: '2 hours ago',
                    text: "omg, same here. i'm dying in fpt deadline"
                },
                {
                    id: 'c-2',
                    author: 'FPT Bá khí',
                    time: '2 hours ago',
                    text: 'Would you like to be a white deer with me???'
                }
            ]
        },
        {
            id: 'post-2',
            authorId: 'user-temposocute',
            authorName: 'Temposocute',
            authorHandle: '@temposocute',
            timeAgo: '5 hours ago',
            avatar: 'assets/tempo-logo.png',
            content: 'Hello, we have updated more background for Focus Zone, check it out now!',
            tags: [
                { label: 'Focus zone', bg: 'bg-[#E3EDE7]', text: 'text-[#3E7059]' },
                { label: 'Background', bg: 'bg-[#FBF0DC]', text: 'text-[#8C6B37]' }
            ],
            thumbnails: [
                'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=300&q=80',
                'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=300&q=80',
                'https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=300&q=80',
                'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=300&q=80'
            ],
            likes: 58,
            commentsCount: 20,
            isLiked: false,
            isBookmarked: false,
            comments: [
                {
                    id: 'c-3',
                    author: 'Sarah W.',
                    time: '3h ago',
                    text: 'When that happens to me, I drop expectations to zero and just do a 10-minute walk with music.'
                }
            ]
        }
    ];

    // Reference 5: Direct Message Conversations (EMPTY BY DEFAULT — NO FABRICATED ENTRIES)
    const INITIAL_CONVERSATIONS = [];

    // State
    let announcements = [...INITIAL_ANNOUNCEMENTS];
    let tips = [...INITIAL_TIPS];
    let learn = [...INITIAL_LEARN];
    let posts = [...INITIAL_POSTS];
    let conversations = [];
    let chatRequests = [];
    let activeTab = 'announcement';
    let activeConvId = null;
    let currentTipsSearch = '';
    let currentLearnSearch = '';
    let currentPostsSearch = '';
    let isFilterMyPosts = false;
    let isFilterBookmarks = false;
    let expandedFullWidthComments = new Set();

    // =========================================================================
    // 2. INITIALIZATION & STORAGE
    // =========================================================================
    function init() {
        loadAnnouncements();
        loadPosts();
        loadConversations();
        loadChatRequests();
        renderHomepagePreview();
        renderUrgentPreview();
        renderRecoveryPreview();
        updateCommunityStaticUI();
        bindEvents();
    }

    function loadAnnouncements() {
        try {
            const saved = localStorage.getItem('tempo_official_announcements');
            if (saved) {
                const parsed = JSON.parse(saved);
                if (Array.isArray(parsed) && parsed.length > 0) announcements = parsed;
            }
        } catch (e) {}
    }

    function saveAnnouncements() {
        try {
            localStorage.setItem('tempo_official_announcements', JSON.stringify(announcements));
        } catch (e) {}
    }

    function getUserBookmarksKey() {
        const currentUser = window.TempoAuth ? window.TempoAuth.getCurrentUser() : null;
        const userId = currentUser ? currentUser.id : 'guest';
        return `tempo_user_bookmarks_${userId}`;
    }

    function getUserBookmarks() {
        try {
            const key = getUserBookmarksKey();
            const saved = localStorage.getItem(key);
            if (saved) {
                const parsed = JSON.parse(saved);
                if (Array.isArray(parsed)) return parsed;
            }
        } catch (e) {}
        return [];
    }

    function saveUserBookmarks(bookmarksList) {
        try {
            const key = getUserBookmarksKey();
            const deduplicated = Array.from(new Set(bookmarksList));
            localStorage.setItem(key, JSON.stringify(deduplicated));
        } catch (e) {}
    }

    function syncUserBookmarksState() {
        const userBookmarks = getUserBookmarks();
        posts.forEach(p => {
            if (userBookmarks.length > 0) {
                p.isBookmarked = userBookmarks.includes(p.id);
            }
            if (Array.isArray(p.comments)) {
                p.commentsCount = p.comments.length;
            }
        });
    }

    function loadPosts() {
        try {
            const saved = localStorage.getItem('tempo_community_posts');
            if (saved) {
                const parsed = JSON.parse(saved);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    posts = INITIAL_POSTS.map(initP => {
                        const existing = parsed.find(p => p.id === initP.id);
                        return existing ? { ...initP, likes: existing.likes, isLiked: existing.isLiked, isBookmarked: existing.isBookmarked, comments: existing.comments || initP.comments } : initP;
                    });
                    parsed.forEach(p => {
                        if (!posts.some(initP => initP.id === p.id)) {
                            const normContent = (p.content || '').toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim();
                            const normAuthor = (p.authorName || '').trim().toLowerCase();
                            const isDup = posts.some(existing => {
                                const exContent = (existing.content || '').toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim();
                                const exAuthor = (existing.authorName || '').trim().toLowerCase();
                                return normAuthor === exAuthor && normContent === exContent;
                            });
                            if (!isDup) {
                                posts.push(p);
                            }
                        }
                    });
                }
            }
        } catch (e) {}
        syncUserBookmarksState();
        savePosts();
    }

    function savePosts() {
        try {
            localStorage.setItem('tempo_community_posts', JSON.stringify(posts));
        } catch (e) {}
    }

    function loadConversations() {
        try {
            const saved = localStorage.getItem('tempo_direct_messages');
            if (saved) {
                const parsed = JSON.parse(saved);
                if (Array.isArray(parsed)) {
                    // Filter out legacy hardcoded mock conversations so no fabricated entries persist
                    conversations = parsed.filter(c => c.id !== 'conv-badminton' && c.id !== 'conv-tempo-admin' && c.id !== 'conv-innie');
                }
            } else {
                conversations = [];
            }
        } catch (e) {
            conversations = [];
        }
        if (conversations.length > 0 && !activeConvId) {
            activeConvId = conversations[0].id;
        } else if (conversations.length === 0) {
            activeConvId = null;
        }
    }

    function saveConversations() {
        try {
            localStorage.setItem('tempo_direct_messages', JSON.stringify(conversations));
        } catch (e) {}
    }

    function loadChatRequests() {
        try {
            const saved = localStorage.getItem('tempo_chat_requests');
            if (saved) {
                const parsed = JSON.parse(saved);
                if (Array.isArray(parsed)) chatRequests = parsed;
            } else {
                chatRequests = [];
            }
        } catch (e) {
            chatRequests = [];
        }
        updateChatRequestsBadge();
    }

    function saveChatRequests() {
        try {
            localStorage.setItem('tempo_chat_requests', JSON.stringify(chatRequests));
        } catch (e) {}
        updateChatRequestsBadge();
    }

    function updateChatRequestsBadge() {
        const badge = document.getElementById('badge-chat-requests-count');
        if (badge) {
            if (chatRequests.length > 0) {
                badge.textContent = chatRequests.length;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        }
    }

    function isUserAdmin() {
        const profile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
        if (profile && (profile.role === 'admin' || profile.role === 'advisor')) return true;
        if (window.TempoApp && typeof window.TempoApp.getCurrentRole === 'function' && window.TempoApp.getCurrentRole() === 'admin') return true;
        return false;
    }

    // =========================================================================
    // 3. TAB NAVIGATION CONTROLLER
    // =========================================================================
    function selectTab(tabKey, updateHash = true) {
        const validTabs = ['announcement', 'tips', 'learn', 'posts', 'messages'];
        if (!validTabs.includes(tabKey)) tabKey = 'announcement';
        activeTab = tabKey;

        // Update URL hash
        if (updateHash) {
            const newHash = (tabKey === 'announcement') ? '#community' : `#community?tab=${tabKey}`;
            try {
                history.replaceState(null, '', newHash);
            } catch (e) {
                window.location.hash = newHash;
            }
        }

        // Update sidebar items active state matching Reference styling with reduced typography
        document.querySelectorAll('.community-nav-item').forEach(btn => {
            const btnTab = btn.getAttribute('data-community-tab');
            if (btnTab === activeTab) {
                btn.className = 'community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer bg-[#F7ECE1] text-[#DE8662]';
            } else {
                btn.className = 'community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]';
            }
        });

        // Update mobile buttons
        document.querySelectorAll('.community-mobile-tab-btn').forEach(btn => {
            const btnTab = btn.getAttribute('data-community-tab');
            if (btnTab === activeTab) {
                btn.className = 'community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-bold transition whitespace-nowrap bg-[#F7ECE1] text-[#DE8662] shadow-2xs';
            } else {
                btn.className = 'community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]';
            }
        });

        // Hide all panels, show active panel
        validTabs.forEach(p => {
            const panelEl = document.getElementById(`community-panel-${p}`);
            if (panelEl) {
                if (p === activeTab) panelEl.classList.remove('hidden');
                else panelEl.classList.add('hidden');
            }
        });

        updateCommunityStaticUI();
        syncAdminUI();

        if (activeTab === 'announcement') renderAnnouncements();
        else if (activeTab === 'tips') renderTips();
        else if (activeTab === 'learn') renderLearn();
        else if (activeTab === 'posts') renderCommunityPosts();
        else if (activeTab === 'messages') renderMessagesView();
    }

    function syncAdminUI() {
        const adminBtn = document.getElementById('btn-admin-new-announcement');
        if (adminBtn) {
            if (isUserAdmin()) adminBtn.classList.remove('hidden');
            else adminBtn.classList.add('hidden');
        }
    }

    function updateReturnButton() {
        const backBtn = document.getElementById('btn-community-back');
        const backLabel = document.getElementById('community-back-label');
        if (!backLabel) return;

        const isVi = isViLocale();
        const textLabel = isVi ? 'Quay lại Dashboard' : 'Return to Dashboard';
        const fullLabel = isVi ? '← Quay lại Dashboard' : '← Return to Dashboard';

        backLabel.textContent = textLabel;

        if (backBtn) {
            backBtn.setAttribute('title', fullLabel);
            backBtn.setAttribute('aria-label', fullLabel);
        }
    }

    function updateCommunitySidebar() {
        const isVi = isViLocale();
        const tabLabels = {
            announcement: isVi ? 'Thông báo' : 'Announcement',
            tips: 'Tips',
            learn: isVi ? 'Kiến thức' : 'Learn',
            posts: isVi ? 'Bài viết' : 'Posts',
            messages: isVi ? 'Tin nhắn riêng' : 'Direct Message'
        };
        document.querySelectorAll('.community-nav-item, .community-mobile-tab-btn').forEach(btn => {
            const tabKey = btn.getAttribute('data-community-tab');
            if (tabKey && tabLabels[tabKey]) {
                btn.textContent = tabLabels[tabKey];
            }
        });
    }

    function updatePostsToolbar() {
        const isVi = isViLocale();
        const labelNew = document.getElementById('label-posts-new');
        if (labelNew) labelNew.textContent = isVi ? 'Đăng bài mới' : 'New post';

        const searchInput = document.getElementById('posts-search-input');
        if (searchInput) searchInput.placeholder = isVi ? 'Tìm kiếm...' : 'Search...';

        const labelMy = document.getElementById('label-posts-filter-my');
        if (labelMy) labelMy.textContent = isVi ? 'Bài viết của tôi' : 'Your posts';

        const notifBtn = document.getElementById('btn-posts-notifications');
        if (notifBtn) {
            const notifText = isVi ? 'Thông báo' : 'Notifications';
            notifBtn.setAttribute('title', notifText);
            notifBtn.setAttribute('aria-label', notifText);
        }

        const bookmarksBtn = document.getElementById('btn-posts-filter-bookmarks');
        if (bookmarksBtn) {
            const bookmarksText = isVi ? 'Bài viết đã lưu' : 'Saved posts';
            bookmarksBtn.setAttribute('title', bookmarksText);
            bookmarksBtn.setAttribute('aria-label', bookmarksText);
        }
    }

    function updateTipsToolbar() {
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
                    usage: 'Try it when you have a lot to do that makes you not want to do anything at all'
                }
            },
            presentation_dread: {
                vi: {
                    title: 'Lo lắng khi thuyết trình',
                    usage: 'Áp dụng khi bạn sắp có một buổi thuyết trình và cảm thấy lo lắng về điều đó.'
                },
                en: {
                    title: 'Presentation anxiety',
                    usage: 'Try it when you have a presentation ahead and you feel anxious about it'
                }
            },
            brain_fog_reset: {
                vi: {
                    title: 'Xua tan sương mù tinh thần và lấy lại đà tập trung',
                    usage: 'Thử áp dụng khi sự mệt mỏi về tinh thần khiến bạn khó tập trung và ngay cả những việc đơn giản cũng trở nên khó khăn.'
                },
                en: {
                    title: 'Brain Fog Reset & Mental Momentum',
                    usage: 'Try it when mental fatigue blocks focus and simple tasks feel impossible'
                }
            },
            exam_panic_surge: {
                vi: {
                    title: 'Giảm hoảng loạn trước kỳ thi bằng kỹ thuật thở dài sinh lý',
                    usage: 'Áp dụng khi bạn đột nhiên cảm thấy hoảng loạn ngay trước hoặc trong một bài kiểm tra quan trọng.'
                },
                en: {
                    title: 'Exam panic & physiological sigh reset',
                    usage: 'Try it when sudden panic spikes right before or during a major test'
                }
            },
            email_paralysis: {
                vi: {
                    title: 'Mẫu email xin gia hạn deadline với giảng viên',
                    usage: 'Sử dụng khi bạn đang chịu áp lực lớn và cần xin gia hạn deadline bài tập một cách khẩn cấp.'
                },
                en: {
                    title: 'Professor extension email template',
                    usage: 'Try it when severe stress requires requesting an urgent assignment extension'
                }
            },
            sleep_runaway: {
                vi: {
                    title: 'Thư giãn khi những suy nghĩ cứ tiếp diễn vào ban đêm',
                    usage: 'Thử áp dụng khi những lo lắng về học tập khiến bạn trằn trọc và không thể ngủ dù đã qua 2 giờ sáng.'
                },
                en: {
                    title: 'Racing night thoughts wind-down',
                    usage: 'Try it when academic worries keep you awake well past 2 AM'
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
            },
            presentation_anxiety: {
                vi: {
                    title: 'Lo lắng khi thuyết trình',
                    usage: 'Cảm giác hồi hộp tột độ, tim đập nhanh hoặc lo sợ trước khi phát biểu trước lớp hoặc thuyết trình.'
                },
                en: {
                    title: 'Presentation anxiety',
                    usage: 'Intense nervousness, racing heartbeat, or dread before speaking in class or giving a presentation.'
                }
            },
            cant_focus: {
                vi: {
                    title: 'Không thể tập trung / khó bắt đầu',
                    usage: 'Nhìn vào màn hình trống rỗng, cảm giác sương mù tinh thần hoặc bị tê liệt khi cố gắng bắt đầu học tập.'
                },
                en: {
                    title: 'Can’t focus / can’t get started',
                    usage: 'Staring at a blank screen, experiencing brain fog, or feeling frozen when trying to begin study tasks.'
                }
            },
            future_uncertainty: {
                vi: {
                    title: 'Mơ hồ về định hướng / tương lai',
                    usage: 'Lo lắng về lựa chọn nghề nghiệp, chọn ngành hoặc cảm thấy mất phương hướng so với bạn bè đồng trang lứa.'
                },
                en: {
                    title: 'Unsure about direction / future',
                    usage: 'Worrying about career choices, major selection, or feeling aimless compared to peers.'
                }
            },
            not_good_enough: {
                vi: {
                    title: 'Cảm giác "mình chưa đủ tốt"',
                    usage: 'Tự nghi ngờ bản thân kéo dài, hội chứng kẻ mạo danh và cảm thấy mọi người xung quanh đều hiểu bài trừ mình.'
                },
                en: {
                    title: 'Feeling "not good enough"',
                    usage: 'Persistent self-doubt, imposter syndrome, and feeling like everyone else understands while you don\'t.'
                }
            },
            expectations_pressure: {
                vi: {
                    title: 'Áp lực từ kỳ vọng của bản thân',
                    usage: 'Chủ nghĩa hoàn hảo, tiêu chuẩn nội tâm khắt khe và nỗi sợ mắc lỗi trong quá trình học tập.'
                },
                en: {
                    title: 'Pressure from expectations of myself',
                    usage: 'Perfectionism, harsh internal standards, and fear of making mistakes in coursework.'
                }
            },
            comparing_others: {
                vi: {
                    title: 'So sánh bản thân với người khác',
                    usage: 'Cảm thấy kém cỏi khi nhìn vào kỳ thực tập, tiến độ học tập hoặc thành tích xã hội của bạn bè.'
                },
                en: {
                    title: 'Comparing myself with other people',
                    usage: 'Feeling inadequate when observing peers’ internships, study pace, or social achievements.'
                }
            },
            too_many_responsibilities: {
                vi: {
                    title: 'Quá nhiều trách nhiệm cùng một lúc',
                    usage: 'Bị quá tải với việc học, công việc làm thêm, câu lạc bộ và các trách nhiệm gia đình diễn ra cùng lúc.'
                },
                en: {
                    title: 'Too many responsibilities at once',
                    usage: 'Overloaded with study, part-time jobs, student clubs, and family commitments simultaneously.'
                }
            },
            relationship_conflict: {
                vi: {
                    title: 'Xung đột với người quan trọng',
                    usage: 'Mâu thuẫn với bạn cùng phòng, người yêu, bạn bè hoặc người thân ảnh hưởng đến khả năng học tập của bạn.'
                },
                en: {
                    title: 'Conflict with someone important',
                    usage: 'Friction with a roommate, partner, friend, or family member impacting your ability to study.'
                }
            },
            loneliness: {
                vi: {
                    title: 'Cô đơn / cảm giác mất kết nối',
                    usage: 'Cảm thấy bị cô lập trong trường học, thiếu cảm giác thuộc về nơi này hoặc không có ai để tâm sự trong những tuần khó khăn.'
                },
                en: {
                    title: 'Loneliness / feeling disconnected',
                    usage: 'Feeling isolated on campus, lacking belonging, or having nobody to confide in during tough weeks.'
                }
            },
            disrupted_routine: {
                vi: {
                    title: 'Lối sống hằng ngày bị xáo trộn kéo dài',
                    usage: 'Lịch ngủ bị đảo lộn, ăn uống thất thường và các thói quen hằng ngày bị xói mòn bởi căng thẳng liên miên.'
                },
                en: {
                    title: 'Daily routine has been disrupted for a while',
                    usage: 'Sleep schedule inverted, meals irregular, and everyday habits eroded by ongoing stress.'
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

    function updateLearnToolbar() {
        const isVi = isViLocale();
        const searchInput = document.getElementById('learn-search-input');
        if (searchInput) searchInput.placeholder = isVi ? 'Tìm kiếm...' : 'Search...';
    }

    function getLearnDisplay(item) {
        const isVi = isViLocale();
        if (window.TempoI18n && typeof window.TempoI18n.t === 'function') {
            const t1 = window.TempoI18n.t(`community.learn.cards.${item.id}.title`, {}, '');
            const t2 = window.TempoI18n.t(`learn.cards.${item.id}.title`, {}, '');
            const locTitle = (t1 && t1 !== 'title' && t1 !== `community.learn.cards.${item.id}.title`) ? t1 :
                             ((t2 && t2 !== 'title' && t2 !== `learn.cards.${item.id}.title`) ? t2 : '');

            const s1 = window.TempoI18n.t(`community.learn.cards.${item.id}.summary`, {}, '');
            const s2 = window.TempoI18n.t(`learn.cards.${item.id}.summary`, {}, '');
            const locSummary = (s1 && s1 !== 'summary' && s1 !== `community.learn.cards.${item.id}.summary`) ? s1 :
                               ((s2 && s2 !== 'summary' && s2 !== `learn.cards.${item.id}.summary`) ? s2 : '');

            if (locTitle) {
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
    }

    function handleReturnNavigation() {
        if (window.TempoCommunity && typeof window.TempoCommunity.closeCommunityModal === 'function') {
            window.TempoCommunity.closeCommunityModal();
        }
        if (window.TempoMode && typeof window.TempoMode.navigateToActiveDashboard === 'function') {
            window.TempoMode.navigateToActiveDashboard();
        } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('today');
        } else {
            window.location.hash = '#today';
        }
    }

    // =========================================================================
    // 4. REFERENCE 1: ANNOUNCEMENT
    // =========================================================================
    function renderAnnouncements() {
        const container = document.getElementById('community-announcements-list');
        const emptyState = document.getElementById('community-announcements-empty');
        if (!container) return;

        if (!Array.isArray(announcements) || announcements.length === 0) {
            container.innerHTML = '';
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }

        if (emptyState) emptyState.classList.add('hidden');

        container.innerHTML = announcements.map(ann => {
            return `
                <div class="bg-[#FFFDFB] border-2 border-[#ECA689] rounded-2xl overflow-hidden shadow-xs grid grid-cols-1 md:grid-cols-12 min-h-[240px]" data-announcement-id="${escapeHtml(ann.id)}">
                    <!-- Left Column: Content -->
                    <div class="md:col-span-5 p-6 sm:p-7 flex flex-col justify-between space-y-3">
                        <div class="space-y-2.5">
                            <h3 class="font-heading text-[19px] sm:text-[21px] font-bold text-[#4A4541] leading-tight">
                                ${escapeHtml(ann.title)}
                            </h3>
                            <p class="text-xs sm:text-[13px] text-[#6E6964] leading-relaxed">
                                ${escapeHtml(ann.summary || '')}
                            </p>
                            <div>
                                <button type="button" 
                                        onclick="window.TempoCommunity.openAnnouncementDetail('${ann.id}')"
                                        class="text-[#DE8662] font-bold text-xs sm:text-[13px] hover:underline inline-flex items-center space-x-1 cursor-pointer">
                                    <span>See more</span>
                                    <span>→</span>
                                </button>
                            </div>
                        </div>

                        ${ann.actionLabel ? `
                            <div class="pt-1">
                                <button type="button" 
                                        onclick="window.TempoCommunity.handleAnnouncementAction('${escapeHtml(ann.actionRoute || '')}')"
                                        class="bg-[#E3B8A3] hover:bg-[#D9A891] text-[#944B27] font-bold px-6 py-2 rounded-2xl shadow-xs transition text-xs sm:text-[13px] cursor-pointer">
                                    ${escapeHtml(ann.actionLabel)}
                                </button>
                            </div>
                        ` : ''}
                    </div>

                    <!-- Right Column: Product Screenshot -->
                    <div class="md:col-span-7 bg-[#F7F5F2] border-t md:border-t-0 md:border-l border-[#ECA689]/40 flex items-center justify-center p-2 sm:p-3 overflow-hidden">
                        <img src="${escapeHtml(ann.coverImage || 'assets/announcement_selfcheck_v21.png')}" 
                             alt="${escapeHtml(ann.title)}" 
                             class="w-full h-full max-h-[260px] object-contain rounded-xl shadow-2xs">
                    </div>
                </div>
            `;
        }).join('');
    }

    function openAnnouncementDetail(id) {
        const ann = announcements.find(a => a.id === id);
        if (!ann) return;

        const modal = document.getElementById('modal-announcement-detail');
        if (!modal) return;

        const titleEl = document.getElementById('announcement-modal-title');
        const metaEl = document.getElementById('announcement-modal-meta');
        const imageEl = document.getElementById('announcement-modal-image');
        const contentEl = document.getElementById('announcement-modal-content');
        const actionBtn = document.getElementById('announcement-modal-action');

        if (titleEl) titleEl.textContent = ann.title;
        if (metaEl) metaEl.textContent = `Published by ${ann.author || 'Tempo Team'} · ${ann.publishedAt || 'Recent'}`;
        if (imageEl) {
            imageEl.src = ann.coverImage || 'assets/announcement_selfcheck_v21.png';
            imageEl.classList.remove('hidden');
        }
        if (contentEl) {
            contentEl.innerHTML = `
                <p class="font-medium text-xs sm:text-[13.5px] text-[#4A4541] leading-relaxed">${escapeHtml(ann.summary || '')}</p>
                <div class="text-xs sm:text-[12.5px] text-[#6E6964] leading-relaxed pt-2 space-y-2">
                    ${escapeHtml(ann.content || '')}
                </div>
            `;
        }
        if (actionBtn) {
            if (ann.actionLabel) {
                actionBtn.textContent = `${ann.actionLabel} ↗`;
                actionBtn.onclick = () => {
                    closeAnnouncementDetail();
                    handleAnnouncementAction(ann.actionRoute);
                };
                actionBtn.classList.remove('hidden');
            } else {
                actionBtn.classList.add('hidden');
            }
        }

        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    function closeAnnouncementDetail() {
        const modal = document.getElementById('modal-announcement-detail');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    function handleAnnouncementAction(route) {
        if (!route) return;
        if (route === 'stress-check' || route === 'strack') {
            if (window.TempoMode && typeof window.TempoMode.showStressCheckScreen === 'function') {
                window.TempoMode.showStressCheckScreen();
            } else if (window.TempoApp) {
                window.TempoApp.navigateTo('stress-check');
            }
        } else if (route === 'recovery-mode') {
            if (window.TempoMode && typeof window.TempoMode.navigateToActiveDashboard === 'function') {
                window.TempoMode.navigateToActiveDashboard();
            } else if (window.TempoApp) {
                window.TempoApp.navigateTo('recovery-mode');
            }
        } else if (window.TempoApp) {
            window.TempoApp.navigateTo(route);
        }
    }

    function openNewAnnouncementModal() {
        if (!isUserAdmin()) {
            if (window.TempoApp) window.TempoApp.showToast("Admin access required to publish announcements.");
            return;
        }
        const modal = document.getElementById('modal-announcement-create');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
        }
    }

    function closeNewAnnouncementModal() {
        const modal = document.getElementById('modal-announcement-create');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    function handleCreateAnnouncementSubmit(e) {
        if (e) e.preventDefault();
        const titleInput = document.getElementById('input-announcement-title');
        const summaryInput = document.getElementById('input-announcement-summary');
        const contentInput = document.getElementById('input-announcement-content');
        const imageInput = document.getElementById('input-announcement-image');
        const actionLabelInput = document.getElementById('input-announcement-action-label');
        const actionRouteSelect = document.getElementById('select-announcement-action-route');

        const title = titleInput?.value?.trim();
        const summary = summaryInput?.value?.trim();
        if (!title || !summary) return;

        const newAnn = {
            id: 'ann-' + Date.now(),
            title,
            summary,
            content: contentInput?.value?.trim() || summary,
            coverImage: imageInput?.value?.trim() || 'assets/announcement_selfcheck_v21.png',
            publishedAt: 'Today',
            author: 'Tempo Product Team',
            actionLabel: actionLabelInput?.value?.trim() || '',
            actionRoute: actionRouteSelect?.value || ''
        };

        announcements.unshift(newAnn);
        saveAnnouncements();
        renderAnnouncements();
        closeNewAnnouncementModal();

        if (titleInput) titleInput.value = '';
        if (summaryInput) summaryInput.value = '';
        if (contentInput) contentInput.value = '';
        if (imageInput) imageInput.value = '';
    }

    // =========================================================================
    // 5. REFERENCE 2: TIPS (SOLVE)
    // =========================================================================
    function renderTips() {
        const container = document.getElementById('tips-cards-grid');
        const emptyState = document.getElementById('tips-empty-state');
        if (!container) return;

        updateTipsToolbar();

        const isVi = isViLocale();
        const usageLabel = isVi ? 'Cách sử dụng:' : 'Usage:';
        const seeMoreText = isVi ? 'Xem thêm' : 'See more';

        let filtered = [...tips];

        // Also merge situations from TempoLearnSolve if not present (Preserve full 19-card dataset)
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
    }

    function handleTipsSearch(query) {
        currentTipsSearch = (query || '').trim();
        renderTips();
    }

    function clearTipsSearch() {
        currentTipsSearch = '';
        const input = document.getElementById('tips-search-input');
        if (input) input.value = '';
        renderTips();
    }

    function filterTipsCategory(cat) {
        renderTips();
    }

    // =========================================================================
    // 6. REFERENCE 3: LEARN
    // =========================================================================
    function renderLearn() {
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
    }

    function openLearnDetail(id) {
        if (window.TempoLearnSolve && typeof window.TempoLearnSolve.openModal === 'function') {
            window.TempoLearnSolve.openModal(id);
        }
    }

    function handleLearnSearch(query) {
        currentLearnSearch = (query || '').trim();
        renderLearn();
    }

    function clearLearnSearch() {
        currentLearnSearch = '';
        const input = document.getElementById('learn-search-input');
        if (input) input.value = '';
        renderLearn();
    }

    // =========================================================================
    // 7. REFERENCE 4: POSTS (CANONICAL DESTINATION CONTROLLER)
    // =========================================================================

    /**
     * Requirement 5: Navigates to the canonical main Posts newsfeed from any nested view.
     * Resets post filters, search queries, active detail states, and scrolls to top of feed.
     */
    function navigateToPostsFeed() {
        // 1. Reset all filter flags
        isFilterMyPosts = false;
        isFilterBookmarks = false;
        currentPostsSearch = '';

        // 2. Clear search input if present
        const searchInput = document.getElementById('posts-search-input');
        if (searchInput) searchInput.value = '';

        // 3. Close any open post creation modal
        closeCreatePostModal();

        // 4. Close any detail modal if open
        const postModal = document.getElementById('modal-community-posts');
        if (postModal && !postModal.classList.contains('hidden')) {
            closeCommunityModal();
        }

        // 5. Select posts tab (updates sidebar styling, panels visibility, hash to #community?tab=posts)
        selectTab('posts', true);

        // 6. Force clean re-render of canonical feed
        renderCommunityPosts();

        // 7. Smoothly focus/scroll feed container
        const feedContainer = document.getElementById('community-panel-posts');
        if (feedContainer) {
            feedContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    function renderCommunityPosts() {
        const container = document.getElementById('community-feed-posts-list');
        const emptyState = document.getElementById('community-posts-empty');
        if (!container) return;

        let filtered = [...posts];

        if (isFilterBookmarks) {
            filtered = filtered.filter(p => p.isBookmarked);
        }
        if (isFilterMyPosts) {
            const profile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
            const myName = profile?.full_name || 'Innie';
            filtered = filtered.filter(p => p.authorName === myName || p.authorName === 'FPT Bá khí');
        }
        if (currentPostsSearch) {
            const q = currentPostsSearch.toLowerCase();
            filtered = filtered.filter(p => (p.content || '').toLowerCase().includes(q) || (p.authorName || '').toLowerCase().includes(q));
        }

        if (filtered.length === 0) {
            container.innerHTML = '';
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }

        if (emptyState) emptyState.classList.add('hidden');

        container.innerHTML = filtered.map(post => {
            if (post.layout === 'two-column') {
                return renderTwoColumnPostHTML(post);
            } else {
                return renderFullWidthPostHTML(post);
            }
        }).join('');
    }

    function renderTwoColumnPostHTML(post) {
        const tagsHTML = (post.tags || []).map(t => `
            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${t.bg} ${t.text}">
                ${escapeHtml(t.label)}
            </span>
        `).join(' ');

        const commentsCount = (post.id === 'post-1') ? 5 : (post.id === 'post-2' ? 20 : ((typeof post.commentsCount === 'number' && post.commentsCount > 0) ? post.commentsCount : (Array.isArray(post.comments) ? post.comments.length : 0)));

        return `
            <div class="bg-white border border-[#4A4541] rounded-3xl overflow-hidden shadow-xs grid grid-cols-1 md:grid-cols-12" data-post-id="${post.id}">
                <!-- Left Column: Post Content & Actions -->
                <div class="md:col-span-7 p-5 sm:p-6 border-b md:border-b-0 md:border-r border-[#4A4541]/30 flex flex-col justify-between space-y-3">
                    <!-- Header -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2.5">
                            <img src="${escapeHtml(post.avatar)}" alt="${escapeHtml(post.authorName)}" class="w-8 h-8 rounded-full object-cover">
                            <div>
                                <h4 class="text-[13px] font-bold text-[#202124]">${escapeHtml(post.authorName)}</h4>
                                <span class="text-[10px] text-[#8E8A85] italic">${escapeHtml(getPostTimeAgoDisplay(post.timeAgo))}</span>
                            </div>
                        </div>

                        <div class="flex items-center space-x-2">
                            ${tagsHTML}
                            <!-- Save / Bookmark Action Symbol (Exact Asset) -->
                            <button type="button" 
                                    onclick="window.TempoCommunity.toggleBookmark('${post.id}')" 
                                    class="p-1.5 rounded-full transition cursor-pointer flex items-center justify-center ${post.isBookmarked ? 'bg-[#FCEFE8] border border-[#DE8662]/70 text-[#DE8662]' : 'hover:bg-[#FAF8F5] text-[#5A5550] border border-transparent'}"
                                    aria-label="${post.isBookmarked ? 'Remove bookmark' : 'Bookmark post'}"
                                    aria-pressed="${post.isBookmarked ? 'true' : 'false'}"
                                    title="${post.isBookmarked ? 'Saved to bookmarks' : 'Save post'}">
                                <img src="assets/bookmark_action_symbol.png" 
                                     alt="Bookmark" 
                                     class="w-3.5 h-3.5 object-contain ${post.isBookmarked ? 'filter brightness-95' : 'opacity-70 hover:opacity-100'}">
                            </button>
                        </div>
                    </div>

                    <!-- Post Body -->
                    <div class="space-y-1.5 py-0.5">
                        <p class="text-xs sm:text-[12.5px] text-[#202124] leading-relaxed whitespace-pre-line">
                            ${escapeHtml(post.content)}
                        </p>
                    </div>

                    <!-- Actions Row (Like, Comment, Direct Message to Author) -->
                    <div class="pt-1.5 flex items-center space-x-5 text-[#4A4541] text-xs font-medium">
                        <!-- Like Action -->
                        <button type="button" onclick="window.TempoCommunity.toggleLike('${post.id}')" 
                                class="flex items-center space-x-1 hover:text-[#DE8662] transition cursor-pointer ${post.isLiked ? 'text-[#DE8662] font-bold' : ''}"
                                aria-label="Like post (${post.likes || 0})"
                                title="${post.isLiked ? 'Unlike' : 'Like'}">
                            <span class="text-sm">${post.isLiked ? '♥' : '♡'}</span>
                            <span class="text-xs">${post.likes || 0}</span>
                        </button>

                        <!-- Comment Action Symbol (Exact Asset) -->
                        <button type="button" onclick="window.TempoCommunity.focusCommentInput('${post.id}')" 
                                class="flex items-center space-x-1.5 hover:text-[#DE8662] transition cursor-pointer text-[#4A4541] group"
                                aria-label="${isViLocale() ? 'Bình luận' : 'Comments'} (${commentsCount})" 
                                title="View or add comments">
                            <img src="assets/comment_action_symbol.png" alt="Comments" class="w-3.5 h-3.5 object-contain group-hover:scale-105 transition-transform">
                            <span class="text-xs font-semibold text-[#5A5550]">${commentsCount}</span>
                        </button>

                        <!-- Direct Message to Post Author Symbol (Exact Asset) -->
                        <button type="button" onclick="window.TempoCommunity.openDirectMessageToAuthor('${post.id}')" 
                                class="flex items-center space-x-1 hover:text-[#DE8662] transition cursor-pointer text-[#4A4541] group" 
                                aria-label="Direct message ${escapeHtml(post.authorName)}" 
                                title="Direct message ${escapeHtml(post.authorName)}">
                            <img src="assets/message_action_symbol.png" alt="Direct message" class="w-3.5 h-3.5 object-contain group-hover:scale-105 transition-transform">
                        </button>
                    </div>
                </div>

                <!-- Right Column: Comments & Replies (Reference 4) -->
                <div class="md:col-span-5 p-4 sm:p-5 bg-[#FFFDFB] flex flex-col justify-between space-y-3">
                    <div class="space-y-3 max-h-60 overflow-y-auto pr-1">
                        ${(post.comments || []).map(c => `
                            <div class="${c.isSubReply ? 'pl-4 sm:pl-5' : ''} space-y-1">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center space-x-1.5">
                                        <img src="${escapeHtml(c.avatar || 'assets/tempo-logo.png')}" alt="${escapeHtml(c.author)}" class="w-5 h-5 rounded-full object-cover">
                                        <span class="text-[11px] font-bold text-[#202124]">${escapeHtml(c.author)}</span>
                                        <span class="text-[9.5px] text-[#8E8A85]">${escapeHtml(getPostTimeAgoDisplay(c.time || ''))}</span>
                                    </div>
                                    <button type="button" class="text-xs text-stone-400 hover:text-[#DE8662]">♡</button>
                                </div>
                                <p class="text-[11px] text-[#4A4541] leading-relaxed pl-6.5">
                                    ${escapeHtml(c.text)}
                                </p>
                            </div>
                        `).join('')}
                    </div>

                    <!-- Add Comment input -->
                    <form onsubmit="window.TempoCommunity.handleInlineCommentSubmit(event, '${post.id}')" class="flex items-center space-x-1.5 pt-2 border-t border-[#EAE4DF]">
                        <input type="text" id="input-comment-${post.id}" 
                               placeholder="${isViLocale() ? 'Trả lời...' : 'Reply...'}" 
                               class="flex-1 px-3 py-1.5 text-xs bg-[#FAF8F5] border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#DE8662]">
                        <button type="submit" class="bg-[#DFB59F] hover:bg-[#D4A38A] text-white px-3 py-1.5 rounded-xl text-xs font-bold shrink-0 transition">
                            ${isViLocale() ? 'Gửi' : 'Post'}
                        </button>
                    </form>
                </div>
            </div>
        `;
    }

    function renderFullWidthPostHTML(post) {
        const tagsHTML = (post.tags || []).map(t => `
            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${t.bg} ${t.text}">
                ${escapeHtml(t.label)}
            </span>
        `).join(' ');

        const commentsCount = (post.id === 'post-1') ? 5 : (post.id === 'post-2' ? 20 : ((typeof post.commentsCount === 'number' && post.commentsCount > 0) ? post.commentsCount : (Array.isArray(post.comments) ? post.comments.length : 0)));
        const isCommentsExpanded = expandedFullWidthComments.has(post.id);

        return `
            <div class="bg-white border border-[#4A4541] rounded-3xl p-5 sm:p-6 space-y-3 shadow-xs" data-post-id="${post.id}">
                <!-- Header -->
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2.5">
                        <img src="${escapeHtml(post.avatar)}" alt="${escapeHtml(post.authorName)}" class="w-8 h-8 rounded-full object-cover">
                        <div>
                            <h4 class="text-[13px] font-bold text-[#202124]">${escapeHtml(post.authorName)}</h4>
                            <span class="text-[10px] text-[#8E8A85]">${escapeHtml(getPostTimeAgoDisplay(post.timeAgo))}</span>
                        </div>
                    </div>

                    <div class="flex items-center space-x-2">
                        ${tagsHTML}
                        <!-- Save / Bookmark Action Symbol (Exact Asset) -->
                        <button type="button" 
                                onclick="window.TempoCommunity.toggleBookmark('${post.id}')" 
                                class="p-1.5 rounded-full transition cursor-pointer flex items-center justify-center ${post.isBookmarked ? 'bg-[#FCEFE8] border border-[#DE8662]/70 text-[#DE8662]' : 'hover:bg-[#FAF8F5] text-[#5A5550] border border-transparent'}"
                                aria-label="${post.isBookmarked ? 'Remove bookmark' : 'Bookmark post'}"
                                aria-pressed="${post.isBookmarked ? 'true' : 'false'}"
                                title="${post.isBookmarked ? 'Saved to bookmarks' : 'Save post'}">
                            <img src="assets/bookmark_action_symbol.png" 
                                 alt="Bookmark" 
                                 class="w-3.5 h-3.5 object-contain ${post.isBookmarked ? 'filter brightness-95' : 'opacity-70 hover:opacity-100'}">
                        </button>
                    </div>
                </div>

                <!-- Content -->
                <div class="space-y-2.5">
                    <p class="text-xs sm:text-[12.5px] text-[#202124] leading-relaxed">
                        ${escapeHtml(post.content)}
                    </p>

                    ${post.thumbnails && post.thumbnails.length > 0 ? `
                        <div class="grid grid-cols-4 gap-2 pt-1">
                            ${post.thumbnails.map(img => `
                                <div class="aspect-4/3 rounded-xl overflow-hidden bg-stone-100 border border-stone-200">
                                    <img src="${escapeHtml(img)}" alt="Attachment" class="w-full h-full object-cover">
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>

                <!-- Actions Row (Like, Comment, Direct Message to Author) -->
                <div class="pt-2 flex items-center space-x-5 text-[#4A4541] text-xs font-medium border-t border-[#EAE4DF]/60">
                    <!-- Like Action -->
                    <button type="button" onclick="window.TempoCommunity.toggleLike('${post.id}')" 
                            class="flex items-center space-x-1 hover:text-[#DE8662] transition cursor-pointer ${post.isLiked ? 'text-[#DE8662] font-bold' : ''}"
                            aria-label="Like post (${post.likes || 0})"
                            title="${post.isLiked ? 'Unlike' : 'Like'}">
                        <span class="text-sm">${post.isLiked ? '♥' : '♡'}</span>
                        <span class="text-xs">${post.likes || 0}</span>
                    </button>

                    <!-- Comment Action Symbol (Exact Asset) -->
                    <button type="button" onclick="window.TempoCommunity.toggleFullWidthComments('${post.id}')" 
                            class="flex items-center space-x-1.5 hover:text-[#DE8662] transition cursor-pointer text-[#4A4541] group"
                            aria-label="${isViLocale() ? 'Bình luận' : 'Comments'} (${commentsCount})" 
                            title="View or add comments">
                        <img src="assets/comment_action_symbol.png" alt="Comments" class="w-3.5 h-3.5 object-contain group-hover:scale-105 transition-transform">
                        <span class="text-xs font-semibold text-[#5A5550]">${commentsCount}</span>
                    </button>

                    <!-- Direct Message to Post Author Symbol (Exact Asset) -->
                    <button type="button" onclick="window.TempoCommunity.openDirectMessageToAuthor('${post.id}')" 
                            class="flex items-center space-x-1 hover:text-[#DE8662] transition cursor-pointer text-[#4A4541] group" 
                            aria-label="Direct message ${escapeHtml(post.authorName)}" 
                            title="Direct message ${escapeHtml(post.authorName)}">
                        <img src="assets/message_action_symbol.png" alt="Direct message" class="w-3.5 h-3.5 object-contain group-hover:scale-105 transition-transform">
                    </button>
                </div>

                <!-- Expandable Comments Drawer for Full-Width Posts -->
                ${isCommentsExpanded ? `
                    <div id="fullwidth-comments-${post.id}" class="pt-3 border-t border-[#EAE4DF] space-y-3 bg-[#FFFDFB] -mx-5 -mb-5 sm:-mx-6 sm:-mb-6 p-4 sm:p-5 rounded-b-3xl">
                        <div class="flex items-center justify-between">
                            <h5 class="text-xs font-bold text-[#4A4541]">${isViLocale() ? 'Bình luận' : 'Comments'} (${commentsCount})</h5>
                            <button type="button" onclick="window.TempoCommunity.toggleFullWidthComments('${post.id}')" class="text-xs text-[#8E8A85] hover:text-[#202124]">✕ Close</button>
                        </div>
                        <div class="space-y-2.5 max-h-60 overflow-y-auto pr-1">
                            ${(post.comments && post.comments.length > 0) ? post.comments.map(c => `
                                <div class="${c.isSubReply ? 'pl-4' : ''} space-y-1">
                                    <div class="flex items-center space-x-1.5">
                                        <img src="${escapeHtml(c.avatar || 'assets/tempo-logo.png')}" alt="${escapeHtml(c.author)}" class="w-5 h-5 rounded-full object-cover">
                                        <span class="text-[11px] font-bold text-[#202124]">${escapeHtml(c.author)}</span>
                                        <span class="text-[9.5px] text-[#8E8A85]">${escapeHtml(getPostTimeAgoDisplay(c.time || ''))}</span>
                                    </div>
                                    <p class="text-[11px] text-[#4A4541] leading-relaxed pl-6.5">
                                        ${escapeHtml(c.text)}
                                    </p>
                                </div>
                            `).join('') : `
                                <p class="text-[11px] text-[#8E8A85] italic py-1">No comments yet. Start the conversation!</p>
                            `}
                        </div>
                        <!-- Add comment form -->
                        <form onsubmit="window.TempoCommunity.handleInlineCommentSubmit(event, '${post.id}')" class="flex items-center space-x-1.5 pt-2 border-t border-[#EAE4DF]">
                            <input type="text" id="input-comment-${post.id}" 
                                   placeholder="${isViLocale() ? 'Trả lời...' : 'Reply...'}" 
                                   class="flex-1 px-3 py-1.5 text-xs bg-[#FAF8F5] border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#DE8662]">
                            <button type="submit" class="bg-[#DFB59F] hover:bg-[#D4A38A] text-white px-3 py-1.5 rounded-xl text-xs font-bold shrink-0 transition">
                                ${isViLocale() ? 'Gửi' : 'Post'}
                            </button>
                        </form>
                    </div>
                ` : ''}
            </div>
        `;
    }

    function toggleLike(postId) {
        const post = posts.find(p => p.id === postId);
        if (!post) return;
        post.isLiked = !post.isLiked;
        post.likes = (post.likes || 0) + (post.isLiked ? 1 : -1);
        if (post.likes < 0) post.likes = 0;
        savePosts();
        renderCommunityPosts();
        renderHomepagePreview();
        renderUrgentPreview();
        renderRecoveryPreview();
    }

    function toggleBookmark(postId) {
        const post = posts.find(p => p.id === postId);
        if (!post) return;

        const currentUser = window.TempoAuth ? window.TempoAuth.getCurrentUser() : null;
        if (!currentUser) {
            if (window.TempoAuth && typeof window.TempoAuth.openSignInModal === 'function') {
                window.TempoAuth.openSignInModal();
            }
            if (window.TempoApp) {
                window.TempoApp.showToast("Please sign in to save bookmarks.");
            }
            return;
        }

        let userBookmarks = getUserBookmarks();
        const isSaved = userBookmarks.includes(postId);

        if (isSaved) {
            userBookmarks = userBookmarks.filter(id => id !== postId);
            post.isBookmarked = false;
        } else {
            userBookmarks.push(postId);
            post.isBookmarked = true;
        }

        // Deduplicate and persist
        userBookmarks = Array.from(new Set(userBookmarks));
        saveUserBookmarks(userBookmarks);
        savePosts();
        renderCommunityPosts();
        renderHomepagePreview();
        renderUrgentPreview();
        renderRecoveryPreview();

        if (window.TempoApp) {
            window.TempoApp.showToast(post.isBookmarked ? "Post saved to your bookmarks." : "Bookmark removed.");
        }
    }

    function filterMyPosts() {
        isFilterMyPosts = !isFilterMyPosts;
        isFilterBookmarks = false;
        renderCommunityPosts();
    }

    function filterBookmarkedPosts() {
        isFilterBookmarks = !isFilterBookmarks;
        isFilterMyPosts = false;
        renderCommunityPosts();
    }

    function handlePostsSearch(query) {
        currentPostsSearch = (query || '').trim();
        renderCommunityPosts();
    }

    function toggleFullWidthComments(postId) {
        if (expandedFullWidthComments.has(postId)) {
            expandedFullWidthComments.delete(postId);
            renderCommunityPosts();
        } else {
            expandedFullWidthComments.add(postId);
            renderCommunityPosts();
            setTimeout(() => {
                const input = document.getElementById(`input-comment-${postId}`);
                if (input) {
                    input.focus();
                    input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }, 50);
        }
    }

    function focusCommentInput(postId) {
        const post = posts.find(p => p.id === postId);
        if (post && post.layout !== 'two-column') {
            if (!expandedFullWidthComments.has(postId)) {
                expandedFullWidthComments.add(postId);
                renderCommunityPosts();
            }
        }
        setTimeout(() => {
            const input = document.getElementById(`input-comment-${postId}`);
            if (input) {
                input.focus();
                input.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 50);
    }

    function handleInlineCommentSubmit(e, postId) {
        if (e) e.preventDefault();
        const post = posts.find(p => p.id === postId);
        if (!post) return;

        const input = document.getElementById(`input-comment-${postId}`);
        const text = input?.value?.trim();
        if (!text) return;

        const profile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
        const myName = profile?.full_name || 'tutamduongtinh';

        if (!post.comments) post.comments = [];
        post.comments.push({
            id: 'c-' + Date.now(),
            author: myName,
            avatar: profile?.avatar_url || 'assets/practice-breathing-mascot.png',
            time: 'Just now',
            text
        });
        post.commentsCount = post.comments.length;

        savePosts();
        input.value = '';
        renderCommunityPosts();
        if (window.TempoApp) window.TempoApp.showToast("Comment added");
    }

    /**
     * Requirement 3: Send a Message Symbol — Direct Message to Post Author
     * Resolves recipient using post author's user ID / name.
     * Reuses existing conversation or starts a new conversation without page reload.
     * Does NOT auto-send messages or create duplicate conversations on repeated clicks.
     */
    function openDirectMessageToAuthor(postId) {
        const post = posts.find(p => p.id === postId);
        if (!post) return;

        // 1. Edge Case: Anonymous post author
        if (post.authorName === 'Anonymous Student' || post.authorHandle === '@anonymous') {
            if (window.TempoApp) {
                window.TempoApp.showToast("Cannot direct message an anonymous post author.");
            }
            return;
        }

        // 2. Edge Case: Unauthenticated user
        const currentUser = window.TempoAuth ? window.TempoAuth.getCurrentUser() : null;
        if (!currentUser) {
            if (window.TempoAuth && typeof window.TempoAuth.openSignInModal === 'function') {
                window.TempoAuth.openSignInModal();
            }
            if (window.TempoApp) {
                window.TempoApp.showToast("Please sign in to message this author.");
            }
            return;
        }

        // 3. Edge Case: Self-messaging
        const currentProfile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
        const currentUserName = currentProfile?.full_name || currentUser.user_metadata?.full_name || currentUser.email || '';
        const currentUserId = currentUser.id;

        const isSelf = (post.authorId && post.authorId === currentUserId) ||
                       (currentUserName && currentUserName.trim().toLowerCase() === post.authorName.trim().toLowerCase());
        if (isSelf) {
            if (window.TempoApp) {
                window.TempoApp.showToast("You cannot direct message yourself.");
            }
            return;
        }

        // 4. Check existing conversation (reuse if already exists, prevent duplicate conversations)
        const targetName = (post.authorName || '').trim().toLowerCase();
        const existingConv = conversations.find(c => {
            if (post.authorId && c.recipientId === post.authorId) return true;
            if (c.name && c.name.trim().toLowerCase() === targetName) return true;
            return false;
        });

        if (existingConv) {
            selectConversation(existingConv.id);
            selectTab('messages', true);
            setTimeout(() => {
                const input = document.getElementById('dm-message-input');
                if (input) input.focus();
            }, 150);
            if (window.TempoApp) {
                window.TempoApp.showToast(`Opened conversation with ${post.authorName}`);
            }
            return;
        }

        // 5. Establish new conversation without separate page reload
        const newConv = {
            id: 'conv-' + Date.now(),
            recipientId: post.authorId || null,
            name: post.authorName,
            avatar: post.avatar || 'assets/tempo-logo.png',
            subtitle: post.authorHandle ? `${post.authorHandle} · Post Author` : 'Community Post Author',
            unreadCount: 0,
            time: 'Just now',
            lastMessage: 'Direct conversation started from post',
            messages: [] // strictly empty without fabricated messages
        };

        conversations.unshift(newConv);
        saveConversations();

        // User-scoped storage persistence
        try {
            localStorage.setItem(`tempo_direct_messages_${currentUserId}`, JSON.stringify(conversations));
        } catch (e) {}

        activeConvId = newConv.id;
        selectTab('messages', true);

        setTimeout(() => {
            const input = document.getElementById('dm-message-input');
            if (input) input.focus();
        }, 150);

        if (window.TempoApp) {
            window.TempoApp.showToast(`Started conversation with ${post.authorName}`);
        }
    }

    function openCreatePostModal() {
        const modal = document.getElementById('modal-create-post');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
            const textarea = document.getElementById('input-modal-post-content');
            if (textarea) textarea.focus();
        }
    }

    function closeCreatePostModal() {
        const modal = document.getElementById('modal-create-post');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    function handleCreateCommunityPost(e) {
        if (e) e.preventDefault();
        const textarea = document.getElementById('input-modal-post-content');
        const tagSelect = document.getElementById('select-modal-post-tag');
        const anonCheckbox = document.getElementById('checkbox-modal-post-anon');

        const content = textarea?.value?.trim();
        if (!content) return;

        const profile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
        const isAnon = anonCheckbox ? anonCheckbox.checked : true;
        const authorName = isAnon ? 'Anonymous Student' : (profile?.full_name || 'Tempo Peer');
        const authorHandle = isAnon ? '@anonymous' : `@${(profile?.full_name || 'peer').toLowerCase().replace(/\s+/g, '_')}`;

        const tagVal = tagSelect?.value || '#mental health';
        const tagObj = {
            label: tagVal,
            bg: tagVal === '#Deadline' ? 'bg-[#FCEFE8]' : 'bg-[#EBF3F5]',
            text: tagVal === '#Deadline' ? 'text-[#DE8662]' : 'text-[#3E707D]'
        };

        const newPost = {
            id: 'post-' + Date.now(),
            authorName,
            authorHandle,
            timeAgo: 'Just now',
            avatar: isAnon ? 'assets/tempo-logo.png' : (profile?.avatar_url || 'assets/tempo-logo.png'),
            content,
            tags: [tagObj],
            likes: 0,
            commentsCount: 0,
            isLiked: false,
            isBookmarked: false,
            layout: 'two-column',
            comments: []
        };

        posts.unshift(newPost);
        savePosts();
        closeCreatePostModal();
        if (textarea) textarea.value = '';

        // Return to newsfeed and render
        navigateToPostsFeed();

        if (window.TempoApp) window.TempoApp.showToast("Post shared to community!");
    }

    // =========================================================================
    // 8. REFERENCE 5: DIRECT MESSAGE & CHAT REQUESTS (DATA-HARDENED & CLEAN EMPTY STATES)
    // =========================================================================

    let dmLoading = false;
    let dmError = null;

    async function renderMessagesView() {
        const guestView = document.getElementById('community-dm-guest-view');
        const authView = document.getElementById('community-dm-auth-view');

        // Check authentication
        const currentUser = window.TempoAuth ? window.TempoAuth.getCurrentUser() : null;
        if (!currentUser) {
            if (guestView) guestView.classList.remove('hidden');
            if (authView) authView.classList.add('hidden');
            return;
        }

        if (guestView) guestView.classList.add('hidden');
        if (authView) authView.classList.remove('hidden');

        updateChatRequestsBadge();
        await loadConversationsFromBackend(currentUser);
    }

    async function loadConversationsFromBackend(currentUser) {
        if (!currentUser) return;
        const userId = currentUser.id || 'anonymous';
        dmLoading = true;
        dmError = null;
        renderConversationsList();
        renderActiveConversation();

        try {
            let loaded = [];
            
            // 1. Inspect Supabase for real support requests/conversations
            if (window.TempoSupabase && typeof window.TempoSupabase.getClient === 'function') {
                try {
                    const client = await window.TempoSupabase.getClient();
                    if (client && userId !== 'anonymous') {
                        const { data, error } = await client
                            .from('support_requests')
                            .select('id, subject, category, status, created_at, updated_at, assigned_volunteer_id, student_id')
                            .or(`student_id.eq.${userId},assigned_volunteer_id.eq.${userId}`)
                            .order('updated_at', { ascending: false });

                        if (error) {
                            // If table is missing or network failure, record error distinctly
                            if (error.code && error.code !== 'PGRST116') {
                                console.warn('[DirectMessage] Supabase response:', error.message);
                            }
                        } else if (Array.isArray(data) && data.length > 0) {
                            loaded = data.map(req => ({
                                id: req.id,
                                name: req.subject || 'Support Session',
                                avatar: 'assets/tempo-logo.png',
                                subtitle: req.category || 'Direct Message',
                                time: 'Recent',
                                lastMessage: `Status: ${req.status}`,
                                unreadCount: 0,
                                messages: []
                            }));
                        }
                    }
                } catch (sbErr) {
                    console.warn('[DirectMessage] Supabase client check:', sbErr);
                }
            }

            // 2. Fetch authenticated user-scoped local conversations (if no Supabase rows)
            if (loaded.length === 0) {
                const userKey = `tempo_direct_messages_${userId}`;
                const saved = localStorage.getItem(userKey);
                if (saved) {
                    try {
                        const parsed = JSON.parse(saved);
                        if (Array.isArray(parsed)) {
                            // Strictly purge any legacy mock IDs
                            loaded = parsed.filter(c => c.id !== 'conv-badminton' && c.id !== 'conv-tempo-admin' && c.id !== 'conv-innie');
                        }
                    } catch (e) {}
                }
            }

            // Update state
            conversations = loaded;
            if (conversations.length > 0) {
                if (!activeConvId || !conversations.some(c => c.id === activeConvId)) {
                    activeConvId = conversations[0].id;
                }
            } else {
                activeConvId = null;
            }
        } catch (err) {
            console.error('[DirectMessage] Fetch error:', err);
            dmError = err.message || 'Failed to load conversations';
        } finally {
            dmLoading = false;
            renderConversationsList();
            renderActiveConversation();
        }
    }

    function renderConversationsList(filterQuery = '') {
        const container = document.getElementById('dm-conversations-list');
        if (!container) return;

        // Loading state
        if (dmLoading) {
            container.innerHTML = `
                <div class="h-44 flex flex-col items-center justify-center p-4 text-center space-y-2 text-[#8E8A85]">
                    <div class="w-5 h-5 border-2 border-[#DE8662] border-t-transparent rounded-full animate-spin"></div>
                    <p class="text-xs font-semibold text-[#5A5550]">Loading conversations...</p>
                </div>
            `;
            return;
        }

        // Error state: Never interpret failed request as empty
        if (dmError) {
            container.innerHTML = `
                <div class="h-44 flex flex-col items-center justify-center p-4 text-center space-y-2 text-[#D92D20]">
                    <span class="text-base">⚠️</span>
                    <p class="text-xs font-bold text-[#D92D20]">Unable to load conversations</p>
                    <p class="text-[10px] text-[#8E8A85] max-w-[190px] leading-tight">${escapeHtml(dmError)}</p>
                    <button type="button" onclick="window.TempoCommunity.retryLoadConversations()" 
                            class="px-3 py-1 bg-stone-100 hover:bg-stone-200 text-[#5A5550] text-[11px] font-bold rounded-lg transition cursor-pointer">
                        Retry
                    </button>
                </div>
            `;
            return;
        }

        let filtered = [...conversations];
        if (filterQuery) {
            const q = filterQuery.toLowerCase();
            filtered = filtered.filter(c => (c.name || '').toLowerCase().includes(q) || (c.lastMessage || '').toLowerCase().includes(q));
        }

        // Clean empty state when authenticated user has no conversations
        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="h-48 flex flex-col items-center justify-center p-4 text-center space-y-2 text-[#8E8A85]">
                    <img src="assets/chat_requests_symbol.png" alt="No conversations" class="w-6 h-6 opacity-40 object-contain mb-0.5">
                    <p class="text-xs font-bold text-[#5A5550]">No conversations yet</p>
                    <p class="text-[10.5px] text-[#8E8A85] leading-relaxed max-w-[190px]">You have not sent or received any messages. New messages and accepted chat requests will appear here.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = filtered.map(c => {
            const isActive = c.id === activeConvId;
            return `
                <div onclick="window.TempoCommunity.selectConversation('${c.id}')"
                     class="p-2.5 rounded-2xl cursor-pointer transition flex items-center space-x-2.5 ${isActive ? 'bg-[#F7ECE1]' : 'hover:bg-[#FAF8F5]'}">
                    <div class="relative shrink-0">
                        <img src="${escapeHtml(c.avatar || 'assets/tempo-logo.png')}" alt="${escapeHtml(c.name)}" class="w-8 h-8 rounded-full object-cover">
                    </div>
                    <div class="flex-1 min-w-0 space-y-0.5">
                        <div class="flex items-center justify-between">
                            <h4 class="text-xs sm:text-[13px] font-bold text-[#202124] truncate">${escapeHtml(c.name)}</h4>
                            <span class="text-[9.5px] text-[#8E8A85] shrink-0">${escapeHtml(c.time || '')}</span>
                        </div>
                        <p class="text-[10.5px] text-[#6E6964] truncate leading-tight">${escapeHtml(c.lastMessage || '')}</p>
                    </div>
                    ${c.unreadCount ? `<span class="w-3.5 h-3.5 rounded-full bg-[#E04B38] text-white text-[9px] font-bold flex items-center justify-center shrink-0">${c.unreadCount}</span>` : ''}
                </div>
            `;
        }).join('');
    }

    function selectConversation(convId) {
        activeConvId = convId;
        const conv = conversations.find(c => c.id === convId);
        if (conv) {
            conv.unreadCount = 0;
            saveConversations();
        }
        renderConversationsList();
        renderActiveConversation();
        mobileToggleConversation(true);
    }

    function renderActiveConversation() {
        const nameEl = document.getElementById('dm-active-name');
        const roleEl = document.getElementById('dm-active-role');
        const avatarEl = document.getElementById('dm-active-avatar');
        const messagesContainer = document.getElementById('dm-messages-container');
        const messageInput = document.getElementById('dm-message-input');
        const sendBtn = document.getElementById('btn-dm-send');

        // Loading state
        if (dmLoading) {
            if (messagesContainer) {
                messagesContainer.innerHTML = `
                    <div class="h-full min-h-[320px] flex flex-col items-center justify-center p-6 text-center space-y-2 text-[#8E8A85]">
                        <div class="w-6 h-6 border-2 border-[#DE8662] border-t-transparent rounded-full animate-spin"></div>
                        <p class="text-xs text-[#8E8A85]">Loading conversation...</p>
                    </div>
                `;
            }
            return;
        }

        // Requirement 2: When user has no conversations or none selected, keep message panel blank
        if (!activeConvId || conversations.length === 0) {
            if (nameEl) nameEl.textContent = 'Direct Messages';
            if (roleEl) roleEl.textContent = 'No active conversation';
            if (avatarEl) avatarEl.src = 'assets/tempo-logo.png';
            if (messagesContainer) {
                messagesContainer.innerHTML = `
                    <div class="h-full min-h-[320px] flex flex-col items-center justify-center p-6 text-center space-y-2.5 text-[#8E8A85]">
                        <img src="assets/chat_requests_symbol.png" alt="No conversation selected" class="w-8 h-8 opacity-40 object-contain">
                        <p class="text-xs sm:text-[13px] font-bold text-[#5A5550]">No conversation selected</p>
                        <p class="text-[11px] text-[#8E8A85] max-w-xs leading-relaxed">Choose a conversation from your list or check Chat Requests to start messaging.</p>
                    </div>
                `;
            }
            if (messageInput) {
                messageInput.disabled = true;
                messageInput.placeholder = 'Select a conversation to message...';
            }
            if (sendBtn) sendBtn.disabled = true;
            return;
        }

        const conv = conversations.find(c => c.id === activeConvId);
        if (!conv) return;

        if (nameEl) nameEl.textContent = conv.name;
        if (roleEl) roleEl.textContent = conv.subtitle || 'Active conversation';
        if (avatarEl) avatarEl.src = conv.avatar || 'assets/tempo-logo.png';

        if (messageInput) {
            messageInput.disabled = false;
            messageInput.placeholder = 'Type a message...';
        }
        if (sendBtn) sendBtn.disabled = false;

        // Requirement 3: If a conversation exists but has no messages, show an empty message area without fabricated message bubbles
        if (messagesContainer) {
            if (!conv.messages || conv.messages.length === 0) {
                messagesContainer.innerHTML = `
                    <div class="h-full min-h-[320px] flex flex-col items-center justify-center p-6 text-center space-y-2 text-[#8E8A85]">
                        <span class="text-2xl">👋</span>
                        <p class="text-xs sm:text-[13px] font-bold text-[#5A5550]">No messages yet</p>
                        <p class="text-[11px] text-[#8E8A85] max-w-xs leading-relaxed">Send a message below to say hello and start the conversation.</p>
                    </div>
                `;
                return;
            }

            messagesContainer.innerHTML = conv.messages.map(m => {
                const isMe = m.sender === 'me';
                if (isMe) {
                    return `
                        <div class="flex flex-col items-end space-y-0.5">
                            <span class="text-[10px] font-bold text-[#202124] pr-10">${escapeHtml(m.senderName || 'tutamduongtinh')}</span>
                            <div class="flex items-end space-x-1.5">
                                <span class="text-[9px] text-[#8E8A85] pb-0.5">${escapeHtml(m.time || '')}</span>
                                <div class="bg-[#CAD8E0] text-[#202124] text-xs p-3 rounded-2xl rounded-tr-xs max-w-md shadow-2xs leading-relaxed">
                                    ${escapeHtml(m.text)}
                                </div>
                                <img src="${escapeHtml(m.avatar || 'assets/practice-breathing-mascot.png')}" alt="Me" class="w-7 h-7 rounded-full object-cover shrink-0">
                            </div>
                        </div>
                    `;
                } else {
                    return `
                        <div class="flex flex-col items-start space-y-0.5">
                            <span class="text-[10px] font-bold text-[#202124] pl-9">${escapeHtml(m.senderName || '')}</span>
                            <div class="flex items-start space-x-1.5">
                                <img src="${escapeHtml(m.avatar || 'assets/tempo-logo.png')}" alt="${escapeHtml(m.senderName || '')}" class="w-7 h-7 rounded-full object-cover shrink-0 mt-0.5">
                                <div class="bg-[#E1EAE3] text-[#202124] text-xs p-3 rounded-2xl rounded-tl-xs max-w-md shadow-2xs leading-relaxed">
                                    ${escapeHtml(m.text)}
                                </div>
                                <span class="text-[9px] text-[#8E8A85] pt-1.5 self-end">${escapeHtml(m.time || '')}</span>
                            </div>
                        </div>
                    `;
                }
            }).join('');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    function handleSendMessage(e) {
        if (e) e.preventDefault();
        const input = document.getElementById('dm-message-input');
        const text = input?.value?.trim();
        if (!text) return;

        const conv = conversations.find(c => c.id === activeConvId);
        if (!conv) return;

        if (!conv.messages) conv.messages = [];
        conv.messages.push({
            id: 'm-' + Date.now(),
            sender: 'me',
            senderName: 'tutamduongtinh',
            avatar: 'assets/practice-breathing-mascot.png',
            text,
            time: 'Just now'
        });
        conv.lastMessage = `Me: ${text}`;
        conv.time = 'Just now';

        saveConversations();
        input.value = '';
        renderActiveConversation();
        renderConversationsList();
    }

    function mobileToggleConversation(showDetail) {
        const listCol = document.getElementById('dm-conversations-column');
        const chatCol = document.getElementById('dm-chat-column');
        if (!listCol || !chatCol) return;

        if (window.innerWidth < 768) {
            if (showDetail) {
                listCol.classList.add('hidden');
                chatCol.classList.remove('hidden');
            } else {
                listCol.classList.remove('hidden');
                chatCol.classList.add('hidden');
            }
        } else {
            listCol.classList.remove('hidden');
            chatCol.classList.remove('hidden');
        }
    }

    function handleDMSearch(query) {
        renderConversationsList((query || '').trim());
    }

    // =========================================================================
    // 9. CHAT REQUESTS INTERACTION (REQUIREMENT 4)
    // =========================================================================

    function openChatRequests() {
        const modal = document.getElementById('modal-chat-requests');
        if (modal) {
            renderChatRequestsList();
            modal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
        }
    }

    function closeChatRequests() {
        const modal = document.getElementById('modal-chat-requests');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    function renderChatRequestsList() {
        const listEl = document.getElementById('chat-requests-list');
        const emptyEl = document.getElementById('chat-requests-empty');
        if (!listEl) return;

        // If no requests, show clean empty state without fake entries
        if (chatRequests.length === 0) {
            listEl.innerHTML = '';
            if (emptyEl) emptyEl.classList.remove('hidden');
            return;
        }

        if (emptyEl) emptyEl.classList.add('hidden');

        listEl.innerHTML = chatRequests.map(req => `
            <div class="p-3 bg-[#FAF8F5] border border-[#EAE4DF] rounded-2xl flex items-center justify-between space-x-3">
                <div class="flex items-center space-x-2.5 min-w-0">
                    <img src="${escapeHtml(req.avatar || 'assets/tempo-logo.png')}" alt="${escapeHtml(req.senderName)}" class="w-8 h-8 rounded-full object-cover shrink-0">
                    <div class="min-w-0">
                        <h4 class="text-xs font-bold text-[#202124] truncate">${escapeHtml(req.senderName)}</h4>
                        <p class="text-[10px] text-[#8E8A85] truncate">${escapeHtml(req.role || 'Peer Student')}</p>
                        <p class="text-[11px] text-[#4A4541] truncate pt-0.5">"${escapeHtml(req.message || 'Hi! Can we connect?')}"</p>
                    </div>
                </div>
                <div class="flex items-center space-x-1.5 shrink-0">
                    <button type="button" onclick="window.TempoCommunity.acceptChatRequest('${req.id}')" 
                            class="bg-[#DE8662] hover:bg-[#C9724F] text-white text-[11px] font-bold px-3 py-1 rounded-xl transition shadow-2xs cursor-pointer">
                        Accept
                    </button>
                    <button type="button" onclick="window.TempoCommunity.declineChatRequest('${req.id}')" 
                            class="bg-stone-200 hover:bg-stone-300 text-[#5A5550] text-[11px] font-semibold px-2.5 py-1 rounded-xl transition cursor-pointer">
                        Decline
                    </button>
                </div>
            </div>
        `).join('');
    }

    function acceptChatRequest(requestId) {
        const idx = chatRequests.findIndex(r => r.id === requestId);
        if (idx === -1) return;
        const req = chatRequests[idx];
        chatRequests.splice(idx, 1);
        saveChatRequests();

        // Establish conversation from request
        const newConv = {
            id: 'conv-' + Date.now(),
            name: req.senderName,
            avatar: req.avatar || 'assets/tempo-logo.png',
            subtitle: req.role || 'Peer Conversation',
            unreadCount: 0,
            time: 'Just now',
            lastMessage: req.message || 'Conversation started',
            messages: req.message ? [
                {
                    id: 'm-' + Date.now(),
                    sender: 'them',
                    senderName: req.senderName,
                    avatar: req.avatar || 'assets/tempo-logo.png',
                    text: req.message,
                    time: 'Just now'
                }
            ] : []
        };

        conversations.unshift(newConv);
        saveConversations();
        activeConvId = newConv.id;

        closeChatRequests();
        renderConversationsList();
        renderActiveConversation();

        if (window.TempoApp) window.TempoApp.showToast(`Chat request from ${req.senderName} accepted.`);
    }

    function declineChatRequest(requestId) {
        const idx = chatRequests.findIndex(r => r.id === requestId);
        if (idx === -1) return;
        const req = chatRequests[idx];
        chatRequests.splice(idx, 1);
        saveChatRequests();
        renderChatRequestsList();
        if (window.TempoApp) window.TempoApp.showToast(`Chat request declined.`);
    }

    // Helper for testing or adding real incoming requests
    function addChatRequest(req) {
        if (!req || !req.id) return;
        if (!chatRequests.some(r => r.id === req.id)) {
            chatRequests.push(req);
            saveChatRequests();
            renderChatRequestsList();
        }
    }

    // =========================================================================
    // 10. PREVIEWS & LEGACY COMPATIBILITY
    // =========================================================================
    function renderHomepagePreview() {
        const container = document.getElementById('homepage-community-posts-list');
        if (!container) return;
        const previewPosts = posts.slice(0, 2);
        if (previewPosts.length === 0) {
            container.innerHTML = `
                <div class="h-48 flex flex-col items-center justify-center text-center p-6 space-y-2 text-[#8E8A85]">
                    <img src="assets/comment_action_symbol.png" alt="No posts" class="w-6 h-6 opacity-40 object-contain mb-0.5">
                    <p class="text-xs font-bold text-[#5A5550]">${isViLocale() ? 'Chưa có bài viết cộng đồng nào' : 'No community posts yet'}</p>
                    <p class="text-[10.5px] text-[#8E8A85] leading-relaxed">${isViLocale() ? 'Hãy là người đầu tiên chia sẻ với bạn bè trong cộng đồng.' : 'Be the first to share with your peers in the community.'}</p>
                </div>
            `;
            return;
        }

        container.innerHTML = previewPosts.map(post => {
            const tagsHTML = (post.tags || []).map(t => `
                <span class="px-3 py-0.5 rounded-full text-xs font-semibold ${t.bg} ${t.text}">
                    ${escapeHtml(t.label)}
                </span>
            `).join(' ');

            const commentsCount = (post.comments && post.comments.length > 0) ? post.comments.length : (post.commentsCount || 0);

            return `
                <div onclick="window.TempoApp.navigateTo('community'); if(window.TempoCommunity) { window.TempoCommunity.selectTab('posts'); setTimeout(() => { const el = document.querySelector('[data-post-id=\'${post.id}\']'); if(el) el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 150); }"
                     class="bg-[#F6F0EB] border border-[#4A4541] rounded-2xl sm:rounded-3xl p-4 sm:p-[18px] space-y-2.5 shadow-xs hover:border-[#DE8662] transition cursor-pointer group"
                     title="Open post by ${escapeHtml(post.authorName)}">
                    <!-- Header -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2.5">
                            <img src="${escapeHtml(post.avatar)}" alt="${escapeHtml(post.authorName)}" class="w-9 h-9 rounded-full object-cover">
                            <div>
                                <h4 class="text-sm font-bold text-[#202124] leading-tight">${escapeHtml(post.authorName)}</h4>
                                <span class="text-xs text-[#8E8A85]">${escapeHtml(getPostTimeAgoDisplay(post.timeAgo || 'Recent'))}</span>
                            </div>
                        </div>
                        <div class="flex items-center space-x-2">
                            ${tagsHTML}
                            <div class="p-1 text-[#4A4541] hover:text-[#DE8662]">
                                <img src="assets/bookmark_action_symbol.png" alt="Bookmark" class="w-4 h-4 object-contain opacity-70">
                            </div>
                        </div>
                    </div>

                    <!-- Content -->
                    <p class="text-xs sm:text-[13px] text-[#202124] leading-relaxed">
                        ${escapeHtml(post.content)}
                    </p>

                    <!-- Thumbnails if present -->
                    ${(post.thumbnails && post.thumbnails.length > 0) ? `
                        <div class="grid grid-cols-4 gap-2 pt-1">
                            ${post.thumbnails.slice(0, 4).map(img => `
                                <div class="aspect-4/3 rounded-xl overflow-hidden bg-stone-100 border border-stone-200">
                                    <img src="${escapeHtml(img)}" alt="Attachment" class="w-full h-full object-cover">
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}

                    <!-- Action stats row matching Reference Screenshot -->
                    <div class="flex items-center space-x-5 text-[#4A4541] text-xs pt-1">
                        <span class="flex items-center space-x-1.5">
                            <span class="text-sm">♡</span>
                            <span>${post.likes || 0}</span>
                        </span>
                        <span class="flex items-center space-x-1.5">
                            <img src="assets/comment_action_symbol.png" alt="Comments" class="w-3.5 h-3.5 object-contain">
                            <span>${commentsCount}</span>
                        </span>
                        <span class="flex items-center space-x-1.5">
                            <img src="assets/message_action_symbol.png" alt="Share" class="w-3.5 h-3.5 object-contain">
                        </span>
                    </div>
                </div>
            `;
        }).join('');
    }

    function getDistinctPosts(postList, maxCount = 2) {
        const list = Array.isArray(postList) ? postList : posts;
        const seenIds = new Set();
        const seenContent = new Set();
        const result = [];

        for (const p of list) {
            if (!p || typeof p !== 'object') continue;
            const id = p.id;
            const normContent = (p.content || '').toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim();
            const normAuthor = (p.authorName || '').trim().toLowerCase();
            const contentKey = `${normAuthor}:::${normContent}`;

            if (id && seenIds.has(id)) continue;
            if (contentKey && seenContent.has(contentKey)) continue;

            if (id) seenIds.add(id);
            if (contentKey) seenContent.add(contentKey);

            result.push(p);
            if (result.length >= maxCount) break;
        }
        return result;
    }

    function getPostTimeAgoDisplay(timeVal) {
        if (window.TempoI18n && typeof window.TempoI18n.formatTimeAgo === 'function') {
            return window.TempoI18n.formatTimeAgo(timeVal);
        }
        return timeVal || 'Recent';
    }

    function renderPreviewPostCardHTML(post) {
        if (!post) return '';
        const tagsHTML = (post.tags || []).map(t => `
            <span class="px-3 py-0.5 rounded-full text-xs font-semibold ${t.bg || 'bg-[#E8F0F5]'} ${t.text || 'text-[#4A728A]'}">
                ${escapeHtml(t.label)}
            </span>
        `).join(' ');

        const commentsCount = (post.comments && post.comments.length > 0) ? post.comments.length : (post.commentsCount || 0);

        let thumbnailsHTML = '';
        if (Array.isArray(post.thumbnails) && post.thumbnails.length > 0) {
            thumbnailsHTML = `
                <div class="grid grid-cols-4 gap-2 pt-1">
                    ${post.thumbnails.slice(0, 4).map(img => `
                        <div class="aspect-4/3 rounded-xl overflow-hidden bg-stone-100 border border-stone-200">
                            <img src="${escapeHtml(img)}" alt="Attachment" class="w-full h-full object-cover">
                        </div>
                    `).join('')}
                </div>
            `;
        }

        let commentPreviewHTML = '';
        if (post.showCommentPreview && Array.isArray(post.comments) && post.comments.length > 0) {
            commentPreviewHTML = `
                <div class="pt-2 border-t border-[#4A4541]/15 space-y-1.5">
                    ${post.comments.slice(0, 2).map((c, idx) => `
                        <div class="flex items-start space-x-2 ${idx > 0 ? 'pl-4' : ''} text-xs leading-snug">
                            <div class="w-4 h-4 rounded-full bg-[#E5B59C] shrink-0 flex items-center justify-center text-[8px] font-bold text-white mt-0.5">
                                ${escapeHtml((c.author || 'P')[0])}
                            </div>
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center space-x-1.5">
                                    <span class="font-bold text-[#202124] text-[11px]">${escapeHtml(c.author || 'Peer')}</span>
                                    <span class="text-[9px] text-[#8E8A85]">${escapeHtml(getPostTimeAgoDisplay(c.time || 'Recent'))}</span>
                                </div>
                                <p class="text-[#202124] text-[10.5px]">${escapeHtml(c.text || '')}</p>
                            </div>
                            <span class="text-[#8E8A85] hover:text-[#DE8662] shrink-0 text-xs cursor-pointer">↩</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        return `
            <div onclick="if(window.TempoApp && typeof window.TempoApp.navigateTo === 'function'){ window.TempoApp.navigateTo('community'); } else { window.location.hash = '#community?tab=posts'; } if(window.TempoCommunity && typeof window.TempoCommunity.selectTab === 'function'){ window.TempoCommunity.selectTab('posts'); setTimeout(() => { const el = document.querySelector('[data-post-id=\'${post.id}\']'); if(el) el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 150); }"
                 class="bg-[#F6F0EB] border border-[#4A4541] rounded-2xl sm:rounded-3xl p-4 sm:p-[18px] space-y-2.5 shadow-xs hover:border-[#DE8662] transition cursor-pointer group"
                 title="Open post by ${escapeHtml(post.authorName || 'Peer')}">
                <!-- Header -->
                <div class="flex items-start justify-between gap-2">
                    <div class="flex items-center space-x-2.5 shrink-0">
                        <img src="${escapeHtml(post.avatar || 'assets/tempo-logo.png')}"
                             alt="${escapeHtml(post.authorName || 'Peer')}"
                             class="w-9 h-9 rounded-full object-cover shrink-0">
                        <div class="shrink-0">
                            <h4 class="text-sm font-bold text-[#202124] leading-tight whitespace-nowrap">${escapeHtml(post.authorName || 'Peer')}</h4>
                            <span class="text-xs text-[#8E8A85] whitespace-nowrap">${escapeHtml(getPostTimeAgoDisplay(post.timeAgo || 'Recent'))}</span>
                        </div>
                    </div>
                    <div class="flex items-center justify-end space-x-1.5 flex-wrap gap-y-1">
                        ${tagsHTML}
                        <button type="button"
                                onclick="event.stopPropagation(); if (window.TempoCommunity && typeof window.TempoCommunity.toggleBookmark === 'function') { window.TempoCommunity.toggleBookmark('${post.id}'); }"
                                class="p-1 text-[#4A4541] hover:text-[#DE8662] transition cursor-pointer shrink-0"
                                title="Bookmark post"
                                aria-label="Bookmark post">
                            <img src="assets/bookmark_action_symbol.png" alt="Bookmark" class="w-4 h-4 object-contain opacity-70 hover:opacity-100 transition">
                        </button>
                    </div>
                </div>

                <!-- Content -->
                <p class="text-xs sm:text-[13px] text-[#202124] leading-relaxed">
                    ${escapeHtml(post.content || '')}
                </p>

                <!-- Thumbnails if present -->
                ${thumbnailsHTML}

                <!-- Action stats row matching EntryHome -->
                <div class="flex items-center space-x-5 text-[#4A4541] text-xs pt-1">
                    <span class="flex items-center space-x-1.5 cursor-pointer hover:text-[#DE8662]" onclick="event.stopPropagation(); if (window.TempoCommunity && typeof window.TempoCommunity.toggleLike === 'function') { window.TempoCommunity.toggleLike('${post.id}'); }">
                        <span class="text-sm">♡</span>
                        <span>${post.likes || 0}</span>
                    </span>
                    <span class="flex items-center space-x-1.5">
                        <img src="assets/comment_action_symbol.png" alt="Comments" class="w-3.5 h-3.5 object-contain">
                        <span>${commentsCount}</span>
                    </span>
                    <span class="flex items-center space-x-1.5 cursor-pointer hover:text-[#DE8662]">
                        <img src="assets/message_action_symbol.png" alt="Share" class="w-3.5 h-3.5 object-contain">
                    </span>
                </div>

                <!-- Comment preview if applicable -->
                ${commentPreviewHTML}
            </div>
        `;
    }

    function renderPreviewEmptyStateHTML() {
        return `
            <div class="py-8 flex flex-col items-center justify-center text-center space-y-2 text-[#8E8A85]">
                <img src="assets/comment-symbol.png" alt="No posts" class="w-6 h-6 opacity-40 object-contain mb-0.5">
                <p class="text-xs font-bold text-[#5A5550]">${isViLocale() ? 'Chưa có bài viết cộng đồng nào' : 'No community posts yet'}</p>
                <p class="text-[11px] text-[#8E8A85] leading-relaxed">${isViLocale() ? 'Hãy là người đầu tiên chia sẻ với bạn bè trong cộng đồng.' : 'Be the first to share with your peers in the community.'}</p>
            </div>
        `;
    }

    function renderUrgentPreview() {
        const container = document.getElementById('urgent-community-posts-list');
        if (!container) return;
        const distinctPosts = getDistinctPosts(posts, 2);
        if (distinctPosts.length === 0) {
            container.innerHTML = renderPreviewEmptyStateHTML();
            return;
        }
        container.innerHTML = distinctPosts.map(p => renderPreviewPostCardHTML(p)).join('');
    }

    function renderRecoveryPreview() {
        const container = document.getElementById('recovery-community-posts-list');
        if (!container) return;
        const distinctPosts = getDistinctPosts(posts, 2);
        if (distinctPosts.length === 0) {
            container.innerHTML = renderPreviewEmptyStateHTML();
            return;
        }
        container.innerHTML = distinctPosts.map(p => renderPreviewPostCardHTML(p)).join('');
    }

    function renderPostCardHTML(post) {
        return renderTwoColumnPostHTML(post);
    }

    function openCommunityModal() {
        const modal = document.getElementById('modal-community-posts');
        if (modal) modal.classList.remove('hidden');
    }

    function closeCommunityModal() {
        const modal = document.getElementById('modal-community-posts');
        if (modal) modal.classList.add('hidden');
    }

    function bindEvents() {
        const dmForm = document.getElementById('dm-message-form');
        if (dmForm) dmForm.onsubmit = handleSendMessage;

        const annForm = document.getElementById('form-create-announcement');
        if (annForm) annForm.onsubmit = handleCreateAnnouncementSubmit;

        const postForm = document.getElementById('form-modal-create-post');
        if (postForm) postForm.onsubmit = handleCreateCommunityPost;
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
        window.TempoI18n.onLanguageChange(() => {
            updateCommunityStaticUI();
            const postsPanel = document.getElementById('community-panel-posts');
            if (postsPanel && !postsPanel.classList.contains('hidden')) {
                renderCommunityPosts();
            }
            const tipsPanel = document.getElementById('community-panel-tips');
            if (tipsPanel && !tipsPanel.classList.contains('hidden')) {
                renderTips();
            }
            const learnPanel = document.getElementById('community-panel-learn');
            if (learnPanel && !learnPanel.classList.contains('hidden')) {
                renderLearn();
            }
            renderUrgentPreview();
            renderRecoveryPreview();
            const homeList = document.getElementById('homepage-community-posts-list');
            if (homeList) {
                const distinctPosts = getDistinctPosts(posts, 2);
                homeList.innerHTML = distinctPosts.map(p => renderPreviewPostCardHTML(p)).join('');
            }
        });
    }

    // Public API
    return {
        init,
        selectTab,
        handleReturnNavigation,
        updateReturnButton,
        updateCommunitySidebar,
        updatePostsToolbar,
        updateTipsToolbar,
        updateLearnToolbar,
        updateCommunityStaticUI,
        getTipDisplay,
        getLearnDisplay,
        // Announcement
        renderAnnouncements,
        openAnnouncementDetail,
        closeAnnouncementDetail,
        handleAnnouncementAction,
        openNewAnnouncementModal,
        closeNewAnnouncementModal,
        handleCreateAnnouncementSubmit,
        // Tips
        renderTips,
        openTipDetail,
        handleTipsSearch,
        clearTipsSearch,
        filterTipsCategory,
        // Learn
        renderLearn,
        openLearnDetail,
        handleLearnSearch,
        clearLearnSearch,
        // Posts (Requirement 5 & Post Action Symbols)
        navigateToPostsFeed,
        renderCommunityPosts,
        openCreatePostModal,
        closeCreatePostModal,
        handleCreateCommunityPost,
        handleInlineCommentSubmit,
        focusCommentInput,
        toggleFullWidthComments,
        toggleLike,
        toggleBookmark,
        openDirectMessageToAuthor,
        getUserBookmarks,
        saveUserBookmarks,
        syncUserBookmarksState,
        filterMyPosts,
        filterBookmarkedPosts,
        handlePostsSearch,
        getPosts: () => posts,
        getAllPosts: () => posts,
        getInitialPosts: () => [...INITIAL_POSTS],
        // Direct Message (Requirement 3 & 4)
        renderMessagesView,
        selectConversation,
        handleSendMessage,
        mobileToggleConversation,
        handleDMSearch,
        openChatRequests,
        closeChatRequests,
        renderChatRequestsList,
        acceptChatRequest,
        declineChatRequest,
        addChatRequest,
        getChatRequests: () => chatRequests,
        getConversations: () => conversations,
        // Previews & Legacy
        renderHomepagePreview,
        renderUrgentPreview,
        renderRecoveryPreview,
        renderPostCardHTML,
        renderPreviewPostCardHTML,
        renderPreviewEmptyStateHTML,
        getDistinctPosts,
        openCommunityModal,
        closeCommunityModal
    };
})();
