with open('mode.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'renderRmodeHeader' in line:
            print(f'{idx}: {line.strip()[:100]}')
