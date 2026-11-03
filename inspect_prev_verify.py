with open('scratch/verify_self_check_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
for m in re.finditer(r'.{0,40}return.{0,40}', text, re.IGNORECASE):
    print(m.group().strip())
