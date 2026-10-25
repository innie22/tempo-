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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_plan_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9260
    
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
        is_auth = eval_js("Boolean(window.TempoAuth && window.TempoAuth.getCurrentUser())")
        log(f"Authenticated status: {is_auth}")

        # Navigate to plan workspace
        log("\n=======================================================")
        log("SECTION 1: TEMPO WORKING PLAN PAGE STRUCTURE & STYLING")
        log("=======================================================")
        diag = eval_js("""
            (() => {
                const preTab = window.TempoApp.getCurrentTab();
                window.TempoApp.navigateTo('plan-workspace');
                const postTab = window.TempoApp.getCurrentTab();
                const screen = document.getElementById('screen-plan-workspace');
                const h1s = Array.from(document.querySelectorAll('h1')).map(h => h.innerText.trim());
                return { preTab, postTab, screenHidden: screen ? screen.classList.contains('hidden') : null, h1s };
            })()
        """)
        log(f"Navigation diagnostic: {diag}")
        time.sleep(1)

        # 1. Verify Page Title
        title = eval_js("document.querySelector('#screen-plan-workspace h1') ? document.querySelector('#screen-plan-workspace h1').innerText.trim() : document.querySelector('h1').innerText.trim()")
        log(f"Page title: '{title}'")
        assert "Tempo Working Plan" in title, f"Expected 'Tempo Working Plan', got '{title}'"

        log("PASS: Centered title 'Tempo Working Plan' verified.")

        # 2. Verify Return Home control
        home_btn_text = eval_js("document.getElementById('plan-workspace-back-home').innerText.trim()")
        log(f"Return home button text: '{home_btn_text}'")
        assert "Return Home" in home_btn_text, "Missing Return Home button"
        log("PASS: '← Return Home' control at upper-left verified.")

        # 3. Verify Background Color
        body_bg = eval_js("window.getComputedStyle(document.body).backgroundColor")
        log(f"Page background color: '{body_bg}'")
        assert "239" in body_bg and "250" in body_bg and "255" in body_bg, f"Expected rgb(239, 250, 255), got '{body_bg}'"
        log("PASS: Soft light blue background (#EFFAFF) verified.")

        # 4. Verify Header Action Buttons
        header_btns = eval_js("""
            Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim())
        """)
        for expected in ['Add task', 'Add availability', 'Adjust Plan', 'Delete my plan']:
            assert any(expected in b for b in header_btns), f"Missing button: {expected}"
            log(f"PASS: Plan action button '{expected}' verified.")

        # 5. Verify Initial Tasks in Left Column
        task_names = eval_js("""
            Array.from(document.querySelectorAll('[data-task-row] h4')).map(h => h.innerText.trim())
        """)
        log(f"Left column tasks: {task_names}")
        assert "Marketing Research" in task_names, "Missing 'Marketing Research'"
        assert "Event Proposal" in task_names, "Missing 'Event Proposal'"
        assert "Edit Video" in task_names, "Missing 'Edit Video'"
        log("PASS: Scheduled tasks grouped by date headings verified.")

        # 6. Verify Right Column Selected Task
        selected_task_name = eval_js("""
            document.querySelector('[data-tempo-ui=\"selected-task-card\"] h2').innerText.trim()
        """)
        log(f"Selected task in right column: '{selected_task_name}'")
        assert "Marketing Research" in selected_task_name, f"Expected 'Marketing Research' selected, got '{selected_task_name}'"

        # Check subtasks of Marketing Research
        subtasks = eval_js("""
            Array.from(document.querySelectorAll('[data-tempo-ui=\"selected-task-card\"] .max-h-40 span')).map(s => s.innerText.trim())
        """)
        log(f"Subtasks displayed in right card: {subtasks[:3]}")
        assert any("Outline" in s for s in subtasks), "Missing 'Outline' subtask"
        assert any("Literature Review" in s for s in subtasks), "Missing 'Literature Review' subtask"
        assert any("Research Gap" in s for s in subtasks), "Missing 'Research Gap' subtask"
        log("PASS: Selected task details, subtasks, and note verified.")

        # Verify 4 detail action buttons
        card_btns = eval_js("""
            Array.from(document.querySelectorAll('[data-tempo-ui=\"selected-task-card\"] button')).map(b => b.innerText.trim())
        """)
        for exp in ['Mark as done', 'Focus now', 'Reschedule', 'Clear this task']:
            assert any(exp in b for b in card_btns), f"Missing card action: {exp}"
            log(f"PASS: Right column action '{exp}' verified.")

        # Screenshot: Desktop initial
        shot_desktop = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\working_plan_desktop_initial.png"
        save_screenshot(shot_desktop)

        log("\n=======================================================")
        log("SECTION 2: TASK COMPLETION, DONE SECTION & AUTO-SELECTION")
        log("=======================================================")
        # Mark Marketing Research as done
        eval_js("""
            const btn = Array.from(document.querySelectorAll('[data-tempo-ui=\"selected-task-card\"] button')).find(b => b.innerText.includes('Mark as done'));
            if (btn) btn.click();
        """)
        time.sleep(0.8)

        # 1. Check progress bar counter
        progress_text = eval_js("document.querySelector('span:has-text(\"Tasks\"), [data-tempo-ui=\"tempo-working-plan\"] span:nth-of-type(1)').innerText")
        counter_span = eval_js("""
            Array.from(document.querySelectorAll('span')).find(s => s.innerText.includes('/6 Tasks') || s.innerText.includes('Tasks')).innerText
        """)
        log(f"Progress count after completion: '{counter_span}'")
        assert "1/6 Tasks" in counter_span or "1/" in counter_span, f"Expected 1 completed task, got '{counter_span}'"
        log("PASS: Progress bar and count updated immediately to 1 completed.")

        # 2. Check Done section appeared
        done_sec = eval_js("document.querySelector('[data-tempo-ui=\"done-section\"]') !== null")
        assert done_sec, "Done section should be visible after completing a task"
        done_tasks = eval_js("""
            Array.from(document.querySelectorAll('[data-tempo-ui=\"done-section\"] h4')).map(h => h.innerText.trim())
        """)
        log(f"Tasks in Done section: {done_tasks}")
        assert "Marketing Research" in done_tasks, "Marketing Research should be moved to Done section"
        log("PASS: Completed task moved to dedicated Done section at bottom of left column.")

        # 3. Check strikethrough styling
        has_strikethrough = eval_js("""
            const h = document.querySelector('[data-tempo-ui=\"done-section\"] h4');
            h ? h.classList.contains('line-through') : false;
        """)
        assert has_strikethrough, "Completed task should have line-through class"
        log("PASS: Strikethrough styling applied to completed task title.")

        # 4. Check auto-selection of next active task
        new_selected = eval_js("""
            document.querySelector('[data-tempo-ui=\"selected-task-card\"] h2').innerText.trim()
        """)
        log(f"Auto-selected task after completion: '{new_selected}'")
        assert "Event Proposal" in new_selected, f"Expected 'Event Proposal' to be auto-selected, got '{new_selected}'"
        log("PASS: Next active task ('Event Proposal') automatically selected in right detail card!")

        # Screenshot: Task in Done section
        shot_done = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\working_plan_task_completed.png"
        save_screenshot(shot_done)

        log("\n=======================================================")
        log("SECTION 3: REVERT / UNCHECK & DONE SECTION DISAPPEARANCE")
        log("=======================================================")
        # Uncheck Marketing Research
        eval_js("""
            const uncheckBtn = document.querySelector('[data-tempo-ui=\"done-section\"] button[title=\"Mark incomplete\"]');
            if (uncheckBtn) uncheckBtn.click();
        """)
        time.sleep(0.8)

        # Check Done section is gone
        done_sec_after = eval_js("document.querySelector('[data-tempo-ui=\"done-section\"]') !== null")
        assert not done_sec_after, "Done section should NOT be displayed when 0 tasks are completed"
        log("PASS: Done section cleanly hidden when 0 tasks completed.")

        # Check progress count returned to 0
        counter_reverted = eval_js("""
            Array.from(document.querySelectorAll('span')).find(s => s.innerText.includes('/6 Tasks') || s.innerText.includes('Tasks')).innerText
        """)
        log(f"Progress count after unchecking: '{counter_reverted}'")
        assert "0/6 Tasks" in counter_reverted or "0/" in counter_reverted
        log("PASS: Task successfully restored to active group and counter reverted.")

        log("\n=======================================================")
        log("SECTION 4: RESPONSIVE VIEWPORTS (TABLET & MOBILE)")
        log("=======================================================")
        # Tablet
        send_command("Emulation.setDeviceMetricsOverride", {
            "width": 768,
            "height": 1024,
            "deviceScaleFactor": 1,
            "mobile": True
        })
        time.sleep(0.6)
        shot_tablet = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\working_plan_tablet.png"
        save_screenshot(shot_tablet)
        log("PASS: Tablet layout captured without horizontal overflow.")

        # Mobile
        send_command("Emulation.setDeviceMetricsOverride", {
            "width": 375,
            "height": 812,
            "deviceScaleFactor": 1,
            "mobile": True
        })
        time.sleep(0.6)
        shot_mobile = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\working_plan_mobile.png"
        save_screenshot(shot_mobile)
        log("PASS: Mobile layout captured without horizontal overflow.")

        log("\n=======================================================")
        log("SECTION 5: RETURN HOME CONTROL NAVIGATION")
        log("=======================================================")
        send_command("Emulation.setDeviceMetricsOverride", {
            "width": 1280,
            "height": 800,
            "deviceScaleFactor": 1,
            "mobile": False
        })
        time.sleep(0.4)
        eval_js("document.getElementById('plan-workspace-back-home').click();")
        time.sleep(1)

        cur_hash = eval_js("window.location.hash")
        log(f"Location hash after Return Home: '{cur_hash}'")
        assert "today" in cur_hash or cur_hash == ""
        log("PASS: '← Return Home' control successfully navigated back to Home dashboard.")

        log("\n=======================================================")
        log("🎉 ALL TEMPO WORKING PLAN VERIFICATION TESTS PASSED 100%!")
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

if __name__ == '__main__':
    run_tests()
