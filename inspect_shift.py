import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_inspect_shift_")
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

    def wait_for_ready():
        for _ in range(30):
            try:
                res = eval_js("Boolean(window.TempoAuth && window.TempoMode && window.TempoApp)")
                if res is True:
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        raise TimeoutError("Tempo was not initialized.")

    wait_for_ready()

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

    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(0.5)

    shift_info = eval_js("""
        (() => {
            const row = document.querySelector('.recovery-support-row');
            const selfCheck = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            const qr = row.querySelector('[title="Quick Relief"]');
            const fn = row.querySelector('[title="Focus Now"]');

            fn.classList.remove('recovery-card-focus-now');
            fn.style.margin = '0px';

            const rSelfCheck = selfCheck.getBoundingClientRect();
            const rQr = qr.getBoundingClientRect();
            const rFn = fn.getBoundingClientRect();

            const centerSelfCheck = rSelfCheck.left + rSelfCheck.width / 2;
            const centerCombinedCards = (rQr.left + rFn.right) / 2;

            return {
                centerSelfCheck,
                centerCombinedCards,
                diffCenter: Math.abs(centerSelfCheck - centerCombinedCards),
                qrLeft: rQr.left,
                fnRight: rFn.right,
                qrTop: rQr.top,
                fnTop: rFn.top,
                gap: rFn.left - rQr.right
            };
        })()
    """)

    print(json.dumps(shift_info, indent=2))

finally:
    if ws: ws.close()
    proc.terminate()
    proc.wait()
