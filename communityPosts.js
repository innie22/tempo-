/**
 * Tempo Community Posts Module
 * Provides lightweight social-feed style peer posts (non-blog, non-article),
 * supporting anonymous sharing, like counters, bookmarks, and topic hashtags.
 */

window.TempoCommunity = (function() {
    // Initial supportive peer posts matching Entry Home reference design
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

    let posts = [...INITIAL_POSTS];
    let currentSection = 'feed';

    function init() {
        loadPosts();
        renderHomepagePreview();
        renderUrgentPreview();
        renderRecoveryPreview();
        bindEvents();
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

    function bindEvents() {
        const seeAllBtn = document.getElementById('btn-see-all-posts');
        if (seeAllBtn) {
            seeAllBtn.addEventListener('click', () => openCommunityModal('feed'));
        }

        const navPostsBtn = document.getElementById('nav-link-posts');
        if (navPostsBtn) {
            navPostsBtn.addEventListener('click', (e) => {
                e.preventDefault();
                openCommunityModal('feed');
            });
        }

        const closeBtn = document.getElementById('btn-close-community-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', closeCommunityModal);
        }

        const feedTabBtn = document.getElementById('tab-community-feed');
        if (feedTabBtn) {
            feedTabBtn.addEventListener('click', () => selectSection('feed'));
        }

        const messagesTabBtn = document.getElementById('tab-community-messages');
        if (messagesTabBtn) {
            messagesTabBtn.addEventListener('click', () => selectSection('messages'));
        }

        const newDmBtn = document.getElementById('btn-new-direct-message');
        if (newDmBtn) {
            newDmBtn.addEventListener('click', () => {
                if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                    window.TempoApp.showToast("Direct messaging connection is ready. Select a peer or mentor to begin.");
                }
                const searchInput = document.getElementById('input-search-direct-messages');
                if (searchInput) searchInput.focus();
            });
        }

        const startDmBtn = document.getElementById('btn-start-first-dm');
        if (startDmBtn) {
            startDmBtn.addEventListener('click', () => {
                if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                    window.TempoApp.showToast("Direct messaging connection is ready. Select a peer or mentor to begin.");
                }
                const searchInput = document.getElementById('input-search-direct-messages');
                if (searchInput) searchInput.focus();
            });
        }

        const newPostForm = document.getElementById('form-create-post');
        if (newPostForm) {
            newPostForm.addEventListener('submit', handleCreatePost);
        }
    }

    function renderPostCardHTML(post, options = {}) {
        if (!post) return '';

        const authorInitial = (post.authorName || 'S').charAt(0).toUpperCase();
        const subtitleText = post.context || (post.university ? `${post.university} · ${post.timeAgo || 'Recently'}` : (post.timeAgo || 'Recently'));

        const tagsHTML = post.tags && post.tags.length > 0
            ? post.tags.map(t => `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${t.bg || 'bg-stone-100'} ${t.text || 'text-stone-700'}">${escapeHtml(t.label || t)}</span>`).join(' ')
            : (post.tag ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FFE9DC] text-[#B83D08]">${escapeHtml(post.tag)}</span>` : '');

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

        const replyPreviewHTML = post.hasReplyPreview
            ? `
                <div class="mt-2.5 pt-2 border-t border-[#EAE4DF] text-[11px] space-y-1.5">
                    <div class="flex items-start space-x-2">
                        <img src="${escapeHtml(post.replyAvatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=80&h=80&q=80')}" alt="Commenter" class="w-4 h-4 rounded-full object-cover shrink-0 mt-0.5" onerror="this.style.display='none'">
                        <div class="min-w-0">
                            <span class="font-bold text-[#202124]">${escapeHtml(post.replyAuthor || 'fess')}:</span>
                            <span class="text-[#6F6B68]">${escapeHtml(post.replyText || '')}</span>
                        </div>
                    </div>
                    ${post.subReplyAuthor ? `
                        <div class="flex items-start space-x-2 pl-4">
                            <img src="${escapeHtml(post.subReplyAvatar || post.avatar || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=80&h=80&q=80')}" alt="Author" class="w-4 h-4 rounded-full object-cover shrink-0 mt-0.5" onerror="this.style.display='none'">
                            <div class="min-w-0">
                                <span class="font-bold text-[#202124]">${escapeHtml(post.subReplyAuthor)}:</span>
                                <span class="text-[#6F6B68]">${escapeHtml(post.subReplyText || '')}</span>
                            </div>
                        </div>
                    ` : ''}
                </div>
            `
            : '';

        return `
            <div class="p-3.5 sm:p-4 bg-[#F6F0EB] border border-[#42413F] rounded-2xl space-y-2.5 transition flex flex-col justify-between" data-post-id="${post.id}">
                <!-- Header: Avatar, Name, Time, Tags, and Bookmark -->
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
                    <!-- Bookmark on right -->
                    <button type="button" 
                            onclick="window.TempoCommunity.toggleBookmark('${post.id}')" 
                            class="hover:text-[#D99E87] transition cursor-pointer p-1 text-[#736F68] shrink-0 ${post.isBookmarked ? 'text-[#D99E87]' : ''}" 
                            title="${post.isBookmarked ? 'Remove bookmark' : 'Bookmark post'}">
                        <svg class="w-4 h-4" fill="${post.isBookmarked ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                        </svg>
                    </button>
                </div>

                <!-- Post Content -->
                <div class="space-y-2 flex-1">
                    <p class="text-xs text-[#202124] leading-relaxed break-words cursor-pointer" onclick="window.TempoCommunity.openPostComments('${post.id}')">
                        ${escapeHtml(post.content)}
                    </p>
                    ${thumbnailsHTML}
                </div>

                <!-- Actions: Like, Comment, Share -->
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
                        <button type="button" 
                                onclick="if(window.TempoApp) window.TempoApp.showToast('Link copied to clipboard');" 
                                class="flex items-center hover:text-[#202124] text-[#736F68] transition cursor-pointer"
                                title="Share">
                            <svg class="w-3.5 h-3.5 text-[#736F68]" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                            </svg>
                        </button>
                    </div>
                </div>

                ${replyPreviewHTML}
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

    function renderModalPosts(filterTag = 'all') {
        const container = document.getElementById('modal-community-posts-list');
        if (!container) return;

        const filtered = filterTag === 'all' 
            ? posts 
            : posts.filter(p => p.tag.toLowerCase() === filterTag.toLowerCase());

        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="p-8 text-center bg-white border border-[#E8E4E1] rounded-2xl space-y-2">
                    <p class="text-sm font-semibold text-[#202124]">No posts in ${filterTag} yet</p>
                    <p class="text-xs text-[#6F6B68]">Be the first student to share an encouraging note or question.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = filtered.map(post => `
            <div class="p-4 bg-white border border-[#E8E4E1] rounded-2xl space-y-3 transition hover:border-[#D3CDC8]">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2.5">
                        <img src="${post.avatar}" alt="${post.authorName}" 
                             class="w-8 h-8 rounded-full object-cover border border-stone-200">
                        <div>
                            <div class="flex items-center space-x-2">
                                <span class="text-xs font-bold text-[#202124]">${post.authorName}</span>
                                ${post.isAnonymous ? '<span class="text-[10px] bg-stone-100 text-stone-600 px-1.5 py-0.5 rounded">Anonymous</span>' : ''}
                            </div>
                            <div class="text-[10px] text-[#6F6B68] flex items-center space-x-1">
                                <span>${post.timeAgo}</span>
                                <span>•</span>
                                <span class="text-[#FF6B2C] font-semibold">${post.tag}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <p class="text-xs text-[#202124] leading-relaxed">
                    ${escapeHtml(post.content)}
                </p>

                <div class="pt-2 border-t border-gray-100 flex items-center justify-between text-xs text-[#6F6B68]">
                    <div class="flex items-center space-x-4">
                        <button onclick="window.TempoCommunity.toggleLike('${post.id}')" 
                                class="flex items-center space-x-1 hover:text-[#FF6B2C] transition ${post.isLiked ? 'text-[#FF6B2C] font-semibold' : ''}">
                            <span>${post.isLiked ? '♥' : '♡'}</span>
                            <span class="text-[11px]">${post.likes}</span>
                        </button>
                        <button onclick="window.TempoCommunity.openPostComments('${post.id}')" 
                                class="flex items-center space-x-1 hover:text-[#202124] transition">
                            <span>💬</span>
                            <span class="text-[11px]">${post.commentsCount} comments</span>
                        </button>
                    </div>
                    <div class="flex items-center space-x-2">
                        <button onclick="window.TempoCommunity.toggleBookmark('${post.id}')" 
                                class="hover:text-[#FF6B2C] transition ${post.isBookmarked ? 'text-[#FF6B2C]' : ''}">
                            <svg class="w-4 h-4" fill="${post.isBookmarked ? 'currentColor' : 'none'}" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                            </svg>
                        </button>
                    </div>
                </div>

                ${post.comments && post.comments.length > 0 ? `
                    <div class="pt-2 mt-2 border-t border-stone-100 space-y-1.5 pl-3 border-l-2 border-[#FFE9DC]">
                        ${post.comments.map(c => `
                            <div class="text-[11px] text-[#202124]">
                                <span class="font-bold text-[#6F6B68]">${c.author}:</span>
                                <span>${escapeHtml(c.text)}</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    function toggleLike(postId) {
        const post = posts.find(p => p.id === postId);
        if (!post) return;

        post.isLiked = !post.isLiked;
        post.likes += post.isLiked ? 1 : -1;
        savePosts();
        renderHomepagePreview();
        renderModalPosts();
    }

    function toggleBookmark(postId) {
        const post = posts.find(p => p.id === postId);
        if (!post) return;

        post.isBookmarked = !post.isBookmarked;
        savePosts();
        renderHomepagePreview();
        renderModalPosts();
        if (window.TempoApp) {
            window.TempoApp.showToast(post.isBookmarked ? "Post saved to bookmarks" : "Post removed from bookmarks");
        }
    }

    function selectSection(section) {
        if (section === 'messages' && (!window.TempoAuth || !window.TempoAuth.getCurrentUser())) {
            closeCommunityModal();
            const src = window.TempoMode && window.TempoMode.getSourceContext ? window.TempoMode.getSourceContext() : 'entry';
            if (window.TempoMode && typeof window.TempoMode.setPendingIntent === 'function') {
                window.TempoMode.setPendingIntent({
                    destination: 'posts',
                    action: 'navigate',
                    source: src,
                    requiredParams: { section: 'messages' },
                    type: 'tool',
                    tool: 'posts',
                    sourceContext: src
                });
            }
            if (window.TempoAuth && typeof window.TempoAuth.openSignInModal === 'function') {
                window.TempoAuth.openSignInModal();
            }
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Please sign in or create an account to view Direct Messages.");
            }
            return false;
        }

        currentSection = section === 'messages' ? 'messages' : 'feed';

        const feedTab = document.getElementById('tab-community-feed');
        const messagesTab = document.getElementById('tab-community-messages');
        const feedView = document.getElementById('community-view-feed');
        const messagesView = document.getElementById('community-view-messages');
        const modalTitle = document.getElementById('community-modal-title');
        const modalSubtitle = document.getElementById('community-modal-subtitle');

        const isVi = (window.TempoAuth && window.TempoAuth.getCurrentAuthLanguage && window.TempoAuth.getCurrentAuthLanguage() === 'vi') || 
                     (window.TempoI18n && window.TempoI18n.getLanguage && window.TempoI18n.getLanguage() === 'vi');

        if (currentSection === 'feed') {
            if (feedTab) {
                feedTab.className = "px-3.5 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-2 bg-[#FFE9DC] text-[#B83D08] cursor-pointer whitespace-nowrap shrink-0";
            }
            if (messagesTab) {
                messagesTab.className = "px-3.5 py-1.5 rounded-xl text-xs font-medium text-[#6F6B68] hover:text-[#202124] hover:bg-[#F3F1EF] transition flex items-center space-x-2 cursor-pointer whitespace-nowrap shrink-0";
            }
            if (feedView) feedView.classList.remove('hidden');
            if (messagesView) messagesView.classList.add('hidden');
            if (modalTitle) modalTitle.textContent = isVi ? "Cộng đồng Tempo" : "From the Tempo Community";
            if (modalSubtitle) modalSubtitle.textContent = isVi ? "Những chia sẻ đồng cảm, chân thành từ sinh viên khi đối mặt với áp lực học tập." : "Supportive, honest thoughts from students navigating university life.";
            renderModalPosts();
        } else {
            if (feedTab) {
                feedTab.className = "px-3.5 py-1.5 rounded-xl text-xs font-medium text-[#6F6B68] hover:text-[#202124] hover:bg-[#F3F1EF] transition flex items-center space-x-2 cursor-pointer whitespace-nowrap shrink-0";
            }
            if (messagesTab) {
                messagesTab.className = "px-3.5 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-2 bg-[#FFE9DC] text-[#B83D08] cursor-pointer whitespace-nowrap shrink-0";
            }
            if (feedView) feedView.classList.add('hidden');
            if (messagesView) messagesView.classList.remove('hidden');
            if (modalTitle) modalTitle.textContent = isVi ? "Tin nhắn trực tiếp" : "Direct Messages";
            if (modalSubtitle) modalSubtitle.textContent = isVi ? "Không gian trò chuyện riêng tư giữa các sinh viên và người đồng hành trong cộng đồng Tempo." : "Direct, private conversations with peer mentors and students in the Tempo community.";
        }
        return true;
    }

    function openCommunityModal(section = 'feed') {
        const modal = document.getElementById('modal-community-posts');
        if (!modal) return;
        const allowed = selectSection(section);
        if (!allowed) return;
        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    function closeCommunityModal() {
        const modal = document.getElementById('modal-community-posts');
        if (!modal) return;
        modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    function handleCreatePost(e) {
        e.preventDefault();
        const textarea = document.getElementById('input-new-post-content');
        const tagSelect = document.getElementById('select-new-post-tag');
        const anonCheckbox = document.getElementById('checkbox-new-post-anon');

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
        renderModalPosts();

        textarea.value = '';
        if (window.TempoApp) {
            window.TempoApp.showToast("Your supportive post was shared with the community!");
        }
    }

    function openPostComments(postId) {
        openCommunityModal('feed');
        const input = document.getElementById('input-new-post-content');
        if (input) input.focus();
    }

    function escapeHtml(str) {
        return (str || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function getAllPosts() {
        if (!Array.isArray(posts) || posts.length === 0) {
            posts = [...INITIAL_POSTS];
            savePosts();
        }
        return posts;
    }

    function getInitialPosts() {
        return [...INITIAL_POSTS];
    }

    return {
        init,
        toggleLike,
        toggleBookmark,
        openCommunityModal,
        closeCommunityModal,
        selectSection,
        getCurrentSection: () => currentSection,
        openPostComments,
        renderModalPosts,
        renderHomepagePreview,
        renderUrgentPreview,
        renderRecoveryPreview,
        renderPostCardHTML,
        getAllPosts,
        getPosts: getAllPosts,
        getInitialPosts
    };
})();
