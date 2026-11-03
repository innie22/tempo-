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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_urmode_popup_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9345

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

    # Navigate to app
    send_cmd("Page.navigate", {"url": "http://127.0.0.1:8000/"})
    
    # Wait for TempoMode
    for _ in range(30):
        ready = eval_js("typeof window.TempoMode !== 'undefined' && typeof window.TempoMode.setMode === 'function'")
        if ready:
            break
        time.sleep(0.3)

    print("Switching to URmode (Emergency)...")
    eval_js("window.TempoMode.setMode('emergency');")
    time.sleep(1.5)

    mode = eval_js("window.TempoMode ? window.TempoMode.getMode() : null")
    print("Active Mode:", mode)
    assert mode == 'emergency', f"Expected mode emergency, got {mode}"

    # Inspect rendered tasks in URmode Working Plan
    cards_info = eval_js("""
        (() => {
            const cards = Array.from(document.querySelectorAll('.urgent-timeline-item'));
            return cards.map(c => ({
                id: c.getAttribute('data-task-id'),
                title: c.querySelector('h4') ? c.querySelector('h4').textContent.trim() : null,
                badge: c.querySelector('span[class*="rounded-full"]') ? c.querySelector('span[class*="rounded-full"]').textContent.trim() : null,
                metaText: c.querySelector('.pl-6\\\\.5') ? c.querySelector('.pl-6\\\\.5').textContent.trim() : null
            }));
        })()
    """)
    print("Rendered URmode Task Cards Count:", len(cards_info))
    print("Rendered URmode Task Cards:", json.dumps(cards_info, indent=2))
    assert len(cards_info) >= 3, f"Expected at least 3 cards in URmode Working Plan, got {len(cards_info)}"

    screenshots = [
        "urmode_popup_task1_marketing_research.png",
        "urmode_popup_task2_event_proposal.png",
        "urmode_popup_task3_edit_video.png"
    ]

    # Test clicking each of the 3 cards
    for idx, card in enumerate(cards_info[:3]):
        taskId = card['id']
        expectedTitle = card['title']
        print(f"\n==================================================")
        print(f"Testing Click on Task {idx + 1}: {expectedTitle} (ID: {taskId})")
        print(f"==================================================")

        click_res = eval_js(f"""
            (() => {{
                const el = document.querySelector('.urgent-timeline-item[data-task-id="{taskId}"]');
                if (el) {{
                    el.click();
                    return {{ clicked: true }};
                }}
                return {{ clicked: false }};
            }})()
        """)
        print("Click result:", click_res)
        time.sleep(0.5)

        modal_data = eval_js("""
            (() => {
                const modal = document.getElementById('urmode-task-detail-modal');
                if (!modal) return { open: false };
                const titleEl = document.getElementById('urmode-task-modal-title');
                const subtaskEls = Array.from(modal.querySelectorAll('.plan-custom-scroll > div'));
                const noteEl = modal.querySelector('.whitespace-pre-line');
                const priorityBtn = modal.querySelector('.relative button');
                const badgeText = priorityBtn ? priorityBtn.textContent.trim().replace('▾', '').trim() : null;
                const buttons = Array.from(modal.querySelectorAll('button')).map(b => b.textContent.trim());
                return {
                    open: true,
                    title: titleEl ? titleEl.textContent.trim() : null,
                    badge: badgeText,
                    subtaskCount: subtaskEls.length,
                    subtasks: subtaskEls.map(d => d.textContent.trim()),
                    note: noteEl ? noteEl.textContent.trim() : null,
                    buttons: buttons
                };
            })()
        """)
        print("Modal inspection:", json.dumps(modal_data, indent=2))
        assert modal_data.get('open') is True, f"Modal failed to open for task {taskId}!"
        assert modal_data.get('title') == expectedTitle, f"Title mismatch! Expected {expectedTitle}, got {modal_data.get('title')}"

        # Capture screenshot for each popup
        ss = send_cmd("Page.captureScreenshot", {"format": "png"})
        ss_path = os.path.join(artifact_dir, screenshots[idx])
        with open(ss_path, "wb") as f:
            f.write(base64.b64decode(ss["data"]))
        print(f"Saved {screenshots[idx]}")

        # Close modal
        eval_js("""
            (() => {
                const closeBtn = document.querySelector('#urmode-task-detail-modal button[aria-label="Close task details"]');
                if (closeBtn) closeBtn.click();
            })()
        """)
        time.sleep(0.3)
        modal_after = eval_js("!!document.getElementById('urmode-task-detail-modal')")
        assert not modal_after, f"Modal failed to close for task {taskId}!"

    # 4. Test In-Modal Actions on Task 1 (Marketing Research)
    print("\n--- Testing In-Modal Actions (Title Edit, Subtask, Note) ---")
    eval_js("window.TempoMode.openUrmodeTaskDetailModal('task-marketing-research');")
    time.sleep(0.5)

    # A. Add subtask
    eval_js("window.TempoMode.toggleUrmodeDetailAddSubtask();")
    time.sleep(0.2)
    eval_js("""
        (() => {
            const input = document.getElementById('urmode-new-subtask-title');
            if (input) input.value = 'Subtask 7: Final Slide Review';
        })()
    """)
    eval_js("window.TempoMode.addUrmodeDetailSubtask('task-marketing-research');")
    time.sleep(0.5)

    subtask_count = eval_js("document.querySelectorAll('#urmode-task-detail-modal .plan-custom-scroll > div').length")
    print("Subtask count after adding:", subtask_count)
    assert subtask_count == 7, f"Expected 7 subtasks, got {subtask_count}"

    # B. Edit Title
    eval_js("window.TempoMode.toggleUrmodeDetailTitleEdit();")
    time.sleep(0.2)
    eval_js("""
        (() => {
            const input = document.getElementById('urmode-edit-title-input');
            if (input) input.value = 'Marketing Research (Updated)';
        })()
    """)
    eval_js("window.TempoMode.saveUrmodeDetailTitleEdit('task-marketing-research');")
    time.sleep(0.5)

    updated_title = eval_js("document.getElementById('urmode-task-modal-title').textContent.trim()")
    print("Updated title in modal:", updated_title)
    assert updated_title == 'Marketing Research (Updated)', f"Title update failed! Got {updated_title}"

    # Capture edited modal screenshot
    ss_edit = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "urmode_popup_subtasks_edit.png"), "wb") as f:
        f.write(base64.b64decode(ss_edit["data"]))
    print("Saved urmode_popup_subtasks_edit.png")

    # Close modal
    eval_js("window.TempoMode.closeUrmodeTaskDetailModal();")
    time.sleep(0.5)

    # 5. Test Mark as Done from inside modal & Done section
    print("\n--- Testing In-Modal Mark as Done & Done Section ---")
    eval_js("window.TempoMode.openUrmodeTaskDetailModal('task-event-proposal');")
    time.sleep(0.5)

    # Click 'Mark as done'
    eval_js("window.TempoMode.toggleUrmodeDetailTaskComplete('task-event-proposal');")
    time.sleep(0.5)

    done_modal_data = eval_js("""
        (() => {
            const modal = document.getElementById('urmode-task-detail-modal');
            const titleEl = document.getElementById('urmode-task-modal-title');
            const activeBtn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.trim() === 'Mark as active');
            const badge = modal.querySelector('.relative button') ? modal.querySelector('.relative button').textContent.trim() : null;
            return {
                isStrikethrough: titleEl ? titleEl.classList.contains('line-through') : false,
                hasActiveBtn: !!activeBtn,
                badge: badge
            };
        })()
    """)
    print("Modal state after Mark as done:", json.dumps(done_modal_data, indent=2))
    assert done_modal_data['hasActiveBtn'] is True, "Missing 'Mark as active' button!"
    assert done_modal_data['isStrikethrough'] is True, "Expected strikethrough title!"

    # Capture completed modal screenshot
    ss_done = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "urmode_popup_task_done.png"), "wb") as f:
        f.write(base64.b64decode(ss_done["data"]))
    print("Saved urmode_popup_task_done.png")

    # Close modal
    eval_js("window.TempoMode.closeUrmodeTaskDetailModal();")
    time.sleep(0.5)

    # Verify task is in the Done section of the dashboard
    done_section_info = eval_js("""
        (() => {
            const doneSection = document.querySelector('[data-tempo-ui="urmode-done-section"]');
            const doneCard = document.querySelector('.urgent-timeline-item[data-task-id="task-event-proposal"]');
            const isLineThrough = doneCard && doneCard.querySelector('h4') ? doneCard.querySelector('h4').classList.contains('line-through') : false;
            return {
                hasDoneSection: !!doneSection,
                doneSectionText: doneSection ? doneSection.textContent.trim() : null,
                hasDoneCard: !!doneCard,
                isLineThrough: isLineThrough
            };
        })()
    """)
    print("Dashboard Done section check:", json.dumps(done_section_info, indent=2))
    assert done_section_info['hasDoneSection'] is True, "Done section not found on dashboard!"
    assert done_section_info['hasDoneCard'] is True, "Event Proposal card not found in Done section!"
    assert done_section_info['isLineThrough'] is True, "Done card not struck through!"

    # Click the done card from the dashboard
    eval_js("""
        (() => {
            const doneCard = document.querySelector('.urgent-timeline-item[data-task-id="task-event-proposal"]');
            if (doneCard) doneCard.click();
        })()
    """)
    time.sleep(0.5)

    opened_from_done = eval_js("!!document.getElementById('urmode-task-detail-modal')")
    assert opened_from_done is True, "Failed to open modal from Done section card!"

    # Click 'Mark as active'
    eval_js("window.TempoMode.toggleUrmodeDetailTaskComplete('task-event-proposal');")
    time.sleep(0.5)

    eval_js("window.TempoMode.closeUrmodeTaskDetailModal();")
    time.sleep(0.5)

    # 6. Test Direct Checkbox Click: MUST NOT open modal
    print("\n--- Testing Direct Checkbox Click ---")
    chk_res = eval_js("""
        (() => {
            const chkBtn = document.querySelector('.urgent-timeline-item[data-task-id="task-edit-video"] button[data-task-toggle]');
            if (chkBtn) {
                chkBtn.click();
                const modal = document.getElementById('urmode-task-detail-modal');
                return { clicked: true, modalOpened: !!modal };
            }
            return { clicked: false };
        })()
    """)
    print("Checkbox click result:", chk_res)
    assert chk_res['clicked'] is True, "Checkbox button not found!"
    assert chk_res['modalOpened'] is False, "Checkbox click erroneously opened the modal!"

    # Toggle back
    eval_js("""
        (() => {
            const chkBtn = document.querySelector('.urgent-timeline-item[data-task-id="task-edit-video"] button[data-task-toggle]');
            if (chkBtn) chkBtn.click();
        })()
    """)
    time.sleep(0.5)

    # 7. Test Escape key dismissal
    print("\n--- Testing Escape Key Dismissal ---")
    eval_js("window.TempoMode.openUrmodeTaskDetailModal('task-edit-video');")
    time.sleep(0.5)
    modal_opened = eval_js("!!document.getElementById('urmode-task-detail-modal')")
    assert modal_opened is True, "Failed to open modal for Escape test!"

    # Send Escape key
    send_cmd("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
    send_cmd("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
    time.sleep(0.3)
    modal_after_esc = eval_js("!!document.getElementById('urmode-task-detail-modal')")
    print("Modal after Escape:", modal_after_esc)
    assert not modal_after_esc, "Modal failed to close on Escape key!"

    # 8. Test Backdrop Click dismissal
    print("\n--- Testing Backdrop Click Dismissal ---")
    eval_js("window.TempoMode.openUrmodeTaskDetailModal('task-edit-video');")
    time.sleep(0.5)
    eval_js("""
        (() => {
            const backdrop = document.getElementById('urmode-task-detail-modal');
            if (backdrop) backdrop.click();
        })()
    """)
    time.sleep(0.3)
    modal_after_bd = eval_js("!!document.getElementById('urmode-task-detail-modal')")
    print("Modal after backdrop click:", modal_after_bd)
    assert not modal_after_bd, "Modal failed to close on backdrop click!"

    # Capture final overview of dashboard
    ss_dash = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "urmode_dashboard_all_cards.png"), "wb") as f:
        f.write(base64.b64decode(ss_dash["data"]))
    print("Saved urmode_dashboard_all_cards.png")

    # 9. Regression check: Test Recovery Mode (Rmode) still opens its popup
    print("\n--- Testing Rmode Regression ---")
    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(1.5)
    rmode_cards = eval_js("document.querySelectorAll('#recovery-working-plan [data-task-id]').length")
    print("Rmode cards count:", rmode_cards)
    assert rmode_cards == 3, f"Expected 3 cards in Rmode, got {rmode_cards}"

    eval_js("window.TempoMode.openRmodeTaskDetailModal('task-marketing-research');")
    time.sleep(0.5)
    rmode_modal_open = eval_js("!!document.getElementById('rmode-task-detail-modal')")
    print("Rmode modal open:", rmode_modal_open)
    assert rmode_modal_open is True, "Rmode modal failed to open!"
    eval_js("window.TempoMode.closeRmodeTaskDetailModal();")

    print("\n==================================================")
    print("ALL URMODE TESTS PASSED! RMODE REGRESSION CLEAN!")
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
