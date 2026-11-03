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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_add_tracker_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9598

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
        res = eval_js("({ ready: document.readyState, setup: typeof window.TempoRecoverySetup, selfCheck: typeof window.TempoRecoverySelfCheck })")
        if res and res.get("setup") == "object" and res.get("selfCheck") == "object":
            print(f"Initialized after {i*0.5}s: {res}")
            break
        time.sleep(0.5)

    print("\n=== STARTING VERIFICATION: REUSE ADD TRACKING ITEM MODAL ===")

    # Setup dev user and initial tracking system
    eval_js("""
        (async () => {
            const u = { id: 'local_dev_alex', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
            localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
            localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
            if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
                await window.TempoAuth.checkSession();
            }

            // Set up active trackers
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
                    check_method: 'yes_no',
                    is_archived: false,
                    type_label: 'Supportive',
                    created_at: new Date().toISOString()
                },
                {
                    id: 'trk_support_2',
                    user_id: uid,
                    name: 'Water',
                    category: 'supportive',
                    check_method: 'quantity',
                    quantity_unit: 'glasses',
                    is_archived: false,
                    type_label: 'Supportive',
                    created_at: new Date().toISOString()
                }
            ];

            localStorage.setItem(`tempo_selfcheck_trackers_${uid}`, JSON.stringify(initialTrackers));
            localStorage.setItem(`tempo_recovery_trackers_${uid}`, JSON.stringify(initialTrackers));
            localStorage.setItem(`tempo_recovery_setup_status_${uid}`, 'completed');
            localStorage.setItem('tempo_language', 'vi');

            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('vi');
            }

            // Install spy on window.prompt to detect if any prompt() is invoked
            window.__promptCalled = false;
            window.__lastPromptMsg = null;
            window.prompt = function(msg) {
                window.__promptCalled = true;
                window.__lastPromptMsg = msg;
                throw new Error("FAIL: window.prompt was called: " + msg);
            };
        })();
    """)
    time.sleep(1.0)

    # -------------------------------------------------------------
    # STEP 1: Enter Rmode Tracking Adjustment Flow (Step 1)
    # -------------------------------------------------------------
    print("\n--- TEST 1: Launch Tracking System Adjustment in Vietnamese ---")
    eval_js("""
        window.TempoRecoverySetup.open();
        window.TempoRecoverySetup.startAdjustmentFlow();
    """)
    time.sleep(0.8)

    stage1_info = eval_js("""
        (() => {
            const container = document.getElementById('recovery-setup-stage-container');
            const items = container ? container.querySelectorAll('[data-tempo-section="adjust-items-list"] > div') : [];
            const addBtn = container ? container.querySelector('button[onclick*="AddTracker"], button[onclick*="promptAddNewTracker"]') : null;
            return {
                title: container ? container.querySelector('h3')?.innerText : null,
                itemCount: items.length,
                addBtnText: addBtn ? addBtn.innerText.trim() : null
            };
        })()
    """)
    print("Stage 1 Info:", stage1_info)
    assert "Điều chỉnh các mục tracking" in stage1_info["title"], f"Unexpected title: {stage1_info['title']}"
    assert stage1_info["itemCount"] == 3, f"Expected 3 initial items, got {stage1_info['itemCount']}"
    assert "+ Thêm mục tracking mới" in stage1_info["addBtnText"], f"Expected '+ Thêm mục tracking mới', got {stage1_info['addBtnText']}"
    print("  [PASS] Step 1 Adjustment rendered correctly with 3 items.")

    # -------------------------------------------------------------
    # STEP 2: Click "+ Thêm mục tracking mới"
    # -------------------------------------------------------------
    print("\n--- TEST 2: Click '+ Thêm mục tracking mới' and verify Add Tracking Item modal ---")
    eval_js("""
        const btn = document.querySelector('button[onclick*="AddTracker"], button[onclick*="promptAddNewTracker"]');
        btn.click();
    """)
    time.sleep(0.5)

    prompt_status = eval_js("({ promptCalled: window.__promptCalled, lastMsg: window.__lastPromptMsg })")
    print("Prompt spy status:", prompt_status)
    assert not prompt_status["promptCalled"], f"Native window.prompt was called! {prompt_status['lastMsg']}"
    print("  [PASS] Native window.prompt was NOT called.")

    modal_state = eval_js("""
        (() => {
            const modal = document.getElementById('modal-selfcheck-tracker-edit');
            const titleEl = document.getElementById('selfcheck-tracker-modal-title');
            const nameInput = document.getElementById('tracker-input-name');
            const catInputs = document.querySelectorAll('input[name="tracker_category"]');
            const methodInputs = document.querySelectorAll('input[name="tracker_method"]');
            const saveBtn = modal ? modal.querySelector('button[type="submit"]') : null;
            const cancelBtn = modal ? modal.querySelector('button[onclick*="closeTrackerModal"]') : null;
            const zIndex = modal ? window.getComputedStyle(modal).zIndex : null;

            return {
                exists: !!modal,
                visible: modal && !modal.classList.contains('hidden'),
                zIndex: zIndex,
                title: titleEl ? titleEl.innerText.trim() : null,
                hasNameInput: !!nameInput,
                categoriesCount: catInputs.length,
                methodsCount: methodInputs.length,
                saveBtnText: saveBtn ? saveBtn.innerText.trim() : null,
                cancelBtnText: cancelBtn ? cancelBtn.innerText.trim() : null
            };
        })()
    """)
    print("Add Tracker Modal state:", modal_state)
    assert modal_state["exists"], "modal-selfcheck-tracker-edit not found in DOM"
    assert modal_state["visible"], "modal-selfcheck-tracker-edit is not visible"
    assert int(modal_state["zIndex"]) >= 70, f"Expected z-index >= 70, got {modal_state['zIndex']}"
    assert "Thêm mục tracking" in modal_state["title"] or "TRACKER CONFIGURATION" in modal_state["title"], f"Unexpected title: {modal_state['title']}"
    assert modal_state["hasNameInput"], "Name input field missing"
    assert modal_state["categoriesCount"] == 3, f"Expected 3 categories, got {modal_state['categoriesCount']}"
    assert modal_state["methodsCount"] == 4, f"Expected 4 methods, got {modal_state['methodsCount']}"
    print("  [PASS] Add Tracking Item modal is visible, stacked properly (z-80), and fully configured.")

    take_screenshot("add_tracker_modal_open_vi.png")

    # -------------------------------------------------------------
    # STEP 3: Fill in Tracker details and submit
    # -------------------------------------------------------------
    print("\n--- TEST 3: Configure and submit new tracker ('Tập giãn cơ buổi tối', Supportive, Quantity/phút) ---")
    eval_js("""
        (() => {
            // Fill name
            const nameInput = document.getElementById('tracker-input-name');
            nameInput.value = 'Tập giãn cơ buổi tối';

            // Select supportive category
            const supRadio = document.querySelector('input[name="tracker_category"][value="supportive"]');
            if (supRadio) {
                supRadio.checked = true;
                window.TempoRecoverySelfCheck.onCategoryChanged();
            }

            // Select quantity check method
            const qtyRadio = document.querySelector('input[name="tracker_method"][value="quantity"]');
            if (qtyRadio) {
                qtyRadio.checked = true;
                window.TempoRecoverySelfCheck.onMethodChanged();
            }

            // Set quantity unit
            const unitInput = document.getElementById('tracker-quantity-unit');
            if (unitInput) unitInput.value = 'phút';

            // Submit form
            const form = document.getElementById('form-selfcheck-tracker');
            form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        })()
    """)
    time.sleep(0.6)

    post_submit_state = eval_js("""
        (() => {
            const modal = document.getElementById('modal-selfcheck-tracker-edit');
            const container = document.getElementById('recovery-setup-stage-container');
            const items = container ? container.querySelectorAll('[data-tempo-section="adjust-items-list"] > div') : [];
            const itemTexts = Array.from(items).map(el => el.innerText);

            return {
                modalClosed: modal ? modal.classList.contains('hidden') : false,
                itemCount: items.length,
                itemTexts: itemTexts
            };
        })()
    """)
    print("Post-submit state:", post_submit_state)
    assert post_submit_state["modalClosed"], "modal-selfcheck-tracker-edit should be closed after submit"
    assert post_submit_state["itemCount"] == 4, f"Expected 4 items in adjustment list, got {post_submit_state['itemCount']}"
    
    found_new_item = any("Tập giãn cơ buổi tối" in text for text in post_submit_state["itemTexts"])
    assert found_new_item, "Newly added tracker 'Tập giãn cơ buổi tối' not found in adjustment list!"
    print("  [PASS] Add Tracking Item modal closed and Adjustment list updated immediately with 4 items.")

    take_screenshot("adjust_trackers_after_add_vi.png")

    # -------------------------------------------------------------
    # STEP 4: Verify Persistence in Storage
    # -------------------------------------------------------------
    print("\n--- TEST 4: Verify persistence using existing Tracking System logic ---")
    persisted_trackers = eval_js("""
        window.TempoRecoverySelfCheck.getTrackers()
    """)
    print(f"Persisted trackers count: {len(persisted_trackers)}")
    saved = next((t for t in persisted_trackers if t.get("name") == "Tập giãn cơ buổi tối"), None)
    assert saved is not None, "Newly added tracker was not saved in localStorage trackers!"
    print("Persisted Tracker Record:", json.dumps(saved, indent=2, ensure_ascii=False))
    assert saved.get("category") == "supportive", f"Expected category supportive, got {saved.get('category')}"
    assert saved.get("check_method") == "quantity", f"Expected check_method quantity, got {saved.get('check_method')}"
    assert saved.get("quantity_unit") == "phút", f"Expected unit 'phút', got {saved.get('quantity_unit')}"
    print("  [PASS] Tracker successfully saved via existing createTracker / persistence pipeline.")

    # -------------------------------------------------------------
    # STEP 5: Verify Edit & Flow Continuation through Step 3 Confirmation
    # -------------------------------------------------------------
    print("\n--- TEST 5: Verify Step 1 Edit sub-modal and Step 3 Confirmation ---")
    # Click edit on the newly added item (index 3)
    eval_js("""
        window.TempoRecoverySetup.openEditTrackerInAdjustment(3, false);
    """)
    time.sleep(0.3)
    edit_modal_visible = eval_js("document.getElementById('adjust-edit-name') !== null")
    assert edit_modal_visible, "Adjustment Edit sub-modal did not open for new tracker"

    # Update unit in edit sub-modal
    eval_js("""
        (() => {
            const unit = document.getElementById('adjust-edit-unit');
            if (unit) unit.value = 'lần';
            window.TempoRecoverySetup.saveTrackerEditInAdjustment(3, false);
        })()
    """)
    time.sleep(0.3)
    updated_text = eval_js("document.querySelector('[data-tempo-section=\"adjust-items-list\"]').innerText")
    assert "lần" in updated_text, "Edited unit 'lần' not reflected in adjustment list"
    print("  [PASS] Newly added item can be edited in Adjustment screen.")

    # Advance to Step 3: Confirmation
    eval_js("""
        window.TempoRecoverySetup.goToStage('adjust_review');
    """)
    time.sleep(0.4)

    review_text = eval_js("document.getElementById('recovery-setup-stage-container').innerText")
    assert "Tập giãn cơ buổi tối" in review_text, "New tracker not displayed in Step 3 Review!"
    assert "4" in review_text, "Expected 4 active items in review summary"
    print("  [PASS] Step 3 Review includes the new tracker.")

    # Execute confirmation
    eval_js("""
        window.TempoRecoverySetup.executeAdjustSetupConfirm();
    """)
    time.sleep(0.8)

    active_setups = eval_js("window.TempoRecoverySelfCheck.getSetups()")
    print("Active setups count:", len(active_setups))
    assert len(active_setups) > 0, "No setups found after confirmation"
    latest_setup = active_setups[-1]
    assert saved["id"] in latest_setup.get("tracker_ids", []), f"New tracker {saved['id']} not in active setup tracker_ids: {latest_setup.get('tracker_ids')}"
    print("  [PASS] Adjustment confirmation committed new tracker to active setup record.")

    # -------------------------------------------------------------
    # STEP 6: Verify English Mode Modal
    # -------------------------------------------------------------
    print("\n--- TEST 6: Verify English Localization ---")
    eval_js("""
        window.TempoI18n.setLanguage('en');
        window.TempoRecoverySetup.open();
        window.TempoRecoverySetup.startAdjustmentFlow();
    """)
    time.sleep(0.5)

    en_add_btn = eval_js("""
        (() => {
            const btn = document.querySelector('button[onclick*="AddTracker"], button[onclick*="promptAddNewTracker"]');
            return btn ? btn.innerText.trim() : null;
        })()
    """)
    print("English Add Button text:", en_add_btn)
    assert "+ Add new tracking item" in en_add_btn, f"Expected '+ Add new tracking item', got {en_add_btn}"

    # Open modal in English
    eval_js("window.TempoRecoverySetup.openAddTrackerInAdjustment()")
    time.sleep(0.5)

    en_modal_state = eval_js("""
        (() => {
            const modal = document.getElementById('modal-selfcheck-tracker-edit');
            const titleEl = document.getElementById('selfcheck-tracker-modal-title');
            return {
                visible: modal && !modal.classList.contains('hidden'),
                title: titleEl ? titleEl.innerText.trim() : null
            };
        })()
    """)
    print("English Modal State:", en_modal_state)
    assert en_modal_state["visible"], "Modal should be visible in English mode"
    assert "Add Tracking Item" in en_modal_state["title"], f"Expected 'Add Tracking Item', got {en_modal_state['title']}"
    print("  [PASS] English mode displays 'Add Tracking Item' title properly.")

    take_screenshot("add_tracker_modal_open_en.png")

    # Close modal
    eval_js("window.TempoRecoverySelfCheck.closeTrackerModal()")
    time.sleep(0.3)
    modal_is_closed = eval_js("document.getElementById('modal-selfcheck-tracker-edit').classList.contains('hidden')")
    assert modal_is_closed, "Modal should be closed"
    print("  [PASS] Modal cancel/close works properly.")

    # Final prompt check
    assert not eval_js("window.__promptCalled"), "window.prompt was invoked at some point!"
    print("\n>>> ALL 6 TESTS PASSED SUCCESSFULLY! ZERO PROMPT CALLS! <<<")

finally:
    try:
        ws.close()
    except Exception:
        pass
    proc.terminate()
    print("Edge process terminated.")
