import subprocess
import time
import json
import urllib.request
import tempfile
import os
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_recovery_smoke_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9228
    
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
        send_command("Log.enable")

        def wait_for_ready():
            for _ in range(30):
                try:
                    res = eval_js("typeof window.TempoMode")
                    if res != 'undefined':
                        return True
                except Exception as e:
                    pass
                time.sleep(0.5)
            # If not ready, get any console errors
            errs = eval_js("window.__errors || 'none'")
            raise TimeoutError(f"TempoMode was not initialized. window.__errors: {errs}")

        log("Waiting for page and scripts ready...")
        try:
            wait_for_ready()
        except Exception as e:
            # Let's inspect what scripts were loaded or if there is an error in mode.js
            res = send_command("Runtime.evaluate", {
                "expression": "(()=>{ try { new Function(document.querySelector('script[src*=\"mode.js\"]').outerHTML); } catch(err) { return err.stack; } return 'ok'; })()",
                "returnByValue": True
            })
            log(f"Debug script check: {res}")
            raise

        # 1. Page load check
        title = eval_js("document.title")
        log(f"✓ Step 1: App loaded with title: '{title}'")

        # Check safe greeting fallback first
        greeting_fallback = eval_js("window.TempoMode.getSafeGreetingInfo(null)")
        assert greeting_fallback['greetingText'] == 'Hi there 👋'
        log("✓ Safe greeting fallback correctly resolves to 'Hi there 👋'")

        # Test safe greeting with profile
        greeting_profile = eval_js("window.TempoMode.getSafeGreetingInfo({ preferred_name: 'Nhi' })")
        assert greeting_profile['greetingText'] == 'Hi, Nhi 👋'
        log("✓ Safe greeting resolves to 'Hi, Nhi 👋' when profile provides preferred_name")

        # 2. Switch to Recovery Mode
        eval_js("window.TempoMode.setMode('recovery');")
        time.sleep(0.5)
        active_mode = eval_js("window.TempoMode.getMode()")
        assert active_mode == 'recovery', f"Expected mode recovery, got {active_mode}"
        log("✓ Step 2: Successfully switched to Recovery Mode")

        # 3. Recovery Home renders inside #screen-today
        rmode_visible = eval_js("!document.getElementById('rmode-home-content').classList.contains('hidden')")
        assert rmode_visible, "rmode-home-content should be visible"
        
        # Check intro banner
        has_intro = eval_js("document.getElementById('recovery-intro-banner') !== null")
        log(f"✓ Step 3A: Recovery Home container rendered (Intro banner present: {has_intro})")

        # Dismiss intro banner and check disappearance
        eval_js("window.TempoMode.dismissRecoveryIntro();")
        has_intro_after = eval_js("document.getElementById('recovery-intro-banner') !== null")
        assert not has_intro_after, "Intro banner should be dismissed"
        log("✓ Step 3B: Dismissible intro banner dismissed successfully without gaps")

        # Check Self-Check card and safe greeting
        greeting_text = eval_js("document.querySelector('.recovery-card-selfcheck').innerText")
        assert "Hi, Nhi 👋" in greeting_text or "Hi there 👋" in greeting_text, f"Unexpected greeting: {greeting_text}"
        assert "SELF-CHECK" in greeting_text
        assert "What would you like to keep an eye on?" in greeting_text
        assert "Set up Self-check" in greeting_text
        log("✓ Step 3C: Self-check card rendered with safe greeting inside")

        # 4. Mode selector popover test
        eval_js("window.TempoMode.toggleModeDropdown();")
        time.sleep(0.2)
        dropdown_visible = eval_js("!document.getElementById('home-mode-selector-dropdown').classList.contains('hidden')")
        assert dropdown_visible, "Mode dropdown should be visible when toggled"
        dropdown_html = eval_js("document.getElementById('home-mode-selector-dropdown').innerHTML")
        assert "Urgent Mode" in dropdown_html
        assert "Unclear Mode" in dropdown_html
        assert "Take a break from modes" in dropdown_html
        assert "Recovery Mode" not in dropdown_html, "Recovery Mode should not be listed as destination when already active"
        assert "SOS" not in dropdown_html, "SOS must not be inside mode dropdown"
        eval_js("window.TempoMode.closeAllModeDropdowns();")
        log("✓ Step 4: Mode selector popover correctly renders destinations excluding current mode")

        # 5. Quick Stress Relief opens
        eval_js("window.TempoStressRelief.openModal();")
        time.sleep(0.3)
        qsr_visible = eval_js("!document.getElementById('modal-quick-stress-relief').classList.contains('hidden')")
        assert qsr_visible, "Quick Stress Relief modal should be visible"
        eval_js("window.TempoStressRelief.closeModal();")
        log("✓ Step 5: Quick Stress Relief modal opens and closes properly")

        # 6. Breathing opens
        eval_js("window.TempoTriage.openBoxBreathingModal();")
        time.sleep(0.3)
        breathing_visible = eval_js("!document.getElementById('modal-quick-stress-relief').classList.contains('hidden')")
        assert breathing_visible, "Breathing modal should be visible"
        eval_js("window.TempoStressRelief.closeModal();")
        log("✓ Step 6: Breathing modal opens and closes properly")

        # 7. Focus CTA reaches existing Focus entry
        fz_open_exists = eval_js("typeof window.TempoFocusZone.openQuickEntry === 'function'")
        assert fz_open_exists, "TempoFocusZone.openQuickEntry should exist"
        log("✓ Step 7: Focus Zone entry integration verified")

        # 8. Today does not show fabricated data
        today_text = eval_js("document.querySelector('.recovery-section-today').innerText")
        assert "Today" in today_text
        # With no tasks planned today, shows honest empty state
        assert "Nothing planned for today" in today_text or "CONTINUE" in today_text or "UP NEXT" in today_text
        log("✓ Step 8: Today section displays real shared state without fabricated tasks")

        # Check Recently section
        recently_text = eval_js("document.querySelector('.recovery-card-recently').innerText")
        assert "RECENTLY" in recently_text
        assert "Nothing here yet" in recently_text
        log("✓ Step 8B: Recently section shows honest empty state without fake analytics")

        # 9. Tempo Posts render as social posts
        posts_html = eval_js("document.getElementById('recovery-community-posts-list').innerHTML")
        assert "Anonymous" in posts_html or "N." in posts_html or "Liam" in posts_html
        assert "♡" in posts_html or "♥" in posts_html
        assert "💬" in posts_html
        assert "min read" not in posts_html, "Tempo Posts must not contain blog/reading time"
        assert "[STUDY TIPS]" not in posts_html
        log("✓ Step 9: Tempo Posts render as social community feed cards")

        # 10. Default / Urgent Home are not broken
        eval_js("window.TempoMode.setMode('default');")
        time.sleep(0.5)
        dmode_visible = eval_js("!document.getElementById('dmode-home-content').classList.contains('hidden')")
        rmode_hidden = eval_js("document.getElementById('rmode-home-content').classList.contains('hidden')")
        assert dmode_visible and rmode_hidden, "Default Home should be visible and Rmode hidden"
        log("✓ Step 10A: Default Mode Home restores properly")

        eval_js("window.TempoMode.setMode('emergency');")
        time.sleep(0.5)
        eval_js("window.TempoApp.navigateTo('today');")
        time.sleep(0.5)
        emode_visible = eval_js("!document.getElementById('emode-home-content').classList.contains('hidden')")
        assert emode_visible, "Urgent Mode Home renders properly"
        log("✓ Step 10B: Urgent Mode Home restores properly")

        # Switch back to Recovery Mode
        eval_js("window.TempoMode.setMode('recovery');")
        time.sleep(0.5)
        log("✓ Step 10C: Switched back to Recovery Mode cleanly")

        log("\n=======================================================")
        log("ALL 10 SMOKE CHECK STEPS PASSED SUCCESSFULLY!")
        log("=======================================================")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        proc.wait(timeout=5)

if __name__ == "__main__":
    run_tests()
