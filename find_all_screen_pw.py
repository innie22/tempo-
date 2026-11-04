# -*- coding: utf-8 -*-
import os

for fname in os.listdir('.'):
    if fname.endswith('.js') or fname.endswith('.html'):
        with open(fname, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f, 1):
                if 'screen-plan-workspace' in line:
                    print(f"{fname}:{idx}: {line.strip()[:100]}")
