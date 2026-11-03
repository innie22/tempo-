# -*- coding: utf-8 -*-
import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import base64
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_ngaymai_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9292

    cmd = [
        edge_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "http://localhost:8000/"
    ]

    log(f"Launching Edge on port {port}...")
    proc = subprocess.Popen(cmd)
    ws = None
    try:
        ws_url = None
        for _ in range(30):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as resp:
                    tabs = json.loads(resp.read().decode())
                    pages = [t for t in tabs if t.get("type") == "page"]
                    if pages:
                        ws_url = pages[0]["webSocketDebuggerUrl"]
                        break
            except Exception:
                time.sleep(0.5)

        if not ws_url:
            raise RuntimeError("Failed to connect to Edge CDP endpoint")

        log(f"Connected to CDP: {ws_url}")
        ws = websocket.create_connection(ws_url)

        msg_id = 1
        def send_command(method, params=None):
            nonlocal msg_id
            cid = msg_id
            msg_id += 1
            req = {"id": cid, "method": method}
            if params:
                req["params"] = params
            ws.send(json.dumps(req))
            while True:
                raw = ws.recv()
                res = json.loads(raw)
                if res.get("id") == cid:
                    return res

        def evaluate(expr):
            res = send_command("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True
            })
            if "exceptionDetails" in res.get("result", {}):
                raise RuntimeError(f"JS Exception: {res['result']['exceptionDetails']}")
            return res.get("result", {}).get("result", {}).get("value")

        def capture_screenshot(filename):
            res = send_command("Page.captureScreenshot", {"format": "png"})
            data = res.get("result", {}).get("data", "")
            if data:
                path = os.path.join(ARTIFACT_DIR, filename)
                with open(path, "wb") as f:
                    f.write(base64.b64decode(data))
                log(f"Saved screenshot: {path}")

        # Wait for page ready
        for _ in range(50):
            try:
                ready = evaluate("Boolean(window.TempoMode && window.TempoApp && window.TempoEmergencySupport && window.TempoI18n)")
                if ready:
                    break
            except Exception:
                pass
            time.sleep(0.3)

        send_command("Emulation.setDeviceMetricsOverride", {
            "width": 1280,
            "height": 950,
            "deviceScaleFactor": 1,
            "mobile": False
        })
        time.sleep(0.5)

        # ---------------------------------------------------------------------
        # TEST 1: Open Human Support Drawer and Verify Order & Vietnamese Copy
        # ---------------------------------------------------------------------
        log("\n--- TEST 1: Order & Vietnamese Copy in Human Support Drawer ---")
        evaluate("window.TempoEmergencySupport.openSOS()")
        evaluate("window.TempoEmergencySupport.openHumanDrawer()")
        time.sleep(0.5)

        drawer_state = evaluate("""(() => {
            const drawer = document.getElementById('human-support-drawer');
            const medCard = document.getElementById('drawer-medical-title');
            const hopeCard = document.getElementById('drawer-hotline-title');
            const ngayMaiCard = document.getElementById('drawer-card-ngaymai');
            const waitingHeader = document.getElementById('drawer-waiting-header');

            // Check order in DOM hierarchy
            const parent = ngayMaiCard ? ngayMaiCard.parentElement : null;
            const children = parent ? Array.from(parent.children) : [];
            
            const medIndex = children.findIndex(el => el.contains(medCard));
            const hopeIndex = children.findIndex(el => el.contains(hopeCard));
            const ngayMaiIndex = children.indexOf(ngayMaiCard);
            const waitingIndex = children.findIndex(el => el.contains(waitingHeader));

            const title = document.getElementById('drawer-ngaymai-title') ? document.getElementById('drawer-ngaymai-title').textContent.trim() : '';
            const badge = document.getElementById('drawer-ngaymai-badge') ? document.getElementById('drawer-ngaymai-badge').textContent.trim() : '';
            const desc = document.getElementById('drawer-ngaymai-desc') ? document.getElementById('drawer-ngaymai-desc').textContent.trim() : '';
            const hours = document.getElementById('drawer-ngaymai-hours') ? document.getElementById('drawer-ngaymai-hours').textContent.trim() : '';
            const callLink = document.getElementById('drawer-ngaymai-call');
            const callText = callLink ? callLink.textContent.trim() : '';
            const callHref = callLink ? callLink.getAttribute('href') : '';

            return {
                drawerVisible: !drawer.classList.contains('hidden'),
                medIndex,
                hopeIndex,
                ngayMaiIndex,
                waitingIndex,
                title,
                badge,
                desc,
                hours,
                callText,
                callHref,
                has115: !!document.getElementById('drawer-medical-call'),
                hasHope: !!document.getElementById('drawer-hotline-call')
            };
        })()""")

        log(f"Drawer state: {drawer_state}")
        assert drawer_state['drawerVisible'] == True, "Drawer should be visible"
        assert drawer_state['has115'] == True, "115 card must be preserved"
        assert drawer_state['hasHope'] == True, "Hope card must be preserved"
        
        # Verify strict order: 115 < Hope < Ngay Mai < Waiting Guidance
        log(f"Order indices: 115={drawer_state['medIndex']}, HOPE={drawer_state['hopeIndex']}, NgayMai={drawer_state['ngayMaiIndex']}, Waiting={drawer_state['waitingIndex']}")
        assert drawer_state['medIndex'] < drawer_state['hopeIndex'], "115 must precede Hope"
        assert drawer_state['hopeIndex'] < drawer_state['ngayMaiIndex'], "Hope must precede Ngay Mai"
        assert drawer_state['ngayMaiIndex'] < drawer_state['waitingIndex'], "Ngay Mai must precede Waiting guidance"

        # Verify Vietnamese strings
        assert drawer_state['title'] == "ĐƯỜNG DÂY NÓNG NGÀY MAI", "Title mismatch"
        assert drawer_state['badge'] == "Hỗ trợ tâm lý", "Badge mismatch"
        assert "096 306 1414" in drawer_state['callText'], "Phone in CTA mismatch"
        assert drawer_state['desc'] == "Hỗ trợ tâm lý miễn phí qua điện thoại cho người đang gặp khủng hoảng tâm lý, trầm cảm và người thân của họ. Lắng nghe không phán xét, bảo mật thông tin.", "Description mismatch"
        assert drawer_state['hours'] == "13:00 – 20:30, Thứ Tư – Chủ Nhật", "Operating hours mismatch"
        assert drawer_state['callText'] == "Gọi 096 306 1414", "CTA text mismatch"
        assert drawer_state['callHref'] == "tel:0963061414", "CTA tel link mismatch"

        log("✓ EXACT ORDER & VIETNAMESE COPY VERIFIED!")
        capture_screenshot("ngaymai_drawer_vi.png")

        # ---------------------------------------------------------------------
        # TEST 2: Switch to English and Verify English Localization
        # ---------------------------------------------------------------------
        log("\n--- TEST 2: Switch to English and Verify English Localization ---")
        evaluate("window.TempoI18n.setLanguage('en')")
        time.sleep(0.5)

        en_state = evaluate("""(() => {
            const title = document.getElementById('drawer-ngaymai-title') ? document.getElementById('drawer-ngaymai-title').textContent.trim() : '';
            const badge = document.getElementById('drawer-ngaymai-badge') ? document.getElementById('drawer-ngaymai-badge').textContent.trim() : '';
            const desc = document.getElementById('drawer-ngaymai-desc') ? document.getElementById('drawer-ngaymai-desc').textContent.trim() : '';
            const hours = document.getElementById('drawer-ngaymai-hours') ? document.getElementById('drawer-ngaymai-hours').textContent.trim() : '';
            const callLink = document.getElementById('drawer-ngaymai-call');
            const callText = callLink ? callLink.textContent.trim() : '';
            const callHref = callLink ? callLink.getAttribute('href') : '';

            return {
                title,
                badge,
                desc,
                hours,
                callText,
                callHref
            };
        })()""")

        log(f"English state: {en_state}")
        assert en_state['title'] == "NGÀY MAI SUPPORT HOTLINE", "EN Title mismatch"
        assert en_state['badge'] == "Mental Health Support", "EN Badge mismatch"
        assert en_state['desc'] == "Free psychological first aid by phone for people experiencing emotional distress or depression, and their loved ones. Confidential and non-judgmental support.", "EN Desc mismatch"
        assert en_state['hours'] == "1:00 PM – 8:30 PM, Wednesday – Sunday", "EN Hours mismatch"
        assert en_state['callText'] == "Call 096 306 1414", "EN CTA mismatch"
        assert en_state['callHref'] == "tel:0963061414", "EN tel link mismatch"

        log("✓ EXACT ENGLISH COPY VERIFIED!")
        capture_screenshot("ngaymai_drawer_en.png")

        # ---------------------------------------------------------------------
        # TEST 3: Switch back to Vietnamese and verify restoration
        # ---------------------------------------------------------------------
        log("\n--- TEST 3: Switch back to Vietnamese ---")
        evaluate("window.TempoI18n.setLanguage('vi')")
        time.sleep(0.5)

        restored_title = evaluate("document.getElementById('drawer-ngaymai-title').textContent.trim()")
        assert restored_title == "ĐƯỜNG DÂY NÓNG NGÀY MAI", "Restored title mismatch"
        log("✓ DYNAMIC RESTORATION TO VIETNAMESE VERIFIED!")

        # ---------------------------------------------------------------------
        # TEST 4: Step 5A Verification
        # ---------------------------------------------------------------------
        log("\n--- TEST 4: Step 5A Still Unsafe Contact Card Verification ---")
        evaluate("window.TempoEmergencySupport.closeHumanDrawer()")
        evaluate("window.TempoEmergencySupport.goToStep('still_unsafe')")
        time.sleep(0.5)

        step5a_state = evaluate("""(() => {
            const step5a = document.getElementById('emergency-step-still_unsafe');
            const card = document.getElementById('step5a-card-ngaymai');
            const title = document.getElementById('step5a-ngaymai-title') ? document.getElementById('step5a-ngaymai-title').textContent.trim() : '';
            const hours = document.getElementById('step5a-ngaymai-hours') ? document.getElementById('step5a-ngaymai-hours').textContent.trim() : '';
            const callLink = document.getElementById('step5a-ngaymai-call');

            return {
                step5aVisible: !step5a.classList.contains('hidden'),
                hasCard: !!card,
                title,
                hours,
                callHref: callLink ? callLink.getAttribute('href') : ''
            };
        })()""")

        log(f"Step 5A state: {step5a_state}")
        assert step5a_state['step5aVisible'] == True, "Step 5A should be visible"
        assert step5a_state['hasCard'] == True, "Step 5A must have Ngay Mai card"
        assert step5a_state['title'] == "ĐƯỜNG DÂY NÓNG NGÀY MAI", "Step 5A title mismatch"
        assert step5a_state['hours'] == "13:00 – 20:30, Thứ Tư – Chủ Nhật", "Step 5A hours mismatch"
        assert step5a_state['callHref'] == "tel:0963061414", "Step 5A tel href mismatch"
        log("✓ STEP 5A CONTACT CARD VERIFIED!")

        log("\n=======================================================")
        log("ALL NGÀY MAI HOTLINE TESTS PASSED (100%)!")
        log("=======================================================")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    run_tests()
