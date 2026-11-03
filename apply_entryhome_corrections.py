# -*- coding: utf-8 -*-
import re

def apply_corrections():
    print("Applying EntryHome Redesign Regression Corrections...")

    # =========================================================================
    # 1. UPDATE index.html (Strict CRLF)
    # Restore navbar logo size from h-9 sm:h-10 to h-14 sm:h-[62px] lg:h-[80px]
    # =========================================================================
    with open('index.html', 'rb') as f:
        idx_bytes = f.read()
    idx_content = idx_bytes.decode('utf-8')

    target_logo = 'class="h-9 sm:h-10 w-auto object-contain block"'
    restored_logo = 'class="h-14 sm:h-[62px] lg:h-[80px] w-auto object-contain block"'
    assert target_logo in idx_content, "Target logo class not found in index.html"
    idx_content = idx_content.replace(target_logo, restored_logo, 1)

    # Ensure strictly CRLF
    idx_content = idx_content.replace('\r\n', '\n').replace('\n', '\r\n')
    with open('index.html', 'wb') as f:
        f.write(idx_content.encode('utf-8'))
    print("1. index.html: Navbar logo size restored to h-14 sm:h-[62px] lg:h-[80px] (CRLF preserved).")

    # =========================================================================
    # 2. UPDATE communityPosts.js (Strict CRLF)
    # Restore INITIAL_POSTS and renderHomepagePreview to match previous appearance
    # =========================================================================
    with open('communityPosts.js', 'rb') as f:
        comm_bytes = f.read()
    comm_content = comm_bytes.decode('utf-8')

    # Update INITIAL_POSTS in communityPosts.js to match previous reference (likes 129, Elena & Marcus; likes 64, Sarah W.)
    p_init_posts_start = comm_content.find('    const INITIAL_POSTS = [')
    p_init_posts_end = comm_content.find('    // Reference 5: Direct Message Conversations')
    assert p_init_posts_start != -1 and p_init_posts_end != -1, "INITIAL_POSTS boundaries not found in communityPosts.js"

    new_init_posts = """    const INITIAL_POSTS = [
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
            likes: 129,
            commentsCount: 2,
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
            likes: 64,
            commentsCount: 2,
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

    # Update renderHomepagePreview in communityPosts.js to restore original warm orange border and card styling
    p_hp_start = comm_content.find('    function renderHomepagePreview() {')
    p_hp_end = comm_content.find('    function renderUrgentPreview() {')
    assert p_hp_start != -1 and p_hp_end != -1, "renderHomepagePreview boundaries not found in communityPosts.js"

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
                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${t.bg} ${t.text}">
                    ${escapeHtml(t.label)}
                </span>
            `).join(' ');

            const commentsCount = (post.comments && post.comments.length > 0) ? post.comments.length : (post.commentsCount || 0);

            // Sub-reply preview matching original Reference
            let replyPreviewHTML = '';
            if (Array.isArray(post.comments) && post.comments.length > 0) {
                replyPreviewHTML = `
                    <div class="pt-2.5 border-t border-[#F0ECE9] space-y-2 text-[11px]">
                        ${post.comments.slice(0, 2).map(c => `
                            <div class="space-y-0.5">
                                <div class="flex items-center space-x-1.5">
                                    <span class="text-xs">🎨</span>
                                    <span class="font-bold text-[#202124]">${escapeHtml(c.author)}</span>
                                    <span class="text-[#8E8A85] text-[10px]">${escapeHtml(c.time || '')}</span>
                                </div>
                                <p class="text-[#5A5550] pl-5 leading-snug">${escapeHtml(c.text)}</p>
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            return `
                <div onclick="window.TempoApp.navigateTo('community'); if(window.TempoCommunity) { window.TempoCommunity.selectTab('posts'); setTimeout(() => { const el = document.querySelector('[data-post-id=\\'${post.id}\\']'); if(el) el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 150); }"
                     class="bg-white border border-[#DE8662] rounded-2xl p-4 sm:p-5 space-y-2.5 shadow-2xs hover:shadow-xs transition cursor-pointer group"
                     title="Open post by ${escapeHtml(post.authorName)}">
                    <!-- Header -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2.5">
                            <img src="${escapeHtml(post.avatar)}" alt="${escapeHtml(post.authorName)}" class="w-9 h-9 rounded-full object-cover">
                            <div>
                                <h4 class="text-[13px] font-bold text-[#202124] leading-tight">${escapeHtml(post.authorName)}</h4>
                                <span class="text-[10px] text-[#8E8A85]">${escapeHtml(post.timeAgo || 'Recent')}</span>
                            </div>
                        </div>
                        <div class="flex items-center space-x-1.5">
                            ${tagsHTML}
                            <div class="p-1 text-[#4A4541] hover:text-[#DE8662]">
                                <img src="assets/bookmark_action_symbol.png" alt="Bookmark" class="w-3.5 h-3.5 object-contain opacity-70">
                            </div>
                        </div>
                    </div>

                    <!-- Content -->
                    <p class="text-xs sm:text-[12.5px] text-[#202124] leading-relaxed">
                        ${escapeHtml(post.content)}
                    </p>

                    <!-- Thumbnails if present -->
                    ${(post.thumbnails && post.thumbnails.length > 0) ? `
                        <div class="grid grid-cols-4 gap-1.5 pt-0.5 pb-0.5">
                            ${post.thumbnails.slice(0, 4).map(img => `
                                <div class="aspect-4/3 rounded-lg overflow-hidden bg-stone-100 border border-stone-200">
                                    <img src="${escapeHtml(img)}" alt="Attachment" class="w-full h-full object-cover">
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}

                    <!-- Action stats row -->
                    <div class="flex items-center space-x-4 text-[#4A4541] text-xs pt-1">
                        <span class="flex items-center space-x-1">
                            <span class="text-xs">♡</span>
                            <span>${post.likes || 0}</span>
                        </span>
                        <span class="flex items-center space-x-1">
                            <img src="assets/comment_action_symbol.png" alt="Comments" class="w-3.5 h-3.5 object-contain">
                            <span>${commentsCount}</span>
                        </span>
                        <span class="flex items-center space-x-1">
                            <img src="assets/message_action_symbol.png" alt="Message" class="w-3.5 h-3.5 object-contain">
                        </span>
                    </div>

                    <!-- Sub-replies snippet -->
                    ${replyPreviewHTML}
                </div>
            `;
        }).join('');
    }\n\n"""

    comm_content = comm_content[:p_hp_start] + new_hp_func + comm_content[p_hp_end:]

    # Ensure strictly CRLF
    comm_content = comm_content.replace('\r\n', '\n').replace('\n', '\r\n')
    with open('communityPosts.js', 'wb') as f:
        f.write(comm_content.encode('utf-8'))
    print("2. communityPosts.js: Restored original Community preview template, orange borders, and post data (CRLF preserved).")

    # =========================================================================
    # 3. UPDATE mode.js (Strict LF)
    # Reduce Welcome card height by ~50%
    # Reduce Quick Relief & Focus Now card heights by ~50%
    # Synchronize renderCommunityPreviewsHTML with orange border and original styling
    # =========================================================================
    with open('mode.js', 'rb') as f:
        mode_bytes = f.read()
    mode_content = mode_bytes.decode('utf-8')

    # Replace renderQuickReliefCardHTML through renderEntryHomeHTML
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
                 class="bg-[#DEECE5] border border-[#728F83]/30 rounded-2xl sm:rounded-[22px] px-4 sm:px-5 py-2.5 sm:py-3 flex items-center justify-between h-[74px] sm:h-[80px] shadow-xs hover:shadow-md transition cursor-pointer group relative overflow-hidden${widthClass}"
                 title="Quick Relief">
                <div class="pr-2 z-10">
                    <h3 class="text-base sm:text-lg font-bold text-[#6D8A7E] leading-tight">
                        Quick Relief
                    </h3>
                </div>
                <img src="assets/quick-relief-mascot-transparent.png"
                     alt="Quick Relief"
                     class="h-12 sm:h-14 w-auto object-contain shrink-0 select-none pointer-events-none group-hover:scale-105 transition-transform" />
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
                 class="bg-[#D29C85] border border-[#4A4541]/20 rounded-2xl sm:rounded-[22px] px-4 sm:px-5 py-2.5 sm:py-3 flex items-center justify-between h-[74px] sm:h-[80px] shadow-xs hover:shadow-md transition cursor-pointer group relative overflow-hidden${widthClass}"
                 title="Focus Now">
                <img src="assets/focus-now-mascot.png"
                     alt="Focus Now"
                     class="h-12 sm:h-14 w-auto object-contain shrink-0 select-none pointer-events-none group-hover:scale-105 transition-transform" />
                <div class="pl-2 z-10 text-right sm:text-left">
                    <h3 class="text-base sm:text-lg font-bold text-white leading-tight">
                        Focus Now
                    </h3>
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
                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${t.bg} ${t.text}">
                    ${escapeHtml(t.label)}
                </span>
            `).join(' ');

            const commentsCount = (post.comments && post.comments.length > 0) ? post.comments.length : (post.commentsCount || 0);

            // Sub-reply preview matching original Reference
            let replyPreviewHTML = '';
            if (Array.isArray(post.comments) && post.comments.length > 0) {
                replyPreviewHTML = `
                    <div class="pt-2.5 border-t border-[#F0ECE9] space-y-2 text-[11px]">
                        ${post.comments.slice(0, 2).map(c => `
                            <div class="space-y-0.5">
                                <div class="flex items-center space-x-1.5">
                                    <span class="text-xs">🎨</span>
                                    <span class="font-bold text-[#202124]">${escapeHtml(c.author)}</span>
                                    <span class="text-[#8E8A85] text-[10px]">${escapeHtml(c.time || '')}</span>
                                </div>
                                <p class="text-[#5A5550] pl-5 leading-snug">${escapeHtml(c.text)}</p>
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            return `
                <div onclick="window.TempoApp.navigateTo('community'); if(window.TempoCommunity) { window.TempoCommunity.selectTab('posts'); setTimeout(() => { const el = document.querySelector('[data-post-id=\\'${post.id}\\']'); if(el) el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 150); }"
                     class="bg-white border border-[#DE8662] rounded-2xl p-4 sm:p-5 space-y-2.5 shadow-2xs hover:shadow-xs transition cursor-pointer group"
                     title="Open post by ${escapeHtml(post.authorName)}">
                    <!-- Header -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2.5">
                            <img src="${escapeHtml(post.avatar)}" alt="${escapeHtml(post.authorName)}" class="w-9 h-9 rounded-full object-cover">
                            <div>
                                <h4 class="text-[13px] font-bold text-[#202124] leading-tight">${escapeHtml(post.authorName)}</h4>
                                <span class="text-[10px] text-[#8E8A85]">${escapeHtml(post.timeAgo || 'Recent')}</span>
                            </div>
                        </div>
                        <div class="flex items-center space-x-1.5">
                            ${tagsHTML}
                            <div class="p-1 text-[#4A4541] hover:text-[#DE8662]">
                                <img src="assets/bookmark_action_symbol.png" alt="Bookmark" class="w-3.5 h-3.5 object-contain opacity-70">
                            </div>
                        </div>
                    </div>

                    <!-- Content -->
                    <p class="text-xs sm:text-[12.5px] text-[#202124] leading-relaxed">
                        ${escapeHtml(post.content)}
                    </p>

                    <!-- Thumbnails if present -->
                    ${(post.thumbnails && post.thumbnails.length > 0) ? `
                        <div class="grid grid-cols-4 gap-1.5 pt-0.5 pb-0.5">
                            ${post.thumbnails.slice(0, 4).map(img => `
                                <div class="aspect-4/3 rounded-lg overflow-hidden bg-stone-100 border border-stone-200">
                                    <img src="${escapeHtml(img)}" alt="Attachment" class="w-full h-full object-cover">
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}

                    <!-- Action stats row -->
                    <div class="flex items-center space-x-4 text-[#4A4541] text-xs pt-1">
                        <span class="flex items-center space-x-1">
                            <span class="text-xs">♡</span>
                            <span>${post.likes || 0}</span>
                        </span>
                        <span class="flex items-center space-x-1">
                            <img src="assets/comment_action_symbol.png" alt="Comments" class="w-3.5 h-3.5 object-contain">
                            <span>${commentsCount}</span>
                        </span>
                        <span class="flex items-center space-x-1">
                            <img src="assets/message_action_symbol.png" alt="Message" class="w-3.5 h-3.5 object-contain">
                        </span>
                    </div>

                    <!-- Sub-replies snippet -->
                    ${replyPreviewHTML}
                </div>
            `;
        }).join('');
    }

    /**
     * REDESIGNED TEMPO ENTRYHOME
     * - Reduced Welcome Card height by ~50% (compact, balanced padding & spacing)
     * - Reduced Quick Relief and Focus Now cards by ~50% (h-[74px] sm:h-[80px])
     * - Restored original Tempo Community preview appearance (orange border, original cards)
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
            <div class="max-w-6xl mx-auto py-2 sm:py-4 space-y-6 sm:space-y-8 font-arimo" data-tempo-ui="entry-home">
                <!-- ==============================================================
                     UPPER SECTION: DESKTOP 2-COLUMN (LEFT: WELCOME + ACTIONS; RIGHT: COMMUNITY)
                     Using items-start so left column stays compact and matches ~50% reduced card heights
                     ============================================================== -->
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 sm:gap-7 items-start">
                    <!-- LEFT COLUMN (approx 58-60% width): Welcome Card + 2 Primary Action Cards -->
                    <div class="lg:col-span-7 flex flex-col space-y-4 sm:space-y-5">
                        <!-- Welcome / Hero Card (Reduced height by ~50%, balanced spacing) -->
                        <div class="bg-white border border-[#EAE4DF] rounded-3xl sm:rounded-[32px] p-6 sm:p-7 shadow-xs flex flex-col space-y-3.5 sm:space-y-4" data-tempo-ui="entry-welcome-card">
                            <div class="space-y-1.5">
                                <span class="text-sm sm:text-base font-bold text-[#DE8662] block tracking-wide">
                                    Welcome to Tempo
                                </span>
                                <h1 class="text-2xl sm:text-3xl lg:text-[36px] font-bold text-[#4A4541] tracking-tight leading-[1.15]">
                                    What do you need right now?
                                </h1>
                            </div>

                            <div class="pt-1">
                                <button type="button"
                                        id="btn-hero-figure-start"
                                        onclick="if (window.TempoApp && typeof window.TempoApp.openRoutingModal === 'function') { window.TempoApp.openRoutingModal(); } else if (window.TempoMode && typeof window.TempoMode.openHelpSelectionModal === 'function') { window.TempoMode.openHelpSelectionModal(); } else { const m = document.getElementById('modal-routing-selection'); if (m) { m.classList.remove('hidden'); document.body.classList.add('overflow-hidden'); } }"
                                        class="px-5 sm:px-6 py-2.5 sm:py-3 rounded-2xl bg-[#D28C74] hover:bg-[#C27C64] text-white font-bold text-sm sm:text-base shadow-xs transition inline-flex items-center space-x-2 cursor-pointer group">
                                    <span>Help me figure out where to start</span>
                                    <span class="group-hover:translate-x-1 transition-transform">→</span>
                                </button>
                            </div>
                        </div>

                        <!-- Two Action Cards Row directly below Welcome Card (Reduced height by ~50%) -->
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5" data-tempo-ui="entry-action-cards">
                            <!-- Action Card 1: Quick Relief -->
                            ${renderQuickReliefCardHTML()}

                            <!-- Action Card 2: Focus Now -->
                            ${renderFocusNowCardHTML()}
                        </div>
                    </div>

                    <!-- RIGHT COLUMN (approx 40-42% width): From the Tempo Community -->
                    <div class="lg:col-span-5 flex flex-col">
                        <div class="bg-white border border-[#EAE4DF] rounded-3xl sm:rounded-[32px] p-5 sm:p-6 shadow-xs flex flex-col space-y-4" data-tempo-ui="entry-community-panel">
                            <!-- Header -->
                            <div class="flex items-center justify-between pb-1">
                                <div class="flex items-center space-x-2.5">
                                    <div class="w-7 h-7 rounded-xl bg-[#F6E6DE] flex items-center justify-center shrink-0">
                                        <img src="assets/comment_action_symbol.png" alt="Community" class="w-4 h-4 object-contain" />
                                    </div>
                                    <h3 class="font-bold text-base sm:text-[17px] text-[#4A4541] tracking-tight">
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
                            <div id="homepage-community-posts-list" class="space-y-3.5 flex-1 flex flex-col">
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

    # Ensure strictly LF
    mode_content = mode_content.replace('\r\n', '\n')
    with open('mode.js', 'wb') as f:
        f.write(mode_content.encode('utf-8'))
    print("3. mode.js: Applied ~50% height reductions to Welcome card and Action cards, restored community preview markup (LF preserved).")

    print("\nAll targeted corrections applied successfully!")

if __name__ == '__main__':
    apply_corrections()
