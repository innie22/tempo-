import subprocess
import time
import json
import urllib.request
import tempfile
import os
import websocket
import sys

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_contract_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9260
    
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
            res = send_command("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
            if "exceptionDetails" in res:
                raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        # Wait for app readiness
        log("Waiting for app and TempoMode to initialize...")
        for _ in range(30):
            ready = eval_js("Boolean(window.TempoMode && window.TempoAuth && window.TempoApp)")
            if ready:
                break
            time.sleep(0.5)

        # Clear any initial state for pristine contract testing
        eval_js("""
            (() => {
                localStorage.clear();
                sessionStorage.clear();
                if (window.TempoAuth && typeof window.TempoAuth.signOut === 'function') {
                    window.TempoAuth.signOut();
                }
                window.location.reload();
            })()
        """)
        time.sleep(1.5)

        # Reconnect after reload
        log("Reconnecting after clean reload...")
        if ws:
            try: ws.close()
            except Exception: pass
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
        ws = websocket.create_connection(ws_url)

        for _ in range(30):
            ready = eval_js("Boolean(window.TempoMode && window.TempoAuth && window.TempoApp)")
            if ready:
                break
            time.sleep(0.5)

        log("\n=======================================================")
        log("STARTING TEMPO MODE LOGIC CONTRACT VERIFICATION")
        log("=======================================================\n")

        # ---------------------------------------------------------------------
        # POINT 1: Entry Home activeContext = null
        # ---------------------------------------------------------------------
        log("--- CHECK 1: Entry Home activeContext = null ---")
        state_guest = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    hasActiveContext: window.TempoMode.hasActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    hasIndicator: Boolean(document.getElementById('header-mode-indicator')),
                    dmodeVisible: !document.getElementById('dmode-home-content').classList.contains('hidden')
                };
            })()
        """)
        assert state_guest["activeContext"] is None, f"Expected activeContext=None, got {state_guest['activeContext']}"
        assert state_guest["hasActiveContext"] is False, "Expected hasActiveContext=False"
        assert state_guest["sourceContext"] == 'entry', f"Expected sourceContext='entry', got {state_guest['sourceContext']}"
        assert state_guest["hasIndicator"] is False, "Active mode indicator should not be visible on Entry Home"
        assert state_guest["dmodeVisible"] is True, "dmode-home-content should be visible for Entry Home"
        log("✓ Guest user starts at Entry Home with activeContext = null, sourceContext = 'entry'.")

        # Sign in a new user with NO established context
        eval_js("""
            (async () => {
                await window.TempoAuth.register('new_user_no_context@test.edu', 'secret123');
                await window.TempoAuth.signIn('new_user_no_context@test.edu', 'secret123');
            })()
        """)
        time.sleep(0.5)
        state_new_auth = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    hasActiveContext: window.TempoMode.hasActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext()
                };
            })()
        """)
        assert state_new_auth["activeContext"] is None, f"Authenticated user with no context should have activeContext=None, got {state_new_auth['activeContext']}"
        assert state_new_auth["hasActiveContext"] is False, "hasActiveContext should be False"
        log("✓ Authenticated user with no established context also has activeContext = null.")

        # ---------------------------------------------------------------------
        # POINT 2: Urmode sets activeContext = emergency
        # ---------------------------------------------------------------------
        log("\n--- CHECK 2: Urmode sets activeContext = emergency ---")
        eval_js("window.TempoMode.transitionContext('emergency');")
        time.sleep(0.3)
        state_urmode = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    hasActiveContext: window.TempoMode.hasActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    emodeVisible: !document.getElementById('emode-home-content').classList.contains('hidden')
                };
            })()
        """)
        assert state_urmode["activeContext"] == 'emergency', f"Expected activeContext='emergency', got {state_urmode['activeContext']}"
        assert state_urmode["hasActiveContext"] is True, "Expected hasActiveContext=True"
        assert state_urmode["sourceContext"] == 'emergency', f"Expected sourceContext='emergency', got {state_urmode['sourceContext']}"
        assert state_urmode["emodeVisible"] is True, "Urgent home view must be visible"
        log("✓ Urmode sets activeContext = 'emergency', sourceContext = 'emergency'.")

        # ---------------------------------------------------------------------
        # POINT 3: Rmode sets activeContext = recovery
        # ---------------------------------------------------------------------
        log("\n--- CHECK 3: Rmode sets activeContext = recovery ---")
        eval_js("window.TempoMode.transitionContext('recovery');")
        time.sleep(0.3)
        state_rmode = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    hasActiveContext: window.TempoMode.hasActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    rmodeVisible: !document.getElementById('rmode-home-content').classList.contains('hidden')
                };
            })()
        """)
        assert state_rmode["activeContext"] == 'recovery', f"Expected activeContext='recovery', got {state_rmode['activeContext']}"
        assert state_rmode["hasActiveContext"] is True, "Expected hasActiveContext=True"
        assert state_rmode["sourceContext"] == 'recovery', f"Expected sourceContext='recovery', got {state_rmode['sourceContext']}"
        assert state_rmode["rmodeVisible"] is True, "Recovery home view must be visible"
        log("✓ Rmode sets activeContext = 'recovery', sourceContext = 'recovery'.")

        # ---------------------------------------------------------------------
        # POINT 4: Entry -> Ucheck preserves sourceContext = entry, activeContext = null
        # ---------------------------------------------------------------------
        log("\n--- CHECK 4: Entry -> Ucheck preserves sourceContext = entry, activeContext = null ---")
        # Reset to Entry Home
        eval_js("window.TempoMode.transitionContext(null);")
        time.sleep(0.2)
        assert eval_js("window.TempoMode.getActiveContext()") is None

        # Open Ucheck from Entry Home
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'entry' });")
        time.sleep(0.3)
        state_ucheck_entry = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool(),
                    getMode: window.TempoMode.getMode(),
                    umodeVisible: !document.getElementById('umode-home-content').classList.contains('hidden')
                };
            })()
        """)
        assert state_ucheck_entry["activeContext"] is None, f"activeContext must remain None when opening Ucheck, got {state_ucheck_entry['activeContext']}"
        assert state_ucheck_entry["sourceContext"] == 'entry', f"sourceContext must be 'entry', got {state_ucheck_entry['sourceContext']}"
        assert state_ucheck_entry["activeSharedTool"] == 'ucheck', "activeSharedTool must be 'ucheck'"
        assert state_ucheck_entry["getMode"] == 'unclear', "getMode() returns 'unclear' for tool display compatibility"
        assert state_ucheck_entry["umodeVisible"] is True, "Ucheck assessment view must be visible"
        log("✓ Opening Ucheck from Entry preserves sourceContext = 'entry', activeContext = null.")

        # ---------------------------------------------------------------------
        # POINT 5: Urmode -> Ucheck preserves sourceContext = emergency, activeContext = emergency
        # ---------------------------------------------------------------------
        log("\n--- CHECK 5: Urmode -> Ucheck preserves sourceContext = emergency, activeContext = emergency ---")
        eval_js("window.TempoMode.transitionContext('emergency');")
        time.sleep(0.2)
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'emergency' });")
        time.sleep(0.3)
        state_ucheck_urmode = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool()
                };
            })()
        """)
        assert state_ucheck_urmode["activeContext"] == 'emergency', f"activeContext must remain 'emergency', got {state_ucheck_urmode['activeContext']}"
        assert state_ucheck_urmode["sourceContext"] == 'emergency', f"sourceContext must be 'emergency', got {state_ucheck_urmode['sourceContext']}"
        assert state_ucheck_urmode["activeSharedTool"] == 'ucheck', "activeSharedTool must be 'ucheck'"
        log("✓ Opening Ucheck from Urmode preserves sourceContext = 'emergency', activeContext = 'emergency'.")

        # ---------------------------------------------------------------------
        # POINT 6: Rmode -> Ucheck preserves sourceContext = recovery, activeContext = recovery
        # ---------------------------------------------------------------------
        log("\n--- CHECK 6: Rmode -> Ucheck preserves sourceContext = recovery, activeContext = recovery ---")
        eval_js("window.TempoMode.transitionContext('recovery');")
        time.sleep(0.2)
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'recovery' });")
        time.sleep(0.3)
        state_ucheck_rmode = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool()
                };
            })()
        """)
        assert state_ucheck_rmode["activeContext"] == 'recovery', f"activeContext must remain 'recovery', got {state_ucheck_rmode['activeContext']}"
        assert state_ucheck_rmode["sourceContext"] == 'recovery', f"sourceContext must be 'recovery', got {state_ucheck_rmode['sourceContext']}"
        assert state_ucheck_rmode["activeSharedTool"] == 'ucheck', "activeSharedTool must be 'ucheck'"
        log("✓ Opening Ucheck from Rmode preserves sourceContext = 'recovery', activeContext = 'recovery'.")

        # ---------------------------------------------------------------------
        # POINT 7: Exiting Ucheck returns to exact source context
        # ---------------------------------------------------------------------
        log("\n--- CHECK 7: Exiting Ucheck returns to exact source context ---")
        # 7a: Return to Entry Home
        eval_js("window.TempoMode.transitionContext(null);")
        time.sleep(0.1)
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'entry' });")
        time.sleep(0.2)
        eval_js("window.TempoMode.returnToSourceContext();")
        time.sleep(0.3)
        res_entry = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool(),
                    dmodeVisible: !document.getElementById('dmode-home-content').classList.contains('hidden')
                };
            })()
        """)
        assert res_entry["activeContext"] is None, "Exiting Ucheck opened from Entry must return to activeContext = null"
        assert res_entry["activeSharedTool"] is None, "activeSharedTool must be cleared"
        assert res_entry["dmodeVisible"] is True, "Entry Home must be visible"
        log("✓ Exiting Ucheck opened from Entry returns to Entry Home.")

        # 7b: Return to Urmode Dashboard
        eval_js("window.TempoMode.transitionContext('emergency');")
        time.sleep(0.1)
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'emergency' });")
        time.sleep(0.2)
        eval_js("window.TempoMode.returnToSourceContext();")
        time.sleep(0.3)
        res_urmode = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    emodeVisible: !document.getElementById('emode-home-content').classList.contains('hidden')
                };
            })()
        """)
        assert res_urmode["activeContext"] == 'emergency', "Exiting Ucheck opened from Urmode must return to activeContext = 'emergency'"
        assert res_urmode["emodeVisible"] is True, "Urgent Home dashboard must be visible"
        log("✓ Exiting Ucheck opened from Urmode returns to Urmode Dashboard.")

        # 7c: Return to Rmode Dashboard
        eval_js("window.TempoMode.transitionContext('recovery');")
        time.sleep(0.1)
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'recovery' });")
        time.sleep(0.2)
        eval_js("window.TempoMode.returnToSourceContext();")
        time.sleep(0.3)
        res_rmode = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    rmodeVisible: !document.getElementById('rmode-home-content').classList.contains('hidden')
                };
            })()
        """)
        assert res_rmode["activeContext"] == 'recovery', "Exiting Ucheck opened from Rmode must return to activeContext = 'recovery'"
        assert res_rmode["rmodeVisible"] is True, "Recovery Home dashboard must be visible"
        log("✓ Exiting Ucheck opened from Rmode returns to Rmode Dashboard.")

        # ---------------------------------------------------------------------
        # POINT 8: Completing Ucheck does not automatically change activeContext
        # ---------------------------------------------------------------------
        log("\n--- CHECK 8: Completing Ucheck does not automatically change activeContext ---")
        eval_js("window.TempoMode.transitionContext(null);")
        time.sleep(0.1)
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'entry', startNew: true });")
        time.sleep(0.3)

        # Walk through stages 1 to 4 to reach Stage 5 completion
        eval_js("""
            (() => {
                window.TempoUnclearMode.toggleConcern('Deadline is too close');
                window.TempoUnclearMode.submitStage1();
                window.TempoUnclearMode.toggleFeeling('Overwhelmed');
                window.TempoUnclearMode.submitStage2();
                window.TempoUnclearMode.setImpactLevel('high');
                window.TempoUnclearMode.submitStage3();
                window.TempoUnclearMode.toggleBroadNeed('handle');
                window.TempoUnclearMode.submitStage4();
            })()
        """)
        time.sleep(0.4)

        stage5_state = eval_js("""
            (() => {
                const draft = window.TempoUnclearMode.getDraft();
                return {
                    stage: draft ? draft.current_stage : null,
                    activeContext: window.TempoMode.getActiveContext(),
                    isStage5Content: Boolean(document.querySelector('button[onclick*="chooseDirection"]'))
                };
            })()
        """)
        assert stage5_state["stage"] == 5, f"Expected Stage 5, got {stage5_state['stage']}"
        assert stage5_state["activeContext"] is None, f"activeContext must remain None upon completing Ucheck, got {stage5_state['activeContext']}"
        assert stage5_state["isStage5Content"] is True, "Stage 5 recommendation screen rendered"
        log("✓ Completed Ucheck presents recommendation without automatically changing activeContext.")

        # ---------------------------------------------------------------------
        # POINT 9: Selecting Urmode from result transitions to emergency
        # ---------------------------------------------------------------------
        log("\n--- CHECK 9: Selecting Urmode from result transitions to emergency ---")
        eval_js("window.TempoUnclearMode.chooseDirection('urgent');")
        time.sleep(0.3)
        context_after_urgent = eval_js("window.TempoMode.getActiveContext()")
        assert context_after_urgent == 'emergency', f"Expected activeContext='emergency', got {context_after_urgent}"
        log("✓ Selecting Urmode explicitly transitions activeContext to 'emergency'.")

        # ---------------------------------------------------------------------
        # POINT 10: Selecting Rmode from result transitions to recovery
        # ---------------------------------------------------------------------
        log("\n--- CHECK 10: Selecting Rmode from result transitions to recovery ---")
        eval_js("window.TempoMode.transitionContext(null);")
        time.sleep(0.1)
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'entry', startNew: true });")
        time.sleep(0.3)
        eval_js("""
            (() => {
                window.TempoUnclearMode.toggleConcern('Feeling exhausted');
                window.TempoUnclearMode.submitStage1();
                window.TempoUnclearMode.toggleFeeling('Tired');
                window.TempoUnclearMode.submitStage2();
                window.TempoUnclearMode.setImpactLevel('medium');
                window.TempoUnclearMode.submitStage3();
                window.TempoUnclearMode.toggleBroadNeed('room');
                window.TempoUnclearMode.submitStage4();
            })()
        """)
        time.sleep(0.4)
        eval_js("window.TempoUnclearMode.chooseDirection('recovery');")
        time.sleep(0.3)
        context_after_recovery = eval_js("window.TempoMode.getActiveContext()")
        assert context_after_recovery == 'recovery', f"Expected activeContext='recovery', got {context_after_recovery}"
        log("✓ Selecting Rmode explicitly transitions activeContext to 'recovery'.")

        # ---------------------------------------------------------------------
        # POINT 11: Incomplete Ucheck can be resumed or a new one started
        # ---------------------------------------------------------------------
        log("\n--- CHECK 11: Incomplete Ucheck resumption and multi-draft retention ---")
        eval_js("window.TempoMode.transitionContext(null);")
        time.sleep(0.1)
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'entry', startNew: true });")
        time.sleep(0.3)

        # Set stage 1 and do not complete
        eval_js("""
            (() => {
                window.TempoUnclearMode.toggleConcern('Incomplete Draft 1');
                window.TempoUnclearMode.submitStage1();
            })()
        """)
        time.sleep(0.2)
        draft1_id = eval_js("window.TempoUnclearMode.getDraft().id")

        # Start another new check-in
        eval_js("window.TempoUnclearMode.startNewCheckIn();")
        time.sleep(0.2)
        draft2_id = eval_js("window.TempoUnclearMode.getDraft().id")
        assert draft1_id != draft2_id, "New check-in should have unique id"

        incomplete_list = eval_js("window.TempoUnclearMode.getIncompleteVersions()")
        assert len(incomplete_list) >= 2, f"Expected at least 2 incomplete drafts preserved, found {len(incomplete_list)}"
        has_draft1 = any(d.get("id") == draft1_id for d in incomplete_list)
        assert has_draft1, "Draft 1 was erroneously auto-deleted"

        # Resume Draft 1
        eval_js(f"window.TempoUnclearMode.resumeDraft('{draft1_id}');")
        time.sleep(0.2)
        resumed_id = eval_js("window.TempoUnclearMode.getDraft().id")
        assert resumed_id == draft1_id, f"Expected resumed draft {draft1_id}, got {resumed_id}"
        log("✓ Incomplete Uchecks are preserved and can be selected / resumed independently.")

        # ---------------------------------------------------------------------
        # POINT 12: Completed Ucheck adjustment creates versioned V2 leaving V1 intact
        # ---------------------------------------------------------------------
        log("\n--- CHECK 12: Completed Ucheck adjustment creates versioned V2 leaving V1 intact ---")
        # Start fresh V1 check-in for isolation
        eval_js("""
            (() => {
                const uid = window.TempoAuth.getCurrentUserId();
                localStorage.removeItem(`tempo_ucheck_versions_${uid}`);
                window.TempoUnclearMode.clearDraft();
                window.TempoUnclearMode.startNewCheckIn();
                window.TempoUnclearMode.toggleConcern('Initial V1 Check');
                window.TempoUnclearMode.submitStage1();
                window.TempoUnclearMode.goToStage(4);
                window.TempoUnclearMode.toggleBroadNeed('handle');
                window.TempoUnclearMode.submitStage4();
                window.TempoUnclearMode.chooseDirection('unclear');
            })()
        """)
        time.sleep(0.3)

        completed_versions = eval_js("window.TempoUnclearMode.getCompletedVersions()")
        v1 = completed_versions[0]
        v1_id = v1["id"]
        v1_ver = v1["version"]
        assert v1["status"] == 'completed', "V1 should be completed"

        # Now Adjust completed check
        eval_js(f"window.TempoUnclearMode.adjustCompletedCheckIn('{v1_id}');")
        time.sleep(0.3)

        active_draft = eval_js("window.TempoUnclearMode.getDraft()")
        assert active_draft["id"] != v1_id, "Adjusted draft must have a new distinct id"
        assert active_draft["parent_version_id"] == v1_id, f"Expected parent_version_id={v1_id}, got {active_draft['parent_version_id']}"
        assert active_draft["version"] == v1_ver + 1, f"Expected version {v1_ver + 1}, got {active_draft['version']}"
        assert active_draft["status"] == 'in_progress', "Adjusted draft should be in_progress"

        # Verify original V1 remains in storage completely unchanged
        all_completed_now = eval_js("window.TempoUnclearMode.getCompletedVersions()")
        v1_check = next((c for c in all_completed_now if c["id"] == v1_id), None)
        assert v1_check is not None, "Original V1 was missing from completed versions!"
        assert v1_check["status"] == 'completed', "Original V1 status should remain completed"
        assert v1_check["version"] == v1_ver, f"Original V1 version should remain {v1_ver}"
        log("✓ Adjusting completed Ucheck creates V(N+1) with parent reference while preserving V(N) intact.")

        # ---------------------------------------------------------------------
        # POINT 13: Accessing Wplan as guest triggers auth; login resumes Wplan without forcing Urmode
        # ---------------------------------------------------------------------
        log("\n--- CHECK 13: Guest Wplan access sets pendingIntent and resumes tool upon login without forcing Urmode ---")
        eval_js("""
            (async () => {
                if (window.TempoAuth && typeof window.TempoAuth.signOut === 'function') {
                    await window.TempoAuth.signOut();
                }
            })()
        """)
        time.sleep(0.5)

        # As guest, attempt to navigate to Wplan
        eval_js("window.TempoApp.navigateTo('plan-workspace');")
        time.sleep(0.3)

        intent_data = eval_js("""
            (() => {
                return {
                    pendingIntent: window.TempoMode.getPendingIntent(),
                    activeContext: window.TempoMode.getActiveContext(),
                    modalOpen: !document.getElementById('modal-signin').classList.contains('hidden')
                };
            })()
        """)
        assert intent_data["pendingIntent"] is not None, "Pending intent must be set for guest Wplan access"
        assert intent_data["pendingIntent"]["type"] == 'tool', f"Expected intent.type='tool', got {intent_data['pendingIntent']['type']}"
        assert intent_data["pendingIntent"]["destination"] == 'plan-workspace', "Expected destination='plan-workspace'"
        assert intent_data["activeContext"] is None, "activeContext must remain None"
        assert intent_data["modalOpen"] is True, "Sign-in modal must open for guest access to Type B tool"

        # Sign in guest user to fulfill pendingIntent
        eval_js("""
            (async () => {
                await window.TempoAuth.register('wplan_guest_user@test.edu', 'secret123');
                await window.TempoAuth.signIn('wplan_guest_user@test.edu', 'secret123');
            })()
        """)
        time.sleep(0.6)

        auth_resume_state = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    currentTab: window.TempoApp ? window.TempoApp.getCurrentTab() : null,
                    pendingIntent: window.TempoMode.getPendingIntent()
                };
            })()
        """)
        assert auth_resume_state["activeContext"] is None, f"Login to resume Wplan must NOT force emergency mode, got {auth_resume_state['activeContext']}"
        assert auth_resume_state["currentTab"] == 'plan-workspace', f"Expected currentTab='plan-workspace', got {auth_resume_state['currentTab']}"
        assert auth_resume_state["pendingIntent"] is None, "Pending intent must be cleared after fulfillment"
        log("✓ Guest Wplan access gates auth, logs in, resumes Wplan, and does NOT force activeContext = 'emergency'.")

        # ---------------------------------------------------------------------
        # POINT 14: Login with existing plan does NOT force emergency
        # ---------------------------------------------------------------------
        log("\n--- CHECK 14: Login with existing plan does not force emergency ---")
        # Save a confirmed emergency plan for this user in TempoPlanStore
        eval_js("""
            (async () => {
                const uid = window.TempoAuth.getCurrentUserId();
                const dummyPlan = {
                    id: 'plan_contract_test_1',
                    planId: 'plan_contract_test_1',
                    planType: 'emergency',
                    status: 'active',
                    tasks: [{ id: 't1', name: 'Study Task', priorityCategory: 'DO_FIRST', durationLabel: '45 min' }],
                    plannedTasks: [{ taskId: 't1', task: { id: 't1', name: 'Study Task', priorityCategory: 'DO_FIRST', durationLabel: '45 min' }, dayDate: '2026-10-06' }]
                };
                if (window.TempoPlanStore) {
                    await window.TempoPlanStore.saveActivePlan('emergency', dummyPlan);
                }
                // Ensure user has NO established context
                localStorage.removeItem('tempo_user_established_context_' + uid);
                localStorage.removeItem('tempo_established_context');
                localStorage.removeItem('tempo_current_mode');
                
                // Sign out and re-authenticate
                window.TempoAuth.signOut();
                await window.TempoAuth.signIn('wplan_guest_user@test.edu', 'secret123');
            })()
        """)
        time.sleep(1.0)

        plan_auth_state = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    hasActiveContext: window.TempoMode.hasActiveContext(),
                    hasPlan: window.TempoPlanStore && window.TempoPlanStore.hasActivePlan('emergency')
                };
            })()
        """)
        assert plan_auth_state["hasPlan"] is True, "Plan should be present in store"
        assert plan_auth_state["activeContext"] is None, f"Login with existing plan must NOT force emergency, got {plan_auth_state['activeContext']}"
        assert plan_auth_state["hasActiveContext"] is False, "hasActiveContext must remain False"
        log("✓ Login with existing plan keeps activeContext = null when no established context was explicitly chosen.")

        # ---------------------------------------------------------------------
        # POINT 15: Logout preserves last established context; Login restores it
        # ---------------------------------------------------------------------
        log("\n--- CHECK 15: Logout preserves last established active context; Login resumes it ---")
        
        # 15a: Urmode -> Logout -> Login -> Urmode
        log("Testing 15a: Urmode -> Logout -> Login -> Urmode...")
        eval_js("""
            (async () => {
                await window.TempoAuth.register('user_restore_urmode@test.edu', 'pass123');
                await window.TempoAuth.signIn('user_restore_urmode@test.edu', 'pass123');
                window.TempoMode.transitionContext('emergency');
            })()
        """)
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getActiveContext()") == 'emergency'
        
        # Logout
        eval_js("(async () => { await window.TempoAuth.signOut(); })()")
        time.sleep(0.5)
        # Immediately logged out guest is at Entry Home
        assert eval_js("window.TempoMode.getActiveContext()") is None
        
        # Log back in
        eval_js("""
            (async () => {
                await window.TempoAuth.signIn('user_restore_urmode@test.edu', 'pass123');
            })()
        """)
        time.sleep(0.5)
        state_15a = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    emodeVisible: !document.getElementById('emode-home-content').classList.contains('hidden')
                };
            })()
        """)
        assert state_15a["activeContext"] == 'emergency', f"Expected activeContext='emergency', got {state_15a['activeContext']}"
        assert state_15a["emodeVisible"] is True, "Expected Urgent Home visible after re-login"
        log("✓ 15a PASSED: Urmode preserved across logout and restored on login.")

        # 15b: Rmode -> Logout -> Login -> Rmode
        log("Testing 15b: Rmode -> Logout -> Login -> Rmode...")
        eval_js("""
            (async () => {
                await window.TempoAuth.register('user_restore_rmode@test.edu', 'pass123');
                await window.TempoAuth.signIn('user_restore_rmode@test.edu', 'pass123');
                window.TempoMode.transitionContext('recovery');
            })()
        """)
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getActiveContext()") == 'recovery'
        
        # Logout
        eval_js("(async () => { await window.TempoAuth.signOut(); })()")
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getActiveContext()") is None
        
        # Log back in
        eval_js("""
            (async () => {
                await window.TempoAuth.signIn('user_restore_rmode@test.edu', 'pass123');
            })()
        """)
        time.sleep(0.5)
        state_15b = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    rmodeVisible: !document.getElementById('rmode-home-content').classList.contains('hidden')
                };
            })()
        """)
        assert state_15b["activeContext"] == 'recovery', f"Expected activeContext='recovery', got {state_15b['activeContext']}"
        assert state_15b["rmodeVisible"] is True, "Expected Recovery Home visible after re-login"
        log("✓ 15b PASSED: Rmode preserved across logout and restored on login.")

        # 15c: Entry with no established context -> Logout -> Login -> Entry
        log("Testing 15c: Entry with no established context -> Logout -> Login -> Entry...")
        eval_js("(async () => { await window.TempoAuth.signOut(); })()")
        time.sleep(0.5)
        eval_js("""
            (async () => {
                await window.TempoAuth.register('user_restore_entry@test.edu', 'pass123');
                await window.TempoAuth.signIn('user_restore_entry@test.edu', 'pass123');
            })()
        """)
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getActiveContext()") is None
        
        # Logout
        eval_js("(async () => { await window.TempoAuth.signOut(); })()")
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getActiveContext()") is None
        
        # Log back in
        eval_js("""
            (async () => {
                await window.TempoAuth.signIn('user_restore_entry@test.edu', 'pass123');
            })()
        """)
        time.sleep(0.5)
        state_15c = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    dmodeVisible: !document.getElementById('dmode-home-content').classList.contains('hidden')
                };
            })()
        """)
        assert state_15c["activeContext"] is None, f"Expected activeContext=None, got {state_15c['activeContext']}"
        assert state_15c["dmodeVisible"] is True, "Expected Entry Home visible after re-login"
        log("✓ 15c PASSED: Entry Home with no established context preserved across logout and restored on login.")

        # 15d: Ucheck does NOT become the restored context
        log("Testing 15d: Ucheck does NOT become the restored context...")
        eval_js("""
            (async () => {
                await window.TempoAuth.signIn('user_restore_urmode@test.edu', 'pass123');
                window.TempoMode.openUcheck({ sourceContext: 'emergency' });
            })()
        """)
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getActiveSharedTool()") == 'ucheck'
        
        # Logout while in Ucheck
        eval_js("(async () => { await window.TempoAuth.signOut(); })()")
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getActiveContext()") is None
        assert eval_js("window.TempoMode.getActiveSharedTool()") is None
        
        # Log back in: must resume Urmode (activeContext = 'emergency'), NOT Ucheck
        eval_js("""
            (async () => {
                await window.TempoAuth.signIn('user_restore_urmode@test.edu', 'pass123');
            })()
        """)
        time.sleep(0.5)
        state_15d = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool(),
                    emodeVisible: !document.getElementById('emode-home-content').classList.contains('hidden'),
                    umodeVisible: !document.getElementById('umode-home-content').classList.contains('hidden')
                };
            })()
        """)
        assert state_15d["activeContext"] == 'emergency', f"Expected activeContext='emergency', got {state_15d['activeContext']}"
        assert state_15d["activeSharedTool"] is None, "activeSharedTool must be null (Ucheck must NOT be restored)"
        assert state_15d["emodeVisible"] is True, "Expected Urgent Home visible, not Ucheck"
        assert state_15d["umodeVisible"] is False, "Ucheck must NOT be visible"
        log("✓ 15d PASSED: Ucheck never becomes the restored context; user resumes Urmode.")

        # 15e: Ucheck flows continuity: Urmode -> Ucheck -> complete -> select Rmode -> Logout -> Login -> Rmode
        log("Testing 15e: Urmode -> Ucheck -> select Rmode -> Logout -> Login -> Rmode...")
        eval_js("""
            (async () => {
                window.TempoMode.openUcheck({ sourceContext: 'emergency', startNew: true });
                window.TempoUnclearMode.toggleConcern('Exhaustion');
                window.TempoUnclearMode.submitStage1();
                window.TempoUnclearMode.goToStage(4);
                window.TempoUnclearMode.toggleBroadNeed('room');
                window.TempoUnclearMode.submitStage4();
                window.TempoUnclearMode.chooseDirection('recovery');
            })()
        """)
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getActiveContext()") == 'recovery'
        
        # Logout
        eval_js("(async () => { await window.TempoAuth.signOut(); })()")
        time.sleep(0.5)
        
        # Login
        eval_js("""
            (async () => {
                await window.TempoAuth.signIn('user_restore_urmode@test.edu', 'pass123');
            })()
        """)
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getActiveContext()") == 'recovery'
        assert eval_js("!document.getElementById('rmode-home-content').classList.contains('hidden')") is True
        log("✓ 15e PASSED: Mode chosen from Ucheck result properly becomes new established context across logout/login.")

        log("\n=======================================================")
        log("🎉 ALL 15 TEMPO MODE LOGIC CONTRACT CHECKS PASSED (100%)!")
        log("=======================================================\n")

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
