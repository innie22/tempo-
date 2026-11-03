with open('selfCheckWorkspace.js', 'r', encoding='utf-8', newline='') as f:
    c = f.read()

assert '\r' not in c, "selfCheckWorkspace.js must be strictly LF"

# 1. Add isViLocale and formatTrackerDisplayName at the beginning of IIFE
target_iife = """(function () {
    'use strict';"""

replace_iife = """(function () {
    'use strict';

    function isViLocale() {
        if (window.TempoI18n && typeof window.TempoI18n.getLanguage === 'function') {
            return window.TempoI18n.getLanguage() === 'vi';
        }
        const stored = localStorage.getItem('tempo_lang');
        if (stored === 'vi' || stored === 'en') return stored === 'vi';
        return (navigator.language || '').toLowerCase().startsWith('vi');
    }

    function formatTrackerDisplayName(name) {
        if (!name || typeof name !== 'string') return '';
        const trimmed = name.trim();
        const lower = trimmed.toLowerCase();
        const isVi = isViLocale();
        if (lower === 'tension' || lower === 'căng thẳng') {
            return isVi ? 'Căng thẳng' : 'Tension';
        }
        if (lower === 'sleep' || lower === 'giấc ngủ' || lower === 'sleep quality') {
            return isVi ? 'Giấc ngủ' : 'Sleep';
        }
        if (lower === 'walk' || lower === 'đi bộ') {
            return isVi ? 'Đi bộ' : 'Walk';
        }
        return trimmed;
    }"""

assert target_iife in c, "target_iife not found"
c = c.replace(target_iife, replace_iife, 1)

# 2. Update getCurrentWeekDays and getWeekDateRangeStr
target_days = """        const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];"""
replace_days = """        const dayLabelsEn = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        const dayLabelsVi = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật'];
        const dayLabels = isViLocale() ? dayLabelsVi : dayLabelsEn;"""

assert target_days in c, "target_days not found"
c = c.replace(target_days, replace_days, 1)

target_range = """    function getWeekDateRangeStr() {
        const days = getCurrentWeekDays();
        const mon = days[0].dateObj;
        const sun = days[6].dateObj;
        const monStr = mon.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        const sunStr = sun.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        return `${monStr} to ${sunStr}`;
    }"""

replace_range = """    function getWeekDateRangeStr() {
        const days = getCurrentWeekDays();
        const mon = days[0].dateObj;
        const sun = days[6].dateObj;
        if (isViLocale()) {
            const pad = n => String(n).padStart(2, '0');
            return `${pad(mon.getDate())}/${pad(mon.getMonth() + 1)} – ${pad(sun.getDate())}/${pad(sun.getMonth() + 1)}`;
        }
        const monStr = mon.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        const sunStr = sun.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        return `${monStr} to ${sunStr}`;
    }"""

assert target_range in c, "target_range not found"
c = c.replace(target_range, replace_range, 1)

# 3. Update calculateTrackerWeeklySummary
target_summary = """        const nameLower = (tracker.name || '').toLowerCase();
        let metricLabel = '';
        let metricValue = '';

        if (tracker.check_method === 'percentage' || nameLower.includes('tension')) {
            const avg = countNumeric > 0 ? `${Math.round(sum / countNumeric)}%` : '0%';
            metricLabel = `Your average ${escapeHTML(nameLower)} level is`;
            metricValue = avg;
        } else if (tracker.check_method === 'yes_no' || nameLower.includes('sleep')) {
            metricLabel = `Nights of Quality Sleep`;
            metricValue = `${goodCount}`;
        } else if (tracker.check_method === 'quantity' || nameLower.includes('walk')) {
            const unit = tracker.quantity_unit || 'min';
            metricLabel = `Total logged this week`;
            metricValue = `${totalQty} ${unit}`;
        } else if (tracker.check_method === 'scale') {
            const avg = countNumeric > 0 ? `${(sum / countNumeric).toFixed(1)}/${tracker.scale_max || 5}` : `0/${tracker.scale_max || 5}`;
            metricLabel = `Average rating`;
            metricValue = avg;
        } else {
            metricLabel = `Your average ${escapeHTML(nameLower)} level is`;
            metricValue = countNumeric > 0 ? `${Math.round(sum / countNumeric)}%` : '0%';
        }"""

replace_summary = """        const nameLower = (tracker.name || '').toLowerCase();
        const isVi = isViLocale();
        let metricLabel = '';
        let metricValue = '';

        if (tracker.check_method === 'percentage' || nameLower.includes('tension') || nameLower.includes('căng thẳng')) {
            const avg = countNumeric > 0 ? `${Math.round(sum / countNumeric)}%` : '0%';
            metricLabel = (nameLower.includes('tension') || nameLower.includes('căng thẳng'))
                ? (isVi ? 'Mức độ căng thẳng trung bình của bạn là' : 'Your average tension level is')
                : (isVi ? `Mức độ ${escapeHTML(formatTrackerDisplayName(tracker.name).toLowerCase())} trung bình của bạn là` : `Your average ${escapeHTML(nameLower)} level is`);
            metricValue = avg;
        } else if (tracker.check_method === 'yes_no' || nameLower.includes('sleep') || nameLower.includes('giấc ngủ')) {
            metricLabel = isVi ? 'Số đêm ngủ ngon' : 'Nights of Quality Sleep';
            metricValue = `${goodCount}`;
        } else if (tracker.check_method === 'quantity' || nameLower.includes('walk') || nameLower.includes('đi bộ')) {
            const unit = tracker.quantity_unit || (isVi ? 'phút' : 'min');
            metricLabel = isVi ? 'Tổng ghi nhận tuần này' : 'Total logged this week';
            metricValue = `${totalQty} ${unit}`;
        } else if (tracker.check_method === 'scale') {
            const avg = countNumeric > 0 ? `${(sum / countNumeric).toFixed(1)}/${tracker.scale_max || 5}` : `0/${tracker.scale_max || 5}`;
            metricLabel = isVi ? 'Đánh giá trung bình' : 'Average rating';
            metricValue = avg;
        } else {
            metricLabel = isVi ? `Mức độ ${escapeHTML(formatTrackerDisplayName(tracker.name).toLowerCase())} trung bình của bạn là` : `Your average ${escapeHTML(nameLower)} level is`;
            metricValue = countNumeric > 0 ? `${Math.round(sum / countNumeric)}%` : '0%';
        }"""

assert target_summary in c, "target_summary not found"
c = c.replace(target_summary, replace_summary, 1)

# 4. Update formatDayObservationValue
target_format_obs = """        if (method === 'yes_no' || method === 'options' || nameLower.includes('sleep')) {
            if (typeof val === 'string' && (val.toLowerCase() === 'good' || val.toLowerCase() === 'yes')) {
                return `<span class="font-semibold text-xs text-[#37352F]">Good</span>`;
            } else if (typeof val === 'string' && (val.toLowerCase() === 'not_good' || val.toLowerCase() === 'no')) {
                return `<span class="font-semibold text-xs text-[#7B7672]">No</span>`;
            }
            return `<span class="font-semibold text-xs text-[#37352F]">${escapeHTML(String(val))}</span>`;
        }

        if (method === 'quantity' || nameLower.includes('walk')) {
            if (val === 'no') {
                return `<span class="font-semibold text-xs text-[#7B7672]">No</span>`;
            }"""

replace_format_obs = """        if (method === 'yes_no' || method === 'options' || nameLower.includes('sleep') || nameLower.includes('giấc ngủ')) {
            const isVi = isViLocale();
            if (typeof val === 'string' && (val.toLowerCase() === 'good' || val.toLowerCase() === 'tốt' || val.toLowerCase() === 'yes' || val.toLowerCase() === 'có')) {
                const label = (nameLower.includes('sleep') || nameLower.includes('giấc ngủ') || val.toLowerCase() === 'good' || val.toLowerCase() === 'tốt')
                    ? (isVi ? 'Tốt' : 'Good')
                    : (isVi ? 'Có' : 'Yes');
                return `<span class="font-semibold text-xs text-[#37352F]">${label}</span>`;
            } else if (typeof val === 'string' && (val.toLowerCase() === 'not_good' || val.toLowerCase() === 'chưa tốt' || val.toLowerCase() === 'no' || val.toLowerCase() === 'không')) {
                const label = (nameLower.includes('sleep') || nameLower.includes('giấc ngủ') || val.toLowerCase() === 'not_good' || val.toLowerCase() === 'chưa tốt')
                    ? (isVi ? 'Chưa tốt' : 'Not good')
                    : (isVi ? 'Không' : 'No');
                return `<span class="font-semibold text-xs text-[#7B7672]">${label}</span>`;
            }
            return `<span class="font-semibold text-xs text-[#37352F]">${escapeHTML(String(val))}</span>`;
        }

        if (method === 'quantity' || nameLower.includes('walk') || nameLower.includes('đi bộ')) {
            const isVi = isViLocale();
            if (val === 'no' || val === 'không') {
                return `<span class="font-semibold text-xs text-[#7B7672]">${isVi ? 'Không' : 'No'}</span>`;
            }"""

assert target_format_obs in c, "target_format_obs not found"
c = c.replace(target_format_obs, replace_format_obs, 1)

# 5. Update renderQuantityCheckinSection
target_qty = """        const dotColor = tracker.type_color || (tracker.category === 'stress_sign' ? '#D48366' : (tracker.category === 'supportive' ? '#166545' : '#1E40AF'));
        const unit = tracker.quantity_unit || 'min';
        const isWalk = (tracker.name || '').toLowerCase().includes('walk');
        const questionText = isWalk ? 'Did you go for a walk today?' : `Did you log your ${escapeHTML((tracker.name || '').toLowerCase())} today?`;
        const radioName = isWalk ? 'selfcheck_walk_today' : `selfcheck_qty_${tracker.id}`;
        const inputId = `selfcheck-qty-input-${tracker.id}`;

        const isYesChecked = choice === 'yes';
        const isNoChecked = choice === 'no';
        const displayVal = draftVal !== undefined && draftVal !== null ? escapeHTML(String(draftVal)) : '';

        return `
            <div class="space-y-1.5" data-quantity-tracker-id="${tracker.id}">
                <div class="flex items-center space-x-2 text-sm font-bold text-[#37352F]">
                    <span class="w-2.5 h-2.5 rounded-full inline-block shrink-0" style="background-color: ${dotColor};"></span>
                    <span>${escapeHTML(tracker.name)}</span>
                </div>
                <p class="text-xs text-[#5B5550]">${questionText}</p>
                <div class="space-y-1.5 text-xs text-[#5B5550]">
                    <div class="flex items-center flex-wrap gap-2">
                        <label class="flex items-center space-x-2 cursor-pointer shrink-0">
                            <input type="radio" 
                                   name="${radioName}" 
                                   value="yes" 
                                   ${isYesChecked ? 'checked' : ''}
                                   onchange="window.TempoSelfCheckWorkspace.setQuantityChoice('${tracker.id}', 'yes')"
                                   class="accent-[#166545]">
                            <span>Yes</span>
                        </label>
                        ${isYesChecked ? `
                            <div class="inline-flex items-center space-x-1.5 pl-0.5">
                                <span class="text-stone-500 font-medium">For</span>
                                <input type="number" 
                                       id="${inputId}"
                                       data-tracker-id="${tracker.id}"
                                       step="any"
                                       min="0"
                                       placeholder="Enter quantity"
                                       value="${displayVal}"
                                       oninput="window.TempoSelfCheckWorkspace.onQuantityInput('${tracker.id}', this.value)"
                                       onchange="window.TempoSelfCheckWorkspace.onQuantityChange('${tracker.id}', this.value)"
                                       class="w-28 sm:w-32 px-2.5 py-1 bg-white border ${errorMsg ? 'border-red-400 focus:border-red-500' : 'border-stone-300 focus:border-[#4A6B5D]'} rounded-lg text-xs font-semibold text-[#202124] placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-[#4A6B5D]">
                                <span class="text-xs font-bold text-[#37352F]">${escapeHTML(unit)}</span>
                            </div>
                        ` : ''}
                    </div>
                    ${isYesChecked && errorMsg ? `<p id="selfcheck-qty-error-${tracker.id}" class="text-[11px] text-red-600 font-medium pl-6">${escapeHTML(errorMsg)}</p>` : ''}
                    <label class="flex items-center space-x-2 cursor-pointer">
                        <input type="radio" 
                               name="${radioName}" 
                               value="no" 
                               ${isNoChecked ? 'checked' : ''}
                               onchange="window.TempoSelfCheckWorkspace.setQuantityChoice('${tracker.id}', 'no')"
                               class="accent-[#166545]">
                        <span>No, i didn't</span>
                    </label>
                </div>
            </div>
        `;"""

replace_qty = """        const isVi = isViLocale();
        const dotColor = tracker.type_color || (tracker.category === 'stress_sign' ? '#D48366' : (tracker.category === 'supportive' ? '#166545' : '#1E40AF'));
        const unit = tracker.quantity_unit || (isVi ? 'phút' : 'min');
        const isWalk = (tracker.name || '').toLowerCase().includes('walk') || (tracker.name || '').toLowerCase().includes('đi bộ');
        const questionText = isWalk 
            ? (isVi ? 'Hôm nay bạn có đi bộ không?' : 'Did you go for a walk today?') 
            : (isVi ? `Hôm nay bạn đã ghi nhận ${escapeHTML(formatTrackerDisplayName(tracker.name).toLowerCase())} chưa?` : `Did you log your ${escapeHTML((tracker.name || '').toLowerCase())} today?`);
        const radioName = isWalk ? 'selfcheck_walk_today' : `selfcheck_qty_${tracker.id}`;
        const inputId = `selfcheck-qty-input-${tracker.id}`;

        const isYesChecked = choice === 'yes';
        const isNoChecked = choice === 'no';
        const displayVal = draftVal !== undefined && draftVal !== null ? escapeHTML(String(draftVal)) : '';

        return `
            <div class="space-y-1.5" data-quantity-tracker-id="${tracker.id}">
                <div class="flex items-center space-x-2 text-sm font-bold text-[#37352F]">
                    <span class="w-2.5 h-2.5 rounded-full inline-block shrink-0" style="background-color: ${dotColor};"></span>
                    <span>${escapeHTML(formatTrackerDisplayName(tracker.name))}</span>
                </div>
                <p class="text-xs text-[#5B5550]">${questionText}</p>
                <div class="space-y-1.5 text-xs text-[#5B5550]">
                    <div class="flex items-center flex-wrap gap-2">
                        <label class="flex items-center space-x-2 cursor-pointer shrink-0">
                            <input type="radio" 
                                   name="${radioName}" 
                                   value="yes" 
                                   ${isYesChecked ? 'checked' : ''}
                                   onchange="window.TempoSelfCheckWorkspace.setQuantityChoice('${tracker.id}', 'yes')"
                                   class="accent-[#166545]">
                            <span>${isVi ? 'Có' : 'Yes'}</span>
                        </label>
                        ${isYesChecked ? `
                            <div class="inline-flex items-center space-x-1.5 pl-0.5">
                                <span class="text-stone-500 font-medium">${isVi ? 'Trong' : 'For'}</span>
                                <input type="number" 
                                       id="${inputId}"
                                       data-tracker-id="${tracker.id}"
                                       step="any"
                                       min="0"
                                       placeholder="${isVi ? 'Nhập số lượng' : 'Enter quantity'}"
                                       value="${displayVal}"
                                       oninput="window.TempoSelfCheckWorkspace.onQuantityInput('${tracker.id}', this.value)"
                                       onchange="window.TempoSelfCheckWorkspace.onQuantityChange('${tracker.id}', this.value)"
                                       class="w-28 sm:w-32 px-2.5 py-1 bg-white border ${errorMsg ? 'border-red-400 focus:border-red-500' : 'border-stone-300 focus:border-[#4A6B5D]'} rounded-lg text-xs font-semibold text-[#202124] placeholder-stone-400 focus:outline-none focus:ring-1 focus:ring-[#4A6B5D]">
                                <span class="text-xs font-bold text-[#37352F]">${escapeHTML(unit)}</span>
                            </div>
                        ` : ''}
                    </div>
                    ${isYesChecked && errorMsg ? `<p id="selfcheck-qty-error-${tracker.id}" class="text-[11px] text-red-600 font-medium pl-6">${escapeHTML(errorMsg)}</p>` : ''}
                    <label class="flex items-center space-x-2 cursor-pointer">
                        <input type="radio" 
                               name="${radioName}" 
                               value="no" 
                               ${isNoChecked ? 'checked' : ''}
                               onchange="window.TempoSelfCheckWorkspace.setQuantityChoice('${tracker.id}', 'no')"
                               class="accent-[#166545]">
                        <span>${isVi ? 'Không' : "No, I didn't"}</span>
                    </label>
                </div>
            </div>
        `;"""

assert target_qty in c, "target_qty not found"
c = c.replace(target_qty, replace_qty, 1)

# 6. Update openWeeklyReport content
target_rep_content = """                    <div class="p-4 rounded-2xl bg-[#EDF7F1] border border-[#CDE9DA] flex items-center justify-between">
                        <div>
                            <span class="text-xs font-bold text-[#166545] uppercase tracking-wider block">CONSISTENCY</span>
                            <h4 class="font-heading text-lg font-extrabold text-[#202124]">${streak} ngày điểm danh liên tiếp</h4>
                        </div>
                        <span class="text-2xl select-none">🌱</span>
                    </div>

                    <div class="space-y-2">
                        <h5 class="text-xs font-bold uppercase tracking-wider text-[#6F6B68]">Tổng kết theo dõi tuần này</h5>
                        <div class="space-y-2">
                            ${summaryItemsHTML || '<p class="text-xs text-stone-500 italic">No active trackers.</p>'}
                        </div>
                    </div>"""

replace_rep_content = """                    <div class="p-4 rounded-2xl bg-[#EDF7F1] border border-[#CDE9DA] flex items-center justify-between">
                        <div>
                            <span class="text-xs font-bold text-[#166545] uppercase tracking-wider block">${isViLocale() ? 'TÍNH NHẤT QUÁN' : 'CONSISTENCY'}</span>
                            <h4 class="font-heading text-lg font-extrabold text-[#202124]">${isViLocale() ? `${streak} ngày điểm danh liên tiếp` : `${streak}-day streak`}</h4>
                        </div>
                        <span class="text-2xl select-none">🌱</span>
                    </div>

                    <div class="space-y-2">
                        <h5 class="text-xs font-bold uppercase tracking-wider text-[#6F6B68]">${isViLocale() ? 'Tổng kết theo dõi tuần này' : 'This week’s tracking summary'}</h5>
                        <div class="space-y-2">
                            ${summaryItemsHTML || `<p class="text-xs text-stone-500 italic">${isViLocale() ? 'Chưa có mục theo dõi nào.' : 'No active trackers.'}</p>`}
                        </div>
                    </div>"""

assert target_rep_content in c, "target_rep_content not found"
c = c.replace(target_rep_content, replace_rep_content, 1)

# 7. Update render() function
target_render = """        // Determine return destination label based on originating source context
        const originMode = (window.TempoMode && typeof window.TempoMode.getOriginatingMode === 'function') 
            ? window.TempoMode.getOriginatingMode() 
            : ((window.TempoMode && typeof window.TempoMode.getSourceContext === 'function') ? window.TempoMode.getSourceContext() : null);
        let returnLabel = 'Return Home';
        if (originMode === 'emergency') {
            returnLabel = 'Return to Urgent Mode';
        } else if (originMode === 'recovery') {
            returnLabel = 'Return to Recovery Mode';
        } else if (originMode === 'unclear') {
            returnLabel = 'Return to Unclear Mode';
        }

        // Master Layout HTML matching reference screenshot
        root.innerHTML = `
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 space-y-6">
                <!-- Top Utility Bar: Return Home & Centered Title -->
                <div class="relative flex items-center justify-between pb-2">
                    <!-- Top Left: ← Return Home -->
                    <div class="shrink-0">
                        <button type="button" 
                                id="btn-self-check-return-home"
                                data-tempo-action="return-home"
                                onclick="window.TempoSelfCheckWorkspace.returnHome()" 
                                class="inline-flex items-center space-x-1.5 text-xs sm:text-sm font-semibold text-[#4A6B5D] hover:text-[#166545] transition cursor-pointer" 
                                title="${returnLabel}">
                            <span class="text-base leading-none">←</span>
                            <span id="selfcheck-return-home-text">${returnLabel}</span>
                        </button>
                    </div>

                    <!-- Centered Title -->
                    <div class="absolute left-1/2 -translate-x-1/2 text-center pointer-events-none">
                        <h1 class="font-heading text-2xl sm:text-3xl md:text-4xl font-extrabold text-[#234E3B] tracking-tight">
                            Tự kiểm tra Tempo
                        </h1>
                    </div>

                    <!-- Spacer for layout symmetry -->
                    <div class="w-24 shrink-0"></div>
                </div>

                <!-- Two-Column Main Content -->
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-10 items-start">
                    <!-- LEFT COLUMN (col-span-5): Summary Card + Action Buttons -->
                    <div class="lg:col-span-5 space-y-4 lg:sticky lg:top-20">
                        <!-- Card: Điểm danh hôm nay -->
                        <div class="bg-[#FEFAF4] rounded-3xl p-6 sm:p-7 shadow-xs border border-white/80 space-y-4">
                            <!-- Category, Title, Streak -->
                            <div class="space-y-1">
                                <span class="text-xs sm:text-sm font-extrabold text-[#4A6B5D] uppercase tracking-wide block">Your daily check-in</span>
                                <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#37352F] tracking-tight leading-snug">Điểm danh hôm nay</h2>
                                <p class="text-xs italic text-[#787570] font-medium">${streak}-day streak</p>
                            </div>

                            <!-- Interactive Trackers -->
                            <div class="space-y-3.5 pt-1">
                                ${activeTrackers.length === 0 ? `
                                    <div class="py-5 text-center space-y-1.5 text-stone-500">
                                        <p class="text-xs font-semibold text-[#5B5550]">Chưa có mục theo dõi nào</p>
                                        <p class="text-[11px] text-[#787570]">Add a tracking item to start recording your daily check-ins.</p>
                                    </div>
                                ` : `
                                    <!-- Tension -->
                                    ${tensionTrk ? `
                                        <div class="space-y-1.5">
                                            <div class="flex items-center space-x-2 text-sm font-bold text-[#37352F]">
                                                <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: ${tensionTrk.type_color || '#D48366'};"></span>
                                                <span>${escapeHTML(tensionTrk.name || 'Tension')}</span>
                                            </div>
                                            <div class="space-y-1">
                                                <input type="range" min="0" max="100" value="${hasTensionAnswered ? tensionVal : 0}"
                                                       class="selfcheck-tension-slider"
                                                       oninput="window.TempoSelfCheckWorkspace.onTensionInput(this.value)"
                                                       onchange="window.TempoSelfCheckWorkspace.onTensionChange(this.value)">
                                                <div class="text-center text-xs font-bold text-[#5B5550]">
                                                    <span id="selfcheck-tension-val">${hasTensionAnswered ? tensionVal + '%' : '0%'}</span>
                                                </div>
                                            </div>
                                        </div>
                                    ` : ''}

                                    <!-- Sleep -->
                                    ${sleepTrk ? `
                                        <div class="space-y-1.5">
                                            <div class="flex items-center space-x-2 text-sm font-bold text-[#37352F]">
                                                <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: ${sleepTrk.type_color || '#166545'};"></span>
                                                <span>${escapeHTML(sleepTrk.name || 'Sleep')}</span>
                                            </div>
                                            <p class="text-xs text-[#5B5550]">How was your sleep last night?</p>
                                            <div class="flex items-center space-x-3 pt-0.5">
                                                <button type="button" 
                                                        onclick="window.TempoSelfCheckWorkspace.setSleepValue('good')"
                                                        class="px-5 py-1.5 rounded-xl text-xs font-semibold border transition cursor-pointer ${sleepVal === 'good' ? 'bg-[#EDF7F1] border-[#166545] text-[#166545] font-bold shadow-2xs' : 'bg-white border-stone-200 text-[#5B5550] hover:bg-stone-50'}">
                                                    Good
                                                </button>
                                                <button type="button" 
                                                        onclick="window.TempoSelfCheckWorkspace.setSleepValue('not_good')"
                                                        class="px-5 py-1.5 rounded-xl text-xs font-semibold border transition cursor-pointer ${sleepVal === 'not_good' ? 'bg-[#FCEEE8] border-[#D48366] text-[#B83D08] font-bold shadow-2xs' : 'bg-white border-stone-200 text-[#5B5550] hover:bg-stone-50'}">
                                                    Not good
                                                </button>
                                            </div>
                                        </div>
                                    ` : ''}

                                    <!-- Quantity Tracker: Walk -->
                                    ${walkTrk ? renderQuantityCheckinSection(walkTrk) : ''}

                                    <!-- Any Custom Trackers -->
                                    ${customTrackersHTML}
                                `}

                                <!-- Create a note for today -->
                                <div class="pt-2">
                                    <button type="button" 
                                            onclick="window.TempoSelfCheckWorkspace.toggleNoteInput()"
                                            class="text-xs font-semibold text-[#D05A3F] hover:underline transition cursor-pointer flex items-center space-x-1">
                                        <span>Create a note for today</span>
                                    </button>
                                    <div id="selfcheck-today-note-box" class="${showNoteInput ? '' : 'hidden'} pt-2 space-y-2">
                                        <textarea id="selfcheck-today-note-textarea" 
                                                  rows="2" 
                                                  placeholder="How are you feeling today?" 
                                                  class="w-full p-2.5 text-xs rounded-xl border border-stone-200 focus:outline-none focus:border-[#4A6B5D] bg-white resize-none">${escapeHTML(todayNote)}</textarea>
                                        <div class="flex justify-end space-x-2">
                                            <button type="button" onclick="window.TempoSelfCheckWorkspace.saveTodayNote()" 
                                                    class="px-3 py-1 rounded-lg text-xs font-bold bg-[#7B9688] text-white hover:bg-[#6D8475] transition cursor-pointer">
                                                Save note
                                            </button>
                                        </div>
                                    </div>
                                </div>

                                <!-- Status line -->
                                <p class="text-xs text-[#5B5550] pt-1">
                                    You checked in on ${answeredTodayCount} of ${activeTrackers.length} things.
                                </p>
                            </div>
                        </div>

                        <!-- Bottom Buttons: My weekly report & My Recovery notice -->
                        <div class="grid grid-cols-2 gap-3 sm:gap-4 pt-1">
                            <!-- My weekly report -->
                            <button type="button" 
                                    onclick="window.TempoSelfCheckWorkspace.openWeeklyReport()"
                                    class="p-4 sm:p-5 rounded-2xl bg-[#E8EFF3] hover:bg-[#DEE7EC] border border-[#D0DDE5] text-left transition cursor-pointer shadow-2xs flex flex-col justify-center space-y-1">
                                <span class="text-sm sm:text-base font-extrabold text-[#202124] block leading-tight">My weekly report</span>
                                <span class="text-[11px] sm:text-xs text-[#6F6B68] font-medium block">${weekDateRangeStr}</span>
                            </button>

                            <!-- My Recovery notice -->
                            <button type="button" 
                                    onclick="window.TempoSelfCheckWorkspace.openRecoveryNotice()"
                                    class="p-4 sm:p-5 rounded-2xl bg-[#7E9685] hover:bg-[#728A79] text-white text-center transition cursor-pointer shadow-xs flex items-center justify-center">
                                <span class="text-sm sm:text-base font-extrabold block leading-tight">My Recovery notice</span>
                            </button>
                        </div>
                    </div>

                    <!-- RIGHT COLUMN (col-span-7): Hệ thống Theo dõi của bạn (Independently Scrollable) -->
                    <div class="lg:col-span-7 flex flex-col space-y-4">
                        <!-- Header: Title + Add Tracking + Clear all -->
                        <div class="flex items-center justify-between gap-3 pb-1">
                            <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#1B4332]">
                                Hệ thống Theo dõi của bạn
                            </h2>
                            <div class="flex items-center space-x-2">
                                <button type="button" 
                                        onclick="window.TempoSelfCheckWorkspace.openAddTracking()"
                                        class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shadow-2xs">
                                    Add Tracking
                                </button>
                                <button type="button" 
                                        onclick="window.TempoSelfCheckWorkspace.promptClearAll()"
                                        class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#C8322B] hover:bg-[#B32B25] text-white transition cursor-pointer shadow-2xs">
                                    Clear all
                                </button>
                            </div>
                        </div>"""

replace_render = """        // Determine return destination label based on originating source context
        const originMode = (window.TempoMode && typeof window.TempoMode.getOriginatingMode === 'function') 
            ? window.TempoMode.getOriginatingMode() 
            : ((window.TempoMode && typeof window.TempoMode.getSourceContext === 'function') ? window.TempoMode.getSourceContext() : null);
        const isVi = isViLocale();
        let returnLabel = isVi ? 'Quay lại trang chủ' : 'Return Home';
        if (originMode === 'emergency') {
            returnLabel = isVi ? 'Quay lại Chế độ khẩn cấp' : 'Return to Urgent Mode';
        } else if (originMode === 'recovery') {
            returnLabel = isVi ? 'Quay lại Chế độ phục hồi' : 'Return to Recovery Mode';
        } else if (originMode === 'unclear') {
            returnLabel = isVi ? 'Quay lại Chế độ mơ hồ' : 'Return to Unclear Mode';
        }
        const returnTitle = isVi ? (originMode === 'emergency' ? '← Quay lại Chế độ khẩn cấp' : `← ${returnLabel}`) : returnLabel;

        // Master Layout HTML matching reference screenshot
        root.innerHTML = `
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 space-y-6">
                <!-- Top Utility Bar: Return Home & Centered Title -->
                <div class="relative flex items-center justify-between pb-2">
                    <!-- Top Left: ← Return Home -->
                    <div class="shrink-0">
                        <button type="button" 
                                id="btn-self-check-return-home"
                                data-tempo-action="return-home"
                                onclick="window.TempoSelfCheckWorkspace.returnHome()" 
                                class="inline-flex items-center space-x-1.5 text-xs sm:text-sm font-semibold text-[#4A6B5D] hover:text-[#166545] transition cursor-pointer" 
                                title="${returnTitle}">
                            <span class="text-base leading-none">←</span>
                            <span id="selfcheck-return-home-text">${returnLabel}</span>
                        </button>
                    </div>

                    <!-- Centered Title -->
                    <div class="absolute left-1/2 -translate-x-1/2 text-center pointer-events-none">
                        <h1 class="font-heading text-2xl sm:text-3xl md:text-4xl font-extrabold text-[#234E3B] tracking-tight">
                            ${isVi ? 'Tự kiểm tra Tempo' : 'Tempo Self-check'}
                        </h1>
                    </div>

                    <!-- Spacer for layout symmetry -->
                    <div class="w-24 shrink-0"></div>
                </div>

                <!-- Two-Column Main Content -->
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-10 items-start">
                    <!-- LEFT COLUMN (col-span-5): Summary Card + Action Buttons -->
                    <div class="lg:col-span-5 space-y-4 lg:sticky lg:top-20">
                        <!-- Card: Điểm danh hôm nay -->
                        <div class="bg-[#FEFAF4] rounded-3xl p-6 sm:p-7 shadow-xs border border-white/80 space-y-4">
                            <!-- Category, Title, Streak -->
                            <div class="space-y-1">
                                <span class="text-xs sm:text-sm font-extrabold text-[#4A6B5D] uppercase tracking-wide block">${isVi ? 'CHECK-IN HẰNG NGÀY' : 'YOUR DAILY CHECK-IN'}</span>
                                <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#37352F] tracking-tight leading-snug">${isVi ? 'Check-in hôm nay' : "Today's Check-in"}</h2>
                                <p class="text-xs italic text-[#787570] font-medium">${isVi ? `Chuỗi ${streak} ngày` : `${streak}-day streak`}</p>
                            </div>

                            <!-- Interactive Trackers -->
                            <div class="space-y-3.5 pt-1">
                                ${activeTrackers.length === 0 ? `
                                    <div class="py-5 text-center space-y-1.5 text-stone-500">
                                        <p class="text-xs font-semibold text-[#5B5550]">${isVi ? 'Chưa có mục theo dõi nào' : 'No tracking items yet'}</p>
                                        <p class="text-[11px] text-[#787570]">${isVi ? 'Thêm mục theo dõi để bắt đầu ghi nhận check-in hằng ngày.' : 'Add a tracking item to start recording your daily check-ins.'}</p>
                                    </div>
                                ` : `
                                    <!-- Tension -->
                                    ${tensionTrk ? `
                                        <div class="space-y-1.5">
                                            <div class="flex items-center space-x-2 text-sm font-bold text-[#37352F]">
                                                <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: ${tensionTrk.type_color || '#D48366'};"></span>
                                                <span>${escapeHTML(formatTrackerDisplayName(tensionTrk.name || 'Tension'))}</span>
                                            </div>
                                            <div class="space-y-1">
                                                <input type="range" min="0" max="100" value="${hasTensionAnswered ? tensionVal : 0}"
                                                       class="selfcheck-tension-slider"
                                                       oninput="window.TempoSelfCheckWorkspace.onTensionInput(this.value)"
                                                       onchange="window.TempoSelfCheckWorkspace.onTensionChange(this.value)">
                                                <div class="text-center text-xs font-bold text-[#5B5550]">
                                                    <span id="selfcheck-tension-val">${hasTensionAnswered ? tensionVal + '%' : '0%'}</span>
                                                </div>
                                            </div>
                                        </div>
                                    ` : ''}

                                    <!-- Sleep -->
                                    ${sleepTrk ? `
                                        <div class="space-y-1.5">
                                            <div class="flex items-center space-x-2 text-sm font-bold text-[#37352F]">
                                                <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: ${sleepTrk.type_color || '#166545'};"></span>
                                                <span>${escapeHTML(formatTrackerDisplayName(sleepTrk.name || 'Sleep'))}</span>
                                            </div>
                                            <p class="text-xs text-[#5B5550]">${isVi ? 'Bạn ngủ thế nào vào tối qua?' : 'How was your sleep last night?'}</p>
                                            <div class="flex items-center space-x-3 pt-0.5">
                                                <button type="button" 
                                                        onclick="window.TempoSelfCheckWorkspace.setSleepValue('good')"
                                                        class="px-5 py-1.5 rounded-xl text-xs font-semibold border transition cursor-pointer ${sleepVal === 'good' ? 'bg-[#EDF7F1] border-[#166545] text-[#166545] font-bold shadow-2xs' : 'bg-white border-stone-200 text-[#5B5550] hover:bg-stone-50'}">
                                                    ${isVi ? 'Tốt' : 'Good'}
                                                </button>
                                                <button type="button" 
                                                        onclick="window.TempoSelfCheckWorkspace.setSleepValue('not_good')"
                                                        class="px-5 py-1.5 rounded-xl text-xs font-semibold border transition cursor-pointer ${sleepVal === 'not_good' ? 'bg-[#FCEEE8] border-[#D48366] text-[#B83D08] font-bold shadow-2xs' : 'bg-white border-stone-200 text-[#5B5550] hover:bg-stone-50'}">
                                                    ${isVi ? 'Chưa tốt' : 'Not good'}
                                                </button>
                                            </div>
                                        </div>
                                    ` : ''}

                                    <!-- Quantity Tracker: Walk -->
                                    ${walkTrk ? renderQuantityCheckinSection(walkTrk) : ''}

                                    <!-- Any Custom Trackers -->
                                    ${customTrackersHTML}
                                `}

                                <!-- Create a note for today -->
                                <div class="pt-2">
                                    <button type="button" 
                                            onclick="window.TempoSelfCheckWorkspace.toggleNoteInput()"
                                            class="text-xs font-semibold text-[#D05A3F] hover:underline transition cursor-pointer flex items-center space-x-1">
                                        <span>${isVi ? 'Tạo ghi chú hôm nay' : 'Create a note for today'}</span>
                                    </button>
                                    <div id="selfcheck-today-note-box" class="${showNoteInput ? '' : 'hidden'} pt-2 space-y-2">
                                        <textarea id="selfcheck-today-note-textarea" 
                                                  rows="2" 
                                                  placeholder="${isVi ? 'Hôm nay bạn cảm thấy thế nào?' : 'How are you feeling today?'}" 
                                                  class="w-full p-2.5 text-xs rounded-xl border border-stone-200 focus:outline-none focus:border-[#4A6B5D] bg-white resize-none">${escapeHTML(todayNote)}</textarea>
                                        <div class="flex justify-end space-x-2">
                                            <button type="button" onclick="window.TempoSelfCheckWorkspace.saveTodayNote()" 
                                                    class="px-3 py-1 rounded-lg text-xs font-bold bg-[#7B9688] text-white hover:bg-[#6D8475] transition cursor-pointer">
                                                ${isVi ? 'Lưu ghi chú' : 'Save note'}
                                            </button>
                                        </div>
                                    </div>
                                </div>

                                <!-- Status line -->
                                <p class="text-xs text-[#5B5550] pt-1">
                                    ${isVi ? `Bạn đã check-in ${answeredTodayCount}/${activeTrackers.length} mục hôm nay.` : `You checked in on ${answeredTodayCount} of ${activeTrackers.length} things.`}
                                </p>
                            </div>
                        </div>

                        <!-- Bottom Buttons: My weekly report & My Recovery notice -->
                        <div class="grid grid-cols-2 gap-3 sm:gap-4 pt-1">
                            <!-- My weekly report -->
                            <button type="button" 
                                    onclick="window.TempoSelfCheckWorkspace.openWeeklyReport()"
                                    class="p-4 sm:p-5 rounded-2xl bg-[#E8EFF3] hover:bg-[#DEE7EC] border border-[#D0DDE5] text-left transition cursor-pointer shadow-2xs flex flex-col justify-center space-y-1">
                                <span class="text-sm sm:text-base font-extrabold text-[#202124] block leading-tight">${isVi ? 'Báo cáo tuần của tôi' : 'My weekly report'}</span>
                                <span class="text-[11px] sm:text-xs text-[#6F6B68] font-medium block">${weekDateRangeStr}</span>
                            </button>

                            <!-- My Recovery notice -->
                            <button type="button" 
                                    onclick="window.TempoSelfCheckWorkspace.openRecoveryNotice()"
                                    class="p-4 sm:p-5 rounded-2xl bg-[#7E9685] hover:bg-[#728A79] text-white text-center transition cursor-pointer shadow-xs flex items-center justify-center">
                                <span class="text-sm sm:text-base font-extrabold block leading-tight">${isVi ? 'Lời nhắn phục hồi' : 'My Recovery notice'}</span>
                            </button>
                        </div>
                    </div>

                    <!-- RIGHT COLUMN (col-span-7): Hệ thống tracking của bạn (Independently Scrollable) -->
                    <div class="lg:col-span-7 flex flex-col space-y-4">
                        <!-- Header: Title + Add Tracking + Clear all -->
                        <div class="flex items-center justify-between gap-3 pb-1">
                            <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#1B4332]">
                                ${isVi ? 'Hệ thống tracking của bạn' : 'Your Tracking System'}
                            </h2>
                            <div class="flex items-center space-x-2">
                                <button type="button" 
                                        onclick="window.TempoSelfCheckWorkspace.openAddTracking()"
                                        class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shadow-2xs">
                                    ${isVi ? 'Thêm tracking' : 'Add Tracking'}
                                </button>
                                <button type="button" 
                                        onclick="window.TempoSelfCheckWorkspace.promptClearAll()"
                                        class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#C8322B] hover:bg-[#B32B25] text-white transition cursor-pointer shadow-2xs">
                                    ${isVi ? 'Xóa tất cả' : 'Clear all'}
                                </button>
                            </div>
                        </div>"""

assert target_render in c, "target_render not found"
c = c.replace(target_render, replace_render, 1)

# 8. Update rightColumnItemsHTML in render()
target_right_empty = """                <div class="p-8 sm:p-10 text-center rounded-3xl border-2 border-dashed border-[#8E9F92]/40 bg-white/40 space-y-3 my-2" data-tempo-ui="selfcheck-empty-state">
                    <h3 class="font-heading text-lg font-bold text-[#1B4332]">Chưa có mục theo dõi nào</h3>
                    <p class="text-xs sm:text-sm text-[#5B5550] max-w-sm mx-auto leading-relaxed">Add a tracking item to start recording your daily check-ins.</p>
                    <div class="pt-2">
                        <button type="button" 
                                onclick="window.TempoSelfCheckWorkspace.openAddTracking()"
                                class="px-4 py-2 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shadow-2xs inline-flex items-center space-x-1.5">
                            <span>+ Add Tracking</span>
                        </button>
                    </div>
                </div>"""

replace_right_empty = """                <div class="p-8 sm:p-10 text-center rounded-3xl border-2 border-dashed border-[#8E9F92]/40 bg-white/40 space-y-3 my-2" data-tempo-ui="selfcheck-empty-state">
                    <h3 class="font-heading text-lg font-bold text-[#1B4332]">${isVi ? 'Chưa có mục theo dõi nào' : 'No tracking items yet'}</h3>
                    <p class="text-xs sm:text-sm text-[#5B5550] max-w-sm mx-auto leading-relaxed">${isVi ? 'Thêm mục theo dõi để bắt đầu ghi nhận check-in hằng ngày.' : 'Add a tracking item to start recording your daily check-ins.'}</p>
                    <div class="pt-2">
                        <button type="button" 
                                onclick="window.TempoSelfCheckWorkspace.openAddTracking()"
                                class="px-4 py-2 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shadow-2xs inline-flex items-center space-x-1.5">
                            <span>+ ${isVi ? 'Thêm tracking' : 'Add Tracking'}</span>
                        </button>
                    </div>
                </div>"""

assert target_right_empty in c, "target_right_empty not found"
c = c.replace(target_right_empty, replace_right_empty, 1)

# 9. Update tracker item rendering in right column
target_card_hdr = """                                <h3 class="font-bold text-base sm:text-lg text-[#37352F] tracking-tight truncate">${escapeHTML(t.name)}</h3>
                                ${alertStatus.triggered ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FFE9DC] text-[#C34D2E] border border-[#FFD2BA] whitespace-nowrap">Alert</span>` : ''}
                            </div>
                            <button type="button" 
                                    onclick="window.TempoSelfCheckWorkspace.openAdjustTracker('${t.id}')"
                                    class="px-3.5 py-1 rounded-xl text-xs font-bold bg-[#8E9F92] hover:bg-[#7D8F81] text-white transition cursor-pointer shadow-2xs shrink-0">
                                Adjust
                            </button>"""

replace_card_hdr = """                                <h3 class="font-bold text-base sm:text-lg text-[#37352F] tracking-tight truncate">${escapeHTML(formatTrackerDisplayName(t.name))}</h3>
                                ${alertStatus.triggered ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FFE9DC] text-[#C34D2E] border border-[#FFD2BA] whitespace-nowrap">${isVi ? 'Cảnh báo' : 'Alert'}</span>` : ''}
                            </div>
                            <button type="button" 
                                    onclick="window.TempoSelfCheckWorkspace.openAdjustTracker('${t.id}')"
                                    class="px-3.5 py-1 rounded-xl text-xs font-bold bg-[#8E9F92] hover:bg-[#7D8F81] text-white transition cursor-pointer shadow-2xs shrink-0">
                                ${isVi ? 'Chỉnh sửa' : 'Adjust'}
                            </button>"""

assert target_card_hdr in c, "target_card_hdr not found"
c = c.replace(target_card_hdr, replace_card_hdr, 1)

target_view_full = """                                <button type="button" 
                                        onclick="window.TempoSelfCheckWorkspace.openFullCheckPlaceholder('${t.id}')"
                                        class="px-3.5 sm:px-4 py-1.5 rounded-full text-xs font-semibold bg-white/90 hover:bg-white border border-[#99A99D] text-[#202124] transition shadow-2xs cursor-pointer whitespace-nowrap">
                                    View my full check
                                </button>"""

replace_view_full = """                                <button type="button" 
                                        onclick="window.TempoSelfCheckWorkspace.openFullCheckPlaceholder('${t.id}')"
                                        class="px-3.5 sm:px-4 py-1.5 rounded-full text-xs font-semibold bg-white/90 hover:bg-white border border-[#99A99D] text-[#202124] transition shadow-2xs cursor-pointer whitespace-nowrap">
                                    ${isVi ? 'Xem full-check' : 'View my full check'}
                                </button>"""

assert target_view_full in c, "target_view_full not found"
c = c.replace(target_view_full, replace_view_full, 1)

# 10. Update clear confirmation modal & weekly report modal in selfCheckWorkspace.js
target_modals = """            <!-- MODAL: Clear All Confirmation -->
            <div id="modal-selfcheck-clear-confirm" class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-4 hidden" role="dialog" aria-modal="true">
                <div class="tempo-card max-w-md w-full p-6 space-y-5 bg-white rounded-3xl shadow-2xl relative border border-[#EAE4DF]">
                    <div class="space-y-2">
                        <h3 class="font-heading text-lg font-bold text-[#202124]">Xóa tất cả mục theo dõi?</h3>
                        <p class="text-xs text-[#6F6B68] leading-relaxed">
                            This will remove active items from your tracking system. Your past check-in history will be preserved safely.
                        </p>
                    </div>
                    <div class="flex items-center justify-end space-x-3 pt-2">
                        <button type="button" onclick="window.TempoSelfCheckWorkspace.closeClearConfirm()" 
                                class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-600 hover:text-stone-900 transition cursor-pointer">
                            Cancel
                        </button>
                        <button type="button" onclick="window.TempoSelfCheckWorkspace.executeClearAll()" 
                                class="px-4 py-2 rounded-xl text-xs font-bold bg-[#C8322B] hover:bg-[#B32B25] text-white transition cursor-pointer shadow-xs">
                            Clear all
                        </button>
                    </div>
                </div>
            </div>

            <!-- MODAL: Weekly Report Popup -->
            <div id="modal-selfcheck-weekly-report" class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-4 hidden" role="dialog" aria-modal="true">
                <div class="tempo-card max-w-xl w-full p-6 sm:p-8 space-y-6 bg-white rounded-3xl shadow-2xl relative border border-[#EAE4DF] max-h-[90vh] overflow-y-auto">
                    <button type="button" onclick="window.TempoSelfCheckWorkspace.closeWeeklyReport()" 
                            class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer" title="Close">✕</button>
                    <div class="space-y-1">
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#4A6B5D]">WEEKLY SUMMARY</span>
                        <h3 class="font-heading text-2xl font-extrabold text-[#202124]">Báo cáo Tuần của tôi</h3>
                        <p id="selfcheck-weekly-report-dates" class="text-xs text-[#6F6B68] font-medium"></p>
                    </div>
                    <div id="selfcheck-weekly-report-content" class="space-y-4"></div>
                    <div class="flex justify-between items-center pt-3 border-t border-stone-100">
                        <button type="button" onclick="if (window.TempoWeeklyReview && typeof window.TempoWeeklyReview.open === 'function') { window.TempoSelfCheckWorkspace.closeWeeklyReport(); window.TempoWeeklyReview.open(); }" 
                                class="text-xs font-bold text-[#166545] hover:underline transition cursor-pointer">
                            Open full weekly reflection →
                        </button>
                        <button type="button" onclick="window.TempoSelfCheckWorkspace.closeWeeklyReport()" 
                                class="px-5 py-2 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shadow-xs">
                            Close
                        </button>
                    </div>
                </div>
            </div>"""

replace_modals = """            <!-- MODAL: Clear All Confirmation -->
            <div id="modal-selfcheck-clear-confirm" class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-4 hidden" role="dialog" aria-modal="true">
                <div class="tempo-card max-w-md w-full p-6 space-y-5 bg-white rounded-3xl shadow-2xl relative border border-[#EAE4DF]">
                    <div class="space-y-2">
                        <h3 class="font-heading text-lg font-bold text-[#202124]">${isVi ? 'Xóa tất cả mục theo dõi?' : 'Clear all tracking items?'}</h3>
                        <p class="text-xs text-[#6F6B68] leading-relaxed">
                            ${isVi ? 'Hành động này sẽ xóa các mục đang hoạt động khỏi hệ thống theo dõi của bạn. Lịch sử check-in trước đây vẫn được lưu an toàn.' : 'This will remove active items from your tracking system. Your past check-in history will be preserved safely.'}
                        </p>
                    </div>
                    <div class="flex items-center justify-end space-x-3 pt-2">
                        <button type="button" onclick="window.TempoSelfCheckWorkspace.closeClearConfirm()" 
                                class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-600 hover:text-stone-900 transition cursor-pointer">
                            ${isVi ? 'Hủy' : 'Cancel'}
                        </button>
                        <button type="button" onclick="window.TempoSelfCheckWorkspace.executeClearAll()" 
                                class="px-4 py-2 rounded-xl text-xs font-bold bg-[#C8322B] hover:bg-[#B32B25] text-white transition cursor-pointer shadow-xs">
                            ${isVi ? 'Xóa tất cả' : 'Clear all'}
                        </button>
                    </div>
                </div>
            </div>

            <!-- MODAL: Weekly Report Popup -->
            <div id="modal-selfcheck-weekly-report" class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-4 hidden" role="dialog" aria-modal="true">
                <div class="tempo-card max-w-xl w-full p-6 sm:p-8 space-y-6 bg-white rounded-3xl shadow-2xl relative border border-[#EAE4DF] max-h-[90vh] overflow-y-auto">
                    <button type="button" onclick="window.TempoSelfCheckWorkspace.closeWeeklyReport()" 
                            class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer" title="${isVi ? 'Đóng' : 'Close'}">✕</button>
                    <div class="space-y-1">
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#4A6B5D]">${isVi ? 'TỔNG KẾT TUẦN' : 'WEEKLY SUMMARY'}</span>
                        <h3 class="font-heading text-2xl font-extrabold text-[#202124]">${isVi ? 'Báo cáo tuần của tôi' : 'My weekly report'}</h3>
                        <p id="selfcheck-weekly-report-dates" class="text-xs text-[#6F6B68] font-medium"></p>
                    </div>
                    <div id="selfcheck-weekly-report-content" class="space-y-4"></div>
                    <div class="flex justify-between items-center pt-3 border-t border-stone-100">
                        <button type="button" onclick="if (window.TempoWeeklyReview && typeof window.TempoWeeklyReview.open === 'function') { window.TempoSelfCheckWorkspace.closeWeeklyReport(); window.TempoWeeklyReview.open(); }" 
                                class="text-xs font-bold text-[#166545] hover:underline transition cursor-pointer">
                            ${isVi ? 'Mở đánh giá tuần đầy đủ →' : 'Open full weekly reflection →'}
                        </button>
                        <button type="button" onclick="window.TempoSelfCheckWorkspace.closeWeeklyReport()" 
                                class="px-5 py-2 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shadow-xs">
                            ${isVi ? 'Đóng' : 'Close'}
                        </button>
                    </div>
                </div>
            </div>"""

assert target_modals in c, "target_modals not found"
c = c.replace(target_modals, replace_modals, 1)

# 11. Add onLanguageChange listener at the end of IIFE
target_export = """    return {
        open,
        render,"""

replace_export = """    if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
        window.TempoI18n.onLanguageChange(() => {
            const screenEl = document.getElementById('screen-stress-check');
            const root = document.getElementById('self-check-workspace-root');
            if (root && screenEl && !screenEl.classList.contains('hidden')) {
                render();
            }
        });
    }

    return {
        open,
        render,"""

assert target_export in c, "target_export not found"
c = c.replace(target_export, replace_export, 1)

assert '\r' not in c, "selfCheckWorkspace.js must retain strictly LF line endings"

with open('selfCheckWorkspace.js', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

print("selfCheckWorkspace.js successfully patched!")
