import glob
import re

keys = set()
for fpath in glob.glob('*.js'):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    # find localStorage.getItem / setItem
    for m in re.finditer(r'localStorage\.(?:getItem|setItem)\([\'\"\`]([^\'\"\`]+)[\'\"\`]', content):
        if any(term in m.group(1).lower() for term in ['track', 'selfcheck', 'stress', 'recovery']):
            keys.add((fpath, m.group(1)))

for fpath, k in sorted(keys):
    print(f'{fpath}: {k}')
