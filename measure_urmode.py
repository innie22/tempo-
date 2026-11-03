import subprocess, time, json, urllib.request, websocket, base64, os, tempfile

CDP_PORT = 9448
user_data_dir = tempfile.mkdtemp(prefix='edge_measure_')

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
                if 'error' in resp:
                    raise Exception(f"CDP Error in {method}: {resp['error']}")
                return resp.get('result', {})

    send("Page.enable")
    send("DOM.enable")

    def eval_js(expr, await_promise=False):
        res = send('Runtime.evaluate', {
            'expression': expr,
            'returnByValue': True,
            'awaitPromise': await_promise
        })
        return res.get('result', {}).get('value')

    time.sleep(1.5)
    eval_js("""
        (async function() {
            const uid = 'usr_test_alex';
            localStorage.clear();
            const mockAccount = {
                id: uid,
                email: 'student@tempo.app',
                password: 'password123',
                full_name: 'Alex Rivera',
                role: 'student',
                user_metadata: { full_name: 'Alex Rivera', role: 'student' }
            };
            localStorage.setItem('tempo_mock_account_student@tempo.app', JSON.stringify(mockAccount));
            localStorage.setItem('tempo_local_dev_user', JSON.stringify(mockAccount));
            localStorage.setItem('tempo_user_role', 'student');
            localStorage.setItem('tempo_active_mode', 'emergency');
            localStorage.setItem('tempo_originating_mode', 'emergency');

            if (window.TempoAuth && typeof window.TempoAuth.signIn === 'function') {
                await window.TempoAuth.signIn('student@tempo.app', 'password123');
            }

            if (window.TempoAuth && typeof window.TempoAuth.closeAllAuthModals === 'function') window.TempoAuth.closeAllAuthModals();
            document.querySelectorAll('.auth-modal-overlay').forEach(m => m.classList.add('hidden'));

            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') window.TempoMode.setMode('emergency');
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') window.TempoApp.navigateTo('today');

            const el = document.getElementById('urgent-rebuilt-section');
            if (el) el.scrollIntoView({ behavior: 'instant', block: 'center' });
        })()
    """, await_promise=True)

    time.sleep(1.5)

    info = eval_js("""
        (() => {
            const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
            const notes = document.querySelector('[data-tempo-ui="lower-create-notes"]');
            if (!streak || !notes) return { error: 'elements not found', streak: !!streak, notes: !!notes };
            const rStreak = streak.getBoundingClientRect();
            const rNotes = notes.getBoundingClientRect();
            const csNotes = window.getComputedStyle(notes);
            return {
                streak: {
                    x: rStreak.x,
                    y: rStreak.y,
                    width: rStreak.width,
                    height: rStreak.height,
                    centerX: rStreak.x + rStreak.width / 2
                },
                notes: {
                    x: rNotes.x,
                    y: rNotes.y,
                    width: rNotes.width,
                    height: rNotes.height,
                    centerX: rNotes.x + rNotes.width / 2,
                    computedWidth: csNotes.width,
                    computedHeight: csNotes.height,
                    classes: notes.className
                }
            };
        })()
    """)
    print("CURRENT RENDERED GEOMETRY:")
    print(json.dumps(info, indent=2))

    # Take screenshot of the lower section
    res = send('Page.captureScreenshot')
    png_data = base64.b64decode(res['data'])
    out_path = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\scratch\urmode_before_measurement.png'
    with open(out_path, 'wb') as f:
        f.write(png_data)
    print(f"Captured: {out_path}")

finally:
    try:
        proc.kill()
    except:
        pass
