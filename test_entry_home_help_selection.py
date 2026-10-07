import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_entry_help_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9275
    
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
                    pages = [t for t in tabs if t.get("type") == "page" and "localhost:8000" in t.get("url", "")]
                    if pages:
                        ws_url = pages[0]["webSocketDebuggerUrl"]
                        break
            except Exception:
                time.sleep(0.5)
                
        if not ws_url:
            raise RuntimeError("Failed to connect to Edge CDP endpoint")
            
        log(f"Connected to CDP page: {ws_url}")
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

        def eval_js(expr):
            res = send_command("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True
            })
            if "exceptionDetails" in res:
                raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        def wait_for_ready():
            for _ in range(30):
                try:
                    ready = eval_js("Boolean(window.TempoMode && window.TempoApp && window.TempoAuth)")
                    if ready:
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise RuntimeError("Timed out waiting for page/scripts to be ready")

        wait_for_ready()

        # Clean slate at Entry Home
        eval_js("""(() => {
            localStorage.clear();
            sessionStorage.clear();
            if (window.TempoMode) {
                window.TempoMode.init();
                window.TempoMode.restoreDefaultHome();
            }
        })()""")
        time.sleep(0.5)

        log("\n=======================================================")
        log("TESTING ENTRY HOME HELP SELECTION & REMOVAL OF TAKE A BREAK")
        log("=======================================================")

        # -------------------------------------------------------------
        # STEP 1: Entry Home initial state
        # -------------------------------------------------------------
        log("\n--- STEP 1: Verify Entry Home initial state ---")
        state1 = eval_js("""(() => {
            return {
                activeContext: window.TempoMode.getActiveContext(),
                mode: window.TempoMode.getMode(),
                hasCtaBtn: !!document.getElementById('btn-hero-figure-start'),
                modalHidden: document.getElementById('modal-routing-selection').classList.contains('hidden')
            };
        })()""")
        assert state1["activeContext"] is None, f"Initial activeContext must be null, got: {state1['activeContext']}"
        assert state1["hasCtaBtn"], "CTA button 'btn-hero-figure-start' must exist on Entry Home"
        assert state1["modalHidden"], "Routing/Help modal must initially be hidden"
        log("✓ Entry Home initialized with activeContext = null and modal hidden.")

        # -------------------------------------------------------------
        # STEP 2: Clicking CTA opens Help Selection popup, NOT direct Urmode
        # -------------------------------------------------------------
        log("\n--- STEP 2: Clicking 'Help me figure out where to start →' opens popup ---")
        eval_js("document.getElementById('btn-hero-figure-start').click();")
        time.sleep(0.3)

        state2 = eval_js("""(() => {
            const modal = document.getElementById('modal-routing-selection');
            return {
                modalOpen: !modal.classList.contains('hidden'),
                activeContext: window.TempoMode.getActiveContext(),
                mode: window.TempoMode.getMode(),
                urgentCard: !!modal.querySelector('.state-choice-card--urgent'),
                recoveryCard: !!modal.querySelector('.state-choice-card--recovery'),
                unclearCard: !!modal.querySelector('.state-choice-card--unclear'),
                supportCard: !!modal.querySelector('.state-choice-card--support')
            };
        })()""")
        assert state2["modalOpen"], "Clicking CTA MUST open modal-routing-selection popup!"
        assert state2["activeContext"] is None, "Opening modal MUST NOT automatically change activeContext!"
        assert state2["urgentCard"], "Modal must have Urgent card"
        assert state2["recoveryCard"], "Modal must have Recovery card"
        assert state2["unclearCard"], "Modal must have Unclear card"
        assert state2["supportCard"], "Modal must have Immediate Support card"
        log("✓ Clicking CTA opens Help Selection popup with all 4 destinations; activeContext remains null.")

        # -------------------------------------------------------------
        # STEP 3: Close popup returns to / remains on Entry Home
        # -------------------------------------------------------------
        log("\n--- STEP 3: Close popup returns to Entry Home ---")
        eval_js("document.getElementById('btn-close-routing-modal').click();")
        time.sleep(0.3)

        state3 = eval_js("""(() => {
            const modal = document.getElementById('modal-routing-selection');
            return {
                modalHidden: modal.classList.contains('hidden'),
                activeContext: window.TempoMode.getActiveContext()
            };
        })()""")
        assert state3["modalHidden"], "Modal must be hidden after clicking close"
        assert state3["activeContext"] is None, "activeContext must remain null after closing modal"
        log("✓ Closing popup remains on Entry Home with activeContext = null.")

        # -------------------------------------------------------------
        # STEP 4: Guest user clicks Urgent -> gates auth with pending intent
        # -------------------------------------------------------------
        log("\n--- STEP 4a: Guest user chooses Urmode -> gates auth ---")
        eval_js("document.getElementById('btn-hero-figure-start').click();")
        time.sleep(0.3)
        eval_js("document.querySelector('#modal-routing-selection .state-choice-card--urgent').click();")
        time.sleep(0.5)

        state4a = eval_js("""(() => {
            const signInModal = document.getElementById('modal-signin');
            const pending = window.TempoMode.getPendingIntent();
            return {
                modalHidden: document.getElementById('modal-routing-selection').classList.contains('hidden'),
                signInOpen: signInModal && !signInModal.classList.contains('hidden'),
                pendingDest: pending ? pending.destination : null,
                activeContext: window.TempoMode.getActiveContext()
            };
        })()""")
        assert state4a["modalHidden"], "Routing modal must be closed"
        assert state4a["signInOpen"], "Sign-in modal must open for guest requesting mode"
        assert state4a["pendingDest"] == "emergency", f"Pending intent must be emergency, got {state4a['pendingDest']}"
        assert state4a["activeContext"] is None, "Guest activeContext remains null until authenticated"
        log("✓ Guest user choosing Urmode properly gates auth and preserves pendingIntent = 'emergency'.")

        # Close signin modal and authenticate user
        eval_js("""(async () => {
            const m = document.getElementById('modal-signin');
            if (m) m.classList.add('hidden');
            await window.TempoAuth.signIn('authed_user@tempo.edu', 'secret123');
        })()""")
        time.sleep(0.5)

        # -------------------------------------------------------------
        # STEP 4b: Authenticated user chooses Urmode -> activeContext = 'emergency'
        # -------------------------------------------------------------
        log("\n--- STEP 4b: Authenticated user chooses Urmode -> activeContext = emergency ---")
        eval_js("document.getElementById('btn-hero-figure-start').click();")
        time.sleep(0.3)
        eval_js("document.querySelector('#modal-routing-selection .state-choice-card--urgent').click();")
        time.sleep(0.5)

        state4b = eval_js("""(() => {
            return {
                activeContext: window.TempoMode.getActiveContext(),
                mode: window.TempoMode.getMode(),
                modalHidden: document.getElementById('modal-routing-selection').classList.contains('hidden')
            };
        })()""")
        assert state4b["activeContext"] == "emergency", f"activeContext must be 'emergency', got {state4b['activeContext']}"
        assert state4b["modalHidden"], "Routing modal must be closed after selection"
        log("✓ Selecting Urmode establishes activeContext = 'emergency'.")

        # Return to Entry Home
        eval_js("window.TempoMode.transitionContext(null);")
        time.sleep(0.3)

        # -------------------------------------------------------------
        # STEP 5: Authenticated user chooses Rmode -> activeContext = 'recovery'
        # -------------------------------------------------------------
        log("\n--- STEP 5: Authenticated user chooses Rmode -> activeContext = recovery ---")
        eval_js("document.getElementById('btn-hero-figure-start').click();")
        time.sleep(0.3)
        eval_js("document.querySelector('#modal-routing-selection .state-choice-card--recovery').click();")
        time.sleep(0.5)

        state5 = eval_js("""(() => {
            return {
                activeContext: window.TempoMode.getActiveContext(),
                mode: window.TempoMode.getMode(),
                modalHidden: document.getElementById('modal-routing-selection').classList.contains('hidden')
            };
        })()""")
        assert state5["activeContext"] == "recovery", f"activeContext must be 'recovery', got {state5['activeContext']}"
        assert state5["modalHidden"], "Routing modal must be closed after selection"
        log("✓ Selecting Rmode establishes activeContext = 'recovery'.")

        # Return to Entry Home
        eval_js("window.TempoMode.transitionContext(null);")
        time.sleep(0.3)

        # -------------------------------------------------------------
        # STEP 6: Choose Ucheck -> open Ucheck with sourceContext = 'entry', activeContext = null
        # -------------------------------------------------------------
        log("\n--- STEP 6: Choose Ucheck from popup ---")
        eval_js("document.getElementById('btn-hero-figure-start').click();")
        time.sleep(0.3)
        eval_js("document.querySelector('#modal-routing-selection .state-choice-card--unclear').click();")
        time.sleep(0.5)

        state6 = eval_js("""(() => {
            return {
                activeContext: window.TempoMode.getActiveContext(),
                sourceContext: window.TempoMode.getSourceContext(),
                modalHidden: document.getElementById('modal-routing-selection').classList.contains('hidden')
            };
        })()""")
        assert state6["activeContext"] is None, f"activeContext must remain null for Ucheck, got {state6['activeContext']}"
        assert state6["sourceContext"] == "entry", f"sourceContext must be 'entry', got {state6['sourceContext']}"
        assert state6["modalHidden"], "Modal must be closed after selection"
        log("✓ Selecting Ucheck opens assessment with sourceContext = 'entry', activeContext = null.")

        # Exit Ucheck back to Entry
        eval_js("window.TempoMode.returnToSourceContext();")
        time.sleep(0.3)

        # -------------------------------------------------------------
        # STEP 7: Choose SOS -> opens SOS flow without changing activeContext
        # -------------------------------------------------------------
        log("\n--- STEP 7: Choose Immediate Support (SOS) from popup ---")
        eval_js("document.getElementById('btn-hero-figure-start').click();")
        time.sleep(0.3)
        eval_js("document.querySelector('#modal-routing-selection .state-choice-card--support').click();")
        time.sleep(0.5)

        state7 = eval_js("""(() => {
            const sosModal = document.getElementById('progressive-emergency-modal') || document.getElementById('modal-emergency-flow');
            return {
                activeContext: window.TempoMode.getActiveContext(),
                sosOpen: sosModal && !sosModal.classList.contains('hidden'),
                routingModalHidden: document.getElementById('modal-routing-selection').classList.contains('hidden')
            };
        })()""")
        assert state7["activeContext"] is None, f"activeContext must remain null for SOS, got {state7['activeContext']}"
        assert state7["sosOpen"], "SOS modal must be open"
        assert state7["routingModalHidden"], "Routing modal must be closed"
        log("✓ Selecting Immediate Support opens SOS flow; activeContext remains null.")

        # Close SOS (force=true to avoid blocking window.confirm in test)
        eval_js("if (window.TempoEmergencySupport) window.TempoEmergencySupport.closeModal(true);")
        time.sleep(0.3)

        # -------------------------------------------------------------
        # STEP 8: ISSUE 2 Verification — No 'Take a Break' in Entry Home or Selection Popups
        # -------------------------------------------------------------
        log("\n--- STEP 8: Verify 'Take a Break' is removed from Entry Home and Selection Popups ---")
        state8 = eval_js("""(() => {
            const dmode = document.getElementById('dmode-home-content');
            const routingModal = document.getElementById('modal-routing-selection');
            const changeModal = document.getElementById('modal-change-mode');

            const dmodeText = dmode ? dmode.innerText : '';
            const routingText = routingModal ? routingModal.innerText : '';
            const changeText = changeModal ? changeModal.innerText : '';

            // Check if there is any button/card with "Take a Break" in these surfaces
            const takeBreakDmode = /take\\s+a\\s+break/i.test(dmodeText);
            const takeBreakRouting = /take\\s+a\\s+break/i.test(routingText);
            const takeBreakChange = /take\\s+a\\s+break/i.test(changeText);

            const optDefault = document.getElementById('change-mode-opt-default');

            return {
                takeBreakDmode,
                takeBreakRouting,
                takeBreakChange,
                hasOptDefault: !!optDefault
            };
        })()""")

        assert not state8["takeBreakDmode"], "Entry Home must NOT contain 'Take a Break'"
        assert not state8["takeBreakRouting"], "Help Selection popup must NOT contain 'Take a Break'"
        assert not state8["takeBreakChange"], "Change Mode popup must NOT contain 'Take a Break'"
        assert not state8["hasOptDefault"], "change-mode-opt-default must be removed from modal-change-mode"
        log("✓ 'Take a Break' is completely removed from Entry Home, Help Selection popup, and Change Mode popup.")

        log("\n=======================================================")
        log(">>> ALL ENTRY HOME HELP SELECTION & TAKE A BREAK TESTS PASSED! <<<")
        log("=======================================================\n")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        proc.wait(timeout=5)

if __name__ == "__main__":
    run_tests()
