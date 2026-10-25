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

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_unclear_ui_")
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
        send_command("Log.enable")
        send_command("Page.enable")
        send_command("Emulation.setDeviceMetricsOverride", {
            "width": 1280,
            "height": 900,
            "deviceScaleFactor": 1,
            "mobile": False
        })

        def wait_for_ready():
            for _ in range(40):
                ready = eval_js("Boolean(window.TempoMode && window.TempoApp && window.TempoUnclearMode)")
                if ready:
                    return True
                time.sleep(0.3)
            return False

        if not wait_for_ready():
            raise RuntimeError("Tempo app did not initialize in time")
            
        log("App initialized and TempoUnclearMode is available.")

        # Register and sign in test user
        eval_js("""
            (async () => {
                try {
                    await window.TempoAuth.register('Innie Tester', 'innie.test@tempo.edu', 'password123');
                } catch (e) {}
                await window.TempoAuth.signIn('innie.test@tempo.edu', 'password123');
            })()
        """)
        time.sleep(0.8)
        log(f"Authenticated user: {eval_js('window.TempoAuth.getCurrentUser()?.email')}")

        # =========================================================================
        # TEST 1: Enter Unclear Mode & Page Background
        # =========================================================================
        log("\n--- TEST 1: Enter Unclear Mode & Verify Page Background (#FEEAE0) ---")
        eval_js("window.TempoMode.setMode('unclear');")
        time.sleep(0.5)

        mode_bg = eval_js("""
            (() => {
                const bodyBg = window.getComputedStyle(document.body).backgroundColor;
                const mainBg = window.getComputedStyle(document.querySelector('main')).backgroundColor;
                const mode = window.TempoMode.getMode();
                const umodeVisible = !document.getElementById('umode-home-content').classList.contains('hidden');
                return { mode, bodyBg, mainBg, umodeVisible };
            })()
        """)
        log(f"Unclear Mode state: {json.dumps(mode_bg, indent=2)}")
        assert mode_bg["mode"] == "unclear", f"Expected mode 'unclear', got {mode_bg['mode']}"
        assert mode_bg["umodeVisible"] is True, "umode-home-content should be visible"
        # #FEEAE0 is rgb(254, 234, 224)
        assert "254, 234, 224" in mode_bg["bodyBg"], f"Expected body bg #FEEAE0, got {mode_bg['bodyBg']}"
        assert "254, 234, 224" in mode_bg["mainBg"], f"Expected main bg #FEEAE0, got {mode_bg['mainBg']}"
        log("✓ Page background is #FEEAE0 in Unclear Mode.")

        # =========================================================================
        # TEST 2: Top Navigation Bar
        # =========================================================================
        log("\n--- TEST 2: Top Navigation Bar (Return Home, Unclear pill, ((SOS)) I don't feel safe) ---")
        top_nav = eval_js("""
            (() => {
                const retHomeBtn = document.querySelector('#unclear-home-view button[onclick*="returnToHome"]');
                const unclearBtn = document.getElementById('btn-home-mode-selector');
                const sosBtn = document.querySelector('#unclear-home-view button[onclick*="openSOS"]');
                
                return {
                    hasReturnHome: Boolean(retHomeBtn),
                    returnHomeText: retHomeBtn ? retHomeBtn.innerText.trim() : null,
                    hasUnclearPill: Boolean(unclearBtn),
                    unclearPillText: unclearBtn ? unclearBtn.innerText.trim() : null,
                    hasSosBtn: Boolean(sosBtn),
                    sosBtnText: sosBtn ? sosBtn.innerText.trim() : null,
                    sosBg: sosBtn ? window.getComputedStyle(sosBtn).backgroundColor : null
                };
            })()
        """)
        log(f"Top nav info: {json.dumps(top_nav, indent=2)}")
        assert top_nav["hasReturnHome"], "Return Home button missing"
        assert "Return Home" in top_nav["returnHomeText"]
        assert top_nav["hasUnclearPill"], "Unclear mode button missing"
        assert "Unclear" in top_nav["unclearPillText"]
        assert top_nav["hasSosBtn"], "SOS button missing"
        assert "I don" in top_nav["sosBtnText"] and "feel safe" in top_nav["sosBtnText"]
        # Check red background
        assert "189, 48, 34" in top_nav["sosBg"] or "192, 50, 33" in top_nav["sosBg"] or "217, 45, 32" in top_nav["sosBg"], f"Unexpected SOS bg: {top_nav['sosBg']}"
        log("✓ Top navigation has Return Home, Unclear pill, and red ((SOS)) I don't feel safe button.")

        # Test Mode Selector Dropdown in Unclear Mode
        log("\n--- TEST 2B: Mode Selector Dropdown in Unclear Mode ---")
        eval_js("document.getElementById('btn-home-mode-selector').click();")
        time.sleep(0.3)
        dd_info = eval_js("""
            (() => {
                const dd = document.getElementById('home-mode-selector-dropdown');
                return {
                    exists: Boolean(dd),
                    isVisible: dd && !dd.classList.contains('hidden'),
                    hasUrgent: dd ? Boolean(dd.querySelector('button[onclick*="emergency"]')) : false,
                    hasRecovery: dd ? Boolean(dd.querySelector('button[onclick*="recovery"]')) : false,
                    hasUnclear: dd ? Boolean(dd.querySelector('button[onclick*="unclear"]')) : false
                };
            })()
        """)
        log(f"Dropdown info: {json.dumps(dd_info, indent=2)}")
        assert dd_info["isVisible"] is True, "Mode selector dropdown did not open"
        assert dd_info["hasUrgent"] is True, "Dropdown should offer Urgent Mode"
        assert dd_info["hasRecovery"] is True, "Dropdown should offer Recovery Mode"
        assert dd_info["hasUnclear"] is False, "Dropdown should not offer active Unclear Mode"
        # Close dropdown
        eval_js("window.TempoMode.closeAllModeDropdowns();")
        time.sleep(0.2)
        log("✓ Mode selector dropdown functions properly in Unclear Mode.")

        # =========================================================================
        # TEST 3: Left Card — Welcome and Tempo Test
        # =========================================================================
        log("\n--- TEST 3: Left Card — Welcome & Tempo Test ---")
        left_card = eval_js("""
            (() => {
                const view = document.getElementById('unclear-home-view');
                const left = view.querySelector('[data-card="welcome-tempo-test"]');
                if (!left) return null;
                const greeting = left.querySelector('div:first-child');
                const h2 = left.querySelector('h2');
                const h3 = left.querySelector('h3');
                const p = left.querySelector('p.italic');
                const btnTempoTest = left.querySelector('button[onclick*="startNewCheckIn"]');
                const btnViewResults = left.querySelector('button[onclick*="my-test-results"]');
                const cs = window.getComputedStyle(left);
                
                return {
                    greetingText: greeting ? greeting.innerText.trim() : null,
                    h2Text: h2 ? h2.innerText.trim() : null,
                    h3Text: h3 ? h3.innerText.trim() : null,
                    descText: p ? p.innerText.trim() : null,
                    hasBtnTempoTest: Boolean(btnTempoTest),
                    btnTempoTestText: btnTempoTest ? btnTempoTest.innerText.trim() : null,
                    btnTempoTestBg: btnTempoTest ? window.getComputedStyle(btnTempoTest).backgroundColor : null,
                    hasBtnViewResults: Boolean(btnViewResults),
                    btnViewResultsText: btnViewResults ? btnViewResults.innerText.trim() : null,
                    bgColor: cs.backgroundColor,
                    borderRadius: cs.borderRadius
                };
            })()
        """)
        log(f"Left card info: {json.dumps(left_card, indent=2)}")
        assert left_card is not None, "Left card missing"
        assert "Hi" in left_card["greetingText"]
        assert left_card["h2Text"] == "Not sure where to start?"
        assert left_card["h3Text"] == "Let’s figure it out together." or "Let's figure it out together." in left_card["h3Text"]
        assert "Let’s try a few quick check-ins to understand what you need." in left_card["descText"] or "Let's try a few quick check-ins" in left_card["descText"]
        assert left_card["hasBtnTempoTest"] is True, "Do Tempo Test button missing"
        assert "Do Tempo Test" in left_card["btnTempoTestText"]
        # Sage green bg rgb(130, 155, 135) or similar
        assert "130, 155, 135" in left_card["btnTempoTestBg"] or "133, 156, 138" in left_card["btnTempoTestBg"], f"Unexpected Do Tempo Test bg: {left_card['btnTempoTestBg']}"
        assert left_card["hasBtnViewResults"] is True, "View my results button missing"
        assert "View my results" in left_card["btnViewResultsText"]
        log("✓ Left card matches reference: Greeting, Headings, Description, Do Tempo Test & View my results buttons.")

        # =========================================================================
        # TEST 4: Right Card — Explore Mental Health Tests
        # =========================================================================
        log("\n--- TEST 4: Right Card — Explore Mental Health Tests ---")
        right_card = eval_js("""
            (() => {
                const view = document.getElementById('unclear-home-view');
                const right = view.querySelector('[data-card="explore-assessments"]');
                if (!right) return null;
                const h2 = right.querySelector('h2');
                const buttons = Array.from(right.querySelectorAll('button[onclick*="explore-mental-health-tests"]'))
                    .map(b => b.innerText.trim());
                const cs = window.getComputedStyle(right);
                
                return {
                    title: h2 ? h2.innerText.trim().replace(/\\s+/g, ' ') : null,
                    buttons,
                    buttonsCount: buttons.length,
                    bgColor: cs.backgroundColor,
                    borderRadius: cs.borderRadius
                };
            })()
        """)
        log(f"Right card info: {json.dumps(right_card, indent=2)}")
        assert right_card is not None, "Right card missing"
        assert "Explore Mental Health Tests" in right_card["title"]
        expected_categories = [
            "Depression Assessments",
            "Stress Assessments",
            "Anxiety Assessments",
            "Other Assessments"
        ]
        assert right_card["buttons"] == expected_categories, f"Category buttons order mismatch: {right_card['buttons']}"
        log("✓ Right card matches reference: Sage green card with 4 category buttons in exact order.")

        # =========================================================================
        # TEST 5: Bottom Tool Cards (Quick Relief, Learn & Solve, Tempo break)
        # =========================================================================
        log("\n--- TEST 5: Bottom Tool Cards (Quick Relief, Learn & Solve, Tempo break) ---")
        tool_cards = eval_js("""
            (() => {
                const view = document.getElementById('unclear-home-view');
                const cards = [
                    view.querySelector('[data-card="quick-relief"]'),
                    view.querySelector('[data-card="learn-solve"]'),
                    view.querySelector('[data-card="tempo-break"]')
                ].filter(Boolean);
                return cards.map(c => {
                    const h3 = c.querySelector('h3');
                    const p = c.querySelector('p');
                    const img = c.querySelector('img');
                    const cs = window.getComputedStyle(c);
                    return {
                        title: h3 ? h3.innerText.trim() : null,
                        desc: p ? p.innerText.trim() : null,
                        imgSrc: img ? img.getAttribute('src') : null,
                        bgColor: cs.backgroundColor,
                        borderRadius: cs.borderRadius
                    };
                });
            })()
        """)
        log(f"Tool cards: {json.dumps(tool_cards, indent=2)}")
        assert len(tool_cards) == 3, f"Expected 3 tool cards, got {len(tool_cards)}"
        # Card 1: Quick Relief
        assert tool_cards[0]["title"] == "Quick Relief"
        assert "Quick ways to ease stress and feel better." in tool_cards[0]["desc"]
        assert "quick-relief-mascot-transparent.png" in tool_cards[0]["imgSrc"]
        # Card 2: Learn & Solve
        assert "Learn & Solve" in tool_cards[1]["title"]
        assert "Tips and tools to help you cope." in tool_cards[1]["desc"]
        assert "learn-solve-mascot.png" in tool_cards[1]["imgSrc"]
        # Card 3: Tempo break
        assert tool_cards[2]["title"] == "Tempo break"
        assert "Take a break with fun activities to unwind." in tool_cards[2]["desc"]
        assert "tempo-break-mascot.png" in tool_cards[2]["imgSrc"]
        log("✓ Three bottom tool cards match reference: Quick Relief, Learn & Solve, and Tempo break.")

        # Capture desktop screenshot of Unclear Mode Home
        capture_screenshot("unclear_mode_dashboard_desktop.png")

        # =========================================================================
        # TEST 6: Do Tempo Test -> Triggers Existing Ucheck Assessment Flow
        # =========================================================================
        log("\n--- TEST 6: Do Tempo Test -> Existing Ucheck Flow ---")
        eval_js("document.querySelector('#unclear-home-view button[onclick*=\"startNewCheckIn\"]').click();")
        time.sleep(0.5)

        ucheck_flow_info = eval_js("""
            (() => {
                const stageBody = document.getElementById('unclear-stage-body');
                const h2 = stageBody ? stageBody.querySelector('h2') : null;
                const stageText = document.querySelector('.max-w-3xl span.text-xs.font-bold');
                const backBtn = document.querySelector('.max-w-3xl button[onclick*="goBack"]');
                return {
                    inFlow: Boolean(stageBody),
                    stageText: stageText ? stageText.innerText.trim() : null,
                    h2Text: h2 ? h2.innerText.trim() : null,
                    hasBackBtn: Boolean(backBtn)
                };
            })()
        """)
        log(f"Ucheck flow state: {json.dumps(ucheck_flow_info, indent=2)}")
        assert ucheck_flow_info["inFlow"] is True, "Failed to enter Ucheck check-in flow"
        assert "1 of 4" in ucheck_flow_info["stageText"]
        assert "What's been on your mind" in ucheck_flow_info["h2Text"]
        assert ucheck_flow_info["hasBackBtn"] is True
        log("✓ Do Tempo Test successfully connects to existing 4-stage Ucheck assessment flow.")

        # Click Back to return to Unclear Mode Home
        eval_js("window.TempoUnclearMode.goBack();")
        time.sleep(0.4)
        assert eval_js("Boolean(document.getElementById('unclear-home-view'))") is True, "Failed to return to Unclear Home view"
        log("✓ Successfully returned to Unclear Mode Home from assessment back navigation.")

        # =========================================================================
        # TEST 7: View my results -> Placeholder Page 1 (My Test Results)
        # =========================================================================
        log("\n--- TEST 7: View my results -> My Test Results Placeholder Page ---")
        eval_js("document.querySelector('#unclear-home-view button[onclick*=\"my-test-results\"]').click();")
        time.sleep(0.5)

        my_results_info = eval_js("""
            (() => {
                const screen = document.getElementById('screen-my-test-results');
                if (!screen || screen.classList.contains('hidden')) return null;
                const h1 = screen.querySelector('h1');
                const p = screen.querySelector('p');
                const backBtn = screen.querySelector('button');
                return {
                    isVisible: true,
                    h1Text: h1 ? h1.innerText.trim() : null,
                    pText: p ? p.innerText.trim() : null,
                    hasBackBtn: Boolean(backBtn),
                    backBtnText: backBtn ? backBtn.innerText.trim() : null,
                    hash: window.location.hash
                };
            })()
        """)
        log(f"My Test Results page: {json.dumps(my_results_info, indent=2)}")
        assert my_results_info is not None, "My Test Results screen is not visible"
        assert my_results_info["h1Text"] == "My Test Results"
        assert "Your assessment results will be collected here." in my_results_info["pText"]
        assert "Back to Unclear Mode" in my_results_info["backBtnText"]
        capture_screenshot("my_test_results_placeholder.png")
        log("✓ My Test Results placeholder page is verified with title, supporting copy, and back button.")

        # Test Back button on My Test Results returns to Unclear Mode
        log("\n--- TEST 7B: Back Button returns from My Test Results to Unclear Mode ---")
        eval_js("document.querySelector('#screen-my-test-results button').click();")
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getMode()") == "unclear", "Mode should be unclear"
        assert eval_js("Boolean(document.getElementById('unclear-home-view'))") is True, "Unclear Home view should be visible"
        log("✓ Back button cleanly returns to Unclear Mode.")

        # =========================================================================
        # TEST 8: Category Buttons -> Explore Mental Health Tests Placeholder Page
        # =========================================================================
        log("\n--- TEST 8: Category Buttons -> Explore Mental Health Tests (with category preselection) ---")
        
        # Test clicking "Anxiety Assessments" from Unclear dashboard
        eval_js("document.querySelectorAll('#unclear-home-view button[onclick*=\"explore-mental-health-tests\"]')[2].click();")
        time.sleep(0.5)

        explore_info = eval_js("""
            (() => {
                const screen = document.getElementById('screen-explore-mental-health-tests');
                if (!screen || screen.classList.contains('hidden')) return null;
                const h1 = screen.querySelector('h1');
                const p = screen.querySelector('p');
                const backBtn = screen.querySelector('button');
                const activeCat = window.TempoExploreAssessments ? window.TempoExploreAssessments.getActiveCategory() : null;
                const selectedHeading = screen.querySelector('#explore-category-content h2');
                const hash = window.location.hash;
                return {
                    isVisible: true,
                    h1Text: h1 ? h1.innerText.trim() : null,
                    pText: p ? p.innerText.trim() : null,
                    hasBackBtn: Boolean(backBtn),
                    backBtnText: backBtn ? backBtn.innerText.trim() : null,
                    activeCat,
                    selectedHeading: selectedHeading ? selectedHeading.innerText.trim() : null,
                    hash
                };
            })()
        """)
        log(f"Explore Mental Health Tests page info: {json.dumps(explore_info, indent=2)}")
        assert explore_info is not None, "Explore Mental Health Tests screen is not visible"
        assert explore_info["h1Text"] == "Explore Mental Health Tests"
        assert "Find an assessment that fits what you need." in explore_info["pText"]
        assert "Back to Unclear Mode" in explore_info["backBtnText"]
        assert explore_info["activeCat"] == "anxiety", f"Expected active category 'anxiety', got {explore_info['activeCat']}"
        assert explore_info["selectedHeading"] == "Anxiety Assessments"
        assert "category=anxiety" in explore_info["hash"]
        capture_screenshot("explore_mental_health_tests_anxiety.png")
        log("✓ Category pre-selection (Anxiety) verified with URL hash synchronization.")

        # Test Switching categories on the page without leaving
        log("\n--- TEST 8B: Switching categories on the shared page ---")
        eval_js("window.TempoExploreAssessments.selectCategory('stress');")
        time.sleep(0.3)
        switch_cat = eval_js("""
            (() => {
                return {
                    activeCat: window.TempoExploreAssessments.getActiveCategory(),
                    heading: document.querySelector('#explore-category-content h2')?.innerText.trim(),
                    hash: window.location.hash
                };
            })()
        """)
        log(f"After switching to stress: {json.dumps(switch_cat, indent=2)}")
        assert switch_cat["activeCat"] == "stress"
        assert switch_cat["heading"] == "Stress Assessments"
        assert "category=stress" in switch_cat["hash"]
        log("✓ Switched to Stress Assessments seamlessly on the shared page.")

        # Test Back button returns to Unclear Mode
        log("\n--- TEST 8C: Back Button returns from Explore Tests to Unclear Mode ---")
        eval_js("document.querySelector('#screen-explore-mental-health-tests button').click();")
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getMode()") == "unclear"
        assert eval_js("Boolean(document.getElementById('unclear-home-view'))") is True
        log("✓ Back button cleanly returns to Unclear Mode.")

        # =========================================================================
        # TEST 9: Return Home Navigation
        # =========================================================================
        log("\n--- TEST 9: Return Home Navigation ---")
        eval_js("document.querySelector('#unclear-home-view button[onclick*=\"returnToHome\"]').click();")
        time.sleep(0.5)

        ret_home = eval_js("""
            (() => {
                const mode = window.TempoMode.getMode();
                const dmodeVisible = !document.getElementById('dmode-home-content').classList.contains('hidden');
                const umodeVisible = !document.getElementById('umode-home-content').classList.contains('hidden');
                const bodyBg = window.getComputedStyle(document.body).backgroundColor;
                return { mode, dmodeVisible, umodeVisible, bodyBg };
            })()
        """)
        log(f"After Return Home: {json.dumps(ret_home, indent=2)}")
        assert ret_home["mode"] == "default", f"Expected mode default, got {ret_home['mode']}"
        assert ret_home["dmodeVisible"] is True, "Entry Home content should be visible"
        assert ret_home["umodeVisible"] is False, "Unclear Mode content should be hidden"
        log("✓ Return Home button cleanly returns to Entry Home.")

        # =========================================================================
        # TEST 10: Responsiveness across Tablet and Mobile Breakpoints
        # =========================================================================
        log("\n--- TEST 10: Responsiveness across Breakpoints ---")
        eval_js("window.TempoMode.setMode('unclear');")
        time.sleep(0.4)

        # Tablet 768x1024
        send_command("Emulation.setDeviceMetricsOverride", {
            "width": 768,
            "height": 1024,
            "deviceScaleFactor": 1,
            "mobile": False
        })
        time.sleep(0.4)
        tablet_overflow = eval_js("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        assert tablet_overflow is False, "Tablet viewport has horizontal overflow!"
        capture_screenshot("unclear_mode_tablet.png")
        log("✓ Tablet breakpoint (768x1024) rendered without overflow.")

        # Mobile 375x812
        send_command("Emulation.setDeviceMetricsOverride", {
            "width": 375,
            "height": 812,
            "deviceScaleFactor": 2,
            "mobile": True
        })
        time.sleep(0.4)
        mobile_overflow = eval_js("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        assert mobile_overflow is False, "Mobile viewport has horizontal overflow!"
        capture_screenshot("unclear_mode_mobile.png")
        log("✓ Mobile breakpoint (375x812) rendered without overflow.")

        log("\n==============================================")
        log("ALL 10 UNCLEAR MODE UI & NAVIGATION TESTS PASSED!")
        log("==============================================")

    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    run_tests()
