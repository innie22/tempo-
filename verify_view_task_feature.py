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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_view_task_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9540

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#tool-notes"
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
    ws_url = app_tabs[0]["webSocketDebuggerUrl"] if app_tabs else tabs[0]["webSocketDebuggerUrl"]

    ws = websocket.create_connection(ws_url)
    send_cmd("Page.enable")
    send_cmd("DOM.enable")

    print("Connected to browser via CDP!")
    time.sleep(1.5)

    # 1. Clean localStorage for clean test run
    eval_js("""
    (() => {
        localStorage.removeItem('tempo_tool_notes');
        const user = window.TempoAuth ? window.TempoAuth.getCurrentUserId() : 'guest';
        localStorage.removeItem('tempo_tool_notes_' + user);
        window.TempoToolNotes.renderToolNotesPage();
    })()
    """)
    time.sleep(0.5)

    # 2. Set language to Vietnamese
    eval_js("window.TempoI18n.setLanguage('vi')")
    time.sleep(0.3)

    # 3. Create a Day Note and a Task Note with known task 'task-marketing-research'
    eval_js("""
    (() => {
        window.TempoToolNotes.saveDayNote('Ghi chú tự suy ngẫm', window.TempoToolNotes.getTodayLocalDateStr(), null, 'Ngày tốt lành');
        window.TempoToolNotes.saveTaskNote('task-marketing-research', 'Marketing Research', 'Chi tiết chuẩn bị tài liệu phân tích thị trường', null, 'Khảo sát thị trường');
    })()
    """)
    time.sleep(0.5)

    notes = eval_js("window.TempoToolNotes.getNotes()")
    day_note = next(n for n in notes if n.get('type') == 'day')
    task_note = next(n for n in notes if n.get('type') == 'task')
    print(f"Created day note ID: {day_note.get('id')}, task note ID: {task_note.get('id')}")

    # -------------------------------------------------------------------------
    # TEST A: Verify Day Note Detail Modal does NOT have "View Task"
    # -------------------------------------------------------------------------
    print("\n--- TEST A: Day Note Detail Modal ---")
    eval_js(f"window.TempoToolNotes.openNoteDetailModal('{day_note.get('id')}')")
    time.sleep(0.3)
    has_view_task_day = eval_js("document.getElementById('btn-note-view-task') !== null")
    print(f"Does Day Note Detail have 'View Task' button? {has_view_task_day} (Expected: False)")
    assert not has_view_task_day, "View Task button should NOT appear for Day Notes!"
    eval_js("window.TempoToolNotes.closeModal()")
    time.sleep(0.2)

    # -------------------------------------------------------------------------
    # TEST B: Verify Task Note Detail Modal in Vietnamese (vi)
    # -------------------------------------------------------------------------
    print("\n--- TEST B: Task Note Detail Modal (Vietnamese) ---")
    eval_js(f"window.TempoToolNotes.openNoteDetailModal('{task_note.get('id')}')")
    time.sleep(0.4)

    btn_view_task_vi = eval_js("document.getElementById('btn-note-view-task')?.innerText.trim()")
    print(f"View Task Button (VI): '{btn_view_task_vi}' (Expected: '📌 Xem task')")
    assert "Xem task" in btn_view_task_vi, f"Button text mismatch in VI: '{btn_view_task_vi}'"

    capture_screenshot("task_note_detail_modal_vi.png")

    # -------------------------------------------------------------------------
    # TEST C: Verify Immediate Update on Language Switch to English (en)
    # -------------------------------------------------------------------------
    print("\n--- TEST C: Language Switch to English (en) ---")
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(0.4)

    btn_view_task_en = eval_js("document.getElementById('btn-note-view-task')?.innerText.trim()")
    print(f"View Task Button (EN): '{btn_view_task_en}' (Expected: '📌 View Task')")
    assert "View Task" in btn_view_task_en, f"Button text mismatch in EN: '{btn_view_task_en}'"

    capture_screenshot("task_note_detail_modal_en.png")

    # -------------------------------------------------------------------------
    # TEST D: Click "View Task" and Verify Task Detail Modal
    # -------------------------------------------------------------------------
    print("\n--- TEST D: Click 'View Task' -> Opens Task Detail Modal ---")
    eval_js("document.getElementById('btn-note-view-task').click()")
    time.sleep(0.6)

    # 1. Verify Note Detail Modal closed
    note_modal_open = eval_js("document.getElementById('note-detail-backdrop') !== null")
    print(f"Is Note Detail modal closed? {not note_modal_open}")
    assert not note_modal_open, "Note detail modal should be closed after clicking View Task!"

    # 2. Verify Task Detail Modal opened
    task_modal_open = eval_js("document.getElementById('urmode-task-detail-modal') !== null")
    print(f"Is Task Detail modal open? {task_modal_open}")
    assert task_modal_open, "Task Detail modal failed to open!"

    # 3. Verify task information
    task_detail_title = eval_js("document.getElementById('urmode-task-modal-title')?.innerText.trim()")
    task_detail_badge = eval_js("document.querySelector('#urmode-task-detail-modal button[onclick*=\"toggleUrmodeDetailLabelMenu\"]')?.innerText.trim()")
    task_schedule_str = eval_js("document.querySelector('#urmode-task-detail-modal div.tracking-wide')?.innerText.trim()")
    task_subtasks_count = eval_js("document.querySelectorAll('#urmode-task-detail-modal [id^=\"subtask-checkbox-\"]').length")
    task_has_note = eval_js("document.querySelector('#urmode-task-detail-modal div.bg-\\[\\#FAF7F4\\]') !== null")

    print(f"Task Title: '{task_detail_title}' (Expected: 'Marketing Research')")
    print(f"Task Priority/Status: '{task_detail_badge}'")
    print(f"Task Schedule/Deadline: '{task_schedule_str}'")
    print(f"Task Subtasks Count: {task_subtasks_count}")
    print(f"Task Has Notes Section: {task_has_note}")

    assert "Marketing Research" in task_detail_title, f"Task title mismatch: {task_detail_title}"
    assert task_detail_badge is not None, "Priority badge missing"
    assert task_schedule_str is not None, "Schedule string missing"

    capture_screenshot("task_detail_modal_from_notes.png")

    # -------------------------------------------------------------------------
    # TEST E: Close Task Detail Modal and Verify Return to Notes Tools
    # -------------------------------------------------------------------------
    print("\n--- TEST E: Close Task Detail Modal ---")
    eval_js("window.TempoMode.closeUrmodeTaskDetailModal()")
    time.sleep(0.4)

    is_task_modal_closed = eval_js("document.getElementById('urmode-task-detail-modal') === null")
    is_notes_screen_active = eval_js("document.getElementById('screen-tool-notes')?.classList.contains('hidden') === false")
    print(f"Is Task Detail modal closed? {is_task_modal_closed}")
    print(f"Is Notes Tools screen still active? {is_notes_screen_active}")
    assert is_task_modal_closed, "Task detail modal should be closed!"
    assert is_notes_screen_active, "User should remain on Notes Tools page!"

    # -------------------------------------------------------------------------
    # TEST F: Unavailable Task Edge Case
    # -------------------------------------------------------------------------
    print("\n--- TEST F: Unavailable Task Edge Case ---")
    eval_js("""
    (() => {
        window.TempoToolNotes.saveTaskNote('deleted_task_id_9999', 'Non-existent Task', 'Note for deleted task', null, 'Zombie Note');
    })()
    """)
    time.sleep(0.3)

    notes = eval_js("window.TempoToolNotes.getNotes()")
    zombie_note = next(n for n in notes if n.get('taskId') == 'deleted_task_id_9999')
    eval_js(f"window.TempoToolNotes.openNoteDetailModal('{zombie_note.get('id')}')")
    time.sleep(0.3)

    # In English mode:
    eval_js("document.getElementById('btn-note-view-task').click()")
    time.sleep(0.3)
    error_msg_en = eval_js("document.getElementById('note-detail-feedback')?.innerText.trim()")
    print(f"Unavailable Task Error (EN): '{error_msg_en}' (Expected: 'This task is no longer available.')")
    assert error_msg_en == "This task is no longer available.", f"Mismatch in EN error: {error_msg_en}"

    # In Vietnamese mode:
    eval_js("window.TempoI18n.setLanguage('vi')")
    time.sleep(0.3)
    eval_js("document.getElementById('btn-note-view-task').click()")
    time.sleep(0.3)
    error_msg_vi = eval_js("document.getElementById('note-detail-feedback')?.innerText.trim()")
    print(f"Unavailable Task Error (VI): '{error_msg_vi}' (Expected: 'Task này hiện không còn tồn tại.')")
    assert error_msg_vi == "Task này hiện không còn tồn tại.", f"Mismatch in VI error: {error_msg_vi}"

    eval_js("window.TempoToolNotes.closeModal()")
    time.sleep(0.2)

    print("\n=======================================================")
    print("ALL FEATURE TESTS AND EDGE CASES PASSED 100%!")
    print("=======================================================")

finally:
    if ws:
        ws.close()
    proc.terminate()
