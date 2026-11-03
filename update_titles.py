with open('toolNotes.js', 'rb') as f:
    raw = f.read()

assert b'\r\n' not in raw, 'toolNotes.js must be LF'
content = raw.decode('utf-8')

old_day_card = '''                                    <div class="flex items-center justify-between gap-2">
                                        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#F9E8E2] text-[#B87561] shrink-0 uppercase tracking-wider">
                                            Day Note
                                        </span>
                                        ${timeStr ? `<span class="text-[11px] text-[#8C827A] font-medium">${escapeHTML(timeStr)}</span>` : ''}
                                    </div>
                                    <p class="text-xs sm:text-[13px] text-[#4A4540] font-medium leading-relaxed line-clamp-2 break-words group-hover:text-[#202124] transition-colors">'''

new_day_card = '''                                    <div class="flex items-center justify-between gap-2">
                                        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#F9E8E2] text-[#B87561] shrink-0 uppercase tracking-wider">
                                            Day Note
                                        </span>
                                        ${timeStr ? `<span class="text-[11px] text-[#8C827A] font-medium">${escapeHTML(timeStr)}</span>` : ''}
                                    </div>
                                    ${n.title ? `<h5 class="text-xs sm:text-sm font-bold text-[#202124] leading-snug break-words">${escapeHTML(n.title)}</h5>` : ''}
                                    <p class="text-xs sm:text-[13px] text-[#4A4540] font-medium leading-relaxed line-clamp-2 break-words group-hover:text-[#202124] transition-colors">'''

assert old_day_card in content, 'old_day_card not found'
content = content.replace(old_day_card, new_day_card, 1)

old_task_card = '''                        ${timeStr ? `<span class="text-[11px] text-[#8C827A] font-medium shrink-0">${escapeHTML(timeStr)}</span>` : ''}
                    </div>
                    <p class="text-xs sm:text-[13px] text-[#4A4540] font-medium leading-relaxed line-clamp-2 break-words group-hover:text-[#202124] transition-colors">'''

new_task_card = '''                        ${timeStr ? `<span class="text-[11px] text-[#8C827A] font-medium shrink-0">${escapeHTML(timeStr)}</span>` : ''}
                    </div>
                    ${n.title ? `<h5 class="text-xs sm:text-sm font-bold text-[#202124] leading-snug break-words">${escapeHTML(n.title)}</h5>` : ''}
                    <p class="text-xs sm:text-[13px] text-[#4A4540] font-medium leading-relaxed line-clamp-2 break-words group-hover:text-[#202124] transition-colors">'''

assert old_task_card in content, 'old_task_card not found'
content = content.replace(old_task_card, new_task_card, 1)

new_raw = content.encode('utf-8')
assert b'\r\n' not in new_raw, 'toolNotes.js must remain LF'

with open('toolNotes.js', 'wb') as f:
    f.write(new_raw)

print('Updated note cards with title display!')
