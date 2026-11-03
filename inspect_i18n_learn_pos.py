import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's inspect where learn: is
for lang in ['vi', 'en']:
    idx = text.find(f'{lang}: {{')
    learn_idx = text.find('learn:', idx)
    print(f"In {lang}, learn: is at {learn_idx}")
    lines = text[learn_idx-300:learn_idx+100].splitlines()
    for l in lines:
        print("  ", l)
    print("---")
