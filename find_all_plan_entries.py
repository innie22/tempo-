# -*- coding: utf-8 -*-
import sys

with open('mode.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'plan-workspace' in line or 'openPlanWorkspace' in line:
            print(f"mode.js:{idx}: {line.strip()[:100]}")

with open('urmodeFlow.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'plan-workspace' in line or 'openPlanWorkspace' in line:
            print(f"urmodeFlow.js:{idx}: {line.strip()[:100]}")

with open('emergencyFlow.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'plan-workspace' in line or 'openPlanWorkspace' in line:
            print(f"emergencyFlow.js:{idx}: {line.strip()[:100]}")
