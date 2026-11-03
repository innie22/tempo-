import subprocess, time, json, urllib.request, websocket, base64, tempfile, os

HTTP_PORT = 8000
CDP_PORT = 9460
artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'
user_data_dir = tempfile.mkdtemp(prefix='edge_verify_urmode_notes_')

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
        params = {
            'expression': expr,
            'returnByValue': True
        }
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
    uid = 'usr_alex_urmode_test'
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

            const el = document.getElementById('urgent-rebuilt-section');
            if (el) el.scrollIntoView({{ behavior: 'instant', block: 'center' }});
        }})()
    """, await_promise=True)
    time.sleep(1.5)

    print("\n================================================================")
    print("STEP 2: Measure Self-check card and Create Notes card geometry")
    print("================================================================")
    geo = eval_js("""
        (function() {
            const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
            const notes = document.querySelector('[data-tempo-ui="lower-create-notes"]');
            if (!streak || !notes) return null;
            const rStreak = streak.getBoundingClientRect();
            const rNotes = notes.getBoundingClientRect();
            const streakCenter = rStreak.left + rStreak.width / 2;
            const notesCenter = rNotes.left + rNotes.width / 2;
            const diffCenter = Math.abs(streakCenter - notesCenter);

            const mascotImg = notes.querySelector('img[src*="create-notes-mascot.png"]');
            const svgIllustration = notes.querySelector('svg');

            return {
                streak: {
                    left: rStreak.left,
                    right: rStreak.right,
                    width: rStreak.width,
                    height: rStreak.height,
                    centerX: streakCenter
                },
                notes: {
                    left: rNotes.left,
                    right: rNotes.right,
                    width: rNotes.width,
                    height: rNotes.height,
                    centerX: notesCenter
                },
                centerDifference: diffCenter,
                widthReducedExactly40px: Math.abs(rNotes.width - 510.0) < 1.0,
                mascot: {
                    hasMascotImg: !!mascotImg,
                    src: mascotImg ? mascotImg.src : null,
                    naturalWidth: mascotImg ? mascotImg.naturalWidth : null,
                    naturalHeight: mascotImg ? mascotImg.naturalHeight : null,
                    complete: mascotImg ? mascotImg.complete : false,
                    hasSvg: !!svgIllustration
                }
            };
        })()
    """)
    print("Rendered Geometry & Mascot Info:")
    print(json.dumps(geo, indent=2))

    assert geo is not None, "Both cards should be rendered in URmode"
    assert abs(geo['notes']['width'] - 510.0) < 1.0, f"Expected notes card width 510px (-40px from 550px), got {geo['notes']['width']}px"
    assert abs(geo['notes']['height'] - 122.0) < 2.0, f"Expected notes card height 122px preserved, got {geo['notes']['height']}px"
    assert geo['centerDifference'] < 0.5, f"Expected center difference < 0.5px, got {geo['centerDifference']}px"
    assert geo['mascot']['hasMascotImg'], "Supplied mascot image should be rendered"
    assert not geo['mascot']['hasSvg'], "Old SVG illustration should be removed"
    assert geo['mascot']['complete'], "Mascot image should be loaded"
    assert geo['mascot']['naturalWidth'] == 146 and geo['mascot']['naturalHeight'] == 133, f"Expected natural dimensions 146x133, got {geo['mascot']['naturalWidth']}x{geo['mascot']['naturalHeight']}"
    print("SUCCESS: Card width reduced by exactly 40px, centered horizontally with Self-check card directly above it, and supplied mascot asset loaded properly.")

    eval_js("""
        (function() {
            const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
            if (streak) streak.scrollIntoView({ behavior: 'instant', block: 'start' });
        })()
    """)
    time.sleep(0.5)

    # Screenshot of the lower section scrolled to show both cards
    take_screenshot('urmode_create_notes_adjusted.png')

    # Closeup screenshot of the two aligned cards
    clip = eval_js("""
        (function() {
            const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
            const notes = document.querySelector('[data-tempo-ui="lower-create-notes"]');
            streak.scrollIntoView({ behavior: 'instant', block: 'start' });
            const r1 = streak.getBoundingClientRect();
            const r2 = notes.getBoundingClientRect();
            const left = Math.min(r1.left, r2.left) - 20;
            const top = Math.min(r1.top, r2.top) - 20;
            const right = Math.max(r1.right, r2.right) + 20;
            const bottom = Math.max(r1.bottom, r2.bottom) + 20;
            return {
                x: Math.max(0, left),
                y: Math.max(0, top),
                width: right - left,
                height: bottom - top,
                scale: 1
            };
        })()
    """)
    take_screenshot('urmode_create_notes_closeup.png', clip=clip)

    print("\n================================================================")
    print("STEP 3: Verify Create Notes Card Interactions")
    print("================================================================")
    interactions_info = eval_js("""
        (function() {
            const notes = document.querySelector('[data-tempo-ui="lower-create-notes"]');
            const viewBtn = notes.querySelector('button');
            const plusBtn = notes.querySelector('button[aria-label="Create a new note"]');
            return {
                viewBtnText: viewBtn ? viewBtn.textContent.trim() : null,
                hasPlusBtn: !!plusBtn,
                plusText: plusBtn ? plusBtn.textContent.trim() : null
            };
        })()
    """)
    print("Interaction buttons info:", interactions_info)
    assert interactions_info['viewBtnText'] == 'View my notes', f"Expected 'View my notes', got {interactions_info['viewBtnText']}"
    assert interactions_info['hasPlusBtn'], "Plus button should exist"
    assert interactions_info['plusText'] == '+', f"Expected '+', got {interactions_info['plusText']}"
    print("SUCCESS: Interactions and buttons intact.")

    print("\n================================================================")
    print("STEP 4: Verify Strict Scope Boundaries (Rmode and EntryHome intact)")
    print("================================================================")
    # Check Rmode
    eval_js("""
        (function() {
            window.TempoMode.setMode('recovery');
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('today');
            }
        })()
    """)
    time.sleep(1.2)
    rmode_ok = eval_js("""
        (function() {
            const rBox = document.getElementById('rmode-home-content');
            return rBox && !rBox.classList.contains('hidden');
        })()
    """)
    assert rmode_ok, "Rmode content should be visible and functional"
    take_screenshot('rmode_verified_intact_notes_task.png')
    print("SUCCESS: Rmode is completely intact and functional.")

    # Check EntryHome
    eval_js("""
        (function() {
            window.TempoMode.setMode(null);
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('today');
            }
        })()
    """)
    time.sleep(1.2)
    entry_ok = eval_js("""
        (function() {
            const dBox = document.getElementById('dmode-home-content');
            return dBox && !dBox.classList.contains('hidden');
        })()
    """)
    assert entry_ok, "EntryHome content should be visible and functional"
    take_screenshot('entryhome_verified_intact_notes_task.png')
    print("SUCCESS: EntryHome is completely intact and functional.")

    print("\n================================================================")
    print("ALL VERIFICATIONS PASSED!")
    print("================================================================")

finally:
    try:
        proc.kill()
    except:
        pass
