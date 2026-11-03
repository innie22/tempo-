import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    user_data_dir = tempfile.mkdtemp(prefix='tempo_measure_')
    edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    port = 9297
    proc = subprocess.Popen([
        edge_path,
        '--headless=new',
        f'--remote-debugging-port={port}',
        '--remote-allow-origins=*',
        f'--user-data-dir={user_data_dir}',
        '--window-size=1440,900',
        'http://localhost:8000/'
    ])
    time.sleep(2)

    ws = None
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as r:
            ws_url = json.loads(r.read().decode())[0]['webSocketDebuggerUrl']

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

        def eval_js(expr):
            res = send_command("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True
            })
            if "exceptionDetails" in res:
                raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        for _ in range(40):
            try:
                ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoEmergencyFlow !== 'undefined'")
                if ready:
                    eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
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
                    id: 'plan_urgent_test_101',
                    planId: 'plan_urgent_test_101',
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
                                    { id: 'sub-u1', title: 'Finish competitor analysis section', completed: false }
                                ]
                            }
                        }
                    ],
                    tasks: []
                };
                testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);
                if (window.TempoPlanStore && window.TempoPlanStore.saveActivePlan) {
                    window.TempoPlanStore.saveActivePlan('emergency', testPlan);
                }
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
                }
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.restorePlanState) {
                    window.TempoEmergencyFlow.restorePlanState();
                }
                window.TempoMode.setMode('emergency');
                window.TempoApp.navigateTo('today');
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(1)

        coords = eval_js("""
            (() => {
                const navbar = document.querySelector('header');
                const navBcr = navbar.getBoundingClientRect();
                const btnHome = document.getElementById('btn-home-mode-selector');
                const btnBcr = btnHome ? btnHome.getBoundingClientRect() : null;
                const rightCol = document.querySelector('.urgent-right-col');
                const rightBcr = rightCol ? rightCol.getBoundingClientRect() : null;
                const noteHeader = document.querySelector('.urgent-right-col .flex.items-center.justify-between.pb-0\\\\.5') || document.querySelector('.urgent-right-col .space-y-1\\\\.5');
                const noteBcr = noteHeader ? noteHeader.getBoundingClientRect() : null;
                const leftCol = document.querySelector('.urgent-left-col');
                const leftBcr = leftCol ? leftCol.getBoundingClientRect() : null;
                const main = document.querySelector('main');
                const mainBcr = main ? main.getBoundingClientRect() : null;

                return {
                    navbar: { top: navBcr.top, bottom: navBcr.bottom, height: navBcr.height },
                    main: { top: mainBcr.top, paddingTop: window.getComputedStyle(main).paddingTop },
                    btnHome: btnBcr ? { top: btnBcr.top, bottom: btnBcr.bottom, height: btnBcr.height } : null,
                    rightCol: rightBcr ? { top: rightBcr.top, bottom: rightBcr.bottom, height: rightBcr.height } : null,
                    noteTop: noteBcr ? noteBcr.top : null,
                    leftCol: leftBcr ? { top: leftBcr.top, bottom: leftBcr.bottom } : null,
                    diffRightColToNavBottom: rightBcr ? (rightBcr.top - navBcr.bottom) : null,
                    diffBtnToNavBottom: btnBcr ? (btnBcr.top - navBcr.bottom) : null,
                    diffRightColToBtn: (rightBcr && btnBcr) ? (rightBcr.top - btnBcr.top) : null
                };
            })()
        """)
        print("GEOMETRY_RESULTS:" + json.dumps(coords, indent=2))
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
