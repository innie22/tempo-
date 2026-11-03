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
user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_recitems_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9638

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
    "http://127.0.0.1:8000/#recovery"
]

proc = subprocess.Popen(cmd)
time.sleep(3.0)

try:
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
        print(f"  [Screenshot] Saved cropped: {filepath}")

    time.sleep(2)
    # Add items to recovery note
    eval_js("""
    window.TempoRecoveryNote.addItem('warning_sign', 'Feeling tension in neck and shoulders');
    window.TempoRecoveryNote.addItem('helper', '5 minutes slow breathing with window open');
    window.TempoRecoveryNote.addItem('reminder', 'You do not have to solve everything today.');
    window.TempoRecoveryNote.addItem('support_person', 'Mai', { relationship: 'Roommate' });
    window.TempoI18n.setLanguage('vi');
    window.TempoRecoveryNote.openViewModal();
    """)
    time.sleep(0.5)
    capture_element("#modal-recovery-note-view .tempo-card", "recovery_notice_modal_vi_with_items.png")

    eval_js("""
    window.TempoI18n.setLanguage('en');
    """)
    time.sleep(0.5)
    capture_element("#modal-recovery-note-view .tempo-card", "recovery_notice_modal_en_with_items.png")
    print("Done testing with items!")
finally:
    try:
        ws.close()
    except Exception:
        pass
    proc.kill()
