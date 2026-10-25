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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_logo_nav_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9252
    
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
        
        log("Authenticating test user...")
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

        def click_logo():
            eval_js("document.getElementById('brand-logo-container').click();")
            time.sleep(0.4)

        def get_dashboard_state():
            return eval_js("""
                (() => {
                    const emode = document.getElementById('emode-home-content');
                    const rmode = document.getElementById('rmode-home-content');
                    const umode = document.getElementById('umode-home-content');
                    const dmode = document.getElementById('dmode-home-content');
                    const todayScreen = document.getElementById('screen-today');
                    const currentTab = window.TempoApp ? window.TempoApp.getCurrentTab() : null;
                    const mode = window.TempoMode ? window.TempoMode.getMode() : null;
                    const activeCtx = window.TempoMode ? window.TempoMode.getActiveContext() : null;
                    const origin = window.TempoMode ? window.TempoMode.getOriginatingMode() : null;

                    return {
                        currentTab,
                        mode,
                        activeCtx,
                        origin,
                        todayVisible: todayScreen && !todayScreen.classList.contains('hidden'),
                        emodeVisible: emode && !emode.classList.contains('hidden'),
                        rmodeVisible: rmode && !rmode.classList.contains('hidden'),
                        umodeVisible: umode && !umode.classList.contains('hidden'),
                        dmodeVisible: dmode && !dmode.classList.contains('hidden'),
                        umodeHomeViewVisible: Boolean(document.getElementById('unclear-home-view'))
                    };
                })()
            """)

        # =========================================================================
        # SECTION 1: RECOVERY MODE -> Various Pages -> Click Tempo Logo
        # =========================================================================
        log("\n=======================================================")
        log("SECTION 1: RECOVERY MODE (Active context = Recovery Mode)")
        log("=======================================================")
        eval_js("window.TempoMode.transitionContext('recovery');")
        time.sleep(0.4)
        s = get_dashboard_state()
        assert s["rmodeVisible"] and s["activeCtx"] == "recovery", f"Setup failed: {s}"
        log(f"Active context established: {s['activeCtx']}")

        # 1A: From Ucheck Stage 1 -> Click Logo -> Return to Rmode Dashboard
        log("\n--- TEST 1A: Rmode -> Ucheck Stage 1 -> Click Logo ---")
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'recovery', startNew: true });")
        time.sleep(0.4)
        eval_js("window.TempoUnclearMode.goToStage(1);")
        time.sleep(0.3)
        click_logo()
        s = get_dashboard_state()
        assert s["rmodeVisible"] and not s["umodeVisible"] and s["activeCtx"] == "recovery", f"Expected Rmode dashboard, got: {s}"
        log(f"PASS: Logo click returned to Recovery Mode dashboard! (rmodeVisible={s['rmodeVisible']})")

        # 1B: From Ucheck Stage 3 -> Click Logo -> Return to Rmode Dashboard
        log("\n--- TEST 1B: Rmode -> Ucheck Stage 3 -> Click Logo ---")
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'recovery', startNew: true });")
        time.sleep(0.4)
        eval_js("window.TempoUnclearMode.goToStage(3);")
        time.sleep(0.3)
        click_logo()
        s = get_dashboard_state()
        assert s["rmodeVisible"] and not s["umodeVisible"] and s["activeCtx"] == "recovery", f"Expected Rmode dashboard, got: {s}"
        log(f"PASS: Logo click returned to Recovery Mode dashboard! (rmodeVisible={s['rmodeVisible']})")

        # 1C: From Ucheck Results (Stage 5) -> Click Logo -> Return to Rmode Dashboard
        log("\n--- TEST 1C: Rmode -> Ucheck Results (Stage 5) -> Click Logo ---")
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'recovery', startNew: true });")
        time.sleep(0.4)
        eval_js("window.TempoUnclearMode.finishCheckIn();")
        time.sleep(0.4)
        click_logo()
        s = get_dashboard_state()
        assert s["rmodeVisible"] and not s["umodeVisible"] and s["activeCtx"] == "recovery", f"Expected Rmode dashboard, got: {s}"
        log(f"PASS: Logo click returned to Recovery Mode dashboard from Results! (rmodeVisible={s['rmodeVisible']})")

        # 1D: From #my-test-results -> Click Logo -> Return to Rmode Dashboard
        log("\n--- TEST 1D: Rmode -> #my-test-results -> Click Logo ---")
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'recovery' });")
        time.sleep(0.3)
        eval_js("window.TempoApp.navigateTo('my-test-results');")
        time.sleep(0.4)
        click_logo()
        s = get_dashboard_state()
        assert s["rmodeVisible"] and s["activeCtx"] == "recovery", f"Expected Rmode dashboard, got: {s}"
        log(f"PASS: Logo click returned to Recovery Mode dashboard from #my-test-results! (rmodeVisible={s['rmodeVisible']})")

        # 1E: From #explore-mental-health-tests -> Click Logo -> Return to Rmode Dashboard
        log("\n--- TEST 1E: Rmode -> #explore-mental-health-tests -> Click Logo ---")
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'recovery' });")
        time.sleep(0.3)
        eval_js("window.TempoApp.navigateTo('explore-mental-health-tests', 'depression');")
        time.sleep(0.4)
        click_logo()
        s = get_dashboard_state()
        assert s["rmodeVisible"] and s["activeCtx"] == "recovery", f"Expected Rmode dashboard, got: {s}"
        log(f"PASS: Logo click returned to Recovery Mode dashboard from #explore-mental-health-tests! (rmodeVisible={s['rmodeVisible']})")

        # 1F: From #about -> Click Logo -> Return to Rmode Dashboard
        log("\n--- TEST 1F: Rmode -> #about -> Click Logo ---")
        eval_js("window.TempoApp.navigateTo('about');")
        time.sleep(0.4)
        click_logo()
        s = get_dashboard_state()
        assert s["rmodeVisible"] and s["activeCtx"] == "recovery", f"Expected Rmode dashboard, got: {s}"
        log(f"PASS: Logo click returned to Recovery Mode dashboard from #about! (rmodeVisible={s['rmodeVisible']})")

        # 1G: From #posts -> Click Logo -> Return to Rmode Dashboard
        log("\n--- TEST 1G: Rmode -> #posts -> Click Logo ---")
        eval_js("window.TempoApp.navigateTo('posts');")
        time.sleep(0.4)
        click_logo()
        s = get_dashboard_state()
        assert s["rmodeVisible"] and s["activeCtx"] == "recovery", f"Expected Rmode dashboard, got: {s}"
        log(f"PASS: Logo click returned to Recovery Mode dashboard from #posts! (rmodeVisible={s['rmodeVisible']})")

        # =========================================================================
        # SECTION 2: URMODE -> Various Pages -> Click Tempo Logo
        # =========================================================================
        log("\n=======================================================")
        log("SECTION 2: URMODE (Active context = Urmode / Emergency)")
        log("=======================================================")
        eval_js("window.TempoMode.transitionContext('emergency');")
        time.sleep(0.4)
        s = get_dashboard_state()
        assert s["emodeVisible"] and s["activeCtx"] == "emergency", f"Setup failed: {s}"
        log(f"Active context established: {s['activeCtx']}")

        # 2A: From Ucheck Stage 2 -> Click Logo -> Return to Urmode Dashboard
        log("\n--- TEST 2A: Urmode -> Ucheck Stage 2 -> Click Logo ---")
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'emergency', startNew: true });")
        time.sleep(0.4)
        eval_js("window.TempoUnclearMode.goToStage(2);")
        time.sleep(0.3)
        click_logo()
        s = get_dashboard_state()
        assert s["emodeVisible"] and not s["umodeVisible"] and s["activeCtx"] == "emergency", f"Expected Urmode dashboard, got: {s}"
        log(f"PASS: Logo click returned to Urmode dashboard! (emodeVisible={s['emodeVisible']})")

        # 2B: From Ucheck Results -> Click Logo -> Return to Urmode Dashboard
        log("\n--- TEST 2B: Urmode -> Ucheck Results -> Click Logo ---")
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'emergency', startNew: true });")
        time.sleep(0.4)
        eval_js("window.TempoUnclearMode.finishCheckIn();")
        time.sleep(0.4)
        click_logo()
        s = get_dashboard_state()
        assert s["emodeVisible"] and not s["umodeVisible"] and s["activeCtx"] == "emergency", f"Expected Urmode dashboard, got: {s}"
        log(f"PASS: Logo click returned to Urmode dashboard from Results! (emodeVisible={s['emodeVisible']})")

        # 2C: From #learn -> Click Logo -> Return to Urmode Dashboard
        log("\n--- TEST 2C: Urmode -> #learn -> Click Logo ---")
        eval_js("window.TempoApp.navigateTo('learn');")
        time.sleep(0.4)
        click_logo()
        s = get_dashboard_state()
        assert s["emodeVisible"] and s["activeCtx"] == "emergency", f"Expected Urmode dashboard, got: {s}"
        log(f"PASS: Logo click returned to Urmode dashboard from #learn! (emodeVisible={s['emodeVisible']})")

        # =========================================================================
        # SECTION 3: ENTRY HOME -> Various Pages -> Click Tempo Logo
        # =========================================================================
        log("\n=======================================================")
        log("SECTION 3: ENTRY HOME (Active context = Entry Home / Default)")
        log("=======================================================")
        eval_js("window.TempoMode.transitionContext(null);")
        time.sleep(0.4)
        s = get_dashboard_state()
        assert s["dmodeVisible"] and s["activeCtx"] is None, f"Setup failed: {s}"
        log(f"Active context established: Entry Home (null)")

        # 3A: From Ucheck Stage 4 -> Click Logo -> Return to Entry Home Dashboard
        log("\n--- TEST 3A: Entry Home -> Ucheck Stage 4 -> Click Logo ---")
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'entry', startNew: true });")
        time.sleep(0.4)
        eval_js("window.TempoUnclearMode.goToStage(4);")
        time.sleep(0.3)
        click_logo()
        s = get_dashboard_state()
        assert s["dmodeVisible"] and not s["umodeVisible"] and s["activeCtx"] is None, f"Expected Entry Home dashboard, got: {s}"
        log(f"PASS: Logo click returned to Entry Home dashboard! (dmodeVisible={s['dmodeVisible']})")

        # 3B: From Ucheck Results -> Click Logo -> Return to Entry Home Dashboard
        log("\n--- TEST 3B: Entry Home -> Ucheck Results -> Click Logo ---")
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'entry', startNew: true });")
        time.sleep(0.4)
        eval_js("window.TempoUnclearMode.finishCheckIn();")
        time.sleep(0.4)
        click_logo()
        s = get_dashboard_state()
        assert s["dmodeVisible"] and not s["umodeVisible"] and s["activeCtx"] is None, f"Expected Entry Home dashboard, got: {s}"
        log(f"PASS: Logo click returned to Entry Home dashboard from Results! (dmodeVisible={s['dmodeVisible']})")

        # 3C: From #about -> Click Logo -> Return to Entry Home Dashboard
        log("\n--- TEST 3C: Entry Home -> #about -> Click Logo ---")
        eval_js("window.TempoApp.navigateTo('about');")
        time.sleep(0.4)
        click_logo()
        s = get_dashboard_state()
        assert s["dmodeVisible"] and s["activeCtx"] is None, f"Expected Entry Home dashboard, got: {s}"
        log(f"PASS: Logo click returned to Entry Home dashboard from #about! (dmodeVisible={s['dmodeVisible']})")

        # =========================================================================
        # SECTION 4: UNCLEAR MODE -> Various Pages -> Click Tempo Logo
        # =========================================================================
        log("\n=======================================================")
        log("SECTION 4: UNCLEAR MODE (Active context = Unclear Mode)")
        log("=======================================================")
        eval_js("window.TempoMode.clearOriginatingMode();")
        eval_js("window.TempoMode.transitionContext('unclear');")
        time.sleep(0.4)
        s = get_dashboard_state()
        assert s["umodeVisible"] and s["activeCtx"] == "unclear", f"Setup failed: {s}"
        log(f"Active context established: {s['activeCtx']}")

        # 4A: From Ucheck Questions Stage 2 -> Click Logo -> Return to Unclear Mode Dashboard
        log("\n--- TEST 4A: Unclear Mode -> Ucheck Stage 2 -> Click Logo ---")
        eval_js("window.TempoUnclearMode.startNewCheckIn();")
        time.sleep(0.3)
        eval_js("window.TempoUnclearMode.goToStage(2);")
        time.sleep(0.3)
        click_logo()
        s = get_dashboard_state()
        assert s["umodeVisible"] and s["umodeHomeViewVisible"] and s["activeCtx"] == "unclear", f"Expected Unclear Mode dashboard, got: {s}"
        log(f"PASS: Logo click returned to Unclear Mode dashboard with compact entry view! (umodeHomeViewVisible={s['umodeHomeViewVisible']})")

        # 4B: From #my-test-results -> Click Logo -> Return to Unclear Mode Dashboard
        log("\n--- TEST 4B: Unclear Mode -> #my-test-results -> Click Logo ---")
        eval_js("window.TempoApp.navigateTo('my-test-results');")
        time.sleep(0.4)
        click_logo()
        s = get_dashboard_state()
        assert s["umodeVisible"] and s["umodeHomeViewVisible"] and s["activeCtx"] == "unclear", f"Expected Unclear Mode dashboard, got: {s}"
        log(f"PASS: Logo click returned to Unclear Mode dashboard from #my-test-results! (umodeHomeViewVisible={s['umodeHomeViewVisible']})")

        # 4C: From #about -> Click Logo -> Return to Unclear Mode Dashboard
        log("\n--- TEST 4C: Unclear Mode -> #about -> Click Logo ---")
        eval_js("window.TempoApp.navigateTo('about');")
        time.sleep(0.4)
        click_logo()
        s = get_dashboard_state()
        assert s["umodeVisible"] and s["activeCtx"] == "unclear", f"Expected Unclear Mode dashboard, got: {s}"
        log(f"PASS: Logo click returned to Unclear Mode dashboard from #about! (umodeVisible={s['umodeVisible']})")

        # =========================================================================
        # SECTION 5: BROWSER REFRESH & PERSISTENCE
        # =========================================================================
        log("\n=======================================================")
        log("SECTION 5: BROWSER REFRESH & PERSISTENCE")
        log("=======================================================")
        # 5A: Rmode -> Ucheck -> Refresh -> Click Logo -> Rmode Dashboard
        log("\n--- TEST 5A: Rmode -> Ucheck -> Refresh -> Click Logo ---")
        eval_js("window.TempoMode.transitionContext('recovery');")
        time.sleep(0.4)
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'recovery', startNew: true });")
        time.sleep(0.4)
        eval_js("window.TempoUnclearMode.goToStage(2);")
        time.sleep(0.3)
        # Simulate browser refresh
        eval_js("window.TempoMode.init();")
        time.sleep(0.4)
        click_logo()
        s = get_dashboard_state()
        assert s["rmodeVisible"] and s["activeCtx"] == "recovery", f"Expected Rmode dashboard after refresh, got: {s}"
        log(f"PASS: Logo click after refresh returned to Recovery Mode dashboard! (rmodeVisible={s['rmodeVisible']})")

        # 5B: Urmode -> Ucheck -> Refresh -> Click Logo -> Urmode Dashboard
        log("\n--- TEST 5B: Urmode -> Ucheck -> Refresh -> Click Logo ---")
        eval_js("window.TempoMode.transitionContext('emergency');")
        time.sleep(0.4)
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'emergency', startNew: true });")
        time.sleep(0.4)
        eval_js("window.TempoUnclearMode.goToStage(3);")
        time.sleep(0.3)
        # Simulate browser refresh
        eval_js("window.TempoMode.init();")
        time.sleep(0.4)
        click_logo()
        s = get_dashboard_state()
        assert s["emodeVisible"] and s["activeCtx"] == "emergency", f"Expected Urmode dashboard after refresh, got: {s}"
        log(f"PASS: Logo click after refresh returned to Urmode dashboard! (emodeVisible={s['emodeVisible']})")

        # 5C: Direct navigation to Ucheck with no prior context -> Click Logo -> Entry Home
        log("\n--- TEST 5C: Direct navigation to Ucheck -> Click Logo -> Entry Home ---")
        eval_js("window.TempoMode.clearOriginatingMode();")
        eval_js("window.TempoMode.transitionContext(null);")
        time.sleep(0.4)
        eval_js("window.TempoMode.openUcheck();")
        time.sleep(0.4)
        click_logo()
        s = get_dashboard_state()
        assert s["dmodeVisible"] and s["activeCtx"] is None, f"Expected Entry Home dashboard, got: {s}"
        log(f"PASS: Logo click with no prior context safely fell back to Entry Home! (dmodeVisible={s['dmodeVisible']})")

        log("\n=======================================================")
        log("🎉 ALL TEMPO LOGO NAVIGATION TESTS PASSED SUCCESSFULLY! (100%)")
        log("=======================================================")

    finally:
        if ws:
            ws.close()
        proc.kill()

if __name__ == "__main__":
    run_tests()
