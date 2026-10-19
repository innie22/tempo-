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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9289

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

    print(f"Launching Edge on port {port}...", flush=True)
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
            raise RuntimeError("Could not connect to Edge DevTools")

        print(f"Connected to CDP at {ws_url}", flush=True)
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

        # Wait for page ready
        for _ in range(40):
            ready = eval_js("document.readyState === 'complete' && Boolean(window.TempoMode && window.TempoPlanStore && window.TempoEmergencyFlow)")
            if ready:
                break
            time.sleep(0.5)

        print("Page ready. Setting up test plan...", flush=True)

        eval_js("""
            (() => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
                const tomorrowDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
                const tomorrow = `${tomorrowDate.getFullYear()}-${pad(tomorrowDate.getMonth() + 1)}-${pad(tomorrowDate.getDate())}`;

                const testPlan = {
                    id: 'plan_urgent_verify',
                    planId: 'plan_urgent_verify',
                    planType: 'emergency',
                    title: 'Urgent Plan',
                    plannedTasks: [
                        {
                            dayDate: today,
                            dayLabel: 'Today',
                            startTime: '10:00 AM',
                            endTime: '11:00 AM',
                            executionBadge: 'DO THIS FIRST',
                            task: {
                                id: 'task-u1',
                                name: 'Marketing Report',
                                description: 'Finish competitor analysis section',
                                hasDeadline: true,
                                deadlineDate: today,
                                deadlineTime: '22:00',
                                durationLabel: '45 min',
                                durationMinutes: 45,
                                completed: false,
                                isInProgress: false,
                                subtasks: [
                                    { id: 'sub-u1', title: 'Finish competitor analysis section', completed: false },
                                    { id: 'sub-u2', title: 'Compile market share graph', completed: false },
                                    { id: 'sub-u3', title: 'Final proofread', completed: true }
                                ]
                            }
                        },
                        {
                            dayDate: today,
                            dayLabel: 'Today',
                            startTime: '02:00 PM',
                            endTime: '03:00 PM',
                            executionBadge: 'THEN',
                            task: {
                                id: 'task-u2',
                                name: 'Read chapter 4',
                                description: 'Read textbook pages 120-145',
                                hasDeadline: false,
                                durationLabel: '30 min',
                                durationMinutes: 30,
                                completed: true,
                                isInProgress: false,
                                subtasks: []
                            }
                        },
                        {
                            dayDate: today,
                            dayLabel: 'Today',
                            startTime: '04:00 PM',
                            endTime: '05:00 PM',
                            executionBadge: 'LATER',
                            task: {
                                id: 'task-u3',
                                name: 'Prepare slides',
                                description: 'Create 5 slides for presentation',
                                hasDeadline: false,
                                durationLabel: '1 hr',
                                durationMinutes: 60,
                                completed: false,
                                isInProgress: false,
                                subtasks: []
                            }
                        }
                    ],
                    tasks: [],
                    availabilityDays: [
                        { date: today, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] },
                        { date: tomorrow, label: 'Tomorrow', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }
                    ]
                };
                testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);

                window.TempoPlanStore.saveActivePlan('emergency', testPlan);
                window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
                window.TempoEmergencyFlow.restorePlanState();
                window.TempoMode.setMode('emergency');
            })()
        """)

        time.sleep(1)

        # Inspect properties
        props = eval_js("""
            (() => {
                const emode = document.getElementById('emode-home-content');
                const taskCard = document.querySelector('[data-tempo-ui="urgent-task-priority-card"]');
                const noteCard = document.querySelector('.urgent-right-col .p-4.rounded-2xl.border');
                const planTitle = document.querySelector('.urgent-right-col h2');
                const selfCheck = document.querySelector('[data-tempo-ui="urgent-home-shell"] [class*="e8ecf1"]');
                const bodyBg = window.getComputedStyle(document.body).backgroundColor;

                let cardBg = null, cardBorder = null;
                if (taskCard) {
                    const st = window.getComputedStyle(taskCard);
                    cardBg = st.backgroundColor;
                    cardBorder = st.border;
                }

                const shell = document.getElementById('mode-indicator-shell');
                const navLinks = document.querySelector('header nav');
                const homeSelector = document.getElementById('btn-home-mode-selector');

                return {
                    emodeVisible: emode && !emode.classList.contains('hidden'),
                    bodyBg: bodyBg,
                    navbarIndicatorHidden: shell ? shell.classList.contains('hidden') : null,
                    navbarIndicatorOffsetWidth: shell ? shell.offsetWidth : null,
                    navbarIndicatorOffsetHeight: shell ? shell.offsetHeight : null,
                    homeModeSelectorExists: !!homeSelector,
                    headerNavVisible: navLinks && !navLinks.classList.contains('hidden'),
                    selfCheckFound: !!selfCheck
                };
            })()
        """)
        print("Inspection Results:", json.dumps(props, indent=2), flush=True)

        # 1. Capture Desktop Top Viewport
        send_command("Emulation.setDeviceMetricsOverride", {
            "width": 1440,
            "height": 900,
            "deviceScaleFactor": 1,
            "mobile": False
        })
        time.sleep(0.5)

        top_shot = send_command("Page.captureScreenshot", {"format": "png"})
        top_path = os.path.join(ARTIFACT_DIR, "urmode_live_desktop_top.png")
        with open(top_path, "wb") as f:
            f.write(base64.b64decode(top_shot["data"]))
        print(f"Saved: {top_path}", flush=True)

        # 2. Capture Desktop Full Page Scroll
        full_shot = send_command("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
        full_path = os.path.join(ARTIFACT_DIR, "urmode_live_desktop_full.png")
        with open(full_path, "wb") as f:
            f.write(base64.b64decode(full_shot["data"]))
        print(f"Saved: {full_path}", flush=True)

        # 3. Switch to Entry Home and capture verification that Entry Home is unchanged
        eval_js("window.TempoMode.restoreDefaultHome();")
        time.sleep(0.8)

        entry_props = eval_js("""
            (() => {
                const dmode = document.getElementById('dmode-home-content');
                const bodyBg = window.getComputedStyle(document.body).backgroundColor;
                return {
                    dmodeVisible: dmode && !dmode.classList.contains('hidden'),
                    bodyBg: bodyBg
                };
            })()
        """)
        print("Entry Home Inspection Results:", json.dumps(entry_props, indent=2), flush=True)

        entry_shot = send_command("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
        entry_path = os.path.join(ARTIFACT_DIR, "entry_home_live_check.png")
        with open(entry_path, "wb") as f:
            f.write(base64.b64decode(entry_shot["data"]))
        print(f"Saved: {entry_path}", flush=True)

    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                pass

if __name__ == "__main__":
    main()
