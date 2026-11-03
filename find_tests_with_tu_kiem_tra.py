import glob
import sys

sys.stdout.reconfigure(encoding='utf-8')

for f in glob.glob('scratch/verify_*.py'):
    c = open(f, encoding='utf-8', errors='ignore').read()
    if 'Tự kiểm tra Tempo' in c or 'selfCheckWorkspace.title' in c:
        print(f)
