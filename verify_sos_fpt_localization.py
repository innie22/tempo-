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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_fpt_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9295

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
        # TEST 1: Open Human Support Drawer and Verify Vietnamese Localization
        # ---------------------------------------------------------------------
        log("\n--- TEST 1: Verify Vietnamese Localization in Support Drawer ---")
        evaluate("window.TempoEmergencySupport.openSOS()")
        evaluate("window.TempoEmergencySupport.openHumanDrawer()")
        time.sleep(0.5)

        vi_state = evaluate("""(() => {
            return {
                waitHeader: document.getElementById('drawer-waiting-header').textContent.trim(),
                waitAction1: document.getElementById('drawer-waiting-action-1').textContent.trim(),
                waitAction2: document.getElementById('drawer-waiting-action-2').textContent.trim(),
                waitAction3: document.getElementById('drawer-waiting-action-3').textContent.trim(),
                waitReassTitle: document.getElementById('drawer-waiting-reass-title').textContent.trim(),
                waitReassurance: document.getElementById('drawer-waiting-reassurance').textContent.trim(),

                trustedTitle: document.getElementById('drawer-trusted-title').textContent.trim(),
                trustedDesc: document.getElementById('drawer-trusted-desc').textContent.trim(),
                trustedQuote: document.getElementById('drawer-trusted-quote').textContent.trim(),
                copyBtnText: document.getElementById('drawer-copy-btn-text').textContent.trim(),

                campusTitle: document.getElementById('drawer-campus-title').textContent.trim(),
                campusBadge: document.getElementById('drawer-campus-badge').textContent.trim(),
                campusDesc: document.getElementById('drawer-campus-desc').textContent.trim(),

                fptTitle: document.getElementById('drawer-fpt-title').textContent.trim(),
                fptDesc: document.getElementById('drawer-fpt-desc').textContent.trim(),
                fptCtaText: document.getElementById('drawer-fpt-cta-text').textContent.trim(),
                fptCtaHref: document.getElementById('drawer-fpt-cta').getAttribute('href'),

                offlineContactPlaceholder: document.getElementById('drawer-offline-contact').getAttribute('placeholder'),
                offlineMsgPlaceholder: document.getElementById('drawer-offline-message').getAttribute('placeholder'),
                offlineBtnText: document.getElementById('drawer-offline-btn-text').textContent.trim(),
                offlineSuccess: document.getElementById('drawer-offline-success').textContent.trim(),
                closeBtnText: document.getElementById('drawer-close-btn-text').textContent.trim(),
            };
        })()""")

        for k, v in vi_state.items():
            log(f"  {k}: {repr(v)}")

        # 1. Safety Instructions Card
        assert vi_state['waitHeader'] == "KHI BẠN ĐANG CHỜ ĐƯỢC HỖ TRỢ", "waitHeader mismatch"
        assert vi_state['waitAction1'] == "Ở cùng một người bạn tin tưởng.", "waitAction1 mismatch"
        assert vi_state['waitAction2'] == "Di chuyển đến một nơi an toàn hơn.", "waitAction2 mismatch"
        assert vi_state['waitAction3'] == "Tạo khoảng cách với những vật có thể gây tổn thương cho bạn.", "waitAction3 mismatch"
        assert vi_state['waitReassTitle'] == "Bạn không cần giải quyết mọi thứ ngay lúc này.", "waitReassTitle mismatch"
        assert vi_state['waitReassurance'] == "Lúc này, chỉ cần tập trung giữ an toàn cho bản thân.", "waitReassurance mismatch"
        assert vi_state['waitReassTitle'] != vi_state['waitReassurance'], "Reassurance text must not repeat twice"

        # 2. Reach Out to Someone You Trust Card
        assert vi_state['trustedTitle'] == "Liên hệ với người bạn tin tưởng", "trustedTitle mismatch"
        assert vi_state['trustedDesc'] == "Bạn có thể sao chép tin nhắn này để gửi cho bạn bè hoặc người thân:", "trustedDesc mismatch"
        assert vi_state['trustedQuote'] == '"Chào bạn, mình đang trải qua một khoảng thời gian rất khó khăn và cảm thấy quá tải. Bạn có thể trò chuyện hoặc ngồi cùng mình một lúc được không?"', "trustedQuote mismatch"
        assert vi_state['copyBtnText'] == "Sao chép tin nhắn", "copyBtnText mismatch"

        # Test copy action
        evaluate("window.TempoEmergencySupport.copyTrustedMessage()")
        toast_vi = evaluate("document.getElementById('app-toast') ? document.getElementById('app-toast').innerText.trim() : ''")
        log(f"Copy toast: {repr(toast_vi)}")
        assert toast_vi == "Đã sao chép tin nhắn! Bạn có thể dán và gửi cho bạn bè hoặc người thân.", "Copy toast mismatch"

        # 3. Campus Student Wellbeing Card
        assert vi_state['campusTitle'] == "HỖ TRỢ SỨC KHỎE TINH THẦN SINH VIÊN", "campusTitle mismatch"
        assert vi_state['campusBadge'] == "Hỗ trợ trong giờ làm việc", "campusBadge mismatch"
        assert "Trong trường hợp khẩn cấp hoặc nguy hiểm tức thời, hãy gọi 115 hoặc 0865 044 400" in vi_state['campusDesc'], "campusDesc mismatch"

        # 4. FPT University Counseling Office
        assert vi_state['fptTitle'] == "Phòng Tư vấn tâm lý – Đại học FPT", "fptTitle mismatch"
        assert vi_state['fptDesc'] == "Dịch vụ tư vấn tâm lý miễn phí và bảo mật dành cho sinh viên Đại học FPT.", "fptDesc mismatch"
        assert vi_state['fptCtaText'] == "Gửi email tư vấn", "fptCtaText mismatch"
        assert vi_state['fptCtaHref'] == "mailto:tuvansinhvien@fpt.edu.vn", "fptCtaHref mismatch"

        # 5. Form Fields
        assert vi_state['offlineContactPlaceholder'] == "Họ tên hoặc email sinh viên (không bắt buộc)", "contact placeholder mismatch"
        assert vi_state['offlineMsgPlaceholder'] == "Mô tả vấn đề hoặc nội dung bạn muốn gửi đến phòng tư vấn", "msg placeholder mismatch"
        assert vi_state['offlineBtnText'] == "Gửi tin nhắn cho bộ phận hỗ trợ", "btn text mismatch"
        assert "Tin nhắn đã được lưu. Bộ phận hỗ trợ sẽ phản hồi trong giờ làm việc." in vi_state['offlineSuccess'], "success text mismatch"
        assert vi_state['closeBtnText'] == "Đóng cửa sổ hỗ trợ", "closeBtnText mismatch"

        log("✓ ALL VIETNAMESE LOCALIZATIONS VERIFIED!")
        capture_screenshot("sos_drawer_vi_complete.png")

        # ---------------------------------------------------------------------
        # TEST 2: Switch to English and Verify English Localization
        # ---------------------------------------------------------------------
        log("\n--- TEST 2: Verify English Localization on Switch ---")
        evaluate("window.TempoI18n.setLanguage('en')")
        time.sleep(0.5)

        en_state = evaluate("""(() => {
            return {
                waitHeader: document.getElementById('drawer-waiting-header').textContent.trim(),
                waitAction1: document.getElementById('drawer-waiting-action-1').textContent.trim(),
                waitAction2: document.getElementById('drawer-waiting-action-2').textContent.trim(),
                waitAction3: document.getElementById('drawer-waiting-action-3').textContent.trim(),
                waitReassTitle: document.getElementById('drawer-waiting-reass-title').textContent.trim(),
                waitReassurance: document.getElementById('drawer-waiting-reassurance').textContent.trim(),

                trustedTitle: document.getElementById('drawer-trusted-title').textContent.trim(),
                trustedDesc: document.getElementById('drawer-trusted-desc').textContent.trim(),
                trustedQuote: document.getElementById('drawer-trusted-quote').textContent.trim(),
                copyBtnText: document.getElementById('drawer-copy-btn-text').textContent.trim(),

                campusTitle: document.getElementById('drawer-campus-title').textContent.trim(),
                campusBadge: document.getElementById('drawer-campus-badge').textContent.trim(),
                campusDesc: document.getElementById('drawer-campus-desc').textContent.trim(),

                fptTitle: document.getElementById('drawer-fpt-title').textContent.trim(),
                fptDesc: document.getElementById('drawer-fpt-desc').textContent.trim(),
                fptCtaText: document.getElementById('drawer-fpt-cta-text').textContent.trim(),
                fptCtaHref: document.getElementById('drawer-fpt-cta').getAttribute('href'),

                offlineContactPlaceholder: document.getElementById('drawer-offline-contact').getAttribute('placeholder'),
                offlineMsgPlaceholder: document.getElementById('drawer-offline-message').getAttribute('placeholder'),
                offlineBtnText: document.getElementById('drawer-offline-btn-text').textContent.trim(),
                offlineSuccess: document.getElementById('drawer-offline-success').textContent.trim(),
                closeBtnText: document.getElementById('drawer-close-btn-text').textContent.trim(),
            };
        })()""")

        for k, v in en_state.items():
            log(f"  {k}: {repr(v)}")

        assert en_state['waitHeader'] == "While you're waiting for support", "EN waitHeader mismatch"
        assert en_state['waitAction1'] == "Stay with someone you trust.", "EN waitAction1 mismatch"
        assert en_state['waitAction2'] == "Move somewhere safer.", "EN waitAction2 mismatch"
        assert en_state['waitAction3'] == "Create distance from anything that could hurt you.", "EN waitAction3 mismatch"
        assert en_state['waitReassTitle'] == "You don't need to solve everything right now.", "EN waitReassTitle mismatch"
        assert en_state['waitReassurance'] == "For now, just focus on staying safe.", "EN waitReassurance mismatch"

        assert en_state['trustedTitle'] == "Reach Out to Someone You Trust:", "EN trustedTitle mismatch"
        assert en_state['trustedDesc'] == "Copy this simple message to reach out to a friend or family member:", "EN trustedDesc mismatch"
        assert "Hey, I'm having a really difficult time" in en_state['trustedQuote'], "EN trustedQuote mismatch"
        assert en_state['copyBtnText'] == "Copy Message", "EN copyBtnText mismatch"

        assert en_state['campusTitle'] == "Campus Student Wellbeing", "EN campusTitle mismatch"
        assert en_state['campusBadge'] == "Office Hours Support", "EN campusBadge mismatch"
        assert "For immediate crisis or danger" in en_state['campusDesc'], "EN campusDesc mismatch"

        assert en_state['fptTitle'] == "FPT University Psychological Counseling Office", "EN fptTitle mismatch"
        assert en_state['fptCtaText'] == "Send counseling email", "EN fptCtaText mismatch"
        assert en_state['fptCtaHref'] == "mailto:tuvansinhvien@fpt.edu.vn", "EN fptCtaHref mismatch"

        assert en_state['offlineContactPlaceholder'] == "Your name or student email (optional)", "EN contact placeholder mismatch"
        assert en_state['offlineBtnText'] == "Leave Message for Campus Staff", "EN btn text mismatch"
        assert en_state['closeBtnText'] == "Close Support Drawer", "EN closeBtnText mismatch"

        log("✓ ALL ENGLISH LOCALIZATIONS VERIFIED!")
        capture_screenshot("sos_drawer_en_complete.png")

        # ---------------------------------------------------------------------
        # TEST 3: Switch back to Vietnamese and verify restoration
        # ---------------------------------------------------------------------
        log("\n--- TEST 3: Switch back to Vietnamese ---")
        evaluate("window.TempoI18n.setLanguage('vi')")
        time.sleep(0.5)

        restored_fpt = evaluate("document.getElementById('drawer-fpt-title').textContent.trim()")
        assert restored_fpt == "Phòng Tư vấn tâm lý – Đại học FPT", "FPT Title restoration failed"
        restored_campus = evaluate("document.getElementById('drawer-campus-title').textContent.trim()")
        assert restored_campus == "HỖ TRỢ SỨC KHỎE TINH THẦN SINH VIÊN", "Campus Title restoration failed"

        log("✓ REACTIVE RESTORATION TO VIETNAMESE VERIFIED!")

        # ---------------------------------------------------------------------
        # TEST 4: Offline Form Submission Test (preserving functionality)
        # ---------------------------------------------------------------------
        log("\n--- TEST 4: Offline Form Submission Test ---")
        evaluate("""(() => {
            document.getElementById('drawer-offline-contact').value = "Nguyen Van A";
            document.getElementById('drawer-offline-message').value = "Em muon dat lich hen tu van tam ly.";
            window.TempoEmergencySupport.submitOfflineMessage('drawer');
        })()""")

        submit_state = evaluate("""(() => {
            const successEl = document.getElementById('drawer-offline-success');
            const toast = document.getElementById('app-toast');
            return {
                successVisible: !successEl.classList.contains('hidden'),
                toastText: toast ? toast.innerText.trim() : ''
            };
        })()""")

        log(f"Submit state: {submit_state}")
        assert submit_state['successVisible'] == True, "Success element must be visible"
        assert "Đã ghi nhận tin nhắn" in submit_state['toastText'], "Toast must acknowledge submission in Vietnamese"

        log("✓ FORM SUBMISSION FUNCTIONALITY PRESERVED!")

        log("\n=======================================================")
        log("ALL SOS COMPLETE LOCALIZATION & FPT CONTACT TESTS PASSED!")
        log("=======================================================")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    run_tests()
