import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('communityPosts.js', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

for i in range(1100, 1145):
    print(f"{i+1}: {lines[i]}", end='')
