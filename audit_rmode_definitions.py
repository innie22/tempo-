import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

print("--- 1. Search for RMODE / RECOVERY definitions in mode.js ---")
for m in re.finditer(r'(function\s+renderRMode|function\s+renderRecovery|initRMode|switchToRMode|enterRMode|requestMode|applyMode|setMode)[\s\S]{0,100}', text):
    print("Match:", m.group(0).split('{')[0].strip())

print("\n--- 2. Search for rmode container / elements ---")
containers = re.findall(r'id=["\']([^"\']*rmode[^"\']*)["\']', text, re.I)
print("RMode IDs in mode.js:", set(containers))

classes = re.findall(r'class=["\']([^"\']*rmode[^"\']*)["\']', text, re.I)
print("RMode Classes in mode.js:", set(classes)[:10])
