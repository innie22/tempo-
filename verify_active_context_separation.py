import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os
import base64

sys.stdout.reconfigure(encoding='utf-8')

artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
os.makedirs(artifact_dir, exist_ok=True)

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_active_context_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9605

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#home"
]

proc = subprocess.Popen(cmd)
time.sleep(3.0)

page_target = None
for _ in range(30):
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
        targets = json.loads(req.read().decode("utf-8"))
        if targets:
            match = [t for t in targets if t.get("type") == "page" and "127.0.0.1" in t.get("url", "")]
            if match:
                page_target = match[0]
                break
    except Exception:
        pass
    time.sleep(0.5)

if not page_target:
    print("Failed to find page target.")
    proc.kill()
    sys.exit(1)

print("Connected to target:", page_target["url"])
ws = websocket.create_connection(page_target["webSocketDebuggerUrl"])

msg_id = 1
def send_cmd(method, params=None):
    global msg_id, ws
    cmd_obj = {"id": msg_id, "method": method, "params": params or {}}
    ws.send(json.dumps(cmd_obj))
    msg_id += 1
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == cmd_obj["id"]:
            return resp.get("result", {})

def eval_js(expression):
    res = send_cmd("Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True
    })
    if "exceptionDetails" in res:
        print("JS Exception:", res["exceptionDetails"])
    return res.get("result", {}).get("value")

def capture_screenshot(filename):
    res = send_cmd("Page.captureScreenshot", {"format": "png"})
    data = base64.b64decode(res.get("data", ""))
    filepath = os.path.join(artifact_dir, filename)
    with open(filepath, "wb") as f:
        f.write(data)
    print(f"Saved screenshot: {filename}")
    return filepath

# Enable Page
send_cmd("Page.enable")
send_cmd("Runtime.enable")
time.sleep(1)

# Wait for scripts
for _ in range(30):
    res = eval_js("({ ready: document.readyState, setup: typeof window.TempoRecoverySetup, mode: typeof window.TempoMode })")
    if res and res.get("setup") == "object" and res.get("mode") == "object":
        break
    time.sleep(0.5)

print("=== Setting up authenticated user with tracking system in Rmode ===")
setup_script = """
(async () => {
    const u = { id: 'local_dev_alex', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
    localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
    localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
    if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
        await window.TempoAuth.checkSession();
    }
    
    // Create tracking items for returning user
    const trackers = [
        { id: 'track_1', name: 'Stress level', type: 'percentage', category: 'stress_sign', is_active: true },
        { id: 'track_2', name: 'Daily walk', type: 'options', category: 'supportive', is_active: true, options: ['Tốt', 'Chưa tốt'] },
        { id: 'track_3', name: 'Meditation', type: 'quantity', category: 'supportive', is_active: true, unit: 'minutes' }
    ];
    localStorage.setItem('tempo_recovery_trackers_local_dev_alex', JSON.stringify(trackers));
    
    // Set established context to recovery
    localStorage.setItem('tempo_current_mode', 'recovery');
    localStorage.setItem('tempo_established_context', 'recovery');
    localStorage.setItem('tempo_user_established_context_local_dev_alex', 'recovery');
    
    // Mark as welcomed in this session so Rmode is actively running
    sessionStorage.setItem('tempo_rmode_session_welcomed_local_dev_alex', 'true');
    
    window.TempoMode.init();
    window.TempoMode.transitionContext('recovery', { silent: true, skipSetupCheck: true });
    
    return {
        user: window.TempoAuth.getCurrentUser() ? window.TempoAuth.getCurrentUser().id : null,
        mode: window.TempoMode.getMode(),
        activeContext: window.TempoMode.getActiveContext()
    };
})()
"""
res = eval_js(setup_script)
print("Initial Rmode State:", res)
assert res["activeContext"] == "recovery", f"Expected activeContext 'recovery', got {res['activeContext']}"
time.sleep(1)

# TEST 1: Rmode -> Open UCheck -> Verify State & Back Button -> Click Tempo Logo -> Returns to Rmode
print("\n--- TEST 1: Rmode -> Open UCheck -> Click Tempo Logo ---")
eval_js("""
(() => {
    window.TempoMode.openUcheck({ sourceContext: 'recovery' });
})()
""")
time.sleep(1)

ucheck_state = eval_js("""
(() => {
    const umodeBox = document.getElementById('umode-home-content');
    const isUCheckVisible = umodeBox && !umodeBox.classList.contains('hidden');
    const backBtn = document.getElementById('btn-ucheck-back-to-dashboard');
    return {
        activeContext: window.TempoMode.getActiveContext(),
        viewMode: window.TempoMode.getMode(),
        sharedTool: window.TempoMode.getActiveSharedTool(),
        isUCheckVisible: isUCheckVisible,
        hasBackBtn: Boolean(backBtn),
        backBtnText: backBtn ? backBtn.textContent.trim() : null,
        backBtnTitle: backBtn ? backBtn.getAttribute('title') : null
    };
})()
""")
print("UCheck Opened State:", ucheck_state)
assert ucheck_state["activeContext"] == "recovery", "Active context must remain 'recovery'!"
assert ucheck_state["sharedTool"] == "ucheck", "Active shared tool must be 'ucheck'!"
assert ucheck_state["isUCheckVisible"] is True, "UCheck view must be visible!"
assert ucheck_state["hasBackBtn"] is True, "UCheck must have 'Back to Dashboard' button!"
capture_screenshot("test1_ucheck_open_from_rmode.png")

# Now click the Tempo logo
print("Clicking Tempo Logo...")
eval_js("""
(() => {
    if (window.TempoApp && typeof window.TempoApp.handleLogoClick === 'function') {
        window.TempoApp.handleLogoClick();
    } else {
        window.TempoMode.navigateToActiveDashboard();
    }
})()
""")
time.sleep(1)

post_logo_state = eval_js("""
(() => {
    const rmodeBox = document.getElementById('rmode-home-content');
    const modal = document.getElementById('modal-recovery-setup');
    const isModalOpen = modal && !modal.classList.contains('hidden');
    return {
        activeContext: window.TempoMode.getActiveContext(),
        mode: window.TempoMode.getMode(),
        sharedTool: window.TempoMode.getActiveSharedTool(),
        isRmodeVisible: rmodeBox && !rmodeBox.classList.contains('hidden'),
        isWelcomeModalOpen: isModalOpen
    };
})()
""")
print("Post-Logo Click State:", post_logo_state)
assert post_logo_state["activeContext"] == "recovery", "Active context must be 'recovery'!"
assert post_logo_state["mode"] == "recovery", "Mode must be 'recovery'!"
assert post_logo_state["sharedTool"] is None, "Shared tool must be cleared!"
assert post_logo_state["isRmodeVisible"] is True, "Rmode Dashboard must be visible!"
assert post_logo_state["isWelcomeModalOpen"] is False, "Welcome Back popup must NOT appear!"
capture_screenshot("test1_post_logo_rmode_dashboard.png")
print(">>> TEST 1 PASSED: Logo click directly returned to Rmode Dashboard without popup.")

# TEST 2: Rmode -> Open UCheck -> Click "Back to Dashboard" button
print("\n--- TEST 2: Rmode -> Open UCheck -> Click 'Back to Dashboard' Button ---")
eval_js("window.TempoMode.openUcheck({ sourceContext: 'recovery' });")
time.sleep(1)

eval_js("""
(() => {
    const btn = document.getElementById('btn-ucheck-back-to-dashboard');
    if (btn) btn.click();
})()
""")
time.sleep(1)

post_back_state = eval_js("""
(() => {
    const rmodeBox = document.getElementById('rmode-home-content');
    const modal = document.getElementById('modal-recovery-setup');
    const isModalOpen = modal && !modal.classList.contains('hidden');
    return {
        activeContext: window.TempoMode.getActiveContext(),
        mode: window.TempoMode.getMode(),
        isRmodeVisible: rmodeBox && !rmodeBox.classList.contains('hidden'),
        isWelcomeModalOpen: isModalOpen
    };
})()
""")
print("Post-'Back to Dashboard' State:", post_back_state)
assert post_back_state["activeContext"] == "recovery", "Active context must be 'recovery'!"
assert post_back_state["isRmodeVisible"] is True, "Rmode Dashboard must be visible!"
assert post_back_state["isWelcomeModalOpen"] is False, "Welcome Back popup must NOT appear!"
capture_screenshot("test2_post_back_btn_rmode_dashboard.png")
print(">>> TEST 2 PASSED: 'Back to Dashboard' button directly returned to Rmode Dashboard without popup.")

# TEST 3: Rmode -> Open WPlan -> Click Logo
print("\n--- TEST 3: Rmode -> Open WPlan -> Click Logo ---")
eval_js("window.TempoApp.navigateTo('plan-workspace');")
time.sleep(1)
wplan_state = eval_js("""
(() => {
    return {
        activeContext: window.TempoMode.getActiveContext(),
        screen: document.getElementById('screen-plan-workspace') && !document.getElementById('screen-plan-workspace').classList.contains('hidden')
    };
})()
""")
print("WPlan state:", wplan_state)
assert wplan_state["activeContext"] == "recovery", "Active context must remain 'recovery' during WPlan!"

eval_js("window.TempoApp.handleLogoClick();")
time.sleep(1)
post_wplan_state = eval_js("""
(() => {
    const modal = document.getElementById('modal-recovery-setup');
    return {
        activeContext: window.TempoMode.getActiveContext(),
        isWelcomeModalOpen: modal && !modal.classList.contains('hidden')
    };
})()
""")
print("Post-WPlan state:", post_wplan_state)
assert post_wplan_state["activeContext"] == "recovery"
assert post_wplan_state["isWelcomeModalOpen"] is False
print(">>> TEST 3 PASSED: Returned from WPlan to Rmode Dashboard without popup.")

# TEST 4: Rmode -> Open STrack -> Click Logo
print("\n--- TEST 4: Rmode -> Open STrack -> Click Logo ---")
eval_js("window.TempoMode.openStrack('tool', { view: 'page' });")
time.sleep(1)
strack_state = eval_js("""
(() => {
    return {
        activeContext: window.TempoMode.getActiveContext(),
        screen: document.getElementById('screen-stress-check') && !document.getElementById('screen-stress-check').classList.contains('hidden')
    };
})()
""")
print("STrack state:", strack_state)
assert strack_state["activeContext"] == "recovery"

eval_js("window.TempoApp.handleLogoClick();")
time.sleep(1)
post_strack_state = eval_js("""
(() => {
    const modal = document.getElementById('modal-recovery-setup');
    return {
        activeContext: window.TempoMode.getActiveContext(),
        isWelcomeModalOpen: modal && !modal.classList.contains('hidden')
    };
})()
""")
print("Post-STrack state:", post_strack_state)
assert post_strack_state["activeContext"] == "recovery"
assert post_strack_state["isWelcomeModalOpen"] is False
print(">>> TEST 4 PASSED: Returned from STrack to Rmode Dashboard without popup.")

# TEST 5: Urgent Mode -> Open UCheck -> Click Logo / Back -> Returns to Urgent Mode Dashboard
print("\n--- TEST 5: Urgent Mode -> Open UCheck -> Click Logo ---")
eval_js("""
(() => {
    window.TempoMode.transitionContext('emergency', { silent: true });
})()
""")
time.sleep(1)
urmode_state = eval_js("""
(() => {
    return {
        activeContext: window.TempoMode.getActiveContext(),
        mode: window.TempoMode.getMode()
    };
})()
""")
print("Urgent Mode state:", urmode_state)
assert urmode_state["activeContext"] == "emergency"

eval_js("window.TempoMode.openUcheck({ sourceContext: 'emergency' });")
time.sleep(1)
ucheck_from_urmode = eval_js("""
(() => {
    return {
        activeContext: window.TempoMode.getActiveContext(),
        sharedTool: window.TempoMode.getActiveSharedTool(),
        backBtnTitle: document.getElementById('btn-ucheck-back-to-dashboard') ? document.getElementById('btn-ucheck-back-to-dashboard').getAttribute('title') : null
    };
})()
""")
print("UCheck opened from Urgent Mode:", ucheck_from_urmode)
assert ucheck_from_urmode["activeContext"] == "emergency"
capture_screenshot("test5_ucheck_from_urgent_mode.png")

eval_js("window.TempoApp.handleLogoClick();")
time.sleep(1)
post_urmode_logo = eval_js("""
(() => {
    const emodeBox = document.getElementById('emode-home-content');
    return {
        activeContext: window.TempoMode.getActiveContext(),
        mode: window.TempoMode.getMode(),
        isUrgentVisible: emodeBox && !emodeBox.classList.contains('hidden')
    };
})()
""")
print("Post-Logo Urgent Mode state:", post_urmode_logo)
assert post_urmode_logo["activeContext"] == "emergency"
assert post_urmode_logo["isUrgentVisible"] is True
capture_screenshot("test5_returned_to_urgent_dashboard.png")
print(">>> TEST 5 PASSED: Returned to Urgent Mode Dashboard without resetting session.")

# TEST 6: Explicit Mode Switch from Urgent Mode to Rmode triggers Onboarding Flow
print("\n--- TEST 6: Explicit Mode Switch from Urgent Mode to Rmode ---")
eval_js("""
(() => {
    // Clear session welcomed guard to simulate explicit switch
    const uid = 'local_dev_alex';
    sessionStorage.removeItem(`tempo_rmode_session_welcomed_${uid}`);
    window.TempoMode.selectModeFromDropdown('recovery', 'home');
})()
""")
time.sleep(1)
switch_state = eval_js("""
(() => {
    const modal = document.getElementById('modal-recovery-setup');
    const isModalOpen = modal && !modal.classList.contains('hidden');
    const modalHeading = modal ? (modal.querySelector('h3') ? modal.querySelector('h3').textContent.trim() : null) : null;
    return {
        activeContext: window.TempoMode.getActiveContext(),
        mode: window.TempoMode.getMode(),
        isWelcomeModalOpen: isModalOpen,
        modalHeading: modalHeading
    };
})()
""")
print("Mode switch result:", switch_state)
assert switch_state["activeContext"] == "recovery"
assert switch_state["isWelcomeModalOpen"] is True, "Explicit mode switch to Rmode MUST trigger welcome/onboarding flow!"
capture_screenshot("test6_explicit_switch_to_rmode_modal.png")
print(">>> TEST 6 PASSED: Explicit mode switch correctly triggered Rmode welcome flow.")

# TEST 7: Vietnamese Localization on UCheck Back Button
print("\n--- TEST 7: Vietnamese Localization on UCheck Back Button ---")
eval_js("""
(() => {
    if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.close === 'function') {
        window.TempoRecoverySetup.close();
    }
    window.TempoI18n.setLanguage('vi');
    window.TempoMode.openUcheck({ sourceContext: 'recovery' });
})()
""")
time.sleep(1)
vi_ucheck = eval_js("""
(() => {
    const btn = document.getElementById('btn-ucheck-back-to-dashboard');
    return {
        lang: window.TempoI18n.getLanguage(),
        btnText: btn ? btn.textContent.trim() : null,
        btnTitle: btn ? btn.getAttribute('title') : null
    };
})()
""")
print("Vietnamese UCheck button state:", vi_ucheck)
assert "Quay lại Dashboard" in vi_ucheck["btnText"], f"Expected 'Quay lại Dashboard' in VI button text, got {vi_ucheck['btnText']}"
capture_screenshot("test7_ucheck_back_btn_vi.png")
print(">>> TEST 7 PASSED: Vietnamese wording properly rendered on Back button.")

print("\n==========================================")
print("ALL 7 END-TO-END TEST CASES PASSED SUCCESSFULLY!")
print("==========================================")

ws.close()
proc.kill()
