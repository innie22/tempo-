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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_fullcheck_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9636

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

print("\n=== STARTING VERIFICATION: FULL-CHECK CALENDAR MODAL LOCALIZATION ===\n")

# Seed authenticated session and mock trackers
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
        if (typeof window.TempoMode.setMode === 'function') window.TempoMode.setMode('recovery');
        if (typeof window.TempoMode.setOriginatingMode === 'function') window.TempoMode.setOriginatingMode('recovery');
        if (typeof window.TempoMode.setSourceContext === 'function') window.TempoMode.setSourceContext('recovery');
    }

    const trackersKey = 'tempo_selfcheck_trackers_local_dev_alex';
    const mockTrackers = [
        { id: 'trk-tension', user_id: 'local_dev_alex', name: 'Tension', category: 'stress_sign', check_method: 'percentage', is_active: true, order_index: 0 },
        { id: 'trk-sleep', user_id: 'local_dev_alex', name: 'Sleep', category: 'supportive', check_method: 'yes_no', is_active: true, order_index: 1 }
    ];
    localStorage.setItem(trackersKey, JSON.stringify(mockTrackers));

    const obsKey = 'tempo_selfcheck_observations_local_dev_alex';
    const mockObs = [
        { tracker_id: 'trk-tension', date: '2026-11-01', value: 35, status: 'answered' },
        { tracker_id: 'trk-tension', date: '2026-11-02', value: 45, status: 'answered' }
    ];
    localStorage.setItem(obsKey, JSON.stringify(mockObs));

    window.TempoI18n.setLanguage('vi');
    if (window.TempoMode && typeof window.TempoMode.showStressCheckScreen === 'function') {
        window.TempoMode.showStressCheckScreen();
    }
    return true;
})()
"""
eval_js(seed_js)
time.sleep(0.5)

# Open Full-check modal for Tension
eval_js("window.TempoSelfCheckWorkspace.openFullCheckPlaceholder('trk-tension', 2026, 10)")
time.sleep(0.5)

# TEST 1: Audit Vietnamese Full-check Modal
print("--- TEST 1: Full-check Calendar Modal in Vietnamese ---")
vi_audit = eval_js("""
(() => {
    const modal = document.getElementById('modal-selfcheck-fullcheck');
    const card = document.getElementById('selfcheck-fullcheck-modal-card');
    if (!modal || !card) return null;

    const heading = card.querySelector('span.text-xs.font-bold')?.innerText.trim();
    const trackerName = card.querySelector('h2')?.innerText.trim();
    const closeBtnTitle = card.querySelector('button.absolute.top-4.right-4')?.getAttribute('title');

    const weekdays = Array.from(card.querySelectorAll('.grid.grid-cols-7 span.text-xs.font-bold')).map(s => s.innerText.trim());
    const monthSelectOptions = Array.from(card.querySelectorAll('#fullcheck-month-select option')).map(o => o.innerText.trim());
    const selectedMonth = card.querySelector('#fullcheck-month-select option:checked')?.innerText.trim();
    const selectedYear = card.querySelector('#fullcheck-year-select option:checked')?.innerText.trim();

    const monthlyOverviewBtn = card.querySelector('button[onclick*="onMonthlyOverviewClick"]')?.innerText.trim();
    const prevMonthTitle = card.querySelector('#fullcheck-prev-month-btn')?.getAttribute('title');

    return {
        heading,
        trackerName,
        closeBtnTitle,
        weekdays,
        selectedMonth,
        selectedYear,
        monthSelectOptions: monthSelectOptions.slice(0, 4),
        monthlyOverviewBtn,
        prevMonthTitle
    };
})()
""")

print("Vietnamese Full-check Audit:\n", json.dumps(vi_audit, ensure_ascii=False, indent=2))

assert vi_audit is not None, "Full-check modal card not found!"
assert vi_audit["heading"] == "Full-check", f"Expected heading 'Full-check', got '{vi_audit['heading']}'"
assert vi_audit["weekdays"] == ["T2", "T3", "T4", "T5", "T6", "T7", "CN"], f"Expected weekdays ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'], got {vi_audit['weekdays']}"
assert vi_audit["monthlyOverviewBtn"] == "Tổng quan tháng", f"Expected 'Tổng quan tháng', got '{vi_audit['monthlyOverviewBtn']}'"
assert vi_audit["selectedMonth"] == "Tháng 11", f"Expected 'Tháng 11', got '{vi_audit['selectedMonth']}'"
assert vi_audit["selectedYear"] == "2026", f"Expected '2026', got '{vi_audit['selectedYear']}'"
assert vi_audit["closeBtnTitle"] == "Đóng", f"Expected 'Đóng', got '{vi_audit['closeBtnTitle']}'"
assert vi_audit["prevMonthTitle"] == "Tháng trước", f"Expected 'Tháng trước', got '{vi_audit['prevMonthTitle']}'"

print("✓ Test 1 passed: All Vietnamese labels in Full-check modal match exact specifications.")
capture_screenshot("fullcheck_modal_vi.png")
capture_element("#selfcheck-fullcheck-modal-card", "fullcheck_modal_vi_closeup.png")


# TEST 2: Live Language Switch to English
print("\n--- TEST 2: Live Switch to English ---")
eval_js("window.TempoI18n.setLanguage('en')")
time.sleep(0.5)

en_audit = eval_js("""
(() => {
    const card = document.getElementById('selfcheck-fullcheck-modal-card');
    const heading = card.querySelector('span.text-xs.font-bold')?.innerText.trim();
    const trackerName = card.querySelector('h2')?.innerText.trim();
    const closeBtnTitle = card.querySelector('button.absolute.top-4.right-4')?.getAttribute('title');

    const weekdays = Array.from(card.querySelectorAll('.grid.grid-cols-7 span.text-xs.font-bold')).map(s => s.innerText.trim());
    const selectedMonth = card.querySelector('#fullcheck-month-select option:checked')?.innerText.trim();
    const selectedYear = card.querySelector('#fullcheck-year-select option:checked')?.innerText.trim();
    const monthlyOverviewBtn = card.querySelector('button[onclick*="onMonthlyOverviewClick"]')?.innerText.trim();
    const prevMonthTitle = card.querySelector('#fullcheck-prev-month-btn')?.getAttribute('title');

    return {
        heading,
        trackerName,
        closeBtnTitle,
        weekdays,
        selectedMonth,
        selectedYear,
        monthlyOverviewBtn,
        prevMonthTitle
    };
})()
""")

print("English Full-check Audit:\n", json.dumps(en_audit, ensure_ascii=False, indent=2))
assert en_audit["heading"] == "Your full check", f"Expected 'Your full check', got '{en_audit['heading']}'"
assert en_audit["weekdays"] == ["Mon", "Tue", "Wed", "Thurs", "Fri", "Sat", "Sun"], f"Expected ['Mon', 'Tue', 'Wed', 'Thurs', 'Fri', 'Sat', 'Sun'], got {en_audit['weekdays']}"
assert en_audit["monthlyOverviewBtn"] == "Monthly Overview", f"Expected 'Monthly Overview', got '{en_audit['monthlyOverviewBtn']}'"
assert en_audit["selectedMonth"] == "November", f"Expected 'November', got '{en_audit['selectedMonth']}'"
assert en_audit["selectedYear"] == "2026", f"Expected '2026', got '{en_audit['selectedYear']}'"
assert en_audit["closeBtnTitle"] == "Close", f"Expected 'Close', got '{en_audit['closeBtnTitle']}'"
assert en_audit["prevMonthTitle"] == "Previous month", f"Expected 'Previous month', got '{en_audit['prevMonthTitle']}'"

print("✓ Test 2 passed: English labels preserved and reactive.")
capture_screenshot("fullcheck_modal_en.png")
capture_element("#selfcheck-fullcheck-modal-card", "fullcheck_modal_en_closeup.png")


# TEST 3: Live Switch Back to Vietnamese
print("\n--- TEST 3: Live Switch Back to Vietnamese ---")
eval_js("window.TempoI18n.setLanguage('vi')")
time.sleep(0.5)

recheck_heading = eval_js("document.querySelector('#selfcheck-fullcheck-modal-card span.text-xs.font-bold')?.innerText.trim()")
recheck_weekdays = eval_js("Array.from(document.querySelectorAll('#selfcheck-fullcheck-modal-card .grid.grid-cols-7 span.text-xs.font-bold')).map(s => s.innerText.trim())")
recheck_btn = eval_js("document.querySelector('#selfcheck-fullcheck-modal-card button[onclick*=\"onMonthlyOverviewClick\"]')?.innerText.trim()")

assert recheck_heading == "Full-check", f"Expected 'Full-check', got '{recheck_heading}'"
assert recheck_weekdays == ["T2", "T3", "T4", "T5", "T6", "T7", "CN"], f"Recheck weekdays failed: {recheck_weekdays}"
assert recheck_btn == "Tổng quan tháng", f"Expected 'Tổng quan tháng', got '{recheck_btn}'"
print("✓ Test 3 passed: Instant live switch back to Vietnamese verified.")


# TEST 4: Navigation controls in Calendar
print("\n--- TEST 4: Calendar Navigation (Prev Month & Return to Current Month) ---")
eval_js("window.TempoSelfCheckWorkspace.prevMonthFullCheck()")
time.sleep(0.4)

prev_month_audit = eval_js("""
(() => {
    const card = document.getElementById('selfcheck-fullcheck-modal-card');
    const selectedMonth = card.querySelector('#fullcheck-month-select option:checked')?.innerText.trim();
    const returnPill = document.getElementById('fullcheck-return-current-btn')?.innerText.trim();
    return { selectedMonth, returnPill };
})()
""")
print("Prev Month Nav Audit:", json.dumps(prev_month_audit, ensure_ascii=False, indent=2))
assert prev_month_audit["selectedMonth"] == "Tháng 10", f"Expected 'Tháng 10', got '{prev_month_audit['selectedMonth']}'"
assert prev_month_audit["returnPill"] == "Tháng hiện tại", f"Expected 'Tháng hiện tại', got '{prev_month_audit['returnPill']}'"

# Return to current month
eval_js("window.TempoSelfCheckWorkspace.jumpToCurrentMonthFullCheck()")
time.sleep(0.4)
returned_month = eval_js("document.querySelector('#fullcheck-month-select option:checked')?.innerText.trim()")
assert returned_month == "Tháng 11", f"Expected 'Tháng 11' after jumpToCurrentMonth, got '{returned_month}'"
print("✓ Test 4 passed: Calendar navigation controls function properly with localized labels.")


# TEST 5: Monthly Overview Modal Localization & Navigation
print("\n--- TEST 5: Monthly Overview Modal in Vietnamese & English ---")
eval_js("window.TempoSelfCheckWorkspace.onMonthlyOverviewClick('trk-tension')")
time.sleep(0.5)

mo_vi_audit = eval_js("""
(() => {
    const card = document.getElementById('selfcheck-monthly-overview-card');
    if (!card) return null;
    const title = card.querySelector('span.text-xs.font-bold')?.innerText.trim();
    const backBtn = card.querySelector('button.inline-flex.items-center span:nth-child(2)')?.innerText.trim();
    const monthYear = card.querySelector('.text-xs.sm\\\\:text-sm.font-extrabold.text-\\\\[\\\\#C87D55\\\\]')?.innerText.trim();
    return { title, backBtn, monthYear };
})()
""")

print("Monthly Overview VI Audit:", json.dumps(mo_vi_audit, ensure_ascii=False, indent=2))
assert mo_vi_audit["title"] == "Tổng quan tháng", f"Expected 'Tổng quan tháng', got '{mo_vi_audit['title']}'"
assert mo_vi_audit["backBtn"] == "Quay lại lịch", f"Expected 'Quay lại lịch', got '{mo_vi_audit['backBtn']}'"
assert "Tháng 11 2026" in mo_vi_audit["monthYear"], f"Expected 'Tháng 11 2026', got '{mo_vi_audit['monthYear']}'"
capture_element("#selfcheck-monthly-overview-card", "monthly_overview_vi_closeup.png")

# Live switch Monthly Overview to English
eval_js("window.TempoI18n.setLanguage('en')")
time.sleep(0.5)

mo_en_audit = eval_js("""
(() => {
    const card = document.getElementById('selfcheck-monthly-overview-card');
    const title = card.querySelector('span.text-xs.font-bold')?.innerText.trim();
    const backBtn = card.querySelector('button.inline-flex.items-center span:nth-child(2)')?.innerText.trim();
    const monthYear = card.querySelector('.text-xs.sm\\\\:text-sm.font-extrabold.text-\\\\[\\\\#C87D55\\\\]')?.innerText.trim();
    return { title, backBtn, monthYear };
})()
""")

print("Monthly Overview EN Audit:", json.dumps(mo_en_audit, ensure_ascii=False, indent=2))
assert mo_en_audit["title"] == "Monthly Overview", f"Expected 'Monthly Overview', got '{mo_en_audit['title']}'"
assert mo_en_audit["backBtn"] == "Back to calendar", f"Expected 'Back to calendar', got '{mo_en_audit['backBtn']}'"
assert "November 2026" in mo_en_audit["monthYear"], f"Expected 'November 2026', got '{mo_en_audit['monthYear']}'"
capture_element("#selfcheck-monthly-overview-card", "monthly_overview_en_closeup.png")

# Test Back to calendar button
eval_js("window.TempoSelfCheckWorkspace.closeMonthlyOverview()")
time.sleep(0.4)
is_fullcheck_visible = eval_js("!document.getElementById('modal-selfcheck-fullcheck')?.classList.contains('hidden')")
assert is_fullcheck_visible, "Full-check calendar modal should be visible after returning from Monthly Overview"
print("✓ Test 5 passed: Monthly Overview localized in VI and EN, seamless back navigation to Full-check calendar.")

# Close Full-check modal
eval_js("window.TempoSelfCheckWorkspace.closeFullCheckPlaceholder()")
time.sleep(0.3)

print("\n=== ALL 5 TESTS PASSED SUCCESSFULLY ===")

try:
    ws.close()
    proc.terminate()
except Exception:
    pass
