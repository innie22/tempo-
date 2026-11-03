import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/rmode_comm_dump.js', 'r', encoding='utf-8') as f:
    print(f.read())
