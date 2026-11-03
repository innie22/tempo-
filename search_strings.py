import glob, sys
sys.stdout.reconfigure(encoding='utf-8')

for fname in sorted(glob.glob('*.js') + glob.glob('*.html')):
    with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    for s in ['Things you wanted to remember', 'Lời nhắn dành cho tôi', 'Chỉnh sửa lời nhắn', 'My Recovery Notice']:
        if s.lower() in content.lower():
            print(f'Found "{s}" in {fname}')
