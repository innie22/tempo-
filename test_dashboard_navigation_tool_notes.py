import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

user_data_dir = tempfile.mkdtemp(prefix="tempo_nav_test_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9297

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "http://localhost:8000/"
]

log(f"Launching Edge on port {port}...")
proc = subprocess.Popen(cmd)
ws = None

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

    if not ws_url:
        raise RuntimeError("Failed to connect to Edge CDP endpoint")

    ws = websocket.create_connection(ws_url)
    msg_id = 1

    def send_command(method, params=None):
        global msg_id
        cid = msg_id
        msg_id += 1
        req = {"id": cid, "method": method}
        if params:
            req["params"] = params
        ws.send(json.dumps(req))
        while True:
            raw = ws.recv()
            msg = json.loads(raw)
            if msg.get("id") == cid:
                if "error" in msg:
                    raise RuntimeError(f"CDP error: {msg['error']}")
                return msg.get("result", {})

    send_command("Emulation.setDeviceMetricsOverride", {"width": 1280, "height": 900, "deviceScaleFactor": 1, "mobile": False})

    def eval_js(expr, await_promise=True):
        res = send_command("Runtime.evaluate", {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": await_promise
        })
        if "exceptionDetails" in res:
            raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
        return res.get("result", {}).get("value")

    def wait_for_ready():
        for _ in range(40):
            try:
                ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined'")
                if ready:
                    eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        raise TimeoutError("Application failed to become ready")

    log("Waiting for application ready state...")
    wait_for_ready()

    # Authenticate mock user
    eval_js("""
        (async () => {
            try {
                if (window.TempoAuth && typeof window.TempoAuth.register === 'function') {
                    await window.TempoAuth.register('Navigation Tester', 'test.nav@tempo.app', 'secret123456');
                }
            } catch (e) {}
            try {
                if (window.TempoAuth && typeof window.TempoAuth.signIn === 'function') {
                    await window.TempoAuth.signIn('test.nav@tempo.app', 'secret123456');
                }
            } catch (e) {}
            if (window.TempoAuth && typeof window.TempoAuth.closeAllAuthModals === 'function') {
                window.TempoAuth.closeAllAuthModals();
            }
        })()
    """, await_promise=True)

    # Setup Working Plan with urgent context
    eval_js("""
        (async () => {
            const todayStr = new Date().toISOString().split('T')[0];
            const testPlan = {
                id: 'plan-nav-test',
                dateCreated: new Date().toISOString(),
                status: 'confirmed',
                executionDate: todayStr,
                plannedTasks: [
                    {
                        dayDate: todayStr,
                        scheduledDay: todayStr,
                        timeBlock: '09:00',
                        task: {
                            id: 'task-nav-1',
                            name: 'Statistics Assignment (Problem Set 4)',
                            durationMinutes: 60,
                            durationLabel: '1h',
                            completed: false
                        }
                    }
                ]
            };
            if (window.TempoPlanStore && window.TempoPlanStore.savePlan) {
                await window.TempoPlanStore.savePlan(testPlan);
            }
            if (window.TempoMode && window.TempoMode.transitionContext) {
                await window.TempoMode.transitionContext('emergency', { silent: true });
            }
            if (window.TempoApp && window.TempoApp.navigateTo) {
                window.TempoApp.navigateTo('today');
            }
        })()
    """, await_promise=True)

    time.sleep(1)

    log("\n--- TEST 1: Navbar Tool Destination ---")
    nav_tool_text = eval_js("document.getElementById('nav-link-plan')?.textContent.trim()")
    log(f"Navbar link text: '{nav_tool_text}'")
    assert nav_tool_text == "Tool", f"Expected 'Tool', got '{nav_tool_text}'"

    # Click Tool in navbar
    eval_js("document.getElementById('nav-link-plan').click()")
    time.sleep(0.5)

    today_hidden = eval_js("document.getElementById('screen-today')?.classList.contains('hidden')")
    plan_hidden = eval_js("document.getElementById('screen-plan-workspace')?.classList.contains('hidden')")
    notes_hidden = eval_js("document.getElementById('screen-tool-notes')?.classList.contains('hidden')")
    log(f"Screen today hidden: {today_hidden}, plan hidden: {plan_hidden}, notes hidden: {notes_hidden}")
    assert today_hidden is False, "User should remain on screen-today"
    assert plan_hidden is True, "screen-plan-workspace should remain hidden"
    assert notes_hidden is True, "screen-tool-notes should remain hidden"

    # Verify #enjoy-tempo-tools exists and is in DOM
    enjoy_tools_exists = eval_js("!!document.getElementById('enjoy-tempo-tools')")
    log(f"enjoy-tempo-tools element exists: {enjoy_tools_exists}")
    assert enjoy_tools_exists is True, "enjoy-tempo-tools element should exist"

    log("\n--- TEST 2: Destination B - NOTE Card & Create your notes ---")
    create_your_notes_btn = eval_js("!!document.querySelector('a[title=\"Create your notes\"]')")
    log(f"Create your notes button exists: {create_your_notes_btn}")
    assert create_your_notes_btn is True, "Create your notes link should exist in urgent mode dashboard"

    # Check note content text
    note_content_text = eval_js("document.querySelector('[data-tempo-ui=\"dashboard-note-card\"] p')?.textContent.trim()")
    log(f"Note card content text: '{note_content_text}'")
    assert "Drink more than 3 cups of water" in note_content_text, f"Expected 'Drink more than 3 cups of water', got '{note_content_text}'"

    # Verify hover and pointer feedback classes
    card_classes = eval_js("document.querySelector('[data-tempo-ui=\"dashboard-note-card\"]').className")
    log(f"Note card classes: '{card_classes}'")
    assert "cursor-pointer" in card_classes, "Note card must have cursor-pointer"
    assert "hover:border-[#D79277]" in card_classes or "hover:border" in card_classes, "Note card must have hover border feedback"
    assert "hover:shadow" in card_classes, "Note card must have hover shadow feedback"
    assert "transition" in card_classes, "Note card must have transition"

    # 2A. Test clicking on the note content text <p> directly
    log("\n--- TEST 2A: Clicking on the note content text 'Drink more than 3 cups of water' ---")
    eval_js("document.querySelector('[data-tempo-ui=\"dashboard-note-card\"] p').click()")
    time.sleep(0.5)

    notes_visible_from_text = eval_js("!document.getElementById('screen-tool-notes')?.classList.contains('hidden')")
    log(f"screen-tool-notes visible from clicking note content text: {notes_visible_from_text}")
    assert notes_visible_from_text is True, "screen-tool-notes should be visible after clicking note content text"

    # Click Back button
    eval_js("document.getElementById('btn-tool-notes-back').click()")
    time.sleep(0.5)

    # 2B. Test clicking on the note card container
    log("\n--- TEST 2B: Clicking on the note card box ---")
    eval_js("document.querySelector('[data-tempo-ui=\"dashboard-note-card\"]').click()")
    time.sleep(0.5)

    notes_visible_from_card = eval_js("!document.getElementById('screen-tool-notes')?.classList.contains('hidden')")
    log(f"screen-tool-notes visible from clicking note card: {notes_visible_from_card}")
    assert notes_visible_from_card is True, "screen-tool-notes should be visible after clicking note card"

    # Click Back button
    eval_js("document.getElementById('btn-tool-notes-back').click()")
    time.sleep(0.5)

    # 2C. Test clicking Create your notes button and verify NO duplicate navigation
    log("\n--- TEST 2C: Clicking 'Create your notes →' and verifying no duplicate navigation ---")
    eval_js("""
        (() => {
            window.__navCalls = [];
            const origNav = window.TempoApp.navigateTo;
            window.TempoApp.navigateTo = function(...args) {
                window.__navCalls.push(args);
                return origNav.apply(this, args);
            };
        })()
    """)

    eval_js("document.querySelector('a[title=\"Create your notes\"]').click()")
    time.sleep(0.5)

    nav_call_count = eval_js("window.__navCalls.length")
    log(f"Navigate calls count when clicking button: {nav_call_count}")
    assert nav_call_count == 1, f"Expected exactly 1 navigation call (no duplicate navigation), got {nav_call_count}"

    notes_visible = eval_js("!document.getElementById('screen-tool-notes')?.classList.contains('hidden')")
    today_hidden_now = eval_js("document.getElementById('screen-today')?.classList.contains('hidden')")
    log(f"screen-tool-notes visible: {notes_visible}, screen-today hidden: {today_hidden_now}")
    assert notes_visible is True, "screen-tool-notes should be visible after clicking Create your notes"
    assert today_hidden_now is True, "screen-today should be hidden"

    # Verify page title, description, and no recovery note modal
    title_text = eval_js("document.querySelector('#screen-tool-notes h1')?.textContent.trim()")
    sub_text = eval_js("document.querySelector('#screen-tool-notes p')?.textContent.trim()")
    log(f"Tool Notes title: '{title_text}', subtext: '{sub_text}'")
    assert title_text == "Tool Notes", f"Expected 'Tool Notes', got '{title_text}'"
    assert "Your notes space is coming soon" in sub_text, f"Unexpected subtext: {sub_text}"

    # Check recovery note modal is not open
    rn_modal_open = eval_js("""
        (() => {
            const m = document.getElementById('modal-recovery-note') || document.getElementById('rn-view-modal') || document.getElementById('rn-edit-modal');
            return m && !m.classList.contains('hidden');
        })()
    """)
    log(f"Recovery Note modal open: {rn_modal_open}")
    assert not rn_modal_open, "Recovery Note modal must NOT be open"

    # Click Back button
    eval_js("document.getElementById('btn-tool-notes-back').click()")
    time.sleep(0.5)

    today_back = eval_js("!document.getElementById('screen-today')?.classList.contains('hidden')")
    notes_back_hidden = eval_js("document.getElementById('screen-tool-notes')?.classList.contains('hidden')")
    log(f"Back to screen-today visible: {today_back}, screen-tool-notes hidden: {notes_back_hidden}")
    assert today_back is True, "Clicking Back should return to screen-today"
    assert notes_back_hidden is True, "screen-tool-notes should be hidden after Back"

    log("\n--- TEST 3: Destination C - Create notes inside Enjoy Tempo Tools ---")
    create_notes_card = eval_js("!!document.querySelector('#enjoy-tempo-tools div[title=\"Create Notes\"]')")
    log(f"Create Notes card inside Enjoy Tempo Tools exists: {create_notes_card}")
    assert create_notes_card is True, "Create Notes card should exist in Enjoy Tempo Tools"

    eval_js("document.querySelector('#enjoy-tempo-tools div[title=\"Create Notes\"]').click()")
    time.sleep(0.5)

    notes_visible_c = eval_js("!document.getElementById('screen-tool-notes')?.classList.contains('hidden')")
    log(f"screen-tool-notes visible from Enjoy Tempo Tools: {notes_visible_c}")
    assert notes_visible_c is True, "screen-tool-notes should open from Enjoy Tempo Tools Create Notes card"

    # Check recovery note modal is not open
    rn_modal_open_c = eval_js("""
        (() => {
            const m = document.getElementById('modal-recovery-note') || document.getElementById('rn-view-modal') || document.getElementById('rn-edit-modal');
            return m && !m.classList.contains('hidden');
        })()
    """)
    assert not rn_modal_open_c, "Recovery Note modal must NOT be open from Create Notes tool card"

    # Return to today
    eval_js("window.TempoApp.navigateTo('today')")
    time.sleep(0.5)

    log("\n--- TEST 4: Destination D - How are you feeling today (Self-check) ---")
    self_check_banner = eval_js("!!document.querySelector('#enjoy-tempo-tools div[title=\"Self-check\"]')")
    log(f"Self-check banner exists: {self_check_banner}")
    assert self_check_banner is True, "Self-check banner should exist in Enjoy Tempo Tools"

    eval_js("document.querySelector('#enjoy-tempo-tools div[title=\"Self-check\"]').click()")
    time.sleep(0.5)

    stress_check_visible = eval_js("!document.getElementById('screen-stress-check')?.classList.contains('hidden')")
    today_hidden_d = eval_js("document.getElementById('screen-today')?.classList.contains('hidden')")
    log(f"screen-stress-check visible: {stress_check_visible}, screen-today hidden: {today_hidden_d}")
    assert stress_check_visible is True, "screen-stress-check should be visible after clicking Self-check"
    assert today_hidden_d is True, "screen-today should be hidden when Self-check is open"

    # Return to urgent mode dashboard
    eval_js("if (window.TempoMode && window.TempoMode.returnToSourceContext) window.TempoMode.returnToSourceContext(); else window.TempoApp.navigateTo('today');")
    time.sleep(0.5)

    today_back_d = eval_js("!document.getElementById('screen-today')?.classList.contains('hidden')")
    log(f"Returned to screen-today: {today_back_d}")
    assert today_back_d is True, "Should return to screen-today from Self-check"

    log("\n--- TEST 5: Navbar Tool from another page (e.g. About) ---")
    eval_js("window.TempoApp.navigateTo('about')")
    time.sleep(0.5)
    about_visible = eval_js("!document.getElementById('screen-about')?.classList.contains('hidden')")
    log(f"screen-about visible: {about_visible}")
    assert about_visible is True, "Should be on screen-about"

    # Click Tool in navbar
    eval_js("document.getElementById('nav-link-plan').click()")
    time.sleep(0.5)

    today_from_about = eval_js("!document.getElementById('screen-today')?.classList.contains('hidden')")
    about_hidden_now = eval_js("document.getElementById('screen-about')?.classList.contains('hidden')")
    log(f"screen-today visible: {today_from_about}, screen-about hidden: {about_hidden_now}")
    assert today_from_about is True, "Clicking Tool from another page should transition to screen-today"
    assert about_hidden_now is True, "screen-about should be hidden"

    log("\n--- Capturing verification screenshots ---")
    import base64
    # 0. Capture Dashboard showing the NOTE Card in the right column
    eval_js("window.TempoApp.navigateTo('today'); window.scrollTo({ top: 0, behavior: 'instant' });")
    time.sleep(0.5)
    shot0 = send_command("Page.captureScreenshot", {"format": "png"})
    with open(r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\dashboard_note_card_verified.png", "wb") as f:
        f.write(base64.b64decode(shot0["data"]))
    log("Saved dashboard_note_card_verified.png")

    # 1. Capture Dashboard with Enjoy Tempo Tools
    eval_js("document.getElementById('enjoy-tempo-tools')?.scrollIntoView({ behavior: 'instant', block: 'start' });")
    time.sleep(0.5)
    shot1 = send_command("Page.captureScreenshot", {"format": "png"})
    with open(r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\dashboard_enjoy_tempo_tools.png", "wb") as f:
        f.write(base64.b64decode(shot1["data"]))
    log("Saved dashboard_enjoy_tempo_tools.png")

    # 2. Capture Tool Notes Placeholder Page
    eval_js("window.TempoApp.navigateTo('tool-notes');")
    time.sleep(0.5)
    shot2 = send_command("Page.captureScreenshot", {"format": "png"})
    with open(r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\tool_notes_placeholder.png", "wb") as f:
        f.write(base64.b64decode(shot2["data"]))
    log("Saved tool_notes_placeholder.png")

    log("\nALL NAVIGATION DESTINATION AND TOOL NOTES TESTS PASSED!")

finally:
    if ws:
        try:
            ws.close()
        except Exception:
            pass
    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
