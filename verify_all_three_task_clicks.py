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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_3_tasks_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9330

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,900"
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
                pages = [t for t in tabs if t.get("type") == "page" and not t.get("url", "").startswith("chrome-extension://")]
                if pages:
                    ws_url = pages[0]["webSocketDebuggerUrl"]
                    break
        except Exception:
            time.sleep(0.5)

    if not ws_url:
        raise RuntimeError("Failed to connect to Edge CDP")

    print(f"Connected to Edge CDP at {ws_url}")
    ws = websocket.create_connection(ws_url)

    # Navigate directly to the app
    send_cmd("Page.navigate", {"url": "http://127.0.0.1:8000/"})
    
    # Wait for window.TempoMode to be available
    for _ in range(30):
        ready = eval_js("typeof window.TempoMode !== 'undefined' && typeof window.TempoMode.setMode === 'function'")
        if ready:
            break
        time.sleep(0.3)

    # Switch to Recovery Mode
    eval_js("""
        if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
            window.TempoMode.setMode('recovery');
        }
    """)
    time.sleep(1.5)

    mode = eval_js("window.TempoMode ? window.TempoMode.getMode() : null")
    print("Active Mode:", mode)

    # Inspect all rendered task cards in recovery plan
    cards_info = eval_js("""
        (() => {
            const cards = Array.from(document.querySelectorAll('#recovery-working-plan [data-task-id]'));
            return cards.map(c => ({
                id: c.getAttribute('data-task-id'),
                title: c.querySelector('h5') ? c.querySelector('h5').textContent.trim() : null,
                timeHeader: c.querySelector('div.font-bold') ? c.querySelector('div.font-bold').textContent.trim() : null,
                dueDate: c.querySelectorAll('p')[0] ? c.querySelectorAll('p')[0].textContent.trim() : null,
                subtasksText: c.querySelectorAll('p')[1] ? c.querySelectorAll('p')[1].textContent.trim() : null,
                tag: c.querySelector('span') ? c.querySelector('span').textContent.trim() : null
            }));
        })()
    """)
    print("Rendered Cards Count:", len(cards_info))
    print("Rendered Cards Details:", json.dumps(cards_info, indent=2))

    assert len(cards_info) == 3, f"Expected 3 cards, got {len(cards_info)}"

    screenshot_names = [
        "rmode_popup_task1_marketing_research.png",
        "rmode_popup_task2_event_proposal.png",
        "rmode_popup_task3_edit_video.png"
    ]

    for idx, c in enumerate(cards_info):
        taskId = c['id']
        expectedTitle = c['title']
        print(f"\n==================================================")
        print(f"Testing Click on Task {idx + 1}: {expectedTitle} (ID: {taskId})")
        print(f"==================================================")

        # 1. Click the task card
        click_res = eval_js(f"""
            (() => {{
                const card = document.querySelector('#recovery-working-plan [data-task-id="{taskId}"] [role="button"]');
                if (card) {{
                    card.click();
                    return {{ clicked: true }};
                }}
                return {{ clicked: false }};
            }})()
        """)
        print(f"Card click result:", click_res)
        time.sleep(0.5)

        # 2. Verify modal opened with correct task data
        modal_data = eval_js("""
            (() => {
                const modal = document.getElementById('rmode-task-detail-modal');
                if (!modal) return { open: false };
                const titleEl = document.getElementById('rmode-task-modal-title');
                const scheduleEl = modal.querySelector('p.font-bold') || modal.querySelector('.font-bold');
                const subtaskEls = Array.from(modal.querySelectorAll('.plan-custom-scroll > div'));
                const subtasks = subtaskEls.map(d => d.textContent.trim());
                const noteEl = modal.querySelector('.whitespace-pre-line');
                const priorityBtn = modal.querySelector('.relative button');
                const badgeText = priorityBtn ? priorityBtn.textContent.trim().replace('▾', '').trim() : null;
                const buttons = Array.from(modal.querySelectorAll('button')).map(b => b.textContent.trim());
                return {
                    open: true,
                    title: titleEl ? titleEl.textContent.trim() : null,
                    schedule: scheduleEl ? scheduleEl.textContent.trim() : null,
                    badge: badgeText,
                    subtaskCount: subtasks.length,
                    subtasks: subtasks,
                    note: noteEl ? noteEl.textContent.trim() : null,
                    hasButtons: buttons.length > 0
                };
            })()
        """)
        print("Modal inspection:", json.dumps(modal_data, indent=2))

        assert modal_data.get('open') is True, f"Modal failed to open for task {taskId}!"
        assert modal_data.get('title') == expectedTitle, f"Title mismatch! Expected {expectedTitle}, got {modal_data.get('title')}"

        # Capture screenshot for each popup
        ss = send_cmd("Page.captureScreenshot", {"format": "png"})
        ss_path = os.path.join(artifact_dir, screenshot_names[idx])
        with open(ss_path, "wb") as f:
            f.write(base64.b64decode(ss["data"]))
        print(f"Saved {screenshot_names[idx]}")

        # Close modal
        close_res = eval_js("""
            (() => {
                const closeBtn = document.querySelector('#rmode-task-detail-modal button[aria-label="Close task details"]');
                if (closeBtn) {
                    closeBtn.click();
                    return { closed: true };
                }
                return { closed: false };
            })()
        """)
        time.sleep(0.3)
        modal_after = eval_js("!!document.getElementById('rmode-task-detail-modal')")
        assert not modal_after, f"Modal failed to close for task {taskId}!"

    # 3. Test TASK DONE column popup opening
    print("\n--- Testing TASK DONE Column Popup ---")
    # Mark task 2 ("task-event-proposal") as done
    eval_js("""
        (() => {
            const card2 = document.querySelector('#recovery-working-plan [data-task-id="task-event-proposal"] [role="button"]');
            if (card2) card2.click();
        })()
    """)
    time.sleep(0.5)

    eval_js("""
        (() => {
            const markDoneBtn = Array.from(document.querySelectorAll('#rmode-task-detail-modal button'))
                .find(b => b.textContent.trim() === 'Mark as done');
            if (markDoneBtn) markDoneBtn.click();
        })()
    """)
    time.sleep(0.5)

    # Close modal
    eval_js("window.TempoMode.closeRmodeTaskDetailModal();")
    time.sleep(0.5)

    # Verify task 2 is now in TASK DONE column
    done_col_info = eval_js("""
        (() => {
            const doneCol = document.querySelector('[data-tempo-column="done"]');
            const doneCard = doneCol ? doneCol.querySelector('[data-task-id="task-event-proposal"]') : null;
            return {
                doneCardPresent: !!doneCard,
                doneCardTitle: doneCard && doneCard.querySelector('h5') ? doneCard.querySelector('h5').textContent.trim() : null
            };
        })()
    """)
    print("Done column check:", json.dumps(done_col_info, indent=2))
    assert done_col_info['doneCardPresent'] is True, "Task 2 not found in TASK DONE column!"

    # Click task 2 in TASK DONE column to open modal
    eval_js("""
        (() => {
            const doneCard = document.querySelector('[data-tempo-column="done"] [data-task-id="task-event-proposal"] [role="button"]');
            if (doneCard) doneCard.click();
        })()
    """)
    time.sleep(0.5)

    done_modal_data = eval_js("""
        (() => {
            const modal = document.getElementById('rmode-task-detail-modal');
            if (!modal) return { open: false };
            const titleEl = document.getElementById('rmode-task-modal-title');
            const activeBtn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.trim() === 'Mark as active');
            const badge = modal.querySelector('.relative button') ? modal.querySelector('.relative button').textContent.trim() : null;
            return {
                open: true,
                title: titleEl ? titleEl.textContent.trim() : null,
                isTitleStrikethrough: titleEl ? titleEl.classList.contains('line-through') : false,
                hasMarkAsActiveBtn: !!activeBtn,
                badge: badge
            };
        })()
    """)
    print("Done task modal data:", json.dumps(done_modal_data, indent=2))
    assert done_modal_data['open'] is True, "Modal failed to open from TASK DONE column!"
    assert done_modal_data['title'] == 'Event Proposal', "Done task modal title mismatch!"
    assert done_modal_data['hasMarkAsActiveBtn'] is True, "Missing 'Mark as active' button in completed task modal!"

    # Capture screenshot of completed task modal
    ss_done = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "rmode_popup_task_done.png"), "wb") as f:
        f.write(base64.b64decode(ss_done["data"]))
    print("Saved rmode_popup_task_done.png")

    # Mark back as active
    eval_js("""
        (() => {
            const activeBtn = Array.from(document.querySelectorAll('#rmode-task-detail-modal button'))
                .find(b => b.textContent.trim() === 'Mark as active');
            if (activeBtn) activeBtn.click();
        })()
    """)
    time.sleep(0.5)

    # Close modal
    eval_js("window.TempoMode.closeRmodeTaskDetailModal();")
    time.sleep(0.5)

    # 4. Direct checkbox click test: must NOT open modal
    print("\n--- Testing Direct Checkbox Click ---")
    direct_chk_res = eval_js("""
        (() => {
            const chk = document.querySelector('#recovery-working-plan [data-task-id="task-edit-video"] button[data-task-toggle]');
            if (chk) {
                chk.click();
                const modal = document.getElementById('rmode-task-detail-modal');
                return { clicked: true, modalOpened: !!modal };
            }
            return { clicked: false };
        })()
    """)
    print("Direct checkbox click result:", direct_chk_res)
    assert direct_chk_res['clicked'] is True, "Checkbox not found or not clicked!"
    assert direct_chk_res['modalOpened'] is False, "Checkbox click erroneously opened modal!"

    # Revert completion
    eval_js("""
        (() => {
            const chk = document.querySelector('#recovery-working-plan [data-task-id="task-edit-video"] button[data-task-toggle]');
            if (chk) chk.click();
        })()
    """)
    time.sleep(0.5)

    # Capture final overview of dashboard
    ss_dash = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "rmode_dashboard_all_cards.png"), "wb") as f:
        f.write(base64.b64decode(ss_dash["data"]))
    print("Saved rmode_dashboard_all_cards.png")

    print("\n==================================================")
    print("ALL 3 TASKS VERIFIED: ALL OPEN POPUPS WITH CORRECT DATA!")
    print("==================================================")

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
