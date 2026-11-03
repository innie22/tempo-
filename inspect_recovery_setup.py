import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('recoverySetup.js', 'r', encoding='utf-8') as f:
    text = f.read()

print("Length of recoverySetup.js:", len(text))
print("First 800 chars of recoverySetup.js:\n", text[:800])

import re
funcs = re.findall(r'function\s+(\w+)\s*\(', text)
print("Functions in recoverySetup.js:", funcs[:20])

# Check exports
return_idx = text.rfind('return {')
print("\nExports in recoverySetup.js:\n", text[return_idx:return_idx+600])
