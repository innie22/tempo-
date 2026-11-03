# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys

sys.stdout.reconfigure(encoding='utf-8')

CDP_PORT = 9515
user_data_dir = tempfile.mkdtemp(prefix='edge_test_save_')

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

    for _ in range(30):
        val = eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'")
        if val:
            break
        time.sleep(0.5)

    # 1. Login user with 0 trackers
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

    # 2. Click button to open setup
    eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            const btn = card.querySelector('button');
            btn.click();
        })()
    """)
    time.sleep(1.0)

    # 3. In the open modal, type tracker name and click save
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

    # 4. Return to Recovery Mode Home
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

    # 5. Check Rmode card now!
    res = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            return {
                text: card ? card.innerText : null,
                buttons: card ? Array.from(card.querySelectorAll('button')).map(b => b.innerText) : [],
                trackersInStorage: localStorage.getItem('tempo_selfcheck_trackers_mock-user-alex')
            };
        })()
    """)
    print("After creating tracker and returning to Rmode:")
    print(json.dumps(res, indent=2))

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
