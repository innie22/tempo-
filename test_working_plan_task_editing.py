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

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_task_edit_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9276
    
    cmd = [
        edge_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "http://localhost:8000/"
    ]
    
    log(f"Launching Edge on port {port}...")
    proc = subprocess.Popen(cmd)
    ws = None
    try:
        ws_url = None
        for _ in range(30):
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
            raise RuntimeError("Failed to connect to Edge CDP endpoint")
            
        log(f"Connected to CDP: {ws_url}")
        ws = websocket.create_connection(ws_url)
        
        msg_id = 1
        def send_command(method, params=None):
            nonlocal msg_id
            cid = msg_id
            msg_id += 1
            req = {"id": cid, "method": method}
            if params:
                req["params"] = params
            ws.send(json.dumps(req))
            while True:
                resp = json.loads(ws.recv())
                if resp.get("id") == cid:
                    return resp.get("result", {})
                    
        def evaluate(expr):
            res = send_command("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True
            })
            if "exceptionDetails" in res:
                log(f"JS Exception for [{expr[:60]}...]: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        def capture_screenshot(filename):
            res = send_command("Page.captureScreenshot", {"format": "png"})
            data = res.get("data")
            if data:
                with open(filename, "wb") as f:
                    f.write(base64.b64decode(data))
                log(f"Screenshot saved: {filename}")

        send_command("Page.enable")
        send_command("DOM.enable")
        send_command("Emulation.setDeviceMetricsOverride", {
            "width": 1280,
            "height": 800,
            "deviceScaleFactor": 1,
            "mobile": False
        })
        time.sleep(1)

        # Wait for scripts to initialize
        log("Waiting for TempoApp initialization...")
        for _ in range(30):
            is_ready = evaluate("typeof window.TempoApp !== 'undefined' && typeof window.TempoApp.navigateTo === 'function'")
            if is_ready:
                break
            time.sleep(0.5)

        # Authenticate test user
        log("Authenticating test user...")
        evaluate("""
            (async () => {
                const mock = {
                    id: 'local_user_test',
                    email: 'alex.chen@university.edu',
                    raw_email: 'alex.chen@university.edu',
                    password: 'password123',
                    user_metadata: { full_name: 'Alex Chen', display_name: 'Alex Chen', role: 'student' }
                };
                localStorage.setItem('tempo_mock_account_alex.chen@university.edu', JSON.stringify(mock));
                if (window.TempoAuth) {
                    await window.TempoAuth.signIn("alex.chen@university.edu", "password123");
                }
            })()
        """)
        time.sleep(1)
        
        # 1. Navigate to plan workspace
        log("\n--- TEST 1: Navigation to Working Plan ---")
        evaluate("window.TempoApp.navigateTo('plan-workspace');")
        time.sleep(1)
        
        page_title = evaluate("document.querySelector('#screen-plan-workspace h1') ? document.querySelector('#screen-plan-workspace h1').innerText : ''")
        log(f"Working Plan title: {page_title}")
        assert "Tempo Working Plan" in page_title, "Page title mismatch"
        
        # 2. Check Requirement 4: Verify '+ Add subtasks' is removed
        log("\n--- TEST 2: Verification of '+ Add subtasks' removal ---")
        has_add_subtasks_button = evaluate("document.body.innerText.includes('+ Add subtasks')")
        log(f"Has '+ Add subtasks': {has_add_subtasks_button}")
        assert not has_add_subtasks_button, "+ Add subtasks button should be removed from task card UI"
        
        # Check subtasks Edit button label (Requirement 3)
        edit_subtask_btn_text = evaluate("""
            (() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const b = btns.find(el => el.innerText.trim() === 'Edit subtask');
                return b ? b.innerText.trim() : null;
            })()
        """)
        log(f"Subtask edit button text: {edit_subtask_btn_text}")
        assert edit_subtask_btn_text == "Edit subtask", "Subtask action should be labelled 'Edit subtask'"
        
        # Check deadline edit button label (Requirement 2)
        edit_due_btn_text = evaluate("""
            (() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const b = btns.find(el => el.innerText.trim() === 'Edit due day');
                return b ? b.innerText.trim() : null;
            })()
        """)
        log(f"Due day edit button text: {edit_due_btn_text}")
        assert edit_due_btn_text == "Edit due day", "Deadline action should be labelled 'Edit due day'"

        # 3. Requirement 5: Default state of note (no note exists)
        log("\n--- TEST 3: Default state of task note ('+ Create a note') ---")
        has_create_note_btn = evaluate("""
            (() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const b = btns.find(el => el.innerText.includes('Create a note'));
                return b ? b.innerText.trim() : null;
            })()
        """)
        log(f"Create note button found: {has_create_note_btn}")
        assert has_create_note_btn and "Create a note" in has_create_note_btn, "+ Create a note button should be present when no note exists"
        
        # Verify placeholder text is NOT shown
        has_placeholder = evaluate("document.body.innerText.includes('Create a sheet to manage references')")
        log(f"Has placeholder text 'Create a sheet to manage references': {has_placeholder}")
        assert not has_placeholder, "Static placeholder text should NOT be rendered when no note exists"

        # 4. Requirement 5: Create and save a task note
        log("\n--- TEST 4: Create and save note, verify Tool Notes integration ---")
        selected_task_id = evaluate("window.TempoPlanWorkspace.getActivePlan().plannedTasks[0].task.id")
        log(f"Selected task id: {selected_task_id}")
        
        # Open note editor
        evaluate(f"window.TempoPlanWorkspace.openNoteEditor('{selected_task_id}');")
        time.sleep(0.5)
        
        modal_visible = evaluate("document.getElementById('modal-edit-task-note') !== null")
        log(f"Note editor modal visible: {modal_visible}")
        assert modal_visible, "Note editor modal should appear"
        
        # Type note and save
        evaluate("""
            const ta = document.getElementById('pw-note-editor-text');
            if (ta) ta.value = 'Review chapter 4 reference sheet and compile citations.';
        """)
        evaluate(f"window.TempoPlanWorkspace.saveNote('{selected_task_id}');")
        time.sleep(0.5)
        
        # Verify note preview rendered in Working Plan card
        note_preview = evaluate("""
            (() => {
                const card = document.querySelector('[data-tempo-ui=\"selected-task-card\"]');
                return card ? card.innerText : '';
            })()
        """)
        log(f"Task card contains note: {'Review chapter 4 reference sheet' in note_preview}")
        assert "Review chapter 4 reference sheet and compile citations." in note_preview, "Saved note should be displayed in task card"
        assert "Edit note" in note_preview, "Edit note button should appear on saved note"

        # Verify note is persisted in window.TempoToolNotes
        tool_note = evaluate(f"window.TempoToolNotes.getNoteForTask('{selected_task_id}')")
        log(f"Tool Note object: {tool_note}")
        assert tool_note is not None, "Note must be stored in Tool Notes system"
        assert "Review chapter 4" in tool_note.get("text", ""), "Tool note text should match"

        # Verify Tool Notes page renders note
        evaluate("window.TempoApp.navigateTo('tool-notes');")
        time.sleep(0.5)
        tool_notes_page_text = evaluate("document.getElementById('screen-tool-notes').innerText")
        log(f"Tool Notes page contains task note: {'Review chapter 4' in tool_notes_page_text}")
        assert "Review chapter 4" in tool_notes_page_text, "Task note must appear on Tool Notes page"
        # Verify Tool Notes contract preserved
        assert "Tool Notes" in tool_notes_page_text, "Tool Notes title must be preserved"
        assert "Your notes space is coming soon" in tool_notes_page_text, "Coming soon message must be preserved"

        # Return to plan workspace
        evaluate("window.TempoApp.navigateTo('plan-workspace');")
        time.sleep(0.5)

        # 5. Requirement 6: Focus Zone note display & editing
        log("\n--- TEST 5: Focus Zone task note integration ---")
        evaluate(f"window.TempoPlanWorkspace.startTaskFocus('{selected_task_id}');")
        time.sleep(0.5)
        
        fz_text = evaluate("document.getElementById('tempo-focus-zone-root').innerText")
        log(f"Focus Zone setup contains note: {'Review chapter 4' in fz_text}")
        assert "Review chapter 4 reference sheet" in fz_text, "Focus Zone must display saved task note"
        
        # Edit note in Focus Zone
        evaluate("window.TempoFocusZone.openEditNoteModal();")
        time.sleep(0.5)
        evaluate("""
            const fzTa = document.getElementById('fz-task-note-textarea');
            if (fzTa) fzTa.value = 'Updated note from Focus Zone session.';
        """)
        evaluate("window.TempoFocusZone.saveNoteFromFocusZone();")
        time.sleep(0.5)
        
        fz_updated_text = evaluate("document.getElementById('tempo-focus-zone-root').innerText")
        assert "Updated note from Focus Zone session." in fz_updated_text, "Updated note should show in Focus Zone"
        
        # Verify sync back to Tool Notes & Working Plan
        updated_tool_note = evaluate(f"window.TempoToolNotes.getNoteForTask('{selected_task_id}')")
        assert "Updated note from Focus Zone session." in updated_tool_note.get("text", ""), "Tool note should reflect Focus Zone update"
        
        evaluate("window.TempoFocusZone.viewTodaysPlanAndClose();")
        evaluate("window.TempoApp.navigateTo('plan-workspace');")
        time.sleep(0.5)
        
        wp_card_text = evaluate("document.querySelector('[data-tempo-ui=\"selected-task-card\"]').innerText")
        assert "Updated note from Focus Zone session." in wp_card_text, "Working Plan should reflect Focus Zone note update"

        # 6. Requirement 1: Editable Now / Later label & AI planner re-sequencing
        log("\n--- TEST 6: Editable Now / Later label and AI planner re-sequencing ---")
        plan_before = evaluate("""
            window.TempoPlanWorkspace.getActivePlan().plannedTasks.map(pt => ({
                id: pt.task.id,
                name: pt.task.name,
                userLabel: pt.task.userLabel || 'none',
                executionBadge: pt.executionBadge
            }))
        """)
        log(f"Plan tasks before label change: {plan_before}")
        
        # Find a task with 'Later' or second task in list
        second_task_id = plan_before[1]["id"]
        second_task_name = plan_before[1]["name"]
        log(f"Changing task '{second_task_name}' ({second_task_id}) from Later to Now...")
        
        # Toggle label menu
        evaluate(f"window.TempoPlanWorkspace.toggleLabelMenu('{second_task_id}');")
        time.sleep(0.3)
        menu_rendered = evaluate(f"document.querySelector('[data-label-menu-container] button') !== null")
        log(f"Label dropdown menu triggered: {menu_rendered}")
        
        # Select 'Now'
        evaluate(f"window.TempoPlanWorkspace.setTaskLabel('{second_task_id}', 'Now');")
        time.sleep(0.5)
        
        plan_after = evaluate("""
            window.TempoPlanWorkspace.getActivePlan().plannedTasks.map(pt => ({
                id: pt.task.id,
                name: pt.task.name,
                userLabel: pt.task.userLabel,
                executionBadge: pt.executionBadge
            }))
        """)
        log(f"Plan tasks after changing to Now: {plan_after}")
        
        # The task that was set to Now must now be at index 0 (moved earlier by AI planner)
        assert plan_after[0]["id"] == second_task_id, f"Task {second_task_id} should be prioritized earlier to index 0"
        assert plan_after[0]["userLabel"] == "Now", "Task label should be 'Now'"
        
        # 7. Requirement 2: Edit due day and confirmation modal
        log("\n--- TEST 7: Edit due day & 'Update your plan?' confirmation modal ---")
        # Toggle deadline edit for first task
        evaluate("window.TempoPlanWorkspace.toggleDeadlineEdit();")
        time.sleep(0.3)
        
        date_input_present = evaluate("document.getElementById('pw-edit-deadline-date') !== null")
        assert date_input_present, "Inline date input should be present"
        
        # Test changing deadline to a date that alters priority order (conflict / reorder)
        # Set task 0 deadline to far future (Oct 29), so task 1 (Oct 18) becomes more urgent
        evaluate("""
            (() => {
                const dInput = document.getElementById('pw-edit-deadline-date');
                if (dInput) dInput.value = '2026-10-29';
                const noFixed = document.getElementById('pw-edit-no-deadline');
                if (noFixed) noFixed.checked = false;
            })()
        """)
        evaluate(f"window.TempoPlanWorkspace.saveDeadlineEdit('{second_task_id}');")
        time.sleep(0.5)
        
        modal_reorder_present = evaluate("document.getElementById('modal-deadline-reorder-confirm') !== null")
        log(f"Update plan modal present: {modal_reorder_present}")
        assert modal_reorder_present, "'Update your plan?' modal must be shown when deadline changes priority order"
        
        modal_title = evaluate("document.getElementById('deadline-reorder-title') ? document.getElementById('deadline-reorder-title').innerText : ''")
        log(f"Modal title: '{modal_title}'")
        assert "Update your plan?" in modal_title, "Modal title must be 'Update your plan?'"
        
        # Test 'Keep current priorities' button
        evaluate("window.TempoPlanWorkspace.confirmDeadlineWithoutReorder();")
        time.sleep(0.5)
        modal_gone = evaluate("document.getElementById('modal-deadline-reorder-confirm') === null")
        log(f"Modal closed after Keep current priorities: {modal_gone}")
        assert modal_gone, "Modal should close after Keep current priorities"
        
        # Test 'Yes, update my plan' flow
        evaluate("window.TempoPlanWorkspace.toggleDeadlineEdit();")
        time.sleep(0.3)
        evaluate("""
            (() => {
                const dInput = document.getElementById('pw-edit-deadline-date');
                if (dInput) dInput.value = '2026-10-30';
                const noFixed = document.getElementById('pw-edit-no-deadline');
                if (noFixed) noFixed.checked = false;
            })()
        """)
        evaluate(f"window.TempoPlanWorkspace.saveDeadlineEdit('{second_task_id}');")
        time.sleep(0.5)
        
        evaluate("window.TempoPlanWorkspace.confirmDeadlineWithReorder();")
        time.sleep(0.5)
        modal_gone2 = evaluate("document.getElementById('modal-deadline-reorder-confirm') === null")
        log(f"Modal closed after Yes, update my plan: {modal_gone2}")
        assert modal_gone2, "Modal should close after Yes, update my plan"

        # 8. Requirement 3: Edit subtask opens Break Task popup
        log("\n--- TEST 8: 'Edit subtask' opens Break Task popup ---")
        evaluate(f"window.TempoPlanWorkspace.openBreakTaskModal('{second_task_id}');")
        time.sleep(0.8)
        
        break_popup_visible = evaluate("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                return modal && !modal.classList.contains('hidden');
            })()
        """)
        log(f"Break Task popup visible: {break_popup_visible}")
        assert break_popup_visible, "Break Task popup must open when clicking Edit subtask"
        
        # Close breakdown modal cleanly back to Working Plan
        evaluate("window.TempoUrmodeFlow.closeModal('plan-workspace');")
        time.sleep(0.5)
        
        back_in_wp = evaluate("document.getElementById('screen-plan-workspace') && !document.getElementById('screen-plan-workspace').classList.contains('hidden')")
        assert back_in_wp, "Should remain cleanly on Working Plan after closing Break Task popup"

        # 9. Clean up / delete note test
        log("\n--- TEST 9: Delete note test ---")
        evaluate(f"window.TempoPlanWorkspace.deleteNote('{selected_task_id}');")
        time.sleep(0.5)
        
        note_deleted_in_wp = evaluate("document.querySelector('[data-tempo-ui=\"selected-task-card\"]').innerText.includes('+ Create a note')")
        log(f"Reverted to '+ Create a note' after deletion: {note_deleted_in_wp}")
        assert note_deleted_in_wp, "Deleting note should revert card to '+ Create a note'"
        
        tool_note_after_del = evaluate(f"window.TempoToolNotes.getNoteForTask('{selected_task_id}')")
        assert tool_note_after_del is None, "Tool note should be deleted"

        # Take screenshot for artifact documentation
        capture_screenshot("C:/Users/YEN NHI/.gemini/antigravity/brain/6baf9c9e-16aa-475f-b2c0-d941b08ac2c6/working_plan_task_editing_verified.png")
        log("\n>>> ALL 9 TESTS PASSED SUCCESSFULLY! <<<")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    run_tests()
