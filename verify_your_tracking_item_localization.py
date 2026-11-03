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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_modal_i18n_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9603

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

    print("\n=== STARTING VERIFICATION: YOUR TRACKING ITEM MODAL LOCALIZATION ===")

    # Initialize environment in Vietnamese
    eval_js("""
    (() => {
        localStorage.setItem('tempo_language', 'vi');
        if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
            window.TempoI18n.setLanguage('vi');
        }
        localStorage.setItem('tempo_active_context', 'rmode');
        localStorage.setItem('tempo_user_id', 'test_modal_i18n_user');

        const state = {
            version: 1,
            phase: 'established',
            activePlan: { title: 'Standard Recovery' },
            onboardingCompleted: true,
            needsReview: false
        };
        localStorage.setItem('tempo_recovery_state', JSON.stringify(state));

        // Setup mock trackers
        const trackers = [
            {
                id: 'tr_tension',
                name: 'Tension',
                category: 'stress_sign',
                type_id: 'stress_sign',
                type_label: 'Dấu hiệu căng thẳng',
                type_color: '#C34D2E',
                check_method: 'percentage',
                is_active: true,
                archived: false,
                alert_enabled: true,
                alert_config: { operator: 'more_than', threshold: 60, days: 4 }
            },
            {
                id: 'tr_walk',
                name: 'Đi bộ',
                category: 'supportive',
                type_id: 'supportive',
                type_label: 'Yếu tố hỗ trợ',
                type_color: '#859B8B',
                check_method: 'quantity',
                quantity_unit: 'phút',
                is_active: true,
                archived: false,
                alert_enabled: true,
                alert_config: { operator: 'more_than', threshold: 30, days: 3 }
            }
        ];
        localStorage.setItem('tempo_recovery_trackers_v2_test_modal_i18n_user', JSON.stringify(trackers));
        localStorage.setItem('tempo_recovery_trackers_v2_guest', JSON.stringify(trackers));

        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.reloadTrackersFromStorage === 'function') {
            window.TempoRecoverySelfCheck.reloadTrackersFromStorage();
        }
    })()
    """)
    time.sleep(0.5)

    # TEST 1: Open Step 1 and Click "+ Thêm mục tracking mới"
    print("\n--- TEST 1: Open modal in Vietnamese and check initial text ---")
    eval_js("""
    (() => {
        if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.startAdjustmentFlow === 'function') {
            window.TempoRecoverySetup.startAdjustmentFlow();
        }
    })()
    """)
    time.sleep(0.5)

    # Click "+ Thêm mục tracking mới"
    eval_js("""
    (() => {
        if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.openAddTrackerInAdjustment === 'function') {
            window.TempoRecoverySetup.openAddTrackerInAdjustment();
        } else if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.openAddTracking === 'function') {
            window.TempoSelfCheckWorkspace.openAddTracking();
        }
    })()
    """)
    time.sleep(0.5)

    vi_check = eval_js("""
    (() => {
        const modal = document.getElementById('modal-selfcheck-adjust');
        if (!modal || modal.classList.contains('hidden')) return { error: 'Modal not visible' };

        const card = document.getElementById('selfcheck-adjust-modal-card');
        const titleEl = card ? card.querySelector('.space-y-1 span') : null;
        const nameInp = document.getElementById('adjust-tracker-name-input');
        const alertTypeSel = document.getElementById('adjust-alert-type');
        const alertOpSel = document.getElementById('adjust-alert-operator');
        const saveBtn = document.getElementById('adjust-save-submit-btn');

        // Extract text
        const text = card.textContent;
        const html = card.innerHTML;

        return {
            modalVisible: !modal.classList.contains('hidden'),
            title: titleEl ? titleEl.textContent.trim() : null,
            placeholder: nameInp ? nameInp.placeholder : null,
            hasLoai: text.includes('Loại:'),
            hasDauHieuCangThang: text.includes('Dấu hiệu căng thẳng'),
            hasYeuToHoTro: text.includes('Yếu tố hỗ trợ'),
            hasTaoLoaiMoi: text.includes('Tạo loại mới'),
            hasHinhThucTracking: text.includes('Hình thức tracking:'),
            hasLuaChon: text.includes('Lựa chọn'),
            hasThangDo: text.includes('Thang đo'),
            hasSoLuong: text.includes('Số lượng'),
            hasCoCheCanhBao: text.includes('Cơ chế cảnh báo'),
            hasBat: text.includes('Bật'),
            hasTat: text.includes('Tắt'),
            hasNoticeMe: text.includes('Cảnh báo khi kết quả tracking của tôi'),
            hasLoaiCanhBao: text.includes('Loại cảnh báo:'),
            hasLonHon: alertOpSel ? alertOpSel.textContent.includes('Lớn hơn') : false,
            hasPhanTramTrong: text.includes('% trong'),
            hasNgayLienTiep: text.includes('ngày liên tiếp'),
            hasHuy: text.includes('Hủy'),
            saveBtnText: saveBtn ? saveBtn.textContent.trim() : null
        };
    })()
    """)
    print("Vietnamese Modal Inspection:", json.dumps(vi_check, indent=2, ensure_ascii=False))

    take_screenshot("your_tracking_item_modal_vi.png")

    assert vi_check.get("modalVisible") is True, "Modal should be visible"
    assert vi_check.get("title") == "Mục tracking của bạn", f"Title mismatch: {vi_check.get('title')}"
    assert vi_check.get("placeholder") == "Nhập tên mục tracking", f"Placeholder mismatch: {vi_check.get('placeholder')}"
    assert vi_check.get("hasLoai") is True, "Type label should be 'Loại:'"
    assert vi_check.get("hasDauHieuCangThang") is True, "Should have 'Dấu hiệu căng thẳng'"
    assert vi_check.get("hasYeuToHoTro") is True, "Should have 'Yếu tố hỗ trợ'"
    assert vi_check.get("hasTaoLoaiMoi") is True, "Should have 'Tạo loại mới'"
    assert vi_check.get("hasHinhThucTracking") is True, "Method label should be 'Hình thức tracking:'"
    assert vi_check.get("hasLuaChon") is True, "Should have 'Lựa chọn'"
    assert vi_check.get("hasThangDo") is True, "Should have 'Thang đo'"
    assert vi_check.get("hasSoLuong") is True, "Should have 'Số lượng'"
    assert vi_check.get("hasCoCheCanhBao") is True, "Alert label should be 'Cơ chế cảnh báo'"
    assert vi_check.get("hasBat") is True, "Should have 'Bật'"
    assert vi_check.get("hasTat") is True, "Should have 'Tắt'"
    assert vi_check.get("hasNoticeMe") is True, "Should have 'Cảnh báo khi kết quả tracking của tôi'"
    assert vi_check.get("hasLoaiCanhBao") is True, "Should have 'Loại cảnh báo:'"
    assert vi_check.get("hasLonHon") is True, "Should have 'Lớn hơn'"
    assert vi_check.get("hasPhanTramTrong") is True, "Should have '% trong'"
    assert vi_check.get("hasNgayLienTiep") is True, "Should have 'ngày liên tiếp'"
    assert vi_check.get("hasHuy") is True, "Should have 'Hủy'"
    assert vi_check.get("saveBtnText") == "Thêm tracking", f"Save btn should be 'Thêm tracking', got: {vi_check.get('saveBtnText')}"
    print("✓ TEST 1 PASSED: All Vietnamese modal texts match requirement table!")

    # TEST 2: User enters values and changes method to Scale
    print("\n--- TEST 2: User types custom values into modal ---")
    eval_js("""
    (() => {
        const nameInp = document.getElementById('adjust-tracker-name-input');
        if (nameInp) {
            nameInp.value = 'Mức độ tập trung';
            if (window.TempoSelfCheckWorkspace.setDraftTrackerName) {
                window.TempoSelfCheckWorkspace.setDraftTrackerName(nameInp.value);
            }
        }
        // Switch to Scale method
        if (window.TempoSelfCheckWorkspace.setAdjustMethod) {
            window.TempoSelfCheckWorkspace.setAdjustMethod('scale');
        }
        const thresh = document.getElementById('adjust-alert-threshold');
        if (thresh) thresh.value = '4';
        const days = document.getElementById('adjust-alert-days');
        if (days) days.value = '6';
        if (window.TempoSelfCheckWorkspace.readCurrentDraftInputs) {
            window.TempoSelfCheckWorkspace.readCurrentDraftInputs();
        }
    })()
    """)
    time.sleep(0.5)

    scale_check_vi = eval_js("""
    (() => {
        const card = document.getElementById('selfcheck-adjust-modal-card');
        return {
            text: card.textContent,
            hasTrenThangDo: card.textContent.includes('trên thang đo 1-5 trong'),
            hasNgayLienTiep: card.textContent.includes('ngày liên tiếp')
        };
    })()
    """)
    print("Scale method in VI:", scale_check_vi)
    assert scale_check_vi.get("hasTrenThangDo") is True, "Scale inline text should contain 'trên thang đo 1-5 trong'"
    print("✓ TEST 2 PASSED: Scale method text properly formatted in Vietnamese!")

    # TEST 3: Live switch language to English without closing or resetting modal
    print("\n--- TEST 3: Switch language to English live ---")
    eval_js("""
    (() => {
        if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
            window.TempoI18n.setLanguage('en');
        }
    })()
    """)
    time.sleep(0.5)

    en_check = eval_js("""
    (() => {
        const modal = document.getElementById('modal-selfcheck-adjust');
        if (!modal || modal.classList.contains('hidden')) return { error: 'Modal closed after language switch' };

        const card = document.getElementById('selfcheck-adjust-modal-card');
        const titleEl = card ? card.querySelector('.space-y-1 span') : null;
        const nameInp = document.getElementById('adjust-tracker-name-input');
        const thresh = document.getElementById('adjust-alert-threshold');
        const days = document.getElementById('adjust-alert-days');
        const saveBtn = document.getElementById('adjust-save-submit-btn');
        const text = card.textContent;

        return {
            modalVisible: !modal.classList.contains('hidden'),
            nameValue: nameInp ? nameInp.value : null,
            threshValue: thresh ? thresh.value : null,
            daysValue: days ? days.value : null,
            title: titleEl ? titleEl.textContent.trim() : null,
            placeholder: nameInp ? nameInp.placeholder : null,
            hasType: text.includes('Type:'),
            hasSignOfStress: text.includes('Sign of stress'),
            hasSupportive: text.includes('Supportive'),
            hasCreateNewType: text.includes('Create new type'),
            hasTrackingMethod: text.includes('Tracking method:'),
            hasOptions: text.includes('Options'),
            hasScale: text.includes('Scale'),
            hasQuantity: text.includes('Quantity'),
            hasAlertSystem: text.includes('Alert system'),
            hasOn: text.includes('On'),
            hasOff: text.includes('Off'),
            hasNoticeMe: text.includes('Notice me if my checks are'),
            hasAlertType: text.includes('Alert type:'),
            hasOnAScaleOf: text.includes('on a scale of 1-5 for'),
            hasDaysInARow: text.includes('days in a row'),
            hasCancel: text.includes('Cancel'),
            saveBtnText: saveBtn ? saveBtn.textContent.trim() : null
        };
    })()
    """)
    print("English Modal Inspection:", json.dumps(en_check, indent=2, ensure_ascii=False))

    take_screenshot("your_tracking_item_modal_en.png")

    assert en_check.get("modalVisible") is True, "Modal must remain open after language change"
    assert en_check.get("nameValue") == "Mức độ tập trung", f"User-entered tracking name must be preserved: {en_check.get('nameValue')}"
    assert en_check.get("threshValue") == "4", f"Threshold 4 must be preserved: {en_check.get('threshValue')}"
    assert en_check.get("daysValue") == "6", f"Days 6 must be preserved: {en_check.get('daysValue')}"
    assert en_check.get("title") == "Your Tracking Item", f"Title should be 'Your Tracking Item', got: {en_check.get('title')}"
    assert en_check.get("placeholder") == "Enter tracking name", f"Placeholder should be 'Enter tracking name', got: {en_check.get('placeholder')}"
    assert en_check.get("hasType") is True, "Should have 'Type:'"
    assert en_check.get("hasSignOfStress") is True, "Should have 'Sign of stress'"
    assert en_check.get("hasSupportive") is True, "Should have 'Supportive'"
    assert en_check.get("hasCreateNewType") is True, "Should have 'Create new type'"
    assert en_check.get("hasTrackingMethod") is True, "Should have 'Tracking method:'"
    assert en_check.get("hasOptions") is True, "Should have 'Options'"
    assert en_check.get("hasScale") is True, "Should have 'Scale'"
    assert en_check.get("hasQuantity") is True, "Should have 'Quantity'"
    assert en_check.get("hasAlertSystem") is True, "Should have 'Alert system'"
    assert en_check.get("hasOn") is True, "Should have 'On'"
    assert en_check.get("hasOff") is True, "Should have 'Off'"
    assert en_check.get("hasNoticeMe") is True, "Should have 'Notice me if my checks are'"
    assert en_check.get("hasAlertType") is True, "Should have 'Alert type:'"
    assert en_check.get("hasOnAScaleOf") is True, "Should have 'on a scale of 1-5 for'"
    assert en_check.get("hasDaysInARow") is True, "Should have 'days in a row'"
    assert en_check.get("hasCancel") is True, "Should have 'Cancel'"
    assert en_check.get("saveBtnText") == "Add tracking", f"Save button should be 'Add tracking', got: {en_check.get('saveBtnText')}"
    print("✓ TEST 3 PASSED: Modal stayed open, user inputs preserved, translated to English cleanly!")

    # TEST 4: Live switch back to Vietnamese and submit tracker
    print("\n--- TEST 4: Switch back to Vietnamese and submit new tracker ---")
    eval_js("""
    (() => {
        if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
            window.TempoI18n.setLanguage('vi');
        }
    })()
    """)
    time.sleep(0.5)

    post_vi = eval_js("""
    (() => {
        const nameInp = document.getElementById('adjust-tracker-name-input');
        const saveBtn = document.getElementById('adjust-save-submit-btn');
        return {
            name: nameInp ? nameInp.value : null,
            saveBtnText: saveBtn ? saveBtn.textContent.trim() : null
        };
    })()
    """)
    print("Post-switch VI state:", post_vi)
    assert post_vi.get("name") == "Mức độ tập trung", "Name should still be preserved"
    assert post_vi.get("saveBtnText") == "Thêm tracking", "Save btn should be 'Thêm tracking'"

    # Submit tracker
    eval_js("""
    (() => {
        const saveBtn = document.getElementById('adjust-save-submit-btn');
        if (saveBtn) saveBtn.click();
    })()
    """)
    time.sleep(1.0)

    post_save = eval_js("""
    (() => {
        const modal = document.getElementById('modal-selfcheck-adjust');
        const listEl = document.querySelector('[data-tempo-section="adjust-items-list"]') || document.getElementById('recovery-setup-stage-container');
        const listText = listEl ? listEl.textContent : '';
        const activeTrackers = window.TempoRecoverySelfCheck ? window.TempoRecoverySelfCheck.getActiveTrackers() : [];

        return {
            modalClosed: modal ? modal.classList.contains('hidden') : true,
            hasNewTrackerInDOM: listText.includes('Mức độ tập trung'),
            hasNewTrackerInStore: activeTrackers.some(t => t.name === 'Mức độ tập trung')
        };
    })()
    """)
    print("Post Save Check:", post_save)
    take_screenshot("adjustment_list_after_add_vi.png")

    assert post_save.get("modalClosed") is True, "Modal should close on save"
    assert post_save.get("hasNewTrackerInDOM") is True, "New tracker should show in adjustment list"
    assert post_save.get("hasNewTrackerInStore") is True, "New tracker should be saved in active trackers store"
    print("✓ TEST 4 PASSED: Tracker saved successfully from Vietnamese modal!")

    # TEST 5: Edit mode ('draft.mode === edit')
    print("\n--- TEST 5: Open existing tracker in Edit mode and verify translations ---")
    eval_js("""
    (() => {
        const active = window.TempoRecoverySelfCheck.getActiveTrackers();
        if (active.length > 0) {
            window.TempoSelfCheckWorkspace.openAdjustTracker(active[0].id);
        }
    })()
    """)
    time.sleep(0.5)

    edit_vi = eval_js("""
    (() => {
        const modal = document.getElementById('modal-selfcheck-adjust');
        const saveBtn = document.getElementById('adjust-save-submit-btn');
        return {
            modalVisible: !modal.classList.contains('hidden'),
            saveBtnText: saveBtn ? saveBtn.textContent.trim() : null
        };
    })()
    """)
    print("Edit mode in VI:", edit_vi)
    take_screenshot("your_tracking_item_modal_edit_vi.png")

    assert edit_vi.get("modalVisible") is True, "Modal should open in edit mode"
    assert edit_vi.get("saveBtnText") == "Lưu thay đổi", f"In edit mode, button should be 'Lưu thay đổi', got: {edit_vi.get('saveBtnText')}"

    # Live switch to English in edit mode
    eval_js("""
    (() => {
        if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
            window.TempoI18n.setLanguage('en');
        }
    })()
    """)
    time.sleep(0.5)

    edit_en = eval_js("""
    (() => {
        const saveBtn = document.getElementById('adjust-save-submit-btn');
        return {
            saveBtnText: saveBtn ? saveBtn.textContent.trim() : null
        };
    })()
    """)
    print("Edit mode in EN:", edit_en)
    assert edit_en.get("saveBtnText") == "Save changes", f"In edit mode EN, button should be 'Save changes', got: {edit_en.get('saveBtnText')}"

    # Close modal
    eval_js("""
    (() => {
        if (window.TempoSelfCheckWorkspace.closeAdjustModal) {
            window.TempoSelfCheckWorkspace.closeAdjustModal();
        }
    })()
    """)

    print("✓ TEST 5 PASSED: Edit mode button shows 'Lưu thay đổi' in VI and 'Save changes' in EN!")

    print("\n=======================================================")
    print("ALL 5 VERIFICATION SUITES PASSED WITH 100% SUCCESS!")
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
