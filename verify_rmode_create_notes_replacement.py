# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys, os, base64

sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
CDP_PORT = 9545
user_data_dir = tempfile.mkdtemp(prefix='edge_verify_rmode_notes_')

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
        res = send('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
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

    for _ in range(30):
        val = eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'")
        if val:
            break
        time.sleep(0.5)

    # =========================================================================
    # PHASE 1: Verify Old NOTE Section is Gone & Create Notes Card Replaces It
    # =========================================================================
    print("\n--- PHASE 1: Verify NOTE section removal and Create Notes card in Rmode ---")
    today = "2026-10-28"
    eval_js("""
        (async function() {
            const email = 'alex.chen@university.edu';
            const mock = {
                id: 'mock-user-alex',
                email: email,
                password: 'password123',
                profile: { id: 'mock-user-alex', full_name: 'Alex Chen', display_name: 'Alex Chen', role: 'student' }
            };
            localStorage.setItem('tempo_mock_account_' + email, JSON.stringify(mock));
            if (window.TempoAuth) {
                await window.TempoAuth.signIn(email, 'password123');
            }
            
            const uid = 'mock-user-alex';
            localStorage.setItem('tempo_active_mode', 'recovery');
            localStorage.setItem('tempo_originating_mode', 'recovery');
            
            // Clear any notes for today to test empty state first
            localStorage.removeItem(`tempo_day_notes_${uid}`);
            localStorage.removeItem('tempo_day_notes');
            localStorage.removeItem(`tempo_tool_notes_${uid}`);
            localStorage.removeItem('tempo_tool_notes');
            
            if (window.TempoMode) {
                window.TempoMode.transitionContext('recovery', { skipSetupCheck: true });
                window.TempoMode.renderRmodeHome();
            }
        })()
    """)
    time.sleep(1.0)

    rmode_check = eval_js("""
        (function() {
            const rmodeBox = document.getElementById('rmode-home-content');
            if (!rmodeBox) return { error: 'rmode-home-content not found' };
            
            const rightCol = rmodeBox.querySelector('.recovery-right-col');
            if (!rightCol) return { error: 'recovery-right-col not found' };

            // Check old note elements
            const oldNoteCard = rmodeBox.querySelector('[data-tempo-ui="dashboard-note-card"]');
            const oldNoteTextFound = rightCol.innerText.includes('Drink more than 3 cups of water');
            const oldNoteHeadingFound = rightCol.innerText.includes('Create your notes');

            // Check Create Notes card
            const createNotesCard = rightCol.querySelector('[data-tempo-ui="urmode-create-notes"]');
            const cardRect = createNotesCard ? createNotesCard.getBoundingClientRect() : null;
            const cs = createNotesCard ? window.getComputedStyle(createNotesCard) : null;
            
            // Check position relative to Recently card
            const recentlyCard = rightCol.querySelector('[data-tempo-ui="recovery-recently"]');
            const recentlyRect = recentlyCard ? recentlyCard.getBoundingClientRect() : null;

            // Check card internal elements
            const title = createNotesCard ? createNotesCard.querySelector('h3') : null;
            const viewBtn = createNotesCard ? createNotesCard.querySelector('button') : null;
            const emptyState = createNotesCard ? createNotesCard.querySelector('[data-tempo-ui="notes-empty-state"]') : null;

            return {
                oldNoteCardExists: !!oldNoteCard,
                oldNoteTextFound: oldNoteTextFound,
                oldNoteHeadingFound: oldNoteHeadingFound,
                createNotesCardExists: !!createNotesCard,
                cardRect: cardRect ? { x: cardRect.x, y: cardRect.y, width: cardRect.width, height: cardRect.height } : null,
                cardHeight: cardRect ? cardRect.height : null,
                cardWidth: cardRect ? cardRect.width : null,
                recentlyTop: recentlyRect ? recentlyRect.top : null,
                cardBottom: cardRect ? cardRect.bottom : null,
                gapToRecently: (recentlyRect && cardRect) ? (recentlyRect.top - cardRect.bottom) : null,
                title: title ? title.innerText.trim() : null,
                viewBtnText: viewBtn ? viewBtn.innerText.trim() : null,
                emptyStateText: emptyState ? emptyState.innerText.trim().replace(/\\n/g, ' ') : null,
                hasMascot: !!(createNotesCard && createNotesCard.querySelector('img'))
            };
        })()
    """)
    print("Rmode Check State:", json.dumps(rmode_check, indent=2))

    # Assertions
    assert not rmode_check['oldNoteCardExists'], "Old NOTE card [data-tempo-ui='dashboard-note-card'] still exists"
    assert not rmode_check['oldNoteTextFound'], "Old text 'Drink more than 3 cups of water' still exists"
    assert not rmode_check['oldNoteHeadingFound'], "Old link 'Create your notes' still exists"
    assert rmode_check['createNotesCardExists'], "Create Notes card was not found in recovery-right-col"
    assert rmode_check['title'] == "Create Notes", f"Expected title 'Create Notes', got '{rmode_check['title']}'"
    assert rmode_check['viewBtnText'] == "View my notes", f"Expected button 'View my notes', got '{rmode_check['viewBtnText']}'"
    assert "Create a note for today" in rmode_check['emptyStateText'], f"Empty state text mismatch: '{rmode_check['emptyStateText']}'"
    assert not rmode_check['hasMascot'], "Mascot should not be present"
    assert abs(rmode_check['cardHeight'] - 122) < 2.0, f"Card height {rmode_check['cardHeight']} should be ~122px"
    assert rmode_check['cardBottom'] <= rmode_check['recentlyTop'], "Create Notes card should be positioned above Recently card"

    r = rmode_check['cardRect']
    capture_screenshot('rmode_create_notes_empty_state.png', clip={
        'x': max(0, r['x'] - 20),
        'y': max(0, r['y'] - 20),
        'width': r['width'] + 40,
        'height': r['height'] + 40,
        'scale': 1
    })
    capture_screenshot('rmode_dashboard_create_notes.png')

    # =========================================================================
    # PHASE 2: Interaction - Click Empty Preview & Click View My Notes
    # =========================================================================
    print("\n--- PHASE 2: Test empty preview click -> Create Note Modal ---")
    eval_js("""
        (function() {
            const emptyEl = document.querySelector('.recovery-right-col [data-tempo-ui="notes-empty-state"]');
            if (emptyEl) emptyEl.click();
        })()
    """)
    time.sleep(1.0)

    modal_info = eval_js("""
        (function() {
            const backdrop = document.getElementById('note-create-backdrop');
            const isVisible = !!(backdrop && !backdrop.classList.contains('hidden'));
            const title = backdrop ? backdrop.querySelector('h3') : null;
            const dayPill = backdrop ? backdrop.querySelector('#modal-pill-day') : null;
            const dateGroup = backdrop ? backdrop.querySelector('#modal-group-date') : null;
            const dateInp = backdrop ? backdrop.querySelector('input[type="date"]') : null;
            return {
                modalVisible: isVisible,
                modalTitle: title ? title.innerText.trim() : null,
                dayPillActive: dayPill ? dayPill.classList.contains('bg-[#C88E7D]') : false,
                dateGroupVisible: dateGroup ? !dateGroup.classList.contains('hidden') : false,
                dateValue: dateInp ? dateInp.value : null
            };
        })()
    """)
    print("Create Note Modal Info:", json.dumps(modal_info, indent=2))
    assert modal_info['modalVisible'], "Create Note modal did not open"
    assert modal_info['modalTitle'] == "Create a Note", f"Expected 'Create a Note', got '{modal_info['modalTitle']}'"
    assert modal_info['dayPillActive'], "Day Note type should be pre-selected on pill"
    assert modal_info['dateGroupVisible'], "Date field group should be visible"
    assert modal_info['dateValue'] is not None and len(modal_info['dateValue']) == 10, f"Date should be prefilled: '{modal_info['dateValue']}'"

    capture_screenshot('rmode_create_note_modal_opened.png')

    # Close modal
    eval_js("""
        (function() {
            if (window.TempoToolNotes && typeof window.TempoToolNotes.closeModal === 'function') {
                window.TempoToolNotes.closeModal();
            }
        })()
    """)
    time.sleep(0.5)

    # Test "View my notes" navigation
    print("\n--- Test 'View my notes' click -> Navigate to Tool Notes ---")
    eval_js("""
        (function() {
            const btn = document.querySelector('.recovery-right-col [data-tempo-ui="urmode-create-notes"] button');
            if (btn) btn.click();
        })()
    """)
    time.sleep(1.0)

    notes_page_visible = eval_js("""
        (function() {
            const scr = document.getElementById('screen-tool-notes');
            return !!(scr && !scr.classList.contains('hidden'));
        })()
    """)
    print(f"Tool Notes page visible after 'View my notes' click: {notes_page_visible}")
    assert notes_page_visible, "Did not navigate to Tool Notes page"

    # Return to Rmode
    eval_js("""
        (function() {
            if (window.TempoApp) window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1.0)

    # =========================================================================
    # PHASE 3: Day Notes Rendering & Detail Modal Click
    # =========================================================================
    print("\n--- PHASE 3: Create Day Note for today & verify preview card ---")
    eval_js("""
        (function() {
            const uid = 'mock-user-alex';
            const todayStr = new Date().toISOString().slice(0, 10);
            const note = {
                id: 'note_test_day_1',
                userId: uid,
                type: 'day',
                date: todayStr,
                text: 'Drank 4 cups of water and took a gentle 20-minute walk outside.',
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString()
            };
            localStorage.setItem('tempo_day_notes_' + uid, JSON.stringify([note]));
            if (window.TempoMode && typeof window.TempoMode.refreshNotesCardIfPresent === 'function') {
                window.TempoMode.refreshNotesCardIfPresent();
            }
        })()
    """)
    time.sleep(1.0)

    card_with_notes = eval_js("""
        (function() {
            const card = document.querySelector('.recovery-right-col [data-tempo-ui="urmode-create-notes"]');
            if (!card) return null;
            const r = card.getBoundingClientRect();
            const noteItems = Array.from(card.querySelectorAll('[data-day-note-id]')).map(el => ({
                id: el.getAttribute('data-day-note-id'),
                text: el.innerText.replace(/\\n/g, ' ')
            }));
            const emptyState = card.querySelector('[data-tempo-ui="notes-empty-state"]');
            return {
                cardRect: { x: r.x, y: r.y, width: r.width, height: r.height },
                notesCount: noteItems.length,
                notes: noteItems,
                emptyStateExists: !!emptyState
            };
        })()
    """)
    print("Card with Notes:", json.dumps(card_with_notes, indent=2))
    assert card_with_notes['notesCount'] == 1, "Expected 1 note preview item"
    assert "Drank 4 cups of water" in card_with_notes['notes'][0]['text'], "Note text missing"
    assert not card_with_notes['emptyStateExists'], "Empty state should not be displayed when notes exist"

    capture_screenshot('rmode_create_notes_with_note.png', clip={
        'x': max(0, card_with_notes['cardRect']['x'] - 20),
        'y': max(0, card_with_notes['cardRect']['y'] - 20),
        'width': card_with_notes['cardRect']['width'] + 40,
        'height': card_with_notes['cardRect']['height'] + 40,
        'scale': 1
    })

    # Click note preview -> opens note detail modal
    print("\n--- Test note preview item click -> Note Detail Modal ---")
    eval_js("""
        (function() {
            const item = document.querySelector('.recovery-right-col [data-day-note-id="note_test_day_1"]');
            if (item) item.click();
        })()
    """)
    time.sleep(1.0)

    detail_modal = eval_js("""
        (function() {
            const backdrop = document.getElementById('note-detail-backdrop');
            const isVisible = !!(backdrop && !backdrop.classList.contains('hidden'));
            const text = backdrop ? backdrop.innerText : '';
            return {
                detailVisible: isVisible,
                hasNoteText: text.includes('Drank 4 cups of water')
            };
        })()
    """)
    print("Detail Modal Info:", json.dumps(detail_modal, indent=2))
    assert detail_modal['detailVisible'], "Note detail modal did not open"
    assert detail_modal['hasNoteText'], "Note detail modal should display note content"
    capture_screenshot('rmode_note_detail_modal_opened.png')

    # Close detail modal
    eval_js("""
        (function() {
            if (window.TempoToolNotes && typeof window.TempoToolNotes.closeModal === 'function') {
                window.TempoToolNotes.closeModal();
            }
        })()
    """)
    time.sleep(0.5)

    # =========================================================================
    # PHASE 4: Non-Regression & Scope Verification
    # =========================================================================
    print("\n--- PHASE 4: Non-Regression & Scope Checks ---")
    eval_js("""
        (async function() {
            if (window.TempoMode) window.TempoMode.setMode('emergency');
            if (window.TempoApp) window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1.0)
    urmode_ok = eval_js("""
        (function() {
            const ebox = document.getElementById('emode-home-content');
            const card = ebox ? ebox.querySelector('[data-tempo-ui="urmode-create-notes"]') : null;
            return !!(ebox && !ebox.classList.contains('hidden') && card);
        })()
    """)
    print(f"URmode intact with Create Notes card: {urmode_ok}")
    assert urmode_ok, "URmode was affected"
    capture_screenshot('urmode_verified_intact_notes_task.png')

    eval_js("""
        (async function() {
            if (window.TempoMode) window.TempoMode.setMode('default');
            if (window.TempoApp) window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1.0)
    entryhome_ok = eval_js("""
        (function() {
            const dbox = document.getElementById('dmode-home-content');
            return !!(dbox && !dbox.classList.contains('hidden') && dbox.children.length > 0);
        })()
    """)
    print(f"EntryHome intact: {entryhome_ok}")
    assert entryhome_ok, "EntryHome was affected"
    capture_screenshot('entryhome_verified_intact_notes_task.png')

    print("\nALL VERIFICATION PHASES PASSED WITH 100% SUCCESS!")

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
