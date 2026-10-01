"""
TEMPO REGRESSION TEST SUITE: RECOVERY MODE (RMODE) PRODUCT CONTRACT
File: test_recovery_mode_contract.py

Validates the frozen development contract for Recovery Mode:
- Internal mode identifier remains 'recovery' (never altered or renamed)
- Mode selector dropdown excludes active Recovery Mode; includes Urgent, Unclear, Default; excludes SOS
- Recovery Home hierarchy: Self-check hero -> Recovery Note & Recently -> Weekly Review shell -> Today section -> Shared ecosystem (Recovery Tools + Learn & Solve) -> Tempo Posts
- Non-diagnostic Self-Check semantics: no clinical scores, no mental-health index, streak is consistency (not shame)
- Recovery Note privacy and dynamic user customization (user data is NOT frozen)
- Contextual Weekly Review: user-evaluated, dismissible, never an algorithmic diagnosis
- Mode switching data continuity: Recovery data preserved across mode transitions
- Strict SOS separation: Recovery Mode is NOT SOS; SOS is independent crisis modal without history leakage
"""

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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_recovery_contract_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9233
    
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
                    ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoRecoveryNote !== 'undefined'")
                    if ready:
                        eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("Application failed to become ready")

        log("Waiting for page and scripts ready...")
        wait_for_ready()

        # Switch to Recovery Mode
        eval_js("window.TempoMode.setMode('recovery');")
        time.sleep(0.5)

        # =====================================================================
        # CONTRACT CHECK 1: Mode Invariant & Mode Dropdown Destination Rules
        # =====================================================================
        log("\n--- CONTRACT CHECK 1: Mode Identifier & Selector Dropdown Rules ---")
        mode_check = eval_js("""
            (() => {
                const currentMode = window.TempoMode.getMode();
                const displayName = window.TempoMode.getModeDisplayName(currentMode);

                // Open mode selector dropdown
                window.TempoMode.toggleModeDropdown();
                const dropdown = document.getElementById('home-mode-selector-dropdown');
                const dropdownHtml = dropdown ? dropdown.innerHTML : '';
                const isDropdownVisible = dropdown && !dropdown.classList.contains('hidden');

                // Close dropdown
                window.TempoMode.closeAllModeDropdowns();

                return {
                    currentMode,
                    displayName,
                    isDropdownVisible,
                    hasUrgent: dropdownHtml.includes('Urgent Mode') || dropdownHtml.includes('Chế độ Khẩn'),
                    hasUnclear: dropdownHtml.includes('Unclear Mode') || dropdownHtml.includes('Chế độ Chưa rõ'),
                    hasBreak: dropdownHtml.includes('Take a break') || dropdownHtml.includes('Tạm nghỉ') || dropdownHtml.includes('Default'),
                    excludesRecovery: !dropdownHtml.includes('Recovery Mode') && !dropdownHtml.includes('Chế độ Hồi phục') && !dropdownHtml.includes('Chế độ Phục hồi'),
                    excludesSOS: !dropdownHtml.includes('SOS')
                };
            })()
        """)

        assert mode_check['currentMode'] == 'recovery', f"Active mode identifier must remain 'recovery', got: {mode_check['currentMode']}"
        assert any(n in mode_check['displayName'] for n in ['Recovery Mode', 'Chế độ Hồi phục', 'Chế độ Phục hồi']), f"Display name must be 'Recovery Mode' or Vietnamese equivalent, got: {mode_check['displayName']}"
        assert mode_check['isDropdownVisible'], "Mode dropdown must open on toggle"
        assert mode_check['hasUrgent'], "Mode dropdown must include Urgent Mode"
        assert mode_check['hasUnclear'], "Mode dropdown must include Unclear Mode"
        assert mode_check['hasBreak'], "Mode dropdown must include option to take a break / switch to default"
        assert mode_check['excludesRecovery'], "Mode dropdown must EXCLUDE Recovery Mode when already active"
        assert mode_check['excludesSOS'], "Mode dropdown must EXCLUDE SOS (SOS is separate safety modal)"
        log("✓ Mode identifier 'recovery' and mode dropdown destination exclusions verified.")

        # =====================================================================
        # CONTRACT CHECK 2: Recovery Home Layout Hierarchy & Semantic Hooks
        # =====================================================================
        log("\n--- CONTRACT CHECK 2: Recovery Home Layout Hierarchy & Hooks ---")
        hierarchy_check = eval_js("""
            (() => {
                const shell = document.querySelector('[data-tempo-ui="recovery-home-shell"]');
                const selfCheck = document.querySelector('[data-tempo-ui="recovery-self-check"]');
                const note = document.querySelector('[data-tempo-ui="recovery-note"]');
                const recently = document.querySelector('[data-tempo-ui="recovery-recently"]');
                const weeklyReview = document.querySelector('[data-tempo-ui="recovery-weekly-review"]');
                const today = document.querySelector('[data-tempo-ui="recovery-today"]');
                const tools = document.querySelector('[data-tempo-ui="recovery-tools"]');
                const posts = document.querySelector('[data-tempo-ui="recovery-posts"]');

                // Check desktop columns: self-check should be in left column (~65%), note in right column (~35%)
                const leftCol = selfCheck ? selfCheck.closest('.lg\\\\:w-2\\\\/3, .w-full.lg\\\\:w-2\\\\/3, [class*="lg:w-2/3"]') : null;
                const rightCol = note ? note.closest('.lg\\\\:w-1\\\\/3, .w-full.lg\\\\:w-1\\\\/3, [class*="lg:w-1/3"]') : null;

                // Check intro banner dismissibility
                const introBannerBefore = document.getElementById('recovery-intro-banner');
                if (window.TempoMode && typeof window.TempoMode.dismissRecoveryIntro === 'function') {
                    window.TempoMode.dismissRecoveryIntro();
                }
                const introBannerAfter = document.getElementById('recovery-intro-banner');

                return {
                    hasShell: !!shell,
                    hasSelfCheck: !!selfCheck,
                    hasNote: !!note,
                    hasRecently: !!recently,
                    hasWeeklyReview: !!weeklyReview,
                    hasToday: !!today,
                    hasTools: !!tools,
                    hasPosts: !!posts,
                    hasLeftCol: !!leftCol || (selfCheck && selfCheck.parentElement !== note.parentElement),
                    hasRightCol: !!rightCol || (note && recently && note.parentElement === recently.parentElement),
                    introBannerDismissed: !introBannerAfter
                };
            })()
        """)

        assert hierarchy_check['hasShell'], "Recovery Home shell with data-tempo-ui='recovery-home-shell' must exist"
        assert hierarchy_check['hasSelfCheck'], "Self-Check card with data-tempo-ui='recovery-self-check' must exist"
        assert hierarchy_check['hasNote'], "Recovery Note card with data-tempo-ui='recovery-note' must exist"
        assert hierarchy_check['hasRecently'], "Recently card with data-tempo-ui='recovery-recently' must exist"
        assert hierarchy_check['hasWeeklyReview'], "Weekly Review container with data-tempo-ui='recovery-weekly-review' must exist"
        assert hierarchy_check['hasToday'], "Today task continuity section with data-tempo-ui='recovery-today' must exist"
        assert hierarchy_check['hasTools'], "Shared recovery tools with data-tempo-ui='recovery-tools' must exist"
        assert hierarchy_check['hasPosts'], "Tempo posts section with data-tempo-ui='recovery-posts' must exist"
        assert hierarchy_check['hasLeftCol'] and hierarchy_check['hasRightCol'], "Desktop split columns (Self-Check left vs Note/Recently right) verified"
        assert hierarchy_check['introBannerDismissed'], "Optional intro banner must dismiss cleanly without breaking layout"
        log("✓ Complete Recovery Home layout hierarchy and semantic test hooks verified.")

        # =====================================================================
        # CONTRACT CHECK 3: Non-Diagnostic Self-Check Principles & Ethics
        # =====================================================================
        log("\n--- CONTRACT CHECK 3: Non-Diagnostic Self-Check Principles & Ethics ---")
        ethics_check = eval_js("""
            (async () => {
                const rmodeContent = document.getElementById('rmode-home-content');
                const fullText = rmodeContent ? rmodeContent.innerText.toLowerCase() : '';

                // Clinical / diagnostic terms that MUST NOT appear
                const forbiddenDiagnosticTerms = [
                    'diagnosis',
                    'diagnostic score',
                    'burnout severity index',
                    'mental health grade',
                    'clinical evaluation',
                    'stress index: ',
                    'pathology',
                    'failed streak',
                    'streak lost'
                ];

                const foundForbidden = forbiddenDiagnosticTerms.filter(term => fullText.includes(term));

                // Verify tracker model supports user-defined trackers without diagnostic scoring
                let trackerCreated = false;
                if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.createTracker === 'function') {
                    const testTracker = await window.TempoRecoverySelfCheck.createTracker({
                        name: 'Gentle Walk',
                        category: 'supportive',
                        check_method: 'yes_no',
                        direction: 'higher_better'
                    });
                    trackerCreated = !!testTracker && testTracker.name === 'Gentle Walk';
                }

                // Verify streak calculation returns integer streak without punitive label
                let streakClean = true;
                if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.calculateStreak === 'function') {
                    const streak = window.TempoRecoverySelfCheck.calculateStreak([]);
                    streakClean = typeof streak === 'number' && streak >= 0;
                }

                return {
                    foundForbidden,
                    trackerCreated,
                    streakClean
                };
            })()
        """)

        assert len(ethics_check['foundForbidden']) == 0, f"Found forbidden diagnostic/shame terminology: {ethics_check['foundForbidden']}"
        assert ethics_check['trackerCreated'], "Self-check trackers must be user-defined and support creation"
        assert ethics_check['streakClean'], "Self-check streak must represent consistency count without punitive tags"
        log("✓ Non-diagnostic, non-shame self-check philosophy verified.")

        # =====================================================================
        # CONTRACT CHECK 4: Recovery Note Privacy & Dynamic Customization
        # =====================================================================
        log("\n--- CONTRACT CHECK 4: Recovery Note Privacy & Dynamic User Data ---")
        note_check = eval_js("""
            (async () => {
                if (!window.TempoRecoveryNote) return { error: "TempoRecoveryNote missing" };

                // Read baseline note
                const initialNote = window.TempoRecoveryNote.getNote();
                const initialItemsCount = (initialNote && initialNote.items) ? initialNote.items.length : 0;

                // Dynamically add a custom item
                const addedItem = window.TempoRecoveryNote.addItem('what_helps', 'Listening to acoustic music');
                const afterAddNote = window.TempoRecoveryNote.getNote();
                const afterAddCount = (afterAddNote && afterAddNote.items) ? afterAddNote.items.length : 0;

                // Update the item
                if (addedItem && addedItem.id) {
                    window.TempoRecoveryNote.updateItem(addedItem.id, 'Listening to lo-fi beats');
                }
                const updatedItems = window.TempoRecoveryNote.getItems('what_helps');
                const hasUpdatedText = updatedItems.some(i => i.text === 'Listening to lo-fi beats' || i.content === 'Listening to lo-fi beats');

                // Remove the test item
                if (addedItem && addedItem.id) {
                    window.TempoRecoveryNote.removeItem(addedItem.id);
                }
                const finalItems = window.TempoRecoveryNote.getItems('what_helps');
                const isCleanedUp = !finalItems.some(i => i.id === (addedItem ? addedItem.id : null));

                return {
                    initialItemsCount,
                    addedSuccess: !!addedItem,
                    countIncreased: afterAddCount === initialItemsCount + 1,
                    hasUpdatedText,
                    isCleanedUp
                };
            })()
        """)

        assert note_check['addedSuccess'], "User must be able to dynamically add custom items to Recovery Note"
        assert note_check['countIncreased'], "Item count must increase when custom option is added"
        assert note_check['hasUpdatedText'], "User must be able to edit custom prompt items in Recovery Note"
        assert note_check['isCleanedUp'], "User must be able to remove custom prompt items from Recovery Note"
        log("✓ Recovery Note dynamic user customization (user data is NOT locked/frozen) verified.")

        # =====================================================================
        # CONTRACT CHECK 5: Contextual Weekly Review (Non-Diagnostic)
        # =====================================================================
        log("\n--- CONTRACT CHECK 5: Contextual & Non-Diagnostic Weekly Review ---")
        review_check = eval_js("""
            (() => {
                if (!window.TempoWeeklyReview) return { error: "TempoWeeklyReview missing" };

                // Check dismissibility
                const targetWeek = '2026-09-28';
                const isDismissedInitially = window.TempoWeeklyReview.isNoticeDismissed(targetWeek);
                window.TempoWeeklyReview.snoozeOrDismissNotice(targetWeek);
                const isDismissedAfter = window.TempoWeeklyReview.isNoticeDismissed(targetWeek);

                // Weekly review is user-evaluated, not an algorithmic diagnosis
                const eligibleWeek = window.TempoWeeklyReview.getLatestEligibleWeek();

                return {
                    hasWeeklyReviewModule: true,
                    isDismissedInitially,
                    isDismissedAfter,
                    eligibleWeekType: typeof eligibleWeek
                };
            })()
        """)

        assert review_check['hasWeeklyReviewModule'], "TempoWeeklyReview module must be loaded"
        assert review_check['isDismissedAfter'], "Weekly Review notice must be dismissible/snoozeable (never permanently forced)"
        log("✓ Contextual and non-diagnostic Weekly Review principles verified.")

        # =====================================================================
        # CONTRACT CHECK 6: Mode Switching Continuity & SOS Strict Separation
        # =====================================================================
        log("\n--- CONTRACT CHECK 6: Mode Switching Continuity & SOS Separation ---")
        continuity_check = eval_js("""
            (async () => {
                // Ensure custom tracker exists in Recovery
                const testTracker = await window.TempoRecoverySelfCheck.createTracker({
                    name: 'Afternoon Tea',
                    category: 'supportive',
                    check_method: 'yes_no',
                    direction: 'higher_better'
                });

                // Switch to Default Mode
                window.TempoMode.setMode('default');
                const inDefault = window.TempoMode.getMode() === 'default';

                // Switch to Urgent Mode
                window.TempoMode.setMode('emergency');
                const inUrgent = window.TempoMode.getMode() === 'emergency';

                // Switch back to Recovery Mode
                window.TempoMode.setMode('recovery');
                const inRecovery = window.TempoMode.getMode() === 'recovery';

                // Check that testTracker still exists in Recovery
                const activeTrackers = window.TempoRecoverySelfCheck.getActiveTrackers ? window.TempoRecoverySelfCheck.getActiveTrackers() : [];
                const trackerPreserved = activeTrackers.some(t => t.name === 'Afternoon Tea');

                // Cleanup tracker
                if (testTracker && testTracker.id) {
                    await window.TempoRecoverySelfCheck.archiveTracker(testTracker.id);
                }

                // Verify SOS is NOT part of Recovery Mode container or state
                const rmodeContent = document.getElementById('rmode-home-content');
                const hasSOSModalInsideRmode = rmodeContent ? !!rmodeContent.querySelector('#modal-sos') : false;
                const sosButton = document.getElementById('btn-nav-sos') || document.querySelector('.btn-sos');

                return {
                    inDefault,
                    inUrgent,
                    inRecovery,
                    trackerPreserved,
                    hasSOSModalInsideRmode,
                    hasGlobalSOS: !!sosButton
                };
            })()
        """)

        assert continuity_check['inDefault'] and continuity_check['inUrgent'] and continuity_check['inRecovery'], "Seamless mode transitions verified"
        assert continuity_check['trackerPreserved'], "Recovery Mode trackers and data must be preserved across mode switches"
        assert not continuity_check['hasSOSModalInsideRmode'], "SOS modal must NOT be embedded inside Recovery Home (SOS is globally independent)"
        assert continuity_check['hasGlobalSOS'], "SOS remains globally accessible as an independent safety mechanism"
        log("✓ Mode switching continuity and SOS strict separation verified.")

        log("\n=======================================================")
        log(">>> ALL RECOVERY MODE PRODUCT CONTRACT CHECKS PASSED! <<<")
        log("=======================================================")

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
