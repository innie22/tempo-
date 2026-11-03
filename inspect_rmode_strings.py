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

files = ['i18n.js', 'selfCheckWorkspace.js', 'mode.js', 'recoverySetup.js']

for fpath in files:
    content = open(fpath, encoding='utf-8').read()
    lines = content.splitlines()
    for idx, line in enumerate(lines):
        for term in terms:
            if term in line:
                print(f"{fpath}:{idx+1}: {line.strip()}")
