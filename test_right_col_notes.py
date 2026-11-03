# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, base64, tempfile, os

CDP_PORT = 9496
artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'
user_data_dir = tempfile.mkdtemp(prefix='edge_test_rc_')

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
            const uid = 'usr_alex_rc_test';
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

    # Now let's inject Create Notes card into rightCol replacing noteCard
    metrics = eval_js("""
        (function() {
            const noteCard = document.querySelector('[data-tempo-ui="dashboard-note-card"]');
            const noteSection = noteCard ? noteCard.closest('.space-y-1\\\\.5') || noteCard.parentElement : null;
            if (!noteSection) return { error: 'noteSection not found' };

            const createNotesCardHTML = `
                <div class="w-full min-h-[122px] max-h-[122px] h-[122px] bg-[#F9E8E2] border border-[#E8D5CA] rounded-3xl px-4 sm:px-5 py-2.5 shadow-xs flex items-center justify-start box-border relative overflow-visible" 
                     data-tempo-ui="urmode-create-notes" 
                     style="width: 100%; height: 122px; min-height: 122px; max-height: 122px; box-sizing: border-box; overflow: visible;">
                    <!-- Left: Title & View Button -->
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

                    <!-- Middle: Supplied Notes Mascot Asset with exactly 5px horizontal gap and 120px height (+20px) allowing transparent overflow -->
                    <div class="shrink-0 select-none flex items-center justify-center relative overflow-visible" 
                         data-tempo-ui="notes-mascot-container"
                         style="margin-left: 5px; margin-right: 0px; overflow: visible;">
                        <img src="assets/create-notes-mascot.png" 
                             alt="Create Notes Mascot" 
                             class="object-contain drop-shadow-2xs select-none pointer-events-none" 
                             style="height: 120px; width: auto; max-height: none; max-width: none; display: block;" />
                    </div>

                    <!-- Right: White Card with Plus Symbol -->
                    <button type="button"
                            onclick="if (window.TempoTools && typeof window.TempoTools.openNotes === 'function') { window.TempoTools.openNotes(); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('notes'); } else { window.location.hash = '#notes'; }"
                            class="bg-[#FEFAF4] hover:bg-white border border-[#EAE4DF] rounded-2xl h-18 sm:h-20 w-20 sm:w-24 md:w-28 flex items-center justify-center transition cursor-pointer group shadow-2xs shrink-0"
                            style="margin-left: auto;"
                            title="Create a new note"
                            aria-label="Create a new note">
                        <span class="text-2xl sm:text-3xl font-light text-[#8C8782] group-hover:text-[#5A5550] transition">+</span>
                    </button>
                </div>
            `;

            noteSection.outerHTML = createNotesCardHTML;

            // Also remove lower create notes card if exists
            const lowerNotes = document.querySelector('[data-tempo-ui="lower-create-notes"]');
            if (lowerNotes) lowerNotes.remove();

            const card = document.querySelector('[data-tempo-ui="urmode-create-notes"]');
            const rightCol = document.querySelector('.urgent-right-col');
            const planCard = document.querySelector('.urgent-working-plan-card');
            const textBlock = card.querySelector('[data-tempo-ui="notes-text-block"]');
            const mascotContainer = card.querySelector('[data-tempo-ui="notes-mascot-container"]');
            const mascotImg = card.querySelector('img[src*="create-notes-mascot.png"]');
            const plusBtn = card.querySelector('button[aria-label="Create a new note"]');

            const rCard = card.getBoundingClientRect();
            const rRightCol = rightCol.getBoundingClientRect();
            const rPlan = planCard.getBoundingClientRect();
            const rText = textBlock.getBoundingClientRect();
            const rMascotCont = mascotContainer.getBoundingClientRect();
            const rMascot = mascotImg.getBoundingClientRect();
            const rPlus = plusBtn.getBoundingClientRect();

            return {
                cardWidth: rCard.width,
                cardHeight: rCard.height,
                rightColWidth: rRightCol.width,
                planWidth: rPlan.width,
                gapTextToMascot: rMascot.left - rText.right,
                mascotRenderedWidth: rMascot.width,
                mascotRenderedHeight: rMascot.height,
                plusBtnWidth: rPlus.width,
                plusBtnHeight: rPlus.height,
                plusBtnRight: rPlus.right,
                cardRight: rCard.right,
                plusBtnMarginToCardRight: rCard.right - rPlus.right,
                gapCardToPlan: rPlan.top - rCard.bottom
            };
        })()
    """)
    print("Metrics:", json.dumps(metrics, indent=2))

    # Take screenshot of the top section and right col
    res = send('Page.captureScreenshot', {'format': 'png'})
    data = base64.b64decode(res['data'])
    shot_path = os.path.join(artifact_dir, 'urmode_test_replacement_overview.png')
    with open(shot_path, 'wb') as f:
        f.write(data)
    print("Screenshot saved to:", shot_path)

    # Closeup of right col
    clip_eval = eval_js("""
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
    if clip_eval:
        res = send('Page.captureScreenshot', {'format': 'png', 'clip': clip_eval})
        data = base64.b64decode(res['data'])
        shot_path_closeup = os.path.join(artifact_dir, 'urmode_test_replacement_closeup.png')
        with open(shot_path_closeup, 'wb') as f:
            f.write(data)
        print("Closeup saved to:", shot_path_closeup)

finally:
    try: ws.close()
    except: pass
    try: proc.terminate()
    except: pass
