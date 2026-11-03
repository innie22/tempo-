import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('selfCheckWorkspace.js', encoding='utf-8') as f:
    lines = f.readlines()

search_words = [
    'returnRecovery',
    'Quay lại Chế độ phục hồi',
    'Return to Recovery Mode',
    'yourTrackingSystem',
    'Hệ thống tracking của bạn',
    'Your Tracking System',
    'addTracking',
    'Thêm tracking',
    'Add Tracking',
    'Add tracking',
    'avgTensionLevel',
    'Mức độ căng thẳng',
    'căng thẳng trung bình',
    'average tension',
    'nightsQualitySleep',
    'Số đêm ngủ ngon',
    'giấc ngủ tốt',
    'Quality Sleep'
]

for idx, line in enumerate(lines):
    for w in search_words:
        if w in line:
            print(f"Line {idx+1}: {line.strip()[:140]}")
            break
