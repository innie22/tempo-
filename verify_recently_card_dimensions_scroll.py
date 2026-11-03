# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys, os, base64

sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
CDP_PORT = 9540
user_data_dir = tempfile.mkdtemp(prefix='edge_verify_recently_')

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

    # Helper function to configure user trackers
    def setup_account(tracker_list, obs_list):
        eval_js(f"""
            (async function() {{
                const email = 'alex.chen@university.edu';
                const mock = {{
                    id: 'mock-user-alex',
                    email: email,
                    password: 'password123',
                    profile: {{ id: 'mock-user-alex', full_name: 'Alex Chen', display_name: 'Alex Chen', role: 'student' }}
                }};
                localStorage.setItem('tempo_mock_account_' + email, JSON.stringify(mock));
                if (window.TempoAuth) {{
                    await window.TempoAuth.signIn(email, 'password123');
                }}
                
                const uid = 'mock-user-alex';
                localStorage.setItem('tempo_active_mode', 'recovery');
                localStorage.setItem('tempo_originating_mode', 'recovery');
                localStorage.setItem('tempo_selfcheck_trackers_' + uid, JSON.stringify({json.dumps(tracker_list)}));
                localStorage.setItem('tempo_selfcheck_observations_' + uid, JSON.stringify({json.dumps(obs_list)}));

                if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.init === 'function') {{
                    window.TempoRecoverySelfCheck.init();
                }}
                if (window.TempoMode) {{
                    window.TempoMode.transitionContext('recovery', {{ skipSetupCheck: true }});
                    window.TempoMode.renderRmodeHome();
                }}
            }})()
        """)
        time.sleep(0.8)

    # =========================================================================
    # PHASE 1: Baseline 3 Trackers (Matching User's Screenshot)
    # =========================================================================
    print("\n--- PHASE 1: Baseline 3 Trackers (Tension, Sleep, Walk) ---")
    today = "2026-10-28"
    trackers_3 = [
        {"id": "trk_tension", "user_id": "mock-user-alex", "name": "Tension", "category": "stress_sign", "check_method": "percentage", "is_archived": False},
        {"id": "trk_sleep", "user_id": "mock-user-alex", "name": "Sleep", "category": "supportive", "check_method": "options", "is_archived": False},
        {"id": "trk_walk", "user_id": "mock-user-alex", "name": "Walk", "category": "supportive", "check_method": "quantity", "quantity_unit": "minutes", "is_archived": False}
    ]
    obs_3 = [
        {"id": "obs_1", "user_id": "mock-user-alex", "tracker_id": "trk_tension", "tracker_name": "Tension", "check_method": "percentage", "value": 47, "date": today},
        {"id": "obs_2", "user_id": "mock-user-alex", "tracker_id": "trk_sleep", "tracker_name": "Sleep", "check_method": "options", "value": "Good", "date": today},
        {"id": "obs_3", "user_id": "mock-user-alex", "tracker_id": "trk_sleep", "tracker_name": "Sleep", "check_method": "options", "value": "Good", "date": "2026-10-27"},
        {"id": "obs_4", "user_id": "mock-user-alex", "tracker_id": "trk_sleep", "tracker_name": "Sleep", "check_method": "options", "value": "Good", "date": "2026-10-26"},
        {"id": "obs_5", "user_id": "mock-user-alex", "tracker_id": "trk_sleep", "tracker_name": "Sleep", "check_method": "options", "value": "Good", "date": "2026-10-25"},
        {"id": "obs_6", "user_id": "mock-user-alex", "tracker_id": "trk_sleep", "tracker_name": "Sleep", "check_method": "options", "value": "Good", "date": "2026-10-24"},
        {"id": "obs_7", "user_id": "mock-user-alex", "tracker_id": "trk_walk", "tracker_name": "Walk", "check_method": "quantity", "value": "no", "quantity_unit": "minutes", "date": today}
    ]
    setup_account(trackers_3, obs_3)

    metrics_info = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!card) return null;
            const r = card.getBoundingClientRect();
            const cs = window.getComputedStyle(card);
            
            const header = card.querySelector('div.shrink-0');
            const hRect = header ? header.getBoundingClientRect() : null;

            const scrollArea = card.querySelector('[data-tempo-ui="recently-metrics-scroll"]');
            const sRect = scrollArea ? scrollArea.getBoundingClientRect() : null;
            const sCs = scrollArea ? window.getComputedStyle(scrollArea) : null;

            const footer = card.querySelector('[data-tempo-ui="recently-countdown-footer"]');
            const fRect = footer ? footer.getBoundingClientRect() : null;

            return {
                card: { width: r.width, height: r.height, rect: { x: r.x, y: r.y, width: r.width, height: r.height } },
                header: hRect ? { y: hRect.y, height: hRect.height } : null,
                scrollArea: sRect ? {
                    y: sRect.y,
                    height: sRect.height,
                    scrollHeight: scrollArea.scrollHeight,
                    clientHeight: scrollArea.clientHeight,
                    overflowY: sCs.overflowY,
                    overflowX: sCs.overflowX
                } : null,
                footer: fRect ? { y: fRect.y, height: fRect.height, text: footer.innerText.trim() } : null
            };
        })()
    """)
    print("Baseline 3-item Card State:", json.dumps(metrics_info, indent=2))

    # Assertions
    card_h = metrics_info['card']['height']
    card_w = metrics_info['card']['width']
    print(f"Card Rendered Height: {card_h}px (Expected 329px)")
    print(f"Card Rendered Width: {card_w}px (Expected unchanged ~418.25px)")
    assert abs(card_h - 329) < 1.0, f"Card height {card_h} should be exactly 329px (289px + 40px)"
    assert abs(card_w - 418.25) < 2.0, f"Card width changed: {card_w}"

    # Check structural layout
    assert metrics_info['header'] is not None, "Header missing"
    assert metrics_info['scrollArea'] is not None, "Scroll area missing"
    assert metrics_info['footer'] is not None, "Footer missing"
    assert metrics_info['scrollArea']['overflowY'] == 'auto', "overflow-y must be auto"
    assert metrics_info['scrollArea']['overflowX'] == 'hidden', "overflow-x must be hidden"

    # Screenshot of 3-item card
    r = metrics_info['card']['rect']
    capture_screenshot('rmode_recently_card_3items_329px.png', clip={
        'x': max(0, r['x'] - 20),
        'y': max(0, r['y'] - 20),
        'width': r['width'] + 40,
        'height': r['height'] + 40,
        'scale': 1
    })
    capture_screenshot('rmode_dashboard_recently_card_329px.png')

    # =========================================================================
    # PHASE 2: Empty State (0 Trackers) - Constant Height
    # =========================================================================
    print("\n--- PHASE 2: Empty State (0 Trackers) ---")
    setup_account([], [])

    empty_info = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!card) return null;
            const r = card.getBoundingClientRect();
            return {
                width: r.width,
                height: r.height,
                text: card.innerText
            };
        })()
    """)
    print(f"0-tracker Card Height: {empty_info['height']}px, Width: {empty_info['width']}px")
    assert abs(empty_info['height'] - 329) < 1.0, f"Card height {empty_info['height']} with 0 items must remain 329px"
    assert abs(empty_info['width'] - card_w) < 1.0, "Card width should not change in empty state"
    assert "No active tracking items." in empty_info['text']

    capture_screenshot('rmode_recently_card_0items_329px.png', clip={
        'x': max(0, r['x'] - 20),
        'y': max(0, r['y'] - 20),
        'width': r['width'] + 40,
        'height': r['height'] + 40,
        'scale': 1
    })

    # =========================================================================
    # PHASE 3: Overflow State (7 Trackers) - Constant Height & Scrolling
    # =========================================================================
    print("\n--- PHASE 3: Overflow State (7 Trackers) ---")
    trackers_7 = [
        {"id": "trk_tension", "user_id": "mock-user-alex", "name": "Tension", "category": "stress_sign", "check_method": "percentage", "is_archived": False},
        {"id": "trk_sleep", "user_id": "mock-user-alex", "name": "Sleep", "category": "supportive", "check_method": "options", "is_archived": False},
        {"id": "trk_walk", "user_id": "mock-user-alex", "name": "Walk", "category": "supportive", "check_method": "quantity", "quantity_unit": "minutes", "is_archived": False},
        {"id": "trk_water", "user_id": "mock-user-alex", "name": "Hydration", "category": "supportive", "check_method": "quantity", "quantity_unit": "cups", "is_archived": False},
        {"id": "trk_energy", "user_id": "mock-user-alex", "name": "Energy Level", "category": "supportive", "check_method": "scale", "scale_max": 5, "is_archived": False},
        {"id": "trk_focus", "user_id": "mock-user-alex", "name": "Mental Focus", "category": "supportive", "check_method": "scale", "scale_max": 5, "is_archived": False},
        {"id": "trk_irritability", "user_id": "mock-user-alex", "name": "Irritability", "category": "stress_sign", "check_method": "percentage", "is_archived": False}
    ]
    obs_7 = [
        {"id": "obs_1", "user_id": "mock-user-alex", "tracker_id": "trk_tension", "tracker_name": "Tension", "check_method": "percentage", "value": 47, "date": today},
        {"id": "obs_2", "user_id": "mock-user-alex", "tracker_id": "trk_sleep", "tracker_name": "Sleep", "check_method": "options", "value": "Good", "date": today},
        {"id": "obs_7", "user_id": "mock-user-alex", "tracker_id": "trk_walk", "tracker_name": "Walk", "check_method": "quantity", "value": "no", "quantity_unit": "minutes", "date": today},
        {"id": "obs_8", "user_id": "mock-user-alex", "tracker_id": "trk_water", "tracker_name": "Hydration", "check_method": "quantity", "value": 4, "quantity_unit": "cups", "date": today},
        {"id": "obs_9", "user_id": "mock-user-alex", "tracker_id": "trk_energy", "tracker_name": "Energy Level", "check_method": "scale", "value": 4, "date": today},
        {"id": "obs_10", "user_id": "mock-user-alex", "tracker_id": "trk_focus", "tracker_name": "Mental Focus", "check_method": "scale", "value": 3, "date": today},
        {"id": "obs_11", "user_id": "mock-user-alex", "tracker_id": "trk_irritability", "tracker_name": "Irritability", "check_method": "percentage", "value": 20, "date": today}
    ]
    setup_account(trackers_7, obs_7)

    overflow_info = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!card) return null;
            const r = card.getBoundingClientRect();
            
            const header = card.querySelector('div.shrink-0');
            const hRect = header ? header.getBoundingClientRect() : null;

            const scrollArea = card.querySelector('[data-tempo-ui="recently-metrics-scroll"]');
            const sRect = scrollArea ? scrollArea.getBoundingClientRect() : null;

            const footer = card.querySelector('[data-tempo-ui="recently-countdown-footer"]');
            const fRect = footer ? footer.getBoundingClientRect() : null;

            return {
                card: { width: r.width, height: r.height },
                header: { top: hRect.top, height: hRect.height },
                scrollArea: {
                    top: sRect.top,
                    height: sRect.height,
                    scrollHeight: scrollArea.scrollHeight,
                    clientHeight: scrollArea.clientHeight,
                    scrollTop: scrollArea.scrollTop
                },
                footer: { top: fRect.top, height: fRect.height, text: footer.innerText.trim() }
            };
        })()
    """)
    print("Overflow 7-item Card State (Scroll top):", json.dumps(overflow_info, indent=2))

    # Outer dimensions check:
    assert abs(overflow_info['card']['height'] - 329) < 1.0, f"Card height {overflow_info['card']['height']} with 7 items must remain 329px"
    assert abs(overflow_info['card']['width'] - card_w) < 1.0, "Card width changed with 7 items"

    # Scrollability check:
    s = overflow_info['scrollArea']
    assert s['scrollHeight'] > s['clientHeight'], f"Scroll area should be scrollable: scrollHeight ({s['scrollHeight']}) > clientHeight ({s['clientHeight']})"
    print(f"Scrollable verified! scrollHeight={s['scrollHeight']} > clientHeight={s['clientHeight']}")

    # Capture top of scrollable list
    capture_screenshot('rmode_recently_card_7items_top.png', clip={
        'x': max(0, r['x'] - 20),
        'y': max(0, r['y'] - 20),
        'width': r['width'] + 40,
        'height': r['height'] + 40,
        'scale': 1
    })

    # Now scroll to bottom
    eval_js("""
        (function() {
            const scrollArea = document.querySelector('[data-tempo-ui="recently-metrics-scroll"]');
            if (scrollArea) {
                scrollArea.scrollTop = scrollArea.scrollHeight;
            }
        })()
    """)
    time.sleep(0.5)

    scrolled_info = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
            const header = card.querySelector('div.shrink-0');
            const hRect = header.getBoundingClientRect();
            const scrollArea = card.querySelector('[data-tempo-ui="recently-metrics-scroll"]');
            const footer = card.querySelector('[data-tempo-ui="recently-countdown-footer"]');
            const fRect = footer.getBoundingClientRect();

            return {
                headerTop: hRect.top,
                footerTop: fRect.top,
                scrollTop: scrollArea.scrollTop,
                scrollHeight: scrollArea.scrollHeight,
                clientHeight: scrollArea.clientHeight
            };
        })()
    """)
    print("Scrolled to bottom info:", json.dumps(scrolled_info, indent=2))

    assert scrolled_info['scrollTop'] > 0, "Scroll position did not change"
    assert abs(scrolled_info['headerTop'] - overflow_info['header']['top']) < 1.0, "Header must remain fixed at top during scrolling"
    assert abs(scrolled_info['footerTop'] - overflow_info['footer']['top']) < 1.0, "Footer must remain fixed at bottom during scrolling"

    # Capture bottom of scrollable list
    capture_screenshot('rmode_recently_card_7items_bottom.png', clip={
        'x': max(0, r['x'] - 20),
        'y': max(0, r['y'] - 20),
        'width': r['width'] + 40,
        'height': r['height'] + 40,
        'scale': 1
    })

    # =========================================================================
    # PHASE 4: Button Interaction (Adjust Tracking)
    # =========================================================================
    print("\n--- PHASE 4: Interaction (Adjust Tracking) ---")
    eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
            const btn = card.querySelector('button');
            if (btn) btn.click();
        })()
    """)
    time.sleep(1.0)

    modal_state = eval_js("""
        (function() {
            const scScreen = document.getElementById('screen-stress-check');
            return scScreen && !scScreen.classList.contains('hidden');
        })()
    """)
    print(f"Adjust Tracking button opened stress-check/adjust screen: {modal_state}")
    assert modal_state, "Adjust Tracking did not open screen"
    capture_screenshot('rmode_recently_adjust_tracking_opened.png')

    # Return to Rmode
    eval_js("""
        (function() {
            if (window.TempoMode && typeof window.TempoMode.returnToSourceContext === 'function') {
                window.TempoMode.returnToSourceContext();
            } else if (window.TempoApp) {
                window.TempoApp.navigateTo('today');
            }
        })()
    """)
    time.sleep(0.8)

    # =========================================================================
    # PHASE 5: Non-Regression & Scope Checks
    # =========================================================================
    print("\n--- PHASE 5: Non-Regression & Scope Checks ---")
    eval_js("""
        (async function() {
            if (window.TempoMode) window.TempoMode.setMode('emergency');
            if (window.TempoApp) window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1.0)
    urmode_ok = eval_js("""
        (function() {
            const ebox = document.getElementById('emode-home-content');
            return ebox && !ebox.classList.contains('hidden') && ebox.children.length > 0;
        })()
    """)
    print(f"URmode intact: {urmode_ok}")
    assert urmode_ok, "URmode was affected"
    capture_screenshot('urmode_verified_intact_recently_task.png')

    eval_js("""
        (async function() {
            if (window.TempoMode) window.TempoMode.setMode('default');
            if (window.TempoApp) window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1.0)
    entryhome_ok = eval_js("""
        (function() {
            const dbox = document.getElementById('dmode-home-content');
            return dbox && !dbox.classList.contains('hidden') && dbox.children.length > 0;
        })()
    """)
    print(f"EntryHome intact: {entryhome_ok}")
    assert entryhome_ok, "EntryHome was affected"
    capture_screenshot('entryhome_verified_intact_recently_task.png')

    print("\nALL VERIFICATION PHASES PASSED WITH 100% SUCCESS!")

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
