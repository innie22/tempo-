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

user_data_dir = tempfile.mkdtemp(prefix="tempo_assessment_test_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9268

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
                id: 'local_user_assessment_test',
                email: 'nav_assessment_user@tempo.edu',
                raw_email: 'nav_assessment_user@tempo.edu',
                password: 'password123',
                user_metadata: { full_name: 'Alex Innie', display_name: 'Alex Innie', role: 'student' }
            };
            localStorage.setItem('tempo_mock_account_nav_assessment_user@tempo.edu', JSON.stringify(mock));
            if (window.TempoAuth) {
                await window.TempoAuth.signIn("nav_assessment_user@tempo.edu", "password123");
            }
        })()
    """)
    time.sleep(1)

    is_auth = eval_js("Boolean(window.TempoAuth && window.TempoAuth.getCurrentUser())")
    log(f"Authenticated: {is_auth}")
    assert is_auth is True

    def get_navbar_items():
        return eval_js("""
            (() => {
                const links = Array.from(document.querySelectorAll('header nav a:not(.hidden)'));
                return links.map(l => l.textContent.trim()).filter(t => t.length > 0 && !t.includes('Volunteer') && !t.includes('Advisor') && !t.includes('tình nguyện') && !t.includes('Cố vấn'));
            })()
        """)

    # -------------------------------------------------------------
    # 1. URMODE VERIFICATION
    # -------------------------------------------------------------
    log("\n--- TEST 1: URmode (Emergency Mode) Navbar ---")
    eval_js("window.TempoMode.setMode('emergency');")
    time.sleep(0.5)

    ur_items = get_navbar_items()
    log(f"URmode items: {ur_items}")
    assert ur_items == ['About', 'Check', 'Assessment', 'Community'], f"Expected ['About', 'Check', 'Assessment', 'Community'], got {ur_items}"

    plan_link_info = eval_js("""
        (() => {
            const a = document.getElementById('nav-link-plan');
            return {
                text: a.textContent.trim(),
                href: a.getAttribute('href'),
                title: a.getAttribute('title')
            };
        })()
    """)
    log(f"nav-link-plan info in URmode: {plan_link_info}")
    assert plan_link_info['text'] == 'Assessment'
    assert plan_link_info['href'] == '#ucheck'
    assert plan_link_info['title'] == 'Assessment'

    # Check other nav items unchanged
    other_items = eval_js("""
        (() => ({
            about: document.getElementById('nav-link-what-is-tempo')?.textContent.trim(),
            check: document.getElementById('nav-link-check')?.textContent.trim(),
            community: document.getElementById('nav-link-community')?.textContent.trim()
        }))()
    """)
    log(f"Other items in URmode: {other_items}")
    assert other_items['about'] == 'About'
    assert other_items['check'] == 'Check'
    assert other_items['community'] == 'Community'

    artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
    capture_screenshot(
        os.path.join(artifact_dir, "urmode_navbar_assessment.png"),
        clip={"x": 0, "y": 0, "width": 1440, "height": 180, "scale": 1}
    )

    # -------------------------------------------------------------
    # 2. CLICK ASSESSMENT -> NAVIGATES TO UCHECK
    # -------------------------------------------------------------
    log("\n--- TEST 2: Clicking Assessment navigates to UCheck ---")
    eval_js("document.getElementById('nav-link-plan').click();")
    time.sleep(0.8)

    active_shared = eval_js("window.TempoMode.getActiveSharedTool ? window.TempoMode.getActiveSharedTool() : null")
    log(f"Active shared tool after clicking Assessment: {active_shared}")
    assert active_shared == 'ucheck', f"Expected active shared tool 'ucheck', got '{active_shared}'"

    ucheck_visible = eval_js("!document.getElementById('umode-home-content').classList.contains('hidden')")
    log(f"UCheck dashboard (#umode-home-content) visible: {ucheck_visible}")
    assert ucheck_visible is True, "UCheck dashboard (#umode-home-content) should be visible"

    capture_screenshot(
        os.path.join(artifact_dir, "ucheck_page_opened_from_assessment_nav.png"),
        clip={"x": 0, "y": 0, "width": 1440, "height": 700, "scale": 1}
    )

    # Return to URmode
    log("Exiting UCheck back to URmode...")
    eval_js("if (window.TempoMode && window.TempoMode.returnToSourceContext) window.TempoMode.returnToSourceContext();")
    time.sleep(0.5)

    current_mode = eval_js("window.TempoMode.getActiveContext()")
    log(f"Context after return: {current_mode}")
    assert current_mode == 'emergency', f"Expected 'emergency', got '{current_mode}'"

    ur_items_again = get_navbar_items()
    log(f"URmode items after return: {ur_items_again}")
    assert ur_items_again == ['About', 'Check', 'Assessment', 'Community']

    # -------------------------------------------------------------
    # 3. RMODE VERIFICATION (UNTOUCHED)
    # -------------------------------------------------------------
    log("\n--- TEST 3: Rmode Navbar Unchanged ---")
    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(0.5)

    rmode_items = get_navbar_items()
    log(f"Rmode items: {rmode_items}")
    assert rmode_items == ['About', 'Plan', 'Tool', 'Community'], f"Expected ['About', 'Plan', 'Tool', 'Community'], got {rmode_items}"

    rmode_plan_info = eval_js("""
        (() => {
            const a = document.getElementById('nav-link-plan');
            return {
                text: a.textContent.trim(),
                href: a.getAttribute('href'),
                title: a.getAttribute('title')
            };
        })()
    """)
    log(f"nav-link-plan info in Rmode: {rmode_plan_info}")
    assert rmode_plan_info['text'] == 'Tool'
    assert rmode_plan_info['href'] == '#enjoy-tempo-tools'
    assert rmode_plan_info['title'] == 'Tool'

    capture_screenshot(
        os.path.join(artifact_dir, "rmode_navbar_verified_tool.png"),
        clip={"x": 0, "y": 0, "width": 1440, "height": 180, "scale": 1}
    )

    # -------------------------------------------------------------
    # 4. ENTRY HOME VERIFICATION (UNTOUCHED)
    # -------------------------------------------------------------
    log("\n--- TEST 4: Entry Home Navbar Unchanged ---")
    eval_js("window.TempoMode.setMode('default');")
    time.sleep(0.5)

    entry_items = get_navbar_items()
    log(f"Entry Home items: {entry_items}")
    assert entry_items == ['About', 'Check', 'Plan', 'Community'], f"Expected ['About', 'Check', 'Plan', 'Community'], got {entry_items}"

    entry_plan_info = eval_js("""
        (() => {
            const a = document.getElementById('nav-link-plan');
            return {
                text: a.textContent.trim(),
                href: a.getAttribute('href'),
                title: a.getAttribute('title')
            };
        })()
    """)
    log(f"nav-link-plan info in Entry Home: {entry_plan_info}")
    assert entry_plan_info['text'] == 'Plan'
    assert entry_plan_info['href'] == '#plan-workspace'
    assert entry_plan_info['title'] == 'Plan'

    capture_screenshot(
        os.path.join(artifact_dir, "entryhome_navbar_verified_plan.png"),
        clip={"x": 0, "y": 0, "width": 1440, "height": 180, "scale": 1}
    )

    # -------------------------------------------------------------
    # 5. CYCLING TESTS
    # -------------------------------------------------------------
    log("\n--- TEST 5: Switching back and forth ---")
    for m in ['emergency', 'recovery', 'default', 'emergency']:
        eval_js(f"window.TempoMode.setMode('{m}');")
        time.sleep(0.2)
        items = get_navbar_items()
        if m == 'emergency':
            assert items == ['About', 'Check', 'Assessment', 'Community'], f"Failed in {m}: {items}"
        elif m == 'recovery':
            assert items == ['About', 'Plan', 'Tool', 'Community'], f"Failed in {m}: {items}"
        elif m == 'default':
            assert items == ['About', 'Check', 'Plan', 'Community'], f"Failed in {m}: {items}"
        log(f"  ✓ Mode '{m}' verified: {items}")

    log("\n🎉 ALL TESTS PASSED SUCCESSFULLY! (100%)")

finally:
    if ws: ws.close()
    proc.terminate()
    proc.wait()
