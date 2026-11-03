# -*- coding: utf-8 -*-
files = [
    'toolNotes.js',
    'mode.js',
    'index.html',
    'migrations/007_tool_notes.sql',
    'supabase/migrations/007_tool_notes.sql'
]

all_pure_lf = True
for fpath in files:
    with open(fpath, 'rb') as f:
        data = f.read()
    crlf = data.count(b'\r\n')
    lf = data.count(b'\n')
    print(f'{fpath}: CRLF={crlf}, LF={lf}')
    if crlf != 0:
        all_pure_lf = False

assert all_pure_lf, "Some files contain CRLF line endings!"
print("\nAll modified files verified: 100% Pure LF line endings (0 CRLF).")
