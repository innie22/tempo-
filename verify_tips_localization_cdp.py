import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os
import base64

sys.stdout.reconfigure(encoding='utf-8')

artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
os.makedirs(artifact_dir, exist_ok=True)

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_tips_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9590

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#community?tab=tips"
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

EXPECTED_VI_CARDS = [
    {
        "title": "Quy tắc bắt đầu 5 phút khi deadline khiến bạn tê liệt",
        "usage": "Cách sử dụng: Thử áp dụng khi bạn có quá nhiều việc phải làm đến mức không biết bắt đầu từ đâu."
    },
    {
        "title": "Lo lắng khi thuyết trình",
        "usage": "Cách sử dụng: Áp dụng khi bạn sắp có một buổi thuyết trình và cảm thấy lo lắng về điều đó."
    },
    {
        "title": "Xua tan sương mù tinh thần và lấy lại đà tập trung",
        "usage": "Cách sử dụng: Thử áp dụng khi sự mệt mỏi về tinh thần khiến bạn khó tập trung và ngay cả những việc đơn giản cũng trở nên khó khăn."
    },
    {
        "title": "Giảm hoảng loạn trước kỳ thi bằng kỹ thuật thở dài sinh lý",
        "usage": "Cách sử dụng: Áp dụng khi bạn đột nhiên cảm thấy hoảng loạn ngay trước hoặc trong một bài kiểm tra quan trọng."
    },
    {
        "title": "Mẫu email xin gia hạn deadline với giảng viên",
        "usage": "Cách sử dụng: Sử dụng khi bạn đang chịu áp lực lớn và cần xin gia hạn deadline bài tập một cách khẩn cấp."
    },
    {
        "title": "Thư giãn khi những suy nghĩ cứ tiếp diễn vào ban đêm",
        "usage": "Cách sử dụng: Thử áp dụng khi những lo lắng về học tập khiến bạn trằn trọc và không thể ngủ dù đã qua 2 giờ sáng."
    },
    {
        "title": "Cảm thấy bị tụt lại phía sau trong học tập",
        "usage": "Cách sử dụng: Khi bạn gặp khó khăn trong việc theo kịp bài giảng, tài liệu đọc bắt buộc hoặc các bài thực hành."
    },
    {
        "title": "Khó khăn khi làm việc nhóm",
        "usage": "Cách sử dụng: Khi khối lượng công việc không được phân chia đồng đều, thành viên nhóm thiếu phản hồi hoặc giao tiếp gặp nhiều trở ngại."
    },
    {
        "title": "Kết quả học tập không như mong đợi",
        "usage": "Cách sử dụng: Khi bạn cảm thấy thất vọng về kết quả học tập và cần tìm ra những bước tiếp theo mang tính xây dựng."
    }
]

EXPECTED_EN_CARDS = [
    {
        "title": "The 5-Minute Starter Rule for Paralyzing Deadlines",
        "usage": "Usage: Try it when you have a lot to do that makes you not want to do anything at all."
    },
    {
        "title": "Presentation anxiety",
        "usage": "Usage: Try it when you have a presentation ahead and you feel anxious about it."
    },
    {
        "title": "Brain Fog Reset & Mental Momentum",
        "usage": "Usage: Try it when mental fatigue blocks focus and simple tasks feel impossible."
    },
    {
        "title": "Exam panic & physiological sigh reset",
        "usage": "Usage: Try it when sudden panic spikes right before or during a major test."
    },
    {
        "title": "Professor extension email template",
        "usage": "Usage: Try it when severe stress requires requesting an urgent assignment extension."
    },
    {
        "title": "Racing night thoughts wind-down",
        "usage": "Usage: Try it when academic worries keep you awake well past 2 AM."
    },
    {
        "title": "Falling behind / not keeping up",
        "usage": "Usage: Struggling to keep pace with lecture material, required readings, or lab work."
    },
    {
        "title": "Teamwork problems",
        "usage": "Usage: Unbalanced workload, unresponsive group members, or communication friction."
    },
    {
        "title": "Grades didn’t go as expected",
        "usage": "Usage: Coping with academic disappointment and extracting constructive next steps."
    }
]

try:
    time.sleep(2.5)
    tabs_res = urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read().decode()
    tabs = json.loads(tabs_res)
    app_tab = next(t for t in tabs if "8000" in t.get("url", ""))

    ws = websocket.create_connection(app_tab["webSocketDebuggerUrl"], timeout=10)
    print("Connected to CDP via WebSocket.")

    send_cmd("Page.enable")
    send_cmd("DOM.enable")
    time.sleep(1.5)

    # 1. Switch to VI
    eval_js("""
    (() => {
        if (window.TempoCommunity) window.TempoCommunity.selectTab('tips');
        if (window.TempoI18n) window.TempoI18n.setLanguage('vi');
    })()
    """)
    time.sleep(1)

    print("\n================== 1. TESTING VIETNAMESE (`vi`) ==================")
    search_placeholder_vi = eval_js("document.getElementById('tips-search-input')?.getAttribute('placeholder')")
    print(f"VI Search placeholder: '{search_placeholder_vi}'")
    assert search_placeholder_vi == "Tìm kiếm...", f"Expected 'Tìm kiếm...', got '{search_placeholder_vi}'"

    cards_vi = eval_js("""
    (() => {
        const cards = [];
        document.querySelectorAll('#tips-cards-grid > div').forEach(c => {
            const title = c.querySelector('h3')?.innerText?.trim();
            const usage = c.querySelector('p')?.innerText?.replace(/\\s+/g, ' ')?.trim();
            const btn = c.querySelector('button')?.innerText?.replace(/\\s+/g, ' ')?.trim();
            cards.push({ title, usage, btn });
        });
        return cards;
    })()
    """)

    print(f"Total VI cards rendered: {len(cards_vi)}")
    assert len(cards_vi) == 9, f"Expected exactly 9 cards, got {len(cards_vi)}"

    for idx, (actual, expected) in enumerate(zip(cards_vi, EXPECTED_VI_CARDS)):
        print(f"\n--- Card {idx+1} ---")
        print(f"Title: {actual['title']}")
        print(f"Usage: {actual['usage']}")
        print(f"Button: {actual['btn']}")
        assert actual["title"] == expected["title"], f"Card {idx+1} title mismatch!\nExpected: {expected['title']}\nGot: {actual['title']}"
        assert actual["usage"] == expected["usage"], f"Card {idx+1} usage mismatch!\nExpected: {expected['usage']}\nGot: {actual['usage']}"
        assert "Xem thêm →" in actual["btn"] or actual["btn"] == "Xem thêm →", f"Card {idx+1} button mismatch: {actual['btn']}"

    capture_screenshot("community_tips_vi.png")

    print("\n================== 2. TESTING ENGLISH (`en`) ==================")
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(1)

    search_placeholder_en = eval_js("document.getElementById('tips-search-input')?.getAttribute('placeholder')")
    print(f"EN Search placeholder: '{search_placeholder_en}'")
    assert search_placeholder_en == "Search...", f"Expected 'Search...', got '{search_placeholder_en}'"

    cards_en = eval_js("""
    (() => {
        const cards = [];
        document.querySelectorAll('#tips-cards-grid > div').forEach(c => {
            const title = c.querySelector('h3')?.innerText?.trim();
            const usage = c.querySelector('p')?.innerText?.replace(/\\s+/g, ' ')?.trim();
            const btn = c.querySelector('button')?.innerText?.replace(/\\s+/g, ' ')?.trim();
            cards.push({ title, usage, btn });
        });
        return cards;
    })()
    """)

    print(f"Total EN cards rendered: {len(cards_en)}")
    assert len(cards_en) == 9, f"Expected exactly 9 cards, got {len(cards_en)}"

    for idx, (actual, expected) in enumerate(zip(cards_en, EXPECTED_EN_CARDS)):
        print(f"\n--- Card {idx+1} ---")
        print(f"Title: {actual['title']}")
        print(f"Usage: {actual['usage']}")
        print(f"Button: {actual['btn']}")
        assert actual["title"] == expected["title"], f"Card {idx+1} title mismatch!\nExpected: {expected['title']}\nGot: {actual['title']}"
        assert actual["usage"] == expected["usage"], f"Card {idx+1} usage mismatch!\nExpected: {expected['usage']}\nGot: {actual['usage']}"
        assert "See more →" in actual["btn"] or actual["btn"] == "See more →", f"Card {idx+1} button mismatch: {actual['btn']}"

    capture_screenshot("community_tips_en.png")

    print("\n================== 3. TESTING DYNAMIC SWITCHING BACK TO VIETNAMESE ==================")
    eval_js("window.TempoI18n.setLanguage('vi')")
    time.sleep(1)

    card1_title_vi = eval_js("document.querySelector('#tips-cards-grid > div h3')?.innerText?.trim()")
    print(f"Card 1 Title after switching back to VI: '{card1_title_vi}'")
    assert card1_title_vi == EXPECTED_VI_CARDS[0]["title"], "Failed to restore VI title upon switching back"

    print("\n================== 4. TESTING SEARCH FILTERING ==================")
    eval_js("""
    (() => {
        window.TempoCommunity.handleTipsSearch('thuyết trình');
    })()
    """)
    time.sleep(0.5)
    filtered_count = eval_js("document.querySelectorAll('#tips-cards-grid > div').length")
    filtered_title = eval_js("document.querySelector('#tips-cards-grid > div h3')?.innerText?.trim()")
    print(f"Search 'thuyết trình' -> count: {filtered_count}, title: '{filtered_title}'")
    assert filtered_count == 1, f"Expected 1 filtered result, got {filtered_count}"
    assert filtered_title == "Lo lắng khi thuyết trình"

    # Reset search
    eval_js("window.TempoCommunity.clearTipsSearch()")
    time.sleep(0.5)
    restored_count = eval_js("document.querySelectorAll('#tips-cards-grid > div').length")
    print(f"Restored count after clearing search: {restored_count}")
    assert restored_count == 9, f"Expected 9 cards restored, got {restored_count}"

    print("\nALL VERIFICATION TESTS COMPLETED AND PASSED 100%! 🎉")

finally:
    try:
        if ws:
            ws.close()
    except Exception:
        pass
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except Exception:
        pass
