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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_ucheck_nav_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9248
    
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
                    return resp.get("result", {})
                    
        def eval_js(expr):
            res = send_command("Runtime.evaluate", {"expression": expr, "returnByValue": True})
            if "exceptionDetails" in res:
                log(f"JS Exception for [{expr[:60]}...]: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        send_command("Page.enable")
        send_command("Runtime.enable")
        time.sleep(2)
        
        log("Logging in as test user...")
        eval_js("""
            (async () => {
                const mock = {
                    id: 'local_user_test',
                    email: 'alex.chen@university.edu',
                    raw_email: 'alex.chen@university.edu',
                    password: 'password123',
                    user_metadata: { full_name: 'Alex Chen', display_name: 'Alex Chen', role: 'student' }
                };
                localStorage.setItem('tempo_mock_account_alex.chen@university.edu', JSON.stringify(mock));
                if (window.TempoAuth) {
                    await window.TempoAuth.signIn("alex.chen@university.edu", "password123");
                }
            })()
        """)
        time.sleep(1)
        is_auth = eval_js("Boolean(window.TempoAuth && window.TempoAuth.getCurrentUser())")
        log(f"Authenticated status: {is_auth}")

        # -------------------------------------------------------------
        # TEST 1: Recovery Mode -> Ucheck -> Exit -> Recovery Mode
        # -------------------------------------------------------------
        log("\n--- TEST 1: Recovery Mode -> Ucheck -> Exit -> Recovery Mode ---")
        eval_js("window.TempoMode.transitionContext('recovery');")
        time.sleep(0.5)
        cur_mode = eval_js("window.TempoMode.getMode()")
        assert cur_mode == "recovery", f"Expected recovery mode, got {cur_mode}"
        log(f"Active mode confirmed: {cur_mode}")
        
        # Open Ucheck from Recovery Mode
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'recovery' });")
        time.sleep(0.5)
        ucheck_mode = eval_js("window.TempoMode.getMode()")
        orig_mode = eval_js("window.TempoMode.getOriginatingMode()")
        assert ucheck_mode == "unclear", f"Expected unclear mode while in Ucheck, got {ucheck_mode}"
        assert orig_mode == "recovery", f"Expected originating mode recovery, got {orig_mode}"
        log(f"In Ucheck: mode={ucheck_mode}, originatingMode={orig_mode}")
        
        # Exit Ucheck via Return Home
        eval_js("window.TempoUnclearMode.returnToHome();")
        time.sleep(0.5)
        after_exit_mode = eval_js("window.TempoMode.getMode()")
        active_ctx = eval_js("window.TempoMode.getActiveContext()")
        assert after_exit_mode == "recovery", f"Expected return to recovery, got {after_exit_mode}"
        assert active_ctx == "recovery", f"Expected activeContext recovery, got {active_ctx}"
        log(f"PASS: Recovery Mode -> Ucheck -> Exit returned to Recovery Mode! (mode={after_exit_mode})")

        # -------------------------------------------------------------
        # TEST 2: Urgent Mode (Urmode) -> Ucheck -> Exit -> Urgent Mode
        # -------------------------------------------------------------
        log("\n--- TEST 2: Urgent Mode -> Ucheck -> Exit -> Urgent Mode ---")
        eval_js("window.TempoMode.transitionContext('emergency');")
        time.sleep(0.5)
        cur_mode = eval_js("window.TempoMode.getMode()")
        assert cur_mode == "emergency", f"Expected emergency mode, got {cur_mode}"
        log(f"Active mode confirmed: {cur_mode}")
        
        # Open Ucheck from Urgent Mode
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'emergency' });")
        time.sleep(0.5)
        ucheck_mode = eval_js("window.TempoMode.getMode()")
        orig_mode = eval_js("window.TempoMode.getOriginatingMode()")
        assert ucheck_mode == "unclear", f"Expected unclear mode while in Ucheck, got {ucheck_mode}"
        assert orig_mode == "emergency", f"Expected originating mode emergency, got {orig_mode}"
        log(f"In Ucheck: mode={ucheck_mode}, originatingMode={orig_mode}")
        
        # Exit Ucheck via Return Home
        eval_js("window.TempoUnclearMode.returnToHome();")
        time.sleep(0.5)
        after_exit_mode = eval_js("window.TempoMode.getMode()")
        active_ctx = eval_js("window.TempoMode.getActiveContext()")
        assert after_exit_mode == "emergency", f"Expected return to emergency, got {after_exit_mode}"
        assert active_ctx == "emergency", f"Expected activeContext emergency, got {active_ctx}"
        log(f"PASS: Urgent Mode -> Ucheck -> Exit returned to Urgent Mode! (mode={after_exit_mode})")

        # -------------------------------------------------------------
        # TEST 3: Entry Home -> Ucheck -> Exit -> Entry Home
        # -------------------------------------------------------------
        log("\n--- TEST 3: Entry Home -> Ucheck -> Exit -> Entry Home ---")
        eval_js("window.TempoMode.transitionContext(null);")
        time.sleep(0.5)
        cur_mode = eval_js("window.TempoMode.getMode()")
        assert cur_mode == "default", f"Expected default mode (entry home), got {cur_mode}"
        log(f"Active mode confirmed: {cur_mode}")
        
        # Open Ucheck from Entry Home
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'entry' });")
        time.sleep(0.5)
        ucheck_mode = eval_js("window.TempoMode.getMode()")
        orig_mode = eval_js("window.TempoMode.getOriginatingMode()")
        assert ucheck_mode == "unclear", f"Expected unclear mode while in Ucheck, got {ucheck_mode}"
        assert orig_mode == "entry", f"Expected originating mode entry, got {orig_mode}"
        log(f"In Ucheck: mode={ucheck_mode}, originatingMode={orig_mode}")
        
        # Exit Ucheck via Return Home
        eval_js("window.TempoUnclearMode.returnToHome();")
        time.sleep(0.5)
        after_exit_mode = eval_js("window.TempoMode.getMode()")
        active_ctx = eval_js("window.TempoMode.getActiveContext()")
        assert after_exit_mode == "default", f"Expected return to default entry home, got {after_exit_mode}"
        assert active_ctx is None, f"Expected activeContext None, got {active_ctx}"
        log(f"PASS: Entry Home -> Ucheck -> Exit returned to Entry Home! (mode={after_exit_mode})")

        # -------------------------------------------------------------
        # TEST 4: Recovery Mode -> Ucheck Assessment Stages 1-4 & Stage 5 Results -> Exit -> Recovery Mode
        # -------------------------------------------------------------
        log("\n--- TEST 4: Rmode -> Ucheck Flow (Stages 1-5) -> Exit -> Recovery Mode ---")
        eval_js("window.TempoMode.transitionContext('recovery');")
        time.sleep(0.5)
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'recovery', startNew: true });")
        time.sleep(0.5)
        
        # Advance through stages 1 -> 2 -> 3 -> 4
        for stage in range(1, 5):
            eval_js(f"window.TempoUnclearMode.goToStage({stage});")
            time.sleep(0.3)
            orig_preserved = eval_js("window.TempoMode.getOriginatingMode()")
            assert orig_preserved == "recovery", f"Stage {stage}: expected originating mode recovery, got {orig_preserved}"
            log(f"Stage {stage} confirmed with preserved origin: {orig_preserved}")
            
        # Complete check-in to reach Stage 5 (Results / Summary)
        eval_js("""
            (function() {
                window.TempoUnclearMode.goToStage(4);
                window.TempoUnclearMode.finishCheckIn();
            })()
        """)
        time.sleep(0.5)
        orig_at_stage5 = eval_js("window.TempoMode.getOriginatingMode()")
        assert orig_at_stage5 == "recovery", f"Stage 5: expected originating mode recovery, got {orig_at_stage5}"
        log(f"Stage 5 (Results view) confirmed with preserved origin: {orig_at_stage5}")
        
        # Exit from Stage 5 results
        eval_js("window.TempoUnclearMode.returnToHome();")
        time.sleep(0.5)
        after_results_mode = eval_js("window.TempoMode.getMode()")
        assert after_results_mode == "recovery", f"Expected recovery mode after results exit, got {after_results_mode}"
        log(f"PASS: Exiting from Stage 5 results returned to Recovery Mode! (mode={after_results_mode})")

        # -------------------------------------------------------------
        # TEST 5: Intermediate screens (#my-test-results, #explore-mental-health-tests)
        # -------------------------------------------------------------
        log("\n--- TEST 5: Rmode -> Ucheck -> Intermediate Screens -> Return -> Recovery Mode ---")
        eval_js("window.TempoMode.transitionContext('recovery');")
        time.sleep(0.5)
        eval_js("window.TempoMode.setMode('unclear', { sourceContext: 'recovery' });")
        time.sleep(0.5)
        
        # Navigate to #my-test-results
        eval_js("window.TempoApp.navigateTo('my-test-results');")
        time.sleep(0.5)
        orig_in_results_page = eval_js("window.TempoMode.getOriginatingMode()")
        assert orig_in_results_page == "recovery", f"Expected originating mode recovery on results page, got {orig_in_results_page}"
        log(f"On #my-test-results: originatingMode={orig_in_results_page}")
        
        # Click back button to return to Unclear Mode
        eval_js("window.TempoMode.setMode('unclear'); window.TempoApp.navigateTo('today');")
        time.sleep(0.5)
        orig_back_unclear = eval_js("window.TempoMode.getOriginatingMode()")
        assert orig_back_unclear == "recovery", f"Expected originating mode recovery after back, got {orig_back_unclear}"
        
        # Navigate to #explore-mental-health-tests
        eval_js("window.TempoApp.navigateTo('explore-mental-health-tests', 'depression');")
        time.sleep(0.5)
        orig_in_explore = eval_js("window.TempoMode.getOriginatingMode()")
        assert orig_in_explore == "recovery", f"Expected originating mode recovery on explore page, got {orig_in_explore}"
        log(f"On #explore-mental-health-tests: originatingMode={orig_in_explore}")
        
        # Click back button to return to Unclear Mode
        eval_js("window.TempoMode.setMode('unclear'); window.TempoApp.navigateTo('today');")
        time.sleep(0.5)
        
        # Exit Unclear Mode
        eval_js("window.TempoUnclearMode.returnToHome();")
        time.sleep(0.5)
        after_intermediate_exit = eval_js("window.TempoMode.getMode()")
        assert after_intermediate_exit == "recovery", f"Expected return to recovery mode, got {after_intermediate_exit}"
        log(f"PASS: Navigating intermediate screens and exiting returned to Recovery Mode! (mode={after_intermediate_exit})")

        # -------------------------------------------------------------
        # TEST 6: Mode Selector dropdown: Rmode -> Unclear Mode -> Exit -> Recovery Mode
        # -------------------------------------------------------------
        log("\n--- TEST 6: Mode Selector dropdown: Rmode -> Unclear Mode -> Exit -> Recovery Mode ---")
        eval_js("window.TempoMode.transitionContext('recovery');")
        time.sleep(0.5)
        
        # Select Unclear Mode from dropdown
        eval_js("window.TempoMode.selectModeFromDropdown('unclear');")
        time.sleep(0.5)
        cur_mode = eval_js("window.TempoMode.getMode()")
        orig_mode = eval_js("window.TempoMode.getOriginatingMode()")
        assert cur_mode == "unclear", f"Expected unclear mode, got {cur_mode}"
        assert orig_mode == "recovery", f"Expected originating mode recovery from dropdown, got {orig_mode}"
        log(f"Selected Unclear from dropdown: mode={cur_mode}, originatingMode={orig_mode}")
        
        eval_js("window.TempoUnclearMode.returnToHome();")
        time.sleep(0.5)
        after_dropdown_exit = eval_js("window.TempoMode.getMode()")
        assert after_dropdown_exit == "recovery", f"Expected recovery mode, got {after_dropdown_exit}"
        log(f"PASS: Selected Unclear from dropdown and returned to Recovery Mode! (mode={after_dropdown_exit})")

        # -------------------------------------------------------------
        # TEST 7: Browser Refresh preservation
        # -------------------------------------------------------------
        log("\n--- TEST 7: Browser Refresh preservation ---")
        eval_js("window.TempoMode.transitionContext('recovery');")
        time.sleep(0.5)
        eval_js("window.TempoMode.setMode('unclear', { sourceContext: 'recovery' });")
        time.sleep(0.5)
        
        # Simulate browser refresh by calling init()
        eval_js("window.TempoMode.init();")
        time.sleep(0.5)
        orig_after_refresh = eval_js("window.TempoMode.getOriginatingMode()")
        assert orig_after_refresh == "recovery", f"Expected recovery originating mode after refresh, got {orig_after_refresh}"
        log(f"After refresh/init: originatingMode={orig_after_refresh}")
        
        eval_js("window.TempoUnclearMode.returnToHome();")
        time.sleep(0.5)
        after_refresh_exit = eval_js("window.TempoMode.getMode()")
        assert after_refresh_exit == "recovery", f"Expected return to recovery after refresh, got {after_refresh_exit}"
        log(f"PASS: Preserved across browser refresh and returned to Recovery Mode! (mode={after_refresh_exit})")

        # -------------------------------------------------------------
        # TEST 8: Direct entry without originating mode falls back to default
        # -------------------------------------------------------------
        log("\n--- TEST 8: Direct open without originating mode falls back to Entry Home ---")
        eval_js("window.TempoMode.clearOriginatingMode();")
        eval_js("window.TempoMode.transitionContext(null);")
        time.sleep(0.5)
        eval_js("window.TempoMode.openUcheck();")
        time.sleep(0.5)
        eval_js("window.TempoUnclearMode.returnToHome();")
        time.sleep(0.5)
        direct_exit_mode = eval_js("window.TempoMode.getMode()")
        assert direct_exit_mode == "default", f"Expected default mode on direct open exit, got {direct_exit_mode}"
        log(f"PASS: Direct open without originating mode returned to Entry Home! (mode={direct_exit_mode})")

        log("\n=======================================================")
        log("ALL 8 UCHECK EXIT NAVIGATION TESTS PASSED SUCCESSFULLY!")
        log("=======================================================")

    finally:
        if ws:
            ws.close()
        proc.kill()

if __name__ == "__main__":
    run_tests()
