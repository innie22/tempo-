with open('mode.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'case1' in line or 'returning' in line.lower() or 'onboarding' in line.lower():
            if 'modal' in line.lower() or 'show' in line.lower() or 'open' in line.lower():
                print(f'{idx}: {line.strip()[:100]}')
