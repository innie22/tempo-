import subprocess, time, json, urllib.request, websocket, tempfile

CDP_PORT = 9462
user_data_dir = tempfile.mkdtemp(prefix='edge_test_css_')

proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={CDP_PORT}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--window-size=1440,1100',
    'http://127.0.0.1:8000/'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    time.sleep(2.5)
    with urllib.request.urlopen(f'http://127.0.0.1:{CDP_PORT}/json') as resp:
        tabs = json.loads(resp.read().decode())
    pages = [t for t in tabs if t.get('type') == 'page' and '127.0.0.1' in t.get('url', '')]
    ws = websocket.create_connection(pages[0]['webSocketDebuggerUrl'])

    mid = [1]
    def send(method, params=None):
        m = mid[0]
        mid[0] += 1
        ws.send(json.dumps({'id': m, 'method': method, 'params': params or {}}))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == m:
                return resp.get('result', {})

    send("Page.enable")
    send("DOM.enable")

    def eval_js(expr):
        res = send('Runtime.evaluate', {
            'expression': expr,
            'returnByValue': True,
            'awaitPromise': True
        })
        return res.get('result', {}).get('value')

    time.sleep(1)
    eval_js("""
        (async function() {
            localStorage.clear();
            const mock = { id: 'u1', email: 'student@tempo.app', role: 'student', user_metadata: { full_name: 'Student' } };
            localStorage.setItem('tempo_mock_account_student@tempo.app', JSON.stringify(mock));
            localStorage.setItem('tempo_local_dev_user', JSON.stringify(mock));
            localStorage.setItem('tempo_active_mode', 'emergency');
            if (window.TempoAuth) await window.TempoAuth.signIn('student@tempo.app', 'password123');
            if (window.TempoMode) window.TempoMode.setMode('emergency');
            if (window.TempoApp) window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1.5)

    test_res = eval_js("""
        (() => {
            const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
            const notes = document.querySelector('[data-tempo-ui="lower-create-notes"]');
            const streakCenter = streak.getBoundingClientRect().left + streak.getBoundingClientRect().width / 2;

            function check(name, applyFn) {
                applyFn();
                const r = notes.getBoundingClientRect();
                const c = r.left + r.width / 2;
                return {
                    name,
                    left: r.left,
                    right: r.right,
                    width: r.width,
                    center: c,
                    diff: Math.abs(c - streakCenter)
                };
            }

            const results = [];

            results.push(check('Current', () => {}));

            results.push(check('alignSelf flex-end + marginRight 84.25px', () => {
                notes.style.alignSelf = 'flex-end';
                notes.style.marginRight = '84.25px';
                notes.style.marginLeft = '';
            }));

            results.push(check('relative left: -44.25px', () => {
                notes.style.alignSelf = '';
                notes.style.marginRight = '';
                notes.style.position = 'relative';
                notes.style.left = '-44.25px';
            }));

            results.push(check('transform: translateX(-44.25px)', () => {
                notes.style.position = '';
                notes.style.left = '';
                notes.style.transform = 'translateX(-44.25px)';
            }));

            results.push(check('marginLeft: -44.25px', () => {
                notes.style.transform = '';
                notes.style.marginLeft = '-44.25px';
                notes.style.marginRight = '';
            }));

            return {
                streakCenter,
                results
            };
        })()
    """)
    print(json.dumps(test_res, indent=2))
finally:
    try:
        proc.kill()
    except:
        pass
