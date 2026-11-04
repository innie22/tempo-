import os, glob

search_terms = ['break task', 'breaktask', 'add subtask', 'addsubtask', 'subtask']
files = [f for f in glob.glob('**/*', recursive=True) if os.path.isfile(f) and not f.startswith('.git') and not f.startswith('scratch')]

for f in files:
    if f.endswith(('.js', '.html')):
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                content = fp.read()
                matches = []
                for term in search_terms:
                    count = content.lower().count(term)
                    if count > 0:
                        matches.append(f"{term} ({count})")
                if matches:
                    print(f"{f}: {', '.join(matches)}")
        except Exception as e:
            pass
