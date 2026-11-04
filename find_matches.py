import os, glob

files = [f for f in glob.glob('**/*', recursive=True) if os.path.isfile(f) and not f.startswith('.git') and not f.startswith('scratch')]

for f in files:
    if f.endswith(('.js', '.html', '.json')):
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                lines = fp.readlines()
                for i, line in enumerate(lines):
                    if 'execute' in line.lower() and 'task' in line.lower():
                        print(f"{f}:{i+1}: {line.strip()[:140]}")
                    elif 'working plan' in line.lower():
                        print(f"{f}:{i+1} [WP]: {line.strip()[:140]}")
        except Exception as e:
            pass
