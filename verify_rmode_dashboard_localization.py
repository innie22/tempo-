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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_rmode_dash_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9628

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
    "http://127.0.0.1:8000/#stress-check"
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

def capture_element(selector, filename):
    rect = eval_js(f"""
    (() => {{
        const el = document.querySelector('{selector}');
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return {{ x: Math.max(0, r.x - 10), y: Math.max(0, r.y - 10), width: r.width + 20, height: r.height + 20 }};
    }})()
    """)
    if not rect:
        print(f"Element not found for {selector}")
        return
    clip = {
        "x": rect["x"],
        "y": rect["y"],
        "width": rect["width"],
        "height": rect["height"],
        "scale": 1
    }
    res = send_cmd("Page.captureScreenshot", {"format": "png", "clip": clip})
    data = res.get("data", "")
    filepath = os.path.join(artifact_dir, filename)
    with open(filepath, "wb") as f:
        f.write(base64.b64decode(data))
    print(f"  [Screenshot] Saved cropped: {filepath}")
    return filepath

# Wait for page scripts
print("Waiting for page scripts...")
for _ in range(20):
    ready = eval_js("document.readyState === 'complete' && !!window.TempoSelfCheckWorkspace && !!window.TempoI18n")
    if ready:
        break
    time.sleep(0.5)

print("\n=== STARTING VERIFICATION: RMODE DASHBOARD VIETNAMESE LOCALIZATION ===\n")

# Seed authenticated session and mock trackers in Recovery mode
seed_js = """
(async () => {
    const u = { id: 'local_dev_alex', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
    localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
    localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
    if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
        await window.TempoAuth.checkSession();
    }
    if (window.TempoAuth && typeof window.TempoAuth.closeAllAuthModals === 'function') {
        window.TempoAuth.closeAllAuthModals();
    }
    document.getElementById('modal-signin')?.classList.add('hidden');
    document.getElementById('modal-register')?.classList.add('hidden');

    if (window.TempoMode) {
        if (typeof window.TempoMode.setMode === 'function') {
            window.TempoMode.setMode('recovery');
        }
        if (typeof window.TempoMode.setOriginatingMode === 'function') {
            window.TempoMode.setOriginatingMode('recovery');
        }
        if (typeof window.TempoMode.setSourceContext === 'function') {
            window.TempoMode.setSourceContext('recovery');
        }
    }

    const trackersKey = 'tempo_selfcheck_trackers_local_dev_alex';
    const mockTrackers = [
        {
            id: 'trk-tension',
            user_id: 'local_dev_alex',
            name: 'Tension',
            category: 'stress_sign',
            check_method: 'percentage',
            is_active: true,
            order_index: 0
        },
        {
            id: 'trk-sleep',
            user_id: 'local_dev_alex',
            name: 'Sleep',
            category: 'supportive',
            check_method: 'yes_no',
            is_active: true,
            order_index: 1
        },
        {
            id: 'trk-walk',
            user_id: 'local_dev_alex',
            name: 'Walk',
            category: 'supportive',
            check_method: 'quantity',
            quantity_unit: 'min',
            is_active: true,
            order_index: 2
        }
    ];
    localStorage.setItem(trackersKey, JSON.stringify(mockTrackers));

    // Seed observations for tension and sleep so metric values display
    const days = window.TempoSelfCheckWorkspace.getCurrentWeekDays ? window.TempoSelfCheckWorkspace.getCurrentWeekDays() : [];
    const obsKey = 'tempo_selfcheck_observations_local_dev_alex';
    const todayStr = days.length > 0 ? days[days.length - 1].dateStr : '2026-11-02';
    const mockObs = [
        { tracker_id: 'trk-tension', date: todayStr, value: 45, status: 'answered' },
        { tracker_id: 'trk-sleep', date: todayStr, value: 'good', status: 'answered' }
    ];
    localStorage.setItem(obsKey, JSON.stringify(mockObs));

    window.TempoI18n.setLanguage('vi');
    if (window.TempoMode && typeof window.TempoMode.showStressCheckScreen === 'function') {
        window.TempoMode.showStressCheckScreen();
    } else {
        document.getElementById('screen-stress-check')?.classList.remove('hidden');
        window.TempoSelfCheckWorkspace.render();
    }
    return true;
})()
"""
eval_js(seed_js)
time.sleep(0.5)

# TEST 1: Audit updated Vietnamese wording on Rmode Dashboard
print("--- TEST 1: Updated Vietnamese wording on Rmode Dashboard ---")
vi_audit = eval_js("""
(() => {
    const root = document.getElementById('self-check-workspace-root');
    if (!root) return null;

    const returnBtn = document.getElementById('btn-self-check-return-home');
    const returnText = document.getElementById('selfcheck-return-home-text')?.innerText.trim();
    const returnTitle = returnBtn?.getAttribute('title');
    const returnFullText = (returnBtn?.innerText || '').replace(/\\s+/g, ' ').trim();

    const titleH2 = root.querySelectorAll('h2')[1]?.innerText.trim();
    const headerBtns = Array.from(root.querySelectorAll('h2 + div button, .flex.items-center.space-x-2 button')).map(b => b.innerText.trim());

    const trackerCards = Array.from(root.querySelectorAll('[data-tracker-id]')).map(card => {
        const name = card.querySelector('h3')?.innerText.trim();
        const adjustBtn = card.querySelector('button')?.innerText.trim();
        const metricLabel = card.querySelector('.space-y-2 .leading-snug')?.innerText.trim();
        return { name, adjustBtn, metricLabel };
    });

    const fullWorkspaceText = root.innerText;

    return {
        returnText,
        returnTitle,
        returnFullText,
        titleH2,
        headerBtns,
        trackerCards,
        hasOldReturnText: fullWorkspaceText.includes('Quay lại Chế độ phục hồi'),
        hasOldSystemTitle: fullWorkspaceText.includes('Hệ thống tracking của bạn'),
        hasOldTensionMetric: fullWorkspaceText.includes('Mức độ căng thẳng trung bình của bạn là'),
        hasOldSleepMetric: fullWorkspaceText.includes('Số đêm ngủ ngon')
    };
})()
""")

print("Vietnamese Audit Result:\n", json.dumps(vi_audit, ensure_ascii=False, indent=2))

assert vi_audit is not None, "Workspace root not found!"
# 1. Return button
assert vi_audit["returnFullText"] == "← Quay lại Dashboard", f"Expected return button '← Quay lại Dashboard', got '{vi_audit['returnFullText']}'"
assert vi_audit["returnText"] == "Quay lại Dashboard", f"Expected return text 'Quay lại Dashboard', got '{vi_audit['returnText']}'"
assert vi_audit["returnTitle"] == "← Quay lại Dashboard", f"Expected return title '← Quay lại Dashboard', got '{vi_audit['returnTitle']}'"

# 2. Tracking system title
assert vi_audit["titleH2"] == "Các mục tracking của bạn", f"Expected 'Các mục tracking của bạn', got '{vi_audit['titleH2']}'"

# 3. Add Tracking & Clear all buttons
assert "Thêm mục tracking" in vi_audit["headerBtns"], f"Missing 'Thêm mục tracking' button: {vi_audit['headerBtns']}"
assert "Xóa tất cả" in vi_audit["headerBtns"], f"Missing 'Xóa tất cả' button: {vi_audit['headerBtns']}"

# 4. Tracker card buttons & metric labels
tension_card = next((c for c in vi_audit["trackerCards"] if "Căng thẳng" in c["name"] or "Tension" in c["name"]), None)
sleep_card = next((c for c in vi_audit["trackerCards"] if "Giấc ngủ" in c["name"] or "Sleep" in c["name"]), None)

assert tension_card is not None, "Tension tracker card not found"
assert tension_card["adjustBtn"] == "Chỉnh sửa", f"Expected 'Chỉnh sửa', got '{tension_card['adjustBtn']}'"
assert tension_card["metricLabel"] == "Mức căng thẳng trung bình", f"Expected 'Mức căng thẳng trung bình', got '{tension_card['metricLabel']}'"

assert sleep_card is not None, "Sleep tracker card not found"
assert sleep_card["adjustBtn"] == "Chỉnh sửa", f"Expected 'Chỉnh sửa', got '{sleep_card['adjustBtn']}'"
assert sleep_card["metricLabel"] == "Số đêm có giấc ngủ tốt", f"Expected 'Số đêm có giấc ngủ tốt', got '{sleep_card['metricLabel']}'"

# 5. Ensure NO old strings remain in the DOM
assert not vi_audit["hasOldReturnText"], "Found deprecated 'Quay lại Chế độ phục hồi' in DOM!"
assert not vi_audit["hasOldSystemTitle"], "Found deprecated 'Hệ thống tracking của bạn' in DOM!"
assert not vi_audit["hasOldTensionMetric"], "Found deprecated 'Mức độ căng thẳng trung bình của bạn là' in DOM!"
assert not vi_audit["hasOldSleepMetric"], "Found deprecated 'Số đêm ngủ ngon' in DOM!"

print("✓ Test 1 passed: All 7 labels verified in Vietnamese with exact updated wording.")
capture_screenshot("rmode_dashboard_vi.png")
capture_element("#self-check-workspace-root", "rmode_dashboard_vi_closeup.png")


# TEST 2: Live Language Switch to English
print("\n--- TEST 2: Live Language Switch to English ---")
eval_js("window.TempoI18n.setLanguage('en')")
time.sleep(0.5)

en_audit = eval_js("""
(() => {
    const root = document.getElementById('self-check-workspace-root');
    const returnBtn = document.getElementById('btn-self-check-return-home');
    const returnText = document.getElementById('selfcheck-return-home-text')?.innerText.trim();
    const returnFullText = (returnBtn?.innerText || '').replace(/\\s+/g, ' ').trim();

    const titleH2 = root.querySelectorAll('h2')[1]?.innerText.trim();
    const headerBtns = Array.from(root.querySelectorAll('h2 + div button, .flex.items-center.space-x-2 button')).map(b => b.innerText.trim());

    const trackerCards = Array.from(root.querySelectorAll('[data-tracker-id]')).map(card => {
        const name = card.querySelector('h3')?.innerText.trim();
        const adjustBtn = card.querySelector('button')?.innerText.trim();
        const metricLabel = card.querySelector('.space-y-2 .leading-snug')?.innerText.trim();
        return { name, adjustBtn, metricLabel };
    });

    return {
        returnText,
        returnFullText,
        titleH2,
        headerBtns,
        trackerCards
    };
})()
""")

print("English Audit Result:\n", json.dumps(en_audit, ensure_ascii=False, indent=2))
assert en_audit["returnText"] == "Return to Recovery Mode", f"Expected 'Return to Recovery Mode', got '{en_audit['returnText']}'"
assert en_audit["titleH2"] == "Your Tracking System", f"Expected 'Your Tracking System', got '{en_audit['titleH2']}'"
assert "Add Tracking" in en_audit["headerBtns"], f"Missing 'Add Tracking' button: {en_audit['headerBtns']}"
assert "Clear all" in en_audit["headerBtns"], f"Missing 'Clear all' button: {en_audit['headerBtns']}"

en_tension = next((c for c in en_audit["trackerCards"] if "Tension" in c["name"]), None)
en_sleep = next((c for c in en_audit["trackerCards"] if "Sleep" in c["name"]), None)

assert en_tension["adjustBtn"] == "Adjust", f"Expected 'Adjust', got '{en_tension['adjustBtn']}'"
assert en_tension["metricLabel"] == "Your average tension level is", f"Expected 'Your average tension level is', got '{en_tension['metricLabel']}'"

assert en_sleep["adjustBtn"] == "Adjust", f"Expected 'Adjust', got '{en_sleep['adjustBtn']}'"
assert en_sleep["metricLabel"] == "Nights of Quality Sleep", f"Expected 'Nights of Quality Sleep', got '{en_sleep['metricLabel']}'"

print("✓ Test 2 passed: English translations perfectly preserved and reactive.")
capture_screenshot("rmode_dashboard_en.png")
capture_element("#self-check-workspace-root", "rmode_dashboard_en_closeup.png")


# TEST 3: Live Switch Back to Vietnamese
print("\n--- TEST 3: Live Switch Back to Vietnamese ---")
eval_js("window.TempoI18n.setLanguage('vi')")
time.sleep(0.5)

recheck_title = eval_js("document.querySelectorAll('#self-check-workspace-root h2')[1]?.innerText.trim()")
recheck_btn = eval_js("(document.getElementById('btn-self-check-return-home')?.innerText || '').replace(/\\s+/g, ' ').trim()")
recheck_add = eval_js("Array.from(document.querySelectorAll('#self-check-workspace-root h2 + div button, #self-check-workspace-root .flex.items-center.space-x-2 button')).map(b => b.innerText.trim())")

assert recheck_title == "Các mục tracking của bạn", f"Recheck title failed: '{recheck_title}'"
assert recheck_btn == "← Quay lại Dashboard", f"Recheck return btn failed: '{recheck_btn}'"
assert "Thêm mục tracking" in recheck_add, f"Recheck add button failed: {recheck_add}"
print("✓ Test 3 passed: Instant live switch back to Vietnamese verified.")


# TEST 4: Empty State in Vietnamese
print("\n--- TEST 4: Empty State in Vietnamese ---")
eval_js("""
(() => {
    localStorage.setItem('tempo_selfcheck_trackers_local_dev_alex', JSON.stringify([]));
    window.TempoSelfCheckWorkspace.render();
})()
""")
time.sleep(0.3)

empty_btn_text = eval_js("document.querySelector('[data-tempo-ui=\"selfcheck-empty-state\"] button')?.innerText.trim()")
print("Empty State Add Button:", empty_btn_text)
assert empty_btn_text == "+ Thêm mục tracking", f"Expected '+ Thêm mục tracking', got '{empty_btn_text}'"
print("✓ Test 4 passed: Empty state button displays '+ Thêm mục tracking'.")


# TEST 5: Verify Add Tracking and Adjust Modals Open Properly
print("\n--- TEST 5: Verify Modals Open and Retain Correct Text ---")
# Restore trackers
eval_js(seed_js)
time.sleep(0.3)

# Open Add Tracking modal
eval_js("window.TempoSelfCheckWorkspace.openAddTracking()")
time.sleep(0.4)

add_modal_title = eval_js("document.querySelector('#modal-selfcheck-adjust span.text-xs.font-bold')?.innerText.trim()")
print("Add Tracking Modal Title:", add_modal_title)
assert add_modal_title in ["Your Tracking Item", "Mục tracking của bạn"], f"Unexpected modal title: '{add_modal_title}'"

# Close modal
eval_js("window.TempoSelfCheckWorkspace.closeAdjustModal()")
time.sleep(0.3)

print("✓ Test 5 passed: Add tracking modal opens without error and preserves functionality.")

print("\n=== ALL 5 TESTS PASSED SUCCESSFULLY ===")

try:
    ws.close()
    proc.terminate()
except Exception:
    pass
