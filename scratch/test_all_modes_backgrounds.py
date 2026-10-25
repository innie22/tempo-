import subprocess, time, json, urllib.request, websocket, tempfile, sys, base64

user_data_dir = tempfile.mkdtemp(prefix='tempo_bg_test_')
port = 9415
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

    print("\n--- 1. Testing Entry Home Background ---")
    eval_js("""
        (() => {
            window.TempoMode.transitionContext(null, { silent: true });
            window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(0.5)
    entry_bg = eval_js("window.getComputedStyle(document.body).backgroundColor")
    print("Entry Home body computed bg:", entry_bg)
    assert entry_bg == "rgb(246, 240, 235)", f"Expected rgb(246, 240, 235) for Entry Home, got {entry_bg}"

    print("\n--- 2. Testing Recovery Mode (Rmode) Background ---")
    eval_js("""
        (async () => {
            const mock = {
                id: 'local_user_selfcheck',
                email: 'selfcheck_user@tempo.edu',
                raw_email: 'selfcheck_user@tempo.edu',
                password: 'password123',
                user_metadata: { full_name: 'Alex Chen', display_name: 'Alex Chen', role: 'student' }
            };
            localStorage.setItem('tempo_mock_account_selfcheck_user@tempo.edu', JSON.stringify(mock));
            if (window.TempoAuth) {
                await window.TempoAuth.signIn("selfcheck_user@tempo.edu", "password123");
            }
            localStorage.setItem('tempo_recovery_intro_seen', 'true');
            localStorage.setItem('tempo_recovery_setup_completed', 'true');
            window.TempoMode.transitionContext('recovery', { skipSetupCheck: true });
            window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1)
    rmode_body_bg = eval_js("window.getComputedStyle(document.body).backgroundColor")
    rmode_main_bg = eval_js("window.getComputedStyle(document.querySelector('main')).backgroundColor")
    wp_card_bg = eval_js("window.getComputedStyle(document.getElementById('recovery-working-plan')).backgroundColor")
    selfcheck_card_bg = eval_js("window.getComputedStyle(document.querySelector('.recovery-card-selfcheck')).backgroundColor")
    recently_card_bg = eval_js("window.getComputedStyle(document.querySelector('.recovery-card-recently')).backgroundColor")
    comm_card_bg = eval_js("window.getComputedStyle(document.querySelector('[data-tempo-ui=\"recovery-community\"]')).backgroundColor")

    print(f"Rmode body bg: {rmode_body_bg}")
    print(f"Rmode main bg: {rmode_main_bg}")
    print(f"Rmode Working Plan card bg: {wp_card_bg}")
    print(f"Rmode SelfCheck card bg: {selfcheck_card_bg}")
    print(f"Rmode Recently card bg: {recently_card_bg}")
    print(f"Rmode Community card bg: {comm_card_bg}")

    assert rmode_body_bg == "rgb(232, 236, 241)", f"Expected rgb(232, 236, 241) (#E8ECF1) for Rmode body, got {rmode_body_bg}"
    assert rmode_main_bg == "rgb(232, 236, 241)", f"Expected rgb(232, 236, 241) (#E8ECF1) for Rmode main, got {rmode_main_bg}"
    assert wp_card_bg == "rgb(254, 250, 244)", f"Expected rgb(254, 250, 244) (#FEFAF4) for Working Plan card, got {wp_card_bg}"
    assert selfcheck_card_bg == "rgb(254, 250, 244)", f"Expected rgb(254, 250, 244) (#FEFAF4) for SelfCheck card, got {selfcheck_card_bg}"
    assert recently_card_bg == "rgb(254, 250, 244)", f"Expected rgb(254, 250, 244) (#FEFAF4) for Recently card, got {recently_card_bg}"
    assert comm_card_bg == "rgb(255, 255, 255)", f"Expected rgb(255, 255, 255) for Community card, got {comm_card_bg}"

    shot_path = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\rmode_page_bg_restored.png"
    save_screenshot(shot_path)

    print("\n--- 3. Testing Emergency Mode (Urmode) Background ---")
    eval_js("""
        (() => {
            window.TempoMode.transitionContext('emergency', { silent: true });
            window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(0.5)
    urmode_body_bg = eval_js("window.getComputedStyle(document.body).backgroundColor")
    print("Urmode body bg:", urmode_body_bg)
    assert urmode_body_bg == "rgb(230, 237, 231)", f"Expected rgb(230, 237, 231) (#e6ede7) for Urmode body, got {urmode_body_bg}"

    print("\n--- 4. Testing Navigation to Self-Check Tool and Return to Rmode ---")
    # Switch back to Rmode
    eval_js("""
        (() => {
            window.TempoMode.transitionContext('recovery', { skipSetupCheck: true });
            window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(0.5)
    # Open Self-Check tool from Rmode
    eval_js("""
        (() => {
            window.TempoMode.openStrack('open', { sourceContext: 'recovery' });
        })()
    """)
    time.sleep(0.5)
    sc_tool_bg = eval_js("window.getComputedStyle(document.body).backgroundColor")
    print("Self-Check tool page bg:", sc_tool_bg)
    assert sc_tool_bg == "rgb(230, 237, 231)", f"Expected rgb(230, 237, 231) (#E6EDE7) for Self-Check page, got {sc_tool_bg}"

    # Return Home from Self-Check tool
    eval_js("""
        (() => {
            window.TempoSelfCheckWorkspace.returnHome();
        })()
    """)
    time.sleep(0.5)
    post_return_bg = eval_js("window.getComputedStyle(document.body).backgroundColor")
    post_return_ctx = eval_js("window.TempoMode.getActiveContext()")
    print(f"After return from Self-Check: context = {post_return_ctx}, body bg = {post_return_bg}")
    assert post_return_ctx == "recovery", f"Expected active context 'recovery', got {post_return_ctx}"
    assert post_return_bg == "rgb(232, 236, 241)", f"Expected rgb(232, 236, 241) (#E8ECF1) for Rmode after return, got {post_return_bg}"

    print("\n--- 5. Testing Navigation to Plan Workspace and Return to Rmode ---")
    eval_js("""
        (() => {
            window.TempoApp.navigateTo('plan-workspace');
        })()
    """)
    time.sleep(0.5)
    pw_bg = eval_js("window.getComputedStyle(document.body).backgroundColor")
    print("Plan workspace body bg:", pw_bg)
    assert pw_bg == "rgb(239, 250, 255)", f"Expected rgb(239, 250, 255) (#EFFAFF) for Plan workspace, got {pw_bg}"

    eval_js("""
        (() => {
            window.TempoPlanWorkspace.navigateHome();
        })()
    """)
    time.sleep(0.5)
    pw_return_bg = eval_js("window.getComputedStyle(document.body).backgroundColor")
    print(f"After return from Plan Workspace: body bg = {pw_return_bg}")
    assert pw_return_bg == "rgb(232, 236, 241)", f"Expected rgb(232, 236, 241) (#E8ECF1) for Rmode after Plan Workspace return, got {pw_return_bg}"

    print("\n=======================================================")
    print("ALL MODE BACKGROUND CHECKS PASSED 100%!")
    print("=======================================================")

finally:
    proc.terminate()
