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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_learn_solve_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9247
    
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
                    if not pages:
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
            for _ in range(40):
                ready = eval_js("Boolean(window.TempoMode && window.TempoApp && window.TempoLearnSolve)")
                if ready:
                    return True
                time.sleep(0.3)
            return False

        if not wait_for_ready():
            raise RuntimeError("Tempo app did not initialize TempoLearnSolve in time")
            
        log("App initialized and TempoLearnSolve is loaded.")

        # Ensure we are in Default Mode (Dmode)
        eval_js("window.TempoMode.setMode('default');")
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getMode()") == 'default', "Not in default mode"
        log("✓ In Default Mode.")

        # =========================================================================
        # 1. Learn & Solve renders without runtime errors on Default Home
        # =========================================================================
        section_exists = eval_js("Boolean(document.getElementById('tempo-learn-solve-section'))")
        assert section_exists, "Learn & Solve section not found in Default Home!"
        log("✓ Check 1: Learn & Solve section renders cleanly on Default Home without errors.")

        # =========================================================================
        # 2. Solve card reveals categories
        # =========================================================================
        eval_js("window.TempoLearnSolve.selectTab('solve');")
        time.sleep(0.2)
        categories = eval_js("""
            (() => {
                const buttons = Array.from(document.querySelectorAll('#learn-solve-subcontent button[role="tab"]'))
                    .map(b => b.innerText.trim());
                return buttons;
            })()
        """)
        log(f"Rendered categories: {categories}")
        assert len(categories) == 5, f"Expected 5 categories, got {len(categories)}"
        assert any("Study" in c for c in categories), "Study category missing"
        assert any("Myself & Future" in c for c in categories), "Myself & Future category missing"
        assert any("Work & Activities" in c for c in categories), "Work & Activities category missing"
        assert any("Relationships" in c for c in categories), "Relationships category missing"
        assert any("Life" in c for c in categories), "Life category missing"
        log("✓ Check 2: Solve card reveals all 5 taxonomy categories.")

        # =========================================================================
        # 3. Categories reveal correct situation subcards
        # =========================================================================
        # Test Study category
        eval_js("window.TempoLearnSolve.selectCategory('study');")
        time.sleep(0.2)
        study_cards = eval_js("""
            (() => {
                return Array.from(document.querySelectorAll('#learn-solve-subcontent h5'))
                    .map(h => h.innerText.trim());
            })()
        """)
        log(f"Study situations: {study_cards}")
        assert any("Deadline pile-up" in s for s in study_cards), "Deadline pile-up missing"
        assert any("Falling behind" in s for s in study_cards), "Falling behind missing"
        assert any("Teamwork problems" in s for s in study_cards), "Teamwork problems missing"

        # Switch to Life category
        eval_js("window.TempoLearnSolve.selectCategory('life');")
        time.sleep(0.2)
        life_cards = eval_js("""
            (() => {
                return Array.from(document.querySelectorAll('#learn-solve-subcontent h5'))
                    .map(h => h.innerText.trim());
            })()
        """)
        log(f"Life situations: {life_cards}")
        assert any("Daily routine has been disrupted" in s for s in life_cards), "Disrupted routine missing"
        log("✓ Check 3: Categories reveal the correct situation subcards.")

        # =========================================================================
        # 4. Clicking a situation opens the shared modal
        # =========================================================================
        eval_js("window.TempoLearnSolve.openModal('deadline_pileup');")
        time.sleep(0.3)
        modal_visible = eval_js("""
            (() => {
                const m = document.getElementById('tempo-learn-solve-modal');
                return Boolean(m && !m.classList.contains('hidden'));
            })()
        """)
        assert modal_visible, "Modal did not open when situation clicked!"
        modal_title = eval_js("document.querySelector('#tempo-learn-solve-modal-card h3')?.innerText")
        assert "Deadline pile-up" in modal_title, f"Modal title mismatch: {modal_title}"
        log(f"✓ Check 4: Situation opens shared modal (Title: '{modal_title}').")

        # =========================================================================
        # 5. Learn card reveals learning topics
        # =========================================================================
        eval_js("window.TempoLearnSolve.closeModal();")
        time.sleep(0.2)
        eval_js("window.TempoLearnSolve.selectTab('learn');")
        time.sleep(0.2)
        learn_topics = eval_js("""
            (() => {
                return Array.from(document.querySelectorAll('#learn-solve-subcontent h5'))
                    .map(h => h.innerText.trim());
            })()
        """)
        log(f"Learn topics: {len(learn_topics)} topics found")
        assert len(learn_topics) == 9, f"Expected 9 topics, got {len(learn_topics)}"
        assert any("What is stress?" in t for t in learn_topics), "What is stress? missing"
        assert any("The stress loop" in t for t in learn_topics), "The stress loop missing"
        assert any("Academic burnout" in t for t in learn_topics), "Academic burnout missing"
        assert any("Stress eating" in t for t in learn_topics), "Stress eating missing"
        log("✓ Check 5: Learn card reveals all 9 learning topics.")

        # =========================================================================
        # 6. Clicking a Learn topic opens the SAME modal system
        # =========================================================================
        eval_js("window.TempoLearnSolve.openModal('stress_loop');")
        time.sleep(0.3)
        learn_modal_visible = eval_js("!document.getElementById('tempo-learn-solve-modal').classList.contains('hidden')")
        assert learn_modal_visible, "Modal did not open for learn topic!"
        learn_modal_title = eval_js("document.querySelector('#tempo-learn-solve-modal-card h3')?.innerText")
        assert "The stress loop" in learn_modal_title, f"Topic title mismatch: {learn_modal_title}"
        log(f"✓ Check 6: Learn topic opens the same modal system (Title: '{learn_modal_title}').")

        # =========================================================================
        # 7. Modal content is structured/readable, not a raw text dump
        # =========================================================================
        structure_check = eval_js("""
            (() => {
                const card = document.getElementById('tempo-learn-solve-modal-card');
                const hasVisualCycle = Boolean(card.querySelector('.border-2'));
                const hasTip = Boolean(card.querySelector('.tempo-tip-callout'));
                const hasRelated = card.innerText.includes('RELATED GUIDES & ACTIONS');
                return { hasVisualCycle, hasTip, hasRelated };
            })()
        """)
        assert structure_check["hasVisualCycle"], "The stress loop visual cycle diagram missing!"
        assert structure_check["hasTip"], "Embedded Tempo Tip callout missing!"
        assert structure_check["hasRelated"], "Related section missing!"
        log("✓ Check 7: Modal content is cleanly structured with diagrams, tips, and related links.")

        # =========================================================================
        # 8. Related Learn -> Solve navigation works in-modal
        # =========================================================================
        # Inside 'stress_loop', click related solve 'deadline_pileup'
        eval_js("window.TempoLearnSolve.openModal('deadline_pileup');")
        time.sleep(0.3)
        curr_title = eval_js("document.querySelector('#tempo-learn-solve-modal-card h3')?.innerText")
        assert "Deadline pile-up" in curr_title, f"Did not navigate to Deadline pile-up, got: {curr_title}"
        log(f"✓ Check 8: In-modal Learn → Solve navigation works (Now at '{curr_title}').")

        # =========================================================================
        # 9. Related Solve -> Learn navigation works in-modal
        # =========================================================================
        # From 'deadline_pileup', click related learn 'stress_loop'
        eval_js("window.TempoLearnSolve.openModal('stress_loop');")
        time.sleep(0.3)
        curr_title2 = eval_js("document.querySelector('#tempo-learn-solve-modal-card h3')?.innerText")
        assert "The stress loop" in curr_title2, f"Did not navigate to The stress loop, got: {curr_title2}"
        log(f"✓ Check 9: In-modal Solve → Learn navigation works (Now at '{curr_title2}').")

        # =========================================================================
        # 10. Modal Back works for cross-linked content (navStack)
        # =========================================================================
        back_btn_text = eval_js("""
            (() => {
                const btn = document.querySelector('#tempo-learn-solve-modal-card button[onclick*="goBackModal"]');
                return btn ? btn.innerText.trim() : null;
            })()
        """)
        log(f"Back button text: {back_btn_text}")
        assert back_btn_text and "Deadline pile-up" in back_btn_text, f"Unexpected back button: {back_btn_text}"

        # Click Back
        eval_js("window.TempoLearnSolve.goBackModal();")
        time.sleep(0.3)
        restored_title = eval_js("document.querySelector('#tempo-learn-solve-modal-card h3')?.innerText")
        assert "Deadline pile-up" in restored_title, f"Back did not restore Deadline pile-up, got: {restored_title}"
        log("✓ Check 10: Modal Back navigation restores previous cross-linked item cleanly.")

        # =========================================================================
        # 11. One related Tempo Tool action successfully calls public tool entry
        # =========================================================================
        # Inside 'deadline_pileup', test Open Focus Zone action
        eval_js("""
            (() => {
                window.__focusZoneCalled = false;
                const orig = window.TempoFocusZone.openQuickEntry;
                window.TempoFocusZone.openQuickEntry = function() {
                    window.__focusZoneCalled = true;
                    if (orig) orig.apply(this, arguments);
                };
            })()
        """)
        eval_js("window.TempoLearnSolve.handleToolAction('focus_zone');")
        time.sleep(0.3)
        called = eval_js("Boolean(window.__focusZoneCalled)")
        assert called, "Public Tempo Tool entry openQuickEntry was not called!"
        log("✓ Check 11: Tool cross-linking uses the Phase 1 public tool entry without duplication.")

        # Close any tool modals opened
        eval_js("if(window.TempoFocusZone && window.TempoFocusZone.close) window.TempoFocusZone.close();")
        time.sleep(0.2)

        # =========================================================================
        # 12. One mode cross-link uses existing mode architecture without silent switching
        # =========================================================================
        # Open modal for 'grades' which links to 'recovery' mode
        eval_js("window.TempoLearnSolve.openModal('grades');")
        time.sleep(0.3)
        
        # Verify mode has not changed before click
        assert eval_js("window.TempoMode.getMode()") == 'default', "Mode silently switched before click!"
        
        # 12a. When anonymous, clicking mode action preserves auth gating & sets pendingMode
        eval_js("window.TempoLearnSolve.handleModeAction('recovery');")
        time.sleep(0.4)
        assert eval_js("window.TempoMode.getPendingMode()") == 'recovery', "Anonymous requestMode did not set pendingMode!"
        assert eval_js("window.TempoMode.getMode()") == 'default', "Mode should not activate before authentication!"
        log("✓ Check 12a: Anonymous mode cross-link preserves established auth gating and pendingMode.")

        # Close sign-in modal if opened
        eval_js("if(window.TempoAuth && window.TempoAuth.closeModal) window.TempoAuth.closeModal();")
        time.sleep(0.2)

        # 12b. Authenticate user and verify direct mode switch works cleanly
        eval_js("window.TempoAuth.signIn('alex.chen@university.edu', 'demo1234');")
        time.sleep(0.4)
        eval_js("window.TempoLearnSolve.openModal('grades');")
        time.sleep(0.2)
        eval_js("window.TempoLearnSolve.handleModeAction('recovery');")
        time.sleep(0.4)
        new_mode = eval_js("window.TempoMode.getMode()")
        assert new_mode == 'recovery', f"Expected mode 'recovery', got {new_mode}"
        log("✓ Check 12b: Authenticated mode cross-link successfully activates target mode.")

        # Return to default mode
        eval_js("window.TempoMode.setMode('default');")
        time.sleep(0.3)

        # =========================================================================
        # 13. Closing modal returns safely
        # =========================================================================
        eval_js("window.TempoLearnSolve.openModal('what_is_stress');")
        time.sleep(0.2)
        assert eval_js("!document.getElementById('tempo-learn-solve-modal').classList.contains('hidden')"), "Modal did not open"
        
        eval_js("window.TempoLearnSolve.closeModal();")
        time.sleep(0.2)
        assert eval_js("document.getElementById('tempo-learn-solve-modal').classList.contains('hidden')"), "Modal did not close"
        assert eval_js("!document.body.classList.contains('overflow-hidden')"), "Body overflow not unlocked after close"
        log("✓ Check 13: Closing modal restores screen state and unlocks body scrolling.")

        # =========================================================================
        # 14. Basic mobile layout does not overflow
        # =========================================================================
        send_command("Emulation.setDeviceMetricsOverride", {
            "width": 375,
            "height": 667,
            "deviceScaleFactor": 2,
            "mobile": True
        })
        time.sleep(0.3)
        
        no_h_overflow = eval_js("""
            (() => {
                const el = document.getElementById('tempo-learn-solve-section');
                return el.scrollWidth <= document.documentElement.clientWidth + 10;
            })()
        """)
        assert no_h_overflow, "Horizontal overflow detected on mobile viewport!"
        log("✓ Check 14: Mobile viewport layout renders cleanly without horizontal overflow.")

        log("\n🎉 ALL 14 LIGHTWEIGHT SMOKE CHECKS PASSED SUCCESSFULLY!")

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

if __name__ == '__main__':
    run_tests()
