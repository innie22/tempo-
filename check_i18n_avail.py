import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print("i18n search for addAvailableTime:")
matches = re.findall(r'.{0,50}(?:addAvailableTime|addTimeWindow|editWorkingHours).{0,50}', text, re.I)
for m in matches:
    print(m.strip())
