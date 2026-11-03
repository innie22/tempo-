import sys, glob

sys.stdout.reconfigure(encoding='utf-8')

targets = [
    "Return Home", "Add availability", "Adjust Plan", "Delete my plan",
    "Break down task", "Focus now", "Edit deadline", "Clear this task",
    "planWorkspace", "screen-plan"
]

for f in glob.glob('*.js') + glob.glob('*.html'):
    try:
        with open(f, 'r', encoding='utf-8') as fp:
            content = fp.read()
            found = [t for t in targets if t.lower() in content.lower()]
            if found:
                print(f"{f}: found {found}")
    except Exception as e:
        pass
