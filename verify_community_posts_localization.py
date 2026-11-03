import sys, os, time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
URL = "http://127.0.0.1:8000/#community?tab=posts"

def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        print(f"Loading {URL}...")
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1000)

        # -------------------------------------------------------------
        # 1. Test VIETNAMESE (Default / Initial)
        # -------------------------------------------------------------
        # Force VI locale to be certain
        page.evaluate("() => window.TempoI18n && window.TempoI18n.setLanguage('vi')")
        page.wait_for_timeout(500)

        print("\n--- 1. Testing VIETNAMESE (`vi`) ---")
        # Navigation
        back_btn_text = page.locator("#btn-community-back").inner_text().replace('\n', ' ').strip()
        back_label_text = page.locator("#community-back-label").inner_text().strip()
        print(f"VI Back Button Full Text: '{back_btn_text}'")
        print(f"VI Back Label Text: '{back_label_text}'")
        assert "Quay lại Dashboard" in back_btn_text, f"Expected 'Quay lại Dashboard' in back button, got '{back_btn_text}'"

        # Sidebar Desktop
        sidebar_desktop = page.evaluate("""() => {
            const tabs = {};
            document.querySelectorAll('#community-sidebar-nav .community-nav-item').forEach(b => {
                tabs[b.getAttribute('data-community-tab')] = b.innerText.trim();
            });
            return tabs;
        }""")
        print(f"VI Desktop Sidebar: {sidebar_desktop}")
        assert sidebar_desktop.get("announcement") == "Thông báo", f"Sidebar announcement mismatch: {sidebar_desktop.get('announcement')}"
        assert sidebar_desktop.get("tips") == "Tips", f"Sidebar tips mismatch: {sidebar_desktop.get('tips')}"
        assert sidebar_desktop.get("learn") == "Learn", f"Sidebar learn mismatch: {sidebar_desktop.get('learn')}"
        assert sidebar_desktop.get("posts") == "Bài viết", f"Sidebar posts mismatch: {sidebar_desktop.get('posts')}"
        assert sidebar_desktop.get("messages") == "Tin nhắn riêng", f"Sidebar messages mismatch: {sidebar_desktop.get('messages')}"

        # Toolbar
        new_post_text = page.locator("#label-posts-new").inner_text().strip()
        search_placeholder = page.locator("#posts-search-input").get_attribute("placeholder")
        my_posts_text = page.locator("#label-posts-filter-my").inner_text().strip()
        notif_title = page.locator("#btn-posts-notifications").get_attribute("title")
        bookmarks_title = page.locator("#btn-posts-filter-bookmarks").get_attribute("title")
        bookmarks_aria = page.locator("#btn-posts-filter-bookmarks").get_attribute("aria-label")

        print(f"VI New Post: '{new_post_text}'")
        print(f"VI Search Placeholder: '{search_placeholder}'")
        print(f"VI My Posts: '{my_posts_text}'")
        print(f"VI Notifications Title: '{notif_title}'")
        print(f"VI Saved Posts Title: '{bookmarks_title}', Aria: '{bookmarks_aria}'")

        assert new_post_text == "Đăng bài mới", f"New post button mismatch: '{new_post_text}'"
        assert search_placeholder == "Tìm kiếm...", f"Search placeholder mismatch: '{search_placeholder}'"
        assert my_posts_text == "Bài viết của tôi", f"My posts button mismatch: '{my_posts_text}'"
        assert notif_title == "Thông báo", f"Notifications title mismatch: '{notif_title}'"
        assert bookmarks_title == "Bài viết đã lưu", f"Saved posts title mismatch: '{bookmarks_title}'"

        # Post Metadata (TimeAgo) & Interactions
        post1_time = page.locator('[data-post-id="post-1"] .italic').first.inner_text().strip()
        post2_time = page.locator('[data-post-id="post-2"] h4 + span').first.inner_text().strip()
        print(f"VI Post 1 Time: '{post1_time}'")
        print(f"VI Post 2 Time: '{post2_time}'")
        assert "2 giờ trước" in post1_time, f"Expected '2 giờ trước', got '{post1_time}'"
        assert "5 giờ trước" in post2_time, f"Expected '5 giờ trước', got '{post2_time}'"

        # Comments time & reply form in Post 1
        comment_time = page.locator('[data-post-id="post-1"] .space-y-2\\.5 span.text-\\[9\\.5px\\]').first.inner_text().strip()
        reply_placeholder = page.locator('#input-comment-post-1').get_attribute("placeholder")
        post_btn_text = page.locator('[data-post-id="post-1"] form button[type="submit"]').inner_text().strip()
        print(f"VI Comment Time: '{comment_time}'")
        print(f"VI Reply Placeholder: '{reply_placeholder}'")
        print(f"VI Submit Button: '{post_btn_text}'")
        assert "2 giờ trước" in comment_time, f"Expected comment time '2 giờ trước', got '{comment_time}'"
        assert reply_placeholder == "Trả lời...", f"Expected placeholder 'Trả lời...', got '{reply_placeholder}'"
        assert post_btn_text == "Gửi", f"Expected submit button 'Gửi', got '{post_btn_text}'"

        # Take screenshot VI
        vi_screenshot_path = os.path.join(ARTIFACT_DIR, "community_posts_vi.png")
        page.screenshot(path=vi_screenshot_path, full_page=False)
        print(f"Saved VI screenshot to {vi_screenshot_path}")

        # -------------------------------------------------------------
        # 2. Test ENGLISH (`en`) via Language Switcher
        # -------------------------------------------------------------
        print("\n--- 2. Testing Switching to ENGLISH (`en`) ---")
        # Click the language toggle or use setLanguage
        page.evaluate("() => window.TempoI18n && window.TempoI18n.setLanguage('en')")
        page.wait_for_timeout(500)

        # Navigation
        back_btn_text_en = page.locator("#btn-community-back").inner_text().replace('\n', ' ').strip()
        back_label_text_en = page.locator("#community-back-label").inner_text().strip()
        print(f"EN Back Button Full Text: '{back_btn_text_en}'")
        print(f"EN Back Label Text: '{back_label_text_en}'")
        assert "Return to Dashboard" in back_btn_text_en, f"Expected 'Return to Dashboard' in back button, got '{back_btn_text_en}'"
        assert back_label_text_en == "Return to Dashboard", f"Expected back label 'Return to Dashboard', got '{back_label_text_en}'"

        # Sidebar Desktop
        sidebar_desktop_en = page.evaluate("""() => {
            const tabs = {};
            document.querySelectorAll('#community-sidebar-nav .community-nav-item').forEach(b => {
                tabs[b.getAttribute('data-community-tab')] = b.innerText.trim();
            });
            return tabs;
        }""")
        print(f"EN Desktop Sidebar: {sidebar_desktop_en}")
        assert sidebar_desktop_en.get("announcement") == "Announcement", f"Sidebar announcement mismatch: {sidebar_desktop_en.get('announcement')}"
        assert sidebar_desktop_en.get("tips") == "Tips", f"Sidebar tips mismatch: {sidebar_desktop_en.get('tips')}"
        assert sidebar_desktop_en.get("learn") == "Learn", f"Sidebar learn mismatch: {sidebar_desktop_en.get('learn')}"
        assert sidebar_desktop_en.get("posts") == "Posts", f"Sidebar posts mismatch: {sidebar_desktop_en.get('posts')}"
        assert sidebar_desktop_en.get("messages") == "Direct Message", f"Sidebar messages mismatch: {sidebar_desktop_en.get('messages')}"

        # Toolbar
        new_post_text_en = page.locator("#label-posts-new").inner_text().strip()
        search_placeholder_en = page.locator("#posts-search-input").get_attribute("placeholder")
        my_posts_text_en = page.locator("#label-posts-filter-my").inner_text().strip()
        notif_title_en = page.locator("#btn-posts-notifications").get_attribute("title")
        bookmarks_title_en = page.locator("#btn-posts-filter-bookmarks").get_attribute("title")
        bookmarks_aria_en = page.locator("#btn-posts-filter-bookmarks").get_attribute("aria-label")

        print(f"EN New Post: '{new_post_text_en}'")
        print(f"EN Search Placeholder: '{search_placeholder_en}'")
        print(f"EN My Posts: '{my_posts_text_en}'")
        print(f"EN Notifications Title: '{notif_title_en}'")
        print(f"EN Saved Posts Title: '{bookmarks_title_en}', Aria: '{bookmarks_aria_en}'")

        assert new_post_text_en == "New post", f"New post button mismatch: '{new_post_text_en}'"
        assert search_placeholder_en == "Search...", f"Search placeholder mismatch: '{search_placeholder_en}'"
        assert my_posts_text_en == "Your posts", f"My posts button mismatch: '{my_posts_text_en}'"
        assert notif_title_en == "Notifications", f"Notifications title mismatch: '{notif_title_en}'"
        assert bookmarks_title_en == "Saved posts", f"Saved posts title mismatch: '{bookmarks_title_en}'"

        # Post Metadata (TimeAgo) & Interactions
        post1_time_en = page.locator('[data-post-id="post-1"] .italic').first.inner_text().strip()
        post2_time_en = page.locator('[data-post-id="post-2"] h4 + span').first.inner_text().strip()
        print(f"EN Post 1 Time: '{post1_time_en}'")
        print(f"EN Post 2 Time: '{post2_time_en}'")
        assert "2 hours ago" in post1_time_en, f"Expected '2 hours ago', got '{post1_time_en}'"
        assert "5 hours ago" in post2_time_en, f"Expected '5 hours ago', got '{post2_time_en}'"

        # Comments time & reply form in Post 1
        comment_time_en = page.locator('[data-post-id="post-1"] .space-y-2\\.5 span.text-\\[9\\.5px\\]').first.inner_text().strip()
        reply_placeholder_en = page.locator('#input-comment-post-1').get_attribute("placeholder")
        post_btn_text_en = page.locator('[data-post-id="post-1"] form button[type="submit"]').inner_text().strip()
        print(f"EN Comment Time: '{comment_time_en}'")
        print(f"EN Reply Placeholder: '{reply_placeholder_en}'")
        print(f"EN Submit Button: '{post_btn_text_en}'")
        assert "2 hours ago" in comment_time_en, f"Expected comment time '2 hours ago', got '{comment_time_en}'"
        assert reply_placeholder_en == "Reply...", f"Expected placeholder 'Reply...', got '{reply_placeholder_en}'"
        assert post_btn_text_en == "Post", f"Expected submit button 'Post', got '{post_btn_text_en}'"

        # Take screenshot EN
        en_screenshot_path = os.path.join(ARTIFACT_DIR, "community_posts_en.png")
        page.screenshot(path=en_screenshot_path, full_page=False)
        print(f"Saved EN screenshot to {en_screenshot_path}")

        # -------------------------------------------------------------
        # 3. Test Navigation back to Dashboard
        # -------------------------------------------------------------
        print("\n--- 3. Testing Navigation to Dashboard ---")
        page.locator("#btn-community-back").click()
        page.wait_for_timeout(500)
        curr_url = page.url
        print(f"URL after clicking return: {curr_url}")
        # Verify dashboard is visible
        today_view = page.locator("#view-today")
        is_today_visible = today_view.is_visible()
        print(f"Dashboard view-today visible: {is_today_visible}")
        assert is_today_visible, "Expected Dashboard to be visible after clicking return"

        browser.close()
        print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    run_tests()
