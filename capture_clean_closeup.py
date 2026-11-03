import subprocess, time, json, urllib.request, websocket, base64, tempfile, os

HTTP_PORT = 8000
CDP_PORT = 9465
artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'
user_data_dir = tempfile.mkdtemp(prefix='edge_closeup_')

proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={CDP_PORT}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--window-size=1440,1100',
    f'http://127.0.0.1:{HTTP_PORT}/'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    time.sleep(2.5)
    with urllib.request.urlopen(f'http://127.0.0.1:{CDP_PORT}/json') as resp:
        tabs = json.loads(resp.read().decode())
    pages = [t for t in tabs if t.get('type') == 'page' and '127.0.0.1' in t.get('url', '')]
    ws_url = (pages[0] if pages else tabs[0])['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)

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
            const mock = { id: 'u1', email: 'student@tempo.app', role: 'student', user_metadata: { full_name: 'Alex' } };
            localStorage.setItem('tempo_mock_account_student@tempo.app', JSON.stringify(mock));
            localStorage.setItem('tempo_local_dev_user', JSON.stringify(mock));
            localStorage.setItem('tempo_active_mode', 'emergency');
            if (window.TempoAuth) await window.TempoAuth.signIn('student@tempo.app', 'password123');
            if (window.TempoMode) window.TempoMode.setMode('emergency');
            if (window.TempoApp) window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1.5)

    eval_js("""
        const el = document.getElementById('urgent-rebuilt-section');
        if (el) el.scrollIntoView({ behavior: 'instant', block: 'start' });
    """)
    time.sleep(0.5)

    clip = eval_js("""
        (() => {
            const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
            const notes = document.querySelector('[data-tempo-ui="lower-create-notes"]');
            const r1 = streak.getBoundingClientRect();
            const r2 = notes.getBoundingClientRect();
            return {
                x: Math.max(0, Math.min(r1.left, r2.left) - 15),
                y: Math.max(0, Math.min(r1.top, r2.top) - 15),
                width: Math.max(r1.right, r2.right) - Math.min(r1.left, r2.left) + 30,
                height: Math.max(r1.bottom, r2.bottom) - Math.min(r1.top, r2.top) + 30,
                scale: 1
            };
        })()
    """)

    print("Clip rect:", clip)
    res = send('Page.captureScreenshot', {'format': 'png', 'clip': clip})
    print("Screenshot response keys:", list(res.keys()))
    if 'data' in res:
        data = base64.b64decode(res['data'])
        out_path = os.path.join(artifact_dir, 'urmode_create_notes_closeup.png')
        with open(out_path, 'wb') as f:
            f.write(data)
        print(f"Captured: {out_path} ({len(data)} bytes)")

    # Full lower section screenshot
    res_full = send('Page.captureScreenshot', {'format': 'png'})
    data_full = base64.b64decode(res_full['data'])
    out_full = os.path.join(artifact_dir, 'urmode_create_notes_adjusted.png')
    with open(out_full, 'wb') as f:
        f.write(data_full)
    print(f"Captured: {out_full} ({len(data_full)} bytes)")

finally:
    try:
        proc.kill()
    except:
        pass
