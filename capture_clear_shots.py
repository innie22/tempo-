# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys, os, base64

sys.stdout.reconfigure(encoding='utf-8')
CDP_PORT = 9561
user_data_dir = tempfile.mkdtemp(prefix='edge_clear_shots_')

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
            localStorage.setItem('tempo_recovery_intro_dismissed', 'true');
            if (window.TempoAuth) {
                await window.TempoAuth.signIn(email, 'password123');
            }
            
            localStorage.setItem('tempo_active_mode', 'recovery');
            localStorage.setItem('tempo_originating_mode', 'recovery');
            
            if (window.TempoMode) {
                window.TempoMode.transitionContext('recovery', { skipSetupCheck: true });
                if (typeof window.TempoMode.closeRecoveryIntroModal === 'function') {
                    window.TempoMode.closeRecoveryIntroModal();
                }
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
    
    # 1. Desktop 1440 full dashboard
    capture_screenshot(os.path.join(artifact_dir, 'rmode_greeting_mode_btn_desktop_1440.png'))
    
    # 2. Desktop 1440 closeup header
    capture_screenshot(os.path.join(artifact_dir, 'rmode_header_closeup_desktop.png'), {
        'x': 80,
        'y': 70,
        'width': 850,
        'height': 80,
        'scale': 1
    })

    # 3. Dropdown opened
    eval_js("document.getElementById('btn-home-mode-selector').click()")
    time.sleep(0.3)
    capture_screenshot(os.path.join(artifact_dir, 'rmode_dropdown_opened.png'))
    eval_js("document.body.click()")
    time.sleep(0.3)

    # 4. Desktop 1024
    send('Emulation.setDeviceMetricsOverride', {
        'width': 1024,
        'height': 768,
        'deviceScaleFactor': 1,
        'mobile': False
    })
    time.sleep(0.5)
    eval_js("window.dispatchEvent(new Event('resize'))")
    time.sleep(0.5)
    capture_screenshot(os.path.join(artifact_dir, 'rmode_greeting_mode_btn_desktop_1024.png'))

    # 5. Mobile 375
    send('Emulation.setDeviceMetricsOverride', {
        'width': 375,
        'height': 812,
        'deviceScaleFactor': 1,
        'mobile': True
    })
    time.sleep(0.5)
    eval_js("window.dispatchEvent(new Event('resize'))")
    time.sleep(0.5)
    capture_screenshot(os.path.join(artifact_dir, 'rmode_greeting_mode_btn_mobile_375.png'))

    print('All clear screenshots successfully captured!')
finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
