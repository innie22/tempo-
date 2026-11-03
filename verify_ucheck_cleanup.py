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

ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"

def run():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_ucheck_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9262
    
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

        def capture_screenshot(filename):
            res = send_command("Page.captureScreenshot", {"format": "png"})
            data = res.get("data")
            if data:
                import base64
                path = os.path.join(ARTIFACT_DIR, filename)
                with open(path, "wb") as f:
                    f.write(base64.b64decode(data))
                log(f"Saved screenshot: {path}")

        send_command("Runtime.enable")
        send_command("Page.enable")
        send_command("Emulation.setDeviceMetricsOverride", {
            "width": 1280,
            "height": 900,
            "deviceScaleFactor": 1,
            "mobile": False
        })

        for _ in range(40):
            ready = eval_js("Boolean(window.TempoMode && window.TempoApp && window.TempoUnclearMode && window.TempoAuth)")
            if ready:
                break
            time.sleep(0.3)

        # Authenticate
        eval_js("""
            (async () => {
                try {
                    await window.TempoAuth.register('Innie Tester', 'innie.test@tempo.edu', 'password123');
                } catch(e) {}
                await window.TempoAuth.signIn('innie.test@tempo.edu', 'password123');
            })()
        """)
        time.sleep(0.5)

        # =====================================================================
        # 1. VERIFY UCHECK VIETNAMESE STATE
        # =====================================================================
        eval_js("window.TempoI18n.setLanguage('vi');")
        eval_js("window.TempoMode.openUcheck();")
        time.sleep(1.0)

        vi_check = eval_js("""
            (() => {
                const header = document.querySelector('header.entry-header');
                const headerVisible = header && window.getComputedStyle(header).display !== 'none';
                
                const navLinks = Array.from(document.querySelectorAll('header nav a')).map(a => ({
                    id: a.id,
                    text: a.textContent.trim(),
                    href: a.getAttribute('href')
                }));
                
                const langLabel = document.getElementById('nav-current-lang-label')?.textContent?.trim();
                const sosBtn = document.getElementById('btn-nav-sos');
                const userBox = document.getElementById('header-authenticated-box');
                const userBoxVisible = userBox && window.getComputedStyle(userBox).display !== 'none';
                
                // Duplicate bar check
                const unclearHomeView = document.getElementById('unclear-home-view');
                const duplicateRow = unclearHomeView ? unclearHomeView.querySelector('button[title="Return Home"], button[title*="Return"]') : null;
                const duplicateSos = unclearHomeView ? unclearHomeView.querySelector('button[onclick*="openSOS"]') : null;
                const duplicateModeBtn = unclearHomeView ? unclearHomeView.querySelector('#btn-home-mode-selector') : null;
                
                // Card checks
                const cards = Array.from(document.querySelectorAll('#unclear-home-view [data-card]')).map(c => c.getAttribute('data-card'));
                
                // Welcome card and Explore card
                const welcomeCard = document.querySelector('[data-card="welcome-tempo-test"]');
                const exploreCard = document.querySelector('[data-card="explore-assessments"]');
                
                return {
                    headerVisible,
                    navLinks,
                    langLabel,
                    hasSosBtn: !!sosBtn,
                    userBoxVisible,
                    hasDuplicateRow: !!duplicateRow,
                    hasDuplicateSos: !!duplicateSos,
                    hasDuplicateModeBtn: !!duplicateModeBtn,
                    cards,
                    hasWelcomeCard: !!welcomeCard,
                    hasExploreCard: !!exploreCard
                };
            })()
        """)

        log(f"UCheck VI Verification:\n{json.dumps(vi_check, indent=2)}")
        assert vi_check["headerVisible"] is True, "Header must be visible"
        assert vi_check["userBoxVisible"] is True, "User avatar box must be visible"
        assert vi_check["hasSosBtn"] is True, "SOS button must be in header"
        assert vi_check["hasDuplicateRow"] is False, "Duplicate in-page return home row must NOT exist"
        assert vi_check["hasDuplicateSos"] is False, "Duplicate SOS button in page must NOT exist"
        assert vi_check["hasDuplicateModeBtn"] is False, "Duplicate mode selector button in page must NOT exist"
        assert "quick-relief" not in vi_check["cards"], "quick-relief card must be removed"
        assert "learn-solve" not in vi_check["cards"], "learn-solve card must be removed"
        assert "tempo-break" not in vi_check["cards"], "tempo-break card must be removed"
        assert vi_check["hasWelcomeCard"] is True, "welcome-tempo-test card must exist"
        assert vi_check["hasExploreCard"] is True, "explore-assessments card must exist"
        
        # Check nav items in VI
        nav_map = {item["id"]: item["text"] for item in vi_check["navLinks"]}
        assert nav_map.get("nav-link-what-is-tempo") == "Giới thiệu", f"Expected 'Giới thiệu', got {nav_map.get('nav-link-what-is-tempo')}"
        assert nav_map.get("nav-link-check") in ["Tự kiểm tra", "Kế hoạch"], f"Unexpected check link: {nav_map.get('nav-link-check')}"
        assert nav_map.get("nav-link-plan") == "Đánh giá", f"Expected 'Đánh giá', got {nav_map.get('nav-link-plan')}"
        assert nav_map.get("nav-link-community") == "Cộng đồng", f"Expected 'Cộng đồng', got {nav_map.get('nav-link-community')}"

        capture_screenshot("ucheck_cleaned_layout_vi.png")

        # =====================================================================
        # 2. VERIFY UCHECK ENGLISH STATE
        # =====================================================================
        eval_js("window.TempoI18n.setLanguage('en');")
        time.sleep(0.5)

        en_check = eval_js("""
            (() => {
                const navLinks = Array.from(document.querySelectorAll('header nav a')).map(a => ({
                    id: a.id,
                    text: a.textContent.trim(),
                    href: a.getAttribute('href')
                }));
                const langLabel = document.getElementById('nav-current-lang-label')?.textContent?.trim();
                return { navLinks, langLabel };
            })()
        """)
        log(f"UCheck EN Verification:\n{json.dumps(en_check, indent=2)}")
        assert en_check["langLabel"] == "EN", f"Expected 'EN', got {en_check['langLabel']}"
        nav_map_en = {item["id"]: item["text"] for item in en_check["navLinks"]}
        assert nav_map_en.get("nav-link-what-is-tempo") == "About", f"Expected 'About', got {nav_map_en.get('nav-link-what-is-tempo')}"
        assert nav_map_en.get("nav-link-check") in ["Check", "Plan"], f"Unexpected check link: {nav_map_en.get('nav-link-check')}"
        assert nav_map_en.get("nav-link-plan") == "Assessment", f"Expected 'Assessment', got {nav_map_en.get('nav-link-plan')}"
        assert nav_map_en.get("nav-link-community") == "Community", f"Expected 'Community', got {nav_map_en.get('nav-link-community')}"

        capture_screenshot("ucheck_cleaned_layout_en.png")

        # =====================================================================
        # 3. VERIFY QUICK RELIEF STILL WORKS ELSEWHERE
        # =====================================================================
        log("Testing Quick Relief in Recovery Mode...")
        eval_js("window.TempoMode.setMode('recovery');")
        time.sleep(0.5)
        qr_status = eval_js("""
            (() => {
                const hasStressRelief = Boolean(window.TempoStressRelief && typeof window.TempoStressRelief.openModal === 'function');
                const hasTriage = Boolean(window.TempoTriage && typeof window.TempoTriage.openQuickReliefModal === 'function');
                return { hasStressRelief, hasTriage };
            })()
        """)
        log(f"Quick Relief availability: {json.dumps(qr_status)}")
        assert qr_status["hasStressRelief"] or qr_status["hasTriage"], "Quick Relief function must remain intact"

        # Switch back to UCheck
        eval_js("window.TempoMode.openUcheck();")
        time.sleep(0.5)
        
        # Test clicking User Profile dropdown in navbar
        user_dropdown_check = eval_js("""
            (() => {
                const avatarBtn = document.getElementById('header-user-avatar-btn');
                if (avatarBtn) avatarBtn.click();
                const dropdown = document.getElementById('header-avatar-dropdown');
                return {
                    dropdownVisible: dropdown && !dropdown.classList.contains('hidden')
                };
            })()
        """)
        log(f"Navbar Avatar Dropdown open check: {json.dumps(user_dropdown_check)}")
        assert user_dropdown_check["dropdownVisible"] is True, "Navbar avatar dropdown must open on click"

        # Test clicking SOS in navbar
        sos_popup_check = eval_js("""
            (() => {
                const sosBtn = document.getElementById('btn-nav-sos');
                if (sosBtn) sosBtn.click();
                const modal = document.getElementById('progressive-emergency-modal');
                return {
                    modalVisible: modal && !modal.classList.contains('hidden')
                };
            })()
        """)
        log(f"Navbar SOS Trigger check: {json.dumps(sos_popup_check)}")
        assert sos_popup_check["modalVisible"] is True, "Navbar SOS button must open emergency modal"

        # Close emergency modal cleanly
        eval_js("window.TempoEmergencySupport.closeModal(true);")

        log("\n>>> ALL UCHECK CLEANUP AND ACTIVE CONTEXT NAVBAR VERIFICATIONS PASSED! <<<")

    finally:
        if ws:
            ws.close()
        proc.terminate()

if __name__ == "__main__":
    run()
