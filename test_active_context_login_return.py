import subprocess, time, json, urllib.request, websocket, tempfile, sys, base64

user_data_dir = tempfile.mkdtemp(prefix='tempo_ctx_test_')
port = 9425
proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={port}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--disable-gpu',
    '--no-first-run',
    'http://localhost:8000/'
])
time.sleep(2)

try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
        pages = [t for t in tabs if t.get('type') == 'page' and 'localhost' in t.get('url', '')]
    ws_url = pages[0]['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)

    msg_id = 1
    def send_cmd(method, params=None):
        global msg_id
        cmd = {'id': msg_id, 'method': method, 'params': params or {}}
        msg_id += 1
        ws.send(json.dumps(cmd))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == cmd['id']:
                return resp.get('result', {})

    def eval_js(expr):
        res = send_cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        if "exceptionDetails" in res:
            print("JS Exception:", res["exceptionDetails"])
        return res.get('result', {}).get('value')

    def save_screenshot(path):
        data = send_cmd("Page.captureScreenshot", {"format": "png"})
        b64 = data.get("data", "")
        if b64:
            with open(path, "wb") as f:
                f.write(base64.b64decode(b64))
            print(f"Saved screenshot: {path}")

    send_cmd('Page.enable')

    for _ in range(30):
        if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'"):
            break
        time.sleep(0.5)

    print("=== STARTING COMPREHENSIVE ACTIVE CONTEXT VERIFICATION ===")

    # Setup mock user accounts for tests
    # Account 1: User with Rmode and Urmode configured
    eval_js("""
        (() => {
            const user1 = {
                id: 'local_user_test_r_u',
                email: 'test_user_ru@tempo.edu',
                raw_email: 'test_user_ru@tempo.edu',
                password: 'password123',
                user_metadata: { full_name: 'Test Student', display_name: 'Test Student', role: 'student' }
            };
            localStorage.setItem('tempo_mock_account_test_user_ru@tempo.edu', JSON.stringify(user1));
            localStorage.setItem('tempo_recovery_intro_seen', 'true');
            localStorage.setItem('tempo_recovery_setup_completed', 'true');

            // Account 2: User with NO active context (new/default user)
            const user2 = {
                id: 'local_user_test_none',
                email: 'test_user_none@tempo.edu',
                raw_email: 'test_user_none@tempo.edu',
                password: 'password123',
                user_metadata: { full_name: 'New Student', display_name: 'New Student', role: 'student' }
            };
            localStorage.setItem('tempo_mock_account_test_user_none@tempo.edu', JSON.stringify(user2));
        })()
    """)

    # -------------------------------------------------------------
    # SCENARIO 1:
    # Set active context to Rmode -> Log out -> Click Self-check -> Log in -> Click Return Home -> Verify Rmode is restored
    # -------------------------------------------------------------
    print("\n--- SCENARIO 1: Rmode -> Logout -> Click Self-check -> Login -> Return Home -> Rmode restored ---")
    eval_js("""
        (async () => {
            await window.TempoAuth.signIn('test_user_ru@tempo.edu', 'password123');
            window.TempoMode.transitionContext('recovery', { skipSetupCheck: true });
            window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1)

    ctx_before = eval_js("window.TempoMode.getActiveContext()")
    persisted_before = eval_js("localStorage.getItem('tempo_user_established_context_local_user_test_r_u')")
    print(f"User 1 logged in: activeContext={ctx_before}, persisted={persisted_before}")
    assert ctx_before == "recovery", f"Expected recovery, got {ctx_before}"
    assert persisted_before == "recovery", f"Expected recovery in storage, got {persisted_before}"

    # Log out
    eval_js("window.TempoAuth.signOut()")
    time.sleep(1)
    is_authed = eval_js("!!(window.TempoAuth && window.TempoAuth.getCurrentUser())")
    ctx_logged_out = eval_js("window.TempoMode.getActiveContext()")
    persisted_after_logout = eval_js("localStorage.getItem('tempo_user_established_context_local_user_test_r_u')")
    print(f"Logged out: isAuthed={is_authed}, activeContext={ctx_logged_out}, persistedForUser={persisted_after_logout}")
    assert not is_authed, "User should be logged out"
    assert ctx_logged_out is None, f"Expected null activeContext after logout, got {ctx_logged_out}"
    assert persisted_after_logout == "recovery", f"User's persisted context MUST be preserved after logout, got {persisted_after_logout}"

    # From Entry Home, click Self-check (as guest)
    eval_js("""
        (() => {
            const scCard = document.querySelector('[data-tempo-ui="entry-lower-section"] > div:first-child');
            if (scCard) scCard.click();
            else window.TempoMode.openStrack('open', { sourceContext: 'entry' });
        })()
    """)
    time.sleep(0.5)
    pending_intent = eval_js("JSON.stringify(window.TempoMode.getPendingIntent())")
    print(f"Pending intent created for guest: {pending_intent}")
    assert "strack" in pending_intent or "stress-check" in pending_intent, f"Expected strack pending intent, got {pending_intent}"

    # Log in
    eval_js("""
        (async () => {
            await window.TempoAuth.signIn('test_user_ru@tempo.edu', 'password123');
        })()
    """)
    time.sleep(1)

    # Verify user is navigated to Self-check tool page
    sc_screen_visible = eval_js("!document.getElementById('screen-stress-check').classList.contains('hidden')")
    today_screen_visible = eval_js("!document.getElementById('screen-today').classList.contains('hidden')")
    print(f"After login into Self-check: SelfCheck screen visible={sc_screen_visible}, Today screen visible={today_screen_visible}")
    assert sc_screen_visible, "Self-check screen MUST be visible after login"

    # Save screenshot of Self-check page after login
    shot1 = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\self_check_after_login_rmode.png"
    save_screenshot(shot1)

    # Click Return Home
    eval_js("""
        (() => {
            const btn = document.getElementById('btn-self-check-return-home') || document.querySelector('[data-tempo-action="return-home"]');
            if (btn) btn.click();
            else window.TempoSelfCheckWorkspace.returnHome();
        })()
    """)
    time.sleep(1)

    # Verify Rmode is restored!
    ctx_after_return = eval_js("window.TempoMode.getActiveContext()")
    persisted_after_return = eval_js("localStorage.getItem('tempo_user_established_context_local_user_test_r_u')")
    sc_screen_hidden = eval_js("document.getElementById('screen-stress-check').classList.contains('hidden')")
    today_visible = eval_js("!document.getElementById('screen-today').classList.contains('hidden')")
    rmode_wp_visible = eval_js("!document.getElementById('recovery-working-plan').classList.contains('hidden')")
    page_bg = eval_js("window.getComputedStyle(document.body).backgroundColor")

    print(f"Returned from Self-check: activeContext={ctx_after_return}, persisted={persisted_after_return}, todayVisible={today_visible}, rmodeWPVisible={rmode_wp_visible}, pageBg={page_bg}")
    assert ctx_after_return == "recovery", f"Expected activeContext='recovery', got {ctx_after_return}"
    assert persisted_after_return == "recovery", f"Expected persisted='recovery', got {persisted_after_return}"
    assert sc_screen_hidden, "Self-check screen should be hidden"
    assert today_visible, "Today screen should be visible"
    assert rmode_wp_visible, "Rmode working plan card should be visible"
    assert page_bg == "rgb(232, 236, 241)", f"Expected Rmode background rgb(232, 236, 241), got {page_bg}"
    print(">>> SCENARIO 1 PASSED 100%! <<<\n")

    # Save screenshot of restored Rmode
    shot2 = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\restored_rmode_after_selfcheck_login.png"
    save_screenshot(shot2)

    # -------------------------------------------------------------
    # SCENARIO 2:
    # Set active context to Urmode -> Log out -> Click Self-check -> Log in -> Click Return Home -> Verify Urmode is restored
    # -------------------------------------------------------------
    print("\n--- SCENARIO 2: Urmode -> Logout -> Click Self-check -> Login -> Return Home -> Urmode restored ---")
    eval_js("""
        (() => {
            window.TempoMode.transitionContext('emergency', { silent: true });
            window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(0.5)

    ctx_urmode = eval_js("window.TempoMode.getActiveContext()")
    persisted_urmode = eval_js("localStorage.getItem('tempo_user_established_context_local_user_test_r_u')")
    print(f"Set to Urmode: activeContext={ctx_urmode}, persisted={persisted_urmode}")
    assert ctx_urmode == "emergency", f"Expected emergency, got {ctx_urmode}"
    assert persisted_urmode == "emergency", f"Expected emergency persisted, got {persisted_urmode}"

    # Log out
    eval_js("window.TempoAuth.signOut()")
    time.sleep(1)
    persisted_ur_after_logout = eval_js("localStorage.getItem('tempo_user_established_context_local_user_test_r_u')")
    assert persisted_ur_after_logout == "emergency", f"Persisted context must remain emergency, got {persisted_ur_after_logout}"

    # From Entry Home, click Self-check (as guest)
    eval_js("window.TempoMode.openStrack('open', { sourceContext: 'entry' })")
    time.sleep(0.5)

    # Log in
    eval_js("""
        (async () => {
            await window.TempoAuth.signIn('test_user_ru@tempo.edu', 'password123');
        })()
    """)
    time.sleep(1)

    sc_screen_visible = eval_js("!document.getElementById('screen-stress-check').classList.contains('hidden')")
    assert sc_screen_visible, "Self-check screen should be visible"

    # Click Return Home
    eval_js("window.TempoSelfCheckWorkspace.returnHome()")
    time.sleep(1)

    ctx_ur_restored = eval_js("window.TempoMode.getActiveContext()")
    persisted_ur_restored = eval_js("localStorage.getItem('tempo_user_established_context_local_user_test_r_u')")
    print(f"Returned from Self-check: activeContext={ctx_ur_restored}, persisted={persisted_ur_restored}")
    assert ctx_ur_restored == "emergency", f"Expected emergency activeContext, got {ctx_ur_restored}"
    assert persisted_ur_restored == "emergency", f"Expected emergency persisted, got {persisted_ur_restored}"
    print(">>> SCENARIO 2 PASSED 100%! <<<\n")

    # -------------------------------------------------------------
    # SCENARIO 3:
    # Access Self-check while already logged in from Rmode -> Click Return Home -> Verify Rmode is restored
    # -------------------------------------------------------------
    print("\n--- SCENARIO 3: Already logged in from Rmode -> Open Self-check -> Return Home -> Rmode restored ---")
    eval_js("""
        (() => {
            window.TempoMode.transitionContext('recovery', { skipSetupCheck: true });
            window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(0.5)

    # Open Self-check (e.g. from navbar or Daily card)
    eval_js("window.TempoMode.openStrack('open', { sourceContext: 'recovery' })")
    time.sleep(0.5)
    sc_screen_visible = eval_js("!document.getElementById('screen-stress-check').classList.contains('hidden')")
    assert sc_screen_visible, "Self-check screen should be open"

    # Click Return Home
    eval_js("window.TempoSelfCheckWorkspace.returnHome()")
    time.sleep(1)

    ctx_rmode_s3 = eval_js("window.TempoMode.getActiveContext()")
    persisted_rmode_s3 = eval_js("localStorage.getItem('tempo_user_established_context_local_user_test_r_u')")
    print(f"Scenario 3 return: activeContext={ctx_rmode_s3}, persisted={persisted_rmode_s3}")
    assert ctx_rmode_s3 == "recovery", f"Expected recovery, got {ctx_rmode_s3}"
    assert persisted_rmode_s3 == "recovery", f"Expected persisted recovery, got {persisted_rmode_s3}"
    print(">>> SCENARIO 3 PASSED 100%! <<<\n")

    # -------------------------------------------------------------
    # SCENARIO 4:
    # Access Self-check while already logged in from Urmode -> Click Return Home -> Verify Urmode is restored
    # -------------------------------------------------------------
    print("\n--- SCENARIO 4: Already logged in from Urmode -> Open Self-check -> Return Home -> Urmode restored ---")
    eval_js("""
        (() => {
            window.TempoMode.transitionContext('emergency', { silent: true });
            window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(0.5)

    # Open Self-check
    eval_js("window.TempoMode.openStrack('open', { sourceContext: 'emergency' })")
    time.sleep(0.5)
    sc_screen_visible = eval_js("!document.getElementById('screen-stress-check').classList.contains('hidden')")
    assert sc_screen_visible, "Self-check screen should be open"

    # Click Return Home
    eval_js("window.TempoSelfCheckWorkspace.returnHome()")
    time.sleep(1)

    ctx_urmode_s4 = eval_js("window.TempoMode.getActiveContext()")
    persisted_urmode_s4 = eval_js("localStorage.getItem('tempo_user_established_context_local_user_test_r_u')")
    print(f"Scenario 4 return: activeContext={ctx_urmode_s4}, persisted={persisted_urmode_s4}")
    assert ctx_urmode_s4 == "emergency", f"Expected emergency, got {ctx_urmode_s4}"
    assert persisted_urmode_s4 == "emergency", f"Expected persisted emergency, got {persisted_urmode_s4}"
    print(">>> SCENARIO 4 PASSED 100%! <<<\n")

    # -------------------------------------------------------------
    # SCENARIO 5:
    # Log in with a user who has no saved active context -> Click Return Home from Self-check -> Verify default Entry Home behavior is preserved
    # -------------------------------------------------------------
    print("\n--- SCENARIO 5: User with NO saved active context -> Return Home from Self-check -> Entry Home preserved ---")
    eval_js("window.TempoAuth.signOut()")
    time.sleep(0.5)

    # Log in as user2 (no saved context)
    eval_js("""
        (async () => {
            await window.TempoAuth.signIn('test_user_none@tempo.edu', 'password123');
            window.TempoMode.openStrack('open', { sourceContext: 'entry' });
        })()
    """)
    time.sleep(1)

    sc_screen_visible = eval_js("!document.getElementById('screen-stress-check').classList.contains('hidden')")
    assert sc_screen_visible, "Self-check screen should be open"

    # Click Return Home
    eval_js("window.TempoSelfCheckWorkspace.returnHome()")
    time.sleep(1)

    ctx_s5 = eval_js("window.TempoMode.getActiveContext()")
    persisted_s5 = eval_js("localStorage.getItem('tempo_user_established_context_local_user_test_none')")
    entry_visible = eval_js("!document.getElementById('screen-today').classList.contains('hidden') && !document.querySelector('[data-tempo-ui=\"entry-lower-section\"]').classList.contains('hidden')")
    entry_bg = eval_js("window.getComputedStyle(document.body).backgroundColor")

    print(f"Scenario 5 return: activeContext={ctx_s5}, persisted={persisted_s5}, entryVisible={entry_visible}, entryBg={entry_bg}")
    assert ctx_s5 is None, f"Expected null activeContext for default user, got {ctx_s5}"
    assert entry_visible, "Entry Home UI elements must be visible"
    assert entry_bg == "rgb(246, 240, 235)", f"Expected Entry Home bg rgb(246, 240, 235), got {entry_bg}"
    print(">>> SCENARIO 5 PASSED 100%! <<<\n")

    # -------------------------------------------------------------
    # SCENARIO 6:
    # Verify refreshing the page on Self-check does not overwrite or lose the user's active context
    # -------------------------------------------------------------
    print("\n--- SCENARIO 6: Refreshing page on Self-check preserves active context ---")
    # Log back into user1 and set Rmode
    eval_js("""
        (async () => {
            await window.TempoAuth.signIn('test_user_ru@tempo.edu', 'password123');
            window.TempoMode.transitionContext('recovery', { skipSetupCheck: true });
            window.TempoMode.openStrack('open', { sourceContext: 'recovery' });
        })()
    """)
    time.sleep(1)

    persisted_before_reload = eval_js("localStorage.getItem('tempo_user_established_context_local_user_test_r_u')")
    print(f"Before reload on #stress-check: persisted={persisted_before_reload}, hash={eval_js('window.location.hash')}")
    assert persisted_before_reload == "recovery", f"Expected recovery, got {persisted_before_reload}"

    # Reload page via CDP
    send_cmd("Page.reload")
    time.sleep(2)

    # Wait for page to initialize
    for _ in range(30):
        if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'"):
            break
        time.sleep(0.5)

    time.sleep(1)

    persisted_after_reload = eval_js("localStorage.getItem('tempo_user_established_context_local_user_test_r_u')")
    ctx_after_reload = eval_js("window.TempoMode.getActiveContext()")
    is_authed_after_reload = eval_js("!!(window.TempoAuth && window.TempoAuth.getCurrentUser())")
    print(f"After reload on #stress-check: isAuthed={is_authed_after_reload}, activeContext={ctx_after_reload}, persisted={persisted_after_reload}")
    assert is_authed_after_reload, "User should still be authenticated after reload"
    assert persisted_after_reload == "recovery", f"Expected persisted='recovery' after reload, got {persisted_after_reload}"

    # Now click Return Home after reload
    eval_js("window.TempoSelfCheckWorkspace.returnHome()")
    time.sleep(1)

    ctx_final = eval_js("window.TempoMode.getActiveContext()")
    persisted_final = eval_js("localStorage.getItem('tempo_user_established_context_local_user_test_r_u')")
    today_final_visible = eval_js("!document.getElementById('screen-today').classList.contains('hidden')")
    rmode_final_wp = eval_js("!document.getElementById('recovery-working-plan').classList.contains('hidden')")
    final_bg = eval_js("window.getComputedStyle(document.body).backgroundColor")

    print(f"Final Return Home after reload: activeContext={ctx_final}, persisted={persisted_final}, todayVisible={today_final_visible}, rmodeWP={rmode_final_wp}, bg={final_bg}")
    assert ctx_final == "recovery", f"Expected activeContext='recovery', got {ctx_final}"
    assert persisted_final == "recovery", f"Expected persisted='recovery', got {persisted_final}"
    assert today_final_visible, "Today screen must be visible"
    assert rmode_final_wp, "Rmode working plan must be visible"
    assert final_bg == "rgb(232, 236, 241)", f"Expected Rmode bg rgb(232, 236, 241), got {final_bg}"
    print(">>> SCENARIO 6 PASSED 100%! <<<\n")

    print("\n=======================================================")
    print("ALL 6 VERIFICATION SCENARIOS PASSED WITH ZERO FAILURES!")
    print("=======================================================\n")

finally:
    proc.terminate()
