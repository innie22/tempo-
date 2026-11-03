with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'let\s+current[A-Za-z0-9_]*\s*=\s*[^;\n]+|const\s+DEFAULT[A-Za-z0-9_]*\s*=\s*[^;\n]+', text)
print(matches)
