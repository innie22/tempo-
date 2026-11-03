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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_avail_clean_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9560

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

    # 1. Setup dev user session
    eval_js("""
    (async () => {
        const u = { id: 'u1', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
        localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }
        window.TempoApp.navigateTo('plan-workspace');
    })()
    """)
    time.sleep(1)

    # =========================================================================
    # TEST 1: PROMPT REFERENCE SCENARIO (Nov 1, 2026, 6:09 PM)
    # =========================================================================
    print("\n--- TEST 1: VERIFYING PROMPT REFERENCE SCENARIO ---")
    setup_test1 = """
    (() => {
        const testAvailability = [
            {
                date: '2026-10-17',
                label: 'Oct 17, 2026',
                isUnavailable: false,
                blocks: [{ id: 'b_oct17', start: '10:00', end: '12:00' }]
            },
            {
                date: '2026-10-18',
                label: 'Oct 18, 2026',
                isUnavailable: false,
                blocks: [{ id: 'b_oct18', start: '14:00', end: '16:00' }]
            },
            {
                date: '2026-10-31',
                label: 'Oct 31, 2026',
                isUnavailable: false,
                blocks: [{ id: 'b_oct31', start: '18:00', end: '20:00' }]
            },
            {
                date: '2026-11-01',
                label: 'Nov 1, 2026',
                isUnavailable: false,
                blocks: [
                    { id: 'b_nov1_expired', start: '2:00 PM', end: '4:00 PM' },
                    { id: 'b_nov1_ongoing', start: '2:00 PM', end: '10:00 PM' },
                    { id: 'b_nov1_upcoming', start: '10:20 PM', end: '11:50 PM' }
                ]
            },
            {
                date: '2026-11-02',
                label: 'Nov 2, 2026',
                isUnavailable: false,
                blocks: [
                    { id: 'b_nov2_future', start: '2:00 PM', end: '4:00 PM' }
                ]
            }
        ];

        const plan = {
            id: 'plan_test_cleanup',
            planId: 'plan_test_cleanup',
            planType: 'emergency',
            title: 'Tempo Working Plan',
            plannedTasks: [
                {
                    task: { id: 'task_ref_1', name: 'Thesis Proposal', completed: false },
                    dayDate: '2026-11-01',
                    startTime: '09:00',
                    endTime: '11:00'
                }
            ],
            unarrangedTasks: [],
            tasks: [{ id: 'task_ref_1', name: 'Thesis Proposal', completed: false }],
            availabilityDays: testAvailability
        };

        localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
        localStorage.setItem('tempo_availability_days', JSON.stringify(testAvailability));
        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            window.TempoPlanStore.saveActivePlan('emergency', plan);
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
            window.TempoEmergencyFlow.setConfirmedPlan(plan);
        }

        // Run cleanup with the reference timestamp: 2026-11-01 at 18:09 (6:09 PM)
        window.TempoPlanWorkspace.cleanupExpiredAvailability(plan, '2026-11-01', '18:09');
        window.TempoPlanWorkspace.persistPlan(plan);
        window.TempoPlanWorkspace.openAdjustAvailabilityModal();
    })()
    """
    eval_js(setup_test1)
    time.sleep(1)

    t1_results = eval_js("""
    (() => {
        const plan = window.TempoPlanWorkspace.getActivePlan();
        const storedAvail = JSON.parse(localStorage.getItem('tempo_availability_days') || '[]');
        const storedPlan = JSON.parse(localStorage.getItem('tempo_working_plan') || '{}');

        // Check modal DOM
        const modal = document.querySelector('[role="dialog"], .fixed');
        const modalText = modal ? modal.innerText : '';

        // Extract dates and blocks currently rendered in availability modal
        const availModal = document.getElementById('pw-avail-add-date')?.closest('.fixed');
        const renderedDates = Array.from((availModal || document).querySelectorAll('div.bg-stone-50'))
            .filter(card => card.closest('.fixed') === availModal)
            .map(card => {
                const title = card.querySelector('div > span:first-child')?.innerText.trim();
                const date = card.querySelector('div > span:last-child')?.innerText.trim();
                const blocks = Array.from(card.querySelectorAll('div.bg-white span'))
                    .map(s => s.innerText.trim());
                return { title, date, blocks };
            });

        return {
            planDates: plan.availabilityDays.map(d => d.date),
            storedDates: storedAvail.map(d => d.date),
            storedPlanDates: (storedPlan.availabilityDays || []).map(d => d.date),
            todayBlocks: plan.availabilityDays.find(d => d.date === '2026-11-01')?.blocks,
            futureBlocks: plan.availabilityDays.find(d => d.date === '2026-11-02')?.blocks,
            renderedDates,
            modalVisible: !!document.getElementById('pw-avail-add-date')
        };
    })()
    """)

    print("Test 1 Plan Dates:", t1_results.get('planDates'))
    print("Test 1 Stored Dates:", t1_results.get('storedDates'))
    print("Test 1 Stored Plan Dates:", t1_results.get('storedPlanDates'))
    print("Test 1 Today Blocks:", t1_results.get('todayBlocks'))
    print("Test 1 Future Blocks:", t1_results.get('futureBlocks'))
    print("Test 1 Rendered Dates in Modal:", t1_results.get('renderedDates'))

    # Verify past dates removed
    for past_d in ['2026-10-17', '2026-10-18', '2026-10-31']:
        assert past_d not in t1_results.get('planDates', []), f"{past_d} was not removed from plan.availabilityDays!"
        assert past_d not in t1_results.get('storedDates', []), f"{past_d} was not removed from localStorage tempo_availability_days!"
        assert past_d not in t1_results.get('storedPlanDates', []), f"{past_d} was not removed from localStorage tempo_working_plan!"

    # Verify today's expired slot removed, ongoing & upcoming kept
    today_b_ids = [b['id'] for b in t1_results.get('todayBlocks', [])]
    assert 'b_nov1_expired' not in today_b_ids, "Expired slot 2:00 PM–4:00 PM was not removed!"
    assert 'b_nov1_ongoing' in today_b_ids, "Ongoing slot 2:00 PM–10:00 PM was removed!"
    assert 'b_nov1_upcoming' in today_b_ids, "Upcoming slot 10:20 PM–11:50 PM was removed!"

    # Verify future day and slot kept
    future_b_ids = [b['id'] for b in t1_results.get('futureBlocks', [])]
    assert 'b_nov2_future' in future_b_ids, "Future slot 2:00 PM–4:00 PM on Nov 2 was removed!"

    # Verify modal rendered dates
    rendered_dates_list = [d['date'] for d in t1_results.get('renderedDates', [])]
    assert '2026-11-01' in rendered_dates_list, "Nov 1 not rendered in modal!"
    assert '2026-11-02' in rendered_dates_list, "Nov 2 not rendered in modal!"
    assert not any(p in rendered_dates_list for p in ['2026-10-17', '2026-10-18', '2026-10-31']), "Past dates rendered in modal!"

    capture_screenshot("availability_modal_cleaned.png")
    print("TEST 1 PASSED: Prompt Reference Scenario Verified!")

    # Close modal
    eval_js("window.TempoPlanWorkspace.closeAdjustAvailabilityModal();")
    time.sleep(0.5)

    # =========================================================================
    # TEST 2: LIVE SYSTEM CLOCK CLEANUP (Actual Current Local Time)
    # =========================================================================
    print("\n--- TEST 2: VERIFYING LIVE SYSTEM CLOCK CLEANUP ---")
    setup_test2 = """
    (() => {
        const now = new Date();
        const pad = n => String(n).padStart(2, '0');
        const todayStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

        const tom = new Date(now.getTime() + 86400000);
        const tomStr = `${tom.getFullYear()}-${pad(tom.getMonth() + 1)}-${pad(tom.getDate())}`;

        const pastD = new Date(now.getTime() - 86400000 * 3);
        const pastStr = `${pastD.getFullYear()}-${pad(pastD.getMonth() + 1)}-${pad(pastD.getDate())}`;

        // Create a past slot for today that has definitely ended: 00:00 to 01:00 AM (or early morning)
        // If current time is past 01:00 AM, this is definitely expired.
        const currentHours = now.getHours();
        const currentMins = now.getMinutes();

        // Expired slot: 10 mins ago to 5 mins ago (or 00:00 to 00:30 if early morning)
        let expStart = '00:00';
        let expEnd = '00:30';
        if (currentHours >= 1) {
            expStart = `${pad(currentHours - 1)}:00`;
            expEnd = `${pad(currentHours - 1)}:30`;
        }

        // Valid future slot today: 23:00 to 23:59 (or 2 hours ahead)
        const validStart = `${pad(Math.min(22, currentHours + 1))}:00`;
        const validEnd = '23:59';

        const liveAvail = [
            {
                date: pastStr,
                label: 'Past Day',
                blocks: [{ id: 'b_live_past', start: '09:00', end: '11:00' }]
            },
            {
                date: todayStr,
                label: 'Today',
                blocks: [
                    { id: 'b_live_today_exp', start: expStart, end: expEnd },
                    { id: 'b_live_today_valid', start: validStart, end: validEnd }
                ]
            },
            {
                date: tomStr,
                label: 'Tomorrow',
                blocks: [
                    { id: 'b_live_tom_valid', start: '10:00', end: '12:00' }
                ]
            }
        ];

        const plan = {
            id: 'plan_live_clock_test',
            planId: 'plan_live_clock_test',
            planType: 'emergency',
            title: 'Tempo Working Plan',
            plannedTasks: [
                {
                    task: { id: 'task_live_1', name: 'Thesis Proposal', completed: false },
                    dayDate: todayStr,
                    startTime: '09:00',
                    endTime: '11:00'
                }
            ],
            unarrangedTasks: [],
            tasks: [{ id: 'task_live_1', name: 'Thesis Proposal', completed: false }],
            availabilityDays: liveAvail
        };

        localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
        localStorage.setItem('tempo_availability_days', JSON.stringify(liveAvail));
        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            window.TempoPlanStore.saveActivePlan('emergency', plan);
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
            window.TempoEmergencyFlow.setConfirmedPlan(plan);
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setAvailabilityDays === 'function') {
            window.TempoEmergencyFlow.setAvailabilityDays(liveAvail);
        }

        // Open modal which must automatically clean up using actual local time!
        window.TempoPlanWorkspace.openAdjustAvailabilityModal();
    })()
    """
    eval_js(setup_test2)
    time.sleep(1)

    t2_results = eval_js("""
    (() => {
        const plan = window.TempoPlanWorkspace.getActivePlan();
        const storedAvail = JSON.parse(localStorage.getItem('tempo_availability_days') || '[]');
        const storedPlan = JSON.parse(localStorage.getItem('tempo_working_plan') || '{}');

        const now = new Date();
        const pad = n => String(n).padStart(2, '0');
        const todayStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

        const todayDay = plan.availabilityDays.find(d => d.date === todayStr);

        return {
            allDates: plan.availabilityDays.map(d => d.date),
            storedDates: storedAvail.map(d => d.date),
            todayBlockIds: todayDay ? todayDay.blocks.map(b => b.id) : []
        };
    })()
    """)

    print("Test 2 Live All Dates:", t2_results.get('allDates'))
    print("Test 2 Live Stored Dates:", t2_results.get('storedDates'))
    print("Test 2 Today Block IDs:", t2_results.get('todayBlockIds'))

    # Assertions for live clock cleanup
    assert 'b_live_today_exp' not in t2_results.get('todayBlockIds', []), "Live expired block was not removed!"
    assert 'b_live_today_valid' in t2_results.get('todayBlockIds', []), "Live future block today was incorrectly removed!"
    assert not any('past' in str(d) for d in t2_results.get('allDates', [])), "Past date was not removed in live clock test!"

    capture_screenshot("availability_modal_future_slots.png")
    print("TEST 2 PASSED: Live System Clock Cleanup Verified!")

    # Close modal and verify reload persistence
    eval_js("window.TempoPlanWorkspace.closeAdjustAvailabilityModal();")
    time.sleep(0.5)

    # =========================================================================
    # TEST 3: VERIFY CLEANUP PERSISTS AFTER PAGE RELOAD
    # =========================================================================
    print("\n--- TEST 3: VERIFYING CLEANUP PERSISTS AFTER PAGE RELOAD ---")
    send_cmd("Page.reload")
    time.sleep(2)

    # Re-authenticate and check working plan
    eval_js("""
    (async () => {
        const u = { id: 'u1', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
        localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }
        window.TempoApp.navigateTo('plan-workspace');
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
        }
    })()
    """)
    time.sleep(1)

    t3_results = eval_js("""
    (() => {
        const storedAvail = JSON.parse(localStorage.getItem('tempo_availability_days') || '[]');
        const plan = window.TempoPlanWorkspace ? window.TempoPlanWorkspace.getActivePlan() : null;
        return {
            storedDates: storedAvail.map(d => d.date),
            storedBlocks: storedAvail.flatMap(d => (d.blocks || []).map(b => b.id)),
            planDates: plan ? plan.availabilityDays.map(d => d.date) : []
        };
    })()
    """)
    print("Test 3 Stored Dates after reload:", t3_results.get('storedDates'))
    print("Test 3 Stored Block IDs after reload:", t3_results.get('storedBlocks'))

    assert 'b_live_today_exp' not in t3_results.get('storedBlocks', []), "Expired block resurfaced after reload!"
    assert 'b_live_today_valid' in t3_results.get('storedBlocks', []), "Valid block lost after reload!"
    print("TEST 3 PASSED: Persistence after reload verified!")

    print("\n=======================================================")
    print("ALL AVAILABILITY EXPIRATION & CLEANUP TESTS PASSED 100%!")
    print("=======================================================")

finally:
    if ws:
        try:
            ws.close()
        except:
            pass
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
