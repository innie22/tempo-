import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

user_data_dir = tempfile.mkdtemp(prefix="tempo_fn_card_test_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9272

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

    def capture_screenshot(filepath, clip=None):
        params = {"format": "png"}
        if clip:
            params["clip"] = clip
        res = send_cmd("Page.captureScreenshot", params)
        import base64
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(res["data"]))
        log(f"Saved screenshot: {filepath}")

    send_cmd("Runtime.enable")
    send_cmd("Page.enable")
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

    log("Authenticating test user...")
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

    is_auth = eval_js("Boolean(window.TempoAuth && window.TempoAuth.getCurrentUser())")
    log(f"Authenticated: {is_auth}")
    assert is_auth is True

    # Switch to Rmode
    log("\n--- TEST 1: Inspecting Support Row Cards in Rmode ---")
    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(0.5)

    row_data = eval_js("""
        (() => {
            const row = document.querySelector('.recovery-support-row');
            if (!row) return null;
            const cards = Array.from(row.children);
            const qr = cards[0];
            const fn = cards[1];
            const qrRect = qr ? qr.getBoundingClientRect() : null;
            const fnRect = fn ? fn.getBoundingClientRect() : null;

            const hasLearnSolve = !!row.querySelector('[title="Learn & Solve"]') || Array.from(row.querySelectorAll('h3')).some(h => (h.textContent || '').includes('Learn'));

            return {
                cardCount: cards.length,
                hasLearnSolve,
                qr: qr ? {
                    title: qr.getAttribute('title') || qr.querySelector('h3')?.textContent.trim(),
                    desc: qr.querySelector('p')?.textContent.trim(),
                    imgSrc: qr.querySelector('img')?.getAttribute('src'),
                    rect: {
                        x: qrRect.x,
                        y: qrRect.y,
                        width: qrRect.width,
                        height: qrRect.height
                    },
                    classes: qr.className
                } : null,
                fn: fn ? {
                    title: fn.getAttribute('title') || fn.querySelector('h3')?.textContent.trim(),
                    desc: fn.querySelector('p')?.textContent.trim(),
                    imgSrc: fn.querySelector('img')?.getAttribute('src'),
                    rect: {
                        x: fnRect.x,
                        y: fnRect.y,
                        width: fnRect.width,
                        height: fnRect.height
                    },
                    classes: fn.className,
                    onclick: fn.getAttribute('onclick')
                } : null,
                gap: fnRect && qrRect ? fnRect.x - (qrRect.x + qrRect.width) : null
            };
        })()
    """)

    log(f"Row data: {json.dumps(row_data, indent=2)}")
    assert row_data is not None, "Support row must exist"
    assert row_data["cardCount"] == 2, f"Expected 2 cards, got {row_data['cardCount']}"
    assert row_data["hasLearnSolve"] is False, "Learn & Solve card must be removed from support row"

    # Verify Focus Now card
    fn = row_data["fn"]
    assert fn is not None, "Focus Now card must exist"
    assert fn["title"] == "Focus Now", f"Expected title 'Focus Now', got '{fn['title']}'"
    assert "workspace" in fn["desc"], f"Expected 'workspace' in desc, got '{fn['desc']}'"
    assert fn["imgSrc"] == "assets/focus-now-mascot.png", f"Expected mascot assets/focus-now-mascot.png, got '{fn['imgSrc']}'"
    assert "bg-[#D29C85]" in fn["classes"], f"Expected bg-[#D29C85], got '{fn['classes']}'"
    assert "rounded-3xl" in fn["classes"], f"Expected rounded-3xl, got '{fn['classes']}'"
    assert fn["rect"]["height"] == 175, f"Expected height 175px, got {fn['rect']['height']}"

    # Verify Quick Relief card
    qr = row_data["qr"]
    assert qr is not None, "Quick Relief card must exist"
    assert qr["title"] == "Quick Relief", f"Expected title 'Quick Relief', got '{qr['title']}'"
    assert qr["imgSrc"] == "assets/quick-relief-mascot-transparent.png"
    assert qr["rect"]["height"] == 175, f"Expected QR height 175px, got {qr['rect']['height']}"

    # Verify alignment & dimensions
    assert fn["rect"]["width"] == qr["rect"]["width"], f"Focus Now width ({fn['rect']['width']}) != Quick Relief width ({qr['rect']['width']})"
    assert fn["rect"]["y"] == qr["rect"]["y"], f"Focus Now top ({fn['rect']['y']}) != Quick Relief top ({qr['rect']['y']})"
    assert abs(row_data["gap"] - 16.0) < 0.5, f"Expected 16px gap, got {row_data['gap']}"
    log("✓ Dimensions, alignment, width, height, and gap perfectly verified!")

    # Verify Click on Focus Now card triggers openQuickEntry
    log("\n--- TEST 2: Testing Focus Now click interaction ---")
    click_test = eval_js("""
        (() => {
            let called = false;
            const originalFn = window.TempoFocusZone ? window.TempoFocusZone.openQuickEntry : null;
            if (!window.TempoFocusZone) window.TempoFocusZone = {};
            window.TempoFocusZone.openQuickEntry = () => { called = true; };

            const fnCard = document.querySelector('.recovery-support-row > div:nth-child(2)');
            if (fnCard) fnCard.click();

            if (originalFn) window.TempoFocusZone.openQuickEntry = originalFn;
            return called;
        })()
    """)
    log(f"Focus Now onclick triggered openQuickEntry: {click_test}")
    assert click_test is True, "Clicking Focus Now must trigger window.TempoFocusZone.openQuickEntry"
    log("✓ Focus Now click interaction verified!")

    # Capture screenshots
    artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
    row_rect = eval_js("""
        (() => {
            const r = document.querySelector('.recovery-support-row').getBoundingClientRect();
            return { x: r.x - 10, y: r.y - 10, width: r.width + 20, height: r.height + 20 };
        })()
    """)
    capture_screenshot(
        os.path.join(artifact_dir, "rmode_focus_now_card_closeup.png"),
        clip={"x": row_rect["x"], "y": row_rect["y"], "width": row_rect["width"], "height": row_rect["height"], "scale": 1}
    )

    capture_screenshot(
        os.path.join(artifact_dir, "rmode_dashboard_with_focus_now_desktop.png"),
        clip={"x": 0, "y": 0, "width": 1440, "height": 900, "scale": 1}
    )

    # Test Mobile Viewport (375x812)
    log("\n--- TEST 3: Mobile Viewport (375px) ---")
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 375,
        "height": 812,
        "deviceScaleFactor": 1,
        "mobile": True
    })
    time.sleep(0.5)

    mobile_info = eval_js("""
        (() => {
            const row = document.querySelector('.recovery-support-row');
            const cards = row ? Array.from(row.children) : [];
            return {
                cardsStacked: cards.length === 2 && cards[1].getBoundingClientRect().y > cards[0].getBoundingClientRect().y,
                noOverflow: document.documentElement.scrollWidth <= window.innerWidth
            };
        })()
    """)
    log(f"Mobile info: {mobile_info}")
    assert mobile_info["cardsStacked"] is True, "Cards should stack vertically on mobile"
    assert mobile_info["noOverflow"] is True, "No horizontal overflow on mobile"

    capture_screenshot(
        os.path.join(artifact_dir, "rmode_dashboard_with_focus_now_mobile.png"),
        clip={"x": 0, "y": 0, "width": 375, "height": 812, "scale": 1}
    )

    # Reset Emulation
    send_cmd("Emulation.clearDeviceMetricsOverride")

    # Verify Non-Rmode pages (URmode, Entry Home)
    log("\n--- TEST 4: Verifying URmode and Entry Home Intact ---")
    eval_js("window.TempoMode.setMode('emergency');")
    time.sleep(0.4)
    ur_cards = eval_js("Array.from(document.querySelectorAll('#emode-home-content h3')).map(h => h.textContent.trim())")
    log(f"URmode cards: {ur_cards}")
    assert "Quick Relief" in ur_cards and "Focus Now" in ur_cards

    eval_js("window.TempoMode.setMode('default');")
    time.sleep(0.4)
    eh_cards = eval_js("Array.from(document.querySelectorAll('#dmode-home-content h3')).map(h => h.textContent.trim())")
    log(f"Entry Home cards: {eh_cards}")
    assert "Quick Relief" in eh_cards and "Focus Now" in eh_cards

    log("\n🎉 ALL TESTS PASSED SUCCESSFULLY! (100%)")

finally:
    if ws: ws.close()
    proc.terminate()
    proc.wait()
