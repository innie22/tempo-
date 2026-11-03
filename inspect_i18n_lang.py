with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('currentLanguage')
if idx != -1:
    print(text[idx-50:idx+200])
