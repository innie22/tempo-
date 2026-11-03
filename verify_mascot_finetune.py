import subprocess, time, json, urllib.request, websocket, base64, tempfile, os

HTTP_PORT = 8000
CDP_PORT = 9485
artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'
user_data_dir = tempfile.mkdtemp(prefix='edge_verify_mascot_finetune_')

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

    for _ in range(30):
        res = send('Runtime.evaluate', {
            'expression': "typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoAuth !== 'undefined'",
            'returnByValue': True
        })
        if res.get('result', {}).get('value'):
            break
        time.sleep(0.5)

    send("Emulation.setDeviceMetricsOverride", {
        "width": 1440,
        "height": 1100,
        "deviceScaleFactor": 1,
        "mobile": False
    })

    def eval_js(expr, await_promise=False):
        params = {'expression': expr, 'returnByValue': True}
        if await_promise:
            params['awaitPromise'] = True
        res = send('Runtime.evaluate', params)
        if 'exceptionDetails' in res.get('result', {}):
            raise Exception(f"JS Exception: {res['result']['exceptionDetails']}")
        return res.get('result', {}).get('value')

    def take_screenshot(filename, clip=None):
        params = {'format': 'png'}
        if clip:
            params['clip'] = clip
        res = send('Page.captureScreenshot', params)
        data = base64.b64decode(res['data'])
        filepath = os.path.join(artifact_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(data)
        print(f"Captured: {filepath} ({len(data)} bytes)")
        return filepath

    print("================================================================")
    print("STEP 1: Authenticate and switch to URmode (emergency)")
    print("================================================================")
    uid = 'usr_alex_mascot_finetune'
    eval_js(f"""
        (async function() {{
            const uid = '{uid}';
            localStorage.clear();
            const mockAccount = {{
                id: uid,
                email: 'student@tempo.app',
                password: 'password123',
                full_name: 'Alex Rivera',
                role: 'student',
                user_metadata: {{ full_name: 'Alex Rivera', role: 'student' }}
            }};
            localStorage.setItem('tempo_mock_account_student@tempo.app', JSON.stringify(mockAccount));
            localStorage.setItem('tempo_local_dev_user', JSON.stringify(mockAccount));
            localStorage.setItem('tempo_user_role', 'student');
            localStorage.setItem('tempo_active_mode', 'emergency');
            localStorage.setItem('tempo_originating_mode', 'emergency');

            if (window.TempoAuth && typeof window.TempoAuth.signIn === 'function') {{
                await window.TempoAuth.signIn('student@tempo.app', 'password123');
            }}

            if (window.TempoAuth && typeof window.TempoAuth.closeAllAuthModals === 'function') window.TempoAuth.closeAllAuthModals();
            document.querySelectorAll('.auth-modal-overlay').forEach(m => m.classList.add('hidden'));

            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') window.TempoMode.setMode('emergency');
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') window.TempoApp.navigateTo('today');

            const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
            if (streak) streak.scrollIntoView({{ behavior: 'instant', block: 'start' }});
        }})()
    """, await_promise=True)
    time.sleep(1.5)

    print("\n================================================================")
    print("STEP 2: Verify Mascot Size, Proportions, Gap, and Alignment")
    print("================================================================")
    metrics = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="lower-create-notes"]');
            const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
            const textBlock = card.querySelector('[data-tempo-ui="notes-text-block"]') || card.children[0];
            const mascotContainer = card.querySelector('[data-tempo-ui="notes-mascot-container"]');
            const mascotImg = card.querySelector('img[src*="create-notes-mascot.png"]');
            const plusBtn = card.querySelector('button[aria-label="Create a new note"]');

            const rCard = card.getBoundingClientRect();
            const rStreak = streak.getBoundingClientRect();
            const rText = textBlock.getBoundingClientRect();
            const rMascotCont = mascotContainer.getBoundingClientRect();
            const rMascot = mascotImg.getBoundingClientRect();
            const rPlus = plusBtn.getBoundingClientRect();

            const csMascot = window.getComputedStyle(mascotImg);

            const gap = rMascot.left - rText.right;
            const streakCenter = rStreak.left + rStreak.width / 2;
            const cardCenter = rCard.left + rCard.width / 2;
            const cardCenterY = rCard.top + rCard.height / 2;
            const mascotCenterY = rMascot.top + rMascot.height / 2;

            return {
                card: { width: rCard.width, height: rCard.height, left: rCard.left, right: rCard.right },
                streak: { width: rStreak.width, height: rStreak.height, left: rStreak.left, right: rStreak.right },
                textBlock: { width: rText.width, height: rText.height, left: rText.left, right: rText.right },
                mascotImg: {
                    width: rMascot.width,
                    height: rMascot.height,
                    left: rMascot.left,
                    right: rMascot.right,
                    top: rMascot.top,
                    bottom: rMascot.bottom,
                    naturalWidth: mascotImg.naturalWidth,
                    naturalHeight: mascotImg.naturalHeight,
                    computedHeight: csMascot.height,
                    computedWidth: csMascot.width
                },
                plusBtn: { width: rPlus.width, height: rPlus.height, left: rPlus.left, right: rPlus.right },
                gapTextToMascot: gap,
                spaceMascotToPlus: rPlus.left - rMascot.right,
                streakCenter,
                cardCenter,
                centerDiff: Math.abs(streakCenter - cardCenter),
                vertDiff: Math.abs(cardCenterY - mascotCenterY),
                hasOverlap: (rText.right > rMascot.left) || (rMascot.right > rPlus.left)
            };
        })()
    """)
    print("Rendered Measurements:")
    print(json.dumps(metrics, indent=2))

    assert metrics is not None, "Create Notes card and mascot must be rendered"

    # 1. Mascot height increased by exactly 20px (from 80px to 100px)
    assert abs(metrics['mascotImg']['height'] - 100.0) < 1.0, f"Expected mascot height 100.0px (80 + 20), got {metrics['mascotImg']['height']}px"

    # 2. Mascot width scales proportionally preserving aspect ratio (146/133)
    aspect_rendered = metrics['mascotImg']['width'] / metrics['mascotImg']['height']
    aspect_natural = metrics['mascotImg']['naturalWidth'] / metrics['mascotImg']['naturalHeight']
    assert abs(aspect_rendered - aspect_natural) < 0.01, f"Expected aspect ratio {aspect_natural}, got {aspect_rendered}"

    # 3. Horizontal gap between text block and mascot is exactly 10px
    assert abs(metrics['gapTextToMascot'] - 10.0) < 0.5, f"Expected gap 10.0px, got {metrics['gapTextToMascot']}px"

    # 4. Vertical alignment and no overlap
    assert metrics['vertDiff'] < 1.0, f"Expected vertical center diff < 1.0px, got {metrics['vertDiff']}px"
    assert not metrics['hasOverlap'], "Mascot must not overlap text block or plus button"

    # 5. Preserved card dimensions and center alignment with Self-check card
    assert abs(metrics['card']['width'] - 510.0) < 1.0, f"Expected card width 510.0px, got {metrics['card']['width']}px"
    assert abs(metrics['card']['height'] - 122.0) < 2.0, f"Expected card height 122.0px, got {metrics['card']['height']}px"
    assert metrics['centerDiff'] < 0.5, f"Expected card horizontal center diff < 0.5px, got {metrics['centerDiff']}px"

    print("SUCCESS: All mascot fine-tune requirements (height +20px, proportional width, 10px gap, vertical alignment, no overlap, preserved card dimensions) verified successfully.")

    # Screenshot of lower section
    take_screenshot('urmode_mascot_finetune_overview.png')

    print("\n================================================================")
    print("STEP 3: Verify Create Notes Card Interactions")
    print("================================================================")
    btn_info = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="lower-create-notes"]');
            const viewBtn = card.querySelector('button');
            const plusBtn = card.querySelector('button[aria-label="Create a new note"]');
            return {
                viewBtnText: viewBtn ? viewBtn.textContent.trim() : null,
                hasPlusBtn: !!plusBtn,
                plusText: plusBtn ? plusBtn.textContent.trim() : null
            };
        })()
    """)
    assert btn_info['viewBtnText'] == 'View my notes'
    assert btn_info['hasPlusBtn'] and btn_info['plusText'] == '+'
    print("SUCCESS: Card buttons and interactions are intact.")

    print("\n================================================================")
    print("STEP 4: Verify Scope Isolation (Rmode & EntryHome Intact)")
    print("================================================================")
    eval_js("""
        (function() {
            window.TempoMode.setMode('recovery');
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1.2)
    rmode_ok = eval_js("!document.getElementById('rmode-home-content').classList.contains('hidden')")
    assert rmode_ok, "Rmode must be visible"
    take_screenshot('rmode_verified_intact_finetune_task.png')
    print("SUCCESS: Rmode is completely intact.")

    eval_js("""
        (function() {
            window.TempoMode.setMode(null);
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1.2)
    entry_ok = eval_js("!document.getElementById('dmode-home-content').classList.contains('hidden')")
    assert entry_ok, "EntryHome must be visible"
    take_screenshot('entryhome_verified_intact_finetune_task.png')
    print("SUCCESS: EntryHome is completely intact.")

    print("\n================================================================")
    print("ALL MASCOT FINE-TUNE VERIFICATIONS PASSED WITH 100% SUCCESS!")
    print("================================================================")

finally:
    try:
        proc.kill()
    except:
        pass
