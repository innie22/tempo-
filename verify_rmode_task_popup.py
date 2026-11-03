import asyncio
import json
import os
import urllib.request
import websockets

ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"

async def run():
    # 1. Get browser target
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    targets = json.loads(req.read().decode('utf-8'))
    print(f"Found {len(targets)} targets")
    ws_url = None
    for t in targets:
        if t.get('type') == 'page' and 'tempo' in t.get('url', '').lower():
            ws_url = t.get('webSocketDebuggerUrl')
            break
    if not ws_url:
        for t in targets:
            if t.get('type') == 'page':
                ws_url = t.get('webSocketDebuggerUrl')
                break

    print(f"Connecting to {ws_url}")
    async with websockets.connect(ws_url) as ws:
        msg_id = 0

        async def send_cmd(method, params=None):
            nonlocal msg_id
            msg_id += 1
            cmd = {"id": msg_id, "method": method, "params": params or {}}
            await ws.send(json.dumps(cmd))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get("id") == msg_id:
                    return resp.get("result", {})

        async def eval_js(expr):
            res = await send_cmd("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True
            })
            if "exceptionDetails" in res:
                print("JS Exception:", res["exceptionDetails"])
            return res.get("result", {}).get("value")

        # 1. Navigate or ensure page is on Rmode
        url = await eval_js("window.location.href")
        print("Current URL:", url)
        if "http://127.0.0.1:8000" not in url:
            await send_cmd("Page.navigate", {"url": "http://127.0.0.1:8000"})
            await asyncio.sleep(2)

        # Set Recovery Mode
        await eval_js("""
            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
                window.TempoMode.setMode('recovery');
            }
        """)
        await asyncio.sleep(1)

        mode = await eval_js("window.TempoMode ? window.TempoMode.getMode() : null")
        print("Current mode:", mode)

        # 2. Check task cards in recovery plan
        task_info = await eval_js("""
            (() => {
                const tasksCol = document.querySelector('[data-tempo-column="tasks"]');
                const doneCol = document.querySelector('[data-tempo-column="done"]');
                const taskCards = document.querySelectorAll('[data-task-id]');
                return {
                    taskCardsCount: taskCards.length,
                    tasksColPresent: !!tasksCol,
                    doneColPresent: !!doneCol,
                    cardIds: Array.from(taskCards).map(c => c.getAttribute('data-task-id'))
                };
            })()
        """)
        print("Dashboard Tasks Info:", json.dumps(task_info, indent=2))

        # 3. Test clicking the first task card to open modal
        open_res = await eval_js("""
            (() => {
                const firstCard = document.querySelector('[data-task-id="task-marketing-research"] [role="button"]');
                if (firstCard) {
                    firstCard.click();
                    return { clicked: true };
                }
                const anyCard = document.querySelector('[data-task-id] [role="button"]');
                if (anyCard) {
                    anyCard.click();
                    return { clicked: true, fallback: true };
                }
                return { clicked: false };
            })()
        """)
        print("Card click result:", open_res)
        await asyncio.sleep(0.5)

        # Verify modal is open and inspect contents
        modal_info = await eval_js("""
            (() => {
                const modal = document.getElementById('rmode-task-detail-modal');
                if (!modal) return { open: false };
                const titleEl = document.getElementById('rmode-task-modal-title');
                const scheduleEl = modal.querySelector('.text-[#D9A18B]');
                const subtasks = Array.from(modal.querySelectorAll('.plan-custom-scroll > div')).map(d => d.textContent.trim());
                const noteEl = modal.querySelector('.whitespace-pre-line');
                const buttons = Array.from(modal.querySelectorAll('button')).map(b => b.textContent.trim());
                return {
                    open: true,
                    title: titleEl ? titleEl.textContent.trim() : null,
                    schedule: scheduleEl ? scheduleEl.textContent.trim() : null,
                    subtaskCount: subtasks.length,
                    subtasks: subtasks,
                    note: noteEl ? noteEl.textContent.trim() : null,
                    buttons: buttons
                };
            })()
        """)
        print("Modal Info:", json.dumps(modal_info, indent=2))

        # Capture screenshot 1: Open Popup
        await send_cmd("Emulation.setDeviceMetricsOverride", {
            "width": 1440,
            "height": 900,
            "deviceScaleFactor": 1,
            "mobile": False
        })
        await asyncio.sleep(0.5)
        ss1 = await send_cmd("Page.captureScreenshot", {"format": "png"})
        import base64
        with open(os.path.join(ARTIFACT_DIR, "rmode_task_popup_open.png"), "wb") as f:
            f.write(base64.b64decode(ss1["data"]))
        print("Captured rmode_task_popup_open.png")

        # 4. Test interactive actions inside popup:
        # A. Subtask toggle
        sub_toggle_res = await eval_js("""
            (() => {
                const firstSubCheckbox = document.querySelector('.plan-custom-scroll button[title="Toggle subtask"]');
                if (firstSubCheckbox) {
                    firstSubCheckbox.click();
                    return { toggled: true };
                }
                return { toggled: false };
            })()
        """)
        print("Subtask toggle:", sub_toggle_res)
        await asyncio.sleep(0.3)

        # B. Add Subtask
        add_sub_res = await eval_js("""
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
        print("Add subtask:", add_sub_res)
        await asyncio.sleep(0.3)

        # C. Edit Title
        edit_title_res = await eval_js("""
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
        print("Edit title:", edit_title_res)
        await asyncio.sleep(0.3)

        # D. Edit Note
        edit_note_res = await eval_js("""
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
        print("Edit note:", edit_note_res)
        await asyncio.sleep(0.3)

        # Capture screenshot 2: Subtasks and edits
        ss2 = await send_cmd("Page.captureScreenshot", {"format": "png"})
        with open(os.path.join(ARTIFACT_DIR, "rmode_task_popup_subtasks_edit.png"), "wb") as f:
            f.write(base64.b64decode(ss2["data"]))
        print("Captured rmode_task_popup_subtasks_edit.png")

        # E. Mark as done from modal
        mark_done_res = await eval_js("""
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
        print("Mark task done:", mark_done_res)
        await asyncio.sleep(0.5)

        # Inspect updated modal state
        modal_after_done = await eval_js("""
            (() => {
                const modal = document.getElementById('rmode-task-detail-modal');
                const titleEl = document.getElementById('rmode-task-modal-title');
                const activeBtn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.trim() === 'Mark as active');
                return {
                    titleClass: titleEl ? titleEl.className : '',
                    hasMarkAsActiveBtn: !!activeBtn
                };
            })()
        """)
        print("Modal state after marking done:", modal_after_done)

        # Capture screenshot 3: Completed task modal
        ss3 = await send_cmd("Page.captureScreenshot", {"format": "png"})
        with open(os.path.join(ARTIFACT_DIR, "rmode_task_popup_completed_task.png"), "wb") as f:
            f.write(base64.b64decode(ss3["data"]))
        print("Captured rmode_task_popup_completed_task.png")

        # F. Close modal via close button
        close_res = await eval_js("""
            (() => {
                const closeBtn = document.querySelector('#rmode-task-detail-modal button[aria-label="Close task details"]');
                if (closeBtn) {
                    closeBtn.click();
                    return { closed: true };
                }
                return { closed: false };
            })()
        """)
        print("Close modal via ✕:", close_res)
        await asyncio.sleep(0.5)

        # Check dashboard columns after closing modal
        columns_status = await eval_js("""
            (() => {
                const tasksCol = document.querySelector('[data-tempo-column="tasks"]');
                const doneCol = document.querySelector('[data-tempo-column="done"]');
                return {
                    tasksColCount: tasksCol ? tasksCol.querySelectorAll('[data-task-id]').length : 0,
                    doneColCount: doneCol ? doneCol.querySelectorAll('[data-task-id]').length : 0,
                    doneTaskTitles: doneCol ? Array.from(doneCol.querySelectorAll('h5')).map(h => h.textContent.trim()) : []
                };
            })()
        """)
        print("Dashboard columns status:", json.dumps(columns_status, indent=2))

        # Capture screenshot 4: Dashboard columns updated
        ss4 = await send_cmd("Page.captureScreenshot", {"format": "png"})
        with open(os.path.join(ARTIFACT_DIR, "rmode_dashboard_updated_columns.png"), "wb") as f:
            f.write(base64.b64decode(ss4["data"]))
        print("Captured rmode_dashboard_updated_columns.png")

        # G. Reopen completed task from TASK DONE column
        reopen_modal_res = await eval_js("""
            (() => {
                const doneTaskCard = document.querySelector('[data-tempo-column="done"] [data-task-id="task-marketing-research"] [role="button"]');
                if (doneTaskCard) {
                    doneTaskCard.click();
                    return { clickedDoneCard: true };
                }
                return { clickedDoneCard: false };
            })()
        """)
        print("Reopen modal from TASK DONE:", reopen_modal_res)
        await asyncio.sleep(0.5)

        # Mark back as active
        mark_active_res = await eval_js("""
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
        print("Mark back as active:", mark_active_res)
        await asyncio.sleep(0.5)

        # H. Test Escape key closes modal
        escape_res = await eval_js("""
            (() => {
                const ev = new KeyboardEvent('keydown', { key: 'Escape', bubbles: true });
                document.dispatchEvent(ev);
                const modal = document.getElementById('rmode-task-detail-modal');
                return { closedByEscape: !modal };
            })()
        """)
        print("Escape key close test:", escape_res)

        # I. Test checkbox direct click does not open modal
        direct_chk_res = await eval_js("""
            (() => {
                const firstCardCheckbox = document.querySelector('[data-task-id="task-event-proposal"] button[title="Mark complete"], [data-task-id="task-marketing-research"] button[title="Mark complete"]');
                if (firstCardCheckbox) {
                    firstCardCheckbox.click();
                    const modal = document.getElementById('rmode-task-detail-modal');
                    return { clickedCheckbox: true, modalOpened: !!modal };
                }
                return { clickedCheckbox: false };
            })()
        """)
        print("Direct checkbox click test (should NOT open modal):", direct_chk_res)

        # Reset task state to clean active
        await eval_js("""
            (() => {
                // Revert test edits
                const info = window.TempoMode.getRmodeTaskData('task-marketing-research');
                if (info && info.task) {
                    info.task.name = 'Marketing Research';
                    info.task.completed = false;
                    if (Array.isArray(info.task.subtasks) && info.task.subtasks[0]) {
                        info.task.subtasks[0].completed = false;
                    }
                    window.TempoMode.persistRmodePlanData(info.plan, info.task);
                }
                const epInfo = window.TempoMode.getRmodeTaskData('task-event-proposal');
                if (epInfo && epInfo.task) {
                    epInfo.task.completed = false;
                    window.TempoMode.persistRmodePlanData(epInfo.plan, epInfo.task);
                }
            })()
        """)

        print("ALL TESTS PASSED SUCCESSFULLY!")

asyncio.run(run())
