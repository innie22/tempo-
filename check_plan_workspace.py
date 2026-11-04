with open('planWorkspace.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'execute my task|openquicktaskmodal', text, re.I)]
print("Matches in planWorkspace.js:", len(matches))
