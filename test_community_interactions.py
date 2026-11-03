import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import base64
import os

user_data_dir = tempfile.mkdtemp(prefix='tempo_test_')
port = 9453
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
time.sleep(2)

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

    print("Testing Tempo Community Interactions...")

    # 1. Test Navigation to Community
    eval_js("window.TempoApp.navigateTo('community');")
    time.sleep(0.5)
    current_tab = eval_js("window.TempoApp.getCurrentTab()")
    print("1. Current tab:", current_tab)
    assert current_tab == 'community', "Should be on community tab"

    # 2. Test Announcements Count & Content
    ann_count = eval_js("document.querySelectorAll('#community-announcements-list > div').length")
    print("2. Announcements count:", ann_count)
    assert ann_count >= 2, "Should render at least 2 announcements"

    # 3. Test Tips Search
    eval_js("window.TempoCommunity.selectTab('tips');")
    time.sleep(0.3)
    tips_all_count = eval_js("document.querySelectorAll('#tips-cards-grid > div').length")
    print("3a. Tips total count:", tips_all_count)
    assert tips_all_count >= 2, "Should have tips rendered"

    eval_js("window.TempoCommunity.handleTipsSearch('5-Minute');")
    time.sleep(0.3)
    tips_filtered_count = eval_js("document.querySelectorAll('#tips-cards-grid > div').length")
    print("3b. Filtered tips ('5-Minute'):", tips_filtered_count)
    assert tips_filtered_count >= 1, "Should filter tips correctly"
    eval_js("window.TempoCommunity.clearTipsSearch();")

    # 4. Test Learn Tab & Search
    eval_js("window.TempoCommunity.selectTab('learn');")
    time.sleep(0.3)
    learn_count = eval_js("document.querySelectorAll('#learn-cards-grid > div').length")
    print("4a. Learn total count:", learn_count)
    assert learn_count >= 2, "Should have learn cards rendered"

    eval_js("window.TempoCommunity.handleLearnSearch('eating');")
    time.sleep(0.3)
    learn_filtered = eval_js("document.querySelectorAll('#learn-cards-grid > div').length")
    print("4b. Filtered learn ('eating'):", learn_filtered)
    assert learn_filtered == 1, "Should filter learn cards correctly"
    eval_js("window.TempoCommunity.clearLearnSearch();")

    # 5. Test Posts Feed, Like Toggle, and Bookmark Toggle
    eval_js("window.TempoCommunity.selectTab('posts');")
    time.sleep(0.3)
    posts_count = eval_js("document.querySelectorAll('#community-feed-posts-list > div').length")
    print("5a. Posts count:", posts_count)
    assert posts_count >= 2, "Should have community posts rendered"

    initial_likes = eval_js("window.TempoCommunity.getPosts()[0].likes")
    eval_js("window.TempoCommunity.toggleLike(window.TempoCommunity.getPosts()[0].id);")
    time.sleep(0.3)
    new_likes = eval_js("window.TempoCommunity.getPosts()[0].likes")
    print(f"5b. Like toggle: {initial_likes} -> {new_likes}")
    assert new_likes == initial_likes + 1, "Like count should increase"

    # 6. Test Inline Comment on Post
    first_post_id = eval_js("window.TempoCommunity.getPosts()[0].id")
    eval_js(f"""
        (() => {{
            const input = document.getElementById('input-comment-{first_post_id}');
            if (input) input.value = 'Great reminder! Fighting!';
            const form = input.closest('form');
            if (form) form.dispatchEvent(new Event('submit', {{ cancelable: true, bubbles: true }}));
        }})();
    """)
    time.sleep(0.3)
    comments_count = eval_js(f"window.TempoCommunity.getPosts().find(p => p.id === '{first_post_id}').comments.length")
    print("6. Comments count after reply:", comments_count)
    assert comments_count >= 3, "New reply should be added to comments"

    # 7. Test Create Post Modal
    eval_js("window.TempoCommunity.openCreatePostModal();")
    time.sleep(0.3)
    modal_open = eval_js("!document.getElementById('modal-create-post').classList.contains('hidden')")
    print("7a. Modal open:", modal_open)
    assert modal_open, "Modal create post should be visible"

    eval_js("""
        document.getElementById('input-modal-post-content').value = 'Test post for Tempo Community!';
        document.getElementById('form-modal-create-post').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    """)
    time.sleep(0.3)
    modal_closed = eval_js("document.getElementById('modal-create-post').classList.contains('hidden')")
    print("7b. Modal closed after submit:", modal_closed)
    assert modal_closed, "Modal should close on submit"

    new_posts_count = eval_js("window.TempoCommunity.getPosts().length")
    print("7c. Total posts count after new post:", new_posts_count)
    assert new_posts_count > posts_count, "New post should be added to posts feed"

    # 8. Test Direct Messages
    eval_js("""
        (() => {
            if (window.TempoAuth) {
                window.TempoAuth.getCurrentUser = () => ({ id: 'u1', email: 'student@tempo.edu' });
            }
            window.TempoCommunity.selectTab('messages');
        })()
    """)
    time.sleep(0.3)
    active_chat_name = eval_js("document.getElementById('dm-active-name').textContent")
    print("8a. Active DM contact name:", active_chat_name)
    assert 'Badminton' in active_chat_name or 'Elena' in active_chat_name or 'Admin' in active_chat_name, "Active DM should be loaded"

    # Send a message in DM
    eval_js("""
        (() => {
            const input = document.getElementById('dm-message-input');
            if (input) input.value = 'See everyone on court tomorrow at 5!';
            const form = document.getElementById('dm-message-form');
            if (form) form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        })()
    """)
    time.sleep(0.3)
    messages_rendered = eval_js("document.querySelectorAll('#dm-messages-container > div').length")
    print("8b. Messages count in active chat:", messages_rendered)
    assert messages_rendered >= 3, "New message should be added and rendered in active thread"

    # 9. Test Return Home Navigation
    eval_js("window.TempoCommunity.handleReturnNavigation();")
    time.sleep(0.3)
    return_tab = eval_js("window.TempoApp.getCurrentTab()")
    print("9. Tab after Return Home:", return_tab)
    assert return_tab in ['home', 'today', 'daily', 'recovery-mode', 'emergency-support'], f"Should return to valid tab, got: {return_tab}"

    print("\nALL 9 FUNCTIONAL TESTS PASSED PERFECTLY!")

finally:
    proc.terminate()
