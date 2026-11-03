import sys, re
sys.stdout.reconfigure(encoding='utf-8')

def format_time_ago(time_input, lang):
    is_vi = (lang == 'vi')
    if not time_input:
        return 'Gần đây' if is_vi else 'Recent'
    s = str(time_input).strip()
    if re.match(r'^(just now|vừa xong)$', s, re.I):
        return 'Vừa xong' if is_vi else 'Just now'
    if re.match(r'^(recent|gần đây)$', s, re.I):
        return 'Gần đây' if is_vi else 'Recent'
    
    m = re.match(r'^(\d+)\s*(hours?|hrs?|h|minutes?|mins?|m|days?|d|months?|years?|giờ|phút|ngày|tháng|năm)\s*(ago|trước)?$', s, re.I)
    if m:
        count = int(m.group(1))
        unit = m.group(2).lower()
        if unit.startswith('h') or unit.startswith('giờ'):
            plural = '' if count == 1 else 's'
            return f'{count} giờ trước' if is_vi else f'{count} hour{plural} ago'
        if unit.startswith('m') or unit.startswith('phút'):
            plural = '' if count == 1 else 's'
            return f'{count} phút trước' if is_vi else f'{count} minute{plural} ago'
        if unit.startswith('d') or unit.startswith('ngày'):
            plural = '' if count == 1 else 's'
            return f'{count} ngày trước' if is_vi else f'{count} day{plural} ago'
        if unit.startswith('month') or unit.startswith('tháng'):
            plural = '' if count == 1 else 's'
            return f'{count} tháng trước' if is_vi else f'{count} month{plural} ago'
        if unit.startswith('y') or unit.startswith('năm'):
            plural = '' if count == 1 else 's'
            return f'{count} năm trước' if is_vi else f'{count} year{plural} ago'
    return s

test_cases = ['2 hours ago', '5 hours ago', 'Just now', '3h ago', '1 hour ago', '15 min ago', '2 giờ trước', 'Vừa xong']
for tc in test_cases:
    print(f'{tc!r:15} -> VI: {format_time_ago(tc, "vi"):15} | EN: {format_time_ago(tc, "en")}')
