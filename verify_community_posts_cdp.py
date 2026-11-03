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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_posts_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9570

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#community?tab=posts"
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
    time.sleep(2.5)
    tabs_res = urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read().decode()
    tabs = json.loads(tabs_res)
    app_tab = next(t for t in tabs if "8000" in t.get("url", ""))

    ws = websocket.create_connection(app_tab["webSocketDebuggerUrl"], timeout=10)
    print("Connected to CDP via WebSocket.")

    send_cmd("Page.enable")
    send_cmd("DOM.enable")

    time.sleep(1.5)

    # Select posts tab and set VI
    eval_js("""
    (() => {
        if (window.TempoCommunity) {
            window.TempoCommunity.selectTab('posts');
        }
        if (window.TempoI18n) {
            window.TempoI18n.setLanguage('vi');
        }
    })()
    """)
    time.sleep(1)

    print("\n================== 1. VERIFYING VIETNAMESE (`vi`) ==================")

    # 1. Navigation
    back_label = eval_js("document.getElementById('community-back-label')?.innerText?.trim()")
    back_btn_full = eval_js("document.getElementById('btn-community-back')?.innerText?.replace(/\\s+/g, ' ')?.trim()")
    back_btn_title = eval_js("document.getElementById('btn-community-back')?.getAttribute('title')")
    print(f"VI Back Label: '{back_label}'")
    print(f"VI Back Button Full Text: '{back_btn_full}'")
    print(f"VI Back Button Title: '{back_btn_title}'")
    assert back_label == "Quay lại Dashboard", f"Expected 'Quay lại Dashboard', got '{back_label}'"
    assert "Quay lại Dashboard" in back_btn_full, f"Expected 'Quay lại Dashboard' in back button, got '{back_btn_full}'"
    assert back_btn_title == "← Quay lại Dashboard", f"Expected '← Quay lại Dashboard', got '{back_btn_title}'"

    # 2. Sidebar Desktop
    sidebar_tabs_vi = eval_js("""
    (() => {
        const tabs = {};
        document.querySelectorAll('#community-sidebar-nav .community-nav-item').forEach(b => {
            tabs[b.getAttribute('data-community-tab')] = b.innerText.trim();
        });
        return tabs;
    })()
    """)
    print(f"VI Desktop Sidebar Tabs: {sidebar_tabs_vi}")
    assert sidebar_tabs_vi.get("announcement") == "Thông báo", f"Sidebar announcement mismatch: {sidebar_tabs_vi}"
    assert sidebar_tabs_vi.get("tips") == "Tips", f"Sidebar tips mismatch: {sidebar_tabs_vi}"
    assert sidebar_tabs_vi.get("learn") == "Learn", f"Sidebar learn mismatch: {sidebar_tabs_vi}"
    assert sidebar_tabs_vi.get("posts") == "Bài viết", f"Sidebar posts mismatch: {sidebar_tabs_vi}"
    assert sidebar_tabs_vi.get("messages") == "Tin nhắn riêng", f"Sidebar messages mismatch: {sidebar_tabs_vi}"

    # 3. Toolbar
    new_post_vi = eval_js("document.getElementById('label-posts-new')?.innerText?.trim()")
    search_placeholder_vi = eval_js("document.getElementById('posts-search-input')?.getAttribute('placeholder')")
    my_posts_vi = eval_js("document.getElementById('label-posts-filter-my')?.innerText?.trim()")
    notif_title_vi = eval_js("document.getElementById('btn-posts-notifications')?.getAttribute('title')")
    notif_aria_vi = eval_js("document.getElementById('btn-posts-notifications')?.getAttribute('aria-label')")
    bookmarks_title_vi = eval_js("document.getElementById('btn-posts-filter-bookmarks')?.getAttribute('title')")
    bookmarks_aria_vi = eval_js("document.getElementById('btn-posts-filter-bookmarks')?.getAttribute('aria-label')")

    print(f"VI New post button: '{new_post_vi}'")
    print(f"VI Search placeholder: '{search_placeholder_vi}'")
    print(f"VI Your posts button: '{my_posts_vi}'")
    print(f"VI Notifications title: '{notif_title_vi}', aria: '{notif_aria_vi}'")
    print(f"VI Saved posts title: '{bookmarks_title_vi}', aria: '{bookmarks_aria_vi}'")

    assert new_post_vi == "Đăng bài mới", f"New post button mismatch: '{new_post_vi}'"
    assert search_placeholder_vi == "Tìm kiếm...", f"Search placeholder mismatch: '{search_placeholder_vi}'"
    assert my_posts_vi == "Bài viết của tôi", f"Your posts button mismatch: '{my_posts_vi}'"
    assert notif_title_vi == "Thông báo", f"Notifications title mismatch: '{notif_title_vi}'"
    assert notif_aria_vi == "Thông báo", f"Notifications aria mismatch: '{notif_aria_vi}'"
    assert bookmarks_title_vi == "Bài viết đã lưu", f"Saved posts title mismatch: '{bookmarks_title_vi}'"
    assert bookmarks_aria_vi == "Bài viết đã lưu", f"Saved posts aria mismatch: '{bookmarks_aria_vi}'"

    # 4. Post Metadata
    post1_time_vi = eval_js("document.querySelector('[data-post-id=\"post-1\"] span.italic')?.innerText?.trim()")
    post2_time_vi = eval_js("document.querySelector('[data-post-id=\"post-2\"] h4 + span')?.innerText?.trim()")
    print(f"VI Post 1 Time: '{post1_time_vi}'")
    print(f"VI Post 2 Time: '{post2_time_vi}'")
    assert post1_time_vi == "2 giờ trước", f"Expected '2 giờ trước', got '{post1_time_vi}'"
    assert post2_time_vi == "5 giờ trước", f"Expected '5 giờ trước', got '{post2_time_vi}'"

    # 5. Post Interactions
    comment1_time_vi = eval_js("document.querySelector('[data-post-id=\"post-1\"] .space-y-1 span:nth-of-type(2)')?.innerText?.trim()")
    reply_placeholder_vi = eval_js("document.getElementById('input-comment-post-1')?.getAttribute('placeholder')")
    submit_btn_vi = eval_js("document.querySelector('[data-post-id=\"post-1\"] form button[type=\"submit\"]')?.innerText?.trim()")
    print(f"VI Comment Time: '{comment1_time_vi}'")
    print(f"VI Reply Placeholder: '{reply_placeholder_vi}'")
    print(f"VI Submit Button: '{submit_btn_vi}'")
    assert comment1_time_vi == "2 giờ trước", f"Expected '2 giờ trước', got '{comment1_time_vi}'"
    assert reply_placeholder_vi == "Trả lời...", f"Expected 'Trả lời...', got '{reply_placeholder_vi}'"
    assert submit_btn_vi == "Gửi", f"Expected 'Gửi', got '{submit_btn_vi}'"

    # Capture VI screenshot
    capture_screenshot("community_posts_vi.png")

    print("\n================== 2. VERIFYING ENGLISH (`en`) ==================")
    # Switch language to English
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(1)

    # 1. Navigation
    back_label_en = eval_js("document.getElementById('community-back-label')?.innerText?.trim()")
    back_btn_full_en = eval_js("document.getElementById('btn-community-back')?.innerText?.replace(/\\s+/g, ' ')?.trim()")
    back_btn_title_en = eval_js("document.getElementById('btn-community-back')?.getAttribute('title')")
    print(f"EN Back Label: '{back_label_en}'")
    print(f"EN Back Button Full Text: '{back_btn_full_en}'")
    print(f"EN Back Button Title: '{back_btn_title_en}'")
    assert back_label_en == "Return to Dashboard", f"Expected 'Return to Dashboard', got '{back_label_en}'"
    assert "Return to Dashboard" in back_btn_full_en, f"Expected 'Return to Dashboard' in back button, got '{back_btn_full_en}'"
    assert back_btn_title_en == "← Return to Dashboard", f"Expected '← Return to Dashboard', got '{back_btn_title_en}'"

    # 2. Sidebar Desktop
    sidebar_tabs_en = eval_js("""
    (() => {
        const tabs = {};
        document.querySelectorAll('#community-sidebar-nav .community-nav-item').forEach(b => {
            tabs[b.getAttribute('data-community-tab')] = b.innerText.trim();
        });
        return tabs;
    })()
    """)
    print(f"EN Desktop Sidebar Tabs: {sidebar_tabs_en}")
    assert sidebar_tabs_en.get("announcement") == "Announcement", f"Sidebar announcement mismatch: {sidebar_tabs_en}"
    assert sidebar_tabs_en.get("tips") == "Tips", f"Sidebar tips mismatch: {sidebar_tabs_en}"
    assert sidebar_tabs_en.get("learn") == "Learn", f"Sidebar learn mismatch: {sidebar_tabs_en}"
    assert sidebar_tabs_en.get("posts") == "Posts", f"Sidebar posts mismatch: {sidebar_tabs_en}"
    assert sidebar_tabs_en.get("messages") == "Direct Message", f"Sidebar messages mismatch: {sidebar_tabs_en}"

    # 3. Toolbar
    new_post_en = eval_js("document.getElementById('label-posts-new')?.innerText?.trim()")
    search_placeholder_en = eval_js("document.getElementById('posts-search-input')?.getAttribute('placeholder')")
    my_posts_en = eval_js("document.getElementById('label-posts-filter-my')?.innerText?.trim()")
    notif_title_en = eval_js("document.getElementById('btn-posts-notifications')?.getAttribute('title')")
    notif_aria_en = eval_js("document.getElementById('btn-posts-notifications')?.getAttribute('aria-label')")
    bookmarks_title_en = eval_js("document.getElementById('btn-posts-filter-bookmarks')?.getAttribute('title')")
    bookmarks_aria_en = eval_js("document.getElementById('btn-posts-filter-bookmarks')?.getAttribute('aria-label')")

    print(f"EN New post button: '{new_post_en}'")
    print(f"EN Search placeholder: '{search_placeholder_en}'")
    print(f"EN Your posts button: '{my_posts_en}'")
    print(f"EN Notifications title: '{notif_title_en}', aria: '{notif_aria_en}'")
    print(f"EN Saved posts title: '{bookmarks_title_en}', aria: '{bookmarks_aria_en}'")

    assert new_post_en == "New post", f"New post button mismatch: '{new_post_en}'"
    assert search_placeholder_en == "Search...", f"Search placeholder mismatch: '{search_placeholder_en}'"
    assert my_posts_en == "Your posts", f"Your posts button mismatch: '{my_posts_en}'"
    assert notif_title_en == "Notifications", f"Notifications title mismatch: '{notif_title_en}'"
    assert notif_aria_en == "Notifications", f"Notifications aria mismatch: '{notif_aria_en}'"
    assert bookmarks_title_en == "Saved posts", f"Saved posts title mismatch: '{bookmarks_title_en}'"
    assert bookmarks_aria_en == "Saved posts", f"Saved posts aria mismatch: '{bookmarks_aria_en}'"

    # 4. Post Metadata
    post1_time_en = eval_js("document.querySelector('[data-post-id=\"post-1\"] span.italic')?.innerText?.trim()")
    post2_time_en = eval_js("document.querySelector('[data-post-id=\"post-2\"] h4 + span')?.innerText?.trim()")
    print(f"EN Post 1 Time: '{post1_time_en}'")
    print(f"EN Post 2 Time: '{post2_time_en}'")
    assert post1_time_en == "2 hours ago", f"Expected '2 hours ago', got '{post1_time_en}'"
    assert post2_time_en == "5 hours ago", f"Expected '5 hours ago', got '{post2_time_en}'"

    # 5. Post Interactions
    comment1_time_en = eval_js("document.querySelector('[data-post-id=\"post-1\"] .space-y-1 span:nth-of-type(2)')?.innerText?.trim()")
    reply_placeholder_en = eval_js("document.getElementById('input-comment-post-1')?.getAttribute('placeholder')")
    submit_btn_en = eval_js("document.querySelector('[data-post-id=\"post-1\"] form button[type=\"submit\"]')?.innerText?.trim()")
    print(f"EN Comment Time: '{comment1_time_en}'")
    print(f"EN Reply Placeholder: '{reply_placeholder_en}'")
    print(f"EN Submit Button: '{submit_btn_en}'")
    assert comment1_time_en == "2 hours ago", f"Expected '2 hours ago', got '{comment1_time_en}'"
    assert reply_placeholder_en == "Reply...", f"Expected 'Reply...', got '{reply_placeholder_en}'"
    assert submit_btn_en == "Post", f"Expected 'Post', got '{submit_btn_en}'"

    # Capture EN screenshot
    capture_screenshot("community_posts_en.png")

    print("\n================== 3. VERIFYING NAVIGATION TO DASHBOARD ==================")
    eval_js("document.getElementById('btn-community-back').click()")
    time.sleep(1)

    is_today_visible = eval_js("""
    (() => {
        const el = document.getElementById('view-today');
        return el && !el.classList.contains('hidden') && el.offsetParent !== null;
    })()
    """)
    current_hash = eval_js("window.location.hash")
    print(f"Current URL Hash after clicking return: '{current_hash}'")
    print(f"view-today visible on page: {is_today_visible}")
    assert is_today_visible or current_hash in ['#today', '#entry-home', '#mode-today'], f"Expected dashboard visible, got hash {current_hash}"

    capture_screenshot("community_posts_navigated_dashboard.png")

    print("\nALL VERIFICATION TESTS COMPLETED SUCCESSFULLY AND PASSED 100%! 🎉")

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
