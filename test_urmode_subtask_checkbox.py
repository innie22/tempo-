import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

user_data_dir = tempfile.mkdtemp(prefix="tempo_subtask_test_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9295

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

    ws = websocket.create_connection(ws_url)
    msg_id = 1

    def send_command(method, params=None):
        global msg_id
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
                ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined' && typeof window.TempoEmergencyFlow !== 'undefined' && typeof window.TempoUrmodeFlow !== 'undefined'")
                if ready:
                    eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        raise TimeoutError("Application failed to become ready")

    log("Waiting for application ready state...")
    wait_for_ready()

    # Authenticate mock user
    eval_js("""
        (async () => {
            if (window.TempoAuth && !window.TempoAuth.getCurrentUser()) {
                const mock = {
                    id: 'local_subtask_user',
                    email: 'test.subtask@tempo.app',
                    raw_email: 'test.subtask@tempo.app',
                    user_metadata: { full_name: 'Subtask Tester' }
                };
                if (window.TempoAuth.setCurrentUser) {
                    window.TempoAuth.setCurrentUser(mock);
                }
            }
        })()
    """)

    # Setup Working Plan with Task 1 having 3 subtasks
    setup_res = eval_js("""
        (async () => {
            const todayStr = new Date().toISOString().split('T')[0];
            const testPlan = {
                id: 'plan-subtask-test',
                dateCreated: new Date().toISOString(),
                status: 'confirmed',
                executionDate: todayStr,
                plannedTasks: [
                    {
                        dayDate: todayStr,
                        scheduledDay: todayStr,
                        timeBlock: '09:00',
                        task: {
                            id: 'task-stats-4',
                            name: 'Statistics Assignment (Problem Set 4)',
                            description: 'Complete problem set 4 questions',
                            durationMinutes: 60,
                            durationLabel: '1h',
                            hasDeadline: true,
                            deadlineDate: todayStr,
                            deadlineTime: '23:59',
                            completed: false,
                            subtasks: [
                                { id: 'step-1', title: 'Identify required problems', completed: false },
                                { id: 'step-2', title: 'Review formulas', completed: false },
                                { id: 'step-3', title: 'Solve problem 1', completed: false }
                            ]
                        }
                    },
                    {
                        dayDate: todayStr,
                        scheduledDay: todayStr,
                        timeBlock: '11:00',
                        task: {
                            id: 'task-chem-2',
                            name: 'Chemistry Lab Report',
                            description: 'Write up lab results',
                            durationMinutes: 45,
                            durationLabel: '45m',
                            hasDeadline: false,
                            completed: false,
                            subtasks: []
                        }
                    }
                ],
                unarrangedTasks: [],
                unallocatedTasks: [],
                tasks: []
            };

            await window.TempoPlanStore.saveActivePlan('emergency', testPlan);
            if (window.TempoEmergencyFlow) {
                window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
            }
            window.TempoMode.setMode('emergency');
            window.TempoMode.renderActiveModeHome();
            return { ok: true };
        })()
    """)
    log(f"Setup plan result: {setup_res}")
    time.sleep(1)

    # 1. Verify Card Initial Rendering
    log("\n--- TEST 1: Initial Card Rendering ---")
    card_info = eval_js("""
        (() => {
            const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
            if (!card) return { found: false };
            const parentCheckbox = document.getElementById('task-for-now-checkbox');
            const subCheckboxes = card.querySelectorAll('input[id^="subtask-checkbox-"]');
            const subLabels = card.querySelectorAll('[data-tempo-ui="subtask-list"] label');
            const metadataText = card.querySelector('.border-t')?.textContent || '';

            return {
                found: true,
                parentChecked: parentCheckbox?.checked,
                subCheckboxCount: subCheckboxes.length,
                subtaskIds: Array.from(subCheckboxes).map(c => c.id),
                subtaskChecked: Array.from(subCheckboxes).map(c => c.checked),
                metadataText: metadataText
            };
        })()
    """)
    log(f"Card Info: {json.dumps(card_info, indent=2)}")
    assert card_info["found"], "Urgent task card not found!"
    assert card_info["parentChecked"] is False, "Parent checkbox should initially be false!"
    assert card_info["subCheckboxCount"] == 3, f"Expected 3 subtask checkboxes, found {card_info['subCheckboxCount']}"
    assert all(chk is False for chk in card_info["subtaskChecked"]), "All subtasks should initially be unchecked!"
    assert "0 / 3 action steps" in card_info["metadataText"], f"Expected '0 / 3 action steps' in metadata, got {card_info['metadataText']}"
    log("PASS: Initial rendering verified.")

    # 2. Check Subtask 1
    log("\n--- TEST 2: Check Subtask 1 ---")
    step1_check_res = eval_js("""
        (async () => {
            const cb1 = document.getElementById('subtask-checkbox-step-1');
            if (!cb1) return { error: 'Checkbox step-1 not found' };
            cb1.checked = true;
            cb1.dispatchEvent(new Event('change'));
            await new Promise(r => setTimeout(r, 200));

            const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
            const cb1After = document.getElementById('subtask-checkbox-step-1');
            const label1 = card?.querySelector('[data-subtask-id="step-1"] span');
            const parentCb = document.getElementById('task-for-now-checkbox');
            const meta = card?.querySelector('.border-t')?.textContent || '';

            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const task = plan?.plannedTasks?.[0]?.task;

            return {
                cb1Checked: cb1After?.checked,
                labelClass: label1?.className,
                hasLineThrough: label1?.classList?.contains('line-through'),
                parentChecked: parentCb?.checked,
                metadataText: meta,
                persistedSub1Completed: task?.subtasks?.find(s => s.id === 'step-1')?.completed,
                persistedParentCompleted: task?.completed
            };
        })()
    """)
    log(f"Step 1 Check Result: {json.dumps(step1_check_res, indent=2)}")
    assert step1_check_res["cb1Checked"] is True, "Subtask 1 checkbox should be checked!"
    assert step1_check_res["hasLineThrough"] is True, "Subtask 1 should have line-through class!"
    assert step1_check_res["parentChecked"] is False, "Parent checkbox MUST remain unchecked! (Independence)"
    assert step1_check_res["persistedSub1Completed"] is True, "Subtask 1 persisted completion must be true!"
    assert step1_check_res["persistedParentCompleted"] is False, "Parent persisted completion MUST be false!"
    assert "1 / 3 action steps" in step1_check_res["metadataText"], "Metadata should show 1 / 3 action steps"
    log("PASS: Subtask 1 checked and verified independent of parent task.")

    # 3. Check Subtask 2
    log("\n--- TEST 3: Check Subtask 2 ---")
    step2_check_res = eval_js("""
        (async () => {
            const cb2 = document.getElementById('subtask-checkbox-step-2');
            if (!cb2) return { error: 'Checkbox step-2 not found' };
            cb2.checked = true;
            cb2.dispatchEvent(new Event('change'));
            await new Promise(r => setTimeout(r, 200));

            const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
            const cb1 = document.getElementById('subtask-checkbox-step-1');
            const cb2After = document.getElementById('subtask-checkbox-step-2');
            const cb3 = document.getElementById('subtask-checkbox-step-3');
            const parentCb = document.getElementById('task-for-now-checkbox');
            const meta = card?.querySelector('.border-t')?.textContent || '';

            return {
                cb1Checked: cb1?.checked,
                cb2Checked: cb2After?.checked,
                cb3Checked: cb3?.checked,
                parentChecked: parentCb?.checked,
                metadataText: meta
            };
        })()
    """)
    log(f"Step 2 Check Result: {json.dumps(step2_check_res, indent=2)}")
    assert step2_check_res["cb1Checked"] is True, "Subtask 1 should still be checked"
    assert step2_check_res["cb2Checked"] is True, "Subtask 2 should be checked"
    assert step2_check_res["cb3Checked"] is False, "Subtask 3 should still be unchecked"
    assert step2_check_res["parentChecked"] is False, "Parent checkbox MUST remain unchecked!"
    assert "2 / 3 action steps" in step2_check_res["metadataText"], "Metadata should show 2 / 3 action steps"
    log("PASS: Subtask 2 checked successfully.")

    # 4. Uncheck Subtask 1
    log("\n--- TEST 4: Uncheck Subtask 1 ---")
    step1_uncheck_res = eval_js("""
        (async () => {
            const cb1 = document.getElementById('subtask-checkbox-step-1');
            if (!cb1) return { error: 'Checkbox step-1 not found' };
            cb1.checked = false;
            cb1.dispatchEvent(new Event('change'));
            await new Promise(r => setTimeout(r, 200));

            const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
            const cb1After = document.getElementById('subtask-checkbox-step-1');
            const label1 = card?.querySelector('[data-subtask-id="step-1"] span');
            const parentCb = document.getElementById('task-for-now-checkbox');
            const meta = card?.querySelector('.border-t')?.textContent || '';

            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const task = plan?.plannedTasks?.[0]?.task;

            return {
                cb1Checked: cb1After?.checked,
                hasLineThrough: label1?.classList?.contains('line-through'),
                parentChecked: parentCb?.checked,
                metadataText: meta,
                persistedSub1Completed: task?.subtasks?.find(s => s.id === 'step-1')?.completed
            };
        })()
    """)
    log(f"Step 1 Uncheck Result: {json.dumps(step1_uncheck_res, indent=2)}")
    assert step1_uncheck_res["cb1Checked"] is False, "Subtask 1 should now be unchecked"
    assert step1_uncheck_res["hasLineThrough"] is False, "Subtask 1 line-through must be removed"
    assert step1_uncheck_res["persistedSub1Completed"] is False, "Persisted state must be false"
    assert "1 / 3 action steps" in step1_uncheck_res["metadataText"], "Metadata should show 1 / 3 action steps"
    log("PASS: Subtask 1 unchecked and UI updated immediately.")

    # 5. Cross-view Consistency: Break Task Popup
    log("\n--- TEST 5: Cross-view Consistency in Break Task Popup ---")
    popup_res = eval_js("""
        (async () => {
            window.TempoUrmodeFlow.renderBreakTaskPopup('task-stats-4');
            await new Promise(r => setTimeout(r, 200));

            const popup = document.getElementById('modal-urmode-flow');
            const cb1 = document.getElementById('breakdown-subtask-checkbox-step-1');
            const cb2 = document.getElementById('breakdown-subtask-checkbox-step-2');
            const cb3 = document.getElementById('breakdown-subtask-checkbox-step-3');

            return {
                popupVisible: popup && !popup.classList.contains('hidden'),
                cb1Checked: cb1?.checked,
                cb2Checked: cb2?.checked,
                cb3Checked: cb3?.checked
            };
        })()
    """)
    log(f"Popup Checkboxes: {json.dumps(popup_res, indent=2)}")
    assert popup_res["popupVisible"] is True, "Break task popup should be visible"
    assert popup_res["cb1Checked"] is False, "Popup step-1 should be unchecked"
    assert popup_res["cb2Checked"] is True, "Popup step-2 should be checked (synced from card)"
    assert popup_res["cb3Checked"] is False, "Popup step-3 should be unchecked"

    # Check step-3 inside Break Task Popup
    popup_step3_res = eval_js("""
        (async () => {
            const cb3 = document.getElementById('breakdown-subtask-checkbox-step-3');
            cb3.checked = true;
            cb3.dispatchEvent(new Event('change'));
            await new Promise(r => setTimeout(r, 250));

            const cb3After = document.getElementById('breakdown-subtask-checkbox-step-3');
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const sub3 = plan?.plannedTasks?.[0]?.task?.subtasks?.find(s => s.id === 'step-3');

            // Close popup
            window.TempoUrmodeFlow.closeModal();
            await new Promise(r => setTimeout(r, 200));

            // Check card in background
            const cardCb3 = document.getElementById('subtask-checkbox-step-3');
            const meta = document.querySelector('[data-tempo-ui="urgent-task-now"] .border-t')?.textContent || '';

            return {
                popupCb3Checked: cb3After?.checked,
                persistedSub3: sub3?.completed,
                cardCb3Checked: cardCb3?.checked,
                metadataText: meta
            };
        })()
    """)
    log(f"Popup Step 3 Check Result: {json.dumps(popup_step3_res, indent=2)}")
    assert popup_step3_res["popupCb3Checked"] is True, "Popup step-3 should be checked"
    assert popup_step3_res["persistedSub3"] is True, "Subtask 3 should be persisted as true"
    assert popup_step3_res["cardCb3Checked"] is True, "Background card step-3 must reflect completion!"
    assert "2 / 3 action steps" in popup_step3_res["metadataText"], "Card metadata should show 2 / 3 action steps"
    log("PASS: Cross-view consistency with Break Task popup verified.")

    # 6. Cross-view Consistency: Plan Workspace
    log("\n--- TEST 6: Cross-view Consistency with Plan Workspace ---")
    workspace_res = eval_js("""
        (async () => {
            window.TempoPlanWorkspace.open();
            await new Promise(r => setTimeout(r, 250));

            const plan = window.TempoPlanWorkspace.getActivePlan();
            const task = plan?.plannedTasks?.[0]?.task;
            const substates = task?.subtasks?.map(s => ({ id: s.id, completed: s.completed }));

            // Test setting subtask completed via TempoPlanWorkspace.setSubtaskCompleted
            window.TempoPlanWorkspace.setSubtaskCompleted('task-stats-4', 'step-1', true);
            await new Promise(r => setTimeout(r, 200));

            const planAfter = window.TempoPlanWorkspace.getActivePlan();
            const sub1After = planAfter?.plannedTasks?.[0]?.task?.subtasks?.find(s => s.id === 'step-1');

            // Navigate back to Urmode home
            window.TempoPlanWorkspace.navigateHome();
            await new Promise(r => setTimeout(r, 200));

            const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
            const cardCb1 = document.getElementById('subtask-checkbox-step-1');
            const meta = card?.querySelector('.border-t')?.textContent || '';

            return {
                initialSubstates: substates,
                workspaceSub1Updated: sub1After?.completed,
                cardCb1Checked: cardCb1?.checked,
                metadataText: meta
            };
        })()
    """)
    log(f"Workspace Result: {json.dumps(workspace_res, indent=2)}")
    assert workspace_res["workspaceSub1Updated"] is True, "Workspace should update subtask state"
    assert workspace_res["cardCb1Checked"] is True, "Card must reflect workspace update"
    assert "3 / 3 action steps" in workspace_res["metadataText"], "Card metadata should show 3 / 3 action steps"
    log("PASS: Plan Workspace interaction and cross-sync verified.")

    # 7. Page Reload Persistence
    log("\n--- TEST 7: Page Reload Persistence ---")
    send_command("Page.reload")
    wait_for_ready()
    time.sleep(1)

    reload_res = eval_js("""
        (() => {
            window.TempoMode.setMode('emergency');
            window.TempoMode.renderActiveModeHome();

            const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
            const parentCb = document.getElementById('task-for-now-checkbox');
            const cb1 = document.getElementById('subtask-checkbox-step-1');
            const cb2 = document.getElementById('subtask-checkbox-step-2');
            const cb3 = document.getElementById('subtask-checkbox-step-3');
            const meta = card?.querySelector('.border-t')?.textContent || '';

            return {
                found: !!card,
                parentChecked: parentCb?.checked,
                cb1Checked: cb1?.checked,
                cb2Checked: cb2?.checked,
                cb3Checked: cb3?.checked,
                metadataText: meta
            };
        })()
    """)
    log(f"Post-Reload Card State: {json.dumps(reload_res, indent=2)}")
    assert reload_res["found"] is True, "Card should still exist after reload"
    assert reload_res["parentChecked"] is False, "Parent task should STILL be incomplete!"
    assert reload_res["cb1Checked"] is True, "Subtask 1 should remain checked after reload"
    assert reload_res["cb2Checked"] is True, "Subtask 2 should remain checked after reload"
    assert reload_res["cb3Checked"] is True, "Subtask 3 should remain checked after reload"
    assert "3 / 3 action steps" in reload_res["metadataText"], "Metadata should still show 3 / 3 action steps"
    log("PASS: Subtask state fully preserved across page reload.")

    # 8. Test Task without existing subtasks (Default Subtask checkbox)
    log("\n--- TEST 8: Task with Default Subtask (No pre-existing subtasks) ---")
    default_subtask_res = eval_js("""
        (async () => {
            // Remove subtasks from the current task to test default state
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const task = plan.plannedTasks[0].task;
            task.subtasks = [];
            task.completed = false;
            await window.TempoPlanStore.saveActivePlan('emergency', plan);
            window.TempoMode.renderActiveModeHome();
            await new Promise(r => setTimeout(r, 100));

            const defaultCb = document.getElementById('subtask-checkbox-default');
            const foundDefault = !!defaultCb;
            const initiallyChecked = defaultCb?.checked;

            // Check default subtask
            defaultCb.checked = true;
            defaultCb.dispatchEvent(new Event('change'));
            await new Promise(r => setTimeout(r, 200));

            const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
            const parentCb = document.getElementById('task-for-now-checkbox');
            const planAfter = window.TempoPlanStore.getActivePlan('emergency');
            const taskAfter = planAfter.plannedTasks[0].task;

            return {
                foundDefault: foundDefault,
                initiallyChecked: initiallyChecked,
                parentChecked: parentCb?.checked,
                subtaskCountAfter: taskAfter?.subtasks?.length,
                subtaskCompletedAfter: taskAfter?.subtasks?.[0]?.completed
            };
        })()
    """)
    log(f"Default Subtask Result: {json.dumps(default_subtask_res, indent=2)}")
    assert default_subtask_res["foundDefault"] is True, "Default subtask checkbox should be present"
    assert default_subtask_res["initiallyChecked"] is False, "Default subtask should be initially unchecked"
    assert default_subtask_res["parentChecked"] is False, "Parent checkbox MUST remain unchecked!"
    assert default_subtask_res["subtaskCountAfter"] == 1, "Should have created 1 subtask"
    assert default_subtask_res["subtaskCompletedAfter"] is True, "Created subtask should be completed"
    log("PASS: Default subtask creation and completion verified.")

    # 9. Test Parent Task Completion Independence
    log("\n--- TEST 9: Parent Task Completion Independence ---")
    parent_complete_res = eval_js("""
        (async () => {
            const parentCb = document.getElementById('task-for-now-checkbox');
            await window.TempoMode.handleCardTaskComplete('task-stats-4', true);
            await new Promise(r => setTimeout(r, 200));

            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const task = plan?.plannedTasks?.[0]?.task;

            return {
                parentPersistedCompleted: task?.completed,
                subtasksPreserved: task?.subtasks?.length > 0,
                subtask0Completed: task?.subtasks?.[0]?.completed
            };
        })()
    """)
    log(f"Parent Complete Result: {json.dumps(parent_complete_res, indent=2)}")
    assert parent_complete_res["parentPersistedCompleted"] is True, "Parent task should now be completed"
    assert parent_complete_res["subtasksPreserved"] is True, "Subtasks should be preserved"
    assert parent_complete_res["subtask0Completed"] is True, "Subtask completion state should be preserved"
    log("PASS: Parent task completion handled independently without disturbing subtasks.")

    # 10. Take a screenshot of the verified card
    log("\n--- Capturing Verified Screenshot ---")
    # Reset parent task to incomplete, with 2 of 3 subtasks complete for beautiful visual confirmation
    eval_js("""
        (async () => {
            const todayStr = new Date().toISOString().split('T')[0];
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const task = plan.plannedTasks[0].task;
            task.completed = false;
            task.subtasks = [
                { id: 'step-1', title: 'Identify required problems', completed: true },
                { id: 'step-2', title: 'Review formulas', completed: true },
                { id: 'step-3', title: 'Solve problem 1', completed: false }
            ];
            await window.TempoPlanStore.saveActivePlan('emergency', plan);
            window.TempoMode.renderActiveModeHome();
            await new Promise(r => setTimeout(r, 200));

            const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
            if (card) {
                card.scrollIntoView({ behavior: 'instant', block: 'center' });
            }
            const toast = document.getElementById('tempo-toast');
            if (toast) toast.remove();
        })()
    """)
    time.sleep(1)

    import base64
    shot = send_command("Page.captureScreenshot", {"format": "png"})
    with open(r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\urmode_subtask_checkbox_verified.png", "wb") as f:
        f.write(base64.b64decode(shot["data"]))
    log("Saved screenshot to urmode_subtask_checkbox_verified.png")

    log("\nALL 9 REQUIREMENTS VERIFIED SUCCESSFULLY!")

finally:
    if ws:
        try:
            ws.close()
        except Exception:
            pass
    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
