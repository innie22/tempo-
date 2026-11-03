import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_debug_')
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9508

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
target_tab = tabs[0]
ws = websocket.create_connection(target_tab['webSocketDebuggerUrl'])

msg_id = 1
def eval_js(expression):
    global msg_id
    cmd_obj = {'id': msg_id, 'method': 'Runtime.evaluate', 'params': {'expression': expression, 'returnByValue': True, 'awaitPromise': True}}
    msg_id += 1
    ws.send(json.dumps(cmd_obj))
    while True:
        res = json.loads(ws.recv())
        if res.get('id') == cmd_obj['id']:
            if 'exceptionDetails' in res.get('result', {}):
                print('JS ERR:', res['result']['exceptionDetails'])
            return res.get('result', {}).get('value')

for _ in range(20):
    time.sleep(0.5)
    if eval_js('!!window.TempoMode'):
        break

js_code = """
(() => {
    const todayStr = window.TempoI18n ? window.TempoI18n.getLocalTodayISO() : '2026-11-01';
    const overdueDateStr = '2026-10-31';

    const plan = {
        id: 'plan_test_overdue',
        createdDate: overdueDateStr,
        updatedAt: new Date().toISOString(),
        status: 'active',
        tasks: [
            {
                id: 'task_overdue_1',
                title: 'Báo cáo tổng kết dự án',
                name: 'Báo cáo tổng kết dự án',
                estimatedMinutes: 60,
                completed: false,
                hasDeadline: true,
                deadlineDate: overdueDateStr,
                deadlineTime: '17:00',
                scheduledDate: overdueDateStr
            }
        ],
        plannedTasks: [
            {
                id: 'pt_overdue_1',
                dayDate: overdueDateStr,
                startTime: '14:00',
                endTime: '16:00',
                task: {
                    id: 'task_overdue_1',
                    title: 'Báo cáo tổng kết dự án',
                    name: 'Báo cáo tổng kết dự án',
                    estimatedMinutes: 60,
                    completed: false,
                    hasDeadline: true,
                    deadlineDate: overdueDateStr,
                    deadlineTime: '17:00'
                }
            }
        ],
        availability: {
            selectedDays: [overdueDateStr, todayStr],
            days: [
                { date: overdueDateStr, blocks: [{ start: '14:00', end: '18:00' }] },
                { date: todayStr, blocks: [{ start: '09:00', end: '17:00' }] }
            ]
        }
    };

    const mockUser = { id: 'dev_user_1', email: 'dev@tempo.local', user_metadata: { full_name: 'Innie', role: 'student' } };
    localStorage.setItem('tempo_local_dev_user', JSON.stringify(mockUser));
    localStorage.setItem('tempo_mock_account_dev@tempo.local', JSON.stringify(mockUser));
    localStorage.setItem('tempo_user_established_context_dev_user_1', 'emergency');
    localStorage.setItem('tempo_established_context', 'emergency');
    localStorage.setItem('tempo_current_mode', 'emergency');

    localStorage.setItem('tempo_confirmed_plan', JSON.stringify(plan));
    localStorage.setItem('tempo_confirmed_plan_dev_user_1', JSON.stringify(plan));
    localStorage.setItem('tempo_plan_workspace_plan_dev_user_1', JSON.stringify(plan));

    const isOverdue = window.TempoMode.isTaskOverdue(plan.tasks[0], plan);
    window.TempoMode.renderActiveModeHome();

    const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
    const allCards = Array.from(document.querySelectorAll('[data-tempo-ui]')).map(el => el.getAttribute('data-tempo-ui'));

    return {
        isOverdue,
        hasCard: !!card,
        allCards,
        bodyText: document.querySelector('#screen-today')?.innerText?.substring(0, 400)
    };
})()
"""

res = eval_js(js_code)
print('Debug result:', json.dumps(res, indent=2, ensure_ascii=False))

ws.close()
proc.terminate()
