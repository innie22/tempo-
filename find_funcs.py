# -*- coding: utf-8 -*-
with open('planWorkspace.js', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'function isTaskOverdue' in line or 'function isTaskMissedSchedule' in line or 'function isMissedSchedulePromptDismissed' in line:
            print(f"{idx}: {line.strip()[:100]}")
