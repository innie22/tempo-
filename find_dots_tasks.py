# -*- coding: utf-8 -*-
import sys

with open('planWorkspace.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if '.task' in line and '&&' not in line and '?' not in line:
            print(f"{idx}: {line.strip()[:100]}")
