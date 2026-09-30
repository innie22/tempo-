/**
 * Tempo Community Posts Module
 * Provides lightweight social-feed style peer posts (non-blog, non-article),
 * supporting anonymous sharing, like counters, bookmarks, and topic hashtags.
 */

window.TempoCommunity = (function() {
    // Initial supportive peer posts
    const INITIAL_POSTS = [
        {
            id: 'post-1',
            authorName: 'Anonymous',
            isAnonymous: true,
            avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=120&h=120&q=80',
            timeAgo: '2h ago',
            tag: '#Deadline',
            tagColor: 'orange',
            content: "Just finished submitting my last assignment!!! I've been so anxious all week but I'm actually proud of myself for pushing through. Small wins count 🧡",
            likes: 128,
            commentsCount: 26,
            isLiked: false,
            isBookmarked: false,
            comments: [
                { author: 'Elena (Advisor)', time: '1h ago', text: 'Huge congrats! Take the rest of the evening to truly decompress.' },
                { author: 'Marcus K.', time: '45m ago', text: 'Needed to see this today. 2 more pages for me!' }
            ]
        },
        {
            id: 'post-2',
            authorName: 'N.',
            isAnonymous: false,
            avatar: 'https://images.unsplash.com/photo-1543610892-0b1f7e6d8ac1?auto=format&fit=crop&w=120&h=120&q=80',
            timeAgo: '5h ago',
            tag: '#MentalHealth',
            tagColor: 'orange',
            content: "Lately I've been feeling unmotivated even though I don't have any big deadlines. Anyone else feel like this? How do you get out of it? 🥺",
            likes: 64,
            commentsCount: 18,
            isLiked: false,
            isBookmarked: false,
            comments: [
                { author: 'Sarah W.', time: '3h ago', text: 'When that happens to me, I drop expectations to zero and just do a 10-minute walk with music.' },
                { author: 'David T.', time: '2h ago', text: 'Low-grade emotional exhaustion is real after exam seasons. Give yourself permission to idle a bit.' }
            ]
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
                posts = JSON.parse(saved);
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
            seeAllBtn.addEventListener('click', openCommunityModal);
        }

        const navPostsBtn = document.getElementById('nav-link-posts');
        if (navPostsBtn) {
            navPostsBtn.addEventListener('click', (e) => {
                e.preventDefault();
                openCommunityModal();
            });
        }

        const closeBtn = document.getElementById('btn-close-community-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', closeCommunityModal);
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

        return `
            <div class="p-4 sm:p-5 bg-white border border-[#E8E4E1] hover:border-[#D3CDC8] rounded-2xl space-y-3 transition shadow-xs flex flex-col justify-between">
                <!-- Header: Avatar, Name, Context/Time -->
                <div class="flex items-start justify-between gap-2">
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
                            <div class="flex items-center space-x-1.5">
                                <span class="text-xs font-bold text-[#202124] truncate">${escapeHtml(post.authorName || 'Anonymous')}</span>
                                ${post.isAnonymous ? '<span class="text-[10px] bg-stone-100 text-stone-600 px-1.5 py-0.5 rounded font-medium">Anonymous</span>' : ''}
                            </div>
                            <div class="text-[10px] text-[#6F6B68] flex items-center space-x-1 truncate">
                                <span>${escapeHtml(subtitleText)}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Post Content -->
                <div class="space-y-2 flex-1">
                    <p class="text-xs text-[#202124] leading-relaxed break-words whitespace-pre-line cursor-pointer" onclick="window.TempoCommunity.openPostComments('${post.id}')">
                        ${escapeHtml(post.content)}
                    </p>
                    ${post.tag ? `
                        <div class="pt-0.5">
                            <span class="text-[11px] font-semibold text-[#FF6B2C] hover:underline cursor-pointer" onclick="window.TempoCommunity.openCommunityModal()">${escapeHtml(post.tag)}</span>
                        </div>
                    ` : ''}
                </div>

                <!-- Actions: Like, Comment, Bookmark -->
                <div class="pt-2 border-t border-[#F5F2EF] flex items-center justify-between text-xs text-[#6F6B68]">
                    <div class="flex items-center space-x-4">
                        <button type="button" 
                                onclick="window.TempoCommunity.toggleLike('${post.id}')" 
                                class="flex items-center space-x-1.5 hover:text-[#FF6B2C] transition cursor-pointer ${post.isLiked ? 'text-[#FF6B2C] font-semibold' : ''}"
                                title="Like">
                            <span class="text-sm leading-none">${post.isLiked ? '♥' : '♡'}</span>
                            <span class="text-[11px] font-medium">${post.likes || 0}</span>
                        </button>
                        <button type="button" 
                                onclick="window.TempoCommunity.openPostComments('${post.id}')" 
                                class="flex items-center space-x-1.5 hover:text-[#202124] transition cursor-pointer"
                                title="Comments">
                            <span class="text-sm leading-none">💬</span>
                            <span class="text-[11px] font-medium">${post.commentsCount || (post.comments ? post.comments.length : 0)}</span>
                        </button>
                    </div>
                    <div class="flex items-center space-x-2">
                        <button type="button" 
                                onclick="window.TempoCommunity.toggleBookmark('${post.id}')" 
                                class="hover:text-[#FF6B2C] transition cursor-pointer ${post.isBookmarked ? 'text-[#FF6B2C]' : ''}" 
                                title="${post.isBookmarked ? 'Remove bookmark' : 'Bookmark post'}">
                            <svg class="w-3.5 h-3.5" fill="${post.isBookmarked ? 'currentColor' : 'none'}" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                            </svg>
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

    function openCommunityModal() {
        const modal = document.getElementById('modal-community-posts');
        if (!modal) return;
        renderModalPosts();
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
        openCommunityModal();
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
        return posts;
    }

    return {
        init,
        toggleLike,
        toggleBookmark,
        openCommunityModal,
        closeCommunityModal,
        openPostComments,
        renderModalPosts,
        renderHomepagePreview,
        renderUrgentPreview,
        renderRecoveryPreview,
        renderPostCardHTML,
        getAllPosts
    };
})();
