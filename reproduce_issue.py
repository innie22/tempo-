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
os.makedirs(artifact_dir, exist_ok=True)

user_data_dir = tempfile.mkdtemp(prefix="tempo_repro_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9299

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,900",
    "http://127.0.0.1:8000/#today"
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
    if "exceptionDetails" in res:
        print(f"JS ERROR: {res['exceptionDetails']}")
    return res.get("result", {}).get("value")

def capture_screenshot(filename):
    res = send_cmd("Page.captureScreenshot", {"format": "png"})
    if "data" in res:
        img_bytes = base64.b64decode(res["data"])
        filepath = os.path.join(artifact_dir, filename)
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        print(f"Screenshot saved: {filepath}")

try:
    time.sleep(2)
    tabs_res = urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read().decode()
    tabs = json.loads(tabs_res)
    app_tabs = [t for t in tabs if "127.0.0.1:8000" in t.get("url", "") or "localhost:8000" in t.get("url", "")]
    target_tab = app_tabs[0] if app_tabs else tabs[0]
    ws_url = target_tab["webSocketDebuggerUrl"]
    ws = websocket.create_connection(ws_url)

    send_cmd("Page.enable")
    send_cmd("Runtime.enable")
    time.sleep(2)

    print("=====================================================================")
    print("REPRODUCING ISSUE: SWITCH TO ENGLISH (EN) ON #today")
    print("=====================================================================")

    # Set language to 'en' using official switcher method
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(1)

    repro_data = eval_js("""
    (() => {
        const switcherText = document.getElementById('navbar-current-lang')?.textContent?.trim();
        const bodyText = document.body.innerText;
        
        const hasKeHoach = bodyText.includes('Kế hoạch') && (bodyText.includes('Làm việc của bạn') || bodyText.includes('làm việc của bạn'));
        const hasDieuChinh = bodyText.includes('Điều chỉnh Kế hoạch') || bodyText.includes('Điều chỉnh kế hoạch');
        const hasGiaiToa = bodyText.includes('Giải tỏa nhanh');
        const hasTapTrung = bodyText.includes('Tập trung ngay');

        // Look for headings and buttons in the working plan and support row
        const headings = Array.from(document.querySelectorAll('h3, button, span, div')).map(el => el.textContent.trim()).filter(Boolean);
        
        return {
            currentLang: window.TempoI18n ? window.TempoI18n.getLanguage() : null,
            switcherText: switcherText,
            hasKeHoach: hasKeHoach,
            hasDieuChinh: hasDieuChinh,
            hasGiaiToa: hasGiaiToa,
            hasTapTrung: hasTapTrung,
            sampleMatches: headings.filter(t => 
                t.includes('Kế hoạch') || t.includes('Điều chỉnh') || t.includes('Giải tỏa') || t.includes('Tập trung')
            ).slice(0, 15)
        };
    })()
    """)

    print("Reproduction Data:", json.dumps(repro_data, indent=2, ensure_ascii=False))
    capture_screenshot("reproduce_en_mode_vietnamese_text.png")

finally:
    if ws:
        ws.close()
    proc.terminate()
