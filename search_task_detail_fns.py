import sys, glob, re

sys.stdout.reconfigure(encoding='utf-8')

for f in glob.glob('*.js'):
    try:
        with open(f, 'r', encoding='utf-8') as fp:
            content = fp.read()
            matches = re.findall(r'(open[A-Za-z0-9]*Task[A-Za-z0-9]*|show[A-Za-z0-9]*Task[A-Za-z0-9]*|render[A-Za-z0-9]*Task[A-Za-z0-9]*Detail[A-Za-z0-9]*)', content)
            if matches:
                print(f"{f}: {set(matches)}")
    except Exception as e:
        pass
