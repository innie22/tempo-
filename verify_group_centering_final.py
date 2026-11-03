# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys, os, base64

sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
CDP_PORT = 9505
user_data_dir = tempfile.mkdtemp(prefix='edge_verify_final_')

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

    def capture_screenshot(filename, clip=None):
        params = {'format': 'png'}
        if clip:
            params['clip'] = clip
        res = send('Page.captureScreenshot', params)
        data = base64.b64decode(res['data'])
        out_path = os.path.join(ARTIFACT_DIR, filename)
        with open(out_path, 'wb') as f:
            f.write(data)
        print(f"Captured screenshot: {filename}")
        return out_path

    # Wait for app readiness
    for _ in range(30):
        val = eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'")
        if val:
            break
        time.sleep(0.5)

    # 1. Switch to Emergency Mode (URmode)
    eval_js("""
        (async function() {
            localStorage.setItem('tempo_active_mode', 'emergency');
            localStorage.setItem('tempo_originating_mode', 'emergency');
            if (window.TempoMode) window.TempoMode.setMode('emergency');
            if (window.TempoApp) window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1.5)

    def measure_group():
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
                const isTwoCol = (cr.left >= sr.right - 2);

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
                    isTwoCol: isTwoCol,
                    hasOverflow: docOverflow,
                    streakRect: { x: sr.x, y: sr.y, width: sr.width, height: sr.height },
                    commRect: { x: cr.x, y: cr.y, width: cr.width, height: cr.height },
                    groupBounds: { x: groupLeft, y: Math.min(sr.top, cr.top), width: groupWidth, height: Math.max(sr.bottom, cr.bottom) - Math.min(sr.top, cr.top) }
                };
            })()
        """)

    print("=== MEASURING URMODE AT VIEWPORTS ===")
    results = {}
    for w in [1440, 1280, 1024, 768, 375]:
        send('Emulation.setDeviceMetricsOverride', {'width': w, 'height': 1100, 'deviceScaleFactor': 1, 'mobile': (w < 768)})
        time.sleep(0.3)
        m = measure_group()
        results[f'{w}px'] = m
        print(f"\n--- Viewport {w}px ---")
        print(f"Page Center: {m['pageCenter']}px, Group Center: {m['groupCenter']}px, Offset: {m['offsetFromPageCenter']}px")
        print(f"Left Margin to Shell: {m['leftMarginToPage']}px, Right Margin to Shell: {m['rightMarginToPage']}px")
        print(f"Streak Card: {m['streakWidth']}px x {m['streakHeight']}px")
        print(f"Community Card: {m['commWidth']}px x {m['commHeight']}px")
        print(f"Gap: {m['gap']}px, Two Column: {m['isTwoCol']}, Horizontal Overflow: {m['hasOverflow']}")

    # Capture screenshots
    # 1. Desktop 1440px
    send('Emulation.setDeviceMetricsOverride', {'width': 1440, 'height': 1100, 'deviceScaleFactor': 1, 'mobile': False})
    time.sleep(0.5)

    # Scroll to lower section
    eval_js("""
        (function() {
            const sec = document.getElementById('urgent-rebuilt-section');
            if (sec) sec.scrollIntoView({ behavior: 'instant', block: 'center' });
        })()
    """)
    time.sleep(0.5)

    m1440 = results['1440px']
    gb = m1440['groupBounds']
    capture_screenshot('urmode_centered_group_desktop_1440.png', clip={
        'x': max(0, gb['x'] - 50),
        'y': max(0, gb['y'] - 40),
        'width': gb['width'] + 100,
        'height': gb['height'] + 80,
        'scale': 1
    })

    # Full page screenshot at 1440px
    capture_screenshot('urmode_full_page_desktop_1440.png')

    # Mobile 375px
    send('Emulation.setDeviceMetricsOverride', {'width': 375, 'height': 900, 'deviceScaleFactor': 1, 'mobile': True})
    time.sleep(0.5)
    eval_js("""
        (function() {
            const sec = document.getElementById('urgent-rebuilt-section');
            if (sec) sec.scrollIntoView({ behavior: 'instant', block: 'start' });
        })()
    """)
    time.sleep(0.5)
    capture_screenshot('urmode_stacked_group_mobile_375.png')

    # Verify Rmode is completely untouched
    send('Emulation.setDeviceMetricsOverride', {'width': 1440, 'height': 1100, 'deviceScaleFactor': 1, 'mobile': False})
    time.sleep(0.3)
    eval_js("""
        (async function() {
            if (window.TempoMode) window.TempoMode.setMode('recovery');
            if (window.TempoApp) window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1.0)
    rmode_intact = eval_js("""
        (function() {
            const rbox = document.getElementById('rmode-home-content');
            return rbox && !rbox.classList.contains('hidden') && rbox.children.length > 0;
        })()
    """)
    print(f"\nRmode intact and active: {rmode_intact}")
    capture_screenshot('rmode_verified_intact_group_centering_task.png')

    # Verify EntryHome is completely untouched
    eval_js("""
        (async function() {
            if (window.TempoMode) window.TempoMode.setMode('default');
            if (window.TempoApp) window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1.0)
    entryhome_intact = eval_js("""
        (function() {
            const dbox = document.getElementById('dmode-home-content');
            return dbox && !dbox.classList.contains('hidden') && dbox.children.length > 0;
        })()
    """)
    print(f"EntryHome intact and active: {entryhome_intact}")
    capture_screenshot('entryhome_verified_intact_group_centering_task.png')

    # Summary assert
    assert results['1440px']['offsetFromPageCenter'] == 0, f"Offset at 1440px was {results['1440px']['offsetFromPageCenter']}"
    assert results['1280px']['offsetFromPageCenter'] == 0, f"Offset at 1280px was {results['1280px']['offsetFromPageCenter']}"
    assert results['1440px']['leftMarginToPage'] == results['1440px']['rightMarginToPage'], "Margins not symmetrical at 1440px"
    assert results['1280px']['leftMarginToPage'] == results['1280px']['rightMarginToPage'], "Margins not symmetrical at 1280px"
    assert results['768px']['hasOverflow'] is False, "Horizontal overflow at 768px"
    assert results['375px']['hasOverflow'] is False, "Horizontal overflow at 375px"
    assert rmode_intact, "Rmode was affected"
    assert entryhome_intact, "EntryHome was affected"

    print("\nALL ASSERTIONS PASSED SUCCESSFULLY!")

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
