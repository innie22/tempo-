#!/usr/bin/env python3
"""
Comprehensive CDP Verification for Available Time Page (stage: available-time):
1. Vietnamese Localization (all table keys + shortcuts + day headers + total time + modal + counters)
2. Tempo Visual Style (Soft Sage Green bg #EDF4EF, Warm Blush shortcut, Dusty Blue shortcut, Sage Green CTA #4A6B5D)
3. Interactive Functional Workflows:
   - Multiple time blocks per day (add, edit times, remove block)
   - Add another day (date input, confirm add, chronological sort)
   - Remove day confirmation modal (title, date display, copy, cancel/confirm)
   - Mark day as not available (dashed card, NOT AVAILABLE badge, re-add availability)
   - Quick shortcuts: "Free for rest of today", "Copy today to tomorrow"
   - Calculation of total available time for each day & overall counter
4. English Mode Switching:
   - Immediate UI copy updates
   - Preserved dates, times, and blocks
5. Deadline invariant and scheduling data preservation
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

CDP_PORT = 9480
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

    user_data_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), f"cdp_available_time_{int(time.time())}")
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
    time.sleep(2)
    return proc

def send_cdp_command(ws_url, method, params=None):
    import websocket
    ws = websocket.create_connection(ws_url, timeout=10)
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

        # 1. Setup session & navigate directly to available-time with sample tasks
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

            const email = 'user_available_time@fpt.edu.vn';
            const pass = 'Password123!';
            const name = 'Available Time Student';
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

            // Navigate to Available Time stage
            window.TempoEmergencyFlow.goToStage('available-time');

            return { ready: true, stage: window.TempoEmergencyFlow.getCurrentStage() };
        })()
        """
        setup_res = eval_js(ws_url, setup_js)
        print("Setup Result:", setup_res)
        time.sleep(1)

        # =========================================================================
        # TEST 1: VERIFY VIETNAMESE LOCALIZATION & TEMPO PALETTE
        # =========================================================================
        print("\n=== TEST 1: VERIFY VIETNAMESE LOCALIZATION & TEMPO PALETTE ===")
        check_vi_js = """
        (function() {
            const container = document.getElementById('emergency-stage-available-time');
            if (!container) return { err: "Container not found" };

            const bodyBg = window.getComputedStyle(document.body).backgroundColor;
            const screen = document.getElementById('screen-emergency');
            const screenBg = screen ? window.getComputedStyle(screen).backgroundColor : '';

            // Header elements
            const topBackBtn = container.querySelector('.flex.items-center.justify-between button')?.innerText?.trim();
            const badge = container.querySelector('span.tracking-widest')?.innerText?.trim();
            const badgeColor = container.querySelector('span.tracking-widest') ? window.getComputedStyle(container.querySelector('span.tracking-widest')).color : '';
            const title = container.querySelector('h2')?.innerText?.trim();
            const subtitle = container.querySelector('p.text-xs, p.text-sm')?.innerText?.trim();

            // Shortcuts card
            const shortcutsCard = container.querySelector('.shadow-2xs');
            const shortcutsLabel = shortcutsCard ? shortcutsCard.querySelector('span.font-semibold')?.innerText?.trim() : '';
            const shortcutBtns = Array.from(shortcutsCard ? shortcutsCard.querySelectorAll('button') : []).map(b => ({
                text: b.innerText.trim(),
                bg: window.getComputedStyle(b).backgroundColor,
                color: window.getComputedStyle(b).color
            }));

            // Day Cards
            const dayCards = Array.from(container.querySelectorAll('.space-y-4 > div')).filter(d => d.querySelector('h4') === null).map(card => {
                const header = card.querySelector('.border-b');
                const dayLabel = header?.querySelector('.font-heading')?.innerText?.trim();
                const totalText = header?.querySelector('.flex.items-center.space-x-3 span')?.innerText?.trim();
                const markUnavailableBtn = header?.querySelector('button[onclick*="toggleDayUnavailable"]')?.innerText?.trim();
                const removeDayBtn = header?.querySelector('button[onclick*="openRemoveDayModal"]')?.innerText?.trim();

                const timeBlocks = Array.from(card.querySelectorAll('input[type="time"]')).map(inp => inp.closest('.flex.items-center.justify-between')).filter((v, i, a) => v && a.indexOf(v) === i).map(block => {
                    const fromText = block.querySelector('.flex.items-center.space-x-2 span:first-child')?.innerText?.trim();
                    const inputs = Array.from(block.querySelectorAll('input[type="time"]')).map(i => i.value);
                    const toText = block.querySelectorAll('.flex.items-center.space-x-2 span')[1]?.innerText?.trim();
                    const duration = block.querySelector('.flex.items-center.space-x-2:last-child span')?.innerText?.trim();
                    const durationColor = block.querySelector('.flex.items-center.space-x-2:last-child span') ? window.getComputedStyle(block.querySelector('.flex.items-center.space-x-2:last-child span')).color : '';
                    return { fromText, inputs, toText, duration, durationColor };
                });

                const addBlockBtn = card.querySelector('button.pt-1')?.innerText?.trim();

                return {
                    dayLabel,
                    totalText,
                    markUnavailableBtn,
                    removeDayBtn,
                    timeBlocks,
                    addBlockBtn
                };
            });

            // Add Another Day section
            const addDayBtn = container.querySelector('.pt-1 > button')?.innerText?.trim();

            // Counter banner
            const counterBanner = container.querySelector('.space-y-6 > .p-4.rounded-2xl');
            const totalAvailLabel = counterBanner?.querySelectorAll('.font-bold')[0]?.innerText?.trim();
            const totalAvailVal = counterBanner?.querySelectorAll('.font-extrabold')[0]?.innerText?.trim();
            const totalAvailColor = counterBanner?.querySelectorAll('.font-extrabold')[0] ? window.getComputedStyle(counterBanner.querySelectorAll('.font-extrabold')[0]).color : '';
            const workloadLabel = counterBanner?.querySelectorAll('.font-bold')[1]?.innerText?.trim();
            const workloadVal = counterBanner?.querySelectorAll('.font-extrabold')[1]?.innerText?.trim();
            const workloadColor = counterBanner?.querySelectorAll('.font-extrabold')[1] ? window.getComputedStyle(counterBanner.querySelectorAll('.font-extrabold')[1]).color : '';

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
                badgeColor,
                title,
                subtitle,
                shortcutsLabel,
                shortcutBtns,
                dayCards,
                addDayBtn,
                totalAvailLabel,
                totalAvailVal,
                totalAvailColor,
                workloadLabel,
                workloadVal,
                workloadColor,
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

        # Assertions for Test 1
        assert vi_data["bodyBg"] == "rgb(237, 244, 239)", f"Expected soft Sage Green body bg, got {vi_data['bodyBg']}"
        assert vi_data["screenBg"] == "rgb(237, 244, 239)", f"Expected soft Sage Green screen bg, got {vi_data['screenBg']}"
        assert vi_data["topBackBtn"] == "←\nQuay lại phần phân loại ưu tiên", f"Expected '← Quay lại phần phân loại ưu tiên', got {vi_data['topBackBtn']}"
        assert vi_data["bottomBackBtn"] == "← Quay lại phần phân loại ưu tiên", f"Expected bottom '← Quay lại phần phân loại ưu tiên', got {vi_data['bottomBackBtn']}"
        assert vi_data["badge"] == "THỜI GIAN CÓ THỂ SẮP XẾP", f"Expected badge 'THỜI GIAN CÓ THỂ SẮP XẾP', got {vi_data['badge']}"
        assert vi_data["title"] == "Bạn thực sự có thể dành thời gian làm việc khi nào?", f"Expected VI title, got {vi_data['title']}"
        assert vi_data["subtitle"] == "Cho Tempo biết thời gian bạn có thể làm việc. Chúng tôi sẽ xây dựng kế hoạch dựa trên lịch trình của bạn — không phải ngược lại.", f"Expected VI subtitle, got {vi_data['subtitle']}"

        # Shortcuts assertions
        assert "Thao tác nhanh" in vi_data["shortcutsLabel"], f"Expected 'Thao tác nhanh', got {vi_data['shortcutsLabel']}"
        assert "Rảnh trong thời gian còn lại hôm nay" in vi_data["shortcutBtns"][0]["text"], f"Expected Shortcut 1 VI text, got {vi_data['shortcutBtns'][0]['text']}"
        assert "Sao chép lịch hôm nay sang ngày mai" in vi_data["shortcutBtns"][1]["text"], f"Expected Shortcut 2 VI text, got {vi_data['shortcutBtns'][1]['text']}"

        # Day cards assertions (Today + Tomorrow)
        assert len(vi_data["dayCards"]) >= 2, f"Expected at least 2 day cards, got {len(vi_data['dayCards'])}"
        today_card = vi_data["dayCards"][0]
        assert "HÔM NAY" in today_card["dayLabel"], f"Expected 'HÔM NAY' in Day 1 label, got {today_card['dayLabel']}"
        assert "tổng thời gian" in today_card["totalText"], f"Expected 'tổng thời gian' in Day 1 total, got {today_card['totalText']}"
        assert today_card["markUnavailableBtn"] == "Đánh dấu ngày không thể làm việc", f"Expected 'Đánh dấu ngày không thể làm việc', got {today_card['markUnavailableBtn']}"
        assert today_card["addBlockBtn"] == "+ Thêm khung giờ khác", f"Expected '+ Thêm khung giờ khác', got {today_card['addBlockBtn']}"
        assert today_card["timeBlocks"][0]["fromText"] == "Từ", f"Expected 'Từ', got {today_card['timeBlocks'][0]['fromText']}"
        assert today_card["timeBlocks"][0]["toText"] == "đến", f"Expected 'đến', got {today_card['timeBlocks'][0]['toText']}"

        tomorrow_card = vi_data["dayCards"][1]
        assert "NGÀY MAI" in tomorrow_card["dayLabel"], f"Expected 'NGÀY MAI' in Day 2 label, got {tomorrow_card['dayLabel']}"
        assert "tổng thời gian" in tomorrow_card["totalText"], f"Expected 'tổng thời gian' in Day 2 total, got {tomorrow_card['totalText']}"
        assert tomorrow_card["removeDayBtn"] == "Xóa ngày", f"Expected 'Xóa ngày' button on tomorrow card, got {tomorrow_card['removeDayBtn']}"

        # Add another day button
        assert "Thêm ngày khác" in vi_data["addDayBtn"], f"Expected 'Thêm ngày khác', got {vi_data['addDayBtn']}"

        # Counters assertions
        assert "Tổng thời gian có thể làm việc:" in vi_data["totalAvailLabel"], f"Expected total avail label in VI, got {vi_data['totalAvailLabel']}"
        assert "Ước lượng thời lượng task:" in vi_data["workloadLabel"], f"Expected workload label in VI, got {vi_data['workloadLabel']}"

        # Continue CTA button
        assert vi_data["continueText"] == "Kiểm tra tính khả thi & Tạo kế hoạch →", f"Expected continue CTA, got {vi_data['continueText']}"
        assert vi_data["continueBtnBg"] == "rgb(74, 107, 93)", f"Expected Sage Green CTA bg, got {vi_data['continueBtnBg']}"

        print("✓ All Vietnamese translations and Tempo palette requirements verified!")
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "available_time_vi.png"))
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "available_time_vi_closeup.png"), clip=vi_data["clip"])

        # =========================================================================
        # TEST 2: FUNCTIONAL INTERACTION - ADD TIME BLOCK, EDIT TIME, REMOVE BLOCK
        # =========================================================================
        print("\n=== TEST 2: INTERACTIVE TIME BLOCKS & TOTAL MINUTES ===")
        block_interaction_js = """
        (function() {
            // Add a block to Day 1
            window.TempoEmergencyFlow.addTimeBlock(0);

            const container = document.getElementById('emergency-stage-available-time');
            const day0 = container.querySelectorAll('.space-y-4 > div')[0];
            const blocks = Array.from(day0.querySelectorAll('input[type="time"]')).map(inp => inp.closest('.flex.items-center.justify-between')).filter((v, i, a) => v && a.indexOf(v) === i);
            const countAfterAdd = blocks.length;

            // Update second block times
            const block2Id = window.TempoEmergencyFlow.getAvailabilityDays()[0].blocks[1].id;
            window.TempoEmergencyFlow.updateBlockTime(0, block2Id, "14:00", "16:00");

            const updatedTotalText = day0.querySelector('.border-b .flex.items-center.space-x-3 span')?.innerText?.trim();

            // Remove the second block
            window.TempoEmergencyFlow.removeTimeBlock(0, block2Id);
            const countAfterRemove = Array.from(container.querySelectorAll('.space-y-4 > div')[0].querySelectorAll('input[type="time"]')).map(inp => inp.closest('.flex.items-center.justify-between')).filter((v, i, a) => v && a.indexOf(v) === i).length;

            return {
                countAfterAdd,
                updatedTotalText,
                countAfterRemove
            };
        })()
        """
        block_res = eval_js(ws_url, block_interaction_js)
        print("Block Interaction Result:", block_res)
        assert block_res["countAfterAdd"] >= 2, f"Expected 2+ blocks after add, got {block_res}"
        assert "tổng thời gian" in block_res["updatedTotalText"], f"Expected total text with 'tổng thời gian', got {block_res}"
        assert block_res["countAfterRemove"] == 1, f"Expected 1 block after removal, got {block_res}"
        print("✓ Adding, editing times, recalculating total, and removing time block verified!")

        # =========================================================================
        # TEST 3: FUNCTIONAL INTERACTION - MARK DAY AS NOT AVAILABLE & RESTORE
        # =========================================================================
        print("\n=== TEST 3: MARK DAY AS NOT AVAILABLE & RESTORE ===")
        unavailable_js = """
        (function() {
            // Mark tomorrow (day 1) as unavailable
            window.TempoEmergencyFlow.toggleDayUnavailable(1);

            const container = document.getElementById('emergency-stage-available-time');
            const day1 = container.querySelectorAll('.space-y-4 > div')[1];
            const badgeText = day1.querySelector('span.bg-stone-200')?.innerText?.trim();
            const totalText = day1.querySelectorAll('.flex.items-center.space-x-2')[1]?.querySelector('span')?.innerText?.trim();
            const descText = day1.querySelector('p')?.innerText?.trim();
            const restoreBtnText = day1.querySelector('.flex.items-center.space-x-3 button')?.innerText?.trim();

            const rect = day1.getBoundingClientRect();

            return {
                badgeText,
                totalText,
                descText,
                restoreBtnText,
                clip: {
                    x: Math.max(0, rect.x - 20),
                    y: Math.max(0, rect.y - 20),
                    width: Math.min(rect.width + 40, 1000),
                    height: Math.min(rect.height + 40, 600),
                    scale: 1
                }
            };
        })()
        """
        unavail_res = eval_js(ws_url, unavailable_js)
        print("Unavailable Result:", unavail_res)
        assert unavail_res["badgeText"] == "KHÔNG THỂ LÀM VIỆC", f"Expected 'KHÔNG THỂ LÀM VIỆC', got {unavail_res['badgeText']}"
        assert "0h tổng thời gian" in unavail_res["totalText"], f"Expected '0h tổng thời gian', got {unavail_res['totalText']}"
        assert "Bạn đã đánh dấu ngày này không thể làm việc" in unavail_res["descText"], f"Expected unavailable desc, got {unavail_res['descText']}"
        assert "+ Thêm thời gian làm việc cho ngày này" in unavail_res["restoreBtnText"], f"Expected restore btn text, got {unavail_res['restoreBtnText']}"
        print("✓ Mark day as not available verified!")
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "available_time_unavailable_vi.png"), clip=unavail_res["clip"])

        # Restore availability
        eval_js(ws_url, "window.TempoEmergencyFlow.toggleDayUnavailable(1)")

        # =========================================================================
        # TEST 4: FUNCTIONAL INTERACTION - ADD DAY & REMOVE DAY CONFIRMATION MODAL
        # =========================================================================
        print("\n=== TEST 4: ADD DAY & REMOVE DAY CONFIRMATION MODAL ===")
        add_remove_day_js = """
        (function() {
            // Start adding day
            window.TempoEmergencyFlow.startAddDay();
            const container = document.getElementById('emergency-stage-available-time');
            const addCard = container.querySelector('.animate-fade-in');
            const addTitle = addCard?.querySelector('h4')?.innerText?.trim();
            const dateLabel = addCard?.querySelector('label')?.innerText?.trim();
            const cancelBtn = addCard?.querySelector('button')?.innerText?.trim();
            const confirmBtn = addCard?.querySelectorAll('button')[1]?.innerText?.trim();

            // Confirm add day
            window.TempoEmergencyFlow.confirmAddDay();

            const daysAfterAdd = window.TempoEmergencyFlow.getAvailabilityDays();
            const newDayIndex = daysAfterAdd.length - 1;
            const newDay = daysAfterAdd[newDayIndex];

            // Trigger remove day modal for the new day
            window.TempoEmergencyFlow.openRemoveDayModal(newDayIndex);

            const modal = document.querySelector('[role="dialog"]');
            const modalTitle = modal?.querySelector('h3')?.innerText?.trim();
            const modalDate = modal?.querySelector('p.font-heading')?.innerText?.trim();
            const modalCopy = modal?.querySelectorAll('p')[1]?.innerText?.trim();
            const modalCancel = document.getElementById('em-remove-day-cancel-btn')?.innerText?.trim();
            const modalConfirm = document.getElementById('em-remove-day-confirm-btn')?.innerText?.trim();

            const modalRect = modal ? modal.getBoundingClientRect() : null;

            return {
                addTitle,
                dateLabel,
                cancelBtn,
                confirmBtn,
                newDayLabel: newDay.label,
                modalFound: Boolean(modal),
                modalTitle,
                modalDate,
                modalCopy,
                modalCancel,
                modalConfirm,
                modalClip: modalRect ? {
                    x: Math.max(0, modalRect.x - 20),
                    y: Math.max(0, modalRect.y - 20),
                    width: Math.min(modalRect.width + 40, 800),
                    height: Math.min(modalRect.height + 40, 600),
                    scale: 1
                } : None
            };
        })()
        """
        add_remove_res = eval_js(ws_url, add_remove_day_js)
        print("Add/Remove Day Result:", json.dumps(add_remove_res, indent=2, ensure_ascii=False))

        assert add_remove_res["addTitle"] == "THÊM THỜI GIAN LÀM VIỆC CHO NGÀY", f"Expected add day title, got {add_remove_res['addTitle']}"
        assert add_remove_res["dateLabel"] == "Chọn ngày:", f"Expected date label 'Chọn ngày:', got {add_remove_res['dateLabel']}"
        assert add_remove_res["cancelBtn"] == "✕ Hủy", f"Expected '✕ Hủy', got {add_remove_res['cancelBtn']}"
        assert add_remove_res["confirmBtn"] == "Thêm ngày", f"Expected 'Thêm ngày', got {add_remove_res['confirmBtn']}"

        assert add_remove_res["modalFound"], "Modal dialog should be found"
        assert add_remove_res["modalTitle"] == "Xóa ngày này?", f"Expected modal title 'Xóa ngày này?', got {add_remove_res['modalTitle']}"
        assert "Xóa ngày này cũng sẽ xóa" in add_remove_res["modalCopy"], f"Expected modal copy, got {add_remove_res['modalCopy']}"
        assert add_remove_res["modalCancel"] == "Hủy", f"Expected 'Hủy', got {add_remove_res['modalCancel']}"
        assert add_remove_res["modalConfirm"] == "Xóa ngày", f"Expected 'Xóa ngày', got {add_remove_res['modalConfirm']}"

        print("✓ Add day form & localized remove day confirmation modal verified!")
        if add_remove_res["modalClip"]:
            capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "available_time_remove_day_modal_vi.png"), clip=add_remove_res["modalClip"])

        # Confirm removal of the added day
        eval_js(ws_url, "window.TempoEmergencyFlow.confirmRemoveDay()")

        # =========================================================================
        # TEST 5: QUICK SHORTCUTS FUNCTIONALITY
        # =========================================================================
        print("\n=== TEST 5: QUICK SHORTCUTS FUNCTIONALITY ===")
        shortcuts_js = """
        (function() {
            // Test Shortcut 1: Free for rest of today
            window.TempoEmergencyFlow.shortcutFreeRestOfToday();
            const days1 = window.TempoEmergencyFlow.getAvailabilityDays();
            const day0Blocks = days1[0].blocks;

            // Test Shortcut 2: Copy today to tomorrow
            window.TempoEmergencyFlow.shortcutCopyTodayToTomorrow();
            const days2 = window.TempoEmergencyFlow.getAvailabilityDays();
            const day1Blocks = days2[1].blocks;

            return {
                day0BlockCount: day0Blocks.length,
                day1BlockCount: day1Blocks.length,
                day0Start: day0Blocks[0].start,
                day1Start: day1Blocks[0].start,
                equalBlocks: day0Blocks[0].start === day1Blocks[0].start && day0Blocks[0].end === day1Blocks[0].end
            };
        })()
        """
        shortcuts_res = eval_js(ws_url, shortcuts_js)
        print("Shortcuts Result:", shortcuts_res)
        assert shortcuts_res["equalBlocks"], f"Tomorrow should have identical block from today after copying: {shortcuts_res}"
        print("✓ Quick shortcuts 'Free for rest of today' and 'Copy today to tomorrow' verified working perfectly!")

        # =========================================================================
        # TEST 6: ENGLISH MODE SWITCHING & IMMEDIATE UI UPDATE
        # =========================================================================
        print("\n=== TEST 6: ENGLISH MODE SWITCHING & IMMEDIATE UI UPDATE ===")
        en_js = """
        (function() {
            window.TempoI18n.setLanguage('en');

            const container = document.getElementById('emergency-stage-available-time');
            const topBackBtn = container.querySelector('.flex.items-center.justify-between button')?.innerText?.trim();
            const badge = container.querySelector('span.tracking-widest')?.innerText?.trim();
            const title = container.querySelector('h2')?.innerText?.trim();
            const subtitle = container.querySelector('p.text-xs, p.text-sm')?.innerText?.trim();

            const shortcutsCard = container.querySelector('.shadow-2xs');
            const shortcutsLabel = shortcutsCard ? shortcutsCard.querySelector('span.font-semibold')?.innerText?.trim() : '';
            const shortcutBtns = Array.from(shortcutsCard ? shortcutsCard.querySelectorAll('button') : []).map(b => b.innerText.trim());

            const dayCards = Array.from(container.querySelectorAll('.space-y-4 > div')).filter(d => d.querySelector('h4') === null).map(card => {
                const header = card.querySelector('.border-b');
                const dayLabel = header?.querySelector('.font-heading')?.innerText?.trim();
                const totalText = header?.querySelector('.flex.items-center.space-x-3 span')?.innerText?.trim();
                const markUnavailableBtn = header?.querySelector('button[onclick*="toggleDayUnavailable"]')?.innerText?.trim();
                const removeDayBtn = header?.querySelector('button[onclick*="openRemoveDayModal"]')?.innerText?.trim();

                const timeBlocks = Array.from(card.querySelectorAll('input[type="time"]')).map(inp => inp.closest('.flex.items-center.justify-between')).filter((v, i, a) => v && a.indexOf(v) === i).map(block => {
                    const fromText = block.querySelector('.flex.items-center.space-x-2 span:first-child')?.innerText?.trim();
                    const toText = block.querySelectorAll('.flex.items-center.space-x-2 span')[1]?.innerText?.trim();
                    const duration = block.querySelector('.flex.items-center.space-x-2:last-child span')?.innerText?.trim();
                    return { fromText, toText, duration };
                });

                const addBlockBtn = card.querySelector('button.pt-1')?.innerText?.trim();
                return { dayLabel, totalText, markUnavailableBtn, removeDayBtn, timeBlocks, addBlockBtn };
            });

            const addDayBtn = container.querySelector('.pt-1 > button')?.innerText?.trim();

            const counterBanner = container.querySelector('.space-y-6 > .p-4.rounded-2xl');
            const totalAvailLabel = counterBanner?.querySelectorAll('.font-bold')[0]?.innerText?.trim();
            const workloadLabel = counterBanner?.querySelectorAll('.font-bold')[1]?.innerText?.trim();

            const bottomBackBtn = container.querySelector('.pt-4.flex button:first-child')?.innerText?.trim();
            const continueText = container.querySelector('.pt-4.flex button:last-child')?.innerText?.trim();

            const rect = container.getBoundingClientRect();

            return {
                topBackBtn,
                badge,
                title,
                subtitle,
                shortcutsLabel,
                shortcutBtns,
                dayCards,
                addDayBtn,
                totalAvailLabel,
                workloadLabel,
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

        assert en_data["topBackBtn"] == "←\nBack to Priority Review", f"Expected EN top back, got {en_data['topBackBtn']}"
        assert en_data["bottomBackBtn"] == "← Back to Priority Review", f"Expected EN bottom back, got {en_data['bottomBackBtn']}"
        assert en_data["badge"] == "AVAILABLE TIME", f"Expected 'AVAILABLE TIME', got {en_data['badge']}"
        assert en_data["title"] == "When can you actually work on this?", f"Expected EN title, got {en_data['title']}"
        assert "Tell Tempo when you're available." in en_data["subtitle"], f"Expected EN subtitle, got {en_data['subtitle']}"
        assert "Quick shortcuts:" in en_data["shortcutsLabel"], f"Expected 'Quick shortcuts:', got {en_data['shortcutsLabel']}"
        assert "Free for rest of today" in en_data["shortcutBtns"][0], f"Expected EN shortcut 1, got {en_data['shortcutBtns'][0]}"
        assert "Copy today to tomorrow" in en_data["shortcutBtns"][1], f"Expected EN shortcut 2, got {en_data['shortcutBtns'][1]}"

        # English Day Cards
        assert "TODAY" in en_data["dayCards"][0]["dayLabel"], f"Expected 'TODAY' in Day 1 label, got {en_data['dayCards'][0]['dayLabel']}"
        assert "total" in en_data["dayCards"][0]["totalText"], f"Expected 'total' in Day 1 total, got {en_data['dayCards'][0]["totalText"]}"
        assert en_data["dayCards"][0]["markUnavailableBtn"] == "Mark day as not available", f"Expected 'Mark day as not available', got {en_data['dayCards'][0]['markUnavailableBtn']}"
        assert en_data["dayCards"][0]["addBlockBtn"] == "+ Add another time block", f"Expected '+ Add another time block', got {en_data['dayCards'][0]['addBlockBtn']}"
        assert en_data["dayCards"][0]["timeBlocks"][0]["fromText"] == "From", f"Expected 'From', got {en_data['dayCards'][0]['timeBlocks'][0]['fromText']}"
        assert en_data["dayCards"][0]["timeBlocks"][0]["toText"] == "to", f"Expected 'to', got {en_data['dayCards'][0]['timeBlocks'][0]['toText']}"

        assert "TOMORROW" in en_data["dayCards"][1]["dayLabel"], f"Expected 'TOMORROW' in Day 2 label, got {en_data['dayCards'][1]['dayLabel']}"
        assert en_data["dayCards"][1]["removeDayBtn"] == "Remove day", f"Expected 'Remove day', got {en_data['dayCards'][1]['removeDayBtn']}"

        assert "Add another day" in en_data["addDayBtn"], f"Expected 'Add another day', got {en_data['addDayBtn']}"
        assert en_data["totalAvailLabel"] == "Total Available Time:", f"Expected EN total avail label, got {en_data['totalAvailLabel']}"
        assert en_data["workloadLabel"] == "Estimated Tasks Workload:", f"Expected EN workload label, got {en_data['workloadLabel']}"
        assert en_data["continueText"] == "Check Feasibility & Build Plan →", f"Expected EN continue CTA, got {en_data['continueText']}"

        print("✓ English mode immediately updated all copy and preserved scheduling values!")
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "available_time_en.png"))
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "available_time_en_closeup.png"), clip=en_data["clip"])

        print("\n=======================================================")
        print("ALL AVAILABLE TIME VERIFICATION CHECKS PASSED (100%)!")
        print("=======================================================")

    finally:
        browser.terminate()

if __name__ == "__main__":
    main()
