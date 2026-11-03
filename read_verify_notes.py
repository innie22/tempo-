import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/verify_notes_scenarios.py', 'r', encoding='utf-8') as f:
    print(f.read()[:600])
