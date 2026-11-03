import subprocess, time, json, urllib.request, tempfile, websocket, sys, os

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_debug_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9603

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "http://127.0.0.1:8000/#home"
]

proc = subprocess.Popen(cmd)
time.sleep(3.0)

page_target = None
for _ in range(30):
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
        targets = json.loads(req.read().decode("utf-8"))
        if targets:
            match = [t for t in targets if t.get("type") == "page" and "127.0.0.1" in t.get("url", "")]
            if match:
                page_target = match[0]
                break
    except Exception:
        pass
    time.sleep(0.5)

ws = websocket.create_connection(page_target["webSocketDebuggerUrl"])
msg_id = 1
def eval_js(expr):
    global msg_id
    msg = json.dumps({'id': msg_id, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}})
    ws.send(msg)
    msg_id += 1
    while True:
        resp = json.loads(ws.recv())
        if resp.get('id') == msg_id - 1:
            print("RESP:", resp)
            return resp.get('result', {}).get('result', {}).get('value')

print("1. Setup auth and rmode:")
eval_js("""
(() => {
    const user = { id: 'test_user', email: 'test@tempo.app', name: 'Innie Test' };
    localStorage.setItem('tempo_auth_user', JSON.stringify(user));
    sessionStorage.setItem('tempo_rmode_session_welcomed_test_user', 'true');
    window.TempoAuth.init();
    window.TempoMode.init();
    window.TempoMode.transitionContext('recovery', { silent: true, skipSetupCheck: true });
    return {
        user: window.TempoAuth.getCurrentUser(),
        context: window.TempoMode.getActiveContext(),
        mode: window.TempoMode.getMode()
    };
})()
""")

print("2. Call openUcheck:")
eval_js("""
(() => {
    window.TempoMode.openUcheck({ sourceContext: 'recovery' });
    return {
        tool: window.TempoMode.getActiveSharedTool(),
        context: window.TempoMode.getActiveContext(),
        mode: window.TempoMode.getMode(),
        umodeBoxHidden: document.getElementById('umode-home-content').classList.contains('hidden'),
        btn: Boolean(document.getElementById('btn-ucheck-back-to-dashboard'))
    };
})()
""")

ws.close()
proc.kill()
