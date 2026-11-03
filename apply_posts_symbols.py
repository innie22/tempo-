# -*- coding: utf-8 -*-
import sys

def main():
    with open('communityPosts.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update State variables to include expandedFullWidthComments
    target_state = "    let isFilterMyPosts = false;\n    let isFilterBookmarks = false;"
    replace_state = "    let isFilterMyPosts = false;\n    let isFilterBookmarks = false;\n    let expandedFullWidthComments = new Set();"
    if target_state not in content:
        # Check CRLF
        target_state = "    let isFilterMyPosts = false;\r\n    let isFilterBookmarks = false;"
        replace_state = "    let isFilterMyPosts = false;\r\n    let isFilterBookmarks = false;\r\n    let expandedFullWidthComments = new Set();"

    assert target_state in content, "State variables target not found"
    content = content.replace(target_state, replace_state, 1)

    # 2. Update INITIAL_POSTS to include authorId and accurate commentsCount
    target_init_posts = """    const INITIAL_POSTS = [
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
    ];"""

    replace_init_posts = """    const INITIAL_POSTS = [
        {
            id: 'post-1',
            authorId: 'user-fpt-bakhi',
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
            commentsCount: 3,
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
            authorId: 'user-temposocute',
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
            commentsCount: 0,
            isLiked: false,
            isBookmarked: false,
            comments: []
        }
    ];"""

    # Normalize CRLF for matching
    if target_init_posts.replace('\n', '\r\n') in content:
        content = content.replace(target_init_posts.replace('\n', '\r\n'), replace_init_posts.replace('\n', '\r\n'), 1)
    elif target_init_posts in content:
        content = content.replace(target_init_posts, replace_init_posts, 1)
    else:
        print("Warning: INITIAL_POSTS exact string match missed; checking normalized whitespace")

    # 3. Add bookmark management helpers & update loadPosts
    target_loadposts = """    function loadPosts() {
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
    }"""

    replace_loadposts = """    function getUserBookmarksKey() {
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
                        if (!INITIAL_POSTS.some(initP => initP.id === p.id)) posts.push(p);
                    });
                }
            }
        } catch (e) {}
        syncUserBookmarksState();
        savePosts();
    }"""

    if target_loadposts.replace('\n', '\r\n') in content:
        content = content.replace(target_loadposts.replace('\n', '\r\n'), replace_loadposts.replace('\n', '\r\n'), 1)
    elif target_loadposts in content:
        content = content.replace(target_loadposts, replace_loadposts, 1)
    else:
        print("Warning: loadPosts exact string match missed")

    # 4. Replace renderTwoColumnPostHTML and renderFullWidthPostHTML
    # Find start of renderTwoColumnPostHTML to toggleLike
    p_start = content.find('    function renderTwoColumnPostHTML(post) {')
    p_end = content.find('    function toggleLike(postId) {')
    assert p_start != -1 and p_end != -1, "Render functions boundary not found"

    new_render_functions = """    function renderTwoColumnPostHTML(post) {
        const tagsHTML = (post.tags || []).map(t => `
            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${t.bg} ${t.text}">
                ${escapeHtml(t.label)}
            </span>
        `).join(' ');

        const commentsCount = Array.isArray(post.comments) ? post.comments.length : (post.commentsCount || 0);

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
                                aria-label="Comments (${commentsCount})" 
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
                        <button type="submit" class="bg-[#DFB59F] hover:bg-[#D4A38A] text-white px-3 py-1.5 rounded-xl text-xs font-bold shrink-0 transition">
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

        const commentsCount = Array.isArray(post.comments) ? post.comments.length : (post.commentsCount || 0);
        const isCommentsExpanded = expandedFullWidthComments.has(post.id);

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
                            aria-label="Comments (${commentsCount})" 
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
                            <h5 class="text-xs font-bold text-[#4A4541]">Comments (${commentsCount})</h5>
                            <button type="button" onclick="window.TempoCommunity.toggleFullWidthComments('${post.id}')" class="text-xs text-[#8E8A85] hover:text-[#202124]">✕ Close</button>
                        </div>
                        <div class="space-y-2.5 max-h-60 overflow-y-auto pr-1">
                            ${(post.comments && post.comments.length > 0) ? post.comments.map(c => `
                                <div class="${c.isSubReply ? 'pl-4' : ''} space-y-1">
                                    <div class="flex items-center space-x-1.5">
                                        <img src="${escapeHtml(c.avatar || 'assets/tempo-logo.png')}" alt="${escapeHtml(c.author)}" class="w-5 h-5 rounded-full object-cover">
                                        <span class="text-[11px] font-bold text-[#202124]">${escapeHtml(c.author)}</span>
                                        <span class="text-[9.5px] text-[#8E8A85]">${escapeHtml(c.time || '')}</span>
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
                                   placeholder="Write a comment..." 
                                   class="flex-1 px-3 py-1.5 text-xs bg-[#FAF8F5] border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#DE8662]">
                            <button type="submit" class="bg-[#DFB59F] hover:bg-[#D4A38A] text-white px-3 py-1.5 rounded-xl text-xs font-bold shrink-0 transition">
                                Post
                            </button>
                        </form>
                    </div>
                ` : ''}
            </div>
        `;
    }\n\n"""

    # Preserve CRLF if needed
    if '\r\n' in content:
        new_render_functions = new_render_functions.replace('\n', '\r\n')

    content = content[:p_start] + new_render_functions + content[p_end:]

    # 5. Replace toggleBookmark through handleInlineCommentSubmit
    p_tb_start = content.find('    function toggleBookmark(postId) {')
    p_tb_end = content.find('    function openCreatePostModal() {')
    assert p_tb_start != -1 and p_tb_end != -1, "Action functions boundary not found"

    new_action_functions = """    function toggleBookmark(postId) {
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
    }\n\n"""

    if '\r\n' in content:
        new_action_functions = new_action_functions.replace('\n', '\r\n')

    content = content[:p_tb_start] + new_action_functions + content[p_tb_end:]

    # 6. Update module return exports
    p_exp = content.find('        // Posts (Requirement 5)')
    assert p_exp != -1, "Export boundary not found"

    target_export = """        // Posts (Requirement 5)
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
        getInitialPosts: () => [...INITIAL_POSTS],"""

    replace_export = """        // Posts (Requirement 5 & Post Action Symbols)
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
        getInitialPosts: () => [...INITIAL_POSTS],"""

    if target_export.replace('\n', '\r\n') in content:
        content = content.replace(target_export.replace('\n', '\r\n'), replace_export.replace('\n', '\r\n'), 1)
    elif target_export in content:
        content = content.replace(target_export, replace_export, 1)
    else:
        print("Warning: export exact match missed")

    # Ensure CRLF line endings
    if '\r\n' not in content:
        content = content.replace('\n', '\r\n')

    with open('communityPosts.js', 'wb') as f:
        f.write(content.encode('utf-8'))

    print("Successfully updated communityPosts.js with all 3 post action symbols and CRLF line endings!")

if __name__ == '__main__':
    main()
