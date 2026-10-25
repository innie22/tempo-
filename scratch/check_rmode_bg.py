import subprocess, time, json, urllib.request, websocket, tempfile, sys

user_data_dir = tempfile.mkdtemp(prefix='tempo_debug_')
port = 9399
proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={port}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--disable-gpu',
    '--no-first-run',
    'http://localhost:8000/'
])
time.sleep(2)
try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
        pages = [t for t in tabs if t.get('type') == 'page' and 'localhost' in t.get('url', '')]
    ws_url = pages[0]['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)

    msg_id = 1
    def send_cmd(method, params=None):
        global msg_id
        cmd = {'id': msg_id, 'method': method, 'params': params or {}}
        msg_id += 1
        ws.send(json.dumps(cmd))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == cmd['id']:
                return resp.get('result', {})

    def eval_js(expr):
        res = send_cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        if "exceptionDetails" in res:
            print("JS Exception:", res["exceptionDetails"])
        return res.get('result', {}).get('value')

    send_cmd('Page.enable')

    for _ in range(30):
        if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'"):
            break
        time.sleep(0.5)

    eval_js("""
        window.TempoMode.setMode('recovery');
        window.TempoApp.navigateTo('today');
    """)
    time.sleep(1)

    js_code = """
        (() => {
            const getInfo = (el) => {
                if (!el) return null;
                const cs = window.getComputedStyle(el);
                return {
                    tag: el.tagName,
                    id: el.id,
                    className: el.className,
                    bgInline: el.style.backgroundColor,
                    bgComputed: cs.backgroundColor,
                    boxShadow: cs.boxShadow
                };
            };
            return {
                body: getInfo(document.body),
                html: getInfo(document.documentElement),
                main: getInfo(document.querySelector('main')),
                screenRecovery: getInfo(document.getElementById('screen-recovery-mode')),
                rmodeContent: getInfo(document.getElementById('rmode-home-content')),
                recoveryShell: getInfo(document.querySelector('[data-tempo-ui="recovery-home-shell"]')),
                mainGrid: getInfo(document.querySelector('.recovery-home-main-grid')),
                leftCol: getInfo(document.querySelector('.recovery-left-col')),
                wpCard: getInfo(document.getElementById('recovery-working-plan')),
                selfCheckCard: getInfo(document.querySelector('.recovery-card-selfcheck')),
                recentlyCard: getInfo(document.querySelector('.recovery-card-recently')),
                activeContext: window.TempoMode ? window.TempoMode.getActiveContext() : null
            };
        })()
    """
    info = eval_js(js_code)
    print('INFO:', json.dumps(info, indent=2))
finally:
    proc.terminate()
