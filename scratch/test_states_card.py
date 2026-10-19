import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_test_')
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9301
proc = subprocess.Popen([
    edge_path, '--headless=new', f'--remote-debugging-port={port}',
    '--remote-allow-origins=*', f'--user-data-dir={user_data_dir}',
    '--disable-gpu', '--no-first-run', '--window-size=1440,900', 'http://localhost:8000/'
])
time.sleep(2)
try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        ws_url = json.loads(resp.read().decode())[0]['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)
    msg_id = 1
    def send_cmd(method, params=None):
        global msg_id
        cid = msg_id
        msg_id += 1
        ws.send(json.dumps({'id': cid, 'method': method, 'params': params or {}}))
        while True:
            m = json.loads(ws.recv())
            if m.get('id') == cid:
                return m.get('result', {})
    def eval_js(expr):
        return send_cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True}).get('result', {}).get('value')

    for _ in range(30):
        if eval_js('document.readyState === "complete" && Boolean(window.TempoMode)'):
            break
        time.sleep(0.5)

    eval_js("""
        (() => {
            window.TempoMode.setMode('emergency');
            window.TempoApp.navigateTo('today');
        })()
    """)
    time.sleep(1)

    initial_card = eval_js("""
        (() => {
            const card = document.querySelector('.urgent-right-col > div:nth-child(2)');
            return {
                text: card ? card.innerText : null,
                height: card ? card.getBoundingClientRect().height : null,
                classes: card ? card.className : null
            };
        })()
    """)
    print("INITIAL (EMPTY/SETUP) STATE:", json.dumps(initial_card, indent=2))

    # Now set a 3-task plan
    eval_js("""
        (() => {
            const now = new Date();
            const pad = n => String(n).padStart(2, '0');
            const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
            const testPlan = {
                id: 'plan_urgent_verify',
                planId: 'plan_urgent_verify',
                planType: 'emergency',
                title: 'Urgent Plan',
                plannedTasks: [
                    {
                        dayDate: today,
                        dayLabel: 'Today',
                        startTime: '10:00 AM',
                        endTime: '11:00 AM',
                        executionBadge: 'DO THIS FIRST',
                        task: { id: 'task-u1', name: 'Marketing Report', completed: false, isInProgress: true, subtasks: [{}, {}, {}] }
                    },
                    {
                        dayDate: today,
                        dayLabel: 'Today',
                        startTime: '02:00 PM',
                        endTime: '03:00 PM',
                        executionBadge: 'THEN',
                        task: { id: 'task-u2', name: 'Read chapter 4', completed: true, isInProgress: false, subtasks: [] }
                    },
                    {
                        dayDate: today,
                        dayLabel: 'Today',
                        startTime: '04:00 PM',
                        endTime: '05:00 PM',
                        executionBadge: 'LATER',
                        task: { id: 'task-u3', name: 'Prepare slides', completed: false, isInProgress: false, subtasks: [] }
                    }
                ],
                tasks: []
            };
            testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);
            window.TempoPlanStore.saveActivePlan('emergency', testPlan);
            window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
            window.TempoEmergencyFlow.restorePlanState();
            window.TempoMode.setMode('emergency');
        })()
    """)
    time.sleep(1)

    pop_card = eval_js("""
        (() => {
            const card = document.querySelector('.urgent-right-col > div:nth-child(2)');
            return {
                text: card ? card.innerText : null,
                height: card ? card.getBoundingClientRect().height : null,
                classes: card ? card.className : null
            };
        })()
    """)
    print("POPULATED STATE:", json.dumps(pop_card, indent=2))

    # Now test NO_WORK_TODAY
    eval_js("""
        (() => {
            const tomorrow = '2026-10-17';
            const testPlan = {
                id: 'plan_no_today',
                planId: 'plan_no_today',
                planType: 'emergency',
                title: 'Urgent Plan',
                plannedTasks: [
                    {
                        dayDate: tomorrow,
                        dayLabel: 'Tomorrow',
                        task: { id: 'task-fut', name: 'Future Task', completed: false }
                    }
                ],
                tasks: []
            };
            window.TempoPlanStore.saveActivePlan('emergency', testPlan);
            window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
            window.TempoMode.renderEmodeHome();
        })()
    """)
    time.sleep(1)

    no_work_card = eval_js("""
        (() => {
            const card = document.querySelector('.urgent-right-col > div:nth-child(2)');
            return {
                text: card ? card.innerText : null,
                height: card ? card.getBoundingClientRect().height : null
            };
        })()
    """)
    print("NO WORK TODAY STATE:", json.dumps(no_work_card, indent=2))

finally:
    try:
        ws.close()
    except Exception:
        pass
    proc.terminate()
