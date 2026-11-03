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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_selfcheck_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9568

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#stress-check"
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
        res = json.loads(ws.recv())
        if res.get("id") == cmd_obj["id"]:
            return res.get("result", {})

def eval_js(expression):
    res = send_cmd("Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True
    })
    if "exceptionDetails" in res:
        print(f"JS ERROR: {res['exceptionDetails']}")
    return res.get("result", {}).get("value")

def capture_screenshot(filename):
    res = send_cmd("Page.captureScreenshot", {"format": "png"})
    if "data" in res:
        img_bytes = base64.b64decode(res["data"])
        filepath = os.path.join(artifact_dir, filename)
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        print(f"Screenshot saved: {filename}")
        return filepath

try:
    time.sleep(2)
    tabs_res = urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read().decode()
    tabs = json.loads(tabs_res)
    app_tab = next(t for t in tabs if "8000" in t.get("url", ""))

    ws = websocket.create_connection(app_tab["webSocketDebuggerUrl"], timeout=10)
    print("Connected to CDP via WebSocket.")

    send_cmd("Page.enable")
    send_cmd("DOM.enable")

    time.sleep(1)

    setup_code = """
    (async () => {
        let waitLimit = 50;
        while ((!window.TempoMode || !window.TempoSelfCheckWorkspace || !window.TempoRecoverySelfCheck) && waitLimit > 0) {
            await new Promise(r => setTimeout(r, 100));
            waitLimit--;
        }

        const u = { id: 'local_dev_alex', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
        localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }

        // Set originating mode to emergency
        if (window.TempoMode && typeof window.TempoMode.setOriginatingMode === 'function') {
            window.TempoMode.setOriginatingMode('emergency');
        }

        // Setup trackers: Tension, Sleep, Walk
        const trackersKey = `tempo_selfcheck_trackers_local_dev_alex`;
        const mockTrackers = [
            {
                id: 'trk-tension',
                user_id: 'local_dev_alex',
                name: 'Tension',
                category: 'stress_sign',
                check_method: 'percentage',
                is_active: true,
                order_index: 0
            },
            {
                id: 'trk-sleep',
                user_id: 'local_dev_alex',
                name: 'Sleep',
                category: 'supportive',
                check_method: 'yes_no',
                is_active: true,
                order_index: 1
            },
            {
                id: 'trk-walk',
                user_id: 'local_dev_alex',
                name: 'Walk',
                category: 'supportive',
                check_method: 'quantity',
                quantity_unit: 'min',
                is_active: true,
                order_index: 2
            }
        ];
        localStorage.setItem(trackersKey, JSON.stringify(mockTrackers));

        // Setup observations for this week
        const days = window.TempoSelfCheckWorkspace.getCurrentWeekDays ? window.TempoSelfCheckWorkspace.getCurrentWeekDays() : [];
        const obsKey = `tempo_selfcheck_observations_local_dev_alex`;
        const checkinsKey = `tempo_selfcheck_checkins_local_dev_alex`;

        // Create observations on mon and tue
        const monStr = days[0] ? days[0].dateStr : '2026-10-26';
        const tueStr = days[1] ? days[1].dateStr : '2026-10-27';

        const mockCheckins = [
            { id: 'chk-1', user_id: 'local_dev_alex', checkin_date: monStr },
            { id: 'chk-2', user_id: 'local_dev_alex', checkin_date: tueStr }
        ];
        localStorage.setItem(checkinsKey, JSON.stringify(mockCheckins));

        const mockObs = [
            { id: 'o-1', checkin_id: 'chk-1', tracker_id: 'trk-tension', value: 40, status: 'answered', check_method: 'percentage' },
            { id: 'o-2', checkin_id: 'chk-1', tracker_id: 'trk-sleep', value: 'good', status: 'answered', check_method: 'yes_no' },
            { id: 'o-3', checkin_id: 'chk-1', tracker_id: 'trk-walk', value: 30, status: 'answered', check_method: 'quantity' },

            { id: 'o-4', checkin_id: 'chk-2', tracker_id: 'trk-tension', value: 60, status: 'answered', check_method: 'percentage' },
            { id: 'o-5', checkin_id: 'chk-2', tracker_id: 'trk-sleep', value: 'not_good', status: 'answered', check_method: 'yes_no' },
            { id: 'o-6', checkin_id: 'chk-2', tracker_id: 'trk-walk', value: 'no', status: 'answered', check_method: 'quantity' }
        ];
        localStorage.setItem(obsKey, JSON.stringify(mockObs));

        window.TempoMode.showStressCheckScreen();
        window.TempoI18n.setLanguage('vi');
        return true;
    })();
    """
    eval_js(setup_code)
    time.sleep(1)

    # 1. Audit VI Strings
    vi_data = eval_js("""
    (() => {
        const root = document.getElementById('self-check-workspace-root');
        if (!root) return { error: 'No root found' };

        const returnBtnText = document.getElementById('selfcheck-return-home-text')?.innerText.trim();
        const returnBtnTitle = document.getElementById('btn-self-check-return-home')?.getAttribute('title');

        const dailyBadge = root.querySelector('span.uppercase')?.innerText.trim();
        const dailyTitle = root.querySelectorAll('h2')[0]?.innerText.trim();
        const ps = Array.from(root.querySelectorAll('p')).map(p => p.innerText.trim());
        const sleepQuestion = ps.find(t => t.includes('ngủ') || t.includes('sleep'));
        const streakText = ps.find(t => t.includes('Chuỗi') || t.includes('streak'));
        const statusLine = ps.find(t => t.includes('check-in') || t.includes('checked in'));

        const sleepButtons = Array.from(root.querySelectorAll('button')).map(b => b.innerText.trim());

        const walkQuestion = root.querySelector('[data-quantity-tracker-id] > p')?.innerText.trim();
        const walkLabels = Array.from(root.querySelectorAll('[data-quantity-tracker-id] label span')).map(s => s.innerText.trim());

        const noteBtn = Array.from(root.querySelectorAll('button span')).find(s => s.innerText.includes('ghi chú') || s.innerText.includes('note'))?.innerText.trim();

        // Right Column
        const trackingSystemTitle = root.querySelectorAll('h2')[1]?.innerText.trim();
        const rightHeaderButtons = Array.from(root.querySelectorAll('h2 + div button')).map(b => b.innerText.trim());

        const trackerCards = Array.from(root.querySelectorAll('[data-tracker-id]')).map(card => {
            const name = card.querySelector('h3')?.innerText.trim();
            const adjustBtn = card.querySelector('button')?.innerText.trim();
            const dayHeaders = Array.from(card.querySelectorAll('.grid-cols-7 > div > span')).map(s => s.innerText.trim());
            const dayValues = Array.from(card.querySelectorAll('.grid-cols-7 > div > div')).map(d => d.innerText.trim()).filter(Boolean);
            const metricLabel = card.querySelector('.space-y-2 .leading-snug')?.innerText.trim();
            const viewFullBtn = card.querySelector('.space-y-2 button')?.innerText.trim();
            return { name, adjustBtn, dayHeaders, dayValues, metricLabel, viewFullBtn };
        });

        // Bottom left buttons
        const bottomButtons = Array.from(root.querySelectorAll('.grid-cols-2 button')).map(b => {
            return {
                title: b.querySelector('span.font-extrabold')?.innerText.trim(),
                subtitle: b.querySelector('span.font-medium')?.innerText.trim() || null
            };
        });

        return {
            returnBtnText,
            returnBtnTitle,
            dailyBadge,
            dailyTitle,
            streakText,
            sleepQuestion,
            sleepButtons,
            walkQuestion,
            walkLabels,
            noteBtn,
            statusLine,
            trackingSystemTitle,
            rightHeaderButtons,
            trackerCards,
            bottomButtons
        };
    })()
    """)
    print("VI Data Audit:\n", json.dumps(vi_data, indent=2, ensure_ascii=False))

    # Assertions for Section 1 (Header & Daily Check-in)
    assert vi_data['returnBtnText'] == 'Quay lại Chế độ khẩn cấp', f"Expected 'Quay lại Chế độ khẩn cấp', got {vi_data['returnBtnText']}"
    assert vi_data['returnBtnTitle'] == '← Quay lại Chế độ khẩn cấp', f"Expected '← Quay lại Chế độ khẩn cấp', got {vi_data['returnBtnTitle']}"
    assert vi_data['dailyBadge'] == 'CHECK-IN HẰNG NGÀY', f"Expected 'CHECK-IN HẰNG NGÀY', got {vi_data['dailyBadge']}"
    assert vi_data['dailyTitle'] == 'Check-in hôm nay', f"Expected 'Check-in hôm nay', got {vi_data['dailyTitle']}"
    assert 'Chuỗi' in vi_data['streakText'] and 'ngày' in vi_data['streakText'], f"Expected Chuỗi X ngày, got {vi_data['streakText']}"
    assert vi_data['sleepQuestion'] == 'Bạn ngủ thế nào vào tối qua?', f"Expected 'Bạn ngủ thế nào vào tối qua?', got {vi_data['sleepQuestion']}"
    assert 'Tốt' in vi_data['sleepButtons'], f"Missing 'Tốt' in sleep buttons: {vi_data['sleepButtons']}"
    assert 'Chưa tốt' in vi_data['sleepButtons'], f"Missing 'Chưa tốt' in sleep buttons: {vi_data['sleepButtons']}"
    assert vi_data['walkQuestion'] == 'Hôm nay bạn có đi bộ không?', f"Expected 'Hôm nay bạn có đi bộ không?', got {vi_data['walkQuestion']}"
    assert 'Có' in vi_data['walkLabels'], f"Missing 'Có' in walk labels: {vi_data['walkLabels']}"
    assert 'Không' in vi_data['walkLabels'], f"Missing 'Không' in walk labels: {vi_data['walkLabels']}"
    assert vi_data['noteBtn'] == 'Tạo ghi chú hôm nay', f"Expected 'Tạo ghi chú hôm nay', got {vi_data['noteBtn']}"
    assert re.search(r'Bạn đã check-in \d+/\d+ mục hôm nay\.', vi_data['statusLine']), f"Unexpected status line: {vi_data['statusLine']}"

    # Assertions for Section 2 (Tracking System)
    assert vi_data['trackingSystemTitle'] == 'Hệ thống tracking của bạn', f"Expected 'Hệ thống tracking của bạn', got {vi_data['trackingSystemTitle']}"
    assert 'Thêm tracking' in vi_data['rightHeaderButtons'], f"Missing 'Thêm tracking': {vi_data['rightHeaderButtons']}"
    assert 'Xóa tất cả' in vi_data['rightHeaderButtons'], f"Missing 'Xóa tất cả': {vi_data['rightHeaderButtons']}"

    card_names = [c['name'] for c in vi_data['trackerCards']]
    assert 'Căng thẳng' in card_names, f"Missing 'Căng thẳng': {card_names}"
    assert 'Giấc ngủ' in card_names, f"Missing 'Giấc ngủ': {card_names}"
    assert 'Đi bộ' in card_names, f"Missing 'Đi bộ': {card_names}"

    for c in vi_data['trackerCards']:
        assert c['adjustBtn'] == 'Chỉnh sửa', f"Expected 'Chỉnh sửa', got {c['adjustBtn']}"
        assert c['viewFullBtn'] == 'Xem full-check', f"Expected 'Xem full-check', got {c['viewFullBtn']}"

    tension_card = next(c for c in vi_data['trackerCards'] if c['name'] == 'Căng thẳng')
    assert tension_card['metricLabel'] == 'Mức độ căng thẳng trung bình của bạn là', f"Unexpected tension metric: {tension_card['metricLabel']}"

    sleep_card = next(c for c in vi_data['trackerCards'] if c['name'] == 'Giấc ngủ')
    assert sleep_card['metricLabel'] == 'Số đêm ngủ ngon', f"Unexpected sleep metric: {sleep_card['metricLabel']}"

    # Assertions for Section 3 (Charts & Statistics)
    expected_vi_days = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']
    assert tension_card['dayHeaders'] == expected_vi_days, f"Expected {expected_vi_days}, got {tension_card['dayHeaders']}"

    assert 'Tốt' in sleep_card['dayValues'], f"Missing 'Tốt' in sleep day values: {sleep_card['dayValues']}"
    assert 'Chưa tốt' in sleep_card['dayValues'], f"Missing 'Chưa tốt' in sleep day values: {sleep_card['dayValues']}"

    walk_card = next(c for c in vi_data['trackerCards'] if c['name'] == 'Đi bộ')
    assert 'Không' in walk_card['dayValues'], f"Missing 'Không' in walk day values: {walk_card['dayValues']}"

    # Assertions for Section 4 (Reports & Recovery)
    assert vi_data['bottomButtons'][0]['title'] == 'Báo cáo tuần của tôi', f"Expected 'Báo cáo tuần của tôi', got {vi_data['bottomButtons'][0]['title']}"
    assert re.match(r'^\d{2}/\d{2} – \d{2}/\d{2}$', vi_data['bottomButtons'][0]['subtitle']), f"Unexpected VI date range: {vi_data['bottomButtons'][0]['subtitle']}"
    assert vi_data['bottomButtons'][1]['title'] == 'Lời nhắn phục hồi', f"Expected 'Lời nhắn phục hồi', got {vi_data['bottomButtons'][1]['title']}"

    capture_screenshot("self_check_page_vi.png")
    print("ALL VI AUDIT CHECKS PASSED PERFECTLY!")

    # 2. Switch to English on-the-fly
    eval_js("window.TempoI18n.setLanguage('en');")
    time.sleep(1)

    en_data = eval_js("""
    (() => {
        const root = document.getElementById('self-check-workspace-root');
        if (!root) return { error: 'No root found' };

        const returnBtnText = document.getElementById('selfcheck-return-home-text')?.innerText.trim();
        const returnBtnTitle = document.getElementById('btn-self-check-return-home')?.getAttribute('title');

        const dailyBadge = root.querySelector('span.uppercase')?.innerText.trim();
        const dailyTitle = root.querySelectorAll('h2')[0]?.innerText.trim();
        const ps = Array.from(root.querySelectorAll('p')).map(p => p.innerText.trim());
        const sleepQuestion = ps.find(t => t.includes('ngủ') || t.includes('sleep'));
        const streakText = ps.find(t => t.includes('Chuỗi') || t.includes('streak'));
        const statusLine = ps.find(t => t.includes('check-in') || t.includes('checked in'));

        const sleepButtons = Array.from(root.querySelectorAll('button')).map(b => b.innerText.trim());

        const walkQuestion = root.querySelector('[data-quantity-tracker-id] > p')?.innerText.trim();
        const walkLabels = Array.from(root.querySelectorAll('[data-quantity-tracker-id] label span')).map(s => s.innerText.trim());

        const noteBtn = Array.from(root.querySelectorAll('button span')).find(s => s.innerText.includes('ghi chú') || s.innerText.includes('note'))?.innerText.trim();

        // Right Column
        const trackingSystemTitle = root.querySelectorAll('h2')[1]?.innerText.trim();
        const rightHeaderButtons = Array.from(root.querySelectorAll('h2 + div button')).map(b => b.innerText.trim());

        const trackerCards = Array.from(root.querySelectorAll('[data-tracker-id]')).map(card => {
            const name = card.querySelector('h3')?.innerText.trim();
            const adjustBtn = card.querySelector('button')?.innerText.trim();
            const dayHeaders = Array.from(card.querySelectorAll('.grid-cols-7 > div > span')).map(s => s.innerText.trim());
            const dayValues = Array.from(card.querySelectorAll('.grid-cols-7 > div > div')).map(d => d.innerText.trim()).filter(Boolean);
            const metricLabel = card.querySelector('.space-y-2 .leading-snug')?.innerText.trim();
            const viewFullBtn = card.querySelector('.space-y-2 button')?.innerText.trim();
            return { name, adjustBtn, dayHeaders, dayValues, metricLabel, viewFullBtn };
        });

        // Bottom left buttons
        const bottomButtons = Array.from(root.querySelectorAll('.grid-cols-2 button')).map(b => {
            return {
                title: b.querySelector('span.font-extrabold')?.innerText.trim(),
                subtitle: b.querySelector('span.font-medium')?.innerText.trim() || null
            };
        });

        return {
            returnBtnText,
            returnBtnTitle,
            dailyBadge,
            dailyTitle,
            streakText,
            sleepQuestion,
            sleepButtons,
            walkQuestion,
            walkLabels,
            noteBtn,
            statusLine,
            trackingSystemTitle,
            rightHeaderButtons,
            trackerCards,
            bottomButtons
        };
    })()
    """)
    print("EN Data Audit:\n", json.dumps(en_data, indent=2, ensure_ascii=False))

    # Assertions for Section 1 (Header & Daily Check-in)
    assert en_data['returnBtnText'] == 'Return to Urgent Mode', f"Expected 'Return to Urgent Mode', got {en_data['returnBtnText']}"
    assert en_data['dailyBadge'] == 'YOUR DAILY CHECK-IN', f"Expected 'YOUR DAILY CHECK-IN', got {en_data['dailyBadge']}"
    assert en_data['dailyTitle'] == "Today's Check-in", f"Expected Today's Check-in, got {en_data['dailyTitle']}"
    assert '-day streak' in en_data['streakText'], f"Expected X-day streak, got {en_data['streakText']}"
    assert en_data['sleepQuestion'] == 'How was your sleep last night?', f"Expected 'How was your sleep last night?', got {en_data['sleepQuestion']}"
    assert 'Good' in en_data['sleepButtons'], f"Missing 'Good' in sleep buttons: {en_data['sleepButtons']}"
    assert 'Not good' in en_data['sleepButtons'], f"Missing 'Not good' in sleep buttons: {en_data['sleepButtons']}"
    assert en_data['walkQuestion'] == 'Did you go for a walk today?', f"Expected 'Did you go for a walk today?', got {en_data['walkQuestion']}"
    assert 'Yes' in en_data['walkLabels'], f"Missing 'Yes' in walk labels: {en_data['walkLabels']}"
    assert "No, I didn't" in en_data['walkLabels'], f"Missing \"No, I didn't\" in walk labels: {en_data['walkLabels']}"
    assert en_data['noteBtn'] == 'Create a note for today', f"Expected 'Create a note for today', got {en_data['noteBtn']}"
    assert re.search(r'You checked in on \d+ of \d+ things\.', en_data['statusLine']), f"Unexpected status line: {en_data['statusLine']}"

    # Assertions for Section 2 (Tracking System)
    assert en_data['trackingSystemTitle'] == 'Your Tracking System', f"Expected 'Your Tracking System', got {en_data['trackingSystemTitle']}"
    assert 'Add Tracking' in en_data['rightHeaderButtons'], f"Missing 'Add Tracking': {en_data['rightHeaderButtons']}"
    assert 'Clear all' in en_data['rightHeaderButtons'], f"Missing 'Clear all': {en_data['rightHeaderButtons']}"

    en_card_names = [c['name'] for c in en_data['trackerCards']]
    assert 'Tension' in en_card_names, f"Missing 'Tension': {en_card_names}"
    assert 'Sleep' in en_card_names, f"Missing 'Sleep': {en_card_names}"
    assert 'Walk' in en_card_names, f"Missing 'Walk': {en_card_names}"

    for c in en_data['trackerCards']:
        assert c['adjustBtn'] == 'Adjust', f"Expected 'Adjust', got {c['adjustBtn']}"
        assert c['viewFullBtn'] == 'View my full check', f"Expected 'View my full check', got {c['viewFullBtn']}"

    en_tension_card = next(c for c in en_data['trackerCards'] if c['name'] == 'Tension')
    assert en_tension_card['metricLabel'] == 'Your average tension level is', f"Unexpected tension metric: {en_tension_card['metricLabel']}"

    en_sleep_card = next(c for c in en_data['trackerCards'] if c['name'] == 'Sleep')
    assert en_sleep_card['metricLabel'] == 'Nights of Quality Sleep', f"Unexpected sleep metric: {en_sleep_card['metricLabel']}"

    # Assertions for Section 3 (Charts & Statistics)
    expected_en_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    assert en_tension_card['dayHeaders'] == expected_en_days, f"Expected {expected_en_days}, got {en_tension_card['dayHeaders']}"

    assert 'Good' in en_sleep_card['dayValues'], f"Missing 'Good' in sleep day values: {en_sleep_card['dayValues']}"
    assert 'Not good' in en_sleep_card['dayValues'], f"Missing 'Not good' in sleep day values: {en_sleep_card['dayValues']}"

    en_walk_card = next(c for c in en_data['trackerCards'] if c['name'] == 'Walk')
    assert 'No' in en_walk_card['dayValues'], f"Missing 'No' in walk day values: {en_walk_card['dayValues']}"

    # Assertions for Section 4 (Reports & Recovery)
    assert en_data['bottomButtons'][0]['title'] == 'My weekly report', f"Expected 'My weekly report', got {en_data['bottomButtons'][0]['title']}"
    assert re.search(r'^[A-Za-z]{3}\s+\d+\s+to\s+[A-Za-z]{3}\s+\d+$', en_data['bottomButtons'][0]['subtitle']), f"Unexpected EN date range: {en_data['bottomButtons'][0]['subtitle']}"
    assert en_data['bottomButtons'][1]['title'] == 'My Recovery notice', f"Expected 'My Recovery notice', got {en_data['bottomButtons'][1]['title']}"

    capture_screenshot("self_check_page_en.png")
    print("ALL EN AUDIT CHECKS PASSED PERFECTLY!")

    # 3. Test opening Weekly Report Modal
    eval_js("""
    (() => {
        window.TempoSelfCheckWorkspace.openWeeklyReport();
    })()
    """)
    time.sleep(0.5)
    modal_title = eval_js("""
    (() => {
        const modal = document.getElementById('modal-selfcheck-weekly-report');
        return modal ? modal.querySelector('h3')?.innerText.trim() : null;
    })()
    """)
    print("Weekly Report Modal Title (EN):", modal_title)
    assert modal_title == 'My weekly report', f"Expected 'My weekly report', got {modal_title}"

    # Close weekly report
    eval_js("window.TempoSelfCheckWorkspace.closeWeeklyReport();")

    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")

finally:
    if ws:
        ws.close()
    proc.terminate()
