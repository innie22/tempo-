import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/verify_tips_full_dataset_cdp.py', 'r', encoding='utf-8') as f:
    text = f.read()

print("Length:", len(text))
print(text[:1200])
