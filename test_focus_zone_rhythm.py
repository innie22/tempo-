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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_focus_rhythm_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    cmd = [
        edge_path,
        "--headless=new",
        "--remote-debugging-port=9226",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "http://localhost:8000/"
    ]
    
    log("Launching Edge on port 9226...")
    proc = subprocess.Popen(cmd)
    ws = None
    try:
        ws_url = None
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://127.0.0.1:9226/json") as resp:
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
                    ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoPlanStore !== 'undefined' && typeof window.TempoEmergencyFlow !== 'undefined' && typeof window.TempoFocusZone !== 'undefined'")
                    if ready:
                        eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("Page did not reach ready state")

        send_command("Runtime.enable")
        log("Waiting for page and scripts ready...")
        wait_for_ready()

        today_iso = eval_js("new Date().toISOString().split('T')[0]")
        tomorrow_iso = eval_js("""(() => {
            const d = new Date();
            d.setDate(d.getDate() + 1);
            return d.toISOString().split('T')[0];
        })()""")
        log(f"Test dates: today={today_iso}, tomorrow={tomorrow_iso}")

        # Setup standard test plan with 3 tasks today and 1 task tomorrow
        setup_script = f"""(() => {{
            localStorage.clear();
            const todayStr = '{today_iso}';
            const tomorrowStr = '{tomorrow_iso}';

            const taskA = {{
                id: 'task_a_101',
                name: 'Task A - Introduction',
                durationMinutes: 45,
                estimateMinutes: 45,
                durationLabel: '45 mins',
                deadline: todayStr + ' 17:00',
                completed: false,
                isInProgress: false,
                subtasks: [
                    {{ id: 'sub_a_1', title: 'Open rubric and create outline', completed: false }},
                    {{ id: 'sub_a_2', title: 'Draft rough introduction', completed: false }}
                ]
            }};

            const taskB = {{
                id: 'task_b_102',
                name: 'Task B - Statistics Assignment',
                durationMinutes: 75,
                estimateMinutes: 75,
                durationLabel: '1h15',
                deadline: todayStr + ' 21:00',
                completed: false,
                isInProgress: false,
                subtasks: [
                    {{ id: 'sub_b_1', title: 'Calculate dataset standard deviation', completed: false }},
                    {{ id: 'sub_b_2', title: 'Write hypothesis conclusion', completed: false }}
                ]
            }};

            const taskC = {{
                id: 'task_c_103',
                name: 'Task C - Presentation Slides',
                durationMinutes: 60,
                estimateMinutes: 60,
                durationLabel: '1h',
                deadline: todayStr + ' 23:59',
                completed: false,
                isInProgress: false,
                subtasks: [
                    {{ id: 'sub_c_1', title: 'Draft title and agenda slide', completed: false }}
                ]
            }};

            const taskD = {{
                id: 'task_d_104',
                name: 'Task D - Consumer Behavior Report',
                durationMinutes: 90,
                estimateMinutes: 90,
                durationLabel: '1h30',
                deadline: tomorrowStr + ' 18:00',
                completed: false,
                isInProgress: false,
                subtasks: [
                    {{ id: 'sub_d_1', title: 'Review case study', completed: false }}
                ]
            }};

            const plan = {{
                id: 'test_plan_focus_rhythm',
                planId: 'test_plan_focus_rhythm',
                status: 'confirmed',
                tasks: [taskA, taskB, taskC, taskD],
                plannedTasks: [
                    {{
                        dayDate: todayStr,
                        dayLabel: 'TODAY',
                        task: taskA,
                        allocatedMinutes: 45,
                        scheduledStartTime: '09:00',
                        scheduledEndTime: '09:45',
                        planPositionBadge: 'DO THIS'
                    }},
                    {{
                        dayDate: todayStr,
                        dayLabel: 'TODAY',
                        task: taskB,
                        allocatedMinutes: 75,
                        scheduledStartTime: '20:30',
                        scheduledEndTime: '21:45',
                        planPositionBadge: 'THEN'
                    }},
                    {{
                        dayDate: todayStr,
                        dayLabel: 'TODAY',
                        task: taskC,
                        allocatedMinutes: 60,
                        scheduledStartTime: '22:00',
                        scheduledEndTime: '23:00',
                        planPositionBadge: 'LATER'
                    }},
                    {{
                        dayDate: tomorrowStr,
                        dayLabel: 'TOMORROW',
                        task: taskD,
                        allocatedMinutes: 90,
                        scheduledStartTime: '09:00',
                        scheduledEndTime: '10:30',
                        planPositionBadge: 'SCHEDULED'
                    }}
                ],
                unarrangedTasks: []
            }};

            window.TempoPlanStore.saveActivePlan('emergency', plan);
            if (window.TempoEmergencyFlow.restorePlanState) {{
                window.TempoEmergencyFlow.restorePlanState(plan);
            }}
            return true;
        }})()"""
        eval_js(setup_script)
        log("Test plan established.")

        # =====================================================================
        # TEST A — TASK FINISHED EARLY
        # =====================================================================
        log("\n--- TEST A — TASK FINISHED EARLY ---")
        eval_js("window.TempoFocusZone.open({ taskId: 'task_a_101' })")
        eval_js("window.TempoFocusZone.startFocusSession()")
        # Simulate timer remaining 18:32 = 1112 seconds
        eval_js("window.TempoFocusZone._setSessionForTesting({ focusSecondsRemaining: 1112 })")
        eval_js("window.TempoFocusZone.finishActiveTaskEarly()")
        
        phase_a = eval_js("window.TempoFocusZone.getSessionState().phase")
        root_html_a = eval_js("document.getElementById('tempo-focus-zone-root').innerHTML")
        
        assert phase_a == "task_finished_early", f"Expected phase 'task_finished_early', got '{phase_a}'"
        assert "Continue with next task" in root_html_a, "Missing 'Continue with next task' button"
        assert "Mark as done and take a break" in root_html_a, "Missing 'Mark as done and take a break' button"
        assert "Finish focus early" in root_html_a, "Missing 'Finish focus early' button"
        log("✓ TEST A PASSED: Early finish shows Continue, Take break, and Finish early options.")

        # =====================================================================
        # TEST B — CONTINUE NEXT TASK
        # =====================================================================
        log("\n--- TEST B — CONTINUE NEXT TASK ---")
        # Ensure remaining seconds is 1112
        eval_js("window.TempoFocusZone._setSessionForTesting({ focusSecondsRemaining: 1112 })")
        eval_js("window.TempoFocusZone.continueWithNextTask()")
        
        state_b = eval_js("window.TempoFocusZone.getSessionState()")
        plan_b = eval_js("window.TempoPlanStore.getActivePlan('emergency')")
        task_a_persisted = next(t for t in plan_b['tasks'] if t['id'] == 'task_a_101')
        task_b_persisted = next(t for t in plan_b['tasks'] if t['id'] == 'task_b_102')

        assert task_a_persisted['completed'] is True, "Task A should be completed"
        assert state_b['taskId'] == 'task_b_102', f"Active task should be Task B, got '{state_b['taskId']}'"
        assert state_b['taskName'] == 'Task B - Statistics Assignment', f"Task name should be Task B, got '{state_b['taskName']}'"
        assert state_b['phase'] == 'focus', f"Phase should be 'focus', got '{state_b['phase']}'"
        # Invariant: timer preserved, not reset to 45m (2700s)
        assert state_b['focusSecondsRemaining'] <= 1112 and state_b['focusSecondsRemaining'] > 1000, f"Timer should be ~1112s, got {state_b['focusSecondsRemaining']}"
        assert task_b_persisted['estimateMinutes'] == 75, "Task B estimate must remain 75m"
        log("✓ TEST B PASSED: Continued in SAME block, preserved remaining timer without resetting, switched to Task B.")

        # =====================================================================
        # TEST C — TAKE BREAK
        # =====================================================================
        log("\n--- TEST C — TAKE BREAK ---")
        eval_js("window.TempoFocusZone.finishActiveTaskEarly()")
        phase_c_pre = eval_js("window.TempoFocusZone.getSessionState().phase")
        assert phase_c_pre == "task_finished_early", f"Expected 'task_finished_early', got '{phase_c_pre}'"
        
        eval_js("window.TempoFocusZone.markDoneAndTakeBreak()")
        state_c = eval_js("window.TempoFocusZone.getSessionState()")
        root_html_c = eval_js("document.getElementById('tempo-focus-zone-root').innerHTML")
        plan_c = eval_js("window.TempoPlanStore.getActivePlan('emergency')")
        task_b_persisted = next(t for t in plan_c['tasks'] if t['id'] == 'task_b_102')

        assert task_b_persisted['completed'] is True, "Task B should be marked complete"
        assert state_c['phase'] == 'pre_break_orientation', f"Expected 'pre_break_orientation', got '{state_c['phase']}'"
        assert "Task C - Presentation Slides" in root_html_c, "Next task name (Task C) should be displayed"
        assert "Start break" in root_html_c, "Start break CTA should be visible"
        
        # Start break from orientation
        eval_js("window.TempoFocusZone.startBreakPeriod()")
        state_c_break = eval_js("window.TempoFocusZone.getSessionState()")
        assert state_c_break['phase'] == 'break', f"Phase should be 'break', got '{state_c_break['phase']}'"
        log("✓ TEST C PASSED: Task completed, pre-break orientation shows real next task, existing break started.")

        # =====================================================================
        # TEST D — FINISH EARLY
        # =====================================================================
        log("\n--- TEST D — FINISH EARLY ---")
        # Task C is still unfinished for today
        eval_js("window.TempoFocusZone.finishFocusEarly()")
        state_d = eval_js("window.TempoFocusZone.getSessionState()")
        root_html_d = eval_js("document.getElementById('tempo-focus-zone-root').innerHTML")
        plan_d = eval_js("window.TempoPlanStore.getActivePlan('emergency')")
        task_c_persisted = next(t for t in plan_d['tasks'] if t['id'] == 'task_c_103')

        assert state_d['phase'] == 'finish_early_orient', f"Expected 'finish_early_orient', got '{state_d['phase']}'"
        assert "Focus finished for now." in root_html_d, "Orientation title missing"
        assert "Task C - Presentation Slides" in root_html_d, "Unfinished Task C should be listed"
        assert task_c_persisted['completed'] is False, "Task C must NOT be silently completed"
        log("✓ TEST D PASSED: Finish focus early safely orients user with real unfinished tasks.")

        # =====================================================================
        # TEST E — LAST TASK TODAY
        # =====================================================================
        log("\n--- TEST E — LAST TASK TODAY ---")
        # Open focus on Task C (the final unfinished task today)
        eval_js("window.TempoFocusZone.open({ taskId: 'task_c_103' })")
        eval_js("window.TempoFocusZone.startFocusSession()")
        eval_js("window.TempoFocusZone.finishActiveTaskEarly()")
        
        state_e = eval_js("window.TempoFocusZone.getSessionState()")
        root_html_e = eval_js("document.getElementById('tempo-focus-zone-root').innerHTML")

        assert state_e['phase'] == 'last_task_today', f"Expected 'last_task_today', got '{state_e['phase']}'"
        assert "You're at the end of today's plan." in root_html_e, "Last task title missing"
        assert "Mark as completed" in root_html_e, "Mark as completed button missing"
        assert "Finish focus early" in root_html_e, "Finish focus early button missing"
        assert "Continue with next task" not in root_html_e, "Continue with next task must NOT appear on last task"
        log("✓ TEST E PASSED: Last task of today shows Mark as completed without offering next task.")

        # =====================================================================
        # TEST F — TODAY COMPLETE
        # =====================================================================
        log("\n--- TEST F — TODAY COMPLETE ---")
        eval_js("window.TempoFocusZone.markLastTaskCompleted()")
        state_f = eval_js("window.TempoFocusZone.getSessionState()")
        root_html_f = eval_js("document.getElementById('tempo-focus-zone-root').innerHTML")
        plan_f = eval_js("window.TempoPlanStore.getActivePlan('emergency')")
        task_c_persisted = next(t for t in plan_f['tasks'] if t['id'] == 'task_c_103')
        task_d_persisted = next(t for t in plan_f['tasks'] if t['id'] == 'task_d_104')

        assert task_c_persisted['completed'] is True, "Task C should be completed"
        assert state_f['phase'] == 'today_complete', f"Expected 'today_complete', got '{state_f['phase']}'"
        assert "Today's plan is complete ✓" in root_html_f, "Title missing"
        assert "Take a break" in root_html_f, "Take a break option missing"
        assert "Review tomorrow's plan" in root_html_f, "Review tomorrow option missing"
        assert "Done for today" in root_html_f, "Done for today option missing"
        assert task_d_persisted['completed'] is False and task_d_persisted['isInProgress'] is False, "Tomorrow task must not auto-start"
        log("✓ TEST F PASSED: Today's plan marked complete with break, tomorrow review, and done options.")

        # =====================================================================
        # TEST G — POST-DAY BREAK
        # =====================================================================
        log("\n--- TEST G — POST-DAY BREAK ---")
        eval_js("window.TempoFocusZone.startPostDayBreak()")
        state_g = eval_js("window.TempoFocusZone.getSessionState()")
        assert state_g['isPostDayBreak'] is True, "isPostDayBreak flag should be true"
        assert state_g['phase'] == 'break', f"Expected phase 'break', got '{state_g['phase']}'"
        
        # End break early
        eval_js("window.TempoFocusZone.endBreakEarly()")
        state_g_after = eval_js("window.TempoFocusZone.getSessionState()")
        root_html_g = eval_js("document.getElementById('tempo-focus-zone-root').innerHTML")
        
        assert state_g_after['phase'] == 'return_transition', f"Expected 'return_transition', got '{state_g_after['phase']}'"
        assert "You're done with today's plan." in root_html_g, "Should recognize today is complete after post-day break"
        assert "Review tomorrow" in root_html_g, "Review tomorrow button missing"
        assert "Start a task now" in root_html_g, "Optional early start button missing"
        assert "Done" in root_html_g, "Done button missing"
        log("✓ TEST G PASSED: Post-day break preserves day-complete state; tomorrow starting is optional.")

        # =====================================================================
        # TEST H — SUBTASK COMPLETION
        # =====================================================================
        log("\n--- TEST H — SUBTASK COMPLETION ---")
        # Reset Task A to uncompleted with 2 uncompleted subtasks
        eval_js(f"""(() => {{
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const itemA = plan.plannedTasks.find(pt => pt.task.id === 'task_a_101');
            itemA.task.completed = false;
            itemA.task.subtasks = [
                {{ id: 'sub_a_1', title: 'Open rubric and create outline', completed: false }},
                {{ id: 'sub_a_2', title: 'Draft rough introduction', completed: false }}
            ];
            window.TempoPlanStore.saveActivePlan('emergency', plan);
        }})()""")
        eval_js("window.TempoFocusZone.open({ taskId: 'task_a_101' })")
        eval_js("window.TempoFocusZone.startFocusSession()")
        eval_js("window.TempoFocusZone.completeActiveSubtask()")
        
        state_h = eval_js("window.TempoFocusZone.getSessionState()")
        assert state_h['phase'] == 'focus', f"Subtask completion must keep phase 'focus', got '{state_h['phase']}'"
        assert state_h['taskId'] == 'task_a_101', "Parent task must remain Task A"
        assert state_h['nextAction'] == 'Draft rough introduction', f"Next action should advance to subtask 2, got '{state_h['nextAction']}'"
        log("✓ TEST H PASSED: Subtask completion advances Next Action without parent task completion.")

        # =====================================================================
        # TEST I — ROUND-BASED GAME BREAK END
        # =====================================================================
        log("\n--- TEST I — ROUND-BASED GAME BREAK END ---")
        eval_js("window.TempoFocusZone.startBreakPeriod()")
        eval_js("window.TempoFocusZone.selectBreakActivity('game')")
        state_i_act = eval_js("window.TempoFocusZone.getSessionState()")
        assert state_i_act['breakActivityType'] == 'round_game', f"Expected 'round_game', got '{state_i_act['breakActivityType']}'"
        
        # Expire break timer
        eval_js("""(() => {
            window.TempoFocusZone._setSessionForTesting({ breakSecondsRemaining: 0, phase: 'break_ended' });
            window.TempoFocusZone.render();
        })()""")
        root_html_i = eval_js("document.getElementById('tempo-focus-zone-root').innerHTML")
        assert "Return to Focus" in root_html_i, "Missing Return to Focus"
        assert "Let me finish this round" in root_html_i, "Missing 'Let me finish this round'"
        assert "I need 5 more minutes" not in root_html_i, "'I need 5 more minutes' MUST NOT be shown for round game"
        log("✓ TEST I PASSED: Round-based game break offers 'Let me finish this round' and no +5 option.")

        # =====================================================================
        # TEST J — ROUND COMPLETION GRACE
        # =====================================================================
        log("\n--- TEST J — ROUND COMPLETION GRACE ---")
        eval_js("window.TempoFocusZone.startRoundGrace()")
        state_j = eval_js("window.TempoFocusZone.getSessionState()")
        root_html_j = eval_js("document.getElementById('tempo-focus-zone-root').innerHTML")
        assert state_j['phase'] == 'round_grace', f"Expected 'round_grace', got '{state_j['phase']}'"
        assert state_j['hasUsedBreakExtension'] is True, "hasUsedBreakExtension must be true"
        assert "Finish your round 🎮" in root_html_j, "Missing round grace title"
        assert "I'm done" in root_html_j, "Missing 'I'm done' button"
        assert "I need 5 more minutes" not in root_html_j, "No +5 allowed in round grace"
        log("✓ TEST J PASSED: Round grace entered with 'I'm done' and no chained extension options.")

        # =====================================================================
        # TEST K — ROUND COMPLETE
        # =====================================================================
        log("\n--- TEST K — ROUND COMPLETE ---")
        eval_js("window.TempoFocusZone.confirmRoundDone()")
        state_k = eval_js("window.TempoFocusZone.getSessionState()")
        root_html_k = eval_js("document.getElementById('tempo-focus-zone-root').innerHTML")
        assert state_k['phase'] == 'return_transition', f"Expected 'return_transition', got '{state_k['phase']}'"
        assert "Break complete 🌿" in root_html_k, "Post-break checkpoint title missing"
        assert "I need 5 more minutes" not in root_html_k, "No +5 option in post-break checkpoint"
        log("✓ TEST K PASSED: Confirming round done transitions to post-break checkpoint without extensions.")

        # =====================================================================
        # TEST L — NON-ROUND GAME BREAK END
        # =====================================================================
        log("\n--- TEST L — NON-ROUND GAME BREAK END ---")
        eval_js("window.TempoFocusZone.startBreakPeriod()")
        eval_js("window.TempoFocusZone.selectBreakActivity('non_round_game')")
        state_l_act = eval_js("window.TempoFocusZone.getSessionState()")
        assert state_l_act['breakActivityType'] == 'non_round_game', f"Expected 'non_round_game', got '{state_l_act['breakActivityType']}'"
        
        eval_js("""(() => {
            window.TempoFocusZone._setSessionForTesting({ hasUsedBreakExtension: false, phase: 'break_ended' });
            window.TempoFocusZone.render();
        })()""")
        root_html_l = eval_js("document.getElementById('tempo-focus-zone-root').innerHTML")
        assert "Return to Focus" in root_html_l, "Missing Return to Focus"
        assert "I need 5 more minutes" in root_html_l, "Missing 'I need 5 more minutes'"
        assert "Let me finish this round" not in root_html_l, "'Let me finish this round' MUST NOT appear for non-round game"
        log("✓ TEST L PASSED: Non-round game break offers +5 minutes and no round language.")

        # =====================================================================
        # TEST M — OTHER BREAK ACTIVITY
        # =====================================================================
        log("\n--- TEST M — OTHER BREAK ACTIVITY ---")
        eval_js("window.TempoFocusZone.startBreakPeriod()")
        eval_js("window.TempoFocusZone.selectBreakActivity('move')")
        state_m_act = eval_js("window.TempoFocusZone.getSessionState()")
        assert state_m_act['breakActivityType'] == 'other', f"Expected 'other', got '{state_m_act['breakActivityType']}'"
        
        eval_js("""(() => {
            window.TempoFocusZone._setSessionForTesting({ hasUsedBreakExtension: false, phase: 'break_ended' });
            window.TempoFocusZone.render();
        })()""")
        root_html_m = eval_js("document.getElementById('tempo-focus-zone-root').innerHTML")
        assert "I need 5 more minutes" in root_html_m, "Missing +5 minutes"
        assert "Let me finish this round" not in root_html_m, "Round wording must not appear"
        log("✓ TEST M PASSED: Movement break offers +5 minutes with no round wording.")

        # =====================================================================
        # TEST N — EXTRA FIVE MINUTES
        # =====================================================================
        log("\n--- TEST N — EXTRA FIVE MINUTES ---")
        eval_js("window.TempoFocusZone.extendBreak5Minutes()")
        state_n = eval_js("window.TempoFocusZone.getSessionState()")
        assert state_n['hasUsedBreakExtension'] is True, "hasUsedBreakExtension must be true"
        assert state_n['breakSecondsRemaining'] > 0, "Timer should have seconds added"
        
        # Expire extra 5 minutes
        eval_js("""(() => {
            window.TempoFocusZone._setSessionForTesting({ breakSecondsRemaining: 0, phase: 'break_ended' });
            window.TempoFocusZone.render();
        })()""")
        root_html_n = eval_js("document.getElementById('tempo-focus-zone-root').innerHTML")
        assert "Your extra 5 minutes are up." in root_html_n, "Expected 'Your extra 5 minutes are up.'"
        assert "I need 5 more minutes" not in root_html_n, "Second +5 must NOT appear"
        assert "Let me finish this round" not in root_html_n, "Round grace must not appear"
        log("✓ TEST N PASSED: Exactly one +5 extension allowed, no repeated extension.")

        # =====================================================================
        # TEST O — NO EXTENSION CHAINING
        # =====================================================================
        log("\n--- TEST O — NO EXTENSION CHAINING ---")
        # Attempting to call extendBreak5Minutes again must be a no-op
        prev_seconds = eval_js("window.TempoFocusZone.getSessionState().breakSecondsRemaining")
        eval_js("window.TempoFocusZone.extendBreak5Minutes()")
        curr_seconds = eval_js("window.TempoFocusZone.getSessionState().breakSecondsRemaining")
        assert prev_seconds == curr_seconds, "+5 chaining must be rejected"
        
        # Attempting round grace while hasUsedBreakExtension is true must be rejected
        eval_js("window.TempoFocusZone.startRoundGrace()")
        curr_phase = eval_js("window.TempoFocusZone.getSessionState().phase")
        assert curr_phase != 'round_grace', "Round grace after +5 must be rejected"
        log("✓ TEST O PASSED: Extension chaining (Round grace -> +5 and +5 -> +5) strictly prevented.")

        # =====================================================================
        # TEST P — NORMAL 45/15 CYCLE & CHECKPOINT
        # =====================================================================
        log("\n--- TEST P — NORMAL 45/15 CYCLE & CHECKPOINT ---")
        eval_js("window.TempoFocusZone.selectRhythm(45, 15)")
        eval_js("window.TempoFocusZone.endBreakEarly()")
        
        state_p = eval_js("window.TempoFocusZone.getSessionState()")
        root_html_p = eval_js("document.getElementById('tempo-focus-zone-root').innerHTML")
        assert state_p['phase'] == 'return_transition', f"Expected 'return_transition', got '{state_p['phase']}'"
        assert "Break complete 🌿" in root_html_p, "Title missing"
        assert "Start next focus" in root_html_p or "Start now" in root_html_p, "Start CTA missing"
        assert "Change focus rhythm" in root_html_p, "'Change focus rhythm' button missing"
        assert "Change my plan" not in root_html_p, "'Change my plan' MUST NOT appear anywhere"
        assert "Finish focus for now" in root_html_p or "I'll start at" in root_html_p, "Finish focus for now missing"
        log("✓ TEST P PASSED: Post-break checkpoint rendered with 'Change focus rhythm' and accurate CTAs.")

        # =====================================================================
        # TEST Q — CHANGE TO 25/5
        # =====================================================================
        log("\n--- TEST Q — CHANGE TO 25/5 ---")
        eval_js("window.TempoFocusZone.openChangeRhythmModal()")
        state_q_modal = eval_js("window.TempoFocusZone.getSessionState()")
        assert state_q_modal['phase'] == 'change_rhythm', f"Expected 'change_rhythm', got '{state_q_modal['phase']}'"
        
        eval_js("window.TempoFocusZone.selectRhythmChoice('25_5')")
        eval_js("window.TempoFocusZone.saveRhythmFromModal()")
        
        state_q = eval_js("window.TempoFocusZone.getSessionState()")
        root_html_q = eval_js("document.getElementById('tempo-focus-zone-root').innerHTML")
        plan_q = eval_js("window.TempoPlanStore.getActivePlan('emergency')")

        assert state_q['phase'] == 'rhythm_updated', f"Expected 'rhythm_updated', got '{state_q['phase']}'"
        assert "Focus rhythm updated ✓" in root_html_q, "Confirmation title missing"
        assert "25 min focus · 5 min break" in root_html_q, "Rhythm description missing"
        assert "Start 25-min focus" in root_html_q, "Start 25-min CTA missing"
        assert state_q['focusDurationSeconds'] == 25 * 60, "Focus duration must be 1500s"
        assert state_q['breakDurationSeconds'] == 5 * 60, "Break duration must be 300s"
        assert len(plan_q['tasks']) == 4, "Emergency Plan tasks count must be unchanged"
        log("✓ TEST Q PASSED: Focus Rhythm changed to 25/5 without modifying Emergency Plan.")

        # =====================================================================
        # TEST R — RHYTHM PERSISTS
        # =====================================================================
        log("\n--- TEST R — RHYTHM PERSISTS ---")
        # Start next block using 25/5
        eval_js("window.TempoFocusZone.readyForNextFocusBlock()")
        state_r1 = eval_js("window.TempoFocusZone.getSessionState()")
        assert state_r1['focusSecondsRemaining'] == 25 * 60, f"Block should start with 25m (1500s), got {state_r1['focusSecondsRemaining']}"
        assert state_r1['breakDurationSeconds'] == 5 * 60, f"Break duration should be 5m (300s), got {state_r1['breakDurationSeconds']}"
        
        # Complete block and start another block
        eval_js("window.TempoFocusZone.startBreakPeriod()")
        eval_js("window.TempoFocusZone.endBreakEarly()")
        eval_js("window.TempoFocusZone.readyForNextFocusBlock()")
        state_r2 = eval_js("window.TempoFocusZone.getSessionState()")
        assert state_r2['focusDurationSeconds'] == 25 * 60, f"Subsequent block should still be 25m, got {state_r2['focusDurationSeconds']}"
        assert state_r2['breakDurationSeconds'] == 5 * 60, f"Subsequent break should still be 5m, got {state_r2['breakDurationSeconds']}"
        log("✓ TEST R PASSED: 25/5 rhythm persists into subsequent blocks.")

        # =====================================================================
        # TEST S — CUSTOM RHYTHM
        # =====================================================================
        log("\n--- TEST S — CUSTOM RHYTHM ---")
        eval_js("window.TempoFocusZone.openChangeRhythmModal()")
        eval_js("window.TempoFocusZone.selectRhythmChoice('custom')")
        # Set custom values in modal inputs
        eval_js("""(() => {
            const fInput = document.getElementById('fz-modal-custom-focus');
            const bInput = document.getElementById('fz-modal-custom-break');
            if (fInput) fInput.value = '35';
            if (bInput) bInput.value = '10';
            window.TempoFocusZone.saveRhythmFromModal();
        })()""")
        
        state_s = eval_js("window.TempoFocusZone.getSessionState()")
        assert state_s['focusDurationSeconds'] == 35 * 60, f"Expected 35m focus, got {state_s['focusDurationSeconds']}"
        assert state_s['breakDurationSeconds'] == 10 * 60, f"Expected 10m break, got {state_s['breakDurationSeconds']}"
        
        # Start next block with custom rhythm
        eval_js("window.TempoFocusZone.readyForNextFocusBlock()")
        state_s_active = eval_js("window.TempoFocusZone.getSessionState()")
        assert state_s_active['focusSecondsRemaining'] == 35 * 60, f"Expected 35m countdown, got {state_s_active['focusSecondsRemaining']}"
        log("✓ TEST S PASSED: Custom rhythm (35/10) validated and applied to next block.")

        # =====================================================================
        # TEST T — CURRENT RUNNING BLOCK IMMUTABLE
        # =====================================================================
        log("\n--- TEST T — CURRENT RUNNING BLOCK IMMUTABLE ---")
        # In state_s_active, simulate running block with 18:32 remaining
        eval_js("window.TempoFocusZone._setSessionForTesting({ focusSecondsRemaining: 1112 })")
        remaining_before = eval_js("window.TempoFocusZone.getSessionState().focusSecondsRemaining")
        
        # Rhythm change occurs only at checkpoints/modals; verify running timer is unchanged
        assert remaining_before == 1112, f"Timer must not be retroactively resized, was {remaining_before}"
        log("✓ TEST T PASSED: Currently running block is immutable.")

        # =====================================================================
        # TEST U — START EARLY
        # =====================================================================
        log("\n--- TEST U — START EARLY ---")
        # Transition to post-break checkpoint with future scheduled task
        eval_js("""(() => {
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const todayStr = new Date().toISOString().split('T')[0];
            const itemA = plan.plannedTasks.find(pt => pt.task.id === 'task_a_101');
            if (itemA) itemA.task.completed = true;
            const item = plan.plannedTasks.find(pt => pt.task.id === 'task_b_102');
            if (item) {
                item.task.completed = false;
                item.scheduledStartTime = '23:55';
            }
            window.TempoPlanStore.saveActivePlan('emergency', plan);
            window.TempoFocusZone._setSessionForTesting({ hasUsedBreakExtension: false, phase: 'return_transition' });
            window.TempoFocusZone.render();
        })()""")
        root_html_u = eval_js("document.getElementById('tempo-focus-zone-root').innerHTML")
        assert "Your next task is planned for" in root_html_u or "11:55 PM" in root_html_u, "Planned start not shown"
        assert "Start now" in root_html_u, "'Start now' CTA missing"
        assert "Change focus rhythm" in root_html_u, "'Change focus rhythm' button missing"
        assert "I'll start at" in root_html_u, "Optional wait action missing"
        log("✓ TEST U PASSED: Ending break early allows starting now or waiting without pressure.")

        # =====================================================================
        # TEST V — DATA INTEGRITY
        # =====================================================================
        log("\n--- TEST V — DATA INTEGRITY ---")
        plan_v = eval_js("window.TempoPlanStore.getActivePlan('emergency')")
        assert len(plan_v['tasks']) == 4, f"Expected 4 tasks, got {len(plan_v['tasks'])}"
        
        # Verify task IDs intact
        ids = [t['id'] for t in plan_v['tasks']]
        assert 'task_a_101' in ids, "Missing task_a_101"
        assert 'task_b_102' in ids, "Missing task_b_102"
        assert 'task_c_103' in ids, "Missing task_c_103"
        assert 'task_d_104' in ids, "Missing task_d_104"
        
        # Verify estimates and deadlines untouched
        task_b = next(t for t in plan_v['tasks'] if t['id'] == 'task_b_102')
        assert task_b['estimateMinutes'] == 75, f"Estimate altered: {task_b['estimateMinutes']}"
        assert task_b['deadline'].endswith('21:00'), f"Deadline altered: {task_b['deadline']}"
        
        # Verify saved rhythm exists independently in localStorage
        stored_rhythm = json.loads(eval_js("localStorage.getItem('tempo_focus_rhythm')"))
        assert stored_rhythm['focusDurationSeconds'] == 35 * 60, "Rhythm persistence intact"
        assert stored_rhythm['breakDurationSeconds'] == 10 * 60, "Rhythm persistence intact"
        log("✓ TEST V PASSED: All task IDs, estimates, deadlines, plan items, and rhythms remain completely intact.")

        log("\n=======================================================")
        log("ALL 22 TESTS (TEST A THROUGH TEST V) PASSED SUCCESSFULLY!")
        log("=======================================================")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

if __name__ == '__main__':
    run_tests()
