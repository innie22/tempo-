# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile

CDP_PORT = 9494
user_data_dir = tempfile.mkdtemp(prefix='edge_test_container_')

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

    def test_setup(setup_js):
        eval_js(setup_js)
        results = {}
        for width in [1440, 1280, 1024, 768, 375]:
            send('Emulation.setDeviceMetricsOverride', {'width': width, 'height': 900, 'deviceScaleFactor': 1, 'mobile': (width < 768)})
            time.sleep(0.3)
            res = eval_js("""
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

                    // Check horizontal overflow
                    const bodyWidth = document.body.clientWidth;
                    const docOverflow = document.documentElement.scrollWidth > window.innerWidth;

                    return {
                        pageWidth: pr.width,
                        pageCenter: pageCenter,
                        groupLeft: groupLeft,
                        groupRight: groupRight,
                        groupWidth: groupRight - groupLeft,
                        groupCenter: groupCenter,
                        offsetFromPageCenter: Math.round((groupCenter - pageCenter) * 100) / 100,
                        streakWidth: Math.round(sr.width * 10) / 10,
                        commWidth: Math.round(cr.width * 10) / 10,
                        isTwoColumn: (cr.left >= sr.right - 2),
                        gap: Math.round((cr.left - sr.right) * 10) / 10,
                        hasOverflow: docOverflow
                    };
                })()
            """)
            results[f'{width}px'] = res
        return results

    # OPTION 1:
    # Notice: In the current HTML:
    # <div id="urgent-rebuilt-section" class="pt-8 border-t border-[#D0E0D7] mt-8 w-full" data-tempo-ui="urgent-lower-section">
    #     <div class="max-w-[960px] mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-5 lg:gap-6 items-start">
    # If we adjust only the parent container:
    # Notice: streak card has `w-full lg:w-[678.5px]`, comm card has `width: calc(100% + 20px); margin: 0 -10px;`.
    # In the current DOM, streak card was sticking out to the left by 128.5px because of `self-end`.
    # If the parent container is:
    # <div class="w-full flex flex-col lg:flex-row items-center lg:items-start justify-center gap-5 lg:gap-6 mx-auto" style="max-width: 1108.5px;">
    # And left column is <div class="w-full lg:w-[678.5px] shrink-0 ...">
    # And right column is <div class="w-full lg:w-[406px] shrink-0 ...">
    # Let's test this:
    print("--- TESTING OPTION 1: Responsive Flex Container ---")
    opt1_res = test_setup("""
        (function() {
            const section = document.getElementById('urgent-rebuilt-section');
            const streakCard = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
            streakCard.classList.remove('self-end');
            const commCard = document.querySelector('[data-tempo-ui="urgent-posts"]');
            commCard.style.width = '100%';
            commCard.style.marginLeft = '0px';
            commCard.style.marginRight = '0px';

            const streakParent = streakCard.parentElement;
            const commParent = commCard.parentElement;
            const gridContainer = streakParent.parentElement;

            gridContainer.className = "w-full mx-auto flex flex-col lg:flex-row items-center lg:items-start justify-center gap-5 lg:gap-6";
            gridContainer.style.maxWidth = "1108.5px";

            streakParent.className = "w-full lg:w-[678.5px] shrink-0 flex flex-col space-y-4";
            streakParent.style.maxWidth = "678.5px";

            commParent.className = "w-full lg:w-[406px] shrink-0 flex flex-col items-center";
            commParent.style.maxWidth = "406px";
        })()
    """)
    print(json.dumps(opt1_res, indent=2))

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
