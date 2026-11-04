import os

files = [
    'gad7Assessment.js', 'communityPosts.js', 'routine.js', 'support.js',
    'toolNotes.js', 'recoveryNote.js', 'unclearMode.js', 'mode.js',
    'planWorkspace.js', 'planStore.js', 'auth.js', 'weeklyReview.js'
]

for f in files:
    if os.path.exists(f):
        with open(f, 'rb') as fp:
            data = fp.read()
        has_crlf = b'\r\n' in data
        has_lone_lf = (b'\n' in data) and not has_crlf
        print(f"{f}: has_crlf={has_crlf}, length={len(data)}")
    else:
        print(f"{f}: NOT FOUND")
