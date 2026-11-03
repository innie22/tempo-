with open('planWorkspace.js', 'rb') as f:
    content = f.read().decode('utf-8')

content = content.replace('\r\n', '\n')

# 1. Update getDefaultReferencePlan availabilityDays to only include today
old_def_avail = """            availabilityDays: [
                {
                    date: todayStr,
                    label: formatScheduledDateLabel(todayStr),
                    isUnavailable: false,
                    blocks: [
                        { id: 'b_today_1', start: '14:00', end: '18:00', minutes: 240 },
                        { id: 'b_today_2', start: '19:00', end: '23:00', minutes: 240 }
                    ]
                },
                {
                    date: tomorrowStr,
                    label: formatScheduledDateLabel(tomorrowStr),
                    isUnavailable: false,
                    blocks: [
                        { id: 'b_tom_1', start: '09:00', end: '12:00', minutes: 180 },
                        { id: 'b_tom_2', start: '14:00', end: '17:00', minutes: 180 }
                    ]
                }
            ],"""

new_def_avail = """            availabilityDays: [
                {
                    date: todayStr,
                    label: formatScheduledDateLabel(todayStr),
                    isUnavailable: false,
                    blocks: [
                        { id: 'b_today_1', start: '14:00', end: '18:00', minutes: 240 },
                        { id: 'b_today_2', start: '19:00', end: '23:00', minutes: 240 }
                    ]
                }
            ],"""

if old_def_avail in content:
    content = content.replace(old_def_avail, new_def_avail)
    print("1. Updated getDefaultReferencePlan availabilityDays to today only")

# 2. In getActivePlan fallback:
old_fallback_avail = """                plan.availabilityDays = [
                    {
                        date: todayStr,
                        label: formatScheduledDateLabel(todayStr),
                        isUnavailable: false,
                        blocks: [
                            { id: 'b_today_1', start: '14:00', end: '18:00', minutes: 240 },
                            { id: 'b_today_2', start: '19:00', end: '23:00', minutes: 240 }
                        ]
                    },
                    {
                        date: tomorrowStr,
                        label: formatScheduledDateLabel(tomorrowStr),
                        isUnavailable: false,
                        blocks: [
                            { id: 'b_tom_1', start: '09:00', end: '12:00', minutes: 180 },
                            { id: 'b_tom_2', start: '14:00', end: '17:00', minutes: 180 }
                        ]
                    }
                ];"""

new_fallback_avail = """                plan.availabilityDays = [
                    {
                        date: todayStr,
                        label: formatScheduledDateLabel(todayStr),
                        isUnavailable: false,
                        blocks: [
                            { id: 'b_today_1', start: '14:00', end: '18:00', minutes: 240 },
                            { id: 'b_today_2', start: '19:00', end: '23:00', minutes: 240 }
                        ]
                    }
                ];"""

if old_fallback_avail in content:
    content = content.replace(old_fallback_avail, new_fallback_avail)
    print("2. Updated getActivePlan fallback availabilityDays to today only")

# 3. In saveRescheduleAvailability: handle exact match and seamless merge
old_overlap_check = """        if (day && Array.isArray(day.blocks)) {
            for (const b of day.blocks) {
                if (start < b.end && end > b.start) {
                    showError(isVi
                        ? `Khung giờ này bị trùng lặp với thời gian làm việc đã có (${formatTime12H(b.start)} – ${formatTime12H(b.end)}).`
                        : `This slot overlaps with existing availability (${formatTime12H(b.start)} – ${formatTime12H(b.end)}).`);
                    return;
                }
            }
        }"""

new_overlap_check = """        if (day && Array.isArray(day.blocks)) {
            const exactMatch = day.blocks.find(b => b.start === start && b.end === end);
            if (exactMatch) {
                // Exact slot already exists -> select it directly
                rescheduleSelectedSlot = {
                    id: exactMatch.id,
                    date: date,
                    start: start,
                    end: end
                };
                rescheduleSelectedWindow = date;
                rescheduleShowAddTime = false;
                render();
                return;
            }

            const overlapping = day.blocks.filter(b => start < b.end && end > b.start);
            if (overlapping.length > 0) {
                // Merge new slot with overlapping blocks seamlessly
                let mergedStart = start;
                let mergedEnd = end;
                overlapping.forEach(b => {
                    if (b.start < mergedStart) mergedStart = b.start;
                    if (b.end > mergedEnd) mergedEnd = b.end;
                });
                day.blocks = day.blocks.filter(b => !(start < b.end && end > b.start));
                const mergedId = overlapping[0].id || ('b_' + Date.now());
                day.blocks.push({
                    id: mergedId,
                    start: mergedStart,
                    end: mergedEnd
                });
                day.blocks.sort((a, b) => a.start.localeCompare(b.start));

                await persistPlan(plan);

                rescheduleSelectedSlot = {
                    id: mergedId,
                    date: date,
                    start: mergedStart,
                    end: mergedEnd
                };
                rescheduleSelectedWindow = date;
                rescheduleShowAddTime = false;
                render();
                return;
            }
        }"""

if old_overlap_check in content:
    content = content.replace(old_overlap_check, new_overlap_check)
    print("3. Updated saveRescheduleAvailability to handle exact match and seamless merge")

with open('planWorkspace.js', 'wb') as f:
    f.write(content.encode('utf-8'))
print("planWorkspace.js updated with LF line endings")
