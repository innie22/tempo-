import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_test_notes_')
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9512

cmd = [
    edge_path,
    '--headless=new',
    f'--remote-debugging-port={port}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--disable-gpu',
    '--no-first-run',
    '--window-size=1440,1100',
    'http://127.0.0.1:8000/#today'
]

proc = subprocess.Popen(cmd)
time.sleep(2)
tabs_res = urllib.request.urlopen(f'http://127.0.0.1:{port}/json').read().decode()
tabs = json.loads(tabs_res)
app_tabs = [t for t in tabs if "127.0.0.1:8000" in t.get("url", "") or "localhost:8000" in t.get("url", "")]
target_tab = app_tabs[0] if app_tabs else tabs[0]
ws = websocket.create_connection(target_tab['webSocketDebuggerUrl'])

msg_id = 1
def send_cmd(method, params=None):
    global msg_id
    cmd_obj = {'id': msg_id, 'method': method, 'params': params or {}}
    msg_id += 1
    ws.send(json.dumps(cmd_obj))
    while True:
        res = json.loads(ws.recv())
        if res.get('id') == cmd_obj['id']:
            return res.get('result', {})

def eval_js(expr):
    res = send_cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
    if 'exceptionDetails' in res:
        print('JS EXCEPTION:', res['exceptionDetails'])
    return res.get('result', {}).get('value')

send_cmd('Page.enable')
send_cmd('Runtime.enable')

# Wait for page ready
for _ in range(30):
    time.sleep(0.5)
    ready = eval_js("document.readyState === 'complete' && !!window.TempoApp")
    if ready:
        break

print('Page ready:', ready)
print('TempoToolNotes exists:', eval_js('!!window.TempoToolNotes'))
print('TempoApp exists:', eval_js('!!window.TempoApp'))
print('TempoMode exists:', eval_js('!!window.TempoMode'))

# Check why toolNotes might or might not exist
scripts_info = eval_js("""
(() => {
    return Array.from(document.querySelectorAll('script[src]')).map(s => s.getAttribute('src'));
})()
""")
print('Scripts on page:', json.dumps(scripts_info, indent=2))

# Let's seed mock user so dashboard renders
seed_res = eval_js("""
(async () => {
    const mockUser = { id: 'dev_user_1', email: 'dev@tempo.local', user_metadata: { full_name: 'Innie', role: 'student' } };
    localStorage.setItem('tempo_local_dev_user', JSON.stringify(mockUser));
    localStorage.setItem('tempo_mock_account_dev@tempo.local', JSON.stringify(mockUser));
    localStorage.setItem('tempo_user_established_context_dev_user_1', 'emergency');
    localStorage.setItem('tempo_established_context', 'emergency');
    localStorage.setItem('tempo_current_mode', 'emergency');

    if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
        await window.TempoAuth.checkSession();
    }
    if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
        window.TempoMode.renderActiveModeHome();
    }
    return true;
})()
""")
print('Mock user seeded:', seed_res)
time.sleep(1)

# Check cards on dashboard
dashboard_info = eval_js("""
(() => {
    const createNotesCard = document.querySelector('[data-tempo-ui="urmode-create-notes"]');
    const emptyState = document.querySelector('[data-tempo-ui="notes-empty-state"]');
    return {
        hasCreateNotesCard: !!createNotesCard,
        hasEmptyState: !!emptyState,
        createNotesCardHTML: createNotesCard ? createNotesCard.outerHTML.substring(0, 400) : null
    };
})()
""")
print('Dashboard Notes card:', json.dumps(dashboard_info, indent=2))

# Test clicking Create Note card
click_test = eval_js("""
(() => {
    const card = document.querySelector('[data-tempo-ui="notes-empty-state"]') || document.querySelector('[data-tempo-ui="urmode-create-notes"]');
    if (!card) return { clicked: false, reason: 'card not found' };
    card.click();
    const modalRoot = document.getElementById('tool-notes-modal-root');
    return {
        clicked: true,
        hasModalRoot: !!modalRoot,
        modalInnerHTML: modalRoot ? modalRoot.innerHTML.substring(0, 300) : null
    };
})()
""")
print('Click create note test:', json.dumps(click_test, indent=2))

# Test navigating to #tool-notes
nav_test = eval_js("""
(() => {
    if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
        window.TempoApp.navigateTo('notes');
    } else {
        window.location.hash = '#tool-notes';
    }
    const screen = document.getElementById('screen-tool-notes');
    const root = document.getElementById('tool-notes-root');
    return {
        screenExists: !!screen,
        screenHidden: screen ? screen.classList.contains('hidden') : null,
        screenDisplay: screen ? window.getComputedStyle(screen).display : null,
        rootExists: !!root,
        rootChildren: root ? root.children.length : 0,
        rootHTML: root ? root.innerHTML.substring(0, 400) : null
    };
})()
""")
print('Nav to tool-notes test:', json.dumps(nav_test, indent=2))

ws.close()
proc.terminate()
