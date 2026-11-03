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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_learn_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9615

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#community?tab=learn"
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
        print("JS Exception:", res["exceptionDetails"])
    return res.get("result", {}).get("value")

def capture_screenshot(path):
    res = send_cmd("Page.captureScreenshot", {"format": "png"})
    data = base64.b64decode(res.get("data", ""))
    with open(path, "wb") as f:
        f.write(data)
    print(f"Captured screenshot: {path}")

try:
    for _ in range(30):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as f:
                targets = json.load(f)
                page_target = next((t for t in targets if t.get("type") == "page"), None)
                if page_target and page_target.get("webSocketDebuggerUrl"):
                    ws = websocket.create_connection(page_target["webSocketDebuggerUrl"])
                    break
        except Exception:
            time.sleep(0.5)

    if not ws:
        raise RuntimeError("Could not connect to Edge DevTools")

    send_cmd("Page.enable")
    send_cmd("Runtime.enable")
    time.sleep(2)

    # Navigate to community learn view and set VI
    eval_js("""
        (() => {
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('community');
            }
            if (window.TempoCommunity && typeof window.TempoCommunity.selectTab === 'function') {
                window.TempoCommunity.selectTab('learn');
            }
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('vi');
            }
        })()
    """)
    time.sleep(1.5)

    print("--- 1. AUDITING VIETNAMESE LEARN FEED ---")
    back_label_vi = eval_js("document.getElementById('community-back-label')?.innerText?.trim()")
    back_btn_full_vi = eval_js("document.getElementById('btn-community-back')?.innerText?.replace(/\\s+/g, ' ')?.trim()")
    back_btn_title_vi = eval_js("document.getElementById('btn-community-back')?.getAttribute('title')")
    print(f"Back Label (VI): '{back_label_vi}' | Full: '{back_btn_full_vi}' | Title: '{back_btn_title_vi}'")
    assert back_label_vi == "Quay lại Dashboard", f"Expected 'Quay lại Dashboard', got: {back_label_vi}"
    assert "Quay lại Dashboard" in back_btn_full_vi, f"Expected 'Quay lại Dashboard' in button, got: {back_btn_full_vi}"

    search_ph_vi = eval_js("document.getElementById('learn-search-input')?.placeholder")
    print(f"Search placeholder (VI): '{search_ph_vi}'")
    assert search_ph_vi == "Tìm kiếm...", f"Expected 'Tìm kiếm...', got: {search_ph_vi}"

    sidebar_tabs_vi = eval_js("""
        (() => {
            const tabs = {};
            document.querySelectorAll('#community-sidebar-nav .community-nav-item').forEach(b => {
                tabs[b.getAttribute('data-community-tab')] = b.innerText.trim();
            });
            return tabs;
        })()
    """)
    print(f"Sidebar Desktop Tabs (VI): {sidebar_tabs_vi}")
    assert sidebar_tabs_vi.get("announcement") == "Thông báo", f"Announcement mismatch: {sidebar_tabs_vi}"
    assert sidebar_tabs_vi.get("tips") == "Tips", f"Tips mismatch: {sidebar_tabs_vi}"
    assert sidebar_tabs_vi.get("learn") == "Kiến thức", f"Learn mismatch: {sidebar_tabs_vi}"
    assert sidebar_tabs_vi.get("posts") == "Bài viết", f"Posts mismatch: {sidebar_tabs_vi}"
    assert sidebar_tabs_vi.get("messages") == "Tin nhắn riêng", f"Messages mismatch: {sidebar_tabs_vi}"

    cards_vi = eval_js("""
        Array.from(document.querySelectorAll('#learn-cards-grid > div')).map(el => ({
            id: el.getAttribute('data-learn-id'),
            title: el.querySelector('h3')?.innerText.trim(),
            summary: el.querySelector('p')?.innerText.trim(),
            btn: el.querySelector('button')?.innerText.trim().replace(/\\s+/g, ' ')
        }))
    """)
    print(f"Found {len(cards_vi)} Learn cards in VI:")
    for c in cards_vi:
        print(f"  - [{c['id']}] {c['title']} | Btn: '{c['btn']}'")
        print(f"    Summary: {c['summary'][:70]}...")

    assert len(cards_vi) == 3, f"Expected 3 cards, got {len(cards_vi)}"
    assert cards_vi[0]['title'] == 'Stress là gì?', f"Expected 'Stress là gì?', got: {cards_vi[0]['title']}"
    assert "Căng thẳng là trạng thái lo lắng" in cards_vi[0]['summary'], "Summary 1 mismatch"
    assert "Xem thêm →" in cards_vi[0]['btn'], f"Expected 'Xem thêm →', got {cards_vi[0]['btn']}"

    assert cards_vi[1]['title'] == 'Ăn uống do căng thẳng', f"Expected 'Ăn uống do căng thẳng', got: {cards_vi[1]['title']}"
    assert "Ăn uống do căng thẳng, hay còn gọi là ăn uống theo cảm xúc" in cards_vi[1]['summary'], "Summary 2 mismatch"
    assert "Xem thêm →" in cards_vi[1]['btn'], f"Expected 'Xem thêm →', got {cards_vi[1]['btn']}"

    assert cards_vi[2]['title'] == 'Vòng lặp căng thẳng ở sinh viên', f"Expected 'Vòng lặp căng thẳng ở sinh viên', got: {cards_vi[2]['title']}"
    assert "Cách những deadline dồn dập kích hoạt trạng thái tê liệt tinh thần" in cards_vi[2]['summary'], "Summary 3 mismatch"
    assert "Xem thêm →" in cards_vi[2]['btn'], f"Expected 'Xem thêm →', got {cards_vi[2]['btn']}"

    capture_screenshot(os.path.join(artifact_dir, "community_learn_vi.png"))

    print("\n--- 2. AUDITING ARTICLE DETAIL MODAL (VI) ---")
    eval_js("window.TempoCommunity.openLearnDetail('what_is_stress')")
    time.sleep(1)

    modal_vi = eval_js("""
        (() => {
            const modal = document.getElementById('tempo-learn-solve-modal');
            const card = document.getElementById('tempo-learn-solve-modal-card');
            if (!modal || modal.classList.contains('hidden') || !card) return null;
            const buttons = Array.from(card.querySelectorAll('button'));
            const closeBtn = buttons.find(b => b.getAttribute('onclick')?.includes('closeModal') && b.innerText.trim() !== '✕');
            return {
                badge: card.querySelector('.uppercase')?.innerText.trim(),
                title: card.querySelector('h3')?.innerText.trim(),
                desc: card.querySelector('[class*=\"space-y-1\"] p')?.innerText.trim(),
                paragraphs: Array.from(card.querySelectorAll('[class*=\"space-y-3\"] p')).map(p => p.innerText.trim()),
                relatedHeading: card.querySelector('.border-t span')?.innerText.trim(),
                toolBtn: card.querySelector('button[onclick*=\"handleToolAction\"]')?.innerText.trim().replace(/\\s+/g, ' '),
                closeBtn: closeBtn ? closeBtn.innerText.trim() : null
            };
        })()
    """)
    print("Modal details (VI):", json.dumps(modal_vi, ensure_ascii=False, indent=2))
    assert modal_vi is not None, "Modal did not open!"
    assert modal_vi['title'] == 'Stress là gì?', f"Expected 'Stress là gì?', got {modal_vi['title']}"
    assert "GIÁO DỤC CĂNG THẲNG" in modal_vi['badge'].upper(), f"Expected badge translation, got {modal_vi['badge']}"
    assert "HƯỚNG DẪN & HÀNH ĐỘNG LIÊN QUAN" in modal_vi['relatedHeading'] or "HƯỚNG DẪN" in modal_vi['relatedHeading'], f"Heading mismatch: {modal_vi['relatedHeading']}"
    assert "Mở Giải tỏa nhanh" in modal_vi['toolBtn'], f"Tool btn mismatch: {modal_vi['toolBtn']}"
    assert modal_vi['closeBtn'] == "Đóng", f"Close btn mismatch: {modal_vi['closeBtn']}"

    capture_screenshot(os.path.join(artifact_dir, "community_learn_modal_vi.png"))

    print("\n--- 3. AUDITING DYNAMIC LANGUAGE SWITCH TO ENGLISH WHILE MODAL IS OPEN ---")
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(1)

    modal_en = eval_js("""
        (() => {
            const card = document.getElementById('tempo-learn-solve-modal-card');
            const buttons = Array.from(card.querySelectorAll('button'));
            const closeBtn = buttons.find(b => b.getAttribute('onclick')?.includes('closeModal') && b.innerText.trim() !== '✕');
            return {
                badge: card.querySelector('.uppercase')?.innerText.trim(),
                title: card.querySelector('h3')?.innerText.trim(),
                desc: card.querySelector('[class*=\"space-y-1\"] p')?.innerText.trim(),
                paragraphs: Array.from(card.querySelectorAll('[class*=\"space-y-3\"] p')).map(p => p.innerText.trim()),
                relatedHeading: card.querySelector('.border-t span')?.innerText.trim(),
                toolBtn: card.querySelector('button[onclick*=\"handleToolAction\"]')?.innerText.trim().replace(/\\s+/g, ' '),
                closeBtn: closeBtn ? closeBtn.innerText.trim() : null
            };
        })()
    """)
    print("Modal details (EN):", json.dumps(modal_en, ensure_ascii=False, indent=2))
    assert modal_en['title'] == 'What is stress?', f"Expected 'What is stress?', got {modal_en['title']}"
    assert "STRESS EDUCATION" in modal_en['badge'].upper(), f"Expected EN badge, got {modal_en['badge']}"
    assert "RELATED GUIDES & ACTIONS" in modal_en['relatedHeading'], f"Heading mismatch: {modal_en['relatedHeading']}"
    assert "Open Quick Relief" in modal_en['toolBtn'], f"Tool btn mismatch: {modal_en['toolBtn']}"
    assert modal_en['closeBtn'] == "Close", f"Close btn mismatch: {modal_en['closeBtn']}"

    capture_screenshot(os.path.join(artifact_dir, "community_learn_modal_en.png"))

    print("\n--- 4. AUDITING ENGLISH LEARN FEED AFTER CLOSING MODAL ---")
    eval_js("window.TempoLearnSolve.closeModal()")
    time.sleep(1)

    back_label_en = eval_js("document.getElementById('community-back-label')?.innerText?.trim()")
    back_btn_full_en = eval_js("document.getElementById('btn-community-back')?.innerText?.replace(/\\s+/g, ' ')?.trim()")
    print(f"Back Label (EN): '{back_label_en}' | Full: '{back_btn_full_en}'")
    assert back_label_en == "Return to Dashboard", f"Expected 'Return to Dashboard', got: {back_label_en}"

    search_ph_en = eval_js("document.getElementById('learn-search-input')?.placeholder")
    print(f"Search placeholder (EN): '{search_ph_en}'")
    assert search_ph_en == "Search...", f"Expected 'Search...', got: {search_ph_en}"

    sidebar_tabs_en = eval_js("""
        (() => {
            const tabs = {};
            document.querySelectorAll('#community-sidebar-nav .community-nav-item').forEach(b => {
                tabs[b.getAttribute('data-community-tab')] = b.innerText.trim();
            });
            return tabs;
        })()
    """)
    print(f"Sidebar Desktop Tabs (EN): {sidebar_tabs_en}")
    assert sidebar_tabs_en.get("announcement") == "Announcement", f"Announcement mismatch: {sidebar_tabs_en}"
    assert sidebar_tabs_en.get("tips") == "Tips", f"Tips mismatch: {sidebar_tabs_en}"
    assert sidebar_tabs_en.get("learn") == "Learn", f"Learn mismatch: {sidebar_tabs_en}"
    assert sidebar_tabs_en.get("posts") == "Posts", f"Posts mismatch: {sidebar_tabs_en}"
    assert sidebar_tabs_en.get("messages") == "Direct Message", f"Messages mismatch: {sidebar_tabs_en}"

    cards_en = eval_js("""
        Array.from(document.querySelectorAll('#learn-cards-grid > div')).map(el => ({
            id: el.getAttribute('data-learn-id'),
            title: el.querySelector('h3')?.innerText.trim(),
            summary: el.querySelector('p')?.innerText.trim(),
            btn: el.querySelector('button')?.innerText.trim().replace(/\\s+/g, ' ')
        }))
    """)
    print(f"Found {len(cards_en)} Learn cards in EN:")
    for c in cards_en:
        print(f"  - [{c['id']}] {c['title']} | Btn: '{c['btn']}'")

    assert cards_en[0]['title'] == 'What is stress?', f"Expected 'What is stress?', got {cards_en[0]['title']}"
    assert "See more →" in cards_en[0]['btn'], f"Expected 'See more →', got {cards_en[0]['btn']}"
    assert cards_en[1]['title'] == 'Stress eating', f"Expected 'Stress eating', got: {cards_en[1]['title']}"
    assert cards_en[2]['title'] == 'The Student Stress Loop', f"Expected 'The Student Stress Loop', got: {cards_en[2]['title']}"

    capture_screenshot(os.path.join(artifact_dir, "community_learn_en.png"))

    print("\n--- 5. AUDITING ARTICLE 3 (STRESS LOOP) WITH VISUAL CYCLE IN VIETNAMESE ---")
    eval_js("window.TempoI18n.setLanguage('vi')")
    time.sleep(0.5)
    eval_js("window.TempoCommunity.openLearnDetail('stress_loop')")
    time.sleep(1)

    modal_loop_vi = eval_js("""
        (() => {
            const card = document.getElementById('tempo-learn-solve-modal-card');
            return {
                title: card.querySelector('h3')?.innerText.trim(),
                cycleHeading: card.querySelector('.border-2 span')?.innerText.trim(),
                nodes: Array.from(card.querySelectorAll('.border-2 .px-3 span:last-child')).map(s => s.innerText.trim()),
                keyInsight: card.querySelector('.border-2 strong')?.parentNode?.innerText.trim()
            };
        })()
    """)
    print("Stress Loop modal (VI):", json.dumps(modal_loop_vi, ensure_ascii=False, indent=2))
    assert modal_loop_vi['title'] == 'Vòng lặp căng thẳng ở sinh viên', f"Title mismatch: {modal_loop_vi['title']}"
    assert "VÒNG LẶP CĂNG THẲNG TRỰC QUAN" in modal_loop_vi['cycleHeading'], f"Heading mismatch: {modal_loop_vi['cycleHeading']}"
    assert len(modal_loop_vi['nodes']) == 6, f"Expected 6 nodes, got {len(modal_loop_vi['nodes'])}"
    assert "Dồn dập deadline" in modal_loop_vi['nodes'][0], f"First node mismatch: {modal_loop_vi['nodes'][0]}"
    assert "Điểm mấu chốt:" in modal_loop_vi['keyInsight'], f"Key insight prefix mismatch: {modal_loop_vi['keyInsight']}"
    eval_js("window.TempoLearnSolve.closeModal()")
    time.sleep(0.5)

    print("\n--- 6. AUDITING ARTICLE 2 (STRESS EATING) WITH ACTION STEPS IN VIETNAMESE ---")
    eval_js("window.TempoCommunity.openLearnDetail('stress_eating')")
    time.sleep(1)

    modal_eating_vi = eval_js("""
        (() => {
            const card = document.getElementById('tempo-learn-solve-modal-card');
            return {
                title: card.querySelector('h3')?.innerText.trim(),
                stepsHeading: card.querySelector('.space-y-3 span.uppercase')?.innerText.trim(),
                steps: Array.from(card.querySelectorAll('.space-y-1 h5')).map(h => h.innerText.trim())
            };
        })()
    """)
    print("Stress Eating modal (VI):", json.dumps(modal_eating_vi, ensure_ascii=False, indent=2))
    assert modal_eating_vi['title'] == 'Ăn uống do căng thẳng', f"Title mismatch: {modal_eating_vi['title']}"
    assert "CÁC BƯỚC THỰC HIỆN" in modal_eating_vi['stepsHeading'], f"Steps heading mismatch: {modal_eating_vi['stepsHeading']}"
    assert len(modal_eating_vi['steps']) == 4, f"Expected 4 steps, got {len(modal_eating_vi['steps'])}"
    assert "Kiểm tra xem bạn đang đói" in modal_eating_vi['steps'][0], f"Step 1 mismatch: {modal_eating_vi['steps'][0]}"
    eval_js("window.TempoLearnSolve.closeModal()")
    time.sleep(0.5)

    print("\n--- 7. AUDITING SEARCH AND FILTER IN VIETNAMESE ---")
    eval_js("window.TempoCommunity.handleLearnSearch('ăn uống')")
    time.sleep(0.5)
    filtered_cards = eval_js("""
        Array.from(document.querySelectorAll('#learn-cards-grid > div')).map(el => el.querySelector('h3')?.innerText.trim())
    """)
    print(f"Search 'ăn uống' returned {len(filtered_cards)} cards:", filtered_cards)
    assert len(filtered_cards) == 1 and filtered_cards[0] == 'Ăn uống do căng thẳng', "Search filtering failed"

    # Reset search
    eval_js("window.TempoCommunity.handleLearnSearch('')")
    time.sleep(0.5)
    reset_count = eval_js("document.querySelectorAll('#learn-cards-grid > div').length")
    print(f"Cards after clearing search: {reset_count}")
    assert reset_count == 3, f"Expected 3 cards restored, got {reset_count}"

    print("\n--- 8. AUDITING BACK NAVIGATION TO DASHBOARD ---")
    eval_js("document.getElementById('btn-community-back').click()")
    time.sleep(1)
    current_hash = eval_js("window.location.hash")
    dashboard_visible = eval_js("""
        const el = document.getElementById('view-today');
        Boolean(el && !el.classList.contains('hidden') && el.offsetHeight > 0);
    """)
    print(f"Current hash after clicking return: '{current_hash}', Dashboard visible: {dashboard_visible}")
    assert dashboard_visible or current_hash in ['', '#', '#dashboard', '#today', '#mode-today'], f"Dashboard expected, got {current_hash}"

    print("\n==========================================")
    print("ALL 8 VERIFICATION SUITES PASSED PERFECTLY!")
    print("==========================================")

finally:
    if ws:
        try:
            ws.close()
        except Exception:
            pass
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except Exception:
        proc.kill()
