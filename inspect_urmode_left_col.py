import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_inspect_cards_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9274

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
            const leftCol = document.querySelector('[data-tempo-ui="urgent-left-col"]');
            const children = leftCol ? Array.from(leftCol.children) : [];
            return children.map(c => {
                const r = c.getBoundingClientRect();
                return {
                    tag: c.tagName,
                    id: c.id,
                    className: c.className,
                    dataTempoUi: c.getAttribute('data-tempo-ui'),
                    rect: { x: r.x, y: r.y, width: r.width, height: r.height, left: r.left, right: r.right, centerX: r.x + r.width / 2 },
                    title: c.querySelector('h1, h2, h3, h4')?.textContent.trim()
                };
            });
        })()
    """)
    print("Children of urgent-left-col:")
    print(json.dumps(info, indent=2))

    # Also check if there is any element containing 'self-check' or 'Self-check' in URmode
    sc_info = eval_js("""
        (() => {
            const all = Array.from(document.querySelectorAll('#emode-home-content *'));
            const matching = all.filter(el => (el.textContent || '').includes('Self-check') && el.children.length === 0);
            return matching.map(el => ({
                tag: el.tagName,
                text: el.textContent.trim(),
                parentTag: el.parentElement.tagName,
                parentClass: el.parentElement.className
            }));
        })()
    """)
    print("\nSelf-check elements in URmode:")
    print(json.dumps(sc_info, indent=2))

finally:
    if ws: ws.close()
    proc.terminate()
    proc.wait()
