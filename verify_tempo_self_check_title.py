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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_selfcheck_title_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9632

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
        return {{ x: Math.max(0, r.x - 15), y: Math.max(0, r.y - 15), width: r.width + 30, height: r.height + 30 }};
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

print("\n=== STARTING VERIFICATION: TEMPO SELF-CHECK CONSISTENT TITLE ===\n")

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
        { id: 'trk-tension', user_id: 'local_dev_alex', name: 'Tension', category: 'stress_sign', check_method: 'percentage', is_active: true, order_index: 0 },
        { id: 'trk-sleep', user_id: 'local_dev_alex', name: 'Sleep', category: 'supportive', check_method: 'yes_no', is_active: true, order_index: 1 }
    ];
    localStorage.setItem(trackersKey, JSON.stringify(mockTrackers));

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

# TEST 1: Verify title in Vietnamese mode is "Tempo Self-check"
print("--- TEST 1: Page title in Vietnamese ('vi') mode ---")
vi_title_info = eval_js("""
(() => {
    const root = document.getElementById('self-check-workspace-root');
    const h1 = root ? root.querySelector('h1') : null;
    const fullText = root ? root.innerText : '';
    return {
        titleText: h1 ? h1.innerText.trim() : null,
        titleClasses: h1 ? h1.className : null,
        containerClasses: h1 && h1.parentElement ? h1.parentElement.className : null,
        hasOldTranslatedTitle: fullText.includes('Tự kiểm tra Tempo')
    };
})()
""")

print("Vietnamese Title Audit:", json.dumps(vi_title_info, ensure_ascii=False, indent=2))
assert vi_title_info["titleText"] == "Tempo Self-check", f"Expected 'Tempo Self-check', got '{vi_title_info['titleText']}'"
assert not vi_title_info["hasOldTranslatedTitle"], "Deprecated title 'Tự kiểm tra Tempo' found in DOM!"
assert "font-heading" in vi_title_info["titleClasses"], "Title font-heading class missing"
assert "text-[#234E3B]" in vi_title_info["titleClasses"], "Title color text-[#234E3B] missing"
assert "absolute left-1/2 -translate-x-1/2" in vi_title_info["containerClasses"], "Centered positioning container missing"
print("✓ Test 1 passed: Page title in Vietnamese mode is exactly 'Tempo Self-check'.")
capture_screenshot("selfcheck_title_vi.png")
capture_element("#self-check-workspace-root .relative.flex.items-center.justify-between", "selfcheck_title_vi_header_closeup.png")


# TEST 2: Verify title in English mode is "Tempo Self-check"
print("\n--- TEST 2: Page title in English ('en') mode ---")
eval_js("window.TempoI18n.setLanguage('en')")
time.sleep(0.5)

en_title_info = eval_js("""
(() => {
    const root = document.getElementById('self-check-workspace-root');
    const h1 = root ? root.querySelector('h1') : null;
    return {
        titleText: h1 ? h1.innerText.trim() : null,
        titleClasses: h1 ? h1.className : null,
        containerClasses: h1 && h1.parentElement ? h1.parentElement.className : null
    };
})()
""")

print("English Title Audit:", json.dumps(en_title_info, ensure_ascii=False, indent=2))
assert en_title_info["titleText"] == "Tempo Self-check", f"Expected 'Tempo Self-check', got '{en_title_info['titleText']}'"
assert "font-heading" in en_title_info["titleClasses"], "Title font-heading class missing"
print("✓ Test 2 passed: Page title in English mode is exactly 'Tempo Self-check'.")
capture_screenshot("selfcheck_title_en.png")
capture_element("#self-check-workspace-root .relative.flex.items-center.justify-between", "selfcheck_title_en_header_closeup.png")


# TEST 3: Live switch back to Vietnamese
print("\n--- TEST 3: Live Switch Back to Vietnamese ---")
eval_js("window.TempoI18n.setLanguage('vi')")
time.sleep(0.5)

recheck_title = eval_js("document.querySelector('#self-check-workspace-root h1')?.innerText.trim()")
assert recheck_title == "Tempo Self-check", f"Expected 'Tempo Self-check' after re-switch, got '{recheck_title}'"
print("✓ Test 3 passed: Title remains 'Tempo Self-check' when switching back to Vietnamese.")

print("\n=== ALL 3 TESTS PASSED SUCCESSFULLY ===")

try:
    ws.close()
    proc.terminate()
except Exception:
    pass
