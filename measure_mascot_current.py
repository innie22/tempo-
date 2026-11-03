import subprocess, time, json, urllib.request, websocket, tempfile, os

HTTP_PORT = 8000
CDP_PORT = 9480
user_data_dir = tempfile.mkdtemp(prefix='edge_measure_mascot_')

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

    def eval_js(expr, await_promise=False):
        params = {'expression': expr, 'returnByValue': True}
        if await_promise:
            params['awaitPromise'] = True
        res = send('Runtime.evaluate', params)
        if 'exceptionDetails' in res.get('result', {}):
            raise Exception(f"JS Exception: {res['result']['exceptionDetails']}")
        return res.get('result', {}).get('value')

    time.sleep(1)
    eval_js("""
        (async function() {
            const uid = 'usr_alex_urmode_test';
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

    eval_js("""
        const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
        if (streak) streak.scrollIntoView({ behavior: 'instant', block: 'start' });
    """)
    time.sleep(0.5)

    info = eval_js("""
        (() => {
            const card = document.querySelector('[data-tempo-ui="lower-create-notes"]');
            const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
            if (!card) return { err: 'card not found', hasEmode: !!document.getElementById('emode-home-content') };
            if (!streak) return { err: 'streak not found' };

            const textBlock = card.children[0];
            const mascotContainer = card.querySelector('[data-tempo-ui="notes-mascot-container"]') || card.children[1];
            const mascotImg = card.querySelector('img[src*="create-notes-mascot.png"]');
            const plusBtn = card.querySelector('button[aria-label="Create a new note"]');

            const rCard = card.getBoundingClientRect();
            const rStreak = streak.getBoundingClientRect();
            const rText = textBlock.getBoundingClientRect();
            const rMascotCont = mascotContainer.getBoundingClientRect();
            const rMascot = mascotImg.getBoundingClientRect();
            const rPlus = plusBtn.getBoundingClientRect();

            const csMascot = window.getComputedStyle(mascotImg);

            return {
                card: { width: rCard.width, height: rCard.height, left: rCard.left, right: rCard.right },
                streak: { width: rStreak.width, height: rStreak.height, left: rStreak.left, right: rStreak.right },
                textBlock: { width: rText.width, height: rText.height, left: rText.left, right: rText.right },
                mascotContainer: { width: rMascotCont.width, height: rMascotCont.height, left: rMascotCont.left, right: rMascotCont.right },
                mascotImg: {
                    width: rMascot.width,
                    height: rMascot.height,
                    left: rMascot.left,
                    right: rMascot.right,
                    top: rMascot.top,
                    bottom: rMascot.bottom,
                    naturalWidth: mascotImg.naturalWidth,
                    naturalHeight: mascotImg.naturalHeight,
                    computedWidth: csMascot.width,
                    computedHeight: csMascot.height
                },
                plusBtn: { width: rPlus.width, height: rPlus.height, left: rPlus.left, right: rPlus.right },
                gapTextToMascotImg: rMascot.left - rText.right,
                gapTextToMascotCont: rMascotCont.left - rText.right,
                gapMascotImgToPlus: rPlus.left - rMascot.right
            };
        })()
    """)
    print("CURRENT DETAILED MEASUREMENTS:")
    print(json.dumps(info, indent=2))

finally:
    try:
        proc.kill()
    except:
        pass
