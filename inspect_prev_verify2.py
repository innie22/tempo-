with open('scratch/verify_self_check_localization.py', 'r', encoding='utf-8') as f:
    text = f.read()

for l in text.splitlines():
    if 'return' in l.lower():
        print(l)
