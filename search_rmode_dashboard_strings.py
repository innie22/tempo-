import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

terms = [
    'Quay lại Chế độ phục hồi',
    'Hệ thống tracking của bạn',
    'Thêm tracking',
    'Mức độ căng thẳng trung bình',
    'Số đêm ngủ ngon'
]

files = [f for f in os.listdir('.') if f.endswith('.js') or f.endswith('.html')]

for fpath in files:
    try:
        content = open(fpath, encoding='utf-8').read()
        for term in terms:
            if term in content:
                count = content.count(term)
                print(f'{fpath}: found "{term}" ({count} times)')
    except Exception as e:
        pass
