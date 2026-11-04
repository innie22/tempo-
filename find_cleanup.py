# -*- coding: utf-8 -*-
with open('planWorkspace.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'function cleanupExpiredAvailability' in line:
            print(f"{idx}: {line.strip()[:100]}")
