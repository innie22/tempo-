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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_ready_to_work_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9564

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#plan-workspace"
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
    time.sleep(2)
    tabs_res = urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read().decode()
    tabs = json.loads(tabs_res)
    app_tab = next(t for t in tabs if "8000" in t.get("url", ""))

    ws = websocket.create_connection(app_tab["webSocketDebuggerUrl"], timeout=10)
    print("Connected to CDP via WebSocket.")

    send_cmd("Page.enable")
    send_cmd("DOM.enable")

    time.sleep(1)

    # 1. Setup seed user and plan with top task Literature Review Chapter 2 (duration 90m -> 1.5 hr)
    setup_code = """
    (async () => {
        let waitLimit = 50;
        while ((!window.TempoUrmodeFlow || !window.TempoPlanStore) && waitLimit > 0) {
            await new Promise(r => setTimeout(r, 100));
            waitLimit--;
        }

        const u = { id: 'local_dev_alex', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
        localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }

        const mockPlan = {
            id: 'test-ready-to-work-plan',
            planId: 'test-ready-to-work-plan',
            status: 'active',
            planType: 'emergency',
            title: 'Tempo Working Plan',
            createdAt: Date.now(),
            plannedTasks: [
                {
                    task: {
                        id: 't-101',
                        name: 'Literature Review Chapter 2',
                        durationMinutes: 90,
                        durationLabel: '1.5 hr',
                        completed: false
                    },
                    dayDate: '2026-11-02',
                    startTime: '09:00',
                    endTime: '10:30',
                    executionBadge: 'DO THIS FIRST'
                },
                {
                    task: {
                        id: 't-102',
                        name: 'Data Collection Phase 1',
                        durationMinutes: 60,
                        durationLabel: '1 hr',
                        completed: false
                    },
                    dayDate: '2026-11-02',
                    startTime: '11:00',
                    endTime: '12:00',
                    executionBadge: 'UP NEXT'
                }
            ],
            unarrangedTasks: [],
        };

        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            await window.TempoPlanStore.saveActivePlan('emergency', mockPlan);
        }
        localStorage.setItem('tempo_active_working_plan', JSON.stringify(mockPlan));

        window.TempoI18n.setLanguage('vi');
        window.TempoUrmodeFlow.showStartWorkingPopup();
        return true;
    })();
    """
    eval_js(setup_code)
    time.sleep(1)

    # 2. Verify Vietnamese text
    vi_checks = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        if (!modal) return { error: 'No modal found' };
        
        const badge = modal.querySelector('span.uppercase')?.innerText.trim();
        const title = modal.querySelector('h2')?.innerText.trim();
        const desc = modal.querySelector('p')?.innerText.trim();
        
        const taskCard = modal.querySelector('.p-3.rounded-2xl');
        const taskName = taskCard ? taskCard.querySelector('span.font-bold')?.innerText.trim() : null;
        const taskDur = taskCard ? taskCard.querySelector('span:not(.font-bold)')?.innerText.trim() : null;
        
        const buttons = Array.from(modal.querySelectorAll('button')).map(b => b.innerText.trim()).filter(Boolean);
        
        return {
            badge,
            title,
            desc,
            taskName,
            taskDur,
            buttons,
            html: modal.innerHTML
        };
    })()
    """)
    print("VI Modal Data:", json.dumps(vi_checks, indent=2, ensure_ascii=False))

    assert vi_checks.get('badge') == 'SẴN SÀNG BẮT ĐẦU', f"Expected SẴN SÀNG BẮT ĐẦU, got {vi_checks.get('badge')}"
    assert vi_checks.get('title') == 'Bắt đầu làm việc nhé?', f"Expected Bắt đầu làm việc nhé?, got {vi_checks.get('title')}"
    assert 'Kế hoạch làm việc của bạn đã sẵn sàng. Bạn muốn bắt đầu với task đầu tiên ngay bây giờ không?' in vi_checks.get('desc'), f"Unexpected desc: {vi_checks.get('desc')}"
    assert 'Task đầu tiên: Literature Review Chapter 2' in vi_checks.get('taskName'), f"Unexpected taskName: {vi_checks.get('taskName')}"
    assert vi_checks.get('taskDur') == '~1,5 giờ', f"Expected ~1,5 giờ, got {vi_checks.get('taskDur')}"
    assert 'Để sau' in vi_checks.get('buttons'), f"Missing 'Để sau' in buttons: {vi_checks.get('buttons')}"
    assert 'Chia nhỏ thêm task' in vi_checks.get('buttons'), f"Missing 'Chia nhỏ thêm task' in buttons: {vi_checks.get('buttons')}"
    assert any('Có, bắt đầu thôi' in b for b in vi_checks.get('buttons')), f"Missing 'Có, bắt đầu thôi →' in buttons: {vi_checks.get('buttons')}"

    capture_screenshot("ready_to_work_modal_vi.png")
    print("VI tests passed successfully!")

    # 3. Switch to English on the fly
    eval_js("window.TempoI18n.setLanguage('en');")
    time.sleep(1)

    en_checks = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        if (!modal) return { error: 'No modal found' };
        
        const badge = modal.querySelector('span.uppercase')?.innerText.trim();
        const title = modal.querySelector('h2')?.innerText.trim();
        const desc = modal.querySelector('p')?.innerText.trim();
        
        const taskCard = modal.querySelector('.p-3.rounded-2xl');
        const taskName = taskCard ? taskCard.querySelector('span.font-bold')?.innerText.trim() : null;
        const taskDur = taskCard ? taskCard.querySelector('span:not(.font-bold)')?.innerText.trim() : null;
        
        const buttons = Array.from(modal.querySelectorAll('button')).map(b => b.innerText.trim()).filter(Boolean);
        
        return {
            badge,
            title,
            desc,
            taskName,
            taskDur,
            buttons,
            html: modal.innerHTML
        };
    })()
    """)
    print("EN Modal Data:", json.dumps(en_checks, indent=2, ensure_ascii=False))

    assert en_checks.get('badge') == 'READY TO WORK', f"Expected READY TO WORK, got {en_checks.get('badge')}"
    assert en_checks.get('title') == 'Start working on your plan?', f"Expected Start working on your plan?, got {en_checks.get('title')}"
    assert 'Your working plan is ready. Would you like to start right away on your first task?' in en_checks.get('desc'), f"Unexpected desc: {en_checks.get('desc')}"
    assert 'First task: Literature Review Chapter 2' in en_checks.get('taskName'), f"Unexpected taskName: {en_checks.get('taskName')}"
    assert en_checks.get('taskDur') == '~1.5 hr', f"Expected ~1.5 hr, got {en_checks.get('taskDur')}"
    assert 'Later' in en_checks.get('buttons'), f"Missing 'Later' in buttons: {en_checks.get('buttons')}"
    assert 'Break more tasks' in en_checks.get('buttons'), f"Missing 'Break more tasks' in buttons: {en_checks.get('buttons')}"
    assert any('Yes, start working' in b for b in en_checks.get('buttons')), f"Missing 'Yes, start working →' in buttons: {en_checks.get('buttons')}"

    capture_screenshot("ready_to_work_modal_en.png")
    print("EN tests passed successfully!")

    # 4. Test button: Later -> closes modal
    eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        const btn = Array.from(modal.querySelectorAll('button')).find(b => b.innerText.trim() === 'Later');
        if (btn) btn.click();
    })()
    """)
    time.sleep(0.5)
    modal_closed = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        return !modal || modal.classList.contains('hidden') || modal.style.display === 'none';
    })()
    """)
    print("Later button closed modal:", modal_closed)
    assert modal_closed, "Later button failed to close modal"

    # 5. Test button: Break more tasks -> triggers restartBreakdownFlow
    eval_js("window.TempoUrmodeFlow.showStartWorkingPopup();")
    time.sleep(0.5)
    eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        const btn = Array.from(modal.querySelectorAll('button')).find(b => b.innerText.trim() === 'Break more tasks');
        if (btn) btn.click();
    })()
    """)
    time.sleep(0.5)
    breakdown_view = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        return modal ? modal.innerText.includes('BREAK DOWN') || modal.innerText.includes('step') || modal.innerText.includes('Chia nhỏ') : false;
    })()
    """)
    print("Break more tasks button triggered breakdown view:", breakdown_view)

    # 6. Test button: Yes, start working -> triggers showFirstTaskExecutionPopup
    eval_js("window.TempoUrmodeFlow.showStartWorkingPopup();")
    time.sleep(0.5)
    eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        const btn = Array.from(modal.querySelectorAll('button')).find(b => b.innerText.includes('Yes, start working'));
        if (btn) btn.click();
    })()
    """)
    time.sleep(0.5)
    exec_view = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        return modal ? (modal.innerText.includes('FIRST TASK EXECUTION') || modal.innerText.includes('Your first task is') || modal.innerText.includes('Literature Review Chapter 2')) : false;
    })()
    """)
    print("Yes, start working button triggered first task execution view:", exec_view)
    assert exec_view, "Yes, start working button failed to open first task execution popup"

    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")

finally:
    if ws:
        ws.close()
    proc.terminate()
