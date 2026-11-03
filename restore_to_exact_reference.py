# -*- coding: utf-8 -*-
"""
Restore Tempo EntryHome and Community Preview to match exact source of truth references:
- media_1792935418362_1094ad43.png (Full layout source of truth)
- media_1792935428708_27233148.png (Community panel detail source of truth)
"""

def restore_to_exact_reference():
    print("Restoring Tempo EntryHome to exact UI reference...")

    # =========================================================================
    # 1. UPDATE index.html (Strict CRLF)
    # Restore logo size to clean medium standard: h-10 sm:h-11
    # =========================================================================
    with open('index.html', 'rb') as f:
        idx_content = f.read().decode('utf-8')

    # Replace logo class
    old_logo_pattern = 'class="h-14 sm:h-[62px] lg:h-[80px] w-auto object-contain block"'
    if old_logo_pattern in idx_content:
        idx_content = idx_content.replace(old_logo_pattern, 'class="h-10 sm:h-11 w-auto object-contain block"')
        print("1. index.html: Logo sizing adjusted to clean standard h-10 sm:h-11.")
    elif 'class="h-9 sm:h-10 w-auto object-contain block"' in idx_content:
        idx_content = idx_content.replace('class="h-9 sm:h-10 w-auto object-contain block"', 'class="h-10 sm:h-11 w-auto object-contain block"')
        print("1. index.html: Logo sizing set to h-10 sm:h-11.")
    else:
        print("1. index.html: Logo pattern check passed.")

    # Ensure CRLF
    idx_content = idx_content.replace('\r\n', '\n').replace('\n', '\r\n')
    with open('index.html', 'wb') as f:
        f.write(idx_content.encode('utf-8'))

    # =========================================================================
    # 2. UPDATE communityPosts.js (Strict CRLF)
    # Restore INITIAL_POSTS and renderHomepagePreview to match media_1792935428708_27233148.png
    # =========================================================================
    with open('communityPosts.js', 'rb') as f:
        comm_content = f.read().decode('utf-8')

    p_init_posts_start = comm_content.find('    const INITIAL_POSTS = [')
    p_init_posts_end = comm_content.find('    // Reference 5: Direct Message Conversations')
    assert p_init_posts_start != -1 and p_init_posts_end != -1, "INITIAL_POSTS boundaries not found"

    new_init_posts = """    const INITIAL_POSTS = [
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
                    author: 'Elena (Advisor)',
                    time: '1h ago',
                    text: 'Huge congrats! Take the rest of the evening to truly decompress.'
                },
                {
                    id: 'c-2',
                    author: 'Marcus K.',
                    time: '45m ago',
                    text: 'Needed to see this today. 2 more pages for me!'
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
    ];\n\n"""

    comm_content = comm_content[:p_init_posts_start] + new_init_posts + comm_content[p_init_posts_end:]

    # Update renderHomepagePreview in communityPosts.js
    p_hp_start = comm_content.find('    function renderHomepagePreview() {')
    p_hp_end = comm_content.find('    function renderUrgentPreview() {')
    assert p_hp_start != -1 and p_hp_end != -1, "renderHomepagePreview boundaries not found"

    new_hp_func = """    function renderHomepagePreview() {
        const container = document.getElementById('homepage-community-posts-list');
        if (!container) return;
        const previewPosts = posts.slice(0, 2);
        if (previewPosts.length === 0) {
            container.innerHTML = `
                <div class="h-48 flex flex-col items-center justify-center text-center p-6 space-y-2 text-[#8E8A85]">
                    <img src="assets/comment_action_symbol.png" alt="No posts" class="w-6 h-6 opacity-40 object-contain mb-0.5">
                    <p class="text-xs font-bold text-[#5A5550]">No community posts yet</p>
                    <p class="text-[10.5px] text-[#8E8A85] leading-relaxed">Be the first to share with your peers in the community.</p>
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
                <div onclick="window.TempoApp.navigateTo('community'); if(window.TempoCommunity) { window.TempoCommunity.selectTab('posts'); setTimeout(() => { const el = document.querySelector('[data-post-id=\\'${post.id}\\']'); if(el) el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 150); }"
                     class="bg-white border border-[#4A4541] rounded-2xl sm:rounded-3xl p-5 space-y-3 shadow-xs hover:border-[#DE8662] transition cursor-pointer group"
                     title="Open post by ${escapeHtml(post.authorName)}">
                    <!-- Header -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2.5">
                            <img src="${escapeHtml(post.avatar)}" alt="${escapeHtml(post.authorName)}" class="w-9 h-9 rounded-full object-cover">
                            <div>
                                <h4 class="text-sm font-bold text-[#202124] leading-tight">${escapeHtml(post.authorName)}</h4>
                                <span class="text-xs text-[#8E8A85]">${escapeHtml(post.timeAgo || 'Recent')}</span>
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
    }\n\n"""

    comm_content = comm_content[:p_hp_start] + new_hp_func + comm_content[p_hp_end:]

    # Ensure CRLF
    comm_content = comm_content.replace('\r\n', '\n').replace('\n', '\r\n')
    with open('communityPosts.js', 'wb') as f:
        f.write(comm_content.encode('utf-8'))
    print("2. communityPosts.js: Updated to exact reference preview (CRLF preserved).")

    # =========================================================================
    # 3. UPDATE mode.js (Strict LF)
    # Restore Quick Relief & Focus Now with descriptions and original dimensions
    # Restore Welcome card proportions
    # Restore community preview markup
    # =========================================================================
    with open('mode.js', 'rb') as f:
        mode_content = f.read().decode('utf-8')

    p_m_start = mode_content.find('    function renderQuickReliefCardHTML(extraClass = \'\') {')
    p_m_end = mode_content.find('    function renderDmodeHome() {')
    assert p_m_start != -1 and p_m_end != -1, "mode.js card boundaries not found"

    new_mode_chunk = """    function renderQuickReliefCardHTML(extraClass = '') {
        const widthClass = extraClass ? ` ${extraClass}` : '';
        return `
            <div onclick="if (window.TempoStressRelief && window.TempoStressRelief.openModal) { window.TempoStressRelief.openModal(); } else if (window.TempoTriage && window.TempoTriage.openQuickReliefModal) { window.TempoTriage.openQuickReliefModal(); }"
                 role="button"
                 tabindex="0"
                 aria-label="Quick Relief"
                 onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); this.click(); }"
                 class="bg-[#DEECE5] border border-[#728F83]/30 rounded-3xl p-6 sm:p-7 flex items-center justify-between min-h-[155px] sm:min-h-[165px] shadow-xs hover:shadow-md transition cursor-pointer group relative overflow-hidden${widthClass}"
                 title="Quick Relief">
                <div class="pr-2 z-10 flex-1 min-w-0">
                    <h3 class="text-2xl sm:text-[26px] font-bold text-[#6D8A7E] leading-tight mb-1.5">
                        Quick Relief
                    </h3>
                    <p class="text-xs sm:text-sm text-[#728F83] leading-snug max-w-[150px]">
                        Quick ways to ease stress and feel better.
                    </p>
                </div>
                <img src="assets/quick-relief-mascot-transparent.png"
                     alt="Quick Relief"
                     class="h-24 sm:h-28 w-auto object-contain shrink-0 select-none pointer-events-none group-hover:scale-105 transition-transform" />
            </div>
        `;
    }

    function renderFocusNowCardHTML(extraClass = '') {
        const widthClass = extraClass ? ` ${extraClass}` : '';
        return `
            <div onclick="if (window.TempoFocusZone && window.TempoFocusZone.openQuickEntry) { window.TempoFocusZone.openQuickEntry(); } else if (window.TempoTriage && window.TempoTriage.launchFocusMode) { window.TempoTriage.launchFocusMode(); }"
                 role="button"
                 tabindex="0"
                 aria-label="Focus Now"
                 onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); this.click(); }"
                 class="bg-[#D29C85] border border-[#4A4541]/20 rounded-3xl p-6 sm:p-7 flex items-center justify-between min-h-[155px] sm:min-h-[165px] shadow-xs hover:shadow-md transition cursor-pointer group relative overflow-hidden${widthClass}"
                 title="Focus Now">
                <img src="assets/focus-now-mascot.png"
                     alt="Focus Now"
                     class="h-24 sm:h-28 w-auto object-contain shrink-0 select-none pointer-events-none -ml-2 group-hover:scale-105 transition-transform" />
                <div class="pl-2 z-10 flex-1 min-w-0 text-right sm:text-left">
                    <h3 class="text-2xl sm:text-[26px] font-bold text-white leading-tight mb-1.5">
                        Focus Now
                    </h3>
                    <p class="text-xs sm:text-sm text-white/90 leading-snug">
                        Your own personalized workspace.
                    </p>
                </div>
            </div>
        `;
    }

    function renderLearnSolveCardHTML(extraClass = '') {
        const widthClass = extraClass ? ` ${extraClass}` : '';
        return `
            <div onclick="if (window.TempoApp) { window.TempoApp.navigateTo('community', 'tips'); } else { window.location.hash = '#community?tab=tips'; }"
                 class="bg-[#FBEDD9] border border-[#736F68] rounded-3xl overflow-hidden p-4 sm:p-5 flex items-center justify-between min-h-[175px] h-[175px]${widthClass} shadow-xs hover:shadow-md transition cursor-pointer group relative"
                 title="Learn & Solve">
                <div class="relative z-10 flex-1 min-w-0 pr-1">
                    <h3 class="text-[22px] sm:text-[25px] font-bold text-[#736F68] mb-1 group-hover:text-[#5B5751] transition leading-tight whitespace-nowrap">
                        Learn &amp; Solve
                    </h3>
                    <p class="text-[14px] sm:text-[16px] text-[#736F68] leading-[1.35] max-w-[155px]">
                        Tips and tools to help you cope.
                    </p>
                </div>
                <img src="assets/learn-solve-mascot.png"
                     alt="Learn & Solve Mascot"
                     class="h-[105px] w-auto object-contain shrink-0 select-none pointer-events-none -mr-1 sm:-mr-2 translate-y-1" />
            </div>
        `;
    }

    function renderCommunityPreviewsHTML(previewPosts) {
        if (!Array.isArray(previewPosts) || previewPosts.length === 0) {
            return `
                <div class="h-48 flex flex-col items-center justify-center text-center p-6 space-y-2 text-[#8E8A85]">
                    <img src="assets/comment_action_symbol.png" alt="No posts" class="w-6 h-6 opacity-40 object-contain mb-0.5">
                    <p class="text-xs font-bold text-[#5A5550]">No community posts yet</p>
                    <p class="text-[10.5px] text-[#8E8A85] leading-relaxed">Be the first to share with your peers in the community.</p>
                </div>
            `;
        }

        return previewPosts.slice(0, 2).map(post => {
            const tagsHTML = (post.tags || []).map(t => `
                <span class="px-3 py-0.5 rounded-full text-xs font-semibold ${t.bg} ${t.text}">
                    ${escapeHtml(t.label)}
                </span>
            `).join(' ');

            const commentsCount = (post.comments && post.comments.length > 0) ? post.comments.length : (post.commentsCount || 0);

            return `
                <div onclick="window.TempoApp.navigateTo('community'); if(window.TempoCommunity) { window.TempoCommunity.selectTab('posts'); setTimeout(() => { const el = document.querySelector('[data-post-id=\\'${post.id}\\']'); if(el) el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 150); }"
                     class="bg-white border border-[#4A4541] rounded-2xl sm:rounded-3xl p-5 space-y-3 shadow-xs hover:border-[#DE8662] transition cursor-pointer group"
                     title="Open post by ${escapeHtml(post.authorName)}">
                    <!-- Header -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2.5">
                            <img src="${escapeHtml(post.avatar)}" alt="${escapeHtml(post.authorName)}" class="w-9 h-9 rounded-full object-cover">
                            <div>
                                <h4 class="text-sm font-bold text-[#202124] leading-tight">${escapeHtml(post.authorName)}</h4>
                                <span class="text-xs text-[#8E8A85]">${escapeHtml(post.timeAgo || 'Recent')}</span>
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

    /**
     * REDESIGNED TEMPO ENTRYHOME
     * Restored to exact visual hierarchy matching reference screenshot media_1792935418362_1094ad43.png
     */
    function renderEntryHomeHTML() {
        let posts = (window.TempoCommunity && typeof window.TempoCommunity.getAllPosts === 'function')
            ? window.TempoCommunity.getAllPosts()
            : [];
        if (!Array.isArray(posts) || posts.length === 0) {
            if (window.TempoCommunity && typeof window.TempoCommunity.getInitialPosts === 'function') {
                posts = window.TempoCommunity.getInitialPosts();
            }
        }
        const previewPosts = (Array.isArray(posts) && posts.length > 0) ? posts.slice(0, 2) : [];

        return `
            <div class="max-w-6xl mx-auto py-2 sm:py-4 space-y-7 sm:space-y-9 font-arimo" data-tempo-ui="entry-home">
                <!-- ==============================================================
                     UPPER SECTION: DESKTOP 2-COLUMN (LEFT: WELCOME + ACTIONS; RIGHT: COMMUNITY)
                     Matches exact Reference Screenshot media_1792935418362_1094ad43.png
                     ============================================================== -->
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 sm:gap-7 items-stretch">
                    <!-- LEFT COLUMN (approx 58-60% width): Welcome Card + 2 Primary Action Cards -->
                    <div class="lg:col-span-7 flex flex-col justify-between space-y-5 sm:space-y-6">
                        <!-- Welcome / Hero Card (Proportional, comfortable spacing matching reference) -->
                        <div class="bg-white border border-[#EAE4DF] rounded-3xl sm:rounded-[32px] p-7 sm:p-8 sm:pb-9 shadow-xs flex flex-col justify-between flex-1 min-h-[230px] sm:min-h-[245px]" data-tempo-ui="entry-welcome-card">
                            <div class="space-y-2">
                                <span class="text-sm sm:text-base font-bold text-[#DE8662] block tracking-wide">
                                    Welcome to Tempo
                                </span>
                                <h1 class="text-3xl sm:text-4xl lg:text-[42px] font-bold text-[#4A4541] tracking-tight leading-[1.12]">
                                    What do you need right now?
                                </h1>
                            </div>

                            <div class="pt-4">
                                <button type="button"
                                        id="btn-hero-figure-start"
                                        onclick="if (window.TempoApp && typeof window.TempoApp.openRoutingModal === 'function') { window.TempoApp.openRoutingModal(); } else if (window.TempoMode && typeof window.TempoMode.openHelpSelectionModal === 'function') { window.TempoMode.openHelpSelectionModal(); } else { const m = document.getElementById('modal-routing-selection'); if (m) { m.classList.remove('hidden'); document.body.classList.add('overflow-hidden'); } }"
                                        class="px-6 py-3 rounded-2xl bg-[#D28C74] hover:bg-[#C27C64] text-white font-bold text-sm sm:text-base shadow-xs transition inline-flex items-center space-x-2 cursor-pointer group">
                                    <span>Help me figure out where to start</span>
                                    <span class="group-hover:translate-x-1 transition-transform">→</span>
                                </button>
                            </div>
                        </div>

                        <!-- Two Action Cards Row directly below Welcome Card -->
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5" data-tempo-ui="entry-action-cards">
                            <!-- Action Card 1: Quick Relief (With supporting description) -->
                            ${renderQuickReliefCardHTML()}

                            <!-- Action Card 2: Focus Now (With supporting description) -->
                            ${renderFocusNowCardHTML()}
                        </div>
                    </div>

                    <!-- RIGHT COLUMN (approx 40-42% width): From the Tempo Community -->
                    <div class="lg:col-span-5 flex flex-col">
                        <div class="bg-white border border-[#EAE4DF] rounded-3xl sm:rounded-[32px] p-5 sm:p-6 shadow-xs flex flex-col justify-between h-full space-y-4" data-tempo-ui="entry-community-panel">
                            <!-- Header -->
                            <div class="flex items-center justify-between pb-1">
                                <div class="flex items-center space-x-2.5">
                                    <div class="w-8 h-8 rounded-full bg-[#F6E6DE] flex items-center justify-center shrink-0">
                                        <img src="assets/comment_action_symbol.png" alt="Community" class="w-4 h-4 object-contain" />
                                    </div>
                                    <h3 class="font-bold text-base sm:text-lg text-[#55504C] tracking-tight">
                                        From the Tempo Community
                                    </h3>
                                </div>
                                <button type="button"
                                        id="btn-see-all-posts"
                                        onclick="window.TempoApp.navigateTo('community'); if(window.TempoCommunity) window.TempoCommunity.selectTab('posts');"
                                        class="px-3.5 py-1 rounded-full bg-[#FCEFE8] hover:bg-[#F8E1D5] text-[#DE8662] text-xs font-bold transition flex items-center space-x-1 cursor-pointer">
                                    <span>See all</span>
                                    <span>→</span>
                                </button>
                            </div>

                            <!-- Community Previews Container -->
                            <div id="homepage-community-posts-list" class="space-y-4 flex-1 flex flex-col justify-between">
                                ${renderCommunityPreviewsHTML(previewPosts)}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- ==============================================================
                     LOWER SECTION: 3 SECONDARY FEATURE CARDS ROW (Reference Screenshot 2)
                     (Self-check • Work Plan • Notes)
                     ============================================================== -->
                <div class="pt-6 sm:pt-8 border-t border-[#EAE4DF]/80" data-tempo-ui="entry-secondary-cards">
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-7">
                        <!-- Card 1: Self-check (Soft Sage) -->
                        <div onclick="if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('open', { sourceContext: 'entry' }); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; }"
                             role="button"
                             tabindex="0"
                             aria-label="Self-check"
                             onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); this.click(); }"
                             class="bg-[#DEECE5] border border-[#728F83]/20 rounded-3xl sm:rounded-[28px] h-[185px] sm:h-[205px] p-5 flex items-center justify-center shadow-xs hover:shadow-md hover:scale-[1.01] transition cursor-pointer relative group overflow-hidden"
                             title="Self-check: Check in with your stress levels">
                            <img src="assets/self-check-mascot.png"
                                 alt="Self-check"
                                 class="h-32 sm:h-36 w-auto object-contain select-none pointer-events-none group-hover:scale-105 transition-transform" />
                        </div>

                        <!-- Card 2: Work Plan (Soft Peach) -->
                        <div onclick="if (window.TempoApp) window.TempoApp.navigateTo('plan-workspace'); else window.location.hash = '#plan-workspace';"
                             role="button"
                             tabindex="0"
                             aria-label="Work Plan"
                             onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); this.click(); }"
                             class="bg-[#FBE9DF] border border-[#F0D5CC]/40 rounded-3xl sm:rounded-[28px] h-[185px] sm:h-[205px] p-5 flex items-center justify-center shadow-xs hover:shadow-md hover:scale-[1.01] transition cursor-pointer relative group overflow-hidden"
                             title="Work Plan: Organize tasks and manage deadlines">
                            <img src="assets/work-plan-mascot.png"
                                 alt="Work Plan"
                                 class="h-32 sm:h-36 w-auto object-contain select-none pointer-events-none group-hover:scale-105 transition-transform" />
                        </div>

                        <!-- Card 3: Notes (Soft Pale Cream) -->
                        <div onclick="if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('tool-notes'); } else { window.location.hash = '#tool-notes'; }"
                             role="button"
                             tabindex="0"
                             aria-label="Notes"
                             onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); this.click(); }"
                             class="bg-[#F9EFE0] border border-[#F1DFC0]/50 rounded-3xl sm:rounded-[28px] h-[185px] sm:h-[205px] p-5 flex items-center justify-center shadow-xs hover:shadow-md hover:scale-[1.01] transition cursor-pointer relative group overflow-hidden"
                             title="Notes: Capture reminders and thoughts">
                            <img src="assets/notes-mascot.png"
                                 alt="Notes"
                                 class="h-32 sm:h-36 w-auto object-contain select-none pointer-events-none group-hover:scale-105 transition-transform" />
                        </div>
                    </div>
                </div>
            </div>
        `;
    }\n\n"""

    mode_content = mode_content[:p_m_start] + new_mode_chunk + mode_content[p_m_end:]

    # Ensure LF
    mode_content = mode_content.replace('\r\n', '\n')
    with open('mode.js', 'wb') as f:
        f.write(mode_content.encode('utf-8'))
    print("3. mode.js: Restored exact visual reference layout and card contents (LF preserved).")

    print("\nExact reference restoration completed successfully!")

if __name__ == '__main__':
    restore_to_exact_reference()
