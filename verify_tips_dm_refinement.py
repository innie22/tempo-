import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_verify_refinement_')
port = 9467
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

    for _ in range(30):
        if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoCommunity !== 'undefined'"):
            break
        time.sleep(0.5)

    print("=== STARTING TEMPO COMMUNITY VERIFICATION SUITE ===")

    # Clear test localStorage
    eval_js("""
        localStorage.removeItem('tempo_direct_messages');
        localStorage.removeItem('tempo_chat_requests');
        window.TempoCommunity.init();
    """)
    time.sleep(0.3)

    # =========================================================================
    # 1. TEST TIPS (SOLVE) RESPONSIVE 3-COLUMN GRID
    # =========================================================================
    eval_js("window.TempoApp.navigateTo('community', 'tips');")
    time.sleep(0.4)

    # 1a. Wide Desktop Screen (1280px >= 1200px): Must be 3 equal columns
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 1280,
        "height": 900,
        "deviceScaleFactor": 1,
        "mobile": False
    })
    time.sleep(0.3)
    grid_cols_1280 = eval_js("""
        (() => {
            const grid = document.getElementById('tips-cards-grid');
            const style = window.getComputedStyle(grid);
            const cols = style.gridTemplateColumns.split(' ');
            const cards = Array.from(grid.children);
            const firstRowCards = cards.slice(0, 3);
            const heights = firstRowCards.map(c => c.getBoundingClientRect().height);
            const widths = firstRowCards.map(c => Math.round(c.getBoundingClientRect().width));

            return {
                columnCount: cols.length,
                colValues: cols,
                widths,
                heights,
                hasOverflow: grid.scrollWidth > grid.clientWidth
            };
        })()
    """)
    print("1a. Desktop (1280px) Tips Grid:", grid_cols_1280)
    assert grid_cols_1280['columnCount'] == 3, f"Wide desktop must have 3 columns, got {grid_cols_1280['columnCount']}"
    assert not grid_cols_1280['hasOverflow'], "Wide desktop must NOT have horizontal overflow"
    # Verify equal widths
    w = grid_cols_1280['widths']
    assert abs(w[0] - w[1]) <= 2 and abs(w[1] - w[2]) <= 2, "Columns must be equal-width"
    print("   Wide desktop 3 equal columns: VERIFIED (PASS)")

    # 1b. Tablet / Medium Screen (800px): Must be 2 columns
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 800,
        "height": 900,
        "deviceScaleFactor": 1,
        "mobile": False
    })
    time.sleep(0.3)
    grid_cols_800 = eval_js("""
        (() => {
            const grid = document.getElementById('tips-cards-grid');
            const style = window.getComputedStyle(grid);
            const cols = style.gridTemplateColumns.split(' ');
            return {
                columnCount: cols.length,
                hasOverflow: grid.scrollWidth > grid.clientWidth
            };
        })()
    """)
    print("1b. Tablet (800px) Tips Grid:", grid_cols_800)
    assert grid_cols_800['columnCount'] == 2, f"Tablet must have 2 columns, got {grid_cols_800['columnCount']}"
    assert not grid_cols_800['hasOverflow'], "Tablet must NOT have horizontal overflow"
    print("   Tablet 2 columns: VERIFIED (PASS)")

    # 1c. Small Mobile Screen (390px): Must be 1 column
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 390,
        "height": 844,
        "deviceScaleFactor": 2,
        "mobile": True
    })
    time.sleep(0.3)
    grid_cols_390 = eval_js("""
        (() => {
            const grid = document.getElementById('tips-cards-grid');
            const style = window.getComputedStyle(grid);
            const cols = style.gridTemplateColumns.split(' ');
            return {
                columnCount: cols.length,
                hasOverflow: grid.scrollWidth > grid.clientWidth
            };
        })()
    """)
    print("1c. Mobile (390px) Tips Grid:", grid_cols_390)
    assert grid_cols_390['columnCount'] == 1, f"Mobile must have 1 column, got {grid_cols_390['columnCount']}"
    assert not grid_cols_390['hasOverflow'], "Mobile must NOT have horizontal overflow"
    print("   Mobile 1 column: VERIFIED (PASS)")

    # Restore Desktop
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 1280,
        "height": 900,
        "deviceScaleFactor": 1,
        "mobile": False
    })
    time.sleep(0.3)

    # 1d. Search in Tips still works
    eval_js("""
        document.getElementById('tips-search-input').value = 'Presentation';
        window.TempoCommunity.handleTipsSearch('Presentation');
    """)
    time.sleep(0.2)
    filtered_tips = eval_js("document.querySelectorAll('#tips-cards-grid > div').length")
    print("1d. Search 'Presentation':", filtered_tips, "card(s)")
    assert filtered_tips >= 1, "Should filter tip cards"
    eval_js("window.TempoCommunity.clearTipsSearch();")

    # =========================================================================
    # 2. TEST DIRECT MESSAGE - REMOVE MOCK DATA & CORRECT EMPTY STATES
    # =========================================================================
    # Authenticate user with zero messages
    eval_js("""
        (() => {
            if (window.TempoAuth) {
                window.TempoAuth.getCurrentUser = () => ({ id: 'u_real_account', email: 'user@tempo.edu' });
            }
            // Ensure no mock keys exist in storage
            localStorage.removeItem('tempo_direct_messages');
            localStorage.removeItem('tempo_direct_messages_u_real_account');
            window.TempoCommunity.selectTab('messages');
        })()
    """)
    time.sleep(0.4)

    dm_check = eval_js("""
        (() => {
            const convsList = document.getElementById('dm-conversations-list').innerText;
            const messagesContainer = document.getElementById('dm-messages-container').innerText;
            const activeName = document.getElementById('dm-active-name').innerText;
            const input = document.getElementById('dm-message-input');
            const convsCount = window.TempoCommunity.getConversations().length;

            return {
                convsCount,
                hasMockBadminton: convsList.includes('Go Badmintonnnn') || convsList.includes('Badminton'),
                hasMockAdmin: convsList.includes('Tempo Admin'),
                hasMockInnie: convsList.includes('Innie'),
                emptyListText: convsList,
                messagePanelText: messagesContainer,
                activeName,
                inputDisabled: input.disabled,
                inputPlaceholder: input.placeholder
            };
        })()
    """)
    print("2a. DM Empty State (Account with no messages):", dm_check)
    assert dm_check['convsCount'] == 0, "No conversations should be fabricated"
    assert not dm_check['hasMockBadminton'], "Mock Badminton must be completely gone"
    assert not dm_check['hasMockAdmin'], "Mock Admin must be completely gone"
    assert not dm_check['hasMockInnie'], "Mock Innie must be completely gone"
    assert "No conversations yet" in dm_check['emptyListText'], "List must show 'No conversations yet'"
    assert "No conversation selected" in dm_check['messagePanelText'], "Panel must be blank / 'No conversation selected'"
    assert dm_check['inputDisabled'], "Input must be disabled"
    print("   Direct Message mock data removal: VERIFIED (PASS)")

    # 2b. Check that opening / refreshing page created NO records
    storage_check = eval_js("""
        (() => {
            return {
                dmStorage: localStorage.getItem('tempo_direct_messages'),
                userDmStorage: localStorage.getItem('tempo_direct_messages_u_real_account')
            };
        })()
    """)
    print("2b. Storage after page visit:", storage_check)
    assert storage_check['dmStorage'] is None or storage_check['dmStorage'] == '[]', "Must not write fabricated records to storage"

    # =========================================================================
    # 3. TEST DIRECT MESSAGE - CHAT REQUESTS SYMBOL & ACTIONS
    # =========================================================================
    symbol_info = eval_js("""
        (() => {
            const btn = document.getElementById('btn-dm-chat-requests');
            const img = btn ? btn.querySelector('img') : null;
            return {
                src: img ? img.getAttribute('src') : null,
                ariaLabel: btn ? btn.getAttribute('aria-label') : null,
                title: btn ? btn.getAttribute('title') : null
            };
        })()
    """)
    print("3a. Chat Requests Symbol Info:", symbol_info)
    assert symbol_info['src'] == 'assets/chat_requests_symbol.png' or symbol_info['src'] == 'assets/chat_requests_icon.png', "Must use supplied symbol"
    assert symbol_info['ariaLabel'] == 'Chat Requests', "Must provide accessible label 'Chat Requests'"
    assert symbol_info['title'] == 'Chat Requests', "Must provide tooltip 'Chat Requests'"

    # Open Chat Requests modal
    eval_js("window.TempoCommunity.openChatRequests();")
    time.sleep(0.3)
    modal_check = eval_js("""
        (() => {
            const modal = document.getElementById('modal-chat-requests');
            const emptyText = document.getElementById('chat-requests-empty').innerText;
            return {
                isOpen: !modal.classList.contains('hidden'),
                emptyText
            };
        })()
    """)
    print("3b. Chat Requests Modal:", modal_check)
    assert modal_check['isOpen'], "Chat Requests modal must open"
    assert "No pending chat requests" in modal_check['emptyText'], "Must show clean empty state when no requests exist"
    eval_js("window.TempoCommunity.closeChatRequests();")

    print("\nALL VERIFICATION CRITERIA COMPLETED AND PASSED 100%!")

finally:
    proc.terminate()
