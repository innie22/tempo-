import re

files = ['index.html', 'app.js', 'mode.js', 'urmodeFlow.js', 'planWorkspace.js']
for f in files:
    try:
        with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
            for i, line in enumerate(fp):
                if re.search(r'planLink|nav-link-plan|nav-plan|data-nav=["\']plan|navigateToPlan|plan-workspace|#plan', line, re.I):
                    print(f"{f}:{i+1}: {line.strip()[:120]}")
    except Exception as e:
        print(f"Error reading {f}: {e}")
