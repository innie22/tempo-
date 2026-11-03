import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/verify_notes_scenarios.py', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()
print('\n'.join(lines[20:70]))
