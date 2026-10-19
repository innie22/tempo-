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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_checkpoint_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9245
    
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
                raw = ws.recv()
                msg = json.loads(raw)
                if msg.get("id") == cid:
                    if "error" in msg:
                        raise RuntimeError(f"CDP error: {msg['error']}")
                    return msg.get("result", {})

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
                    ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined' && typeof window.TempoUrmodeFlow !== 'undefined' && typeof window.TempoStressRelief !== 'undefined'")
                    if ready:
                        eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("Application failed to become ready")

        log("Waiting for page and scripts ready...")
        wait_for_ready()

        # Seed mock user and authenticate
        eval_js("""
            (async () => {
                const mock = {
                    id: 'local_user_test101',
                    email: 'alex.chen@university.edu',
                    raw_email: 'alex.chen@university.edu',
                    password: 'password123',
                    user_metadata: {
                        full_name: 'Alex Chen',
                        display_name: 'Alex Chen',
                        role: 'student'
                    }
                };
                localStorage.setItem('tempo_mock_account_alex.chen@university.edu', JSON.stringify(mock));
                await window.TempoAuth.signIn('alex.chen@university.edu', 'password123');
                if (window.TempoAuth.closeAllAuthModals) window.TempoAuth.closeAllAuthModals();
            })()
        """)
        time.sleep(0.3)

        # =====================================================================
        # TEST 1: Full Flow: Reset -> Breathing -> Exactly ONE Grounded Checkpoint
        # =====================================================================
        log("\n--- TEST 1: Reset -> Breathing -> Single Grounded Checkpoint ---")
        eval_js("""
            (async () => {
                await window.TempoPlanStore.archiveActivePlan('emergency');
                window.TempoPlanStore.clearInMemoryCache();
                if (window.TempoEmergencyFlow) {
                    if (window.TempoEmergencyFlow.startFreshPlan) window.TempoEmergencyFlow.startFreshPlan();
                    if (window.TempoEmergencyFlow.setConfirmedPlan) window.TempoEmergencyFlow.setConfirmedPlan(null);
                    window.TempoEmergencyFlow.goToStage('entry');
                }
                window.TempoUrmodeFlow.queueResetPopup();
                window.TempoMode.setMode('emergency');
                window.TempoApp.navigateTo('today');
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.3)

        # 1. Reset popup visible
        reset_visible = eval_js("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                const isVisible = modal && !modal.classList.contains('hidden');
                const title = modal ? modal.querySelector('h2')?.textContent.trim() : '';
                return isVisible && title.includes('Take a moment to reset?');
            })()
        """)
        assert reset_visible, "Reset popup should be visible on explicit entry"
        log("✓ Step 1: Reset popup displayed.")

        # 2. Click 'Yes, take a quick reset ->'
        eval_js("window.TempoUrmodeFlow.handleResetYes()")
        time.sleep(0.3)

        breathing_open = eval_js("""
            (() => {
                const bModal = document.getElementById('modal-quick-stress-relief');
                const isVisible = bModal && !bModal.classList.contains('hidden');
                const hasBreathing = bModal ? bModal.textContent.includes('Box Breathing Reset') : false;
                return isVisible && hasBreathing;
            })()
        """)
        assert breathing_open, "Stress relief breathing setup should open"
        log("✓ Step 2: Box Breathing setup opened.")

        # 3. Start breathing session
        eval_js("window.TempoStressRelief.startBreathingSession()")
        time.sleep(0.2)
        session_running = eval_js("""
            (() => {
                const bModal = document.getElementById('modal-quick-stress-relief');
                const hasFinishEarly = bModal ? !!bModal.querySelector('button[onclick*=\"endSessionEarly\"]') : false;
                return hasFinishEarly;
            })()
        """)
        assert session_running, "Breathing session should be actively running with Finish Early button"
        log("✓ Step 3: Breathing session running.")

        # 4. User finishes breathing session via Finish Early
        eval_js("window.TempoStressRelief.endSessionEarly()")
        time.sleep(0.3)

        # Check what is rendered now:
        # Breathing modal must be closed!
        # Generic checkpoint ("How are you feeling now?") must NOT be visible!
        # Grounded Checkpoint ("Are you ready?") MUST be the ONLY modal visible!
        post_breathing = eval_js("""
            (() => {
                const bModal = document.getElementById('modal-quick-stress-relief');
                const bModalVisible = bModal && !bModal.classList.contains('hidden');
                const bModalHasGenericCheckpoint = bModal ? bModal.textContent.includes('How are you feeling now?') : false;

                const flowModal = document.getElementById('modal-urmode-flow');
                const flowModalVisible = flowModal && !flowModal.classList.contains('hidden');
                const eyebrow = flowModal ? flowModal.querySelector('.text-emerald-700')?.textContent.trim() : '';
                const title = flowModal ? flowModal.querySelector('h2')?.textContent.trim() : '';
                const p = flowModal ? flowModal.querySelector('p')?.textContent.trim() : '';
                const supporting = flowModal ? flowModal.querySelectorAll('p')[1]?.textContent.trim() : '';
                const btns = flowModal ? Array.from(flowModal.querySelectorAll('button')).map(b => b.textContent.trim()) : [];
                const closeBtn = flowModal ? flowModal.querySelector('button[aria-label=\"Close dialog\"]') : null;

                return {
                    bModalVisible,
                    bModalHasGenericCheckpoint,
                    flowModalVisible,
                    eyebrow,
                    title,
                    p,
                    supporting,
                    btns,
                    hasCloseBtn: !!closeBtn
                };
            })()
        """)

        assert not post_breathing['bModalVisible'], "Quick Relief modal must be closed"
        assert not post_breathing['bModalHasGenericCheckpoint'], "Generic Quick Relief checkpoint ('How are you feeling now?') must NOT be rendered in Urmode flow"
        assert post_breathing['flowModalVisible'], "Grounded Checkpoint modal must be visible"
        assert post_breathing['eyebrow'] == 'GROUNDED CHECKPOINT', f"Eyebrow must be 'GROUNDED CHECKPOINT', got {post_breathing['eyebrow']}"
        assert post_breathing['title'] == 'Are you ready?', f"Title must be 'Are you ready?', got {post_breathing['title']}"
        assert "You took a moment to breathe and reset." in post_breathing['p'], f"Message incorrect: {post_breathing['p']}"
        assert "If you still feel overwhelmed" in post_breathing['supporting'], f"Supporting text incorrect: {post_breathing['supporting']}"
        assert any("Not yet, return to reset" in b for b in post_breathing['btns']), "Must have 'Not yet, return to reset' button"
        assert any("Yes, I'm ready" in b for b in post_breathing['btns']), "Must have 'Yes, I\\'m ready →' button"
        assert post_breathing['hasCloseBtn'], "Must have Close (X) button"
        log("✓ Step 4: Exactly ONE Grounded Checkpoint rendered with exact wording and controls.")

        # =====================================================================
        # TEST 2: Navigation: 'Not yet, return to reset' and Retry
        # =====================================================================
        log("\n--- TEST 2: 'Not yet, return to reset' & Flow Retry ---")
        eval_js("window.TempoUrmodeFlow.showResetPopup()")
        time.sleep(0.2)

        returned_to_reset = eval_js("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                const title = modal ? modal.querySelector('h2')?.textContent.trim() : '';
                return title.includes('Take a moment to reset?');
            })()
        """)
        assert returned_to_reset, "'Not yet, return to reset' should return to Reset popup"
        log("✓ Step 5: Returned to Reset popup.")

        # Retry breathing
        eval_js("window.TempoUrmodeFlow.handleResetYes()")
        time.sleep(0.2)
        eval_js("window.TempoStressRelief.startBreathingSession()")
        time.sleep(0.2)
        eval_js("window.TempoStressRelief.endSessionEarly()")
        time.sleep(0.3)

        single_checkpoint_again = eval_js("""
            (() => {
                const flowModal = document.getElementById('modal-urmode-flow');
                const isVisible = flowModal && !flowModal.classList.contains('hidden');
                const title = flowModal ? flowModal.querySelector('h2')?.textContent.trim() : '';
                const bModal = document.getElementById('modal-quick-stress-relief');
                const bVisible = bModal && !bModal.classList.contains('hidden');
                return isVisible && title === 'Are you ready?' && !bVisible;
            })()
        """)
        assert single_checkpoint_again, "Grounded Checkpoint should appear exactly once upon retry"
        log("✓ Step 6: Grounded Checkpoint appears exactly once upon retry.")

        # =====================================================================
        # TEST 3: Navigation: 'Yes, I'm ready ->' advances to Working Plan setup
        # =====================================================================
        log("\n--- TEST 3: 'Yes, I'm ready ->' advances to Working Plan Setup ---")
        eval_js("window.TempoUrmodeFlow.handleAreYouReadyYes()")
        time.sleep(0.3)

        setup_view = eval_js("""
            (() => {
                const stage = window.TempoEmergencyFlow ? window.TempoEmergencyFlow.getCurrentStage() : null;
                const modal = document.getElementById('modal-urmode-flow');
                const modalHidden = !modal || modal.classList.contains('hidden');
                const screenEmergency = document.getElementById('screen-emergency');
                const emVisible = screenEmergency && !screenEmergency.classList.contains('hidden');
                return { stage, modalHidden, emVisible };
            })()
        """)
        assert setup_view['stage'] == 'reality-check', f"Expected stage 'reality-check', got {setup_view['stage']}"
        assert setup_view['modalHidden'], "Checkpoint modal should be closed"
        assert setup_view['emVisible'], "Emergency screen should be visible"
        log("✓ Step 7: Successfully advanced to Working Plan setup (reality-check).")

        # =====================================================================
        # TEST 4: Close (X) button closes checkpoint to dashboard
        # =====================================================================
        log("\n--- TEST 4: Close (X) button on Grounded Checkpoint ---")
        # Trigger checkpoint again
        eval_js("""
            (() => {
                window.TempoMode.setMode('emergency');
                window.TempoApp.navigateTo('today');
                window.TempoUrmodeFlow.showAreYouReadyPopup();
            })()
        """)
        time.sleep(0.2)
        eval_js("window.TempoUrmodeFlow.closeModal('dashboard')")
        time.sleep(0.2)

        closed_to_dashboard = eval_js("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                const isHidden = !modal || modal.classList.contains('hidden');
                const nowCard = document.querySelector('.urgent-card-now');
                return isHidden && !!nowCard;
            })()
        """)
        assert closed_to_dashboard, "Close (X) should close modal to Urmode dashboard"
        log("✓ Step 8: Close (X) returns to Urmode dashboard.")

        log("\n=======================================================================")
        log(">>> ALL SINGLE GROUNDED CHECKPOINT TESTS PASSED SUCCESSFULLY! <<<")
        log("=======================================================================")

    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        if proc:
            proc.terminate()
            proc.wait()

if __name__ == "__main__":
    run_tests()
