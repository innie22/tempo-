import os, sys, re

sys.stdout.reconfigure(encoding='utf-8')

files = ['planWorkspace.js', 'mode.js', 'app.js', 'emergencyFlow.js', 'urmodeFlow.js']

for fname in files:
    if not os.path.exists(fname): continue
    with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    print(f"\n=================== {fname} ===================")
    for m in re.finditer(r'addEventListener\s*\(\s*[\'"]click[\'"]', content):
        lno = content.count('\n', 0, m.start()) + 1
        print(f"Click listener at L{lno}: {content.splitlines()[lno-1].strip()[:100]}")
