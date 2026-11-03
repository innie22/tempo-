# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys

sys.stdout.reconfigure(encoding='utf-8')

CDP_PORT = 9497
user_data_dir = tempfile.mkdtemp(prefix='edge_test_container_variations_')

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

    def measure(w):
        send('Emulation.setDeviceMetricsOverride', {'width': w, 'height': 900, 'deviceScaleFactor': 1, 'mobile': (w < 768)})
        time.sleep(0.3)
        return eval_js("""
            (function() {
                const page = document.querySelector('[data-tempo-ui="urgent-home-shell"]');
                const pr = page.getBoundingClientRect();
                const pageCenter = pr.left + pr.width / 2;

                const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
                const comm = document.querySelector('[data-tempo-ui="urgent-posts"]');
                const sr = streak.getBoundingClientRect();
                const cr = comm.getBoundingClientRect();

                const groupLeft = Math.min(sr.left, cr.left);
                const groupRight = Math.max(sr.right, cr.right);
                const groupWidth = groupRight - groupLeft;
                const groupCenter = (groupLeft + groupRight) / 2;
                const offset = groupCenter - pageCenter;

                const docOverflow = document.documentElement.scrollWidth > window.innerWidth;

                return {
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
                    commWidth: Math.round(cr.width * 100) / 100,
                    gap: Math.round((cr.left - sr.right) * 100) / 100,
                    hasOverflow: docOverflow
                };
            })()
        """)

    # Let's test VARIATION A:
    # Desktop margin shift of +59.25px on the parent container via style or class
    print("\n--- VARIATION A: parent style.transform = translateX(59.25px) on @media (min-width: 1024px) ---")
    eval_js("""
        (function() {
            const container = document.querySelector('#urgent-rebuilt-section > div');
            container.id = 'urgent-lower-parent-container';
            let styleEl = document.getElementById('test-custom-style');
            if (!styleEl) {
                styleEl = document.createElement('style');
                styleEl.id = 'test-custom-style';
                document.head.appendChild(styleEl);
            }
            styleEl.textContent = `
                @media (min-width: 1200px) {
                    #urgent-lower-parent-container {
                        transform: translateX(59.25px);
                    }
                }
            `;
        })()
    """)
    for w in [1440, 1280, 1200, 1024, 768, 375]:
        print(f"Viewport {w}px:", measure(w))

    # Let's test VARIATION B:
    # What if the parent container uses max-w-[1098.5px] or max-w-fit?
    # What happens if we don't shift by 59.25px, but adjust the parent container's width/margins?
    print("\n--- VARIATION B: parent container width / grid columns ---")
    eval_js("""
        (function() {
            const styleEl = document.getElementById('test-custom-style');
            if (styleEl) styleEl.textContent = '';
            const container = document.querySelector('#urgent-rebuilt-section > div');
            // If parent container is a 2-column flex/grid matching the cards:
            // What if styleEl defines:
            styleEl.textContent = `
                @media (min-width: 1024px) {
                    #urgent-lower-parent-container {
                        max-width: 1098.5px !important;
                        display: flex !important;
                        flex-direction: row !important;
                        align-items: flex-start !important;
                        justify-content: center !important;
                        gap: 24px !important;
                        margin-left: auto !important;
                        margin-right: auto !important;
                    }
                    #urgent-lower-parent-container > div:first-child {
                        width: 678.5px !important;
                        flex-shrink: 0 !important;
                    }
                    #urgent-lower-parent-container > div:last-child {
                        width: 406px !important;
                        flex-shrink: 0 !important;
                    }
                    [data-tempo-ui="lower-selfcheck-streak"] {
                        align-self: auto !important;
                    }
                    [data-tempo-ui="urgent-posts"] {
                        width: 100% !important;
                        margin-left: 0 !important;
                        margin-right: 0 !important;
                    }
                }
            `;
        })()
    """)
    for w in [1440, 1280, 1200, 1024, 768, 375]:
        print(f"Viewport {w}px:", measure(w))

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
