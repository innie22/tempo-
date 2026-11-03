import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

def test_margins():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_margin_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9298
    
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

        # Setup plan
        eval_js("""
            (() => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
                const testPlan = {
                    id: 'plan_urgent_test',
                    planId: 'plan_urgent_test',
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
                                subtasks: []
                            }
                        }
                    ],
                    tasks: []
                };
                testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);
                window.TempoPlanStore.saveActivePlan('emergency', testPlan);
                window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
                window.TempoMode.setMode('emergency');
            })()
        """)
        time.sleep(1)

        # Measure with different negative margins
        for test_margin in [0, -100, -110, -114, -116, -118, -120]:
            eval_js(f"document.querySelector('.urgent-right-col').style.marginTop = '{test_margin}px';")
            time.sleep(0.1)
            metrics = eval_js("""
                (() => {
                    const nav = document.querySelector('header').getBoundingClientRect();
                    const btn = document.getElementById('btn-home-mode-selector').getBoundingClientRect();
                    const rightCol = document.querySelector('.urgent-right-col').getBoundingClientRect();
                    const noteHeader = document.querySelector('.urgent-right-col .flex.items-center.justify-between.pb-0\\\\.5').getBoundingClientRect();
                    const noteText = document.querySelector('.urgent-right-col .space-y-1\\\\.5 span').getBoundingClientRect();
                    const primaryCard = document.querySelector('.urgent-left-col > div').getBoundingClientRect();
                    const workingPlan = document.querySelector('.urgent-right-col > div:nth-child(2)').getBoundingClientRect();

                    return {
                        navBottom: nav.bottom,
                        btnTop: btn.top,
                        btnBottom: btn.bottom,
                        btnHeight: btn.height,
                        rightColTop: rightCol.top,
                        noteHeaderTop: noteHeader.top,
                        noteTextTop: noteText.top,
                        deltaBtnToNoteHeader: noteHeader.top - btn.top,
                        deltaBtnToRightCol: rightCol.top - btn.top,
                        primaryCardTop: primaryCard.top,
                        workingPlanTop: workingPlan.top,
                        deltaCards: workingPlan.top - primaryCard.top
                    };
                })()
            """)
            print(f"Margin: {test_margin}px -> noteHeaderTop: {metrics['noteHeaderTop']:.1f}, btnTop: {metrics['btnTop']:.1f}, deltaBtnToNoteHeader: {metrics['deltaBtnToNoteHeader']:.1f}, deltaBtnToRightCol: {metrics['deltaBtnToRightCol']:.1f}, deltaCards: {metrics['deltaCards']:.1f}")

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
    test_margins()
