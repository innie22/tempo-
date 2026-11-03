import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.parse
from websocket import create_connection

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PORT = 9228
USER_DATA = r"C:\Users\YEN NHI\AppData\Local\Temp\edge_test_navbar_label"
ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"

def start_edge():
    cmd = [
        EDGE_PATH,
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={USER_DATA}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1280,1000",
        "http://127.0.0.1:8000/#recovery"
    ]
    return subprocess.Popen(cmd)

def send_cdp(ws, method, params=None, msg_id=[1]):
    m = {"id": msg_id[0], "method": method, "params": params or {}}
    msg_id[0] += 1
    ws.send(json.dumps(m))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == m["id"]:
            return resp

def evaluate_js(ws, expr):
    res = send_cdp(ws, "Runtime.evaluate", {
        "expression": expr,
        "returnByValue": True,
        "awaitPromise": True
    })
    if "exceptionDetails" in res.get("result", {}):
        print("JS Exception:", res["result"]["exceptionDetails"])
    if "result" in res and "result" in res["result"]:
        return res["result"]["result"].get("value")
    return None

def capture_screenshot(ws, clip, file_path):
    params = {"format": "png"}
    if clip:
        params["clip"] = clip
    res = send_cdp(ws, "Page.captureScreenshot", params)
    if "result" in res and "data" in res["result"]:
        import base64
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(res["result"]["data"]))
        print(f"Saved screenshot: {file_path}")

def run_test():
    print("Starting Edge on port", PORT)
    proc = start_edge()
    time.sleep(2)

    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")
        tabs = json.loads(req.read().decode())
        page_tabs = [t for t in tabs if t.get("type") == "page"]
        target = page_tabs[0] if page_tabs else tabs[0]
        ws_url = target["webSocketDebuggerUrl"]
        print("Connecting to CDP target:", target.get("url"))
        ws = create_connection(ws_url)

        send_cdp(ws, "Page.enable")
        send_cdp(ws, "Runtime.enable")
        time.sleep(1)

        for _ in range(20):
            ready = evaluate_js(ws, "Boolean(window.TempoMode && window.TempoMode.updateNavbarForMode && window.TempoI18n)")
            if ready:
                break
            time.sleep(0.5)

        # Helper to get navbar status
        get_navbar_status = """
        (() => {
            const l1 = document.getElementById('nav-link-what-is-tempo');
            const l2 = document.getElementById('nav-link-check');
            const l3 = document.getElementById('nav-link-plan');
            const l4 = document.getElementById('nav-link-community');
            const nav = document.querySelector('header nav');
            const rect = nav ? nav.getBoundingClientRect() : null;
            return {
                l1: l1 ? { text: l1.textContent.trim(), href: l1.getAttribute('href') } : null,
                l2: l2 ? { text: l2.textContent.trim(), href: l2.getAttribute('href'), title: l2.getAttribute('title') } : null,
                l3: l3 ? { text: l3.textContent.trim(), href: l3.getAttribute('href'), title: l3.getAttribute('title') } : null,
                l4: l4 ? { text: l4.textContent.trim(), href: l4.getAttribute('href') } : null,
                clip: rect ? { x: Math.max(0, rect.x - 100), y: Math.max(0, rect.y - 10), width: rect.width + 200, height: rect.height + 20, scale: 1 } : null
            };
        })()
        """

        header_clip = {"x": 0, "y": 0, "width": 1280, "height": 80, "scale": 1}

        # -------------------------------------------------------------
        # STEP 1: Verify Rmode in Vietnamese mode (vi)
        # -------------------------------------------------------------
        print("\n=== 1. Testing Rmode in Vietnamese mode (vi) ===")
        evaluate_js(ws, """
        (() => {
            window.TempoMode.setMode('recovery');
            window.TempoI18n.setLanguage('vi');
        })()
        """)
        time.sleep(0.5)
        rmode_vi = evaluate_js(ws, get_navbar_status)
        print("Rmode (VI) Navbar status:", json.dumps(rmode_vi, ensure_ascii=False, indent=2))

        assert rmode_vi["l2"]["text"] == "Plan", f"Expected Link 2 in Rmode (VI) to be 'Plan', got: {rmode_vi['l2']['text']}"
        assert rmode_vi["l2"]["href"] == "#recovery-working-plan", f"Expected Link 2 href to be '#recovery-working-plan', got: {rmode_vi['l2']['href']}"
        assert rmode_vi["l2"]["title"] == "Plan", f"Expected Link 2 title to be 'Plan', got: {rmode_vi['l2']['title']}"
        assert rmode_vi["l1"]["text"] == "Giới thiệu", f"Expected Link 1 to be 'Giới thiệu', got: {rmode_vi['l1']['text']}"
        assert rmode_vi["l3"]["text"] == "Test", f"Expected Link 3 to be 'Test', got: {rmode_vi['l3']['text']}"
        assert rmode_vi["l4"]["text"] == "Cộng đồng", f"Expected Link 4 to be 'Cộng đồng', got: {rmode_vi['l4']['text']}"
        print("✓ Rmode (VI) correctly displays 'Plan' for Link 2 with '#recovery-working-plan' destination preserved!")

        ss_rmode_vi = os.path.join(ARTIFACT_DIR, "rmode_navbar_vi.png")
        capture_screenshot(ws, header_clip, ss_rmode_vi)

        # Test Link 2 click behavior in Rmode
        click_test = evaluate_js(ws, """
        (() => {
            let scrolled = false;
            const origScroll = window.TempoApp.scrollToRecoveryPlan;
            window.TempoApp.scrollToRecoveryPlan = () => { scrolled = true; };
            const l2 = document.getElementById('nav-link-check');
            l2.click();
            window.TempoApp.scrollToRecoveryPlan = origScroll;
            return { scrolled };
        })()
        """)
        assert click_test["scrolled"] == True, "Expected Link 2 click to trigger scrollToRecoveryPlan"
        print("✓ Link 2 click behavior preserved and triggers scrollToRecoveryPlan successfully!")

        # -------------------------------------------------------------
        # STEP 2: Verify Rmode in English mode (en)
        # -------------------------------------------------------------
        print("\n=== 2. Testing Rmode in English mode (en) ===")
        evaluate_js(ws, """
        (() => {
            window.TempoI18n.setLanguage('en');
        })()
        """)
        time.sleep(0.5)
        rmode_en = evaluate_js(ws, get_navbar_status)
        print("Rmode (EN) Navbar status:", json.dumps(rmode_en, ensure_ascii=False, indent=2))

        assert rmode_en["l2"]["text"] == "Plan", f"Expected Link 2 in Rmode (EN) to be 'Plan', got: {rmode_en['l2']['text']}"
        assert rmode_en["l2"]["href"] == "#recovery-working-plan", f"Expected Link 2 href to be '#recovery-working-plan', got: {rmode_en['l2']['href']}"
        assert rmode_en["l2"]["title"] == "Plan", f"Expected Link 2 title to be 'Plan', got: {rmode_en['l2']['title']}"
        assert rmode_en["l1"]["text"] == "About", f"Expected Link 1 to be 'About', got: {rmode_en['l1']['text']}"
        assert rmode_en["l3"]["text"] == "Assessment", f"Expected Link 3 to be 'Assessment', got: {rmode_en['l3']['text']}"
        assert rmode_en["l4"]["text"] == "Community", f"Expected Link 4 to be 'Community', got: {rmode_en['l4']['text']}"
        print("✓ Rmode (EN) correctly displays 'Plan' for Link 2 with '#recovery-working-plan' destination preserved!")

        ss_rmode_en = os.path.join(ARTIFACT_DIR, "rmode_navbar_en.png")
        capture_screenshot(ws, header_clip, ss_rmode_en)

        # -------------------------------------------------------------
        # STEP 3: Verify URmode navbar is NOT modified
        # -------------------------------------------------------------
        print("\n=== 3. Testing URmode navbar (must remain unchanged) ===")
        # URmode VI
        evaluate_js(ws, """
        (() => {
            window.TempoMode.setMode('emergency');
            window.TempoI18n.setLanguage('vi');
        })()
        """)
        time.sleep(0.5)
        urmode_vi = evaluate_js(ws, get_navbar_status)
        print("URmode (VI) Navbar status:", json.dumps(urmode_vi, ensure_ascii=False, indent=2))
        assert urmode_vi["l2"]["text"] == "Check", f"Expected URmode Link 2 to be 'Check', got: {urmode_vi['l2']['text']}"
        assert urmode_vi["l3"]["text"] == "Test", f"Expected URmode Link 3 (VI) to be 'Test', got: {urmode_vi['l3']['text']}"
        print("✓ URmode (VI) navbar is completely unmodified (Check · Test)!")

        ss_urmode_vi = os.path.join(ARTIFACT_DIR, "urmode_navbar_vi.png")
        capture_screenshot(ws, header_clip, ss_urmode_vi)

        # URmode EN
        evaluate_js(ws, """
        (() => {
            window.TempoI18n.setLanguage('en');
        })()
        """)
        time.sleep(0.5)
        urmode_en = evaluate_js(ws, get_navbar_status)
        print("URmode (EN) Navbar status:", json.dumps(urmode_en, ensure_ascii=False, indent=2))
        assert urmode_en["l2"]["text"] == "Check", f"Expected URmode Link 2 to be 'Check', got: {urmode_en['l2']['text']}"
        assert urmode_en["l3"]["text"] == "Assessment", f"Expected URmode Link 3 (EN) to be 'Assessment', got: {urmode_en['l3']['text']}"
        print("✓ URmode (EN) navbar is completely unmodified (Check · Assessment)!")

        # -------------------------------------------------------------
        # STEP 4: Verify Entry Home navbar is NOT modified
        # -------------------------------------------------------------
        print("\n=== 4. Testing Entry Home navbar (must remain unchanged) ===")
        evaluate_js(ws, """
        (() => {
            window.TempoMode.setMode('default');
            window.TempoI18n.setLanguage('vi');
        })()
        """)
        time.sleep(0.5)
        entry_vi = evaluate_js(ws, get_navbar_status)
        print("Entry (VI) Navbar status:", json.dumps(entry_vi, ensure_ascii=False, indent=2))
        assert entry_vi["l2"]["text"] == "Check", f"Expected Entry Link 2 to be 'Check', got: {entry_vi['l2']['text']}"
        assert entry_vi["l3"]["text"] == "Plan", f"Expected Entry Link 3 to be 'Plan', got: {entry_vi['l3']['text']}"
        print("✓ Entry Home (VI) navbar is completely unmodified (Check · Plan)!")

        evaluate_js(ws, """
        (() => {
            window.TempoI18n.setLanguage('en');
        })()
        """)
        time.sleep(0.5)
        entry_en = evaluate_js(ws, get_navbar_status)
        print("Entry (EN) Navbar status:", json.dumps(entry_en, ensure_ascii=False, indent=2))
        assert entry_en["l2"]["text"] == "Check", f"Expected Entry Link 2 to be 'Check', got: {entry_en['l2']['text']}"
        assert entry_en["l3"]["text"] == "Plan", f"Expected Entry Link 3 to be 'Plan', got: {entry_en['l3']['text']}"
        print("✓ Entry Home (EN) navbar is completely unmodified (Check · Plan)!")

        print("\n" + "="*55)
        print("ALL RMODE NAVBAR LABEL VERIFICATION CHECKS PASSED!")
        print("="*55)

    finally:
        try:
            ws.close()
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    run_test()
