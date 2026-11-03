import glob, sys
sys.stdout.reconfigure(encoding='utf-8')

for fname in sorted(glob.glob('*.js')):
    with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f, 1):
            if 'chào mừng bạn quay lại' in line.lower() or 'welcome back' in line.lower():
                print(f'{fname}:{idx}: {line.strip()[:100]}')
