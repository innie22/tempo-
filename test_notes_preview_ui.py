# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, base64, tempfile, os

CDP_PORT = 9485
artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'
user_data_dir = tempfile.mkdtemp(prefix='edge_test_notes_ui_')

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
            const uid = 'usr_alex_preview_test';
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

    def test_render(notes_data, filename):
        eval_js(f"""
            (function() {{
                const targetCard = document.querySelector('[data-tempo-ui="urmode-create-notes"]');
                if (!targetCard) return 'card not found';

                const notes = {json.dumps(notes_data)};
                let notesListHTML = '';
                if (!notes || notes.length === 0) {{
                    notesListHTML = `
                        <div class="h-full min-h-[78px] flex flex-col items-center justify-center text-center px-3 py-2 bg-[#FCF5F0]/70 border border-dashed border-[#E8D5CA] rounded-2xl select-none" data-tempo-ui="notes-empty-state">
                            <span class="text-base text-[#B87561] mb-0.5">📝</span>
                            <p class="text-xs font-semibold text-[#8C7D75]">No notes for today yet.</p>
                        </div>
                    `;
                }} else {{
                    notesListHTML = `
                        <div class="overflow-y-auto max-h-[96px] space-y-1.5 pr-1 text-left custom-scrollbar" data-tempo-ui="notes-scroll-list" style="max-height: 96px; overflow-y: auto;">
                            ${{notes.map(n => `
                                <div class="bg-white/90 hover:bg-white border border-[#EBDCD3] rounded-xl px-2.5 py-1.5 transition text-xs shadow-2xs group cursor-default" data-day-note-id="${{n.id}}">
                                    <div class="flex items-center justify-between gap-1 mb-0.5">
                                        <span class="text-[10px] font-bold uppercase tracking-wider text-[#B87561] flex items-center gap-1">
                                            <span>📝</span>
                                            <span>Day Note</span>
                                        </span>
                                        ${{n.time ? `<span class="text-[10px] text-[#9E9087] font-medium">${{n.time}}</span>` : ''}}
                                    </div>
                                    <p class="text-[11.5px] text-[#484541] font-medium leading-snug line-clamp-2 break-words">
                                        ${{n.text}}
                                    </p>
                                </div>
                            `).join('')}}
                        </div>
                    `;
                }}

                targetCard.outerHTML = `
                    <div class="w-full min-h-[122px] max-h-[122px] h-[122px] bg-[#F9E8E2] border border-[#E8D5CA] rounded-3xl p-3.5 sm:p-4 shadow-xs flex flex-row items-center justify-between box-border relative overflow-hidden" 
                         data-tempo-ui="urmode-create-notes" 
                         style="width: 100%; height: 122px; min-height: 122px; max-height: 122px; box-sizing: border-box;">
                        <!-- Left: Title & View Button -->
                        <div class="flex flex-col justify-between shrink-0 space-y-2 pr-3 sm:pr-4 border-r border-[#E8D5CA]/70" data-tempo-ui="notes-text-block" style="min-width: 120px; max-width: 135px;">
                            <h3 class="text-lg sm:text-xl font-bold text-[#554741] leading-tight tracking-tight">
                                Create Notes
                            </h3>
                            <div>
                                <button type="button"
                                        onclick="if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {{ window.TempoApp.navigateTo('notes'); }} else {{ window.location.hash = '#notes'; }}"
                                        class="px-3 py-1.5 rounded-xl font-bold text-xs bg-[#C88E7D] hover:bg-[#B97F6E] text-white shadow-2xs transition cursor-pointer inline-flex items-center justify-center whitespace-nowrap">
                                    View my notes
                                </button>
                            </div>
                        </div>

                        <!-- Right: Today's Day Notes List (Scrollable) -->
                        <div class="flex-1 min-w-0 pl-3 sm:pl-4 h-full flex flex-col justify-center" data-tempo-ui="notes-list-container">
                            ${{notesListHTML}}
                        </div>
                    </div>
                `;
            }})()
        """)
        time.sleep(0.5)

        clip_rc = eval_js("""
            (function() {
                const rightCol = document.querySelector('.urgent-right-col');
                const r = rightCol.getBoundingClientRect();
                return {
                    x: Math.max(0, r.x - 20),
                    y: Math.max(0, r.y - 20),
                    width: r.width + 40,
                    height: Math.min(800, r.height + 40),
                    scale: 1
                };
            })()
        """)
        if clip_rc:
            res = send('Page.captureScreenshot', {'format': 'png', 'clip': clip_rc})
            data = base64.b64decode(res['data'])
            filepath = os.path.join(artifact_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(data)
            print(f"Captured {filename} ({len(data)} bytes)")

    # 1. Test Empty State
    print("Testing Empty State...")
    test_render([], 'urmode_preview_empty_state.png')

    # 2. Test Populated State (2 notes)
    print("Testing Populated State (2 notes)...")
    test_render([
        {"id": "dn_1", "text": "Drink more water and step outside for 5 mins.", "time": "10:30 AM"},
        {"id": "dn_2", "text": "Review formulas for the afternoon session.", "time": "02:15 PM"}
    ], 'urmode_preview_populated_2notes.png')

    # 3. Test Scrollable State (4 notes)
    print("Testing Scrollable State (4 notes)...")
    test_render([
        {"id": "dn_1", "text": "Drink more water and step outside for 5 mins.", "time": "10:30 AM"},
        {"id": "dn_2", "text": "Review formulas for the afternoon session.", "time": "02:15 PM"},
        {"id": "dn_3", "text": "Remember to submit lab report before 5 PM.", "time": "03:45 PM"},
        {"id": "dn_4", "text": "Evening reflection: 3 priority tasks finished.", "time": "05:00 PM"}
    ], 'urmode_preview_scrollable_4notes.png')

finally:
    try: ws.close()
    except: pass
    try: proc.terminate()
    except: pass
