function renderEmodeCreateNotesCard(ctx) {
        const todayStr = (ctx && ctx.todayStr) || (typeof getTodayISOString === 'function' ? getTodayISOString() : new Date().toISOString().slice(0, 10));
        const dayNotes = getUmodeDayNotesForToday(todayStr);
        const isVi = typeof isViLocale === 'function' ? isViLocale() : (window.TempoI18n?.getCurrentLanguage?.() === 'vi');
        const createNoteForTodayLabel = window.t ? window.t('modes.urgent.createNoteForToday', {}, (isVi ? 'Tạo ghi chú cho hôm nay' : 'Create a note for today')) : (isVi ? 'Tạo ghi chú cho hôm nay' : 'Create a note for today');
        const createNotesTitleLabel = window.t ? window.t('modes.urgent.createNotes', {}, (isVi ? 'Tạo Notes' : 'Create Notes')) : (isVi ? 'Tạo Notes' : 'Create Notes');
        const viewMyNotesLabel = window.t ? window.t('modes.urgent.viewMyNotes', {}, (isVi ? 'Xem ghi chú' : 'View my notes')) : (isVi ? 'Xem ghi chú' : 'View my notes');

        let notesListHTML = '';
        if (!dayNotes || dayNotes.length === 0) {
            notesListHTML = `
                <div data-no-card-click="true"
                     onclick="event.stopPropagation(); if (window.TempoToolNotes && typeof window.TempoToolNotes.openCreateNoteModal === 'function') { window.TempoToolNotes.openCreateNoteModal('day'); }"
                     class="h-full min-h-[78px] flex flex-col items-center justify-center text-center px-3 py-2 bg-[#FCF5F0]/70 hover:bg-[#F6E3DA] border border-dashed border-[#E8D5CA] hover:border-[#D79277] rounded-2xl transition cursor-pointer select-none group" 
                     data-tempo-ui="notes-empty-state"
                     title="${escapeHTML(createNoteForTodayLabel)}">
                    <span class="text-base text-[#B87561] mb-0.5 group-hover:scale-110 transition-transform">📝</span>
                    <p class="text-xs font-semibold text-[#8C7D75] group-hover:text-[#554741] transition-colors">${escapeHTML(createNoteForTodayLabel)}</p>
                </div>
            `;
        } else {
            notesListHTML = `
                <div class="overflow-y-auto max-h-[96px] space-y-1.5 pr-1 text-left custom-scrollbar" data-tempo-ui="notes-scroll-list" style="max-height: 96px; overflow-y: auto;">
                    ${dayNotes.map(n => {
                        const noteText = escapeHTML(n.text || n.content || n.note || '');
                        const timeStr = formatNoteTime(n);
                        const safeId = escapeHTML(String(n.id || ''));
                        return `
                            <div data-no-card-click="true"
                                 onclick="event.stopPropagation(); if (window.TempoToolNotes && typeof window.TempoToolNotes.openNoteDetailModal === 'function') { window.TempoToolNotes.openNoteDetailModal('${safeId}'); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('notes'); }"
                                 class="bg-white/90 hover:bg-white border border-[#EBDCD3] hover:border-[#D9C4B7] rounded-xl px-2.5 py-1.5 transition text-xs shadow-2xs group cursor-pointer" 
                                 data-day-note-id="${safeId}"
                                 title="Click to view full note details">
                                <div class="flex items-center justify-between gap-1 mb-0.5 pointer-events-none">
                                    <span class="text-[10px] font-bold uppercase tracking-wider text-[#B87561] flex items-center gap-1">
                                        <span>📝</span>
                                        <span>Day Note</span>
                                    </span>
                                    ${timeStr ? `<span class="text-[10px] text-[#9E9087] font-medium">${escapeHTML(timeStr)}</span>` : ''}
                                </div>
                                <p class="text-[11.5px] text-[#484541] font-medium leading-snug line-clamp-2 break-words pointer-events-none">
                                    ${noteText}
                                </p>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }

        return `
            <div class="w-full min-h-[122px] max-h-[122px] h-[122px] bg-[#F9E8E2] border border-[#E8D5CA] rounded-3xl p-3.5 sm:p-4 shadow-xs flex flex-row items-center justify-between box-border relative overflow-hidden cursor-pointer" 
                 data-tempo-ui="urmode-create-notes" 
                 onclick="if (event.target.closest('[data-no-card-click]')) return; if (window.TempoToolNotes && typeof window.TempoToolNotes.openCreateNoteModal === 'function') { window.TempoToolNotes.openCreateNoteModal('day'); }"
                 title="Click to create a note"
                 style="width: 100%; height: 122px; min-height: 122px; max-height: 122px; box-sizing: border-box; overflow: hidden;">
                <!-- Left: Title & View Button -->
                <div class="flex flex-col justify-between shrink-0 space-y-2 pr-3 sm:pr-4 border-r border-[#E8D5CA]/70" data-tempo-ui="notes-text-block" style="min-width: 120px; max-width: 135px;">
                    <h3 class="text-lg sm:text-xl font-bold text-[#554741] leading-tight tracking-tight">
                        ${escapeHTML(createNotesTitleLabel)}
                    </h3>
                    <div>
                        <button type="button"
                                data-no-card-click="true"
                                onclick="event.stopPropagation(); if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('notes'); } else { window.location.hash = '#notes'; }"
                                class="px-3 py-1.5 rounded-xl font-bold text-xs bg-[#C88E7D] hover:bg-[#B97F6E] text-white shadow-2xs transition cursor-pointer inline-flex items-center justify-center whitespace-nowrap">
                            ${escapeHTML(viewMyNotesLabel)}
                        </button>
                    </div>
                </div>

                <!-- Right: Today's Day Notes List (Scrollable) -->
                <div class="flex-1 min-w-0 pl-3 sm:pl-4 h-full flex flex-col justify-center" data-tempo-ui="notes-list-container">
                    ${notesListHTML}
                </div>
            </div>
        `;
    }

    function refreshNotesCardIfPresent() {
        const cardEls = document.querySelectorAll('[data-tempo-ui="urmode-create-notes"]');
        if (!cardEls || cardEls.length === 0) return;
        cardEls.forEach(cardEl => {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = renderEmodeCreateNotesCard().trim();
            const newCard = tempDiv.firstElementChild;
            if (newCard) {
                cardEl.replaceWith(newCard);
            }
        });
    }

    function renderLowerCreateNotesCard() {
        return renderEmodeCreateNotesCard();
    }

    // -------------------------------------------------------------------------
    // LOWER SCROLL SECTION: Reconstructed Two-Column Dashboard Section
    // -------------------------------------------------------------------------
    function renderEmodeLowerSection() {
        return `
            <div id="urgent-rebuilt-section" class="pt-8 border-t border-[#D0E0D7] mt-8 w-full" data-tempo-ui="urgent-lower-section">
                <div class="max-w-[960px] mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-5 lg:gap-6 items-start lg:translate-x-[59.25px]" data-tempo-ui="urgent-lower-grid">
                    
                    <!-- LEFT COLUMN (approx 58%): Self-check Streak -->
                    <div class="lg:col-span-7 flex flex-col space-y-4 w-full">
                        ${renderLowerSelfCheckStreakCard()}
                    </div>

                    <!-- RIGHT COLUMN (approx 42%): Từ Cộng đồng Tempo Panel -->
                    <div class="lg:col-span-5 w-full flex flex-col items-center">
                        ${renderTempoPostsSection()}
                    </div>

                </div>
                <style>
                    @media (min-width: 1024px) {
                        [data-tempo-ui="urgent-lower-grid"] {
                            transform: translateX(59.25px);
                        }
                    }
                </style>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // -------------------------------------------------------------------------
    // TEMPO POSTS COMPONENT (Lightweight Community Social Feed Previews)
    // Visual design matches EntryHome Từ Cộng đồng Tempo preview exactly
    // -------------------------------------------------------------------------
    function renderTempoPostsSection() {
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
            <div class="urgent-section-posts bg-[#FEFAF4] border border-[#EAE4DF] rounded-3xl sm:rounded-[32px] p-4.5 sm:p-5 shadow-xs flex flex-col justify-between space-y-3.5 box-border" 
                 data-tempo-ui="urgent-posts"
                 style="width: calc(100% + 20px); margin-left: -10px; margin-right: -10px; box-sizing: border-box;">
                <!-- Header -->
                <div class="flex items-center justify-between pb-0.5 w-full">
                    <div class="flex items-center space-x-2.5">
                        <div class="w-8 h-8 rounded-full bg-[#F6E6DE] flex items-center justify-center shrink-0">
                            <img src="assets/comment_action_symbol.png" alt="Community" class="w-4 h-4 object-contain" />
                        </div>
                        <h3 class="font-bold text-base sm:text-lg text-[#55504C] tracking-tight">
                            ${window.t ? window.t('modes.urgent.fromCommunity', {}, (isViLocale() ? 'Cộng đồng Tempo' : 'From the Tempo Community')) : (isViLocale() ? 'Cộng đồng Tempo' : 'From the Tempo Community')}
                        </h3>
                    </div>
                    <button type="button" 
                            id="btn-see-all-posts-urgent"
                            onclick="if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('community'); } else { window.location.hash = '#community?tab=posts'; } if (window.TempoCommunity && typeof window.TempoCommunity.selectTab === 'function') { window.TempoCommunity.selectTab('posts'); }" 
                            class="px-3.5 py-1 rounded-full bg-[#FCEFE8] hover:bg-[#F8E1D5] text-[#DE8662] text-xs font-bold transition flex items-center space-x-1 cursor-pointer"
                            aria-label="${isViLocale() ? 'Xem tất cả →' : 'View all →'}" title="${isViLocale() ? 'Xem tất cả →' : 'View all →'}">
                        <span>${(window.t ? (window.t('modes.urgent.viewAll') || window.t('modes.urgent.seeAll')) : null) || (isViLocale() ? 'Xem tất cả' : 'View all')}</span>
                        <span class="text-xs">&rarr;</span>
                    </button>
                </div>

                <!-- Posts list -->
                <div id="urgent-community-posts-list" class="space-y-3 flex-1 flex flex-col justify-between w-full">
                    ${postsCardsHTML}
                </div>
            </div>
        `;
    }

    // Preserved for backwards compatibility
    function renderQuickToolsSection(modeContext = 'active') {
        return renderSupportRowHTML();
    }

    // =========================================================================
    // RECOVERY MODE HOME (RMODE) IMPLEMENTATION (PHASE 1)
    // =========================================================================

    let selfCheckConfigState = null;
    let recentlyConfigState = null;
    let weeklyReviewDismissed = false;
    let weeklyReviewOverrideReady = false;

    function getSelfCheckState() {
        if (selfCheckConfigState) return selfCheckConfigState;
        try {
            if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getState === 'function') {
                return window.TempoRecoverySelfCheck.getState();
            }
            const saved = localStorage.getItem('tempo_recovery_selfcheck_config');
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (e) {}
        return { type: 'STATE_A' }; // Default honest empty for Phase 1
    }

    function setSelfCheckState(state) {
        selfCheckConfigState = state;
        try {
            localStorage.setItem('tempo_recovery_selfcheck_config', JSON.stringify(state));
        } catch (e) {}
        if (activeContext === MODES.RECOVERY) renderRmodeHome();
    }

    function handleRecoveryIntroSetupClick() {
        if (window.TempoRecoverySetup) {
            if (typeof window.TempoRecoverySetup.open === 'function') {
                window.TempoRecoverySetup.open(1);
            }
            if (typeof window.TempoRecoverySetup.goToStage === 'function') {
                window.TempoRecoverySetup.goToStage(1);
            }
        } else if (typeof openStrack === 'function') {
            openStrack('setup', { stage: 1 });
        }
    }

    function handleAddTrackingDirectClick() {
        openStrack('open', { sourceContext: 'recovery', openAdjust: true });
    }

    function handleSelfCheckSetupClick() {
        handleRecoveryIntroSetupClick();
    }

    function handleSelfCheckAction(action) {
        openStrack(action);
    }

    function handleStreakCardCheckin() {
        if (window.TempoRecoverySelfCheck) {
            let active = (typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function')
                ? window.TempoRecoverySelfCheck.getActiveTrackers()
                : [];

            if (active.length === 0) {
                if (typeof window.TempoRecoverySelfCheck.openSetup === 'function') {
                    window.TempoRecoverySelfCheck.openSetup();
                } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                    window.TempoApp.navigateTo('stress-check');
                } else {
                    window.location.hash = '#stress-check';
                }
                return;
            }

            const todayCheckin = (typeof window.TempoRecoverySelfCheck.getTodayCheckin === 'function')
                ? window.TempoRecoverySelfCheck.getTodayCheckin()
                : null;

            // Check if all active trackers have been answered today
            let allAnswered = false;
            if (todayCheckin && active.length > 0) {
                const obs = (typeof window.TempoRecoverySelfCheck.getObservationsForCheckin === 'function')
                    ? window.TempoRecoverySelfCheck.getObservationsForCheckin(todayCheckin.id)
                    : [];
                const answeredIds = new Set(obs.filter(o => o.status === 'answered' && o.value !== null && o.value !== undefined && o.value !== '').map(o => o.tracker_id));
                active.forEach(trk => {
                    if (Array.isArray(trk.alias_ids)) {
                        for (const aid of trk.alias_ids) {
                            if (answeredIds.has(aid)) {
                                answeredIds.add(trk.id);
                                break;
                            }
                        }
                    }
                });
                allAnswered = active.every(t => answeredIds.has(t.id));
            }

            if (allAnswered) {
                // If user has already completed today's check-in, open the view modal (which includes "Edit check-in")
                if (typeof window.TempoRecoverySelfCheck.openViewToday === 'function') {
                    window.TempoRecoverySelfCheck.openViewToday();
                } else if (typeof window.TempoRecoverySelfCheck.openDailyCheckin === 'function') {
                    window.TempoRecoverySelfCheck.openDailyCheckin(true);
                } else {
                    openStrack('view', { sourceContext: 'emergency' });
                }
            } else {
                // If not yet completed (or partial), open daily check-in modal directly
                if (typeof window.TempoRecoverySelfCheck.openDailyCheckin === 'function') {
                    window.TempoRecoverySelfCheck.openDailyCheckin(Boolean(todayCheckin));
                } else {
                    openStrack('checkin', { sourceContext: 'emergency' });
                }
            }
        } else {
            openStrack('checkin', { sourceContext: 'emergency' });
        }
    }

    function refreshStreakCardIfPresent() {
        const cardEl = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
        if (cardEl && cardEl.parentNode) {
            const temp = document.createElement('div');
            temp.innerHTML = renderLowerSelfCheckStreakCard();
            if (temp.firstElementChild) {
                cardEl.parentNode.replaceChild(temp.firstElementChild, cardEl);
            }
            if (typeof syncUmodeCreateNotesAlignment === 'function') {
                requestAnimationFrame(syncUmodeCreateNotesAlignment);
            }
        }
    }

    let isSubmittingUmodeCheckin = false;

    function getUmodeSkippedTrackers() {
        const uid = (typeof getRmodeUserId === 'function') ? getRmodeUserId() : 'local_user';
        const todayStr = (typeof getRmodeTodayDateStr === 'function') ? getRmodeTodayDateStr() : new Date().toISOString().slice(0, 10);
        const key = `tempo_umode_skipped_trackers_${uid}_${todayStr}`;
        try {
            const raw = localStorage.getItem(key);
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            return [];
        }
    }

    function addUmodeSkippedTracker(trackerId) {
        if (!trackerId) return;
        const uid = (typeof getRmodeUserId === 'function') ? getRmodeUserId() : 'local_user';
        const todayStr = (typeof getRmodeTodayDateStr === 'function') ? getRmodeTodayDateStr() : new Date().toISOString().slice(0, 10);
        const key = `tempo_umode_skipped_trackers_${uid}_${todayStr}`;
        const list = getUmodeSkippedTrackers();
        if (!list.includes(trackerId)) {
            list.push(trackerId);
            try {
                localStorage.setItem(key, JSON.stringify(list));
            } catch (e) {}
        }
    }

    function removeUmodeSkippedTracker(trackerId) {
        if (!trackerId) return;
        const uid = (typeof getRmodeUserId === 'function') ? getRmodeUserId() : 'local_user';
        const todayStr = (typeof getRmodeTodayDateStr === 'function') ? getRmodeTodayDateStr() : new Date().toISOString().slice(0, 10);
        const key = `tempo_umode_skipped_trackers_${uid}_${todayStr}`;
        let list = getUmodeSkippedTrackers();
        list = list.filter(id => id !== trackerId);
        try {
            localStorage.setItem(key, JSON.stringify(list));
        } catch (e) {}
    }

    function resetUmodeSkippedTrackers() {
        const uid = (typeof getRmodeUserId === 'function') ? getRmodeUserId() : 'local_user';
        const todayStr = (typeof getRmodeTodayDateStr === 'function') ? getRmodeTodayDateStr() : new Date().toISOString().slice(0, 10);
        const key = `tempo_umode_skipped_trackers_${uid}_${todayStr}`;
        try {
            localStorage.removeItem(key);
        } catch (e) {}
        refreshStreakCardIfPresent();
    }

    function skipUmodeCurrentSelfCheck(trackerId) {
        if (isSubmittingUmodeCheckin) return;
        if (!trackerId) return;
        isSubmittingUmodeCheckin = true;
        try {
            addUmodeSkippedTracker(trackerId);
            refreshStreakCardIfPresent();
        } catch (e) {
            console.error("Failed to skip Umode self-check tracker:", e);
        } finally {
            setTimeout(() => { isSubmittingUmodeCheckin = false; }, 200);
        }
    }

    function handleUmodeSliderInput(inputEl, trackerId) {
        if (!inputEl) return;
        const val = Math.max(0, Math.min(100, parseInt(inputEl.value, 10) || 0));
        inputEl.setAttribute('aria-valuenow', val);
        const fill = document.getElementById('umode-slider-fill');
        if (fill) fill.style.width = val + '%';
        const thumb = document.getElementById('umode-slider-thumb');
        if (thumb) thumb.style.left = val + '%';
        const badge = document.getElementById('umode-slider-badge');
        if (badge) badge.textContent = val + '%';
    }

    function handleUmodeSliderChange(inputEl, trackerId) {
        if (!inputEl) return;
        const val = Math.max(0, Math.min(100, parseInt(inputEl.value, 10) || 0));
        submitUmodeSelfCheckValue(trackerId, val, false);
    }

    function handleUmodeTrackPointer(e, trackerId) {
        const container = document.getElementById('umode-slider-track-container');
        const input = document.getElementById('umode-selfcheck-range');
        if (!container || !input) return;
        const rect = container.getBoundingClientRect();
        if (rect.width <= 0) return;
        const clientX = (e.clientX !== undefined) ? e.clientX : (e.touches && e.touches[0] ? e.touches[0].clientX : rect.left);
        const offsetX = Math.max(0, Math.min(rect.width, clientX - rect.left));
        const percent = Math.round((offsetX / rect.width) * 100);
        input.value = percent;
        handleUmodeSliderInput(input, trackerId);
        if (e.type === 'pointerup' || e.type === 'mouseup' || e.type === 'touchend') {
            handleUmodeSliderChange(input, trackerId);
        }
    }

    function confirmUmodePercentage(trackerId) {
        const input = document.getElementById('umode-selfcheck-range');
        let val = 50;
        if (input) {
            val = Math.max(0, Math.min(100, parseInt(input.value, 10) || 0));
        }
        submitUmodeSelfCheckValue(trackerId, val, true);
    }

    function confirmUmodeQuantity(trackerId) {
        const input = document.getElementById(`umode-qty-input-${trackerId}`);
        if (!input) return;
        const raw = input.value.trim();
        if (!raw || isNaN(Number(raw))) {
            input.classList.add('border-red-400', 'ring-1', 'ring-red-400');
            setTimeout(() => input.classList.remove('border-red-400', 'ring-1', 'ring-red-400'), 1500);
            return;
        }
        submitUmodeSelfCheckValue(trackerId, Number(raw), true);
    }

    function submitUmodeSelfCheckValue(trackerId, value, shouldAdvance = true) {
        if (isSubmittingUmodeCheckin) return;
        if (!trackerId || value === null || value === undefined || (typeof value === 'string' && value.trim() === '')) {
            return;
        }
        isSubmittingUmodeCheckin = true;

        try {
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.setTodayObservation === 'function') {
                window.TempoSelfCheckWorkspace.setTodayObservation(trackerId, value, 'answered');
            } else if (typeof saveRmodeFallbackObservation === 'function') {
                saveRmodeFallbackObservation(trackerId, value, 'answered');
            } else {
                const uid = (typeof getRmodeUserId === 'function') ? getRmodeUserId() : 'local_user';
                const todayStr = (typeof getRmodeTodayDateStr === 'function') ? getRmodeTodayDateStr() : new Date().toISOString().slice(0, 10);
                const checkinsKey = `tempo_selfcheck_checkins_${uid}`;
                const obsKey = `tempo_selfcheck_observations_${uid}`;
                let checkins = [];
                try { checkins = JSON.parse(localStorage.getItem(checkinsKey) || '[]'); } catch (e) {}
                let allObs = [];
                try { allObs = JSON.parse(localStorage.getItem(obsKey) || '[]'); } catch (e) {}
                let todayChk = checkins.find(c => c.checkin_date === todayStr);
                if (!todayChk) {
                    todayChk = {
                        id: 'chk_' + todayStr.replace(/-/g, '') + '_' + Math.random().toString(36).substr(2, 4),
                        user_id: uid,
                        checkin_date: todayStr,
                        completed_at: new Date().toISOString(),
                        created_at: new Date().toISOString(),
                        updated_at: new Date().toISOString()
                    };
                    checkins.push(todayChk);
                    localStorage.setItem(checkinsKey, JSON.stringify(checkins));
                }
                const existingIdx = allObs.findIndex(o => o.checkin_id === todayChk.id && o.tracker_id === trackerId);
                if (existingIdx !== -1) {
                    allObs[existingIdx].value = value;
                    allObs[existingIdx].status = 'answered';
                    allObs[existingIdx].updated_at = new Date().toISOString();
                } else {
                    allObs.push({
                        id: 'obs_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
                        checkin_id: todayChk.id,
                        tracker_id: trackerId,
                        value: value,
                        status: 'answered',
                        note: '',
                        created_at: new Date().toISOString(),
                        updated_at: new Date().toISOString()
                    });
                }
                localStorage.setItem(obsKey, JSON.stringify(allObs));
            }

            // Confirm save succeeded
            let savedObs = null;
            if (typeof getRmodeTodayObservation === 'function') {
                savedObs = getRmodeTodayObservation(trackerId);
            }
            const isConfirmed = savedObs && savedObs.status === 'answered' && savedObs.value !== null && savedObs.value !== undefined;
            if (!isConfirmed) {
                console.error("Save confirmation failed for Umode check-in:", trackerId);
                if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                    window.TempoApp.showToast("Could not save check-in. Please try again.");
                }
                isSubmittingUmodeCheckin = false;
                return;
            }

            removeUmodeSkippedTracker(trackerId);
            if (typeof removeRmodeSkippedTracker === 'function') {
                removeRmodeSkippedTracker(trackerId);
            }

            if (shouldAdvance) {
                refreshStreakCardIfPresent();
            }

            try {
                window.dispatchEvent(new CustomEvent('tempo:selfcheck-updated'));
            } catch (e) {}

            if (window.TempoAlertSystem && typeof window.TempoAlertSystem.evaluateAndTriggerAlert === 'function') {
                window.TempoAlertSystem.evaluateAndTriggerAlert(trackerId);
            }
        } catch (e) {
            console.error("Failed to save Umode self-check value:", e);
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Could not save check-in. Please try again.");
            }
        } finally {
            setTimeout(() => { isSubmittingUmodeCheckin = false; }, 250);
        }
    }

    function getRecentlyState() {
        if (recentlyConfigState) return recentlyConfigState;
        try {
            if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getRecentlyState === 'function') {
                return window.TempoRecoverySelfCheck.getRecentlyState();
            }
            if (window.TempoRecoveryRecently && typeof window.TempoRecoveryRecently.getState === 'function') {
                return window.TempoRecoveryRecently.getState();
            }
            const saved = localStorage.getItem('tempo_recovery_recently_state');
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (e) {}
        return { type: 'EMPTY' }; // Default honest empty for Phase 1
    }

    function setRecentlyState(state) {
        recentlyConfigState = state;
        try {
            localStorage.setItem('tempo_recovery_recently_state', JSON.stringify(state));
        } catch (e) {}
        if (activeContext === MODES.RECOVERY) renderRmodeHome();
    }

    function checkIsWeeklyReviewReady() {
        if (weeklyReviewDismissed) return false;
        if (weeklyReviewOverrideReady) return true;
        try {
            if (window.TempoWeeklyReview && typeof window.TempoWeeklyReview.isReady === 'function') {
                return window.TempoWeeklyReview.isReady();
            }
        } catch (e) {}
        return false;
    }

    function setWeeklyReviewReady(isReady) {
        weeklyReviewOverrideReady = !!isReady;
        weeklyReviewDismissed = false;
        if (activeContext === MODES.RECOVERY) renderRmodeHome();
    }

    function dismissWeeklyReviewNotice() {
        weeklyReviewDismissed = true;
        if (window.TempoWeeklyReview && typeof window.TempoWeeklyReview.getLatestEligibleWeek === 'function') {
            const wk = window.TempoWeeklyReview.getLatestEligibleWeek();
            if (wk) window.TempoWeeklyReview.snoozeOrDismissNotice(wk.start);
        }
        if (activeContext === MODES.RECOVERY) renderRmodeHome();
    }

    function dismissRecoveryIntro() {
        try {
            localStorage.setItem('tempo_recovery_intro_dismissed', 'true');
        } catch (e) {}
        const banner = document.getElementById('recovery-intro-banner');
        if (banner) {
            banner.remove();
        }
    }

    function renderRmodeHome() {
        applyModeVisibility(MODES.RECOVERY);

        const rmodeBox = document.getElementById('rmode-home-content');
        if (!rmodeBox) return;

        // Shared emergency/recovery state: Prefer active plan from TempoPlanWorkspace / TempoPlanStore / TempoEmergencyFlow
        let confirmedPlan = null;
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.getActivePlan === 'function') {
            confirmedPlan = window.TempoPlanWorkspace.getActivePlan();
        }
        if (!confirmedPlan && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            confirmedPlan = window.TempoPlanStore.getActivePlan('recovery') || window.TempoPlanStore.getActivePlan('emergency') || window.TempoPlanStore.getActivePlan('default');
        }
        if (!confirmedPlan && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            confirmedPlan = window.TempoEmergencyFlow.getConfirmedPlan();
        }
        if (!confirmedPlan || (!confirmedPlan.plannedTasks && !confirmedPlan.tasks)) {
            try {
                const savedPlan = localStorage.getItem('tempo_working_plan') || localStorage.getItem('tempo_store_active_emergency_guest');
                if (savedPlan) {
                    const parsed = JSON.parse(savedPlan);
                    if (parsed && ((parsed.plannedTasks && parsed.plannedTasks.length > 0) || (parsed.tasks && parsed.tasks.length > 0))) {
                        confirmedPlan = parsed;
                    }
                }
            } catch (e) {}
        }
        if (!confirmedPlan && window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.getDefaultReferencePlan === 'function') {
            confirmedPlan = window.TempoPlanWorkspace.getDefaultReferencePlan();
        }

        const todayStr = getTodayISOString();
        const profile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
        const greetingInfo = getSafeGreetingInfo(profile);
        const userName = (greetingInfo && !greetingInfo.isFallback && greetingInfo.name)
            || (profile && (profile.preferredName || profile.displayName || profile.display_name || profile.full_name || profile.name))
            || 'Innie';
        const selfCheckState = getSelfCheckState();
        const recentlyState = getRecentlyState();

        rmodeBox.innerHTML = `
            <!-- ONE CONTINUOUS RECOVERY DASHBOARD -->
            <div class="space-y-10" data-tempo-ui="recovery-home-shell">
                <!-- FIRST SCREEN: Asymmetric Grid (~65% Left / ~35% Right on Desktop) -->
                <div class="recovery-home-main-grid">
                    <!-- LEFT COLUMN (~65%) -->
                    <div class="recovery-left-col space-y-4">
                        ${renderRmodeHeader(userName)}

                        ${renderSelfCheckCard(selfCheckState, greetingInfo)}
                        ${renderRecoverySupportRowHTML()}
                    </div>

                    <!-- RIGHT COLUMN (~35%) -->
                    <div class="recovery-right-col">
                        ${renderRecoveryNoteCard({ todayStr })}
                        ${renderRecentlyCard(recentlyState)}
                        
                        <!-- Prompt and mode-switch button -->
                        <div class="recovery-prompt-wrap pt-0 flex flex-col items-center text-center space-y-2.5" style="margin-top: 20px;">
                            <p class="font-bold text-base sm:text-[17px] text-[#55504A]">
                                ${window.t ? window.t('modes.recovery.transitionQuestion', {}, (isViLocale() ? 'Bạn đang cảm thấy quá tải hơn?' : 'Are things feeling more overwhelming now?')) : (isViLocale() ? 'Bạn đang cảm thấy quá tải hơn?' : 'Are things feeling more overwhelming now?')}
                            </p>
                            <button type="button" 
                                    onclick="window.TempoMode.openChangeModeModal()"
                                    class="w-full max-w-[280px] py-3 rounded-2xl font-bold text-sm sm:text-base bg-[#D79277] hover:bg-[#C68166] text-white shadow-xs border border-[#C68166]/30 transition cursor-pointer">
                                ${window.t ? window.t('modes.urgent.changeMyMode', {}, (isViLocale() ? 'Chuyển chế độ' : 'Change my mode')) : (isViLocale() ? 'Chuyển chế độ' : 'Change my mode')}
                            </button>
                        </div>
                    </div>
                </div>

                <!-- SECOND SCREEN (Continuous vertical scroll directly beneath first screen) -->
                <!-- Two-Column Section: ~65% Working Plan / ~35% Community -->
                <div class="recovery-plan-comm-grid">
                    <!-- LEFT COLUMN (~65%): Kế hoạch Làm việc của bạn -->
                    <div class="recovery-plan-col">
                        ${renderRecoveryWorkingPlanSection(confirmedPlan, todayStr)}
                    </div>

                    <!-- RIGHT COLUMN (~35%): Từ Cộng đồng Tempo -->
                    <div class="recovery-comm-col">
                        ${renderRecoveryCommunityCard()}
                    </div>
                </div>
            </div>
            <!-- RMODE TASK DETAIL MODAL ROOT -->
            <div id="rmode-task-modal-root">
                ${renderRmodeTaskDetailModalHTML()}
            </div>
        `;

        syncModeSelectorDOM(MODES.RECOVERY);

        // Also trigger community posts preview sync
        if (window.TempoCommunity && typeof window.TempoCommunity.renderRecoveryPreview === 'function') {
            window.TempoCommunity.renderRecoveryPreview();
        }

        if (typeof syncRmodeSelfCheckAlignment === 'function') {
            requestAnimationFrame(syncRmodeSelfCheckAlignment);
        }
    }

    function renderUmodeHome() {
        applyModeVisibility(MODES.UNCLEAR);

        if (window.TempoUnclearMode && typeof window.TempoUnclearMode.renderHome === 'function') {
            window.TempoUnclearMode.renderHome();
            syncModeSelectorDOM(MODES.UNCLEAR);
            return;
        }

        const umodeBox = document.getElementById('umode-home-content');
        if (!umodeBox) return;

        const todayObj = new Date();
        const formattedDate = window.TempoI18n ? window.TempoI18n.formatDate(todayObj, {
            weekday: 'short',
            month: 'short',
            day: 'numeric'
        }) : todayObj.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric'
        });

        umodeBox.innerHTML = `
            <div class="relative pb-1">
                <div class="flex items-center justify-between gap-4">
                    <div id="home-mode-selector-wrapper" class="relative inline-block text-left">
                        <button id="btn-home-mode-selector" 
                                type="button" 
                                onclick="window.TempoMode.toggleModeDropdown(event)" 
                                class="px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#FEF7EC] text-[#9A5B13] hover:bg-[#FDEBD0] border border-[#FDE5BE] transition flex items-center space-x-1.5 shadow-xs cursor-pointer"
                                aria-haspopup="true"
                                aria-expanded="false"
                                title="Switch Tempo Mode">
                            <span>🧭</span>
                            <span class="font-extrabold">${window.t ? window.t('modes.unclear.name', {}, 'Unclear Mode') : 'Unclear Mode'}</span>
                            <span class="text-[10px] ml-0.5 opacity-80">▾</span>
                        </button>
                        <div id="home-mode-selector-dropdown" class="hidden absolute left-0 mt-2 w-72 sm:w-80 bg-white rounded-2xl shadow-xl border border-[#EAE4DF] z-50 overflow-hidden" role="menu"></div>
                    </div>
                    <div class="text-xs font-semibold text-[#8E8A85]">
                        ${formattedDate}
                    </div>
                </div>
            </div>
        `;
        syncModeSelectorDOM(MODES.UNCLEAR);
    }

    function renderActiveModeHome() {
        renderShellIndicator();
        const curShared = getActiveSharedTool();
        if (curShared === 'ucheck' || activeSharedTool === 'ucheck' || activeContext === MODES.UNCLEAR) {
            renderUmodeHome();
            return;
        }
        switch (activeContext) {
            case MODES.EMERGENCY:
                renderEmodeHome();
                break;
            case MODES.RECOVERY:
                renderRmodeHome();
                break;
            case MODES.UNCLEAR:
                renderUmodeHome();
                break;
            default:
                restoreDefaultHome();
                break;
        }
    }

    function syncRmodeSelfCheckAlignment() {
        const selfCheck = document.querySelector('[data-tempo-ui="recovery-self-check"]');
        const recently = document.querySelector('[data-tempo-ui="recovery-recently"]');
        if (!selfCheck || !recently) return;

        if (window.innerWidth >= 1024) {
            selfCheck.style.marginTop = '';
            const scTop = selfCheck.getBoundingClientRect().top;
            const rcTop = recently.getBoundingClientRect().top;
            const diff = rcTop - scTop;
            const curMt = parseFloat(window.getComputedStyle(selfCheck).marginTop) || 0;
            selfCheck.style.marginTop = (curMt + diff) + 'px';
        } else {
            selfCheck.style.marginTop = '';
        }
    }

    function renderRmodeHeader(userName = 'Innie') {
        return `
            <div class="relative recovery-mode-header pb-0" data-tempo-ui="recovery-header-row">
                <!-- Top Mode Selector and Greeting Stacked Group -->
                <div class="flex flex-col items-start" data-tempo-ui="recovery-header-stack" style="gap: 20px;">
                    <!-- Anchored Mode Selector Dropdown -->
                    <div id="home-mode-selector-wrapper" class="relative inline-block text-left shrink-0">
                        <button id="btn-home-mode-selector" 
                                type="button" 
                                data-tempo-ui="mode-selector-btn"
                                onclick="window.TempoMode.toggleModeDropdown(event)" 
                                class="rounded-full text-[17px] font-bold bg-[#EDF7F1] text-[#166545] hover:bg-[#DDF0E5] border border-[#CDE9DA] transition inline-flex items-center justify-center space-x-1.5 shadow-xs cursor-pointer"
                                style="height: 40px; aspect-ratio: 5.1917 / 1; padding: 0 16px;"
                                aria-haspopup="true"
                                aria-expanded="false"
                                title="Switch Tempo Mode">
                            <span class="font-extrabold text-[17px]">${window.t ? window.t('modes.recovery.name', {}, 'Recovery Mode') : 'Recovery Mode'}</span>
                            <span class="text-[10px] ml-0.5 opacity-80">▾</span>
                        </button>
                        <div id="home-mode-selector-dropdown" class="hidden absolute left-0 mt-2 w-72 sm:w-80 bg-white rounded-2xl shadow-xl border border-[#EAE4DF] z-50 overflow-hidden" role="menu"></div>
                    </div>

                    <!-- Greeting (Terracotta #D48366) directly below Mode button -->
                    <div class="recovery-greeting pb-0 pt-0" style="margin-top: 0 !important; margin-bottom: 0 !important; padding: 0 !important;">
                        <h2 class="text-[29px] sm:text-[33px] font-extrabold text-[#D48366] tracking-tight flex items-center space-x-2.5 whitespace-normal sm:whitespace-nowrap leading-none" style="line-height: 1; margin: 0 !important;">
                            <span class="text-3xl select-none leading-none">👋</span>
                            <span class="leading-none">Hi ${escapeHTML(userName)}, how are you today?</span>
                        </h2>
                    </div>
                </div>
            </div>
        `;
    }


    function renderRecoveryIntroBanner() {
        let isDismissed = false;
        try {
            isDismissed = localStorage.getItem('tempo_recovery_intro_dismissed') === 'true';
        } catch (e) {}

        if (isDismissed) return '';

        return `
            <div id="recovery-intro-banner" class="bg-[#EDF7F1] border border-[#CDE9DA] rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all">
                <div class="flex items-start space-x-3.5">
                    <span class="text-xl sm:text-2xl mt-0.5 select-none">🌱</span>
                    <div class="space-y-1">
                        <h4 class="font-heading text-sm sm:text-base font-bold text-[#166545]">
                            ${window.t ? window.t('modes.recovery.name', {}, "You're in Recovery Mode") : "You're in Recovery Mode"}
                        </h4>
                        <p class="text-xs sm:text-sm text-[#2D6A4F] leading-relaxed max-w-2xl">
                            ${window.t ? window.t('modes.recovery.introBanner', {}, 'Nothing you need to complete here. Use this space to slow things down, check in when you want to, or simply take a little breathing room.') : 'Nothing you need to complete here. Use this space to slow things down, check in when you want to, or simply take a little breathing room.'}
                        </p>
                    </div>
                </div>
                <button type="button" 
                        onclick="window.TempoMode.dismissRecoveryIntro()" 
                        class="px-4 py-2 bg-white hover:bg-stone-50 text-[#166545] border border-[#CDE9DA] font-bold text-xs rounded-xl shadow-xs shrink-0 self-start sm:self-auto transition cursor-pointer">
                    ${window.t ? window.t('modes.recovery.dismissBanner', {}, 'Got it') : 'Got it'}
                </button>
            </div>
        `;
    }

    // =========================================================================
    // RMODE SEQUENTIAL DAILY SELF-CHECK & SKIP CONTROLLER
    // =========================================================================

    let isSubmittingRmodeSelfCheck = false;

    function getRmodeUserId() {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') {
            const uid = window.TempoAuth.getCurrentUserId();
            if (uid) return uid;
        }
        return 'local_user';
    }

    function getRmodeTodayDateStr() {
        return getLocalTodayISO();
    }

    function getRmodeSkippedTrackers() {
        const uid = getRmodeUserId();
        const todayStr = getRmodeTodayDateStr();
        const key = `tempo_rmode_skipped_trackers_${uid}_${todayStr}`;
        try {
            const raw = localStorage.getItem(key);
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            return [];
        }
    }

    function addRmodeSkippedTracker(trackerId) {
        if (!trackerId) return;
        const uid = getRmodeUserId();
        const todayStr = getRmodeTodayDateStr();
        const key = `tempo_rmode_skipped_trackers_${uid}_${todayStr}`;
        const list = getRmodeSkippedTrackers();
        if (!list.includes(trackerId)) {
            list.push(trackerId);
            try {
                localStorage.setItem(key, JSON.stringify(list));
            } catch (e) {}
        }
    }

    function removeRmodeSkippedTracker(trackerId) {
        if (!trackerId) return;
        const uid = getRmodeUserId();
        const todayStr = getRmodeTodayDateStr();
        const key = `tempo_rmode_skipped_trackers_${uid}_${todayStr}`;
        let list = getRmodeSkippedTrackers();
        list = list.filter(id => id !== trackerId);
        try {
            localStorage.setItem(key, JSON.stringify(list));
        } catch (e) {}
    }

    function resetRmodeSkippedTrackers() {
        const uid = getRmodeUserId();
        const todayStr = getRmodeTodayDateStr();
        const key = `tempo_rmode_skipped_trackers_${uid}_${todayStr}`;
        try {
            localStorage.removeItem(key);
        } catch (e) {}
        renderRmodeHome();
    }

    function getRmodeTodayObservation(trackerId) {
        if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.getTodayObservation === 'function') {
            const obs = window.TempoSelfCheckWorkspace.getTodayObservation(trackerId);
            if (obs) return obs;
        }
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTodayCheckin === 'function' && typeof window.TempoRecoverySelfCheck.getObservationsForCheckin === 'function') {
            const todayChk = window.TempoRecoverySelfCheck.getTodayCheckin();
            if (todayChk) {
                const obsList = window.TempoRecoverySelfCheck.getObservationsForCheckin(todayChk.id);
                const trk = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerById === 'function')
                    ? window.TempoRecoverySelfCheck.getTrackerById(trackerId)
                    : null;
                const aliasIds = (trk && Array.isArray(trk.alias_ids)) ? trk.alias_ids : [];
                const found = obsList.find(o => o.tracker_id === trackerId || aliasIds.includes(o.tracker_id));
                if (found) return found;
            }
        }
        const uid = getRmodeUserId();
        const todayStr = getRmodeTodayDateStr();
        const checkinsKey = `tempo_selfcheck_checkins_${uid}`;
        const obsKey = `tempo_selfcheck_observations_${uid}`;
        try {
            const rawChk = localStorage.getItem(checkinsKey) || (uid === 'local_user' ? localStorage.getItem('tempo_selfcheck_checkins') : null);
            const rawObs = localStorage.getItem(obsKey) || (uid === 'local_user' ? localStorage.getItem('tempo_selfcheck_observations') : null);
            const checkins = rawChk ? JSON.parse(rawChk) : [];
            const todayChk = checkins.find(c => c.checkin_date === todayStr);
            if (todayChk && rawObs) {
                const allObs = JSON.parse(rawObs);
                const trk = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerById === 'function')
                    ? window.TempoRecoverySelfCheck.getTrackerById(trackerId)
                    : null;
                const aliasIds = (trk && Array.isArray(trk.alias_ids)) ? trk.alias_ids : [];
                return allObs.find(o => o.checkin_id === todayChk.id && (o.tracker_id === trackerId || aliasIds.includes(o.tracker_id))) || null;
            }
        } catch (e) {}
        return null;
    }

    function isRmodeTrackerAnsweredToday(trackerId) {
        const obs = getRmodeTodayObservation(trackerId);
        if (!obs) return false;
        if (obs.status !== 'answered') return false;
        if (obs.value === null || obs.value === undefined || obs.value === '') return false;
        return true;
    }

    function saveRmodeFallbackObservation(trackerId, value, status = 'answered') {
        const uid = getRmodeUserId();
        const todayStr = getRmodeTodayDateStr();
        const checkinsKey = `tempo_selfcheck_checkins_${uid}`;
        const obsKey = `tempo_selfcheck_observations_${uid}`;

        let checkins = [];
        try {
            checkins = JSON.parse(localStorage.getItem(checkinsKey) || '[]');
            if (checkins.length === 0 && uid === 'local_user') {
                checkins = JSON.parse(localStorage.getItem('tempo_selfcheck_checkins') || '[]');
            }
        } catch (e) {}

        let allObs = [];
        try {
            allObs = JSON.parse(localStorage.getItem(obsKey) || '[]');
            if (allObs.length === 0 && uid === 'local_user') {
                allObs = JSON.parse(localStorage.getItem('tempo_selfcheck_observations') || '[]');
            }
        } catch (e) {}

        let todayChk = checkins.find(c => c.checkin_date === todayStr);
        if (!todayChk) {
            todayChk = {
                id: 'chk_' + todayStr.replace(/-/g, '') + '_' + Math.random().toString(36).substr(2, 4),
                user_id: uid,
                checkin_date: todayStr,
                completed_at: new Date().toISOString(),
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            };
            checkins.push(todayChk);
            localStorage.setItem(checkinsKey, JSON.stringify(checkins));
            if (uid === 'local_user') localStorage.setItem('tempo_selfcheck_checkins', JSON.stringify(checkins));
        }

        const existingIdx = allObs.findIndex(o => o.checkin_id === todayChk.id && o.tracker_id === trackerId);
        if (existingIdx !== -1) {
            allObs[existingIdx].value = value;
            allObs[existingIdx].status = status;
            allObs[existingIdx].updated_at = new Date().toISOString();
        } else {
            allObs.push({
                id: 'obs_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
                checkin_id: todayChk.id,
                tracker_id: trackerId,
                value: value,
                status: status,
                note: '',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            });
        }

        localStorage.setItem(obsKey, JSON.stringify(allObs));
        if (uid === 'local_user') localStorage.setItem('tempo_selfcheck_observations', JSON.stringify(allObs));
    }

    function submitRmodeSelfCheckValue(trackerId, value) {
        if (isSubmittingRmodeSelfCheck) return;
        isSubmittingRmodeSelfCheck = true;

        try {
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.setTodayObservation === 'function') {
                window.TempoSelfCheckWorkspace.setTodayObservation(trackerId, value, 'answered');
            } else {
                saveRmodeFallbackObservation(trackerId, value, 'answered');
            }

            removeRmodeSkippedTracker(trackerId);
            renderRmodeHome();
            if (typeof refreshStreakCardIfPresent === 'function') {
                refreshStreakCardIfPresent();
            }

            if (window.TempoAlertSystem && typeof window.TempoAlertSystem.evaluateAndTriggerAlert === 'function') {
                window.TempoAlertSystem.evaluateAndTriggerAlert(trackerId);
            }
        } catch (e) {
            console.error("Failed to save check-in:", e);
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Could not save check-in. Please try again.");
            }
        } finally {
            setTimeout(() => { isSubmittingRmodeSelfCheck = false; }, 300);
        }
    }

    function skipRmodeCurrentSelfCheck(trackerId) {
        if (isSubmittingRmodeSelfCheck) return;
        isSubmittingRmodeSelfCheck = true;

        try {
            addRmodeSkippedTracker(trackerId);
            renderRmodeHome();
        } finally {
            setTimeout(() => { isSubmittingRmodeSelfCheck = false; }, 300);
        }
    }

    function submitRmodeQuantityValue(trackerId) {
        const input = document.getElementById(`rmode-qty-input-${trackerId}`);
        if (!input) return;
        const raw = input.value.trim();
        if (!raw) {
            input.classList.add('border-red-400', 'ring-1', 'ring-red-400');
            input.focus();
            return;
        }
        const num = parseFloat(raw);
        if (isNaN(num) || num < 0 || !isFinite(num)) {
            input.classList.add('border-red-400', 'ring-1', 'ring-red-400');
            input.focus();
            return;
        }
        input.classList.remove('border-red-400', 'ring-1', 'ring-red-400');
        submitRmodeSelfCheckValue(trackerId, num);
    }

    function renderSelfCheckCard(selfCheckState, greetingInfo) {
        const streakCount = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.calculateStreak === 'function')
            ? window.TempoRecoverySelfCheck.calculateStreak()
            : ((selfCheckState && typeof selfCheckState.streak === 'number') ? selfCheckState.streak : 0);

        let rawActiveTrackers = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function')
            ? window.TempoRecoverySelfCheck.getActiveTrackers()
            : [];

        // Deduplicate by canonical concept
        const seenSelfCheckConcepts = new Set();
        const activeTrackers = [];
        rawActiveTrackers.forEach(trk => {
            if (!trk || !trk.name) return;
            const nameLower = trk.name.trim().toLowerCase();
            const conceptKey = nameLower.includes('tension') 
                ? 'stress_sign::tension' 
                : `${(trk.category || 'stress_sign').toLowerCase()}::${nameLower}`;
            if (!seenSelfCheckConcepts.has(conceptKey)) {
                seenSelfCheckConcepts.add(conceptKey);
                activeTrackers.push(trk);
            }
        });

        if (activeTrackers.length === 0) {
            return `
                <div class="recovery-card-selfcheck bg-[#FEFAF4] rounded-3xl p-6 sm:p-7 soft-card-shadow border border-white/60 flex flex-col justify-between lg:mt-[52px]" style="min-height: 290px; width: calc(100% - 30px); margin-inline: auto; background-color: #FEFAF4;" data-tempo-ui="recovery-self-check">
                    <div class="space-y-1">
                        <span class="text-xs sm:text-sm font-extrabold text-[#4A6B5D] uppercase tracking-wide block">Your daily check-in</span>
                        <h3 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#484541] tracking-tight leading-snug">Today’s self-check</h3>
                        <p class="text-xs italic text-[#7B7672] font-medium">${streakCount}-day streak</p>
                    </div>
                    <div class="py-3 text-center space-y-1">
                        <p class="text-xs font-semibold text-[#5B5550]">No tracking items in your system yet.</p>
                        <p class="text-[11px] text-stone-400">Add habits or indicators in your Self-check tool to check in here.</p>
                    </div>
                    <div class="pt-1 flex flex-wrap items-center gap-3" data-tempo-ui="rmode-selfcheck-empty-actions">
                        <button type="button" 
                                id="btn-rmode-add-tracking"
                                data-tempo-ui="rmode-add-tracking-btn"
                                onclick="if (window.TempoMode && typeof window.TempoMode.handleAddTrackingDirectClick === 'function') { window.TempoMode.handleAddTrackingDirectClick(); } else if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('open', { sourceContext: 'recovery', openAdjust: true }); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; }"
                                class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-white border border-[#7B9688] text-[#4A6B5D] hover:bg-[#F4F7F5] shadow-xs transition cursor-pointer">
                            Add Tracking
                        </button>
                        <button type="button" 
                                id="btn-rmode-setup-tracking"
                                data-tempo-ui="rmode-setup-tracking-btn"
                                onclick="if (window.TempoMode && typeof window.TempoMode.handleRecoveryIntroSetupClick === 'function') { window.TempoMode.handleRecoveryIntroSetupClick(); } else if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.open === 'function') { window.TempoRecoverySetup.open(1); if (typeof window.TempoRecoverySetup.goToStage === 'function') window.TempoRecoverySetup.goToStage(1); } else if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('setup', { stage: 1 }); }"
                                class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-[#7B9688] hover:bg-[#6D8475] text-white shadow-xs transition cursor-pointer">
                            Set Up My Tracking System
                        </button>
                    </div>
                </div>
            `;
        }

        const answeredTrackers = activeTrackers.filter(t => isRmodeTrackerAnsweredToday(t.id));
        const answeredCount = answeredTrackers.length;
        const totalCount = activeTrackers.length;
        const progressPercent = Math.round((answeredCount / totalCount) * 100);

        const skippedIds = new Set(getRmodeSkippedTrackers());
        const skippedTrackers = activeTrackers.filter(t => !isRmodeTrackerAnsweredToday(t.id) && skippedIds.has(t.id));

        const pendingTrackers = activeTrackers.filter(t => !isRmodeTrackerAnsweredToday(t.id) && !skippedIds.has(t.id));

        // Middle Section HTML: Single current tracker OR completed state
        let middleSectionHTML = '';

        if (pendingTrackers.length > 0) {
            const currentTracker = pendingTrackers[0];
            const dotColor = currentTracker.type_color || (currentTracker.category === 'stress_sign' ? '#D48366' : (currentTracker.category === 'supportive' ? '#166545' : '#1E40AF'));
            const method = currentTracker.check_method;
            const nameLower = (currentTracker.name || '').toLowerCase();

            let controlsHTML = '';

            if (method === 'percentage' || nameLower.includes('tension')) {
                controlsHTML = `
                    <div class="space-y-1.5 pt-0.5 pb-1">
                        <div class="flex items-center justify-between text-xs">
                            <span class="text-[#7B7672] font-medium">Select level:</span>
                            <span id="rmode-slider-val" class="font-extrabold text-[#37352F] text-sm">50%</span>
                        </div>
                        <div class="flex items-center space-x-2.5">
                            <input type="range" min="0" max="100" value="50" 
                                   id="rmode-selfcheck-range"
                                   oninput="const el = document.getElementById('rmode-slider-val'); if (el) el.textContent = this.value + '%'"
                                   class="w-full accent-[#4A6B5D] cursor-pointer">
                            <button type="button" 
                                    onclick="window.TempoMode.submitRmodeSelfCheckValue('${currentTracker.id}', parseInt(document.getElementById('rmode-selfcheck-range').value, 10))"
                                    class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shrink-0 shadow-2xs">
                                ${window.t ? window.t('modes.recovery.save', {}, (isViLocale() ? 'Lưu' : 'Save')) : (isViLocale() ? 'Lưu' : 'Save')}
                            </button>
                        </div>
                    </div>
                `;
            } else if (method === 'options' || method === 'yes_no' || nameLower.includes('sleep')) {
                let opts = currentTracker.options;
                if (!opts || !Array.isArray(opts) || opts.length === 0) {
                    opts = nameLower.includes('sleep') ? ['Good', 'Not good'] : ['Yes', 'No'];
                }
                controlsHTML = `
                    <div class="pt-0.5 pb-1">
                        <div class="flex items-center flex-wrap gap-2">
                            ${opts.map(opt => `
                                <button type="button" 
                                        onclick="window.TempoMode.submitRmodeSelfCheckValue('${currentTracker.id}', '${escapeHTML(opt)}')"
                                        class="px-4 py-1.5 rounded-xl text-xs font-bold bg-white hover:bg-[#F4F7F5] border border-stone-300/80 text-[#37352F] hover:border-[#7B9688] hover:text-[#166545] transition cursor-pointer shadow-2xs">
                                    ${escapeHTML(opt)}
                                </button>
                            `).join('')}
                        </div>
                    </div>
                `;
            } else if (method === 'scale') {
                const scaleMax = currentTracker.scale_max || (currentTracker.scale_range === '1-10' ? 10 : 5);
                const scaleNums = [];
                for (let n = 1; n <= scaleMax; n++) scaleNums.push(n);
                controlsHTML = `
                    <div class="pt-0.5 pb-1">
                        <div class="flex items-center space-x-1.5 overflow-x-auto pb-0.5">
                            ${scaleNums.map(n => `
                                <button type="button" 
                                        onclick="window.TempoMode.submitRmodeSelfCheckValue('${currentTracker.id}', ${n})"
                                        class="w-8 h-8 rounded-xl text-xs font-bold bg-white hover:bg-[#F4F7F5] border border-stone-300/80 text-[#37352F] hover:border-[#7B9688] hover:text-[#166545] transition cursor-pointer flex items-center justify-center shrink-0 shadow-2xs">
                                    ${n}
                                </button>
                            `).join('')}
                        </div>
                    </div>
                `;
            } else if (method === 'quantity' || nameLower.includes('walk')) {
                const unit = currentTracker.quantity_unit || 'min';
                controlsHTML = `
                    <div class="pt-0.5 pb-1">
                        <div class="flex items-center flex-wrap gap-2">
                            <input type="number" 
                                   id="rmode-qty-input-${currentTracker.id}"
                                   placeholder="Enter quantity"
                                   min="0"
                                   step="any"
                                   class="w-28 sm:w-32 px-3 py-1.5 text-xs font-semibold rounded-xl border border-stone-300 focus:outline-none focus:border-[#4A6B5D] bg-white shadow-2xs">
                            <span class="text-xs font-bold text-[#5B5550]">${escapeHTML(unit)}</span>
                            <button type="button" 
                                    onclick="window.TempoMode.submitRmodeQuantityValue('${currentTracker.id}')"
                                    class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shrink-0 shadow-2xs">
                                ${window.t ? window.t('modes.recovery.save', {}, (isViLocale() ? 'Lưu' : 'Save')) : (isViLocale() ? 'Lưu' : 'Save')}
                            </button>
                            <button type="button" 
                                    onclick="window.TempoMode.submitRmodeSelfCheckValue('${currentTracker.id}', 'no')"
                                    class="px-2.5 py-1.5 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-700 hover:bg-stone-100 transition cursor-pointer">
                                Didn't do
                            </button>
                        </div>
                    </div>
                `;
            } else {
                controlsHTML = `
                    <div class="pt-0.5 pb-1 flex items-center space-x-2">
                        <button type="button" 
                                onclick="window.TempoMode.submitRmodeSelfCheckValue('${currentTracker.id}', 'yes')"
                                class="px-4 py-1.5 rounded-xl text-xs font-bold bg-[#7B9688] text-white hover:bg-[#6D8475] shadow-2xs transition">
                            Check in
                        </button>
                    </div>
                `;
            }

            middleSectionHTML = `
                <div class="space-y-2 py-1">
                    <!-- Tracker Header with Color Dot & Small Secondary Skip Button -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2 text-sm font-bold text-[#484541] truncate min-w-0">
                            <span class="w-2.5 h-2.5 rounded-full inline-block shrink-0" style="background-color: ${dotColor};"></span>
                            <span class="truncate">${escapeHTML(currentTracker.name)}</span>
                        </div>
                        <button type="button" 
                                onclick="window.TempoMode.skipRmodeCurrentSelfCheck('${currentTracker.id}')"
                                class="text-xs font-semibold text-[#8C8681] hover:text-[#37352F] hover:bg-stone-200/50 px-2.5 py-1 rounded-lg transition cursor-pointer shrink-0"
                                title="Skip for now">
                            ${window.t ? window.t('modes.recovery.skip', {}, (isViLocale() ? 'Bỏ qua' : 'Skip')) : (isViLocale() ? 'Bỏ qua' : 'Skip')}
                        </button>
                    </div>

                    <!-- Single Interactive Control -->
                    ${controlsHTML}

                    <!-- Summary Line (without progress bar) -->
                    <div class="pt-1 flex items-center justify-between text-xs text-[#5B5550]">
                        <span>${window.t ? window.t('modes.recovery.checkinSummary', { completed: answeredCount, total: totalCount }, (isViLocale() ? `Bạn đã check ${answeredCount}/${totalCount} mục hôm nay.` : `You checked in on ${answeredCount} of ${totalCount} things.`)) : (isViLocale() ? `Bạn đã check ${answeredCount}/${totalCount} mục hôm nay.` : `You checked in on ${answeredCount} of ${totalCount} things.`)}</span>
                        ${skippedTrackers.length > 0 ? `<span class="text-[11px] text-[#8C8681]">(${skippedTrackers.length} skipped)</span>` : ''}
                    </div>
                </div>
            `;
        } else {
            // Completed / All Items Processed Summary State
            const allChecked = answeredCount === totalCount;
            middleSectionHTML = `
                <div class="space-y-2 py-1.5">
                    <div class="flex items-center space-x-2 text-sm font-bold ${allChecked ? 'text-[#166545]' : 'text-[#484541]'}">
                        <span class="w-2.5 h-2.5 rounded-full ${allChecked ? 'bg-[#166545]' : 'bg-[#7B9688]'} inline-block"></span>
                        <span>${allChecked ? 'All check-ins completed today! 🎉' : 'Today’s check-in complete'}</span>
                    </div>

                    <!-- Summary Line (without progress bar) -->
                    <div class="pt-0.5 flex items-center justify-between text-xs text-[#5B5550]">
                        <span>${window.t ? window.t('modes.recovery.checkinSummary', { completed: answeredCount, total: totalCount }, (isViLocale() ? `Bạn đã check ${answeredCount}/${totalCount} mục hôm nay.` : `You checked in on ${answeredCount} of ${totalCount} things.`)) : (isViLocale() ? `Bạn đã check ${answeredCount}/${totalCount} mục hôm nay.` : `You checked in on ${answeredCount} of ${totalCount} things.`)}</span>
                        ${skippedTrackers.length > 0 ? `
                            <button type="button" 
                                    onclick="window.TempoMode.resetRmodeSkippedTrackers()"
                                    class="text-xs font-bold text-[#4A6B5D] hover:underline cursor-pointer">
                                Review ${skippedTrackers.length} skipped
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        return `
            <div class="recovery-card-selfcheck bg-[#FEFAF4] rounded-3xl p-6 sm:p-7 soft-card-shadow border border-white/60 flex flex-col justify-between lg:mt-[52px]" style="min-height: 290px; width: calc(100% - 30px); margin-inline: auto; background-color: #FEFAF4;" data-tempo-ui="recovery-self-check">
                <!-- Top Block: Category, Title, Streak -->
                <div class="space-y-1">
                    <span class="text-xs sm:text-sm font-extrabold text-[#4A6B5D] uppercase tracking-wide block">Your daily check-in</span>
                    <h3 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#484541] tracking-tight leading-snug">Today’s self-check</h3>
                    <p class="text-xs italic text-[#7B7672] font-medium">${streakCount}-day streak</p>
                </div>

                <!-- Middle Block: Single Tracking Item OR Completed State -->
                ${middleSectionHTML}

                <!-- Bottom Block: Action Buttons -->
                <div class="pt-1 flex flex-wrap items-center gap-3">
                    <button type="button" 
                            onclick="window.TempoMode.handleSelfCheckAction('view')"
                            class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-[#7B9688] hover:bg-[#6D8475] text-white shadow-xs transition cursor-pointer">
                        ${window.t ? window.t('modes.recovery.viewTodayCheckin', {}, (isViLocale() ? 'Xem check-in hôm nay' : "View today's checkin")) : (isViLocale() ? 'Xem check-in hôm nay' : "View today's checkin")}
                    </button>
                    <button type="button" 
                            onclick="if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('open', { sourceContext: 'recovery' }); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; }"
                            class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-white border border-[#7B9688] text-[#4A6B5D] hover:bg-[#F4F7F5] shadow-xs transition cursor-pointer">
                        ${window.t ? window.t('modes.recovery.editTrackingSystem', {}, (isViLocale() ? 'Sửa tracking' : 'Edit tracking system')) : (isViLocale() ? 'Sửa tracking' : 'Edit tracking system')}
                    </button>
                </div>
            </div>
        `;
    }

    // Side-by-side Quick Relief & Focus Now cards beneath Today's self-check
    function renderRecoverySupportRowHTML() {
        return `
            <div class="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-5 w-full recovery-support-row" data-tempo-ui="recovery-support" style="margin-left: auto; margin-right: auto;">
                <!-- Tool 1: Quick Relief -->
                ${renderQuickReliefCardHTML()}

                <!-- Tool 2: Focus Now -->
                ${renderFocusNowCardHTML()}
            </div>
        `;
    }

    function getAuthoritativeTrackerObservations(trackerOrId) {
        const uid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function')
            ? (window.TempoAuth.getCurrentUserId() || 'local_user')
            : 'local_user';
        const checkinsKey = `tempo_selfcheck_checkins_${uid}`;
        const obsKey = `tempo_selfcheck_observations_${uid}`;

        let checkins = [];
        let allObs = [];
        try {
            checkins = JSON.parse(localStorage.getItem(checkinsKey) || (uid === 'local_user' ? (localStorage.getItem('tempo_selfcheck_checkins') || '[]') : '[]'));
            allObs = JSON.parse(localStorage.getItem(obsKey) || (uid === 'local_user' ? (localStorage.getItem('tempo_selfcheck_observations') || '[]') : '[]'));
        } catch (e) {}

        const dateMap = {};
        if (Array.isArray(checkins)) {
            checkins.forEach(c => {
                if (c && c.id && c.checkin_date) {
                    dateMap[c.id] = c.checkin_date;
                }
            });
        }

        const todayStr = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTodayDateStr === 'function')
            ? window.TempoRecoverySelfCheck.getTodayDateStr()
            : getLocalTodayISO();

        if (!Array.isArray(allObs)) return [];

        const trackerId = (trackerOrId && typeof trackerOrId === 'object') ? trackerOrId.id : trackerOrId;
        const trackerObj = (trackerOrId && typeof trackerOrId === 'object')
            ? trackerOrId
            : (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerById === 'function' ? window.TempoRecoverySelfCheck.getTrackerById(trackerId) : null);

        const trackerName = (trackerObj && trackerObj.name) ? trackerObj.name.trim().toLowerCase() : '';
        const isTension = trackerName.includes('tension');
        const aliasIds = new Set();
        if (trackerId) aliasIds.add(trackerId);
        if (trackerObj && Array.isArray(trackerObj.alias_ids)) {
            trackerObj.alias_ids.forEach(aid => aliasIds.add(aid));
        }

        // Also match any trackers with identical canonical name/concept in storage
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackers === 'function') {
            try {
                const allTrks = window.TempoRecoverySelfCheck.getTrackers(true);
                allTrks.forEach(t => {
                    if (t && t.name) {
                        const tName = t.name.trim().toLowerCase();
                        if (trackerName && tName === trackerName) aliasIds.add(t.id);
                        if (isTension && tName.includes('tension')) aliasIds.add(t.id);
                    }
                });
            } catch (e) {}
        }

        const matchedObs = allObs
            .filter(o => o && aliasIds.has(o.tracker_id) && o.status === 'answered' && o.value !== null && o.value !== undefined && o.value !== '')
            .map(o => ({
                ...o,
                date: dateMap[o.checkin_id] || todayStr
            }))
            .filter(o => o.date <= todayStr);

        // Deduplicate observations by date (keep the most recently updated observation per calendar date)
        const obsByDate = new Map();
        matchedObs.forEach(o => {
            const dateKey = o.date;
            const existing = obsByDate.get(dateKey);
            if (!existing) {
                obsByDate.set(dateKey, o);
            } else {
                const existingTime = existing.updated_at || existing.created_at || '';
                const newTime = o.updated_at || o.created_at || '';
                if (newTime >= existingTime) {
                    obsByDate.set(dateKey, o);
                }
            }
        });

        return Array.from(obsByDate.values())
            .sort((a, b) => (a.date || '').localeCompare(b.date || ''));
    }

    function getWeeklyReportCountdownText() {
        const now = new Date();
        const day = now.getDay(); // 0 is Sunday, 1 is Monday, ..., 6 is Saturday
        // Weekly review cycle in Tempo runs Monday to Sunday.
        // The weekly report is available at the end of the weekly cycle (Sunday).
        const days = (7 - day) % 7;
        if (days === 0) {
            return 'Your weekly report is ready today.';
        }
        return `${days} day${days === 1 ? '' : 's'} until your weekly report.`;
    }

    function renderRecentlyCard(recentlyState) {
        let activeTrackers = [];
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function') {
            activeTrackers = window.TempoRecoverySelfCheck.getActiveTrackers();
        } else {
            try {
                const uid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function')
                    ? (window.TempoAuth.getCurrentUserId() || 'local_user')
                    : 'local_user';
                const raw = localStorage.getItem(`tempo_selfcheck_trackers_${uid}`) || localStorage.getItem('tempo_selfcheck_trackers');
                if (raw) {
                    const parsed = JSON.parse(raw);
                    activeTrackers = Array.isArray(parsed) ? parsed.filter(t => !t.archived && !t.is_archived) : [];
                }
            } catch (e) {}
        }

        // Defensive deduplication by canonical tracker concept
        const seenConcepts = new Set();
        const uniqueActiveTrackers = [];
        activeTrackers.forEach(trk => {
            if (!trk || !trk.name) return;
            const nameLower = trk.name.trim().toLowerCase();
            const conceptKey = nameLower.includes('tension') 
                ? 'stress_sign::tension' 
                : `${(trk.category || 'stress_sign').toLowerCase()}::${nameLower}`;
            if (!seenConcepts.has(conceptKey)) {
                seenConcepts.add(conceptKey);
                uniqueActiveTrackers.push(trk);
            }
        });
        activeTrackers = uniqueActiveTrackers;

        const countdownText = getWeeklyReportCountdownText();

        let itemsHTML = '';
        if (activeTrackers.length === 0) {
            itemsHTML = `
                <div class="py-3 text-center">
                    <p class="text-xs text-[#7B7672]">No active tracking items.</p>
                </div>
            `;
        } else {
            itemsHTML = activeTrackers.map(tracker => {
                const nameLower = (tracker.name || '').toLowerCase();
                const dotColor = tracker.type_color || (
                    tracker.category === 'stress_sign' ? '#D48366' :
                    (nameLower.includes('sleep') ? '#5A9E75' :
                    (tracker.category === 'supportive' ? '#5A9E75' : '#7B9688'))
                );

                const observations = getAuthoritativeTrackerObservations(tracker);
                const latestObs = observations.length > 0 ? observations[observations.length - 1] : null;

                let description = '';
                let formattedValue = '';

                const isTension = nameLower.includes('tension');
                const method = isTension ? 'percentage' : (latestObs?.check_method || tracker.check_method || 'yes_no');

                if (!latestObs) {
                    // Missing data: never invent values, never treat missing check-in as zero
                    if (method === 'percentage' || isTension) {
                        description = `Your average ${escapeHTML(nameLower)} level is`;
                    } else if (method === 'options' || method === 'yes_no') {
                        description = nameLower.includes('sleep') ? 'Nights of Quality Sleep' : 'Latest recorded choice';
                    } else if (method === 'scale') {
                        description = 'Latest recorded rating';
                    } else if (method === 'quantity' || nameLower.includes('walk')) {
                        description = nameLower.includes('walk') ? 'You have walked for' : 'You have logged';
                    } else {
                        description = `Your average ${escapeHTML(nameLower)} level is`;
                    }
                    formattedValue = '<span class="text-[#8E8A85] text-sm font-normal">—</span>';
                } else {
                    // Format historical values according to the method that was active when recorded
                    if (method === 'percentage' || isTension) {
                        const pctObs = observations.filter(o => 
                            o.value !== null && o.value !== undefined && o.value !== '' &&
                            (typeof o.value === 'number' || (typeof o.value === 'string' && !isNaN(Number(o.value.replace('%', '')))))
                        );
                        if (pctObs.length > 0) {
                            const sum = pctObs.reduce((acc, o) => acc + parseFloat(String(o.value).replace('%', '')), 0);
                            const avg = Math.round(sum / pctObs.length);
                            description = `Your average ${escapeHTML(nameLower)} level is`;
                            formattedValue = `${avg}%`;
                        } else {
                            description = `Your average ${escapeHTML(nameLower)} level is`;
                            formattedValue = '<span class="text-[#8E8A85] text-sm font-normal">—</span>';
                        }
                    } else if (method === 'options' || method === 'yes_no') {
                        if (nameLower.includes('sleep')) {
                            description = 'Nights of Quality Sleep';
                            const goodCount = observations.filter(o => {
                                const valStr = String(o.value || '').trim().toLowerCase();
                                return valStr === 'good' || valStr === 'yes' || valStr === 'true';
                            }).length;
                            formattedValue = `${goodCount}`;
                        } else {
                            description = 'Latest recorded choice';
                            let valStr = String(latestObs.value || '');
                            if (valStr.toLowerCase() === 'true' || valStr.toLowerCase() === 'yes') valStr = 'Yes';
                            else if (valStr.toLowerCase() === 'false' || valStr.toLowerCase() === 'no') valStr = 'No';
                            formattedValue = escapeHTML(valStr);
                        }
                    } else if (method === 'scale') {
                        const max = (tracker.scale_max !== undefined) ? tracker.scale_max : 5;
                        description = 'Latest recorded rating';
                        formattedValue = `${escapeHTML(String(latestObs.value))}/${max}`;
                    } else if (method === 'quantity') {
                        const unit = latestObs.quantity_unit || tracker.quantity_unit || (nameLower.includes('walk') ? 'min' : '');
                        if (nameLower.includes('walk')) {
                            description = 'You have walked for';
                            const formattedUnit = (!unit || unit === 'min' || unit === 'm') ? 'm' : ` ${unit}`;
                            formattedValue = `${escapeHTML(String(latestObs.value))}${formattedUnit}`;
                        } else {
                            description = 'You have logged';
                            const formattedUnit = unit ? ` ${unit}` : '';
                            formattedValue = `${escapeHTML(String(latestObs.value))}${formattedUnit}`;
                        }
                    } else {
                        description = `Your average ${escapeHTML(nameLower)} level is`;
                        formattedValue = escapeHTML(String(latestObs.value));
                    }
                }

                return `
                    <div class="flex items-center justify-between">
                        <div class="space-y-0.5">
                            <div class="flex items-center space-x-2 text-sm font-bold text-[#484541]">
                                <span class="w-2.5 h-2.5 rounded-full inline-block shrink-0" style="background-color: ${dotColor};"></span>
                                <span class="truncate">${escapeHTML(tracker.name)}</span>
                            </div>
                            <p class="text-xs text-[#7B7672] pl-4.5">${description}</p>
                        </div>
                        <div class="text-base font-extrabold text-[#4A6B5D] text-right shrink-0">
                            ${formattedValue}
                        </div>
                    </div>
                `;
            }).join('');
        }

        return `
            <div class="recovery-card-recently bg-[#FEFAF4] rounded-3xl p-6 shadow-xs border border-white/60 flex flex-col mt-2.5" style="margin-top: 10px; background-color: #FEFAF4; height: 329px; min-height: 329px; max-height: 329px; box-sizing: border-box;" data-tempo-ui="recovery-recently">
                <!-- Fixed Header -->
                <div class="shrink-0 space-y-3">
                    <div class="flex items-center justify-between pb-1">
                        <h4 class="font-heading text-xl font-extrabold text-[#484541]">
                            Recently
                        </h4>
                        <button type="button" 
                                onclick="if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('open', { sourceContext: 'recovery' }); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; }"
                                class="px-3 py-1 rounded-full text-xs font-bold bg-[#7D9485] hover:bg-[#6D8475] text-white shadow-2xs transition cursor-pointer">
                            Adjust Tracking
                        </button>
                    </div>

                    <!-- Divider line -->
                    <div class="border-b border-[#F0EBE6]"></div>
                </div>

                <!-- Scrollable Metrics Content -->
                <div class="flex-1 min-h-0 overflow-y-auto overflow-x-hidden pt-3 pb-1 space-y-3 pr-1" data-tempo-ui="recently-metrics-scroll" style="scrollbar-width: thin;">
                    ${itemsHTML}
                </div>

                <!-- Fixed Footer -->
                <div class="pt-3 text-center text-xs font-bold text-[#55504A] shrink-0" data-tempo-ui="recently-countdown-footer">
                    ${countdownText}
                </div>
            </div>
        `;
    }

    