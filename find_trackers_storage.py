with open('recoverySelfCheck.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'getActiveTrackers' in line or 'setActiveTrackers' in line or 'active_trackers' in line:
            print(f'{idx}: {line.strip()[:100]}')
