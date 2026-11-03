import re

# 1. Generate updated communityPosts.js
community_js_content = r'''/**
 * Tempo Community Module
 * Pixel-accurate reproduction of the 5 user-supplied reference screenshots:
 * Reference 1 — Announcement
 * Reference 2 — Tips (Solve)
 * Reference 3 — Learn
 * Reference 4 — Posts
 * Reference 5 — Direct Message
 */

window.TempoCommunity = (function() {
    'use strict';

    // =========================================================================
    // 1. DATASETS & EXACT REFERENCE CONTENT
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
            title: 'The 20-20 Cognitive Reset for Severe Brain Fog',
            usage: "Try it when your eyes see the words, but your brain doesn't process them."
        },
        {
            id: 'ask_professor_extension',
            title: 'How to Ask a Professor for an Extension (With Email Template)',
            usage: 'Try it when you want to ask for help,'
        },
        {
            id: 'falling_behind',
            title: 'Catching Up When Falling Several Weeks Behind',
            usage: 'Try it when missed lectures accumulate into an overwhelming backlog'
        },
        {
            id: 'roommate_friction',
            title: 'Setting Clear Boundaries with Noisy Roommates',
            usage: 'Try it when shared living friction disrupts your study and rest cycles'
        }
    ];

    // Reference 3: Learn (Knowledge Library)
    const INITIAL_LEARN = [
        {
            id: 'what_is_stress',
            title: 'What is stress?',
            summary: 'A normal response to pressure, change, or demands requiring adaptation.',
            image: 'assets/what_is_stress_scribble.svg'
        },
        {
            id: 'stress_eating',
            title: 'Stress eating',
            summary: 'A compassionate, non-shaming approach to eating when stressed.',
            image: 'assets/stress_eating_donut.jpg'
        },
        {
            id: 'stress_loop',
            title: 'The Stress Loop',
            summary: 'Understand how physiological arousal, catastrophic thoughts, and avoidance behavior reinforce each other in a closed cycle.',
            image: 'assets/practice-breathing-mascot.png'
        }
    ];

    // Reference 4: Community Posts
    const INITIAL_POSTS = [
        {
            id: 'post-ref-1',
            authorName: 'FPT Bá khí',
            avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=120&h=120&q=80',
            timeAgo: '2 hours ago',
            tags: [
                { label: 'mental health', bg: 'bg-[#DDE4E8]', text: 'text-[#4A5D6B]' },
                { label: 'Deadline', bg: 'bg-[#D4957D]', text: 'text-white' }
            ],
            tag: '#Deadline',
            content: 'How to survive 4 projects in just 2 weeks without destroying my mental health?\nUrgent situation; please give me some tips. Thank you all.',
            likes: 29,
            commentsCount: 5,
            isLiked: false,
            isBookmarked: false,
            layout: 'two-column',
            comments: [
                {
                    author: 'Innie',
                    avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=120&h=120&q=80',
                    time: '1 hours ago',
                    text: "Omg, same here, i'm dying in SSB deadline."
                },
                {
                    author: 'FPT Bá khí',
                    avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=120&h=120&q=80',
                    time: '1 hours ago',
                    isSubReply: true,
                    text: 'Would you like to be on a work date with me ><?'
                },
                {
                    author: 'tutamduongtinh',
                    avatar: 'assets/practice-breathing-mascot.png',
                    time: '3 hours ago',
                    text: 'Try urgent mode dude, still mental hurt, but less than.'
                }
            ]
        },
        {
            id: 'post-ref-2',
            authorName: 'Temposocute',
            avatar: 'assets/tempo-logo.png',
            timeAgo: '5 hours ago',
            tags: [
                { label: 'Focus zone', bg: 'bg-[#7C9985]', text: 'text-white' },
                { label: 'Background', bg: 'bg-[#FBF0DC]', text: 'text-[#8C6B37]' }
            ],
            tag: '#Focus',
            content: 'Hello, we have updated more background for Focus Zone, check it out now!',
            layout: 'full-width',
            thumbnails: [
                'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=200&h=130&q=80',
                'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=200&h=130&q=80',
                'https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=200&h=130&q=80',
                'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=200&h=130&q=80'
            ],
            likes: 58,
            commentsCount: 20,
            isLiked: false,
            isBookmarked: false,
            comments: []
        }
    ];

    // Reference 5: Direct Message Conversations & Threads
    const INITIAL_CONVERSATIONS = [
        {
            id: 'conv-tempo-admin',
            name: 'Tempo Admin',
            avatar: 'assets/tempo-logo.png',
            unreadCount: 1,
            time: '20m',
            lastMessage: 'Admin: We appreciate your...',
            subtitle: 'Official Tempo Support',
            messages: [
                {
                    id: 'm-adm-1',
                    sender: 'them',
                    senderName: 'Tempo Admin',
                    avatar: 'assets/tempo-logo.png',
                    text: 'Welcome to Tempo Community! Feel free to ask any questions regarding student support.',
                    time: 'Yesterday'
                }
            ]
        },
        {
            id: 'conv-innie',
            name: 'Innie',
            avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=120&h=120&q=80',
            unreadCount: 0,
            time: '1h',
            lastMessage: "Me: I'm free for Tuesday nig...",
            subtitle: 'Peer Student · Psychology',
            messages: [
                {
                    id: 'm-inn-1',
                    sender: 'them',
                    senderName: 'Innie',
                    avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=120&h=120&q=80',
                    text: 'Are you joining the study group on Tuesday?',
                    time: '1h ago'
                },
                {
                    id: 'm-inn-2',
                    sender: 'me',
                    senderName: 'tutamduongtinh',
                    avatar: 'assets/practice-breathing-mascot.png',
                    text: "I'm free for Tuesday night! Let's meet at the quiet zone.",
                    time: '1h ago'
                }
            ]
        },
        {
            id: 'conv-badminton',
            name: 'Go Badmintonnnn',
            avatar: 'assets/avatar_koala.jpg',
            unreadCount: 0,
            time: '1h',
            lastMessage: 'FPT Bá Khí: 7pm alright?',
            subtitle: 'You, Innie, FPT Bá Khí and 3 others',
            messages: [
                {
                    id: 'm-bad-1',
                    sender: 'me',
                    senderName: 'tutamduongtinh',
                    avatar: 'assets/practice-breathing-mascot.png',
                    text: 'I really need a game to wind down from this stress in this semester',
                    time: 'Mon. 10:00'
                },
                {
                    id: 'm-bad-2',
                    sender: 'them',
                    senderName: 'Innie',
                    avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=120&h=120&q=80',
                    text: 'Same here, count me in',
                    time: 'Mon. 10:10'
                },
                {
                    id: 'm-bad-3',
                    sender: 'them',
                    senderName: 'FPT Bá Khí',
                    avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=120&h=120&q=80',
                    text: 'Maybe next Sunday?',
                    time: 'Mon. 10:10'
                },
                {
                    id: 'm-bad-4',
                    sender: 'them',
                    senderName: 'FPT Bá Khí',
                    avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=120&h=120&q=80',
                    text: '7pm alright?',
                    time: 'Mon. 10:10'
                }
            ]
        }
    ];

    // State
    let announcements = [...INITIAL_ANNOUNCEMENTS];
    let tips = [...INITIAL_TIPS];
    let learn = [...INITIAL_LEARN];
    let posts = [...INITIAL_POSTS];
    let conversations = [...INITIAL_CONVERSATIONS];
    let activeTab = 'announcement';
    let activeConvId = 'conv-badminton';
    let currentTipsSearch = '';
    let currentLearnSearch = '';
    let currentPostsSearch = '';
    let isFilterMyPosts = false;
    let isFilterBookmarks = false;

    // =========================================================================
    // 2. INITIALIZATION & STORAGE
    // =========================================================================
    function init() {
        loadAnnouncements();
        loadPosts();
        loadConversations();
        renderHomepagePreview();
        renderUrgentPreview();
        renderRecoveryPreview();
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
                        if (!INITIAL_POSTS.some(initP => initP.id === p.id)) posts.push(p);
                    });
                    savePosts();
                }
            }
        } catch (e) {}
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
                if (Array.isArray(parsed) && parsed.length > 0) conversations = parsed;
            }
        } catch (e) {}
    }

    function saveConversations() {
        try {
            localStorage.setItem('tempo_direct_messages', JSON.stringify(conversations));
        } catch (e) {}
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

        // Update sidebar items active state matching Reference styling
        document.querySelectorAll('.community-nav-item').forEach(btn => {
            const btnTab = btn.getAttribute('data-community-tab');
            if (btnTab === activeTab) {
                btn.className = 'community-nav-item w-full flex items-center px-5 py-3 rounded-2xl text-[19px] sm:text-[20px] font-bold transition text-left cursor-pointer bg-[#F7ECE1] text-[#DE8662]';
            } else {
                btn.className = 'community-nav-item w-full flex items-center px-5 py-3 rounded-2xl text-[19px] sm:text-[20px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]';
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

        updateReturnButton();
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
        const backLabel = document.getElementById('community-back-label');
        if (!backLabel) return;

        const sourceContext = (window.TempoMode && typeof window.TempoMode.getSourceContext === 'function')
            ? window.TempoMode.getSourceContext()
            : null;
        const currentMode = (window.TempoMode && typeof window.TempoMode.getActiveContext === 'function' && window.TempoMode.getActiveContext())
            || (window.TempoMode && typeof window.TempoMode.getMode === 'function' ? window.TempoMode.getMode() : null);

        if (sourceContext === 'recovery' || (!sourceContext && currentMode === 'recovery')) {
            backLabel.textContent = 'Return to Recovery Mode';
        } else if (sourceContext === 'emergency' || (!sourceContext && currentMode === 'emergency')) {
            backLabel.textContent = 'Return to Emergency Support';
        } else {
            backLabel.textContent = 'Return Home';
        }
    }

    function handleReturnNavigation() {
        const sourceContext = (window.TempoMode && typeof window.TempoMode.getSourceContext === 'function')
            ? window.TempoMode.getSourceContext()
            : null;
        const currentMode = (window.TempoMode && typeof window.TempoMode.getActiveContext === 'function' && window.TempoMode.getActiveContext())
            || (window.TempoMode && typeof window.TempoMode.getMode === 'function' ? window.TempoMode.getMode() : null);

        if (sourceContext === 'recovery' || (!sourceContext && currentMode === 'recovery')) {
            if (window.TempoMode && typeof window.TempoMode.navigateToActiveDashboard === 'function') {
                window.TempoMode.navigateToActiveDashboard();
            } else if (window.TempoApp) {
                window.TempoApp.navigateTo('recovery-mode');
            }
        } else if (sourceContext === 'emergency' || (!sourceContext && currentMode === 'emergency')) {
            if (window.TempoApp) window.TempoApp.navigateTo('emergency');
        } else {
            if (window.TempoApp) window.TempoApp.navigateTo('today');
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
                <div class="bg-[#FFFDFB] border-2 border-[#ECA689] rounded-2xl overflow-hidden shadow-xs grid grid-cols-1 md:grid-cols-12 min-h-[260px]" data-announcement-id="${escapeHtml(ann.id)}">
                    <!-- Left Column: Content -->
                    <div class="md:col-span-5 p-7 sm:p-8 flex flex-col justify-between space-y-4">
                        <div class="space-y-3">
                            <h3 class="font-heading text-2xl sm:text-[26px] font-bold text-[#4A4541] leading-tight">
                                ${escapeHtml(ann.title)}
                            </h3>
                            <p class="text-sm sm:text-[15px] text-[#6E6964] leading-relaxed">
                                ${escapeHtml(ann.summary || '')}
                            </p>
                            <div>
                                <button type="button" 
                                        onclick="window.TempoCommunity.openAnnouncementDetail('${ann.id}')"
                                        class="text-[#DE8662] font-bold text-sm sm:text-base hover:underline inline-flex items-center space-x-1 cursor-pointer">
                                    <span>See more</span>
                                    <span>→</span>
                                </button>
                            </div>
                        </div>

                        ${ann.actionLabel ? `
                            <div class="pt-2">
                                <button type="button" 
                                        onclick="window.TempoCommunity.handleAnnouncementAction('${escapeHtml(ann.actionRoute || '')}')"
                                        class="bg-[#E3B8A3] hover:bg-[#D9A891] text-[#944B27] font-bold px-8 py-3 rounded-2xl shadow-xs transition text-sm sm:text-base cursor-pointer">
                                    ${escapeHtml(ann.actionLabel)}
                                </button>
                            </div>
                        ` : ''}
                    </div>

                    <!-- Right Column: Product Screenshot -->
                    <div class="md:col-span-7 bg-[#F7F5F2] border-t md:border-t-0 md:border-l border-[#ECA689]/40 flex items-center justify-center p-2 sm:p-3 overflow-hidden">
                        <img src="${escapeHtml(ann.coverImage || 'assets/announcement_selfcheck_v21.png')}" 
                             alt="${escapeHtml(ann.title)}" 
                             class="w-full h-full max-h-[300px] object-contain rounded-xl shadow-2xs">
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
                <p class="font-medium text-base text-[#4A4541] leading-relaxed">${escapeHtml(ann.summary || '')}</p>
                <div class="text-sm text-[#6E6964] leading-relaxed pt-2 space-y-2">
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

    function handleCreateAnnouncement(e) {
        if (e) e.preventDefault();
        if (!isUserAdmin()) return;

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
            actionLabel: actionLabelInput?.value?.trim() || 'Try it now',
            actionRoute: actionRouteSelect?.value || 'stress-check'
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
                <div class="bg-[#FFFDFB] border-2 border-[#ECA689] rounded-3xl p-6 sm:p-7 shadow-xs flex flex-col justify-between space-y-4 min-h-[220px]">
                    <div class="space-y-3">
                        <h3 class="font-heading text-lg sm:text-[20px] font-bold text-[#4A4541] leading-snug">
                            ${escapeHtml(item.title)}
                        </h3>
                        <p class="text-sm sm:text-base text-[#6E6964] leading-relaxed">
                            <strong class="text-[#DE8662] font-bold">Usage:</strong> ${escapeHtml(item.usage)}
                        </p>
                    </div>

                    <div>
                        <button type="button" 
                                onclick="window.TempoCommunity.openTipDetail('${escapeHtml(item.id)}')"
                                class="text-[#DE8662] font-bold text-sm sm:text-base flex items-center space-x-1 hover:underline cursor-pointer">
                            <span>See more</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    function openTipDetail(tipId) {
        if (window.TempoLearnSolve && typeof window.TempoLearnSolve.openModal === 'function') {
            window.TempoLearnSolve.openModal(tipId);
        }
    }

    function handleTipsSearch(query) {
        currentTipsSearch = (query || '').trim();
        renderTips();
    }

    function clearTipsSearch() {
        const input = document.getElementById('tips-search-input');
        if (input) input.value = '';
        handleTipsSearch('');
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
                <div class="bg-[#FFFDFB] border-2 border-[#ECA689] rounded-3xl p-6 sm:p-7 shadow-xs flex flex-col md:flex-row items-center justify-between gap-6">
                    <!-- Left Side: Text -->
                    <div class="flex-1 space-y-3">
                        <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#4A4541]">
                            ${escapeHtml(item.title)}
                        </h3>
                        <p class="text-sm sm:text-base text-[#6E6964] leading-relaxed">
                            ${escapeHtml(item.summary)}
                        </p>
                        <div>
                            <button type="button" 
                                    onclick="window.TempoCommunity.openLearnDetail('${escapeHtml(item.id)}')"
                                    class="text-[#DE8662] font-bold text-sm sm:text-base hover:underline inline-flex items-center space-x-1 cursor-pointer">
                                <span>See more</span>
                                <span>→</span>
                            </button>
                        </div>
                    </div>

                    <!-- Right Side: Illustration / Photo -->
                    <div class="w-full md:w-72 h-44 sm:h-48 overflow-hidden rounded-2xl bg-stone-50 flex items-center justify-center shrink-0">
                        <img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.title)}" class="w-full h-full object-cover">
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
        const input = document.getElementById('learn-search-input');
        if (input) input.value = '';
        handleLearnSearch('');
    }

    // =========================================================================
    // 7. REFERENCE 4: POSTS
    // =========================================================================
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
            <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold ${t.bg} ${t.text}">
                ${escapeHtml(t.label)}
            </span>
        `).join(' ');

        return `
            <div class="bg-white border border-[#4A4541] rounded-3xl overflow-hidden shadow-xs grid grid-cols-1 md:grid-cols-12" data-post-id="${post.id}">
                <!-- Left Column: Post Content & Actions -->
                <div class="md:col-span-7 p-6 sm:p-7 border-b md:border-b-0 md:border-r border-[#4A4541]/30 flex flex-col justify-between space-y-4">
                    <!-- Header -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <img src="${escapeHtml(post.avatar)}" alt="${escapeHtml(post.authorName)}" class="w-9 h-9 rounded-full object-cover">
                            <div>
                                <h4 class="text-sm font-bold text-[#202124]">${escapeHtml(post.authorName)}</h4>
                                <span class="text-[11px] text-[#8E8A85] italic">${escapeHtml(post.timeAgo)}</span>
                            </div>
                        </div>

                        <div class="flex items-center space-x-2">
                            ${tagsHTML}
                            <button type="button" onclick="window.TempoCommunity.toggleBookmark('${post.id}')" 
                                    class="p-1 text-[#4A4541] hover:text-[#DE8662] transition cursor-pointer text-base ${post.isBookmarked ? 'text-[#DE8662]' : ''}">
                                ${post.isBookmarked ? '🔖' : '🏷️'}
                            </button>
                        </div>
                    </div>

                    <!-- Post Body -->
                    <div class="space-y-2 py-1">
                        <p class="text-xs sm:text-sm text-[#202124] leading-relaxed whitespace-pre-line">
                            ${escapeHtml(post.content)}
                        </p>
                    </div>

                    <!-- Actions Row -->
                    <div class="pt-2 flex items-center space-x-6 text-[#4A4541] text-xs font-medium">
                        <button type="button" onclick="window.TempoCommunity.toggleLike('${post.id}')" 
                                class="flex items-center space-x-1.5 hover:text-[#DE8662] transition cursor-pointer ${post.isLiked ? 'text-[#DE8662] font-bold' : ''}">
                            <span class="text-base">${post.isLiked ? '♥' : '♡'}</span>
                            <span>${post.likes || 0}</span>
                        </button>
                        <button type="button" onclick="window.TempoCommunity.focusCommentInput('${post.id}')" 
                                class="flex items-center space-x-1.5 hover:text-[#202124] transition cursor-pointer">
                            <span class="text-base">💬</span>
                            <span>${post.commentsCount || (post.comments ? post.comments.length : 0)}</span>
                        </button>
                        <button type="button" onclick="if(window.TempoApp) window.TempoApp.showToast('Link copied to clipboard');" 
                                class="hover:text-[#202124] transition cursor-pointer text-base" title="Share">
                            ▷
                        </button>
                    </div>
                </div>

                <!-- Right Column: Comments & Replies (Reference 4) -->
                <div class="md:col-span-5 p-5 sm:p-6 bg-[#FFFDFB] flex flex-col justify-between space-y-4">
                    <div class="space-y-3.5">
                        ${(post.comments || []).map(c => `
                            <div class="${c.isSubReply ? 'pl-5 sm:pl-6' : ''} space-y-1">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center space-x-2">
                                        <img src="${escapeHtml(c.avatar || 'assets/tempo-logo.png')}" alt="${escapeHtml(c.author)}" class="w-6 h-6 rounded-full object-cover">
                                        <span class="text-xs font-bold text-[#202124]">${escapeHtml(c.author)}</span>
                                        <span class="text-[10px] text-[#8E8A85]">${escapeHtml(c.time || '')}</span>
                                    </div>
                                    <button type="button" class="text-xs text-stone-400 hover:text-[#DE8662]">♡</button>
                                </div>
                                <p class="text-xs text-[#4A4541] leading-relaxed pl-8">
                                    ${escapeHtml(c.text)}
                                </p>
                            </div>
                        `).join('')}
                    </div>

                    <!-- Add Comment input -->
                    <form onsubmit="window.TempoCommunity.handleInlineCommentSubmit(event, '${post.id}')" class="flex items-center space-x-2 pt-2 border-t border-[#EAE4DF]">
                        <input type="text" id="input-comment-${post.id}" 
                               placeholder="Reply..." 
                               class="flex-1 px-3 py-1.5 text-xs bg-[#FAF8F5] border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#DE8662]">
                        <button type="submit" class="bg-[#DFB59F] text-white px-3 py-1.5 rounded-xl text-xs font-bold shrink-0">
                            Post
                        </button>
                    </form>
                </div>
            </div>
        `;
    }

    function renderFullWidthPostHTML(post) {
        const tagsHTML = (post.tags || []).map(t => `
            <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold ${t.bg} ${t.text}">
                ${escapeHtml(t.label)}
            </span>
        `).join(' ');

        return `
            <div class="bg-white border border-[#4A4541] rounded-3xl p-6 sm:p-7 space-y-4 shadow-xs" data-post-id="${post.id}">
                <!-- Header -->
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <img src="${escapeHtml(post.avatar)}" alt="${escapeHtml(post.authorName)}" class="w-9 h-9 rounded-full object-cover">
                        <div>
                            <h4 class="text-sm font-bold text-[#202124]">${escapeHtml(post.authorName)}</h4>
                            <span class="text-[11px] text-[#8E8A85]">${escapeHtml(post.timeAgo)}</span>
                        </div>
                    </div>

                    <div class="flex items-center space-x-2">
                        ${tagsHTML}
                        <button type="button" onclick="window.TempoCommunity.toggleBookmark('${post.id}')" 
                                class="p-1 text-[#4A4541] hover:text-[#DE8662] transition cursor-pointer text-base ${post.isBookmarked ? 'text-[#DE8662]' : ''}">
                            ${post.isBookmarked ? '🔖' : '🏷️'}
                        </button>
                    </div>
                </div>

                <!-- Content -->
                <div class="space-y-3">
                    <p class="text-xs sm:text-sm text-[#202124] leading-relaxed">
                        ${escapeHtml(post.content)}
                    </p>

                    ${post.thumbnails && post.thumbnails.length > 0 ? `
                        <div class="grid grid-cols-4 gap-2.5 pt-1">
                            ${post.thumbnails.map(img => `
                                <div class="aspect-4/3 rounded-xl overflow-hidden bg-stone-100 border border-stone-200">
                                    <img src="${escapeHtml(img)}" alt="Attachment" class="w-full h-full object-cover">
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>

                <!-- Actions Row -->
                <div class="pt-2 flex items-center space-x-6 text-[#4A4541] text-xs font-medium border-t border-[#EAE4DF]/60">
                    <button type="button" onclick="window.TempoCommunity.toggleLike('${post.id}')" 
                            class="flex items-center space-x-1.5 hover:text-[#DE8662] transition cursor-pointer ${post.isLiked ? 'text-[#DE8662] font-bold' : ''}">
                        <span class="text-base">${post.isLiked ? '♥' : '♡'}</span>
                        <span>${post.likes || 0}</span>
                    </button>
                    <button type="button" onclick="if(window.TempoApp) window.TempoApp.showToast('Comments');" 
                            class="flex items-center space-x-1.5 hover:text-[#202124] transition cursor-pointer">
                        <span class="text-base">💬</span>
                        <span>${post.commentsCount || 0}</span>
                    </button>
                    <button type="button" onclick="if(window.TempoApp) window.TempoApp.showToast('Link copied to clipboard');" 
                            class="hover:text-[#202124] transition cursor-pointer text-base" title="Share">
                        ▷
                    </button>
                </div>
            </div>
        `;
    }

    function toggleLike(postId) {
        const post = posts.find(p => p.id === postId);
        if (!post) return;
        post.isLiked = !post.isLiked;
        post.likes += post.isLiked ? 1 : -1;
        savePosts();
        renderCommunityPosts();
        renderHomepagePreview();
    }

    function toggleBookmark(postId) {
        const post = posts.find(p => p.id === postId);
        if (!post) return;
        post.isBookmarked = !post.isBookmarked;
        savePosts();
        renderCommunityPosts();
        renderHomepagePreview();
        if (window.TempoApp) {
            window.TempoApp.showToast(post.isBookmarked ? "Post saved to bookmarks" : "Post removed from bookmarks");
        }
    }

    function handleInlineCommentSubmit(e, postId) {
        if (e) e.preventDefault();
        const input = document.getElementById(`input-comment-${postId}`);
        const text = input?.value?.trim();
        if (!text) return;

        const post = posts.find(p => p.id === postId);
        if (!post) return;

        if (!post.comments) post.comments = [];
        const profile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
        const author = profile?.full_name || 'Innie';

        post.comments.push({
            author,
            avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=120&h=120&q=80',
            time: 'Just now',
            text
        });
        post.commentsCount = post.comments.length;
        savePosts();
        input.value = '';
        renderCommunityPosts();
    }

    function focusCommentInput(postId) {
        const input = document.getElementById(`input-comment-${postId}`);
        if (input) input.focus();
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

        const isAnon = anonCheckbox ? anonCheckbox.checked : false;
        const tag = tagSelect ? tagSelect.value : '#Deadline';

        const profile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
        const authorName = isAnon ? 'Anonymous' : (profile?.full_name || 'Innie');
        const avatar = isAnon 
            ? 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&h=120&q=80'
            : 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=120&h=120&q=80';

        const newPost = {
            id: 'post-' + Date.now(),
            authorName,
            avatar,
            timeAgo: 'Just now',
            tags: [
                { label: tag.replace('#', ''), bg: 'bg-[#D4957D]', text: 'text-white' }
            ],
            tag,
            content,
            likes: 0,
            commentsCount: 0,
            isLiked: false,
            isBookmarked: false,
            layout: 'two-column',
            comments: []
        };

        posts.unshift(newPost);
        savePosts();
        renderCommunityPosts();
        renderHomepagePreview();
        closeCreatePostModal();

        if (textarea) textarea.value = '';
        if (window.TempoApp) window.TempoApp.showToast("Your supportive post was published!");
    }

    // =========================================================================
    // 8. REFERENCE 5: DIRECT MESSAGE
    // =========================================================================
    function renderMessagesView() {
        const guestView = document.getElementById('community-dm-guest-view');
        const authView = document.getElementById('community-dm-auth-view');
        const isAuth = !!(window.TempoAuth && window.TempoAuth.getCurrentUser());

        if (!isAuth) {
            if (guestView) guestView.classList.remove('hidden');
            if (authView) authView.classList.add('hidden');
            return;
        }

        if (guestView) guestView.classList.add('hidden');
        if (authView) authView.classList.remove('hidden');

        renderConversationsList();
        renderActiveConversation();
    }

    function renderConversationsList(filterQuery = '') {
        const container = document.getElementById('dm-conversations-list');
        if (!container) return;

        let filtered = [...conversations];
        if (filterQuery) {
            const q = filterQuery.toLowerCase();
            filtered = filtered.filter(c => (c.name || '').toLowerCase().includes(q) || (c.lastMessage || '').toLowerCase().includes(q));
        }

        container.innerHTML = filtered.map(c => {
            const isActive = c.id === activeConvId;
            return `
                <div onclick="window.TempoCommunity.selectConversation('${c.id}')"
                     class="p-3 rounded-2xl cursor-pointer transition flex items-center space-x-3 ${isActive ? 'bg-[#F7ECE1]' : 'hover:bg-[#FAF8F5]'}">
                    <div class="relative shrink-0">
                        <img src="${escapeHtml(c.avatar)}" alt="${escapeHtml(c.name)}" class="w-10 h-10 rounded-full object-cover">
                    </div>
                    <div class="flex-1 min-w-0 space-y-0.5">
                        <div class="flex items-center justify-between">
                            <h4 class="text-xs sm:text-sm font-bold text-[#202124] truncate">${escapeHtml(c.name)}</h4>
                            <span class="text-[10px] text-[#8E8A85] shrink-0">${escapeHtml(c.time || '')}</span>
                        </div>
                        <p class="text-[11px] text-[#6E6964] truncate leading-tight">${escapeHtml(c.lastMessage)}</p>
                    </div>
                    ${c.unreadCount ? `<span class="w-4 h-4 rounded-full bg-[#E04B38] text-white text-[10px] font-bold flex items-center justify-center shrink-0">${c.unreadCount}</span>` : ''}
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
        const conv = conversations.find(c => c.id === activeConvId);
        if (!conv) return;

        const nameEl = document.getElementById('dm-active-name');
        const roleEl = document.getElementById('dm-active-role');
        const avatarEl = document.getElementById('dm-active-avatar');
        const messagesContainer = document.getElementById('dm-messages-container');

        if (nameEl) nameEl.textContent = conv.name;
        if (roleEl) roleEl.textContent = conv.subtitle || 'Active conversation';
        if (avatarEl) avatarEl.src = conv.avatar;

        if (messagesContainer) {
            messagesContainer.innerHTML = (conv.messages || []).map(m => {
                const isMe = m.sender === 'me';
                if (isMe) {
                    // Outgoing message (Reference 5: tutamduongtinh, blue bubble bg-[#CAD8E0], avatar on right)
                    return `
                        <div class="flex flex-col items-end space-y-1">
                            <span class="text-[11px] font-bold text-[#202124] pr-12">${escapeHtml(m.senderName || 'tutamduongtinh')}</span>
                            <div class="flex items-end space-x-2">
                                <span class="text-[10px] text-[#8E8A85] pb-1">${escapeHtml(m.time || '')}</span>
                                <div class="bg-[#CAD8E0] text-[#202124] text-xs sm:text-sm p-3.5 rounded-2xl rounded-tr-xs max-w-md shadow-2xs leading-relaxed">
                                    ${escapeHtml(m.text)}
                                </div>
                                <img src="${escapeHtml(m.avatar || 'assets/practice-breathing-mascot.png')}" alt="Me" class="w-8 h-8 rounded-full object-cover shrink-0">
                            </div>
                        </div>
                    `;
                } else {
                    // Incoming message (Reference 5: sage green bubble bg-[#E1EAE3], avatar on left)
                    return `
                        <div class="flex flex-col items-start space-y-1">
                            <span class="text-[11px] font-bold text-[#202124] pl-10">${escapeHtml(m.senderName || '')}</span>
                            <div class="flex items-start space-x-2">
                                <img src="${escapeHtml(m.avatar || 'assets/tempo-logo.png')}" alt="${escapeHtml(m.senderName || '')}" class="w-8 h-8 rounded-full object-cover shrink-0 mt-0.5">
                                <div class="bg-[#E1EAE3] text-[#202124] text-xs sm:text-sm p-3.5 rounded-2xl rounded-tl-xs max-w-md shadow-2xs leading-relaxed">
                                    ${escapeHtml(m.text)}
                                </div>
                                <span class="text-[10px] text-[#8E8A85] pt-2 self-end">${escapeHtml(m.time || '')}</span>
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
    // 9. HOMEPAGE PREVIEWS & LEGACY COMPATIBILITY
    // =========================================================================
    function renderPostCardHTML(post, options = {}) {
        if (!post) return '';
        const tagsHTML = (post.tags && post.tags.length > 0
            ? post.tags.map(t => `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${t.bg || 'bg-stone-100'} ${t.text || 'text-stone-700'}">${escapeHtml(t.label || t)}</span>`).join(' ')
            : (post.tag ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FFE9DC] text-[#B83D08]">${escapeHtml(post.tag)}</span>` : ''));

        return `
            <div class="p-3.5 sm:p-4 bg-[#F6F0EB] border border-[#42413F] rounded-2xl space-y-2.5 transition flex flex-col justify-between" data-post-id="${post.id}">
                <div class="flex items-center justify-between gap-2">
                    <div class="flex items-center space-x-2.5 min-w-0">
                        <img src="${escapeHtml(post.avatar || 'assets/tempo-logo.png')}" alt="${escapeHtml(post.authorName || 'Student')}" 
                             class="w-8 h-8 rounded-full object-cover border border-stone-200 shrink-0">
                        <div class="min-w-0">
                            <div class="flex items-center space-x-1.5 flex-wrap">
                                <span class="text-xs font-bold text-[#202124]">${escapeHtml(post.authorName || 'Anonymous')}</span>
                                ${tagsHTML}
                            </div>
                            <div class="text-[10px] text-[#8E8A85]">
                                <span>${escapeHtml(post.timeAgo || 'Recently')}</span>
                            </div>
                        </div>
                    </div>
                    <button type="button" onclick="window.TempoCommunity.toggleBookmark('${post.id}')" 
                            class="hover:text-[#DE8662] transition cursor-pointer p-1 text-[#736F68] shrink-0 ${post.isBookmarked ? 'text-[#DE8662]' : ''}">
                        ${post.isBookmarked ? '🔖' : '🏷️'}
                    </button>
                </div>

                <p class="text-xs text-[#202124] leading-relaxed break-words">
                    ${escapeHtml(post.content)}
                </p>

                <div class="pt-2 border-t border-[#EAE4DF] flex items-center justify-between text-xs text-[#736F68]">
                    <div class="flex items-center space-x-4">
                        <button type="button" onclick="window.TempoCommunity.toggleLike('${post.id}')" 
                                class="flex items-center space-x-1 hover:text-[#DE8662] transition cursor-pointer ${post.isLiked ? 'text-[#DE8662] font-semibold' : ''}">
                            <span>${post.isLiked ? '♥' : '♡'}</span>
                            <span class="text-[11px]">${post.likes || 0}</span>
                        </button>
                        <button type="button" onclick="window.TempoApp.navigateTo('community', 'posts')" 
                                class="flex items-center space-x-1 hover:text-[#202124] text-[#736F68] transition cursor-pointer">
                            <span>💬</span>
                            <span class="text-[11px]">${post.commentsCount || 0}</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function renderUrgentPreview() {
        const container = document.getElementById('urgent-community-posts-list');
        if (!container) return;
        container.innerHTML = posts.slice(0, 2).map(p => renderPostCardHTML(p)).join('');
    }

    function renderRecoveryPreview() {
        const container = document.getElementById('recovery-community-posts-list');
        if (!container) return;
        container.innerHTML = posts.slice(0, 2).map(p => renderPostCardHTML(p)).join('');
    }

    function renderHomepagePreview() {
        const container = document.getElementById('homepage-community-posts-list');
        if (container) {
            container.innerHTML = posts.slice(0, 2).map(post => renderPostCardHTML(post)).join('');
        }
        renderUrgentPreview();
        renderRecoveryPreview();
    }

    function openCommunityModal(section = 'feed') {
        if (window.TempoApp) {
            const targetTab = section === 'messages' ? 'messages' : 'posts';
            window.TempoApp.navigateTo('community', targetTab);
        }
    }

    function closeCommunityModal() {
        const modal = document.getElementById('modal-community-posts');
        if (modal) modal.classList.add('hidden');
    }

    function bindEvents() {
        const dmForm = document.getElementById('dm-message-form');
        if (dmForm) dmForm.addEventListener('submit', handleSendMessage);

        const annForm = document.getElementById('form-create-announcement');
        if (annForm) annForm.addEventListener('submit', handleCreateAnnouncement);

        const postForm = document.getElementById('form-modal-create-post');
        if (postForm) postForm.addEventListener('submit', handleCreateCommunityPost);
    }

    function escapeHtml(str) {
        return (str || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    return {
        init,
        selectTab,
        getActiveTab: () => activeTab,
        handleReturnNavigation,
        updateReturnButton,
        // Announcement
        renderAnnouncements,
        openAnnouncementDetail,
        closeAnnouncementDetail,
        handleAnnouncementAction,
        openNewAnnouncementModal,
        closeNewAnnouncementModal,
        handleCreateAnnouncement,
        getAnnouncements: () => announcements,
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
        // Posts
        renderCommunityPosts,
        openCreatePostModal,
        closeCreatePostModal,
        handleCreateCommunityPost,
        handleInlineCommentSubmit,
        focusCommentInput,
        toggleLike,
        toggleBookmark,
        filterMyPosts,
        filterBookmarkedPosts,
        handlePostsSearch,
        getPosts: () => posts,
        getAllPosts: () => posts,
        getInitialPosts: () => [...INITIAL_POSTS],
        // Direct Message
        renderMessagesView,
        selectConversation,
        handleSendMessage,
        mobileToggleConversation,
        handleDMSearch,
        // Previews & Legacy
        renderHomepagePreview,
        renderUrgentPreview,
        renderRecoveryPreview,
        renderPostCardHTML,
        openCommunityModal,
        closeCommunityModal
    };
})();
'''

# Convert line endings to CRLF for communityPosts.js
community_js_crlf = community_js_content.replace('\r\n', '\n').replace('\n', '\r\n')
with open('communityPosts.js', 'wb') as f:
    f.write(community_js_crlf.encode('utf-8'))
print("Successfully generated pixel-perfect communityPosts.js (CRLF).")
