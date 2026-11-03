# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, base64, tempfile, os

CDP_PORT = 9487
artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'
user_data_dir = tempfile.mkdtemp(prefix='edge_verify_tool_notes_')

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
        val = eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoToolNotes !== 'undefined'")
        if val:
            break
        time.sleep(0.5)

    print("App loaded. Authenticating mock user...")
    eval_js("""
        (async function() {
            const uid = 'usr_alex_tool_notes_e2e';
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

            // Setup a couple mock tasks in emergency flow for Task Note selector testing
            const mockTasks = [
                { id: 'task_cs101', name: 'CS 101 - Algorithm Analysis Homework', deadlineDate: '2026-10-30', completed: false },
                { id: 'task_math201', name: 'Math 201 - Linear Algebra Problem Set', deadlineDate: '2026-10-29', completed: false }
            ];
            if (window.TempoEmergencyFlow) {
                window.TempoEmergencyFlow.setConfirmedPlan({
                    plannedTasks: mockTasks.map(t => ({ task: t, dayDate: '2026-10-28' })),
                    tasks: mockTasks
                });
            }
            localStorage.setItem('tempo_tasks_' + uid, JSON.stringify(mockTasks));

            if (window.TempoAuth && typeof window.TempoAuth.signIn === 'function') {
                await window.TempoAuth.signIn('student@tempo.app', 'password123');
            }
            if (window.TempoAuth && typeof window.TempoAuth.closeAllAuthModals === 'function') window.TempoAuth.closeAllAuthModals();
            document.querySelectorAll('.auth-modal-overlay').forEach(m => m.classList.add('hidden'));

            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') window.TempoMode.setMode('emergency');
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') window.TempoApp.navigateTo('notes');
        })()
    """, await_promise=True)
    time.sleep(2)

    # 1. VERIFY TOOL NOTES PAGE IS RENDERED & PLACEHOLDER IS GONE
    print("Checking Tool Notes page structure...")
    page_info = eval_js("""
        (function() {
            const root = document.getElementById('tool-notes-root');
            const placeholder = document.body.innerText.includes('Your notes space is coming soon');
            const createSection = document.querySelector('[data-tempo-ui="tool-notes-create-section"]');
            const dayPanel = document.querySelector('[data-tempo-ui="tool-notes-day-panel"]');
            const taskPanel = document.querySelector('[data-tempo-ui="tool-notes-task-panel"]');
            const dayEmpty = document.querySelector('[data-tempo-ui="day-notes-empty"]');
            const taskEmpty = document.querySelector('[data-tempo-ui="task-notes-empty"]');
            const taskOptions = Array.from(document.querySelectorAll('#select-note-task option')).map(o => o.text);

            return {
                rootExists: !!root,
                placeholderGone: !placeholder,
                createSectionExists: !!createSection,
                dayPanelExists: !!dayPanel,
                taskPanelExists: !!taskPanel,
                dayEmptyExists: !!dayEmpty,
                taskEmptyExists: !!taskEmpty,
                taskOptionsCount: taskOptions.length,
                taskOptionsSample: taskOptions.slice(0, 3)
            };
        })()
    """)
    print("Page Info:", json.dumps(page_info, indent=2))
    assert page_info['rootExists'] == True, "tool-notes-root missing"
    assert page_info['placeholderGone'] == True, "Placeholder still present!"
    assert page_info['createSectionExists'] == True, "Creation section missing"
    assert page_info['dayPanelExists'] == True, "Day notes panel missing"
    assert page_info['taskPanelExists'] == True, "Task notes panel missing"
    assert page_info['dayEmptyExists'] == True, "Day notes empty state missing initially"
    assert page_info['taskEmptyExists'] == True, "Task notes empty state missing initially"
    assert page_info['taskOptionsCount'] >= 2, "Task options not populated from available tasks"

    # Capture initial empty state screenshot of Tool Notes page
    shot_empty = send('Page.captureScreenshot', {})
    with open(os.path.join(artifact_dir, 'tool_notes_page_empty_state.png'), 'wb') as f:
        f.write(base64.b64decode(shot_empty['data']))
    print("Saved: tool_notes_page_empty_state.png")

    # 2. TEST NOTE CREATION FORM: Day Note
    print("Testing creation of a Day Note via the form...")
    eval_js("""
        (function() {
            window.TempoToolNotes.setCreationType('day');
            const ta = document.getElementById('textarea-note-content');
            ta.value = 'Today reflections: Completed initial draft of triage paper and took gentle breathing break.';
            window.TempoToolNotes.handleCreateFormSubmit();
        })()
    """)
    time.sleep(1)

    state_after_day_note = eval_js("""
        (function() {
            const dayCards = document.querySelectorAll('#tool-notes-root [data-day-note-id]');
            const dayEmpty = document.querySelector('[data-tempo-ui="day-notes-empty"]');
            const badge = document.getElementById('day-notes-count-badge');
            return {
                dayCardsCount: dayCards.length,
                hasEmpty: !!dayEmpty,
                badgeCount: badge ? badge.innerText.trim() : null,
                noteText: dayCards.length > 0 ? dayCards[0].querySelector('p').innerText : null
            };
        })()
    """)
    print("State after Day Note creation:", json.dumps(state_after_day_note, indent=2))
    assert state_after_day_note['dayCardsCount'] == 1, "Day note not rendered in panel"
    assert state_after_day_note['hasEmpty'] == False, "Empty state still present after note creation"
    assert state_after_day_note['badgeCount'] == '1', f"Badge count expected '1', got {state_after_day_note['badgeCount']}"

    # 3. TEST NOTE CREATION FORM: Task Note
    print("Testing creation of a Task Note via the form...")
    eval_js("""
        (function() {
            window.TempoToolNotes.setCreationType('task');
            const sel = document.getElementById('select-note-task');
            if (sel.options.length > 1) sel.selectedIndex = 1;
            const ta = document.getElementById('textarea-note-content');
            ta.value = 'Remember to verify lemma 3 in the problem set before submitting the final PDF.';
            window.TempoToolNotes.handleCreateFormSubmit();
        })()
    """)
    time.sleep(1)

    state_after_task_note = eval_js("""
        (function() {
            const taskCards = document.querySelectorAll('#tool-notes-root [data-task-note-id]');
            const taskEmpty = document.querySelector('[data-tempo-ui="task-notes-empty"]');
            const badge = document.getElementById('task-notes-count-badge');
            return {
                taskCardsCount: taskCards.length,
                hasEmpty: !!taskEmpty,
                badgeCount: badge ? badge.innerText.trim() : null,
                taskTitle: taskCards.length > 0 ? taskCards[0].querySelector('span.text-xs.font-bold').innerText : null,
                noteText: taskCards.length > 0 ? taskCards[0].querySelector('p').innerText : null
            };
        })()
    """)
    print("State after Task Note creation:", json.dumps(state_after_task_note, indent=2))
    assert state_after_task_note['taskCardsCount'] == 1, "Task note not rendered in panel"
    assert state_after_task_note['hasEmpty'] == False, "Task empty state still present after note creation"
    assert state_after_task_note['badgeCount'] == '1', f"Badge count expected '1', got {state_after_task_note['badgeCount']}"

    # Capture populated screenshot of Tool Notes page
    shot_populated = send('Page.captureScreenshot', {})
    with open(os.path.join(artifact_dir, 'tool_notes_page_populated.png'), 'wb') as f:
        f.write(base64.b64decode(shot_populated['data']))
    print("Saved: tool_notes_page_populated.png")

    # 4. TEST NOTE DETAIL POPUP (Modal)
    print("Testing Note Detail Popup by clicking Day Note card...")
    eval_js("""
        (function() {
            const dayCard = document.querySelector('#tool-notes-root [data-day-note-id]');
            if (dayCard) dayCard.click();
        })()
    """)
    time.sleep(0.5)

    modal_info = eval_js("""
        (function() {
            const root = document.getElementById('tool-notes-modal-root');
            const backdrop = document.getElementById('note-detail-backdrop');
            const title = document.getElementById('note-detail-title');
            const fullContent = root ? root.querySelector('p.whitespace-pre-wrap') : null;
            const deleteBtn = root ? root.querySelector('button[onclick*="confirmDeleteNote"]') : null;
            const editBtn = root ? root.querySelector('button[onclick*="openNoteEditModal"]') : null;

            return {
                isOpen: !!backdrop,
                titleText: title ? title.innerText.trim() : null,
                contentText: fullContent ? fullContent.innerText.trim() : null,
                hasDeleteBtn: !!deleteBtn,
                hasEditBtn: !!editBtn
            };
        })()
    """)
    print("Detail Modal Info:", json.dumps(modal_info, indent=2))
    assert modal_info['isOpen'] == True, "Detail modal not opened"
    assert "Today reflections:" in (modal_info['contentText'] or ""), "Complete content missing in detail popup"
    assert modal_info['hasDeleteBtn'] == True, "Delete button missing"
    assert modal_info['hasEditBtn'] == True, "Edit button missing"

    # Capture detail modal screenshot
    shot_detail = send('Page.captureScreenshot', {})
    with open(os.path.join(artifact_dir, 'tool_notes_detail_modal.png'), 'wb') as f:
        f.write(base64.b64decode(shot_detail['data']))
    print("Saved: tool_notes_detail_modal.png")

    # 5. TEST EDITING NOTE VIA MODAL
    print("Testing Edit Note modal...")
    eval_js("""
        (function() {
            const editBtn = document.querySelector('#tool-notes-modal-root button[onclick*="openNoteEditModal"]');
            if (editBtn) editBtn.click();
        })()
    """)
    time.sleep(0.5)

    eval_js("""
        (function() {
            const ta = document.getElementById('edit-note-content');
            ta.value = 'Updated reflections: Successfully revised and expanded note content!';
            const form = document.querySelector('#tool-notes-modal-root form');
            if (form) form.dispatchEvent(new Event('submit', { cancelable: true }));
        })()
    """)
    time.sleep(0.5)

    updated_modal_info = eval_js("""
        (function() {
            const root = document.getElementById('tool-notes-modal-root');
            const fullContent = root ? root.querySelector('p.whitespace-pre-wrap') : null;
            return {
                contentText: fullContent ? fullContent.innerText.trim() : null
            };
        })()
    """)
    print("Updated Modal Info:", json.dumps(updated_modal_info, indent=2))
    assert "Successfully revised and expanded" in (updated_modal_info['contentText'] or ""), "Note edit failed to update"

    # Close modal
    eval_js("window.TempoToolNotes.closeModal();")
    time.sleep(0.5)

    # 6. TEST URMODE CREATE NOTES CARD INTEGRATION
    print("Testing URmode Create Notes card integration...")
    eval_js("window.TempoApp.navigateTo('today');")
    time.sleep(1.5)

    urmode_card_info = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="urmode-create-notes"]');
            if (!card) return { found: false };
            const r = card.getBoundingClientRect();
            const noteItems = card.querySelectorAll('[data-day-note-id]');
            const viewBtn = card.querySelector('[data-tempo-ui="notes-text-block"] button');
            const emptyState = card.querySelector('[data-tempo-ui="notes-empty-state"]');

            return {
                found: true,
                cardHeight: r.height,
                cardWidth: r.width,
                dayNotesInCard: noteItems.length,
                hasEmptyState: !!emptyState,
                viewBtnText: viewBtn ? viewBtn.innerText.trim() : null,
                firstItemPreview: noteItems.length > 0 ? noteItems[0].querySelector('p').innerText.trim() : null
            };
        })()
    """)
    print("URmode Card Info with existing Day Note:", json.dumps(urmode_card_info, indent=2))
    assert urmode_card_info['found'] == True, "Create Notes card missing in URmode"
    assert abs(urmode_card_info['cardHeight'] - 122) < 2, f"Card height disrupted: {urmode_card_info['cardHeight']}"
    assert urmode_card_info['dayNotesInCard'] == 1, "Today's Day Note not displayed in URmode card"
    assert "Successfully revised" in (urmode_card_info['firstItemPreview'] or ""), "Updated Day Note not previewed in URmode card"

    # Test clicking note in URmode card opens note detail popup
    print("Clicking note inside URmode card to test detail popup...")
    eval_js("""
        (function() {
            const noteItem = document.querySelector('[data-tempo-ui="urmode-create-notes"] [data-day-note-id]');
            if (noteItem) noteItem.click();
        })()
    """)
    time.sleep(0.5)

    card_modal_opened = eval_js("!!document.getElementById('note-detail-backdrop')")
    print(f"Detail modal opened from URmode card click: {card_modal_opened}")
    assert card_modal_opened == True, "Clicking note in URmode card did not open detail popup"
    eval_js("window.TempoToolNotes.closeModal();")
    time.sleep(0.5)

    # Now delete the Day Note to test empty state in URmode
    print("Deleting day note to test empty state in URmode...")
    eval_js("""
        (function() {
            const notes = window.TempoToolNotes.getDayNotes();
            if (notes.length > 0) window.TempoToolNotes.deleteNote(notes[0].id);
        })()
    """)
    time.sleep(0.5)

    urmode_empty_info = eval_js("""
        (function() {
            const emptyState = document.querySelector('[data-tempo-ui="notes-empty-state"]');
            const emptyText = emptyState ? emptyState.innerText.trim() : null;
            return {
                hasEmptyState: !!emptyState,
                emptyText: emptyText
            };
        })()
    """)
    print("URmode Card Empty Info:", json.dumps(urmode_empty_info, indent=2))
    assert urmode_empty_info['hasEmptyState'] == True, "Empty state missing in URmode card when no notes exist"
    assert "Create a note for today" in (urmode_empty_info['emptyText'] or ""), f"Empty text mismatch: {urmode_empty_info['emptyText']}"

    # Test clicking empty state opens note create modal
    print("Clicking empty state in URmode card...")
    eval_js("""
        (function() {
            const emptyState = document.querySelector('[data-tempo-ui="notes-empty-state"]');
            if (emptyState) emptyState.click();
        })()
    """)
    time.sleep(0.5)

    create_modal_opened = eval_js("""
        (function() {
            const backdrop = document.getElementById('note-create-backdrop');
            const pillDay = document.getElementById('modal-pill-day');
            const dateInput = document.getElementById('modal-input-date');
            return {
                isOpen: !!backdrop,
                dayPillActive: pillDay ? pillDay.classList.contains('bg-[#C88E7D]') : false,
                dateValue: dateInput ? dateInput.value : null
            };
        })()
    """)
    print("Create Modal Info from empty state click:", json.dumps(create_modal_opened, indent=2))
    assert create_modal_opened['isOpen'] == True, "Clicking empty state did not open creation modal"
    assert create_modal_opened['dayPillActive'] == True, "Day Note not selected by default"
    assert len(create_modal_opened['dateValue'] or '') == 10, "Date not prefilled"

    eval_js("window.TempoToolNotes.closeModal();")
    time.sleep(0.5)

    # 7. CHECK SCOPE: Rmode & EntryHome
    print("Verifying Rmode is intact...")
    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(1)
    rmode_ok = eval_js("!!document.querySelector('#rmode-home-content') && !document.querySelector('#rmode-home-content').classList.contains('hidden')")
    assert rmode_ok == True, "Rmode is not intact"

    print("Verifying EntryHome is intact...")
    eval_js("window.TempoMode.setMode('default');")
    time.sleep(1)
    dmode_ok = eval_js("!!document.querySelector('#dmode-home-content') && !document.querySelector('#dmode-home-content').classList.contains('hidden')")
    assert dmode_ok == True, "EntryHome is not intact"

    print("\nALL VERIFICATIONS PASSED WITH 100% SUCCESS!")

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
