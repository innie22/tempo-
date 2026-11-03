# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, base64, tempfile, os

CDP_PORT = 9486
artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'
user_data_dir = tempfile.mkdtemp(prefix='edge_verify_daily_notes_')

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

    print("App loaded. Initializing auth and emergency mode...")
    eval_js("""
        (async function() {
            const uid = 'usr_alex_verify_daily_notes';
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

    # 1. Verify Card Exists in URmode
    card_info = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="urmode-create-notes"]');
            if (!card) return { found: false };
            const r = card.getBoundingClientRect();
            const mascot = document.querySelector('[data-tempo-ui="urmode-create-notes"] img[src*="create-notes-mascot"]');
            const plusBtn = document.querySelector('[data-tempo-ui="urmode-create-notes"] [aria-label="Create a new note"]');
            const emptyState = document.querySelector('[data-tempo-ui="notes-empty-state"]');
            const viewBtn = document.querySelector('[data-tempo-ui="notes-text-block"] button');
            const heading = document.querySelector('[data-tempo-ui="notes-text-block"] h3');

            return {
                found: true,
                width: r.width,
                height: r.height,
                hasMascot: !!mascot,
                hasPlusBtn: !!plusBtn,
                emptyStateText: emptyState ? emptyState.innerText.trim() : null,
                viewBtnText: viewBtn ? viewBtn.innerText.trim() : null,
                headingText: heading ? heading.innerText.trim() : null
            };
        })()
    """)
    print("Initial Card State:", json.dumps(card_info, indent=2))
    assert card_info['found'] == True, "Create Notes card not found in URmode"
    assert card_info['hasMascot'] == False, "Mascot illustration still present"
    assert card_info['hasPlusBtn'] == False, "Plus button still present"
    assert "No notes for today yet" in (card_info['emptyStateText'] or ""), f"Empty state text mismatch: {card_info['emptyStateText']}"
    assert card_info['viewBtnText'] == "View my notes", f"View button text mismatch: {card_info['viewBtnText']}"
    assert card_info['headingText'] == "Create Notes", f"Heading mismatch: {card_info['headingText']}"
    assert abs(card_info['height'] - 122) < 2, f"Card height is not 122px: {card_info['height']}"

    # Capture empty state screenshot
    clip_card = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="urmode-create-notes"]');
            const r = card.getBoundingClientRect();
            return { x: Math.max(0, r.left - 20), y: Math.max(0, r.top - 20), width: r.width + 40, height: r.height + 40, scale: 1 };
        })()
    """)
    shot1 = send('Page.captureScreenshot', {'clip': clip_card})
    with open(os.path.join(artifact_dir, 'urmode_daily_notes_empty_state.png'), 'wb') as f:
        f.write(base64.b64decode(shot1['data']))
    print("Saved: urmode_daily_notes_empty_state.png")

    # 2. Add Day Note for Today via window.TempoToolNotes.saveDayNote
    eval_js("""
        (function() {
            window.TempoToolNotes.saveDayNote('Review physics assignment chapter 4 and submit before 5 PM');
        })()
    """)
    time.sleep(0.5)

    # Verify reactive update
    state_after_note1 = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="urmode-create-notes"]');
            const items = card.querySelectorAll('[data-day-note-id]');
            const emptyState = card.querySelector('[data-tempo-ui="notes-empty-state"]');
            const r = card.getBoundingClientRect();
            return {
                notesCount: items.length,
                hasEmptyState: !!emptyState,
                cardHeight: r.height,
                firstNoteText: items.length > 0 ? items[0].querySelector('p').innerText.trim() : null
            };
        })()
    """)
    print("State after 1 Day Note:", json.dumps(state_after_note1, indent=2))
    assert state_after_note1['notesCount'] == 1, f"Expected 1 note, got {state_after_note1['notesCount']}"
    assert state_after_note1['hasEmptyState'] == False, "Empty state still visible"
    assert "Review physics assignment" in state_after_note1['firstNoteText'], "Note text mismatch"
    assert abs(state_after_note1['cardHeight'] - 122) < 2, "Card height disrupted after note added"

    # 3. Add Task Note - verify it is STRICTLY EXCLUDED
    eval_js("""
        (function() {
            window.TempoToolNotes.saveTaskNote('task_math_999', 'Calculus III', 'This is a TASK NOTE and MUST NOT APPEAR in Daily Notes');
        })()
    """)
    time.sleep(0.5)

    state_after_task_note = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="urmode-create-notes"]');
            const items = card.querySelectorAll('[data-day-note-id]');
            const allText = card.innerText;
            return {
                notesCount: items.length,
                containsTaskNote: allText.includes('TASK NOTE and MUST NOT APPEAR')
            };
        })()
    """)
    print("State after adding Task Note:", json.dumps(state_after_task_note, indent=2))
    assert state_after_task_note['notesCount'] == 1, "Task note was incorrectly added to daily notes list"
    assert state_after_task_note['containsTaskNote'] == False, "Task note text leaked into daily notes list"

    # 4. Add Yesterday's Day Note - verify it is STRICTLY EXCLUDED
    eval_js("""
        (function() {
            window.TempoToolNotes.saveDayNote('Yesterday Day Note that MUST NOT APPEAR', '2026-10-27');
        })()
    """)
    time.sleep(0.5)

    state_after_yesterday_note = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="urmode-create-notes"]');
            const items = card.querySelectorAll('[data-day-note-id]');
            const allText = card.innerText;
            return {
                notesCount: items.length,
                containsYesterdayNote: allText.includes('Yesterday Day Note')
            };
        })()
    """)
    print("State after adding Yesterday Day Note:", json.dumps(state_after_yesterday_note, indent=2))
    assert state_after_yesterday_note['notesCount'] == 1, "Yesterday note was incorrectly added to today's daily notes list"
    assert state_after_yesterday_note['containsYesterdayNote'] == False, "Yesterday note leaked into daily notes list"

    # 5. Add 3 more Day Notes for today -> verify scrollable internal list & stable 122px outer height
    eval_js("""
        (function() {
            window.TempoToolNotes.saveDayNote('Prepare bibliography citations for literature review');
            window.TempoToolNotes.saveDayNote('Email Professor Davis regarding extension request');
            window.TempoToolNotes.saveDayNote('Take a 15-minute hydration and stretch break');
        })()
    """)
    time.sleep(0.5)

    state_after_4notes = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="urmode-create-notes"]');
            const items = card.querySelectorAll('[data-day-note-id]');
            const scrollList = card.querySelector('[data-tempo-ui="notes-scroll-list"]');
            const r = card.getBoundingClientRect();
            return {
                notesCount: items.length,
                cardHeight: r.height,
                scrollHeight: scrollList ? scrollList.scrollHeight : 0,
                clientHeight: scrollList ? scrollList.clientHeight : 0,
                isScrollable: scrollList ? (scrollList.scrollHeight > scrollList.clientHeight) : false
            };
        })()
    """)
    print("State after 4 Day Notes:", json.dumps(state_after_4notes, indent=2))
    assert state_after_4notes['notesCount'] == 4, f"Expected 4 notes, got {state_after_4notes['notesCount']}"
    assert state_after_4notes['isScrollable'] == True, f"List should be scrollable: scrollHeight={state_after_4notes['scrollHeight']}, clientHeight={state_after_4notes['clientHeight']}"
    assert abs(state_after_4notes['cardHeight'] - 122) < 2, f"Card height changed! Expected 122px, got {state_after_4notes['cardHeight']}"

    # Capture populated scrollable state screenshot
    shot2 = send('Page.captureScreenshot', {'clip': clip_card})
    with open(os.path.join(artifact_dir, 'urmode_daily_notes_populated_4notes.png'), 'wb') as f:
        f.write(base64.b64decode(shot2['data']))
    print("Saved: urmode_daily_notes_populated_4notes.png")

    # Capture full URmode view screenshot
    shot_urmode_full = send('Page.captureScreenshot', {})
    with open(os.path.join(artifact_dir, 'urmode_daily_notes_full_page.png'), 'wb') as f:
        f.write(base64.b64decode(shot_urmode_full['data']))
    print("Saved: urmode_daily_notes_full_page.png")

    # 6. Verify Delete Day Note updates list
    eval_js("""
        (function() {
            const notes = window.TempoToolNotes.getDayNotes();
            if (notes.length > 0) {
                window.TempoToolNotes.deleteDayNote(notes[0].id);
            }
        })()
    """)
    time.sleep(0.5)
    count_after_del = eval_js("document.querySelectorAll('[data-tempo-ui=\"urmode-create-notes\"] [data-day-note-id]').length")
    print(f"Notes count after deletion: {count_after_del} (expected 3)")
    assert count_after_del == 3, f"Expected 3 notes after deletion, got {count_after_del}"

    # 7. Check Scope: Rmode intact
    print("Checking Rmode intactness...")
    eval_js("""
        (function() {
            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
                window.TempoMode.setMode('recovery');
            }
        })()
    """)
    time.sleep(1.5)

    rmode_intact = eval_js("""
        (function() {
            const rmodeHome = document.querySelector('#rmode-home-content');
            const isVisible = rmodeHome && !rmodeHome.classList.contains('hidden') && rmodeHome.offsetParent !== null;
            const streakCard = document.querySelector('#rmode-selfcheck-card');
            const workingPlan = document.querySelector('#rmode-working-plan');
            return {
                rmodeFound: !!rmodeHome,
                rmodeVisible: isVisible,
                streakCardFound: !!streakCard,
                workingPlanFound: !!workingPlan
            };
        })()
    """)
    print("Rmode verification:", json.dumps(rmode_intact, indent=2))
    assert rmode_intact['rmodeFound'] == True, "Rmode home content missing"
    assert rmode_intact['rmodeVisible'] == True, "Rmode home content not visible"

    shot_rmode = send('Page.captureScreenshot', {})
    with open(os.path.join(artifact_dir, 'rmode_verified_intact_daily_notes_task.png'), 'wb') as f:
        f.write(base64.b64decode(shot_rmode['data']))
    print("Saved: rmode_verified_intact_daily_notes_task.png")

    # 8. Check Scope: EntryHome intact
    print("Checking EntryHome intactness...")
    eval_js("""
        (function() {
            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
                window.TempoMode.setMode('default');
            }
        })()
    """)
    time.sleep(1.5)

    dmode_intact = eval_js("""
        (function() {
            const dmodeHome = document.querySelector('#dmode-home-content');
            const isVisible = dmodeHome && !dmodeHome.classList.contains('hidden') && dmodeHome.offsetParent !== null;
            const todayHeader = document.querySelector('#screen-today');
            return {
                dmodeFound: !!dmodeHome,
                dmodeVisible: isVisible,
                todayHeaderFound: !!todayHeader
            };
        })()
    """)
    print("EntryHome verification:", json.dumps(dmode_intact, indent=2))
    assert dmode_intact['dmodeFound'] == True, "EntryHome content missing"
    assert dmode_intact['dmodeVisible'] == True, "EntryHome content not visible"

    shot_dmode = send('Page.captureScreenshot', {})
    with open(os.path.join(artifact_dir, 'entryhome_verified_intact_daily_notes_task.png'), 'wb') as f:
        f.write(base64.b64decode(shot_dmode['data']))
    print("Saved: entryhome_verified_intact_daily_notes_task.png")

    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
