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
    