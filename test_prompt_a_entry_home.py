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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_prompt_a_")
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
        # Wait for CDP endpoint
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
            for _ in range(40):
                try:
                    ready = eval_js("document.readyState === 'complete' && typeof window.TempoI18n !== 'undefined' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined'")
                    if ready:
                        return True
                except Exception:
                    pass
                time.sleep(0.2)
            raise RuntimeError("Timed out waiting for page/scripts to be ready")

        wait_for_ready()

        # =====================================================================
        # TEST A: Anonymous -> Entry Home
        # =====================================================================
        log("\n--- TEST A: Anonymous -> Entry Home ---")
        eval_js("""(() => {
            localStorage.clear();
            if (window.TempoPlanStore) window.TempoPlanStore.clearInMemoryCache();
            if (window.TempoMode) {
                window.TempoMode.init();
            }
        })()""")
        time.sleep(0.5)

        test_a = eval_js("""(() => {
            const mode = window.TempoMode.getMode();
            const dmodeBox = document.getElementById('dmode-home-content');
            const emodeBox = document.getElementById('emode-home-content');
            const rmodeBox = document.getElementById('rmode-home-content');
            const modeShell = document.getElementById('mode-indicator-shell');
            const primaryCard = document.querySelector('[data-tempo-ui="entry-card-primary"]');
            const communityPanel = document.querySelector('[data-tempo-ui="entry-community-panel"]');
            const quickTools = document.querySelector('[data-tempo-ui="entry-quick-tools"]');
            
            return {
                mode,
                dmodeVisible: dmodeBox && !dmodeBox.classList.contains('hidden'),
                emodeHidden: emodeBox && emodeBox.classList.contains('hidden'),
                rmodeHidden: rmodeBox && rmodeBox.classList.contains('hidden'),
                modeShellHidden: modeShell && modeShell.classList.contains('hidden'),
                hasPrimaryCard: !!primaryCard,
                hasCommunityPanel: !!communityPanel,
                hasQuickTools: !!quickTools
            };
        })()""")

        assert test_a["mode"] == "default", f"Anonymous mode must be 'default', got: {test_a['mode']}"
        assert test_a["dmodeVisible"], "dmode-home-content must be visible for anonymous user"
        assert test_a["emodeHidden"] and test_a["rmodeHidden"], "Other modes must be hidden"
        assert test_a["modeShellHidden"], "Mode indicator badge shell must be hidden on Entry Home (no mode badge)"
        assert test_a["hasPrimaryCard"], "Primary Entry card must exist"
        assert test_a["hasCommunityPanel"], "Community panel must exist"
        assert test_a["hasQuickTools"], "Quick tools must exist"
        log("✓ TEST A PASSED: Anonymous user routes directly to Entry Home with no mode badge.")

        # =====================================================================
        # TEST B: New authenticated / no-context account -> Entry Home
        # =====================================================================
        log("\n--- TEST B: New authenticated / no-context account -> Entry Home ---")
        test_b = eval_js("""(() => {
            // Simulate newly authenticated user with no established context
            const mockUser = { id: 'new-user-123', email: 'newstudent@example.com' };
            const mockProfile = { id: 'new-user-123', email: 'newstudent@example.com', display_name: 'Minh', role: 'student' };
            
            // Set current user on TempoAuth mock or state
            if (window.TempoAuth) {
                window.TempoAuth._mockUser = mockUser;
                window.TempoAuth._mockProfile = mockProfile;
            }
            
            const hasContext = window.TempoMode.hasEstablishedContext();
            window.TempoMode.init();
            
            const mode = window.TempoMode.getMode();
            const dmodeBox = document.getElementById('dmode-home-content');
            const primaryCard = document.querySelector('[data-tempo-ui="entry-card-primary"]');
            const text = dmodeBox ? dmodeBox.textContent : '';
            
            return {
                hasContext,
                mode,
                dmodeVisible: dmodeBox && !dmodeBox.classList.contains('hidden'),
                hasPrimaryCard: !!primaryCard,
                hasYourDay: text.includes('Your Day') || text.includes('Hôm nay của bạn')
            };
        })()""")

        assert not test_b["hasContext"], "New authenticated user must have hasEstablishedContext() === false"
        assert test_b["mode"] == "default", f"New authenticated user with no context must be in 'default', got: {test_b['mode']}"
        assert test_b["dmodeVisible"] and test_b["hasPrimaryCard"], "New authenticated user must see Entry Home"
        assert not test_b["hasYourDay"], "New authenticated user must NOT see a generic 'Your Day' dashboard"
        log("✓ TEST B PASSED: New authenticated user with no context routes to Entry Home, not an empty dashboard.")

        # =====================================================================
        # TEST C: Login alone does not replace Entry Home with an empty dashboard
        # =====================================================================
        log("\n--- TEST C: Login alone does not replace Entry Home with an empty dashboard ---")
        test_c = eval_js("""(() => {
            // Re-render active mode home
            window.TempoMode.renderActiveModeHome();
            const dmodeBox = document.getElementById('dmode-home-content');
            const primaryCard = document.querySelector('[data-tempo-ui="entry-card-primary"]');
            const text = dmodeBox ? dmodeBox.textContent : '';
            
            return {
                mode: window.TempoMode.getMode(),
                hasPrimaryCard: !!primaryCard,
                hasDominantQuestion: text.includes('What do you need right now?') || text.includes('Lúc này bạn cần gì?'),
                hasFakeStats: text.includes('0 of 0') || text.includes('0/0')
            };
        })()""")

        assert test_c["hasPrimaryCard"], "Primary Entry card must remain after login"
        assert test_c["hasDominantQuestion"], "Dominant question 'What do you need right now?' / 'Lúc này bạn cần gì?' must be present"
        assert not test_c["hasFakeStats"], "Must NOT create fake dashboard statistics"
        log("✓ TEST C PASSED: Login alone does not replace Entry Home with an empty dashboard.")

        # =====================================================================
        # TEST D: Passive public / tool use does not create a new mode
        # =====================================================================
        log("\n--- TEST D: Passive public / tool use does not create a new mode ---")
        test_d = eval_js("""(() => {
            const initialMode = window.TempoMode.getMode();
            
            // 1. Open Breathing
            if (window.TempoBreathing && window.TempoBreathing.openModal) {
                window.TempoBreathing.openModal();
                if (window.TempoBreathing.closeModal) window.TempoBreathing.closeModal();
            }
            const modeAfterBreathing = window.TempoMode.getMode();
            
            // 2. Open Quick Stress Relief
            if (window.TempoStressRelief && window.TempoStressRelief.openModal) {
                window.TempoStressRelief.openModal();
                if (window.TempoStressRelief.closeModal) window.TempoStressRelief.closeModal();
            }
            const modeAfterRelief = window.TempoMode.getMode();
            
            // 3. Open Community Modal
            if (window.TempoCommunity && window.TempoCommunity.openCommunityModal) {
                window.TempoCommunity.openCommunityModal();
                if (window.TempoCommunity.closeCommunityModal) window.TempoCommunity.closeCommunityModal();
            }
            const modeAfterCommunity = window.TempoMode.getMode();
            
            // 4. Return to Home
            if (window.TempoApp && window.TempoApp.navigateTo) {
                window.TempoApp.navigateTo('today');
            }
            const finalMode = window.TempoMode.getMode();
            const primaryCard = document.querySelector('[data-tempo-ui="entry-card-primary"]');
            
            return {
                initialMode,
                modeAfterBreathing,
                modeAfterRelief,
                modeAfterCommunity,
                finalMode,
                hasPrimaryCard: !!primaryCard
            };
        })()""")

        assert test_d["initialMode"] == "default", "Initial mode should be 'default'"
        assert test_d["modeAfterBreathing"] == "default", "Breathing must not establish new mode"
        assert test_d["modeAfterRelief"] == "default", "Quick Stress Relief must not establish new mode"
        assert test_d["modeAfterCommunity"] == "default", "Reading posts must not establish new mode"
        assert test_d["finalMode"] == "default", "Returning Home must still be in 'default'"
        assert test_d["hasPrimaryCard"], "Entry Home must still be displayed after passive tool usage"
        log("✓ TEST D PASSED: Passive tool and post usage does not create a new mode or exit Entry Home.")

        # =====================================================================
        # TEST E: Existing established Urgent behavior is not broken
        # =====================================================================
        log("\n--- TEST E: Existing established Urgent behavior is not broken ---")
        test_e = eval_js("""(() => {
            const todayISO = new Date().toISOString().split('T')[0];
            const urgentPlan = {
                id: 'established-urgent-plan-1',
                plan_type: 'emergency',
                tasks: [{ id: 'u-task-1', name: 'Establish Urgent Task', durationMinutes: 45, completed: false, isInProgress: true }],
                plannedTasks: [{ dayDate: todayISO, task: { id: 'u-task-1', name: 'Establish Urgent Task', completed: false, isInProgress: true } }]
            };
            window.TempoPlanStore.saveActivePlan('emergency', urgentPlan);
            window.TempoMode.setMode('emergency');
            window.TempoMode.renderActiveModeHome();
            
            const mode = window.TempoMode.getMode();
            const emodeBox = document.getElementById('emode-home-content');
            const dmodeBox = document.getElementById('dmode-home-content');
            const hasTaskNow = emodeBox && !!emodeBox.querySelector('[data-tempo-ui="urgent-task-now"], .urgent-card-now');
            
            return {
                mode,
                emodeVisible: emodeBox && !emodeBox.classList.contains('hidden'),
                dmodeHidden: dmodeBox && dmodeBox.classList.contains('hidden'),
                hasTaskNow
            };
        })()""")

        assert test_e["mode"] == "emergency", f"Established urgent user should be in 'emergency', got: {test_e['mode']}"
        assert test_e["emodeVisible"], "Urgent home must be visible for established urgent user"
        assert test_e["dmodeHidden"], "Entry Home must be hidden when Urgent mode is active"
        assert test_e["hasTaskNow"], "Urgent Home execution core must be intact"
        log("✓ TEST E PASSED: Established Urgent Mode user behavior is completely preserved.")

        # =====================================================================
        # TEST F: Existing established Recovery behavior is not broken
        # =====================================================================
        log("\n--- TEST F: Existing established Recovery behavior is not broken ---")
        test_f = eval_js("""(() => {
            localStorage.setItem('tempo_recovery_selfcheck_config', JSON.stringify({ type: 'STATE_B', selectedItems: ['sleep', 'movement'] }));
            localStorage.setItem('tempo_recovery_note_content', 'My gentle pace today');
            window.TempoMode.setMode('recovery');
            window.TempoMode.renderActiveModeHome();
            
            const mode = window.TempoMode.getMode();
            const rmodeBox = document.getElementById('rmode-home-content');
            const dmodeBox = document.getElementById('dmode-home-content');
            const hasSelfCheck = rmodeBox && (!!rmodeBox.querySelector('[data-tempo-ui="recovery-self-check"]') || rmodeBox.textContent.includes('TỰ KIỂM TRA') || rmodeBox.textContent.includes('SELF-CHECK'));
            
            return {
                mode,
                rmodeVisible: rmodeBox && !rmodeBox.classList.contains('hidden'),
                dmodeHidden: dmodeBox && dmodeBox.classList.contains('hidden'),
                hasSelfCheck
            };
        })()""")

        assert test_f["mode"] == "recovery", f"Established recovery user should be in 'recovery', got: {test_f['mode']}"
        assert test_f["rmodeVisible"], "Recovery Home must be visible for established recovery user"
        assert test_f["dmodeHidden"], "Entry Home must be hidden when Recovery mode is active"
        assert test_f["hasSelfCheck"], "Recovery Home hierarchy must be intact"
        log("✓ TEST F PASSED: Established Recovery Mode user behavior is completely preserved.")

        # =====================================================================
        # TEST G: VI / EN Language switch on Entry Home
        # =====================================================================
        log("\n--- TEST G: VI / EN Language switch on Entry Home ---")
        eval_js("""(() => {
            // Clean state back to default/Entry Home
            localStorage.clear();
            if (window.TempoPlanStore) window.TempoPlanStore.clearInMemoryCache();
            window.TempoMode.setMode('default');
            window.TempoMode.renderActiveModeHome();
        })()""")
        time.sleep(0.3)

        # 1. Check Vietnamese (Default)
        vi_entry = eval_js("""(() => {
            window.TempoI18n.setLanguage('vi');
            const dmodeBox = document.getElementById('dmode-home-content');
            return dmodeBox ? dmodeBox.textContent : '';
        })()""")

        assert "CHÀO MỪNG ĐẾN TEMPO" in vi_entry, f"Expected 'CHÀO MỪNG ĐẾN TEMPO' in VI, got: {vi_entry[:200]}"
        assert "Lúc này bạn cần gì?" in vi_entry, f"Expected 'Lúc này bạn cần gì?' in VI, got: {vi_entry[:200]}"
        assert "Giúp tôi tìm điểm bắt đầu" in vi_entry, f"Expected 'Giúp tôi tìm điểm bắt đầu' in VI"
        assert "Chưa đến 1 phút" in vi_entry, f"Expected 'Chưa đến 1 phút' in VI"
        assert "Hướng dẫn phù hợp với bạn" in vi_entry, f"Expected 'Hướng dẫn phù hợp với bạn' in VI"
        assert "Công cụ nhanh" in vi_entry, f"Expected 'Công cụ nhanh' in VI"
        log("✓ Vietnamese Entry Home copy verified.")

        # 2. Check English switch
        en_entry = eval_js("""(() => {
            window.TempoI18n.setLanguage('en');
            const dmodeBox = document.getElementById('dmode-home-content');
            return dmodeBox ? dmodeBox.textContent : '';
        })()""")

        assert "WELCOME TO TEMPO" in en_entry, f"Expected 'WELCOME TO TEMPO' in EN, got: {en_entry[:200]}"
        assert "What do you need right now?" in en_entry, f"Expected 'What do you need right now?' in EN, got: {en_entry[:200]}"
        assert "Help me figure out where to start" in en_entry, f"Expected 'Help me figure out where to start' in EN"
        assert "Takes less than 1 minute" in en_entry, f"Expected 'Takes less than 1 minute' in EN"
        assert "Personalized guidance" in en_entry, f"Expected 'Personalized guidance' in EN"
        assert "Quick Tools" in en_entry, f"Expected 'Quick Tools' in EN"
        log("✓ English Entry Home switch copy verified.")

        # Switch back to default 'vi'
        eval_js("window.TempoI18n.setLanguage('vi');")
        log("✓ TEST G PASSED: VI/EN dynamic switching on Entry Home verified.")

        # =====================================================================
        # TEST H: Entry Home Structural Composition Invariants
        # =====================================================================
        log("\n--- TEST H: Entry Home Structural Composition Invariants ---")
        composition = eval_js("""(() => {
            const primaryCard = document.querySelector('[data-tempo-ui="entry-card-primary"]');
            const communityPanel = document.querySelector('[data-tempo-ui="entry-community-panel"]');
            const quickTools = document.querySelector('[data-tempo-ui="entry-quick-tools"]');
            
            const primaryParent = primaryCard ? primaryCard.closest('.lg\\\\:col-span-8') : null;
            const communityParent = communityPanel ? communityPanel.closest('.lg\\\\:col-span-4') : null;
            
            const toolCards = quickTools ? quickTools.querySelectorAll('.grid > div') : [];
            const postsCards = communityPanel ? communityPanel.querySelectorAll('#homepage-community-posts-list > div') : [];
            
            return {
                hasPrimaryCard: !!primaryCard,
                hasCommunityPanel: !!communityPanel,
                hasQuickTools: !!quickTools,
                isLeftWider: !!primaryParent && !!communityParent,
                toolCardsCount: toolCards.length,
                postsCardsCount: postsCards.length
            };
        })()""")

        assert composition["hasPrimaryCard"], "Primary Entry Card must be present"
        assert composition["hasCommunityPanel"], "Tempo Community panel must be present"
        assert composition["hasQuickTools"], "Quick Tools must be present"
        assert composition["isLeftWider"], "Left primary card must be substantially wider than right panel (8 cols vs 4 cols)"
        assert composition["toolCardsCount"] == 4, f"Quick Tools must render exactly 4 tools (Focus Zone, Breathing, Quick Relief, Self-check), got: {composition['toolCardsCount']}"
        assert composition["postsCardsCount"] == 2, f"Community panel should render 2 social peer posts, got: {composition['postsCardsCount']}"
        log("✓ TEST H PASSED: Entry Home structural composition adheres strictly to the approved visual reference.")

        log("\n=======================================================")
        log(">>> ALL 8 PROMPT A TESTS (TEST A - TEST H) PASSED! <<<")
        log("=======================================================\n")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        proc.wait(timeout=5)

if __name__ == "__main__":
    run_tests()
