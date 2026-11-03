import sys
sys.stdout.reconfigure(encoding='utf-8')

for fn in ['i18n.js', 'communityPosts.js', 'index.html', 'mode.js']:
    with open(fn, 'rb') as f:
        data = f.read()
    crlf_count = data.count(b'\r\n')
    lf_count = data.count(b'\n') - crlf_count
    cr_count = data.count(b'\r') - crlf_count
    print(f'{fn:20}: CRLF={crlf_count}, lone LF={lf_count}, lone CR={cr_count}')
