import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('recoverySelfCheck.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines[:300]):
    if 'function getTrackers' in line or 'function getActiveTrackers' in line or 'function getDailyCheckins' in line or 'localStorage' in line or 'supabase' in line.lower():
        start = max(0, i - 5)
        end = min(len(lines), i + 25)
        print(f"--- Line {i+1} ---")
        print(''.join(lines[start:end]))
