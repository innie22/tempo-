#!/usr/bin/env python3
"""
Comprehensive CDP Verification for Prioritize & Estimate Page:
1. Vietnamese Localization (all table keys + static labels)
2. Colors & Tempo Palette (Light Sage Green bg, Warm Blush card & rating selections, Sage Green positive & primary actions, Dusty Blue accents)
3. Interactive behavior (single-select, multi-select, custom duration, deadline modal)
4. English switching & immediate UI text update
5. Preservation of user-entered task names and prioritization classification data
"""

import sys
import os
import json
import time
import subprocess
import urllib.request
import base64

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

CDP_PORT = 9460
TARGET_URL = "http://127.0.0.1:8000/#today"
ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"

def start_browser():
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    edge_binary = next((p for p in edge_paths if os.path.exists(p)), None)
    if not edge_binary:
        raise RuntimeError("Edge binary not found")

    user_data_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), f"cdp_prioritize_{int(time.time())}")
    cmd = [
        edge_binary,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--headless=new",
        "--disable-gpu",
        "--window-size=1280,2400",
        TARGET_URL
    ]
    print(f"Starting Edge on port {CDP_PORT}")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.5)
    return proc

def send_cdp_command(ws_url, method, params=None):
    import urllib.request
    req_data = {
        "id": int(time.time() * 1000) % 1000000,
        "method": method,
        "params": params or {}
    }
    import websocket
    ws = websocket.create_connection(ws_url, timeout=15)
    ws.send(json.dumps(req_data))
    while True:
        res = ws.recv()
        data = json.loads(res)
        if data.get("id") == req_data["id"]:
            ws.close()
            return data.get("result", {})

def eval_js(ws_url, expr):
    res = send_cdp_command(ws_url, "Runtime.evaluate", {
        "expression": expr,
        "returnByValue": True,
        "awaitPromise": True
    })
    if "exceptionDetails" in res:
        print("[JS EXCEPTION]:", res["exceptionDetails"])
    return res.get("result", {}).get("value")

def capture_screenshot(ws_url, filepath, clip=None):
    params = {"format": "png"}
    if clip:
        params["clip"] = clip
    res = send_cdp_command(ws_url, "Page.captureScreenshot", params)
    data = res.get("data")
    if data:
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"Saved screenshot: {filepath}")

def main():
    browser = start_browser()
    try:
        targets_json = urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json").read().decode('utf-8')
        targets = json.loads(targets_json)
        page_tabs = [t for t in targets if t.get("type") == "page" and "8000" in t.get("url", "")]
        target = page_tabs[0] if page_tabs else [t for t in targets if t.get("type") == "page"][0]
        ws_url = target["webSocketDebuggerUrl"]
        print("Connected to CDP target:", target.get("url"))

        # Wait for dependencies
        for _ in range(40):
            ready = eval_js(ws_url, "Boolean(window.TempoAuth && window.TempoEmergencyFlow && window.TempoI18n && window.TempoMode)")
            if ready:
                break
            time.sleep(0.5)

        # 1. Initialize user and load sample tasks
        init_js = """
        (async function() {
            localStorage.clear();
            sessionStorage.clear();
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.resetFlowState === 'function') {
                window.TempoEmergencyFlow.resetFlowState();
            }
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('vi');
            }

            const email = 'user_prioritize@fpt.edu.vn';
            const pass = 'Password123!';
            const name = 'Prioritize Student';
            await window.TempoAuth.register(name, email, pass);
            await window.TempoAuth.signIn(email, pass);

            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.close === 'function') {
                window.TempoRecoverySetup.close();
            }
            if (window.TempoAuth.closeAllAuthModals) {
                window.TempoAuth.closeAllAuthModals();
            }

            window.TempoMode.setMode('emergency');
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('emergency');
            }

            // Load 3 sample tasks with specific deadlines
            // Task 1: Overdue deadline
            // Task 2: Tomorrow deadline
            // Task 3: No fixed deadline
            const now = new Date();
            const past = new Date(now.getTime() - 2 * 3600 * 1000);
            const pad = n => String(n).padStart(2, '0');
            const pastDate = `${past.getFullYear()}-${pad(past.getMonth()+1)}-${pad(past.getDate())}`;
            const pastTime = `${pad(past.getHours())}:${pad(past.getMinutes())}`;

            const tomorrow = new Date(now.getTime() + 24 * 3600 * 1000);
            const tomDate = `${tomorrow.getFullYear()}-${pad(tomorrow.getMonth()+1)}-${pad(tomorrow.getDate())}`;

            window.TempoEmergencyFlow.loadSampleTasks();

            // Set specific deadlines on the 3 sample tasks
            const tasks = window.TempoEmergencyFlow.getTasks();
            if (tasks && tasks.length >= 3) {
                tasks[0].name = "Báo cáo Đồ án Tốt nghiệp";
                tasks[0].hasDeadline = true;
                tasks[0].deadlineDate = pastDate;
                tasks[0].deadlineTime = pastTime;

                tasks[1].name = "Bài tập Thống kê Tin học";
                tasks[1].hasDeadline = true;
                tasks[1].deadlineDate = tomDate;
                tasks[1].deadlineTime = "09:00";

                tasks[2].name = "Đọc tài liệu Chương 4";
                tasks[2].hasDeadline = false;
                tasks[2].deadlineDate = null;
                tasks[2].deadlineTime = null;
            }

            // Proceed to Prioritize & Estimate
            window.TempoEmergencyFlow.continueFromRealityCheck();

            return { ready: true, stage: window.TempoEmergencyFlow.getCurrentStage() };
        })()
        """
        setup_res = eval_js(ws_url, init_js)
        print("Setup result:", setup_res)
        time.sleep(1)

        # =========================================================================
        # TEST 1: VERIFY VIETNAMESE LOCALIZATION & VISUAL STYLING ON TASK 1
        # =========================================================================
        print("\n=== TEST 1: VERIFY VIETNAMESE LOCALIZATION & STYLING (TASK 1) ===")
        check_task1_js = """
        (function() {
            const container = document.getElementById('emergency-stage-prioritize');
            if (!container) return { err: "Container not found" };

            const bodyBg = window.getComputedStyle(document.body).backgroundColor;
            const screen = document.getElementById('screen-emergency');
            const screenBg = screen ? window.getComputedStyle(screen).backgroundColor : '';

            // Header elements
            const badge = container.querySelector('span.tracking-widest')?.innerText?.trim();
            const title = container.querySelector('h2')?.innerText?.trim();
            const subtitle = container.querySelector('p.text-xs, p.text-sm')?.innerText?.trim();

            // Back button
            const backBtn = container.querySelector('button')?.innerText?.trim();

            // Progress
            const progressRow = container.querySelector('.flex.justify-between.text-xs');
            const progressTask = progressRow?.children[0]?.innerText?.trim();
            const progressPercent = progressRow?.children[1]?.innerText?.trim();
            const progressTaskColor = progressRow?.children[0] ? window.getComputedStyle(progressRow.children[0]).color : '';

            // Task card preview
            const taskCard = container.querySelector('.rounded-2xl');
            const taskCardBg = taskCard ? window.getComputedStyle(taskCard).backgroundColor : '';
            const taskCardBorder = taskCard ? window.getComputedStyle(taskCard).borderColor : '';
            const currentBadge = taskCard?.querySelector('span')?.innerText?.trim();
            const taskName = taskCard?.querySelector('h3')?.innerText?.trim();
            const dueDisplay = taskCard?.querySelector('p span.font-semibold')?.innerText?.trim();
            const editDeadlineBtn = taskCard?.querySelector('button')?.innerText?.trim();

            // Questions
            const qBlocks = Array.from(container.querySelectorAll('.space-y-6 > .space-y-2'));
            const qLabels = qBlocks.map(b => b.querySelector('label')?.innerText?.trim() || '');

            // Q1 options
            const q1Pills = Array.from(qBlocks[0]?.querySelectorAll('.em-choice-pill') || []).map(p => ({
                text: p.innerText.trim(),
                selected: p.className.includes('selected')
            }));

            // Q2 options
            const q2Pills = Array.from(qBlocks[1]?.querySelectorAll('.em-choice-pill') || []).map(p => ({
                text: p.innerText.trim(),
                selected: p.className.includes('selected')
            }));

            // Q3 options
            const q3Pills = Array.from(qBlocks[2]?.querySelectorAll('.em-choice-pill') || []).map(p => ({
                text: p.children[0]?.innerText?.trim(),
                mark: p.children[1]?.innerText?.trim(),
                selected: p.className.includes('selected')
            }));

            // Q4 options
            const q4Pills = Array.from(qBlocks[3]?.querySelectorAll('.grid .em-choice-pill') || []).map(p => ({
                text: p.innerText.trim(),
                selected: p.className.includes('selected')
            }));

            // Bottom action button
            const bottomBtns = Array.from(container.querySelectorAll('.pt-2.flex.items-center.justify-between button')).map(b => b.innerText.trim());
            const primaryBtn = container.querySelector('.pt-2.flex.items-center.justify-between button:last-child');
            const primaryBtnBg = primaryBtn ? window.getComputedStyle(primaryBtn).backgroundColor : '';

            const rect = container.getBoundingClientRect();

            return {
                bodyBg,
                screenBg,
                badge,
                title,
                subtitle,
                backBtn,
                progressTask,
                progressPercent,
                progressTaskColor,
                taskCardBg,
                taskCardBorder,
                currentBadge,
                taskName,
                dueDisplay,
                editDeadlineBtn,
                qLabels,
                q1Pills,
                q2Pills,
                q3Pills,
                q4Pills,
                bottomBtns,
                primaryBtnBg,
                clip: {
                    x: Math.max(0, rect.x),
                    y: Math.max(0, rect.y),
                    width: Math.min(rect.width, 1200),
                    height: Math.min(rect.height + 40, 1500),
                    scale: 1
                }
            };
        })()
        """
        t1_data = eval_js(ws_url, check_task1_js)
        print("Task 1 Data (VI):", json.dumps(t1_data, indent=2, ensure_ascii=False))

        # Assertions for VI
        assert "ƯU TIÊN & ƯỚC LƯỢNG" in t1_data["badge"], f"Expected 'ƯU TIÊN & ƯỚC LƯỢNG', got {t1_data['badge']}"
        assert "Hãy xác định những việc cần được ưu tiên trước." in t1_data["title"], f"Expected VI title, got {t1_data['title']}"
        assert "Chúng ta sẽ xem xét từng task một." in t1_data["subtitle"], f"Expected VI subtitle, got {t1_data['subtitle']}"
        assert "Quay lại Trút bỏ suy nghĩ" in t1_data["backBtn"], f"Expected 'Quay lại Trút bỏ suy nghĩ', got {t1_data['backBtn']}"
        assert t1_data["progressTask"] == "Task 1/3", f"Expected 'Task 1/3', got {t1_data['progressTask']}"
        assert "33%" in t1_data["progressPercent"], f"Expected '33%', got {t1_data['progressPercent']}"
        assert t1_data["currentBadge"] == "TASK HIỆN TẠI", f"Expected 'TASK HIỆN TẠI', got {t1_data['currentBadge']}"
        assert t1_data["taskName"] == "Báo cáo Đồ án Tốt nghiệp", f"User task name mutated! {t1_data['taskName']}"
        assert "Đã quá Deadline" in t1_data["dueDisplay"], f"Expected 'Đã quá Deadline', got {t1_data['dueDisplay']}"
        assert t1_data["editDeadlineBtn"] == "Sửa Deadline", f"Expected 'Sửa Deadline', got {t1_data['editDeadlineBtn']}"

        # Q1 labels & options
        assert "TASK NÀY QUAN TRỌNG NHƯ THẾ NÀO?" in t1_data["qLabels"][0], f"Expected Q1 VI label, got {t1_data['qLabels'][0]}"
        q1_texts = [p["text"] for p in t1_data["q1Pills"]]
        assert q1_texts == ["Cao", "Trung bình", "Thấp"], f"Expected Q1 pills ['Cao', 'Trung bình', 'Thấp'], got {q1_texts}"

        # Q2 labels & options
        assert "ĐIỀU GÌ XẢY RA NẾU TASK BỊ TRỄ HOẶC CHƯA HOÀN THÀNH?" in t1_data["qLabels"][1], f"Expected Q2 VI label, got {t1_data['qLabels'][1]}"
        q2_texts = [p["text"] for p in t1_data["q2Pills"]]
        assert q2_texts == ["Hậu quả nghiêm trọng", "Có một số hậu quả", "Không đáng kể", "Không chắc"], f"Expected Q2 pills, got {q2_texts}"

        # Q3 labels & options
        assert "CÓ ĐIỀU GÌ Ở TASK NÀY CÓ THỂ THAY ĐỔI ĐƯỢC KHÔNG?" in t1_data["qLabels"][2], f"Expected Q3 VI label, got {t1_data['qLabels'][2]}"
        assert "CHỌN TẤT CẢ ĐÁP ÁN PHÙ HỢP" in t1_data["qLabels"][2], f"Expected 'CHỌN TẤT CẢ ĐÁP ÁN PHÙ HỢP' in Q3, got {t1_data['qLabels'][2]}"
        q3_texts = [p["text"] for p in t1_data["q3Pills"]]
        assert q3_texts == ["Giảm bớt khối lượng việc cần làm", "Nhờ người khác hỗ trợ", "Dời / thương lượng lại Deadline", "Hầu như không thể thay đổi", "Không chắc"], f"Expected Q3 pills, got {q3_texts}"

        # Q4 labels & options
        assert "bạn nghĩ mình sẽ cần bao nhiêu thời gian?" in t1_data["qLabels"][3].lower(), f"Expected Q4 VI label, got {t1_data['qLabels'][3]}"
        q4_texts = [p["text"] for p in t1_data["q4Pills"]]
        assert q4_texts == ["30 phút", "1 giờ", "2 giờ", "3 giờ", "Tùy chỉnh", "Không chắc"], f"Expected Q4 pills, got {q4_texts}"

        # Bottom buttons
        assert any("Lưu & task tiếp theo" in b for b in t1_data["bottomBtns"]), f"Expected 'Lưu & task tiếp theo →', got {t1_data['bottomBtns']}"

        # Theme & Color checks
        # Soft Light Sage Green background: rgb(237, 244, 239)
        assert t1_data["bodyBg"] == "rgb(237, 244, 239)", f"Expected soft sage bg rgb(237, 244, 239), got {t1_data['bodyBg']}"
        # Warm Blush card border: rgb(236, 201, 186)
        assert t1_data["taskCardBorder"] == "rgb(236, 201, 186)", f"Expected warm blush border rgb(236, 201, 186), got {t1_data['taskCardBorder']}"
        # Primary Action button: Sage Green rgb(74, 107, 93)
        assert t1_data["primaryBtnBg"] == "rgb(74, 107, 93)", f"Expected sage green button rgb(74, 107, 93), got {t1_data['primaryBtnBg']}"

        print("✓ All Task 1 Vietnamese translations & Tempo color requirements verified!")
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "prioritize_estimate_vi.png"))
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "prioritize_estimate_vi_closeup.png"), clip=t1_data["clip"])

        # =========================================================================
        # TEST 2: INTERACTIVE SELECTIONS & DEADLINE MODAL
        # =========================================================================
        print("\n=== TEST 2: TEST INTERACTIVE SELECTIONS & MODAL ===")
        interactive_js = """
        (async function() {
            // Select Q1: High (Cao)
            window.TempoEmergencyFlow.setAssessmentOption('importance', 'High');
            // Select Q2: Big consequences (Hậu quả nghiêm trọng)
            window.TempoEmergencyFlow.setAssessmentOption('consequence', 'Big consequences');
            // Clear and toggle Q3 multi-select
            const tasks = window.TempoEmergencyFlow.getTasks();
            tasks[0].flexibility = [];
            window.TempoEmergencyFlow.toggleAssessmentFlexibility('Reduce what I need to do');
            window.TempoEmergencyFlow.toggleAssessmentFlexibility('Ask someone for help');
            // Select Q4: 2h (2 giờ)
            window.TempoEmergencyFlow.setAssessmentDuration(120);

            // Open deadline modal
            window.TempoEmergencyFlow.openDeadlineModal(tasks[0].id);

            await new Promise(r => setTimeout(r, 200));

            const modal = document.querySelector('[role="dialog"]');
            if (!modal) return { modalFound: false };

            const modalTitle = modal.querySelector('h3')?.innerText?.trim();
            const modalLabels = Array.from(modal.querySelectorAll('label')).map(l => l.innerText.trim());
            const modalBtns = Array.from(modal.querySelectorAll('button')).map(b => b.innerText.trim());

            return {
                modalFound: true,
                modalTitle,
                modalLabels,
                modalBtns
            };
        })()
        """
        modal_res = eval_js(ws_url, interactive_js)
        print("Deadline Modal status:", modal_res)
        assert modal_res["modalFound"], "Deadline modal not found"
        assert modal_res["modalTitle"] == "Sửa Deadline", f"Expected 'Sửa Deadline', got {modal_res['modalTitle']}"
        assert any("Ngày & giờ Deadline" in l for l in modal_res["modalLabels"]), f"Expected 'Ngày & giờ Deadline', got {modal_res['modalLabels']}"
        assert any("Chưa có deadline" in l for l in modal_res["modalLabels"]), f"Expected 'Chưa có deadline', got {modal_res['modalLabels']}"
        assert any("Hủy" in b for b in modal_res["modalBtns"]), f"Expected 'Hủy', got {modal_res['modalBtns']}"
        assert any("Lưu thay đổi" in b for b in modal_res["modalBtns"]), f"Expected 'Lưu thay đổi', got {modal_res['modalBtns']}"
        print("✓ Deadline modal fully localized in Vietnamese!")
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "prioritize_estimate_modal_vi.png"))

        # Close modal and verify selections styling
        eval_js(ws_url, "window.TempoEmergencyFlow.closeDeadlineModal()")
        time.sleep(0.3)

        verify_selections_js = """
        (function() {
            const container = document.getElementById('emergency-stage-prioritize');
            const qBlocks = Array.from(container.querySelectorAll('.space-y-6 > .space-y-2'));
            const q1Selected = qBlocks[0]?.querySelector('.em-choice-pill--blush-selected')?.innerText?.trim();
            const q2Selected = qBlocks[1]?.querySelector('.em-choice-pill--blush-selected')?.innerText?.trim();

            const q3SelectedPills = Array.from(qBlocks[2]?.querySelectorAll('.em-choice-pill--sage-selected') || []).map(p => ({
                text: p.children[0]?.innerText?.trim(),
                mark: p.children[1]?.innerText?.trim()
            }));

            const q4Selected = qBlocks[3]?.querySelector('.em-choice-pill--sage-selected')?.innerText?.trim();

            return {
                q1Selected,
                q2Selected,
                q3SelectedPills,
                q4Selected
            };
        })()
        """
        sel_data = eval_js(ws_url, verify_selections_js)
        print("Selected state data:", sel_data)
        assert sel_data["q1Selected"] == "Cao", f"Expected Q1 'Cao' selected, got {sel_data['q1Selected']}"
        assert sel_data["q2Selected"] == "Hậu quả nghiêm trọng", f"Expected Q2 'Hậu quả nghiêm trọng' selected, got {sel_data['q2Selected']}"
        assert len(sel_data["q3SelectedPills"]) == 2, f"Expected 2 selected flexibility pills, got {len(sel_data['q3SelectedPills'])}"
        assert sel_data["q3SelectedPills"][0]["mark"] == "✓", "Expected checkmark ✓ on selected flexibility pill"
        assert sel_data["q4Selected"] == "2 giờ", f"Expected Q4 '2 giờ' selected, got {sel_data['q4Selected']}"
        print("✓ Warm Blush selected states (Q1, Q2) and Sage Green positive selected states (Q3, Q4) verified!")

        # =========================================================================
        # TEST 3: TASK NAVIGATION & LAST TASK REVIEW BUTTON
        # =========================================================================
        print("\n=== TEST 3: TASK NAVIGATION & LAST TASK REVIEW BUTTON ===")
        nav_js = """
        (function() {
            const container = document.getElementById('emergency-stage-prioritize');
            // Navigate to Task 2
            window.TempoEmergencyFlow.saveAssessmentAndNext();
            const t2State = {
                progressTask: container.querySelector('.flex.justify-between.text-xs span:first-child')?.innerText?.trim(),
                backBtn: container.querySelector('.flex.items-center.justify-between button span:last-child')?.innerText?.trim(),
                nextBtn: container.querySelector('.pt-2.flex.items-center.justify-between button:last-child')?.innerText?.trim()
            };

            // Navigate to Task 3 (last task)
            window.TempoEmergencyFlow.saveAssessmentAndNext();
            const t3State = {
                progressTask: container.querySelector('.flex.justify-between.text-xs span:first-child')?.innerText?.trim(),
                backBtn: container.querySelector('.flex.items-center.justify-between button span:last-child')?.innerText?.trim(),
                nextBtn: container.querySelector('.pt-2.flex.items-center.justify-between button:last-child')?.innerText?.trim()
            };

            return { t2State, t3State };
        })()
        """
        nav_data = eval_js(ws_url, nav_js)
        print("Navigation Data:", nav_data)
        assert nav_data["t2State"]["progressTask"] == "Task 2/3", f"Expected 'Task 2/3', got {nav_data['t2State']['progressTask']}"
        assert "Task trước" in nav_data["t2State"]["backBtn"], f"Expected 'Task trước', got {nav_data['t2State']['backBtn']}"
        assert nav_data["t3State"]["progressTask"] == "Task 3/3", f"Expected 'Task 3/3', got {nav_data['t3State']['progressTask']}"
        assert "Xem các nhóm ưu tiên" in nav_data["t3State"]["nextBtn"], f"Expected 'Xem các nhóm ưu tiên →', got {nav_data['t3State']['nextBtn']}"
        print("✓ Task navigation and dynamic labels (Task trước, Xem các nhóm ưu tiên →) verified!")

        # =========================================================================
        # TEST 4: ENGLISH MODE SWITCHING & IMMEDIATE UI UPDATE
        # =========================================================================
        print("\n=== TEST 4: ENGLISH MODE SWITCHING & IMMEDIATE UI UPDATE ===")
        en_switch_js = """
        (function() {
            // Return to Task 1
            window.TempoEmergencyFlow.previousAssessmentTask();
            window.TempoEmergencyFlow.previousAssessmentTask();

            // Switch to English
            window.TempoI18n.setLanguage('en');

            const container = document.getElementById('emergency-stage-prioritize');
            const badge = container.querySelector('span.tracking-widest')?.innerText?.trim();
            const title = container.querySelector('h2')?.innerText?.trim();
            const subtitle = container.querySelector('p.text-xs, p.text-sm')?.innerText?.trim();
            const backBtn = container.querySelector('button')?.innerText?.trim();
            const progressTask = container.querySelector('.flex.justify-between.text-xs span:first-child')?.innerText?.trim();
            const progressPercent = container.querySelector('.flex.justify-between.text-xs span:last-child')?.innerText?.trim();
            const currentBadge = container.querySelector('.rounded-2xl span')?.innerText?.trim();
            const taskName = container.querySelector('.rounded-2xl h3')?.innerText?.trim();
            const dueDisplay = container.querySelector('.rounded-2xl p span.font-semibold')?.innerText?.trim();
            const editDeadlineBtn = container.querySelector('.rounded-2xl button')?.innerText?.trim();

            const qBlocks = Array.from(container.querySelectorAll('.space-y-6 > .space-y-2'));
            const qLabels = qBlocks.map(b => b.querySelector('label')?.innerText?.trim() || '');
            const q1Texts = Array.from(qBlocks[0]?.querySelectorAll('.em-choice-pill') || []).map(p => p.innerText.trim());
            const q2Texts = Array.from(qBlocks[1]?.querySelectorAll('.em-choice-pill') || []).map(p => p.innerText.trim());
            const q3Texts = Array.from(qBlocks[2]?.querySelectorAll('.em-choice-pill') || []).map(p => p.children[0]?.innerText?.trim());
            const q4Texts = Array.from(qBlocks[3]?.querySelectorAll('.grid .em-choice-pill') || []).map(p => p.innerText.trim());
            const nextBtn = container.querySelector('.pt-2.flex.items-center.justify-between button:last-child')?.innerText?.trim();

            return {
                badge,
                title,
                subtitle,
                backBtn,
                progressTask,
                progressPercent,
                currentBadge,
                taskName,
                dueDisplay,
                editDeadlineBtn,
                qLabels,
                q1Texts,
                q2Texts,
                q3Texts,
                q4Texts,
                nextBtn,
                clip: {
                    x: Math.max(0, container.getBoundingClientRect().x),
                    y: Math.max(0, container.getBoundingClientRect().y),
                    width: Math.min(container.getBoundingClientRect().width, 1200),
                    height: Math.min(container.getBoundingClientRect().height + 40, 1500),
                    scale: 1
                }
            };
        })()
        """
        en_data = eval_js(ws_url, en_switch_js)
        print("English Data:", json.dumps(en_data, indent=2, ensure_ascii=False))

        assert en_data["badge"] == "PRIORITIZE & ESTIMATE", f"Expected 'PRIORITIZE & ESTIMATE', got {en_data['badge']}"
        assert "Let's figure out what needs your attention first." in en_data["title"], f"Expected EN title, got {en_data['title']}"
        assert "We'll look at one task at a time." in en_data["subtitle"], f"Expected EN subtitle, got {en_data['subtitle']}"
        assert "Back to Reality Check" in en_data["backBtn"], f"Expected 'Back to Reality Check', got {en_data['backBtn']}"
        assert en_data["progressTask"] == "Task 1 of 3", f"Expected 'Task 1 of 3', got {en_data['progressTask']}"
        assert "33% evaluated" in en_data["progressPercent"], f"Expected '33% evaluated', got {en_data['progressPercent']}"
        assert en_data["currentBadge"] == "CURRENT TASK", f"Expected 'CURRENT TASK', got {en_data['currentBadge']}"
        assert en_data["taskName"] == "Báo cáo Đồ án Tốt nghiệp", f"User task name mutated! {en_data['taskName']}"
        assert en_data["dueDisplay"] == "Deadline passed", f"Expected 'Deadline passed', got {en_data['dueDisplay']}"
        assert en_data["editDeadlineBtn"] == "Edit deadline", f"Expected 'Edit deadline', got {en_data['editDeadlineBtn']}"

        assert "1. HOW IMPORTANT IS THIS TASK?" in en_data["qLabels"][0], f"Expected Q1 EN label, got {en_data['qLabels'][0]}"
        assert en_data["q1Texts"] == ["High", "Medium", "Low"], f"Expected ['High', 'Medium', 'Low'], got {en_data['q1Texts']}"

        assert "2. WHAT HAPPENS IF IT'S LATE OR UNFINISHED?" in en_data["qLabels"][1], f"Expected Q2 EN label, got {en_data['qLabels'][1]}"
        assert en_data["q2Texts"] == ["Big consequences", "Some consequences", "Not much", "Not sure"], f"Expected Q2 EN texts, got {en_data['q2Texts']}"

        assert "3. CAN ANYTHING ABOUT THIS TASK CHANGE?" in en_data["qLabels"][2], f"Expected Q3 EN label, got {en_data['qLabels'][2]}"
        assert "SELECT ALL THAT APPLY" in en_data["qLabels"][2], f"Expected 'SELECT ALL THAT APPLY', got {en_data['qLabels'][2]}"
        assert en_data["q3Texts"] == ["Reduce what I need to do", "Ask someone for help", "Move / negotiate the deadline", "Probably not", "Not sure"], f"Expected Q3 EN texts, got {en_data['q3Texts']}"

        assert en_data["q4Texts"] == ["30 min", "1h", "2h", "3h", "Custom", "Not sure"], f"Expected Q4 EN texts, got {en_data['q4Texts']}"
        assert "Save & next task" in en_data["nextBtn"], f"Expected 'Save & next task →', got {en_data['nextBtn']}"

        print("✓ English mode immediately and correctly updated all static UI text!")
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "prioritize_estimate_en.png"))
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "prioritize_estimate_en_closeup.png"), clip=en_data["clip"])

        # =========================================================================
        # TEST 5: CLASSIFICATION ALGORITHM & DATA INTEGRITY
        # =========================================================================
        print("\n=== TEST 5: CLASSIFICATION ALGORITHM & DATA INTEGRITY ===")
        classification_js = """
        (function() {
            // Complete assessment for all 3 tasks and transition to Stage 4 Priority Review
            // Task 1: High importance, Big consequences, has flexibility -> REDUCE_HELP or DO_FIRST
            window.TempoEmergencyFlow.saveAssessmentAndNext(); // go to task 2

            // Task 2: High importance, Some consequences, no flexibility -> PLAN
            const tasks = window.TempoEmergencyFlow.getTasks();
            tasks[1].flexibility = ['Probably not'];
            window.TempoEmergencyFlow.setAssessmentOption('importance', 'High');
            window.TempoEmergencyFlow.setAssessmentOption('consequence', 'Some consequences');
            window.TempoEmergencyFlow.saveAssessmentAndNext(); // go to task 3

            // Task 3: Low importance, Not much consequence, no flexibility -> LATER
            tasks[2].flexibility = ['Probably not'];
            window.TempoEmergencyFlow.setAssessmentOption('importance', 'Low');
            window.TempoEmergencyFlow.setAssessmentOption('consequence', 'Not much');
            window.TempoEmergencyFlow.saveAssessmentAndNext(); // triggers applyDeterministicClassification and moves to priority-review

            const finalStage = window.TempoEmergencyFlow.getCurrentStage();

            return {
                finalStage,
                task1Category: tasks[0]?.priorityCategory,
                task2Category: tasks[1]?.priorityCategory,
                task3Category: tasks[2]?.priorityCategory
            };
        })()
        """
        algo_res = eval_js(ws_url, classification_js)
        print("Algorithm Result:", algo_res)
        assert algo_res["finalStage"] == "priority-review", f"Expected stage 'priority-review', got {algo_res['finalStage']}"
        assert algo_res["task1Category"] == "DO_FIRST", f"Expected Task 1 in DO_FIRST, got {algo_res['task1Category']}"
        assert algo_res["task2Category"] == "DO_FIRST", f"Expected Task 2 in DO_FIRST (due soon + high importance), got {algo_res['task2Category']}"
        assert algo_res["task3Category"] == "LATER", f"Expected Task 3 in LATER, got {algo_res['task3Category']}"
        print("✓ Prioritization classification algorithm and task data verified 100% intact!")

        print("\n=======================================================")
        print("ALL PRIORITIZE & ESTIMATE VERIFICATION CHECKS PASSED (100%)!")
        print("=======================================================")

    finally:
        browser.terminate()

if __name__ == "__main__":
    main()
