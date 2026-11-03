import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Grab the whole Rmode rendering pipeline
funcs = [
    'renderRmodeHome',
    'renderRmodeHeader',
    'renderSelfCheckCard',
    'renderRecoverySupportRowHTML',
    'renderQuickReliefCardHTML',
    'renderFocusNowCardHTML',
    'renderRecoveryNoteCard',
    'renderEmodeCreateNotesCard',
    'renderRecentlyCard',
    'renderRecoveryWorkingPlanSection',
    'renderRecoveryCommunityCard',
    'renderRmodeTaskDetailModalHTML'
]

combined_html = ""
for fn in funcs:
    idx = text.find(f'function {fn}(')
    if idx != -1:
        # take up to next function or 500 lines
        block = text[idx:idx+15000]
        combined_html += block + "\n"

# Extract all onclick="..."
onclicks = re.findall(r'onclick="([^"]+)"', combined_html)
print(f"Total onclick handlers in Rmode UI: {len(onclicks)}")

unique_handlers = set()
for oc in onclicks:
    # clean up code to get function call names
    matches = re.findall(r'(?:window\.)?([A-Za-z0-9_$]+(?:\.[A-Za-z0-9_$]+)+)\s*\(', oc)
    for m in matches:
        unique_handlers.add(m)

print("\n--- Handlers called from Rmode UI ---")
for h in sorted(unique_handlers):
    print(" ", h)
