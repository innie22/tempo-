# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys

sys.stdout.reconfigure(encoding='utf-8')
CDP_PORT = 9558
user_data_dir = tempfile.mkdtemp(prefix='edge_proto_test_')

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
    time.sleep(2.0)
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
            raise Exception('JS Exception: ' + str(res['result']['exceptionDetails']))
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
                profile: { id: 'mock-user-alex', full_name: 'Innietest', display_name: 'Innietest', role: 'student' }
            };
            localStorage.setItem('tempo_mock_account_' + email, JSON.stringify(mock));
            if (window.TempoAuth) {
                await window.TempoAuth.signIn(email, 'password123');
            }
            
            localStorage.setItem('tempo_active_mode', 'recovery');
            localStorage.setItem('tempo_originating_mode', 'recovery');
            
            if (window.TempoMode) {
                window.TempoMode.transitionContext('recovery', { skipSetupCheck: true });
                window.TempoMode.renderRmodeHome();
            }
        })()
    """)
    time.sleep(1.0)

    # Prototype update
    eval_js("""
        (function() {
            const leftCol = document.querySelector('.recovery-left-col');
            const header = document.querySelector('.recovery-mode-header');
            const greeting = document.querySelector('.recovery-greeting');
            
            // Replace header and greeting with combined row
            header.className = 'relative recovery-mode-header pb-0';
            header.innerHTML = `
                <div class="flex items-center gap-[10px] flex-wrap sm:flex-nowrap" data-tempo-ui="recovery-header-row">
                    <!-- Anchored Mode Selector Dropdown -->
                    <div id="home-mode-selector-wrapper" class="relative inline-block text-left shrink-0">
                        <button id="btn-home-mode-selector" 
                                type="button" 
                                data-tempo-ui="mode-selector-btn"
                                onclick="window.TempoMode.toggleModeDropdown(event)" 
                                class="px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#EDF7F1] text-[#166545] hover:bg-[#DDF0E5] border border-[#CDE9DA] transition flex items-center space-x-1.5 shadow-xs cursor-pointer"
                                aria-haspopup="true"
                                aria-expanded="false"
                                title="Switch Tempo Mode">
                            <span>🌱</span>
                            <span class="font-extrabold">${window.t ? window.t('modes.recovery.name', {}, 'Recovery Mode') : 'Recovery Mode'}</span>
                            <span class="text-[10px] ml-0.5 opacity-80">▾</span>
                        </button>
                        <div id="home-mode-selector-dropdown" class="hidden absolute left-0 mt-2 w-72 sm:w-80 bg-white rounded-2xl shadow-xl border border-[#EAE4DF] z-50 overflow-hidden" role="menu"></div>
                    </div>

                    <!-- Greeting (Terracotta #D48366) -->
                    <div class="recovery-greeting pb-0 pt-0" style="margin-top: 0 !important; margin-bottom: 0 !important;">
                        <h2 class="text-[29px] sm:text-[33px] font-extrabold text-[#D48366] tracking-tight flex items-center space-x-2.5 whitespace-nowrap leading-none" style="font-size: 33px; line-height: 1;">
                            <span class="text-3xl select-none">👋</span>
                            <span>Hi Innietest, how are you today?</span>
                        </h2>
                    </div>
                </div>
            `;
            if (greeting) {
                greeting.remove();
            }
            if (window.TempoMode && typeof window.TempoMode.syncRmodeSelfCheckAlignment === 'function') {
                window.TempoMode.syncRmodeSelfCheckAlignment();
            }
        })()
    """)
    time.sleep(0.5)

    metrics = eval_js("""
        (function() {
            const btn = document.getElementById('btn-home-mode-selector');
            const h2 = document.querySelector('.recovery-greeting h2');
            const sc = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            const rc = document.querySelector('[data-tempo-ui="recovery-recently"]');

            const bR = btn.getBoundingClientRect();
            const hR = h2.getBoundingClientRect();
            const scR = sc.getBoundingClientRect();
            const rcR = rc.getBoundingClientRect();

            const csH2 = window.getComputedStyle(h2);

            return {
                btn: { left: bR.left, right: bR.right, top: bR.top, bottom: bR.bottom, height: bR.height, centerY: (bR.top + bR.bottom)/2 },
                greeting: { left: hR.left, right: hR.right, top: hR.top, bottom: hR.bottom, height: hR.height, centerY: (hR.top + hR.bottom)/2, fontSize: csH2.fontSize },
                horizontalGap: Math.round((hR.left - bR.right) * 10) / 10,
                centerYDiff: Math.abs(((hR.top + hR.bottom)/2) - ((bR.top + bR.bottom)/2)),
                selfCheckTop: scR.top,
                recentlyTop: rcR.top,
                alignmentDiff: Math.abs(rcR.top - scR.top)
            };
        })()
    """)
    print("PROTOTYPE METRICS:", json.dumps(metrics, indent=2))

    # Test dropdown click
    dropdown_status = eval_js("""
        (function() {
            const btn = document.getElementById('btn-home-mode-selector');
            btn.click();
            const dd = document.getElementById('home-mode-selector-dropdown');
            return {
                isExpanded: btn.getAttribute('aria-expanded'),
                dropdownHidden: dd.classList.contains('hidden'),
                dropdownChildCount: dd.children.length
            };
        })()
    """)
    print("DROPDOWN STATUS:", json.dumps(dropdown_status, indent=2))

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
