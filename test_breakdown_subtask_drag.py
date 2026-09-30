import subprocess
import time
import json
import urllib.request
import tempfile
import os
import websocket
import sys

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_subtask_drag_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    cmd = [
        edge_path,
        "--headless=new",
        "--remote-debugging-port=9224",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "http://localhost:8000/"
    ]
    
    log("Launching Edge on port 9224...")
    proc = subprocess.Popen(cmd)
    ws = None
    try:
        ws_url = None
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://127.0.0.1:9224/json") as resp:
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
                data = json.loads(raw)
                if data.get("id") == cid:
                    return data.get("result", {})
                    
        def eval_js(expr):
            res = send_command("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True
            })
            if "exceptionDetails" in res:
                raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        log("Waiting for page and scripts ready...")
        for _ in range(40):
            ready = eval_js("document.readyState === 'complete' && !!window.TempoEmergencyFlow && !!window.TempoPlanStore")
            if ready:
                break
            time.sleep(0.2)

        # Setup test data with 4 subtasks as described in prompt
        setup_script = """
        (function() {
            localStorage.clear();
            const task = {
                id: 'task_essay_1',
                name: 'History Essay',
                deadlineDate: '2026-10-02',
                deadlineTime: '17:00',
                hasFixedDeadline: true,
                durationMinutes: 120,
                durationLabel: '2h',
                importance: 'HIGH',
                consequence: 'Grade drop',
                flexibility: 'NONE',
                executionStatus: 'pending',
                subtasks: [
                    { id: 'st_1', title: 'Open rubric and paste prompt into a clean doc', durationMinutes: 15 },
                    { id: 'st_2', title: 'Write bullet outline for the 3 main sections', durationMinutes: 30 },
                    { id: 'st_3', title: 'Draft rough introduction and first body paragraph', durationMinutes: 45 },
                    { id: 'st_4', title: 'Proofread and check reference citations', durationMinutes: 30 }
                ]
            };

            const confirmedPlan = {
                id: 'plan_test_subtask',
                tasks: [task],
                plannedTasks: [
                    {
                        task: task,
                        dayDate: '2026-10-01',
                        dayLabel: 'Tomorrow',
                        startTime: '9:00 AM',
                        endTime: '11:30 AM',
                        executionBadge: 'UP NEXT'
                    }
                ],
                unarrangedTasks: [],
                availability: [
                    { date: '2026-10-01', dayOfWeek: 'Thursday', slots: [{ from: '09:00', to: '17:00' }] }
                ]
            };

            document.querySelectorAll('.screen-container').forEach(s => s.classList.add('hidden'));
            const emScreen = document.getElementById('screen-emergency');
            if (emScreen) emScreen.classList.remove('hidden');
            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
                window.TempoMode.setMode('emergency');
            }
            window.location.hash = '#emergency';
            window.TempoPlanStore.saveActivePlan('emergency', confirmedPlan);
            window.TempoEmergencyFlow.restorePlanState();
            window.TempoEmergencyFlow.goToStage('breakdown');
            return true;
        })()
        """
        eval_js(setup_script)
        time.sleep(0.3)

        # -------------------------------------------------------------
        # TEST 1: Initial Breakdown UI Verification
        # -------------------------------------------------------------
        log("\n--- TEST 1: INITIAL BREAKDOWN UI VERIFICATION ---")
        init_ui = eval_js("""
        (function() {
            const subtaskCards = document.querySelectorAll('.em-subtask-item');
            const titles = Array.from(subtaskCards).map(c => c.querySelector('.truncate')?.textContent?.trim());
            const numbers = Array.from(subtaskCards).map(c => c.querySelector('.rounded-full')?.textContent?.trim());
            const handles = document.querySelectorAll('.em-subtask-drag-handle');
            const removeBtns = document.querySelectorAll('.em-subtask-item button[title="Remove step"]');
            const arrowUp = Array.from(document.querySelectorAll('.em-subtask-item button')).filter(b => b.textContent.includes('▲'));
            const arrowDown = Array.from(document.querySelectorAll('.em-subtask-item button')).filter(b => b.textContent.includes('▼'));

            return {
                cardCount: subtaskCards.length,
                titles: titles,
                numbers: numbers,
                handlesCount: handles.length,
                removeBtnsCount: removeBtns.length,
                arrowUpCount: arrowUp.length,
                arrowDownCount: arrowDown.length
            };
        })()
        """)
        log(f"Initial UI State: {json.dumps(init_ui, indent=2)}")

        assert init_ui["cardCount"] == 4, f"Expected 4 subtasks, got {init_ui['cardCount']}"
        assert init_ui["arrowUpCount"] == 0, f"Expected 0 ▲ buttons, got {init_ui['arrowUpCount']}"
        assert init_ui["arrowDownCount"] == 0, f"Expected 0 ▼ buttons, got {init_ui['arrowDownCount']}"
        assert init_ui["handlesCount"] == 4, f"Expected 4 drag handles, got {init_ui['handlesCount']}"
        assert init_ui["removeBtnsCount"] == 4, f"Expected 4 remove ✕ buttons, got {init_ui['removeBtnsCount']}"
        assert init_ui["numbers"] == ['1', '2', '3', '4'], f"Expected numbers 1..4, got {init_ui['numbers']}"
        assert init_ui["titles"][0] == "Open rubric and paste prompt into a clean doc"
        assert init_ui["titles"][2] == "Draft rough introduction and first body paragraph"
        log(">>> TEST 1 PASSED: Arrows removed, drag handles present, remove buttons intact.")

        # -------------------------------------------------------------
        # TEST 2: Drag Step 3 above Step 1 (Index 2 -> Index 0)
        # -------------------------------------------------------------
        log("\n--- TEST 2: DRAG STEP 3 ABOVE STEP 1 (Index 2 -> Index 0) ---")
        drag_res = eval_js("""
        (function() {
            const cards = document.querySelectorAll('.em-subtask-item');
            const card3 = cards[2];
            const card1 = cards[0];

            // Simulate dragstart on card 3 (index 2)
            const dt = new DataTransfer();
            const dragStartEvt = new DragEvent('dragstart', {
                bubbles: true,
                cancelable: true,
                dataTransfer: dt
            });
            card3.dispatchEvent(dragStartEvt);

            // Simulate dragover on card 1 (index 0)
            const dragOverEvt = new DragEvent('dragover', {
                bubbles: true,
                cancelable: true,
                dataTransfer: dt
            });
            card1.dispatchEvent(dragOverEvt);

            // Simulate drop on card 1 (index 0)
            const dropEvt = new DragEvent('drop', {
                bubbles: true,
                cancelable: true,
                dataTransfer: dt
            });
            card1.dispatchEvent(dropEvt);

            // Simulate dragend
            const dragEndEvt = new DragEvent('dragend', {
                bubbles: true,
                cancelable: true,
                dataTransfer: dt
            });
            card3.dispatchEvent(dragEndEvt);

            const updatedCards = document.querySelectorAll('.em-subtask-item');
            const updatedTitles = Array.from(updatedCards).map(c => c.querySelector('.truncate')?.textContent?.trim());
            const updatedNumbers = Array.from(updatedCards).map(c => c.querySelector('.rounded-full')?.textContent?.trim());

            return {
                titles: updatedTitles,
                numbers: updatedNumbers
            };
        })()
        """)
        log(f"After dragging Step 3 above Step 1: {json.dumps(drag_res, indent=2)}")

        expected_titles = [
            "Draft rough introduction and first body paragraph",
            "Open rubric and paste prompt into a clean doc",
            "Write bullet outline for the 3 main sections",
            "Proofread and check reference citations"
        ]
        assert drag_res["titles"] == expected_titles, f"Expected {expected_titles}, got {drag_res['titles']}"
        assert drag_res["numbers"] == ['1', '2', '3', '4'], f"Expected numbers 1..4, got {drag_res['numbers']}"
        log(">>> TEST 2 PASSED: Subtask successfully reordered via drag-and-drop.")

        # -------------------------------------------------------------
        # TEST 3: Drag Step 4 to position 2 (Index 3 -> Index 1)
        # -------------------------------------------------------------
        log("\n--- TEST 3: DRAG STEP 4 TO POSITION 2 (Index 3 -> Index 1) ---")
        drag_res2 = eval_js("""
        (function() {
            window.TempoEmergencyFlow.reorderSubtasks(3, 1);
            const cards = document.querySelectorAll('.em-subtask-item');
            const titles = Array.from(cards).map(c => c.querySelector('.truncate')?.textContent?.trim());
            const numbers = Array.from(cards).map(c => c.querySelector('.rounded-full')?.textContent?.trim());
            return { titles, numbers };
        })()
        """)
        log(f"After moving Step 4 to position 2: {json.dumps(drag_res2, indent=2)}")

        expected_titles_2 = [
            "Draft rough introduction and first body paragraph",
            "Proofread and check reference citations",
            "Open rubric and paste prompt into a clean doc",
            "Write bullet outline for the 3 main sections"
        ]
        assert drag_res2["titles"] == expected_titles_2, f"Expected {expected_titles_2}, got {drag_res2['titles']}"
        log(">>> TEST 3 PASSED: Direct reorderSubtasks call reordered correctly.")

        # -------------------------------------------------------------
        # TEST 4: Touch Reordering Simulation
        # -------------------------------------------------------------
        log("\n--- TEST 4: TOUCH DRAGGING SIMULATION ---")
        touch_res = eval_js("""
        (function() {
            const handles = document.querySelectorAll('.em-subtask-drag-handle');
            const handle1 = handles[1]; // Index 1: "Proofread and check reference citations"
            const cards = document.querySelectorAll('.em-subtask-item');
            const cardLast = cards[3]; // Move to last position (index 3)

            cardLast.scrollIntoView({ block: 'center' });
            const rectTarget = cardLast.getBoundingClientRect();

            // Touch start on handle 1
            const touchObj = {
                clientX: rectTarget.left + 20,
                clientY: rectTarget.top + rectTarget.height / 2
            };

            // Call handlers directly
            window.TempoEmergencyFlow.handleSubtaskTouchStart({
                currentTarget: handle1,
                touches: [touchObj]
            }, 1);

            const elemAtPoint = document.elementFromPoint(touchObj.clientX, touchObj.clientY);

            // Touch move over cardLast
            window.TempoEmergencyFlow.handleSubtaskTouchMove({
                touches: [touchObj],
                cancelable: true,
                preventDefault: () => {}
            });

            // Touch end
            window.TempoEmergencyFlow.handleSubtaskTouchEnd({
                cancelable: true
            });

            const updatedCards = document.querySelectorAll('.em-subtask-item');
            const titles = Array.from(updatedCards).map(c => c.querySelector('.truncate')?.textContent?.trim());
            return {
                titles,
                elemAtPointFound: !!elemAtPoint,
                elemTag: elemAtPoint ? elemAtPoint.tagName : null,
                rectTarget: { top: rectTarget.top, left: rectTarget.left, height: rectTarget.height },
                viewportH: window.innerHeight
            };
        })()
        """)
        log(f"After touch dragging: {json.dumps(touch_res, indent=2)}")
        assert touch_res["titles"][3] == "Proofread and check reference citations", "Expected Proofread at index 3"
        log(">>> TEST 4 PASSED: Touch dragging reordered correctly.")

        # -------------------------------------------------------------
        # TEST 5: Persistence & Subtask Integrity Across Reload
        # -------------------------------------------------------------
        log("\n--- TEST 5: PERSISTENCE & SUBTASK INTEGRITY ACROSS RELOAD ---")
        before_reload = eval_js("""
        (function() {
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const subtasks = plan.plannedTasks[0].task.subtasks;
            return {
                taskId: plan.plannedTasks[0].task.id,
                subtaskCount: subtasks.length,
                subtaskTitles: subtasks.map(s => s.title),
                subtaskIds: subtasks.map(s => s.id),
                subtaskDurations: subtasks.map(s => s.durationMinutes)
            };
        })()
        """)
        log(f"State before reload: {json.dumps(before_reload, indent=2)}")

        # Reload the page
        log("Reloading page...")
        eval_js("location.reload()")
        time.sleep(1.5)

        for _ in range(40):
            ready = eval_js("document.readyState === 'complete' && !!window.TempoEmergencyFlow && !!window.TempoPlanStore")
            if ready:
                break
            time.sleep(0.2)

        after_reload = eval_js("""
        (function() {
            document.querySelectorAll('.screen-container').forEach(s => s.classList.add('hidden'));
            const emScreen = document.getElementById('screen-emergency');
            if (emScreen) emScreen.classList.remove('hidden');
            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
                window.TempoMode.setMode('emergency');
            }
            window.location.hash = '#emergency';
            window.TempoEmergencyFlow.restorePlanState();
            window.TempoEmergencyFlow.goToStage('breakdown');
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            if (!plan || !plan.plannedTasks) return null;
            const subtasks = plan.plannedTasks[0].task.subtasks;
            const cards = document.querySelectorAll('.em-subtask-item');
            const domTitles = Array.from(cards).map(c => c.querySelector('.truncate')?.textContent?.trim());
            const handlesCount = document.querySelectorAll('.em-subtask-drag-handle').length;
            const arrowsCount = Array.from(document.querySelectorAll('.em-subtask-item button')).filter(b => b.textContent.includes('▲') || b.textContent.includes('▼')).length;

            return {
                taskId: plan.plannedTasks[0].task.id,
                subtaskCount: subtasks.length,
                subtaskTitles: subtasks.map(s => s.title),
                subtaskIds: subtasks.map(s => s.id),
                subtaskDurations: subtasks.map(s => s.durationMinutes),
                domTitles: domTitles,
                handlesCount: handlesCount,
                arrowsCount: arrowsCount
            };
        })()
        """)
        log(f"State after reload: {json.dumps(after_reload, indent=2)}")

        assert after_reload["taskId"] == before_reload["taskId"], "Task ID changed after reload!"
        assert after_reload["subtaskTitles"] == before_reload["subtaskTitles"], "Subtask order lost after reload!"
        assert after_reload["subtaskIds"] == before_reload["subtaskIds"], "Subtask IDs changed after reload!"
        assert after_reload["subtaskDurations"] == before_reload["subtaskDurations"], "Subtask durations lost!"
        assert after_reload["domTitles"] == before_reload["subtaskTitles"], "DOM titles do not match persisted order!"
        assert after_reload["handlesCount"] == 4, "Drag handles count mismatch after reload!"
        assert after_reload["arrowsCount"] == 0, "Arrow buttons reappeared after reload!"
        log(">>> TEST 5 PASSED: Persistence and subtask integrity verified across reload.")

        # -------------------------------------------------------------
        # TEST 6: Add and Remove Subtask Functionality
        # -------------------------------------------------------------
        log("\n--- TEST 6: ADD AND REMOVE SUBTASK FUNCTIONALITY ---")
        add_remove_res = eval_js("""
        (function() {
            // Add a new subtask
            window.TempoEmergencyFlow.addSubtask('Fifth action step', 20);
            const afterAddCount = document.querySelectorAll('.em-subtask-item').length;
            const afterAddHandles = document.querySelectorAll('.em-subtask-drag-handle').length;

            // Remove subtask at index 0
            window.TempoEmergencyFlow.removeSubtask(0);
            const afterRemoveCount = document.querySelectorAll('.em-subtask-item').length;
            const cards = document.querySelectorAll('.em-subtask-item');
            const numbers = Array.from(cards).map(c => c.querySelector('.rounded-full')?.textContent?.trim());

            return {
                afterAddCount,
                afterAddHandles,
                afterRemoveCount,
                numbers
            };
        })()
        """)
        log(f"Add/Remove result: {json.dumps(add_remove_res, indent=2)}")
        assert add_remove_res["afterAddCount"] == 5, "Add subtask failed"
        assert add_remove_res["afterAddHandles"] == 5, "New subtask missing drag handle"
        assert add_remove_res["afterRemoveCount"] == 4, "Remove subtask failed"
        assert add_remove_res["numbers"] == ['1', '2', '3', '4'], "Numbers re-sequencing failed after remove"
        log(">>> TEST 6 PASSED: Add and remove subtask verified.")

        log("\n=======================================================")
        log("ALL BREAKDOWN SUBTASK TESTS PASSED WITH 100% SUCCESS!")
        log("=======================================================")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    run_tests()
