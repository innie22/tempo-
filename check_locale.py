import glob, sys
sys.stdout.reconfigure(encoding='utf-8')

for fname in ['i18n.js', 'recoveryNote.js', 'recoverySetup.js', 'mode.js', 'selfCheckWorkspace.js']:
    with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    print(f'{fname}: "isViLocale" in file? {"isViLocale" in content}')
    for kw in ['setLocale', 'localeChanged', 'languageChanged', 'tempo:locale']:
        if kw in content:
            print(f'  contains {kw}')
