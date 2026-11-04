import os, sys, re

sys.stdout.reconfigure(encoding='utf-8')

for root, dirs, files in os.walk('.'):
    if any(x in root for x in ['.git', 'node_modules', '.gemini', 'scratch']):
        continue
    for file in files:
        if file.endswith('.js') or file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for target in ['openAdjustAvailabilityModal', 'openScheduleModal', 'adjust-availability', 'scheduleModalState']:
                    for m in re.finditer(re.escape(target), content):
                        lno = content.count('\n', 0, m.start()) + 1
                        line = content.split('\n')[lno-1].strip()
                        print(f"{filepath}:{lno} [{target}] -> {line[:120]}")
