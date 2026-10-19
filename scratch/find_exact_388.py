import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_388_")
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

        for _ in range(40):
            try:
                ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined' && typeof window.TempoEmergencyFlow !== 'undefined'")
                if ready:
                    break
            except Exception:
                pass
            time.sleep(0.5)

        eval_js("""
            (() => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
                const testPlan = {
                    id: 'plan_urgent_verify', planId: 'plan_urgent_verify', planType: 'emergency', title: 'Urgent Plan',
                    plannedTasks: [
                        { dayDate: today, dayLabel: 'Today', startTime: '10:00 AM', endTime: '11:00 AM', executionBadge: 'DO THIS FIRST',
                          task: { id: 'task-u1', name: 'Marketing Report', description: 'Finish competitor analysis section', hasDeadline: true, deadlineDate: today, deadlineTime: '22:00', durationLabel: '45 min', durationMinutes: 45, completed: false, isInProgress: true, subtasks: [{}, {}, {}] } },
                        { dayDate: today, dayLabel: 'Today', startTime: '02:00 PM', endTime: '03:00 PM', executionBadge: 'THEN',
                          task: { id: 'task-u2', name: 'Read chapter 4', description: 'Read textbook pages 120-145', hasDeadline: false, durationLabel: '30 min', durationMinutes: 30, completed: true, isInProgress: false, subtasks: [] } },
                        { dayDate: today, dayLabel: 'Today', startTime: '04:00 PM', endTime: '05:00 PM', executionBadge: 'LATER',
                          task: { id: 'task-u3', name: 'Prepare slides', description: 'Create 5 slides for presentation', hasDeadline: false, durationLabel: '1 hr', durationMinutes: 60, completed: false, isInProgress: false, subtasks: [] } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }]
                };
                testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);
                window.TempoPlanStore.saveActivePlan('emergency', testPlan);
                window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
                window.TempoEmergencyFlow.restorePlanState();
                window.TempoMode.setMode('emergency');
            })()
        """)
        time.sleep(1)

        # Function to test CSS rule variations and measure natural content height and rendered height
        res = eval_js("""
            (() => {
                const card = document.querySelector('.urgent-working-plan-card');
                // Remove min-height temporarily to measure natural height
                card.style.minHeight = '0px';

                // Let's test adjustments:
                // Test 1: Baseline natural height without min-height
                const naturalHeight = card.getBoundingClientRect().height;

                return { naturalHeight };
            })()
        """)
        print("Natural Populated Height without min-height constraint:", res)

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
