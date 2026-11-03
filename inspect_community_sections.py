# -*- coding: utf-8 -*-
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line_num in [4878, 4901]:
    print(f"\n=================== Line {line_num} ===================")
    start = max(0, line_num - 5)
    end = min(len(lines), line_num + 55)
    for i in range(start, end):
        print(f"{i+1}: {lines[i]}", end='')
