with open('exploreAssessments.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print("Functions in exploreAssessments.js:")
for m in re.finditer(r'function\s+([a-zA-Z0-9_]+)', text):
    print("  ", m.group(1))

print("\nStorage calls:")
for m in re.finditer(r'(?:localStorage|sessionStorage)\.[a-zA-Z]+\([^\)]+\)', text):
    print("  ", m.group(0))
