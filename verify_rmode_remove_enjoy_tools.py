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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_enjoy_tools_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9348

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1200"
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
        resp = json.loads(ws.recv())
        if resp.get("id") == cmd_obj["id"]:
            return resp.get("result", {})

def eval_js(expr):
    res = send_cmd("Runtime.evaluate", {
        "expression": expr,
        "returnByValue": True,
        "awaitPromise": True
    })
    if "exceptionDetails" in res:
        print("JS Exception:", res["exceptionDetails"])
    return res.get("result", {}).get("value")

try:
    ws_url = None
    for _ in range(40):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as resp:
                tabs = json.loads(resp.read().decode())
                pages = [t for t in tabs if t.get("type") == "page" and not t.get("url", "").startswith("chrome-extension://")]
                if pages:
                    ws_url = pages[0]["webSocketDebuggerUrl"]
                    break
        except Exception:
            time.sleep(0.5)

    if not ws_url:
        raise RuntimeError("Failed to connect to Edge CDP")

    ws = websocket.create_connection(ws_url)

    send_cmd("Page.navigate", {"url": "http://127.0.0.1:8000/"})
    for _ in range(30):
        ready = eval_js("typeof window.TempoMode !== 'undefined' && typeof window.TempoMode.setMode === 'function'")
        if ready:
            break
        time.sleep(0.3)

    # 1. Switch to Recovery Mode
    print("\n--- Test 1: Switch to Recovery Mode ---")
    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(1.5)
    mode = eval_js("window.TempoMode.getMode()")
    assert mode == 'recovery', f"Expected recovery mode, got {mode}"
    print("Mode is recovery.")

    # 2. Check for absence of Enjoy Tempo Tools section
    print("\n--- Test 2: Check Enjoy Tempo Tools Absence ---")
    check_info = eval_js("""
        (() => {
            const enjoySec = document.getElementById('enjoy-tempo-tools');
            const enjoyDataUi = document.querySelector('[data-tempo-ui="recovery-enjoy-tempo-tools"]');
            const headings = Array.from(document.querySelectorAll('h2, h3, h4')).map(h => h.textContent.trim());
            const hasHeading = headings.some(h => h.includes('Enjoy Tempo Tools'));
            const shell = document.querySelector('[data-tempo-ui="recovery-home-shell"]');
            const lastChild = shell ? shell.lastElementChild : null;
            const grid = document.querySelector('.recovery-plan-comm-grid');
            
            return {
                hasEnjoySec: !!enjoySec,
                hasEnjoyDataUi: !!enjoyDataUi,
                hasHeading: hasHeading,
                lastChildClass: lastChild ? lastChild.className : null,
                lastChildIsGrid: lastChild === grid,
                planExists: !!document.getElementById('recovery-working-plan'),
                commExists: !!document.querySelector('[data-tempo-ui="recovery-community"]')
            };
        })()
    """)
    print("DOM absence check:", json.dumps(check_info, indent=2))
    assert check_info['hasEnjoySec'] is False, "Found #enjoy-tempo-tools still in DOM!"
    assert check_info['hasEnjoyDataUi'] is False, "Found [data-tempo-ui='recovery-enjoy-tempo-tools'] still in DOM!"
    assert check_info['hasHeading'] is False, "Found 'Enjoy Tempo Tools' heading still in DOM!"
    assert check_info['lastChildIsGrid'] is True, "Expected last element of recovery-home-shell to be .recovery-plan-comm-grid!"
    assert check_info['planExists'] is True, "Working plan card missing!"
    assert check_info['commExists'] is True, "Community card missing!"

    # 3. Capture desktop screenshot of bottom section and full page
    print("\n--- Test 3: Capture Screenshots ---")
    # Scroll to bottom
    eval_js("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(0.5)
    ss_bottom = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "rmode_dashboard_bottom_no_enjoy_tools.png"), "wb") as f:
        f.write(base64.b64decode(ss_bottom["data"]))
    print("Saved rmode_dashboard_bottom_no_enjoy_tools.png")

    # Full page screenshot
    eval_js("window.scrollTo(0, 0);")
    time.sleep(0.5)
    ss_full = send_cmd("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
    with open(os.path.join(artifact_dir, "rmode_full_page_no_enjoy_tools.png"), "wb") as f:
        f.write(base64.b64decode(ss_full["data"]))
    print("Saved rmode_full_page_no_enjoy_tools.png")

    # 4. Mobile (375px) responsive check
    print("\n--- Test 4: Mobile Responsive Check ---")
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 375,
        "height": 812,
        "deviceScaleFactor": 2,
        "mobile": True
    })
    time.sleep(0.5)
    eval_js("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(0.5)
    ss_mobile = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "rmode_mobile_bottom_no_enjoy_tools.png"), "wb") as f:
        f.write(base64.b64decode(ss_mobile["data"]))
    print("Saved rmode_mobile_bottom_no_enjoy_tools.png")
    send_cmd("Emulation.clearDeviceMetricsOverride")

    # 5. Verify Underlying Tools remain accessible
    print("\n--- Test 5: Verify Underlying Tools Accessibility ---")
    # Focus Zone
    has_focus_func = eval_js("typeof window.TempoFocusZone !== 'undefined' && typeof window.TempoFocusZone.open === 'function'")
    print("TempoFocusZone accessible:", has_focus_func)
    assert has_focus_func is True, "TempoFocusZone not accessible!"

    # Breathing Modal
    has_breathing_func = eval_js("typeof window.TempoBreathing !== 'undefined' || typeof window.TempoTriage?.openBoxBreathingModal === 'function'")
    print("Breathing modal accessible:", has_breathing_func)
    assert has_breathing_func is True, "Breathing modal not accessible!"

    # Notes Tool navigation
    eval_js("if (window.TempoApp && window.TempoApp.navigateTo) window.TempoApp.navigateTo('tool-notes');")
    time.sleep(0.8)
    notes_visible = eval_js("!document.getElementById('view-notes')?.classList.contains('hidden')")
    print("Notes tool navigated and visible:", notes_visible)
    assert notes_visible is True, "Notes tool route failed!"

    # 6. Verify URmode and EntryHome untouched
    print("\n--- Test 6: Verify URmode Untouched ---")
    eval_js("window.TempoMode.setMode('emergency');")
    time.sleep(1.2)
    ur_mode = eval_js("window.TempoMode.getMode()")
    assert ur_mode == 'emergency', "Failed to switch to emergency mode!"
    ur_plan = eval_js("!!document.querySelector('[data-tempo-ui=\"urgent-posts\"]')")
    assert ur_plan is True, "URmode community posts missing!"
    print("URmode verified untouched and fully operational.")

    print("\n==================================================")
    print("ALL REMOVAL & REGRESSION TESTS PASSED!")
    print("==================================================")

finally:
    if ws:
        try:
            ws.close()
        except Exception:
            pass
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()
