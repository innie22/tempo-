# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, base64, tempfile, os

CDP_PORT = 9494
artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'
user_data_dir = tempfile.mkdtemp(prefix='edge_test_resp_')

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

    def eval_js(expr, await_promise=False):
        params = {'expression': expr, 'returnByValue': True}
        if await_promise:
            params['awaitPromise'] = True
        res = send('Runtime.evaluate', params)
        if 'exceptionDetails' in res.get('result', {}):
            raise Exception(f"JS Exception: {res['result']['exceptionDetails']}")
        return res.get('result', {}).get('value')

    for _ in range(30):
        val = eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoAuth !== 'undefined'")
        if val:
            break
        time.sleep(0.5)

    eval_js("""
        (async function() {
            const uid = 'usr_alex_resp_test';
            localStorage.clear();
            const mockAccount = {
                id: uid,
                email: 'student@tempo.app',
                password: 'password123',
                full_name: 'Alex Rivera',
                role: 'student',
                user_metadata: { full_name: 'Alex Rivera', role: 'student' }
            };
            localStorage.setItem('tempo_mock_account_student@tempo.app', JSON.stringify(mockAccount));
            localStorage.setItem('tempo_local_dev_user', JSON.stringify(mockAccount));
            localStorage.setItem('tempo_user_role', 'student');
            localStorage.setItem('tempo_active_mode', 'emergency');
            localStorage.setItem('tempo_originating_mode', 'emergency');

            if (window.TempoAuth && typeof window.TempoAuth.signIn === 'function') {
                await window.TempoAuth.signIn('student@tempo.app', 'password123');
            }
            if (window.TempoAuth && typeof window.TempoAuth.closeAllAuthModals === 'function') window.TempoAuth.closeAllAuthModals();
            document.querySelectorAll('.auth-modal-overlay').forEach(m => m.classList.add('hidden'));

            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') window.TempoMode.setMode('emergency');
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') window.TempoApp.navigateTo('today');
        })()
    """, await_promise=True)
    time.sleep(2)

    def inject_card():
        eval_js("""
            (function() {
                const noteCard = document.querySelector('[data-tempo-ui="dashboard-note-card"]');
                const noteSection = noteCard ? noteCard.closest('.space-y-1\\\\.5') || noteCard.parentElement : null;
                const existingCard = document.querySelector('[data-tempo-ui="lower-create-notes"]');
                if (existingCard) existingCard.remove();
                
                let targetEl = document.querySelector('[data-tempo-ui="urmode-create-notes"]');
                if (!targetEl && noteSection) {
                    targetEl = document.createElement('div');
                    noteSection.replaceWith(targetEl);
                }
                if (targetEl) {
                    targetEl.outerHTML = `
                        <div class="w-full min-h-[122px] max-h-[122px] h-[122px] bg-[#F9E8E2] border border-[#E8D5CA] rounded-3xl px-4 sm:px-5 py-2.5 shadow-xs flex items-center justify-start box-border relative overflow-visible" 
                             data-tempo-ui="urmode-create-notes" 
                             style="width: 100%; height: 122px; min-height: 122px; max-height: 122px; box-sizing: border-box; overflow: visible;">
                            <div class="flex flex-col justify-between space-y-2.5 shrink-0" data-tempo-ui="notes-text-block">
                                <h3 class="text-xl sm:text-[22px] font-bold text-[#554741] leading-tight">
                                    Create Notes
                                </h3>
                                <div>
                                    <button type="button"
                                            onclick="if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('notes'); } else { window.location.hash = '#notes'; }"
                                            class="px-4 py-2 rounded-xl font-bold text-xs bg-[#C88E7D] hover:bg-[#B97F6E] text-white shadow-2xs transition cursor-pointer inline-flex items-center justify-center">
                                        View my notes
                                    </button>
                                </div>
                            </div>

                            <div class="shrink-0 select-none flex items-center justify-center relative overflow-visible" 
                                 data-tempo-ui="notes-mascot-container"
                                 style="margin-left: 5px; margin-right: 0px; overflow: visible;">
                                <img src="assets/create-notes-mascot.png" 
                                     alt="Create Notes Mascot" 
                                     class="object-contain drop-shadow-2xs select-none pointer-events-none" 
                                     style="height: 120px; width: auto; max-height: none; max-width: none; display: block;" />
                            </div>

                            <button type="button"
                                    onclick="if (window.TempoTools && typeof window.TempoTools.openNotes === 'function') { window.TempoTools.openNotes(); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('notes'); } else { window.location.hash = '#notes'; }"
                                    class="bg-[#FEFAF4] hover:bg-white border border-[#EAE4DF] rounded-2xl h-18 sm:h-20 w-18 sm:w-20 md:w-20 flex items-center justify-center transition cursor-pointer group shadow-2xs shrink-0"
                                    style="margin-left: auto; width: 80px; min-width: 60px;"
                                    title="Create a new note"
                                    aria-label="Create a new note">
                                <span class="text-2xl sm:text-3xl font-light text-[#8C8782] group-hover:text-[#5A5550] transition">+</span>
                            </button>
                        </div>
                    `;
                }
            })()
        """)

    # Test Mobile 375px
    send('Emulation.setDeviceMetricsOverride', {'width': 375, 'height': 812, 'deviceScaleFactor': 1, 'mobile': True})
    time.sleep(1)
    inject_card()
    resMobile = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="urmode-create-notes"]');
            const r = card.getBoundingClientRect();
            const textBlock = card.querySelector('[data-tempo-ui="notes-text-block"]').getBoundingClientRect();
            const mascot = card.querySelector('img[src*="create-notes-mascot.png"]').getBoundingClientRect();
            const plus = card.querySelector('button[aria-label="Create a new note"]').getBoundingClientRect();
            return {
                card: { w: r.width, h: r.height },
                gapTextMascot: mascot.left - textBlock.right,
                mascot: { w: mascot.width, h: mascot.height },
                plus: { w: plus.width, h: plus.height },
                overflowX: document.documentElement.scrollWidth > window.innerWidth
            };
        })()
    """)
    print("Mobile 375px:", json.dumps(resMobile, indent=2))

    res = send('Page.captureScreenshot', {'format': 'png'})
    with open(os.path.join(artifact_dir, 'urmode_mobile_375px.png'), 'wb') as f:
        f.write(base64.b64decode(res['data']))

finally:
    try: ws.close()
    except: pass
    try: proc.terminate()
    except: pass
