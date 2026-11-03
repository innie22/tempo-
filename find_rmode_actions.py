with open('mode.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'submitRmodeSelfCheckValue' in line or 'skipRmodeCurrentSelfCheck' in line or 'refreshRmodeSelfCheckCard' in line:
            print(f'{idx}: {line.strip()[:100]}')
