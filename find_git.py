import os, sys, glob

sys.stdout.reconfigure(encoding='utf-8')

# Find git.exe
possible_git = [
    r"C:\Program Files\Git\cmd\git.exe",
    r"C:\Program Files (x86)\Git\cmd\git.exe",
    r"C:\Users\YEN NHI\AppData\Local\Programs\Git\cmd\git.exe"
]

git_path = None
for p in possible_git:
    if os.path.exists(p):
        git_path = p
        break

if not git_path:
    # Search in LocalAppData
    matches = glob.glob(r"C:\Users\YEN NHI\AppData\**\git.exe", recursive=True)
    if matches:
        git_path = matches[0]

print("git path:", git_path)
if git_path:
    import subprocess
    res = subprocess.run([git_path, 'log', '-n', '8', '--oneline'], capture_output=True, text=True)
    print("Recent commits:")
    print(res.stdout)
