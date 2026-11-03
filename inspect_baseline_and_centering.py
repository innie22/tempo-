# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys

sys.stdout.reconfigure(encoding='utf-8')

CDP_PORT = 9496
user_data_dir = tempfile.mkdtemp(prefix='edge_test_centering_')

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

    def measure():
        return eval_js("""
            (function() {
                const page = document.querySelector('[data-tempo-ui="urgent-home-shell"]');
                if (!page) return { error: 'No urgent-home-shell' };
                const pr = page.getBoundingClientRect();
                const pageCenter = pr.left + pr.width / 2;

                const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
                const comm = document.querySelector('[data-tempo-ui="urgent-posts"]');
                if (!streak || !comm) return { error: 'No streak or comm' };
                const sr = streak.getBoundingClientRect();
                const cr = comm.getBoundingClientRect();

                const groupLeft = Math.min(sr.left, cr.left);
                const groupRight = Math.max(sr.right, cr.right);
                const groupWidth = groupRight - groupLeft;
                const groupCenter = (groupLeft + groupRight) / 2;
                const offset = groupCenter - pageCenter;

                const docOverflow = document.documentElement.scrollWidth > window.innerWidth;

                return {
                    pageLeft: Math.round(pr.left * 100) / 100,
                    pageRight: Math.round(pr.right * 100) / 100,
                    pageWidth: Math.round(pr.width * 100) / 100,
                    pageCenter: Math.round(pageCenter * 100) / 100,
                    groupLeft: Math.round(groupLeft * 100) / 100,
                    groupRight: Math.round(groupRight * 100) / 100,
                    groupWidth: Math.round(groupWidth * 100) / 100,
                    groupCenter: Math.round(groupCenter * 100) / 100,
                    offsetFromPageCenter: Math.round(offset * 100) / 100,
                    leftMarginToPage: Math.round((groupLeft - pr.left) * 100) / 100,
                    rightMarginToPage: Math.round((pr.right - groupRight) * 100) / 100,
                    streakWidth: Math.round(sr.width * 100) / 100,
                    streakHeight: Math.round(sr.height * 100) / 100,
                    commWidth: Math.round(cr.width * 100) / 100,
                    commHeight: Math.round(cr.height * 100) / 100,
                    gap: Math.round((cr.left - sr.right) * 100) / 100,
                    hasOverflow: docOverflow
                };
            })()
        """)

    print("=== BASELINE MEASUREMENTS (CURRENT UNEDITED) ===")
    for w in [1440, 1280, 1024, 768, 375]:
        send('Emulation.setDeviceMetricsOverride', {'width': w, 'height': 900, 'deviceScaleFactor': 1, 'mobile': (w < 768)})
        time.sleep(0.3)
        print(f"\nViewport {w}px:")
        print(json.dumps(measure(), indent=2))

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
