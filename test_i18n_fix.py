import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's inspect community in vi
idx_comm = text.find('community: {')
print(text[idx_comm:idx_comm+200])
