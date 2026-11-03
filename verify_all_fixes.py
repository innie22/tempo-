import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_verify_fixes_')
port = 9465
proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={port}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
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

    print("=== RUNNING TEMPO COMMUNITY VERIFICATION SUITE ===")

    # Clear any previous test localStorage
    eval_js("""
        localStorage.removeItem('tempo_direct_messages');
        localStorage.removeItem('tempo_chat_requests');
        window.TempoCommunity.init();
    """)
    time.sleep(0.3)

    # =========================================================================
    # 1. TEST SEARCH BAR LAYOUT & ZERO OVERLAP
    # =========================================================================
    eval_js("window.TempoApp.navigateTo('community', 'tips');")
    time.sleep(0.4)

    search_geom = eval_js("""
        (() => {
            const input = document.getElementById('tips-search-input');
            const container = input.parentElement;
            const icon = container.querySelector('svg');
            const inRect = input.getBoundingClientRect();
            const icRect = icon.getBoundingClientRect();
            const inCenterY = inRect.top + inRect.height / 2;
            const icCenterY = icRect.top + icRect.height / 2;

            return {
                inputLeft: inRect.left,
                iconRight: icRect.right,
                iconLeft: icRect.left,
                overlap: inRect.left < icRect.right,
                gap: inRect.left - icRect.right,
                verticalDiff: Math.abs(inCenterY - icCenterY),
                inputFontSize: window.getComputedStyle(input).fontSize
            };
        })()
    """)
    print("1a. Tips Search Bar Geometry:", search_geom)
    assert not search_geom['overlap'], "Input must NOT overlap icon!"
    assert search_geom['gap'] >= 5, f"Input text must have clearance from icon, got {search_geom['gap']}px"
    assert search_geom['verticalDiff'] < 4, "Icon and input must be vertically centered"

    # Test typing text into search bar
    eval_js("""
        const input = document.getElementById('tips-search-input');
        input.value = '5-Minute starter';
        window.TempoCommunity.handleTipsSearch(input.value);
    """)
    time.sleep(0.3)
    typed_geom = eval_js("""
        (() => {
            const input = document.getElementById('tips-search-input');
            const icon = input.parentElement.querySelector('svg');
            return input.getBoundingClientRect().left >= icon.getBoundingClientRect().right;
        })()
    """)
    assert typed_geom, "Typed text must not overlap icon!"
    print("1b. Typed text clearance: VERIFIED (PASS)")

    # Test Mobile Viewport Search Bar (390px)
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 390,
        "height": 844,
        "deviceScaleFactor": 2,
        "mobile": True
    })
    time.sleep(0.3)
    mobile_search = eval_js("""
        (() => {
            const input = document.getElementById('tips-search-input');
            const icon = input.parentElement.querySelector('svg');
            const inRect = input.getBoundingClientRect();
            const icRect = icon.getBoundingClientRect();
            return {
                overlap: inRect.left < icRect.right,
                gap: inRect.left - icRect.right,
                width: inRect.width
            };
        })()
    """)
    print("1c. Mobile Search Bar Geometry (390px):", mobile_search)
    assert not mobile_search['overlap'], "Mobile search must not overlap icon!"
    assert mobile_search['width'] > 150, "Mobile search input should have responsive width"

    # Restore Desktop
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 1280,
        "height": 900,
        "deviceScaleFactor": 1,
        "mobile": False
    })
    time.sleep(0.3)

    # =========================================================================
    # 2. TEST TYPOGRAPHY REDUCTION (~5px)
    # =========================================================================
    font_sizes = eval_js("""
        (() => {
            const navItem = document.querySelector('.community-nav-item');
            const backBtn = document.getElementById('btn-community-back');
            const tipTitle = document.querySelector('#tips-cards-grid h3');
            const searchInput = document.getElementById('tips-search-input');

            return {
                navItemFontSize: navItem ? window.getComputedStyle(navItem).fontSize : null,
                backBtnFontSize: backBtn ? window.getComputedStyle(backBtn).fontSize : null,
                tipTitleFontSize: tipTitle ? window.getComputedStyle(tipTitle).fontSize : null,
                searchInputFontSize: searchInput ? window.getComputedStyle(searchInput).fontSize : null
            };
        })()
    """)
    print("2. Computed Font Sizes:", font_sizes)
    # Verify ~14-15px on nav items (was 19-20px)
    nav_px = float(font_sizes['navItemFontSize'].replace('px', ''))
    assert 13.5 <= nav_px <= 16, f"Nav label font size should be ~14-15px, got {nav_px}px"
    # Verify tip title ~13.5-15px (was 18-20px)
    tip_px = float(font_sizes['tipTitleFontSize'].replace('px', ''))
    assert 13 <= tip_px <= 15.5, f"Tip card title font size should be ~14px, got {tip_px}px"
    print("   Typography reduction (~5px reduction): VERIFIED (PASS)")

    # =========================================================================
    # 3. TEST DIRECT MESSAGE EMPTY STATES (NO FABRICATED DATA)
    # =========================================================================
    eval_js("""
        (() => {
            if (window.TempoAuth) {
                window.TempoAuth.getCurrentUser = () => ({ id: 'u_test_clean', email: 'student@tempo.edu' });
            }
            window.TempoCommunity.selectTab('messages');
        })()
    """)
    time.sleep(0.4)

    dm_state = eval_js("""
        (() => {
            const convsList = document.getElementById('dm-conversations-list').innerText;
            const messagesContainer = document.getElementById('dm-messages-container').innerText;
            const activeName = document.getElementById('dm-active-name').innerText;
            const input = document.getElementById('dm-message-input');

            return {
                convCount: window.TempoCommunity.getConversations().length,
                hasFabricatedAdmin: convsList.includes('Tempo Admin'),
                hasFabricatedBadminton: convsList.includes('Go Badmintonnnn'),
                emptyListText: convsList,
                messagesAreaText: messagesContainer,
                activeName,
                inputDisabled: input.disabled
            };
        })()
    """)
    print("3a. DM Empty State Analysis:", dm_state)
    assert dm_state['convCount'] == 0, "No conversations should exist by default"
    assert not dm_state['hasFabricatedAdmin'], "Must NOT have fabricated Tempo Admin contact!"
    assert not dm_state['hasFabricatedBadminton'], "Must NOT have fabricated Badminton contact!"
    assert 'No conversations yet' in dm_state['emptyListText'], "List must show 'No conversations yet'"
    assert 'No conversation selected' in dm_state['messagesAreaText'], "Message area must show 'No conversation selected'"
    assert dm_state['inputDisabled'], "Input must be disabled when no conversation is selected"
    print("   Clean empty DM state without fabricated data: VERIFIED (PASS)")

    # =========================================================================
    # 4. TEST CHAT REQUESTS (EXACT ASSET, OPEN, EMPTY, ACCEPT/DECLINE)
    # =========================================================================
    symbol_src = eval_js("""
        (() => {
            const btn = document.getElementById('btn-dm-chat-requests');
            const img = btn ? btn.querySelector('img') : null;
            return img ? img.getAttribute('src') : null;
        })()
    """)
    print("4a. Chat Requests Symbol Asset:", symbol_src)
    assert symbol_src == 'assets/chat_requests_icon.png', f"Must use exact supplied asset, got {symbol_src}"

    # Click to open Chat Requests modal
    eval_js("window.TempoCommunity.openChatRequests();")
    time.sleep(0.3)
    modal_open = eval_js("!document.getElementById('modal-chat-requests').classList.contains('hidden')")
    empty_req_text = eval_js("document.getElementById('chat-requests-empty').innerText")
    print("4b. Chat Requests Modal Open:", modal_open, "| Empty State:", empty_req_text.strip())
    assert modal_open, "Modal must be open"
    assert "No pending chat requests" in empty_req_text, "Empty state must display 'No pending chat requests'"

    # Test adding a real incoming chat request
    eval_js("""
        window.TempoCommunity.addChatRequest({
            id: 'req-test-1',
            senderName: 'Linh Nguyen',
            role: 'Peer Mentor · Psychology',
            message: 'Hi! I saw your note about deadline stress. Happy to help you organize.',
            avatar: 'assets/tempo-logo.png'
        });
    """)
    time.sleep(0.3)
    req_count = eval_js("document.querySelectorAll('#chat-requests-list > div').length")
    print("4c. Chat Requests list with pending request:", req_count)
    assert req_count == 1, "Should render 1 pending request"

    # Test accepting the request -> establishes conversation!
    eval_js("window.TempoCommunity.acceptChatRequest('req-test-1');")
    time.sleep(0.3)
    post_accept = eval_js("""
        (() => {
            const convs = window.TempoCommunity.getConversations();
            const activeName = document.getElementById('dm-active-name').innerText;
            const messages = document.querySelectorAll('#dm-messages-container > div').length;
            const input = document.getElementById('dm-message-input');

            return {
                convsLength: convs.length,
                activeName,
                messagesCount: messages,
                inputEnabled: !input.disabled
            };
        })()
    """)
    print("4d. Post-Accept Conversation Status:", post_accept)
    assert post_accept['convsLength'] == 1, "Conversation should be created after accepting request"
    assert 'Linh Nguyen' in post_accept['activeName'], "Active conversation should be set to Linh Nguyen"
    assert post_accept['inputEnabled'], "Message input should now be enabled"
    assert post_accept['messagesCount'] == 1, "Introductory message from request should be rendered"
    print("   Chat Requests symbol, empty state, and accept workflow: VERIFIED (PASS)")

    # =========================================================================
    # 5. TEST POSTS NAVIGATION (CANONICAL MAIN NEWSFEED RETURN)
    # =========================================================================
    eval_js("window.TempoApp.navigateTo('community', 'posts');")
    time.sleep(0.3)

    # 5a. Navigate to "Your posts" filter
    eval_js("window.TempoCommunity.filterMyPosts();")
    time.sleep(0.2)
    # Now click sidebar Posts
    eval_js("window.TempoCommunity.navigateToPostsFeed();")
    time.sleep(0.3)
    feed_state1 = eval_js("""
        (() => {
            return {
                postsCount: document.querySelectorAll('#community-feed-posts-list > div').length,
                currentTab: window.location.hash
            };
        })()
    """)
    print("5a. From 'Your posts' -> Click sidebar Posts:", feed_state1)
    assert feed_state1['postsCount'] >= 2, "Must return to full canonical newsfeed (not filtered to my posts)"
    assert feed_state1['currentTab'] == '#community?tab=posts', "Hash must be #community?tab=posts"

    # 5b. Navigate to "Bookmarks" filter
    eval_js("window.TempoCommunity.filterBookmarkedPosts();")
    time.sleep(0.2)
    eval_js("window.TempoCommunity.navigateToPostsFeed();")
    time.sleep(0.3)
    feed_state2 = eval_js("document.querySelectorAll('#community-feed-posts-list > div').length")
    print("5b. From 'Bookmarks' -> Click sidebar Posts count:", feed_state2)
    assert feed_state2 >= 2, "Must return to full canonical newsfeed (not filtered to bookmarks)"

    # 5c. Search typed in posts search
    eval_js("""
        document.getElementById('posts-search-input').value = 'xyznonexistent';
        window.TempoCommunity.handlePostsSearch('xyznonexistent');
    """)
    time.sleep(0.2)
    filtered_cnt = eval_js("document.querySelectorAll('#community-feed-posts-list > div').length")
    assert filtered_cnt == 0, "Filtered search should be 0"

    # Click sidebar Posts -> clears search and returns to full feed!
    eval_js("window.TempoCommunity.navigateToPostsFeed();")
    time.sleep(0.3)
    cleared_search_val = eval_js("document.getElementById('posts-search-input').value")
    feed_state3 = eval_js("document.querySelectorAll('#community-feed-posts-list > div').length")
    print("5c. From Search Filter -> Click sidebar Posts:", {"searchVal": cleared_search_val, "feedCount": feed_state3})
    assert cleared_search_val == '', "Search input must be cleared"
    assert feed_state3 >= 2, "Full feed must be restored"

    # 5d. While Create Post modal is open
    eval_js("window.TempoCommunity.openCreatePostModal();")
    time.sleep(0.2)
    modal_was_open = eval_js("!document.getElementById('modal-create-post').classList.contains('hidden')")
    assert modal_was_open, "Modal should be open"
    eval_js("window.TempoCommunity.navigateToPostsFeed();")
    time.sleep(0.3)
    modal_now_closed = eval_js("document.getElementById('modal-create-post').classList.contains('hidden')")
    print("5d. From Modal Open -> Click sidebar Posts (Modal closed?):", modal_now_closed)
    assert modal_now_closed, "Modal must be closed when navigating to Posts feed"

    print("\nALL 5 REQUIRED SCENARIOS HAVE BEEN RIGOROUSLY TESTED AND PASSED 100%!")

finally:
    proc.terminate()
