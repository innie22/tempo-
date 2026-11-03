import sys, glob

sys.stdout.reconfigure(encoding='utf-8')

for f in glob.glob('*.js'):
    try:
        with open(f, 'r', encoding='utf-8') as fp:
            content = fp.read()
            if 'tool-notes' in content:
                print(f"Found 'tool-notes' in {f}")
    except Exception as e:
        pass
