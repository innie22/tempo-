# -*- coding: utf-8 -*-
with open('urmodeFlow.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in [560, 565, 1865, 1870, 2580, 2585]:
    for j in range(max(0, i-3), min(len(lines), i+4)):
        print(f"{j+1}: {lines[j]}", end='')
    print("---")
