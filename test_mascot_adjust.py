import subprocess, time, json, urllib.request, websocket, tempfile

CDP_PORT = 9482
user_data_dir = tempfile.mkdtemp(prefix='edge_test_mascot_')

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

            if (window.TempoAuth) await window.TempoAuth.signIn('student@tempo.app', 'password123');
            if (window.TempoAuth && typeof window.TempoAuth.closeAllAuthModals === 'function') window.TempoAuth.closeAllAuthModals();
            document.querySelectorAll('.auth-modal-overlay').forEach(m => m.classList.add('hidden'));

            if (window.TempoMode) window.TempoMode.setMode('emergency');
            if (window.TempoApp) window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1.5)

    test_res = eval_js("""
        (() => {
            const card = document.querySelector('[data-tempo-ui="lower-create-notes"]');
            const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
            const textBlock = card.children[0];
            const mascotContainer = card.querySelector('[data-tempo-ui="notes-mascot-container"]');
            const mascotImg = card.querySelector('img[src*="create-notes-mascot.png"]');
            const plusBtn = card.querySelector('button[aria-label="Create a new note"]');

            // Apply adjustments
            card.style.height = '122px';
            card.style.maxHeight = '122px';
            card.style.minHeight = '122px';
            card.style.paddingTop = '10px';
            card.style.paddingBottom = '10px';
            card.style.justifyContent = 'flex-start';

            textBlock.classList.add('shrink-0');
            textBlock.style.marginRight = '0px';

            mascotContainer.style.marginLeft = '10px';
            mascotContainer.style.marginRight = '0px';

            mascotImg.style.height = '100px';
            mascotImg.style.width = 'auto';
            mascotImg.style.maxHeight = '100px';
            mascotImg.style.maxWidth = 'none';

            plusBtn.style.marginLeft = 'auto';

            const rCard = card.getBoundingClientRect();
            const rStreak = streak.getBoundingClientRect();
            const rText = textBlock.getBoundingClientRect();
            const rMascot = mascotImg.getBoundingClientRect();
            const rPlus = plusBtn.getBoundingClientRect();

            const streakCenter = rStreak.left + rStreak.width / 2;
            const cardCenter = rCard.left + rCard.width / 2;
            const gap = rMascot.left - rText.right;
            const spaceToPlus = rPlus.left - rMascot.right;

            // Check vertical centering
            const cardInnerCenterY = rCard.top + rCard.height / 2;
            const mascotCenterY = rMascot.top + rMascot.height / 2;
            const vertDiff = Math.abs(cardInnerCenterY - mascotCenterY);

            return {
                cardWidth: rCard.width,
                cardHeight: rCard.height,
                mascotHeight: rMascot.height,
                mascotWidth: rMascot.width,
                aspectRatio: rMascot.width / rMascot.height,
                naturalAspectRatio: mascotImg.naturalWidth / mascotImg.naturalHeight,
                horizontalGapTextToMascot: gap,
                spaceFromMascotToPlus: spaceToPlus,
                streakCenter,
                cardCenter,
                centerDiff: Math.abs(streakCenter - cardCenter),
                cardInnerCenterY,
                mascotCenterY,
                vertDiff,
                hasOverlap: (rText.right > rMascot.left) || (rMascot.right > rPlus.left)
            };
        })()
    """)
    print("PROTOTYPED LAYOUT TEST RESULTS:")
    print(json.dumps(test_res, indent=2))
finally:
    try:
        proc.kill()
    except:
        pass
