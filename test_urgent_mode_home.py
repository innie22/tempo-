import subprocess
import time
import json
import urllib.request
import tempfile
import os
import websocket
import sys

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_urgent_home_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9227
    
    cmd = [
        edge_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "http://localhost:8000/"
    ]
    
    log(f"Launching Edge on port {port}...")
    proc = subprocess.Popen(cmd)
    ws = None
    try:
        ws_url = None
        for _ in range(30):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as resp:
                    tabs = json.loads(resp.read().decode())
                    pages = [t for t in tabs if t.get("type") == "page"]
                    if pages:
                        ws_url = pages[0]["webSocketDebuggerUrl"]
                        break
            except Exception:
                time.sleep(0.5)
        
        if not ws_url:
            raise RuntimeError("Failed to connect to Edge CDP endpoint")
            
        log(f"Connected to CDP: {ws_url}")
        ws = websocket.create_connection(ws_url)
        
        msg_id = 1
        def send_command(method, params=None):
            nonlocal msg_id
            cid = msg_id
            msg_id += 1
            req = {"id": cid, "method": method}
            if params:
                req["params"] = params
            ws.send(json.dumps(req))
            while True:
                raw = ws.recv()
                msg = json.loads(raw)
                if msg.get("id") == cid:
                    if "error" in msg:
                        raise RuntimeError(f"CDP error: {msg['error']}")
                    return msg.get("result", {})

        def eval_js(expr, await_promise=True):
            res = send_command("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": await_promise
            })
            if "exceptionDetails" in res:
                raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        def wait_for_ready():
            for _ in range(40):
                try:
                    ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined' && typeof window.TempoEmergencyFlow !== 'undefined'")
                    if ready:
                        eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("Application failed to become ready")

        log("Waiting for page and scripts ready...")
        wait_for_ready()

        # Helper to set up a clean confirmed plan
        eval_js("""
            window.__setupTestPlan = function() {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
                const tomorrowDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
                const tomorrow = `${tomorrowDate.getFullYear()}-${pad(tomorrowDate.getMonth() + 1)}-${pad(tomorrowDate.getDate())}`;

                const testPlan = {
                    id: 'plan_urgent_test_101',
                    planId: 'plan_urgent_test_101',
                    planType: 'emergency',
                    title: 'Urgent Plan',
                    plannedTasks: [
                        {
                            dayDate: today,
                            dayLabel: 'Today',
                            startTime: '10:00 AM',
                            endTime: '11:00 AM',
                            executionBadge: 'DO THIS FIRST',
                            task: {
                                id: 'task-u1',
                                name: 'Marketing Report',
                                description: 'Finish competitor analysis section',
                                hasDeadline: true,
                                deadlineDate: today,
                                deadlineTime: '22:00',
                                durationLabel: '45 min',
                                durationMinutes: 45,
                                completed: false,
                                isInProgress: false,
                                subtasks: [
                                    { id: 'sub-u1', title: 'Finish competitor analysis section', completed: false },
                                    { id: 'sub-u2', title: 'Compile market share graph', completed: false },
                                    { id: 'sub-u3', title: 'Final proofread', completed: true }
                                ]
                            }
                        },
                        {
                            dayDate: today,
                            dayLabel: 'Today',
                            startTime: '02:00 PM',
                            endTime: '03:00 PM',
                            executionBadge: 'THEN',
                            task: {
                                id: 'task-u2',
                                name: 'Read chapter 4',
                                description: 'Read textbook pages 120-145',
                                hasDeadline: false,
                                durationLabel: '30 min',
                                durationMinutes: 30,
                                completed: true,
                                isInProgress: false,
                                subtasks: []
                            }
                        },
                        {
                            dayDate: today,
                            dayLabel: 'Today',
                            startTime: '04:00 PM',
                            endTime: '05:00 PM',
                            executionBadge: 'LATER',
                            task: {
                                id: 'task-u3',
                                name: 'Prepare slides',
                                description: 'Create 5 slides for presentation',
                                hasDeadline: false,
                                durationLabel: '1 hr',
                                durationMinutes: 60,
                                completed: false,
                                isInProgress: false,
                                subtasks: []
                            }
                        },
                        {
                            dayDate: tomorrow,
                            dayLabel: 'Tomorrow',
                            startTime: '09:00 AM',
                            endTime: '10:00 AM',
                            executionBadge: 'DO THIS FIRST',
                            task: {
                                id: 'task-u4',
                                name: 'Tomorrow Lab writeup',
                                description: 'Draft lab conclusions',
                                hasDeadline: false,
                                durationLabel: '1 hr',
                                durationMinutes: 60,
                                completed: false,
                                isInProgress: false,
                                subtasks: []
                            }
                        }
                    ],
                    tasks: [],
                    availabilityDays: [
                        { date: today, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] },
                        { date: tomorrow, label: 'Tomorrow', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }
                    ]
                };
                testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);

                // Seed into both TempoEmergencyFlow and TempoPlanStore
                if (window.TempoPlanStore && window.TempoPlanStore.saveActivePlan) {
                    window.TempoPlanStore.saveActivePlan('emergency', testPlan);
                }
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
                }
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.restorePlanState) {
                    window.TempoEmergencyFlow.restorePlanState();
                }

                // Switch to emergency mode
                window.TempoMode.setMode('emergency');
                window.TempoApp.navigateTo('today');
                window.TempoMode.renderEmodeHome();
                return { today, tomorrow };
            };
        """)

        # =====================================================================
        # TEST 1: Header, Date, Greeting, and Mode Dropdown
        # =====================================================================
        log("\n--- TEST 1: Header, Date, Greeting, and Mode Dropdown ---")
        eval_js("window.__setupTestPlan();")

        header_info = eval_js("""
            (() => {
                const btn = document.getElementById('btn-home-mode-selector');
                const dropdown = document.getElementById('home-mode-selector-dropdown');
                const h1 = document.querySelector('#emode-home-content h1');
                const ambientRing = document.querySelector('.urgent-ambient-ring');

                return {
                    btnExists: !!btn,
                    btnText: btn ? btn.textContent.trim() : '',
                    dropdownExists: !!dropdown,
                    dropdownHidden: dropdown ? dropdown.classList.contains('hidden') : false,
                    h1Exists: !!h1,
                    h1Text: h1 ? h1.textContent.trim() : '',
                    ringHidden: ambientRing ? (window.getComputedStyle(ambientRing).display === 'none') : true
                };
            })()
        """)

        assert header_info['btnExists'], "Mode selector button #btn-home-mode-selector should exist"
        assert any(m in header_info['btnText'] for m in ["Urgent Mode", "Chế độ Khẩn"]), f"Button should say 'Urgent Mode' or 'Chế độ Khẩn', got: {header_info['btnText']}"
        assert "⚡" in header_info['btnText'], "Button should display lightning icon ⚡"
        assert not header_info['h1Exists'], f"Large hero H1 should NOT exist in Urgent Mode Home, found: {header_info['h1Text']}"
        assert header_info['ringHidden'], "Oversized decorative hero ring must be removed/hidden"
        log("✓ Compact top utility row and hero removal verified.")

        # Test Opening & Closing the Dropdown
        dropdown_state = eval_js("""
            (() => {
                // Click trigger to open
                const btn = document.getElementById('btn-home-mode-selector');
                btn.click();
                const dropdown = document.getElementById('home-mode-selector-dropdown');
                const isOpen = !dropdown.classList.contains('hidden');
                const itemsCount = dropdown.querySelectorAll('[role=\"menuitem\"]').length;
                const dropdownText = dropdown.textContent;

                // Press Escape to close
                window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
                const isClosed = dropdown.classList.contains('hidden');

                return { isOpen, itemsCount, dropdownText, isClosed };
            })()
        """)

        assert dropdown_state['isOpen'], "Dropdown should open on button click"
        # Popover does NOT repeat Urgent Mode; lists Recovery, Unclear, and Take a break
        assert dropdown_state['itemsCount'] == 3, f"Dropdown should contain 3 destination items, got: {dropdown_state['itemsCount']}"
        assert not any(m in dropdown_state['dropdownText'] for m in ["⚡ Urgent Mode", "⚡ Chế độ Khẩn"]), "Dropdown popover should NOT redundantly list active Urgent Mode"
        assert any(m in dropdown_state['dropdownText'] for m in ["Recovery Mode", "Chế độ Hồi phục", "Chế độ Phục hồi"]), "Dropdown should list Recovery Mode"
        assert any(m in dropdown_state['dropdownText'] for m in ["Unclear Mode", "Chế độ Chưa rõ"]), "Dropdown should list Unclear Mode"
        assert any(m in dropdown_state['dropdownText'] for m in ["Take a break from modes", "Tạm nghỉ các chế độ", "Tạm nghỉ"]), "Dropdown should list Take a break from modes"
        assert dropdown_state['isClosed'], "Dropdown should close on Escape key"
        log("✓ Mode dropdown opening, destination options (excluding active mode), and keyboard closing verified.")

        # Test Safe Display Name Helper (getSafeGreetingInfo)
        name_tests = eval_js("""
            (() => {
                const fn = window.TempoMode.getSafeGreetingInfo;
                if (!fn) return { error: 'getSafeGreetingInfo not exported' };

                return {
                    fallbackNull: fn(null),
                    rawDigits: fn({ full_name: 'nguyenyennhidang62' }),
                    emailFormat: fn({ full_name: 'john.smith@school.edu' }),
                    technicalSymbols: fn({ full_name: 'jane_doe' }),
                    overlyLong: fn({ full_name: 'supercalifragilistic' }),
                    cleanFullName: fn({ full_name: 'Sarah Connor' }),
                    cleanPrefName: fn({ preferred_name: 'Alex' }),
                    cleanDisplayName: fn({ display_name: 'Jordan' })
                };
            })()
        """)

        assert name_tests['fallbackNull']['isFallback'] and any(g in name_tests['fallbackNull']['greetingText'] for g in ['Hi there', 'Chào bạn']), f"Null profile failed: {name_tests['fallbackNull']}"
        assert name_tests['rawDigits']['isFallback'] and any(g in name_tests['rawDigits']['greetingText'] for g in ['Hi there', 'Chào bạn']), f"Raw digits failed: {name_tests['rawDigits']}"
        assert name_tests['emailFormat']['isFallback'] and any(g in name_tests['emailFormat']['greetingText'] for g in ['Hi there', 'Chào bạn']), f"Email format failed: {name_tests['emailFormat']}"
        assert name_tests['technicalSymbols']['isFallback'] and any(g in name_tests['technicalSymbols']['greetingText'] for g in ['Hi there', 'Chào bạn']), f"Technical symbols failed: {name_tests['technicalSymbols']}"
        assert name_tests['overlyLong']['isFallback'] and any(g in name_tests['overlyLong']['greetingText'] for g in ['Hi there', 'Chào bạn']), f"Overly long name failed: {name_tests['overlyLong']}"
        assert not name_tests['cleanFullName']['isFallback'] and any(g in name_tests['cleanFullName']['greetingText'] for g in ['Hi, Sarah', 'Chào Sarah']), f"Clean full name failed: {name_tests['cleanFullName']}"
        assert not name_tests['cleanPrefName']['isFallback'] and any(g in name_tests['cleanPrefName']['greetingText'] for g in ['Hi, Alex', 'Chào Alex']), f"Preferred name failed: {name_tests['cleanPrefName']}"
        assert not name_tests['cleanDisplayName']['isFallback'] and any(g in name_tests['cleanDisplayName']['greetingText'] for g in ['Hi, Jordan', 'Chào Jordan']), f"Display name failed: {name_tests['cleanDisplayName']}"
        log("✓ Safe display name resolution and sanitization rules verified.")

        # =====================================================================
        # TEST 2: Priority #1 "Your Task for Now"
        # =====================================================================
        log("\n--- TEST 2: Priority #1 'Your Task for Now' ---")
        now_info = eval_js("""
            (() => {
                const nowCard = document.querySelector('.urgent-card-now');
                if (!nowCard) return null;

                const greetingEl = nowCard.querySelector('.font-semibold.text-\\\\[\\\\#6F6B68\\\\]');
                const label = nowCard.querySelector('.text-\\\\[\\\\#B83D08\\\\]');
                const nowBadge = nowCard.querySelector('.bg-\\\\[\\\\#FF6B2C\\\\].text-white');
                const title = nowCard.querySelector('h3');
                const subtitle = nowCard.querySelector('p');
                const focusBtn = nowCard.querySelector('button.btn-primary');
                const viewBtn = nowCard.querySelectorAll('button')[1];

                return {
                    greetingText: greetingEl ? greetingEl.textContent.trim() : '',
                    label: label ? label.textContent.trim() : '',
                    hasNowBadge: !!nowBadge,
                    title: title ? title.textContent.trim() : '',
                    subtitle: subtitle ? subtitle.textContent.trim() : '',
                    focusBtnText: focusBtn ? focusBtn.textContent.trim() : '',
                    viewBtnText: viewBtn ? viewBtn.textContent.trim() : ''
                };
            })()
        """)

        assert now_info is not None, "Priority #1 'Your Task for Now' card should be rendered"
        assert any(g in now_info['greetingText'] for g in ["Hi", "Chào"]), f"Greeting should be inside urgent-card-now, got: {now_info['greetingText']}"
        assert any(l in now_info['label'] for l in ["YOUR TASK FOR NOW", "VIỆC CẦN LÀM NGAY"]), f"Label should say 'YOUR TASK FOR NOW', got: {now_info['label']}"
        assert now_info['hasNowBadge'], "Card should display NOW badge"
        assert now_info['title'] == 'Marketing Report', f"Title should be 'Marketing Report', got: {now_info['title']}"
        assert now_info['subtitle'] == 'Finish competitor analysis section', f"Subtitle should show first unfinished subtask, got: {now_info['subtitle']}"
        assert any(b in now_info['focusBtnText'] for b in ["Focus on this task", "Tập trung vào việc này"]), f"Focus button mismatch: {now_info['focusBtnText']}"
        assert any(b in now_info['viewBtnText'] for b in ["View task", "Xem công việc"]), f"View task button mismatch: {now_info['viewBtnText']}"
        log("✓ Priority #1 'Your Task for Now' structure with internal greeting verified.")

        # Test Clicking "Focus on this task" opens Focus Zone with task-u1
        fz_debug = eval_js("""
            (() => {
                const focusBtn = document.querySelector('.urgent-card-now button.btn-primary');
                if (!focusBtn) return { error: 'focusBtn not found' };
                focusBtn.click();
                const fzRoot = document.getElementById('tempo-focus-zone-root');
                const isVisible = fzRoot && !fzRoot.classList.contains('hidden');
                const text = fzRoot ? fzRoot.textContent : '';
                const hasTask = text.includes('Marketing Report');
                
                // Close focus zone
                if (window.TempoFocusZone && window.TempoFocusZone.close) {
                    window.TempoFocusZone.close();
                }
                return { isVisible, hasTask, textSnippet: text.slice(0, 120), btnText: focusBtn.textContent.trim() };
            })()
        """)
        log(f"Focus zone debug info: {fz_debug}")
        assert fz_debug.get('isVisible'), f"Focus zone root should be visible: {fz_debug}"
        assert fz_debug.get('hasTask'), f"Focus zone should contain task name 'Marketing Report': {fz_debug}"
        log("✓ 'Focus on this task' button successfully launches Focus Zone with current task.")

        # =====================================================================
        # TEST 3: Priority #2 "Your Plan for Today"
        # =====================================================================
        log("\n--- TEST 3: Priority #2 'Your Plan for Today' ---")
        eval_js("window.__setupTestPlan();")

        plan_info = eval_js("""
            (() => {
                const rightCol = document.querySelector('.urgent-right-col');
                if (!rightCol) return null;

                const header = rightCol.querySelector('h3');
                const viewPlanBtn = rightCol.querySelector('button');
                const progressText = rightCol.querySelector('.text-\\\\[\\\\#6F6B68\\\\].font-medium');
                const timelineItems = rightCol.querySelectorAll('.urgent-timeline-item');
                const timelineLines = rightCol.querySelectorAll('.urgent-timeline-line');

                const items = [];
                timelineItems.forEach(el => {
                    const h4 = el.querySelector('h4');
                    const badge = el.querySelector('span[class*=\"rounded-full\"]');
                    items.push({
                        title: h4 ? h4.textContent.trim() : '',
                        isStrikethrough: h4 ? h4.classList.contains('line-through') : false,
                        badge: badge ? badge.textContent.trim() : ''
                    });
                });

                return {
                    headerText: header ? header.textContent.trim() : '',
                    viewPlanText: viewPlanBtn ? viewPlanBtn.textContent.trim() : '',
                    progressText: progressText ? progressText.textContent.trim() : '',
                    timelineCount: timelineItems.length,
                    lineCount: timelineLines.length,
                    items
                };
            })()
        """)

        assert plan_info is not None, "Right column should be rendered"
        assert any(h in plan_info['headerText'] for h in ['Your plan for today', 'Kế hoạch hôm nay']), f"Header mismatch: {plan_info['headerText']}"
        assert any(v in plan_info['viewPlanText'] for v in ["View / Edit Plan", "Xem / Sửa kế hoạch", "Xem / Chỉnh sửa kế hoạch", "Xem / chỉnh sửa"]), f"Button text mismatch: {plan_info['viewPlanText']}"
        assert any(p in plan_info['progressText'] for p in ["1 of 3 completed", "1/3 hoàn thành", "1/3 đã hoàn thành", "1 trên 3"]), f"Progress text mismatch: {plan_info['progressText']}"
        assert plan_info['timelineCount'] == 3, f"Today has 3 planned tasks, got: {plan_info['timelineCount']}"
        assert plan_info['lineCount'] == 2, f"Should have connector lines between items (3 items = 2 lines), got: {plan_info['lineCount']}"

        # Check badges
        assert plan_info['items'][0]['title'] == 'Marketing Report' and (plan_info['items'][0]['badge'] in ['NOW', 'ĐANG LÀM', 'Đang làm'])
        assert plan_info['items'][1]['title'] == 'Read chapter 4' and (plan_info['items'][1]['badge'] in ['Completed', 'Đã xong', 'Đã hoàn thành', 'Hoàn thành']) and plan_info['items'][1]['isStrikethrough']
        assert plan_info['items'][2]['title'] == 'Prepare slides' and (plan_info['items'][2]['badge'] in ['UP NEXT', 'TIẾP THEO', 'Tiếp theo'])
        log("✓ Priority #2 'Your plan for today' vertical timeline, connectors, badges, and progress bar verified.")

        # Test Toggling Completion from Home
        toggle_res = eval_js("""
            (() => {
                // Toggle task-u3 to completed
                window.TempoMode.toggleTaskCompletion('task-u3');
                const rightCol = document.querySelector('.urgent-right-col');
                const progressText = rightCol ? rightCol.querySelector('.text-\\\\[\\\\#6F6B68\\\\].font-medium').textContent.trim() : '';
                return progressText;
            })()
        """)
        assert any(p in toggle_res for p in ["2 of 3 completed", "2/3 hoàn thành", "2/3 đã hoàn thành", "2 trên 3"]), f"Progress text should update to 2 of 3, got: {toggle_res}"
        log("✓ Task completion toggle updates progress and re-renders timeline accurately.")

        # =====================================================================
        # TEST 4: Support Row & Tempo Posts (Social Community Feed)
        # =====================================================================
        log("\n--- TEST 4: Support Row & Tempo Posts (Social Community Feed) ---")
        support_posts_info = eval_js("""
            (() => {
                const supportRow = document.querySelector('.urgent-support-row');
                const cardOverwhelmed = document.querySelector('.urgent-card-overwhelmed');
                const cardFocusNow = document.querySelector('.urgent-card-focus-now');
                const postsSection = document.querySelector('.urgent-section-posts');

                const postsCards = postsSection ? postsSection.querySelectorAll('#urgent-community-posts-list > div') : [];
                const postTexts = [];
                const hasReactions = [];
                const hasAvatars = [];

                postsCards.forEach(c => {
                    postTexts.push(c.textContent);
                    const likeBtn = c.querySelector('button[title=\"Like\"]');
                    const commentBtn = c.querySelector('button[title=\"Comments\"]');
                    const bookmarkBtn = c.querySelector('button[title*=\"bookmark\" i], button[title*=\"Bookmark\"], button[title*=\"Save\"]');
                    hasReactions.push(!!likeBtn && !!commentBtn && !!bookmarkBtn);
                    const avatar = c.querySelector('img, .rounded-full');
                    hasAvatars.push(!!avatar);
                });

                const sectionText = postsSection ? postsSection.textContent : '';

                return {
                    hasSupportRow: !!supportRow,
                    hasCardOverwhelmed: !!cardOverwhelmed,
                    hasCardFocusNow: !!cardFocusNow,
                    hasPostsSection: !!postsSection,
                    postCardsCount: postsCards.length,
                    postTexts,
                    hasReactions,
                    hasAvatars,
                    sectionText
                };
            })()
        """)

        assert support_posts_info['hasSupportRow'], "Support row should exist"
        assert support_posts_info['hasCardOverwhelmed'], "Card 'Feeling overwhelmed?' should exist"
        assert support_posts_info['hasCardFocusNow'], "Card 'Focus now' should exist"
        assert support_posts_info['hasPostsSection'], "Tempo Posts section should exist"

        # Assert exactly 2 social posts previewed in Urgent Mode
        assert support_posts_info['postCardsCount'] == 2, f"Tempo Posts should preview 2 social posts, got: {support_posts_info['postCardsCount']}"

        # Assert complete absence of blog/editorial semantics
        assert "4 min read" not in support_posts_info['sectionText'], "Blog reading time '4 min read' must be removed"
        assert "3 min read" not in support_posts_info['sectionText'], "Blog reading time '3 min read' must be removed"
        assert "5 min read" not in support_posts_info['sectionText'], "Blog reading time '5 min read' must be removed"
        assert "STUDY TIPS" not in support_posts_info['sectionText'], "Editorial category 'STUDY TIPS' must be removed"
        assert "WELL-BEING" not in support_posts_info['sectionText'], "Editorial category 'WELL-BEING' must be removed"

        # Assert social post structure: avatars, author, content, tags, reactions
        assert all(support_posts_info['hasAvatars']), "All social posts must have avatars or fallback initial avatars"
        assert all(support_posts_info['hasReactions']), "All social posts must have social reaction rows (like, comment, bookmark)"
        assert any("#Deadline" in t for t in support_posts_info['postTexts']), "Post tags such as #Deadline should be present"

        # Test social interaction: toggle like on first post
        like_interaction = eval_js("""
            (() => {
                const firstLikeBtn = document.querySelector('#urgent-community-posts-list button[title=\"Like\"]');
                if (!firstLikeBtn) return null;
                const countBefore = parseInt(firstLikeBtn.textContent.trim().replace(/[^0-9]/g, ''), 10) || 0;
                firstLikeBtn.click();
                const newLikeBtn = document.querySelector('#urgent-community-posts-list button[title=\"Like\"]');
                const countAfter = parseInt(newLikeBtn.textContent.trim().replace(/[^0-9]/g, ''), 10) || 0;
                return { countBefore, countAfter };
            })()
        """)
        assert like_interaction is not None, "Like button should be interactive"
        assert like_interaction['countAfter'] == like_interaction['countBefore'] + 1, f"Liking should increment count from {like_interaction['countBefore']} to {like_interaction['countAfter']}"

        # Test "See all posts →" opens community modal
        see_all_res = eval_js("""
            (() => {
                const seeAllBtn = document.querySelector('.urgent-section-posts button');
                if (!seeAllBtn) return { error: 'See all button not found' };
                seeAllBtn.click();
                const modal = document.getElementById('modal-community-posts');
                const isOpen = modal && !modal.classList.contains('hidden');
                if (window.TempoCommunity && window.TempoCommunity.closeCommunityModal) {
                    window.TempoCommunity.closeCommunityModal();
                }
                return { isOpen };
            })()
        """)
        assert see_all_res.get('isOpen'), "Clicking 'See all posts' should open the existing community modal"

        log("✓ Support row, social post anatomy, reactions, and community modal integration verified.")

        # =====================================================================
        # TEST 5: Dynamic States
        # =====================================================================
        log("\n--- TEST 5: Dynamic Home States ---")

        # State A: PLAN_INCOMPLETE
        eval_js("""
            (() => {
                if (window.TempoPlanStore) {
                    window.TempoPlanStore.archiveActivePlan('emergency');
                    window.TempoPlanStore.clearInMemoryCache();
                }
                if (window.TempoEmergencyFlow) {
                    if (window.TempoEmergencyFlow.startFreshPlan) {
                        window.TempoEmergencyFlow.startFreshPlan();
                    }
                    window.TempoEmergencyFlow.goToStage('reality-check');
                }
                window.TempoMode.renderEmodeHome();
            })()
        """)
        incomplete_text = eval_js("document.getElementById('emode-home-content').textContent")
        assert any(t in incomplete_text for t in ["You're still setting up your plan.", "Bạn vẫn đang thiết lập kế hoạch của mình."]), "PLAN_INCOMPLETE state should be rendered"
        assert any(t in incomplete_text for t in ["YOUR URGENT PLAN", "KẾ HOẠCH KHẨN CỦA BẠN"]), "PLAN_INCOMPLETE should use 'YOUR URGENT PLAN'"
        assert any(t in incomplete_text for t in ["Continue building my plan", "Tiếp tục tạo kế hoạch của tôi"]), "PLAN_INCOMPLETE should show continue button"
        assert any(t in incomplete_text for t in ["Feeling overwhelmed?", "Cảm thấy quá tải?"]), "Support row should be accessible in PLAN_INCOMPLETE"
        assert "Tempo Posts" in incomplete_text, "Tempo Posts should be accessible in PLAN_INCOMPLETE"
        log("✓ State PLAN_INCOMPLETE verified.")

        # State B: TODAY_COMPLETE
        eval_js("""
            (() => {
                const dates = window.__setupTestPlan();
                // Mark all today's tasks as completed
                window.TempoEmergencyFlow.toggleTaskCompleted('task-u1');
                window.TempoEmergencyFlow.toggleTaskCompleted('task-u3');
                window.TempoMode.renderEmodeHome();
            })()
        """)
        today_done_text = eval_js("document.getElementById('emode-home-content').textContent")
        assert any(t in today_done_text for t in ["You're done for today.", "Bạn đã hoàn thành việc hôm nay.", "Bạn đã hoàn thành công việc hôm nay."]), "TODAY_COMPLETE state should be rendered"
        assert any(t in today_done_text for t in ["TODAY'S WORK DONE", "ĐÃ XONG VIỆC HÔM NAY", "CÔNG VIỆC HÔM NAY ĐÃ XONG"]), "Should show TODAY'S WORK DONE badge"
        assert any(t in today_done_text for t in ["Tomorrow", "Ngày mai"]), "Should reference next scheduled work tomorrow"
        assert any(t in today_done_text for t in ["Feeling overwhelmed?", "Cảm thấy quá tải?"]), "Support row should be accessible in TODAY_COMPLETE"
        assert "Tempo Posts" in today_done_text, "Tempo Posts should be accessible in TODAY_COMPLETE"
        log("✓ State TODAY_COMPLETE verified (does not pull tomorrow's work into today).")

        # State C: PLAN_COMPLETE
        eval_js("""
            (() => {
                window.__setupTestPlan();
                // Mark all tasks in entire plan as completed
                window.TempoEmergencyFlow.toggleTaskCompleted('task-u1');
                window.TempoEmergencyFlow.toggleTaskCompleted('task-u3');
                window.TempoEmergencyFlow.toggleTaskCompleted('task-u4');
                window.TempoMode.renderEmodeHome();
            })()
        """)
        plan_done_text = eval_js("document.getElementById('emode-home-content').textContent")
        assert any(t in plan_done_text for t in ["Your Urgent Plan is complete.", "Kế hoạch Khẩn của bạn đã hoàn tất.", "Kế hoạch Khẩn của bạn đã hoàn thành."]), "PLAN_COMPLETE state should be rendered"
        assert any(t in plan_done_text for t in ["Shift to Recovery Mode", "Chuyển sang Chế độ Hồi phục", "Chuyển sang Chế độ Phục hồi"]), "Should recommend shifting to Recovery Mode"
        assert any(t in plan_done_text for t in ["Stay in Urgent Mode", "Ở lại Chế độ Khẩn"]), "Should provide option to stay in Urgent Mode"
        log("✓ State PLAN_COMPLETE verified.")

        # =====================================================================
        # TEST 6: User-Facing Terminology Audit
        # =====================================================================
        log("\n--- TEST 6: User-Facing Terminology Audit ---")
        eval_js("window.__setupTestPlan();")

        # Check all visible text on screen-today
        home_text = eval_js("""
            (() => {
                const el = document.getElementById('emode-home-content');
                return el ? el.innerText : '';
            })()
        """)
        
        # Check global mode badge text
        badge_text = eval_js("""
            (() => {
                const el = document.getElementById('mode-badge-label');
                return el ? el.textContent.trim() : '';
            })()
        """)

        assert any(m in badge_text for m in ["Urgent Mode", "Chế độ Khẩn"]), f"Navbar badge should say 'Urgent Mode' or 'Chế độ Khẩn', got: {badge_text}"
        assert "Emergency Mode" not in home_text, f"Home page should not contain 'Emergency Mode', found: {home_text}"
        assert "Emergency Plan" not in home_text, f"Home page should not contain 'Emergency Plan', found: {home_text}"

        # Verify genuine crisis SOS text is intact
        sos_text = eval_js("""
            (() => {
                const sos = document.getElementById('btn-nav-sos');
                return sos ? sos.textContent.trim() : '';
            })()
        """)
        assert "SOS" in sos_text, "Genuine SOS safety button must be preserved"
        log("✓ Terminology audit passed: zero occurrences of 'Emergency Mode'/'Emergency Plan' in academic triage, genuine SOS preserved.")

        log("\n=======================================================")
        log("ALL TESTS (TEST 1 THROUGH TEST 6) PASSED SUCCESSFULLY!")
        log("=======================================================")

    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()

if __name__ == "__main__":
    run_tests()
