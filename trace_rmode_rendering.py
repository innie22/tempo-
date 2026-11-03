import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's find functions starting with renderRecovery or renderRmode
functions = re.findall(r'function\s+(renderRecovery\w+|renderRMode\w*)\s*\(', text)
print("Recovery/Rmode render functions in mode.js:", set(functions))

# Let's search for where applyModeVisibility(MODES.RECOVERY) is called and what happens inside
match = re.search(r'function\s+renderRecoveryHome\w*|function\s+renderRmodeHome\w*|renderActiveModeHome', text)
for m in re.finditer(r'applyModeVisibility\(MODES\.RECOVERY\)', text):
    start = max(0, m.start() - 200)
    end = min(len(text), m.end() + 800)
    print("--- applyModeVisibility(MODES.RECOVERY) context ---")
    print(text[start:end])
