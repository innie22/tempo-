# Python script to generate communityPosts.js with CRLF line endings
import os

content = r'''/**
 * Tempo Community Module
 * Unified Community Hub featuring five distinct categories:
 * 1. Announcement — Official system and product updates
 * 2. Tips (Solve) — Practical, actionable solutions for students
 * 3. Learn — Educational stress concepts and knowledge library
 * 4. Posts — Peer feed, discussions, anonymous sharing, likes, and bookmarks
 * 5. Direct Message — Private 1-on-1 mentorship & support conversations
 */

window.TempoCommunity = (function() {
    'use strict';

    // =========================================================================
    // 1. DATASETS & PERSISTENCE
    // =========================================================================

    // Official System & Product Announcements
    const INITIAL_ANNOUNCEMENTS = [
        {
            id: 'ann-1',
            title: 'New High-Definition Backgrounds & Ambient Audio in Focus Zone',
            summary: 'We have updated Focus Zone with 4 new ambient soundscapes and high-definition immersive backgrounds to help you maintain deep study focus.',
            content: 'Focus Zone now features calming nature and coffee shop environments with synchronized lo-fi audio, helping you minimize distractions during long study blocks. You can switch scenes anytime while your timer is running.',
            coverImage: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&h=450&q=80',
            publishedAt: 'Oct 24, 2026',
            author: 'Tempo Product Team',
            badge: 'Feature Launch',
            actionLabel: 'Try Focus Zone',
            actionRoute: 'focus-zone'
        },
        {
            id: 'ann-2',
            title: 'Standardized Clinical Assessments Launched in UCheck',
            summary: 'PHQ-9 (Depression), GAD-7 (Anxiety), and PAS (Academic Stress) are now live with confidential scoring and tailored guidance.',
            content: 'Tempo UCheck now offers evidence-based assessments including the PHQ-9, GAD-7, and Perception of Academic Stress scale. Each assessment gives you confidential, non-diagnostic insight into your current symptom levels along with relevant next steps within Tempo.',
            coverImage: 'https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&w=800&h=450&q=80',
            publishedAt: 'Oct 22, 2026',
            author: 'Tempo Wellbeing Advisory',
            badge: 'Clinical Tools',
            actionLabel: 'Explore Assessments',
            actionRoute: 'explore-mental-health-tests'
        },
        {
            id: 'ann-3',
            title: 'Enhanced Daily Self-Check & Stress Signal Alert System',
            summary: 'Configure persistent stress pattern alerts and supportive habit reminders directly in your Daily Self-Check.',
            content: 'You can now set custom consecutive-day thresholds for bodily stress signals (such as Tension or Trouble focusing) as well as supportive habit check-ins (such as daily walks or hydration). Tempo will gently alert you when a sustained pattern is detected.',
            coverImage: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&h=450&q=80',
            publishedAt: 'Oct 18, 2026',
            author: 'Tempo Clinical Team',
            badge: 'System Update',
            actionLabel: 'Check-in Now',
            actionRoute: 'stress-check'
        }
    ];

    // Peer Supportive Posts
    const INITIAL_POSTS = [
        {
            id: 'post-ref-1',
            authorName: 'FPT Bá khí',
            isAnonymous: false,
            avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=120&h=120&q=80',
            timeAgo: '2 hours ago',
            tags: [
                { label: 'mental health', bg: 'bg-[#E3E8EC]', text: 'text-[#4A5D6B]' },
                { label: 'Deadline', bg: 'bg-[#D4957D]', text: 'text-white' }
            ],
            tag: '#Deadline',
            tagColor: 'orange',
            content: "How to survive 4 projects in just 2 weeks without destroying my mental health? Urgent situation, please give me some tips. Thank you all.",
            likes: 29,
            commentsCount: 5,
            isLiked: false,
            isBookmarked: false,
            hasReplyPreview: false,
            replyAuthor: 'fess',
            replyAvatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=80&h=80&q=80',
            replyText: "Omg same here I'm dying with deadline...",
            subReplyAuthor: 'FPT Bá khí',
            subReplyAvatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=80&h=80&q=80',
            subReplyText: "Where can I find a solution with this? :<",
            comments: [
                { author: 'fess', time: '1h ago', text: "Omg same here I'm dying with deadline..." }
            ]
        },
        {
            id: 'post-ref-2',
            authorName: 'Temposocute',
            isAnonymous: false,
            avatar: 'assets/tempo-logo.png',
            timeAgo: '5 hours ago',
            tags: [
                { label: 'Focus zone', bg: 'bg-[#7C9985]', text: 'text-white' },
                { label: 'Background', bg: 'bg-[#FBF0DC]', text: 'text-[#8C6B37]' }
            ],
            tag: '#Focus',
            tagColor: 'orange',
            content: "Hello, we have updated more background for Focus Zone, check it out now!",
            thumbnails: [
                'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=120&h=80&q=80',
                'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=120&h=80&q=80',
                'https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=120&h=80&q=80',
                'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=120&h=80&q=80'
            ],
            likes: 58,
            commentsCount: 20,
            isLiked: false,
            isBookmarked: false,
            comments: []
        },
        {
            id: 'post-3',
            authorName: 'Anonymous',
            isAnonymous: true,
            avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&h=120&q=80',
            timeAgo: '1d ago',
            tag: '#Focus',
            tagColor: 'orange',
            content: "The 45m focus / 15m rest cycle actually stopped my 4-hour doom scroll spiral yesterday. Doing another session right now!",
            likes: 92,
            commentsCount: 11,
            isLiked: false,
            isBookmarked: false,
            comments: []
        },
        {
            id: 'post-4',
            authorName: 'Liam Chen',
            isAnonymous: false,
            avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=120&h=120&q=80',
            timeAgo: '1d ago',
            tag: '#Recovery',
            tagColor: 'orange',
            content: "Reminder to everyone studying late: drinking a glass of water and stepping outside for 3 minutes is not 'wasting time'. It's maintenance.",
            likes: 145,
            commentsCount: 32,
            isLiked: false,
            isBookmarked: false,
            comments: []
        }
    ];

    // Direct Messages Initial Conversations
    const INITIAL_CONVERSATIONS = [
        {
            id: 'conv-1',
            contactName: 'Dr. Elena Vance',
            contactRole: 'Campus Wellbeing Advisor',
            contactAvatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=120&h=120&q=80',
            isOnline: true,
            lastActive: 'Active now',
            unreadCount: 1,
            messages: [
                { id: 'm1', sender: 'them', text: 'Hi there! I saw you checked out the stress management strategies. How are you feeling today?', time: '10:30 AM' },
                { id: 'm2', sender: 'me', text: 'Hey Dr. Vance. Things are a bit overwhelming with the 3 finals coming up next week, but I am trying the 5-minute rule.', time: '10:32 AM' },
                { id: 'm3', sender: 'them', text: 'Starting with 5 minutes is a tremendous first step. Don’t hesitate to reach out if you need an official extension letter support.', time: '10:35 AM' }
            ]
        },
        {
            id: 'conv-2',
            contactName: 'Alex Rivera',
            contactRole: 'Senior Peer Mentor',
            contactAvatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=120&h=120&q=80',
            isOnline: false,
            lastActive: 'Active 20m ago',
            unreadCount: 0,
            messages: [
                { id: 'm201', sender: 'them', text: 'Hey! Just checking in on your project milestone. Remember to take a quick walk between pomodoros!', time: 'Yesterday' },
                { id: 'm202', sender: 'me', text: 'Thanks Alex! Just finished module 2. Stepping out for fresh air now.', time: 'Yesterday' }
            ]
        },
        {
            id: 'conv-3',
            contactName: 'Sarah Lin',
            contactRole: 'Peer Supporter · Sophomore',
            contactAvatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&h=120&q=80',
            isOnline: true,
            lastActive: 'Active now',
            unreadCount: 0,
            messages: [
                { id: 'm301', sender: 'them', text: 'Hi! Hope your study session is going smoothly. Let me know if you want to do a quiet co-study in Focus Zone!', time: '2 days ago' }
            ]
        }
    ];

    // State
    let announcements = [...INITIAL_ANNOUNCEMENTS];
    let posts = [...INITIAL_POSTS];
    let conversations = [...INITIAL_CONVERSATIONS];
    let activeTab = 'announcement';
    let currentTipsCategory = 'all';
    let currentTipsSearch = '';
    let currentLearnSearch = '';
    let currentPostsTag = 'all';
    let currentPostsSearch = '';
    let activeConvId = 'conv-1';
    let expandedPostComments = {}; // map postId -> boolean

    // Legacy modal compatibility
    let currentSection = 'feed';

    // =========================================================================
    // 2. INITIALIZATION
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
                if (Array.isArray(parsed) && parsed.length > 0) {
                    announcements = parsed;
                } else {
                    announcements = [...INITIAL_ANNOUNCEMENTS];
                    saveAnnouncements();
                }
            } else {
                announcements = [...INITIAL_ANNOUNCEMENTS];
                saveAnnouncements();
            }
        } catch (e) {
            announcements = [...INITIAL_ANNOUNCEMENTS];
        }
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
                        if (!INITIAL_POSTS.some(initP => initP.id === p.id)) {
                            posts.push(p);
                        }
                    });
                    savePosts();
                } else {
                    posts = [...INITIAL_POSTS];
                    savePosts();
                }
            } else {
                posts = [...INITIAL_POSTS];
                savePosts();
            }
        } catch (e) {
            posts = [...INITIAL_POSTS];
        }
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
                if (Array.isArray(parsed) && parsed.length > 0) {
                    conversations = parsed;
                } else {
                    conversations = [...INITIAL_CONVERSATIONS];
                    saveConversations();
                }
            } else {
                conversations = [...INITIAL_CONVERSATIONS];
                saveConversations();
            }
        } catch (e) {
            conversations = [...INITIAL_CONVERSATIONS];
        }
    }

    function saveConversations() {
        try {
            localStorage.setItem('tempo_direct_messages', JSON.stringify(conversations));
        } catch (e) {}
    }

    function isUserAdmin() {
        const profile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
        if (profile && (profile.role === 'admin' || profile.role === 'advisor')) {
            return true;
        }
        if (window.TempoApp && typeof window.TempoApp.getCurrentRole === 'function' && window.TempoApp.getCurrentRole() === 'admin') {
            return true;
        }
        return false;
    }

    // =========================================================================
    // 3. TAB SELECTION & SCREEN CONTROLLER
    // =========================================================================
    function selectTab(tabKey, updateHash = true) {
        const validTabs = ['announcement', 'tips', 'learn', 'posts', 'messages'];
        if (!validTabs.includes(tabKey)) {
            tabKey = 'announcement';
        }
        activeTab = tabKey;

        // Update URL hash
        if (updateHash) {
            const newHash = (tabKey === 'announcement') ? '#community' : `#community?tab=${tabKey}`;
            if (window.location.hash !== newHash) {
                try {
                    history.replaceState(null, '', newHash);
                } catch (e) {
                    window.location.hash = newHash;
                }
            }
        }

        // Update sidebar items active state
        document.querySelectorAll('.community-nav-item').forEach(btn => {
            const btnTab = btn.getAttribute('data-community-tab');
            if (btnTab === activeTab) {
                btn.className = 'community-nav-item w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs font-bold transition text-left cursor-pointer bg-[#FFE9DC] text-[#B83D08] shadow-2xs';
            } else {
                btn.className = 'community-nav-item w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs font-medium transition text-left cursor-pointer text-[#6F6B68] hover:bg-[#F8F6F4] hover:text-[#202124]';
            }
        });

        // Update mobile pill buttons
        document.querySelectorAll('.community-mobile-tab-btn').forEach(btn => {
            const btnTab = btn.getAttribute('data-community-tab');
            if (btnTab === activeTab) {
                btn.className = 'community-mobile-tab-btn px-4 py-2 rounded-full text-xs font-bold transition whitespace-nowrap bg-[#FF6B2C] text-white shadow-2xs';
            } else {
                btn.className = 'community-mobile-tab-btn px-4 py-2 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]';
            }
        });

        // Hide all panels, show active panel
        const panels = ['announcement', 'tips', 'learn', 'posts', 'messages'];
        panels.forEach(p => {
            const panelEl = document.getElementById(`community-panel-${p}`);
            if (panelEl) {
                if (p === activeTab) {
                    panelEl.classList.remove('hidden');
                } else {
                    panelEl.classList.add('hidden');
                }
            }
        });

        // Update return navigation button
        updateReturnButton();

        // Check and sync admin action controls
        syncAdminUI();

        // Render specific panel content
        if (activeTab === 'announcement') {
            renderAnnouncements();
        } else if (activeTab === 'tips') {
            renderTips();
        } else if (activeTab === 'learn') {
            renderLearn();
        } else if (activeTab === 'posts') {
            renderCommunityPosts();
        } else if (activeTab === 'messages') {
            renderMessagesView();
        }
    }

    function syncAdminUI() {
        const adminBtn = document.getElementById('btn-admin-new-announcement');
        if (adminBtn) {
            if (isUserAdmin()) {
                adminBtn.classList.remove('hidden');
            } else {
                adminBtn.classList.add('hidden');
            }
        }
    }

    function updateReturnButton() {
        const backBtn = document.getElementById('btn-community-back');
        const backLabel = document.getElementById('community-back-label');
        if (!backBtn || !backLabel) return;

        const currentMode = (window.TempoMode && typeof window.TempoMode.getActiveContext === 'function' && window.TempoMode.getActiveContext())
            || (window.TempoMode && typeof window.TempoMode.getMode === 'function' ? window.TempoMode.getMode() : null);
        const sourceContext = (window.TempoMode && typeof window.TempoMode.getSourceContext === 'function')
            ? window.TempoMode.getSourceContext()
            : (currentMode || 'today');

        if (sourceContext === 'recovery' || currentMode === 'recovery') {
            backLabel.textContent = 'Back to Recovery Mode';
        } else if (sourceContext === 'emergency' || currentMode === 'emergency') {
            backLabel.textContent = 'Back to Emergency Support';
        } else {
            backLabel.textContent = 'Back to Today';
        }
    }

    function handleReturnNavigation() {
        const currentMode = (window.TempoMode && typeof window.TempoMode.getActiveContext === 'function' && window.TempoMode.getActiveContext())
            || (window.TempoMode && typeof window.TempoMode.getMode === 'function' ? window.TempoMode.getMode() : null);
        const sourceContext = (window.TempoMode && typeof window.TempoMode.getSourceContext === 'function')
            ? window.TempoMode.getSourceContext()
            : (currentMode || 'today');

        if (sourceContext === 'recovery' || currentMode === 'recovery') {
            if (window.TempoMode && typeof window.TempoMode.navigateToActiveDashboard === 'function') {
                window.TempoMode.navigateToActiveDashboard();
            } else if (window.TempoApp) {
                window.TempoApp.navigateTo('recovery-mode');
            }
        } else if (sourceContext === 'emergency' || currentMode === 'emergency') {
            if (window.TempoApp) window.TempoApp.navigateTo('emergency');
        } else {
            if (window.TempoApp) window.TempoApp.navigateTo('today');
        }
    }

    // =========================================================================
    // 4. ANNOUNCEMENT CATEGORY
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

        // Update badge count
        const badgeEl = document.getElementById('badge-announcements-count');
        if (badgeEl) badgeEl.textContent = announcements.length;

        container.innerHTML = announcements.map(ann => {
            const hasAction = ann.actionLabel && ann.actionRoute;
            return `
                <div class="bg-white border border-[#EAE4DF] rounded-3xl overflow-hidden shadow-xs hover:border-[#FF6B2C]/40 transition flex flex-col justify-between" data-announcement-id="${escapeHtml(ann.id)}">
                    <!-- Cover Image -->
                    ${ann.coverImage ? `
                        <div class="w-full h-44 sm:h-52 overflow-hidden bg-stone-100 relative">
                            <img src="${escapeHtml(ann.coverImage)}" alt="${escapeHtml(ann.title)}" class="w-full h-full object-cover">
                            ${ann.badge ? `
                                <span class="absolute top-3.5 left-3.5 px-3 py-1 rounded-full text-[11px] font-extrabold bg-[#202124]/80 backdrop-blur-xs text-white">
                                    ${escapeHtml(ann.badge)}
                                </span>
                            ` : ''}
                        </div>
                    ` : ''}

                    <!-- Content Details -->
                    <div class="p-5 sm:p-6 space-y-3 flex-1 flex flex-col justify-between">
                        <div class="space-y-2">
                            <div class="flex items-center justify-between text-xs text-[#8E8A85]">
                                <span class="font-bold text-[#FF6B2C] uppercase tracking-wider text-[10px]">Official Announcement</span>
                                <span>${escapeHtml(ann.publishedAt || 'Recently')}</span>
                            </div>
                            <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124] leading-snug">
                                ${escapeHtml(ann.title)}
                            </h3>
                            <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                                ${escapeHtml(ann.summary || ann.content || '')}
                            </p>
                        </div>

                        <!-- Actions row -->
                        <div class="pt-3 border-t border-[#EAE4DF]/80 flex items-center justify-between gap-3 flex-wrap">
                            <button type="button" 
                                    onclick="window.TempoCommunity.openAnnouncementDetail('${ann.id}')"
                                    class="px-4 py-2 rounded-xl bg-[#FFE9DC] hover:bg-[#FFD9C2] text-[#B83D08] font-bold text-xs flex items-center space-x-1.5 transition cursor-pointer">
                                <span>See more</span>
                                <span>→</span>
                            </button>

                            ${hasAction ? `
                                <button type="button" 
                                        onclick="window.TempoCommunity.handleAnnouncementAction('${escapeHtml(ann.actionRoute)}')"
                                        class="px-4 py-2 rounded-xl bg-[#202124] hover:bg-[#363533] text-white font-bold text-xs flex items-center space-x-1.5 transition cursor-pointer">
                                    <span>${escapeHtml(ann.actionLabel)}</span>
                                    <span>↗</span>
                                </button>
                            ` : ''}
                        </div>
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
        const badgeEl = document.getElementById('announcement-modal-badge');
        const imageEl = document.getElementById('announcement-modal-image');
        const contentEl = document.getElementById('announcement-modal-content');
        const actionBtn = document.getElementById('announcement-modal-action');

        if (titleEl) titleEl.textContent = ann.title;
        if (metaEl) metaEl.textContent = `Published by ${ann.author || 'Tempo Team'} · ${ann.publishedAt || 'Recent'}`;
        if (badgeEl) badgeEl.textContent = ann.badge || 'Official System Update';

        if (imageEl) {
            if (ann.coverImage) {
                imageEl.src = ann.coverImage;
                imageEl.classList.remove('hidden');
            } else {
                imageEl.classList.add('hidden');
            }
        }

        if (contentEl) {
            contentEl.innerHTML = `
                <p class="font-medium text-sm text-[#202124] leading-relaxed">${escapeHtml(ann.summary || '')}</p>
                <div class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed pt-2 border-t border-[#EAE4DF]/70 space-y-2">
                    ${escapeHtml(ann.content || '')}
                </div>
            `;
        }

        if (actionBtn) {
            if (ann.actionLabel && ann.actionRoute) {
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
        if (route === 'focus-zone' && window.TempoFocusZone && typeof window.TempoFocusZone.openModal === 'function') {
            window.TempoFocusZone.openModal();
        } else if (route === 'explore-mental-health-tests' || route === 'ucheck') {
            if (window.TempoApp) window.TempoApp.navigateTo('explore-mental-health-tests');
        } else if (route === 'stress-check' || route === 'strack') {
            if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                window.TempoMode.openStrack('tool', { view: 'page' });
            } else if (window.TempoApp) {
                window.TempoApp.navigateTo('stress-check');
            }
        } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo(route);
        }
    }

    function openNewAnnouncementModal() {
        if (!isUserAdmin()) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Only authorized administrators can publish official announcements.");
            }
            return;
        }

        const modal = document.getElementById('modal-announcement-create');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
            const titleInput = document.getElementById('input-announcement-title');
            if (titleInput) titleInput.focus();
        }
    }

    function closeNewAnnouncementModal() {
        const modal = document.getElementById('modal-announcement-create');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    function handleCreateAnnouncement(e) {
        if (e) e.preventDefault();

        if (!isUserAdmin()) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Permission denied: Admin role required to create announcements.");
            }
            return;
        }

        const titleInput = document.getElementById('input-announcement-title');
        const summaryInput = document.getElementById('input-announcement-summary');
        const contentInput = document.getElementById('input-announcement-content');
        const imageInput = document.getElementById('input-announcement-image');
        const actionLabelInput = document.getElementById('input-announcement-action-label');
        const actionRouteSelect = document.getElementById('select-announcement-action-route');

        const title = titleInput?.value?.trim();
        const summary = summaryInput?.value?.trim();
        const content = contentInput?.value?.trim();

        if (!title || !summary) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Please provide both a title and short summary.");
            }
            return;
        }

        const newAnn = {
            id: 'ann-' + Date.now(),
            title,
            summary,
            content: content || summary,
            coverImage: imageInput?.value?.trim() || 'https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=800&h=450&q=80',
            publishedAt: 'Today',
            author: 'Tempo Administration',
            badge: 'Official Update',
            actionLabel: actionLabelInput?.value?.trim() || '',
            actionRoute: actionRouteSelect?.value || ''
        };

        announcements.unshift(newAnn);
        saveAnnouncements();
        renderAnnouncements();
        closeNewAnnouncementModal();

        // Clear form
        if (titleInput) titleInput.value = '';
        if (summaryInput) summaryInput.value = '';
        if (contentInput) contentInput.value = '';
        if (imageInput) imageInput.value = '';
        if (actionLabelInput) actionLabelInput.value = '';

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("Official announcement published successfully!");
        }
    }

    // =========================================================================
    // 5. TIPS (SOLVE) CATEGORY
    // =========================================================================
    function renderTips() {
        const container = document.getElementById('tips-cards-grid');
        const emptyState = document.getElementById('tips-empty-state');
        if (!container) return;

        // Retrieve raw situations from TempoLearnSolve
        let situations = [];
        if (window.TempoLearnSolve && typeof window.TempoLearnSolve.getSituations === 'function') {
            situations = window.TempoLearnSolve.getSituations();
        }

        // Apply Category filter
        let filtered = [...situations];
        if (currentTipsCategory !== 'all') {
            filtered = filtered.filter(s => s.category === currentTipsCategory);
        }

        // Apply Search filter
        if (currentTipsSearch) {
            const q = currentTipsSearch.toLowerCase();
            filtered = filtered.filter(s => {
                const titleMatch = (s.title || '').toLowerCase().includes(q);
                const descMatch = (s.shortDescription || '').toLowerCase().includes(q);
                const stepsMatch = (s.steps || []).some(step => (step.heading || '').toLowerCase().includes(q) || (step.detail || '').toLowerCase().includes(q));
                return titleMatch || descMatch || stepsMatch;
            });
        }

        if (filtered.length === 0) {
            container.innerHTML = '';
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }

        if (emptyState) emptyState.classList.add('hidden');

        container.innerHTML = filtered.map(item => {
            const stepCount = item.steps ? item.steps.length : 3;
            return `
                <div class="bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:p-6 shadow-xs hover:border-[#FF6B2C]/50 hover:shadow-sm transition flex flex-col justify-between space-y-4">
                    <div class="space-y-2.5">
                        <div class="flex items-center justify-between gap-2">
                            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-[#FFE9DC] text-[#B83D08] uppercase tracking-wider">
                                ${escapeHtml(item.badge || 'Solve · Situation')}
                            </span>
                            <span class="text-xl select-none">${item.icon || '💡'}</span>
                        </div>
                        <h3 class="font-heading text-base sm:text-lg font-bold text-[#202124] leading-snug">
                            ${escapeHtml(item.title)}
                        </h3>
                        <p class="text-xs text-[#6F6B68] leading-relaxed">
                            ${escapeHtml(item.shortDescription || '')}
                        </p>
                    </div>

                    <div class="pt-3 border-t border-[#EAE4DF]/80 flex items-center justify-between">
                        <span class="text-[11px] font-medium text-[#8E8A85]">
                            ${stepCount} concrete steps
                        </span>
                        <button type="button" 
                                onclick="window.TempoLearnSolve.openModal('${escapeHtml(item.id)}')"
                                class="px-3.5 py-1.5 rounded-xl bg-[#FFE9DC] hover:bg-[#FFD9C2] text-[#B83D08] font-bold text-xs flex items-center space-x-1 transition cursor-pointer">
                            <span>See more</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    function filterTipsCategory(catKey) {
        currentTipsCategory = catKey;
        // Update active pill UI
        document.querySelectorAll('.tips-category-pill').forEach(pill => {
            const pillKey = pill.getAttribute('data-tips-category');
            if (pillKey === catKey) {
                pill.className = 'tips-category-pill px-3.5 py-1.5 rounded-full text-xs font-bold transition whitespace-nowrap bg-[#FF6B2C] text-white shadow-2xs';
            } else {
                pill.className = 'tips-category-pill px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]';
            }
        });
        renderTips();
    }

    function handleTipsSearch(query) {
        currentTipsSearch = (query || '').trim();
        const clearBtn = document.getElementById('btn-clear-tips-search');
        if (clearBtn) {
            if (currentTipsSearch) clearBtn.classList.remove('hidden');
            else clearBtn.classList.add('hidden');
        }
        renderTips();
    }

    function clearTipsSearch() {
        const input = document.getElementById('tips-search-input');
        if (input) input.value = '';
        handleTipsSearch('');
    }

    // =========================================================================
    // 6. LEARN (KNOWLEDGE LIBRARY) CATEGORY
    // =========================================================================
    function renderLearn() {
        const container = document.getElementById('learn-cards-grid');
        const emptyState = document.getElementById('learn-empty-state');
        if (!container) return;

        let topics = [];
        if (window.TempoLearnSolve && typeof window.TempoLearnSolve.getTopics === 'function') {
            topics = window.TempoLearnSolve.getTopics();
        }

        let filtered = [...topics];
        if (currentLearnSearch) {
            const q = currentLearnSearch.toLowerCase();
            filtered = filtered.filter(t => {
                const titleMatch = (t.title || '').toLowerCase().includes(q);
                const descMatch = (t.shortDescription || '').toLowerCase().includes(q);
                const conceptMatch = (t.concept || '').toLowerCase().includes(q);
                return titleMatch || descMatch || conceptMatch;
            });
        }

        if (filtered.length === 0) {
            container.innerHTML = '';
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }

        if (emptyState) emptyState.classList.add('hidden');

        container.innerHTML = filtered.map(topic => {
            return `
                <div class="bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:p-6 shadow-xs hover:border-[#FF6B2C]/50 hover:shadow-sm transition flex flex-col justify-between space-y-4">
                    <div class="space-y-2.5">
                        <div class="flex items-center justify-between gap-2">
                            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-[#E6F4EA] text-[#137333] uppercase tracking-wider">
                                ${escapeHtml(topic.badge || 'Stress Education')}
                            </span>
                            <span class="text-xl select-none">${topic.icon || '🧠'}</span>
                        </div>
                        <h3 class="font-heading text-base sm:text-lg font-bold text-[#202124] leading-snug">
                            ${escapeHtml(topic.title)}
                        </h3>
                        <p class="text-xs text-[#6F6B68] leading-relaxed">
                            ${escapeHtml(topic.shortDescription || '')}
                        </p>
                    </div>

                    <div class="pt-3 border-t border-[#EAE4DF]/80 flex items-center justify-between">
                        <span class="text-[11px] font-medium text-[#8E8A85]">
                            Educational Guide
                        </span>
                        <button type="button" 
                                onclick="window.TempoLearnSolve.openModal('${escapeHtml(topic.id)}')"
                                class="px-3.5 py-1.5 rounded-xl bg-[#FFE9DC] hover:bg-[#FFD9C2] text-[#B83D08] font-bold text-xs flex items-center space-x-1 transition cursor-pointer">
                            <span>See more</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    function handleLearnSearch(query) {
        currentLearnSearch = (query || '').trim();
        const clearBtn = document.getElementById('btn-clear-learn-search');
        if (clearBtn) {
            if (currentLearnSearch) clearBtn.classList.remove('hidden');
            else clearBtn.classList.add('hidden');
        }
        renderLearn();
    }

    function clearLearnSearch() {
        const input = document.getElementById('learn-search-input');
        if (input) input.value = '';
        handleLearnSearch('');
    }

    // =========================================================================
    // 7. POSTS CATEGORY
    // =========================================================================
    function renderCommunityPosts() {
        const container = document.getElementById('community-feed-posts-list');
        const emptyState = document.getElementById('community-posts-empty');
        if (!container) return;

        let filtered = [...posts];

        // Tag filter
        if (currentPostsTag !== 'all') {
            filtered = filtered.filter(p => (p.tag || '').toLowerCase() === currentPostsTag.toLowerCase());
        }

        // Search filter
        if (currentPostsSearch) {
            const q = currentPostsSearch.toLowerCase();
            filtered = filtered.filter(p => {
                return (p.content || '').toLowerCase().includes(q) || (p.authorName || '').toLowerCase().includes(q);
            });
        }

        if (filtered.length === 0) {
            container.innerHTML = '';
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }

        if (emptyState) emptyState.classList.add('hidden');

        container.innerHTML = filtered.map(post => {
            const isExpanded = !!expandedPostComments[post.id];
            const authorInitial = (post.authorName || 'S').charAt(0).toUpperCase();
            const tagsHTML = (post.tags && post.tags.length > 0
                ? post.tags.map(t => `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${t.bg || 'bg-stone-100'} ${t.text || 'text-stone-700'}">${escapeHtml(t.label || t)}</span>`).join(' ')
                : (post.tag ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FFE9DC] text-[#B83D08]">${escapeHtml(post.tag)}</span>` : ''));

            return `
                <div class="bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:p-6 space-y-4 shadow-xs hover:border-[#D3CDC8] transition" data-post-id="${escapeHtml(post.id)}">
                    <!-- Post Header -->
                    <div class="flex items-center justify-between gap-3">
                        <div class="flex items-center space-x-3 min-w-0">
                            ${post.avatar ? `
                                <img src="${escapeHtml(post.avatar)}" alt="${escapeHtml(post.authorName || 'Student')}" 
                                     class="w-9 h-9 rounded-full object-cover border border-stone-200 shrink-0"
                                     onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='flex';">
                                <div class="w-9 h-9 rounded-full bg-[#FFE9DC] text-[#B83D08] items-center justify-center text-xs font-bold shrink-0 hidden">
                                    ${escapeHtml(authorInitial)}
                                </div>
                            ` : `
                                <div class="w-9 h-9 rounded-full bg-[#FFE9DC] text-[#B83D08] flex items-center justify-center text-xs font-bold shrink-0">
                                    ${escapeHtml(authorInitial)}
                                </div>
                            `}
                            <div class="min-w-0">
                                <div class="flex items-center space-x-2 flex-wrap">
                                    <span class="text-xs sm:text-sm font-bold text-[#202124]">${escapeHtml(post.authorName || 'Anonymous')}</span>
                                    ${post.isAnonymous ? '<span class="text-[10px] bg-stone-100 text-stone-600 px-1.5 py-0.5 rounded">Anonymous</span>' : ''}
                                    ${tagsHTML}
                                </div>
                                <div class="text-[10px] text-[#8E8A85]">
                                    <span>${escapeHtml(post.timeAgo || 'Recently')}</span>
                                </div>
                            </div>
                        </div>

                        <!-- Bookmark button -->
                        <button type="button" 
                                onclick="window.TempoCommunity.toggleBookmark('${post.id}')"
                                class="p-1.5 rounded-lg text-[#736F68] hover:text-[#FF6B2C] transition cursor-pointer shrink-0 ${post.isBookmarked ? 'text-[#FF6B2C]' : ''}"
                                title="${post.isBookmarked ? 'Remove bookmark' : 'Bookmark post'}">
                            <svg class="w-4 h-4" fill="${post.isBookmarked ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                            </svg>
                        </button>
                    </div>

                    <!-- Post Body -->
                    <div class="space-y-3">
                        <p class="text-xs sm:text-sm text-[#202124] leading-relaxed break-words">
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

                    <!-- Post Actions Bar -->
                    <div class="pt-3 border-t border-[#EAE4DF]/80 flex items-center justify-between text-xs text-[#736F68]">
                        <div class="flex items-center space-x-5">
                            <button type="button" 
                                    onclick="window.TempoCommunity.toggleLike('${post.id}')"
                                    class="flex items-center space-x-1.5 hover:text-[#FF6B2C] transition cursor-pointer ${post.isLiked ? 'text-[#FF6B2C] font-semibold' : ''}"
                                    title="Like">
                                <span class="text-sm">${post.isLiked ? '♥' : '♡'}</span>
                                <span class="text-xs">${post.likes || 0}</span>
                            </button>

                            <button type="button" 
                                    onclick="window.TempoCommunity.togglePostCommentsExpand('${post.id}')"
                                    class="flex items-center space-x-1.5 hover:text-[#202124] transition cursor-pointer"
                                    title="Comments">
                                <span class="text-sm">💬</span>
                                <span class="text-xs">${post.comments ? post.comments.length : (post.commentsCount || 0)} comments</span>
                            </button>
                        </div>

                        <button type="button" 
                                onclick="if(window.TempoApp) window.TempoApp.showToast('Link copied to clipboard');"
                                class="hover:text-[#202124] transition cursor-pointer flex items-center space-x-1"
                                title="Share">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                            </svg>
                            <span class="text-[11px]">Share</span>
                        </button>
                    </div>

                    <!-- Inline Comments Section (Toggleable) -->
                    ${isExpanded ? `
                        <div class="pt-3 border-t border-[#EAE4DF] space-y-3 bg-[#FAF8F5] -mx-5 sm:-mx-6 -mb-5 sm:-mb-6 p-5 sm:p-6 rounded-b-3xl">
                            <div class="space-y-2">
                                ${post.comments && post.comments.length > 0 ? post.comments.map(c => `
                                    <div class="text-xs p-2.5 rounded-xl bg-white border border-[#EAE4DF] space-y-1">
                                        <div class="flex items-center justify-between text-[#8E8A85] text-[10px]">
                                            <span class="font-bold text-[#202124]">${escapeHtml(c.author)}</span>
                                            <span>${escapeHtml(c.time || 'Recently')}</span>
                                        </div>
                                        <p class="text-[#42413F]">${escapeHtml(c.text)}</p>
                                    </div>
                                `).join('') : '<p class="text-xs text-[#8E8A85] italic">No replies yet. Share an encouraging note!</p>'}
                            </div>

                            <!-- Comment Input Form -->
                            <form onsubmit="window.TempoCommunity.handleInlineCommentSubmit(event, '${post.id}')" class="flex items-center space-x-2 pt-1">
                                <input type="text" 
                                       id="input-comment-${post.id}"
                                       placeholder="Add an encouraging reply..." 
                                       class="flex-1 px-3 py-2 text-xs bg-white border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#FF6B2C] focus:ring-1 focus:ring-[#FF6B2C]">
                                <button type="submit" class="btn-primary px-3 py-2 rounded-xl text-xs font-bold shrink-0">
                                    Reply
                                </button>
                            </form>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }

    function togglePostCommentsExpand(postId) {
        expandedPostComments[postId] = !expandedPostComments[postId];
        renderCommunityPosts();
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
        const author = profile?.full_name || 'Tempo Peer';

        post.comments.push({
            author,
            time: 'Just now',
            text
        });
        post.commentsCount = post.comments.length;
        savePosts();
        input.value = '';
        renderCommunityPosts();

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("Your supportive comment was posted!");
        }
    }

    function filterPostsTag(tag) {
        currentPostsTag = tag;
        document.querySelectorAll('.posts-tag-pill').forEach(pill => {
            const pillTag = pill.getAttribute('data-posts-tag');
            if (pillTag === tag) {
                pill.className = 'posts-tag-pill px-3 py-1.5 rounded-full text-xs font-bold transition whitespace-nowrap bg-[#FF6B2C] text-white shadow-2xs';
            } else {
                pill.className = 'posts-tag-pill px-3 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]';
            }
        });
        renderCommunityPosts();
    }

    function handlePostsSearch(query) {
        currentPostsSearch = (query || '').trim();
        renderCommunityPosts();
    }

    function handleCreateCommunityPost(e) {
        if (e) e.preventDefault();
        const textarea = document.getElementById('community-post-content');
        const tagSelect = document.getElementById('community-post-tag');
        const anonCheckbox = document.getElementById('community-post-anon');

        const content = textarea?.value?.trim();
        if (!content) return;

        const isAnon = anonCheckbox ? anonCheckbox.checked : true;
        const tag = tagSelect ? tagSelect.value : '#General';

        const profile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
        const authorName = isAnon ? 'Anonymous' : (profile?.full_name || 'Tempo Student');
        const avatar = isAnon 
            ? 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=120&h=120&q=80'
            : 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&h=120&q=80';

        const newPost = {
            id: 'post-' + Date.now(),
            authorName,
            isAnonymous: isAnon,
            avatar,
            timeAgo: 'Just now',
            tag,
            tagColor: 'orange',
            content,
            likes: 0,
            commentsCount: 0,
            isLiked: false,
            isBookmarked: false,
            comments: []
        };

        posts.unshift(newPost);
        savePosts();
        renderHomepagePreview();
        renderCommunityPosts();

        if (textarea) textarea.value = '';
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("Your supportive post was shared with the community!");
        }
    }

    // =========================================================================
    // 8. DIRECT MESSAGE CATEGORY
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
            filtered = filtered.filter(c => {
                return (c.contactName || '').toLowerCase().includes(q) || (c.contactRole || '').toLowerCase().includes(q);
            });
        }

        if (filtered.length === 0) {
            container.innerHTML = '<div class="p-6 text-center text-xs text-[#8E8A85]">No conversations found.</div>';
            return;
        }

        container.innerHTML = filtered.map(c => {
            const isActive = c.id === activeConvId;
            const lastMsg = c.messages && c.messages.length > 0 ? c.messages[c.messages.length - 1] : null;
            const lastSnippet = lastMsg ? lastMsg.text : 'No messages yet';
            const lastTime = lastMsg ? lastMsg.time : '';

            return `
                <div onclick="window.TempoCommunity.selectConversation('${c.id}')"
                     class="p-3.5 rounded-2xl cursor-pointer transition flex items-center space-x-3 ${isActive ? 'bg-[#FFE9DC] border border-[#FFD5C0]' : 'hover:bg-[#FAF8F5] border border-transparent'}">
                    <div class="relative shrink-0">
                        <img src="${escapeHtml(c.contactAvatar)}" alt="${escapeHtml(c.contactName)}" class="w-10 h-10 rounded-full object-cover border border-stone-200">
                        ${c.isOnline ? '<span class="w-3 h-3 rounded-full bg-emerald-500 border-2 border-white absolute bottom-0 right-0"></span>' : ''}
                    </div>
                    <div class="flex-1 min-w-0 space-y-0.5">
                        <div class="flex items-center justify-between">
                            <h4 class="text-xs font-bold text-[#202124] truncate">${escapeHtml(c.contactName)}</h4>
                            <span class="text-[10px] text-[#8E8A85] shrink-0">${escapeHtml(lastTime)}</span>
                        </div>
                        <p class="text-[11px] text-[#8E8A85] truncate font-medium">${escapeHtml(c.contactRole)}</p>
                        <p class="text-[11px] text-[#6F6B68] truncate leading-tight">${escapeHtml(lastSnippet)}</p>
                    </div>
                    ${c.unreadCount ? `<span class="px-1.5 py-0.5 rounded-full text-[10px] bg-[#FF6B2C] text-white font-bold shrink-0">${c.unreadCount}</span>` : ''}
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

        // On mobile, show chat view and hide list view
        mobileToggleConversation(true);
    }

    function renderActiveConversation() {
        const conv = conversations.find(c => c.id === activeConvId);
        if (!conv) return;

        const nameEl = document.getElementById('dm-active-name');
        const roleEl = document.getElementById('dm-active-role');
        const avatarEl = document.getElementById('dm-active-avatar');
        const statusEl = document.getElementById('dm-active-status');
        const messagesContainer = document.getElementById('dm-messages-container');

        if (nameEl) nameEl.textContent = conv.contactName;
        if (roleEl) roleEl.textContent = conv.contactRole;
        if (avatarEl) avatarEl.src = conv.contactAvatar;
        if (statusEl) {
            statusEl.textContent = conv.isOnline ? 'Online' : (conv.lastActive || 'Active recently');
            statusEl.className = conv.isOnline ? 'text-[11px] font-bold text-emerald-600' : 'text-[11px] text-[#8E8A85]';
        }

        if (messagesContainer) {
            if (!conv.messages || conv.messages.length === 0) {
                messagesContainer.innerHTML = `
                    <div class="py-12 text-center text-xs text-[#8E8A85] space-y-2">
                        <p>No messages in this conversation yet.</p>
                        <p class="text-[11px]">Send a friendly greeting to start your conversation.</p>
                    </div>
                `;
            } else {
                messagesContainer.innerHTML = conv.messages.map(m => {
                    const isMe = m.sender === 'me';
                    return `
                        <div class="flex flex-col ${isMe ? 'items-end' : 'items-start'} space-y-1">
                            <div class="max-w-[78%] px-4 py-2.5 rounded-2xl text-xs sm:text-sm leading-relaxed ${isMe ? 'bg-[#FF6B2C] text-white rounded-br-xs' : 'bg-white border border-[#EAE4DF] text-[#202124] rounded-bl-xs shadow-2xs'}">
                                ${escapeHtml(m.text)}
                            </div>
                            <span class="text-[10px] text-[#8E8A85] px-1">${escapeHtml(m.time || '')}</span>
                        </div>
                    `;
                }).join('');
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
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
            text,
            time: 'Just now'
        });

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
    // 9. HOMEPAGE & PREVIEWS (PRESERVED)
    // =========================================================================
    function renderPostCardHTML(post, options = {}) {
        if (!post) return '';

        const authorInitial = (post.authorName || 'S').charAt(0).toUpperCase();
        const subtitleText = post.context || (post.university ? `${post.university} · ${post.timeAgo || 'Recently'}` : (post.timeAgo || 'Recently'));

        const tagsHTML = (post.tags && post.tags.length > 0
            ? post.tags.map(t => `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${t.bg || 'bg-stone-100'} ${t.text || 'text-stone-700'}">${escapeHtml(t.label || t)}</span>`).join(' ')
            : (post.tag ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FFE9DC] text-[#B83D08]">${escapeHtml(post.tag)}</span>` : '')) + (post.tag ? ` <span class="sr-only">${escapeHtml(post.tag)}</span>` : '');

        const thumbnailsHTML = post.thumbnails && post.thumbnails.length > 0
            ? `
                <div class="grid grid-cols-4 gap-2 pt-1">
                    ${post.thumbnails.map(img => `
                        <div class="aspect-4/3 rounded-xl overflow-hidden bg-stone-100 border border-stone-200">
                            <img src="${img}" alt="Preview" class="w-full h-full object-cover">
                        </div>
                    `).join('')}
                </div>
            `
            : '';

        return `
            <div class="p-3.5 sm:p-4 bg-[#F6F0EB] border border-[#42413F] rounded-2xl space-y-2.5 transition flex flex-col justify-between" data-post-id="${post.id}">
                <div class="flex items-center justify-between gap-2">
                    <div class="flex items-center space-x-2.5 min-w-0">
                        ${post.avatar ? `
                            <img src="${escapeHtml(post.avatar)}" alt="${escapeHtml(post.authorName || 'Student')}" 
                                 class="w-8 h-8 rounded-full object-cover border border-stone-200 shrink-0"
                                 onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='flex';">
                            <div class="w-8 h-8 rounded-full bg-[#FFE9DC] text-[#B83D08] items-center justify-center text-xs font-bold shrink-0 hidden">
                                ${escapeHtml(authorInitial)}
                            </div>
                        ` : `
                            <div class="w-8 h-8 rounded-full bg-[#FFE9DC] text-[#B83D08] flex items-center justify-center text-xs font-bold shrink-0">
                                ${escapeHtml(authorInitial)}
                            </div>
                        `}
                        <div class="min-w-0">
                            <div class="flex items-center space-x-1.5 flex-wrap">
                                <span class="text-xs font-bold text-[#202124]">${escapeHtml(post.authorName || 'Anonymous')}</span>
                                ${tagsHTML}
                            </div>
                            <div class="text-[10px] text-[#8E8A85]">
                                <span>${escapeHtml(subtitleText)}</span>
                            </div>
                        </div>
                    </div>
                    <button type="button" 
                            onclick="window.TempoCommunity.toggleBookmark('${post.id}')" 
                            class="hover:text-[#D99E87] transition cursor-pointer p-1 text-[#736F68] shrink-0 ${post.isBookmarked ? 'text-[#D99E87]' : ''}" 
                            title="${post.isBookmarked ? 'Remove bookmark' : 'Bookmark post'}">
                        <svg class="w-4 h-4" fill="${post.isBookmarked ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                        </svg>
                    </button>
                </div>

                <div class="space-y-2 flex-1">
                    <p class="text-xs text-[#202124] leading-relaxed break-words cursor-pointer" onclick="window.TempoCommunity.openPostComments('${post.id}')">
                        ${escapeHtml(post.content)}
                    </p>
                    ${thumbnailsHTML}
                </div>

                <div class="pt-2 border-t border-[#EAE4DF] flex items-center justify-between text-xs text-[#736F68]">
                    <div class="flex items-center space-x-4">
                        <button type="button" 
                                onclick="window.TempoCommunity.toggleLike('${post.id}')" 
                                class="flex items-center space-x-1 hover:text-[#D99E87] transition cursor-pointer ${post.isLiked ? 'text-[#D99E87] font-semibold' : ''}"
                                title="Like">
                            <svg class="w-3.5 h-3.5 ${post.isLiked ? 'fill-current text-[#D99E87]' : 'none text-[#736F68]'}" fill="${post.isLiked ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                            </svg>
                            <span class="text-[11px] font-medium">${post.likes || 0}</span>
                        </button>
                        <button type="button" 
                                onclick="window.TempoCommunity.openPostComments('${post.id}')" 
                                class="flex items-center space-x-1 hover:text-[#202124] text-[#736F68] transition cursor-pointer"
                                title="Comments">
                            <svg class="w-3.5 h-3.5 text-[#736F68]" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                            </svg>
                            <span class="text-[11px] font-medium">${post.commentsCount || (post.comments ? post.comments.length : 0)}</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function renderUrgentPreview() {
        const container = document.getElementById('urgent-community-posts-list');
        if (!container) return;
        const previewPosts = posts.slice(0, 2);
        container.innerHTML = previewPosts.map(p => renderPostCardHTML(p)).join('');
    }

    function renderRecoveryPreview() {
        const container = document.getElementById('recovery-community-posts-list');
        if (!container) return;
        let previewPosts = posts.filter(p => p.tag === '#Recovery' || p.tag === '#MentalHealth');
        if (previewPosts.length < 2) {
            previewPosts = posts.slice(0, 2);
        } else {
            previewPosts = previewPosts.slice(0, 2);
        }
        container.innerHTML = previewPosts.map(p => renderPostCardHTML(p)).join('');
    }

    function renderHomepagePreview() {
        const container = document.getElementById('homepage-community-posts-list');
        if (container) {
            if (!Array.isArray(posts) || posts.length === 0) {
                posts = [...INITIAL_POSTS];
                savePosts();
            }
            const previewPosts = posts.slice(0, 2);
            container.innerHTML = previewPosts.map(post => renderPostCardHTML(post)).join('');
        }
        renderUrgentPreview();
        renderRecoveryPreview();
    }

    function toggleLike(postId) {
        const post = posts.find(p => p.id === postId);
        if (!post) return;

        post.isLiked = !post.isLiked;
        post.likes += post.isLiked ? 1 : -1;
        savePosts();
        renderHomepagePreview();
        renderCommunityPosts();
        renderModalPosts();
    }

    function toggleBookmark(postId) {
        const post = posts.find(p => p.id === postId);
        if (!post) return;

        post.isBookmarked = !post.isBookmarked;
        savePosts();
        renderHomepagePreview();
        renderCommunityPosts();
        renderModalPosts();
        if (window.TempoApp) {
            window.TempoApp.showToast(post.isBookmarked ? "Post saved to bookmarks" : "Post removed from bookmarks");
        }
    }

    // Legacy modal compatibility methods
    function selectSection(section) {
        if (section === 'messages') {
            selectTab('messages');
        } else {
            selectTab('posts');
        }
        currentSection = section;
    }

    function openCommunityModal(section = 'feed') {
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            const targetTab = section === 'messages' ? 'messages' : 'posts';
            window.TempoApp.navigateTo('community', targetTab);
            return;
        }
        const modal = document.getElementById('modal-community-posts');
        if (modal) modal.classList.remove('hidden');
    }

    function closeCommunityModal() {
        const modal = document.getElementById('modal-community-posts');
        if (modal) modal.classList.add('hidden');
    }

    function renderModalPosts(filterTag = 'all') {
        const container = document.getElementById('modal-community-posts-list');
        if (!container) return;

        const filtered = filterTag === 'all' 
            ? posts 
            : posts.filter(p => p.tag.toLowerCase() === filterTag.toLowerCase());

        container.innerHTML = filtered.map(p => renderPostCardHTML(p)).join('');
    }

    function openPostComments(postId) {
        if (window.TempoApp) {
            window.TempoApp.navigateTo('community', 'posts');
        } else {
            selectTab('posts');
        }
        expandedPostComments[postId] = true;
        renderCommunityPosts();
        setTimeout(() => {
            const input = document.getElementById(`input-comment-${postId}`);
            if (input) input.focus();
        }, 150);
    }

    function bindEvents() {
        const form = document.getElementById('community-create-post-form');
        if (form) {
            form.addEventListener('submit', handleCreateCommunityPost);
        }

        const dmForm = document.getElementById('dm-message-form');
        if (dmForm) {
            dmForm.addEventListener('submit', handleSendMessage);
        }

        const annForm = document.getElementById('form-create-announcement');
        if (annForm) {
            annForm.addEventListener('submit', handleCreateAnnouncement);
        }
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
        // Tips
        renderTips,
        filterTipsCategory,
        handleTipsSearch,
        clearTipsSearch,
        // Learn
        renderLearn,
        handleLearnSearch,
        clearLearnSearch,
        // Posts
        renderCommunityPosts,
        filterPostsTag,
        handlePostsSearch,
        handleCreateCommunityPost,
        handleInlineCommentSubmit,
        togglePostCommentsExpand,
        toggleLike,
        toggleBookmark,
        openPostComments,
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
        renderModalPosts,
        openCommunityModal,
        closeCommunityModal,
        selectSection,
        getCurrentSection: () => currentSection,
        getAllPosts: () => posts,
        getPosts: () => posts,
        getInitialPosts: () => [...INITIAL_POSTS],
        getAnnouncements: () => announcements
    };
})();
'''

# Convert line endings to CRLF for communityPosts.js
content_crlf = content.replace('\r\n', '\n').replace('\n', '\r\n')
with open('communityPosts.js', 'wb') as f:
    f.write(content_crlf.encode('utf-8'))
print('Successfully wrote communityPosts.js with CRLF line endings.')
