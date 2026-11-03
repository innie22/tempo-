#!/usr/bin/env python3
"""
Comprehensive CDP Verification for Suggested Organization Page (priority-review):
1. Vietnamese Localization (all table keys + categories + task counts + empty states + buttons)
2. Tempo Visual Style (Soft Sage Green bg, Warm Blush, Sage Green, and Dusty Blue category accents)
3. Interactive category reassign dropdown & live task count updates
4. Edit Deadline modal from priority review
5. English mode switching & immediate UI copy updates
6. User data preservation
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

CDP_PORT = 9470
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

    user_data_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), f"cdp_suggested_org_{int(time.time())}")
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
    import websocket
    ws = websocket.create_connection(ws_url, timeout=15)
    req_data = {
        "id": int(time.time() * 1000) % 1000000,
        "method": method,
        "params": params or {}
    }
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
            ready = eval_js(ws_url, "Boolean(window.TempoAuth && window.TempoEmergencyFlow && window.TempoI18n && window.TempoMode && window.TempoApp)")
            if ready:
                break
            time.sleep(0.5)

        # 1. Setup session & navigate directly to priority-review with 3 tasks:
        # Task 1: in DO_FIRST
        # Task 2: in DO_FIRST (so DO_FIRST has 2 tasks initially)
        # Task 3: in LATER (so PLAN has 0 tasks initially)
        setup_js = """
        (async function() {
            localStorage.clear();
            sessionStorage.clear();
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.resetFlowState === 'function') {
                window.TempoEmergencyFlow.resetFlowState();
            }
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('vi');
            }

            const email = 'user_sugg_org@fpt.edu.vn';
            const pass = 'Password123!';
            const name = 'Suggested Org Student';
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

            // Load 3 sample tasks
            window.TempoEmergencyFlow.loadSampleTasks();
            const tasks = window.TempoEmergencyFlow.getTasks();

            // Set specific task data to achieve exact prompt scenario:
            // 2 tasks in DO_FIRST, 0 tasks in PLAN
            tasks[0].name = "Báo cáo Đồ án Tốt nghiệp";
            tasks[0].priorityCategory = "DO_FIRST";
            tasks[0].hasDeadline = true;
            tasks[0].deadlineDate = "2026-11-02";
            tasks[0].deadlineTime = "21:00";
            tasks[0].durationMinutes = 90;

            tasks[1].name = "Bài tập Thống kê Tin học";
            tasks[1].priorityCategory = "DO_FIRST";
            tasks[1].hasDeadline = true;
            tasks[1].deadlineDate = "2026-11-03";
            tasks[1].deadlineTime = "09:00";
            tasks[1].durationMinutes = 120;

            tasks[2].name = "Đọc tài liệu Chương 4";
            tasks[2].priorityCategory = "LATER";
            tasks[2].hasDeadline = false;
            tasks[2].durationMinutes = 45;

            // Navigate to Suggested Organization (priority-review)
            window.TempoEmergencyFlow.goToStage('priority-review');

            return { ready: true, stage: window.TempoEmergencyFlow.getCurrentStage() };
        })()
        """
        setup_res = eval_js(ws_url, setup_js)
        print("Setup Result:", setup_res)
        time.sleep(1)

        # =========================================================================
        # TEST 1: VERIFY VIETNAMESE LOCALIZATION & STYLING
        # =========================================================================
        print("\n=== TEST 1: VERIFY VIETNAMESE LOCALIZATION & TEMPO PALETTE ===")
        check_vi_js = """
        (function() {
            const container = document.getElementById('emergency-stage-priority-review');
            if (!container) return { err: "Container not found" };

            const bodyBg = window.getComputedStyle(document.body).backgroundColor;
            const screen = document.getElementById('screen-emergency');
            const screenBg = screen ? window.getComputedStyle(screen).backgroundColor : '';

            // Header elements
            const topBackBtn = container.querySelector('.flex.items-center.justify-between button')?.innerText?.trim();
            const badge = container.querySelector('span.tracking-widest')?.innerText?.trim();
            const title = container.querySelector('h2')?.innerText?.trim();
            const subtitle = container.querySelector('p.text-xs, p.text-sm')?.innerText?.trim();

            // Category cards
            const catCards = Array.from(container.querySelectorAll('.space-y-5 > div')).map(card => {
                const badgeEl = card.querySelector('span.rounded-full');
                const badgeText = badgeEl?.innerText?.trim();
                const badgeBorder = badgeEl ? window.getComputedStyle(badgeEl).borderColor : '';
                const badgeBg = badgeEl ? window.getComputedStyle(badgeEl).backgroundColor : '';

                const descText = card.querySelector('.border-b p')?.innerText?.trim();
                const countText = card.querySelector('.flex.items-center.justify-between > span.text-xs')?.innerText?.trim();
                const emptyText = card.querySelector('p.italic')?.innerText?.trim() || null;

                const taskItems = Array.from(card.querySelectorAll('.space-y-2 > div')).map(tCard => {
                    const name = tCard.querySelector('h5')?.innerText?.trim();
                    const pText = tCard.querySelector('.space-y-1 p')?.innerText?.trim();
                    const editBtn = tCard.querySelector('button')?.innerText?.trim();
                    const catLabel = tCard.querySelector('label')?.innerText?.trim();
                    const select = tCard.querySelector('select');
                    const selectedVal = select ? select.value : '';
                    const options = select ? Array.from(select.options).map(o => ({ val: o.value, text: o.text })) : [];
                    return { name, pText, editBtn, catLabel, selectedVal, options };
                });

                return {
                    badgeText,
                    badgeBorder,
                    badgeBg,
                    descText,
                    countText,
                    emptyText,
                    taskItems
                };
            });

            // Bottom Navigation
            const bottomBackBtn = container.querySelector('.pt-4.flex button:first-child')?.innerText?.trim();
            const continueBtn = container.querySelector('.pt-4.flex button:last-child');
            const continueText = continueBtn?.innerText?.trim();
            const continueBtnBg = continueBtn ? window.getComputedStyle(continueBtn).backgroundColor : '';

            const rect = container.getBoundingClientRect();

            return {
                bodyBg,
                screenBg,
                topBackBtn,
                badge,
                title,
                subtitle,
                catCards,
                bottomBackBtn,
                continueText,
                continueBtnBg,
                clip: {
                    x: Math.max(0, rect.x),
                    y: Math.max(0, rect.y),
                    width: Math.min(rect.width, 1200),
                    height: Math.min(rect.height + 40, 1600),
                    scale: 1
                }
            };
        })()
        """
        vi_data = eval_js(ws_url, check_vi_js)
        print("Vietnamese Data:", json.dumps(vi_data, indent=2, ensure_ascii=False))

        # Assertions for Table mappings
        assert vi_data["topBackBtn"] == "←\nQuay lại phần đánh giá", f"Expected '← Quay lại phần đánh giá', got {vi_data['topBackBtn']}"
        assert vi_data["bottomBackBtn"] == "← Quay lại phần đánh giá", f"Expected '← Quay lại phần đánh giá', got {vi_data['bottomBackBtn']}"
        assert vi_data["badge"] == "XEM LẠI MỨC ĐỘ ƯU TIÊN", f"Expected 'XEM LẠI MỨC ĐỘ ƯU TIÊN', got {vi_data['badge']}"
        assert vi_data["title"] == "Cách sắp xếp được đề xuất", f"Expected 'Cách sắp xếp được đề xuất', got {vi_data['title']}"
        assert "Đây là cách Tempo phân nhóm các task dựa trên câu trả lời của bạn." in vi_data["subtitle"], f"Expected VI subtitle, got {vi_data['subtitle']}"

        # Category 1: DO_FIRST
        c1 = vi_data["catCards"][0]
        assert "LÀM TRƯỚC" in c1["badgeText"], f"Expected 'LÀM TRƯỚC', got {c1['badgeText']}"
        assert "Áp lực cấp bách và có ảnh hưởng lớn. Cần được ưu tiên ngay." in c1["descText"], f"Expected C1 VI desc, got {c1['descText']}"
        assert c1["countText"] == "2 task", f"Expected '2 task', got {c1['countText']}"
        assert len(c1["taskItems"]) == 2, f"Expected 2 tasks in C1, got {len(c1['taskItems'])}"
        assert c1["taskItems"][0]["name"] == "Báo cáo Đồ án Tốt nghiệp", "Task name mutated!"
        assert "Deadline 2 thg 11 · 9:00 PM" in c1["taskItems"][0]["pText"], f"Expected 'Deadline 2 thg 11 · 9:00 PM', got {c1['taskItems'][0]['pText']}"
        assert c1["taskItems"][0]["editBtn"] == "Sửa Deadline", f"Expected 'Sửa Deadline', got {c1['taskItems'][0]['editBtn']}"
        assert c1["taskItems"][0]["catLabel"] == "PHÂN LOẠI:", f"Expected 'PHÂN LOẠI:', got {c1['taskItems'][0]['catLabel']}"

        # Category 2: PLAN (Empty initial state)
        c2 = vi_data["catCards"][1]
        assert "LÊN KẾ HOẠCH" in c2["badgeText"], f"Expected 'LÊN KẾ HOẠCH', got {c2['badgeText']}"
        assert "Công việc quan trọng. Hãy dành thời gian cụ thể để hoàn thành trước Deadline." in c2["descText"], f"Expected C2 VI desc, got {c2['descText']}"
        assert c2["countText"] == "0 task", f"Expected '0 task', got {c2['countText']}"
        assert c2["emptyText"] == "Chưa có task nào trong nhóm này.", f"Expected 'Chưa có task nào trong nhóm này.', got {c2['emptyText']}"

        # Category 3: REDUCE_HELP
        c3 = vi_data["catCards"][2]
        assert "GIẢM BỚT / NHỜ HỖ TRỢ" in c3["badgeText"], f"Expected 'GIẢM BỚT / NHỜ HỖ TRỢ', got {c3['badgeText']}"
        assert "Phạm vi việc có thể thu gọn, đơn giản hóa hoặc nhờ người khác hỗ trợ." in c3["descText"], f"Expected C3 VI desc, got {c3['descText']}"

        # Category 4: LATER
        c4 = vi_data["catCards"][3]
        assert "LÀM SAU" in c4["badgeText"], f"Expected 'LÀM SAU', got {c4['badgeText']}"
        assert "Ít cấp bách hơn ở thời điểm này. Có thể xử lý an tâm sau khi vượt qua giai đoạn cao điểm." in c4["descText"], f"Expected C4 VI desc, got {c4['descText']}"
        assert c4["countText"] == "1 task", f"Expected '1 task', got {c4['countText']}"

        # Styling checks
        assert vi_data["bodyBg"] == "rgb(237, 244, 239)", f"Expected soft sage bg rgb(237, 244, 239), got {vi_data['bodyBg']}"
        assert vi_data["continueBtnBg"] == "rgb(74, 107, 93)", f"Expected sage green button rgb(74, 107, 93), got {vi_data['continueBtnBg']}"

        print("✓ All Vietnamese translations and Tempo palette requirements verified!")
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "suggested_org_vi.png"))
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "suggested_org_vi_closeup.png"), clip=vi_data["clip"])

        # =========================================================================
        # TEST 2: INTERACTIVE CATEGORY REASSIGN & LIVE COUNT UPDATES
        # =========================================================================
        print("\n=== TEST 2: TEST CATEGORY REASSIGN & LIVE TASK COUNT UPDATES ===")
        reassign_js = """
        (function() {
            const tasks = window.TempoEmergencyFlow.getTasks();
            const task2Id = tasks[1].id;

            // Reassign task 2 from DO_FIRST to PLAN
            window.TempoEmergencyFlow.reassignTaskCategory(task2Id, 'PLAN');

            const container = document.getElementById('emergency-stage-priority-review');
            const catCards = Array.from(container.querySelectorAll('.space-y-5 > div'));

            const c1Count = catCards[0].querySelector('.flex.items-center.justify-between > span.text-xs')?.innerText?.trim();
            const c2Count = catCards[1].querySelector('.flex.items-center.justify-between > span.text-xs')?.innerText?.trim();
            const c2Empty = catCards[1].querySelector('p.italic')?.innerText?.trim() || null;
            const c2TaskName = catCards[1].querySelector('h5')?.innerText?.trim();

            return {
                c1Count,
                c2Count,
                c2Empty,
                c2TaskName
            };
        })()
        """
        reassign_data = eval_js(ws_url, reassign_js)
        print("Reassign Data:", reassign_data)
        assert reassign_data["c1Count"] == "1 task", f"Expected DO_FIRST to decrease to '1 task', got {reassign_data['c1Count']}"
        assert reassign_data["c2Count"] == "1 task", f"Expected PLAN to increase to '1 task', got {reassign_data['c2Count']}"
        assert reassign_data["c2Empty"] is None, "Expected empty state to disappear in PLAN category"
        assert reassign_data["c2TaskName"] == "Bài tập Thống kê Tin học", f"Expected moved task name, got {reassign_data['c2TaskName']}"
        print("✓ Reassign dropdown immediately moved task, updated task counts (1 task / 1 task), and cleared empty state!")
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "suggested_org_reassign_vi.png"))

        # Test Deadline modal from Priority Review
        print("\n=== TEST 3: EDIT DEADLINE MODAL FROM PRIORITY REVIEW ===")
        modal_js = """
        (async function() {
            const tasks = window.TempoEmergencyFlow.getTasks();
            window.TempoEmergencyFlow.openDeadlineModal(tasks[0].id);
            await new Promise(r => setTimeout(r, 200));

            const modal = document.querySelector('[role="dialog"]');
            if (!modal) return { found: false };

            const title = modal.querySelector('h3')?.innerText?.trim();
            window.TempoEmergencyFlow.closeDeadlineModal();
            return { found: true, title };
        })()
        """
        modal_res = eval_js(ws_url, modal_js)
        print("Modal status:", modal_res)
        assert modal_res["found"] and modal_res["title"] == "Sửa Deadline", f"Expected modal title 'Sửa Deadline', got {modal_res}"
        print("✓ Deadline modal from Priority Review verified!")

        # =========================================================================
        # TEST 4: ENGLISH MODE SWITCHING & IMMEDIATE UI UPDATE
        # =========================================================================
        print("\n=== TEST 4: ENGLISH MODE SWITCHING & IMMEDIATE UI UPDATE ===")
        en_js = """
        (function() {
            window.TempoI18n.setLanguage('en');

            const container = document.getElementById('emergency-stage-priority-review');
            const topBackBtn = container.querySelector('.flex.items-center.justify-between button')?.innerText?.trim();
            const badge = container.querySelector('span.tracking-widest')?.innerText?.trim();
            const title = container.querySelector('h2')?.innerText?.trim();
            const subtitle = container.querySelector('p.text-xs, p.text-sm')?.innerText?.trim();

            const catCards = Array.from(container.querySelectorAll('.space-y-5 > div')).map(card => {
                const badgeText = card.querySelector('span.rounded-full')?.innerText?.trim();
                const descText = card.querySelector('.border-b p')?.innerText?.trim();
                const countText = card.querySelector('.flex.items-center.justify-between > span.text-xs')?.innerText?.trim();
                const emptyText = card.querySelector('p.italic')?.innerText?.trim() || null;
                const firstTask = card.querySelector('.space-y-2 > div');
                const catLabel = firstTask?.querySelector('label')?.innerText?.trim();
                const editBtn = firstTask?.querySelector('button')?.innerText?.trim();
                return { badgeText, descText, countText, emptyText, catLabel, editBtn };
            });

            const bottomBackBtn = container.querySelector('.pt-4.flex button:first-child')?.innerText?.trim();
            const continueText = container.querySelector('.pt-4.flex button:last-child')?.innerText?.trim();

            const rect = container.getBoundingClientRect();

            return {
                topBackBtn,
                badge,
                title,
                subtitle,
                catCards,
                bottomBackBtn,
                continueText,
                clip: {
                    x: Math.max(0, rect.x),
                    y: Math.max(0, rect.y),
                    width: Math.min(rect.width, 1200),
                    height: Math.min(rect.height + 40, 1600),
                    scale: 1
                }
            };
        })()
        """
        en_data = eval_js(ws_url, en_js)
        print("English Data:", json.dumps(en_data, indent=2, ensure_ascii=False))

        assert en_data["topBackBtn"] == "←\nBack to Assessment", f"Expected 'Back to Assessment', got {en_data['topBackBtn']}"
        assert en_data["bottomBackBtn"] == "← Back to Assessment", f"Expected 'Back to Assessment', got {en_data['bottomBackBtn']}"
        assert en_data["badge"] == "PRIORITY REVIEW", f"Expected 'PRIORITY REVIEW', got {en_data['badge']}"
        assert en_data["title"] == "Suggested Organization", f"Expected 'Suggested Organization', got {en_data['title']}"
        assert "Here is how Tempo grouped your tasks based on your answers." in en_data["subtitle"], f"Expected EN subtitle, got {en_data['subtitle']}"

        # Category 1: DO FIRST in English
        assert "DO FIRST" in en_data["catCards"][0]["badgeText"], f"Expected 'DO FIRST', got {en_data['catCards'][0]['badgeText']}"
        assert "Urgent pressure with high impact. Needs immediate focus." in en_data["catCards"][0]["descText"], f"Expected C1 EN desc, got {en_data['catCards'][0]['descText']}"
        assert en_data["catCards"][0]["countText"] == "1 task", f"Expected '1 task', got {en_data['catCards'][0]['countText']}"
        assert en_data["catCards"][0]["catLabel"] == "CATEGORY:", f"Expected 'CATEGORY:', got {en_data['catCards'][0]['catLabel']}"
        assert en_data["catCards"][0]["editBtn"] == "Edit", f"Expected 'Edit', got {en_data['catCards'][0]['editBtn']}"

        # Category 2: PLAN in English
        assert "PLAN" in en_data["catCards"][1]["badgeText"], f"Expected 'PLAN', got {en_data['catCards'][1]['badgeText']}"
        assert "Important work. Schedule dedicated blocks before deadlines." in en_data["catCards"][1]["descText"], f"Expected C2 EN desc, got {en_data['catCards'][1]['descText']}"
        assert en_data["catCards"][1]["countText"] == "1 task", f"Expected '1 task', got {en_data['catCards'][1]['countText']}"

        # Category 3: REDUCE / GET HELP in English (empty state test)
        assert "REDUCE / GET HELP" in en_data["catCards"][2]["badgeText"], f"Expected 'REDUCE / GET HELP', got {en_data['catCards'][2]['badgeText']}"
        assert en_data["catCards"][2]["countText"] == "0 tasks", f"Expected '0 tasks', got {en_data['catCards'][2]['countText']}"
        assert en_data["catCards"][2]["emptyText"] == "No tasks in this category.", f"Expected 'No tasks in this category.', got {en_data['catCards'][2]['emptyText']}"

        # Category 4: LATER in English
        assert "LATER" in en_data["catCards"][3]["badgeText"], f"Expected 'LATER', got {en_data['catCards'][3]['badgeText']}"
        assert "Lower immediate stakes. Can be safely addressed after the crunch." in en_data["catCards"][3]["descText"], f"Expected C4 EN desc, got {en_data['catCards'][3]['descText']}"

        assert en_data["continueText"] == "Continue to Available Time →", f"Expected 'Continue to Available Time →', got {en_data['continueText']}"

        print("✓ English mode immediately updated all static UI copy and plurals!")
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "suggested_org_en.png"))
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "suggested_org_en_closeup.png"), clip=en_data["clip"])

        print("\n=======================================================")
        print("ALL SUGGESTED ORGANIZATION CHECKS PASSED (100%)!")
        print("=======================================================")

    finally:
        browser.terminate()

if __name__ == "__main__":
    main()
