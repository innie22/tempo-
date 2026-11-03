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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_step3_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9612

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
        print("JS Exception:", res["exceptionDetails"])
    return res.get("result", {}).get("value")

def capture_screenshot(filename):
    res = send_cmd("Page.captureScreenshot", {"format": "png"})
    data = res.get("data", "")
    filepath = os.path.join(artifact_dir, filename)
    with open(filepath, "wb") as f:
        f.write(base64.b64decode(data))
    print(f"  [Screenshot] Saved: {filepath}")
    return filepath

# Wait for page scripts
print("Waiting for page scripts...")
for _ in range(20):
    ready = eval_js("document.readyState === 'complete' && !!window.TempoRecoverySetup && !!window.TempoRecoverySelfCheck")
    if ready:
        break
    time.sleep(0.5)

print("\n=== STARTING VERIFICATION: STEP 3 LOCALIZATION & RECOVERY NOTICE ===\n")

# TEST 1: Open Step 3 in Vietnamese with 3 active trackers and 0 reflection items
print("--- TEST 1: Step 3 Final Confirmation in Vietnamese ---")
eval_js("""
    localStorage.setItem('tempo_language', 'vi');
    if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
        window.TempoI18n.setLanguage('vi');
    }
    localStorage.setItem('tempo_selfcheck_trackers_local_user', JSON.stringify([]));
    localStorage.setItem('tempo_selfcheck_active_setup_local_user', JSON.stringify({ tracker_ids: [] }));
    const t1 = window.TempoRecoverySelfCheck.createTracker({
        name: 'Mức độ căng thẳng',
        category: 'stress_sign',
        check_method: 'percentage'
    });
    const t2 = window.TempoRecoverySelfCheck.createTracker({
        name: 'Thời gian đi bộ thư giãn',
        category: 'supportive',
        check_method: 'quantity',
        quantity_unit: 'phút'
    });

    window.TempoRecoverySetup.open();
    window.TempoRecoverySetup.startAdjustmentFlow();

    // Add a 3rd tracker as a new tracker in adjustment draft
    window.TempoRecoverySetup.getAdjustmentDraft().newTrackers = [{
        name: 'Uống đủ nước',
        check_method: 'options',
        options: ['Tốt', 'Chưa tốt'],
        category: 'supportive'
    }];
    // Set 0 note items
    window.TempoRecoverySetup.getAdjustmentDraft().noteItems = [];

    // Navigate to step 3
    window.TempoRecoverySetup.goToStage('adjust_review');
""")
time.sleep(0.8)

test1_info = eval_js("""
    (() => {
        const modal = document.getElementById('modal-recovery-setup');
        if (!modal || modal.classList.contains('hidden')) return { modalVisible: false };
        const container = document.querySelector('[data-tempo-ui="adjust-review-confirm"]');
        if (!container) return { containerFound: false };

        const fullText = container.innerText;
        const badges = Array.from(container.querySelectorAll('span')).map(s => s.innerText.trim());
        const backBtn = container.querySelector('button[onclick*="adjust_trackers"]');
        const confirmBtn = container.querySelector('button[onclick*="executeAdjustSetupConfirm"]');

        return {
            modalVisible: true,
            hasStepBadge: fullText.includes('BƯỚC 3/3 · XÁC NHẬN CUỐI CÙNG'),
            hasTagLabel: fullText.includes('Xem lại & xác nhận'),
            hasTitle: fullText.includes('Xem lại các thay đổi thiết lập'),
            hasDesc: fullText.includes('Vui lòng kiểm tra và xác nhận các thay đổi. Thiết lập chỉ được lưu sau khi bạn xác nhận.'),
            hasActiveHeader: fullText.includes('CÁC MỤC TRACKING ĐANG HOẠT ĐỘNG (3)'),
            hasActiveBadge: badges.some(b => b === 'Đang tracking'),
            hasNoticeHeader: fullText.includes('LỜI NHẮN PHỤC HỒI'),
            hasNoticeZeroText: fullText.includes('Chưa có nội dung chia sẻ cá nhân nào được lưu.'),
            backBtnText: backBtn ? backBtn.innerText.trim() : null,
            confirmBtnText: confirmBtn ? confirmBtn.innerText.trim() : null
        };
    })()
""")

print("Test 1 Result:", json.dumps(test1_info, indent=2, ensure_ascii=False))
capture_screenshot("recovery_setup_step3_vi.png")

assert test1_info.get("modalVisible") is True, "Modal should be visible"
assert test1_info.get("hasStepBadge") is True, "Step badge should be 'BƯỚC 3/3 · XÁC NHẬN CUỐI CÙNG'"
assert test1_info.get("hasTagLabel") is True, "Tag label should be 'Xem lại & xác nhận'"
assert test1_info.get("hasTitle") is True, "Title should be 'Xem lại các thay đổi thiết lập'"
assert test1_info.get("hasDesc") is True, "Description should match table"
assert test1_info.get("hasActiveHeader") is True, "Header should be 'CÁC MỤC TRACKING ĐANG HOẠT ĐỘNG (3)'"
assert test1_info.get("hasActiveBadge") is True, "Badge should be 'Đang tracking'"
assert test1_info.get("hasNoticeHeader") is True, "Notice header should be 'LỜI NHẮN PHỤC HỒI'"
assert test1_info.get("hasNoticeZeroText") is True, "Zero items text should be 'Chưa có nội dung chia sẻ cá nhân nào được lưu.'"
assert "Quay lại chỉnh sửa" in test1_info.get("backBtnText", ""), "Back button should contain 'Quay lại chỉnh sửa'"
assert "Xác nhận & lưu thiết lập ✓" in test1_info.get("confirmBtnText", ""), "Confirm button should be 'Xác nhận & lưu thiết lập ✓'"
print("✓ TEST 1 PASSED: Step 3 matches all Vietnamese translation mappings exactly!\n")


# TEST 2: Step 3 in English
print("--- TEST 2: Step 3 Final Confirmation in English ---")
eval_js("""
    window.TempoI18n.setLanguage('en');
    window.TempoRecoverySetup.goToStage('adjust_review');
""")
time.sleep(0.6)

test2_info = eval_js("""
    (() => {
        const container = document.querySelector('[data-tempo-ui="adjust-review-confirm"]');
        if (!container) return { containerFound: false };
        const fullText = container.innerText;
        const badges = Array.from(container.querySelectorAll('span')).map(s => s.innerText.trim());
        const backBtn = container.querySelector('button[onclick*="adjust_trackers"]');
        const confirmBtn = container.querySelector('button[onclick*="executeAdjustSetupConfirm"]');

        return {
            hasStepBadge: fullText.includes('STEP 3 OF 3 · FINAL CONFIRMATION'),
            hasTagLabel: fullText.includes('Review & Confirm'),
            hasTitle: fullText.includes('Review proposed setup changes'),
            hasDesc: fullText.includes('Please confirm your updates. Changes will be saved only after explicit confirmation.'),
            hasActiveHeader: fullText.includes('ACTIVE TRACKING ITEMS (3)'),
            hasActiveBadge: badges.some(b => b === 'Active'),
            hasNoticeHeader: fullText.includes('RECOVERY NOTICE'),
            hasNoticeZeroText: fullText.includes('0 personal reflection items saved.'),
            backBtnText: backBtn ? backBtn.innerText.trim() : null,
            confirmBtnText: confirmBtn ? confirmBtn.innerText.trim() : null
        };
    })()
""")

print("Test 2 Result:", json.dumps(test2_info, indent=2, ensure_ascii=False))
capture_screenshot("recovery_setup_step3_en.png")

assert test2_info.get("hasStepBadge") is True, "English step badge"
assert test2_info.get("hasTagLabel") is True, "English tag label"
assert test2_info.get("hasTitle") is True, "English title"
assert test2_info.get("hasDesc") is True, "English description"
assert test2_info.get("hasActiveHeader") is True, "English active items header"
assert test2_info.get("hasActiveBadge") is True, "English active badge"
assert test2_info.get("hasNoticeHeader") is True, "English notice header 'RECOVERY NOTICE'"
assert test2_info.get("hasNoticeZeroText") is True, "English zero text '0 personal reflection items saved.'"
assert "Back to Edit" in test2_info.get("backBtnText", ""), "Back button in English"
assert "Confirm & Save Setup ✓" in test2_info.get("confirmBtnText", ""), "Confirm button in English"
print("✓ TEST 2 PASSED: English labels render accurately with 'RECOVERY NOTICE'!\n")


# TEST 3: Terminology Verification Across Rmode Setup Flow
print("--- TEST 3: Terminology Verification across Steps 1, 2, and 3 ---")
test3_info = eval_js("""
    (() => {
        window.TempoI18n.setLanguage('en');
        window.TempoRecoverySetup.goToStage('adjust_trackers');
        const step1Btn = document.querySelector('button[onclick*="adjust_note"]')?.innerText.trim();

        window.TempoRecoverySetup.goToStage('adjust_note');
        const step2Badge = document.querySelector('[data-tempo-ui="adjust-recovery-note"]')?.innerText;

        window.TempoRecoverySetup.goToStage('adjust_review');
        const step3Text = document.querySelector('[data-tempo-ui="adjust-review-confirm"]')?.innerText;

        const hasOldNoteInStep1 = (step1Btn || '').includes('Recovery Note');
        const hasNewNoticeInStep1 = (step1Btn || '').includes('Recovery Notice');

        const hasOldNoteInStep2 = (step2Badge || '').includes('RECOVERY NOTE');
        const hasNewNoticeInStep2 = (step2Badge || '').includes('RECOVERY NOTICE');

        const hasOldNoteInStep3 = (step3Text || '').includes('RECOVERY NOTE');
        const hasNewNoticeInStep3 = (step3Text || '').includes('RECOVERY NOTICE');

        return {
            step1Btn,
            hasOldNoteInStep1,
            hasNewNoticeInStep1,
            hasOldNoteInStep2,
            hasNewNoticeInStep2,
            hasOldNoteInStep3,
            hasNewNoticeInStep3
        };
    })()
""")

print("Test 3 Result:", json.dumps(test3_info, indent=2, ensure_ascii=False))

assert test3_info.get("hasNewNoticeInStep1") is True, "Step 1 button uses 'Recovery Notice'"
assert test3_info.get("hasOldNoteInStep1") is False, "Step 1 does not use old 'Recovery Note'"
assert test3_info.get("hasNewNoticeInStep2") is True, "Step 2 uses 'RECOVERY NOTICE'"
assert test3_info.get("hasOldNoteInStep2") is False, "Step 2 does not use old 'RECOVERY NOTE'"
assert test3_info.get("hasNewNoticeInStep3") is True, "Step 3 uses 'RECOVERY NOTICE'"
assert test3_info.get("hasOldNoteInStep3") is False, "Step 3 does not use old 'RECOVERY NOTE'"
print("✓ TEST 3 PASSED: Standardized 'Recovery Notice' across entire setup flow!\n")


# TEST 4: Non-zero Reflection Items Test
print("--- TEST 4: Non-zero personal reflection items ---")
eval_js("""
    window.TempoI18n.setLanguage('vi');
    window.TempoRecoverySetup.getAdjustmentDraft().noteItems = [
        { type: 'warning_sign', text: 'Thở dốc khi căng thẳng' },
        { type: 'helper', text: 'Uống nước ấm' }
    ];
    window.TempoRecoverySetup.goToStage('adjust_review');
""")
time.sleep(0.5)

test4_vi = eval_js("""
    (() => {
        const text = document.querySelector('[data-tempo-ui="adjust-review-confirm"]')?.innerText || '';
        return {
            hasTwoItemsVi: text.includes('2 nội dung chia sẻ cá nhân đã lưu.')
        };
    })()
""")
print("Test 4 Result (VI):", test4_vi)
capture_screenshot("recovery_setup_step3_items_vi.png")
assert test4_vi.get("hasTwoItemsVi") is True, "Vietnamese non-zero count should match format"

eval_js("""
    window.TempoI18n.setLanguage('en');
    window.TempoRecoverySetup.goToStage('adjust_review');
""")
time.sleep(0.5)
test4_en = eval_js("""
    (() => {
        const text = document.querySelector('[data-tempo-ui="adjust-review-confirm"]')?.innerText || '';
        return {
            hasTwoItemsEn: text.includes('2 personal reflection items saved.')
        };
    })()
""")
print("Test 4 Result (EN):", test4_en)
assert test4_en.get("hasTwoItemsEn") is True, "English non-zero count should match format"
print("✓ TEST 4 PASSED: Dynamic item counts format properly in both languages!\n")


# TEST 5: Confirm & Save Setup Interaction
print("--- TEST 5: Confirm and Save Setup ---")
eval_js("""
    window.TempoRecoverySetup.goToStage('adjust_review');
    const confirmBtn = document.querySelector('button[onclick*="executeAdjustSetupConfirm"]');
    confirmBtn.click();
""")
time.sleep(0.8)

test5_info = eval_js("""
    (() => {
        const modal = document.getElementById('modal-recovery-setup');
        const isHidden = !modal || modal.classList.contains('hidden');
        const activeTrackers = window.TempoRecoverySelfCheck.getActiveTrackers();
        const noteItems = window.TempoRecoveryNote.getItems();

        return {
            modalClosed: isHidden,
            activeTrackersCount: activeTrackers.length,
            noteItemsCount: noteItems.length
        };
    })()
""")

print("Test 5 Result:", json.dumps(test5_info, indent=2, ensure_ascii=False))
assert test5_info.get("modalClosed") is True, "Modal should close on confirm"
assert test5_info.get("activeTrackersCount") >= 2, "Active trackers preserved/saved"
assert test5_info.get("noteItemsCount") == 2, "Reflection note items saved"
print("✓ TEST 5 PASSED: Confirm and save executes cleanly with complete data integrity!\n")

# Cleanup browser
try:
    ws.close()
    proc.terminate()
    proc.wait(timeout=3)
except Exception:
    pass

print("=======================================================")
print("ALL 5 VERIFICATION SUITES PASSED WITH 100% SUCCESS!")
print("=======================================================")
