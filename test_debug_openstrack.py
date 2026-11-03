# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys

sys.stdout.reconfigure(encoding='utf-8')

CDP_PORT = 9513
user_data_dir = tempfile.mkdtemp(prefix='edge_test_debug_')

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
        res = send('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
        if 'exceptionDetails' in res.get('result', {}):
            raise Exception(f"JS Exception: {res['result']['exceptionDetails']}")
        return res.get('result', {}).get('value')

    for _ in range(30):
        val = eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'")
        if val:
            break
        time.sleep(0.5)

    res = eval_js("""
        (function() {
            const uid = 'test_user_empty';
            localStorage.setItem('tempo_auth_user', JSON.stringify({
                id: uid,
                email: 'test@example.com',
                name: 'Test Innie',
                preferredName: 'Test Innie'
            }));
            localStorage.setItem('tempo_active_mode', 'recovery');
            localStorage.setItem('tempo_originating_mode', 'recovery');
            
            // Check isUserAuthenticated() inside TempoMode:
            let authBefore = false;
            if (window.TempoAuth && window.TempoAuth.getCurrentUser) {
                authBefore = !!window.TempoAuth.getCurrentUser();
            }

            try {
                window.TempoMode.openStrack('open', { sourceContext: 'recovery', openAdjust: true });
            } catch (e) {
                return { error: e.toString() };
            }

            const scScreen = document.getElementById('screen-stress-check');
            return {
                authBefore: authBefore,
                scScreenExists: !!scScreen,
                scScreenHidden: scScreen ? scScreen.classList.contains('hidden') : null,
                activeScreen: window.TempoApp ? window.TempoApp.activeScreen : null
            };
        })()
    """)
    print("Debug result:", json.dumps(res, indent=2))

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
