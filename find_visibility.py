# -*- coding: utf-8 -*-
with open('mode.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'function applyModeVisibility' in line:
            print(f"{idx}: {line.strip()[:100]}")
