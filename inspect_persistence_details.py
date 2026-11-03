import sys, os, re

sys.stdout.reconfigure(encoding='utf-8')

print("=== CHECKING SUPABASE PERSISTENCE ACROSS CORE RMODE MODULES ===")
for fname in ['planStore.js', 'recoverySelfCheck.js', 'toolNotes.js', 'weeklyReview.js', 'recoverySetup.js', 'auth.js']:
    if not os.path.exists(fname): continue
    with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    sb_calls = re.findall(r'supabaseClient|supabase\.(?:from\([\'"][^\'"]+[\'"]\)|rpc)', text)
    ls_calls = re.findall(r'localStorage\.(?:getItem|setItem)\([\'"][^\'"]+[\'"]', text)
    print(f"\n{fname}:")
    print(f"  Supabase references: {len(sb_calls)} ({set(sb_calls)})")
    print(f"  LocalStorage keys ({len(ls_calls)}): {set(ls_calls[:10])}")
