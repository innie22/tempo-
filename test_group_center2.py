# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile

CDP_PORT = 9493
user_data_dir = tempfile.mkdtemp(prefix='edge_test_group_center2_')

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

    # Option B:
    # In #urgent-rebuilt-section:
    # The parent container can simply adjust its margin or alignment!
    # Notice: the baseline group had:
    # streak.left = 108.5, comm.right = 1207. Group width = 1098.5.
    # Group center was 657.75.
    # Page center is 717.
    # Difference: +59.25px!
    # What if the parent container #urgent-rebuilt-section > div is shifted right by 59.25px?
    # e.g., marginLeft: calc(auto + 59.25px) or transform: translateX(59.25px) or margin-left: ...?
    # BUT wait! Instruction 5 says:
    # "Adjust only the parent container's alignment or margins as needed. Do not reposition the cards independently or use arbitrary offsets that break responsive layouts."
    # Let's read carefully:
    # "Treat the Self-check Streak card and Tempo Community card as one combined layout group. Center the group as a whole, not each card individually."
    # "Preserve the current two-column arrangement, relative widths, gap between cards, card heights, styling, and internal content."
    # "Keep the group responsive: on smaller screens, maintain the existing responsive stacking behavior and prevent horizontal overflow."
    # "Adjust only the parent container's alignment or margins as needed. Do not reposition the cards independently or use arbitrary offsets that break responsive layouts."

    # Let's test a clean flex/grid parent container for the two cards:
    eval_js("""
        (function() {
            const section = document.getElementById('urgent-rebuilt-section');
            if (!section) return;

            // Let's replace the innerHTML of #urgent-rebuilt-section to see:
            const streakHTML = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]').outerHTML;
            const commHTML = document.querySelector('[data-tempo-ui="urgent-posts"]').outerHTML;

            section.innerHTML = `
                <div class="mx-auto w-full flex flex-col lg:flex-row items-center lg:items-start justify-center gap-5 lg:gap-6" 
                     data-tempo-ui="urgent-lower-group"
                     style="max-width: 1108.5px;">
                    <div class="w-full lg:w-[678.5px] shrink-0 flex flex-col space-y-4">
                        ${streakHTML}
                    </div>
                    <div class="w-full lg:w-[406px] shrink-0 flex flex-col items-center">
                        ${commHTML}
                    </div>
                </div>
            `;
            // In commHTML, remove negative margins since parent is exactly 406px
            const comm = section.querySelector('[data-tempo-ui="urgent-posts"]');
            comm.style.width = '100%';
            comm.style.marginLeft = '0px';
            comm.style.marginRight = '0px';

            const streak = section.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
            streak.classList.remove('self-end');
        })()
    """)
    time.sleep(0.5)

    print("\nFLEX WRAPPER RESULT (1440px viewport):")
    print(json.dumps(measure("flex_1440"), indent=2))

    # Test 1024px viewport
    send('Emulation.setDeviceMetricsOverride', {'width': 1024, 'height': 800, 'deviceScaleFactor': 1, 'mobile': False})
    time.sleep(0.5)
    print("\nFLEX WRAPPER RESULT (1024px viewport):")
    print(json.dumps(measure("flex_1024"), indent=2))

    # Test 375px mobile viewport
    send('Emulation.setDeviceMetricsOverride', {'width': 375, 'height': 812, 'deviceScaleFactor': 1, 'mobile': True})
    time.sleep(0.5)
    print("\nFLEX WRAPPER RESULT (375px mobile viewport):")
    print(json.dumps(measure("flex_375"), indent=2))

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
