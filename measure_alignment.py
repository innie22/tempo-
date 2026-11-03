# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys, os

sys.stdout.reconfigure(encoding='utf-8')

CDP_PORT = 9550
user_data_dir = tempfile.mkdtemp(prefix='edge_measure_align_')

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
    ws_url = (pages[0] if pages else tabs[0])['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)

    msg_id = [1]
    def send(method, params=None):
        mid = msg_id[0]
        msg_id[0] += 1
        ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == mid:
                return resp.get('result', {})

    send('Page.enable')
    send('DOM.enable')

    def eval_js(expr):
        res = send('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        if 'exceptionDetails' in res.get('result', {}):
            raise Exception(f"JS Exception: {res['result']['exceptionDetails']}")
        return res.get('result', {}).get('value')

    for _ in range(30):
        val = eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'")
        if val:
            break
        time.sleep(0.5)

    eval_js("""
        (async function() {
            const email = 'alex.chen@university.edu';
            const mock = {
                id: 'mock-user-alex',
                email: email,
                password: 'password123',
                profile: { id: 'mock-user-alex', full_name: 'Alex Chen', display_name: 'Alex Chen', role: 'student' }
            };
            localStorage.setItem('tempo_mock_account_' + email, JSON.stringify(mock));
            if (window.TempoAuth) {
                await window.TempoAuth.signIn(email, 'password123');
            }
            
            const uid = 'mock-user-alex';
            localStorage.setItem('tempo_active_mode', 'recovery');
            localStorage.setItem('tempo_originating_mode', 'recovery');
            
            if (window.TempoMode) {
                window.TempoMode.transitionContext('recovery', { skipSetupCheck: true });
                window.TempoMode.renderRmodeHome();
            }
        })()
    """)
    time.sleep(1.0)

    res = eval_js("""
        (function() {
            function getBox(el) {
                if (!el) return null;
                const r = el.getBoundingClientRect();
                const cs = window.getComputedStyle(el);
                return {
                    top: r.top,
                    bottom: r.bottom,
                    left: r.left,
                    right: r.right,
                    width: r.width,
                    height: r.height,
                    marginTop: cs.marginTop,
                    marginBottom: cs.marginBottom,
                    paddingTop: cs.paddingTop,
                    paddingBottom: cs.paddingBottom
                };
            }

            const selfCheck = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            const recently = document.querySelector('[data-tempo-ui="recovery-recently"]');
            const createNotes = document.querySelector('.recovery-right-col [data-tempo-ui="urmode-create-notes"]');
            const greeting = document.querySelector('.recovery-greeting');
            const header = document.querySelector('.recovery-mode-header');
            const leftCol = document.querySelector('.recovery-left-col');
            const rightCol = document.querySelector('.recovery-right-col');

            const scBox = getBox(selfCheck);
            const rcBox = getBox(recently);

            return {
                leftCol: getBox(leftCol),
                rightCol: getBox(rightCol),
                header: getBox(header),
                greeting: getBox(greeting),
                selfCheck: scBox,
                createNotes: getBox(createNotes),
                recently: rcBox,
                diff_recently_minus_selfcheck_top: (scBox && rcBox) ? (rcBox.top - scBox.top) : null
            };
        })()
    """)

    print(json.dumps(res, indent=2))

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
