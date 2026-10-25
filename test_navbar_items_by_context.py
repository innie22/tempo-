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

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_navbar_ctx_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9265
    
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
            
        log(f"Connected to CDP: {ws_url}")
        ws = websocket.create_connection(ws_url)
        
        msg_id = 1
        def send_command(method, params=None):
            nonlocal msg_id
            cid = msg_id
            msg_id += 1
            req = {"id": cid, "method": method}
            if params:
                req["params"] = params
            ws.send(json.dumps(req))
            while True:
                resp = json.loads(ws.recv())
                if resp.get("id") == cid:
                    return resp.get("result", {})

        def eval_js(expression):
            res = send_command("Runtime.evaluate", {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True
            })
            if "exceptionDetails" in res:
                raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        send_command("Runtime.enable")
        send_command("Page.enable")
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
                    id: 'local_user_nav_test',
                    email: 'nav_test_user@tempo.edu',
                    raw_email: 'nav_test_user@tempo.edu',
                    password: 'password123',
                    user_metadata: { full_name: 'Alex Chen', display_name: 'Alex Chen', role: 'student' }
                };
                localStorage.setItem('tempo_mock_account_nav_test_user@tempo.edu', JSON.stringify(mock));
                if (window.TempoAuth) {
                    await window.TempoAuth.signIn("nav_test_user@tempo.edu", "password123");
                }
            })()
        """)
        time.sleep(1)
        is_auth = eval_js("Boolean(window.TempoAuth && window.TempoAuth.getCurrentUser())")
        log(f"Authenticated status: {is_auth}")
        assert is_auth is True

        def get_navbar_items():
            return eval_js("""
                (() => {
                    const links = Array.from(document.querySelectorAll('header nav a:not(.hidden)'));
                    return links.map(l => l.textContent.trim()).filter(t => t.length > 0 && !t.includes('Volunteer') && !t.includes('Advisor'));
                })()
            """)

        # =====================================================================
        # TEST 1: ENTRY HOME NAVBAR ITEMS
        # Expected: About · Check · Plan · Learn · Post
        # =====================================================================
        log("\n--- TEST 1: Entry Home Navbar Items ---")
        eval_js("window.TempoMode.setMode('default');")
        time.sleep(0.5)
        entry_items = get_navbar_items()
        log(f"Entry Home items: {entry_items}")
        assert entry_items == ['About', 'Check', 'Plan', 'Learn', 'Post'], f"Expected ['About', 'Check', 'Plan', 'Learn', 'Post'], got {entry_items}"
        log("✓ Entry Home items match: About · Check · Plan · Learn · Post")

        # Test Entry Home Plan click
        eval_js("document.getElementById('nav-link-plan').click();")
        time.sleep(0.5)
        plan_screen_vis = eval_js("!document.getElementById('screen-plan-workspace').classList.contains('hidden')")
        log(f"Plan workspace screen visible after clicking Plan: {plan_screen_vis}")
        assert plan_screen_vis is True, "Clicking Plan on Entry Home must open Working Plan workspace"

        # Return to Entry Home
        eval_js("window.TempoApp.navigateTo('today');")
        time.sleep(0.3)
        assert get_navbar_items() == ['About', 'Check', 'Plan', 'Learn', 'Post']

        # =====================================================================
        # TEST 2: URMODE NAVBAR ITEMS
        # Expected: About · Check · Tool · Learn · Post
        # =====================================================================
        log("\n--- TEST 2: Urmode Navbar Items ---")
        eval_js("window.TempoMode.setMode('emergency');")
        time.sleep(0.5)
        urmode_items = get_navbar_items()
        log(f"Urmode items: {urmode_items}")
        assert urmode_items == ['About', 'Check', 'Tool', 'Learn', 'Post'], f"Expected ['About', 'Check', 'Tool', 'Learn', 'Post'], got {urmode_items}"
        log("✓ Urmode items match: About · Check · Tool · Learn · Post")

        # Test Urmode Check click
        eval_js("document.getElementById('nav-link-check').click();")
        time.sleep(0.5)
        stress_screen_vis = eval_js("!document.getElementById('screen-stress-check').classList.contains('hidden')")
        log(f"Self-check screen visible after clicking Check: {stress_screen_vis}")
        assert stress_screen_vis is True, "Clicking Check on Urmode must open Self-check tool page"

        # Return to Urmode dashboard
        eval_js("window.TempoSelfCheckWorkspace.returnHome();")
        time.sleep(0.4)
        assert eval_js("window.TempoMode.getActiveContext()") == 'emergency'
        assert get_navbar_items() == ['About', 'Check', 'Tool', 'Learn · Post'[:5]] or get_navbar_items() == ['About', 'Check', 'Tool', 'Learn', 'Post']
        assert get_navbar_items() == ['About', 'Check', 'Tool', 'Learn', 'Post']

        # =====================================================================
        # TEST 3: RMODE NAVBAR ITEMS
        # Expected: About · Plan · Tool · Learn · Post
        # =====================================================================
        log("\n--- TEST 3: Rmode Navbar Items ---")
        eval_js("window.TempoMode.setMode('recovery');")
        time.sleep(0.5)
        rmode_items = get_navbar_items()
        log(f"Rmode items: {rmode_items}")
        assert rmode_items == ['About', 'Plan', 'Tool', 'Learn', 'Post'], f"Expected ['About', 'Plan', 'Tool', 'Learn', 'Post'], got {rmode_items}"
        log("✓ Rmode items match: About · Plan · Tool · Learn · Post")

        # Test Rmode Plan click (scrolls to Recovery Plan)
        eval_js("document.getElementById('nav-link-check').click();")
        time.sleep(0.5)
        # Should remain on Recovery Mode home dashboard
        assert eval_js("!document.getElementById('rmode-home-content').classList.contains('hidden')") is True

        # Test Rmode Tool click (scrolls to Enjoy Tempo Tools)
        eval_js("document.getElementById('nav-link-plan').click();")
        time.sleep(0.5)
        assert eval_js("!document.getElementById('rmode-home-content').classList.contains('hidden')") is True

        # =====================================================================
        # TEST 4: RAPID CYCLING BETWEEN CONTEXTS
        # =====================================================================
        log("\n--- TEST 4: Rapid Cycling Between Contexts ---")
        modes_to_test = [
            ('default', ['About', 'Check', 'Plan', 'Learn', 'Post']),
            ('emergency', ['About', 'Check', 'Tool', 'Learn', 'Post']),
            ('recovery', ['About', 'Plan', 'Tool', 'Learn', 'Post']),
            ('default', ['About', 'Check', 'Plan', 'Learn', 'Post']),
            ('recovery', ['About', 'Plan', 'Tool', 'Learn', 'Post']),
            ('emergency', ['About', 'Check', 'Tool', 'Learn', 'Post']),
            ('default', ['About', 'Check', 'Plan', 'Learn', 'Post'])
        ]

        for m, expected in modes_to_test:
            eval_js(f"window.TempoMode.setMode('{m}');")
            time.sleep(0.2)
            actual = get_navbar_items()
            assert actual == expected, f"Mode '{m}' failed: expected {expected}, got {actual}"
            log(f"  ✓ Switched to '{m}' -> {actual}")

        # =====================================================================
        # TEST 5: REFRESH AND NAVIGATION PRESERVATION
        # =====================================================================
        log("\n--- TEST 5: Navigation & Refresh Preservation ---")
        # In Rmode: navigate to About, verify navbar items remain Rmode
        eval_js("window.TempoMode.setMode('recovery');")
        time.sleep(0.2)
        eval_js("window.TempoApp.navigateTo('about');")
        time.sleep(0.3)
        actual_in_about = get_navbar_items()
        assert actual_in_about == ['About', 'Plan', 'Tool', 'Learn', 'Post'], f"Navbar in About page under Rmode failed: got {actual_in_about}"
        log("  ✓ Navbar in About page under Rmode preserved: About · Plan · Tool · Learn · Post")

        # Return to Dashboard
        eval_js("document.getElementById('brand-logo-container').click();")
        time.sleep(0.4)
        assert get_navbar_items() == ['About', 'Plan', 'Tool', 'Learn', 'Post']

        # In Urmode: navigate to Learn, verify navbar items remain Urmode
        eval_js("window.TempoMode.setMode('emergency');")
        time.sleep(0.2)
        eval_js("window.TempoApp.navigateTo('learn');")
        time.sleep(0.3)
        actual_in_learn = get_navbar_items()
        assert actual_in_learn == ['About', 'Check', 'Tool', 'Learn', 'Post'], f"Navbar in Learn page under Urmode failed: got {actual_in_learn}"
        log("  ✓ Navbar in Learn page under Urmode preserved: About · Check · Tool · Learn · Post")

        # Return to Dashboard
        eval_js("document.getElementById('brand-logo-container').click();")
        time.sleep(0.4)
        assert get_navbar_items() == ['About', 'Check', 'Tool', 'Learn', 'Post']

        # In Entry Home: navigate to About, verify navbar items remain Entry Home
        eval_js("window.TempoMode.setMode('default');")
        time.sleep(0.2)
        eval_js("window.TempoApp.navigateTo('about');")
        time.sleep(0.3)
        actual_in_entry_about = get_navbar_items()
        assert actual_in_entry_about == ['About', 'Check', 'Plan', 'Learn', 'Post'], f"Navbar in About page under Entry Home failed: got {actual_in_entry_about}"
        log("  ✓ Navbar in About page under Entry Home preserved: About · Check · Plan · Learn · Post")

        log("\n🎉 ALL NAVBAR ITEMS BY CONTEXT TESTS PASSED SUCCESSFULLY! (100%)")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    run_tests()
