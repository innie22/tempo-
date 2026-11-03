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
PORT = 9229
USER_DATA = r"C:\Users\YEN NHI\AppData\Local\Temp\edge_test_about_page"
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
        "http://127.0.0.1:8000/#about"
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
            ready = evaluate_js(ws, "Boolean(window.TempoApp && window.TempoI18n && window.TempoI18n.updateAboutPageStaticHtml)")
            if ready:
                break
            time.sleep(0.5)

        # Navigate to About page
        evaluate_js(ws, "window.TempoApp.navigateTo('about')")
        time.sleep(0.5)

        # -------------------------------------------------------------
        # STEP 1: Verify Vietnamese Mode
        # -------------------------------------------------------------
        print("\n=== 1. Testing About Page in Vietnamese Mode (vi) ===")
        evaluate_js(ws, "window.TempoI18n.setLanguage('vi')")
        time.sleep(0.5)

        vi_texts = evaluate_js(ws, """
        (() => {
            const getT = id => {
                const el = document.getElementById(id);
                return el ? el.textContent.trim() : null;
            };
            return {
                // S01
                heroBadge: getT('about-hero-badge'),
                heroTitle: getT('about-hero-title'),
                heroDesc: getT('about-hero-desc'),
                heroCta: getT('about-hero-cta-text'),
                previewBadge: getT('about-preview-badge'),
                card1Title: getT('about-card1-title'),
                card1Badge: getT('about-card1-badge'),
                card1Desc: getT('about-card1-desc'),
                card2Title: getT('about-card2-title'),
                card2Badge: getT('about-card2-badge'),
                card2Desc: getT('about-card2-desc'),
                card3Title: getT('about-card3-title'),
                card3Badge: getT('about-card3-badge'),
                card3Desc: getT('about-card3-desc'),
                previewFooter: getT('about-preview-footer'),

                // S02
                s02Eyebrow: getT('about-s02-eyebrow'),
                s02Title: getT('about-s02-title'),
                s02Desc: getT('about-s02-desc'),
                s02C1Eyebrow: getT('about-s02-c1-eyebrow'),
                s02C1Title: getT('about-s02-c1-title'),
                s02C1Desc: getT('about-s02-c1-desc'),
                s02C1HelpEyebrow: getT('about-s02-c1-help-eyebrow'),
                s02C1HelpTitle: getT('about-s02-c1-help-title'),
                s02C1HelpDesc: getT('about-s02-c1-help-desc'),

                s02C2Eyebrow: getT('about-s02-c2-eyebrow'),
                s02C2Title: getT('about-s02-c2-title'),
                s02C2Desc: getT('about-s02-c2-desc'),
                s02C2HelpEyebrow: getT('about-s02-c2-help-eyebrow'),
                s02C2HelpTitle: getT('about-s02-c2-help-title'),
                s02C2HelpDesc: getT('about-s02-c2-help-desc'),

                s02C3Eyebrow: getT('about-s02-c3-eyebrow'),
                s02C3Title: getT('about-s02-c3-title'),
                s02C3Desc: getT('about-s02-c3-desc'),
                s02C3HelpEyebrow: getT('about-s02-c3-help-eyebrow'),
                s02C3HelpTitle: getT('about-s02-c3-help-title'),
                s02C3HelpDesc: getT('about-s02-c3-help-desc'),

                // S03
                s03Eyebrow: getT('about-s03-eyebrow'),
                s03Title: getT('about-s03-title'),
                s03Desc: getT('about-s03-desc'),

                // 3.1
                modesEyebrow: getT('about-modes-eyebrow'),
                modesTitle: getT('about-modes-title'),
                modesSubtitle: getT('about-modes-subtitle'),
                modesDesc: getT('about-modes-desc'),
                modeUrgent: getT('about-mode-urgent'),
                modeRecovery: getT('about-mode-recovery'),
                modeUnclear: getT('about-mode-unclear'),
                sosTitle: getT('about-sos-title'),
                sosFlow: getT('about-sos-flow'),
                sosNote: getT('about-sos-note'),

                // 3.2
                toolsEyebrow: getT('about-tools-eyebrow'),
                toolsTitle: getT('about-tools-title'),
                toolsSubtitle: getT('about-tools-subtitle'),
                toolsDesc: getT('about-tools-desc'),
                toolFocusZone: getT('about-tool-focus-zone'),
                toolWorkingPlan: getT('about-tool-working-plan'),
                toolSelfCheck: getT('about-tool-self-check'),
                toolBreathing: getT('about-tool-breathing'),
                toolNotes: getT('about-tool-notes'),
                hasStrack: Boolean(document.getElementById('about-tool-strack') || Array.from(document.querySelectorAll('#screen-about span')).some(s => s.textContent.trim() === 'Strack')),

                // 3.3
                reliefEyebrow: getT('about-relief-eyebrow'),
                reliefTitle: getT('about-relief-title'),
                reliefSubtitle: getT('about-relief-subtitle'),
                reliefDesc: getT('about-relief-desc'),
                reliefC1Title: getT('about-relief-c1-title'),
                reliefC1Desc: getT('about-relief-c1-desc'),
                reliefC2Title: getT('about-relief-c2-title'),
                reliefC2Desc: getT('about-relief-c2-desc'),

                // 3.4
                commEyebrow: getT('about-comm-eyebrow'),
                commTitle: getT('about-comm-title'),
                commSubtitle: getT('about-comm-subtitle'),
                commDesc: getT('about-comm-desc'),
                commC1Title: getT('about-comm-c1-title'),
                commC1Desc: getT('about-comm-c1-desc'),
                commC2Title: getT('about-comm-c2-title'),
                commC2Desc: getT('about-comm-c2-desc'),

                // S04
                s04Eyebrow: getT('about-s04-eyebrow'),
                s04Title: getT('about-s04-title'),
                s04Desc: getT('about-s04-desc'),
                step1Title: getT('about-step1-title'),
                step1Desc: getT('about-step1-desc'),
                step2Title: getT('about-step2-title'),
                step2Desc: getT('about-step2-desc'),
                step3Title: getT('about-step3-title'),
                step3Desc: getT('about-step3-desc'),

                // S05
                s05Eyebrow: getT('about-s05-eyebrow'),
                s05Title: getT('about-s05-title'),
                s05Desc: getT('about-s05-desc'),
                s05Cta: getT('about-s05-cta-text')
            };
        })()
        """)

        # Assertions for Section 1 (Hero)
        assert vi_texts["heroBadge"] == "GẶP GỠ TEMPO", f"heroBadge: {vi_texts['heroBadge']}"
        assert vi_texts["heroTitle"] == "Không gian đồng hành cùng bạn trên hành trình sinh viên.", f"heroTitle: {vi_texts['heroTitle']}"
        assert "Được thiết kế dành cho sinh viên Đại học FPT" in vi_texts["heroDesc"], f"heroDesc: {vi_texts['heroDesc']}"
        assert vi_texts["heroCta"] == "Khám phá Tempo", f"heroCta: {vi_texts['heroCta']}"
        assert vi_texts["previewBadge"] == "TEMPO · KHÔNG GIAN SỨC KHỎE TINH THẦN FPT", f"previewBadge: {vi_texts['previewBadge']}"
        assert vi_texts["card1Title"] == "Chế độ Khẩn cấp", f"card1Title: {vi_texts['card1Title']}"
        assert vi_texts["card1Badge"] == "Hỗ trợ xử lý Deadline", f"card1Badge: {vi_texts['card1Badge']}"
        assert vi_texts["card1Desc"] == "Chia nhỏ sự bế tắc thành MỘT bước khả thi.", f"card1Desc: {vi_texts['card1Desc']}"
        assert vi_texts["card2Title"] == "Self-check", f"card2Title: {vi_texts['card2Title']}"
        assert vi_texts["card2Badge"] == "6 khía cạnh", f"card2Badge: {vi_texts['card2Badge']}"
        assert vi_texts["card2Desc"] == "Tự nhìn nhận bản thân nhẹ nhàng, không áp lực hay phán xét.", f"card2Desc: {vi_texts['card2Desc']}"
        assert vi_texts["card3Title"] == "Luyện tập hít thở", f"card3Title: {vi_texts['card3Title']}"
        assert vi_texts["card3Badge"] == "2 phút thư giãn", f"card3Badge: {vi_texts['card3Badge']}"
        assert vi_texts["card3Desc"] == "Giúp cơ thể và tâm trí tạm dừng, thả lỏng.", f"card3Desc: {vi_texts['card3Desc']}"
        assert vi_texts["previewFooter"] == "Luôn bảo mật và có sự đồng hành từ cộng đồng đồng trang lứa.", f"previewFooter: {vi_texts['previewFooter']}"
        print("✓ Section 1 (Hero) verified in Vietnamese!")

        # Assertions for Section 2 (When things feel like too much)
        assert vi_texts["s02Eyebrow"] == "KHI MỌI THỨ TRỞ NÊN QUÁ SỨC", f"s02Eyebrow: {vi_texts['s02Eyebrow']}"
        assert vi_texts["s02Title"] == "Khi mọi thứ trở nên quá sức", f"s02Title: {vi_texts['s02Title']}"
        assert "Cuộc sống sinh viên đôi khi mang đến những thời điểm" in vi_texts["s02Desc"], f"s02Desc: {vi_texts['s02Desc']}"
        assert vi_texts["s02C1Eyebrow"] == "KHI MỌI THỨ DỒN DẬP", f"s02C1Eyebrow: {vi_texts['s02C1Eyebrow']}"
        assert vi_texts["s02C1Title"] == "Khi mọi thứ dồn dập, bạn không biết nên bắt đầu từ đâu?", f"s02C1Title: {vi_texts['s02C1Title']}"
        assert vi_texts["s02C1HelpEyebrow"] == "TEMPO GIÚP BẠN THẾ NÀO?", f"s02C1HelpEyebrow: {vi_texts['s02C1HelpEyebrow']}"
        assert vi_texts["s02C1HelpTitle"] == "Tìm ra điều cần ưu tiên và bước tiếp theo.", f"s02C1HelpTitle: {vi_texts['s02C1HelpTitle']}"
        assert vi_texts["s02C2Eyebrow"] == "KHI CĂNG THẲNG LẤN ÁT", f"s02C2Eyebrow: {vi_texts['s02C2Eyebrow']}"
        assert vi_texts["s02C2Title"] == "Khi căng thẳng lấn át, bạn cần chậm lại một chút?", f"s02C2Title: {vi_texts['s02C2Title']}"
        assert vi_texts["s02C2HelpTitle"] == "Lấy lại cân bằng lúc này. Xây dựng kỹ năng cho tương lai.", f"s02C2HelpTitle: {vi_texts['s02C2HelpTitle']}"
        assert vi_texts["s02C3Eyebrow"] == "KHI BẠN CHƯA BIẾT MÌNH CẦN GÌ", f"s02C3Eyebrow: {vi_texts['s02C3Eyebrow']}"
        assert vi_texts["s02C3Title"] == "Khi chưa rõ mình đang cảm thấy thế nào hoặc nên bắt đầu từ đâu?", f"s02C3Title: {vi_texts['s02C3Title']}"
        assert vi_texts["s02C3HelpTitle"] == "Hiểu bản thân trước, tìm kiếm sự hỗ trợ phù hợp sau.", f"s02C3HelpTitle: {vi_texts['s02C3HelpTitle']}"
        print("✓ Section 2 (When Things Feel Like Too Much) verified in Vietnamese!")

        # Assertions for Section 3 (Explore Tempo)
        assert vi_texts["s03Eyebrow"] == "KHÁM PHÁ TEMPO", f"s03Eyebrow: {vi_texts['s03Eyebrow']}"
        assert vi_texts["s03Title"] == "Một không gian, nhiều cách tìm lại nhịp độ của riêng bạn.", f"s03Title: {vi_texts['s03Title']}"
        assert vi_texts["modesEyebrow"] == "CÁC CHẾ ĐỘ & SOS", f"modesEyebrow: {vi_texts['modesEyebrow']}"
        assert vi_texts["modesTitle"] == "Tìm kiếm sự hỗ trợ bạn cần", f"modesTitle: {vi_texts['modesTitle']}"
        assert vi_texts["modesSubtitle"] == "Mỗi tình huống đều cần một cách hỗ trợ khác nhau.", f"modesSubtitle: {vi_texts['modesSubtitle']}"
        assert vi_texts["modeUrgent"] == "Khẩn cấp", f"modeUrgent: {vi_texts['modeUrgent']}"
        assert vi_texts["modeRecovery"] == "Hồi phục", f"modeRecovery: {vi_texts['modeRecovery']}"
        assert vi_texts["modeUnclear"] == "Chưa rõ", f"modeUnclear: {vi_texts['modeUnclear']}"
        assert vi_texts["sosTitle"] == "SOS – Hỗ trợ khẩn cấp", f"sosTitle: {vi_texts['sosTitle']}"
        assert vi_texts["sosFlow"] == "Quy trình hỗ trợ riêng", f"sosFlow: {vi_texts['sosFlow']}"

        assert vi_texts["toolsEyebrow"] == "CÔNG CỤ CÁ NHÂN", f"toolsEyebrow: {vi_texts['toolsEyebrow']}"
        assert vi_texts["toolsTitle"] == "Công cụ phù hợp với nhu cầu của bạn", f"toolsTitle: {vi_texts['toolsTitle']}"
        assert vi_texts["toolFocusZone"] == "Focus Zone", f"toolFocusZone: {vi_texts['toolFocusZone']}"
        assert vi_texts["toolWorkingPlan"] == "Working Plan", f"toolWorkingPlan: {vi_texts['toolWorkingPlan']}"
        assert vi_texts["toolSelfCheck"] == "Self-check", f"toolSelfCheck: {vi_texts['toolSelfCheck']}"
        assert vi_texts["toolBreathing"] == "Hít thở", f"toolBreathing: {vi_texts['toolBreathing']}"
        assert vi_texts["toolNotes"] == "Ghi chú", f"toolNotes: {vi_texts['toolNotes']}"
        assert vi_texts["hasStrack"] == False, "Expected Strack NOT to be displayed as a duplicate separate tool!"

        assert vi_texts["reliefEyebrow"] == "THƯ GIÃN & HỌC HỎI", f"reliefEyebrow: {vi_texts['reliefEyebrow']}"
        assert vi_texts["reliefTitle"] == "Thư giãn, học hỏi và phát triển", f"reliefTitle: {vi_texts['reliefTitle']}"
        assert vi_texts["reliefC1Title"] == "Thư giãn", f"reliefC1Title: {vi_texts['reliefC1Title']}"
        assert vi_texts["reliefC1Desc"] == "Những hoạt động thư giãn thể chất và tinh thần chỉ trong 2 phút.", f"reliefC1Desc: {vi_texts['reliefC1Desc']}"
        assert vi_texts["reliefC2Title"] == "Learn & Solve", f"reliefC2Title: {vi_texts['reliefC2Title']}"
        assert vi_texts["reliefC2Desc"] == "Những phương pháp thiết thực giúp bạn ứng phó với áp lực đại học.", f"reliefC2Desc: {vi_texts['reliefC2Desc']}"

        assert vi_texts["commEyebrow"] == "CỘNG ĐỒNG", f"commEyebrow: {vi_texts['commEyebrow']}"
        assert vi_texts["commTitle"] == "Bạn không đơn độc", f"commTitle: {vi_texts['commTitle']}"
        assert vi_texts["commC1Title"] == "Cộng đồng Tempo", f"commC1Title: {vi_texts['commC1Title']}"
        assert vi_texts["commC1Desc"] == "Những câu chuyện chân thực, suy nghĩ chân thành và sự động viên từ cộng đồng sinh viên.", f"commC1Desc: {vi_texts['commC1Desc']}"
        assert vi_texts["commC2Title"] == "Tempo Post", f"commC2Title: {vi_texts['commC2Title']}"
        assert vi_texts["commC2Desc"] == "Tự do chia sẻ ẩn danh hoặc sử dụng hồ sơ sinh viên của bạn.", f"commC2Desc: {vi_texts['commC2Desc']}"
        print("✓ Section 3 (Explore Tempo, Modes, Tools, Relief, Community) verified in Vietnamese!")

        # Assertions for Section 4 (Your journey, your pace)
        assert vi_texts["s04Eyebrow"] == "HÀNH TRÌNH CỦA BẠN, NHỊP ĐIỆU CỦA RIÊNG BẠN", f"s04Eyebrow: {vi_texts['s04Eyebrow']}"
        assert vi_texts["s04Title"] == "Sử dụng Tempo theo cách của bạn", f"s04Title: {vi_texts['s04Title']}"
        assert vi_texts["step1Title"] == "01 — Bắt đầu từ chính bạn", f"step1Title: {vi_texts['step1Title']}"
        assert vi_texts["step2Title"] == "02 — Tìm ra điều phù hợp với bạn", f"step2Title: {vi_texts['step2Title']}"
        assert vi_texts["step3Title"] == "03 — Tiến bước theo nhịp độ riêng", f"step3Title: {vi_texts['step3Title']}"
        print("✓ Section 4 (Your Journey, Your Pace) verified in Vietnamese!")

        # Assertions for Section 5 (Final CTA)
        assert vi_texts["s05Eyebrow"] == "TEMPO · CHƯƠNG TIẾP THEO CỦA BẠN", f"s05Eyebrow: {vi_texts['s05Eyebrow']}"
        assert vi_texts["s05Title"] == "Sẵn sàng tìm lại nhịp điệu của riêng mình?", f"s05Title: {vi_texts['s05Title']}"
        assert vi_texts["s05Cta"] == "Bắt đầu ngay", f"s05Cta: {vi_texts['s05Cta']}"
        print("✓ Section 5 (Final CTA) verified in Vietnamese!")

        # Capture screenshots for Vietnamese mode
        capture_screenshot(ws, None, os.path.join(ARTIFACT_DIR, "about_page_vi_hero.png"))
        evaluate_js(ws, "document.getElementById('about-section-03').scrollIntoView()")
        time.sleep(0.3)
        capture_screenshot(ws, None, os.path.join(ARTIFACT_DIR, "about_page_vi_stacked.png"))

        # -------------------------------------------------------------
        # STEP 2: Verify English Mode
        # -------------------------------------------------------------
        print("\n=== 2. Testing About Page in English Mode (en) ===")
        evaluate_js(ws, "window.TempoI18n.setLanguage('en')")
        time.sleep(0.5)

        en_texts = evaluate_js(ws, """
        (() => {
            const getT = id => {
                const el = document.getElementById(id);
                return el ? el.textContent.trim() : null;
            };
            return {
                heroBadge: getT('about-hero-badge'),
                heroTitle: getT('about-hero-title'),
                heroCta: getT('about-hero-cta-text'),
                card1Title: getT('about-card1-title'),
                card1Badge: getT('about-card1-badge'),
                card3Title: getT('about-card3-title'),
                card3Badge: getT('about-card3-badge'),
                s02Eyebrow: getT('about-s02-eyebrow'),
                s02Title: getT('about-s02-title'),
                s02C1Title: getT('about-s02-c1-title'),
                modesTitle: getT('about-modes-title'),
                modeUrgent: getT('about-mode-urgent'),
                modeRecovery: getT('about-mode-recovery'),
                modeUnclear: getT('about-mode-unclear'),
                toolBreathing: getT('about-tool-breathing'),
                toolNotes: getT('about-tool-notes'),
                reliefC1Title: getT('about-relief-c1-title'),
                commC1Title: getT('about-comm-c1-title'),
                step1Title: getT('about-step1-title'),
                s05Title: getT('about-s05-title'),
                s05Cta: getT('about-s05-cta-text')
            };
        })()
        """)

        assert en_texts["heroBadge"] == "MEET TEMPO", f"heroBadge (EN): {en_texts['heroBadge']}"
        assert en_texts["heroTitle"] == "Your space to navigate student life.", f"heroTitle (EN): {en_texts['heroTitle']}"
        assert en_texts["heroCta"] == "Explore Tempo", f"heroCta (EN): {en_texts['heroCta']}"
        assert en_texts["card1Title"] == "Urgent Mode", f"card1Title (EN): {en_texts['card1Title']}"
        assert en_texts["card1Badge"] == "Deadline triage", f"card1Badge (EN): {en_texts['card1Badge']}"
        assert en_texts["card3Title"] == "Breathing Practice", f"card3Title (EN): {en_texts['card3Title']}"
        assert en_texts["card3Badge"] == "2-minute reset", f"card3Badge (EN): {en_texts['card3Badge']}"
        assert en_texts["s02Eyebrow"] == "WHEN THINGS FEEL LIKE TOO MUCH", f"s02Eyebrow (EN): {en_texts['s02Eyebrow']}"
        assert en_texts["s02Title"] == "When things feel like too much", f"s02Title (EN): {en_texts['s02Title']}"
        assert en_texts["s02C1Title"] == "Not sure where to start when everything piles up?", f"s02C1Title (EN): {en_texts['s02C1Title']}"
        assert en_texts["modesTitle"] == "Find the support you need.", f"modesTitle (EN): {en_texts['modesTitle']}"
        assert en_texts["modeUrgent"] == "Urgent", f"modeUrgent (EN): {en_texts['modeUrgent']}"
        assert en_texts["modeRecovery"] == "Recovery", f"modeRecovery (EN): {en_texts['modeRecovery']}"
        assert en_texts["modeUnclear"] == "Unclear", f"modeUnclear (EN): {en_texts['modeUnclear']}"
        assert en_texts["toolBreathing"] == "Breathing", f"toolBreathing (EN): {en_texts['toolBreathing']}"
        assert en_texts["toolNotes"] == "Notes", f"toolNotes (EN): {en_texts['toolNotes']}"
        assert en_texts["reliefC1Title"] == "Quick Relief", f"reliefC1Title (EN): {en_texts['reliefC1Title']}"
        assert en_texts["commC1Title"] == "Tempo Community", f"commC1Title (EN): {en_texts['commC1Title']}"
        assert en_texts["step1Title"] == "01 — Start with yourself", f"step1Title (EN): {en_texts['step1Title']}"
        assert en_texts["s05Title"] == "Ready to find your own rhythm again?", f"s05Title (EN): {en_texts['s05Title']}"
        assert en_texts["s05Cta"] == "Get Started", f"s05Cta (EN): {en_texts['s05Cta']}"
        print("✓ English mode verified across all sections!")

        evaluate_js(ws, "window.scrollTo(0, 0)")
        time.sleep(0.3)
        capture_screenshot(ws, None, os.path.join(ARTIFACT_DIR, "about_page_en_hero.png"))

        # Test CTA functionality
        cta_test = evaluate_js(ws, """
        (() => {
            let navigated = false;
            const origNav = window.TempoApp.navigateTo;
            window.TempoApp.navigateTo = tab => { if (tab === 'today') navigated = true; };
            document.getElementById('btn-about-get-started').click();
            window.TempoApp.navigateTo = origNav;
            return { navigated };
        })()
        """)
        assert cta_test["navigated"] == True, "Expected Get Started CTA to navigate to today"
        print("✓ Get Started CTA functionality preserved!")

        print("\n" + "="*55)
        print("ALL ABOUT PAGE LOCALIZATION VERIFICATION CHECKS PASSED!")
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
