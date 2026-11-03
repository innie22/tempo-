# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys

sys.stdout.reconfigure(encoding='utf-8')
CDP_PORT = 9565
user_data_dir = tempfile.mkdtemp(prefix='edge_reposition_proto_')

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
            localStorage.setItem('tempo_lang', 'en');
            const email = 'alex.chen@university.edu';
            const mock = {
                id: 'mock-user-alex',
                email: email,
                password: 'password123',
                profile: { id: 'mock-user-alex', full_name: 'Innietest', display_name: 'Innietest', role: 'student' }
            };
            localStorage.setItem('tempo_mock_account_' + email, JSON.stringify(mock));
            localStorage.setItem('tempo_recovery_intro_dismissed', 'true');
            if (window.TempoAuth) {
                await window.TempoAuth.signIn(email, 'password123');
            }
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('en');
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

    # Prototype:
    # 1. Mode button:
    #    - Remove tree/sprout symbol
    #    - Height increases by 10px (30px -> 40px)
    #    - Width increases proportionally (4/3 ratio)
    # 2. Greeting:
    #    - Placed directly below the button
    #    - Vertical gap: exactly 10px
    #    - Left aligned with button
    #    - Font size: 33px desktop / 29px mobile, terracotta #D48366
    eval_js("""
        (function() {
            const header = document.querySelector('.recovery-mode-header');
            if (!header) return;

            // Original rendered button dimensions before sprout removal:
            // Height = 30px, Width in EN = 155.75px. Ratio = 155.75 / 30 = 5.19167
            // New height = 40px. New proportional width = 40 * (155.75 / 30) = 207.67px
            const origW = 155.75;
            const origH = 30;
            const newH = origH + 10; // 40px
            const newW = Math.round(origW * (newH / origH) * 100) / 100; // 207.67px

            header.className = 'relative recovery-mode-header pb-0';
            header.innerHTML = `
                <div class="flex flex-col items-start" data-tempo-ui="recovery-header-stack" style="gap: 10px;">
                    <!-- Anchored Mode Selector Dropdown -->
                    <div id="home-mode-selector-wrapper" class="relative inline-block text-left shrink-0">
                        <button id="btn-home-mode-selector" 
                                type="button" 
                                data-tempo-ui="mode-selector-btn"
                                onclick="window.TempoMode.toggleModeDropdown(event)" 
                                class="rounded-full text-xs font-bold bg-[#EDF7F1] text-[#166545] hover:bg-[#DDF0E5] border border-[#CDE9DA] transition inline-flex items-center justify-center space-x-1.5 shadow-xs cursor-pointer"
                                style="height: 40px; width: ${newW}px; padding: 0 16px;"
                                aria-haspopup="true"
                                aria-expanded="false"
                                title="Switch Tempo Mode">
                            <span class="font-extrabold">${window.t ? window.t('modes.recovery.name', {}, 'Recovery Mode') : 'Recovery Mode'}</span>
                            <span class="text-[10px] ml-0.5 opacity-80">▾</span>
                        </button>
                        <div id="home-mode-selector-dropdown" class="hidden absolute left-0 mt-2 w-72 sm:w-80 bg-white rounded-2xl shadow-xl border border-[#EAE4DF] z-50 overflow-hidden" role="menu"></div>
                    </div>

                    <!-- Greeting (Terracotta #D48366) directly below Mode button -->
                    <div class="recovery-greeting pb-0 pt-0" style="margin: 0 !important; padding: 0 !important;">
                        <h2 class="text-[29px] sm:text-[33px] font-extrabold text-[#D48366] tracking-tight flex items-center space-x-2.5 whitespace-normal sm:whitespace-nowrap leading-none" style="line-height: 1; margin: 0 !important;">
                            <span class="text-3xl select-none leading-none">👋</span>
                            <span class="leading-none">Hi Innietest, how are you today?</span>
                        </h2>
                    </div>
                </div>
            `;

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
            const csBtn = window.getComputedStyle(btn);

            return {
                btnText: btn.innerText.replace(/\\s+/g, ' ').trim(),
                greetingText: h2.innerText.replace(/\\s+/g, ' ').trim(),
                hasSproutSymbol: btn.innerText.includes('🌱'),
                btn: {
                    left: bR.left,
                    right: bR.right,
                    top: bR.top,
                    bottom: bR.bottom,
                    width: bR.width,
                    height: bR.height
                },
                greeting: {
                    left: hR.left,
                    right: hR.right,
                    top: hR.top,
                    bottom: hR.bottom,
                    width: hR.width,
                    height: hR.height,
                    fontSize: csH2.fontSize
                },
                verticalGap: Math.round((hR.top - bR.bottom) * 10) / 10,
                leftAlignmentDiff: Math.abs(hR.left - bR.left),
                heightIncrease: bR.height - 30,
                widthProportion: bR.width / 155.75,
                heightProportion: bR.height / 30,
                aspectRatio: bR.width / bR.height,
                selfCheckTop: scR.top,
                recentlyTop: rcR.top,
                cardsAlignmentDiff: Math.abs(rcR.top - scR.top)
            };
        })()
    """)
    print("PROTOTYPE RESULTS:")
    print(json.dumps(metrics, indent=2))

    # Capture screenshot
    shot = send('Page.captureScreenshot', {'format': 'png'})
    import base64
    with open(r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\scratch\proto_stacked_header.png', 'wb') as f:
        f.write(base64.b64decode(shot['data']))
    print('Screenshot saved: proto_stacked_header.png')

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
