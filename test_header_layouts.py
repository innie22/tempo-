# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys, os

sys.stdout.reconfigure(encoding='utf-8')
CDP_PORT = 9556
user_data_dir = tempfile.mkdtemp(prefix='edge_test_layout_')

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

    for _ in range(30):
        val = eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'")
        if val:
            break
        time.sleep(0.5)

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

    # Let's test Layout 1: Mode button then greeting
    eval_js("""
        (function() {
            const leftCol = document.querySelector('.recovery-left-col');
            const header = document.querySelector('.recovery-mode-header');
            const greeting = document.querySelector('.recovery-greeting');
            const btnWrapper = document.getElementById('home-mode-selector-wrapper');
            const greetingH2 = document.querySelector('.recovery-greeting h2');

            // Create a test container for layout 1
            const container = document.createElement('div');
            container.id = 'test-header-row';
            container.style.display = 'flex';
            container.style.alignItems = 'center';
            container.style.gap = '10px';
            container.style.flexWrap = 'wrap';
            container.style.marginBottom = '16px';

            greetingH2.style.fontSize = '33px';
            greetingH2.style.lineHeight = '38px';
            greetingH2.style.whiteSpace = 'nowrap';
            greeting.style.marginTop = '0';
            greeting.style.marginBottom = '0';
            greeting.style.paddingTop = '0';
            greeting.style.paddingBottom = '0';

            // Place btnWrapper and greeting inside container
            header.innerHTML = '';
            header.style.paddingBottom = '0';
            header.appendChild(container);
            container.appendChild(btnWrapper);
            container.appendChild(greeting);
        })()
    """)
    time.sleep(0.5)

    def capture_screenshot(filename, clip=None):
        params = {'format': 'png'}
        if clip:
            params['clip'] = clip
        shot = send('Page.captureScreenshot', params)
        import base64
        with open(filename, 'wb') as f:
            f.write(base64.b64decode(shot['data']))

    capture_screenshot(r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\scratch\layout1_btn_greeting.png')

    res1 = eval_js("""
        (function() {
            const btn = document.getElementById('btn-home-mode-selector');
            const greeting = document.querySelector('.recovery-greeting h2');
            const bR = btn.getBoundingClientRect();
            const gR = greeting.getBoundingClientRect();
            const sc = document.querySelector('[data-tempo-ui="recovery-self-check"]').getBoundingClientRect();
            const rc = document.querySelector('[data-tempo-ui="recovery-recently"]').getBoundingClientRect();

            return {
                btn: { left: bR.left, right: bR.right, top: bR.top, bottom: bR.bottom, centerY: (bR.top + bR.bottom)/2 },
                greeting: { left: gR.left, right: gR.right, top: gR.top, bottom: gR.bottom, centerY: (gR.top + gR.bottom)/2, fontSize: window.getComputedStyle(greeting).fontSize },
                gap: gR.left - bR.right,
                centerYDiff: ((gR.top + gR.bottom)/2) - ((bR.top + bR.bottom)/2),
                selfCheckTop: sc.top,
                recentlyTop: rc.top,
                alignmentDiff: rc.top - sc.top
            };
        })()
    """)
    print("Layout 1 (Button then Greeting):", json.dumps(res1, indent=2))

    # Now let's test Layout 2: Greeting then button
    eval_js("""
        (function() {
            const container = document.getElementById('test-header-row');
            const btnWrapper = document.getElementById('home-mode-selector-wrapper');
            const greeting = document.querySelector('.recovery-greeting');
            container.innerHTML = '';
            container.appendChild(greeting);
            container.appendChild(btnWrapper);
        })()
    """)
    time.sleep(0.5)

    capture_screenshot(r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\scratch\layout2_greeting_btn.png')

    res2 = eval_js("""
        (function() {
            const btn = document.getElementById('btn-home-mode-selector');
            const greeting = document.querySelector('.recovery-greeting h2');
            const bR = btn.getBoundingClientRect();
            const gR = greeting.getBoundingClientRect();
            const sc = document.querySelector('[data-tempo-ui="recovery-self-check"]').getBoundingClientRect();
            const rc = document.querySelector('[data-tempo-ui="recovery-recently"]').getBoundingClientRect();

            return {
                btn: { left: bR.left, right: bR.right, top: bR.top, bottom: bR.bottom, centerY: (bR.top + bR.bottom)/2 },
                greeting: { left: gR.left, right: gR.right, top: gR.top, bottom: gR.bottom, centerY: (gR.top + gR.bottom)/2, fontSize: window.getComputedStyle(greeting).fontSize },
                gap: bR.left - gR.right,
                centerYDiff: ((gR.top + gR.bottom)/2) - ((bR.top + bR.bottom)/2),
                selfCheckTop: sc.top,
                recentlyTop: rc.top,
                alignmentDiff: rc.top - sc.top
            };
        })()
    """)
    print("Layout 2 (Greeting then Button):", json.dumps(res2, indent=2))

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
