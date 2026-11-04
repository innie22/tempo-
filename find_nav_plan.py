# -*- coding: utf-8 -*-
with open('i18n.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if "'plan':" in line or '"plan":' in line or 'plan:' in line:
            print(f"{idx}: {line.strip()[:100]}")
