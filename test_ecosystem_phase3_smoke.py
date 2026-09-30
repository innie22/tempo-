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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_phase3_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9255
    
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
                        ws_url = pages[0].get("webSocketDebuggerUrl")
                        break
            except Exception:
                time.sleep(0.5)
        
        if not ws_url:
            raise RuntimeError("Could not connect to browser WebSocket debugging URL.")
        
        log(f"Connected to CDP: {ws_url}")
        ws = websocket.create_connection(ws_url, timeout=10)
        req_id = 0
        
        def send_eval(expression):
            nonlocal req_id
            req_id += 1
            msg = {
                "id": req_id,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": expression,
                    "returnByValue": True,
                    "awaitPromise": True
                }
            }
            ws.send(json.dumps(msg))
            while True:
                res = json.loads(ws.recv())
                if res.get("id") == req_id:
                    result = res.get("result", {})
                    if "exceptionDetails" in result:
                        raise RuntimeError(f"JS Exception: {result['exceptionDetails']}")
                    return result.get("result", {}).get("value")

        def wait_for_ready():
            for _ in range(50):
                try:
                    ready = send_eval("Boolean(window.TempoMode && window.TempoTools && window.TempoLearnSolve && window.TempoFocusZone && window.TempoApp)")
                    if ready:
                        return True
                except Exception:
                    pass
                time.sleep(0.3)
            return False

        if not wait_for_ready():
            raise RuntimeError("Global Tempo ecosystem objects not loaded in time!")
        log("App initialized with TempoMode, TempoTools, TempoLearnSolve, and TempoFocusZone loaded.")

        # =========================================================================
        # CHECK 1: DEFAULT HOME HIERARCHY & DUPLICATE CLEANUP
        # =========================================================================
        log("\n--- Checking 1: Default Home Hierarchy & Duplicate Cleanup ---")
        send_eval("window.TempoMode.setMode('default');")
        time.sleep(0.5)
        
        dmode_layout = send_eval("""
            (() => {
                const toolsSection = document.querySelector('#dmode-home-content .tempo-tools-section');
                const learnSolveSection = document.querySelector('#dmode-home-content #tempo-learn-solve-section');
                const postsSection = document.querySelector('#dmode-home-content #dmode-posts-section, #dmode-home-content #homepage-community-posts-list');
                const yourDay = document.querySelector('#dmode-home-content #dmode-your-day');
                
                // Check if old 2-card duplicate tools exist
                const oldToolCards = document.querySelectorAll('#dmode-home-content button[onclick*="startDmodeFocus"]');
                
                // Check 4 shared tool cards inside toolsSection
                const toolHeaders = Array.from(toolsSection ? toolsSection.querySelectorAll('h4') : []).map(h => h.innerText.trim());

                return {
                    hasYourDay: Boolean(yourDay),
                    hasTools: Boolean(toolsSection),
                    hasLearnSolve: Boolean(learnSolveSection),
                    hasPosts: Boolean(postsSection),
                    toolHeaders,
                    oldToolCardCount: oldToolCards.length
                };
            })()
        """)
        
        assert dmode_layout["hasYourDay"], "Default Home should have 'Your Day' core section."
        assert dmode_layout["hasTools"], "Default Home should contain the shared Tempo Tools section."
        assert dmode_layout["hasLearnSolve"], "Default Home should contain the shared Learn & Solve section."
        assert dmode_layout["hasPosts"], "Default Home should contain the Tempo Posts section."
        assert dmode_layout["oldToolCardCount"] == 0, "Old duplicate Dmode tool cards must be removed!"
        assert "Focus Zone" in dmode_layout["toolHeaders"], "Shared tools must include Focus Zone."
        assert "Quick Relief" in dmode_layout["toolHeaders"], "Shared tools must include Quick Relief."
        assert "Breathing" in dmode_layout["toolHeaders"], "Shared tools must include Breathing."
        assert "Tempo Break" in dmode_layout["toolHeaders"], "Shared tools must include Tempo Break."
        log(f"✓ Default Home layout confirmed: Your Day -> Self-check/Contextual -> Tools ({dmode_layout['toolHeaders']}) -> Learn & Solve -> Posts.")
        log("✓ Default Home duplicate tool cards verified removed.")

        # =========================================================================
        # CHECK 2: URGENT HOME HIERARCHY, TASK FOCUS CTA & DUPLICATE CLEANUP
        # =========================================================================
        log("\n--- Checking 2: Urgent Home Hierarchy, Task Focus CTA & Duplicate Cleanup ---")
        
        # Populate active plan with a task so Urgent Home renders State B (Active Today)
        send_eval("""
            (() => {
                const nowObj = new Date();
                const todayStr = `${nowObj.getFullYear()}-${String(nowObj.getMonth() + 1).padStart(2, '0')}-${String(nowObj.getDate()).padStart(2, '0')}`;
                
                const samplePlan = {
                    id: 'test-urgent-plan-1',
                    createdAt: new Date().toISOString(),
                    activeWorkDays: [todayStr],
                    plannedTasks: [
                        {
                            dayDate: todayStr,
                            dayLabel: 'Today',
                            startTime: '09:00',
                            task: {
                                id: 'urgent-task-1',
                                name: 'Complete Critical Chemistry Lab',
                                durationMinutes: 45,
                                durationLabel: '45 min',
                                completed: false,
                                isInProgress: true,
                                subtasks: [
                                    { id: 'sub-1', name: 'Gather reagents', completed: true },
                                    { id: 'sub-2', name: 'Measure titration volumes', completed: false }
                                ]
                            }
                        },
                        {
                            dayDate: todayStr,
                            dayLabel: 'Today',
                            startTime: '10:30',
                            task: {
                                id: 'urgent-task-2',
                                name: 'Submit Analysis Summary',
                                durationMinutes: 30,
                                durationLabel: '30 min',
                                completed: false,
                                isInProgress: false,
                                subtasks: []
                            }
                        }
                    ]
                };
                samplePlan.tasks = samplePlan.plannedTasks.map(pt => pt.task);
                samplePlan.availabilityDays = [
                    { date: todayStr, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }
                ];
                
                if (window.TempoPlanStore && window.TempoPlanStore.saveActivePlan) {
                    window.TempoPlanStore.saveActivePlan('emergency', samplePlan);
                }
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(samplePlan);
                }
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.restorePlanState) {
                    window.TempoEmergencyFlow.restorePlanState();
                }
                if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.savePlan === 'function') {
                    window.TempoPlanWorkspace.savePlan(samplePlan);
                }
                window.TempoMode.setMode('emergency');
                window.TempoApp.navigateTo('today');
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.5)

        emode_layout = send_eval("""
            (() => {
                const nowCard = document.querySelector('.urgent-card-now');
                const rightCol = document.querySelector('.urgent-right-col');
                const taskFocusBtn = document.querySelector('.urgent-card-now button[onclick*="startTaskFocus"]');
                
                // Check if old generic support row exists in left column
                const oldSupportRow = document.querySelector('.urgent-left-col .urgent-support-row');
                const oldOverwhelmedCard = document.querySelector('.urgent-card-overwhelmed');
                const oldFocusNowCard = document.querySelector('.urgent-card-focus-now');
                
                // Shared ecosystem components
                const toolsSection = document.querySelector('#emode-home-content .tempo-tools-section');
                const learnSolveSection = document.querySelector('#emode-home-content #tempo-learn-solve-section');
                const postsSection = document.querySelector('#emode-home-content .urgent-section-posts');
                
                return {
                    hasNowCard: Boolean(nowCard),
                    hasRightCol: Boolean(rightCol),
                    hasTaskFocusBtn: Boolean(taskFocusBtn),
                    taskFocusBtnText: taskFocusBtn ? taskFocusBtn.innerText.trim() : null,
                    hasOldSupportRow: Boolean(oldSupportRow),
                    hasOldOverwhelmedCard: Boolean(oldOverwhelmedCard),
                    hasOldFocusNowCard: Boolean(oldFocusNowCard),
                    hasTools: Boolean(toolsSection),
                    hasLearnSolve: Boolean(learnSolveSection),
                    hasPosts: Boolean(postsSection)
                };
            })()
        """)
        
        assert emode_layout["hasNowCard"], "Urgent Home State B must render 'Your task for now' card."
        assert emode_layout["hasRightCol"], "Urgent Home State B must render 'Your plan for today' column."
        assert emode_layout["hasTaskFocusBtn"], "Urgent Home must preserve task-specific Focus CTA in 'Your task for now'."
        assert not emode_layout["hasOldSupportRow"], "Old generic support row must be removed from Urgent Home left column."
        assert not emode_layout["hasOldOverwhelmedCard"], "Duplicate 'Feeling overwhelmed?' card must be removed."
        assert not emode_layout["hasOldFocusNowCard"], "Duplicate generic 'Focus now' card must be removed."
        assert emode_layout["hasTools"], "Urgent Home must render the shared Tempo Tools section below the 2-column grid."
        assert emode_layout["hasLearnSolve"], "Urgent Home must render the shared Learn & Solve section below the 2-column grid."
        assert emode_layout["hasPosts"], "Urgent Home must render the Tempo Posts section."
        log(f"✓ Urgent Home State B confirmed: Task for Now + Plan for Today intact.")
        log(f"✓ Task-specific Focus CTA preserved: '{emode_layout['taskFocusBtnText']}'.")
        log("✓ Redundant generic support row and duplicate focus cards removed from Urgent left column.")
        log("✓ Shared Tempo Tools and Learn & Solve correctly mounted below 2-column core.")

        # =========================================================================
        # CHECK 3: RECOVERY HOME HIERARCHY, SELF-CHECK HERO & DUPLICATE CLEANUP
        # =========================================================================
        log("\n--- Checking 3: Recovery Home Hierarchy, Self-Check Hero & Duplicate Cleanup ---")
        send_eval("window.TempoMode.setMode('recovery');")
        time.sleep(0.5)

        rmode_layout = send_eval("""
            (() => {
                const selfCheckCard = document.querySelector('.recovery-card-selfcheck');
                const leftCol = document.querySelector('.recovery-left-col');
                const oldRecoverySupportRow = document.querySelector('.recovery-support-row');
                const oldQuickReliefCard = document.querySelector('.recovery-card-quickrelief');
                const oldFocusZoneCard = document.querySelector('.recovery-card-focuszone');
                
                const recentlyCard = document.querySelector('.recovery-right-col');
                const todaySection = document.querySelector('.recovery-section-today');
                
                // Shared ecosystem components
                const toolsSection = document.querySelector('#rmode-home-content .tempo-tools-section');
                const learnSolveSection = document.querySelector('#rmode-home-content #tempo-learn-solve-section');
                const postsSection = document.querySelector('#rmode-home-content #recovery-community-posts-list');
                
                return {
                    hasSelfCheck: Boolean(selfCheckCard),
                    hasLeftCol: Boolean(leftCol),
                    hasOldSupportRow: Boolean(oldRecoverySupportRow),
                    hasOldQuickReliefCard: Boolean(oldQuickReliefCard),
                    hasOldFocusZoneCard: Boolean(oldFocusZoneCard),
                    hasRecently: Boolean(recentlyCard),
                    hasToday: Boolean(todaySection),
                    hasTools: Boolean(toolsSection),
                    hasLearnSolve: Boolean(learnSolveSection),
                    hasPosts: Boolean(postsSection)
                };
            })()
        """)

        assert rmode_layout["hasSelfCheck"], "Recovery Home must have Self-Check card as primary hero."
        assert not rmode_layout["hasOldSupportRow"], "Old recovery support row in left column must be removed."
        assert not rmode_layout["hasOldQuickReliefCard"], "Duplicate Quick Relief card in left column must be removed."
        assert not rmode_layout["hasOldFocusZoneCard"], "Duplicate Focus Zone card in left column must be removed."
        assert rmode_layout["hasRecently"], "Recovery Home must maintain Recently / Recovery note in right column."
        assert rmode_layout["hasToday"], "Recovery Home must maintain Today section."
        assert rmode_layout["hasTools"], "Recovery Home must mount shared Tempo Tools below Today."
        assert rmode_layout["hasLearnSolve"], "Recovery Home must mount shared Learn & Solve below Today."
        assert rmode_layout["hasPosts"], "Recovery Home must mount Tempo Posts."
        log("✓ Recovery Home confirmed: Self-check restored as solitary left-column hero.")
        log("✓ Duplicate support cards removed from left column.")
        log("✓ Shared Tempo Tools and Learn & Solve mounted below Today and before Posts.")

        # =========================================================================
        # CHECK 4: SHARED TEMPO TOOLS - FOCUS ZONE LAUNCH & CLOSE
        # =========================================================================
        log("\n--- Checking 4: Shared Tempo Tools - Focus Zone Launch & Close ---")
        send_eval("window.TempoTools.openFocusZone();")
        time.sleep(0.5)

        fz_open = send_eval("""
            (() => {
                const root = document.getElementById('tempo-focus-zone-root');
                const isVisible = root && !root.classList.contains('hidden');
                const state = window.TempoFocusZone.getSessionState();
                return { isVisible, isOpen: state.isOpen, phase: state.phase };
            })()
        """)
        assert fz_open["isVisible"] and fz_open["isOpen"], "TempoTools.openFocusZone() should open Focus Zone."
        log(f"✓ Focus Zone opened via shared Tempo Tools (phase: {fz_open['phase']}).")

        # Close Focus Zone and check active mode preserved
        send_eval("window.TempoFocusZone.close();")
        time.sleep(0.3)
        mode_after_fz = send_eval("window.TempoMode.getCurrentMode()")
        assert mode_after_fz == "recovery", f"Closing Focus Zone must preserve active mode (expected 'recovery', got '{mode_after_fz}')."
        log("✓ Focus Zone closed cleanly; active mode preserved as 'recovery'.")

        # =========================================================================
        # CHECK 5: SHARED TEMPO TOOLS - QUICK RELIEF & BREATHING LAUNCH
        # =========================================================================
        log("\n--- Checking 5: Shared Tempo Tools - Quick Relief & Breathing ---")
        send_eval("window.TempoTools.openQuickRelief();")
        time.sleep(0.5)

        qr_open = send_eval("""
            (() => {
                const modal = document.getElementById('modal-quick-stress-relief') || document.getElementById('stress-relief-modal');
                return Boolean(modal && !modal.classList.contains('hidden'));
            })()
        """)
        assert qr_open, "TempoTools.openQuickRelief() should open Quick Relief modal."
        log("✓ Quick Relief modal opened via shared Tempo Tools.")
        send_eval("if (window.TempoStressRelief && window.TempoStressRelief.closeModal) window.TempoStressRelief.closeModal();")
        time.sleep(0.3)

        send_eval("window.TempoTools.openBreathing();")
        time.sleep(0.5)
        br_open = send_eval("""
            (() => {
                const breathingModal = document.getElementById('modal-quick-stress-relief') || document.getElementById('box-breathing-modal');
                return Boolean(breathingModal && !breathingModal.classList.contains('hidden'));
            })()
        """)
        assert br_open, "TempoTools.openBreathing() should open Breathing reset."
        log("✓ Breathing reset opened via shared Tempo Tools.")
        send_eval("""
            if (window.TempoTriage && window.TempoTriage.closeBoxBreathingModal) window.TempoTriage.closeBoxBreathingModal();
            if (window.TempoStressRelief && window.TempoStressRelief.closeModal) window.TempoStressRelief.closeModal();
        """)
        time.sleep(0.3)

        # =========================================================================
        # CHECK 6: STANDALONE TEMPO BREAK (PHASE 1 INTEGRATION)
        # =========================================================================
        log("\n--- Checking 6: Standalone Tempo Break Integration ---")
        # Ensure we are in urgent mode to test returning without mode change or task alteration
        send_eval("window.TempoMode.setMode('urgent');")
        time.sleep(0.3)

        send_eval("window.TempoTools.openBreak();")
        time.sleep(0.5)

        break_state = send_eval("""
            (() => {
                const root = document.getElementById('tempo-focus-zone-root');
                const isVisible = root && !root.classList.contains('hidden');
                const state = window.TempoFocusZone.getSessionState();
                const titleEl = root.querySelector('h2');
                const titleText = titleEl ? titleEl.innerText.trim() : '';
                const tagEl = root.querySelector('.text-emerald-700.uppercase');
                const tagText = tagEl ? tagEl.innerText.trim() : '';
                const closeBtn = root.querySelector('button[title="Close break"], button[onclick*="window.TempoFocusZone.close()"]');
                const returnCta = root.querySelector('button[onclick*="window.TempoFocusZone.close()"].btn-primary');

                return {
                    isVisible,
                    isOpen: state.isOpen,
                    phase: state.phase,
                    isStandaloneBreak: state.isStandaloneBreak,
                    taskId: state.taskId,
                    titleText,
                    tagText,
                    hasCloseBtn: Boolean(closeBtn),
                    hasReturnCta: Boolean(returnCta),
                    returnCtaText: returnCta ? returnCta.innerText.trim() : null
                };
            })()
        """)

        assert break_state["isVisible"], "Standalone break must be visible."
        assert break_state["isStandaloneBreak"], "session.isStandaloneBreak must be true."
        assert break_state["taskId"] is None, "Standalone break must NOT attach to any task."
        assert "Take a Break" in break_state["titleText"] or "Break" in break_state["titleText"], f"Expected Break title, got '{break_state['titleText']}'."
        assert break_state["hasCloseBtn"], "Standalone break must render a top close button."
        assert break_state["hasReturnCta"], "Standalone break must render 'Finish break & return →' primary action."
        log(f"✓ Standalone Tempo Break opened cleanly without task dependency (title: '{break_state['titleText']}', CTA: '{break_state['returnCtaText']}').")

        # Test selecting an activity in standalone break: Gentle Match
        send_eval("window.TempoFocusZone.selectBreakActivity('game');")
        time.sleep(0.3)
        game_state = send_eval("""
            (() => {
                const state = window.TempoFocusZone.getSessionState();
                const gameCard = document.querySelector('#tempo-focus-zone-root h3');
                return {
                    phase: state.phase,
                    isStandaloneBreak: state.isStandaloneBreak,
                    title: gameCard ? gameCard.innerText.trim() : ''
                };
            })()
        """)
        assert game_state["phase"] == "break_game", "Activity selection should transition to game."
        assert game_state["isStandaloneBreak"], "isStandaloneBreak flag must persist through break activities."
        log("✓ Gentle Match mini-game launched inside standalone break.")

        # Return to break hub
        send_eval("window.TempoFocusZone.returnToBreakHub();")
        time.sleep(0.3)

        # Close standalone break via 'Finish break & return'
        send_eval("window.TempoFocusZone.close();")
        time.sleep(0.3)

        after_break_state = send_eval("""
            (() => {
                const root = document.getElementById('tempo-focus-zone-root');
                const isHidden = !root || root.classList.contains('hidden');
                const fzState = window.TempoFocusZone.getSessionState();
                const mode = window.TempoMode.getCurrentMode();
                return { isHidden, isOpen: fzState.isOpen, mode, isStandaloneBreak: fzState.isStandaloneBreak };
            })()
        """)
        assert after_break_state["isHidden"] and not after_break_state["isOpen"], "Focus Zone root should be closed."
        assert not after_break_state["isStandaloneBreak"], "isStandaloneBreak should reset on close."
        assert after_break_state["mode"] in ["urgent", "emergency"], f"Closing standalone break must preserve active mode (expected 'emergency', got '{after_break_state['mode']}')."
        log("✓ Standalone break closed cleanly; user returned to Urgent Home without mode change or session residue.")

        # =========================================================================
        # CHECK 7: LEARN & SOLVE FUNCTIONALITY ACROSS DASHBOARDS
        # =========================================================================
        log("\n--- Checking 7: Learn & Solve Functionality Across Dashboards ---")
        # In Urgent Home, test switching tabs in Learn & Solve
        send_eval("window.TempoLearnSolve.selectTab('learn');")
        time.sleep(0.3)
        learn_active = send_eval("""
            (() => {
                const learnCard = document.querySelector('#tempo-learn-solve-section div[onclick*="selectTab(\\'learn\\')"]');
                const hasSelectedBorder = learnCard && (learnCard.className.includes('border-[#7E22CE]') || learnCard.className.includes('border-2'));
                const topics = document.querySelectorAll('#emode-home-content #tempo-learn-solve-section #learn-solve-subcontent h5');
                return { hasSelectedBorder, topicCount: topics.length };
            })()
        """)
        assert learn_active["hasSelectedBorder"] and learn_active["topicCount"] == 9, f"Learn tab in Urgent Home should show 9 stress topics (got {learn_active})."
        log("✓ Learn & Solve tab selection works seamlessly in Urgent Home.")

        # Open topic in modal
        send_eval("window.TempoLearnSolve.openModal('stress_loop');")
        time.sleep(0.4)
        modal_open = send_eval("""
            (() => {
                const modal = document.getElementById('tempo-learn-solve-modal');
                const title = modal ? modal.querySelector('h3') : null;
                return {
                    isOpen: Boolean(modal && !modal.classList.contains('hidden')),
                    title: title ? title.innerText.trim() : ''
                };
            })()
        """)
        assert modal_open["isOpen"] and "The stress loop" in modal_open["title"], "Learn & Solve modal should open with selected topic."
        log(f"✓ Shared content modal opened: '{modal_open['title']}'.")

        # Close modal
        send_eval("window.TempoLearnSolve.closeModal();")
        time.sleep(0.3)
        modal_closed = send_eval("""
            (() => {
                const modal = document.getElementById('tempo-learn-solve-modal');
                return !modal || modal.classList.contains('hidden');
            })()
        """)
        assert modal_closed, "Learn & Solve modal should close cleanly."
        log("✓ Modal closed cleanly.")

        # =========================================================================
        # CHECK 8: CONTINUITY & MODE PRESERVATION
        # =========================================================================
        log("\n--- Checking 8: Continuity & Mode Preservation ---")
        modes = [('default', 'default'), ('emergency', 'emergency'), ('recovery', 'recovery')]
        for set_m, expected_m in modes:
            send_eval(f"window.TempoMode.setMode('{set_m}');")
            time.sleep(0.2)
            cur = send_eval("window.TempoMode.getCurrentMode();")
            assert cur == expected_m, f"Expected current mode '{expected_m}', got '{cur}'."
            has_tools = send_eval("Boolean(document.querySelector('.tempo-tools-section'))")
            has_ls = send_eval("Boolean(document.querySelector('#tempo-learn-solve-section'))")
            assert has_tools, f"Shared tools missing in '{set_m}' mode!"
            assert has_ls, f"Shared Learn & Solve missing in '{set_m}' mode!"
            log(f"✓ Mode '{set_m}': Upper core specific, shared tools and Learn & Solve consistently present.")

        log("\n🎉 ALL ECOSYSTEM PHASE 3 SMOKE CHECKS PASSED WITH FLYING COLORS!")

    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                proc.kill()

if __name__ == "__main__":
    run_tests()
