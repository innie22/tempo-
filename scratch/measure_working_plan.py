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

def main():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_mwp_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9395
    
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
                ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined'")
                if ready:
                    break
            except Exception:
                pass
            time.sleep(0.5)

        eval_js("if (window.TempoI18n) window.TempoI18n.setLanguage('en');")

        # 1. Populated with 1 task
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

        m1 = eval_js("""
            (() => {
                const card = document.querySelector('.urgent-working-plan-card');
                if (!card) return null;
                const r = card.getBoundingClientRect();
                const cs = window.getComputedStyle(card);
                return {
                    width: r.width,
                    height: r.height,
                    minHeight: cs.minHeight,
                    maxHeight: cs.maxHeight,
                    padding: cs.padding,
                    scrollHeight: card.scrollHeight,
                    clientHeight: card.clientHeight
                };
            })()
        """)
        print("Card with 1 task:", json.dumps(m1, indent=2))

        # 2. Populated with 5 tasks
        eval_js("""
            (() => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
                const testPlan = {
                    id: 'plan_urgent_active', planId: 'plan_urgent_active', planType: 'emergency', title: 'Urgent Plan',
                    plannedTasks: [
                        { dayDate: today, task: { id: 't1', name: 'Task 1: Marketing Research', hasDeadline: true, deadlineDate: today, deadlineTime: '12:00', completed: false, isInProgress: true, subtasks: [] } },
                        { dayDate: today, task: { id: 't2', name: 'Task 2: Literature Review Notes', hasDeadline: true, deadlineDate: today, deadlineTime: '14:00', completed: false, isInProgress: false, subtasks: [] } },
                        { dayDate: today, task: { id: 't3', name: 'Task 3: Draft Section A Findings', hasDeadline: false, completed: false, isInProgress: false, subtasks: [] } },
                        { dayDate: today, task: { id: 't4', name: 'Task 4: Review Statistical Tables', hasDeadline: false, completed: false, isInProgress: false, subtasks: [] } },
                        { dayDate: today, task: { id: 't5', name: 'Task 5: Final Submission Check', hasDeadline: true, deadlineDate: today, deadlineTime: '20:00', completed: false, isInProgress: false, subtasks: [] } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }]
                };
                testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);
                window.TempoPlanStore.saveActivePlan('emergency', testPlan);
                window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.5)

        m5 = eval_js("""
            (() => {
                const card = document.querySelector('.urgent-working-plan-card');
                if (!card) return null;
                const r = card.getBoundingClientRect();
                const cs = window.getComputedStyle(card);
                return {
                    width: r.width,
                    height: r.height,
                    minHeight: cs.minHeight,
                    maxHeight: cs.maxHeight,
                    scrollHeight: card.scrollHeight,
                    clientHeight: card.clientHeight
                };
            })()
        """)
        print("Card with 5 tasks (current behavior):", json.dumps(m5, indent=2))

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
