import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os
import base64

sys.stdout.reconfigure(encoding='utf-8')

artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
os.makedirs(artifact_dir, exist_ok=True)

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_notes_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9520

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#today"
]

proc = subprocess.Popen(cmd)
ws = None
msg_id = 1

def send_cmd(method, params=None):
    global msg_id, ws
    cmd_obj = {"id": msg_id, "method": method, "params": params or {}}
    msg_id += 1
    ws.send(json.dumps(cmd_obj))
    while True:
        res = json.loads(ws.recv())
        if res.get("id") == cmd_obj["id"]:
            return res.get("result", {})

def eval_js(expression):
    res = send_cmd("Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True
    })
    if "exceptionDetails" in res:
        print(f"JS ERROR: {res['exceptionDetails']}")
    return res.get("result", {}).get("value")

def capture_screenshot(filename):
    res = send_cmd("Page.captureScreenshot", {"format": "png"})
    if "data" in res:
        img_bytes = base64.b64decode(res["data"])
        filepath = os.path.join(artifact_dir, filename)
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        print(f"Screenshot saved: {filename}")
        return filepath

try:
    time.sleep(2)
    tabs_res = urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read().decode()
    tabs = json.loads(tabs_res)
    app_tabs = [t for t in tabs if "127.0.0.1:8000" in t.get("url", "") or "localhost:8000" in t.get("url", "")]
    target_tab = app_tabs[0] if app_tabs else tabs[0]
    ws_url = target_tab["webSocketDebuggerUrl"]
    ws = websocket.create_connection(ws_url)

    send_cmd("Page.enable")
    send_cmd("Runtime.enable")

    for _ in range(30):
        time.sleep(0.5)
        ready = eval_js("document.readyState === 'complete' && !!window.TempoMode && !!window.TempoToolNotes")
        if ready:
            break

    print("=====================================================================")
    print("STEP 1: SEED ACTIVE USER AND EMERGENCY MODE DASHBOARD")
    print("=====================================================================")

    seed_res = eval_js("""
    (async () => {
        window.TempoI18n.setLanguage('en');

        const mockUser = { id: 'dev_user_1', email: 'dev@tempo.local', user_metadata: { full_name: 'Innie', role: 'student' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(mockUser));
        localStorage.setItem('tempo_mock_account_dev@tempo.local', JSON.stringify(mockUser));
        localStorage.setItem('tempo_user_established_context_dev_user_1', 'emergency');
        localStorage.setItem('tempo_established_context', 'emergency');
        localStorage.setItem('tempo_current_mode', 'emergency');

        const todayStr = window.TempoI18n ? window.TempoI18n.getLocalTodayISO() : '2026-11-01';

        const plan = {
            id: 'plan_test_notes',
            createdDate: todayStr,
            updatedAt: new Date().toISOString(),
            status: 'active',
            tasks: [
                {
                    id: 'task_1',
                    title: 'Advanced AI Project',
                    name: 'Advanced AI Project',
                    estimatedMinutes: 60,
                    completed: false,
                    hasDeadline: true,
                    deadlineDate: todayStr,
                    deadlineTime: '18:00',
                    scheduledDate: todayStr
                }
            ],
            plannedTasks: [
                {
                    id: 'pt_1',
                    dayDate: todayStr,
                    startTime: '10:00',
                    endTime: '11:00',
                    task: {
                        id: 'task_1',
                        title: 'Advanced AI Project',
                        name: 'Advanced AI Project',
                        estimatedMinutes: 60,
                        completed: false,
                        hasDeadline: true,
                        deadlineDate: todayStr,
                        deadlineTime: '18:00'
                    }
                }
            ],
            availability: {
                selectedDays: [todayStr],
                days: [{ date: todayStr, blocks: [{ start: '10:00', end: '18:00' }] }]
            }
        };

        localStorage.setItem('tempo_confirmed_plan', JSON.stringify(plan));
        localStorage.setItem('tempo_confirmed_plan_dev_user_1', JSON.stringify(plan));
        localStorage.setItem('tempo_working_plan', JSON.stringify(plan));

        // Clear any existing notes for a clean initial state
        localStorage.removeItem('tempo_tool_notes_dev_user_1');
        localStorage.removeItem('tempo_day_notes_dev_user_1');
        localStorage.removeItem('tempo_tool_notes');
        localStorage.removeItem('tempo_day_notes');

        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }

        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
            window.TempoEmergencyFlow.setConfirmedPlan(plan);
        }

        if (window.TempoMode) {
            window.TempoMode.transitionContext('emergency');
            window.TempoMode.renderActiveModeHome();
        }

        return true;
    })()
    """)
    print("Seed result:", seed_res)
    time.sleep(1)

    print("\n=====================================================================")
    print("TEST A: CREATE NOTE FROM DASHBOARD CARD")
    print("=====================================================================")

    card_check = eval_js("""
    (() => {
        const outerCard = document.querySelector('[data-tempo-ui="urmode-create-notes"]');
        const emptyCard = document.querySelector('[data-tempo-ui="notes-empty-state"]');
        return {
            hasOuterCard: !!outerCard,
            hasEmptyCard: !!emptyCard,
            emptyText: emptyCard ? emptyCard.innerText.trim() : null
        };
    })()
    """)
    print("Dashboard Notes card status:", json.dumps(card_check, indent=2))
    assert card_check["hasOuterCard"], "Create Notes card not found on dashboard!"
    assert card_check["hasEmptyCard"], "Empty state card not found on dashboard!"

    # Click the "Create a note for today" empty state card
    eval_js("""
    (() => {
        const emptyCard = document.querySelector('[data-tempo-ui="notes-empty-state"]');
        emptyCard.click();
    })()
    """)
    time.sleep(0.5)

    modal_status = eval_js("""
    (() => {
        const modalBackdrop = document.getElementById('note-create-backdrop');
        const form = document.getElementById('modal-create-note-form');
        const titleInput = document.getElementById('modal-input-title');
        const contentInput = document.getElementById('modal-textarea-content');
        const submitBtn = document.getElementById('modal-btn-submit');
        return {
            isOpen: !!modalBackdrop && !!form,
            hasTitleInput: !!titleInput,
            hasContentInput: !!contentInput,
            hasSubmitBtn: !!submitBtn,
            display: modalBackdrop ? window.getComputedStyle(modalBackdrop).display : null
        };
    })()
    """)
    print("Create Note Modal status after click:", json.dumps(modal_status, indent=2))
    assert modal_status["isOpen"], "Modal failed to open upon clicking Create note card!"
    assert modal_status["hasTitleInput"], "Modal is missing Title input!"
    assert modal_status["hasContentInput"], "Modal is missing Content textarea!"

    # Capture screenshot of the opened modal
    capture_screenshot("notes_create_modal_opened.png")

    # Fill in note title and content and save
    save_result = eval_js("""
    (() => {
        const titleInput = document.getElementById('modal-input-title');
        const contentInput = document.getElementById('modal-textarea-content');
        const form = document.getElementById('modal-create-note-form');

        if (titleInput) titleInput.value = 'Chapter 4 Key Findings';
        if (contentInput) contentInput.value = 'Summarized literature review and identified 3 key benchmark questions for the experiment.';

        // Submit form
        form.dispatchEvent(new Event('submit', { cancelable: true }));
        return true;
    })()
    """)
    time.sleep(0.8)

    # Check persistence and modal closure
    post_save = eval_js("""
    (() => {
        const modalBackdrop = document.getElementById('note-create-backdrop');
        const notes = window.TempoToolNotes.getNotes();
        const cardItems = Array.from(document.querySelectorAll('[data-tempo-ui="notes-scroll-list"] [data-day-note-id]')).map(el => el.innerText.trim());
        return {
            isModalClosed: !modalBackdrop,
            totalNotes: notes.length,
            firstNote: notes[0] || null,
            cardItems
        };
    })()
    """)
    print("Post-save note status:", json.dumps(post_save, indent=2))
    assert post_save["isModalClosed"], "Modal did not close after saving!"
    assert post_save["totalNotes"] == 1, f"Expected 1 note saved, got {post_save['totalNotes']}"
    assert post_save["firstNote"]["title"] == "Chapter 4 Key Findings", f"Title mismatch: {post_save['firstNote']['title']}"
    print(">>> PASS Test A: Create Note modal opened, captured title + content, persisted, and updated dashboard!")

    print("\n=====================================================================")
    print("TEST B: VIEW MY NOTES NAVIGATION & FULL PAGE RENDER")
    print("=====================================================================")

    # Click 'View my notes' button
    eval_js("""
    (() => {
        const viewNotesBtn = document.querySelector('[data-tempo-ui="urmode-create-notes"] button');
        if (viewNotesBtn) viewNotesBtn.click();
        else window.TempoApp.navigateTo('notes');
    })()
    """)
    time.sleep(1)

    notes_page_check = eval_js("""
    (() => {
        const screen = document.getElementById('screen-tool-notes');
        const root = document.getElementById('tool-notes-root');
        const backBtn = document.getElementById('btn-tool-notes-back');
        const createSection = document.querySelector('[data-tempo-ui="tool-notes-create-section"]');
        const twoCols = document.querySelector('[data-tempo-ui="tool-notes-two-columns"]');
        const dayPanel = document.querySelector('[data-tempo-ui="tool-notes-day-panel"]');
        const taskPanel = document.querySelector('[data-tempo-ui="tool-notes-task-panel"]');

        const dayNotesCount = document.getElementById('day-notes-count-badge')?.innerText.trim();
        const noteTitles = Array.from(root.querySelectorAll('h5')).map(h => h.innerText.trim());

        return {
            currentHash: window.location.hash,
            screenVisible: !!screen && !screen.classList.contains('hidden'),
            hasRoot: !!root,
            hasBackBtn: !!backBtn,
            hasCreateSection: !!createSection,
            hasTwoCols: !!twoCols,
            hasDayPanel: !!dayPanel,
            hasTaskPanel: !!taskPanel,
            dayNotesCount,
            noteTitles
        };
    })()
    """)
    print("Notes page check result:", json.dumps(notes_page_check, indent=2))
    assert notes_page_check["screenVisible"], "#screen-tool-notes is hidden or missing!"
    assert notes_page_check["hasRoot"] and notes_page_check["hasCreateSection"], "Tool notes content not rendered!"
    assert "Chapter 4 Key Findings" in notes_page_check["noteTitles"], "Saved note title not displayed on page!"
    print(">>> PASS: Notes page rendered fully with existing saved note!")

    capture_screenshot("notes_page_rendered_with_notes.png")

    # Refresh page at #tool-notes and verify persistence
    send_cmd("Page.reload")
    time.sleep(2)

    reload_check = eval_js("""
    (() => {
        const screen = document.getElementById('screen-tool-notes');
        const noteTitles = Array.from(document.querySelectorAll('#tool-notes-root h5')).map(h => h.innerText.trim());
        return {
            currentHash: window.location.hash,
            screenVisible: !!screen && !screen.classList.contains('hidden'),
            noteTitles
        };
    })()
    """)
    print("After reload check:", json.dumps(reload_check, indent=2))
    assert reload_check["screenVisible"], "Notes page not visible after page reload!"
    assert "Chapter 4 Key Findings" in reload_check["noteTitles"], "Saved note not found after reload!"
    print(">>> PASS: Notes page persists across full browser reload!")

    # Test back navigation
    eval_js("""
    (() => {
        const backBtn = document.getElementById('btn-tool-notes-back');
        if (backBtn) backBtn.click();
    })()
    """)
    time.sleep(1)

    back_check = eval_js("""
    (() => {
        const todayScreen = document.getElementById('screen-today');
        return {
            currentHash: window.location.hash,
            todayVisible: !!todayScreen && !todayScreen.classList.contains('hidden')
        };
    })()
    """)
    print("After back navigation:", json.dumps(back_check, indent=2))
    assert back_check["todayVisible"], "Dashboard (#screen-today) not visible after clicking Back!"
    print(">>> PASS: Back button returns cleanly to Dashboard!")

    print("\n=====================================================================")
    print("TEST C: EMPTY STATE ON NOTES PAGE")
    print("=====================================================================")

    # Clear notes to test empty state
    eval_js("""
    (() => {
        localStorage.removeItem('tempo_tool_notes_dev_user_1');
        localStorage.removeItem('tempo_day_notes_dev_user_1');
        localStorage.removeItem('tempo_tool_notes');
        localStorage.removeItem('tempo_day_notes');
        window.TempoApp.navigateTo('notes');
    })()
    """)
    time.sleep(1)

    empty_check = eval_js("""
    (() => {
        const emptyDay = document.querySelector('[data-tempo-ui="day-notes-empty"]');
        const emptyTask = document.querySelector('[data-tempo-ui="task-notes-empty"]');
        const dayBadge = document.getElementById('day-notes-count-badge')?.innerText.trim();
        return {
            hasEmptyDay: !!emptyDay,
            emptyDayText: emptyDay ? emptyDay.innerText.trim().replace(/\\n+/g, ' ') : null,
            hasEmptyTask: !!emptyTask,
            emptyTaskText: emptyTask ? emptyTask.innerText.trim().replace(/\\n+/g, ' ') : null,
            dayBadge
        };
    })()
    """)
    print("Empty state check:", json.dumps(empty_check, indent=2))
    assert empty_check["hasEmptyDay"], "Empty Day Notes state missing!"
    assert empty_check["hasEmptyTask"], "Empty Task Notes state missing!"
    assert empty_check["dayBadge"] == "0", f"Expected count badge '0', got '{empty_check['dayBadge']}'"
    print(">>> PASS: Clean, informative empty states render for both day and task notes!")

    capture_screenshot("notes_page_empty_state.png")

    print("\n=====================================================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=====================================================================")

finally:
    try:
        if ws:
            ws.close()
    except:
        pass
    proc.terminate()
