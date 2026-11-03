# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys, os, base64

sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
CDP_PORT = 9520
user_data_dir = tempfile.mkdtemp(prefix='edge_verify_rmode_setup_')

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
        res = send('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        if 'exceptionDetails' in res.get('result', {}):
            raise Exception(f"JS Exception: {res['result']['exceptionDetails']}")
        return res.get('result', {}).get('value')

    def capture_screenshot(filename, clip=None):
        params = {'format': 'png'}
        if clip:
            params['clip'] = clip
        res = send('Page.captureScreenshot', params)
        data = base64.b64decode(res['data'])
        out_path = os.path.join(ARTIFACT_DIR, filename)
        with open(out_path, 'wb') as f:
            f.write(data)
        print(f"Captured screenshot: {filename}")
        return out_path

    for _ in range(30):
        val = eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'")
        if val:
            break
        time.sleep(0.5)

    # =========================================================================
    # STEP 1: Login user with 0 configured tracking items in Recovery Mode
    # =========================================================================
    print("\n--- STEP 1: Test account with 0 tracking items ---")
    eval_js("""
        (async function() {
            const email = 'alex.chen@university.edu';
            const mock = {
                id: 'mock-user-alex',
                email: email,
                password: 'password123',
                profile: { id: 'mock-user-alex', full_name: 'Alex Chen', display_name: 'Alex Chen', role: 'student' }
            };
            localStorage.setItem('tempo_mock_account_' + email, JSON.stringify(mock));
            if (window.TempoAuth) {
                await window.TempoAuth.signIn(email, 'password123');
            }
            
            const uid = 'mock-user-alex';
            localStorage.setItem('tempo_active_mode', 'recovery');
            localStorage.setItem('tempo_originating_mode', 'recovery');
            localStorage.setItem(`tempo_recovery_setup_status_${uid}`, 'completed');
            localStorage.removeItem(`tempo_selfcheck_trackers_${uid}`);
            localStorage.removeItem(`tempo_recovery_setups_${uid}`);
            
            if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.init === 'function') {
                window.TempoRecoverySelfCheck.init();
            }
            if (window.TempoMode) {
                window.TempoMode.transitionContext('recovery', { skipSetupCheck: true });
                window.TempoMode.renderRmodeHome();
            }
        })()
    """)
    time.sleep(1.0)

    # Verify card inspection
    card_empty = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            if (!card) return null;
            const rect = card.getBoundingClientRect();
            const btns = Array.from(card.querySelectorAll('button')).map(b => ({
                id: b.id,
                text: b.innerText.trim(),
                dataTempoUi: b.getAttribute('data-tempo-ui'),
                className: b.className
            }));
            return {
                cardText: card.innerText,
                buttons: btns,
                rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
            };
        })()
    """)
    print("Empty card state:", json.dumps(card_empty, indent=2))

    assert card_empty is not None, "Card not found"
    assert len(card_empty['buttons']) == 1, f"Expected exactly 1 button in empty state, found {len(card_empty['buttons'])}"
    btn_text = card_empty['buttons'][0]['text']
    assert btn_text == "Set Up My Tracking System", f"Expected 'Set Up My Tracking System', got '{btn_text}'"

    # Capture closeup of unconfigured card
    r = card_empty['rect']
    capture_screenshot('rmode_selfcheck_card_empty_setup_btn.png', clip={
        'x': max(0, r['x'] - 20),
        'y': max(0, r['y'] - 20),
        'width': r['width'] + 40,
        'height': r['height'] + 40,
        'scale': 1
    })
    # Capture desktop view of empty dashboard
    capture_screenshot('rmode_dashboard_empty_setup_btn.png')

    # =========================================================================
    # STEP 2: Click "Set Up My Tracking System" button
    # =========================================================================
    print("\n--- STEP 2: Click 'Set Up My Tracking System' button ---")
    eval_js("""
        (function() {
            const btn = document.getElementById('btn-rmode-setup-tracking') || document.querySelector('[data-tempo-ui="rmode-setup-tracking-btn"]');
            if (btn) btn.click();
        })()
    """)
    time.sleep(1.0)

    click_state = eval_js("""
        (function() {
            const scScreen = document.getElementById('screen-stress-check');
            const scVisible = scScreen && !scScreen.classList.contains('hidden');
            const adjustModal = document.getElementById('modal-selfcheck-adjust');
            const adjustVisible = adjustModal && !adjustModal.classList.contains('hidden');
            const titleEl = adjustModal ? adjustModal.querySelector('h3') : null;
            const nameInp = document.getElementById('adjust-tracker-name-input');
            return {
                scVisible: scVisible,
                adjustVisible: adjustVisible,
                modalTitle: titleEl ? titleEl.innerText : null,
                inputExists: !!nameInp
            };
        })()
    """)
    print("State after click:", json.dumps(click_state, indent=2))
    assert click_state['scVisible'], "Self-check screen did not open"
    assert click_state['adjustVisible'], "Tracking setup / adjust modal did not open"
    assert click_state['inputExists'], "Tracking name input not found"

    capture_screenshot('rmode_setup_tracking_modal_opened.png')

    # =========================================================================
    # STEP 3: Add and configure a tracking item & save
    # =========================================================================
    print("\n--- STEP 3: Save tracking item and verify reactive UI update ---")
    eval_js("""
        (function() {
            const nameInp = document.getElementById('adjust-tracker-name-input');
            if (nameInp) {
                nameInp.value = 'Mindful Breathing';
                if (window.TempoSelfCheckWorkspace) {
                    window.TempoSelfCheckWorkspace.setDraftTrackerName('Mindful Breathing');
                }
            }
            const saveBtn = document.getElementById('adjust-save-submit-btn');
            if (saveBtn) saveBtn.click();
        })()
    """)
    time.sleep(1.0)

    # Return to Recovery Mode
    eval_js("""
        (function() {
            if (window.TempoMode && typeof window.TempoMode.returnToSourceContext === 'function') {
                window.TempoMode.returnToSourceContext();
            } else if (window.TempoApp) {
                window.TempoApp.navigateTo('today');
            }
        })()
    """)
    time.sleep(1.0)

    # Check updated card state
    card_configured = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            if (!card) return null;
            const rect = card.getBoundingClientRect();
            const btns = Array.from(card.querySelectorAll('button')).map(b => ({
                id: b.id,
                text: b.innerText.trim(),
                dataTempoUi: b.getAttribute('data-tempo-ui')
            }));
            const activeTrackers = window.TempoRecoverySelfCheck ? window.TempoRecoverySelfCheck.getActiveTrackers() : [];
            return {
                cardText: card.innerText,
                buttons: btns,
                activeCount: activeTrackers.length,
                trackerNames: activeTrackers.map(t => t.name),
                rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
            };
        })()
    """)
    print("Configured card state:", json.dumps(card_configured, indent=2))

    assert card_configured['activeCount'] == 1, f"Expected 1 active tracker, found {card_configured['activeCount']}"
    assert 'Mindful Breathing' in card_configured['trackerNames'], "Mindful Breathing not in active trackers"
    
    # Verify "Set Up My Tracking System" button is GONE
    btn_labels = [b['text'] for b in card_configured['buttons']]
    assert "Set Up My Tracking System" not in btn_labels, "'Set Up My Tracking System' button still present after setup"
    assert "View today's checkin" in btn_labels, "Missing 'View today's checkin' button"
    assert "Edit tracking system" in btn_labels, "Missing 'Edit tracking system' button"

    r2 = card_configured['rect']
    capture_screenshot('rmode_selfcheck_card_configured_after_setup.png', clip={
        'x': max(0, r2['x'] - 20),
        'y': max(0, r2['y'] - 20),
        'width': r2['width'] + 40,
        'height': r2['height'] + 40,
        'scale': 1
    })

    # =========================================================================
    # STEP 4: Scope & Non-Regression: URmode and EntryHome
    # =========================================================================
    print("\n--- STEP 4: Scope & Non-Regression Checks ---")
    eval_js("""
        (async function() {
            if (window.TempoMode) window.TempoMode.setMode('emergency');
            if (window.TempoApp) window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1.0)
    urmode_intact = eval_js("""
        (function() {
            const ebox = document.getElementById('emode-home-content');
            return ebox && !ebox.classList.contains('hidden') && ebox.children.length > 0;
        })()
    """)
    print(f"URmode intact and active: {urmode_intact}")
    assert urmode_intact, "URmode was affected"
    capture_screenshot('urmode_verified_intact_rmode_task.png')

    eval_js("""
        (async function() {
            if (window.TempoMode) window.TempoMode.setMode('default');
            if (window.TempoApp) window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1.0)
    entryhome_intact = eval_js("""
        (function() {
            const dbox = document.getElementById('dmode-home-content');
            return dbox && !dbox.classList.contains('hidden') && dbox.children.length > 0;
        })()
    """)
    print(f"EntryHome intact and active: {entryhome_intact}")
    assert entryhome_intact, "EntryHome was affected"
    capture_screenshot('entryhome_verified_intact_rmode_task.png')

    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
