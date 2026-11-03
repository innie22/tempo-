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
PORT = 9230
USER_DATA = r"C:\Users\YEN NHI\AppData\Local\Temp\edge_test_reality_check"
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
        "http://127.0.0.1:8000/#emergency"
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
            ready = evaluate_js(ws, "Boolean(window.TempoEmergencyFlow && window.TempoEmergencyFlow.goToStage)")
            if ready:
                break
            time.sleep(0.5)

        print("\n=== STEP 1: NAVIGATE TO REALITY CHECK IN VIETNAMESE (DEFAULT) ===")
        setup_res = evaluate_js(ws, """
        (() => {
            localStorage.clear();
            sessionStorage.clear();
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.resetFlowState === 'function') {
                window.TempoEmergencyFlow.resetFlowState();
            }
            // Set language to Vietnamese
            localStorage.setItem('tempo_language', 'vi');
            localStorage.setItem('tempo_lang', 'vi');
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('vi');
            }

            // Navigate to emergency screen & reality-check stage
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('emergency');
            }
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.goToStage === 'function') {
                window.TempoEmergencyFlow.goToStage('reality-check');
            }

            return { ready: true };
        })()
        """)
        print("Setup result:", setup_res)
        time.sleep(1.5)

        # Scrape Reality Check elements in Vietnamese
        vi_data = evaluate_js(ws, """
        (() => {
            const bodyBg = window.getComputedStyle(document.body).backgroundColor;
            const container = document.getElementById('emergency-stage-reality-check');
            const card = container ? container.querySelector('.bg-white') : null;
            const cardBg = card ? window.getComputedStyle(card).backgroundColor : null;

            // Flow Shell Header
            const backHome = document.getElementById('em-header-back-home')?.textContent.trim();
            const sosLabel = document.getElementById('em-header-sos-label')?.textContent.trim();
            const phaseReset = document.getElementById('em-phase-reset')?.textContent.trim();
            const phaseOrganize = document.getElementById('em-phase-organize')?.textContent.trim();
            const phasePlan = document.getElementById('em-phase-plan')?.textContent.trim();
            const phaseReady = document.getElementById('em-phase-ready')?.textContent.trim();

            // Content
            const badge = container?.querySelector('span.text-xs.font-extrabold')?.textContent.trim();
            const title = container?.querySelector('h2')?.textContent.trim();
            const subtitle = container?.querySelector('h3')?.textContent.trim();
            const desc = container?.querySelector('p.text-xs, p.text-sm')?.textContent.trim();

            // Form
            const inputLabel = container?.querySelector('label[for="rc-task-name"]')?.textContent.trim();
            const inputPlaceholder = document.getElementById('rc-task-name')?.getAttribute('placeholder');
            const deadlineLabel = container?.querySelectorAll('label.block')[1]?.textContent.trim();
            const noDeadlineText = document.getElementById('rc-no-deadline-cb')?.parentElement?.textContent.trim();
            const addBtn = container?.querySelector('button[onclick*="addRealityCheckTask"]')?.textContent.trim();
            const loadSamplesBtn = container?.querySelector('button[onclick*="loadSampleTasks"]')?.textContent.trim();

            // Tasks list
            const taskCountHeader = container?.querySelector('h4')?.textContent.trim();
            const emptyState = document.getElementById('rc-tasks-list')?.textContent.trim();

            // Bottom CTA
            const backBtn = container?.querySelector('button[onclick*="goToStage"]')?.textContent.trim();
            const continueBtn = document.getElementById('btn-rc-continue')?.textContent.trim();

            return {
                bodyBg,
                cardBg,
                backHome,
                sosLabel,
                phaseReset,
                phaseOrganize,
                phasePlan,
                phaseReady,
                badge,
                title,
                subtitle,
                desc,
                inputLabel,
                inputPlaceholder,
                deadlineLabel,
                noDeadlineText,
                addBtn,
                loadSamplesBtn,
                taskCountHeader,
                emptyState,
                backBtn,
                continueBtn
            };
        })()
        """)
        print("\n[VIETNAMESE REALITY CHECK DATA]:")
        print(json.dumps(vi_data, ensure_ascii=False, indent=2))

        # Check background color in VI
        print("\nChecking Background Color in VI:")
        print(f"  Body background: {vi_data['bodyBg']}")
        print(f"  Card background: {vi_data['cardBg']}")
        # rgb(237, 244, 239) is #EDF4EF (light Sage Green)
        assert "237, 244, 239" in vi_data['bodyBg'] or "edf4ef" in vi_data['bodyBg'].lower(), \
            f"Expected light Sage Green (#EDF4EF), got: {vi_data['bodyBg']}"
        print("✓ Verified soft, light Sage Green (#EDF4EF) background active on Reality Check!")

        # Verify exact Vietnamese mappings from user request table
        assert vi_data['backHome'] == "Về trang chủ", f"Expected 'Về trang chủ', got: {vi_data['backHome']}"
        assert vi_data['sosLabel'] == "Hỗ trợ SOS", f"Expected 'Hỗ trợ SOS', got: {vi_data['sosLabel']}"
        assert vi_data['phaseReset'] == "Thư giãn" or vi_data['phaseReset'] == "THƯ GIÃN", f"Expected 'Thư giãn', got: {vi_data['phaseReset']}"
        assert vi_data['phaseOrganize'] == "Sắp xếp" or vi_data['phaseOrganize'] == "SẮP XẾP", f"Expected 'Sắp xếp', got: {vi_data['phaseOrganize']}"
        assert vi_data['phasePlan'] == "Lên kế hoạch" or vi_data['phasePlan'] == "LÊN KẾ HOẠCH", f"Expected 'Lên kế hoạch', got: {vi_data['phasePlan']}"
        assert vi_data['phaseReady'] == "Sẵn sàng" or vi_data['phaseReady'] == "SẴN SÀNG", f"Expected 'Sẵn sàng', got: {vi_data['phaseReady']}"
        assert "CHẾ ĐỘ KHẨN CẤP" in vi_data['badge'] or "Chế độ Khẩn cấp" in vi_data['badge'], f"Expected 'Chế độ Khẩn cấp', got: {vi_data['badge']}"
        assert vi_data['title'] == "Trút bỏ suy nghĩ", f"Expected 'Trút bỏ suy nghĩ', got: {vi_data['title']}"
        assert vi_data['subtitle'] == "Đưa mọi điều đang khiến bạn bận tâm ra khỏi đầu.", f"Expected 'Đưa mọi điều đang khiến bạn bận tâm ra khỏi đầu.', got: {vi_data['subtitle']}"
        assert vi_data['desc'] == "Liệt kê những việc bạn cần hoàn thành. Tempo sẽ giúp bạn sắp xếp chúng.", f"Expected description, got: {vi_data['desc']}"
        assert vi_data['inputLabel'] == "Bạn cần hoàn thành những việc gì?", f"Expected 'Bạn cần hoàn thành những việc gì?', got: {vi_data['inputLabel']}"
        assert vi_data['inputPlaceholder'] == "VD: Báo cáo Marketing, Bài tập Thống kê, Đọc chương 4...", f"Expected placeholder, got: {vi_data['inputPlaceholder']}"
        assert vi_data['deadlineLabel'] == "Deadline", f"Expected 'Deadline', got: {vi_data['deadlineLabel']}"
        assert vi_data['noDeadlineText'] == "Chưa có deadline", f"Expected 'Chưa có deadline', got: {vi_data['noDeadlineText']}"
        assert vi_data['addBtn'] == "+ Thêm task", f"Expected '+ Thêm task', got: {vi_data['addBtn']}"
        assert vi_data['loadSamplesBtn'] == "+ Thêm 3 task mẫu", f"Expected '+ Thêm 3 task mẫu', got: {vi_data['loadSamplesBtn']}"
        assert vi_data['taskCountHeader'] == "Task đã thêm (0)", f"Expected 'Task đã thêm (0)', got: {vi_data['taskCountHeader']}"
        assert vi_data['emptyState'] == "Chưa có task nào. Hãy nhập những task cần làm ở phía trên nhé.", f"Expected empty state text, got: {vi_data['emptyState']}"
        print("✓ All 18 Vietnamese translation requirements verified perfectly!")

        # Capture Vietnamese screenshots
        clip_vi = evaluate_js(ws, """
        (() => {
            const container = document.getElementById('emergency-stage-reality-check');
            if (!container) return null;
            container.scrollIntoView({ behavior: 'instant', block: 'start' });
            const rect = container.getBoundingClientRect();
            return {
                x: Math.max(0, rect.x - 10),
                y: Math.max(0, rect.y - 10),
                width: rect.width + 20,
                height: rect.height + 20,
                scale: 1
            };
        })()
        """)
        capture_screenshot(ws, None, os.path.join(ARTIFACT_DIR, "reality_check_vi.png"))
        if clip_vi:
            capture_screenshot(ws, clip_vi, os.path.join(ARTIFACT_DIR, "reality_check_vi_closeup.png"))

        print("\n=== STEP 2: LOAD SAMPLE TASKS IN VIETNAMESE & TEST INTERACTIONS ===")
        evaluate_js(ws, "window.TempoEmergencyFlow.loadSampleTasks()")
        time.sleep(1)

        tasks_vi = evaluate_js(ws, """
        (() => {
            const container = document.getElementById('emergency-stage-reality-check');
            const taskCountHeader = container?.querySelector('h4')?.textContent.trim();
            const rows = Array.from(document.querySelectorAll('#rc-tasks-list > div')).map(el => {
                const name = el.querySelector('h5')?.textContent.trim();
                const due = el.querySelector('p')?.textContent.trim();
                const btns = Array.from(el.querySelectorAll('button')).map(b => b.textContent.trim());
                return { name, due, btns };
            });
            const continueDisabled = document.getElementById('btn-rc-continue')?.hasAttribute('disabled');
            return { taskCountHeader, rows, continueDisabled };
        })()
        """)
        print("[SAMPLE TASKS VI]:", json.dumps(tasks_vi, ensure_ascii=False, indent=2))
        assert tasks_vi['taskCountHeader'] == "Task đã thêm (3)", f"Expected 'Task đã thêm (3)', got: {tasks_vi['taskCountHeader']}"
        assert len(tasks_vi['rows']) == 3, f"Expected 3 tasks, got: {len(tasks_vi['rows'])}"
        assert tasks_vi['continueDisabled'] is False, "Continue button should be enabled"
        # Check UGC preservation: sample task names remain as entered
        assert any("Statistics Assignment" in r['name'] for r in tasks_vi['rows'])
        assert any("Marketing Report" in r['name'] for r in tasks_vi['rows'])
        assert any("Biology Chapter 6 Notes" in r['name'] for r in tasks_vi['rows'])
        # Check action buttons in VI
        for r in tasks_vi['rows']:
            assert "Sửa" in r['btns'] and "Xóa" in r['btns'], f"Expected 'Sửa' and 'Xóa', got: {r['btns']}"
        print("✓ Sample tasks loaded and displayed with Vietnamese action buttons ('Sửa' / 'Xóa')!")

        # Test Edit Task form in Vietnamese
        first_id = evaluate_js(ws, "document.querySelector('#rc-tasks-list > div')?.getAttribute('data-task-id')")
        evaluate_js(ws, f"window.TempoEmergencyFlow.editRealityCheckTask('{first_id}')")
        time.sleep(0.5)

        edit_form_vi = evaluate_js(ws, """
        (() => {
            const editEl = document.querySelector('[data-editing="true"]');
            if (!editEl) return null;
            const labels = Array.from(editEl.querySelectorAll('label')).map(l => l.textContent.trim());
            const btns = Array.from(editEl.querySelectorAll('button')).map(b => b.textContent.trim());
            return { labels, btns };
        })()
        """)
        print("[EDIT FORM VI]:", edit_form_vi)
        assert any("Tên task" in l for l in edit_form_vi['labels']), "Expected 'Tên task' in edit form"
        assert any("Deadline" in l for l in edit_form_vi['labels']), "Expected 'Deadline' in edit form"
        assert any("Chưa có deadline" in l for l in edit_form_vi['labels']), "Expected 'Chưa có deadline' in edit form"
        assert "Hủy" in edit_form_vi['btns'] and "Lưu" in edit_form_vi['btns'], "Expected 'Hủy' and 'Lưu' buttons"
        print("✓ Edit task inline form fully localized in Vietnamese ('Tên task', 'Chưa có deadline', 'Hủy', 'Lưu')!")

        # Cancel edit
        evaluate_js(ws, "window.TempoEmergencyFlow.cancelRealityCheckTaskEdit()")
        time.sleep(0.5)

        print("\n=== STEP 3: SWITCH TO ENGLISH MODE (en) ===")
        evaluate_js(ws, """
        (() => {
            localStorage.setItem('tempo_language', 'en');
            localStorage.setItem('tempo_lang', 'en');
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('en');
            }
        })()
        """)
        time.sleep(1.5)

        en_data = evaluate_js(ws, """
        (() => {
            const bodyBg = window.getComputedStyle(document.body).backgroundColor;
            const container = document.getElementById('emergency-stage-reality-check');

            // Flow Shell Header
            const backHome = document.getElementById('em-header-back-home')?.textContent.trim();
            const sosLabel = document.getElementById('em-header-sos-label')?.textContent.trim();
            const phaseReset = document.getElementById('em-phase-reset')?.textContent.trim();
            const phaseOrganize = document.getElementById('em-phase-organize')?.textContent.trim();
            const phasePlan = document.getElementById('em-phase-plan')?.textContent.trim();
            const phaseReady = document.getElementById('em-phase-ready')?.textContent.trim();

            // Content
            const badge = container?.querySelector('span.text-xs.font-extrabold')?.textContent.trim();
            const title = container?.querySelector('h2')?.textContent.trim();
            const subtitle = container?.querySelector('h3')?.textContent.trim();
            const desc = container?.querySelector('p.text-xs, p.text-sm')?.textContent.trim();

            // Form
            const inputLabel = container?.querySelector('label[for="rc-task-name"]')?.textContent.trim();
            const inputPlaceholder = document.getElementById('rc-task-name')?.getAttribute('placeholder');
            const deadlineLabel = container?.querySelectorAll('label.block')[1]?.textContent.trim();
            const noDeadlineText = document.getElementById('rc-no-deadline-cb')?.parentElement?.textContent.trim();
            const addBtn = container?.querySelector('button[onclick*="addRealityCheckTask"]')?.textContent.trim();
            const loadSamplesBtn = container?.querySelector('button[onclick*="loadSampleTasks"]')?.textContent.trim();

            // Tasks list
            const taskCountHeader = container?.querySelector('h4')?.textContent.trim();
            const rows = Array.from(document.querySelectorAll('#rc-tasks-list > div')).map(el => {
                const name = el.querySelector('h5')?.textContent.trim();
                const due = el.querySelector('p')?.textContent.trim();
                const btns = Array.from(el.querySelectorAll('button')).map(b => b.textContent.trim());
                return { name, due, btns };
            });

            // Bottom CTA
            const backBtn = container?.querySelector('button[onclick*="goToStage"]')?.textContent.trim();
            const continueBtn = document.getElementById('btn-rc-continue')?.textContent.trim();

            return {
                bodyBg,
                backHome,
                sosLabel,
                phaseReset,
                phaseOrganize,
                phasePlan,
                phaseReady,
                badge,
                title,
                subtitle,
                desc,
                inputLabel,
                inputPlaceholder,
                deadlineLabel,
                noDeadlineText,
                addBtn,
                loadSamplesBtn,
                taskCountHeader,
                rows,
                backBtn,
                continueBtn
            };
        })()
        """)
        print("\n[ENGLISH REALITY CHECK DATA]:")
        print(json.dumps(en_data, ensure_ascii=False, indent=2))

        # Verify English labels
        assert en_data['backHome'] == "Back to Home", f"Expected 'Back to Home', got: {en_data['backHome']}"
        assert en_data['sosLabel'] == "SOS Support", f"Expected 'SOS Support', got: {en_data['sosLabel']}"
        assert en_data['phaseReset'] == "RESET" or en_data['phaseReset'] == "Reset", f"Expected 'RESET', got: {en_data['phaseReset']}"
        assert en_data['phaseOrganize'] == "ORGANIZE" or en_data['phaseOrganize'] == "Organize", f"Expected 'ORGANIZE', got: {en_data['phaseOrganize']}"
        assert en_data['phasePlan'] == "PLAN" or en_data['phasePlan'] == "Plan", f"Expected 'PLAN', got: {en_data['phasePlan']}"
        assert en_data['phaseReady'] == "READY" or en_data['phaseReady'] == "Ready", f"Expected 'READY', got: {en_data['phaseReady']}"
        assert en_data['badge'] == "URGENT MODE", f"Expected 'URGENT MODE', got: {en_data['badge']}"
        assert en_data['title'] == "Reality Check", f"Expected 'Reality Check', got: {en_data['title']}"
        assert en_data['subtitle'] == "Get everything out of your head.", f"Expected 'Get everything out of your head.', got: {en_data['subtitle']}"
        assert en_data['desc'] == "Add what you need to get done. We'll organize it next.", f"Expected description, got: {en_data['desc']}"
        assert en_data['inputLabel'] == "What do you need to get done?", f"Expected 'What do you need to get done?', got: {en_data['inputLabel']}"
        assert en_data['inputPlaceholder'] == "e.g. Marketing Report, Statistics Lab, Chapter 4 Reading...", f"Expected placeholder, got: {en_data['inputPlaceholder']}"
        assert en_data['deadlineLabel'] == "Deadline", f"Expected 'Deadline', got: {en_data['deadlineLabel']}"
        assert en_data['noDeadlineText'] == "No fixed deadline", f"Expected 'No fixed deadline', got: {en_data['noDeadlineText']}"
        assert en_data['addBtn'] == "+ Add task", f"Expected '+ Add task', got: {en_data['addBtn']}"
        assert en_data['loadSamplesBtn'] == "+ Load 3 sample tasks", f"Expected '+ Load 3 sample tasks', got: {en_data['loadSamplesBtn']}"
        assert en_data['taskCountHeader'] == "Added Tasks (3)", f"Expected 'Added Tasks (3)', got: {en_data['taskCountHeader']}"
        assert en_data['backBtn'] == "← Back to Reset", f"Expected '← Back to Reset', got: {en_data['backBtn']}"
        assert "I've added everything" in en_data['continueBtn'], f"Expected 'I've added everything', got: {en_data['continueBtn']}"
        for r in en_data['rows']:
            assert "Edit" in r['btns'] and "Remove" in r['btns'], f"Expected 'Edit' and 'Remove', got: {r['btns']}"
        print("✓ All English labels verified perfectly!")

        # Capture English screenshots
        clip_en = evaluate_js(ws, """
        (() => {
            const container = document.getElementById('emergency-stage-reality-check');
            if (!container) return null;
            container.scrollIntoView({ behavior: 'instant', block: 'start' });
            const rect = container.getBoundingClientRect();
            return {
                x: Math.max(0, rect.x - 10),
                y: Math.max(0, rect.y - 10),
                width: rect.width + 20,
                height: rect.height + 20,
                scale: 1
            };
        })()
        """)
        capture_screenshot(ws, None, os.path.join(ARTIFACT_DIR, "reality_check_en.png"))
        if clip_en:
            capture_screenshot(ws, clip_en, os.path.join(ARTIFACT_DIR, "reality_check_en_closeup.png"))

        print("\n=== STEP 4: VERIFY BACKGROUND REVERSION ON STAGE NAVIGATION ===")
        # Navigate back to 'entry' (Reset stage)
        evaluate_js(ws, "window.TempoEmergencyFlow.goToStage('entry')")
        time.sleep(1)

        entry_bg = evaluate_js(ws, "window.getComputedStyle(document.body).backgroundColor")
        print(f"Entry stage (Reset) body background: {entry_bg}")
        # Default warm cream is rgb(250, 247, 242)
        assert "250, 247, 242" in entry_bg or "faf7f2" in entry_bg.lower(), \
            f"Expected warm cream (#FAF7F2), got: {entry_bg}"
        print("✓ Verified background reverted to warm cream (#FAF7F2) on Reset stage!")

        # Navigate back to 'reality-check'
        evaluate_js(ws, "window.TempoEmergencyFlow.goToStage('reality-check')")
        time.sleep(1)

        rc_bg_again = evaluate_js(ws, "window.getComputedStyle(document.body).backgroundColor")
        print(f"Reality Check body background again: {rc_bg_again}")
        assert "237, 244, 239" in rc_bg_again, f"Expected Sage Green (#EDF4EF), got: {rc_bg_again}"
        print("✓ Verified background seamlessly returns to light Sage Green (#EDF4EF) on Reality Check!")

        # Navigate to Today dashboard
        evaluate_js(ws, "window.TempoApp.navigateTo('today')")
        time.sleep(1)

        today_bg = evaluate_js(ws, "window.getComputedStyle(document.body).backgroundColor")
        print(f"Today dashboard body background: {today_bg}")
        assert "250, 247, 242" in today_bg or "faf7f2" in today_bg.lower(), \
            f"Expected warm cream (#FAF7F2), got: {today_bg}"
        print("✓ Verified background clean cleanup when navigating away from emergency flow!")

        print("\n=======================================================")
        print("ALL REALITY CHECK LOCALIZATION & THEME CHECKS PASSED!")
        print("=======================================================")

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
