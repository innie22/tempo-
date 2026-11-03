import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_audit_rmode_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9620

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#today"
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

    print("=== 1. TESTING GUEST MODE SELECTION OF RMODE ===")
    # Ensure guest mode first
    eval_js("""
        (() => {
            if (window.TempoAuth && typeof window.TempoAuth.signOut === 'function') {
                window.TempoAuth.signOut();
            }
            if (window.TempoMode) {
                window.TempoMode.requestMode('recovery');
            }
        })()
    """)
    time.sleep(1)

    guest_pending = eval_js("localStorage.getItem('tempo_pending_mode')")
    auth_modal_open = eval_js("""
        const m = document.getElementById('modal-signin') || document.getElementById('auth-modal');
        Boolean(m && !m.classList.contains('hidden'));
    """)
    print(f"Guest pending mode saved: '{guest_pending}', Auth modal displayed: {auth_modal_open}")

    print("\n=== 2. TESTING AUTHENTICATED USER TRANSITION TO RMODE ===")
    eval_js("""
        (() => {
            // Set mock authenticated user
            const mockUser = { id: 'audit_user_123', email: 'audit@tempo.edu.vn', name: 'Innie Test' };
            localStorage.setItem('tempo_local_dev_user', JSON.stringify(mockUser));
            if (window.TempoAuth) {
                if (typeof window.TempoAuth.init === 'function') window.TempoAuth.init();
            }
            if (window.TempoMode) {
                window.TempoMode.setMode('recovery');
            }
        })()
    """)
    time.sleep(1.5)

    active_ctx = eval_js("window.TempoMode.getActiveContext()")
    rmode_visible = eval_js("""
        const el = document.getElementById('rmode-home-content');
        Boolean(el && !el.classList.contains('hidden') && el.offsetHeight > 0);
    """)
    print(f"Active context: '{active_ctx}', #rmode-home-content visible: {rmode_visible}")

    print("\n=== 3. AUDITING RMODE DASHBOARD COMPONENTS ===")
    components = eval_js("""
        (() => {
            const root = document.getElementById('rmode-home-content');
            if (!root) return null;
            return {
                modeSelectorText: root.querySelector('#btn-home-mode-selector')?.innerText.trim().replace(/\\s+/g, ' '),
                hasSelfCheckCard: Boolean(root.querySelector('[data-tempo-ui="recovery-self-check"], .recovery-card-selfcheck, #recovery-self-check')),
                hasSupportRow: Boolean(root.querySelector('[data-tempo-ui="recovery-support"]')),
                quickReliefBtn: Boolean(root.querySelector('.recovery-card-quick-relief')),
                focusNowBtn: Boolean(root.querySelector('.recovery-support-focus-now')),
                hasNotesCard: Boolean(root.querySelector('[data-tempo-ui="urmode-create-notes"]')),
                hasRecentlyCard: Boolean(root.querySelector('[data-tempo-ui="recovery-recently"]')),
                hasWorkingPlan: Boolean(root.querySelector('[data-tempo-ui="recovery-working-plan"]')),
                hasCommunityCard: Boolean(root.querySelector('[data-tempo-ui="recovery-community"]')),
                changeModeBtn: Boolean(root.querySelector('.recovery-prompt-wrap button')),
                taskCount: root.querySelectorAll('.recovery-task-card-group').length
            };
        })()
    """)
    print("Discovered components in Rmode DOM:", json.dumps(components, indent=2))

    print("\n=== 4. TESTING TASK POPUP MODAL IN RMODE ===")
    eval_js("""
        (() => {
            const firstTask = document.querySelector('.recovery-task-card-group');
            if (firstTask) {
                const taskId = firstTask.getAttribute('data-task-id');
                window.TempoMode.openRmodeTaskDetailModal(taskId);
            }
        })()
    """)
    time.sleep(1)

    modal_info = eval_js("""
        (() => {
            const modal = document.getElementById('rmode-task-detail-modal');
            if (!modal || modal.classList.contains('hidden')) return null;
            return {
                title: modal.querySelector('#rmode-task-modal-title')?.innerText.trim(),
                hasSubtasks: Boolean(modal.querySelector('[data-subtask-id]')),
                hasDoneBtn: Boolean(modal.querySelector('button[onclick*=\"toggleRmodeDetailTaskComplete\"]')),
                hasFocusBtn: Boolean(modal.querySelector('button[onclick*=\"handleRmodeTaskFocus\"]'))
            };
        })()
    """)
    print("Rmode task detail modal state:", json.dumps(modal_info, indent=2))

    eval_js("window.TempoMode.closeRmodeTaskDetailModal()")
    time.sleep(0.5)

    print("\n=== 5. TESTING MODE SWITCHING TO EMERGENCY AND BACK ===")
    eval_js("window.TempoMode.setMode('emergency')")
    time.sleep(1)
    emode_visible = eval_js("""
        const el = document.getElementById('emode-home-content');
        Boolean(el && !el.classList.contains('hidden') && el.offsetHeight > 0);
    """)
    print(f"Switched to Emode. #emode-home-content visible: {emode_visible}")

    eval_js("window.TempoMode.setMode('recovery')")
    time.sleep(1)
    rmode_reopened = eval_js("""
        const el = document.getElementById('rmode-home-content');
        Boolean(el && !el.classList.contains('hidden') && el.offsetHeight > 0);
    """)
    print(f"Switched back to Rmode. #rmode-home-content visible: {rmode_reopened}")

    print("\n=== 6. TESTING RECOVERY MODE PERSISTENCE ACROSS PAGE RELOAD ===")
    send_cmd("Page.reload")
    time.sleep(2.5)

    persisted_context = eval_js("window.TempoMode ? window.TempoMode.getActiveContext() : null")
    persisted_visible = eval_js("""
        const el = document.getElementById('rmode-home-content');
        Boolean(el && !el.classList.contains('hidden') && el.offsetHeight > 0);
    """)
    print(f"After page reload: activeContext='{persisted_context}', #rmode-home-content visible: {persisted_visible}")

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
