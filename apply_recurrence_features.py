import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('planWorkspace.js', 'r', encoding='utf-8') as f:
    pw_text = f.read()

assert '\r\n' not in pw_text, "planWorkspace.js has CRLF!"

# 1. Add recurrence state variable
old_state = "    let adjustAvailShowAdd = false;"
new_state = "    let adjustAvailShowAdd = false;\n    let repeatConfigDate = null;"
assert old_state in pw_text, "old_state not found in planWorkspace.js"
pw_text = pw_text.replace(old_state, new_state, 1)

# 2. Add recurrence helpers right after cleanupExpiredAvailability
old_cleanup_end = """        if (changed) {
            plan.availabilityDays = cleanedDays;
        }

        return changed;
    }"""

new_recurrence_helpers = """        if (changed) {
            plan.availabilityDays = cleanedDays;
        }

        return changed;
    }

    /**
     * Recurrence & Copy helpers for Availability
     */
    function getRecurringRules() {
        try {
            const saved = localStorage.getItem('tempo_availability_recurring_rules');
            if (saved) {
                const parsed = JSON.parse(saved);
                if (Array.isArray(parsed)) return parsed;
            }
        } catch (e) {}
        const plan = getActivePlan();
        if (plan && Array.isArray(plan.recurringAvailabilityRules)) {
            return plan.recurringAvailabilityRules;
        }
        return [];
    }

    function saveRecurringRule(rule) {
        const rules = getRecurringRules().filter(r => r.id !== rule.id && r.sourceDate !== rule.sourceDate);
        rules.push(rule);
        try {
            localStorage.setItem('tempo_availability_recurring_rules', JSON.stringify(rules));
        } catch (e) {}
        const plan = getActivePlan();
        if (plan) {
            plan.recurringAvailabilityRules = rules;
        }
        return rules;
    }

    function disableRecurringRule(sourceDate) {
        const rules = getRecurringRules();
        const rule = rules.find(r => r.sourceDate === sourceDate || (r.startDate && r.startDate === sourceDate));
        if (rule) {
            rule.enabled = false;
            try {
                localStorage.setItem('tempo_availability_recurring_rules', JSON.stringify(rules));
            } catch (e) {}
            const plan = getActivePlan();
            if (plan) {
                plan.recurringAvailabilityRules = rules;
                const todayStr = getLocalTodayISO();
                (plan.availabilityDays || []).forEach(day => {
                    if (day.date >= todayStr && Array.isArray(day.blocks)) {
                        day.blocks = day.blocks.filter(b => !String(b.id).startsWith(`b_rec_${rule.id}`));
                    }
                });
            }
        }
        return rules;
    }

    function getRecurringRuleForDate(dateStr) {
        const rules = getRecurringRules();
        return rules.find(r => r.enabled !== false && (r.sourceDate === dateStr || r.startDate === dateStr));
    }

    function applyRecurringRulesToPlan(plan) {
        if (!plan) return false;
        if (!Array.isArray(plan.availabilityDays)) plan.availabilityDays = [];

        const rules = getRecurringRules().filter(r => r.enabled !== false && Array.isArray(r.slots) && r.slots.length > 0);
        if (rules.length === 0) return false;

        const todayStr = getLocalTodayISO();
        let changed = false;

        rules.forEach(rule => {
            if (!rule.startDate) return;
            const [sY, sM, sD] = rule.startDate.split('-').map(Number);
            let curDate = new Date(sY, sM - 1, sD);

            while (curDate.getDay() !== rule.weekday) {
                curDate.setDate(curDate.getDate() + 1);
            }

            const maxWeeks = 8;
            const maxDate = new Date(curDate.getTime() + maxWeeks * 7 * 86400000);
            const pad = n => String(n).padStart(2, '0');

            while (curDate <= maxDate) {
                const dateStr = `${curDate.getFullYear()}-${pad(curDate.getMonth() + 1)}-${pad(curDate.getDate())}`;

                if (rule.endDate && dateStr > rule.endDate) {
                    break;
                }

                if (dateStr >= todayStr) {
                    let day = plan.availabilityDays.find(d => d.date === dateStr);
                    if (!day) {
                        day = {
                            date: dateStr,
                            label: formatScheduledDateLabel(dateStr, isViLocale()) || dateStr,
                            isUnavailable: false,
                            blocks: []
                        };
                        plan.availabilityDays.push(day);
                        changed = true;
                    }
                    if (!Array.isArray(day.blocks)) day.blocks = [];

                    rule.slots.forEach((s, sIdx) => {
                        const exists = day.blocks.some(b => b.start === s.start && b.end === s.end);
                        if (!exists) {
                            day.blocks.push({
                                id: `b_rec_${rule.id}_${dateStr}_${sIdx}`,
                                start: s.start,
                                end: s.end
                            });
                            changed = true;
                        }
                    });
                    day.blocks.sort((a, b) => a.start.localeCompare(b.start));
                }

                curDate.setDate(curDate.getDate() + 7);
            }
        });

        if (changed) {
            plan.availabilityDays.sort((a, b) => a.date.localeCompare(b.date));
        }
        return changed;
    }

    function copyTodayAvailabilityToTomorrow() {
        const plan = getActivePlan();
        if (!plan) return;

        const todayStr = getLocalTodayISO();
        const tomorrowStr = getLocalTomorrowISO();

        const todayDay = (plan.availabilityDays || []).find(d => d.date === todayStr);
        const todayBlocks = todayDay && Array.isArray(todayDay.blocks) ? todayDay.blocks : [];

        if (todayBlocks.length === 0) {
            const noMsg = window.t ? window.t('workspace.noWorkingHours', {}, 'No working hours available to copy.') : 'No working hours available to copy.';
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast(noMsg);
            } else {
                alert(noMsg);
            }
            return;
        }

        if (!Array.isArray(plan.availabilityDays)) plan.availabilityDays = [];
        let tomorrowDay = plan.availabilityDays.find(d => d.date === tomorrowStr);
        if (!tomorrowDay) {
            tomorrowDay = {
                date: tomorrowStr,
                label: formatScheduledDateLabel(tomorrowStr, isViLocale()) || tomorrowStr,
                isUnavailable: false,
                blocks: []
            };
            plan.availabilityDays.push(tomorrowDay);
            plan.availabilityDays.sort((a, b) => a.date.localeCompare(b.date));
        }
        if (!Array.isArray(tomorrowDay.blocks)) tomorrowDay.blocks = [];

        let copiedCount = 0;
        todayBlocks.forEach(b => {
            const exists = tomorrowDay.blocks.some(tb => tb.start === b.start && tb.end === b.end);
            if (!exists) {
                tomorrowDay.blocks.push({
                    id: 'b_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
                    start: b.start,
                    end: b.end
                });
                copiedCount++;
            }
        });

        tomorrowDay.blocks.sort((a, b) => a.start.localeCompare(b.start));
        persistPlan(plan);

        const successMsg = window.t ? window.t('workspace.copiedSuccessfully', {}, 'Working hours copied successfully.') : 'Working hours copied successfully.';
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(successMsg);
        } else {
            alert(successMsg);
        }
        render();
    }

    function openRepeatWeeklyModal(dateStr) {
        repeatConfigDate = dateStr;
        activeModal = 'repeat-weekly-config';
        render();
    }

    function closeRepeatWeeklyModal() {
        activeModal = 'adjust-availability';
        repeatConfigDate = null;
        render();
    }

    function confirmRepeatWeekly() {
        if (!repeatConfigDate) return;
        const plan = getActivePlan();
        if (!plan) return;

        const repeatEveryWeekCb = document.getElementById('pw-repeat-every-week');
        const startDateInput = document.getElementById('pw-repeat-start-date');
        const endDateInput = document.getElementById('pw-repeat-end-date');

        const enabled = repeatEveryWeekCb ? repeatEveryWeekCb.checked : true;
        const startDate = startDateInput ? startDateInput.value.trim() : repeatConfigDate;
        const endDate = endDateInput ? endDateInput.value.trim() : '';

        if (!enabled) {
            disableRecurringRule(repeatConfigDate);
            persistPlan(plan);
            const disabledMsg = isViLocale() ? 'Đã tắt lặp lại hàng tuần.' : 'Weekly recurrence disabled.';
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast(disabledMsg);
            }
            closeRepeatWeeklyModal();
            return;
        }

        const day = (plan.availabilityDays || []).find(d => d.date === repeatConfigDate);
        const dayBlocks = day && Array.isArray(day.blocks) ? day.blocks : [];

        if (dayBlocks.length === 0) {
            const noMsg = window.t ? window.t('workspace.noWorkingHours', {}, 'No working hours available to copy.') : 'No working hours available to copy.';
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast(noMsg);
            } else {
                alert(noMsg);
            }
            return;
        }

        const [sY, sM, sD] = startDate.split('-').map(Number);
        const sDateObj = new Date(sY, sM - 1, sD);
        const weekday = sDateObj.getDay();

        const existingRule = getRecurringRuleForDate(repeatConfigDate);
        const rule = {
            id: existingRule ? existingRule.id : 'rec_' + Date.now(),
            sourceDate: repeatConfigDate,
            weekday: weekday,
            slots: dayBlocks.map(b => ({ start: b.start, end: b.end })),
            startDate: startDate,
            endDate: endDate || null,
            enabled: true,
            createdAt: Date.now()
        };

        saveRecurringRule(rule);
        applyRecurringRulesToPlan(plan);
        persistPlan(plan);

        const successMsg = isViLocale() ? 'Đã cài đặt lặp lại hàng tuần thành công.' : 'Weekly recurrence configured successfully.';
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(successMsg);
        } else {
            alert(successMsg);
        }
        closeRepeatWeeklyModal();
    }"""

assert old_cleanup_end in pw_text, "old_cleanup_end not found!"
pw_text = pw_text.replace(old_cleanup_end, new_recurrence_helpers, 1)

# 3. In openAdjustAvailabilityModal: apply recurring rules as well
old_open_avail = """    function openAdjustAvailabilityModal() {
        const plan = getActivePlan();
        if (plan) {
            const changed = cleanupExpiredAvailability(plan);
            if (changed) {
                persistPlan(plan);
            }
        }
        activeModal = 'adjust-availability';
        adjustAvailShowAdd = false;
        render();
    }"""

new_open_avail = """    function openAdjustAvailabilityModal() {
        const plan = getActivePlan();
        if (plan) {
            const c1 = cleanupExpiredAvailability(plan);
            const c2 = applyRecurringRulesToPlan(plan);
            if (c1 || c2) {
                persistPlan(plan);
            }
        }
        activeModal = 'adjust-availability';
        adjustAvailShowAdd = false;
        render();
    }"""
assert old_open_avail in pw_text, "old_open_avail not found!"
pw_text = pw_text.replace(old_open_avail, new_open_avail, 1)

# 4. In render(): also apply recurring rules
old_render_avail = """        // Automatically clean up expired availability slots on load/render
        const availExpiredChanged = cleanupExpiredAvailability(plan);
        if (availExpiredChanged) {
            persistPlan(plan);
        }"""

new_render_avail = """        // Automatically clean up expired availability slots on load/render
        const availExpiredChanged = cleanupExpiredAvailability(plan);
        const availRecurringChanged = applyRecurringRulesToPlan(plan);
        if (availExpiredChanged || availRecurringChanged) {
            persistPlan(plan);
        }"""
assert old_render_avail in pw_text, "old_render_avail not found!"
pw_text = pw_text.replace(old_render_avail, new_render_avail, 1)

# 5. In adjust-availability modal render: add Copy to Tomorrow and Repeat Weekly buttons
old_avail_days_render = """                        <div class="space-y-4 text-xs">
                            ${days.map(d => `
                                <div class="p-3.5 bg-stone-50 rounded-2xl border border-stone-100 space-y-2">
                                    <div class="flex items-center justify-between font-bold text-stone-800">
                                        <span>${escapeHTML(d.label || d.date)}</span>
                                        <span class="text-[10px] text-stone-500 uppercase tracking-wider">${d.date}</span>
                                    </div>

                                    <div class="space-y-1.5">
                                        ${(d.blocks || []).map(b => `
                                            <div class="p-2 bg-white rounded-xl border border-gray-200 flex items-center justify-between">
                                                <span class="font-semibold text-[#202124]">${formatTime12H(b.start)} – ${formatTime12H(b.end)}</span>
                                                <button onclick="window.TempoPlanWorkspace.removeAvailabilityBlock('${d.date}', '${b.id}')"
                                                        class="text-stone-400 hover:text-rose-600 text-xs px-1">✕</button>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            `).join('')}"""

new_avail_days_render = """                        <div class="space-y-4 text-xs">
                            ${days.map(d => {
                                const todayStr = getLocalTodayISO();
                                const isToday = (d.date === todayStr);
                                const dayBlocks = Array.isArray(d.blocks) ? d.blocks : [];
                                const recurringRule = getRecurringRuleForDate(d.date);
                                const isRecurring = !!recurringRule && recurringRule.enabled !== false;

                                return `
                                    <div class="p-3.5 bg-stone-50 rounded-2xl border border-stone-100 space-y-2.5" data-avail-day="${d.date}">
                                        <div class="flex flex-wrap items-center justify-between gap-2 font-bold text-stone-800">
                                            <div class="flex items-center space-x-2">
                                                <span class="text-xs sm:text-sm text-[#202124]">${escapeHTML(formatScheduledDateLabel(d.date, isViLocale()) || d.label || d.date)}</span>
                                                <span class="text-[10px] text-stone-500 uppercase tracking-wider">${d.date}</span>
                                                ${isRecurring ? `
                                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#E8EFE8] text-[#556B54] border border-[#C5D8C3]" title="${window.t ? window.t('workspace.repeatEveryWeek', {}, 'Repeat every week') : 'Repeat every week'}">
                                                        🔄 ${isViLocale() ? 'Hàng tuần' : 'Weekly'}
                                                    </span>
                                                ` : ''}
                                            </div>

                                            <!-- Day Actions -->
                                            <div class="flex items-center space-x-1.5 shrink-0">
                                                ${isToday ? `
                                                    <button type="button"
                                                            id="btn-copy-to-tomorrow"
                                                            onclick="window.TempoPlanWorkspace.copyTodayAvailabilityToTomorrow()"
                                                            class="px-2.5 py-1 rounded-xl text-xs font-semibold text-[#688270] bg-[#E8EFE8] hover:bg-[#D5E4D4] border border-[#CCDCCD] transition cursor-pointer flex items-center space-x-1"
                                                            title="${window.t ? window.t('workspace.copyToTomorrow', {}, 'Copy to Tomorrow') : 'Copy to Tomorrow'}">
                                                        <span>📋</span>
                                                        <span>${window.t ? window.t('workspace.copyToTomorrow', {}, 'Copy to Tomorrow') : 'Copy to Tomorrow'}</span>
                                                    </button>
                                                ` : ''}
                                                <button type="button"
                                                        data-repeat-day="${d.date}"
                                                        onclick="window.TempoPlanWorkspace.openRepeatWeeklyModal('${d.date}')"
                                                        class="px-2.5 py-1 rounded-xl text-xs font-semibold ${isRecurring ? 'text-amber-800 bg-amber-100 border border-amber-300 hover:bg-amber-200' : 'text-[#8C6D62] bg-[#F7EFEA] hover:bg-[#EFE3DC] border border-[#E8D7CE]'} transition cursor-pointer flex items-center space-x-1"
                                                        title="${window.t ? window.t('workspace.repeatWeekly', {}, 'Repeat Weekly') : 'Repeat Weekly'}">
                                                    <span>🔄</span>
                                                    <span>${window.t ? window.t('workspace.repeatWeekly', {}, 'Repeat Weekly') : 'Repeat Weekly'}</span>
                                                </button>
                                            </div>
                                        </div>

                                        <div class="space-y-1.5">
                                            ${dayBlocks.length > 0 ? dayBlocks.map(b => `
                                                <div class="p-2 bg-white rounded-xl border border-gray-200 flex items-center justify-between">
                                                    <span class="font-semibold text-[#202124]">${formatTime12H(b.start)} – ${formatTime12H(b.end)}</span>
                                                    <button onclick="window.TempoPlanWorkspace.removeAvailabilityBlock('${d.date}', '${b.id}')"
                                                            class="text-stone-400 hover:text-rose-600 text-xs px-1"
                                                            title="Remove">✕</button>
                                                </div>
                                            `).join('') : `
                                                <div class="text-[11px] text-stone-400 italic py-1">
                                                    ${window.t ? window.t('workspace.noWorkingHours', {}, 'No working hours available to copy.') : 'No working hours available.'}
                                                </div>
                                            `}
                                        </div>
                                    </div>
                                `;
                            }).join('')}"""

assert old_avail_days_render in pw_text, "old_avail_days_render not found!"
pw_text = pw_text.replace(old_avail_days_render, new_avail_days_render, 1)

# 6. In renderModalsHTML: add repeat-weekly-config modal dialog
repeat_modal_code = """        if (activeModal === 'repeat-weekly-config' && repeatConfigDate) {
            const day = (plan.availabilityDays || []).find(d => d.date === repeatConfigDate);
            const dayBlocks = day && Array.isArray(day.blocks) ? day.blocks : [];
            const existingRule = getRecurringRuleForDate(repeatConfigDate);
            const dayLabel = formatScheduledDateLabel(repeatConfigDate, isViLocale()) || repeatConfigDate;

            return `
                <div id="modal-repeat-weekly"
                     onclick="if (event.target === this) window.TempoPlanWorkspace.closeRepeatWeeklyModal();"
                     class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4"
                     role="dialog"
                     aria-modal="true">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-md w-full relative">
                        <button type="button"
                                onclick="window.TempoPlanWorkspace.closeRepeatWeeklyModal()"
                                class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer"
                                title="Close">✕</button>

                        <div class="space-y-1 pr-6">
                            <h3 class="font-heading text-lg sm:text-xl font-bold text-[#202124]">
                                ${window.t ? window.t('workspace.repeatWeekly', {}, 'Repeat Weekly') : 'Repeat Weekly'}
                            </h3>
                            <p class="text-xs text-[#6F6B68]">
                                ${escapeHTML(dayLabel)} (${repeatConfigDate})
                            </p>
                        </div>

                        <!-- Current pattern summary -->
                        <div class="p-3 bg-[#FDFBF6] border border-[#E3C7A5] rounded-xl space-y-1.5 text-xs">
                            <div class="font-semibold text-stone-700">
                                ${isViLocale() ? 'Khung giờ lặp lại:' : 'Working hours pattern:'}
                            </div>
                            <div class="text-[#202124] font-medium space-y-0.5">
                                ${dayBlocks.length > 0 ? dayBlocks.map(b => `<div>• ${formatTime12H(b.start)} – ${formatTime12H(b.end)}</div>`).join('') : `<div class="italic text-stone-400">${window.t ? window.t('workspace.noWorkingHours', {}, 'No working hours available.') : 'No working hours available.'}</div>`}
                            </div>
                        </div>

                        <!-- Recurrence Form Settings -->
                        <div class="space-y-3.5 text-xs">
                            <!-- Repeat every week checkbox -->
                            <div class="flex items-center space-x-2.5">
                                <input id="pw-repeat-every-week"
                                       type="checkbox"
                                       ${!existingRule || existingRule.enabled !== false ? 'checked' : ''}
                                       class="w-4 h-4 rounded text-[#D99E87] focus:ring-[#D99E87] cursor-pointer">
                                <label for="pw-repeat-every-week" class="font-bold text-stone-800 cursor-pointer">
                                    ${window.t ? window.t('workspace.repeatEveryWeek', {}, 'Repeat every week') : 'Repeat every week'}
                                </label>
                            </div>

                            <!-- Start date -->
                            <div>
                                <label class="block text-[11px] font-semibold text-stone-600 mb-1">
                                    ${window.t ? window.t('workspace.startDate', {}, 'Start date') : 'Start date'}
                                </label>
                                <input id="pw-repeat-start-date"
                                       type="date"
                                       value="${existingRule?.startDate || repeatConfigDate}"
                                       class="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:outline-none focus:ring-1 focus:ring-[#D99E87]">
                            </div>

                            <!-- End date (optional) -->
                            <div>
                                <label class="block text-[11px] font-semibold text-stone-600 mb-1">
                                    ${window.t ? window.t('workspace.endDate', {}, 'End date (optional)') : 'End date (optional)'}
                                </label>
                                <input id="pw-repeat-end-date"
                                       type="date"
                                       value="${existingRule?.endDate || ''}"
                                       placeholder="YYYY-MM-DD"
                                       class="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:outline-none focus:ring-1 focus:ring-[#D99E87]">
                                <span class="text-[10px] text-stone-400 mt-0.5 block">
                                    ${isViLocale() ? 'Để trống nếu muốn lặp lại liên tục.' : 'Leave empty for ongoing weekly recurrence.'}
                                </span>
                            </div>
                        </div>

                        <!-- Action buttons -->
                        <div class="flex items-center justify-end space-x-3 pt-2 border-t border-gray-100">
                            <button type="button"
                                    onclick="window.TempoPlanWorkspace.closeRepeatWeeklyModal()"
                                    class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-600 hover:text-stone-900 border border-transparent hover:bg-stone-50 transition cursor-pointer">
                                ${window.t ? window.t('workspace.cancel', {}, 'Cancel') : 'Cancel'}
                            </button>
                            <button type="button"
                                    id="btn-confirm-repeat-weekly"
                                    onclick="window.TempoPlanWorkspace.confirmRepeatWeekly()"
                                    class="btn-primary px-5 py-2 rounded-xl text-xs font-bold shadow-sm transition cursor-pointer">
                                ${window.t ? window.t('workspace.confirm', {}, 'Confirm') : 'Confirm'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }\n\n"""

target_modal_insert = "        if (activeModal === 'adjust-availability') {"
assert target_modal_insert in pw_text, "target_modal_insert not found!"
pw_text = pw_text.replace(target_modal_insert, repeat_modal_code + target_modal_insert, 1)

# 7. Add exported methods to window.TempoPlanWorkspace
old_exports = "        openAdjustAvailabilityModal,\n        closeAdjustAvailabilityModal,\n        cleanupExpiredAvailability,"
new_exports = """        openAdjustAvailabilityModal,
        closeAdjustAvailabilityModal,
        cleanupExpiredAvailability,
        copyTodayAvailabilityToTomorrow,
        openRepeatWeeklyModal,
        closeRepeatWeeklyModal,
        confirmRepeatWeekly,
        getRecurringRules,
        saveRecurringRule,
        disableRecurringRule,
        applyRecurringRulesToPlan,"""
assert old_exports in pw_text, "old_exports not found!"
pw_text = pw_text.replace(old_exports, new_exports, 1)

assert '\r\n' not in pw_text, "CRLF detected in planWorkspace.js"
with open('planWorkspace.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(pw_text)
print("planWorkspace.js updated successfully with Recurrence & Copy features! (LF only)")
