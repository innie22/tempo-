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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_your_tracking_item_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9602

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

targets = None
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
    print("Failed to find 127.0.0.1 page target. Available targets:", targets)
    sys.exit(1)

print("Connected to target:", page_target["url"])
ws = websocket.create_connection(page_target["webSocketDebuggerUrl"])

msg_id = 1
def send_cmd(method, params=None):
    global msg_id, ws
    cmd_obj = {"id": msg_id, "method": method, "params": params or {}}
    msg_id += 1
    ws.send(json.dumps(cmd_obj))
    while True:
        raw = ws.recv()
        res = json.loads(raw)
        if res.get("id") == cmd_obj["id"]:
            return res.get("result", {})

def eval_js(expression):
    res = send_cmd("Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True
    })
    if "exceptionDetails" in res:
        print(f"JS Exception: {res['exceptionDetails']}")
    return res.get("result", {}).get("value")

def take_screenshot(filename):
    res = send_cmd("Page.captureScreenshot", {"format": "png"})
    data = base64.b64decode(res.get("data", ""))
    target_path = os.path.join(artifact_dir, filename)
    with open(target_path, "wb") as f:
        f.write(data)
    print(f"  [Screenshot] Saved: {target_path}")

try:
    send_cmd("Page.enable")
    send_cmd("Runtime.enable")

    print("Waiting for page scripts to initialize...")
    for i in range(30):
        res = eval_js("({ ready: document.readyState, setup: typeof window.TempoRecoverySetup, workspace: typeof window.TempoSelfCheckWorkspace })")
        if res and res.get("setup") == "object" and res.get("workspace") == "object":
            print(f"Initialized after {i*0.5}s: {res}")
            break
        time.sleep(0.5)

    print("\n=== STARTING VERIFICATION: UNIFY ON 'YOUR TRACKING ITEM' MODAL ===")

    # Setup dev user and initial tracking system
    eval_js("""
        (async () => {
            const u = { id: 'local_dev_alex', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
            localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
            localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
            if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
                await window.TempoAuth.checkSession();
            }

            const uid = 'local_dev_alex';
            const initialTrackers = [
                {
                    id: 'trk_stress_1',
                    user_id: uid,
                    name: 'Trouble focusing',
                    category: 'stress_sign',
                    check_method: 'percentage',
                    is_archived: false,
                    type_label: 'Sign of stress',
                    created_at: new Date().toISOString()
                },
                {
                    id: 'trk_support_1',
                    user_id: uid,
                    name: 'Went outside',
                    category: 'supportive',
                    check_method: 'options',
                    options: ['Good', 'Not good'],
                    is_archived: false,
                    type_label: 'Supportive',
                    created_at: new Date().toISOString()
                }
            ];

            localStorage.setItem(`tempo_selfcheck_trackers_${uid}`, JSON.stringify(initialTrackers));
            localStorage.setItem(`tempo_recovery_trackers_${uid}`, JSON.stringify(initialTrackers));
            localStorage.setItem(`tempo_recovery_setup_status_${uid}`, 'completed');

            // Set up prompt and alert spies to ensure no native dialogs are used
            window.__promptCalled = false;
            window.__alertCalled = false;
            window.prompt = function(msg) { window.__promptCalled = true; throw new Error("Native prompt called"); };
            window.alert = function(msg) { window.__alertCalled = true; throw new Error("Native alert called"); };
        })();
    """)
    time.sleep(1.0)

    # -------------------------------------------------------------
    # TEST 1: Verify Duplicate Modal Is Removed
    # -------------------------------------------------------------
    print("\n--- TEST 1: Verify Duplicate Modal (#modal-selfcheck-tracker-edit) Is Removed ---")
    duplicate_check = eval_js("""
        ({
            duplicateModalExists: document.getElementById('modal-selfcheck-tracker-edit') !== null,
            duplicateFormExists: document.getElementById('form-selfcheck-tracker') !== null,
            duplicateTitleExists: document.getElementById('selfcheck-tracker-modal-title') !== null
        })
    """)
    print("Duplicate check:", duplicate_check)
    assert not duplicate_check["duplicateModalExists"], "FAIL: Duplicate modal #modal-selfcheck-tracker-edit is still present in DOM!"
    assert not duplicate_check["duplicateFormExists"], "FAIL: Duplicate form #form-selfcheck-tracker is still present in DOM!"
    print("  [PASS] Duplicate 'TRACKER CONFIGURATION' modal component completely removed from DOM.")

    # -------------------------------------------------------------
    # TEST 2: Open Tracking System Adjustment and click '+ Thêm mục tracking mới'
    # -------------------------------------------------------------
    print("\n--- TEST 2: Open Adjustment and Click Add Tracking Button ---")
    eval_js("""
        window.TempoRecoverySetup.open();
        window.TempoRecoverySetup.startAdjustmentFlow();
    """)
    time.sleep(0.5)

    # Click '+ Thêm mục tracking mới' button
    eval_js("""
        const btn = document.querySelector('button[onclick*="AddTracker"], button[onclick*="promptAddNewTracker"]');
        btn.click();
    """)
    time.sleep(0.5)

    assert not eval_js("window.__promptCalled"), "FAIL: window.prompt was called!"
    assert not eval_js("window.__alertCalled"), "FAIL: window.alert was called!"

    your_tracking_item_modal = eval_js("""
        (() => {
            const modal = document.getElementById('modal-selfcheck-adjust');
            const card = document.getElementById('selfcheck-adjust-modal-card');
            const heading = card ? card.querySelector('.font-bold.text-\\\\[\\\\#3B5441\\\\]')?.innerText : null;
            const nameInput = document.getElementById('adjust-tracker-name-input');
            const saveBtn = document.getElementById('adjust-save-submit-btn');
            const alertToggle = card ? card.querySelector('button[onclick*="toggleAdjustAlertSystem"]') : null;
            const zIndex = modal ? window.getComputedStyle(modal).zIndex : null;

            return {
                modalFound: !!modal,
                modalVisible: modal && !modal.classList.contains('hidden'),
                zIndex: zIndex,
                headingText: heading,
                hasNameInput: !!nameInput,
                nameInputPlaceholder: nameInput ? nameInput.placeholder : null,
                saveBtnText: saveBtn ? saveBtn.innerText.trim() : null,
                hasAlertToggle: !!alertToggle,
                types: Array.from(card.querySelectorAll('button[onclick*="setAdjustType"]')).map(b => b.innerText.trim()),
                methods: Array.from(card.querySelectorAll('button[onclick*="setAdjustMethod"]')).map(b => b.innerText.trim())
            };
        })()
    """)
    print("Your Tracking Item Modal State:", your_tracking_item_modal)
    assert your_tracking_item_modal["modalFound"], "FAIL: #modal-selfcheck-adjust not found!"
    assert your_tracking_item_modal["modalVisible"], "FAIL: #modal-selfcheck-adjust is not visible!"
    assert int(your_tracking_item_modal["zIndex"]) >= 70, f"Expected z-index >= 70, got {your_tracking_item_modal['zIndex']}"
    assert your_tracking_item_modal["headingText"] == "Your Tracking Item", f"Expected 'Your Tracking Item', got: {your_tracking_item_modal['headingText']}"
    assert your_tracking_item_modal["hasNameInput"], "Name input missing!"
    assert your_tracking_item_modal["saveBtnText"] == "Add tracking", f"Expected 'Add tracking' button, got: {your_tracking_item_modal['saveBtnText']}"
    assert your_tracking_item_modal["hasAlertToggle"], "Alert toggle missing!"
    assert "Sign of stress" in your_tracking_item_modal["types"] and "Supportive" in your_tracking_item_modal["types"], "Types missing!"
    assert "%" in your_tracking_item_modal["methods"] and "Options" in your_tracking_item_modal["methods"] and "Scale" in your_tracking_item_modal["methods"] and "Quantity" in your_tracking_item_modal["methods"], "Methods missing!"
    print("  [PASS] 'Your Tracking Item' modal correctly opened at z-80 with full configuration options.")

    take_screenshot("your_tracking_item_modal_in_adjustment.png")

    # -------------------------------------------------------------
    # TEST 3: Add new tracking item via 'Your Tracking Item' modal
    # -------------------------------------------------------------
    print("\n--- TEST 3: Configure and Add Tracking Item ---")
    eval_js("""
        (() => {
            // Set Name
            const nameInput = document.getElementById('adjust-tracker-name-input');
            nameInput.value = 'Evening Meditation';
            window.TempoSelfCheckWorkspace.setDraftTrackerName('Evening Meditation');

            // Select Supportive
            window.TempoSelfCheckWorkspace.setAdjustType('supportive', 'Supportive', '#859B8B');

            // Select Quantity method
            window.TempoSelfCheckWorkspace.setAdjustMethod('quantity');
            window.TempoSelfCheckWorkspace.setAdjustQuantityUnit('minutes');

            // Save
            window.TempoSelfCheckWorkspace.saveAdjustTracker();
        })()
    """)
    time.sleep(0.8)

    post_add_state = eval_js("""
        (() => {
            const modal = document.getElementById('modal-selfcheck-adjust');
            const items = document.querySelectorAll('[data-tempo-section="adjust-items-list"] > div');
            const itemTexts = Array.from(items).map(el => el.innerText);

            return {
                modalClosed: modal ? modal.classList.contains('hidden') : false,
                itemCount: items.length,
                itemTexts: itemTexts
            };
        })()
    """)
    print("Post-add state:", post_add_state)
    assert post_add_state["modalClosed"], "FAIL: Modal was not closed after Add Tracking!"
    assert post_add_state["itemCount"] == 3, f"Expected 3 items in adjustment list, got {post_add_state['itemCount']}"
    found_item = any("Evening Meditation" in t for t in post_add_state["itemTexts"])
    assert found_item, "FAIL: 'Evening Meditation' not in adjustment list!"
    print("  [PASS] Item created and adjustment list updated immediately with 3 items.")

    take_screenshot("adjustment_list_after_your_tracking_item.png")

    # -------------------------------------------------------------
    # TEST 4: Verify Single Storage Record (No Duplicates)
    # -------------------------------------------------------------
    print("\n--- TEST 4: Verify Storage Record and Alert Config ---")
    trackers = eval_js("window.TempoRecoverySelfCheck.getTrackers()")
    meditation_trackers = [t for t in trackers if t.get("name") == "Evening Meditation"]
    assert len(meditation_trackers) == 1, f"Expected exactly 1 record for 'Evening Meditation', got {len(meditation_trackers)}"
    med_t = meditation_trackers[0]
    print("Saved tracker:", json.dumps(med_t, indent=2))
    assert med_t.get("category") == "supportive", f"Expected category supportive, got {med_t.get('category')}"
    assert med_t.get("check_method") == "quantity", f"Expected check_method quantity, got {med_t.get('check_method')}"
    assert med_t.get("quantity_unit") == "minutes", f"Expected unit minutes, got {med_t.get('quantity_unit')}"
    assert med_t.get("alert_enabled") is True, "Alert enabled should be True"
    print("  [PASS] Single tracker saved in storage with complete alert configuration.")

    # -------------------------------------------------------------
    # TEST 5: Verify Stage 5 (Setup) Entry Point
    # -------------------------------------------------------------
    print("\n--- TEST 5: Verify Initial Rmode Setup Entry Point (Stage 5) ---")
    eval_js("window.TempoRecoverySetup.goToStage(5)")
    time.sleep(0.5)

    custom_btn_text = eval_js("""
        (() => {
            const container = document.getElementById('modal-recovery-setup');
            const btn = container ? container.querySelector('button[onclick*="openAddTracking"], button[onclick*="openTrackerModal"]') : null;
            return btn ? btn.innerText.trim() : null;
        })()
    """)
    print("Stage 5 custom add button:", custom_btn_text)
    assert "+ Add custom tracker" in custom_btn_text

    # Click + Add custom tracker in Stage 5
    eval_js("""
        (() => {
            const container = document.getElementById('modal-recovery-setup');
            const btn = container ? container.querySelector('button[onclick*="openAddTracking"], button[onclick*="openTrackerModal"]') : null;
            if (btn) btn.click();
        })()
    """)
    time.sleep(0.5)

    stage5_modal_open = eval_js("""
        (() => {
            const modal = document.getElementById('modal-selfcheck-adjust');
            const card = document.getElementById('selfcheck-adjust-modal-card');
            const heading = card ? card.querySelector('.font-bold.text-\\\\[\\\\#3B5441\\\\]')?.innerText : null;
            return {
                visible: modal && !modal.classList.contains('hidden'),
                heading: heading
            };
        })()
    """)
    print("Stage 5 modal check:", stage5_modal_open)
    assert stage5_modal_open["visible"], "Modal not visible from Stage 5!"
    assert stage5_modal_open["heading"] == "Your Tracking Item", f"Expected 'Your Tracking Item', got: {stage5_modal_open['heading']}"
    print("  [PASS] Stage 5 opens 'Your Tracking Item' modal.")

    # Close modal
    eval_js("window.TempoSelfCheckWorkspace.closeAdjustModal()")
    time.sleep(0.3)
    assert eval_js("document.getElementById('modal-selfcheck-adjust').classList.contains('hidden')")
    print("  [PASS] Cancel closes modal cleanly.")

    # -------------------------------------------------------------
    # TEST 6: Verify Dashboard Entry Point
    # -------------------------------------------------------------
    print("\n--- TEST 6: Verify Dashboard Entry Point ---")
    eval_js("""
        window.TempoRecoverySetup.close();
        if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
            window.TempoMode.renderRmodeHome();
        }
        window.TempoSelfCheckWorkspace.openAddTracking();
    """)
    time.sleep(0.5)

    dash_modal_open = eval_js("""
        (() => {
            const modal = document.getElementById('modal-selfcheck-adjust');
            const card = document.getElementById('selfcheck-adjust-modal-card');
            const heading = card ? card.querySelector('.font-bold.text-\\\\[\\\\#3B5441\\\\]')?.innerText : null;
            return {
                visible: modal && !modal.classList.contains('hidden'),
                heading: heading
            };
        })()
    """)
    print("Dashboard modal check:", dash_modal_open)
    assert dash_modal_open["visible"], "Modal not visible from Dashboard entry!"
    assert dash_modal_open["heading"] == "Your Tracking Item", f"Expected 'Your Tracking Item', got: {dash_modal_open['heading']}"
    print("  [PASS] Dashboard entry point opens 'Your Tracking Item' modal.")

    take_screenshot("your_tracking_item_modal_dashboard.png")

    eval_js("window.TempoSelfCheckWorkspace.closeAdjustModal()")
    time.sleep(0.3)

    print("\n>>> ALL 6 TESTS PASSED! ONE UNIFIED 'YOUR TRACKING ITEM' MODAL! <<<")

finally:
    try:
        ws.close()
    except Exception:
        pass
    proc.terminate()
    print("Edge process terminated.")
