import subprocess, time, json, urllib.request, tempfile, websocket, sys, os, base64

sys.stdout.reconfigure(encoding='utf-8')

artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_posts_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9565

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#community?tab=posts"
]

proc = subprocess.Popen(cmd)
ws = None
msg_id = 1

def send_cmd(method, params=None):
    global msg_id, ws
    cmd_obj = {"id": msg_id, "method": method, "params": params or {}}
    msg_id += 1
    ws.send(json.dumps(cmd_obj))
    while True:
        res = json.loads(ws.recv())
        if res.get("id") == cmd_obj["id"]:
            return res.get("result", {})

def eval_js(expression):
    res = send_cmd("Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True
    })
    return res.get("result", {}).get("value")

try:
    time.sleep(2.5)
    tabs_res = urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read().decode()
    tabs = json.loads(tabs_res)
    app_tab = next(t for t in tabs if "8000" in t.get("url", ""))

    ws = websocket.create_connection(app_tab["webSocketDebuggerUrl"], timeout=10)
    send_cmd("Page.enable")
    send_cmd("DOM.enable")
    time.sleep(1)

    eval_js("window.TempoCommunity.selectTab('posts'); window.TempoI18n.setLanguage('vi');")
    time.sleep(0.5)

    spans = eval_js("""
    (() => {
        const post1 = document.querySelector('[data-post-id="post-1"]');
        const list = [];
        post1.querySelectorAll('.space-y-1').forEach(c => {
            const spans = c.querySelectorAll('span');
            list.push(Array.from(spans).map(s => s.innerText.trim()));
        });
        return list;
    })()
    """)
    print("Comment spans in post-1:", spans)
finally:
    try:
        ws.close()
    except Exception:
        pass
    proc.terminate()
