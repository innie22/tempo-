# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys, os, base64

sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
CDP_PORT = 9560
user_data_dir = tempfile.mkdtemp(prefix='edge_verify_align_')

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

    def resize_window(w, h):
        send('Emulation.setDeviceMetricsOverride', {
            'width': w,
            'height': h,
            'deviceScaleFactor': 1,
            'mobile': (w < 1024)
        })
        eval_js("window.dispatchEvent(new Event('resize'))")
        time.sleep(0.5)

    for _ in range(30):
        val = eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'")
        if val:
            break
        time.sleep(0.5)

    # Setup Rmode Account with 3 Trackers
    today = "2026-10-28"
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
            
            const trackers = [
                { id: 'trk_tension', user_id: uid, name: 'Tension', category: 'stress_sign', check_method: 'percentage', is_archived: false },
                { id: 'trk_sleep', user_id: uid, name: 'Sleep', category: 'supportive', check_method: 'options', is_archived: false },
                { id: 'trk_walk', user_id: uid, name: 'Walk', category: 'supportive', check_method: 'quantity', quantity_unit: 'minutes', is_archived: false }
            ];
            localStorage.setItem(`tempo_selfcheck_trackers_${uid}`, JSON.stringify(trackers));
            
            const obs = [
                { id: 'obs_1', user_id: uid, tracker_id: 'trk_tension', tracker_name: 'Tension', check_method: 'percentage', value: 47, date: '2026-10-28' },
                { id: 'obs_2', user_id: uid, tracker_id: 'trk_sleep', tracker_name: 'Sleep', check_method: 'options', value: 'Good', date: '2026-10-28' },
                { id: 'obs_3', user_id: uid, tracker_id: 'trk_walk', tracker_name: 'Walk', check_method: 'quantity', value: 'no', quantity_unit: 'minutes', date: '2026-10-28' }
            ];
            localStorage.setItem(`tempo_selfcheck_observations_${uid}`, JSON.stringify(obs));

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

    # =========================================================================
    # PHASE 1: Desktop 1440px Alignment Verification
    # =========================================================================
    print("\n--- PHASE 1: Desktop 1440px Alignment Verification ---")
    d1440_info = eval_js("""
        (function() {
            const sc = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            const rc = document.querySelector('[data-tempo-ui="recovery-recently"]');
            const leftCol = document.querySelector('.recovery-left-col');
            const rightCol = document.querySelector('.recovery-right-col');
            
            const scR = sc.getBoundingClientRect();
            const rcR = rc.getBoundingClientRect();
            const lR = leftCol.getBoundingClientRect();
            const rR = rightCol.getBoundingClientRect();

            return {
                scTop: scR.top,
                rcTop: rcR.top,
                diff: Math.abs(rcR.top - scR.top),
                scWidth: scR.width,
                scHeight: scR.height,
                rcWidth: rcR.width,
                rcHeight: rcR.height,
                colGap: rR.left - lR.right,
                clipRect: {
                    x: Math.min(scR.x, rcR.x) - 10,
                    y: Math.min(scR.y, rcR.y) - 20,
                    width: Math.max(scR.right, rcR.right) - Math.min(scR.left, rcR.left) + 20,
                    height: Math.max(scR.bottom, rcR.bottom) - Math.min(scR.top, rcR.top) + 40
                }
            };
        })()
    """)
    print("Desktop 1440px Measurements:", json.dumps(d1440_info, indent=2))

    print(f"Self-check Top: {d1440_info['scTop']}px")
    print(f"Recently Top: {d1440_info['rcTop']}px")
    print(f"Difference: {d1440_info['diff']}px")

    assert d1440_info['diff'] < 0.5, f"Top edges must align: diff is {d1440_info['diff']}px"
    assert abs(d1440_info['scWidth'] - 743.75) < 2.0, f"Self-check width changed: {d1440_info['scWidth']}"
    assert abs(d1440_info['scHeight'] - 290) < 2.0, f"Self-check height changed: {d1440_info['scHeight']}"
    assert abs(d1440_info['rcWidth'] - 418.25) < 2.0, f"Recently width changed: {d1440_info['rcWidth']}"
    assert abs(d1440_info['rcHeight'] - 329) < 2.0, f"Recently height changed: {d1440_info['rcHeight']}"
    assert abs(d1440_info['colGap'] - 24.0) < 1.0, f"Column gap changed: {d1440_info['colGap']}"

    capture_screenshot('rmode_aligned_cards_desktop_1440.png', clip={
        'x': max(0, d1440_info['clipRect']['x']),
        'y': max(0, d1440_info['clipRect']['y']),
        'width': d1440_info['clipRect']['width'],
        'height': d1440_info['clipRect']['height'],
        'scale': 1
    })
    capture_screenshot('rmode_dashboard_aligned_desktop_1440.png')

    # =========================================================================
    # PHASE 2: Desktop Breakpoint 1024px Alignment Verification
    # =========================================================================
    print("\n--- PHASE 2: Desktop Breakpoint 1024px Alignment Verification ---")
    resize_window(1024, 900)
    d1024_info = eval_js("""
        (function() {
            const sc = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            const rc = document.querySelector('[data-tempo-ui="recovery-recently"]');
            const scR = sc.getBoundingClientRect();
            const rcR = rc.getBoundingClientRect();
            return {
                scTop: scR.top,
                rcTop: rcR.top,
                diff: Math.abs(rcR.top - scR.top),
                clipRect: {
                    x: Math.min(scR.x, rcR.x) - 10,
                    y: Math.min(scR.y, rcR.y) - 20,
                    width: Math.max(scR.right, rcR.right) - Math.min(scR.left, rcR.left) + 20,
                    height: Math.max(scR.bottom, rcR.bottom) - Math.min(scR.top, rcR.top) + 40
                }
            };
        })()
    """)
    print("Desktop 1024px Measurements:", json.dumps(d1024_info, indent=2))
    assert d1024_info['diff'] < 0.5, f"1024px breakpoint top edges must align: diff is {d1024_info['diff']}px"
    capture_screenshot('rmode_aligned_cards_desktop_1024.png', clip={
        'x': max(0, d1024_info['clipRect']['x']),
        'y': max(0, d1024_info['clipRect']['y']),
        'width': d1024_info['clipRect']['width'],
        'height': d1024_info['clipRect']['height'],
        'scale': 1
    })

    # =========================================================================
    # PHASE 3: Mobile Stacking (< 1024px)
    # =========================================================================
    print("\n--- PHASE 3: Mobile Stacking (< 1024px) ---")
    resize_window(375, 812)
    mobile_info = eval_js("""
        (function() {
            const sc = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            const rc = document.querySelector('[data-tempo-ui="recovery-recently"]');
            const scR = sc.getBoundingClientRect();
            const rcR = rc.getBoundingClientRect();
            return {
                scTop: scR.top,
                rcTop: rcR.top,
                isStacked: rcR.top > scR.bottom,
                scMarginTop: sc.style.marginTop
            };
        })()
    """)
    print("Mobile 375px Measurements:", json.dumps(mobile_info, indent=2))
    assert mobile_info['isStacked'], "Cards must stack vertically on mobile"
    assert mobile_info['scMarginTop'] == '', "No desktop margin-top on mobile"
    capture_screenshot('rmode_stacked_cards_mobile_375.png')

    # Return to 1440 desktop
    resize_window(1440, 1100)

    # =========================================================================
    # PHASE 4: Unconfigured Account Alignment
    # =========================================================================
    print("\n--- PHASE 4: Unconfigured Account Alignment ---")
    eval_js("""
        (function() {
            const uid = 'mock-user-alex';
            localStorage.removeItem(`tempo_selfcheck_trackers_${uid}`);
            localStorage.removeItem(`tempo_selfcheck_observations_${uid}`);
            if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.init === 'function') {
                window.TempoRecoverySelfCheck.init();
            }
            if (window.TempoMode) {
                window.TempoMode.renderRmodeHome();
            }
        })()
    """)
    time.sleep(0.8)

    unconf_info = eval_js("""
        (function() {
            const sc = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            const rc = document.querySelector('[data-tempo-ui="recovery-recently"]');
            const scR = sc.getBoundingClientRect();
            const rcR = rc.getBoundingClientRect();
            return {
                scTop: scR.top,
                rcTop: rcR.top,
                diff: Math.abs(rcR.top - scR.top)
            };
        })()
    """)
    print("Unconfigured Alignment:", json.dumps(unconf_info, indent=2))
    assert unconf_info['diff'] < 0.5, f"Unconfigured card must align: diff is {unconf_info['diff']}px"

    # =========================================================================
    # PHASE 5: Non-Regression & Scope Verification
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
            return !!(ebox && !ebox.classList.contains('hidden') && ebox.children.length > 0);
        })()
    """)
    print(f"URmode intact: {urmode_ok}")
    assert urmode_ok, "URmode was affected"
    capture_screenshot('urmode_verified_intact_alignment_task.png')

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
            return !!(dbox && !dbox.classList.contains('hidden') && dbox.children.length > 0);
        })()
    """)
    print(f"EntryHome intact: {entryhome_ok}")
    assert entryhome_ok, "EntryHome was affected"
    capture_screenshot('entryhome_verified_intact_alignment_task.png')

    print("\nALL VERIFICATION PHASES PASSED WITH 100% SUCCESS!")

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
