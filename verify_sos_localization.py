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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_sos_loc_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9288

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
            "height": 900,
            "deviceScaleFactor": 1,
            "mobile": False
        })
        time.sleep(0.5)

        # ---------------------------------------------------------------------
        # TEST 1: Default Vietnamese Localization Verification
        # ---------------------------------------------------------------------
        log("\n--- TEST 1: Exact Vietnamese Copy in SOS Popup ---")
        curr_lang = evaluate("window.TempoI18n.getLanguage()")
        log(f"Current language: {curr_lang}")
        assert curr_lang == 'vi', "Initial language must be 'vi'"

        # Open SOS modal
        evaluate("window.TempoEmergencySupport.openSOS()")
        time.sleep(0.5)

        vi_texts = evaluate("""(() => {
            return {
                headerTitle: document.getElementById('sos-header-title').textContent.trim(),
                headerSubtitle: document.getElementById('sos-header-subtitle').textContent.trim(),
                pillSupport: document.getElementById('sos-pill-get-support').textContent.trim(),
                safetyBannerHeading: document.getElementById('sos-safety-mode-active-heading').textContent.trim(),
                safetyBannerDesc: document.getElementById('sos-safety-mode-active-desc').textContent.trim(),
                eyebrow: document.getElementById('sos-eyebrow').textContent.trim(),
                mainHeading: document.getElementById('sos-main-heading').textContent.trim(),
                situationIntro: document.getElementById('sos-card-situation-intro').textContent.trim(),
                sit1: document.getElementById('sos-situation-1').textContent.trim(),
                sit2: document.getElementById('sos-situation-2').textContent.trim(),
                sit3: document.getElementById('sos-situation-3').textContent.trim(),
                reassTitle: document.getElementById('sos-reassurance-title').textContent.trim(),
                reassBody: document.getElementById('sos-reassurance-body').textContent.trim(),
                primaryCta: document.getElementById('sos-cta-label').textContent.trim(),
                altHeading: document.getElementById('sos-alt-options-heading').textContent.trim(),
                optATitle: document.getElementById('sos-option-a-title').textContent.trim(),
                optADesc: document.getElementById('sos-option-a-desc').textContent.trim(),
                optBTitle: document.getElementById('sos-option-b-title').textContent.trim(),
                optBDesc: document.getElementById('sos-option-b-desc').textContent.trim(),
                optCTitle: document.getElementById('sos-option-c-title').textContent.trim(),
                optCDesc: document.getElementById('sos-option-c-desc').textContent.trim(),
                optDLabel: document.getElementById('sos-option-d-label').textContent.trim(),
            };
        })()""")

        for k, v in vi_texts.items():
            log(f"  {k}: {repr(v)}")

        # Exact copy assertions
        assert vi_texts['headerTitle'] == "SOS · Hỗ trợ khẩn cấp", "Header title mismatch"
        assert vi_texts['headerSubtitle'] == "An toàn của bạn là ưu tiên hàng đầu", "Header subtitle mismatch"
        assert vi_texts['pillSupport'] == "Nhận hỗ trợ ngay →", "Header support pill mismatch"
        assert vi_texts['safetyBannerHeading'] == "Chế độ an toàn đang bật", "Safety banner heading mismatch"
        assert vi_texts['safetyBannerDesc'] == "Bạn không cần phải trải qua điều này một mình. Hãy để chúng tôi giúp bạn.", "Safety banner desc mismatch"
        assert vi_texts['eyebrow'] == "SOS · Hỗ trợ khẩn cấp", "Eyebrow mismatch"
        assert vi_texts['mainHeading'] == "Tôi không cảm thấy an toàn lúc này", "Main heading mismatch"
        assert vi_texts['situationIntro'] == "Nếu ngay lúc này bạn đang:", "Situation intro mismatch"
        assert vi_texts['sit1'] == "Hoảng loạn và cảm thấy mất kiểm soát", "Situation 1 mismatch"
        assert vi_texts['sit2'] == "Có suy nghĩ hoặc thôi thúc làm tổn thương bản thân", "Situation 2 mismatch"
        assert vi_texts['sit3'] == "Cảm thấy không an toàn khi ở một mình", "Situation 3 mismatch"
        assert vi_texts['reassTitle'] == "An toàn của bạn là ưu tiên hàng đầu.", "Reassurance title mismatch"
        assert vi_texts['reassBody'] == "Bạn không cần phải tự mình vượt qua tất cả.", "Reassurance body mismatch"
        assert vi_texts['primaryCta'] == "Nhận hỗ trợ ngay →", "Primary CTA mismatch"
        assert vi_texts['altHeading'] == "Hoặc chọn điều bạn cần lúc này", "Alternative options heading mismatch"
        assert vi_texts['optATitle'] == "Lựa chọn A · Quá tải hoặc hoảng loạn", "Option A title mismatch"
        assert vi_texts['optADesc'] == "Tôi cảm thấy căng thẳng, quá tải hoặc không thể suy nghĩ rõ ràng.", "Option A desc mismatch"
        assert vi_texts['optBTitle'] == "Lựa chọn B · Khủng hoảng cảm xúc", "Option B title mismatch"
        assert vi_texts['optBDesc'] == "Tôi đang trải qua trạng thái cảm xúc rất tiêu cực và cần được hỗ trợ ngay.", "Option B desc mismatch"
        assert vi_texts['optCTitle'] == "Lựa chọn C · Cần hỗ trợ khẩn cấp", "Option C title mismatch"
        assert vi_texts['optCDesc'] == "Tôi đang nghĩ đến việc làm tổn thương bản thân hoặc tự tử.", "Option C desc mismatch"
        assert vi_texts['optDLabel'] == "Tôi không chắc — đầu óc tôi đang rối bời và tôi chỉ muốn được giúp bình tĩnh lại.", "Option D label mismatch"

        log("✓ ALL EXACT VIETNAMESE STRINGS VERIFIED!")
        capture_screenshot("sos_vietnamese_exact.png")

        # ---------------------------------------------------------------------
        # TEST 2: Copy Confirmation Notification in Vietnamese
        # ---------------------------------------------------------------------
        log("\n--- TEST 2: Copy Confirmation Notification Verification ---")
        evaluate("window.TempoEmergencySupport.copyTrustedMessage()")
        toast_vi = evaluate("""(() => {
            const toast = document.getElementById('app-toast');
            return toast ? toast.innerText.trim() : '';
        })()""")
        log(f"Toast message: {repr(toast_vi)}")
        assert toast_vi == "Đã sao chép tin nhắn! Bạn có thể dán và gửi cho bạn bè hoặc người thân.", "Toast message mismatch"
        log("✓ EXACT COPY CONFIRMATION NOTIFICATION VERIFIED!")

        # ---------------------------------------------------------------------
        # TEST 3: Switch to English and Verify English Preservation
        # ---------------------------------------------------------------------
        log("\n--- TEST 3: English Copy Preservation ---")
        evaluate("window.TempoI18n.setLanguage('en')")
        time.sleep(0.5)

        en_texts = evaluate("""(() => {
            return {
                headerTitle: document.getElementById('sos-header-title').textContent.trim(),
                headerSubtitle: document.getElementById('sos-header-subtitle').textContent.trim(),
                pillSupport: document.getElementById('sos-pill-get-support').textContent.trim(),
                safetyBannerHeading: document.getElementById('sos-safety-mode-active-heading').textContent.trim(),
                safetyBannerDesc: document.getElementById('sos-safety-mode-active-desc').textContent.trim(),
                eyebrow: document.getElementById('sos-eyebrow').textContent.trim(),
                mainHeading: document.getElementById('sos-main-heading').textContent.trim(),
                situationIntro: document.getElementById('sos-card-situation-intro').textContent.trim(),
                sit1: document.getElementById('sos-situation-1').textContent.trim(),
                sit2: document.getElementById('sos-situation-2').textContent.trim(),
                sit3: document.getElementById('sos-situation-3').textContent.trim(),
                reassTitle: document.getElementById('sos-reassurance-title').textContent.trim(),
                reassBody: document.getElementById('sos-reassurance-body').textContent.trim(),
                primaryCta: document.getElementById('sos-cta-label').textContent.trim(),
                altHeading: document.getElementById('sos-alt-options-heading').textContent.trim(),
                optABadge: document.getElementById('sos-option-a-badge').textContent.trim(),
                optATitle: document.getElementById('sos-option-a-title').textContent.trim(),
                optADesc: document.getElementById('sos-option-a-desc').textContent.trim(),
                optBBadge: document.getElementById('sos-option-b-badge').textContent.trim(),
                optBTitle: document.getElementById('sos-option-b-title').textContent.trim(),
                optBDesc: document.getElementById('sos-option-b-desc').textContent.trim(),
                optCBadge: document.getElementById('sos-option-c-badge').textContent.trim(),
                optCTitle: document.getElementById('sos-option-c-title').textContent.trim(),
                optCDesc: document.getElementById('sos-option-c-desc').textContent.trim(),
                optDLabel: document.getElementById('sos-option-d-label').textContent.trim(),
            };
        })()""")

        for k, v in en_texts.items():
            log(f"  {k}: {repr(v)}")

        assert en_texts['headerTitle'] == "SOS · Immediate Support", "EN header title mismatch"
        assert en_texts['headerSubtitle'] == "Your safety comes first", "EN header subtitle mismatch"
        assert en_texts['pillSupport'] == "Get support now →", "EN pill support mismatch"
        assert "Safety Mode Active" in en_texts['safetyBannerHeading'], "EN banner heading mismatch"
        assert "You don't need to finish" in en_texts['safetyBannerDesc'], "EN banner desc mismatch"
        assert en_texts['mainHeading'] == "I don't feel safe right now", "EN main heading mismatch"
        assert en_texts['situationIntro'] == "If right now you're:", "EN intro mismatch"
        assert en_texts['sit1'] == "panicking and feel out of control", "EN sit 1 mismatch"
        assert en_texts['sit2'] == "having thoughts or urges to hurt yourself", "EN sit 2 mismatch"
        assert en_texts['sit3'] == "not feeling safe being alone", "EN sit 3 mismatch"
        assert en_texts['reassTitle'] == "Your safety comes first.", "EN reass title mismatch"
        assert en_texts['reassBody'] == "You don't need to handle everything by yourself right now.", "EN reass body mismatch"
        assert en_texts['primaryCta'] == "Get support now →", "EN primary CTA mismatch"
        assert en_texts['altHeading'] == "Or choose what you need right now", "EN alt heading mismatch"
        assert en_texts['optABadge'] == "Option A", "EN opt A badge mismatch"
        assert en_texts['optATitle'] == "I'm overwhelmed or panicking", "EN opt A title mismatch"
        assert en_texts['optADesc'] == "I feel stressed, overwhelmed, or unable to think clearly.", "EN opt A desc mismatch"
        assert en_texts['optDLabel'] == "I'm not sure — my mind is racing and I just need help slowing down", "EN opt D mismatch"

        log("✓ ALL ENGLISH STRINGS PRESERVED VERBATIM!")
        capture_screenshot("sos_english_preserved.png")

        # ---------------------------------------------------------------------
        # TEST 4: Switch Back to Vietnamese and Re-Verify
        # ---------------------------------------------------------------------
        log("\n--- TEST 4: Reactive Restoration back to Vietnamese ---")
        evaluate("window.TempoI18n.setLanguage('vi')")
        time.sleep(0.5)

        restored_title = evaluate("document.getElementById('sos-option-a-title').textContent.trim()")
        assert restored_title == "Lựa chọn A · Quá tải hoặc hoảng loạn", "Option A restoration failed"
        restored_badge_disp = evaluate("document.getElementById('sos-option-a-badge').style.display")
        assert restored_badge_disp == "none", "Option A badge should be hidden in vi"

        evaluate("window.TempoEmergencySupport.copyTrustedMessage()")
        toast_vi2 = evaluate("""(() => {
            const toast = document.getElementById('app-toast');
            return toast ? toast.innerText.trim() : '';
        })()""")
        assert toast_vi2 == "Đã sao chép tin nhắn! Bạn có thể dán và gửi cho bạn bè hoặc người thân.", "Toast restoration mismatch"

        log("✓ REACTIVE VIETNAMESE RESTORATION SUCCEEDED!")

        log("\n=======================================================")
        log("ALL SOS LOCALIZATION VERIFICATION CHECKS PASSED (100%)!")
        log("=======================================================")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    run_tests()
