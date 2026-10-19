import subprocess
import time
import json
import urllib.request
import tempfile
import websocket

def main():
    user_data_dir = tempfile.mkdtemp(prefix='tempo_measure_')
    edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    port = 9295
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
                ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined' && typeof window.TempoEmergencyFlow !== 'undefined'")
                if ready:
                    eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                    break
            except Exception:
                pass
            time.sleep(0.5)

        eval_js('''(() => {
            const today = new Date().toISOString().split('T')[0];
            const plan = {
                id: 'p1', planId: 'p1', planType: 'emergency', title: 'U',
                plannedTasks: [{ dayDate: today, dayLabel: 'Today', task: { id: 't1', name: 'Task 1', completed: false, subtasks: [] } }],
                tasks: []
            };
            window.TempoPlanStore.saveActivePlan('emergency', plan);
            window.TempoEmergencyFlow.setConfirmedPlan(plan);
            window.TempoMode.setMode('emergency');
        })()''')
        time.sleep(1)

        coords = eval_js('''(() => {
            const navbar = document.querySelector('header');
            const navBcr = navbar.getBoundingClientRect();
            const btnHome = document.getElementById('btn-home-mode-selector');
            const btnBcr = btnHome ? btnHome.getBoundingClientRect() : null;
            const rightCol = document.querySelector('.urgent-right-col');
            const rightBcr = rightCol ? rightCol.getBoundingClientRect() : null;
            const main = document.querySelector('main');
            const mainBcr = main ? main.getBoundingClientRect() : null;

            return {
                navbarBottom: navBcr.bottom,
                mainTop: mainBcr.top,
                btnHomeTop: btnBcr ? btnBcr.top : null,
                btnHomeHeight: btnBcr ? btnBcr.height : null,
                rightColTop: rightBcr ? rightBcr.top : null,
                diffBtnAndRight: (rightBcr && btnBcr) ? (rightBcr.top - btnBcr.top) : null,
                diffNavAndBtn: (btnBcr) ? (btnBcr.top - navBcr.bottom) : null
            };
        })()''')
        print("MEASUREMENTS:", json.dumps(coords, indent=2))
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
