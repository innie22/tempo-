import sys
sys.stdout.reconfigure(encoding='utf-8')

for fname in ['selfCheckWorkspace.js', 'recoverySelfCheck.js']:
    print(f"=== {fname} ===")
    with open(fname, 'r', encoding='utf-8') as f:
        text = f.read()
    # find window.Tempo... export
    idx = text.rfind('window.Tempo')
    if idx != -1:
        print(text[idx:idx+800])
    else:
        print("no window.Tempo export found")
