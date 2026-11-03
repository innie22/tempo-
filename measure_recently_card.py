# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys, os

sys.stdout.reconfigure(encoding='utf-8')

CDP_PORT = 9535
user_data_dir = tempfile.mkdtemp(prefix='edge_measure_recently_')

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
            
            // Set 3 trackers matching the user's screenshot: Tension, Sleep, Walk
            const trackers = [
                { id: 'trk_tension', user_id: uid, name: 'Tension', category: 'stress_sign', check_method: 'percentage', is_archived: false },
                { id: 'trk_sleep', user_id: uid, name: 'Sleep', category: 'supportive', check_method: 'options', is_archived: false },
                { id: 'trk_walk', user_id: uid, name: 'Walk', category: 'supportive', check_method: 'quantity', quantity_unit: 'minutes', is_archived: false }
            ];
            localStorage.setItem(`tempo_selfcheck_trackers_${uid}`, JSON.stringify(trackers));
            
            // Set observations matching the screenshot:
            // Tension: 47%, Sleep: 5 good nights, Walk: no minutes
            const today = new Date().toISOString().split('T')[0];
            const observations = [
                { id: 'obs_1', user_id: uid, tracker_id: 'trk_tension', tracker_name: 'Tension', check_method: 'percentage', value: 47, date: today },
                { id: 'obs_2', user_id: uid, tracker_id: 'trk_sleep', tracker_name: 'Sleep', check_method: 'options', value: 'Good', date: today },
                { id: 'obs_3', user_id: uid, tracker_id: 'trk_sleep', tracker_name: 'Sleep', check_method: 'options', value: 'Good', date: '2026-10-27' },
                { id: 'obs_4', user_id: uid, tracker_id: 'trk_sleep', tracker_name: 'Sleep', check_method: 'options', value: 'Good', date: '2026-10-26' },
                { id: 'obs_5', user_id: uid, tracker_id: 'trk_sleep', tracker_name: 'Sleep', check_method: 'options', value: 'Good', date: '2026-10-25' },
                { id: 'obs_6', user_id: uid, tracker_id: 'trk_sleep', tracker_name: 'Sleep', check_method: 'options', value: 'Good', date: '2026-10-24' },
                { id: 'obs_7', user_id: uid, tracker_id: 'trk_walk', tracker_name: 'Walk', check_method: 'quantity', value: 'no', quantity_unit: 'minutes', date: today }
            ];
            localStorage.setItem(`tempo_selfcheck_observations_${uid}`, JSON.stringify(observations));

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

    card_measurements = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!card) return null;
            const rect = card.getBoundingClientRect();
            const cs = window.getComputedStyle(card);
            
            // Header
            const header = card.querySelector('div.flex.items-center.justify-between');
            const headerRect = header ? header.getBoundingClientRect() : null;
            
            // Metrics container
            const metrics = card.querySelector('div.space-y-3.pt-1');
            const metricsRect = metrics ? metrics.getBoundingClientRect() : null;
            const metricItems = metrics ? Array.from(metrics.children).map(c => ({
                text: c.innerText.replace(/\\n/g, ' '),
                height: c.getBoundingClientRect().height
            })) : [];

            // Footer
            const footer = card.querySelector('div.pt-3.text-center');
            const footerRect = footer ? footer.getBoundingClientRect() : null;

            return {
                card: {
                    width: rect.width,
                    height: rect.height,
                    paddingTop: cs.paddingTop,
                    paddingBottom: cs.paddingBottom,
                    paddingLeft: cs.paddingLeft,
                    paddingRight: cs.paddingRight,
                    boxSizing: cs.boxSizing
                },
                header: headerRect ? { height: headerRect.height } : null,
                metrics: metricsRect ? { height: metricsRect.height, items: metricItems } : null,
                footer: footerRect ? { height: footerRect.height, text: footer.innerText } : null
            };
        })()
    """)

    print("Current Recently Card Measurements:")
    print(json.dumps(card_measurements, indent=2))

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
