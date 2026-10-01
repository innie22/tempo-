"""
TEMPO REGRESSION TEST SUITE: VIETNAMESE-FIRST LOCALIZATION SYSTEM
File: test_localization.py

Validates all 13 checks (A through M) specified in Section 30:
A: Fresh first visit defaults to vi
B: VI -> EN updates visible system copy
C: EN -> VI updates visible system copy
D: Page refresh / reload preserves saved language preference
E: Language change does not alter currentMode
F: Language change does not reset or alter Eplan
G: Language change does not reset Recovery State
H: Internal mode identifier "emergency" remains strictly unchanged
I: Internal mode identifier "recovery" remains strictly unchanged
J: PLAN_* internal states remain strictly unchanged
K: User-generated Tempo Post content is NOT translated or modified
L: Missing translation key produces safe fallback
M: Pre-login auth experience can switch language before login
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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_loc_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9235
    
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
                    ready = eval_js("document.readyState === 'complete' && typeof window.TempoI18n !== 'undefined' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined'")
                    if ready:
                        eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("Application failed to become ready")

        log("Waiting for page and scripts ready...")
        wait_for_ready()

        # =====================================================================
        # CHECK A: Fresh First Visit Defaults to Vietnamese (vi)
        # =====================================================================
        log("\n--- CHECK A: Fresh first visit defaults to vi ---")
        init_state = eval_js("""
            (() => {
                const lang = window.TempoI18n.getLanguage();
                const navBtn = document.getElementById('nav-btn-language');
                const navLabel = document.getElementById('nav-current-lang-label');
                const signinBtn = document.getElementById('btn-header-signin');
                const registerBtn = document.getElementById('btn-header-register');
                const searchInput = document.getElementById('global-search-input');
                
                return {
                    lang,
                    navLabel: navLabel ? navLabel.textContent.trim() : (navBtn ? navBtn.textContent.trim() : ''),
                    signinBtnText: signinBtn ? signinBtn.textContent.trim() : '',
                    registerBtnText: registerBtn ? registerBtn.textContent.trim() : '',
                    searchPlaceholder: searchInput ? searchInput.placeholder : ''
                };
            })()
        """)
        assert init_state['lang'] == 'vi', f"Default language must be 'vi', got: {init_state['lang']}"
        assert "VI" in init_state['navLabel'], f"Language button should show VI, got: {init_state['navLabel']}"
        assert init_state['signinBtnText'] == 'Đăng nhập', f"Initial sign in button must be 'Đăng nhập', got: {init_state['signinBtnText']}"
        assert init_state['registerBtnText'] == 'Đăng ký', f"Initial register button must be 'Đăng ký', got: {init_state['registerBtnText']}"
        log(f"✓ CHECK A PASSED: First visit defaults to 'vi', UI shows VI / Đăng nhập / Đăng ký.")

        # =====================================================================
        # CHECK B: VI -> EN Updates Visible System Copy
        # =====================================================================
        log("\n--- CHECK B: Switching VI -> EN updates visible system copy ---")
        eval_js("window.TempoI18n.setLanguage('en');")
        time.sleep(0.3)
        en_state = eval_js("""
            (() => {
                const lang = window.TempoI18n.getLanguage();
                const navLabel = document.getElementById('nav-current-lang-label');
                const signinBtn = document.getElementById('btn-header-signin');
                const registerBtn = document.getElementById('btn-header-register');
                const searchInput = document.getElementById('global-search-input');
                
                return {
                    lang,
                    navLabel: navLabel ? navLabel.textContent.trim() : '',
                    signinBtnText: signinBtn ? signinBtn.textContent.trim() : '',
                    registerBtnText: registerBtn ? registerBtn.textContent.trim() : '',
                    searchPlaceholder: searchInput ? searchInput.placeholder : ''
                };
            })()
        """)
        assert en_state['lang'] == 'en', f"Language should be 'en', got: {en_state['lang']}"
        assert "EN" in en_state['navLabel'], f"Language button should show EN, got: {en_state['navLabel']}"
        assert en_state['signinBtnText'] == 'Sign In', f"Sign in button text should be 'Sign In', got: {en_state['signinBtnText']}"
        assert en_state['registerBtnText'] == 'Register', f"Register button text should be 'Register', got: {en_state['registerBtnText']}"
        assert en_state['searchPlaceholder'] == 'Search Tempo...', f"Search placeholder should be 'Search Tempo...', got: {en_state['searchPlaceholder']}"
        log("✓ CHECK B PASSED: VI -> EN instantly updates navbar and system copy.")

        # =====================================================================
        # CHECK C: EN -> VI Updates Visible System Copy
        # =====================================================================
        log("\n--- CHECK C: Switching EN -> VI updates visible system copy ---")
        eval_js("window.TempoI18n.setLanguage('vi');")
        time.sleep(0.3)
        vi_state = eval_js("""
            (() => {
                const lang = window.TempoI18n.getLanguage();
                const navLabel = document.getElementById('nav-current-lang-label');
                const signinBtn = document.getElementById('btn-header-signin');
                const registerBtn = document.getElementById('btn-header-register');
                const searchInput = document.getElementById('global-search-input');
                
                return {
                    lang,
                    navLabel: navLabel ? navLabel.textContent.trim() : '',
                    signinBtnText: signinBtn ? signinBtn.textContent.trim() : '',
                    registerBtnText: registerBtn ? registerBtn.textContent.trim() : '',
                    searchPlaceholder: searchInput ? searchInput.placeholder : ''
                };
            })()
        """)
        assert vi_state['lang'] == 'vi', f"Language should be 'vi', got: {vi_state['lang']}"
        assert "VI" in vi_state['navLabel'], f"Language button should show VI, got: {vi_state['navLabel']}"
        assert vi_state['signinBtnText'] == 'Đăng nhập', f"Sign in button text should return to 'Đăng nhập', got: {vi_state['signinBtnText']}"
        assert vi_state['registerBtnText'] == 'Đăng ký', f"Register button text should return to 'Đăng ký', got: {vi_state['registerBtnText']}"
        assert vi_state['searchPlaceholder'] == 'Tìm kiếm trên Tempo...', f"Search placeholder should return to 'Tìm kiếm trên Tempo...', got: {vi_state['searchPlaceholder']}"
        log("✓ CHECK C PASSED: EN -> VI restores Vietnamese system copy.")

        # =====================================================================
        # CHECK D: Page Reload Preserves Saved Language Preference
        # =====================================================================
        log("\n--- CHECK D: Page reload preserves saved language preference ---")
        eval_js("window.TempoI18n.setLanguage('en');")
        time.sleep(0.2)
        send_command("Page.reload")
        time.sleep(1.0)
        wait_for_ready()

        reloaded_en = eval_js("window.TempoI18n.getLanguage();")
        assert reloaded_en == 'en', f"Language after reload should remain 'en', got: {reloaded_en}"

        # Switch to vi and reload
        eval_js("window.TempoI18n.setLanguage('vi');")
        time.sleep(0.2)
        send_command("Page.reload")
        time.sleep(1.0)
        wait_for_ready()

        reloaded_vi = eval_js("window.TempoI18n.getLanguage();")
        assert reloaded_vi == 'vi', f"Language after reload should remain 'vi', got: {reloaded_vi}"
        log("✓ CHECK D PASSED: Language preference persists across page reloads.")

        # =====================================================================
        # CHECK E: Language Change Does Not Alter currentMode
        # =====================================================================
        log("\n--- CHECK E: Language change does not alter currentMode ---")
        mode_check = eval_js("""
            (() => {
                const results = [];
                const modes = ['default', 'emergency', 'recovery', 'unclear'];
                
                for (const m of modes) {
                    window.TempoMode.setMode(m);
                    const before = window.TempoMode.getMode();
                    window.TempoI18n.setLanguage('en');
                    const duringEn = window.TempoMode.getMode();
                    window.TempoI18n.setLanguage('vi');
                    const duringVi = window.TempoMode.getMode();
                    results.push({ target: m, before, duringEn, duringVi, intact: (before === m && duringEn === m && duringVi === m) });
                }
                return results;
            })()
        """)
        for r in mode_check:
            assert r['intact'], f"Mode {r['target']} was corrupted by language switch: {r}"
        log("✓ CHECK E PASSED: Language change preserves currentMode across all 4 modes.")

        # =====================================================================
        # CHECK F: Language Change Does Not Reset or Alter Active Urgent Plan
        # =====================================================================
        log("\n--- CHECK F: Language change does not reset or alter Eplan ---")
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

                const testPlan = {
                    id: 'plan_loc_test_101',
                    planId: 'plan_loc_test_101',
                    planType: 'emergency',
                    title: 'Urgent Plan',
                    plannedTasks: [
                        {
                            dayDate: today,
                            startTime: '10:00 AM',
                            task: {
                                id: 'task-loc-1',
                                name: 'Quantum Physics Problem Set',
                                durationMinutes: 60,
                                durationLabel: '1 hr',
                                completed: false,
                                subtasks: [{ id: 's1', title: 'Problem 1', completed: false }]
                            }
                        }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, blocks: [{ start: '09:00', end: '18:00' }] }]
                };
                testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);
                await window.TempoPlanStore.saveActivePlan('emergency', testPlan);
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
                }
            })()
        """)

        plan_test = eval_js("""
            (() => {
                const planBefore = window.TempoPlanStore.getActivePlan('emergency');
                window.TempoI18n.setLanguage('en');
                const planEn = window.TempoPlanStore.getActivePlan('emergency');
                window.TempoI18n.setLanguage('vi');
                const planVi = window.TempoPlanStore.getActivePlan('emergency');

                return {
                    sameId: planBefore.planId === planEn.planId && planEn.planId === planVi.planId,
                    taskName: planVi.plannedTasks[0].task.name,
                    taskCount: planVi.plannedTasks.length
                };
            })()
        """)
        assert plan_test['sameId'], "Plan ID must remain strictly identical across language changes"
        assert plan_test['taskName'] == 'Quantum Physics Problem Set', "Task name must remain completely untouched"
        assert plan_test['taskCount'] == 1, "Task count must remain intact"
        log("✓ CHECK F PASSED: Urgent Plan data, tasks, and structure are completely preserved.")

        # =====================================================================
        # CHECK G: Language Change Does Not Reset Recovery State
        # =====================================================================
        log("\n--- CHECK G: Language change does not reset Recovery State ---")
        rec_test = eval_js("""
            (async () => {
                window.TempoMode.setMode('recovery');
                let addedItem = null;
                if (window.TempoRecoveryNote) {
                    addedItem = window.TempoRecoveryNote.addItem('what_helps', 'Reading favorite comic books');
                }
                
                const beforeItems = window.TempoRecoveryNote ? window.TempoRecoveryNote.getItems('what_helps') : [];
                window.TempoI18n.setLanguage('en');
                const enItems = window.TempoRecoveryNote ? window.TempoRecoveryNote.getItems('what_helps') : [];
                window.TempoI18n.setLanguage('vi');
                const viItems = window.TempoRecoveryNote ? window.TempoRecoveryNote.getItems('what_helps') : [];

                return {
                    hasCustomItem: viItems.some(i => (i.text || i.content) === 'Reading favorite comic books'),
                    countMatch: beforeItems.length === enItems.length && enItems.length === viItems.length
                };
            })()
        """)
        assert rec_test['hasCustomItem'], "Recovery Note custom item must be preserved across language changes"
        assert rec_test['countMatch'], "Recovery Note item count must remain stable"
        log("✓ CHECK G PASSED: Recovery State and user notes preserved across language changes.")

        # =====================================================================
        # CHECK H: Internal Mode Identifier "emergency" Remains Strictly Unchanged
        # =====================================================================
        log("\n--- CHECK H: Internal mode identifier 'emergency' remains strictly unchanged ---")
        eval_js("window.TempoMode.setMode('emergency');")
        h_test = eval_js("""
            (() => {
                const modeVal = window.TempoMode.getMode();
                const storageVal = localStorage.getItem('tempo_current_mode');
                const hasStoreEmergency = window.TempoPlanStore.hasActivePlan('emergency');
                const hasStoreUrgent = window.TempoPlanStore.hasActivePlan('urgent');
                return { modeVal, storageVal, hasStoreEmergency, hasStoreUrgent };
            })()
        """)
        assert h_test['modeVal'] == 'emergency', f"Internal mode must be 'emergency', got: {h_test['modeVal']}"
        assert h_test['storageVal'] == 'emergency', f"Storage mode must be 'emergency', got: {h_test['storageVal']}"
        assert h_test['hasStoreEmergency'] is True, "TempoPlanStore must store plans under 'emergency'"
        assert h_test['hasStoreUrgent'] is False, "TempoPlanStore must NOT have 'urgent' key"
        log("✓ CHECK H PASSED: Internal identifier 'emergency' is preserved without alias pollution.")

        # =====================================================================
        # CHECK I: Internal Mode Identifier "recovery" Remains Strictly Unchanged
        # =====================================================================
        log("\n--- CHECK I: Internal mode identifier 'recovery' remains strictly unchanged ---")
        eval_js("window.TempoMode.setMode('recovery');")
        i_test = eval_js("""
            (() => {
                const modeVal = window.TempoMode.getMode();
                const storageVal = localStorage.getItem('tempo_current_mode');
                return { modeVal, storageVal };
            })()
        """)
        assert i_test['modeVal'] == 'recovery', f"Internal mode must be 'recovery', got: {i_test['modeVal']}"
        assert i_test['storageVal'] == 'recovery', f"Storage mode must be 'recovery', got: {i_test['storageVal']}"
        log("✓ CHECK I PASSED: Internal identifier 'recovery' remains strictly unchanged.")

        # =====================================================================
        # CHECK J: PLAN_* Internal States Remain Strictly Unchanged
        # =====================================================================
        log("\n--- CHECK J: PLAN_* internal states remain strictly unchanged ---")
        j_test = eval_js("""
            (() => {
                const states = window.TempoMode.EPLAN_STATES || {};
                const stateKeys = Object.keys(states);
                const hasActive = states.ACTIVE_TODAY === 'PLAN_ACTIVE_TODAY';
                const hasDone = states.TODAY_COMPLETE === 'PLAN_TODAY_COMPLETE';
                const hasStale = states.STALE === 'PLAN_STALE';
                const hasComp = states.COMPLETE === 'PLAN_COMPLETE';
                
                return { stateKeys, hasActive, hasDone, hasStale, hasComp };
            })()
        """)
        assert j_test['hasActive'], "PLAN_ACTIVE_TODAY invariant broken"
        assert j_test['hasDone'], "PLAN_TODAY_COMPLETE invariant broken"
        assert j_test['hasStale'], "PLAN_STALE invariant broken"
        assert j_test['hasComp'], "PLAN_COMPLETE invariant broken"
        log("✓ CHECK J PASSED: All internal PLAN_* state enums remain strictly unchanged.")

        # =====================================================================
        # CHECK K: User-Generated Tempo Post Content Is NOT Translated
        # =====================================================================
        log("\n--- CHECK K: User-generated Tempo Post content is NOT translated ---")
        eval_js("window.TempoMode.setMode('emergency'); window.TempoMode.renderEmodeHome();")
        time.sleep(0.3)
        post_test = eval_js("""
            (() => {
                window.TempoI18n.setLanguage('vi');
                if (window.TempoCommunity && window.TempoCommunity.renderUrgentPreview) {
                    window.TempoCommunity.renderUrgentPreview();
                }
                const posts = window.TempoCommunity ? window.TempoCommunity.getPosts() : [];
                const firstPostContent = posts.length > 0 ? posts[0].content : '';
                const postsList = document.getElementById('urgent-community-posts-list');
                const viText = postsList ? postsList.textContent : '';

                window.TempoI18n.setLanguage('en');
                if (window.TempoCommunity && window.TempoCommunity.renderUrgentPreview) {
                    window.TempoCommunity.renderUrgentPreview();
                }
                const enPosts = window.TempoCommunity ? window.TempoCommunity.getPosts() : [];
                const enFirstContent = enPosts.length > 0 ? enPosts[0].content : '';
                const enText = postsList ? postsList.textContent : '';

                window.TempoI18n.setLanguage('vi');

                const sampleSnippet = "Small wins count";
                return {
                    samePostContent: firstPostContent === enFirstContent && firstPostContent.length > 0,
                    hasInVi: viText.includes(sampleSnippet),
                    hasInEn: enText.includes(sampleSnippet)
                };
            })()
        """)
        assert post_test['samePostContent'] and post_test['hasInVi'] and post_test['hasInEn'], f"User post body text must remain untranslated and identical, got: {post_test}"
        log("✓ CHECK K PASSED: Community post user-generated content preserved verbatim.")

        # =====================================================================
        # CHECK L: Missing Translation Key Produces Safe Fallback
        # =====================================================================
        log("\n--- CHECK L: Missing translation key produces safe fallback ---")
        l_test = eval_js("""
            (() => {
                const withExplicitFallback = window.TempoI18n.t('nonexistent.missing.key', {}, 'Custom Fallback Text');
                const withoutFallback = window.TempoI18n.t('nonexistent.missing.key');
                const interpolationVi = window.TempoI18n.t('modes.urgent.completedOf', { completed: 2, total: 5 });
                window.TempoI18n.setLanguage('en');
                const interpolationEn = window.TempoI18n.t('modes.urgent.completedOf', { completed: 2, total: 5 });
                window.TempoI18n.setLanguage('vi');

                return {
                    withExplicitFallback,
                    withoutFallback,
                    interpolationVi,
                    interpolationEn
                };
            })()
        """)
        assert l_test['withExplicitFallback'] == 'Custom Fallback Text', f"Fallback text failed: {l_test['withExplicitFallback']}"
        assert l_test['withoutFallback'] is not None and l_test['withoutFallback'] != 'undefined', "Must not return undefined or null"
        assert "2 trên 5 đã xong" in l_test['interpolationVi'] or "2" in l_test['interpolationVi'], f"Vietnamese interpolation failed: {l_test['interpolationVi']}"
        assert "2 of 5 completed" in l_test['interpolationEn'], f"English interpolation failed: {l_test['interpolationEn']}"
        log("✓ CHECK L PASSED: Safe fallbacks and parameterized string interpolations verified.")

        # =====================================================================
        # CHECK M: Pre-login Auth Experience Can Switch Language Before Login
        # =====================================================================
        log("\n--- CHECK M: Pre-login auth experience can switch language before login ---")
        m_test = eval_js("""
            (() => {
                // Ensure logged out for guest test
                if (window.TempoAuth && window.TempoAuth.signOut) {
                    window.TempoAuth.signOut();
                }

                // 1. Open Register Modal in Vietnamese
                window.TempoI18n.setLanguage('vi');
                window.TempoAuth.openRegisterModal();
                const regModal = document.getElementById('modal-register');
                const regTitleVi = regModal ? regModal.querySelector('h2, h3').textContent : '';

                // 2. Switch to English with register modal open
                window.TempoI18n.setLanguage('en');
                const regTitleEn = regModal ? regModal.querySelector('h2, h3').textContent : '';
                window.TempoAuth.closeRegisterModal();

                // 3. Open Sign In Modal in English
                window.TempoAuth.openSignInModal();
                const signModal = document.getElementById('modal-signin');
                const signTitleEn = signModal ? signModal.querySelector('h2, h3').textContent : '';

                // 4. Switch to Vietnamese with sign in modal open
                window.TempoI18n.setLanguage('vi');
                const signTitleVi = signModal ? signModal.querySelector('h2, h3').textContent : '';
                window.TempoAuth.closeSignInModal();

                return {
                    regTitleVi,
                    regTitleEn,
                    signTitleEn,
                    signTitleVi
                };
            })()
        """)
        assert any(t in m_test['regTitleVi'] for t in ['TẠO TÀI KHOẢN', 'Chào mừng']), f"Register VI title mismatch: {m_test['regTitleVi']}"
        assert any(t in m_test['regTitleEn'] for t in ['CREATE', 'Welcome']), f"Register EN title mismatch: {m_test['regTitleEn']}"
        assert any(t in m_test['signTitleEn'] for t in ['WELCOME BACK', 'Welcome Back']), f"Sign In EN title mismatch: {m_test['signTitleEn']}"
        assert any(t in m_test['signTitleVi'] for t in ['CHÀO MỪNG TRỞ LẠI', 'Chào mừng trở lại']), f"Sign In VI title mismatch: {m_test['signTitleVi']}"
        log("✓ CHECK M PASSED: Pre-login auth modals switch languages reactively before login.")

        log("\n=======================================================")
        log(">>> ALL 13 LOCALIZATION CHECKS (A THROUGH M) PASSED! <<<")
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
