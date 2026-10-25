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

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_selector_reactivity_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9277
    
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
                    if "error" in resp:
                        raise RuntimeError(f"CDP error: {resp['error']}")
                    return resp.get("result", {})

        def eval_js(expr, await_promise=True):
            res = send_command("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": await_promise
            })
            if "exceptionDetails" in res:
                raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        # Wait for page ready
        for _ in range(30):
            ready = eval_js("Boolean(window.TempoMode && window.TempoAuth && window.TempoApp)")
            if ready:
                break
            time.sleep(0.5)

        # Clear and reload clean
        eval_js("""
            (() => {
                localStorage.clear();
                sessionStorage.clear();
            })()
        """)

        # Sign in as authenticated user
        eval_js("""
            (async () => {
                try {
                    await window.TempoAuth.register('Alex Chen', 'alex.chen@university.edu', 'demo1234');
                } catch (e) {}
                await window.TempoAuth.signIn('alex.chen@university.edu', 'demo1234');
            })()
        """)
        time.sleep(0.8)
        log("Authenticated test user: alex.chen@university.edu")

        # =========================================================================
        # TEST 1: ENTER URMODE -> OPEN SELECTOR -> SELECT RMODE WITHOUT RELOAD
        # =========================================================================
        log("\n--- TEST 1: Urmode -> Mode Selector -> Rmode ---")
        eval_js("window.TempoMode.transitionContext('emergency');")
        time.sleep(0.5)

        mode1 = eval_js("window.TempoMode.getMode()")
        assert mode1 == "emergency", f"Expected emergency, got {mode1}"
        btn_text1 = eval_js("document.getElementById('btn-home-mode-selector').innerText")
        assert "⚡" in btn_text1 or "Urgent" in btn_text1 or "Khẩn" in btn_text1, f"Expected Urgent button, got {btn_text1}"
        log("1A: In Urmode, Mode Selector trigger displays Urgent Mode.")

        # Open Mode Selector in Urmode
        eval_js("document.getElementById('btn-home-mode-selector').click();")
        time.sleep(0.2)

        dropdown_state1 = eval_js("""
            (() => {
                const dd = document.getElementById('home-mode-selector-dropdown');
                return {
                    exists: !!dd,
                    isVisible: dd && !dd.classList.contains('hidden'),
                    hasRecovery: !!dd.querySelector('button[onclick*="recovery"]'),
                    hasUnclear: !!dd.querySelector('button[onclick*="unclear"]'),
                    hasUrgent: !!dd.querySelector('button[onclick*="emergency"]')
                };
            })()
        """)
        assert dropdown_state1["exists"] and dropdown_state1["isVisible"], "Dropdown should be visible in Urmode"
        assert dropdown_state1["hasRecovery"], "Dropdown in Urmode should offer Recovery Mode"
        assert dropdown_state1["hasUnclear"], "Dropdown in Urmode should offer Unclear Mode"
        assert not dropdown_state1["hasUrgent"], "Dropdown in Urmode must NOT offer Urgent Mode"
        log("1B: Mode Selector dropdown opened cleanly in Urmode with Recovery and Unclear options.")

        # Click Recovery Mode inside dropdown
        eval_js("document.querySelector('#home-mode-selector-dropdown button[onclick*=\"recovery\"]').click();")
        time.sleep(0.5)

        mode2 = eval_js("window.TempoMode.getMode()")
        assert mode2 == "recovery", f"Expected recovery after selecting Rmode, got {mode2}"
        log("1C: Mode successfully switched to Rmode without page reload.")

        # =========================================================================
        # TEST 2: IN RMODE -> MODE SELECTOR IMMEDIATELY INTERACTIVE WITHOUT RELOAD
        # =========================================================================
        log("\n--- TEST 2: Rmode Mode Selector interactivity without reload ---")
        btn_text2 = eval_js("document.getElementById('btn-home-mode-selector').innerText")
        assert "🌱" in btn_text2 or "Recovery" in btn_text2 or "Hồi phục" in btn_text2, f"Expected Recovery button, got {btn_text2}"
        log("2A: In Rmode, Mode Selector trigger displays Recovery Mode.")

        # Open Mode Selector in Rmode
        eval_js("document.getElementById('btn-home-mode-selector').click();")
        time.sleep(0.2)

        dropdown_state2 = eval_js("""
            (() => {
                const dd = document.getElementById('home-mode-selector-dropdown');
                return {
                    exists: !!dd,
                    isVisible: dd && !dd.classList.contains('hidden'),
                    parentContainer: dd ? dd.closest('#rmode-home-content') !== null : false,
                    hasUrgent: !!dd.querySelector('button[onclick*="emergency"]'),
                    hasUnclear: !!dd.querySelector('button[onclick*="unclear"]'),
                    hasRecovery: !!dd.querySelector('button[onclick*="recovery"]')
                };
            })()
        """)
        assert dropdown_state2["exists"], "Dropdown should exist in Rmode"
        assert dropdown_state2["isVisible"], "Dropdown in Rmode MUST be visible when opened without page reload!"
        assert dropdown_state2["parentContainer"], "Dropdown must be scoped inside rmode-home-content"
        assert dropdown_state2["hasUrgent"], "Dropdown in Rmode should offer Urgent Mode"
        assert dropdown_state2["hasUnclear"], "Dropdown in Rmode should offer Unclear Mode"
        assert not dropdown_state2["hasRecovery"], "Dropdown in Rmode must NOT offer Recovery Mode"
        log("2B: Mode Selector dropdown opened immediately in Rmode and is fully interactive!")

        # Click Urgent Mode inside dropdown
        eval_js("document.querySelector('#home-mode-selector-dropdown button[onclick*=\"emergency\"]').click();")
        time.sleep(0.5)

        mode3 = eval_js("window.TempoMode.getMode()")
        assert mode3 == "emergency", f"Expected emergency after selecting Urmode, got {mode3}"
        log("2C: Mode successfully switched back to Urmode without page reload.")

        # =========================================================================
        # TEST 3: BACK IN URMODE -> MODE SELECTOR WORKS -> SELECT UNCLEAR MODE (UCHECK)
        # =========================================================================
        log("\n--- TEST 3: Urmode -> Mode Selector -> Unclear Mode (Ucheck) ---")
        btn_text3 = eval_js("document.getElementById('btn-home-mode-selector').innerText")
        assert "⚡" in btn_text3 or "Urgent" in btn_text3 or "Khẩn" in btn_text3, f"Expected Urgent button, got {btn_text3}"

        eval_js("document.getElementById('btn-home-mode-selector').click();")
        time.sleep(0.2)

        dropdown_state3 = eval_js("""
            (() => {
                const dd = document.getElementById('home-mode-selector-dropdown');
                return {
                    exists: !!dd,
                    isVisible: dd && !dd.classList.contains('hidden'),
                    parentContainer: dd ? dd.closest('#emode-home-content') !== null : false,
                    hasRecovery: !!dd.querySelector('button[onclick*="recovery"]'),
                    hasUnclear: !!dd.querySelector('button[onclick*="unclear"]')
                };
            })()
        """)
        assert dropdown_state3["isVisible"], "Dropdown in Urmode MUST be visible after roundtrip transition"
        assert dropdown_state3["parentContainer"], "Dropdown must be scoped inside emode-home-content"
        log("3A: Mode Selector in Urmode remains fully interactive after roundtrip transition.")

        # Select Unclear Mode from dropdown
        eval_js("document.querySelector('#home-mode-selector-dropdown button[onclick*=\"unclear\"]').click();")
        time.sleep(0.5)

        ucheck_state = eval_js("""
            (() => {
                return {
                    mode: window.TempoMode.getMode(),
                    activeContext: window.TempoMode.getActiveContext(),
                    umodeVisible: !document.getElementById('umode-home-content').classList.contains('hidden')
                };
            })()
        """)
        assert ucheck_state["mode"] == "unclear", f"Expected mode=unclear, got {ucheck_state['mode']}"
        assert ucheck_state["umodeVisible"], "Unclear Mode content should be visible"
        log("3B: Unclear Mode opened cleanly from Mode Selector without page reload.")

        # =========================================================================
        # TEST 4: IN UNCLEAR MODE -> MODE SELECTOR WORKS -> SWITCH TO RMODE
        # =========================================================================
        log("\n--- TEST 4: Unclear Mode -> Mode Selector -> Rmode ---")
        eval_js("document.getElementById('btn-home-mode-selector').click();")
        time.sleep(0.2)

        dropdown_state4 = eval_js("""
            (() => {
                const dd = document.getElementById('home-mode-selector-dropdown');
                return {
                    exists: !!dd,
                    isVisible: dd && !dd.classList.contains('hidden'),
                    parentContainer: dd ? dd.closest('#umode-home-content') !== null : false,
                    hasUrgent: !!dd.querySelector('button[onclick*="emergency"]'),
                    hasRecovery: !!dd.querySelector('button[onclick*="recovery"]'),
                    hasUnclear: !!dd.querySelector('button[onclick*="unclear"]')
                };
            })()
        """)
        assert dropdown_state4["isVisible"], "Dropdown in Unclear Mode MUST be visible"
        assert dropdown_state4["parentContainer"], "Dropdown must be scoped inside umode-home-content"
        assert dropdown_state4["hasUrgent"], "Dropdown in Unclear Mode should offer Urgent Mode"
        assert dropdown_state4["hasRecovery"], "Dropdown in Unclear Mode should offer Recovery Mode"
        assert not dropdown_state4["hasUnclear"], "Dropdown in Unclear Mode must NOT offer Unclear Mode"
        log("4A: Mode Selector in Unclear Mode opened cleanly with Urgent and Recovery options.")

        # Switch to Recovery Mode from Unclear Mode dropdown
        eval_js("document.querySelector('#home-mode-selector-dropdown button[onclick*=\"recovery\"]').click();")
        time.sleep(0.5)

        mode4 = eval_js("window.TempoMode.getMode()")
        assert mode4 == "recovery", f"Expected recovery, got {mode4}"
        assert eval_js("window.TempoMode.getActiveSharedTool()") is None, "activeSharedTool should be cleared after selecting mode"
        log("4B: Switched from Unclear Mode to Recovery Mode via Mode Selector without page reload.")

        # =========================================================================
        # TEST 5: NAVBAR MODE INDICATOR & DROPDOWN SYNCHRONIZATION
        # =========================================================================
        log("\n--- TEST 5: Navbar mode indicator and dropdown reactive sync ---")
        nav_state1 = eval_js("""
            (() => {
                const shell = document.getElementById('mode-indicator-shell');
                const label = document.getElementById('mode-badge-label');
                const icon = document.getElementById('mode-badge-icon');
                return {
                    shellVisible: !shell.classList.contains('hidden'),
                    labelText: label ? label.textContent.trim() : '',
                    iconText: icon ? icon.textContent.trim() : ''
                };
            })()
        """)
        assert nav_state1["shellVisible"], "Navbar mode indicator shell should be visible in Recovery Mode"
        assert nav_state1["iconText"] == "🌱", f"Navbar icon should be 🌱, got {nav_state1['iconText']}"
        log("5A: Navbar mode badge correctly reflects Recovery Mode.")

        # Open navbar mode dropdown
        eval_js("document.getElementById('btn-mode-indicator-trigger').click();")
        time.sleep(0.2)

        nav_dropdown_state = eval_js("""
            (() => {
                const dd = document.getElementById('navbar-mode-dropdown');
                return {
                    isVisible: dd && !dd.classList.contains('hidden'),
                    hasUrgent: !!dd.querySelector('button[onclick*="emergency"]'),
                    hasUnclear: !!dd.querySelector('button[onclick*="unclear"]'),
                    hasRecovery: !!dd.querySelector('button[onclick*="recovery"]')
                };
            })()
        """)
        assert nav_dropdown_state["isVisible"], "Navbar dropdown should be visible when toggled"
        assert nav_dropdown_state["hasUrgent"], "Navbar dropdown should offer Urgent Mode"
        assert not nav_dropdown_state["hasRecovery"], "Navbar dropdown should NOT offer active Recovery Mode"
        log("5B: Navbar mode dropdown opened cleanly and excludes active mode.")

        # Switch to Urgent Mode via navbar dropdown
        eval_js("document.querySelector('#navbar-mode-dropdown button[onclick*=\"emergency\"]').click();")
        time.sleep(0.5)

        nav_state2 = eval_js("""
            (() => {
                const shell = document.getElementById('mode-indicator-shell');
                const label = document.getElementById('mode-badge-label');
                const icon = document.getElementById('mode-badge-icon');
                return {
                    shellVisible: !shell.classList.contains('hidden'),
                    iconText: icon ? icon.textContent.trim() : '',
                    mode: window.TempoMode.getMode()
                };
            })()
        """)
        assert nav_state2["mode"] == "emergency", f"Expected mode=emergency, got {nav_state2['mode']}"
        assert nav_state2["iconText"] == "⚡", f"Navbar icon should update to ⚡, got {nav_state2['iconText']}"
        log("5C: Mode transitioned via navbar dropdown; navbar badge reactively updated immediately!")

        # Close dropdowns
        eval_js("window.TempoMode.closeAllModeDropdowns();")
        time.sleep(0.2)

        log("\n=======================================================")
        log("🎉 ALL MODE SELECTOR REACTIVE SYNCHRONIZATION TESTS PASSED! (100%)")
        log("=======================================================")

    finally:
        try:
            if ws:
                ws.close()
        except Exception:
            pass
        if proc:
            proc.kill()

if __name__ == '__main__':
    run_tests()
