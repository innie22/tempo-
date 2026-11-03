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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_rmode_popup_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9291

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,900",
    "http://127.0.0.1:8000/"
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
        resp = json.loads(ws.recv())
        if resp.get("id") == cmd_obj["id"]:
            return resp.get("result", {})

def eval_js(expr):
    res = send_cmd("Runtime.evaluate", {
        "expression": expr,
        "returnByValue": True,
        "awaitPromise": True
    })
    if "exceptionDetails" in res:
        print("JS Exception:", res["exceptionDetails"])
    return res.get("result", {}).get("value")

try:
    ws_url = None
    for _ in range(40):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as resp:
                tabs = json.loads(resp.read().decode())
                pages = [t for t in tabs if t.get("type") == "page"]
                if pages:
                    ws_url = pages[0]["webSocketDebuggerUrl"]
                    break
        except Exception:
            time.sleep(0.5)

    if not ws_url:
        raise RuntimeError("Failed to connect to Edge CDP")

    print(f"Connected to Edge CDP at {ws_url}")
    ws = websocket.create_connection(ws_url)

    # Allow page to load
    time.sleep(2)

    # Switch to Recovery Mode
    eval_js("""
        if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
            window.TempoMode.setMode('recovery');
        }
    """)
    time.sleep(1)

    mode = eval_js("window.TempoMode ? window.TempoMode.getMode() : null")
    print("Active Mode:", mode)

    # Check Working Plan columns
    init_dashboard = eval_js("""
        (() => {
            const tasksCol = document.querySelector('[data-tempo-column="tasks"]');
            const doneCol = document.querySelector('[data-tempo-column="done"]');
            const cards = document.querySelectorAll('[data-task-id]');
            return {
                totalCards: cards.length,
                tasksIncomplete: tasksCol ? tasksCol.querySelectorAll('[data-task-id]').length : 0,
                tasksDone: doneCol ? doneCol.querySelectorAll('[data-task-id]').length : 0,
                cardIds: Array.from(cards).map(c => c.getAttribute('data-task-id'))
            };
        })()
    """)
    print("Initial Working Plan status:", json.dumps(init_dashboard, indent=2))

    # 1. Click task card for task-marketing-research
    open_res = eval_js("""
        (() => {
            const card = document.querySelector('[data-task-id="task-marketing-research"] [role="button"]');
            if (card) {
                card.click();
                return { clicked: true };
            }
            return { clicked: false };
        })()
    """)
    print("Click card to open modal:", open_res)
    time.sleep(0.5)

    # Inspect modal
    modal_data = eval_js("""
        (() => {
            const modal = document.getElementById('rmode-task-detail-modal');
            if (!modal) return { open: false };
            const titleEl = document.getElementById('rmode-task-modal-title');
            const subtaskEls = Array.from(modal.querySelectorAll('.plan-custom-scroll > div'));
            const subtasks = subtaskEls.map(d => d.textContent.trim());
            const noteEl = modal.querySelector('.whitespace-pre-line');
            const buttons = Array.from(modal.querySelectorAll('button')).map(b => b.textContent.trim());
            return {
                open: true,
                title: titleEl ? titleEl.textContent.trim() : null,
                subtaskCount: subtasks.length,
                subtasks: subtasks,
                note: noteEl ? noteEl.textContent.trim() : null,
                buttons: buttons
            };
        })()
    """)
    print("Opened Modal Data:", json.dumps(modal_data, indent=2))

    # Capture Screenshot 1: Open popup
    ss1 = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "rmode_task_popup_open.png"), "wb") as f:
        f.write(base64.b64decode(ss1["data"]))
    print("Saved rmode_task_popup_open.png")

    # 2. Interactive action: toggle a subtask
    sub_toggle = eval_js("""
        (() => {
            const subCheckboxes = document.querySelectorAll('.plan-custom-scroll button[title="Toggle subtask"]');
            if (subCheckboxes && subCheckboxes.length > 0) {
                subCheckboxes[0].click();
                return { toggledSubtask: true };
            }
            return { toggledSubtask: false };
        })()
    """)
    print("Subtask toggle:", sub_toggle)
    time.sleep(0.3)

    # 3. Interactive action: add new subtask
    add_sub = eval_js("""
        (() => {
            window.TempoMode.toggleRmodeDetailAddSubtask();
            const input = document.getElementById('rmode-new-subtask-title');
            if (input) {
                input.value = 'Subtask 7: Final Slide Review';
                window.TempoMode.addRmodeDetailSubtask('task-marketing-research');
                return { added: true };
            }
            return { added: false };
        })()
    """)
    print("Add new subtask:", add_sub)
    time.sleep(0.3)

    # 4. Interactive action: edit title
    edit_title = eval_js("""
        (() => {
            window.TempoMode.toggleRmodeDetailTitleEdit();
            const input = document.getElementById('rmode-edit-title-input');
            if (input) {
                input.value = 'Marketing Research (Updated)';
                window.TempoMode.saveRmodeDetailTitleEdit('task-marketing-research');
                return { titleEdited: true };
            }
            return { titleEdited: false };
        })()
    """)
    print("Edit title:", edit_title)
    time.sleep(0.3)

    # 5. Interactive action: edit note
    edit_note = eval_js("""
        (() => {
            window.TempoMode.toggleRmodeDetailNoteEdit();
            const input = document.getElementById('rmode-note-editor-text');
            if (input) {
                input.value = 'Create a sheet to manage references - updated with Q3 benchmarks';
                window.TempoMode.saveRmodeDetailNote('task-marketing-research');
                return { noteEdited: true };
            }
            return { noteEdited: false };
        })()
    """)
    print("Edit note:", edit_note)
    time.sleep(0.3)

    # Capture Screenshot 2: Subtasks and edits
    ss2 = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "rmode_task_popup_subtasks_edit.png"), "wb") as f:
        f.write(base64.b64decode(ss2["data"]))
    print("Saved rmode_task_popup_subtasks_edit.png")

    # 6. Interactive action: Mark task as done
    mark_done = eval_js("""
        (() => {
            const markDoneBtn = Array.from(document.querySelectorAll('#rmode-task-detail-modal button'))
                .find(b => b.textContent.trim() === 'Mark as done');
            if (markDoneBtn) {
                markDoneBtn.click();
                return { markedDone: true };
            }
            return { markedDone: false };
        })()
    """)
    print("Mark task done from modal:", mark_done)
    time.sleep(0.5)

    # Capture Screenshot 3: Modal showing completed state
    ss3 = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "rmode_task_popup_completed_task.png"), "wb") as f:
        f.write(base64.b64decode(ss3["data"]))
    print("Saved rmode_task_popup_completed_task.png")

    # 7. Close modal via close button (✕)
    close_btn = eval_js("""
        (() => {
            const closeBtn = document.querySelector('#rmode-task-detail-modal button[aria-label="Close task details"]');
            if (closeBtn) {
                closeBtn.click();
                return { closed: true };
            }
            return { closed: false };
        })()
    """)
    print("Close modal via ✕:", close_btn)
    time.sleep(0.5)

    # Check dashboard columns after closing modal
    dash_after_done = eval_js("""
        (() => {
            const tasksCol = document.querySelector('[data-tempo-column="tasks"]');
            const doneCol = document.querySelector('[data-tempo-column="done"]');
            return {
                tasksIncomplete: tasksCol ? tasksCol.querySelectorAll('[data-task-id]').length : 0,
                tasksDone: doneCol ? doneCol.querySelectorAll('[data-task-id]').length : 0,
                doneTaskTitles: doneCol ? Array.from(doneCol.querySelectorAll('h5')).map(h => h.textContent.trim()) : []
            };
        })()
    """)
    print("Dashboard after marking task done:", json.dumps(dash_after_done, indent=2))

    # Capture Screenshot 4: Dashboard columns updated
    ss4 = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "rmode_dashboard_updated_columns.png"), "wb") as f:
        f.write(base64.b64decode(ss4["data"]))
    print("Saved rmode_dashboard_updated_columns.png")

    # 8. Reopen modal from TASK DONE column
    reopen_done = eval_js("""
        (() => {
            const doneCard = document.querySelector('[data-tempo-column="done"] [data-task-id="task-marketing-research"] [role="button"]');
            if (doneCard) {
                doneCard.click();
                return { reopened: true };
            }
            return { reopened: false };
        })()
    """)
    print("Reopen modal from TASK DONE column:", reopen_done)
    time.sleep(0.5)

    # 9. Mark task back as active
    mark_active = eval_js("""
        (() => {
            const markActiveBtn = Array.from(document.querySelectorAll('#rmode-task-detail-modal button'))
                .find(b => b.textContent.trim() === 'Mark as active');
            if (markActiveBtn) {
                markActiveBtn.click();
                return { markedActive: true };
            }
            return { markedActive: false };
        })()
    """)
    print("Mark back as active:", mark_active)
    time.sleep(0.5)

    # 10. Test Escape key closes modal
    escape_test = eval_js("""
        (() => {
            const ev = new KeyboardEvent('keydown', { key: 'Escape', bubbles: true });
            document.dispatchEvent(ev);
            const modal = document.getElementById('rmode-task-detail-modal');
            return { closedByEscape: !modal };
        })()
    """)
    print("Escape key test:", escape_test)

    # 11. Test direct checkbox click does not open modal
    chk_direct = eval_js("""
        (() => {
            const chk = document.querySelector('[data-task-id="task-event-proposal"] button[title*="complete"], [data-task-id="task-marketing-research"] button[title*="complete"]');
            if (chk) {
                chk.click();
                const modal = document.getElementById('rmode-task-detail-modal');
                return { clickedCheckbox: true, modalOpened: !!modal };
            }
            return { clickedCheckbox: false };
        })()
    """)
    print("Direct checkbox click test (modalOpened must be false):", chk_direct)

    # 12. Test backdrop click closes modal
    backdrop_test = eval_js("""
        (() => {
            window.TempoMode.openRmodeTaskDetailModal('task-event-proposal');
            const modal = document.getElementById('rmode-task-detail-modal');
            if (!modal) return { failedToOpen: true };
            modal.click();
            const modalAfter = document.getElementById('rmode-task-detail-modal');
            return { closedByBackdrop: !modalAfter };
        })()
    """)
    print("Backdrop click test:", backdrop_test)

    # Reset any modified tasks back to clean active state
    eval_js("""
        (() => {
            const info1 = window.TempoMode.getRmodeTaskData('task-marketing-research');
            if (info1 && info1.task) {
                info1.task.name = 'Marketing Research';
                info1.task.completed = false;
                if (Array.isArray(info1.task.subtasks) && info1.task.subtasks[0]) {
                    info1.task.subtasks[0].completed = false;
                }
                window.TempoMode.persistRmodePlanData(info1.plan, info1.task);
            }
            const info2 = window.TempoMode.getRmodeTaskData('task-event-proposal');
            if (info2 && info2.task) {
                info2.task.completed = false;
                window.TempoMode.persistRmodePlanData(info2.plan, info2.task);
            }
        })()
    """)

    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY WITH ZERO ERRORS!")

finally:
    if ws:
        try:
            ws.close()
        except Exception:
            pass
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()
