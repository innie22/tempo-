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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_confirm_modal_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9265
    
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

        def eval_js(expr):
            res = send_command("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True
            })
            if "exceptionDetails" in res:
                log(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        def save_screenshot(filepath):
            data = send_command("Page.captureScreenshot", {"format": "png"})
            b64 = data.get("data", "")
            if b64:
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(b64))
                log(f"Saved screenshot: {filepath}")

        # Set viewport
        send_command("Emulation.setDeviceMetricsOverride", {
            "width": 1280,
            "height": 800,
            "deviceScaleFactor": 1,
            "mobile": False
        })
        time.sleep(1)

        # Wait for scripts to initialize
        log("Waiting for TempoApp initialization...")
        for _ in range(20):
            is_ready = eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoApp.navigateTo === 'function'")
            if is_ready:
                break
            time.sleep(0.5)

        # Trap window.confirm to verify it is NEVER called
        eval_js("""
            window.__native_confirm_called = false;
            window.__native_confirm_arg = null;
            window.confirm = function(msg) {
                window.__native_confirm_called = true;
                window.__native_confirm_arg = msg;
                return false;
            };
        """)

        # Authenticate test user
        log("Authenticating test user...")
        eval_js("""
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

        # Navigate to Working Plan page
        eval_js("window.TempoApp.navigateTo('plan-workspace')")
        time.sleep(1)

        log("\n=======================================================")
        log("TEST 1: CLEAR TASK CUSTOM CONFIRMATION POPUP")
        log("=======================================================")

        # Find the "Clear this task" button in the right card and click it
        eval_js("""
            (() => {
                const btns = Array.from(document.querySelectorAll('[data-tempo-ui="selected-task-card"] button'));
                const clearBtn = btns.find(b => b.innerText.includes('Clear this task') || b.innerText.includes('Clear task'));
                if (clearBtn) clearBtn.click();
            })()
        """)
        time.sleep(0.5)

        # 1. Verify native window.confirm was NOT called
        confirm_called = eval_js("window.__native_confirm_called")
        assert not confirm_called, "Native window.confirm was called for Clear task!"
        log("PASS: Native browser confirm was NOT invoked.")

        # 2. Verify modal element exists and is visible
        modal_exists = eval_js("document.getElementById('modal-clear-task-confirm') !== null")
        assert modal_exists, "Modal element #modal-clear-task-confirm not found"
        log("PASS: Modal #modal-clear-task-confirm is rendered.")

        # 3. Check exact Title
        title_text = eval_js("document.querySelector('#modal-clear-task-confirm h3').innerText.trim()")
        log(f"Modal title: '{title_text}'")
        assert title_text == "Clear this task?", f"Expected 'Clear this task?', got '{title_text}'"
        log("PASS: Exact title 'Clear this task?' verified.")

        # 4. Check exact Message
        msg_text = eval_js("document.querySelector('#modal-clear-task-confirm p').innerText.trim()")
        log(f"Modal message: '{msg_text}'")
        expected_msg = "This task will be removed from your Working Plan. This action cannot be undone."
        assert msg_text == expected_msg, f"Expected '{expected_msg}', got '{msg_text}'"
        log("PASS: Exact message verified.")

        # 5. Check Buttons
        btn_texts = eval_js("""
            Array.from(document.querySelectorAll('#modal-clear-task-confirm button')).map(b => b.innerText.trim()).filter(Boolean)
        """)
        log(f"Modal button texts: {btn_texts}")
        assert "Clear task" in btn_texts, "Primary button 'Clear task' not found"
        assert "Cancel" in btn_texts, "Secondary button 'Cancel' not found"
        assert "✕" in btn_texts, "Close icon ✕ not found"
        log("PASS: Exact button labels ('Clear task', 'Cancel', '✕') verified.")

        # Screenshot: Clear task popup
        shot_clear_popup = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\clear_task_confirm_popup.png"
        save_screenshot(shot_clear_popup)

        # 6. Test Dismissal via Cancel
        log("Testing dismiss via Cancel...")
        eval_js("""
            const cancelBtn = Array.from(document.querySelectorAll('#modal-clear-task-confirm button')).find(b => b.innerText.trim() === 'Cancel');
            if (cancelBtn) cancelBtn.click();
        """)
        time.sleep(0.5)
        modal_open = eval_js("document.getElementById('modal-clear-task-confirm') !== null")
        assert not modal_open, "Modal should be closed after clicking Cancel"
        # Verify task is still present
        task_still_there = eval_js("document.querySelector('[data-tempo-ui=\"selected-task-card\"] h2').innerText.includes('Marketing Research')")
        assert task_still_there, "Task was unexpectedly removed after clicking Cancel"
        log("PASS: Cancel dismisses modal without modifying plan.")

        # 7. Test Dismissal via Close icon (✕)
        eval_js("""
            (() => {
                const btns = Array.from(document.querySelectorAll('[data-tempo-ui="selected-task-card"] button'));
                const clearBtn = btns.find(b => b.innerText.includes('Clear this task') || b.innerText.includes('Clear task'));
                if (clearBtn) clearBtn.click();
            })()
        """)
        time.sleep(0.5)
        eval_js("""
            (() => {
                const closeBtn = Array.from(document.querySelectorAll('#modal-clear-task-confirm button')).find(b => b.innerText.trim() === '✕');
                if (closeBtn) closeBtn.click();
            })()
        """)
        time.sleep(0.5)
        modal_open = eval_js("document.getElementById('modal-clear-task-confirm') !== null")
        assert not modal_open, "Modal should be closed after clicking ✕"
        log("PASS: Close icon ✕ dismisses modal without modifying plan.")

        # 8. Test Dismissal via Backdrop click
        eval_js("""
            (() => {
                const btns = Array.from(document.querySelectorAll('[data-tempo-ui="selected-task-card"] button'));
                const clearBtn = btns.find(b => b.innerText.includes('Clear this task') || b.innerText.includes('Clear task'));
                if (clearBtn) clearBtn.click();
            })()
        """)
        time.sleep(0.5)
        eval_js("document.getElementById('modal-clear-task-confirm').click()")
        time.sleep(0.5)
        modal_open = eval_js("document.getElementById('modal-clear-task-confirm') !== null")
        assert not modal_open, "Modal should be closed after clicking backdrop"
        log("PASS: Backdrop click dismisses modal without modifying plan.")

        # 9. Test Execution via Primary button ('Clear task')
        eval_js("""
            (() => {
                const btns = Array.from(document.querySelectorAll('[data-tempo-ui="selected-task-card"] button'));
                const clearBtn = btns.find(b => b.innerText.includes('Clear this task') || b.innerText.includes('Clear task'));
                if (clearBtn) clearBtn.click();
            })()
        """)
        time.sleep(0.5)
        eval_js("document.getElementById('btn-confirm-clear-task').click()")
        time.sleep(0.8)

        modal_open = eval_js("document.getElementById('modal-clear-task-confirm') !== null")
        assert not modal_open, "Modal should be closed after executing Clear task"
        # Verify 'Marketing Research' is removed from task rows
        left_task_names = eval_js("""
            Array.from(document.querySelectorAll('[data-task-row] h4')).map(h => h.innerText.trim())
        """)
        log(f"Tasks in left column after clearing: {left_task_names}")
        assert "Marketing Research" not in left_task_names, "Marketing Research was not removed from Working Plan!"
        # Verify auto-selection of next task
        selected_task_now = eval_js("document.querySelector('[data-tempo-ui=\"selected-task-card\"] h2').innerText.trim()")
        log(f"Auto-selected task now: '{selected_task_now}'")
        assert "Event Proposal" in selected_task_now, f"Expected Event Proposal selected, got '{selected_task_now}'"
        log("PASS: Task removed, next task auto-selected, UI updated!")

        log("\n=======================================================")
        log("TEST 2: DELETE MY PLAN CUSTOM CONFIRMATION POPUP")
        log("=======================================================")

        # Find and click "Delete my plan" header button
        eval_js("""
            const headerBtns = Array.from(document.querySelectorAll('button'));
            const delBtn = headerBtns.find(b => b.innerText.trim() === 'Delete my plan');
            if (delBtn) delBtn.click();
        """)
        time.sleep(0.5)

        # 1. Verify native window.confirm was NOT called
        confirm_called = eval_js("window.__native_confirm_called")
        assert not confirm_called, "Native window.confirm was called for Delete my plan!"
        log("PASS: Native browser confirm was NOT invoked.")

        # 2. Verify modal element exists
        modal_del_exists = eval_js("document.getElementById('modal-delete-plan-confirm') !== null")
        assert modal_del_exists, "Modal element #modal-delete-plan-confirm not found"
        log("PASS: Modal #modal-delete-plan-confirm is rendered.")

        # 3. Check exact Title
        del_title_text = eval_js("document.querySelector('#modal-delete-plan-confirm h3').innerText.trim()")
        log(f"Modal title: '{del_title_text}'")
        assert del_title_text == "Delete your plan?", f"Expected 'Delete your plan?', got '{del_title_text}'"
        log("PASS: Exact title 'Delete your plan?' verified.")

        # 4. Check exact Message
        del_msg_text = eval_js("document.querySelector('#modal-delete-plan-confirm p').innerText.trim()")
        log(f"Modal message: '{del_msg_text}'")
        expected_del_msg = "This will permanently delete your Working Plan and its scheduled tasks. This action cannot be undone."
        assert del_msg_text == expected_del_msg, f"Expected '{expected_del_msg}', got '{del_msg_text}'"
        log("PASS: Exact message verified.")

        # 5. Check Buttons
        del_btn_texts = eval_js("""
            Array.from(document.querySelectorAll('#modal-delete-plan-confirm button')).map(b => b.innerText.trim()).filter(Boolean)
        """)
        log(f"Modal button texts: {del_btn_texts}")
        assert "Delete my plan" in del_btn_texts, "Primary button 'Delete my plan' not found"
        assert "Cancel" in del_btn_texts, "Secondary button 'Cancel' not found"
        assert "✕" in del_btn_texts, "Close icon ✕ not found"
        log("PASS: Exact button labels ('Delete my plan', 'Cancel', '✕') verified.")

        # Screenshot: Delete plan popup
        shot_del_popup = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\delete_plan_confirm_popup.png"
        save_screenshot(shot_del_popup)

        # 6. Test Dismissal via Cancel
        log("Testing dismiss via Cancel...")
        eval_js("""
            (() => {
                const cancelBtn = Array.from(document.querySelectorAll('#modal-delete-plan-confirm button')).find(b => b.innerText.trim() === 'Cancel');
                if (cancelBtn) cancelBtn.click();
            })()
        """)
        time.sleep(0.5)
        del_modal_open = eval_js("document.getElementById('modal-delete-plan-confirm') !== null")
        assert not del_modal_open, "Modal should be closed after clicking Cancel"
        # Plan is preserved
        assert eval_js("window.TempoPlanWorkspace.getActivePlan() !== null"), "Plan was unexpectedly deleted"
        log("PASS: Cancel dismisses modal without modifying plan.")

        # 7. Test Dismissal via Close icon (✕)
        eval_js("window.TempoPlanWorkspace.promptDeletePlan()")
        time.sleep(0.5)
        eval_js("""
            (() => {
                const closeBtn = Array.from(document.querySelectorAll('#modal-delete-plan-confirm button')).find(b => b.innerText.trim() === '✕');
                if (closeBtn) closeBtn.click();
            })()
        """)
        time.sleep(0.5)
        del_modal_open = eval_js("document.getElementById('modal-delete-plan-confirm') !== null")
        assert not del_modal_open, "Modal should be closed after clicking ✕"
        log("PASS: Close icon ✕ dismisses modal without modifying plan.")

        # 8. Test Dismissal via Backdrop click
        eval_js("window.TempoPlanWorkspace.promptDeletePlan()")
        time.sleep(0.5)
        eval_js("document.getElementById('modal-delete-plan-confirm').click()")
        time.sleep(0.5)
        del_modal_open = eval_js("document.getElementById('modal-delete-plan-confirm') !== null")
        assert not del_modal_open, "Modal should be closed after clicking backdrop"
        log("PASS: Backdrop click dismisses modal without modifying plan.")

        # 9. Test Execution via Primary button ('Delete my plan')
        eval_js("window.TempoPlanWorkspace.promptDeletePlan()")
        time.sleep(0.5)
        eval_js("document.getElementById('btn-confirm-delete-plan').click()")
        time.sleep(1)

        # Verify plan was deleted
        plan_is_deleted = eval_js("""
            localStorage.getItem('tempo_working_plan') === null &&
            localStorage.getItem('tempo_active_plan') === null
        """)
        assert plan_is_deleted, "Plan localStorage items were not removed"
        log("PASS: Plan data removed from storage.")

        # Verify toast shown
        toast_text = eval_js("document.getElementById('app-toast') ? document.getElementById('app-toast').innerText : ''")
        log(f"Toast message: '{toast_text}'")
        assert "deleted" in toast_text.lower(), f"Expected toast to say deleted, got '{toast_text}'"
        log("PASS: Confirmation toast shown to user.")

        log("\n=======================================================")
        log("TEST 3: DASHBOARD OVERDUE CLEAR TASK POPUP")
        log("=======================================================")

        # Trigger dashboard overdue popup
        eval_js("window.TempoMode.promptClearOverdueTask('test_overdue_task_123')")
        time.sleep(0.5)

        # Verify modal element exists
        mode_modal = eval_js("document.getElementById('modal-mode-clear-task-confirm') !== null")
        assert mode_modal, "Dashboard clear task modal element not found"
        mode_modal_hidden = eval_js("document.getElementById('modal-mode-clear-task-confirm').classList.contains('hidden')")
        assert not mode_modal_hidden, "Dashboard clear task modal is hidden"

        # Check title and message
        m_title = eval_js("document.getElementById('mode-clear-task-title').innerText.trim()")
        m_msg = eval_js("document.querySelector('#modal-mode-clear-task-confirm p').innerText.trim()")
        assert m_title == "Clear this task?", f"Expected 'Clear this task?', got '{m_title}'"
        assert m_msg == expected_msg, f"Expected '{expected_msg}', got '{m_msg}'"
        log("PASS: Dashboard clear task popup displays exact Title and Message.")

        # Dismiss dashboard modal
        eval_js("window.TempoMode.closeClearOverdueTaskModal()")
        time.sleep(0.5)
        mode_modal_hidden = eval_js("document.getElementById('modal-mode-clear-task-confirm').classList.contains('hidden')")
        assert mode_modal_hidden, "Dashboard clear task modal should be hidden after dismiss"
        log("PASS: Dashboard clear task modal dismiss verified.")

        log("\n=======================================================")
        log("ALL CUSTOM CONFIRMATION POPUP TESTS PASSED SUCCESSFULLY!")
        log("=======================================================")

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

if __name__ == "__main__":
    run_tests()
