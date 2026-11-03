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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_tips_full_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9600

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

EXPECTED_19_EN = [
    ("The 5-Minute Starter Rule for Paralyzing Deadlines", "Usage: Try it when you have a lot to do that makes you not want to do anything at all"),
    ("Presentation anxiety", "Usage: Try it when you have a presentation ahead and you feel anxious about it"),
    ("Brain Fog Reset & Mental Momentum", "Usage: Try it when mental fatigue blocks focus and simple tasks feel impossible"),
    ("Exam panic & physiological sigh reset", "Usage: Try it when sudden panic spikes right before or during a major test"),
    ("Professor extension email template", "Usage: Try it when severe stress requires requesting an urgent assignment extension"),
    ("Racing night thoughts wind-down", "Usage: Try it when academic worries keep you awake well past 2 AM"),
    ("Falling behind / not keeping up", "Usage: Struggling to keep pace with lecture material, required readings, or lab work."),
    ("Teamwork problems", "Usage: Unbalanced workload, unresponsive group members, or communication friction."),
    ("Grades didn’t go as expected", "Usage: Coping with academic disappointment and extracting constructive next steps."),
    ("Presentation anxiety", "Usage: Intense nervousness, racing heartbeat, or dread before speaking in class or giving a presentation."),
    ("Can’t focus / can’t get started", "Usage: Staring at a blank screen, experiencing brain fog, or feeling frozen when trying to begin study tasks."),
    ("Unsure about direction / future", "Usage: Worrying about career choices, major selection, or feeling aimless compared to peers."),
    ("Feeling \"not good enough\"", "Usage: Persistent self-doubt, imposter syndrome, and feeling like everyone else understands while you don't."),
    ("Pressure from expectations of myself", "Usage: Perfectionism, harsh internal standards, and fear of making mistakes in coursework."),
    ("Comparing myself with other people", "Usage: Feeling inadequate when observing peers’ internships, study pace, or social achievements."),
    ("Too many responsibilities at once", "Usage: Overloaded with study, part-time jobs, student clubs, and family commitments simultaneously."),
    ("Conflict with someone important", "Usage: Friction with a roommate, partner, friend, or family member impacting your ability to study."),
    ("Loneliness / feeling disconnected", "Usage: Feeling isolated on campus, lacking belonging, or having nobody to confide in during tough weeks."),
    ("Daily routine has been disrupted for a while", "Usage: Sleep schedule inverted, meals irregular, and everyday habits eroded by ongoing stress.")
]

EXPECTED_19_VI = [
    ("Quy tắc bắt đầu 5 phút khi deadline khiến bạn tê liệt", "Cách sử dụng: Thử áp dụng khi bạn có quá nhiều việc phải làm đến mức không biết bắt đầu từ đâu."),
    ("Lo lắng khi thuyết trình", "Cách sử dụng: Áp dụng khi bạn sắp có một buổi thuyết trình và cảm thấy lo lắng về điều đó."),
    ("Xua tan sương mù tinh thần và lấy lại đà tập trung", "Cách sử dụng: Thử áp dụng khi sự mệt mỏi về tinh thần khiến bạn khó tập trung và ngay cả những việc đơn giản cũng trở nên khó khăn."),
    ("Giảm hoảng loạn trước kỳ thi bằng kỹ thuật thở dài sinh lý", "Cách sử dụng: Áp dụng khi bạn đột nhiên cảm thấy hoảng loạn ngay trước hoặc trong một bài kiểm tra quan trọng."),
    ("Mẫu email xin gia hạn deadline với giảng viên", "Cách sử dụng: Sử dụng khi bạn đang chịu áp lực lớn và cần xin gia hạn deadline bài tập một cách khẩn cấp."),
    ("Thư giãn khi những suy nghĩ cứ tiếp diễn vào ban đêm", "Cách sử dụng: Thử áp dụng khi những lo lắng về học tập khiến bạn trằn trọc và không thể ngủ dù đã qua 2 giờ sáng."),
    ("Cảm thấy bị tụt lại phía sau trong học tập", "Cách sử dụng: Khi bạn gặp khó khăn trong việc theo kịp bài giảng, tài liệu đọc bắt buộc hoặc các bài thực hành."),
    ("Khó khăn khi làm việc nhóm", "Cách sử dụng: Khi khối lượng công việc không được phân chia đồng đều, thành viên nhóm thiếu phản hồi hoặc giao tiếp gặp nhiều trở ngại."),
    ("Kết quả học tập không như mong đợi", "Cách sử dụng: Khi bạn cảm thấy thất vọng về kết quả học tập và cần tìm ra những bước tiếp theo mang tính xây dựng."),
    ("Lo lắng khi thuyết trình", "Cách sử dụng: Cảm giác hồi hộp tột độ, tim đập nhanh hoặc lo sợ trước khi phát biểu trước lớp hoặc thuyết trình."),
    ("Không thể tập trung / khó bắt đầu", "Cách sử dụng: Nhìn vào màn hình trống rỗng, cảm giác sương mù tinh thần hoặc bị tê liệt khi cố gắng bắt đầu học tập."),
    ("Mơ hồ về định hướng / tương lai", "Cách sử dụng: Lo lắng về lựa chọn nghề nghiệp, chọn ngành hoặc cảm thấy mất phương hướng so với bạn bè đồng trang lứa."),
    ("Cảm giác \"mình chưa đủ tốt\"", "Cách sử dụng: Tự nghi ngờ bản thân kéo dài, hội chứng kẻ mạo danh và cảm thấy mọi người xung quanh đều hiểu bài trừ mình."),
    ("Áp lực từ kỳ vọng của bản thân", "Cách sử dụng: Chủ nghĩa hoàn hảo, tiêu chuẩn nội tâm khắt khe và nỗi sợ mắc lỗi trong quá trình học tập."),
    ("So sánh bản thân với người khác", "Cách sử dụng: Cảm thấy kém cỏi khi nhìn vào kỳ thực tập, tiến độ học tập hoặc thành tích xã hội của bạn bè."),
    ("Quá nhiều trách nhiệm cùng một lúc", "Cách sử dụng: Bị quá tải với việc học, công việc làm thêm, câu lạc bộ và các trách nhiệm gia đình diễn ra cùng lúc."),
    ("Xung đột với người quan trọng", "Cách sử dụng: Mâu thuẫn với bạn cùng phòng, người yêu, bạn bè hoặc người thân ảnh hưởng đến khả năng học tập của bạn."),
    ("Cô đơn / cảm giác mất kết nối", "Cách sử dụng: Cảm thấy bị cô lập trong trường học, thiếu cảm giác thuộc về nơi này hoặc không có ai để tâm sự trong những tuần khó khăn."),
    ("Lối sống hằng ngày bị xáo trộn kéo dài", "Cách sử dụng: Lịch ngủ bị đảo lộn, ăn uống thất thường và các thói quen hằng ngày bị xói mòn bởi căng thẳng liên miên.")
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

    print("\n================== 1. VERIFYING VIETNAMESE FULL DATASET (`vi`) ==================")
    search_placeholder_vi = eval_js("document.getElementById('tips-search-input')?.getAttribute('placeholder')")
    print(f"VI Search placeholder: '{search_placeholder_vi}'")
    assert search_placeholder_vi == "Tìm kiếm...", f"Expected 'Tìm kiếm...', got '{search_placeholder_vi}'"

    cards_vi = eval_js("""
    (() => {
        const cards = [];
        document.querySelectorAll('#tips-cards-grid > div').forEach(c => {
            const id = c.getAttribute('data-tip-id');
            const title = c.querySelector('h3')?.innerText?.trim();
            const usage = c.querySelector('p')?.innerText?.replace(/\\s+/g, ' ')?.trim();
            const btn = c.querySelector('button')?.innerText?.replace(/\\s+/g, ' ')?.trim();
            cards.push({ id, title, usage, btn });
        });
        return cards;
    })()
    """)

    print(f"Total VI cards rendered: {len(cards_vi)}")
    assert len(cards_vi) == 19, f"Expected exactly 19 cards, got {len(cards_vi)}"

    for idx, (actual, (expected_title, expected_usage)) in enumerate(zip(cards_vi, EXPECTED_19_VI)):
        print(f"Card {idx+1}: [{actual['id']}] {actual['title']}")
        assert actual["title"] == expected_title, f"Card {idx+1} title mismatch!\nExpected: {expected_title}\nGot: {actual['title']}"
        assert actual["usage"] == expected_usage, f"Card {idx+1} usage mismatch!\nExpected: {expected_usage}\nGot: {actual['usage']}"
        assert actual["btn"] == "Xem thêm →", f"Card {idx+1} button mismatch: {actual['btn']}"

    capture_screenshot("community_tips_full_dataset_vi.png")

    print("\n================== 2. VERIFYING ENGLISH FULL DATASET (`en`) ==================")
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(1)

    search_placeholder_en = eval_js("document.getElementById('tips-search-input')?.getAttribute('placeholder')")
    print(f"EN Search placeholder: '{search_placeholder_en}'")
    assert search_placeholder_en == "Search...", f"Expected 'Search...', got '{search_placeholder_en}'"

    cards_en = eval_js("""
    (() => {
        const cards = [];
        document.querySelectorAll('#tips-cards-grid > div').forEach(c => {
            const id = c.getAttribute('data-tip-id');
            const title = c.querySelector('h3')?.innerText?.trim();
            const usage = c.querySelector('p')?.innerText?.replace(/\\s+/g, ' ')?.trim();
            const btn = c.querySelector('button')?.innerText?.replace(/\\s+/g, ' ')?.trim();
            cards.push({ id, title, usage, btn });
        });
        return cards;
    })()
    """)

    print(f"Total EN cards rendered: {len(cards_en)}")
    assert len(cards_en) == 19, f"Expected exactly 19 cards, got {len(cards_en)}"

    for idx, (actual, (expected_title, expected_usage)) in enumerate(zip(cards_en, EXPECTED_19_EN)):
        print(f"Card {idx+1}: [{actual['id']}] {actual['title']}")
        assert actual["title"] == expected_title, f"Card {idx+1} title mismatch!\nExpected: {expected_title}\nGot: {actual['title']}"
        assert actual["usage"] == expected_usage, f"Card {idx+1} usage mismatch!\nExpected: {expected_usage}\nGot: {actual['usage']}"
        assert actual["btn"] == "See more →", f"Card {idx+1} button mismatch: {actual['btn']}"

    capture_screenshot("community_tips_full_dataset_en.png")

    print("\n================== 3. VERIFYING MODAL OPEN INTERACTION ==================")
    # Click card 7 (falling_behind)
    eval_js("window.TempoCommunity.openTipDetail('falling_behind')")
    time.sleep(0.5)
    modal_visible = eval_js("!document.getElementById('tempo-learn-solve-modal')?.classList.contains('hidden')")
    print(f"Modal opened for 'falling_behind': {modal_visible}")
    assert modal_visible, "Expected modal to open on openTipDetail"
    # Close modal
    eval_js("window.TempoLearnSolve?.closeModal()")
    time.sleep(0.5)

    print("\nALL 19 CARDS & FULL DATASET VERIFICATION PASSED 100%! 🎉")

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
