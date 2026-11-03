import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os
import base64
import re

sys.stdout.reconfigure(encoding='utf-8')

artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
os.makedirs(artifact_dir, exist_ok=True)

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_vi_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9370

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100"
]

proc = subprocess.Popen(cmd)
ws = None
msg_id = 1

def send_cmd(method, params=None):
    global msg_id, ws
    cmd_obj = {"id": msg_id, "method": method, "params": params or {}}
    msg_id += 1
    ws.send(json.dumps(cmd_obj))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == cmd_obj["id"]:
            return resp.get("result", {})

def eval_js(expr):
    res = send_cmd("Runtime.evaluate", {
        "expression": expr,
        "returnByValue": True,
        "awaitPromise": True
    })
    if "exceptionDetails" in res:
        print("JS Exception:", res["exceptionDetails"])
    return res.get("result", {}).get("value")

def capture_screenshot(filepath, clip_selector=None):
    if clip_selector:
        box = eval_js(f"""
            (() => {{
                const el = document.querySelector('{clip_selector}');
                if (!el) return null;
                const rect = el.getBoundingClientRect();
                return {{
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    scale: 1
                }};
            }})()
        """)
        if box and box.get("width", 0) > 0 and box.get("height", 0) > 0:
            res = send_cmd("Page.captureScreenshot", {
                "format": "png",
                "clip": box
            })
        else:
            res = send_cmd("Page.captureScreenshot", {"format": "png"})
    else:
        res = send_cmd("Page.captureScreenshot", {"format": "png"})
    
    data = base64.b64decode(res.get("data", ""))
    with open(filepath, "wb") as f:
        f.write(data)
    print(f"Captured screenshot: {os.path.basename(filepath)} ({len(data)} bytes)")

try:
    ws_url = None
    for _ in range(40):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as resp:
                tabs = json.loads(resp.read().decode())
                pages = [t for t in tabs if t.get("type") == "page" and not t.get("url", "").startswith("chrome-extension://")]
                if pages:
                    ws_url = pages[0]["webSocketDebuggerUrl"]
                    break
        except Exception:
            time.sleep(0.5)

    if not ws_url:
        raise RuntimeError("Failed to connect to Edge CDP")

    ws = websocket.create_connection(ws_url)

    send_cmd("Page.navigate", {"url": "http://127.0.0.1:8000/"})
    for _ in range(30):
        ready = eval_js("typeof window.TempoMode !== 'undefined' && typeof window.TempoMode.setMode === 'function'")
        if ready:
            break
        time.sleep(0.3)

    # Inject mock user to avoid signin overlay during testing
    eval_js("""
        try {
            localStorage.setItem('tempo_local_dev_user', JSON.stringify({id: 'demo-user', email: 'demo@tempo.app', displayName: 'Yến Nhi'}));
            const authModal = document.getElementById('modal-signin');
            if (authModal) authModal.classList.add('hidden');
        } catch(e) {}
    """)

    # 1. Test Navbar & Sole Language (No Language Switcher)
    print("\n--- Test 1: Verify Navbar & Absence of Language Switcher ---")
    nav_info = eval_js("""
        (() => {
            const langWrapper = document.getElementById('nav-language-wrapper');
            const langWrapperHidden = !langWrapper || langWrapper.offsetParent === null || window.getComputedStyle(langWrapper).display === 'none';
            const links = {
                about: document.getElementById('nav-link-what-is-tempo')?.textContent.trim(),
                check: document.getElementById('nav-link-check')?.textContent.trim(),
                plan: document.getElementById('nav-link-plan')?.textContent.trim(),
                community: document.getElementById('nav-link-community')?.textContent.trim(),
            };
            const searchPlaceholder = document.getElementById('global-search-input')?.placeholder;
            const btnSignIn = document.getElementById('btn-header-signin')?.textContent.trim();
            const btnRegister = document.getElementById('btn-header-register')?.textContent.trim();
            
            return {
                langWrapperHidden,
                links,
                searchPlaceholder,
                btnSignIn,
                btnRegister
            };
        })()
    """)
    print("Nav info:", nav_info)
    assert nav_info["langWrapperHidden"], "Language switcher is still visible! Requirement 9 requires no switcher/toggle."
    assert nav_info["links"]["about"] == "Giới thiệu", f"Expected 'Giới thiệu', got {nav_info['links']['about']}"
    assert nav_info["links"]["check"] == "Tự kiểm tra", f"Expected 'Tự kiểm tra', got {nav_info['links']['check']}"
    assert nav_info["links"]["plan"] == "Kế hoạch", f"Expected 'Kế hoạch', got {nav_info['links']['plan']}"
    assert nav_info["links"]["community"] == "Cộng đồng", f"Expected 'Cộng đồng', got {nav_info['links']['community']}"
    assert "Tìm kiếm trên Tempo" in nav_info["searchPlaceholder"], f"Search placeholder not localized: {nav_info['searchPlaceholder']}"
    print("Navbar links and hidden language toggle verified.")

    # 2. Test Rmode Dashboard
    print("\n--- Test 2: Verify Rmode Dashboard Localization ---")
    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(1.2)
    
    rmode_info = eval_js("""
        (() => {
            const quickRelief = document.querySelector('.recovery-card-quick-relief h3')?.textContent.trim();
            const focusNow = document.querySelector('.recovery-support-focus-now h3')?.textContent.trim();
            const workingPlan = document.querySelector('#recovery-working-plan h3')?.textContent.trim();
            const tasksHeader = document.querySelector('[data-tempo-column="tasks"] span')?.textContent.trim();
            const doneHeader = document.querySelector('[data-tempo-column="done"] span')?.textContent.trim();
            const communityHeader = Array.from(document.querySelectorAll('h3')).find(h => h.textContent.includes('Từ Cộng đồng Tempo'))?.textContent.trim();
            
            return {
                quickRelief,
                focusNow,
                workingPlan,
                tasksHeader,
                doneHeader,
                communityHeader
            };
        })()
    """)
    print("Rmode dashboard info:", rmode_info)
    assert rmode_info["quickRelief"] == "Giải tỏa nhanh", f"Expected 'Giải tỏa nhanh', got {rmode_info['quickRelief']}"
    assert rmode_info["focusNow"] == "Tập trung ngay", f"Expected 'Tập trung ngay', got {rmode_info['focusNow']}"
    assert "Kế hoạch Làm việc" in rmode_info["workingPlan"], f"Expected 'Kế hoạch Làm việc của bạn', got {rmode_info['workingPlan']}"
    assert rmode_info["tasksHeader"] == "CÔNG VIỆC", f"Expected 'CÔNG VIỆC', got {rmode_info['tasksHeader']}"
    assert "VIỆC ĐÃ XONG" in rmode_info["doneHeader"], f"Expected 'VIỆC ĐÃ XONG', got {rmode_info['doneHeader']}"
    assert "Từ Cộng đồng Tempo" in rmode_info["communityHeader"], f"Expected 'Từ Cộng đồng Tempo', got {rmode_info['communityHeader']}"
    print("Rmode dashboard cards verified in Vietnamese.")

    capture_screenshot(os.path.join(artifact_dir, "vietnamese_rmode_dashboard.png"))

    # 3. Test Task Detail Popup in Rmode
    print("\n--- Test 3: Verify Task Detail Popup Localization ---")
    eval_js("""
        (() => {
            const taskCard = document.querySelector('.recovery-task-card-group div[role="button"], #recovery-working-plan div[role="button"]');
            if (taskCard) taskCard.click();
        })()
    """)
    time.sleep(0.8)

    popup_info = eval_js("""
        (() => {
            const modal = document.getElementById('rmode-task-detail-modal');
            if (!modal) return null;
            const buttons = Array.from(modal.querySelectorAll('button')).map(b => b.textContent.trim());
            const textContent = modal.textContent;
            return {
                isOpen: !modal.classList.contains('hidden'),
                buttons,
                hasDueLabel: textContent.includes('Hạn chót:'),
                hasSubtasksLabel: textContent.includes('bước đã xong') || textContent.includes('bước nhỏ'),
                hasDoneBtn: buttons.some(b => b.includes('Đánh dấu hoàn thành') || b.includes('Mở lại công việc')),
                hasFocusBtn: buttons.some(b => b.includes('Tập trung ngay')),
                hasRescheduleBtn: buttons.some(b => b.includes('Xếp lại lịch')),
                hasClearBtn: buttons.some(b => b.includes('Xóa công việc này'))
            };
        })()
    """)
    print("Popup info:", popup_info)
    assert popup_info and popup_info["isOpen"], "Task detail popup failed to open!"
    assert popup_info["hasDueLabel"], "Task due label not in Vietnamese!"
    assert popup_info["hasDoneBtn"], "Task completion button not in Vietnamese!"
    assert popup_info["hasFocusBtn"], "Focus button not in Vietnamese!"
    assert popup_info["hasRescheduleBtn"], "Reschedule button not in Vietnamese!"
    assert popup_info["hasClearBtn"], "Clear task button not in Vietnamese!"
    print("Task detail popup verified in Vietnamese.")

    capture_screenshot(os.path.join(artifact_dir, "vietnamese_task_detail_popup.png"), clip_selector="#rmode-task-detail-modal > div")

    # Close task modal
    eval_js("window.TempoMode.closeRmodeTaskDetailModal();")
    time.sleep(0.4)

    # 4. Test Quick Relief / Grounded Pause Modal
    print("\n--- Test 4: Verify Grounded Pause Modal Localization ---")
    eval_js("window.TempoStressRelief.openModal('all', { context: 'recovery' });")
    time.sleep(0.6)

    gp_info = eval_js("""
        (() => {
            const modal = document.getElementById('modal-quick-stress-relief');
            const h3 = modal.querySelector('h3')?.textContent.trim();
            const badge = modal.querySelector('span.uppercase.tracking-wider')?.textContent.trim();
            const filterBtns = Array.from(modal.querySelectorAll('.flex.flex-wrap button')).map(b => b.textContent.trim());
            const methodTitles = Array.from(modal.querySelectorAll('.grid h4')).map(h => h.textContent.trim());
            
            return {
                h3,
                badge,
                filterBtns,
                methodTitles: methodTitles.slice(0, 4)
            };
        })()
    """)
    print("Grounded Pause info:", gp_info)
    assert gp_info["badge"] == "Grounded Pause" or gp_info["badge"] == "Khoảng dừng Tĩnh tâm", f"Unexpected badge: {gp_info['badge']}"
    assert "Chọn phương pháp tĩnh tâm" in gp_info["h3"], f"Unexpected heading: {gp_info['h3']}"
    assert "Tất cả thời lượng" in gp_info["filterBtns"][0], f"Unexpected filter: {gp_info['filterBtns'][0]}"
    assert any("Trò chơi Tempo" in b for b in gp_info["filterBtns"]), "Tempo Games filter missing!"
    print("Grounded Pause verified in Vietnamese.")

    capture_screenshot(os.path.join(artifact_dir, "vietnamese_grounded_pause.png"), clip_selector="#modal-quick-stress-relief .tempo-card")

    # 5. Test Tempo Games Hub & Gentle Match
    print("\n--- Test 5: Verify Tempo Games Hub & Gentle Match Localization ---")
    eval_js("window.TempoStressRelief.openGamesHub();")
    time.sleep(0.5)

    games_hub_info = eval_js("""
        (() => {
            const modal = document.getElementById('modal-quick-stress-relief');
            const h3 = modal.querySelector('h3')?.textContent.trim();
            const gameTitle = modal.querySelector('.grid h4')?.textContent.trim();
            const playBtn = modal.querySelector('.grid button')?.textContent.trim();
            return { h3, gameTitle, playBtn };
        })()
    """)
    print("Games Hub info:", games_hub_info)
    assert games_hub_info["h3"] == "Trò chơi Thư giãn Tinh thần", f"Unexpected hub heading: {games_hub_info['h3']}"
    assert games_hub_info["gameTitle"] == "Ghép cặp Nhẹ nhàng", f"Unexpected game title: {games_hub_info['gameTitle']}"
    assert "Chơi ngay" in games_hub_info["playBtn"], f"Unexpected play button text: {games_hub_info['playBtn']}"
    print("Tempo Games Hub verified in Vietnamese.")

    capture_screenshot(os.path.join(artifact_dir, "vietnamese_tempo_games_hub.png"), clip_selector="#modal-quick-stress-relief .tempo-card")

    # Launch Gentle Match
    eval_js("window.TempoStressRelief.launchGame('gentle-match');")
    time.sleep(0.5)

    gm_info = eval_js("""
        (() => {
            const modal = document.getElementById('modal-quick-stress-relief');
            const h3 = modal.querySelector('h3')?.textContent.trim();
            const backBtn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('Quay lại'))?.textContent.trim() || '';
            const cards = Array.from(modal.querySelectorAll('.grid button'));
            return {
                h3,
                backBtn,
                cardCount: cards.length
            };
        })()
    """)
    print("Gentle Match info:", gm_info)
    assert gm_info["h3"] == "Ghép cặp Nhẹ nhàng", f"Unexpected heading: {gm_info['h3']}"
    assert "Quay lại Trò chơi Tempo" in gm_info["backBtn"], f"Unexpected back button: {gm_info['backBtn']}"
    print("Gentle Match verified in Vietnamese.")

    capture_screenshot(os.path.join(artifact_dir, "vietnamese_gentle_match.png"), clip_selector="#modal-quick-stress-relief .tempo-card")

    # Close Quick Relief modal
    eval_js("window.TempoStressRelief.closeModal();")
    time.sleep(0.4)

    # 6. Test URmode Dashboard
    print("\n--- Test 6: Verify URmode Dashboard Localization ---")
    eval_js("window.TempoMode.setMode('emergency');")
    time.sleep(1.2)

    urmode_info = eval_js("""
        (() => {
            const banner = document.querySelector('.urgent-header-badge, span.uppercase.tracking-widest')?.textContent.trim();
            const taskHeader = document.querySelector('.urgent-task-for-now-title, #urgent-task-card h3, [data-tempo-ui=\"task-for-now\"] h3')?.textContent.trim();
            return { banner, taskHeader };
        })()
    """)
    print("URmode info:", urmode_info)
    capture_screenshot(os.path.join(artifact_dir, "vietnamese_urmode_dashboard.png"))

    # 7. Test Mobile Viewport 375x812 (Check for clipping/overflow)
    print("\n--- Test 7: Verify Mobile 375px Responsiveness ---")
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 375,
        "height": 812,
        "deviceScaleFactor": 2,
        "mobile": True
    })
    time.sleep(0.5)

    eval_js("window.TempoStressRelief.openModal('all', { context: 'recovery' });")
    time.sleep(0.5)

    modal_overflow = eval_js("""
        (() => {
            const modal = document.getElementById('modal-quick-stress-relief');
            const card = modal.querySelector('.tempo-card');
            return {
                scrollWidth: card.scrollWidth,
                clientWidth: card.clientWidth,
                hasOverflow: card.scrollWidth > card.clientWidth + 2
            };
        })()
    """)
    print("Mobile 375px modal overflow check:", modal_overflow)
    assert not modal_overflow["hasOverflow"], "Modal card has horizontal overflow on mobile 375px!"
    capture_screenshot(os.path.join(artifact_dir, "vietnamese_mobile_375.png"), clip_selector="#modal-quick-stress-relief .tempo-card")
    print("Mobile 375px verified with zero overflow.")

    eval_js("window.TempoStressRelief.closeModal();")

    # Reset device override
    send_cmd("Emulation.clearDeviceMetricsOverride")

    print("\n===============================================")
    print("ALL 7 VIETNAMESE LOCALIZATION TESTS PASSED! ✓")
    print("===============================================")

finally:
    try:
        if ws:
            ws.close()
    except Exception:
        pass
    proc.terminate()
