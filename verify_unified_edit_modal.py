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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_unified_edit_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9604

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

    print("\n=== STARTING VERIFICATION: UNIFIED EDIT TRACKING MODAL ===")

    # Initialize environment in Vietnamese
    eval_js("""
    (() => {
        localStorage.setItem('tempo_language', 'vi');
        if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
            window.TempoI18n.setLanguage('vi');
        }
        localStorage.setItem('tempo_active_context', 'rmode');
        localStorage.setItem('tempo_user_id', 'test_unified_edit_user');

        const state = {
            version: 1,
            phase: 'established',
            activePlan: { title: 'Standard Recovery' },
            onboardingCompleted: true,
            needsReview: false
        };
        localStorage.setItem('tempo_recovery_state', JSON.stringify(state));

        // Clear existing trackers and seed mock trackers via API
        localStorage.removeItem('tempo_selfcheck_trackers_' + (window.TempoAuth && window.TempoAuth.getCurrentUserId ? window.TempoAuth.getCurrentUserId() : 'local_user'));
        localStorage.removeItem('tempo_selfcheck_trackers_local_user');

        const t1 = window.TempoRecoverySelfCheck.createTracker({
            name: 'Tension',
            category: 'stress_sign',
            type_id: 'stress_sign',
            type_label: 'Dấu hiệu căng thẳng',
            type_color: '#C34D2E',
            check_method: 'percentage',
            alert_enabled: true,
            alert_config: { operator: 'more_than', threshold: 60, days: 4 }
        });

        const t2 = window.TempoRecoverySelfCheck.createTracker({
            name: 'Đi bộ',
            category: 'supportive',
            type_id: 'supportive',
            type_label: 'Yếu tố hỗ trợ',
            type_color: '#859B8B',
            check_method: 'quantity',
            quantity_unit: 'phút',
            alert_enabled: true,
            alert_config: { operator: 'more_than', threshold: 30, days: 3 }
        });

        window.__test_t1_id = t1.id;
        window.__test_t2_id = t2.id;
    })()
    """)
    time.sleep(0.5)

    # 1. Open Step 1 of Tracking Adjustment
    print("\n--- TEST 1: Open Step 1 and Click 'Chỉnh sửa' on Tension ---")
    eval_js("""
    (() => {
        if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.startAdjustmentFlow === 'function') {
            window.TempoRecoverySetup.startAdjustmentFlow();
        }
    })()
    """)
    time.sleep(0.5)

    # Click Edit on the first tracker
    eval_js("""
    (() => {
        if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.openEditTrackerInAdjustment === 'function') {
            window.TempoRecoverySetup.openEditTrackerInAdjustment(0, false);
        }
    })()
    """)
    time.sleep(0.5)

    edit_modal_check_vi = eval_js("""
    (() => {
        const sharedModal = document.getElementById('modal-selfcheck-adjust');
        const card = document.getElementById('selfcheck-adjust-modal-card');
        const titleEl = card ? card.querySelector('.space-y-1 span') : null;
        const nameInp = document.getElementById('adjust-tracker-name-input');
        const alertThresholdInp = document.getElementById('adjust-alert-threshold');
        const alertDaysInp = document.getElementById('adjust-alert-days');
        const saveBtn = document.getElementById('adjust-save-submit-btn');

        // Check if old simplified modal is in DOM
        const oldSimplifiedNameInp = document.getElementById('adjust-edit-name');
        const oldSimplifiedMethodSel = document.getElementById('adjust-edit-method');

        return {
            sharedModalVisible: sharedModal ? !sharedModal.classList.contains('hidden') : false,
            titleText: titleEl ? titleEl.textContent.trim() : null,
            prefilledName: nameInp ? nameInp.value : null,
            prefilledThreshold: alertThresholdInp ? alertThresholdInp.value : null,
            prefilledDays: alertDaysInp ? alertDaysInp.value : null,
            saveBtnText: saveBtn ? saveBtn.textContent.trim() : null,
            hasOldSimplifiedModal: !!(oldSimplifiedNameInp || oldSimplifiedMethodSel)
        };
    })()
    """)
    print("Edit Modal in VI Check:", json.dumps(edit_modal_check_vi, indent=2, ensure_ascii=False))
    take_screenshot("unified_edit_modal_step1_vi.png")

    assert edit_modal_check_vi.get("sharedModalVisible") is True, "Shared modal #modal-selfcheck-adjust must be visible"
    assert edit_modal_check_vi.get("titleText") == "Chỉnh sửa mục tracking", f"Title should be 'Chỉnh sửa mục tracking', got: {edit_modal_check_vi.get('titleText')}"
    assert edit_modal_check_vi.get("prefilledName") == "Tension", f"Name should be prefilled with 'Tension', got: {edit_modal_check_vi.get('prefilledName')}"
    assert edit_modal_check_vi.get("prefilledThreshold") == "60", f"Threshold should be 60, got: {edit_modal_check_vi.get('prefilledThreshold')}"
    assert edit_modal_check_vi.get("prefilledDays") == "4", f"Days should be 4, got: {edit_modal_check_vi.get('prefilledDays')}"
    assert edit_modal_check_vi.get("saveBtnText") == "Lưu thay đổi", f"Button text should be 'Lưu thay đổi', got: {edit_modal_check_vi.get('saveBtnText')}"
    assert edit_modal_check_vi.get("hasOldSimplifiedModal") is False, "Old simplified edit modal must be completely removed from DOM"
    print("✓ TEST 1 PASSED: Shared modal opened for editing with pre-filled fields and 'Chỉnh sửa mục tracking' title!")

    # 2. Live language switch in Edit mode to English
    print("\n--- TEST 2: Live switch language to English in Edit mode ---")
    eval_js("""
    (() => {
        if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
            window.TempoI18n.setLanguage('en');
        }
    })()
    """)
    time.sleep(0.5)

    edit_modal_check_en = eval_js("""
    (() => {
        const sharedModal = document.getElementById('modal-selfcheck-adjust');
        const card = document.getElementById('selfcheck-adjust-modal-card');
        const titleEl = card ? card.querySelector('.space-y-1 span') : null;
        const nameInp = document.getElementById('adjust-tracker-name-input');
        const saveBtn = document.getElementById('adjust-save-submit-btn');

        return {
            sharedModalVisible: sharedModal ? !sharedModal.classList.contains('hidden') : false,
            titleText: titleEl ? titleEl.textContent.trim() : null,
            prefilledName: nameInp ? nameInp.value : null,
            saveBtnText: saveBtn ? saveBtn.textContent.trim() : null
        };
    })()
    """)
    print("Edit Modal in EN Check:", json.dumps(edit_modal_check_en, indent=2, ensure_ascii=False))
    take_screenshot("unified_edit_modal_step1_en.png")

    assert edit_modal_check_en.get("sharedModalVisible") is True, "Modal must remain open after switching to EN"
    assert edit_modal_check_en.get("titleText") == "Edit Tracking Item", f"Title should be 'Edit Tracking Item', got: {edit_modal_check_en.get('titleText')}"
    assert edit_modal_check_en.get("saveBtnText") == "Save changes", f"Save button should be 'Save changes', got: {edit_modal_check_en.get('saveBtnText')}"
    assert edit_modal_check_en.get("prefilledName") == "Tension", "Tracker name must be preserved"
    print("✓ TEST 2 PASSED: Edit mode translated to 'Edit Tracking Item' and 'Save changes' live!")

    # Switch back to Vietnamese
    eval_js("""
    (() => {
        if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
            window.TempoI18n.setLanguage('vi');
        }
    })()
    """)
    time.sleep(0.3)

    # 3. Edit fields and Save
    print("\n--- TEST 3: Modify fields and save updated tracker ---")
    eval_js("""
    (() => {
        const nameInp = document.getElementById('adjust-tracker-name-input');
        if (nameInp) {
            nameInp.value = 'Mức độ căng thẳng & lo âu';
            if (window.TempoSelfCheckWorkspace.setDraftTrackerName) {
                window.TempoSelfCheckWorkspace.setDraftTrackerName(nameInp.value);
            }
        }
        // Change method to Scale
        if (window.TempoSelfCheckWorkspace.setAdjustMethod) {
            window.TempoSelfCheckWorkspace.setAdjustMethod('scale');
        }
        const thresh = document.getElementById('adjust-alert-threshold');
        if (thresh) thresh.value = '4';
        const days = document.getElementById('adjust-alert-days');
        if (days) days.value = '5';
        if (window.TempoSelfCheckWorkspace.readCurrentDraftInputs) {
            window.TempoSelfCheckWorkspace.readCurrentDraftInputs();
        }
    })()
    """)
    time.sleep(0.5)

    # Click Save changes
    eval_js("""
    (() => {
        const saveBtn = document.getElementById('adjust-save-submit-btn');
        if (saveBtn) saveBtn.click();
    })()
    """)
    time.sleep(1.0)

    post_edit_check = eval_js("""
    (() => {
        const sharedModal = document.getElementById('modal-selfcheck-adjust');
        const activeTrackers = window.TempoRecoverySelfCheck ? window.TempoRecoverySelfCheck.getActiveTrackers() : [];
        const originalTracker = activeTrackers.find(t => t.id === window.__test_t1_id);
        const listEl = document.querySelector('[data-tempo-section="adjust-items-list"]') || document.getElementById('recovery-setup-stage-container');
        const listText = listEl ? listEl.textContent : '';

        return {
            modalClosed: sharedModal ? sharedModal.classList.contains('hidden') : true,
            totalActiveCount: activeTrackers.length,
            originalIdPreserved: !!originalTracker,
            updatedName: originalTracker ? originalTracker.name : null,
            updatedMethod: originalTracker ? originalTracker.check_method : null,
            hasNewNameInList: listText.includes('Mức độ căng thẳng & lo âu')
        };
    })()
    """)
    print("Post Edit Check:", json.dumps(post_edit_check, indent=2, ensure_ascii=False))
    take_screenshot("adjustment_list_after_unified_edit.png")

    assert post_edit_check.get("modalClosed") is True, "Modal must close on save"
    assert post_edit_check.get("totalActiveCount") == 2, f"Total tracker count must remain 2 (no duplicates!), got: {post_edit_check.get('totalActiveCount')}"
    assert post_edit_check.get("originalIdPreserved") is True, "Original ID 'tr_tension_unique_123' must be preserved"
    assert post_edit_check.get("updatedName") == "Mức độ căng thẳng & lo âu", f"Name should be updated, got: {post_edit_check.get('updatedName')}"
    assert post_edit_check.get("updatedMethod") == "scale", f"Method should be updated to scale, got: {post_edit_check.get('updatedMethod')}"
    assert post_edit_check.get("hasNewNameInList") is True, "Step 1 adjustment list must show updated tracker name immediately"
    print("✓ TEST 3 PASSED: Tracker updated in place, ID preserved, no duplicates, list updated immediately!")

    # 4. Verify Create mode still uses the same modal correctly
    print("\n--- TEST 4: Create mode still uses the same modal with 'Mục tracking của bạn' title ---")
    eval_js("""
    (() => {
        if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.openAddTrackerInAdjustment === 'function') {
            window.TempoRecoverySetup.openAddTrackerInAdjustment();
        }
    })()
    """)
    time.sleep(0.5)

    create_modal_check = eval_js("""
    (() => {
        const sharedModal = document.getElementById('modal-selfcheck-adjust');
        const card = document.getElementById('selfcheck-adjust-modal-card');
        const titleEl = card ? card.querySelector('.space-y-1 span') : null;
        const nameInp = document.getElementById('adjust-tracker-name-input');
        const saveBtn = document.getElementById('adjust-save-submit-btn');

        return {
            sharedModalVisible: sharedModal ? !sharedModal.classList.contains('hidden') : false,
            titleText: titleEl ? titleEl.textContent.trim() : null,
            nameValue: nameInp ? nameInp.value : null,
            placeholder: nameInp ? nameInp.placeholder : null,
            saveBtnText: saveBtn ? saveBtn.textContent.trim() : null
        };
    })()
    """)
    print("Create Mode Modal Check:", json.dumps(create_modal_check, indent=2, ensure_ascii=False))

    assert create_modal_check.get("sharedModalVisible") is True, "Shared modal must open for create mode"
    assert create_modal_check.get("titleText") == "Mục tracking của bạn", f"In Create mode, title must be 'Mục tracking của bạn', got: {create_modal_check.get('titleText')}"
    assert create_modal_check.get("nameValue") == "", "Create mode should start with empty name"
    assert create_modal_check.get("saveBtnText") == "Thêm tracking", f"Save button must be 'Thêm tracking', got: {create_modal_check.get('saveBtnText')}"

    # Close modal
    eval_js("""
    (() => {
        if (window.TempoSelfCheckWorkspace.closeAdjustModal) {
            window.TempoSelfCheckWorkspace.closeAdjustModal();
        }
    })()
    """)
    print("✓ TEST 4 PASSED: Create mode opens with empty fields and 'Mục tracking của bạn' title!")

    print("\n=======================================================")
    print("ALL 4 VERIFICATION SUITES PASSED WITH 100% SUCCESS!")
    print("=======================================================")

finally:
    try:
        ws.close()
    except Exception:
        pass
    try:
        proc.terminate()
    except Exception:
        pass
