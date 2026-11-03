# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile

CDP_PORT = 9489
user_data_dir = tempfile.mkdtemp(prefix='edge_test_width_')

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

    before_info = eval_js("""
        (function() {
            const el = document.querySelector('[data-tempo-ui="urgent-posts"]');
            const r = el.getBoundingClientRect();
            const parent = el.parentElement;
            const pr = parent.getBoundingClientRect();
            return {
                width: r.width,
                left: r.left,
                center: r.left + r.width / 2,
                parentWidth: pr.width,
                parentCenter: pr.left + pr.width / 2
            };
        })()
    """)
    print("BEFORE:", json.dumps(before_info, indent=2))

    eval_js("""
        (function() {
            const el = document.querySelector('[data-tempo-ui="urgent-posts"]');
            el.style.width = 'calc(100% + 20px)';
            el.style.marginLeft = '-10px';
            el.style.marginRight = '-10px';
            el.style.boxSizing = 'border-box';
        })()
    """)
    time.sleep(0.5)

    after_info = eval_js("""
        (function() {
            const el = document.querySelector('[data-tempo-ui="urgent-posts"]');
            const r = el.getBoundingClientRect();
            const parent = el.parentElement;
            const pr = parent.getBoundingClientRect();
            return {
                width: r.width,
                left: r.left,
                center: r.left + r.width / 2,
                parentWidth: pr.width,
                parentCenter: pr.left + pr.width / 2,
                diffWidth: r.width - 386,
                centerDiff: (r.left + r.width / 2) - (pr.left + pr.width / 2)
            };
        })()
    """)
    print("AFTER:", json.dumps(after_info, indent=2))

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
