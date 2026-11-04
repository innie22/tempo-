# -*- coding: utf-8 -*-
with open('mode.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'init:' in line or 'function init(' in line or 'init()' in line:
            print(f"{idx}: {line.strip()[:100]}")
