import subprocess
import time
import json
import urllib.request
import tempfile
import base64
import websocket
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def capture_screenshots():
    artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
    user_data_dir = tempfile.mkdtemp(prefix="tempo_capture_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9240
    
    cmd = [
        edge_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--window-size=1280,900",
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
                raw = ws.recv()
                msg = json.loads(raw)
                if msg.get("id") == cid:
                    if "error" in msg:
                        raise RuntimeError(f"CDP error: {msg['error']}")
                    return msg.get("result", {})

        def eval_js(expr, await_promise=True):
            res = send_command("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": await_promise
            })
            if "exceptionDetails" in res:
                raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        def take_screenshot(filename):
            res = send_command("Page.captureScreenshot", {"format": "png"})
            data = base64.b64decode(res["data"])
            path = os.path.join(artifact_dir, filename)
            with open(path, "wb") as f:
                f.write(data)
            log(f"Saved screenshot: {path}")

        def wait_for_ready():
            for _ in range(40):
                try:
                    ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined' && typeof window.TempoUrmodeFlow !== 'undefined'")
                    if ready:
                        eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("Application failed to become ready")

        send_command("Runtime.enable")
        log("Waiting for page and scripts ready...")
        wait_for_ready()

        # Sign in mock user for realistic session experience
        eval_js("""
            (async () => {
                const mock = {
                    id: 'local_user_test101',
                    email: 'alex.chen@university.edu',
                    raw_email: 'alex.chen@university.edu',
                    password: 'password123',
                    user_metadata: {
                        full_name: 'Alex Chen',
                        display_name: 'Alex Chen',
                        role: 'student'
                    }
                };
                localStorage.setItem('tempo_mock_account_alex.chen@university.edu', JSON.stringify(mock));
                await window.TempoAuth.signIn('alex.chen@university.edu', 'password123');
                if (window.TempoAuth.closeAllAuthModals) window.TempoAuth.closeAllAuthModals();
            })()
        """)
        time.sleep(0.5)

        # 1. Reset popup (Case 1: First-time entry)
        eval_js("""
            (async () => {
                await window.TempoPlanStore.archiveActivePlan('emergency');
                window.TempoPlanStore.clearInMemoryCache();
                if (window.TempoEmergencyFlow) {
                    if (window.TempoEmergencyFlow.startFreshPlan) window.TempoEmergencyFlow.startFreshPlan();
                    window.TempoEmergencyFlow.setConfirmedPlan(null);
                    window.TempoEmergencyFlow.goToStage('entry');
                }
                window.TempoUrmodeFlow.queueResetPopup();
                window.TempoMode.setMode('emergency');
                window.TempoApp.navigateTo('today');
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.5)
        take_screenshot("urmode_reset_popup_case1.png")

        # 2. Case 1 Path C: Empty dashboard with Setup & Execute buttons
        eval_js("window.TempoUrmodeFlow.handleResetClose()")
        time.sleep(0.5)
        take_screenshot("urmode_empty_dashboard_path_c.png")

        # 3. Quick task creation popup
        eval_js("window.TempoUrmodeFlow.openQuickTaskModal()")
        time.sleep(0.5)
        take_screenshot("urmode_quick_task_popup.png")

        # 4. Step Breakdown popup over 'plan-workspace'
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
                const testPlan = {
                    id: 'plan_break_demo',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: today, startTime: '10:00 AM', task: { id: 'bd-1', name: 'Macroeconomics Final Essay', durationMinutes: 60, completed: false, subtasks: [{ id: 's1', title: 'Outline thesis & 3 arguments', completed: false }] } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, blocks: [{ start: '09:00', end: '18:00' }] }]
                };
                testPlan.tasks = testPlan.plannedTasks.map(p => p.task);
                await window.TempoPlanStore.saveActivePlan('emergency', testPlan);
                window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
                window.TempoUrmodeFlow.startBreakTaskFlow('bd-1');
            })()
        """)
        time.sleep(0.5)
        take_screenshot("urmode_break_task_popup_workspace.png")

        # 5. Review Summary popup with OVERDUE task (Case 3)
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const yestDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
                const yesterday = `${yestDate.getFullYear()}-${pad(yestDate.getMonth() + 1)}-${pad(yestDate.getDate())}`;
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

                const overduePlan = {
                    id: 'plan_review_demo',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: yesterday, startTime: '09:00 AM', task: { id: 'ov-1', name: 'Overdue Reading & Chapter Summary', durationMinutes: 45, completed: false, subtasks: [] } },
                        { dayDate: today, startTime: '01:00 PM', task: { id: 'ov-2', name: 'Calculus Problem Set 4', durationMinutes: 60, completed: false, subtasks: [] } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, blocks: [{ start: '09:00', end: '18:00' }] }]
                };
                overduePlan.tasks = overduePlan.plannedTasks.map(p => p.task);
                await window.TempoPlanStore.saveActivePlan('emergency', overduePlan);
                window.TempoEmergencyFlow.setConfirmedPlan(overduePlan);
                window.TempoUrmodeFlow.showReviewSummaryPopup();
            })()
        """)
        time.sleep(0.5)
        take_screenshot("urmode_review_summary_overdue.png")

        # 6. Adjustment Step 1: Choose tasks to keep
        eval_js("window.TempoUrmodeFlow.startAdjustmentFlow()")
        time.sleep(0.5)
        take_screenshot("urmode_adjustment_step1_keep.png")

        log("All screenshots captured successfully.")

    finally:
        if ws:
            try: ws.close()
            except Exception: pass
        if proc:
            proc.terminate()
            proc.wait()

if __name__ == "__main__":
    capture_screenshots()
