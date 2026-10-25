import subprocess, time, json, urllib.request, websocket, tempfile, sys, base64

user_data_dir = tempfile.mkdtemp(prefix='tempo_wp_shot_')
port = 9422
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
        return res.get('result', {}).get('value')

    def save_screenshot(path):
        data = send_cmd('Page.captureScreenshot', {'format': 'png'})
        b64 = data.get('data', '')
        if b64:
            with open(path, 'wb') as f:
                f.write(base64.b64decode(b64))

    send_cmd('Page.enable')
    send_cmd('Emulation.setDeviceMetricsOverride', {'width': 1280, 'height': 900, 'deviceScaleFactor': 1, 'mobile': False})

    for _ in range(30):
        if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'"):
            break
        time.sleep(0.5)

    eval_js("""
        (async () => {
            const mock = {
                id: 'local_user_selfcheck',
                email: 'selfcheck_user@tempo.edu',
                raw_email: 'selfcheck_user@tempo.edu',
                password: 'password123',
                user_metadata: { full_name: 'Alex Chen', display_name: 'Alex Chen', role: 'student' }
            };
            localStorage.setItem('tempo_mock_account_selfcheck_user@tempo.edu', JSON.stringify(mock));
            if (window.TempoAuth) {
                await window.TempoAuth.signIn('selfcheck_user@tempo.edu', 'password123');
            }
            localStorage.setItem('tempo_recovery_intro_seen', 'true');
            localStorage.setItem('tempo_recovery_setup_completed', 'true');
            window.TempoMode.transitionContext('recovery', { skipSetupCheck: true });
            window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1)

    eval_js('document.querySelector(\'[data-tempo-ui="recovery-working-plan"]\').scrollIntoView({ block: "center" })')
    time.sleep(0.5)
    save_screenshot(r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\rmode_wp_card_on_e8ecf1_page.png')
    print('SUCCESS')
finally:
    proc.terminate()
