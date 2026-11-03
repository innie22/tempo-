import subprocess, time, json, urllib.request, tempfile, websocket

user_data_dir = tempfile.mkdtemp(prefix='tempo_measure_')
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9296
proc = subprocess.Popen([
    edge_path, '--headless=new', f'--remote-debugging-port={port}',
    '--remote-allow-origins=*', f'--user-data-dir={user_data_dir}',
    '--window-size=1440,900', 'http://localhost:8000/'
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
        ready = eval_js("document.readyState === 'complete' && Boolean(window.TempoMode && window.TempoPlanStore && window.TempoEmergencyFlow)")
        if ready:
            break
        time.sleep(0.5)

    eval_js("""
        (() => {
            const today = new Date().toISOString().split('T')[0];
            const testPlan = {
                id: 'plan_test', planId: 'plan_test', planType: 'emergency', title: 'Test Plan',
                plannedTasks: [
                    { dayDate: today, dayLabel: 'Today', task: { id: 't1', name: 'Task 1', completed: false, subtasks: [] } }
                ],
                tasks: []
            };
            window.TempoPlanStore.saveActivePlan('emergency', testPlan);
            window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
            window.TempoEmergencyFlow.restorePlanState();
            window.TempoMode.setMode('emergency');
        })()
    """)
    time.sleep(1)

    res = eval_js("""
        (() => {
            const navbar = document.querySelector('header');
            const navBcr = navbar.getBoundingClientRect();
            const btnHome = document.getElementById('btn-home-mode-selector');
            const btnBcr = btnHome ? btnHome.getBoundingClientRect() : null;
            const rightCol = document.querySelector('.urgent-right-col');
            const rightBcr = rightCol ? rightCol.getBoundingClientRect() : null;
            const noteHeading = document.querySelector('.urgent-right-col h3');
            const noteHeadingBcr = noteHeading ? noteHeading.getBoundingClientRect() : null;
            const main = document.querySelector('main');
            const mainBcr = main ? main.getBoundingClientRect() : null;
            const headerEl = document.querySelector('[data-tempo-ui="urgent-home-shell"] > .relative.pb-1');
            const headerBcr = headerEl ? headerEl.getBoundingClientRect() : null;

            return {
                navbarBottom: navBcr.bottom,
                btnHomeTop: btnBcr ? btnBcr.top : null,
                btnHomeHeight: btnBcr ? btnBcr.height : null,
                headerHeight: headerBcr ? headerBcr.height : null,
                rightColTop: rightBcr ? rightBcr.top : null,
                noteHeadingTop: noteHeadingBcr ? noteHeadingBcr.top : null,
                diffBtnToRightCol: (btnBcr && rightBcr) ? (rightBcr.top - btnBcr.top) : null,
                diffBtnToNoteHeading: (btnBcr && noteHeadingBcr) ? (noteHeadingBcr.top - btnBcr.top) : null,
                distanceFromNavbarToBtn: btnBcr ? (btnBcr.top - navBcr.bottom) : null
            };
        })()
    """)
    print("CURRENT POSITIONS:", json.dumps(res, indent=2))
finally:
    if ws:
        try: ws.close()
        except: pass
    try: proc.terminate()
    except: pass
