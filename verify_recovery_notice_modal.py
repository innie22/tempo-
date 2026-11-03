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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_recnotice_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9637

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
    "http://127.0.0.1:8000/#recovery"
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
    proc.kill()
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

try:
    print("Waiting for page scripts...")
    for _ in range(20):
        ready = eval_js("document.readyState === 'complete' && !!window.TempoRecoveryNote && !!window.TempoI18n")
        if ready:
            break
        time.sleep(0.5)

    print("Page ready! Initializing test...")

    # -------------------------------------------------------------
    # TEST 1: Vietnamese Mode
    # -------------------------------------------------------------
    print("\n--- TEST 1: Vietnamese Mode ---")
    eval_js("window.TempoI18n.setLanguage('vi')")
    time.sleep(0.3)
    eval_js("window.TempoRecoveryNote.openViewModal()")
    time.sleep(0.5)

    is_visible = eval_js("!document.getElementById('modal-recovery-note-view').classList.contains('hidden')")
    assert is_visible, "View modal should be visible"

    info_vi = eval_js("""
    (() => {
        return {
            header: document.getElementById('modal-recovery-note-view-header')?.textContent?.trim(),
            title: document.getElementById('modal-recovery-note-view-title')?.textContent?.trim(),
            subtitle: document.getElementById('modal-recovery-note-view-subtitle')?.textContent?.trim(),
            editBtn: document.getElementById('modal-recovery-note-view-edit-btn')?.textContent?.trim(),
            closeBtn: document.getElementById('modal-recovery-note-view-close-btn')?.textContent?.trim(),
            closeXTitle: document.getElementById('modal-recovery-note-view-close-x')?.getAttribute('title')
        };
    })()
    """)

    print("Vietnamese Modal Texts:", json.dumps(info_vi, indent=2, ensure_ascii=False))
    assert info_vi['header'] == "LỜI NHẮN PHỤC HỒI", f"Header mismatch: {info_vi['header']}"
    assert info_vi['title'] == "Lời nhắn dành cho tôi", f"Title mismatch: {info_vi['title']}"
    assert info_vi['subtitle'] == "Những điều bạn muốn nhắc nhở bản thân khi mọi thứ trở nên khó khăn.", f"Subtitle mismatch: {info_vi['subtitle']}"
    assert info_vi['editBtn'] == "Chỉnh sửa lời nhắn", f"Edit btn mismatch: {info_vi['editBtn']}"
    assert info_vi['closeBtn'] == "Đóng", f"Close btn mismatch: {info_vi['closeBtn']}"
    assert info_vi['closeXTitle'] == "Đóng", f"Close X title mismatch: {info_vi['closeXTitle']}"
    print("✓ Test 1 Passed: Vietnamese texts match exact specifications!")

    capture_screenshot("recovery_notice_modal_vi.png")
    capture_element("#modal-recovery-note-view .tempo-card", "recovery_notice_modal_vi_closeup.png")

    # -------------------------------------------------------------
    # TEST 2: English Mode (Live Switch while modal is open)
    # -------------------------------------------------------------
    print("\n--- TEST 2: English Mode (Live Switch) ---")
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(0.5)

    info_en = eval_js("""
    (() => {
        return {
            header: document.getElementById('modal-recovery-note-view-header')?.textContent?.trim(),
            title: document.getElementById('modal-recovery-note-view-title')?.textContent?.trim(),
            subtitle: document.getElementById('modal-recovery-note-view-subtitle')?.textContent?.trim(),
            editBtn: document.getElementById('modal-recovery-note-view-edit-btn')?.textContent?.trim(),
            closeBtn: document.getElementById('modal-recovery-note-view-close-btn')?.textContent?.trim(),
            closeXTitle: document.getElementById('modal-recovery-note-view-close-x')?.getAttribute('title')
        };
    })()
    """)

    print("English Modal Texts:", json.dumps(info_en, indent=2, ensure_ascii=False))
    assert info_en['header'] == "RECOVERY NOTICE", f"Header mismatch: {info_en['header']}"
    assert info_en['title'] == "My Recovery Notice", f"Title mismatch: {info_en['title']}"
    assert info_en['subtitle'] == "Things you wanted to remember when things feel heavy.", f"Subtitle mismatch: {info_en['subtitle']}"
    assert info_en['editBtn'] == "Edit note", f"Edit btn mismatch: {info_en['editBtn']}"
    assert info_en['closeBtn'] == "Close", f"Close btn mismatch: {info_en['closeBtn']}"
    assert info_en['closeXTitle'] == "Close", f"Close X title mismatch: {info_en['closeXTitle']}"
    print("✓ Test 2 Passed: English texts match exact specifications!")

    capture_screenshot("recovery_notice_modal_en.png")
    capture_element("#modal-recovery-note-view .tempo-card", "recovery_notice_modal_en_closeup.png")

    # -------------------------------------------------------------
    # TEST 3: Switch back to Vietnamese
    # -------------------------------------------------------------
    print("\n--- TEST 3: Switch back to Vietnamese ---")
    eval_js("window.TempoI18n.setLanguage('vi')")
    time.sleep(0.3)

    info_vi_again = eval_js("""
    (() => {
        return {
            header: document.getElementById('modal-recovery-note-view-header')?.textContent?.trim(),
            title: document.getElementById('modal-recovery-note-view-title')?.textContent?.trim(),
            editBtn: document.getElementById('modal-recovery-note-view-edit-btn')?.textContent?.trim(),
            closeBtn: document.getElementById('modal-recovery-note-view-close-btn')?.textContent?.trim()
        };
    })()
    """)
    assert info_vi_again['header'] == "LỜI NHẮN PHỤC HỒI"
    assert info_vi_again['title'] == "Lời nhắn dành cho tôi"
    assert info_vi_again['editBtn'] == "Chỉnh sửa lời nhắn"
    assert info_vi_again['closeBtn'] == "Đóng"
    print("✓ Test 3 Passed: Dynamic toggle back to Vietnamese confirmed!")

    # -------------------------------------------------------------
    # TEST 4: Buttons Behavior
    # -------------------------------------------------------------
    print("\n--- TEST 4: Buttons Behavior ---")
    # 4a. Click Edit note
    eval_js("document.getElementById('modal-recovery-note-view-edit-btn').click()")
    time.sleep(0.3)
    view_hidden = eval_js("document.getElementById('modal-recovery-note-view').classList.contains('hidden')")
    edit_visible = eval_js("!document.getElementById('modal-recovery-note-edit').classList.contains('hidden')")
    assert view_hidden, "View modal should hide on Edit click"
    assert edit_visible, "Edit modal should open on Edit click"
    print("✓ 4a: Edit note button opens edit modal correctly")

    # Close edit modal
    eval_js("window.TempoRecoveryNote.closeEditModal()")
    time.sleep(0.3)

    # 4b. Reopen and click Close button
    eval_js("window.TempoRecoveryNote.openViewModal()")
    time.sleep(0.3)
    eval_js("document.getElementById('modal-recovery-note-view-close-btn').click()")
    time.sleep(0.3)
    assert eval_js("document.getElementById('modal-recovery-note-view').classList.contains('hidden')"), "View modal closed via Close button"
    print("✓ 4b: Close button works correctly")

    # 4c. Reopen and click Close X button
    eval_js("window.TempoRecoveryNote.openViewModal()")
    time.sleep(0.3)
    eval_js("document.getElementById('modal-recovery-note-view-close-x').click()")
    time.sleep(0.3)
    assert eval_js("document.getElementById('modal-recovery-note-view').classList.contains('hidden')"), "View modal closed via ✕ button"
    print("✓ 4c: Close ✕ button works correctly")

    print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")

finally:
    try:
        ws.close()
    except Exception:
        pass
    proc.kill()
