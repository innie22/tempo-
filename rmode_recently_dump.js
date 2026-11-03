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

    function renderRecoveryNoteCard(ctx) {
        return renderEmodeCreateNotesCard(ctx);
    }

    // Canonical task completion status evaluator: strictly source of truth
    function isTaskExplicitlyCompleted(taskItem) {
        if (!taskItem) return false;
        const task = (taskItem && taskItem.task) ? taskItem.task : taskItem;

        // 1. Direct boolean property
        if (task.completed === true || taskItem.completed === true) return true;
        if (task.completed === false || taskItem.completed === false) return false;

        // 2. String representation ("true" / "false")
        if (task.completed === 'true' || taskItem.completed === 'true') return true;
        if (task.completed === 'false' || taskItem.completed === 'false') return false;

        // 3. Execution / progress status
        const status = String(task.executionStatus || task.execution_status || task.status || taskItem.executionStatus || taskItem.status || '').toLowerCase();
        if (status === 'completed' || status === 'done') return true;
        if (status === 'pending' || status === 'in_progress' || status === 'active' || status === 'not_started') return false;

        // 4. Default: strictly NOT completed (never infer completion from missing value, position, or mock state)
        return false;
    }

    function formatPlanDateHeader(dateStr, fallbackLabel) {
        if (!dateStr || typeof dateStr !== 'string') return fallbackLabel || (isViLocale() ? 'Đã lên lịch' : 'Scheduled');
        const clean = dateStr.split(/[T ]/)[0];
        if (window.TempoI18n && typeof window.TempoI18n.formatCalendarDate === 'function') {
            return window.TempoI18n.formatCalendarDate(clean, isViLocale() ? 'vi' : 'en');
        }
        return fallbackLabel || dateStr;
    }

    