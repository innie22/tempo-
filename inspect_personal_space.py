import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('personalSpace.js', 'r', encoding='utf-8') as f:
    text = f.read()

print("Length of personalSpace.js:", len(text))
print("First 1000 chars of personalSpace.js:\n", text[:1000])
