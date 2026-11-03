# -*- coding: utf-8 -*-
import sys

def main():
    print("Redesigning Tempo EntryHome...")

    # =========================================================================
    # 1. UPDATE mode.js (Preserve LF)
    # =========================================================================
    with open('mode.js', 'r', encoding='utf-8') as f:
        mode_content = f.read()

    # Check background in applyModeVisibility
    target_bg = """        } else {
            document.body.style.backgroundColor = '';
            if (mainEl) mainEl.style.backgroundColor = '';
        }"""
    replace_bg = """        } else {
            document.body.style.backgroundColor = '#FAF7F2';
            if (mainEl) mainEl.style.backgroundColor = '#FAF7F2';
        }"""
    if target_bg in mode_content:
        mode_content = mode_content.replace(target_bg, replace_bg, 1)

    # Locate renderQuickReliefCardHTML through renderEntryHomeHTML
    p_start = mode_content.find('    function renderQuickReliefCardHTML(extraClass = \'\') {')
    p_end = mode_content.find('    function renderDmodeHome() {')
    assert p_start != -1 and p_end != -1, "mode.js boundaries not found"

    new_mode_chunk = """    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function renderQuickReliefCardHTML(extraClass = '') {
        const widthClass = extraClass ? ` ${extraClass}` : '';
        return `
            <div onclick="if (window.TempoStressRelief && window.TempoStressRelief.openModal) { window.TempoStressRelief.openModal(); } else if (window.TempoTriage && window.TempoTriage.openQuickReliefModal) { window.TempoTriage.openQuickReliefModal(); }"
                 role="button"
                 tabindex="0"
                 aria-label="Quick Relief"
                 onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); this.click(); }"
                 class="bg-[#DEECE5] border border-[#728F83]/30 rounded-3xl p-5 sm:p-6 flex items-center justify-between h-[140px] sm:h-[150px] shadow-xs hover:shadow-md transition cursor-pointer group relative overflow-hidden${widthClass}"
                 title="Quick Relief">
                <div class="pr-2 z-10">
                    <h3 class="text-xl sm:text-[22px] font-bold text-[#6D8A7E] leading-tight">
                        Quick Relief
                    </h3>
                </div>
                <img src="assets/quick-relief-mascot-transparent.png"
                     alt="Quick Relief"
                     class="h-24 sm:h-28 w-auto object-contain shrink-0 select-none pointer-events-none -mr-2 group-hover:scale-105 transition-transform" />
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
                 class="bg-[#D29C85] border border-[#4A4541]/20 rounded-3xl p-5 sm:p-6 flex items-center justify-between h-[140px] sm:h-[150px] shadow-xs hover:shadow-md transition cursor-pointer group relative overflow-hidden${widthClass}"
                 title="Focus Now">
                <img src="assets/focus-now-mascot.png"
                     alt="Focus Now"
                     class="h-24 sm:h-28 w-auto object-contain shrink-0 select-none pointer-events-none -ml-3 group-hover:scale-105 transition-transform" />
                <div class="pl-2 z-10 text-right sm:text-left">
                    <h3 class="text-xl sm:text-[22px] font-bold text-white leading-tight">
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
                <div class="h-64 flex flex-col items-center justify-center text-center p-6 space-y-2 text-[#8E8A85]">
                    <img src="assets/comment_action_symbol.png" alt="No posts" class="w-6 h-6 opacity-40 object-contain mb-0.5">
                    <p class="text-xs font-bold text-[#5A5550]">No community posts yet</p>
                    <p class="text-[10.5px] text-[#8E8A85] leading-relaxed">Be the first to share with your peers in the community.</p>
                </div>
            `;
        }

        return previewPosts.slice(0, 2).map(post => {
            const tagsHTML = (post.tags || []).map(t => `
                <span class="px-2 py-0.5 rounded-full text-[9.5px] font-bold ${t.bg} ${t.text}">
                    ${escapeHtml(t.label)}
                </span>
            `).join(' ');

            const commentsCount = (post.comments && post.comments.length > 0) ? post.comments.length : (post.commentsCount || 0);

            // Sub-reply preview for post-1 if available (matching Reference Screenshot 1)
            let replyPreviewHTML = '';
            if (Array.isArray(post.comments) && post.comments.length > 0) {
                const firstComment = post.comments[0];
                const secondComment = post.comments.length > 1 ? post.comments[1] : null;
                replyPreviewHTML = `
                    <div class="pt-2 border-t border-[#F0ECE9] space-y-1.5 text-[10.5px]">
                        <div class="flex items-center space-x-1.5">
                            <img src="${escapeHtml(firstComment.avatar || 'assets/tempo-logo.png')}" alt="${escapeHtml(firstComment.author)}" class="w-4 h-4 rounded-full object-cover">
                            <span class="font-bold text-[#202124]">${escapeHtml(firstComment.author)}</span>
                            <span class="text-[#8E8A85] text-[9px]">${escapeHtml(firstComment.time || '')}</span>
                        </div>
                        <p class="text-[#5A5550] pl-5.5 leading-snug">${escapeHtml(firstComment.text)}</p>

                        ${secondComment ? `
                            <div class="flex items-center space-x-1.5 pt-0.5 pl-3">
                                <img src="${escapeHtml(secondComment.avatar || 'assets/tempo-logo.png')}" alt="${escapeHtml(secondComment.author)}" class="w-3.5 h-3.5 rounded-full object-cover">
                                <span class="font-bold text-[#202124]">${escapeHtml(secondComment.author)}</span>
                                <span class="text-[#8E8A85] text-[9px]">${escapeHtml(secondComment.time || '')}</span>
                            </div>
                            <p class="text-[#5A5550] pl-8.5 leading-snug">${escapeHtml(secondComment.text)}</p>
                        ` : ''}
                    </div>
                `;
            }

            return `
                <div onclick="window.TempoApp.navigateTo('community'); if(window.TempoCommunity) { window.TempoCommunity.selectTab('posts'); setTimeout(() => { const el = document.querySelector('[data-post-id=\\'${post.id}\\']'); if(el) el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 150); }"
                     class="bg-white border border-[#4A4541]/40 rounded-2xl p-4 sm:p-4.5 space-y-2.5 shadow-2xs hover:border-[#DE8662] transition cursor-pointer group"
                     title="Open post by ${escapeHtml(post.authorName)}">
                    <!-- Header -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <img src="${escapeHtml(post.avatar)}" alt="${escapeHtml(post.authorName)}" class="w-7 h-7 sm:w-8 sm:h-8 rounded-full object-cover">
                            <div>
                                <h4 class="text-xs sm:text-[12.5px] font-bold text-[#202124] leading-tight">${escapeHtml(post.authorName)}</h4>
                                <span class="text-[9.5px] text-[#8E8A85]">${escapeHtml(post.timeAgo || 'Recent')}</span>
                            </div>
                        </div>
                        <div class="flex items-center space-x-1.5">
                            ${tagsHTML}
                            <div class="p-1 text-[#4A4541] hover:text-[#DE8662]">
                                <img src="assets/bookmark_action_symbol.png" alt="Bookmark" class="w-3 h-3 object-contain opacity-70">
                            </div>
                        </div>
                    </div>

                    <!-- Content -->
                    <p class="text-xs text-[#202124] leading-relaxed line-clamp-2">
                        ${escapeHtml(post.content)}
                    </p>

                    <!-- Thumbnails if present (Post 2 in Screenshot 1) -->
                    ${(post.thumbnails && post.thumbnails.length > 0) ? `
                        <div class="grid grid-cols-4 gap-1.5 pt-0.5">
                            ${post.thumbnails.slice(0, 4).map(img => `
                                <div class="aspect-4/3 rounded-lg overflow-hidden bg-stone-100 border border-stone-200">
                                    <img src="${escapeHtml(img)}" alt="Attachment" class="w-full h-full object-cover">
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}

                    <!-- Action stats row -->
                    <div class="flex items-center space-x-4 text-[#4A4541] text-[11px] pt-1">
                        <span class="flex items-center space-x-1">
                            <span class="text-xs">♡</span>
                            <span>${post.likes || 0}</span>
                        </span>
                        <span class="flex items-center space-x-1">
                            <img src="assets/comment_action_symbol.png" alt="Comments" class="w-3 h-3 object-contain">
                            <span>${commentsCount}</span>
                        </span>
                        <span class="flex items-center space-x-1">
                            <img src="assets/message_action_symbol.png" alt="Message" class="w-3 h-3 object-contain">
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
     * Faithful desktop reproduction of user-supplied references:
     * - Reference 1: Welcome Card + Quick Relief & Focus Now (Left) | From the Tempo Community (Right)
     * - Reference 2: 3-Card Row (Self-check • Work Plan • Notes)
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
            <div class="max-w-6xl mx-auto py-2 sm:py-4 space-y-8 sm:space-y-10 font-arimo" data-tempo-ui="entry-home">
                <!-- ==============================================================
                     UPPER SECTION: DESKTOP 2-COLUMN (LEFT: WELCOME + ACTIONS; RIGHT: COMMUNITY)
                     ============================================================== -->
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 sm:gap-7 items-stretch">
                    <!-- LEFT COLUMN (approx 58-60% width): Welcome Card + 2 Primary Action Cards -->
                    <div class="lg:col-span-7 flex flex-col justify-between space-y-5 sm:space-y-6">
                        <!-- Welcome / Hero Card (Reference Screenshot 1) -->
                        <div class="bg-white border border-[#EAE4DF] rounded-3xl sm:rounded-[32px] p-7 sm:p-9 shadow-xs flex flex-col justify-between flex-1 min-h-[240px] sm:min-h-[260px]" data-tempo-ui="entry-welcome-card">
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

                        <!-- Two Action Cards Row directly below Welcome Card (Reference Screenshot 1) -->
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5" data-tempo-ui="entry-action-cards">
                            <!-- Action Card 1: Quick Relief -->
                            ${renderQuickReliefCardHTML()}

                            <!-- Action Card 2: Focus Now -->
                            ${renderFocusNowCardHTML()}
                        </div>
                    </div>

                    <!-- RIGHT COLUMN (approx 40-42% width): From the Tempo Community (Reference Screenshot 1) -->
                    <div class="lg:col-span-5 flex flex-col">
                        <div class="bg-white border border-[#EAE4DF] rounded-3xl sm:rounded-[32px] p-5 sm:p-6 shadow-xs flex flex-col justify-between h-full space-y-4" data-tempo-ui="entry-community-panel">
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
                                        class="px-3 py-1 rounded-full bg-[#FCEFE8] hover:bg-[#F8E1D5] text-[#DE8662] text-xs font-bold transition flex items-center space-x-1 cursor-pointer">
                                    <span>See all</span>
                                    <span>→</span>
                                </button>
                            </div>

                            <!-- Community Previews Container -->
                            <div id="homepage-community-posts-list" class="space-y-3.5 flex-1 flex flex-col justify-between">
                                ${renderCommunityPreviewsHTML(previewPosts)}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- ==============================================================
                     LOWER SECTION: 3 SECONDARY FEATURE CARDS ROW (Reference Screenshot 2)
                     (Self-check • Work Plan • Notes)
                     ============================================================== -->
                <div class="pt-2 sm:pt-4" data-tempo-ui="entry-secondary-cards">
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-7">
                        <!-- Card 1: Self-check (Soft Sage) -->
                        <div onclick="if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('open', { sourceContext: 'entry' }); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; }"
                             role="button"
                             tabindex="0"
                             aria-label="Self-check"
                             onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); this.click(); }"
                             class="bg-[#DEECE5] border border-[#728F83]/20 rounded-3xl sm:rounded-[28px] h-[190px] sm:h-[210px] p-6 flex items-center justify-center shadow-xs hover:shadow-md hover:scale-[1.01] transition cursor-pointer relative group overflow-hidden"
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
                             class="bg-[#FBE9DF] border border-[#F0D5CC]/40 rounded-3xl sm:rounded-[28px] h-[190px] sm:h-[210px] p-6 flex items-center justify-center shadow-xs hover:shadow-md hover:scale-[1.01] transition cursor-pointer relative group overflow-hidden"
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
                             class="bg-[#F9EFE0] border border-[#F1DFC0]/50 rounded-3xl sm:rounded-[28px] h-[190px] sm:h-[210px] p-6 flex items-center justify-center shadow-xs hover:shadow-md hover:scale-[1.01] transition cursor-pointer relative group overflow-hidden"
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

    mode_content = mode_content[:p_start] + new_mode_chunk + mode_content[p_end:]

    # Ensure strictly LF
    mode_content = mode_content.replace('\r\n', '\n')
    with open('mode.js', 'wb') as f:
        f.write(mode_content.encode('utf-8'))
    print("mode.js updated with strictly LF line endings!")

    # =========================================================================
    # 2. UPDATE communityPosts.js (Preserve CRLF)
    # =========================================================================
    with open('communityPosts.js', 'r', encoding='utf-8') as f:
        comm_content = f.read()

    # Update renderHomepagePreview in communityPosts.js to use the rich preview format
    p_hp_start = comm_content.find('    function renderHomepagePreview() {')
    p_hp_end = comm_content.find('    function renderUrgentPreview() {')
    assert p_hp_start != -1 and p_hp_end != -1, "communityPosts.js preview boundaries not found"

    new_hp_chunk = """    function renderHomepagePreview() {
        const container = document.getElementById('homepage-community-posts-list');
        if (!container) return;
        const previewPosts = posts.slice(0, 2);
        if (previewPosts.length === 0) {
            container.innerHTML = `
                <div class="h-64 flex flex-col items-center justify-center text-center p-6 space-y-2 text-[#8E8A85]">
                    <img src="assets/comment_action_symbol.png" alt="No posts" class="w-6 h-6 opacity-40 object-contain mb-0.5">
                    <p class="text-xs font-bold text-[#5A5550]">No community posts yet</p>
                    <p class="text-[10.5px] text-[#8E8A85] leading-relaxed">Be the first to share with your peers in the community.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = previewPosts.map(post => {
            const tagsHTML = (post.tags || []).map(t => `
                <span class="px-2 py-0.5 rounded-full text-[9.5px] font-bold ${t.bg} ${t.text}">
                    ${escapeHtml(t.label)}
                </span>
            `).join(' ');

            const commentsCount = (post.comments && post.comments.length > 0) ? post.comments.length : (post.commentsCount || 0);

            let replyPreviewHTML = '';
            if (Array.isArray(post.comments) && post.comments.length > 0) {
                const firstComment = post.comments[0];
                const secondComment = post.comments.length > 1 ? post.comments[1] : null;
                replyPreviewHTML = `
                    <div class="pt-2 border-t border-[#F0ECE9] space-y-1.5 text-[10.5px]">
                        <div class="flex items-center space-x-1.5">
                            <img src="${escapeHtml(firstComment.avatar || 'assets/tempo-logo.png')}" alt="${escapeHtml(firstComment.author)}" class="w-4 h-4 rounded-full object-cover">
                            <span class="font-bold text-[#202124]">${escapeHtml(firstComment.author)}</span>
                            <span class="text-[#8E8A85] text-[9px]">${escapeHtml(firstComment.time || '')}</span>
                        </div>
                        <p class="text-[#5A5550] pl-5.5 leading-snug">${escapeHtml(firstComment.text)}</p>

                        ${secondComment ? `
                            <div class="flex items-center space-x-1.5 pt-0.5 pl-3">
                                <img src="${escapeHtml(secondComment.avatar || 'assets/tempo-logo.png')}" alt="${escapeHtml(secondComment.author)}" class="w-3.5 h-3.5 rounded-full object-cover">
                                <span class="font-bold text-[#202124]">${escapeHtml(secondComment.author)}</span>
                                <span class="text-[#8E8A85] text-[9px]">${escapeHtml(secondComment.time || '')}</span>
                            </div>
                            <p class="text-[#5A5550] pl-8.5 leading-snug">${escapeHtml(secondComment.text)}</p>
                        ` : ''}
                    </div>
                `;
            }

            return `
                <div onclick="window.TempoApp.navigateTo('community'); if(window.TempoCommunity) { window.TempoCommunity.selectTab('posts'); setTimeout(() => { const el = document.querySelector('[data-post-id=\\'${post.id}\\']'); if(el) el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 150); }"
                     class="bg-white border border-[#4A4541]/40 rounded-2xl p-4 sm:p-4.5 space-y-2.5 shadow-2xs hover:border-[#DE8662] transition cursor-pointer group"
                     title="Open post by ${escapeHtml(post.authorName)}">
                    <!-- Header -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <img src="${escapeHtml(post.avatar)}" alt="${escapeHtml(post.authorName)}" class="w-7 h-7 sm:w-8 sm:h-8 rounded-full object-cover">
                            <div>
                                <h4 class="text-xs sm:text-[12.5px] font-bold text-[#202124] leading-tight">${escapeHtml(post.authorName)}</h4>
                                <span class="text-[9.5px] text-[#8E8A85]">${escapeHtml(post.timeAgo || 'Recent')}</span>
                            </div>
                        </div>
                        <div class="flex items-center space-x-1.5">
                            ${tagsHTML}
                            <div class="p-1 text-[#4A4541] hover:text-[#DE8662]">
                                <img src="assets/bookmark_action_symbol.png" alt="Bookmark" class="w-3 h-3 object-contain opacity-70">
                            </div>
                        </div>
                    </div>

                    <!-- Content -->
                    <p class="text-xs text-[#202124] leading-relaxed line-clamp-2">
                        ${escapeHtml(post.content)}
                    </p>

                    <!-- Thumbnails if present -->
                    ${(post.thumbnails && post.thumbnails.length > 0) ? `
                        <div class="grid grid-cols-4 gap-1.5 pt-0.5">
                            ${post.thumbnails.slice(0, 4).map(img => `
                                <div class="aspect-4/3 rounded-lg overflow-hidden bg-stone-100 border border-stone-200">
                                    <img src="${escapeHtml(img)}" alt="Attachment" class="w-full h-full object-cover">
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}

                    <!-- Action stats row -->
                    <div class="flex items-center space-x-4 text-[#4A4541] text-[11px] pt-1">
                        <span class="flex items-center space-x-1">
                            <span class="text-xs">♡</span>
                            <span>${post.likes || 0}</span>
                        </span>
                        <span class="flex items-center space-x-1">
                            <img src="assets/comment_action_symbol.png" alt="Comments" class="w-3 h-3 object-contain">
                            <span>${commentsCount}</span>
                        </span>
                        <span class="flex items-center space-x-1">
                            <img src="assets/message_action_symbol.png" alt="Message" class="w-3 h-3 object-contain">
                        </span>
                    </div>

                    <!-- Sub-replies snippet -->
                    ${replyPreviewHTML}
                </div>
            `;
        }).join('');
    }\n\n"""

    if '\r\n' in comm_content:
        new_hp_chunk = new_hp_chunk.replace('\n', '\r\n')

    comm_content = comm_content[:p_hp_start] + new_hp_chunk + comm_content[p_hp_end:]

    # Ensure strictly CRLF
    if '\r\n' not in comm_content:
        comm_content = comm_content.replace('\n', '\r\n')
    with open('communityPosts.js', 'wb') as f:
        f.write(comm_content.encode('utf-8'))
    print("communityPosts.js updated with strictly CRLF line endings!")

    # =========================================================================
    # 3. UPDATE index.html (Preserve CRLF)
    # =========================================================================
    with open('index.html', 'r', encoding='utf-8') as f:
        idx_content = f.read()

    # Update body class for warm cream background
    idx_content = idx_content.replace(
        '<body class="bg-[#F6F0EB]',
        '<body class="bg-[#FAF7F2]'
    )

    # Update header background and border
    idx_content = idx_content.replace(
        '<header class="bg-[#FEFAF4] border-b border-[#E8E4E1]',
        '<header class="bg-[#FAF7F2] border-b border-[#EAE4DF]'
    )

    # Update logo height in header
    idx_content = idx_content.replace(
        'class="h-14 sm:h-[62px] lg:h-[80px] w-auto object-contain block"',
        'class="h-9 sm:h-10 w-auto object-contain block"'
    )

    # Update nav links text color to #4A4541
    idx_content = idx_content.replace(
        'text-sm sm:text-[15px] font-semibold text-[#736F68]',
        'text-sm sm:text-[15px] font-bold text-[#4A4541]'
    )

    # Ensure strictly CRLF
    if '\r\n' not in idx_content:
        idx_content = idx_content.replace('\n', '\r\n')
    with open('index.html', 'wb') as f:
        f.write(idx_content.encode('utf-8'))
    print("index.html updated with strictly CRLF line endings!")

    print("Redesign successfully applied across all files!")

if __name__ == '__main__':
    main()
