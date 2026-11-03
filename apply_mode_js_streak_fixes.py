import sys

def main():
    with open('mode.js', 'r', encoding='utf-8') as f:
        content = f.read()

    assert '\r' not in content, "mode.js must have LF line endings!"

    # 1. Summary text & buttons in renderLowerSelfCheckStreakCard
    target1 = """        let summaryText = `You checked in on ${answeredCount} of ${totalCount} things.` + (skippedTrackers.length > 0 ? ` (${skippedTrackers.length} skipped)` : '');
        let btn1Text = "View today's checkin";
        let btn1Action = "if (window.TempoMode && typeof window.TempoMode.handleStreakCardCheckin === 'function') { window.TempoMode.handleStreakCardCheckin(); } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openDailyCheckin === 'function') { window.TempoRecoverySelfCheck.openDailyCheckin(false); } else { window.location.hash = '#stress-check'; }";
        let btn2Text = 'Edit tracking system';"""

    repl1 = """        const baseSummary = window.t ? window.t('modes.urgent.checkinSummary', { completed: answeredCount, total: totalCount }, (isViLocale() ? `Bạn đã check ${answeredCount}/${totalCount} mục hôm nay.` : `You checked in on ${answeredCount} of ${totalCount} things.`)) : (isViLocale() ? `Bạn đã check ${answeredCount}/${totalCount} mục hôm nay.` : `You checked in on ${answeredCount} of ${totalCount} things.`);
        const skippedExtra = skippedTrackers.length > 0 ? (isViLocale() ? ` (${skippedTrackers.length} đã bỏ qua)` : ` (${skippedTrackers.length} skipped)`) : '';
        let summaryText = baseSummary + skippedExtra;
        let btn1Text = window.t ? window.t('modes.urgent.viewTodayCheckin', {}, (isViLocale() ? 'Xem check-in hôm nay' : "View today's checkin")) : (isViLocale() ? 'Xem check-in hôm nay' : "View today's checkin");
        let btn1Action = "if (window.TempoMode && typeof window.TempoMode.handleStreakCardCheckin === 'function') { window.TempoMode.handleStreakCardCheckin(); } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openDailyCheckin === 'function') { window.TempoRecoverySelfCheck.openDailyCheckin(false); } else { window.location.hash = '#stress-check'; }";
        let btn2Text = window.t ? window.t('modes.urgent.editTrackingSystem', {}, (isViLocale() ? 'Sửa tracking' : 'Edit tracking system')) : (isViLocale() ? 'Sửa tracking' : 'Edit tracking system');
        const skipBtnText = window.t ? window.t('modes.urgent.skip', {}, (isViLocale() ? 'Bỏ qua' : 'Skip')) : (isViLocale() ? 'Bỏ qua' : 'Skip');
        const saveBtnText = window.t ? window.t('modes.urgent.save', {}, (isViLocale() ? 'Lưu' : 'Save')) : (isViLocale() ? 'Lưu' : 'Save');
        const streakHeadingText = window.t ? window.t('modes.urgent.streakHeading', {}, (isViLocale() ? 'Chuỗi Self-check 🔥' : 'Your Self-check Streak 🔥')) : (isViLocale() ? 'Chuỗi Self-check 🔥' : 'Your Self-check Streak 🔥');"""

    assert target1 in content, "target1 not found"
    content = content.replace(target1, repl1, 1)

    # 2. Completed state summary
    target2 = """                    <div class="flex items-center justify-between text-xs sm:text-[13px] text-[#5B5550] pt-0.5">
                        <span data-tempo-ui="streak-card-summary">You checked in on ${answeredCount} of ${totalCount} things.</span>"""
    repl2 = """                    <div class="flex items-center justify-between text-xs sm:text-[13px] text-[#5B5550] pt-0.5">
                        <span data-tempo-ui="streak-card-summary">${baseSummary}</span>"""
    assert target2 in content, "target2 not found"
    content = content.replace(target2, repl2, 1)

    # 3. Skip button in scale control
    target_skip1 = """                                title="Skip for now"
                                data-tempo-ui="streak-card-skip-btn">
                            Skip
                        </button>"""
    repl_skip1 = """                                title="Skip for now"
                                data-tempo-ui="streak-card-skip-btn">
                            ${skipBtnText}
                        </button>"""
    assert target_skip1 in content, "target_skip1 not found"
    content = content.replace(target_skip1, repl_skip1)

    # 4. Save button in quantity control
    target_save_qty = """                        <button type="button" 
                                onclick="window.TempoMode.confirmUmodeQuantity('${displayTracker.id}')"
                                class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#859B8B] hover:bg-[#758B7B] text-white transition cursor-pointer shrink-0 shadow-2xs">
                            Save
                        </button>"""
    repl_save_qty = """                        <button type="button" 
                                onclick="window.TempoMode.confirmUmodeQuantity('${displayTracker.id}')"
                                class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#859B8B] hover:bg-[#758B7B] text-white transition cursor-pointer shrink-0 shadow-2xs">
                            ${saveBtnText}
                        </button>"""
    assert target_save_qty in content, "target_save_qty not found"
    content = content.replace(target_save_qty, repl_save_qty, 1)

    # 5. Save button in percentage control
    target_save_pct = """                        <button type="button" 
                                id="btn-umode-save-percentage"
                                onclick="window.TempoMode.confirmUmodePercentage('${displayTracker.id}')"
                                class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#859B8B] hover:bg-[#758B7B] text-white shadow-2xs transition cursor-pointer shrink-0">
                            Save
                        </button>"""
    repl_save_pct = """                        <button type="button" 
                                id="btn-umode-save-percentage"
                                onclick="window.TempoMode.confirmUmodePercentage('${displayTracker.id}')"
                                class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#859B8B] hover:bg-[#758B7B] text-white shadow-2xs transition cursor-pointer shrink-0">
                            ${saveBtnText}
                        </button>"""
    assert target_save_pct in content, "target_save_pct not found"
    content = content.replace(target_save_pct, repl_save_pct, 1)

    # 6. Streak Card Heading
    target_head = """                <!-- Header: Heading & Flame Badge -->
                <div class="flex items-center space-x-3">
                    <h3 class="text-xl sm:text-[23px] font-extrabold text-[#375344] tracking-tight leading-tight">
                        Your Self-check Streak
                    </h3>"""
    repl_head = """                <!-- Header: Heading & Flame Badge -->
                <div class="flex items-center space-x-3">
                    <h3 class="text-xl sm:text-[23px] font-extrabold text-[#375344] tracking-tight leading-tight">
                        ${streakHeadingText}
                    </h3>"""
    assert target_head in content, "target_head not found"
    content = content.replace(target_head, repl_head, 1)

    # 7. Urgent Community Heading
    target_comm = """                        <h3 class="font-bold text-base sm:text-lg text-[#55504C] tracking-tight">
                            Từ Cộng đồng Tempo
                        </h3>"""
    repl_comm = """                        <h3 class="font-bold text-base sm:text-lg text-[#55504C] tracking-tight">
                            ${window.t ? window.t('modes.urgent.fromCommunity', {}, (isViLocale() ? 'Cộng đồng Tempo' : 'From the Tempo Community')) : (isViLocale() ? 'Cộng đồng Tempo' : 'From the Tempo Community')}
                        </h3>"""
    assert target_comm in content, "target_comm not found"
    content = content.replace(target_comm, repl_comm, 1)

    # 8. Recovery Community Heading
    target_rec_comm = """                        <h3 class="font-bold text-base sm:text-lg text-[#55504C] tracking-tight">
                            ${isViLocale() ? 'Từ Cộng đồng Tempo' : 'From the Tempo Community'}
                        </h3>"""
    repl_rec_comm = """                        <h3 class="font-bold text-base sm:text-lg text-[#55504C] tracking-tight">
                            ${window.t ? window.t('modes.recovery.fromCommunity', {}, (isViLocale() ? 'Cộng đồng Tempo' : 'From the Tempo Community')) : (isViLocale() ? 'Cộng đồng Tempo' : 'From the Tempo Community')}
                        </h3>"""
    assert target_rec_comm in content, "target_rec_comm not found"
    content = content.replace(target_rec_comm, repl_rec_comm, 1)

    # 9. Recovery Mode Self-check Card Buttons & Text
    target_rmode_skip = """                        <button type="button" 
                                onclick="window.TempoMode.skipRmodeCurrentSelfCheck('${currentTracker.id}')"
                                class="text-xs font-semibold text-[#8C8681] hover:text-[#37352F] hover:bg-stone-200/50 px-2.5 py-1 rounded-lg transition cursor-pointer shrink-0"
                                title="Skip for now">
                            Skip
                        </button>"""
    repl_rmode_skip = """                        <button type="button" 
                                onclick="window.TempoMode.skipRmodeCurrentSelfCheck('${currentTracker.id}')"
                                class="text-xs font-semibold text-[#8C8681] hover:text-[#37352F] hover:bg-stone-200/50 px-2.5 py-1 rounded-lg transition cursor-pointer shrink-0"
                                title="Skip for now">
                            ${window.t ? window.t('modes.recovery.skip', {}, (isViLocale() ? 'Bỏ qua' : 'Skip')) : (isViLocale() ? 'Bỏ qua' : 'Skip')}
                        </button>"""
    assert target_rmode_skip in content, "target_rmode_skip not found"
    content = content.replace(target_rmode_skip, repl_rmode_skip, 1)

    target_rmode_save1 = """                            <button type="button" 
                                    onclick="window.TempoMode.submitRmodeSelfCheckValue('${currentTracker.id}', parseInt(document.getElementById('rmode-selfcheck-range').value, 10))"
                                    class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shrink-0 shadow-2xs">
                                Save
                            </button>"""
    repl_rmode_save1 = """                            <button type="button" 
                                    onclick="window.TempoMode.submitRmodeSelfCheckValue('${currentTracker.id}', parseInt(document.getElementById('rmode-selfcheck-range').value, 10))"
                                    class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shrink-0 shadow-2xs">
                                ${window.t ? window.t('modes.recovery.save', {}, (isViLocale() ? 'Lưu' : 'Save')) : (isViLocale() ? 'Lưu' : 'Save')}
                            </button>"""
    assert target_rmode_save1 in content, "target_rmode_save1 not found"
    content = content.replace(target_rmode_save1, repl_rmode_save1, 1)

    target_rmode_save2 = """                            <button type="button" 
                                    onclick="window.TempoMode.submitRmodeQuantityValue('${currentTracker.id}')"
                                    class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shrink-0 shadow-2xs">
                                Save
                            </button>"""
    repl_rmode_save2 = """                            <button type="button" 
                                    onclick="window.TempoMode.submitRmodeQuantityValue('${currentTracker.id}')"
                                    class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shrink-0 shadow-2xs">
                                ${window.t ? window.t('modes.recovery.save', {}, (isViLocale() ? 'Lưu' : 'Save')) : (isViLocale() ? 'Lưu' : 'Save')}
                            </button>"""
    assert target_rmode_save2 in content, "target_rmode_save2 not found"
    content = content.replace(target_rmode_save2, repl_rmode_save2, 1)

    target_rmode_sum1 = """                    <!-- Summary Line (without progress bar) -->
                    <div class="pt-1 flex items-center justify-between text-xs text-[#5B5550]">
                        <span>You checked in on ${answeredCount} of ${totalCount} things.</span>"""
    repl_rmode_sum1 = """                    <!-- Summary Line (without progress bar) -->
                    <div class="pt-1 flex items-center justify-between text-xs text-[#5B5550]">
                        <span>${window.t ? window.t('modes.recovery.checkinSummary', { completed: answeredCount, total: totalCount }, (isViLocale() ? `Bạn đã check ${answeredCount}/${totalCount} mục hôm nay.` : `You checked in on ${answeredCount} of ${totalCount} things.`)) : (isViLocale() ? `Bạn đã check ${answeredCount}/${totalCount} mục hôm nay.` : `You checked in on ${answeredCount} of ${totalCount} things.`)}</span>"""
    assert target_rmode_sum1 in content, "target_rmode_sum1 not found"
    content = content.replace(target_rmode_sum1, repl_rmode_sum1, 1)

    target_rmode_sum2 = """                    <!-- Summary Line (without progress bar) -->
                    <div class="pt-0.5 flex items-center justify-between text-xs text-[#5B5550]">
                        <span>You checked in on ${answeredCount} of ${totalCount} things.</span>"""
    repl_rmode_sum2 = """                    <!-- Summary Line (without progress bar) -->
                    <div class="pt-0.5 flex items-center justify-between text-xs text-[#5B5550]">
                        <span>${window.t ? window.t('modes.recovery.checkinSummary', { completed: answeredCount, total: totalCount }, (isViLocale() ? `Bạn đã check ${answeredCount}/${totalCount} mục hôm nay.` : `You checked in on ${answeredCount} of ${totalCount} things.`)) : (isViLocale() ? `Bạn đã check ${answeredCount}/${totalCount} mục hôm nay.` : `You checked in on ${answeredCount} of ${totalCount} things.`)}</span>"""
    assert target_rmode_sum2 in content, "target_rmode_sum2 not found"
    content = content.replace(target_rmode_sum2, repl_rmode_sum2, 1)

    target_rmode_btns = """                    <button type="button" 
                            onclick="window.TempoMode.handleSelfCheckAction('view')"
                            class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-[#7B9688] hover:bg-[#6D8475] text-white shadow-xs transition cursor-pointer">
                        View today's checkin
                    </button>
                    <button type="button" 
                            onclick="if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('open', { sourceContext: 'recovery' }); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; }"
                            class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-white border border-[#7B9688] text-[#4A6B5D] hover:bg-[#F4F7F5] shadow-xs transition cursor-pointer">
                        Edit tracking system
                    </button>"""
    repl_rmode_btns = """                    <button type="button" 
                            onclick="window.TempoMode.handleSelfCheckAction('view')"
                            class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-[#7B9688] hover:bg-[#6D8475] text-white shadow-xs transition cursor-pointer">
                        ${window.t ? window.t('modes.recovery.viewTodayCheckin', {}, (isViLocale() ? 'Xem check-in hôm nay' : "View today's checkin")) : (isViLocale() ? 'Xem check-in hôm nay' : "View today's checkin")}
                    </button>
                    <button type="button" 
                            onclick="if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('open', { sourceContext: 'recovery' }); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; }"
                            class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-white border border-[#7B9688] text-[#4A6B5D] hover:bg-[#F4F7F5] shadow-xs transition cursor-pointer">
                        ${window.t ? window.t('modes.recovery.editTrackingSystem', {}, (isViLocale() ? 'Sửa tracking' : 'Edit tracking system')) : (isViLocale() ? 'Sửa tracking' : 'Edit tracking system')}
                    </button>"""
    assert target_rmode_btns in content, "target_rmode_btns not found"
    content = content.replace(target_rmode_btns, repl_rmode_btns, 1)

    # 10. Post timeAgo in mode.js
    target_post_time = """<span class="text-xs text-[#8E8A85]">${escapeHtml(post.timeAgo || 'Recent')}</span>"""
    repl_post_time = """<span class="text-xs text-[#8E8A85]">${escapeHtml((window.TempoI18n && typeof window.TempoI18n.formatTimeAgo === 'function') ? window.TempoI18n.formatTimeAgo(post.timeAgo || 'Recent') : (post.timeAgo || 'Recent'))}</span>"""
    if target_post_time in content:
        content = content.replace(target_post_time, repl_post_time)

    assert '\r' not in content, "CRLF found in content before writing mode.js"

    with open('mode.js', 'wb') as f:
        f.write(content.encode('utf-8'))
    print('Successfully updated mode.js with LF line endings!')

if __name__ == '__main__':
    main()
