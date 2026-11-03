import sys, re
sys.stdout.reconfigure(encoding='utf-8')

for fname in ['urmodeFlow.js', 'emergencyFlow.js', 'mode.js', 'planWorkspace.js']:
    with open(fname, 'r', encoding='utf-8') as f:
        text = f.read()
    matches = re.findall(r'.{0,40}(?:READY TO WORK|Start working on your plan|Break more tasks|showStartWorkingPopup).{0,40}', text, re.IGNORECASE)
    if matches:
        print(f"=== {fname} ===")
        for m in matches[:10]:
            print(m.strip())
