import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_test_card_content_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9275

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
msg_id = 1
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

    ws = websocket.create_connection(ws_url)

    def send_cmd(method, params=None):
        global msg_id
        cid = msg_id
        msg_id += 1
        ws.send(json.dumps({"id": cid, "method": method, "params": params or {}}))
        while True:
            resp = json.loads(ws.recv())
            if resp.get("id") == cid:
                return resp.get("result", {})

    def eval_js(expr):
        res = send_cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
        if "exceptionDetails" in res:
            raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
        return res.get("result", {}).get("value")

    send_cmd("Runtime.enable")
    time.sleep(1)

    eval_js("""
        (async () => {
            const mock = {
                id: 'local_user_test',
                email: 'test@tempo.edu',
                raw_email: 'test@tempo.edu',
                password: 'password123',
                user_metadata: { full_name: 'Innietest', display_name: 'Innietest', role: 'student' }
            };
            localStorage.setItem('tempo_mock_account_test@tempo.edu', JSON.stringify(mock));
            if (window.TempoAuth) {
                await window.TempoAuth.signIn("test@tempo.edu", "password123");
            }
        })()
    """)
    time.sleep(1)

    eval_js("window.TempoMode.setMode('emergency');")
    time.sleep(0.5)

    info = eval_js("""
        (() => {
            const qr = document.querySelector('[data-tempo-ui="urgent-support"] [title="Quick Relief"]');
            const fn = document.querySelector('[data-tempo-ui="urgent-support"] [title="Focus Now"]');
            
            const qrText = qr.querySelector('h3');
            const qrImg = qr.querySelector('img');
            const fnText = fn.querySelector('h3');
            const fnImg = fn.querySelector('img');

            const getR = el => el.getBoundingClientRect();

            return {
                qrCard: getR(qr),
                qrText: getR(qrText),
                qrImg: getR(qrImg),
                qrTextRightToImgLeft: getR(qrImg).left - getR(qrText).right,
                fnCard: getR(fn),
                fnText: getR(fnText),
                fnImg: getR(fnImg),
                fnImgRightToTextLeft: getR(fnText).left - getR(fnImg).right
            };
        })()
    """)
    print("Content metrics inside cards:")
    print(json.dumps(info, indent=2))

finally:
    if ws: ws.close()
    proc.terminate()
    proc.wait()
