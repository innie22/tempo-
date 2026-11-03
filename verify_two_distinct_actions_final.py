# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys, os, base64

sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
CDP_PORT = 9530
user_data_dir = tempfile.mkdtemp(prefix='edge_verify_two_actions_')

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
    # STEP 1: Unconfigured Account (0 tracking items)
    # =========================================================================
    print("\n--- STEP 1: Setup Unconfigured Account (0 Trackers) in Rmode ---")
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

    card_info = eval_js("""
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
    print("Unconfigured card buttons:", json.dumps(card_info['buttons'], indent=2))

    assert card_info is not None, "Today's self-check card not found"
    assert len(card_info['buttons']) == 2, f"Expected exactly 2 buttons in empty state, found {len(card_info['buttons'])}"
    
    btn_labels = [b['text'] for b in card_info['buttons']]
    assert "Add Tracking" in btn_labels, f"Missing 'Add Tracking' button, found: {btn_labels}"
    assert "Set Up My Tracking System" in btn_labels, f"Missing 'Set Up My Tracking System' button, found: {btn_labels}"

    add_btn = next(b for b in card_info['buttons'] if b['text'] == "Add Tracking")
    setup_btn = next(b for b in card_info['buttons'] if b['text'] == "Set Up My Tracking System")

    # Verify visual distinction:
    assert 'bg-white' in add_btn['className'] and 'border' in add_btn['className'], "Add Tracking should be secondary outline button"
    assert 'bg-[#7B9688]' in setup_btn['className'] and 'text-white' in setup_btn['className'], "Set Up My Tracking System should be primary filled button"

    # Capture screenshots of unconfigured state
    r = card_info['rect']
    capture_screenshot('rmode_unconfigured_card_two_buttons.png', clip={
        'x': max(0, r['x'] - 20),
        'y': max(0, r['y'] - 20),
        'width': r['width'] + 40,
        'height': r['height'] + 40,
        'scale': 1
    })
    capture_screenshot('rmode_dashboard_two_buttons.png')

    # =========================================================================
    # STEP 2: Test Action 1 - "Add Tracking"
    # =========================================================================
    print("\n--- STEP 2: Click 'Add Tracking' (Direct add-item flow) ---")
    eval_js("""
        (function() {
            const btn = document.getElementById('btn-rmode-add-tracking');
            btn.click();
        })()
    """)
    time.sleep(1.0)

    add_tracking_state = eval_js("""
        (function() {
            const scScreen = document.getElementById('screen-stress-check');
            const scVisible = scScreen && !scScreen.classList.contains('hidden');
            const adjustModal = document.getElementById('modal-selfcheck-adjust');
            const adjustVisible = adjustModal && !adjustModal.classList.contains('hidden');
            const recoverySetupModal = document.getElementById('modal-recovery-setup');
            const recoverySetupVisible = recoverySetupModal && !recoverySetupModal.classList.contains('hidden');
            const nameInp = document.getElementById('adjust-tracker-name-input');
            return {
                scVisible: scVisible,
                adjustVisible: adjustVisible,
                recoverySetupVisible: recoverySetupVisible,
                nameInputExists: !!nameInp
            };
        })()
    """)
    print("Add Tracking state:", json.dumps(add_tracking_state, indent=2))
    assert add_tracking_state['scVisible'], "Self-check screen did not open"
    assert add_tracking_state['adjustVisible'], "Adjust / add tracking modal did not open"
    assert not add_tracking_state['recoverySetupVisible'], "Recovery setup introduction modal should NOT open when Add Tracking is clicked"
    assert add_tracking_state['nameInputExists'], "Name input does not exist"

    capture_screenshot('rmode_add_tracking_direct_flow.png')

    # Close modal and return to Rmode dashboard
    eval_js("""
        (function() {
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.closeAdjustModal === 'function') {
                window.TempoSelfCheckWorkspace.closeAdjustModal();
            }
            if (window.TempoMode && typeof window.TempoMode.returnToSourceContext === 'function') {
                window.TempoMode.returnToSourceContext();
            } else if (window.TempoApp) {
                window.TempoApp.navigateTo('today');
            }
        })()
    """)
    time.sleep(1.0)

    # =========================================================================
    # STEP 3: Test Action 2 - "Set Up My Tracking System"
    # =========================================================================
    print("\n--- STEP 3: Click 'Set Up My Tracking System' (Recovery Intro Modal) ---")
    eval_js("""
        (function() {
            const btn = document.getElementById('btn-rmode-setup-tracking');
            btn.click();
        })()
    """)
    time.sleep(1.0)

    intro_state = eval_js("""
        (function() {
            const modal = document.getElementById('modal-recovery-setup');
            const isVisible = modal && !modal.classList.contains('hidden');
            const heading = modal ? modal.querySelector('h2') : null;
            const badge = modal ? modal.querySelector('.uppercase') : null;
            const adjustModal = document.getElementById('modal-selfcheck-adjust');
            const adjustVisible = adjustModal && !adjustModal.classList.contains('hidden');
            const btns = modal ? Array.from(modal.querySelectorAll('button')).map(b => b.innerText.trim()) : [];
            return {
                isVisible: isVisible,
                heading: heading ? heading.innerText.trim() : null,
                badge: badge ? badge.innerText.trim() : null,
                adjustVisible: adjustVisible,
                buttons: btns
            };
        })()
    """)
    print("Intro Modal state:", json.dumps(intro_state, indent=2))
    assert intro_state['isVisible'], "Recovery Mode setup introduction modal did not open"
    assert not intro_state['adjustVisible'], "Adjust modal should NOT open when Set Up My Tracking System is clicked"
    assert intro_state['heading'] == "Give yourself some space to recover.", f"Expected heading 'Give yourself some space to recover.', got '{intro_state['heading']}'"
    assert "RECOVERY MODE" in (intro_state['badge'] or ""), "Recovery Mode badge missing"
    assert any("Start my recovery check-in" in b for b in intro_state['buttons']), "Missing 'Start my recovery check-in' button"
    assert any("I'll explore first" in b for b in intro_state['buttons']), "Missing 'I\\'ll explore first' button"

    capture_screenshot('rmode_setup_intro_modal_opened.png')

    # Click "Start my recovery check-in" and verify progression to Stage 2
    eval_js("""
        (function() {
            const modal = document.getElementById('modal-recovery-setup');
            const startBtn = Array.from(modal.querySelectorAll('button')).find(b => b.innerText.includes('Start my recovery check-in'));
            if (startBtn) startBtn.click();
        })()
    """)
    time.sleep(0.8)

    stage2_state = eval_js("""
        (function() {
            try {
                const modal = document.getElementById('modal-recovery-setup');
                const h3 = modal ? modal.querySelector('h3') : null;
                const spans = modal ? Array.from(modal.querySelectorAll('span')) : [];
                const stepSpan = spans.find(s => s.innerText.includes('STEP 1 OF 5'));
                return {
                    heading: h3 ? h3.innerText.trim() : null,
                    step: stepSpan ? stepSpan.innerText.trim() : null
                };
            } catch(e) {
                return { error: e.toString() };
            }
        })()
    """)
    print("Stage 2 state:", json.dumps(stage2_state, indent=2))
    assert stage2_state['heading'] == "What did you notice in yourself?", f"Expected Stage 2 heading, got '{stage2_state['heading']}'"
    capture_screenshot('rmode_setup_stage2_looking_back.png')

    # Close modal
    eval_js("""
        (function() {
            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.close === 'function') {
                window.TempoRecoverySetup.close();
            }
            if (window.TempoMode) window.TempoMode.renderRmodeHome();
        })()
    """)
    time.sleep(0.5)

    # =========================================================================
    # STEP 4: Save Tracking Item & Verify Reactive UI Update
    # =========================================================================
    print("\n--- STEP 4: Save tracking item and verify configured state ---")
    eval_js("""
        (function() {
            const uid = 'mock-user-alex';
            const tracker = {
                id: 'trk_test_custom_1',
                user_id: uid,
                name: 'Mindful Breathing',
                category: 'supportive',
                check_method: 'percentage',
                is_archived: false,
                created_at: new Date().toISOString()
            };
            if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.createTracker === 'function') {
                window.TempoRecoverySelfCheck.createTracker(tracker);
            }
            try {
                window.dispatchEvent(new CustomEvent('tempo:selfcheck-updated', { detail: { tracker, action: 'create' } }));
            } catch (e) {}
            if (window.TempoMode) window.TempoMode.renderRmodeHome();
        })()
    """)
    time.sleep(1.0)

    card_configured = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            if (!card) return null;
            const rect = card.getBoundingClientRect();
            const btns = Array.from(card.querySelectorAll('button')).map(b => b.innerText.trim());
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

    assert card_configured['activeCount'] >= 1, "Should have active trackers"
    assert "Mindful Breathing" in card_configured['trackerNames'], "Mindful Breathing missing"
    assert "Add Tracking" not in card_configured['buttons'], "'Add Tracking' button should not be present in configured state"
    assert "Set Up My Tracking System" not in card_configured['buttons'], "'Set Up My Tracking System' button should not be present in configured state"
    assert "View today's checkin" in card_configured['buttons'], "Missing 'View today\\'s checkin' button"
    assert "Edit tracking system" in card_configured['buttons'], "Missing 'Edit tracking system' button"

    r_conf = card_configured['rect']
    capture_screenshot('rmode_configured_card_after_setup.png', clip={
        'x': max(0, r_conf['x'] - 20),
        'y': max(0, r_conf['y'] - 20),
        'width': r_conf['width'] + 40,
        'height': r_conf['height'] + 40,
        'scale': 1
    })

    # =========================================================================
    # STEP 5: Scope & Non-Regression
    # =========================================================================
    print("\n--- STEP 5: Scope & Non-Regression Checks ---")
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
    print(f"URmode intact: {urmode_intact}")
    assert urmode_intact, "URmode was affected"
    capture_screenshot('urmode_verified_intact_two_actions_task.png')

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
    print(f"EntryHome intact: {entryhome_intact}")
    assert entryhome_intact, "EntryHome was affected"
    capture_screenshot('entryhome_verified_intact_two_actions_task.png')

    print("\nALL 5 TEST PHASES PASSED WITH 100% SUCCESS!")

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
