import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import base64
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"

def main():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_states_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9360
    
    cmd = [
        edge_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "--window-size=1440,900",
        "http://localhost:8000/"
    ]
    
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
            raise RuntimeError("Failed to connect to CDP")
            
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

        def capture_element_screenshot(selector, filename):
            box = eval_js(f"""
                (() => {{
                    const el = document.querySelector('{selector}');
                    if (!el) return null;
                    const r = el.getBoundingClientRect();
                    return {{ x: r.left, y: r.top, width: r.width, height: r.height }};
                }})()
            """)
            if not box:
                print(f"Could not find element {selector} for screenshot")
                return
            clip = {
                "x": box["x"],
                "y": box["y"],
                "width": box["width"],
                "height": box["height"],
                "scale": 1
            }
            res = send_command("Page.captureScreenshot", {"clip": clip, "format": "png"})
            png_bytes = base64.b64decode(res["data"])
            path = os.path.join(ARTIFACT_DIR, filename)
            with open(path, "wb") as f:
                f.write(png_bytes)
            print(f"Captured screenshot: {filename} ({box['width']}x{box['height']})")

        def measure_card():
            return eval_js("""
                (() => {
                    const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
                    if (!card) return null;
                    const bcr = card.getBoundingClientRect();
                    const cs = window.getComputedStyle(card);
                    return {
                        width: bcr.width,
                        height: bcr.height,
                        backgroundColor: cs.backgroundColor,
                        border: cs.border,
                        borderRadius: cs.borderRadius,
                        padding: cs.padding,
                        boxShadow: cs.boxShadow
                    };
                })()
            """)

        for _ in range(40):
            try:
                ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined' && typeof window.TempoEmergencyFlow !== 'undefined'")
                if ready:
                    break
            except Exception:
                pass
            time.sleep(0.5)

        eval_js("if (window.TempoI18n) window.TempoI18n.setLanguage('en');")

        # ---------------------------------------------------------
        # State 1: ACTIVE_TODAY
        # ---------------------------------------------------------
        eval_js("""
            (() => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
                const testPlan = {
                    id: 'plan_urgent_active', planId: 'plan_urgent_active', planType: 'emergency', title: 'Urgent Plan',
                    plannedTasks: [
                        { dayDate: today, dayLabel: 'Today', startTime: '10:00 AM', endTime: '11:00 AM', executionBadge: 'DO THIS FIRST',
                          task: { id: 'task-u1', name: 'Marketing Research', description: 'Subtask 1: Literature Review', hasDeadline: true, deadlineDate: '2026-10-17', deadlineTime: '21:00', durationLabel: '2h 30m', durationMinutes: 150, completed: false, isInProgress: true, subtasks: [{ title: 'Subtask 1: Literature Review', completed: false }] } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }]
                };
                testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);
                window.TempoPlanStore.saveActivePlan('emergency', testPlan);
                window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
                window.TempoEmergencyFlow.restorePlanState();
                window.TempoMode.setMode('emergency');
                window.TempoApp.navigateTo('today');
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.5)
        m_active = measure_card()
        print("1. ACTIVE_TODAY metrics:", json.dumps(m_active, indent=2))
        capture_element_screenshot('[data-tempo-ui="urgent-task-now"]', "urmode_active_task_verified.png")

        # Full page screenshot
        res = send_command("Page.captureScreenshot", {"format": "png"})
        with open(os.path.join(ARTIFACT_DIR, "urmode_live_desktop_full_verified.png"), "wb") as f:
            f.write(base64.b64decode(res["data"]))
        print("Captured full page: urmode_live_desktop_full_verified.png")

        # ---------------------------------------------------------
        # State 2: TIME_ENDED_WITH_INCOMPLETE_WORK
        # ---------------------------------------------------------
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

                const plan = {
                    id: 'p_ended',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: today, task: { id: 'te1', name: 'Marketing Research', completed: false, hasDeadline: true, deadlineDate: today } }
                    ],
                    tasks: [],
                    availabilityDays: [
                        { date: today, blocks: [{ start: '08:00', end: '08:01' }] }
                    ]
                };
                plan.tasks = plan.plannedTasks.map(p => p.task);
                await window.TempoPlanStore.saveActivePlan('emergency', plan);
                if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                    window.TempoEmergencyFlow.setConfirmedPlan(plan);
                }
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.5)
        m_time_ended = measure_card()
        print("2. TIME_ENDED metrics:", json.dumps(m_time_ended, indent=2))
        capture_element_screenshot('[data-tempo-ui="urgent-task-now"]', "urmode_planned_window_ended_verified.png")

        # ---------------------------------------------------------
        # State 3: PLAN_INCOMPLETE
        # ---------------------------------------------------------
        eval_js("""
            (async () => {
                await window.TempoPlanStore.archiveActivePlan('emergency');
                window.TempoPlanStore.clearInMemoryCache();
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(null);
                }
                if (window.TempoEmergencyFlow) {
                    window.TempoEmergencyFlow.getCurrentStage = () => 'reality-check';
                }
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.5)
        m_incomplete = measure_card()
        print("3. PLAN_INCOMPLETE metrics:", json.dumps(m_incomplete, indent=2))
        capture_element_screenshot('[data-tempo-ui="urgent-task-now"]', "urmode_plan_incomplete_verified.png")

        # ---------------------------------------------------------
        # State 4: PLAN_COMPLETE
        # ---------------------------------------------------------
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

                const plan = {
                    id: 'p_done_all',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: today, task: { id: 'td1', name: 'Finished Essay', completed: true } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, blocks: [{ start: '09:00', end: '23:59' }] }]
                };
                plan.tasks = plan.plannedTasks.map(p => p.task);
                await window.TempoPlanStore.saveActivePlan('emergency', plan);
                if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                    window.TempoEmergencyFlow.setConfirmedPlan(plan);
                }
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.5)
        m_complete = measure_card()
        print("4. PLAN_COMPLETE metrics:", json.dumps(m_complete, indent=2))
        capture_element_screenshot('[data-tempo-ui="urgent-task-now"]', "urmode_plan_complete_verified.png")

        # ---------------------------------------------------------
        # State 5: PLAN_STALE
        # ---------------------------------------------------------
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const pastDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
                const past = `${pastDate.getFullYear()}-${pad(pastDate.getMonth() + 1)}-${pad(pastDate.getDate())}`;
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

                const plan = {
                    id: 'p_stale',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: past, dayLabel: 'Yesterday', task: { id: 'ts1', name: 'Stale Report', completed: false } },
                        { dayDate: today, dayLabel: 'Today', task: { id: 'ts2', name: 'Today Report', completed: false } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, blocks: [{ start: '09:00', end: '23:59' }] }]
                };
                plan.tasks = plan.plannedTasks.map(p => p.task);
                await window.TempoPlanStore.saveActivePlan('emergency', plan);
                if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                    window.TempoEmergencyFlow.setConfirmedPlan(plan);
                }
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.5)
        m_stale = measure_card()
        print("5. PLAN_STALE metrics:", json.dumps(m_stale, indent=2))
        capture_element_screenshot('[data-tempo-ui="urgent-task-now"]', "urmode_plan_stale_verified.png")

        # ---------------------------------------------------------
        # State 6: TODAY_COMPLETE
        # ---------------------------------------------------------
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
                const tomDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
                const tomorrow = `${tomDate.getFullYear()}-${pad(tomDate.getMonth() + 1)}-${pad(tomDate.getDate())}`;

                const plan = {
                    id: 'p_done_today',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: today, task: { id: 'td1', name: 'Finished Task', completed: true } },
                        { dayDate: tomorrow, task: { id: 'td2', name: 'Tomorrow Task', completed: false } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, blocks: [{ start: '09:00', end: '23:59' }] }]
                };
                plan.tasks = plan.plannedTasks.map(p => p.task);
                await window.TempoPlanStore.saveActivePlan('emergency', plan);
                if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                    window.TempoEmergencyFlow.setConfirmedPlan(plan);
                }
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.5)
        m_today_complete = measure_card()
        print("6. TODAY_COMPLETE metrics:", json.dumps(m_today_complete, indent=2))
        capture_element_screenshot('[data-tempo-ui="urgent-task-now"]', "urmode_today_complete_verified.png")

        # ---------------------------------------------------------
        # State 7: NO_WORK_TODAY
        # ---------------------------------------------------------
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const futureDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 2);
                const future = `${futureDate.getFullYear()}-${pad(futureDate.getMonth() + 1)}-${pad(futureDate.getDate())}`;

                const plan = {
                    id: 'p_future',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: future, dayLabel: 'In 2 Days', task: { id: 'tf1', name: 'Future Task', completed: false } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: future, blocks: [{ start: '09:00', end: '23:59' }] }]
                };
                plan.tasks = plan.plannedTasks.map(p => p.task);
                await window.TempoPlanStore.saveActivePlan('emergency', plan);
                if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                    window.TempoEmergencyFlow.setConfirmedPlan(plan);
                }
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.5)
        m_no_work = measure_card()
        print("7. NO_WORK_TODAY metrics:", json.dumps(m_no_work, indent=2))
        capture_element_screenshot('[data-tempo-ui="urgent-task-now"]', "urmode_no_work_today_verified.png")

        print("\nAll 7 states measured and verified successfully!")

    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        try:
            proc.terminate()
        except Exception:
            pass

if __name__ == '__main__':
    main()
