# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, base64, tempfile, os

CDP_PORT = 9490
artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'
user_data_dir = tempfile.mkdtemp(prefix='edge_verify_community_')

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
    time.sleep(2)

    # 1. Inspect Community Container Dimensions
    dims = eval_js("""
        (function() {
            const el = document.querySelector('[data-tempo-ui="urgent-posts"]');
            if (!el) return { found: false };
            const r = el.getBoundingClientRect();
            const parent = el.parentElement;
            const pr = parent.getBoundingClientRect();
            const postsList = el.querySelector('#urgent-community-posts-list');
            const plr = postsList ? postsList.getBoundingClientRect() : null;

            return {
                found: true,
                width: r.width,
                height: r.height,
                left: r.left,
                right: r.right,
                center: r.left + r.width / 2,
                parentWidth: pr.width,
                parentCenter: pr.left + pr.width / 2,
                diffFromBase386: r.width - 386,
                centerOffset: (r.left + r.width / 2) - (pr.left + pr.width / 2),
                postsListWidth: plr ? plr.width : null
            };
        })()
    """)

    print("Dimensions Check:", json.dumps(dims, indent=2))
    assert dims['found'] == True, "Community container not found"
    assert abs(dims['diffFromBase386'] - 20) < 0.1, f"Expected +20px increase, got {dims['diffFromBase386']}"
    assert abs(dims['centerOffset']) < 0.1, f"Expected horizontal centering, got offset {dims['centerOffset']}"
    assert abs(dims['width'] - 406) < 0.1, f"Expected 406px width, got {dims['width']}"

    # 2. Scroll into view and capture close-up of Community container
    eval_js("""
        (function() {
            const el = document.querySelector('[data-tempo-ui="urgent-posts"]');
            if (el) el.scrollIntoView({ behavior: 'instant', block: 'center' });
        })()
    """)
    time.sleep(0.5)

    clip_community = eval_js("""
        (function() {
            const el = document.querySelector('[data-tempo-ui="urgent-posts"]');
            const r = el.getBoundingClientRect();
            return { x: Math.max(0, r.left - 20), y: Math.max(0, r.top - 20), width: r.width + 40, height: r.height + 40, scale: 1 };
        })()
    """)
    shot_community = send('Page.captureScreenshot', {'clip': clip_community})
    with open(os.path.join(artifact_dir, 'urmode_community_container_plus20px.png'), 'wb') as f:
        f.write(base64.b64decode(shot_community['data']))
    print("Saved: urmode_community_container_plus20px.png")

    # 3. Capture overview of lower section (Streak Card + Community Container)
    clip_section = eval_js("""
        (function() {
            const el = document.querySelector('#urgent-rebuilt-section');
            const r = el.getBoundingClientRect();
            return { x: Math.max(0, r.left - 10), y: Math.max(0, r.top - 10), width: r.width + 20, height: r.height + 20, scale: 1 };
        })()
    """)
    shot_section = send('Page.captureScreenshot', {'clip': clip_section})
    with open(os.path.join(artifact_dir, 'urmode_lower_section_community_plus20px.png'), 'wb') as f:
        f.write(base64.b64decode(shot_section['data']))
    print("Saved: urmode_lower_section_community_plus20px.png")

    # 4. Verify Rmode intactness
    print("Verifying Rmode is intact...")
    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(1)
    rmode_ok = eval_js("!!document.querySelector('#rmode-home-content') && !document.querySelector('#rmode-home-content').classList.contains('hidden')")
    assert rmode_ok == True, "Rmode is not intact"

    shot_rmode = send('Page.captureScreenshot', {})
    with open(os.path.join(artifact_dir, 'rmode_verified_intact_community_task.png'), 'wb') as f:
        f.write(base64.b64decode(shot_rmode['data']))
    print("Saved: rmode_verified_intact_community_task.png")

    # 5. Verify EntryHome intactness
    print("Verifying EntryHome is intact...")
    eval_js("window.TempoMode.setMode('default');")
    time.sleep(1)
    dmode_ok = eval_js("!!document.querySelector('#dmode-home-content') && !document.querySelector('#dmode-home-content').classList.contains('hidden')")
    assert dmode_ok == True, "EntryHome is not intact"

    shot_dmode = send('Page.captureScreenshot', {})
    with open(os.path.join(artifact_dir, 'entryhome_verified_intact_community_task.png'), 'wb') as f:
        f.write(base64.b64decode(shot_dmode['data']))
    print("Saved: entryhome_verified_intact_community_task.png")

    print("\nALL VERIFICATIONS PASSED WITH 100% SUCCESS!")

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
