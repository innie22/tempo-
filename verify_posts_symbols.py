# -*- coding: utf-8 -*-
import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import base64
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_symbols_test_')
port = 9458
proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={port}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--disable-gpu',
    '--no-first-run',
    'http://localhost:8000/'
])
time.sleep(2.5)

try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
        pages = [t for t in tabs if t.get('type') == 'page' and 'localhost' in t.get('url', '')]
    ws_url = pages[0]['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)

    msg_id = 1
    def send_cmd(method, params=None):
        global msg_id
        cmd = {'id': msg_id, 'method': method, 'params': params or {}}
        msg_id += 1
        ws.send(json.dumps(cmd))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == cmd['id']:
                return resp.get('result', {})

    def eval_js(expr):
        res = send_cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        return res.get('result', {}).get('value')

    def capture_screenshot(filename):
        res = send_cmd("Page.captureScreenshot", {"format": "png"})
        data = base64.b64decode(res.get("data", ""))
        with open(filename, "wb") as f:
            f.write(data)
        print(f"Captured screenshot: {filename} ({len(data)} bytes)")

    send_cmd('Page.enable')
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 1280,
        "height": 900,
        "deviceScaleFactor": 1,
        "mobile": False
    })

    for _ in range(30):
        if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoCommunity !== 'undefined'"):
            break
        time.sleep(0.5)

    print("=" * 60)
    print("VERIFYING TEMPO COMMUNITY POSTS ACTION SYMBOLS")
    print("=" * 60)

    # 1. Navigate to Community -> Posts Tab
    eval_js("window.TempoApp.navigateTo('community');")
    time.sleep(0.3)
    eval_js("window.TempoCommunity.selectTab('posts');")
    time.sleep(0.4)

    # 2. Verify all 3 symbol image assets render and have natural dimensions
    images_info = eval_js("""
        (() => {
            const results = {};
            const imgs = document.querySelectorAll('#community-feed-posts-list img');
            imgs.forEach(img => {
                const src = img.getAttribute('src');
                if (src && (src.includes('bookmark') || src.includes('comment') || src.includes('message'))) {
                    results[src] = {
                        complete: img.complete,
                        naturalWidth: img.naturalWidth,
                        naturalHeight: img.naturalHeight,
                        alt: img.getAttribute('alt')
                    };
                }
            });
            return results;
        })()
    """)
    print("1. Rendered Symbol Images Info:", json.dumps(images_info, indent=2))
    assert 'assets/bookmark_action_symbol.png' in images_info, "Bookmark symbol must be rendered"
    assert images_info['assets/bookmark_action_symbol.png']['naturalWidth'] > 0, "Bookmark symbol image must load"
    assert 'assets/comment_action_symbol.png' in images_info, "Comment symbol must be rendered"
    assert images_info['assets/comment_action_symbol.png']['naturalWidth'] > 0, "Comment symbol image must load"
    assert 'assets/message_action_symbol.png' in images_info, "Message symbol must be rendered"
    assert images_info['assets/message_action_symbol.png']['naturalWidth'] > 0, "Message symbol image must load"

    # Verify no legacy emojis in action buttons
    legacy_emojis = eval_js("""
        (() => {
            const feed = document.getElementById('community-feed-posts-list');
            if (!feed) return [];
            const text = feed.innerHTML;
            const found = [];
            ['🔖', '🏷️', '💬', '▷'].forEach(icon => {
                if (text.includes(icon)) found.push(icon);
            });
            return found;
        })()
    """)
    print("Legacy emojis in action buttons:", legacy_emojis)
    assert len(legacy_emojis) == 0, f"Found legacy emojis: {legacy_emojis}"

    # 3. Test Save / Bookmark Symbol Behavior
    print("\n--- TEST: Bookmark Action ---")
    # 3a. Unauthenticated user: clicking bookmark prompts sign in and does not save
    eval_js("""
        if (window.TempoAuth) window.TempoAuth.getCurrentUser = () => null;
        window.TempoCommunity.toggleBookmark('post-1');
    """)
    time.sleep(0.2)
    p1_bookmarked_unauth = eval_js("window.TempoCommunity.getPosts().find(p => p.id === 'post-1').isBookmarked")
    print("3a. Unauthenticated bookmark attempt on post-1 isBookmarked:", p1_bookmarked_unauth)
    assert p1_bookmarked_unauth == False, "Unauthenticated user should not be able to bookmark"

    # Close modal after unauthenticated test
    eval_js("if (window.TempoAuth && typeof window.TempoAuth.closeModal === 'function') window.TempoAuth.closeModal();")

    # 3b. Authenticated user: save post-1
    eval_js("""
        if (window.TempoAuth) {
            window.TempoAuth.getCurrentUser = () => ({ id: 'user_tester_99', email: 'tester@tempo.edu' });
            window.TempoAuth.getCurrentProfile = () => ({ id: 'user_tester_99', full_name: 'Tester Student' });
        }
        window.TempoCommunity.toggleBookmark('post-1');
    """)
    time.sleep(0.3)
    p1_bookmarked_auth = eval_js("window.TempoCommunity.getPosts().find(p => p.id === 'post-1').isBookmarked")
    print("3b. Authenticated bookmark on post-1 isBookmarked:", p1_bookmarked_auth)
    assert p1_bookmarked_auth == True, "Post should be bookmarked for authenticated user"

    # Check button styling (active background and aria attributes)
    bookmark_btn_state = eval_js("""
        (() => {
            const btn = document.querySelector('[data-post-id="post-1"] button[title="Saved to bookmarks"]');
            if (!btn) return null;
            return {
                ariaPressed: btn.getAttribute('aria-pressed'),
                ariaLabel: btn.getAttribute('aria-label'),
                hasActiveBg: btn.className.includes('bg-[#FCEFE8]')
            };
        })()
    """)
    print("3c. Bookmark button visual state:", bookmark_btn_state)
    assert bookmark_btn_state['ariaPressed'] == 'true'
    assert bookmark_btn_state['hasActiveBg'] == True

    # Check localStorage persistence
    user_bookmarks_storage = eval_js("JSON.parse(localStorage.getItem('tempo_user_bookmarks_user_tester_99') || '[]')")
    print("3d. User bookmarks in localStorage:", user_bookmarks_storage)
    assert 'post-1' in user_bookmarks_storage

    # 3e. Test duplicate prevention
    eval_js("""
        window.TempoCommunity.saveUserBookmarks(['post-1', 'post-1', 'post-1']);
    """)
    deduped_storage = eval_js("JSON.parse(localStorage.getItem('tempo_user_bookmarks_user_tester_99') || '[]')")
    print("3e. Deduplicated storage length:", len(deduped_storage))
    assert len(deduped_storage) == 1

    # 4. Test Comment Symbol Behavior
    print("\n--- TEST: Comment Action ---")
    # 4a. Two-column post: focus input
    eval_js("window.TempoCommunity.focusCommentInput('post-1');")
    time.sleep(0.2)
    active_el_id = eval_js("document.activeElement ? document.activeElement.id : null")
    print("4a. Active element after clicking comment on post-1:", active_el_id)
    assert active_el_id == 'input-comment-post-1', "Should focus comment input of post-1"

    # 4b. Full-width post (post-2): clicking comment symbol expands comment panel
    is_expanded_before = eval_js("document.getElementById('fullwidth-comments-post-2') !== null")
    print("4b. post-2 comments expanded before click:", is_expanded_before)
    assert is_expanded_before == False, "Comments drawer should be closed initially"

    eval_js("window.TempoCommunity.toggleFullWidthComments('post-2');")
    time.sleep(0.3)
    is_expanded_after = eval_js("document.getElementById('fullwidth-comments-post-2') !== null")
    print("4c. post-2 comments expanded after click:", is_expanded_after)
    assert is_expanded_after == True, "Comments drawer should be open after click"

    # Repeated clicks should not create duplicate comment panels
    eval_js("window.TempoCommunity.focusCommentInput('post-2');")
    time.sleep(0.2)
    panels_count = eval_js("document.querySelectorAll('#fullwidth-comments-post-2').length")
    print("4d. Duplicate panels count:", panels_count)
    assert panels_count == 1, "Only 1 comment drawer should exist"

    # 4e. Submit comment on post-2 and check synchronized count
    initial_comment_count = eval_js("window.TempoCommunity.getPosts().find(p => p.id === 'post-2').commentsCount")
    eval_js("""
        (() => {
            const input = document.getElementById('input-comment-post-2');
            input.value = 'These study backgrounds look so calming and aesthetic!';
            const form = input.closest('form');
            form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        })()
    """)
    time.sleep(0.3)
    new_comment_count = eval_js("window.TempoCommunity.getPosts().find(p => p.id === 'post-2').commentsCount")
    actual_comments_len = eval_js("window.TempoCommunity.getPosts().find(p => p.id === 'post-2').comments.length")
    print(f"4e. post-2 comment count updated: {initial_comment_count} -> {new_comment_count} (array length: {actual_comments_len})")
    assert new_comment_count == initial_comment_count + 1
    assert new_comment_count == actual_comments_len

    # 5. Test Send a Message Symbol (Direct Message to Post Author)
    print("\n--- TEST: Direct Message to Post Author Action ---")
    # 5a. Anonymous author post
    eval_js("""
        window.TempoCommunity.getPosts().unshift({
            id: 'post-anon',
            authorName: 'Anonymous Student',
            authorHandle: '@anonymous',
            timeAgo: 'Just now',
            content: 'Anonymous test post',
            commentsCount: 0,
            comments: [],
            layout: 'two-column'
        });
        window.TempoCommunity.renderCommunityPosts();
    """)
    eval_js("window.TempoCommunity.openDirectMessageToAuthor('post-anon');")
    time.sleep(0.2)
    active_tab = eval_js("window.location.hash")
    print("5a. Hash after anonymous DM attempt:", active_tab)
    assert active_tab == '#community?tab=posts', "Should stay on posts feed"

    # 5b. Self-messaging prevention
    eval_js("""
        window.TempoCommunity.getPosts().unshift({
            id: 'post-mine',
            authorId: 'user_tester_99',
            authorName: 'Tester Student',
            authorHandle: '@tester',
            timeAgo: 'Just now',
            content: 'My own post',
            commentsCount: 0,
            comments: [],
            layout: 'two-column'
        });
        window.TempoCommunity.renderCommunityPosts();
    """)
    eval_js("window.TempoCommunity.openDirectMessageToAuthor('post-mine');")
    time.sleep(0.2)
    active_tab_mine = eval_js("window.location.hash")
    print("5b. Hash after self-messaging attempt:", active_tab_mine)
    assert active_tab_mine == '#community?tab=posts', "Should prevent self-messaging"

    # Clean up test posts
    eval_js("""
        window.TempoCommunity.getPosts().splice(0, 2);
        window.TempoCommunity.renderCommunityPosts();
    """)

    # 5c. Valid DM to post author: post-2 authored by Temposocute
    convs_before_count = eval_js("window.TempoCommunity.getConversations().length")
    eval_js("window.TempoCommunity.openDirectMessageToAuthor('post-2');")
    time.sleep(0.4)

    active_tab_dm = eval_js("window.location.hash")
    print("5c. Active tab after DM click:", active_tab_dm)
    assert active_tab_dm == '#community?tab=messages', "Should navigate to messages view"

    dm_active_recipient = eval_js("document.getElementById('dm-active-name').textContent")
    print("5d. Active conversation recipient name:", dm_active_recipient)
    assert dm_active_recipient == 'Temposocute', "Recipient must be Temposocute"

    messages_in_thread = eval_js("""
        window.TempoCommunity.getConversations().find(c => c.name === 'Temposocute').messages.length
    """)
    print("5e. Messages in new thread (should be 0 without auto-send):", messages_in_thread)
    assert messages_in_thread == 0, "Must not automatically send a message"

    # 5d. Test repeated clicks do NOT create duplicate conversations
    eval_js("window.TempoCommunity.selectTab('posts');")
    time.sleep(0.3)
    eval_js("window.TempoCommunity.openDirectMessageToAuthor('post-2');")
    time.sleep(0.3)
    temposocute_convs = eval_js("""
        window.TempoCommunity.getConversations().filter(c => c.name === 'Temposocute').length
    """)
    print("5f. Conversations with Temposocute count after repeat click:", temposocute_convs)
    assert temposocute_convs == 1, "Should reuse existing conversation without duplicate"

    # Close any open modal
    eval_js("if (window.TempoAuth && typeof window.TempoAuth.closeModal === 'function') window.TempoAuth.closeModal();")
    eval_js("document.querySelectorAll('.modal, [id^=\"modal-\"]').forEach(m => m.classList.add('hidden')); document.body.classList.remove('overflow-hidden');")

    # 6. Capture Clean Screenshots
    eval_js("window.TempoCommunity.selectTab('posts');")
    eval_js("window.TempoCommunity.toggleFullWidthComments('post-2');")
    time.sleep(0.5)

    artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
    capture_screenshot(os.path.join(artifact_dir, "community_posts_action_symbols.png"))

    eval_js("window.TempoCommunity.selectTab('messages');")
    time.sleep(0.5)
    capture_screenshot(os.path.join(artifact_dir, "community_dm_author_opened.png"))

    # Mobile test
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 375,
        "height": 812,
        "deviceScaleFactor": 2,
        "mobile": True
    })
    eval_js("window.TempoCommunity.selectTab('posts');")
    time.sleep(0.5)
    capture_screenshot(os.path.join(artifact_dir, "community_mobile_posts_action_symbols.png"))

    print("\nALL VERIFICATION TESTS COMPLETED AND CLEAN SCREENSHOTS SAVED!")

finally:
    ws.close()
    proc.terminate()
    proc.wait()
