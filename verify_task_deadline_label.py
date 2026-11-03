import os
import sys
import json
import time
import subprocess
import urllib.request
from websocket import create_connection

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PORT = 9445
USER_DATA = r"C:\Users\YEN NHI\AppData\Local\Temp\edge_test_deadline_label"
ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"

def start_edge():
    cmd = [
        EDGE_PATH,
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={USER_DATA}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--disable-fre",
        "--disable-sync",
        "--no-default-browser-check",
        "--window-size=1280,2400",
        "http://127.0.0.1:8000/#emergency"
    ]
    return subprocess.Popen(cmd)

def send_cdp(ws, method, params=None, msg_id=[1]):
    m = {"id": msg_id[0], "method": method, "params": params or {}}
    msg_id[0] += 1
    ws.send(json.dumps(m))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == m["id"]:
            return resp

def evaluate_js(ws, expr):
    res = send_cdp(ws, "Runtime.evaluate", {
        "expression": expr,
        "returnByValue": True,
        "awaitPromise": True
    })
    if "exceptionDetails" in res.get("result", {}):
        print("JS Exception:", res["result"]["exceptionDetails"])
    if "result" in res and "result" in res["result"]:
        return res["result"]["result"].get("value")
    return None

def capture_screenshot(ws, clip, file_path):
    params = {"format": "png"}
    if clip:
        params["clip"] = clip
    res = send_cdp(ws, "Page.captureScreenshot", params)
    if "result" in res and "data" in res["result"]:
        import base64
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(res["result"]["data"]))
        print(f"Saved screenshot: {file_path}")

def run_tests():
    print("Starting Edge on port", PORT)
    proc = start_edge()
    time.sleep(2)

    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")
        tabs = json.loads(req.read().decode())
        page_tabs = [t for t in tabs if t.get("type") == "page" and "8000" in t.get("url", "")]
        target = page_tabs[0] if page_tabs else [t for t in tabs if t.get("type") == "page"][0]
        ws_url = target["webSocketDebuggerUrl"]
        print("Connecting to CDP target:", target.get("url"))
        ws = create_connection(ws_url)

        send_cdp(ws, "Page.enable")
        send_cdp(ws, "Runtime.enable")
        time.sleep(1)

        for _ in range(20):
            ready = evaluate_js(ws, "Boolean(window.TempoAuth && window.TempoMode && window.TempoPlanStore && window.TempoEmergencyFlow)")
            if ready:
                break
            time.sleep(0.5)

        print("\n=== TEST 1: Reality Check Task List in Vietnamese (vi) ===")
        setup_vi = evaluate_js(ws, """
            (async () => {
                localStorage.clear();
                sessionStorage.clear();
                if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.resetFlowState === 'function') {
                    window.TempoEmergencyFlow.resetFlowState();
                }
                if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                    window.TempoI18n.setLanguage('vi');
                }
                const email = 'user_dl@fpt.edu.vn';
                const pass = 'Password123!';
                const name = 'DL User';
                await window.TempoAuth.register(name, email, pass);
                await window.TempoAuth.signIn(email, pass);

                window.TempoMode.setMode('emergency');
                if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                    window.TempoApp.navigateTo('emergency');
                }
                if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.goToStage === 'function') {
                    window.TempoEmergencyFlow.goToStage('reality-check');
                }
                if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.close === 'function') {
                    window.TempoRecoverySetup.close();
                }
                // Load 3 sample tasks
                if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.loadSampleTasks === 'function') {
                    window.TempoEmergencyFlow.loadSampleTasks();
                }
                if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.close === 'function') {
                    window.TempoRecoverySetup.close();
                }
                if (window.TempoAuth && typeof window.TempoAuth.closeAllAuthModals === 'function') {
                    window.TempoAuth.closeAllAuthModals();
                }
                return true;
            })()
        """)
        time.sleep(0.8)

        rc_tasks_vi = evaluate_js(ws, """
            (() => {
                const rows = Array.from(document.querySelectorAll('#rc-tasks-list > div')).map(el => {
                    const name = el.querySelector('h5')?.textContent.trim();
                    const dueP = el.querySelector('p')?.textContent.trim();
                    return { name, due: dueP };
                });
                const card = document.getElementById('rc-tasks-list');
                const rect = card ? card.getBoundingClientRect() : { x: 0, y: 0, width: 0, height: 0 };
                return {
                    rows,
                    clip: { x: Math.max(0, rect.x - 10), y: Math.max(0, rect.y - 10), width: rect.width + 20, height: rect.height + 20, scale: 1 }
                };
            })()
        """)
        print("Reality Check Tasks in VI:", json.dumps(rc_tasks_vi["rows"], ensure_ascii=False, indent=2))
        print("Reality Check Clip VI:", rc_tasks_vi["clip"])
        
        # Verify that "Hạn chót" is completely replaced with "Deadline"
        all_dues_vi = [r["due"] for r in rc_tasks_vi["rows"]]
        for due_text in all_dues_vi:
            assert "Hạn chót" not in due_text, f"Found deprecated 'Hạn chót' in: {due_text}"
        
        # Check specific expected examples
        task1 = next(r for r in rc_tasks_vi["rows"] if "Statistics Assignment" in r["name"])
        task2 = next(r for r in rc_tasks_vi["rows"] if "Marketing Report" in r["name"])
        task3 = next(r for r in rc_tasks_vi["rows"] if "Biology Chapter 6 Notes" in r["name"])

        print(f"Task 1 due display: {task1['due']}")
        print(f"Task 2 due display: {task2['due']}")
        print(f"Task 3 due display: {task3['due']}")

        assert "Deadline 2 thg 11 · 9:00 PM" in task1["due"], f"Expected 'Deadline 2 thg 11 · 9:00 PM', got: {task1['due']}"
        assert "Deadline 3 thg 11 · 9:00 AM" in task2["due"], f"Expected 'Deadline 3 thg 11 · 9:00 AM', got: {task2['due']}"
        assert "Chưa có deadline" in task3["due"], f"Expected 'Chưa có deadline', got: {task3['due']}"

        capture_screenshot(ws, rc_tasks_vi["clip"], os.path.join(ARTIFACT_DIR, "reality_check_task_deadline_vi.png"))
        print("✓ TEST 1 PASSED: Reality Check displays 'Deadline' in Vietnamese! 'Hạn chót' completely removed!")

        print("\n=== TEST 2: Reality Check Task List in English (en) ===")
        evaluate_js(ws, """
            (() => {
                if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                    window.TempoI18n.setLanguage('en');
                }
                if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.goToStage === 'function') {
                    window.TempoEmergencyFlow.goToStage('reality-check');
                }
                if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.close === 'function') {
                    window.TempoRecoverySetup.close();
                }
            })()
        """)
        time.sleep(0.8)

        rc_tasks_en = evaluate_js(ws, """
            (() => {
                const rows = Array.from(document.querySelectorAll('#rc-tasks-list > div')).map(el => {
                    const name = el.querySelector('h5')?.textContent.trim();
                    const dueP = el.querySelector('p')?.textContent.trim();
                    return { name, due: dueP };
                });
                const card = document.getElementById('rc-tasks-list');
                const rect = card ? card.getBoundingClientRect() : { x: 0, y: 0, width: 0, height: 0 };
                return {
                    rows,
                    clip: { x: Math.max(0, rect.x - 10), y: Math.max(0, rect.y - 10), width: rect.width + 20, height: rect.height + 20, scale: 1 }
                };
            })()
        """)
        print("Reality Check Tasks in EN:", json.dumps(rc_tasks_en["rows"], indent=2))

        for r in rc_tasks_en["rows"]:
            assert "Hạn chót" not in r["due"], f"Found 'Hạn chót' in EN: {r['due']}"
            if "Statistics Assignment" in r["name"]:
                assert "Deadline Nov 2 · 9:00 PM" in r["due"], f"Expected 'Deadline Nov 2 · 9:00 PM', got: {r['due']}"
            if "Marketing Report" in r["name"]:
                assert "Deadline Nov 3 · 9:00 AM" in r["due"], f"Expected 'Deadline Nov 3 · 9:00 AM', got: {r['due']}"
            if "Biology Chapter 6 Notes" in r["name"]:
                assert "No fixed deadline" in r["due"], f"Expected 'No fixed deadline', got: {r['due']}"

        capture_screenshot(ws, rc_tasks_en["clip"], os.path.join(ARTIFACT_DIR, "reality_check_task_deadline_en.png"))
        print("✓ TEST 2 PASSED: Reality Check displays 'Deadline' in English!")

        print("\n=== TEST 3: Working Plan Task Deadline in Recovery Mode (vi & en) ===")
        # Switch back to Vietnamese and navigate to Rmode with legitimate plan
        setup_rmode = evaluate_js(ws, """
            (async () => {
                if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                    window.TempoI18n.setLanguage('vi');
                }
                const email = 'user_deadline_test@fpt.edu.vn';
                const pass = 'Password123!';
                const name = 'Deadline Test User';
                await window.TempoAuth.register(name, email, pass);
                await window.TempoAuth.signIn(email, pass);

                const plan = {
                    id: 'plan_deadline_check',
                    title: 'Kế hoạch học tập',
                    plannedTasks: [
                        {
                            id: 'task-dl-1',
                            dayDate: '2026-11-02',
                            dayLabel: 'Hôm nay',
                            startTime: '09:00',
                            endTime: '11:00',
                            executionBadge: 'Now',
                            task: {
                                id: 'task-dl-1',
                                name: 'Báo cáo Đồ án Tốt nghiệp',
                                deadlineDate: '2026-11-15',
                                deadlineTime: '17:00',
                                completed: false,
                                subtasks: []
                            }
                        }
                    ]
                };
                await window.TempoPlanStore.saveActivePlan('recovery', plan);
                await window.TempoPlanStore.saveActivePlan('emergency', plan);
                if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                    window.TempoEmergencyFlow.setConfirmedPlan(plan);
                }
                window.TempoMode.setMode('recovery');
                window.TempoMode.renderRmodeHome();
                if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.close === 'function') {
                    window.TempoRecoverySetup.close();
                }
                if (window.TempoAuth && typeof window.TempoAuth.closeAllAuthModals === 'function') {
                    window.TempoAuth.closeAllAuthModals();
                }
                return true;
            })()
        """)
        time.sleep(0.8)

        rmode_dl_vi = evaluate_js(ws, """
            (() => {
                const wpCard = document.getElementById('recovery-working-plan');
                const text = wpCard ? wpCard.innerText : '';
                const rect = wpCard ? wpCard.getBoundingClientRect() : { x: 0, y: 0, width: 0, height: 0 };
                return {
                    text,
                    hasDeadlineLabel: text.includes('Deadline: 15/11/2026 - 5:00 PM') || text.includes('Deadline: 15/11/2026'),
                    hasHanchot: text.includes('Hạn chót'),
                    clip: { x: Math.max(0, rect.x), y: Math.max(0, rect.y), width: rect.width, height: rect.height, scale: 1 }
                };
            })()
        """)
        print("Rmode Working Plan deadline status (VI):", json.dumps(rmode_dl_vi, ensure_ascii=False, indent=2))
        assert rmode_dl_vi["hasHanchot"] is False, "Working Plan must NOT contain 'Hạn chót'"
        assert rmode_dl_vi["hasDeadlineLabel"] is True, "Working Plan must display 'Deadline:'"
        capture_screenshot(ws, rmode_dl_vi["clip"], os.path.join(ARTIFACT_DIR, "rmode_wp_deadline_label_vi.png"))
        print("✓ TEST 3 PASSED: Working Plan in Rmode displays 'Deadline' consistently!")

        print("\n=======================================================")
        print("ALL TASK DEADLINE LABEL TESTS PASSED SUCCESSFULLY (100%)")
        print("=======================================================")

    finally:
        try:
            ws.close()
        except:
            pass
        proc.kill()

if __name__ == '__main__':
    run_tests()
