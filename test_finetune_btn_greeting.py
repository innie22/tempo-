# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys

sys.stdout.reconfigure(encoding='utf-8')
CDP_PORT = 9569
user_data_dir = tempfile.mkdtemp(prefix='edge_finetune_test_')

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
                window.TempoMode.renderRmodeHome();
            }
        })()
    """)
    time.sleep(1.0)

    # 1. Inspect current button label font size
    current_metrics = eval_js("""
        (function() {
            const btn = document.getElementById('btn-home-mode-selector');
            const labelSpan = btn ? btn.querySelector('span.font-extrabold') : null;
            const arrowSpan = btn ? btn.querySelector('span.text-\\\\[10px\\\\]') : null;
            const greeting = document.querySelector('.recovery-greeting h2');
            
            const btnCs = window.getComputedStyle(btn);
            const labelCs = labelSpan ? window.getComputedStyle(labelSpan) : null;
            const greetingCs = greeting ? window.getComputedStyle(greeting) : null;

            const bR = btn.getBoundingClientRect();
            const gR = greeting.getBoundingClientRect();

            return {
                btnFontSize: btnCs.fontSize,
                labelFontSize: labelCs ? labelCs.fontSize : null,
                greetingFontSize: greetingCs ? greetingCs.fontSize : null,
                verticalGap: gR.top - bR.bottom,
                btnWidth: bR.width,
                btnHeight: bR.height
            };
        })()
    """)
    print("CURRENT METRICS:", json.dumps(current_metrics, indent=2))

    # 2. Prototype update
    eval_js("""
        (function() {
            const stack = document.querySelector('[data-tempo-ui="recovery-header-stack"]');
            if (stack) {
                stack.style.gap = '20px';
            }
            const btn = document.getElementById('btn-home-mode-selector');
            const labelSpan = btn ? btn.querySelector('span.font-extrabold') : null;
            if (labelSpan) {
                labelSpan.style.fontSize = '17px';
                labelSpan.classList.add('text-[17px]');
            }
            if (window.TempoMode && typeof window.TempoMode.syncRmodeSelfCheckAlignment === 'function') {
                window.TempoMode.syncRmodeSelfCheckAlignment();
            }
        })()
    """)
    time.sleep(0.5)

    proto_metrics = eval_js("""
        (function() {
            const btn = document.getElementById('btn-home-mode-selector');
            const labelSpan = btn.querySelector('span.font-extrabold');
            const greeting = document.querySelector('.recovery-greeting h2');
            const sc = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            const rc = document.querySelector('[data-tempo-ui="recovery-recently"]');

            const bR = btn.getBoundingClientRect();
            const gR = greeting.getBoundingClientRect();
            const scR = sc.getBoundingClientRect();
            const rcR = rc.getBoundingClientRect();

            const csLabel = window.getComputedStyle(labelSpan);
            const csGreeting = window.getComputedStyle(greeting);

            return {
                labelFontSize: csLabel.fontSize,
                greetingFontSize: csGreeting.fontSize,
                verticalGap: Math.round((gR.top - bR.bottom) * 10) / 10,
                leftDiff: Math.abs(gR.left - bR.left),
                btnHeight: bR.height,
                btnWidth: bR.width,
                aspectRatio: bR.width / bR.height,
                cardsAlignmentDiff: Math.abs(rcR.top - scR.top)
            };
        })()
    """)
    print("PROTOTYPE RESULTS:", json.dumps(proto_metrics, indent=2))

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
