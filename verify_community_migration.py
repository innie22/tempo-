import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import sys
import base64
import os

user_data_dir = tempfile.mkdtemp(prefix='tempo_comm_test_')
port = 9438
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
        if "exceptionDetails" in res:
            print("JS Exception:", res["exceptionDetails"])
        return res.get('result', {}).get('value')

    def save_screenshot(path):
        data = send_cmd("Page.captureScreenshot", {"format": "png"})
        b64 = data.get("data", "")
        if b64:
            with open(path, "wb") as f:
                f.write(base64.b64decode(b64))
            print(f"Saved screenshot: {path}")

    send_cmd('Page.enable')

    # Wait for Tempo app initialization
    for _ in range(30):
        if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoCommunity !== 'undefined'"):
            break
        time.sleep(0.5)

    print("=== STARTING TEMPO COMMUNITY VERIFICATION SUITE ===")
    test_results = {}

    # Test 1: Navigation integrity
    print("\n[Test 1] Primary Navigation Audit:")
    nav_links = eval_js("""
        (() => {
            const nav = document.querySelector('header nav');
            const links = Array.from(nav.querySelectorAll('a:not(.hidden)')).map(a => ({
                id: a.id,
                text: a.textContent.trim(),
                href: a.getAttribute('href')
            }));
            const hasLearn = !!document.getElementById('nav-link-learn');
            const commLink = document.getElementById('nav-link-community');
            const mobileCommLink = document.querySelector('nav.md\\\\:hidden a[href="#community"]');
            return { links, hasLearn, hasComm: !!commLink, mobileComm: !!mobileCommLink };
        })()
    """)
    print("Desktop nav links:", nav_links['links'])
    print("Has standalone Learn link:", nav_links['hasLearn'])
    print("Has Community link:", nav_links['hasComm'])
    print("Has Mobile Community link:", nav_links['mobileComm'])
    
    t1_pass = not nav_links['hasLearn'] and nav_links['hasComm'] and nav_links['mobileComm']
    test_results['1_primary_navigation'] = t1_pass
    print("Result Test 1:", "PASS" if t1_pass else "FAIL")

    # Test 2: Navigate to Community
    print("\n[Test 2] Navigate to Community screen:")
    eval_js("window.TempoApp.navigateTo('community');")
    time.sleep(0.5)
    comm_state = eval_js("""
        (() => {
            const screen = document.getElementById('screen-community');
            const isVisible = screen && !screen.classList.contains('hidden');
            const activeTab = window.TempoCommunity.getActiveTab();
            const announcementPanel = document.getElementById('community-panel-announcement');
            const isAnnVisible = announcementPanel && !announcementPanel.classList.contains('hidden');
            return { isVisible, activeTab, isAnnVisible };
        })()
    """)
    print("Community screen visible:", comm_state['isVisible'])
    print("Active tab default:", comm_state['activeTab'])
    print("Announcement panel visible:", comm_state['isAnnVisible'])
    t2_pass = comm_state['isVisible'] and comm_state['activeTab'] == 'announcement' and comm_state['isAnnVisible']
    test_results['2_navigate_community'] = t2_pass
    print("Result Test 2:", "PASS" if t2_pass else "FAIL")

    # Test 3: Announcement features & details
    print("\n[Test 3] Announcement Cards & Detail Modal:")
    ann_data = eval_js("""
        (() => {
            const cards = document.querySelectorAll('#community-announcements-list [data-announcement-id]');
            const count = cards.length;
            const firstTitle = cards[0]?.querySelector('h3')?.textContent?.trim();
            // Test opening detail modal
            window.TempoCommunity.openAnnouncementDetail('ann-1');
            const modal = document.getElementById('modal-announcement-detail');
            const modalOpen = modal && !modal.classList.contains('hidden');
            const modalTitle = document.getElementById('announcement-modal-title')?.textContent?.trim();
            const actionBtn = document.getElementById('announcement-modal-action');
            const hasAction = actionBtn && !actionBtn.classList.contains('hidden');
            window.TempoCommunity.closeAnnouncementDetail();
            const modalClosed = modal && modal.classList.contains('hidden');
            return { count, firstTitle, modalOpen, modalTitle, hasAction, modalClosed };
        })()
    """)
    print("Announcement cards count:", ann_data['count'])
    print("Announcement modal opened:", ann_data['modalOpen'])
    print("Modal title matches:", ann_data['modalTitle'])
    print("Modal action button exists:", ann_data['hasAction'])
    print("Modal closed cleanly:", ann_data['modalClosed'])
    t3_pass = ann_data['count'] >= 3 and ann_data['modalOpen'] and ann_data['modalClosed']
    test_results['3_announcement_features'] = t3_pass
    print("Result Test 3:", "PASS" if t3_pass else "FAIL")

    # Test 4: Announcement Permissions Enforcement (Admin vs Non-admin)
    print("\n[Test 4] Announcement Permissions Enforcement:")
    perm_test = eval_js("""
        (() => {
            // Student role:
            window.TempoApp.setRole('student');
            window.TempoCommunity.selectTab('announcement');
            const studentBtnVisible = !document.getElementById('btn-admin-new-announcement')?.classList.contains('hidden');
            
            // Try to create as non-admin programmatically:
            const initialCount = window.TempoCommunity.getAnnouncements().length;
            window.TempoCommunity.handleCreateAnnouncement();
            const countAfterNonAdmin = window.TempoCommunity.getAnnouncements().length;

            // Admin role:
            window.TempoApp.setRole('admin');
            window.TempoCommunity.selectTab('announcement');
            const adminBtnVisible = !document.getElementById('btn-admin-new-announcement')?.classList.contains('hidden');

            // Switch back to student for regular user tests
            window.TempoApp.setRole('student');

            return { studentBtnVisible, adminBtnVisible, countBlocked: initialCount === countAfterNonAdmin };
        })()
    """)
    print("Student sees admin button (should be False):", perm_test['studentBtnVisible'])
    print("Admin sees admin button (should be True):", perm_test['adminBtnVisible'])
    print("Unauthorized creation blocked:", perm_test['countBlocked'])
    t4_pass = not perm_test['studentBtnVisible'] and perm_test['adminBtnVisible'] and perm_test['countBlocked']
    test_results['4_announcement_permissions'] = t4_pass
    print("Result Test 4:", "PASS" if t4_pass else "FAIL")

    # Test 5: Tips (Solve) Tab, Categories & Search
    print("\n[Test 5] Tips (Solve) Tab:")
    eval_js("window.TempoCommunity.selectTab('tips');")
    time.sleep(0.5)
    tips_test = eval_js("""
        (() => {
            const panel = document.getElementById('community-panel-tips');
            const isVisible = panel && !panel.classList.contains('hidden');
            const initialCards = document.querySelectorAll('#tips-cards-grid > div').length;

            // Filter category to study
            window.TempoCommunity.filterTipsCategory('study');
            const studyCards = document.querySelectorAll('#tips-cards-grid > div').length;

            // Search for 'deadline'
            window.TempoCommunity.filterTipsCategory('all');
            window.TempoCommunity.handleTipsSearch('deadline');
            const searchCards = document.querySelectorAll('#tips-cards-grid > div').length;
            
            // Reset search
            window.TempoCommunity.clearTipsSearch();
            const resetCards = document.querySelectorAll('#tips-cards-grid > div').length;

            // Test opening situation step modal
            window.TempoLearnSolve.openModal('deadline_pileup');
            const modal = document.getElementById('tempo-learn-solve-modal');
            const modalOpen = modal && !modal.classList.contains('hidden');
            const modalTitle = modal?.querySelector('h3')?.textContent?.trim();
            window.TempoLearnSolve.closeModal();

            return { isVisible, initialCards, studyCards, searchCards, resetCards, modalOpen, modalTitle };
        })()
    """)
    print("Tips panel visible:", tips_test['isVisible'])
    print("Initial tips cards count:", tips_test['initialCards'])
    print("Study filtered count:", tips_test['studyCards'])
    print("Search 'deadline' count:", tips_test['searchCards'])
    print("Step modal opened:", tips_test['modalOpen'])
    print("Step modal title:", tips_test['modalTitle'])
    t5_pass = tips_test['isVisible'] and tips_test['initialCards'] > 0 and tips_test['searchCards'] > 0 and tips_test['modalOpen']
    test_results['5_tips_solve'] = t5_pass
    print("Result Test 5:", "PASS" if t5_pass else "FAIL")

    # Test 6: Learn Tab & Search
    print("\n[Test 6] Learn Tab & Knowledge Topics:")
    eval_js("window.TempoCommunity.selectTab('learn');")
    time.sleep(0.5)
    learn_test = eval_js("""
        (() => {
            const panel = document.getElementById('community-panel-learn');
            const isVisible = panel && !panel.classList.contains('hidden');
            const initialCards = document.querySelectorAll('#learn-cards-grid > div').length;

            // Search for 'loop'
            window.TempoCommunity.handleLearnSearch('loop');
            const searchCards = document.querySelectorAll('#learn-cards-grid > div').length;

            // Clear search
            window.TempoCommunity.clearLearnSearch();
            const resetCards = document.querySelectorAll('#learn-cards-grid > div').length;

            // Open topic modal
            window.TempoLearnSolve.openModal('stress_loop');
            const modal = document.getElementById('tempo-learn-solve-modal');
            const modalOpen = modal && !modal.classList.contains('hidden');
            const modalTitle = modal?.querySelector('h3')?.textContent?.trim();
            window.TempoLearnSolve.closeModal();

            return { isVisible, initialCards, searchCards, resetCards, modalOpen, modalTitle };
        })()
    """)
    print("Learn panel visible:", learn_test['isVisible'])
    print("Initial learn cards count:", learn_test['initialCards'])
    print("Search 'loop' count:", learn_test['searchCards'])
    print("Learn modal opened:", learn_test['modalOpen'])
    print("Learn modal title:", learn_test['modalTitle'])
    t6_pass = learn_test['isVisible'] and learn_test['initialCards'] > 0 and learn_test['modalOpen']
    test_results['6_learn_knowledge'] = t6_pass
    print("Result Test 6:", "PASS" if t6_pass else "FAIL")

    # Test 7: Posts Tab, Creation, Likes, Comments, Bookmarks
    print("\n[Test 7] Posts Feed, Creation, Likes & Bookmarks:")
    eval_js("window.TempoCommunity.selectTab('posts');")
    time.sleep(0.5)
    posts_test = eval_js("""
        (() => {
            const panel = document.getElementById('community-panel-posts');
            const isVisible = panel && !panel.classList.contains('hidden');
            const initialCount = window.TempoCommunity.getPosts().length;

            // 1. Create a post
            const textarea = document.getElementById('community-post-content');
            textarea.value = 'Automated test peer message: Stay hydrated and take small steps!';
            const form = document.getElementById('community-create-post-form');
            window.TempoCommunity.handleCreateCommunityPost();
            const countAfter = window.TempoCommunity.getPosts().length;

            // 2. Toggle like on the new post
            const newPost = window.TempoCommunity.getPosts()[0];
            const likesBefore = newPost.likes;
            window.TempoCommunity.toggleLike(newPost.id);
            const likesAfter = window.TempoCommunity.getPosts()[0].likes;

            // 3. Toggle bookmark
            const bmBefore = window.TempoCommunity.getPosts()[0].isBookmarked;
            window.TempoCommunity.toggleBookmark(newPost.id);
            const bmAfter = window.TempoCommunity.getPosts()[0].isBookmarked;

            // 4. Add comment
            window.TempoCommunity.togglePostCommentsExpand(newPost.id);
            const inputComment = document.getElementById('input-comment-' + newPost.id);
            if (inputComment) inputComment.value = 'Great reminder, thank you!';
            window.TempoCommunity.handleInlineCommentSubmit(null, newPost.id);
            const commentsCount = window.TempoCommunity.getPosts()[0].comments.length;

            return { isVisible, created: countAfter === initialCount + 1, liked: likesAfter === likesBefore + 1, bookmarked: bmAfter && !bmBefore, commentsCount };
        })()
    """)
    print("Posts panel visible:", posts_test['isVisible'])
    print("New post created:", posts_test['created'])
    print("Post like toggled:", posts_test['liked'])
    print("Post bookmarked:", posts_test['bookmarked'])
    print("Post comments count:", posts_test['commentsCount'])
    t7_pass = posts_test['isVisible'] and posts_test['created'] and posts_test['liked'] and posts_test['bookmarked'] and posts_test['commentsCount'] >= 1
    test_results['7_posts_interactions'] = t7_pass
    print("Result Test 7:", "PASS" if t7_pass else "FAIL")

    # Test 8: Direct Message (Guest State vs Authenticated State)
    print("\n[Test 8] Direct Messages Gating & Live Messaging:")
    eval_js("window.TempoCommunity.selectTab('messages');")
    time.sleep(0.5)
    dm_guest = eval_js("""
        (() => {
            const guestView = document.getElementById('community-dm-guest-view');
            const authView = document.getElementById('community-dm-auth-view');
            return {
                guestVisible: guestView && !guestView.classList.contains('hidden'),
                authHidden: authView && authView.classList.contains('hidden')
            };
        })()
    """)
    print("Guest sign-in prompt visible for unauthenticated user:", dm_guest['guestVisible'])

    # Mock user login to test full authenticated DM interface
    eval_js("""
        (() => {
            if (window.TempoAuth) {
                window.TempoAuth.__orig_getUser = window.TempoAuth.getCurrentUser;
                window.TempoAuth.getCurrentUser = () => ({ id: 'test-user-123', email: 'student@tempo.edu' });
            }
            window.TempoCommunity.renderMessagesView();
        })()
    """)
    time.sleep(0.5)
    dm_auth = eval_js("""
        (() => {
            const guestView = document.getElementById('community-dm-guest-view');
            const authView = document.getElementById('community-dm-auth-view');
            const convsCount = document.querySelectorAll('#dm-conversations-list > div').length;
            const activeName = document.getElementById('dm-active-name')?.textContent?.trim();

            // Send a test message
            const input = document.getElementById('dm-message-input');
            input.value = 'Hello Dr. Vance, testing live DM message transmission.';
            window.TempoCommunity.handleSendMessage();
            const messages = Array.from(document.querySelectorAll('#dm-messages-container > div')).map(m => m.textContent);
            const lastMsg = messages[messages.length - 1];

            // Restore TempoAuth
            if (window.TempoAuth && window.TempoAuth.__orig_getUser) {
                window.TempoAuth.getCurrentUser = window.TempoAuth.__orig_getUser;
            }

            return {
                authVisible: authView && !authView.classList.contains('hidden'),
                guestHidden: guestView && guestView.classList.contains('hidden'),
                convsCount,
                activeName,
                lastMsgContains: lastMsg && lastMsg.includes('testing live DM')
            };
        })()
    """)
    print("Auth DM interface displayed:", dm_auth['authVisible'])
    print("Conversations count:", dm_auth['convsCount'])
    print("Active contact:", dm_auth['activeName'])
    print("Message successfully sent and rendered in bubble:", dm_auth['lastMsgContains'])
    t8_pass = dm_guest['guestVisible'] and dm_auth['authVisible'] and dm_auth['convsCount'] >= 3 and dm_auth['lastMsgContains']
    test_results['8_direct_messages'] = t8_pass
    print("Result Test 8:", "PASS" if t8_pass else "FAIL")

    # Test 9: Deep Links & Legacy Hash Redirects
    print("\n[Test 9] Deep Links & Backward Compatibility:")
    deep_link_tests = eval_js("""
        (() => {
            const results = {};
            // Test 1: #community?tab=tips
            window.TempoApp.navigateTo('community', 'tips');
            results.tips = window.TempoCommunity.getActiveTab() === 'tips';

            // Test 2: #learn redirect
            window.TempoApp.navigateTo('learn');
            results.learnRedirect = window.TempoCommunity.getActiveTab() === 'learn';

            // Test 3: #solve redirect
            window.TempoApp.navigateTo('solve');
            results.solveRedirect = window.TempoCommunity.getActiveTab() === 'tips';

            // Test 4: #posts redirect
            window.TempoApp.navigateTo('posts');
            results.postsRedirect = window.TempoCommunity.getActiveTab() === 'posts';

            // Test 5: #direct-messages redirect
            window.TempoApp.navigateTo('direct-messages');
            results.dmRedirect = window.TempoCommunity.getActiveTab() === 'messages';

            return results;
        })()
    """)
    print("Deep link results:", deep_link_tests)
    t9_pass = all(deep_link_tests.values())
    test_results['9_deep_links'] = t9_pass
    print("Result Test 9:", "PASS" if t9_pass else "FAIL")

    # Test 10: Return Navigation Context
    print("\n[Test 10] Return Navigation Context (Mode preservation):")
    return_test = eval_js("""
        (() => {
            // Mock sourceContext from recovery mode
            if (window.TempoMode && typeof window.TempoMode.setSourceContext === 'function') {
                window.TempoMode.setSourceContext('recovery');
            }
            window.TempoApp.navigateTo('community');
            const labelRecovery = document.getElementById('community-back-label')?.textContent?.trim();

            // Test clicking return button
            window.TempoCommunity.handleReturnNavigation();

            // From Today / Entry
            if (window.TempoMode && typeof window.TempoMode.setSourceContext === 'function') {
                window.TempoMode.setSourceContext('entry');
            }
            window.TempoApp.navigateTo('today');
            window.TempoApp.navigateTo('community');
            const labelToday = document.getElementById('community-back-label')?.textContent?.trim();

            return { labelRecovery, labelToday };
        })()
    """)
    print("Label when from Recovery:", return_test['labelRecovery'])
    print("Label when from Today:", return_test['labelToday'])
    t10_pass = 'Recovery' in return_test['labelRecovery'] and 'Today' in return_test['labelToday']
    test_results['10_return_navigation'] = t10_pass
    print("Result Test 10:", "PASS" if t10_pass else "FAIL")

    # Take Screenshot of Community Hub
    eval_js("window.TempoApp.navigateTo('community', 'announcement');")
    time.sleep(1)
    os.makedirs(r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6', exist_ok=True)
    shot_path = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\community_announcement_tab.png'
    save_screenshot(shot_path)

    eval_js("window.TempoCommunity.selectTab('tips');")
    time.sleep(0.5)
    shot_tips = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\community_tips_tab.png'
    save_screenshot(shot_tips)

    eval_js("window.TempoCommunity.selectTab('posts');")
    time.sleep(0.5)
    shot_posts = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\community_posts_tab.png'
    save_screenshot(shot_posts)

    print("\n=== SUMMARY OF TEST RESULTS ===")
    all_passed = True
    for k, v in test_results.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
        if not v: all_passed = False

    print("\nFINAL OVERALL STATUS:", "ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED")

finally:
    proc.terminate()
