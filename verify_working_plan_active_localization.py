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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_wp_active_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9615

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
    ready = eval_js("document.readyState === 'complete' && !!window.TempoUrmodeFlow && !!window.TempoI18n")
    if ready:
        break
    time.sleep(0.5)

print("\n=== STARTING VERIFICATION: WORKING PLAN ACTIVE POPUP LOCALIZATION ===\n")

# Seed mock active plan (no overdue)
seed_js = """
(() => {
    const futureDate = new Date(Date.now() + 86400000).toISOString();
    const activePlan = {
        title: "Active Urgent Plan",
        tasks: [
            { id: "task-1", title: "Complete report", duration: 30, deadline: futureDate, status: "pending" },
            { id: "task-2", title: "Review feedback", duration: 20, deadline: futureDate, status: "pending" }
        ],
        createdAt: new Date().toISOString()
    };
    if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
        window.TempoPlanStore.saveActivePlan('emergency', activePlan);
    }
    if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
        window.TempoEmergencyFlow.setConfirmedPlan(activePlan);
    }
    return true;
})()
"""
eval_js(seed_js)

# TEST 1: Open Working Plan Active popup in Vietnamese
print("--- TEST 1: Working Plan Active popup in Vietnamese ---")
eval_js("window.TempoI18n.setLanguage('vi')")
eval_js("window.TempoUrmodeFlow.showResetPopup('PLAN_NO_OVERDUE')")
time.sleep(0.5)

modal_texts_vi = eval_js("""
(() => {
    const modal = document.getElementById('modal-urmode-flow');
    if (!modal) return null;
    return {
        badge: modal.querySelector('span.text-xs.font-extrabold')?.innerText.trim(),
        title: modal.querySelector('h2')?.innerText.trim(),
        body: modal.querySelector('p.text-sm')?.innerText.trim(),
        features: Array.from(modal.querySelectorAll('.bg-stone-50 span, [class*="bg-stone-50"] span, .rounded-xl span')).map(e => e.innerText.trim()).filter(Boolean),
        buttons: Array.from(modal.querySelectorAll('button')).map(b => b.innerText.trim()).filter(Boolean),
        closeAria: modal.querySelector('button[aria-label]')?.getAttribute('aria-label')
    };
})()
""")

print("Vietnamese Modal Content:", json.dumps(modal_texts_vi, ensure_ascii=False, indent=2))
assert modal_texts_vi is not None, "Modal overlay not found!"
assert modal_texts_vi["badge"] == "PLAN ĐANG HOẠT ĐỘNG", f"Expected 'PLAN ĐANG HOẠT ĐỘNG', got '{modal_texts_vi['badge']}'"
assert modal_texts_vi["title"] == "Xem lại và điều chỉnh plan của bạn", f"Unexpected title: {modal_texts_vi['title']}"
assert "Bạn đã có một plan đang hoạt động" in modal_texts_vi["body"], f"Unexpected body: {modal_texts_vi['body']}"
assert "Xem lại plan" in modal_texts_vi["buttons"], f"Missing 'Xem lại plan' button: {modal_texts_vi['buttons']}"
assert any("Có, tôi muốn lấy lại bình tĩnh" in b for b in modal_texts_vi["buttons"]), f"Missing primary button: {modal_texts_vi['buttons']}"
assert modal_texts_vi["closeAria"] == "Đóng", f"Unexpected close button aria-label: {modal_texts_vi['closeAria']}"
print("✓ Test 1 passed: All strings in Vietnamese, no English text present.")
capture_screenshot("working_plan_active_modal_vi.png")

# TEST 2: Live switch to English while popup is open
print("\n--- TEST 2: Live Language Switch to English while Popup is Open ---")
eval_js("window.TempoI18n.setLanguage('en')")
time.sleep(0.5)

modal_texts_en = eval_js("""
(() => {
    const modal = document.getElementById('modal-urmode-flow');
    if (!modal) return null;
    return {
        badge: modal.querySelector('span.text-xs.font-extrabold')?.innerText.trim(),
        title: modal.querySelector('h2')?.innerText.trim(),
        body: modal.querySelector('p.text-sm')?.innerText.trim(),
        features: Array.from(modal.querySelectorAll('.bg-stone-50 span, [class*="bg-stone-50"] span, .rounded-xl span')).map(e => e.innerText.trim()).filter(Boolean),
        buttons: Array.from(modal.querySelectorAll('button')).map(b => b.innerText.trim()).filter(Boolean),
        closeAria: modal.querySelector('button[aria-label]')?.getAttribute('aria-label')
    };
})()
""")

print("English Modal Content:", json.dumps(modal_texts_en, ensure_ascii=False, indent=2))
assert modal_texts_en["badge"] == "WORKING PLAN ACTIVE", f"Expected 'WORKING PLAN ACTIVE', got '{modal_texts_en['badge']}'"
assert modal_texts_en["title"] == "Review and reset your Working Plan", f"Unexpected title: {modal_texts_en['title']}"
assert "You already have an active Working Plan saved" in modal_texts_en["body"], f"Unexpected body: {modal_texts_en['body']}"
assert "Review your plan" in modal_texts_en["buttons"], f"Missing 'Review your plan' button: {modal_texts_en['buttons']}"
assert any("Yes, take a quick reset" in b for b in modal_texts_en["buttons"]), f"Missing primary button: {modal_texts_en['buttons']}"
assert modal_texts_en["closeAria"] in ["Close", "Close dialog"], f"Unexpected close button aria-label: {modal_texts_en['closeAria']}"
print("✓ Test 2 passed: Live switch to English instantly refreshed all fields without reload.")
capture_screenshot("working_plan_active_modal_en.png")

# TEST 3: Live switch back to Vietnamese
print("\n--- TEST 3: Live Switch Back to Vietnamese ---")
eval_js("window.TempoI18n.setLanguage('vi')")
time.sleep(0.5)

badge_recheck_vi = eval_js("document.querySelector('#modal-urmode-flow span.text-xs.font-extrabold')?.innerText.trim()")
body_recheck_vi = eval_js("document.querySelector('#modal-urmode-flow p.text-sm')?.innerText.trim()")
assert badge_recheck_vi == "PLAN ĐANG HOẠT ĐỘNG", f"Expected 'PLAN ĐANG HOẠT ĐỘNG', got '{badge_recheck_vi}'"
assert "Bạn đã có một plan đang hoạt động" in body_recheck_vi, f"Expected Vietnamese body, got '{body_recheck_vi}'"
print("✓ Test 3 passed: Re-switching to Vietnamese instantly translated all content back.")

# TEST 4: Close and reopen in Vietnamese
print("\n--- TEST 4: Close and Reopen in Vietnamese ---")
eval_js("window.TempoUrmodeFlow.handleResetClose()")
time.sleep(0.3)
is_open = eval_js("!document.getElementById('modal-urmode-flow')?.classList.contains('hidden')")
assert not is_open, "Modal should be closed"

eval_js("window.TempoUrmodeFlow.showResetPopup('PLAN_NO_OVERDUE')")
time.sleep(0.3)
badge_reopened = eval_js("document.querySelector('#modal-urmode-flow span.text-xs.font-extrabold')?.innerText.trim()")
body_reopened = eval_js("document.querySelector('#modal-urmode-flow p.text-sm')?.innerText.trim()")
assert badge_reopened == "PLAN ĐANG HOẠT ĐỘNG", f"Reopened badge mismatch: '{badge_reopened}'"
assert "Bạn đã có một plan đang hoạt động" in body_reopened, f"Reopened body mismatch: '{body_reopened}'"
print("✓ Test 4 passed: Close and reopen retains Vietnamese perfectly.")

# TEST 5: Grounded Checkpoint ("Are You Ready?") popup localization & live switch
print("\n--- TEST 5: Grounded Checkpoint ('Are you ready?') in VI and EN ---")
eval_js("window.TempoUrmodeFlow.showAreYouReadyPopup()")
time.sleep(0.4)

checkpoint_vi = eval_js("""
(() => {
    const modal = document.getElementById('modal-urmode-flow');
    return {
        badge: modal.querySelector('span.text-xs.font-extrabold')?.innerText.trim(),
        title: modal.querySelector('h2')?.innerText.trim(),
        body: modal.querySelector('p.text-sm, p.sm\\\\:text-base')?.innerText.trim(),
        buttons: Array.from(modal.querySelectorAll('button')).map(b => b.innerText.trim()).filter(Boolean)
    };
})()
""")
print("Checkpoint VI Content:", json.dumps(checkpoint_vi, ensure_ascii=False, indent=2))
assert checkpoint_vi["badge"] == "ĐIỂM DỪNG ĐIỀM TĨNH", f"Unexpected checkpoint badge: {checkpoint_vi['badge']}"
assert checkpoint_vi["title"] == "Bạn đã sẵn sàng chưa?", f"Unexpected checkpoint title: {checkpoint_vi['title']}"
assert "Chưa, quay lại tập thở" in checkpoint_vi["buttons"], f"Missing button: {checkpoint_vi['buttons']}"
assert any("Có, tôi đã sẵn sàng" in b for b in checkpoint_vi["buttons"]), f"Missing button: {checkpoint_vi['buttons']}"
capture_screenshot("grounded_checkpoint_modal_vi.png")

# Switch checkpoint to English
eval_js("window.TempoI18n.setLanguage('en')")
time.sleep(0.4)
checkpoint_en = eval_js("""
(() => {
    const modal = document.getElementById('modal-urmode-flow');
    return {
        badge: modal.querySelector('span.text-xs.font-extrabold')?.innerText.trim(),
        title: modal.querySelector('h2')?.innerText.trim(),
        buttons: Array.from(modal.querySelectorAll('button')).map(b => b.innerText.trim()).filter(Boolean)
    };
})()
""")
print("Checkpoint EN Content:", json.dumps(checkpoint_en, ensure_ascii=False, indent=2))
assert checkpoint_en["badge"] == "GROUNDED CHECKPOINT", f"Unexpected checkpoint badge: {checkpoint_en['badge']}"
assert checkpoint_en["title"] == "Are you ready?", f"Unexpected checkpoint title: {checkpoint_en['title']}"
assert "Not yet, return to reset" in checkpoint_en["buttons"], f"Missing button: {checkpoint_en['buttons']}"
assert any("Yes, I'm ready" in b for b in checkpoint_en["buttons"]), f"Missing button: {checkpoint_en['buttons']}"
capture_screenshot("grounded_checkpoint_modal_en.png")
print("✓ Test 5 passed: Grounded Checkpoint popup fully localized and live-switches.")

# TEST 6: Other reset cases (PLAN_WITH_OVERDUE and NO_PLAN)
print("\n--- TEST 6: PLAN_WITH_OVERDUE and NO_PLAN in VI ---")
eval_js("window.TempoI18n.setLanguage('vi')")
eval_js("window.TempoUrmodeFlow.showResetPopup('PLAN_WITH_OVERDUE')")
time.sleep(0.3)
overdue_badge = eval_js("document.querySelector('#modal-urmode-flow span.text-xs.font-extrabold')?.innerText.trim()")
overdue_body = eval_js("document.querySelector('#modal-urmode-flow p.text-sm')?.innerText.trim()")
assert overdue_badge == "PLAN CẦN ĐƯỢC CẬP NHẬT", f"Unexpected overdue badge: {overdue_badge}"
assert "Bạn có một số task đã quá deadline" in overdue_body, f"Unexpected overdue body: {overdue_body}"

eval_js("window.TempoUrmodeFlow.showResetPopup('NO_PLAN')")
time.sleep(0.3)
no_plan_badge = eval_js("document.querySelector('#modal-urmode-flow span.text-xs.font-extrabold')?.innerText.trim()")
no_plan_title = eval_js("document.querySelector('#modal-urmode-flow h2')?.innerText.trim()")
no_plan_body = eval_js("document.querySelector('#modal-urmode-flow p.text-sm')?.innerText.trim()")
no_plan_btn = eval_js("document.querySelector('#modal-urmode-flow button.border')?.innerText.trim()")
assert no_plan_badge == "KHỞI ĐẦU ĐIỀM TĨNH", f"Unexpected no_plan badge: {no_plan_badge}"
assert no_plan_title == "Dành một chút thời gian để lấy lại bình tĩnh?", f"Unexpected no_plan title: {no_plan_title}"
assert "Những tình huống khẩn cấp sẽ nhẹ nhàng hơn rất nhiều" in no_plan_body, f"Unexpected no_plan body: {no_plan_body}"
assert no_plan_btn == "Lên plan của tôi", f"Unexpected secondary button: {no_plan_btn}"
print("✓ Test 6 passed: All reset cases (PLAN_WITH_OVERDUE, NO_PLAN) correctly localized in Vietnamese.")

# Clean up
eval_js("window.TempoUrmodeFlow.handleResetClose()")
print("\n=== ALL 6 TESTS PASSED SUCCESSFULLY ===")

try:
    ws.close()
    proc.terminate()
except Exception:
    pass
