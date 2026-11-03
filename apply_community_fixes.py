import re
import os

print("Preparing comprehensive Tempo Community UI & Navigation fixes...")

# ==============================================================================
# 1. GENERATE UPDATED communityPosts.js
# ==============================================================================
community_js_content = r'''/**
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
            authorName: 'FPT Bá khí',
            authorHandle: '@fpt_bakhi',
            timeAgo: '2h',
            avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=120&h=120&q=80',
            content: 'How can I finish 3 deadlines in 1 day? Help me please.',
            tags: [
                { label: '#mental health', bg: 'bg-[#EBF3F5]', text: 'text-[#3E707D]' },
                { label: '#Deadline', bg: 'bg-[#FCEFE8]', text: 'text-[#DE8662]' }
            ],
            likes: 29,
            commentsCount: 5,
            isLiked: false,
            isBookmarked: false,
            layout: 'two-column',
            comments: [
                {
                    id: 'c-1',
                    author: 'Innie',
                    avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=120&h=120&q=80',
                    time: '1h',
                    text: 'Same problem here, you are not alone'
                },
                {
                    id: 'c-2',
                    author: 'FPT Bá khí',
                    avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=120&h=120&q=80',
                    time: '45m',
                    text: 'Glad to hear that',
                    isSubReply: true
                },
                {
                    id: 'c-3',
                    author: 'tutamduongtinh',
                    avatar: 'assets/practice-breathing-mascot.png',
                    time: '30m',
                    text: 'First, take a deep breath. Try to break it down. Which one is the closest deadline and takes the least time to do? If you can finish one, you might feel a bit better to continue with the rest.'
                }
            ]
        },
        {
            id: 'post-2',
            authorName: 'Temposocute',
            authorHandle: '@temposocute',
            timeAgo: '3h',
            avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=120&h=120&q=80',
            content: 'Sharing some peaceful study backgrounds that helped me stay calm through midterm week.',
            tags: [
                { label: '#Focus zone', bg: 'bg-[#EBF3F5]', text: 'text-[#3E707D]' },
                { label: '#Background', bg: 'bg-[#F2EAE3]', text: 'text-[#5A5550]' }
            ],
            thumbnails: [
                'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=300&q=80',
                'https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=300&q=80',
                'https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=300&q=80',
                'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=300&q=80'
            ],
            likes: 42,
            commentsCount: 8,
            isLiked: false,
            isBookmarked: false,
            comments: []
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
            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
                window.TempoMode.setMode('recovery');
            }
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
                <div class="bg-[#FFFDFB] border-2 border-[#ECA689] rounded-3xl p-5 sm:p-6 shadow-xs flex flex-col justify-between space-y-3 min-h-[190px]">
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
                                <span class="text-[10px] text-[#8E8A85] italic">${escapeHtml(post.timeAgo)}</span>
                            </div>
                        </div>

                        <div class="flex items-center space-x-2">
                            ${tagsHTML}
                            <button type="button" onclick="window.TempoCommunity.toggleBookmark('${post.id}')" 
                                    class="p-1 text-[#4A4541] hover:text-[#DE8662] transition cursor-pointer text-sm ${post.isBookmarked ? 'text-[#DE8662]' : ''}">
                                ${post.isBookmarked ? '🔖' : '🏷️'}
                            </button>
                        </div>
                    </div>

                    <!-- Post Body -->
                    <div class="space-y-1.5 py-0.5">
                        <p class="text-xs sm:text-[12.5px] text-[#202124] leading-relaxed whitespace-pre-line">
                            ${escapeHtml(post.content)}
                        </p>
                    </div>

                    <!-- Actions Row -->
                    <div class="pt-1.5 flex items-center space-x-5 text-[#4A4541] text-xs font-medium">
                        <button type="button" onclick="window.TempoCommunity.toggleLike('${post.id}')" 
                                class="flex items-center space-x-1 hover:text-[#DE8662] transition cursor-pointer ${post.isLiked ? 'text-[#DE8662] font-bold' : ''}">
                            <span class="text-sm">${post.isLiked ? '♥' : '♡'}</span>
                            <span class="text-xs">${post.likes || 0}</span>
                        </button>
                        <button type="button" onclick="window.TempoCommunity.focusCommentInput('${post.id}')" 
                                class="flex items-center space-x-1 hover:text-[#202124] transition cursor-pointer">
                            <span class="text-sm">💬</span>
                            <span class="text-xs">${post.commentsCount || (post.comments ? post.comments.length : 0)}</span>
                        </button>
                        <button type="button" onclick="if(window.TempoApp) window.TempoApp.showToast('Link copied to clipboard');" 
                                class="hover:text-[#202124] transition cursor-pointer text-sm" title="Share">
                            ▷
                        </button>
                    </div>
                </div>

                <!-- Right Column: Comments & Replies (Reference 4) -->
                <div class="md:col-span-5 p-4 sm:p-5 bg-[#FFFDFB] flex flex-col justify-between space-y-3">
                    <div class="space-y-3">
                        ${(post.comments || []).map(c => `
                            <div class="${c.isSubReply ? 'pl-4 sm:pl-5' : ''} space-y-1">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center space-x-1.5">
                                        <img src="${escapeHtml(c.avatar || 'assets/tempo-logo.png')}" alt="${escapeHtml(c.author)}" class="w-5 h-5 rounded-full object-cover">
                                        <span class="text-[11px] font-bold text-[#202124]">${escapeHtml(c.author)}</span>
                                        <span class="text-[9.5px] text-[#8E8A85]">${escapeHtml(c.time || '')}</span>
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
            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${t.bg} ${t.text}">
                ${escapeHtml(t.label)}
            </span>
        `).join(' ');

        return `
            <div class="bg-white border border-[#4A4541] rounded-3xl p-5 sm:p-6 space-y-3 shadow-xs" data-post-id="${post.id}">
                <!-- Header -->
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2.5">
                        <img src="${escapeHtml(post.avatar)}" alt="${escapeHtml(post.authorName)}" class="w-8 h-8 rounded-full object-cover">
                        <div>
                            <h4 class="text-[13px] font-bold text-[#202124]">${escapeHtml(post.authorName)}</h4>
                            <span class="text-[10px] text-[#8E8A85]">${escapeHtml(post.timeAgo)}</span>
                        </div>
                    </div>

                    <div class="flex items-center space-x-2">
                        ${tagsHTML}
                        <button type="button" onclick="window.TempoCommunity.toggleBookmark('${post.id}')" 
                                class="p-1 text-[#4A4541] hover:text-[#DE8662] transition cursor-pointer text-sm ${post.isBookmarked ? 'text-[#DE8662]' : ''}">
                            ${post.isBookmarked ? '🔖' : '🏷️'}
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

                <!-- Actions Row -->
                <div class="pt-2 flex items-center space-x-5 text-[#4A4541] text-xs font-medium border-t border-[#EAE4DF]/60">
                    <button type="button" onclick="window.TempoCommunity.toggleLike('${post.id}')" 
                            class="flex items-center space-x-1 hover:text-[#DE8662] transition cursor-pointer ${post.isLiked ? 'text-[#DE8662] font-bold' : ''}">
                        <span class="text-sm">${post.isLiked ? '♥' : '♡'}</span>
                        <span class="text-xs">${post.likes || 0}</span>
                    </button>
                    <button type="button" onclick="if(window.TempoApp) window.TempoApp.showToast('Comments');" 
                            class="flex items-center space-x-1 hover:text-[#202124] transition cursor-pointer">
                        <span class="text-sm">💬</span>
                        <span class="text-xs">${post.commentsCount || 0}</span>
                    </button>
                    <button type="button" onclick="if(window.TempoApp) window.TempoApp.showToast('Link copied to clipboard');" 
                            class="hover:text-[#202124] transition cursor-pointer text-sm" title="Share">
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
        post.likes = (post.likes || 0) + (post.isLiked ? 1 : -1);
        if (post.likes < 0) post.likes = 0;
        savePosts();
        renderCommunityPosts();
    }

    function toggleBookmark(postId) {
        const post = posts.find(p => p.id === postId);
        if (!post) return;
        post.isBookmarked = !post.isBookmarked;
        savePosts();
        renderCommunityPosts();
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

    function focusCommentInput(postId) {
        const input = document.getElementById(`input-comment-${postId}`);
        if (input) {
            input.focus();
            input.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
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
            avatar: 'assets/practice-breathing-mascot.png',
            time: 'Just now',
            text
        });
        post.commentsCount = post.comments.length;

        savePosts();
        input.value = '';
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
    // 8. REFERENCE 5: DIRECT MESSAGE & CHAT REQUESTS
    // =========================================================================

    function renderMessagesView() {
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

        // Requirement 3: Empty conversation list without fabricated entries
        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="h-44 flex flex-col items-center justify-center p-4 text-center space-y-1.5 text-[#8E8A85]">
                    <span class="text-xl">💬</span>
                    <p class="text-xs font-bold text-[#5A5550]">No conversations yet</p>
                    <p class="text-[10.5px] text-[#8E8A85] leading-relaxed max-w-[200px]">Incoming messages and accepted chat requests will appear here.</p>
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

        // Requirement 3: If there is no selected conversation, keep the message panel empty
        if (!activeConvId || conversations.length === 0) {
            if (nameEl) nameEl.textContent = 'Direct Messages';
            if (roleEl) roleEl.textContent = 'Select a conversation from the left to start messaging';
            if (avatarEl) avatarEl.src = 'assets/tempo-logo.png';
            if (messagesContainer) {
                messagesContainer.innerHTML = `
                    <div class="h-full min-h-[320px] flex flex-col items-center justify-center p-6 text-center space-y-2 text-[#8E8A85]">
                        <span class="text-3xl">✉️</span>
                        <p class="text-xs sm:text-[13px] font-bold text-[#5A5550]">No conversation selected</p>
                        <p class="text-[11px] text-[#8E8A85] max-w-xs leading-relaxed">Choose a contact from your conversations list or check Chat Requests to begin chatting.</p>
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
        const latest = posts.slice(0, 2);
        container.innerHTML = latest.map(p => `
            <div class="p-3 bg-white border border-[#EAE4DF] rounded-2xl space-y-1">
                <div class="flex items-center justify-between text-xs">
                    <span class="font-bold text-[#202124]">${escapeHtml(p.authorName)}</span>
                    <span class="text-[#8E8A85] text-[10px]">${escapeHtml(p.timeAgo)}</span>
                </div>
                <p class="text-xs text-[#5A5550] line-clamp-2">${escapeHtml(p.content)}</p>
            </div>
        `).join('');
    }

    function renderUrgentPreview() {
        const container = document.getElementById('urgent-community-posts-list');
        if (!container) return;
        const deadlinePosts = posts.filter(p => (p.tags || []).some(t => t.label.toLowerCase().includes('deadline'))).slice(0, 2);
        container.innerHTML = deadlinePosts.map(p => `
            <div class="p-3 bg-white border border-[#EAE4DF] rounded-2xl space-y-1">
                <span class="font-bold text-xs text-[#202124]">${escapeHtml(p.authorName)}</span>
                <p class="text-xs text-[#5A5550] line-clamp-2">${escapeHtml(p.content)}</p>
            </div>
        `).join('');
    }

    function renderRecoveryPreview() {
        const container = document.getElementById('recovery-community-posts-list');
        if (!container) return;
        const mentalPosts = posts.filter(p => (p.tags || []).some(t => t.label.toLowerCase().includes('mental'))).slice(0, 2);
        container.innerHTML = mentalPosts.map(p => `
            <div class="p-3 bg-white border border-[#EAE4DF] rounded-2xl space-y-1">
                <span class="font-bold text-xs text-[#202124]">${escapeHtml(p.authorName)}</span>
                <p class="text-xs text-[#5A5550] line-clamp-2">${escapeHtml(p.content)}</p>
            </div>
        `).join('');
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

    // Public API
    return {
        init,
        selectTab,
        handleReturnNavigation,
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
        // Posts (Requirement 5)
        navigateToPostsFeed,
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
        openCommunityModal,
        closeCommunityModal
    };
})();
'''

# Convert line endings to CRLF for communityPosts.js
community_js_crlf = community_js_content.replace('\r\n', '\n').replace('\n', '\r\n')
with open('communityPosts.js', 'wb') as f:
    f.write(community_js_crlf.encode('utf-8'))
print("1. Successfully updated communityPosts.js (CRLF).")

# ==============================================================================
# 2. UPDATE index.html
# ==============================================================================
with open('index.html', 'r', encoding='utf-8') as f:
    index_content = f.read()

# Replace <section id="screen-community">...</section>
new_screen_community = r'''<section id="screen-community" class="screen-container hidden space-y-6 bg-[#FEFAF4] -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8 py-6 sm:py-8 min-h-[calc(100vh-140px)]">
            <!-- Two-Column Layout (Desktop Sidebar + Content Area) -->
            <div class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                
                <!-- Left Sidebar Navigation -->
                <aside class="lg:col-span-3 xl:col-span-3 w-full">
                    <!-- Return Home Navigation Button (Typography reduced to 12-13px) -->
                    <div class="mb-5">
                        <button type="button" id="btn-community-back" onclick="window.TempoCommunity.handleReturnNavigation()" 
                                class="inline-flex items-center space-x-1.5 text-[12px] sm:text-[13px] font-bold text-[#5A5550] hover:text-[#DE8662] transition cursor-pointer">
                            <span class="text-base">←</span>
                            <span id="community-back-label">Return Home</span>
                        </button>
                    </div>

                    <!-- Mobile Horizontal Tab Strip (shown on mobile, hidden on lg) -->
                    <div class="lg:hidden flex items-center space-x-1.5 overflow-x-auto pb-4 scrollbar-none" role="tablist">
                        <button type="button" role="tab" data-community-tab="announcement" onclick="window.TempoCommunity.selectTab('announcement')" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-bold transition whitespace-nowrap bg-[#F7ECE1] text-[#DE8662]">
                            Announcement
                        </button>
                        <button type="button" role="tab" data-community-tab="tips" onclick="window.TempoCommunity.selectTab('tips')" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Tips
                        </button>
                        <button type="button" role="tab" data-community-tab="learn" onclick="window.TempoCommunity.selectTab('learn')" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Learn
                        </button>
                        <button type="button" role="tab" data-community-tab="posts" onclick="window.TempoCommunity.navigateToPostsFeed()" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Posts
                        </button>
                        <button type="button" role="tab" data-community-tab="messages" onclick="window.TempoCommunity.selectTab('messages')" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Direct Message
                        </button>
                    </div>

                    <!-- Desktop Vertical Tab Navigation (Typography reduced to 14-15px) -->
                    <nav class="hidden lg:flex flex-col space-y-1.5" role="tablist" id="community-sidebar-nav">
                        <button type="button" role="tab" data-community-tab="announcement" onclick="window.TempoCommunity.selectTab('announcement')" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer bg-[#F7ECE1] text-[#DE8662]">
                            Announcement
                        </button>

                        <button type="button" role="tab" data-community-tab="tips" onclick="window.TempoCommunity.selectTab('tips')" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Tips
                        </button>

                        <button type="button" role="tab" data-community-tab="learn" onclick="window.TempoCommunity.selectTab('learn')" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Learn
                        </button>

                        <!-- Requirement 5: Posts button always navigates to main Posts newsfeed -->
                        <button type="button" role="tab" data-community-tab="posts" onclick="window.TempoCommunity.navigateToPostsFeed()" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Posts
                        </button>

                        <button type="button" role="tab" data-community-tab="messages" onclick="window.TempoCommunity.selectTab('messages')" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Direct Message
                        </button>
                    </nav>

                    <!-- Optional Admin Button if admin -->
                    <div class="pt-5 hidden" id="admin-actions-container">
                        <button type="button" id="btn-admin-new-announcement" onclick="window.TempoCommunity.openNewAnnouncementModal()" 
                                class="hidden px-3.5 py-1.5 rounded-xl bg-[#DE8662] hover:bg-[#C9724F] text-white font-bold text-xs flex items-center space-x-1.5 shadow-xs transition cursor-pointer">
                            <span>📢</span>
                            <span>+ New Announcement</span>
                        </button>
                    </div>
                </aside>

                <!-- Right Main Content Area -->
                <main class="lg:col-span-9 xl:col-span-9 w-full min-w-0">
                    
                    <!-- PANEL 1: ANNOUNCEMENT (Reference 1) -->
                    <div id="community-panel-announcement" class="community-panel space-y-5">
                        <div id="community-announcements-list" class="space-y-5 flex flex-col">
                            <!-- Populated dynamically by communityPosts.js -->
                        </div>

                        <!-- Empty State -->
                        <div id="community-announcements-empty" class="hidden text-center py-12 px-4 bg-white border border-[#ECA689] rounded-3xl space-y-2.5">
                            <h3 class="font-heading text-sm sm:text-base font-bold text-[#4A4541]">No announcements at this time</h3>
                            <p class="text-xs text-[#6E6964]">Check back soon for system updates and new feature releases.</p>
                        </div>
                    </div>

                    <!-- PANEL 2: TIPS (SOLVE) (Reference 2) -->
                    <div id="community-panel-tips" class="community-panel space-y-5 hidden">
                        <!-- Stable Flex Search Bar (Zero Overlap, Requirement 1) -->
                        <div class="relative flex items-center w-full bg-[#F2EAE3] rounded-full px-4 py-2.5 space-x-2.5 transition shadow-2xs">
                            <svg class="w-4 h-4 text-[#736F68] shrink-0 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                            <input type="text" id="tips-search-input" 
                                   oninput="window.TempoCommunity.handleTipsSearch(this.value)"
                                   placeholder="Search..." 
                                   class="w-full bg-transparent border-none text-[13px] text-[#2D2A26] placeholder-[#8E8A85] focus:outline-none p-0 leading-normal">
                            <button type="button" id="btn-clear-tips-search" onclick="window.TempoCommunity.clearTipsSearch()" 
                                    class="hidden text-[#8E8A85] hover:text-[#202124] text-xs px-1 cursor-pointer" title="Clear">✕</button>
                        </div>

                        <!-- Tips Cards Grid (2 columns, Reference 2) -->
                        <div id="tips-cards-grid" class="grid grid-cols-1 md:grid-cols-2 gap-5">
                            <!-- Populated dynamically by communityPosts.js -->
                        </div>

                        <!-- Empty State -->
                        <div id="tips-empty-state" class="hidden text-center py-10 px-4 bg-white border border-[#ECA689] rounded-3xl space-y-2.5">
                            <h3 class="font-heading text-sm font-bold text-[#4A4541]">No matching solutions found</h3>
                            <p class="text-xs text-[#6E6964]">Try searching with different terms.</p>
                            <button type="button" onclick="window.TempoCommunity.clearTipsSearch();" 
                                    class="px-3.5 py-1.5 rounded-xl bg-[#F7ECE1] text-[#DE8662] font-bold text-xs cursor-pointer">
                                Reset Search
                            </button>
                        </div>
                    </div>

                    <!-- PANEL 3: LEARN (Reference 3) -->
                    <div id="community-panel-learn" class="community-panel space-y-5 hidden">
                        <!-- Stable Flex Search Bar (Zero Overlap, Requirement 1) -->
                        <div class="relative flex items-center w-full bg-[#F2EAE3] rounded-full px-4 py-2.5 space-x-2.5 transition shadow-2xs">
                            <svg class="w-4 h-4 text-[#736F68] shrink-0 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                            <input type="text" id="learn-search-input" 
                                   oninput="window.TempoCommunity.handleLearnSearch(this.value)"
                                   placeholder="Search..." 
                                   class="w-full bg-transparent border-none text-[13px] text-[#2D2A26] placeholder-[#8E8A85] focus:outline-none p-0 leading-normal">
                            <button type="button" id="btn-clear-learn-search" onclick="window.TempoCommunity.clearLearnSearch()" 
                                    class="hidden text-[#8E8A85] hover:text-[#202124] text-xs px-1 cursor-pointer" title="Clear">✕</button>
                        </div>

                        <!-- Learn Cards Stacked (Reference 3) -->
                        <div id="learn-cards-grid" class="space-y-5 flex flex-col">
                            <!-- Populated dynamically by communityPosts.js -->
                        </div>

                        <!-- Empty State -->
                        <div id="learn-empty-state" class="hidden text-center py-10 px-4 bg-white border border-[#ECA689] rounded-3xl space-y-2.5">
                            <h3 class="font-heading text-sm font-bold text-[#4A4541]">No educational topics found</h3>
                            <p class="text-xs text-[#6E6964]">Try searching with a broader keyword or clearing your search.</p>
                            <button type="button" onclick="window.TempoCommunity.clearLearnSearch();" 
                                    class="px-3.5 py-1.5 rounded-xl bg-[#F7ECE1] text-[#DE8662] font-bold text-xs cursor-pointer">
                                Reset Search
                            </button>
                        </div>
                    </div>

                    <!-- PANEL 4: POSTS (Reference 4) -->
                    <div id="community-panel-posts" class="community-panel space-y-5 hidden">
                        <!-- Top Action Bar (Reference 4) -->
                        <div class="flex items-center space-x-2.5">
                            <!-- New Post Button -->
                            <button type="button" onclick="window.TempoCommunity.openCreatePostModal()" 
                                    class="bg-[#DCE7EB] hover:bg-[#CAD9DF] text-[#2D2A26] px-4 py-2 rounded-full font-bold text-xs transition shadow-2xs cursor-pointer flex items-center space-x-1.5 shrink-0">
                                <span>New post</span>
                            </button>

                            <!-- Stable Flex Search Input (Zero Overlap, Requirement 1) -->
                            <div class="relative flex items-center flex-1 bg-[#F2EAE3] rounded-full px-3.5 py-2 space-x-2.5 transition shadow-2xs">
                                <svg class="w-3.5 h-3.5 text-[#736F68] shrink-0 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                                <input type="text" id="posts-search-input" 
                                       oninput="window.TempoCommunity.handlePostsSearch(this.value)"
                                       placeholder="Search..." 
                                       class="w-full bg-transparent border-none text-[13px] text-[#2D2A26] placeholder-[#8E8A85] focus:outline-none p-0 leading-normal">
                            </div>

                            <!-- Your Posts Button -->
                            <button type="button" onclick="window.TempoCommunity.filterMyPosts()" 
                                    class="bg-[#DFB59F] hover:bg-[#D4A38A] text-[#2D2A26] px-3.5 py-2 rounded-full font-bold text-xs transition shadow-2xs cursor-pointer shrink-0">
                                <span>Your posts</span>
                            </button>

                            <!-- Bell Notifications Button -->
                            <button type="button" onclick="if(window.TempoApp) window.TempoApp.showToast('No new notifications');" 
                                    class="bg-[#F3DCD0] hover:bg-[#E9CDBC] text-[#5A5550] p-2 rounded-full transition shadow-2xs cursor-pointer shrink-0" title="Notifications">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                                </svg>
                            </button>

                            <!-- Bookmark Button -->
                            <button type="button" onclick="window.TempoCommunity.filterBookmarkedPosts()" 
                                    class="bg-[#F3DCD0] hover:bg-[#E9CDBC] text-[#5A5550] p-2 rounded-full transition shadow-2xs cursor-pointer shrink-0" title="Bookmarks">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                                </svg>
                            </button>
                        </div>

                        <!-- Posts Feed List (Reference 4) -->
                        <div id="community-feed-posts-list" class="space-y-5">
                            <!-- Populated dynamically by communityPosts.js -->
                        </div>

                        <!-- Empty State -->
                        <div id="community-posts-empty" class="hidden text-center py-10 px-4 bg-white border border-[#4A4541] rounded-3xl space-y-2.5">
                            <h3 class="font-heading text-sm font-bold text-[#4A4541]">No posts found</h3>
                            <p class="text-xs text-[#6E6964]">Be the first to share your thoughts or questions.</p>
                        </div>
                    </div>

                    <!-- PANEL 5: DIRECT MESSAGE (Reference 5 & Requirements 3 & 4) -->
                    <div id="community-panel-messages" class="community-panel space-y-5 hidden">
                        <!-- Guest Unauthenticated View -->
                        <div id="community-dm-guest-view" class="p-8 sm:p-12 text-center bg-white border border-[#EAE4DF] rounded-3xl space-y-4 max-w-xl mx-auto shadow-xs hidden">
                            <div class="w-12 h-12 rounded-2xl bg-[#F7ECE1] text-[#DE8662] flex items-center justify-center mx-auto text-xl font-bold">
                                ✉️
                            </div>
                            <div class="space-y-1.5">
                                <h3 class="font-heading text-base font-bold text-[#202124]">Sign in for Direct Mentorship</h3>
                                <p class="text-xs text-[#6F6B68] leading-relaxed">
                                    Direct messaging allows private, confidential conversations between you and mentors.
                                </p>
                            </div>
                            <div>
                                <button type="button" 
                                        onclick="if(window.TempoAuth && typeof window.TempoAuth.openSignInModal === 'function') window.TempoAuth.openSignInModal();"
                                        class="bg-[#DFB59F] text-white px-5 py-2 rounded-full font-bold text-xs shadow-xs transition cursor-pointer">
                                    Sign In to Access Messages
                                </button>
                            </div>
                        </div>

                        <!-- Unified Direct Message Card -->
                        <div id="community-dm-auth-view" class="bg-white border border-[#EAE4DF] rounded-3xl overflow-hidden shadow-xs grid grid-cols-1 md:grid-cols-12 min-h-[580px]">
                            
                            <!-- Left Column: Conversations List -->
                            <div id="dm-conversations-column" class="md:col-span-5 lg:col-span-5 border-r border-[#EAE4DF] flex flex-col bg-white">
                                <!-- Search & Chat Requests Action Icon (Requirement 4: exact supplied symbol) -->
                                <div class="p-3.5 border-b border-[#EAE4DF] flex items-center space-x-2">
                                    <!-- Stable Flex Search Input (Zero Overlap) -->
                                    <div class="relative flex items-center flex-1 bg-[#F2EAE3] rounded-full px-3 py-1.5 space-x-2 transition">
                                        <svg class="w-3.5 h-3.5 text-[#736F68] shrink-0 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                        </svg>
                                        <input type="text" id="dm-search-conversations" 
                                               oninput="window.TempoCommunity.handleDMSearch(this.value)"
                                               placeholder="Search..." 
                                               class="w-full bg-transparent border-none text-[12px] text-[#2D2A26] placeholder-[#8E8A85] focus:outline-none p-0 leading-normal">
                                    </div>
                                    <!-- Exact Chat Requests Symbol Asset Button -->
                                    <button type="button" id="btn-dm-chat-requests" onclick="window.TempoCommunity.openChatRequests()" 
                                            class="relative p-2 rounded-full hover:bg-stone-100 transition cursor-pointer shrink-0" 
                                            title="Chat Requests">
                                        <img src="assets/chat_requests_icon.png" alt="Chat Requests" class="w-4 h-4 object-contain">
                                        <span id="badge-chat-requests-count" class="hidden absolute -top-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-[#E04B38] text-white text-[9px] font-bold flex items-center justify-center">0</span>
                                    </button>
                                    <button type="button" onclick="if(window.TempoApp) window.TempoApp.showToast('Create Group');" class="p-2 rounded-full hover:bg-stone-100 text-[#5A5550] text-sm cursor-pointer shrink-0" title="New Group">👥</button>
                                </div>

                                <!-- Conversations Scrollable List (Requirement 3: Empty state when no conversations) -->
                                <div id="dm-conversations-list" class="flex-1 overflow-y-auto p-2.5 space-y-1 max-h-[500px]">
                                    <!-- Populated dynamically by communityPosts.js -->
                                </div>
                            </div>

                            <!-- Right Column: Active Chat Thread (Requirement 3: Empty state when no selected conv) -->
                            <div id="dm-chat-column" class="md:col-span-7 lg:col-span-7 flex flex-col bg-[#FAF8F5] hidden md:flex">
                                <!-- Chat Header -->
                                <div class="p-3.5 border-b border-[#EAE4DF] bg-white flex items-center justify-between">
                                    <div class="flex items-center space-x-2.5">
                                        <button type="button" id="btn-dm-mobile-back" onclick="window.TempoCommunity.mobileToggleConversation(false)" 
                                                class="md:hidden text-[#736F68] hover:text-[#202124] p-1 font-bold text-xs">
                                            ← Back
                                        </button>
                                        <img id="dm-active-avatar" src="assets/tempo-logo.png" 
                                             alt="Avatar" class="w-8 h-8 rounded-full object-cover border border-stone-200">
                                        <div>
                                            <h4 id="dm-active-name" class="text-xs sm:text-[13px] font-bold text-[#202124]">Direct Messages</h4>
                                            <p id="dm-active-role" class="text-[10px] text-[#8E8A85]">Select a conversation to start messaging</p>
                                        </div>
                                    </div>
                                </div>

                                <!-- Messages Container -->
                                <div id="dm-messages-container" class="flex-1 p-4 sm:p-5 overflow-y-auto space-y-3.5 max-h-[420px]">
                                    <!-- Populated dynamically by communityPosts.js -->
                                </div>

                                <!-- Message Input Row -->
                                <div class="p-3.5 bg-white border-t border-[#EAE4DF]">
                                    <form id="dm-message-form" onsubmit="window.TempoCommunity.handleSendMessage(event)" class="flex items-center space-x-2">
                                        <button type="button" onclick="if(window.TempoApp) window.TempoApp.showToast('Attach media');" 
                                                class="w-8 h-8 rounded-full bg-[#F2EAE3] hover:bg-[#EAE1D9] text-[#5A5550] flex items-center justify-center text-base font-bold shrink-0 cursor-pointer">+</button>
                                        <input type="text" id="dm-message-input" 
                                               placeholder="Type a message..." 
                                               class="flex-1 px-3.5 py-2 text-xs sm:text-[12.5px] bg-[#F2EAE3] border-none rounded-full text-[#2D2A26] placeholder-[#8E8A85] focus:outline-none focus:ring-1 focus:ring-[#DE8662]">
                                        <button type="submit" id="btn-dm-send" 
                                                class="w-8 h-8 rounded-full bg-[#DFB59F] hover:bg-[#D4A38A] text-white flex items-center justify-center text-xs font-bold shrink-0 shadow-2xs cursor-pointer">
                                            ➤
                                        </button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>

                </main>
            </div>
        </section>'''

# Match and replace #screen-community
pattern = r'<section id="screen-community"[\s\S]*?</section>'
index_content = re.sub(pattern, new_screen_community, index_content, count=1)

# Check and insert #modal-chat-requests if not already present
if 'id="modal-chat-requests"' not in index_content:
    chat_requests_modal = r'''
    <!-- 4e. CHAT REQUESTS MODAL (Requirement 4) -->
    <div id="modal-chat-requests" class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-3 sm:p-6 overflow-y-auto hidden">
        <div class="tempo-card max-w-md w-full max-h-[85vh] overflow-y-auto bg-white rounded-3xl p-5 sm:p-6 space-y-4 relative shadow-2xl">
            <div class="flex items-center justify-between pb-3 border-b border-gray-100">
                <div class="flex items-center space-x-2">
                    <img src="assets/chat_requests_icon.png" alt="Chat Requests" class="w-4 h-4 object-contain">
                    <h3 class="font-heading text-sm sm:text-base font-bold text-[#202124]">Chat Requests</h3>
                </div>
                <button type="button" onclick="window.TempoCommunity.closeChatRequests()" class="text-gray-400 hover:text-gray-700 p-1 rounded-lg text-base transition cursor-pointer">✕</button>
            </div>

            <!-- Requests List Container -->
            <div id="chat-requests-list" class="space-y-2.5">
                <!-- Populated dynamically by communityPosts.js -->
            </div>

            <!-- Empty State (Requirement 4) -->
            <div id="chat-requests-empty" class="hidden py-8 text-center space-y-2">
                <div class="w-9 h-9 rounded-full bg-[#F7ECE1] text-[#DE8662] flex items-center justify-center mx-auto text-base">
                    ✉️
                </div>
                <p class="text-xs font-bold text-[#202124]">No pending chat requests</p>
                <p class="text-[11px] text-[#8E8A85] leading-relaxed max-w-xs mx-auto">When another student or mentor sends you a direct chat request, it will appear here.</p>
            </div>

            <div class="pt-2.5 border-t border-gray-100 flex items-center justify-end">
                <button type="button" onclick="window.TempoCommunity.closeChatRequests()" 
                        class="px-3.5 py-1.5 rounded-xl text-xs font-semibold text-[#736F68] hover:bg-stone-100 transition cursor-pointer">
                    Close
                </button>
            </div>
        </div>
    </div>
'''
    pos = index_content.find('id="modal-create-post"')
    if pos != -1:
        # Find closing div of modal-create-post
        end_pos = index_content.find('</div>\n    </div>', pos)
        if end_pos != -1:
            insert_idx = end_pos + len('</div>\n    </div>')
            index_content = index_content[:insert_idx] + '\n' + chat_requests_modal + index_content[insert_idx:]
            print("Inserted modal-chat-requests after modal-create-post.")
        else:
            index_content += '\n' + chat_requests_modal
    else:
        index_content += '\n' + chat_requests_modal

# Write index.html with CRLF preservation
index_crlf = index_content.replace('\r\n', '\n').replace('\n', '\r\n')
with open('index.html', 'wb') as f:
    f.write(index_crlf.encode('utf-8'))
print("2. Successfully updated index.html (CRLF).")

# ==============================================================================
# 3. UPDATE app.js (LF PRESERVATION)
# ==============================================================================
with open('app.js', 'r', encoding='utf-8') as f:
    app_content = f.read()

# In app.js lines 244-247, ensure navigating to 'posts' uses window.TempoCommunity.navigateToPostsFeed()
old_app_block = r'''            // Select active category in TempoCommunity controller
            if (window.TempoCommunity && typeof window.TempoCommunity.selectTab === 'function') {
                window.TempoCommunity.selectTab(targetTab, false);
            }'''

new_app_block = r'''            // Select active category in TempoCommunity controller (Requirement 5: canonical posts navigation)
            if (window.TempoCommunity) {
                if (targetTab === 'posts' && typeof window.TempoCommunity.navigateToPostsFeed === 'function') {
                    window.TempoCommunity.navigateToPostsFeed();
                } else if (typeof window.TempoCommunity.selectTab === 'function') {
                    window.TempoCommunity.selectTab(targetTab, false);
                }
            }'''

if old_app_block in app_content:
    app_content = app_content.replace(old_app_block, new_app_block)
    print("3. Updated app.js to use navigateToPostsFeed for canonical posts navigation.")

# Write app.js with LF preservation
app_lf = app_content.replace('\r\n', '\n')
with open('app.js', 'wb') as f:
    f.write(app_lf.encode('utf-8'))
print("Successfully wrote app.js (LF).")

print("All updates applied cleanly!")
