# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile

CDP_PORT = 9495
user_data_dir = tempfile.mkdtemp(prefix='edge_test_approaches_')

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
                const pr = page.getBoundingClientRect();
                const pageCenter = pr.left + pr.width / 2;

                const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
                const comm = document.querySelector('[data-tempo-ui="urgent-posts"]');
                const sr = streak.getBoundingClientRect();
                const cr = comm.getBoundingClientRect();

                const groupLeft = Math.min(sr.left, cr.left);
                const groupRight = Math.max(sr.right, cr.right);
                const groupCenter = (groupLeft + groupRight) / 2;
                const offset = groupCenter - pageCenter;

                return {
                    pageLeft: pr.left,
                    pageRight: pr.right,
                    pageWidth: pr.width,
                    pageCenter: pageCenter,
                    groupLeft: groupLeft,
                    groupRight: groupRight,
                    groupWidth: groupWidth,
                    groupCenter: groupCenter,
                    offsetFromPageCenter: Math.round(offset * 100) / 100,
                    leftMarginToPage: Math.round((groupLeft - pr.left) * 100) / 100,
                    rightMarginToPage: Math.round((pr.right - groupRight) * 100) / 100,
                    streakWidth: sr.width,
                    commWidth: cr.width,
                    gap: Math.round((cr.left - sr.right) * 100) / 100
                };
            })()
        """)

    # TEST APPROACH 1: Parent container margin adjustment on desktop (lg:)
    print("=== APPROACH 1: Parent container margin adjustment ===")
    eval_js("""
        (function() {
            const container = document.querySelector('#urgent-rebuilt-section > div');
            // Since on desktop with max-w-[960px] mx-auto, the group offset is -59.25px.
            // Shifting the parent container on desktop via margin:
            // container.style.transform = 'translateX(59.25px)';
            // OR container.style.marginLeft = 'calc(auto + 59.25px)';
            // Let's test container.style.transform = 'translateX(59.25px)':
            container.style.transform = 'translateX(59.25px)';
        })()
    """)
    time.sleep(0.5)
    print("1440px:", json.dumps(measure(), indent=2))

    # TEST APPROACH 2: Setting parent container style without transform
    # What if container has:
    # margin: 0 auto;
    # But instead of transform, container's position / margin-left:
    eval_js("""
        (function() {
            const container = document.querySelector('#urgent-rebuilt-section > div');
            container.style.transform = '';
            container.style.position = 'relative';
            container.style.left = '59.25px';
        })()
    """)
    time.sleep(0.5)
    print("\n=== APPROACH 2: relative left 59.25px ===")
    print("1440px:", json.dumps(measure(), indent=2))

    # TEST APPROACH 3: Container centering the two columns via CSS Grid / Flex
    # What if the parent container is:
    # <div class="urgent-lower-group-container w-full mx-auto ...">
    # Where the two cards are naturally side by side with gap-6:
    eval_js("""
        (function() {
            const container = document.querySelector('#urgent-rebuilt-section > div');
            container.style.transform = '';
            container.style.position = '';
            container.style.left = '';

            // If the parent container has max-width: 1098.5px; margin: 0 auto;
            // and the two columns don't have artificial overflow:
            // Let's see: streakCard is 678.5px, commCard is 406px, gap is 14px (or 24px)
            // If the container is a flex container:
            container.className = "w-full mx-auto flex flex-col lg:flex-row items-center lg:items-start justify-center gap-5 lg:gap-6";
            container.style.maxWidth = "1108.5px";

            const streak = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
            streak.classList.remove('self-end');
            const comm = document.querySelector('[data-tempo-ui="urgent-posts"]');
            comm.style.width = '406px';
            comm.style.marginLeft = '0px';
            comm.style.marginRight = '0px';

            streak.parentElement.className = "w-full lg:w-[678.5px] shrink-0 flex flex-col space-y-4";
            comm.parentElement.className = "w-full lg:w-[406px] shrink-0 flex flex-col items-center";
        })()
    """)
    time.sleep(0.5)
    print("\n=== APPROACH 3: Natural flex container centered with mx-auto ===")
    print("1440px:", json.dumps(measure(), indent=2))

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
