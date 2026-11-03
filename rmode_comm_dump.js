function renderRecoveryCommunityCard() {
        let allPosts = (window.TempoCommunity && typeof window.TempoCommunity.getAllPosts === 'function')
            ? window.TempoCommunity.getAllPosts()
            : [];
        if (!Array.isArray(allPosts) || allPosts.length === 0) {
            if (window.TempoCommunity && typeof window.TempoCommunity.getInitialPosts === 'function') {
                allPosts = window.TempoCommunity.getInitialPosts();
            }
        }
        const distinctPosts = (window.TempoCommunity && typeof window.TempoCommunity.getDistinctPosts === 'function')
            ? window.TempoCommunity.getDistinctPosts(allPosts, 2)
            : (Array.isArray(allPosts) ? allPosts.slice(0, 2) : []);

        let postsCardsHTML = '';
        if (distinctPosts.length > 0) {
            if (window.TempoCommunity && typeof window.TempoCommunity.renderPreviewPostCardHTML === 'function') {
                postsCardsHTML = distinctPosts.map(p => window.TempoCommunity.renderPreviewPostCardHTML(p)).join('');
            } else if (typeof renderCommunityPreviewsHTML === 'function') {
                postsCardsHTML = renderCommunityPreviewsHTML(distinctPosts);
            }
        } else {
            postsCardsHTML = `
                <div class="h-48 flex flex-col items-center justify-center text-center p-6 space-y-2 text-[#8E8A85]">
                    <img src="assets/comment_action_symbol.png" alt="No posts" class="w-6 h-6 opacity-40 object-contain mb-0.5">
                    <p class="text-xs font-bold text-[#5A5550]">No community posts yet</p>
                    <p class="text-[10.5px] text-[#8E8A85] leading-relaxed">Be the first to share with your peers in the community.</p>
                </div>
            `;
        }

        return `
            <div class="recovery-section-posts bg-[#FEFAF4] border border-[#EAE4DF] rounded-3xl sm:rounded-[32px] p-4.5 sm:p-5 shadow-xs flex flex-col justify-between space-y-3.5 box-border w-full" 
                 data-tempo-ui="recovery-community">
                <!-- Header -->
                <div class="flex items-center justify-between pb-0.5 w-full">
                    <div class="flex items-center space-x-2.5">
                        <div class="w-8 h-8 rounded-full bg-[#F6E6DE] flex items-center justify-center shrink-0">
                            <img src="assets/comment_action_symbol.png" alt="Community" class="w-4 h-4 object-contain" />
                        </div>
                        <h3 class="font-bold text-base sm:text-lg text-[#55504C] tracking-tight">
                            ${window.t ? window.t('modes.recovery.fromCommunity', {}, (isViLocale() ? 'Cộng đồng Tempo' : 'From the Tempo Community')) : (isViLocale() ? 'Cộng đồng Tempo' : 'From the Tempo Community')}
                        </h3>
                    </div>
                    <button type="button" 
                            id="btn-see-all-posts-recovery"
                            onclick="if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('community'); } else { window.location.hash = '#community?tab=posts'; } if (window.TempoCommunity && typeof window.TempoCommunity.selectTab === 'function') { window.TempoCommunity.selectTab('posts'); }" 
                            class="px-3.5 py-1 rounded-full bg-[#FCEFE8] hover:bg-[#F8E1D5] text-[#DE8662] text-xs font-bold transition flex items-center space-x-1 cursor-pointer"
                            aria-label="${isViLocale() ? 'Xem tất cả →' : 'View all →'}" title="${isViLocale() ? 'Xem tất cả →' : 'View all →'}">
                        <span>${(window.t ? (window.t('modes.recovery.viewAll') || window.t('modes.recovery.seeAll')) : null) || (isViLocale() ? 'Xem tất cả' : 'View all')}</span>
                        <span class="text-xs">&rarr;</span>
                    </button>
                </div>

                <!-- Social Post Previews -->
                <div id="recovery-community-posts-list" class="space-y-3 flex-1 flex flex-col justify-between w-full">
                    ${postsCardsHTML}
                </div>
            </div>
        `;
    }

    // Preserved for backwards compatibility - Enjoy Tempo Tools section removed from Rmode
    