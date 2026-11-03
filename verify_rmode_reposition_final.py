# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys, os, base64

sys.stdout.reconfigure(encoding='utf-8')
CDP_PORT = 9568
user_data_dir = tempfile.mkdtemp(prefix='edge_verify_reposition_')

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
            localStorage.setItem('tempo_lang', 'en');
            const email = 'alex.chen@university.edu';
            const mock = {
                id: 'mock-user-alex',
                email: email,
                password: 'password123',
                profile: { id: 'mock-user-alex', full_name: 'Innietest', display_name: 'Innietest', role: 'student' }
            };
            localStorage.setItem('tempo_mock_account_' + email, JSON.stringify(mock));
            localStorage.setItem('tempo_recovery_intro_dismissed', 'true');
            if (window.TempoAuth) {
                await window.TempoAuth.signIn(email, 'password123');
            }
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('en');
            }
            localStorage.setItem('tempo_active_mode', 'recovery');
            localStorage.setItem('tempo_originating_mode', 'recovery');
            
            if (window.TempoMode) {
                window.TempoMode.transitionContext('recovery', { skipSetupCheck: true });
                const modal = document.getElementById('recovery-mode-intro-modal');
                if (modal) modal.classList.add('hidden');
                const backdrop = document.querySelector('[data-tempo-ui="recovery-intro-backdrop"]');
                if (backdrop) backdrop.classList.add('hidden');
                window.TempoMode.renderRmodeHome();
            }
        })()
    """)
    time.sleep(1.0)

    artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'

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
                hasSprout: btn.innerText.includes('🌱'),
                btnRect: { left: bR.left, right: bR.right, top: bR.top, bottom: bR.bottom, width: bR.width, height: bR.height },
                h2Rect: { left: hR.left, right: hR.right, top: hR.top, bottom: hR.bottom, width: hR.width, height: hR.height },
                fontSize: csH2.fontSize,
                fontWeight: csH2.fontWeight,
                color: csH2.color,
                verticalGap: Math.round((hR.top - bR.bottom) * 10) / 10,
                leftDiff: Math.abs(hR.left - bR.left),
                heightIncrease: bR.height - 30,
                aspectRatio: bR.width / bR.height,
                selfCheckTop: scR.top,
                recentlyTop: rcR.top,
                cardsAlignmentDiff: Math.abs(rcR.top - scR.top)
            };
        })()
    """)
    print("DESKTOP 1440 METRICS:")
    print(json.dumps(d1440, indent=2))

    assert d1440['hasSprout'] is False, "Sprout symbol should be removed"
    assert d1440['btnRect']['height'] == 40, f"Button height should be 40px (+10px), got {d1440['btnRect']['height']}px"
    assert abs(d1440['btnRect']['width'] - 207.7) <= 2, f"Button width should be ~208px, got {d1440['btnRect']['width']}px"
    assert d1440['verticalGap'] == 10.0, f"Vertical gap should be 10.0px, got {d1440['verticalGap']}px"
    assert d1440['leftDiff'] <= 1.0, f"Greeting should be left-aligned with button, got diff {d1440['leftDiff']}px"
    assert d1440['fontSize'] == '33px', f"Greeting font size should be 33px, got {d1440['fontSize']}"
    assert d1440['cardsAlignmentDiff'] <= 1.0, f"Daily self-check and recently cards should be aligned, got diff {d1440['cardsAlignmentDiff']}px"
    print("✓ Desktop 1440px assertions passed!")

    # Capture screenshots
    capture_screenshot(os.path.join(artifact_dir, 'rmode_repositioned_header_desktop_1440.png'))
    capture_screenshot(os.path.join(artifact_dir, 'rmode_repositioned_header_closeup.png'), {
        'x': 80,
        'y': 65,
        'width': 850,
        'height': 130,
        'scale': 1
    })

    # Test dropdown click
    eval_js("document.getElementById('btn-home-mode-selector').click()")
    time.sleep(0.3)
    dd_open = eval_js("!document.getElementById('home-mode-selector-dropdown').classList.contains('hidden')")
    assert dd_open is True, "Dropdown should open on button click"
    capture_screenshot(os.path.join(artifact_dir, 'rmode_repositioned_dropdown_opened.png'))
    eval_js("document.body.click()")
    time.sleep(0.3)
    dd_closed = eval_js("document.getElementById('home-mode-selector-dropdown').classList.contains('hidden')")
    assert dd_closed is True, "Dropdown should close on outside click"
    print("✓ Mode dropdown assertion passed!")

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
            return {
                verticalGap: Math.round((hR.top - bR.bottom) * 10) / 10,
                leftDiff: Math.abs(hR.left - bR.left),
                btnHeight: bR.height,
                btnWidth: bR.width,
                fontSize: window.getComputedStyle(h2).fontSize
            };
        })()
    """)
    print("DESKTOP 1024 METRICS:", json.dumps(d1024, indent=2))
    assert d1024['verticalGap'] == 10.0
    assert d1024['leftDiff'] <= 1.0
    assert d1024['btnHeight'] == 40
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
                verticalGap: Math.round((hR.top - bR.bottom) * 10) / 10,
                leftDiff: Math.abs(hR.left - bR.left),
                btnHeight: bR.height,
                fontSize: csH2.fontSize,
                scrollWidth: document.documentElement.scrollWidth,
                innerWidth: window.innerWidth,
                hasHorizontalOverflow: document.documentElement.scrollWidth > window.innerWidth
            };
        })()
    """)
    print("MOBILE 375 METRICS:", json.dumps(m375, indent=2))
    assert m375['verticalGap'] == 10.0, f"Expected 10px vertical gap, got {m375['verticalGap']}px"
    assert m375['hasHorizontalOverflow'] is False, "No horizontal overflow on mobile"
    capture_screenshot(os.path.join(artifact_dir, 'rmode_repositioned_header_mobile_375.png'))
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
    capture_screenshot(os.path.join(artifact_dir, 'urmode_verified_intact_reposition_task.png'))
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
    capture_screenshot(os.path.join(artifact_dir, 'entryhome_verified_intact_reposition_task.png'))
    print("✓ EntryHome regression check passed!")

    print("\nALL VERIFICATIONS COMPLETED SUCCESSFULLY!")

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
