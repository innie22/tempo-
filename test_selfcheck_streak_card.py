import sys
import subprocess
import os

sys.stdout.reconfigure(encoding='utf-8')

files_to_check = ['mode.js', 'recoverySelfCheck.js', 'selfCheckWorkspace.js']

print("--- 1. Checking LF line endings (0 CRLF) ---")
all_lf = True
for f in files_to_check:
    with open(f, 'rb') as fp:
        content = fp.read()
    crlf_count = content.count(b'\r\n')
    lf_count = content.count(b'\n') - crlf_count
    print(f"{f}: CRLF={crlf_count}, LF={lf_count}")
    if crlf_count > 0:
        all_lf = False
        print(f"FAILED: {f} has {crlf_count} CRLF line endings. Converting to LF...")
        content_lf = content.replace(b'\r\n', b'\n')
        with open(f, 'wb') as fp:
            fp.write(content_lf)
        print(f"Converted {f} to LF.")

print("--- 2. Checking JS Syntax with Node ---")
for f in files_to_check:
    res = subprocess.run(['node', '--check', f], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"{f}: Syntax OK")
    else:
        print(f"{f}: Syntax ERROR:\n{res.stderr}")
        sys.exit(1)

print("Pre-checks passed.")
