import sys, os, json, time, subprocess, urllib.request, websocket

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CDP_PORT = 9543
TARGET_URL = "http://127.0.0.1:8000/"

def run():
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    edge_binary = next((p for p in edge_paths if os.path.exists(p)), None)
    user_data_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), f"cdp_dbg_{int(time.time())}")
    cmd = [
        edge_binary,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--headless=new",
        "--disable-gpu",
        "--window-size=1280,1000",
        TARGET_URL
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.0)

    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json")
        pages = json.loads(req.read().decode())
        ws_url = None
        for page in pages:
            if page.get("type") == "page" and "127.0.0.1:8000" in page.get("url", ""):
                ws_url = page["webSocketDebuggerUrl"]
                break
        if not ws_url:
            ws_url = pages[0]["webSocketDebuggerUrl"]
        ws = websocket.create_connection(ws_url, timeout=15)
        
        req_id = 0
        def eval_js(code):
            nonlocal req_id
            req_id += 1
            ws.send(json.dumps({"id": req_id, "method": "Runtime.evaluate", "params": {"expression": code, "returnByValue": True, "awaitPromise": True}}))
            while True:
                r = json.loads(ws.recv())
                if r.get("id") == req_id:
                    if "exceptionDetails" in r.get("result", {}):
                        print("JS Error:", r["result"]["exceptionDetails"])
                    return r.get("result", {}).get("result", {}).get("value")

        print("Testing plan-workspace navigation...")
        eval_js("""
            if (window.TempoAuth) {
                window.TempoAuth.getCurrentUser = () => ({ id: 'mock-user-1', email: 'user@tempo.test' });
            }
            if (window.TempoMode) {
                window.TempoMode.switchMode('emergency');
            }
        """)
        time.sleep(0.5)

        h1 = eval_js("window.location.hash")
        print("Hash 1:", h1)

        eval_js("window.TempoApp.navigateTo('plan-workspace')")
        time.sleep(0.5)

        h2 = eval_js("window.location.hash")
        print("Hash 2:", h2)

        is_pw_open = eval_js("!document.getElementById('screen-plan-workspace').classList.contains('hidden')")
        print("Plan workspace screen visible:", is_pw_open)

        # Now test openBreakTaskModal from plan workspace
        eval_js("window.TempoPlanWorkspace.openBreakTaskModal('task-test-1')")
        time.sleep(0.5)

        ret_dest = eval_js("window.TempoUrmodeFlow.getBreakdownReturnDestination()")
        print("Breakdown return destination:", ret_dest)

        # Now close modal
        eval_js("window.TempoUrmodeFlow.closeModal(window.TempoUrmodeFlow.getBreakdownReturnDestination())")
        time.sleep(0.5)

        h3 = eval_js("window.location.hash")
        print("Hash 3 (after close):", h3)

        ws.close()
    finally:
        proc.kill()

run()
