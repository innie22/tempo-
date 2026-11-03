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
