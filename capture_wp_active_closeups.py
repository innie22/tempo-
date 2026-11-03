import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os
import base64

sys.stdout.reconfigure(encoding='utf-8')

artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"

user_data_dir = tempfile.mkdtemp(prefix="tempo_crop_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9618

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#home"
]

proc = subprocess.Popen(cmd)
time.sleep(3.0)

req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
targets = json.loads(req.read().decode("utf-8"))
page_target = [t for t in targets if t.get("type") == "page" and "127.0.0.1" in t.get("url", "")][0]
ws = websocket.create_connection(page_target["webSocketDebuggerUrl"])

msg_id = 1
def send_cmd(method, params=None):
    global msg_id, ws
    cmd_obj = {"id": msg_id, "method": method, "params": params or {}}
    msg_id += 1
    ws.send(json.dumps(cmd_obj))
    while True:
        raw = ws.recv()
        res = json.loads(raw)
        if res.get("id") == cmd_obj["id"]:
            return res.get("result", {})

def eval_js(expression):
    res = send_cmd("Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True
    })
    return res.get("result", {}).get("value")

def capture_element(selector, filename):
    rect = eval_js(f"""
    (() => {{
        const el = document.querySelector('{selector}');
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return {{ x: Math.max(0, r.x - 10), y: Math.max(0, r.y - 10), width: r.width + 20, height: r.height + 20 }};
    }})()
    """)
    if not rect:
        print(f"Element not found for {selector}")
        return
    clip = {
        "x": rect["x"],
        "y": rect["y"],
        "width": rect["width"],
        "height": rect["height"],
        "scale": 1
    }
    res = send_cmd("Page.captureScreenshot", {"format": "png", "clip": clip})
    data = res.get("data", "")
    filepath = os.path.join(artifact_dir, filename)
    with open(filepath, "wb") as f:
        f.write(base64.b64decode(data))
    print(f"Saved cropped screenshot: {filepath}")

time.sleep(2.0)

# Seed plan and VI
eval_js("""
(() => {
    const futureDate = new Date(Date.now() + 86400000).toISOString();
    const activePlan = {
        title: "Active Urgent Plan",
        tasks: [{ id: "task-1", title: "Complete report", duration: 30, deadline: futureDate, status: "pending" }]
    };
    window.TempoPlanStore.saveActivePlan('emergency', activePlan);
    window.TempoI18n.setLanguage('vi');
    window.TempoUrmodeFlow.showResetPopup('PLAN_NO_OVERDUE');
})()
""")
time.sleep(0.5)
capture_element("#modal-urmode-flow .tempo-card", "working_plan_active_modal_vi_closeup.png")

# EN
eval_js("window.TempoI18n.setLanguage('en')")
time.sleep(0.5)
capture_element("#modal-urmode-flow .tempo-card", "working_plan_active_modal_en_closeup.png")

# Checkpoint VI
eval_js("""
(() => {
    window.TempoI18n.setLanguage('vi');
    window.TempoUrmodeFlow.showAreYouReadyPopup();
})()
""")
time.sleep(0.5)
capture_element("#modal-urmode-flow .tempo-card", "grounded_checkpoint_modal_vi_closeup.png")

# Checkpoint EN
eval_js("window.TempoI18n.setLanguage('en')")
time.sleep(0.5)
capture_element("#modal-urmode-flow .tempo-card", "grounded_checkpoint_modal_en_closeup.png")

ws.close()
proc.terminate()
print("Done capturing closeups!")
