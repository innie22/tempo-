import re, sys
sys.stdout.reconfigure(encoding='utf-8')

def formatTimeAgo(timeInput, lang):
    isVi = lang == 'vi'
    if not timeInput:
        return 'Gần đây' if isVi else 'Recent'
    
    if isinstance(timeInput, str):
        s = timeInput.strip()
        if re.match(r'^(just now|vừa xong)$', s, re.I):
            return 'Vừa xong' if isVi else 'Just now'
        if re.match(r'^(recent|gần đây)$', s, re.I):
            return 'Gần đây' if isVi else 'Recent'
        m = re.match(r'^(\d+)\s*(hour|hr|minute|min|day|month|year|giờ|phút|ngày|tháng|năm)s?\s*(ago|trước)?$', s, re.I)
        if m:
            count = int(m.group(1))
            unit = m.group(2).lower()
            if unit.startswith('h') or unit.startswith('giờ'):
                s_suffix = '' if count == 1 else 's'
                return f'{count} giờ trước' if isVi else f'{count} hour{s_suffix} ago'
            if unit.startswith('m') or unit.startswith('phút'):
                s_suffix = '' if count == 1 else 's'
                return f'{count} phút trước' if isVi else f'{count} minute{s_suffix} ago'
            if unit.startswith('d') or unit.startswith('ngày'):
                s_suffix = '' if count == 1 else 's'
                return f'{count} ngày trước' if isVi else f'{count} day{s_suffix} ago'
            if unit.startswith('tháng'):
                s_suffix = '' if count == 1 else 's'
                return f'{count} tháng trước' if isVi else f'{count} month{s_suffix} ago'
            if unit.startswith('y') or unit.startswith('năm'):
                s_suffix = '' if count == 1 else 's'
                return f'{count} năm trước' if isVi else f'{count} year{s_suffix} ago'
    return str(timeInput)

print('2 hours ago (vi):', formatTimeAgo('2 hours ago', 'vi'))
print('2 hours ago (en):', formatTimeAgo('2 hours ago', 'en'))
print('5 hours ago (vi):', formatTimeAgo('5 hours ago', 'vi'))
print('5 hours ago (en):', formatTimeAgo('5 hours ago', 'en'))
print('2 giờ trước (en):', formatTimeAgo('2 giờ trước', 'en'))
print('2 giờ trước (vi):', formatTimeAgo('2 giờ trước', 'vi'))
print('1 hour ago (vi):', formatTimeAgo('1 hour ago', 'vi'))
print('1 hour ago (en):', formatTimeAgo('1 hour ago', 'en'))
print('10 minutes ago (vi):', formatTimeAgo('10 minutes ago', 'vi'))
print('10 minutes ago (en):', formatTimeAgo('10 minutes ago', 'en'))
