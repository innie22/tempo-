# -*- coding: utf-8 -*-
import sys

with open('emergencyFlow.js', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update Entry state resume box (Urgent Plan -> Working Plan)
code = code.replace(
    '''<span class="px-3 py-1 rounded-full text-xs font-extrabold bg-[#FFE9DC] text-[#B83D08] uppercase tracking-wider">\n                            Active Urgent Plan\n                        </span>''',
    '''<span class="px-3 py-1 rounded-full text-xs font-extrabold bg-[#DCE7DF] text-[#2B4B39] uppercase tracking-wider">\n                            ${isViLocale() ? 'Working Plan đang hoạt động' : 'Active Working Plan'}\n                        </span>'''
)
code = code.replace(
    '''<h4 class="font-heading text-lg font-bold text-[#202124]">You have an active Urgent Plan</h4>''',
    '''<h4 class="font-heading text-lg font-bold text-[#202124]">${isViLocale() ? 'Bạn đang có một Working Plan hoạt động' : 'You have an active Working Plan'}</h4>'''
)

# 2. Update Handoff state (Urgent Plan -> Working Plan)
code = code.replace(
    '''<span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">URGENT PLAN READY</span>''',
    '''<span class="text-xs font-extrabold uppercase tracking-widest text-[#4A6B5D]">${isViLocale() ? 'WORKING PLAN ĐÃ SẴN SÀNG' : 'WORKING PLAN READY'}</span>'''
)
code = code.replace(
    '''You've completed every task in this Urgent Plan.''',
    '''You've completed every task in this Working Plan.'''
)
code = code.replace(
    '''View / Edit Urgent Plan''',
    '''${isVi ? 'Xem / Sửa Working Plan' : 'View / Edit Working Plan'}'''
)

# 3. Replace renderPlanReview & renderPlanEditWarningModalHTML
idx_pr_start = code.find('    function renderPlanReview() {')
idx_pr_end = code.find('    function navigateBackFromPlan() {')
if idx_pr_start == -1 or idx_pr_end == -1:
    raise Exception('Could not find renderPlanReview block boundaries')

new_render_plan_review = '''    function renderPlanReview() {
        const container = document.getElementById('emergency-stage-plan-review');
        if (!container || !confirmedPlan) return;
        const isVi = isViLocale();

        // Group planned tasks by Day in order of availabilityDays
        const daysMap = {};
        availabilityDays.forEach(day => {
            daysMap[day.date] = { dayObj: day, tasks: [] };
        });
        confirmedPlan.plannedTasks.forEach((item, idx) => {
            const targetDate = item.dayDate || (availabilityDays.find(d => d.label === item.dayLabel)?.date) || (availabilityDays[0] ? availabilityDays[0].date : '');
            if (!daysMap[targetDate]) {
                const dayObj = availabilityDays.find(d => d.date === targetDate) || { date: targetDate, label: formatDayLabel(targetDate, isVi) };
                daysMap[targetDate] = { dayObj, tasks: [] };
            }
            daysMap[targetDate].tasks.push({ ...item, globalIndex: idx });
        });

        const activeDayDates = Object.keys(daysMap).filter(dateKey => daysMap[dateKey].tasks.length > 0);
        const hasSavedActive = !!(confirmedPlan && confirmedPlan.plannedTasks && confirmedPlan.plannedTasks.length > 0 && window.TempoPlanStore && window.TempoPlanStore.getActivePlan('emergency'));
        const returnToHandoff = viewingFromHandoff || hasSavedActive;

        container.innerHTML = `
            <div class="max-w-2xl mx-auto py-8 sm:py-10 space-y-6">
                <!-- Secondary Back Navigation -->
                <div class="flex items-center justify-between">
                    <button onclick="${returnToHandoff ? "window.TempoEmergencyFlow.goToStage('handoff')" : "window.TempoEmergencyFlow.navigateBackFromPlan()"}" 
                            class="inline-flex items-center text-xs font-semibold text-[#5C665F] hover:text-[#202124] transition py-1 group cursor-pointer">
                        <span class="mr-1.5 group-hover:-translate-x-0.5 transition-transform">←</span>
                        <span>${returnToHandoff 
                            ? (isVi ? 'Quay lại tổng quan kế hoạch' : 'Back to plan overview') 
                            : (isVi ? 'Quay lại phần thời gian có thể sắp xếp' : 'Back to availability')}</span>
                    </button>
                </div>

                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#4A6B5D]">WORKING PLAN</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        ${isVi ? 'Working Plan của bạn' : 'Your Working Plan'}
                    </h2>
                    <p class="text-xs sm:text-sm text-[#5C665F] max-w-md mx-auto leading-relaxed">
                        ${isVi 
                            ? 'Đây là kế hoạch gợi ý dựa trên thông tin bạn cung cấp. Bạn có thể sắp xếp lại thứ tự, chuyển task giữa các ngày hoặc điều chỉnh thời lượng bất cứ lúc nào.' 
                            : "Here's a starting point based on what you told us. You can reorder, move between days, or adjust estimates anytime."}
                    </p>
                </div>

                <!-- Unallocated Tasks Notice (if any) -->
                ${confirmedPlan.unallocatedTasks && confirmedPlan.unallocatedTasks.length > 0 ? `
                    <div class="p-4 bg-amber-50 border border-amber-200 rounded-2xl space-y-2 text-xs text-amber-900 shadow-xs">
                        <div class="flex items-center space-x-2 font-bold">
                            <span>⚠️</span>
                            <span>${confirmedPlan.unallocatedTasks.length} task${!isVi && confirmedPlan.unallocatedTasks.length > 1 ? 's' : ''} ${isVi ? 'cần thêm thời gian làm việc' : 'need more available working blocks'}</span>
                        </div>
                        <p class="text-amber-800">
                            ${isVi ? 'Chúng tôi đã ưu tiên sắp xếp những việc vừa với khung giờ. Các việc sau vẫn cần thêm thời gian: ' : 'We scheduled what fits first. The following work still needs dedicated time: '}
                            <strong>${confirmedPlan.unallocatedTasks.map(t => escapeHTML(t.name)).join(', ')}</strong>.
                        </p>
                        <button onclick="window.TempoEmergencyFlow.navigateBackFromPlan()" 
                                class="text-xs font-bold text-[#446A7B] hover:text-[#2F4D5B] underline cursor-pointer">
                            ${isVi ? '+ Thêm thời gian làm việc để xếp hết các task' : '+ Add more availability to fit everything'}
                        </button>
                    </div>
                ` : ''}

                <!-- Lightweight Timeline -->
                <div class="space-y-6">
                    ${activeDayDates.length === 0 ? `
                        <div class="p-8 bg-white border border-[#D5DED7] rounded-[22px] text-center text-xs text-[#5C665F]">
                            ${isVi ? 'Không có task nào trong kế hoạch. Hãy quay lại phần Trút bỏ suy nghĩ để thêm task.' : 'No tasks scheduled in plan. Return to Reality Check to add tasks.'}
                        </div>
                    ` : activeDayDates.map(dayDate => {
                        const dayEntry = daysMap[dayDate];
                        const dayObj = dayEntry ? dayEntry.dayObj : null;
                        const dayTasks = dayEntry ? dayEntry.tasks : [];
                        const dayLabelFormatted = formatDayLabel(dayDate, isVi);
                        const hasDayConflict = dayTasks.some(item => item.isOverCapacity);
                        const isToday = dayDate === getTodayISO();
                        const isTomorrow = dayDate === getTomorrowISO();

                        const conflictMsg = isToday
                            ? (isVi ? 'Các task được lên lịch hôm nay vượt quá tổng thời gian bạn có thể dành ra.' : 'Tasks scheduled for TODAY exceed available capacity.')
                            : (isTomorrow
                                ? (isVi ? 'Các task được lên lịch ngày mai vượt quá tổng thời gian bạn có thể dành ra.' : 'Tasks scheduled for TOMORROW exceed available capacity.')
                                : (isVi ? `Các task được lên lịch ${dayLabelFormatted} vượt quá tổng thời gian bạn có thể dành ra.` : `Tasks scheduled for ${dayLabelFormatted} exceed available capacity.`));

                        return `
                        <div class="space-y-3"
                             ondragover="window.TempoEmergencyFlow.handleDragOver(event)"
                             ondrop="window.TempoEmergencyFlow.handleDropOnDay(event, '${dayDate}')">
                            <div class="flex items-center justify-between px-1">
                                <h4 class="font-heading text-xs font-extrabold tracking-wider text-[#4A6B5D] uppercase">
                                    ${dayLabelFormatted}
                                </h4>
                            </div>

                            ${hasDayConflict ? `
                                <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-center space-x-2">
                                    <span>⚠️</span>
                                    <span><strong>${isVi ? 'Xung đột thời gian:' : 'Availability conflict:'}</strong> ${conflictMsg}</span>
                                </div>
                            ` : ''}

                            <div class="space-y-3">
                                ${dayTasks.map((item, dIdx) => {
                                    const nextItem = dayTasks[dIdx + 1];
                                    const badgeClass = item.executionBadge === 'UP NEXT'
                                        ? 'bg-[#DCE7DF] text-[#244634] border border-[#8EA28F]/40'
                                        : (item.executionBadge === 'THEN' 
                                            ? 'bg-[#E3EDF2] text-[#244759] border border-[#93AFBC]/40' 
                                            : 'bg-[#FAF2EE] text-[#7B4B3B] border border-[#ECC9BA]/50');

                                    const badgeText = item.executionBadge === 'UP NEXT'
                                        ? (isVi ? 'TIẾP THEO' : 'UP NEXT')
                                        : (item.executionBadge === 'THEN'
                                            ? (isVi ? 'SAU ĐÓ' : 'THEN')
                                            : (isVi ? 'LÀM SAU' : 'LATER'));

                                    const isWarned = item.hasDeadlineConflict && !ignoredDeadlineWarnings.has(item.task.id);

                                    return `
                                        <div class="em-timeline-card group p-4 sm:p-5 space-y-3 shadow-xs hover:shadow-md transition-all border border-[#D5DED7] hover:border-[#CAD5CD] rounded-[22px] bg-white cursor-default"
                                             data-global-index="${item.globalIndex}"
                                             data-task-id="${item.task.id}"
                                             draggable="true"
                                             ondragstart="window.TempoEmergencyFlow.handleDragStart(event, ${item.globalIndex})"
                                             ondragover="window.TempoEmergencyFlow.handleDragOver(event)"
                                             ondragenter="window.TempoEmergencyFlow.handleDragEnter(event)"
                                             ondragleave="window.TempoEmergencyFlow.handleDragLeave(event)"
                                             ondrop="window.TempoEmergencyFlow.handleDrop(event, ${item.globalIndex})"
                                             ondragend="window.TempoEmergencyFlow.handleDragEnd(event)">
                                            <!-- Top Meta Row -->
                                            <div class="flex items-center justify-between">
                                                <div class="flex items-center space-x-2">
                                                    <!-- Subtle Drag Handle -->
                                                    <div class="em-drag-handle flex items-center justify-center text-stone-400 group-hover:text-stone-700 hover:text-[#244634] hover:bg-[#EDF4EF] px-1.5 py-1 rounded-md select-none transition-colors mr-0.5 cursor-grab active:cursor-grabbing"
                                                         title="${isVi ? 'Kéo để thay đổi thứ tự ưu tiên' : 'Drag to change execution order'}"
                                                         aria-label="${isVi ? 'Kéo để thay đổi thứ tự ưu tiên' : 'Drag to change execution order'}"
                                                         tabindex="0"
                                                         data-drag-handle="true">
                                                        <span class="text-sm font-bold tracking-widest leading-none select-none pointer-events-none">⋮⋮</span>
                                                    </div>
                                                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold tracking-wider uppercase border ${badgeClass}">
                                                        ${badgeText}
                                                    </span>
                                                    ${item.startTime && item.endTime ? `
                                                        <span class="text-xs font-extrabold text-[#202124]">
                                                            ${item.startTime} – ${item.endTime}
                                                        </span>
                                                    ` : (item.task.isUnknownDuration ? `
                                                        <span class="px-2 py-0.5 bg-stone-100 text-stone-600 rounded text-[11px] font-semibold">
                                                            ${isVi ? 'Linh hoạt / Chưa xếp giờ' : 'Flexible / Untimed'}
                                                        </span>
                                                    ` : (item.isOverCapacity ? `
                                                        <span class="px-2 py-0.5 bg-amber-100 text-amber-800 rounded text-[11px] font-semibold">
                                                            ⚠️ ${isVi ? 'Đã lên lịch (Vượt quá khung giờ)' : 'Scheduled (Beyond available blocks)'}
                                                        </span>
                                                    ` : `
                                                        <span class="px-2 py-0.5 bg-stone-100 text-stone-600 rounded text-[11px] font-semibold">
                                                            ${isVi ? 'Linh hoạt' : 'Flexible'}
                                                        </span>
                                                    `))}
                                                </div>
                                                <div class="flex items-center space-x-1.5">
                                                    <!-- "Do this task later" Action -->
                                                    <button type="button" onclick="window.TempoEmergencyFlow.openScheduleModal(${item.globalIndex})"
                                                            class="px-3 py-1.5 text-xs font-bold border border-[#D5DED7] hover:border-[#8EA28F] hover:bg-[#EDF4EF] text-[#3D4842] hover:text-[#244634] rounded-xl transition flex items-center space-x-1 shadow-2xs cursor-pointer"
                                                            title="${isVi ? 'Để task này làm sau' : 'Do this task later'}">
                                                        <span>${isVi ? 'Để task này làm sau' : 'Do this task later'}</span>
                                                    </button>
                                                </div>
                                            </div>

                                            <!-- Task Details -->
                                            <div class="space-y-1">
                                                <h4 class="font-heading text-base font-bold text-[#202124]">${escapeHTML(item.task.name)}</h4>
                                                <p class="text-xs text-[#5C665F] flex items-center space-x-1.5 flex-wrap">
                                                    <span>${isVi ? 'Thời lượng dự kiến:' : 'Estimate:'} <strong>${item.task.durationLabel || (isVi ? 'Chưa rõ' : 'Not sure')}</strong></span>
                                                    <button onclick="window.TempoEmergencyFlow.openEditEstimateModal(${item.globalIndex})" 
                                                            class="text-[#446A7B] hover:text-[#2F4D5B] hover:underline font-semibold text-[11px] cursor-pointer">
                                                        ${isVi ? 'Sửa thời lượng' : 'Edit estimate'}
                                                    </button>
                                                    <span>•</span>
                                                    <span>Deadline: ${item.task.hasDeadline ? formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime, isVi) : (isVi ? 'Chưa có deadline' : 'No fixed deadline')}</span>
                                                    <button onclick="window.TempoEmergencyFlow.openDeadlineModal('${item.task.id}')" 
                                                            class="text-[#446A7B] hover:text-[#2F4D5B] hover:underline font-semibold text-[11px] cursor-pointer">
                                                        ${isVi ? 'Sửa Deadline' : 'Edit deadline'}
                                                    </button>
                                                </p>
                                                ${item.rhythm && item.rhythm.breaksCount > 0 ? `
                                                    <div class="text-[11px] text-[#5C665F] flex items-center space-x-1 font-medium bg-[#FEFDFB] px-2.5 py-1 rounded-lg border border-[#D5DED7] w-fit mt-1">
                                                        <span class="text-[#4A6B5D] font-bold">${isVi ? 'Nhịp làm việc:' : 'Cadence:'}</span>
                                                        <span>${item.rhythm.chunks.map((c, i) => `${c}m ${isVi ? 'tập trung' : 'focus'}${i < item.rhythm.chunks.length - 1 ? (isVi ? ' + 15m nghỉ ngơi' : ' + 15m break') : ''}`).join(' • ')}</span>
                                                    </div>
                                                ` : ''}
                                            </div>

                                            <!-- Availability Conflict Banner if task exceeds day availability -->
                                            ${item.isOverCapacity ? `
                                                <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                                    <span>⚠️ <strong>${isVi ? 'Xung đột thời gian:' : 'Availability conflict:'}</strong> ${isVi ? 'Thứ tự này cần nhiều thời gian hơn quỹ thời gian hiện có của bạn trong ngày này.' : 'This order needs more time than your current availability on this day.'}</span>
                                                    <button type="button" onclick="window.TempoEmergencyFlow.openScheduleModal(${item.globalIndex})"
                                                            class="px-2.5 py-1 bg-amber-200 hover:bg-amber-300 text-amber-900 font-bold rounded-lg text-[10px] shrink-0 cursor-pointer">
                                                        ${isVi ? 'Để task này làm sau' : 'Do this task later'}
                                                    </button>
                                                </div>
                                            ` : ''}

                                            <!-- Deadline Warning Banner if reordered past deadline -->
                                            ${isWarned ? `
                                                <div data-deadline-warning="true" class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                                    <span>⚠️ <strong>${isVi ? 'Rủi ro Deadline:' : 'Deadline risk:'}</strong> ${isVi 
                                                        ? `Với thứ tự này, ${escapeHTML(item.task.name)} có Deadline vào ${formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime, true)} và có thể hoàn thành sau Deadline.` 
                                                        : `With this order, ${escapeHTML(item.task.name)} is due on ${formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime, false)} and may finish after its deadline.`}</span>
                                                    <button onclick="window.TempoEmergencyFlow.ignoreDeadlineWarning('${item.task.id}')"
                                                            class="px-2.5 py-1 bg-amber-200 hover:bg-amber-300 text-amber-900 font-bold rounded-lg text-[10px] shrink-0 cursor-pointer">
                                                        ${isVi ? 'Giữ nguyên thứ tự của tôi' : 'Keep my order'}
                                                    </button>
                                                </div>
                                            ` : ''}
                                        </div>

                                        <!-- 30m Recovery Indicator between adjacent completed tasks -->
                                        ${nextItem && item.endTime && nextItem.startTime ? `
                                            <div class="flex items-center justify-center py-0.5">
                                                <span class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#FAF2EE] text-[#7B4B3B] text-[11px] font-medium border border-[#ECC9BA]/60">
                                                    <span>🌱</span>
                                                    <span class="font-bold">${isVi ? '30m hồi phục' : '30m recovery'}</span>
                                                    <span class="text-[#ECC9BA]">•</span>
                                                    <span>${item.endTime} – ${nextItem.startTime}</span>
                                                </span>
                                            </div>
                                        ` : ''}
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    `;
                    }).join('')}
                </div>

                <!-- Dedicated UNARRANGED Section (if any) -->
                ${confirmedPlan.unarrangedTasks && confirmedPlan.unarrangedTasks.length > 0 ? `
                    <div class="space-y-3 pt-2">
                        <div class="px-1">
                            <h4 class="font-heading text-xs font-extrabold tracking-wider text-[#4A6B5D] uppercase">
                                ${isVi ? `Tasks chưa xếp lịch (${confirmedPlan.unarrangedTasks.length})` : `Unarranged Tasks (${confirmedPlan.unarrangedTasks.length})`}
                            </h4>
                            <p class="text-xs text-[#5C665F]">
                                ${isVi ? 'Các task này chưa được ấn định khung giờ cụ thể. Bạn có thể xếp lịch cho chúng bất cứ lúc nào.' : "These tasks are not currently scheduled into a specific time window. You can schedule them whenever you're ready."}
                            </p>
                        </div>
                        <div class="space-y-2">
                            ${confirmedPlan.unarrangedTasks.map((t, uIdx) => `
                                <div class="p-4 bg-white border border-[#D5DED7] rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
                                    <div>
                                        <div class="font-bold text-sm text-[#202124]">${escapeHTML(t.name)}</div>
                                        <div class="text-xs text-[#5C665F] mt-0.5">
                                            <span>${isVi ? 'Thời lượng dự kiến:' : 'Estimate:'} ~${t.durationLabel || (isVi ? 'Chưa rõ' : 'Not sure')}</span>
                                            <span class="mx-1">•</span>
                                            <span>Deadline: ${t.hasDeadline ? formatHumanDeadline(t.deadlineDate, t.deadlineTime, isVi) : (isVi ? 'Chưa có deadline' : 'No fixed deadline')}</span>
                                        </div>
                                    </div>
                                    <button onclick="window.TempoEmergencyFlow.openScheduleModalFromUnarranged(${uIdx})"
                                            class="px-3.5 py-1.5 bg-[#EDF4EF] hover:bg-[#DCE7DF] text-[#2B4B39] font-bold text-xs rounded-xl border border-[#8EA28F]/40 transition shrink-0 self-start sm:self-auto flex items-center space-x-1 shadow-2xs cursor-pointer">
                                        <span>${isVi ? 'Xếp lịch task' : 'Schedule task'}</span>
                                        <span>→</span>
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Confirmation Card -->
                ${returnToHandoff ? `
                    <div class="p-5 bg-white border border-[#D5DED7] rounded-[22px] space-y-4 text-center shadow-xs">
                        <div class="space-y-1">
                            <h4 class="font-heading text-base font-bold text-[#202124]">${isVi ? 'Kế hoạch đã được cập nhật và lưu' : 'Plan is updated and saved'}</h4>
                            <p class="text-xs text-[#5C665F]">${isVi ? 'Mọi thay đổi bạn thực hiện đều được tự động lưu lại.' : 'Any adjustments you make are automatically saved.'}</p>
                        </div>
                        <div class="pt-1 flex flex-col sm:flex-row items-center justify-center gap-3">
                            <button onclick="window.TempoEmergencyFlow.goToStage('handoff')" 
                                     class="btn-primary w-full sm:w-auto px-6 py-3 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer">
                                ${isVi ? 'Quay lại Tổng quan Kế hoạch →' : 'Return to Plan Overview →'}
                            </button>
                            <button onclick="window.TempoEmergencyFlow.launchFocusZone()" 
                                     class="w-full sm:w-auto px-5 py-3 rounded-xl border border-[#4A6B5D] text-[#4A6B5D] hover:bg-[#EDF4EF] text-xs font-bold transition cursor-pointer">
                                ${isVi ? 'Bắt đầu Focus Zone →' : 'Start Focus Zone →'}
                            </button>
                        </div>
                    </div>
                ` : `
                    <div class="p-5 bg-white border border-[#D5DED7] rounded-[22px] space-y-4 text-center shadow-xs">
                        <div class="space-y-1">
                            <h4 class="font-heading text-base font-bold text-[#202124]">${isVi ? 'Bạn thấy kế hoạch này đã ổn chưa?' : 'Does this plan feel workable?'}</h4>
                            <p class="text-xs text-[#5C665F]">${isVi ? 'Bạn có thể điều chỉnh lại bất cứ lúc nào trong quá trình làm việc.' : 'You can change it again later as you make progress.'}</p>
                        </div>
                        <button id="btn-em-use-plan" onclick="window.TempoEmergencyFlow.savePlan()" 
                                 class="btn-primary w-full py-3.5 rounded-xl font-bold text-sm shadow-xs flex items-center justify-center space-x-2 transition cursor-pointer">
                            <span>${isVi ? 'Sử dụng kế hoạch này →' : 'Use this plan →'}</span>
                        </button>
                    </div>
                `}
            </div>

            <!-- Schedule Task Modal Dialog (if active) -->
            ${renderScheduleModalHTML()}

            <!-- Move Task Modal Dialog (if active) -->
            ${renderMoveTaskModalHTML()}

            <!-- User-Edited Plan Warning Modal (if active) -->
            ${renderPlanEditWarningModalHTML()}

            <!-- Edit Estimate Modal Dialog (if active) -->
            ${renderEditEstimateModalHTML()}

            <!-- Deadline Modal Dialog (if active) -->
            ${renderDeadlineModalHTML()}
        `;
    }

    function renderPlanEditWarningModalHTML() {
        if (!showPlanEditWarningModal) return '';
        const isVi = isViLocale();

        return `
            <div class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
                <div class="bg-white border border-[#D5DED7] rounded-[22px] max-w-md w-full p-6 space-y-4 shadow-2xl">
                    <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                        <h3 class="font-heading text-sm sm:text-base font-extrabold text-[#202124]">
                            ${isVi ? 'Kế hoạch đã được chỉnh sửa' : 'Plan Modified'}
                        </h3>
                        <button onclick="window.TempoEmergencyFlow.cancelPlanEditWarning()" 
                                class="text-gray-400 hover:text-gray-600 text-lg p-1 cursor-pointer"
                                title="${isVi ? 'Đóng' : 'Close'}">✕</button>
                    </div>

                    <p class="text-xs sm:text-sm text-[#5C665F] leading-relaxed">
                        ${isVi ? 'Bạn đã thực hiện các thay đổi trên kế hoạch này. Việc cập nhật lại thời gian có thể làm thay đổi các phần đã sắp xếp.' : "You've made changes to this plan. Updating your availability may require Tempo to rebuild parts of it."}
                    </p>

                    <div class="pt-3 flex flex-col-reverse sm:flex-row items-center justify-end gap-2 border-t border-gray-100">
                        <button onclick="window.TempoEmergencyFlow.cancelPlanEditWarning()"
                                class="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition cursor-pointer">
                            ${isVi ? 'Hủy' : 'Cancel'}
                        </button>
                        <button onclick="window.TempoEmergencyFlow.confirmPlanEditWarningAndGoBack()"
                                class="btn-primary w-full sm:w-auto px-5 py-2.5 rounded-xl font-bold text-xs shadow-xs transition cursor-pointer">
                            ${isVi ? 'Tiếp tục sửa thời gian' : 'Continue editing availability'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

'''

code = code[:idx_pr_start] + new_render_plan_review + code[idx_pr_end:]

# 4. Replace renderMoveTaskModalHTML & renderMoveModalWarningsHTML
idx_move_start = code.find('    function renderMoveTaskModalHTML() {')
idx_move_end = code.find('    function openMoveTaskModal(taskIndex) {')
if idx_move_start == -1 or idx_move_end == -1:
    raise Exception('Could not find renderMoveTaskModalHTML block boundaries')

new_move_task_block = '''    function renderMoveTaskModalHTML() {
        if (!moveModalState || !confirmedPlan || !confirmedPlan.plannedTasks) return '';
        const item = confirmedPlan.plannedTasks[moveModalState.taskIndex];
        if (!item) return '';
        const isVi = isViLocale();

        return `
            <div class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                <div class="bg-white border border-[#D5DED7] rounded-[22px] max-w-md w-full p-6 space-y-5 shadow-2xl">
                    <div class="flex items-center justify-between pb-3 border-b border-gray-100">
                        <h3 class="font-heading text-base font-extrabold text-[#202124]">
                            ${isVi ? 'Di chuyển task' : 'Move Task'}
                        </h3>
                        <button onclick="window.TempoEmergencyFlow.closeMoveTaskModal()" 
                                class="text-gray-400 hover:text-gray-600 text-lg p-1 cursor-pointer">✕</button>
                    </div>

                    <div class="space-y-4 text-xs">
                        <div>
                            <span class="text-[#5C665F] font-medium">Task:</span>
                            <p class="text-sm font-bold text-[#202124] mt-0.5">${escapeHTML(item.task.name)}</p>
                            <p class="text-[#5C665F] text-[11px]">${isVi ? 'Thời lượng dự kiến:' : 'Estimate:'} ~${item.task.durationLabel || (isVi ? 'Chưa rõ' : 'Not sure')} • Deadline: ${item.task.hasDeadline ? formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime, isVi) : (isVi ? 'Chưa có deadline' : 'No fixed deadline')}</p>
                        </div>

                        <div class="space-y-1">
                            <label class="block font-bold text-gray-700 uppercase tracking-wider text-[10px]">${isVi ? 'Chọn ngày chuyển đến:' : 'Select Target Day:'}</label>
                            <select id="em-move-target-day" onchange="window.TempoEmergencyFlow.updateMoveModalPreview(this.value, null)"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-xl bg-white font-semibold text-xs focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] focus:outline-none">
                                ${availabilityDays.map(day => {
                                    const isSelected = day.date === moveModalState.targetDayDate;
                                    const dayNameFormatted = formatDayLabel(day.date, isVi);
                                    const availText = day.isUnavailable 
                                        ? (isVi ? '(Không thể làm việc)' : '(Unavailable)') 
                                        : (isVi ? `(${formatDurationMinutes(calculateDayMinutes(day))} có thể làm việc)` : `(${formatDurationMinutes(calculateDayMinutes(day))} available)`);
                                    return `<option value="${day.date}" ${isSelected ? 'selected' : ''}>${dayNameFormatted} ${availText}</option>`;
                                }).join('')}
                            </select>
                        </div>

                        <div class="space-y-1">
                            <label class="block font-bold text-gray-700 uppercase tracking-wider text-[10px]">${isVi ? 'Vị trí trong ngày:' : 'Position in day:'}</label>
                            <select id="em-move-target-pos" onchange="window.TempoEmergencyFlow.updateMoveModalPreview(null, this.value)"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-xl bg-white font-semibold text-xs focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] focus:outline-none">
                                <option value="first" ${moveModalState.targetPosition === 'first' ? 'selected' : ''}>${isVi ? 'Đầu ngày' : 'Start of this day'}</option>
                                <option value="last" ${moveModalState.targetPosition === 'last' ? 'selected' : ''}>${isVi ? 'Cuối ngày' : 'End of this day'}</option>
                            </select>
                        </div>

                        <!-- Conflict / Feasibility Preview Warnings -->
                        <div id="em-move-modal-warnings" class="space-y-2">
                            ${renderMoveModalWarningsHTML(item, moveModalState.targetDayDate, isVi)}
                        </div>
                    </div>

                    <div class="pt-2 flex items-center justify-end space-x-2 border-t border-gray-100">
                        <button onclick="window.TempoEmergencyFlow.closeMoveTaskModal()"
                                class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition cursor-pointer">
                            ${isVi ? 'Hủy' : 'Cancel'}
                        </button>
                        <button onclick="window.TempoEmergencyFlow.executeMoveTask()"
                                class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs shadow-xs transition cursor-pointer">
                            ${isVi ? 'Giữ lựa chọn & Di chuyển' : 'Keep my choice & Move'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function renderMoveModalWarningsHTML(item, targetDate, isVi = isViLocale()) {
        const targetDay = availabilityDays.find(d => d.date === targetDate);
        if (!targetDay) return '';

        const warnings = [];

        // 1. Availability check
        if (targetDay.isUnavailable) {
            warnings.push(`
                <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-xs">
                    ⚠️ <strong>${isVi ? 'Ngày không thể làm việc:' : 'Day is unavailable:'}</strong> ${isVi ? 'Bạn đã đánh dấu ngày này không thể làm việc. Task sẽ được xếp ở trạng thái linh hoạt/chưa có giờ cố định trừ khi bạn thêm thời gian làm việc.' : 'You marked this day as unavailable. This task will be scheduled as flexible/untimed unless availability is added.'}
                </div>
            `);
        } else {
            const dayAvailableMin = calculateDayMinutes(targetDay);
            const otherTasksDuration = confirmedPlan.plannedTasks
                .filter((p, i) => i !== moveModalState.taskIndex && p.dayDate === targetDate)
                .reduce((sum, p) => sum + (p.task.durationMinutes || 0), 0);
            const remainingMin = dayAvailableMin - otherTasksDuration;
            const taskMin = item.task.durationMinutes || 0;

            if (!item.task.isUnknownDuration && !item.task.isLongTerm && taskMin > remainingMin) {
                warnings.push(`
                    <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-xs">
                        ⚠️ <strong>${isVi ? 'Lưu ý thời gian:' : 'Time limit note:'}</strong> ${isVi ? `Ngày này chỉ còn khoảng ${formatDurationMinutes(Math.max(0, remainingMin))} trống, nhưng task này cần khoảng ${item.task.durationLabel}.` : `This day has ~${formatDurationMinutes(Math.max(0, remainingMin))} remaining, but this task needs ~${item.task.durationLabel}.`}
                    </div>
                `);
            }
        }

        // 2. Deadline check
        if (item.task.hasDeadline && item.task.deadlineDate && targetDate > item.task.deadlineDate) {
            const targetDayLabel = formatDayLabel(targetDate, isVi);
            warnings.push(`
                <div class="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-900 text-xs">
                    ⚠️ <strong>${isVi ? 'Cảnh báo Deadline:' : 'Deadline warning:'}</strong> ${isVi ? `Task này có Deadline vào ${formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime, true)}. Di chuyển sang ${targetDayLabel} sẽ khiến task bị quá Deadline.` : `This task is due on ${formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime, false)}. Moving it to ${targetDay.label} places it after its deadline.`}
                </div>
            `);
        }

        return warnings.join('');
    }

'''

code = code[:idx_move_start] + new_move_task_block + code[idx_move_end:]

# 5. Replace renderEditEstimateModalHTML
idx_est_start = code.find('    function renderEditEstimateModalHTML() {')
idx_est_end = code.find('    function openDeadlineModal(taskId) {')
if idx_est_start == -1 or idx_est_end == -1:
    raise Exception('Could not find renderEditEstimateModalHTML block boundaries')

new_edit_estimate_block = '''    function renderEditEstimateModalHTML() {
        if (!editEstimateModalState) return '';
        const { taskIndex, isNotSure, value, unit } = editEstimateModalState;
        const item = confirmedPlan && confirmedPlan.plannedTasks ? confirmedPlan.plannedTasks[taskIndex] : null;
        if (!item || !item.task) return '';
        const isVi = isViLocale();
        const task = item.task;

        return `
            <div class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in"
                 onclick="if (event.target === this) window.TempoEmergencyFlow.closeEditEstimateModal()">
                <div class="bg-white border border-[#D5DED7] rounded-[22px] max-w-md w-full p-6 space-y-5 shadow-2xl animate-scale-up"
                     role="dialog" aria-modal="true" aria-labelledby="em-edit-estimate-title">
                    <div class="flex items-center justify-between pb-3 border-b border-gray-100">
                        <h3 id="em-edit-estimate-title" class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">
                            ${isVi ? 'Sửa thời lượng dự kiến' : 'Edit time estimate'}
                        </h3>
                        <button onclick="window.TempoEmergencyFlow.closeEditEstimateModal()"
                                class="text-gray-400 hover:text-gray-600 text-lg p-1 transition cursor-pointer"
                                aria-label="Close dialog">✕</button>
                    </div>

                    <div class="space-y-4">
                        <div>
                            <span class="text-[11px] font-bold text-gray-500 uppercase tracking-wider block">Task</span>
                            <p class="text-sm font-extrabold text-[#202124] mt-0.5">${escapeHTML(task.name)}</p>
                        </div>

                        <div class="space-y-2">
                            <label class="block text-xs font-semibold text-gray-700">
                                ${isVi ? 'Bạn nghĩ task này sẽ mất bao lâu?' : 'How long do you think this task will take?'}
                            </label>
                            <div class="flex items-center space-x-2">
                                <input id="em-edit-estimate-value" type="number" min="0.1" step="any"
                                       value="${isNotSure ? '' : (value !== '' && value !== null && value !== undefined ? value : '')}"
                                       ${isNotSure ? 'disabled' : ''}
                                       placeholder="${isVi ? 'VD: 1.5' : 'e.g. 1.5'}"
                                       class="w-28 px-3 py-2 text-xs sm:text-sm border border-gray-300 rounded-xl text-center font-bold text-[#202124] focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] focus:outline-none transition ${isNotSure ? 'opacity-40 bg-stone-100 cursor-not-allowed' : 'bg-white'}">
                                <select id="em-edit-estimate-unit"
                                        ${isNotSure ? 'disabled' : ''}
                                        class="px-3 py-2 text-xs sm:text-sm border border-gray-300 rounded-xl bg-white font-semibold text-[#202124] focus:ring-1 focus:ring-[#8EA28F] focus:border-[#8EA28F] focus:outline-none transition ${isNotSure ? 'opacity-40 bg-stone-100 cursor-not-allowed' : ''}">
                                    <option value="minutes" ${unit === 'minutes' ? 'selected' : ''}>${isVi ? 'phút' : 'minutes'}</option>
                                    <option value="hours" ${unit === 'hours' ? 'selected' : ''}>${isVi ? 'giờ' : 'hours'}</option>
                                    <option value="days" ${unit === 'days' ? 'selected' : ''}>${isVi ? 'ngày' : 'days'}</option>
                                    <option value="weeks" ${unit === 'weeks' ? 'selected' : ''}>${isVi ? 'tuần' : 'weeks'}</option>
                                    <option value="months" ${unit === 'months' ? 'selected' : ''}>${isVi ? 'tháng' : 'months'}</option>
                                </select>
                            </div>
                        </div>

                        <div class="pt-1">
                            <label class="inline-flex items-center space-x-2 cursor-pointer select-none">
                                <input type="checkbox" id="em-edit-estimate-notsure"
                                       ${isNotSure ? 'checked' : ''}
                                       onchange="window.TempoEmergencyFlow.toggleEditEstimateNotSure(this.checked)"
                                       class="w-4 h-4 rounded text-[#4A6B5D] focus:ring-[#8EA28F] border-gray-300">
                                <span class="text-xs sm:text-sm font-medium text-gray-700">${isVi ? 'Tôi chưa chắc chắn' : "I'm not sure yet"}</span>
                            </label>
                        </div>
                    </div>

                    <div class="pt-3 flex items-center justify-end space-x-3 border-t border-gray-100">
                        <button id="em-edit-estimate-cancel-btn"
                                onclick="window.TempoEmergencyFlow.closeEditEstimateModal()"
                                class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs sm:text-sm font-semibold text-gray-700 hover:bg-stone-50 transition cursor-pointer">
                            ${isVi ? 'Hủy' : 'Cancel'}
                        </button>
                        <button id="em-edit-estimate-save-btn"
                                onclick="window.TempoEmergencyFlow.saveEditEstimate()"
                                class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer">
                            ${isVi ? 'Lưu thời lượng' : 'Save estimate'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

'''

code = code[:idx_est_start] + new_edit_estimate_block + code[idx_est_end:]

# Ensure LF line endings
code = code.replace('\r\n', '\n')

with open('emergencyFlow.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(code)

print('Successfully applied working plan updates!')
