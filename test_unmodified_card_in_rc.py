# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, base64, tempfile, os

CDP_PORT = 9498
artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'
user_data_dir = tempfile.mkdtemp(prefix='edge_test_unmod_')

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
    send('Emulation.setDeviceMetricsOverride', {'width': 1440, 'height': 1100, 'deviceScaleFactor': 1, 'mobile': False})

    def eval_js(expr, await_promise=False):
        params = {'expression': expr, 'returnByValue': True}
        if await_promise:
            params['awaitPromise'] = True
        res = send('Runtime.evaluate', params)
        if 'exceptionDetails' in res.get('result', {}):
            raise Exception(f"JS Exception: {res['result']['exceptionDetails']}")
        return res.get('result', {}).get('value')

    for _ in range(30):
        val = eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoAuth !== 'undefined'")
        if val:
            break
        time.sleep(0.5)

    eval_js("""
        (async function() {
            const uid = 'usr_alex_unmod_test';
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
        })()
    """, await_promise=True)
    time.sleep(2)

    # Let's inspect the existing card in lower section
    lowerCardInfo = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="lower-create-notes"]');
            if (!card) return 'lower-create-notes not found';
            const plusBtn = card.querySelector('button[aria-label="Create a new note"]');
            const rCard = card.getBoundingClientRect();
            const rPlus = plusBtn.getBoundingClientRect();
            return {
                cardHtml: card.outerHTML,
                cardRect: { w: rCard.width, h: rCard.height },
                plusRect: { w: rPlus.width, h: rPlus.height },
                plusClasses: plusBtn.className
            };
        })()
    """)
    print("Existing Lower Card Info:", json.dumps({k: v for k, v in lowerCardInfo.items() if k != 'cardHtml'}, indent=2))

    # Now let's test moving this card into the right column
    resMove = eval_js("""
        (function() {
            const noteCard = document.querySelector('[data-tempo-ui="dashboard-note-card"]');
            const noteSection = noteCard ? noteCard.closest('.space-y-1\\\\.5') || noteCard.parentElement : null;
            const existingCard = document.querySelector('[data-tempo-ui="lower-create-notes"]');
            if (!noteSection || !existingCard) return 'elements missing';

            // Clone card, set width to 100% and remove margin-left
            const newCard = existingCard.cloneNode(true);
            newCard.style.width = '100%';
            newCard.style.marginLeft = '0px';
            newCard.style.marginRight = '0px';
            newCard.className = newCard.className.replace('w-[calc(100%-40px)]', 'w-full').replace('lg:w-[510px]', 'w-full').replace('mx-auto', '');

            noteSection.replaceWith(newCard);
            existingCard.remove();

            const rNew = newCard.getBoundingClientRect();
            const rightCol = document.querySelector('.urgent-right-col');
            const planCard = document.querySelector('.urgent-working-plan-card');
            const rRightCol = rightCol.getBoundingClientRect();
            const rPlan = planCard.getBoundingClientRect();

            const textBlock = newCard.querySelector('[data-tempo-ui="notes-text-block"]');
            const mascotImg = newCard.querySelector('img[src*="create-notes-mascot.png"]');
            const plusBtn = newCard.querySelector('button[aria-label="Create a new note"]');

            const rText = textBlock.getBoundingClientRect();
            const rMascot = mascotImg.getBoundingClientRect();
            const rPlus = plusBtn.getBoundingClientRect();

            return {
                cardRect: { w: rNew.width, h: rNew.height, left: rNew.left, right: rNew.right },
                rightColRect: { w: rRightCol.width, h: rRightCol.height, left: rRightCol.left, right: rRightCol.right },
                planRect: { w: rPlan.width, h: rPlan.height, left: rPlan.left, right: rPlan.right },
                textRect: { w: rText.width, h: rText.height, right: rText.right },
                mascotRect: { w: rMascot.width, h: rMascot.height, left: rMascot.left, right: rMascot.right },
                plusRect: { w: rPlus.width, h: rPlus.height, left: rPlus.left, right: rPlus.right },
                gapTextToMascot: rMascot.left - rText.right,
                gapMascotToPlus: rPlus.left - rMascot.right,
                marginRightPlusToCard: rNew.right - rPlus.right
            };
        })()
    """)
    print("Move Metrics:", json.dumps(resMove, indent=2))

    # Capture screenshots
    clip_eval = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="lower-create-notes"]');
            const rightCol = document.querySelector('.urgent-right-col');
            const r = rightCol.getBoundingClientRect();
            return {
                x: Math.max(0, r.x - 20),
                y: Math.max(0, r.y - 20),
                width: r.width + 40,
                height: Math.min(800, r.height + 40),
                scale: 1
            };
        })()
    """)
    if clip_eval:
        res = send('Page.captureScreenshot', {'format': 'png', 'clip': clip_eval})
        data = base64.b64decode(res['data'])
        shot_path_closeup = os.path.join(artifact_dir, 'urmode_unmod_closeup.png')
        with open(shot_path_closeup, 'wb') as f:
            f.write(data)
        print("Closeup saved to:", shot_path_closeup)

finally:
    try: ws.close()
    except: pass
    try: proc.terminate()
    except: pass
