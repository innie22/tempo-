# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile

CDP_PORT = 9492
user_data_dir = tempfile.mkdtemp(prefix='edge_test_group_center_')

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
    send('Emulation.setDeviceMetricsOverride', {'width': 1440, 'height': 1100, 'deviceScaleFactor': 1, 'mobile': False})

    def eval_js(expr):
        res = send('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
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
            localStorage.setItem('tempo_active_mode', 'emergency');
            localStorage.setItem('tempo_originating_mode', 'emergency');
            if (window.TempoMode) window.TempoMode.setMode('emergency');
            if (window.TempoApp) window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1.5)

    def measure(label):
        return eval_js(f"""
            (function() {{
                const page = document.querySelector('[data-tempo-ui="urgent-home-shell"]');
                const pageRect = page.getBoundingClientRect();
                const pageCenter = pageRect.left + pageRect.width / 2;

                const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
                const comm = document.querySelector('[data-tempo-ui="urgent-posts"]');
                const sr = streak.getBoundingClientRect();
                const cr = comm.getBoundingClientRect();

                const groupLeft = Math.min(sr.left, cr.left);
                const groupRight = Math.max(sr.right, cr.right);
                const groupWidth = groupRight - groupLeft;
                const groupCenter = (groupLeft + groupRight) / 2;
                const offsetFromPageCenter = groupCenter - pageCenter;

                return {{
                    label: '{label}',
                    pageCenter: pageCenter,
                    groupLeft: groupLeft,
                    groupRight: groupRight,
                    groupWidth: groupWidth,
                    groupCenter: groupCenter,
                    offsetFromPageCenter: offsetFromPageCenter,
                    streakWidth: sr.width,
                    streakHeight: sr.height,
                    commWidth: cr.width,
                    commHeight: cr.height,
                    gap: cr.left - sr.right
                }};
            }})()
        """)

    print("CURRENT BASELINE:")
    print(json.dumps(measure("current"), indent=2))

    # Test Option A: Adjusting parent container alignment/margins
    # In current DOM: #urgent-rebuilt-section > div is the parent container.
    # What if the parent container has max-width: 1108.5px (or width to fit both cards plus gap) and mx-auto?
    eval_js("""
        (function() {
            const container = document.querySelector('#urgent-rebuilt-section > div');
            // Check current container
            container.style.maxWidth = '1108.5px';
            container.style.marginLeft = 'auto';
            container.style.marginRight = 'auto';
            // Also check streakCard self-end
            const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
            streak.classList.remove('self-end');
            // Remove negative margins on comm panel if any, or see how container behaves
        })()
    """)
    time.sleep(0.5)

    print("\nAFTER OPTION A:")
    print(json.dumps(measure("option_A"), indent=2))

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
