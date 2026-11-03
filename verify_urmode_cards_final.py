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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_urmode_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9279

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

    # Sign in as Innietest
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

    # Set mode to Emergency (URmode)
    eval_js("window.TempoMode.setMode('emergency');")
    time.sleep(0.5)

    # 1. Desktop Metrics Inspection (1440x900)
    desktop_metrics = eval_js("""
        (() => {
            const row = document.querySelector('[data-tempo-ui="urgent-support"]');
            const cardAbove = document.querySelector('[data-tempo-ui="urgent-left-col"] > :first-child');
            const qr = row.querySelector('[title="Quick Relief"]');
            const fn = row.querySelector('[title="Focus Now"]');

            const rCardAbove = cardAbove.getBoundingClientRect();
            const rQr = qr.getBoundingClientRect();
            const rFn = fn.getBoundingClientRect();
            const rRow = row.getBoundingClientRect();

            const csQr = window.getComputedStyle(qr);
            const csFn = window.getComputedStyle(fn);

            const qrMascot = qr.querySelector('img');
            const fnMascot = fn.querySelector('img');
            const rQrMascot = qrMascot ? qrMascot.getBoundingClientRect() : null;
            const rFnMascot = fnMascot ? fnMascot.getBoundingClientRect() : null;

            const qrText = qr.innerText.trim();
            const fnText = fn.innerText.trim();

            const centerCardAbove = rCardAbove.left + rCardAbove.width / 2;
            const centerCombinedCards = (rQr.left + rFn.right) / 2;

            return {
                cardAbove: {
                    x: rCardAbove.left,
                    y: rCardAbove.top,
                    width: rCardAbove.width,
                    height: rCardAbove.height,
                    center: centerCardAbove
                },
                qr: {
                    x: rQr.left,
                    y: rQr.top,
                    width: rQr.width,
                    height: rQr.height,
                    overflow: csQr.overflow,
                    text: qrText,
                    hasSubtitle: qrText.includes('Quick ways to ease stress'),
                    mascot: {
                        src: qrMascot ? qrMascot.getAttribute('src') : null,
                        width: rQrMascot ? rQrMascot.width : null,
                        height: rQrMascot ? rQrMascot.height : null
                    }
                },
                fn: {
                    x: rFn.left,
                    y: rFn.top,
                    width: rFn.width,
                    height: rFn.height,
                    overflow: csFn.overflow,
                    text: fnText,
                    hasSubtitle: fnText.includes('Your own personalized workspace'),
                    mascot: {
                        src: fnMascot ? fnMascot.getAttribute('src') : null,
                        width: rFnMascot ? rFnMascot.width : null,
                        height: rFnMascot ? rFnMascot.height : null
                    }
                },
                group: {
                    left: rQr.left,
                    right: rFn.right,
                    width: rFn.right - rQr.left,
                    gap: rFn.left - rQr.right,
                    center: centerCombinedCards,
                    diffFromCardAboveCenter: Math.abs(centerCardAbove - centerCombinedCards)
                }
            };
        })()
    """)

    print("=== DESKTOP METRICS (1440x900) ===")
    print(json.dumps(desktop_metrics, indent=2))

    # Helper function to take screenshot
    def save_screenshot(filename, clip=None):
        params = {"format": "png"}
        if clip:
            params["clip"] = clip
        res = send_cmd("Page.captureScreenshot", params)
        data = base64.b64decode(res["data"])
        filepath = os.path.join(artifact_dir, filename)
        with open(filepath, "wb") as f:
            f.write(data)
        print(f"Saved screenshot: {filepath} ({len(data)} bytes)")

    # Capture Desktop Full Dashboard
    save_screenshot("urmode_dashboard_desktop_1440.png")

    # Capture Closeup of the Two-Card Group + bottom of card above
    clip_closeup = eval_js("""
        (() => {
            const row = document.querySelector('[data-tempo-ui="urgent-support"]');
            const cardAbove = document.querySelector('[data-tempo-ui="urgent-left-col"] > :first-child');
            const rRow = row.getBoundingClientRect();
            const rCardAbove = cardAbove.getBoundingClientRect();

            const top = Math.max(0, rCardAbove.bottom - 40);
            const bottom = rRow.bottom + 40;
            const left = Math.max(0, rCardAbove.left - 20);
            const right = rCardAbove.right + 20;

            return {
                x: left,
                y: top,
                width: right - left,
                height: bottom - top,
                scale: 1
            };
        })()
    """)
    save_screenshot("urmode_cards_closeup.png", clip_closeup)

    # Test Mobile Viewport (375x812)
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 375,
        "height": 812,
        "deviceScaleFactor": 1,
        "mobile": True
    })
    time.sleep(0.5)

    mobile_metrics = eval_js("""
        (() => {
            const row = document.querySelector('[data-tempo-ui="urgent-support"]');
            const qr = row.querySelector('[title="Quick Relief"]');
            const fn = row.querySelector('[title="Focus Now"]');

            const rQr = qr.getBoundingClientRect();
            const rFn = fn.getBoundingClientRect();

            return {
                scrollWidth: document.documentElement.scrollWidth,
                innerWidth: window.innerWidth,
                hasOverflow: document.documentElement.scrollWidth > window.innerWidth,
                qrWidth: rQr.width,
                qrHeight: rQr.height,
                fnWidth: rFn.width,
                fnHeight: rFn.height,
                stackedVertically: rFn.top >= rQr.bottom
            };
        })()
    """)

    print("\n=== MOBILE METRICS (375x812) ===")
    print(json.dumps(mobile_metrics, indent=2))

    save_screenshot("urmode_dashboard_mobile_375.png")

    # Reset viewport back to desktop for modal click test
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 1440,
        "height": 900,
        "deviceScaleFactor": 1,
        "mobile": False
    })
    time.sleep(0.5)

    # Click Quick Relief card
    click_result = eval_js("""
        (() => {
            const qr = document.querySelector('[data-tempo-ui="urgent-support"] [title="Quick Relief"]');
            qr.click();
            return true;
        })()
    """)
    time.sleep(0.5)

    modal_open = eval_js("""
        (() => {
            const modal = document.querySelector('#quickReliefModal, [data-tempo-modal="stress-relief"], .quick-relief-modal, #stressReliefModal') ||
                          document.querySelector('[id*="relief" i], [id*="stress" i]');
            return modal ? { id: modal.id, visible: window.getComputedStyle(modal).display !== 'none' } : null;
        })()
    """)
    print("\n=== QUICK RELIEF MODAL TEST ===")
    print("Modal status:", modal_open)
    save_screenshot("urmode_quick_relief_modal.png")

    # Close modal if open
    eval_js("""
        (() => {
            if (window.TempoStressRelief && window.TempoStressRelief.closeModal) window.TempoStressRelief.closeModal();
            const closeBtn = document.querySelector('#quickReliefModal button, [data-close-modal]');
            if (closeBtn) closeBtn.click();
        })()
    """)
    time.sleep(0.3)

    # Verify Rmode is intact
    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(0.5)
    rmode_intact = eval_js("""
        (() => {
            const rbox = document.getElementById('rmodeDashboard');
            return {
                hasRmode: Boolean(rbox),
                title: rbox ? rbox.querySelector('h1, h2, h3')?.innerText : null
            };
        })()
    """)
    print("\n=== RMODE INTEGRITY ===")
    print(rmode_intact)

    print("\nVerification complete!")

finally:
    if ws: ws.close()
    proc.terminate()
    proc.wait()
