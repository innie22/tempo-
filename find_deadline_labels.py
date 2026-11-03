import sys, re

sys.stdout.reconfigure(encoding='utf-8')

files = ['emergencyFlow.js', 'mode.js', 'planWorkspace.js', 'urmodeFlow.js', 'focusZone.js', 'i18n.js']

for fname in files:
    with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f, 1):
            if re.search(r'Due[:\s]|Hạn chót|formatDeadline|formatHumanDeadline|formatPlanDateHeader|deadlineDate', line, re.IGNORECASE):
                # filter out pure logic / assignments if not UI template
                if any(k in line for k in ['span', 'div', 'p', 'Due', 'Hạn', 'Deadline', 'duePrefix', 'dueDate']):
                    print(f"{fname}:{idx}: {line.strip()[:140]}")
