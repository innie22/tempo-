# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys, os, base64

sys.stdout.reconfigure(encoding='utf-8')
CDP_PORT = 9560
user_data_dir = tempfile.mkdtemp(prefix='edge_verify_final_')

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
    time.sleep(2.0)
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
            raise Exception('JS Exception: ' + str(res['result']['exceptionDetails']))
        return res.get('result', {}).get('value')

    def capture_screenshot(filename, clip=None):
        params = {'format': 'png'}
        if clip:
            params['clip'] = clip
        shot = send('Page.captureScreenshot', params)
        with open(filename, 'wb') as f:
            f.write(base64.b64decode(shot['data']))

    for _ in range(30):
        val = eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'")
        if val:
            break
        time.sleep(0.5)

    # 1. Sign in as Innietest and enter Recovery Mode
    eval_js("""
        (async function() {
            const email = 'alex.chen@university.edu';
            const mock = {
                id: 'mock-user-alex',
                email: email,
                password: 'password123',
                profile: { id: 'mock-user-alex', full_name: 'Innietest', display_name: 'Innietest', role: 'student' }
            };
            localStorage.setItem('tempo_mock_account_' + email, JSON.stringify(mock));
            if (window.TempoAuth) {
                await window.TempoAuth.signIn(email, 'password123');
            }
            
            localStorage.setItem('tempo_active_mode', 'recovery');
            localStorage.setItem('tempo_originating_mode', 'recovery');
            
            if (window.TempoMode) {
                window.TempoMode.transitionContext('recovery', { skipSetupCheck: true });
                window.TempoMode.renderRmodeHome();
            }
        })()
    """)
    time.sleep(1.0)

    # TEST 1: Desktop Viewport (1440px)
    d1440 = eval_js("""
        (function() {
            const btn = document.getElementById('btn-home-mode-selector');
            const h2 = document.querySelector('.recovery-greeting h2');
            const sc = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            const rc = document.querySelector('[data-tempo-ui="recovery-recently"]');

            const bR = btn.getBoundingClientRect();
            const hR = h2.getBoundingClientRect();
            const scR = sc.getBoundingClientRect();
            const rcR = rc.getBoundingClientRect();

            const csH2 = window.getComputedStyle(h2);
            const csBtn = window.getComputedStyle(btn);

            return {
                btnText: btn.innerText.replace(/\\s+/g, ' ').trim(),
                greetingText: h2.innerText.replace(/\\s+/g, ' ').trim(),
                btnRect: { left: bR.left, right: bR.right, top: bR.top, bottom: bR.bottom, width: bR.width, height: bR.height },
                h2Rect: { left: hR.left, right: hR.right, top: hR.top, bottom: hR.bottom, width: hR.width, height: hR.height },
                fontSize: csH2.fontSize,
                fontWeight: csH2.fontWeight,
                color: csH2.color,
                horizontalGap: Math.round((hR.left - bR.right) * 10) / 10,
                centerYDiff: Math.abs(((hR.top + hR.bottom)/2) - ((bR.top + bR.bottom)/2)),
                selfCheckTop: scR.top,
                recentlyTop: rcR.top,
                alignmentDiff: Math.abs(rcR.top - scR.top)
            };
        })()
    """)
    print("DESKTOP 1440 METRICS:")
    print(json.dumps(d1440, indent=2))

    # Assertions for 1440px
    assert d1440['fontSize'] == '33px', f"Expected 33px font size, got {d1440['fontSize']}"
    assert d1440['horizontalGap'] == 10.0, f"Expected 10.0px horizontal gap, got {d1440['horizontalGap']}px"
    assert d1440['centerYDiff'] <= 1.0, f"Expected vertically aligned (< 1px diff), got {d1440['centerYDiff']}px"
    assert d1440['alignmentDiff'] <= 1.0, f"Expected selfCheck and recently aligned, got {d1440['alignmentDiff']}px"
    print("✓ Desktop 1440px assertions passed!")

    # Save artifacts for 1440px
    artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'
    capture_screenshot(os.path.join(artifact_dir, 'rmode_greeting_mode_btn_desktop_1440.png'))
    
    # Close-up clip of the header
    capture_screenshot(os.path.join(artifact_dir, 'rmode_header_closeup_desktop.png'), {
        'x': 80,
        'y': 60,
        'width': 850,
        'height': 100,
        'scale': 1
    })

    # Test Mode dropdown toggle
    eval_js("document.getElementById('btn-home-mode-selector').click()")
    time.sleep(0.3)
    dd_open = eval_js("!document.getElementById('home-mode-selector-dropdown').classList.contains('hidden')")
    assert dd_open is True, "Dropdown should open on button click"
    capture_screenshot(os.path.join(artifact_dir, 'rmode_dropdown_opened.png'))
    eval_js("document.body.click()")
    time.sleep(0.3)
    dd_closed = eval_js("document.getElementById('home-mode-selector-dropdown').classList.contains('hidden')")
    assert dd_closed is True, "Dropdown should close on outside click"
    print("✓ Mode dropdown toggle assertion passed!")

    # TEST 2: Desktop 1024px Viewport
    send('Emulation.setDeviceMetricsOverride', {
        'width': 1024,
        'height': 768,
        'deviceScaleFactor': 1,
        'mobile': False
    })
    time.sleep(0.5)
    eval_js("window.dispatchEvent(new Event('resize'))")
    time.sleep(0.5)

    d1024 = eval_js("""
        (function() {
            const btn = document.getElementById('btn-home-mode-selector');
            const h2 = document.querySelector('.recovery-greeting h2');
            const bR = btn.getBoundingClientRect();
            const hR = h2.getBoundingClientRect();
            const csH2 = window.getComputedStyle(h2);

            return {
                fontSize: csH2.fontSize,
                horizontalGap: Math.round((hR.left - bR.right) * 10) / 10,
                centerYDiff: Math.abs(((hR.top + hR.bottom)/2) - ((bR.top + bR.bottom)/2))
            };
        })()
    """)
    print("DESKTOP 1024 METRICS:", json.dumps(d1024, indent=2))
    assert d1024['fontSize'] == '33px'
    assert d1024['horizontalGap'] == 10.0
    capture_screenshot(os.path.join(artifact_dir, 'rmode_greeting_mode_btn_desktop_1024.png'))
    print("✓ Desktop 1024px assertions passed!")

    # TEST 3: Mobile 375px Viewport
    send('Emulation.setDeviceMetricsOverride', {
        'width': 375,
        'height': 812,
        'deviceScaleFactor': 1,
        'mobile': True
    })
    time.sleep(0.5)
    eval_js("window.dispatchEvent(new Event('resize'))")
    time.sleep(0.5)

    m375 = eval_js("""
        (function() {
            const btn = document.getElementById('btn-home-mode-selector');
            const h2 = document.querySelector('.recovery-greeting h2');
            const bR = btn.getBoundingClientRect();
            const hR = h2.getBoundingClientRect();
            const csH2 = window.getComputedStyle(h2);

            return {
                fontSize: csH2.fontSize,
                isWrapped: hR.top >= bR.bottom,
                scrollWidth: document.documentElement.scrollWidth,
                innerWidth: window.innerWidth,
                hasHorizontalOverflow: document.documentElement.scrollWidth > window.innerWidth
            };
        })()
    """)
    print("MOBILE 375 METRICS:", json.dumps(m375, indent=2))
    assert m375['fontSize'] == '29px', f"Expected 29px font size on mobile, got {m375['fontSize']}"
    assert m375['isWrapped'] is True, "Greeting should wrap below button on mobile"
    assert m375['hasHorizontalOverflow'] is False, "No horizontal overflow on mobile"
    capture_screenshot(os.path.join(artifact_dir, 'rmode_greeting_mode_btn_mobile_375.png'))
    print("✓ Mobile 375px assertions passed!")

    # TEST 4: URmode regression check
    send('Emulation.setDeviceMetricsOverride', {
        'width': 1440,
        'height': 1100,
        'deviceScaleFactor': 1,
        'mobile': False
    })
    time.sleep(0.5)
    eval_js("""
        (function() {
            if (window.TempoMode) {
                window.TempoMode.transitionContext('urgent');
            }
        })()
    """)
    time.sleep(0.8)
    ur_status = eval_js("""
        (function() {
            const emodeBox = document.getElementById('emode-home-content');
            const btn = emodeBox ? emodeBox.querySelector('#btn-home-mode-selector') : null;
            return {
                isVisible: emodeBox && !emodeBox.classList.contains('hidden'),
                hasModeBtn: !!btn,
                btnText: btn ? btn.innerText.replace(/\\s+/g, ' ').trim() : ''
            };
        })()
    """)
    print("URMODE STATUS:", json.dumps(ur_status, indent=2))
    assert ur_status['isVisible'] is True
    assert ur_status['hasModeBtn'] is True
    capture_screenshot(os.path.join(artifact_dir, 'urmode_verified_intact_greeting_task.png'))
    print("✓ URmode regression check passed!")

    # TEST 5: EntryHome regression check
    eval_js("""
        (function() {
            if (window.TempoMode) {
                window.TempoMode.transitionContext('default');
            }
        })()
    """)
    time.sleep(0.8)
    dmode_status = eval_js("""
        (function() {
            const dmodeBox = document.getElementById('dmode-home-content');
            return {
                isVisible: dmodeBox && !dmodeBox.classList.contains('hidden')
            };
        })()
    """)
    print("ENTRYHOME STATUS:", json.dumps(dmode_status, indent=2))
    assert dmode_status['isVisible'] is True
    capture_screenshot(os.path.join(artifact_dir, 'entryhome_verified_intact_greeting_task.png'))
    print("✓ EntryHome regression check passed!")

    print("\nALL VERIFICATIONS COMPLETED SUCCESSFULLY!")

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
