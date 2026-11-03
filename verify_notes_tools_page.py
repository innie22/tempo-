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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_tool_notes_page_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9530

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#tool-notes"
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
    app_tabs = [t for t in tabs if "127.0.0.1:8000" in t.get("url", "") or "localhost:8000" in t.get("url", "")]
    if not app_tabs:
        ws_url = tabs[0]["webSocketDebuggerUrl"]
    else:
        ws_url = app_tabs[0]["webSocketDebuggerUrl"]

    ws = websocket.create_connection(ws_url)
    send_cmd("Page.enable")
    send_cmd("DOM.enable")

    print("Connected to browser via CDP!")
    time.sleep(1.5)

    # Clear notes in localStorage for clean test baseline
    eval_js("""
    (() => {
        localStorage.removeItem('tempo_tool_notes');
        const user = window.TempoAuth ? window.TempoAuth.getCurrentUserId() : 'guest';
        localStorage.removeItem('tempo_tool_notes_' + user);
        window.TempoToolNotes.renderToolNotesPage();
    })()
    """)
    time.sleep(0.5)

    # -------------------------------------------------------------------------
    # TEST 1: Vietnamese Mode (vi) Initial Empty State
    # -------------------------------------------------------------------------
    print("\n--- TEST 1: Vietnamese Mode (vi) Empty State ---")
    eval_js("window.TempoI18n.setLanguage('vi')")
    time.sleep(0.5)

    vi_empty_page = eval_js("""
    (() => {
        return {
            backBtn: document.getElementById('btn-tool-notes-back')?.innerText.trim(),
            pageTitle: document.querySelector('#tool-notes-root h1')?.innerText.trim(),
            pageSubtitle: document.querySelector('#tool-notes-root p.text-xs, #tool-notes-root p.text-sm')?.innerText.trim(),
            createHeading: document.querySelector('[data-tempo-ui="tool-notes-create-section"] h2')?.innerText.trim(),
            pillDay: document.getElementById('pill-type-day')?.innerText.trim(),
            pillTask: document.getElementById('pill-type-task')?.innerText.trim(),
            titleLabel: document.querySelector("label[for='input-note-title']")?.innerText.trim(),
            titlePlaceholder: document.getElementById('input-note-title')?.getAttribute('placeholder'),
            dateLabel: document.querySelector("label[for='input-note-date']")?.innerText.trim(),
            dateHelper: document.querySelector('#form-group-day-date p')?.innerText.trim(),
            contentLabel: document.querySelector("label[for='textarea-note-content']")?.innerText.trim(),
            contentPlaceholder: document.getElementById('textarea-note-content')?.getAttribute('placeholder'),
            cancelBtn: document.querySelector('#tool-notes-create-form button[type="button"]')?.innerText.trim(),
            saveBtn: document.getElementById('btn-save-note-submit')?.innerText.trim(),
            dayPanelHeading: document.querySelector('[data-tempo-ui="tool-notes-day-panel"] h3')?.innerText.trim(),
            dayGroupedBy: document.querySelector('[data-tempo-ui="tool-notes-day-panel"] span.text-xs')?.innerText.trim(),
            emptyDayTitle: document.querySelector('[data-tempo-ui="day-notes-empty"] h4')?.innerText.trim(),
            emptyDayDesc: document.querySelector('[data-tempo-ui="day-notes-empty"] p')?.innerText.trim(),
            emptyDayBtn: document.querySelector('[data-tempo-ui="day-notes-empty"] button')?.innerText.trim(),
            taskPanelHeading: document.querySelector('[data-tempo-ui="tool-notes-task-panel"] h3')?.innerText.trim(),
            taskAttachedTo: document.querySelector('[data-tempo-ui="tool-notes-task-panel"] span.text-xs')?.innerText.trim()
        };
    })()
    """)

    for k, v in vi_empty_page.items():
        print(f"  {k}: '{v}'")

    assert vi_empty_page['backBtn'] == "← Trở về Dashboard", f"backBtn mismatch: {vi_empty_page['backBtn']}"
    assert vi_empty_page['pageTitle'] == "Notes Tools", f"pageTitle mismatch: {vi_empty_page['pageTitle']}"
    assert vi_empty_page['pageSubtitle'] == "Không gian riêng để lưu giữ những suy nghĩ hằng ngày và ghi chú cho các task học tập của bạn.", f"pageSubtitle mismatch: {vi_empty_page['pageSubtitle']}"
    assert vi_empty_page['createHeading'] == "Tạo ghi chú", f"createHeading mismatch: {vi_empty_page['createHeading']}"
    assert "Note theo ngày" in vi_empty_page['pillDay'], f"pillDay mismatch: {vi_empty_page['pillDay']}"
    assert "Note theo task" in vi_empty_page['pillTask'], f"pillTask mismatch: {vi_empty_page['pillTask']}"
    assert vi_empty_page['titleLabel'] == "Tiêu đề (không bắt buộc)", f"titleLabel mismatch: {vi_empty_page['titleLabel']}"
    assert vi_empty_page['dateLabel'] == "Ngày ghi chú", f"dateLabel mismatch: {vi_empty_page['dateLabel']}"
    assert vi_empty_page['dateHelper'] == "Ngày mặc định là hôm nay. Bạn có thể chọn ngày khác nếu cần.", f"dateHelper mismatch: {vi_empty_page['dateHelper']}"
    assert vi_empty_page['contentLabel'] == "Nội dung ghi chú", f"contentLabel mismatch: {vi_empty_page['contentLabel']}"
    assert vi_empty_page['contentPlaceholder'] == "Ghi lại suy nghĩ, lời nhắc hoặc những điều bạn muốn lưu giữ trong ngày...", f"contentPlaceholder mismatch: {vi_empty_page['contentPlaceholder']}"
    assert vi_empty_page['cancelBtn'] == "Hủy", f"cancelBtn mismatch: {vi_empty_page['cancelBtn']}"
    assert vi_empty_page['saveBtn'] == "Lưu ghi chú", f"saveBtn mismatch: {vi_empty_page['saveBtn']}"
    assert vi_empty_page['dayPanelHeading'] == "Note theo ngày", f"dayPanelHeading mismatch: {vi_empty_page['dayPanelHeading']}"
    assert vi_empty_page['dayGroupedBy'] == "Nhóm theo ngày", f"dayGroupedBy mismatch: {vi_empty_page['dayGroupedBy']}"
    assert vi_empty_page['emptyDayTitle'] == "Chưa có ghi chú theo ngày nào.", f"emptyDayTitle mismatch: {vi_empty_page['emptyDayTitle']}"
    assert vi_empty_page['emptyDayDesc'] == "Ghi lại suy nghĩ, mức năng lượng hoặc những cảm nhận của bạn mỗi ngày.", f"emptyDayDesc mismatch: {vi_empty_page['emptyDayDesc']}"
    assert vi_empty_page['emptyDayBtn'] == "+ Thêm note theo ngày", f"emptyDayBtn mismatch: {vi_empty_page['emptyDayBtn']}"
    assert vi_empty_page['taskPanelHeading'] == "Note theo task", f"taskPanelHeading mismatch: {vi_empty_page['taskPanelHeading']}"
    assert vi_empty_page['taskAttachedTo'] == "Được liên kết với task", f"taskAttachedTo mismatch: {vi_empty_page['taskAttachedTo']}"

    # -------------------------------------------------------------------------
    # TEST 2: Create Day Note and Task Note
    # -------------------------------------------------------------------------
    print("\n--- TEST 2: Create Day Note & Task Note ---")
    # 2a. Create a Day Note
    day_note_title = "Suy nghĩ buổi sáng"
    day_note_content = "Cảm thấy tập trung tốt sau giấc ngủ ngon."
    eval_js(f"""
    (() => {{
        window.TempoToolNotes.saveDayNote({json.dumps(day_note_content)}, window.TempoToolNotes.getTodayLocalDateStr(), null, {json.dumps(day_note_title)});
    }})()
    """)

    # 2b. Create a Task Note
    task_id = "task_cs101_ps4"
    task_name = "Statistics Assignment (Problem Set 4)"
    task_note_content = "Công thức cần áp dụng: P(A|B) = P(B|A)*P(A)/P(B)"
    eval_js(f"""
    (() => {{
        window.TempoToolNotes.saveTaskNote({json.dumps(task_id)}, {json.dumps(task_name)}, {json.dumps(task_note_content)}, null, '');
    }})()
    """)
    time.sleep(0.5)

    # -------------------------------------------------------------------------
    # TEST 3: Inspect Populated Vietnamese Mode
    # -------------------------------------------------------------------------
    print("\n--- TEST 3: Inspect Populated Vietnamese Mode ---")
    vi_populated = eval_js("""
    (() => {
        const taskCard = document.querySelector('[data-tempo-ui="tool-notes-task-panel"] [data-task-note-id]');
        const dayCard = document.querySelector('[data-tempo-ui="tool-notes-day-panel"] [data-day-note-id]');
        return {
            dayBadgeCount: document.getElementById('day-notes-count-badge')?.innerText.trim(),
            taskBadgeCount: document.getElementById('task-notes-count-badge')?.innerText.trim(),
            dayCardBadge: dayCard?.querySelector('span.rounded-full')?.innerText.trim(),
            dayCardTitle: dayCard?.querySelector('h5')?.innerText.trim(),
            dayViewDetails: dayCard?.querySelector('.border-t span.font-medium')?.innerText.trim(),
            dayClickExpand: dayCard?.querySelector('.border-t span.text-stone-400')?.innerText.trim(),
            taskCardBadge: taskCard?.querySelector('span.rounded-full')?.innerText.trim(),
            taskCardTaskName: taskCard?.querySelector('.truncate')?.innerText.trim(),
            taskCardTitle: taskCard?.querySelector('h5')?.innerText.trim(),
            taskViewDetails: taskCard?.querySelector('.border-t span.font-medium')?.innerText.trim(),
            taskClickExpand: taskCard?.querySelector('.border-t span.text-stone-400')?.innerText.trim()
        };
    })()
    """)

    for k, v in vi_populated.items():
        print(f"  {k}: '{v}'")

    assert vi_populated['dayBadgeCount'] == "1", f"dayBadgeCount mismatch: {vi_populated['dayBadgeCount']}"
    assert vi_populated['taskBadgeCount'] == "1", f"taskBadgeCount mismatch: {vi_populated['taskBadgeCount']}"
    assert "note theo ngày" in vi_populated['dayCardBadge'].lower(), f"dayCardBadge mismatch: {vi_populated['dayCardBadge']}"
    assert vi_populated['dayCardTitle'] == day_note_title, f"dayCardTitle mismatch: {vi_populated['dayCardTitle']}"
    assert vi_populated['dayViewDetails'] == "Xem chi tiết →", f"dayViewDetails mismatch: {vi_populated['dayViewDetails']}"
    assert vi_populated['dayClickExpand'] == "Nhấn để mở rộng", f"dayClickExpand mismatch: {vi_populated['dayClickExpand']}"
    assert vi_populated['taskCardBadge'] == "NOTE THEO TASK", f"taskCardBadge mismatch: {vi_populated['taskCardBadge']}"
    assert vi_populated['taskCardTitle'] == f"Note cho {task_name}", f"taskCardTitle mismatch: {vi_populated['taskCardTitle']}"
    assert vi_populated['taskViewDetails'] == "Xem chi tiết →", f"taskViewDetails mismatch: {vi_populated['taskViewDetails']}"
    assert vi_populated['taskClickExpand'] == "Nhấn để mở rộng", f"taskClickExpand mismatch: {vi_populated['taskClickExpand']}"

    capture_screenshot("notes_tool_page_vi.png")

    # -------------------------------------------------------------------------
    # TEST 4: Switch to English Mode (en)
    # -------------------------------------------------------------------------
    print("\n--- TEST 4: English Mode (en) Inspection ---")
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(0.5)

    en_populated = eval_js("""
    (() => {
        const taskCard = document.querySelector('[data-tempo-ui="tool-notes-task-panel"] [data-task-note-id]');
        const dayCard = document.querySelector('[data-tempo-ui="tool-notes-day-panel"] [data-day-note-id]');
        return {
            backBtn: document.getElementById('btn-tool-notes-back')?.innerText.trim(),
            pageTitle: document.querySelector('#tool-notes-root h1')?.innerText.trim(),
            pageSubtitle: document.querySelector('#tool-notes-root p.text-xs, #tool-notes-root p.text-sm')?.innerText.trim(),
            createHeading: document.querySelector('[data-tempo-ui="tool-notes-create-section"] h2')?.innerText.trim(),
            pillDay: document.getElementById('pill-type-day')?.innerText.trim(),
            pillTask: document.getElementById('pill-type-task')?.innerText.trim(),
            titleLabel: document.querySelector("label[for='input-note-title']")?.innerText.trim(),
            dateLabel: document.querySelector("label[for='input-note-date']")?.innerText.trim(),
            dateHelper: document.querySelector('#form-group-day-date p')?.innerText.trim(),
            contentLabel: document.querySelector("label[for='textarea-note-content']")?.innerText.trim(),
            contentPlaceholder: document.getElementById('textarea-note-content')?.getAttribute('placeholder'),
            cancelBtn: document.querySelector('#tool-notes-create-form button[type="button"]')?.innerText.trim(),
            saveBtn: document.getElementById('btn-save-note-submit')?.innerText.trim(),
            dayPanelHeading: document.querySelector('[data-tempo-ui="tool-notes-day-panel"] h3')?.innerText.trim(),
            dayGroupedBy: document.querySelector('[data-tempo-ui="tool-notes-day-panel"] span.text-xs')?.innerText.trim(),
            dayCardBadge: dayCard?.querySelector('span.rounded-full')?.innerText.trim(),
            dayViewDetails: dayCard?.querySelector('.border-t span.font-medium')?.innerText.trim(),
            dayClickExpand: dayCard?.querySelector('.border-t span.text-stone-400')?.innerText.trim(),
            taskPanelHeading: document.querySelector('[data-tempo-ui="tool-notes-task-panel"] h3')?.innerText.trim(),
            taskAttachedTo: document.querySelector('[data-tempo-ui="tool-notes-task-panel"] span.text-xs')?.innerText.trim(),
            taskCardBadge: taskCard?.querySelector('span.rounded-full')?.innerText.trim(),
            taskCardTitle: taskCard?.querySelector('h5')?.innerText.trim(),
            taskViewDetails: taskCard?.querySelector('.border-t span.font-medium')?.innerText.trim(),
            taskClickExpand: taskCard?.querySelector('.border-t span.text-stone-400')?.innerText.trim()
        };
    })()
    """)

    for k, v in en_populated.items():
        print(f"  {k}: '{v}'")

    assert en_populated['backBtn'] == "← Back to Dashboard", f"backBtn EN mismatch: {en_populated['backBtn']}"
    assert en_populated['pageTitle'] == "Notes Tool", f"pageTitle EN mismatch: {en_populated['pageTitle']}"
    assert en_populated['pageSubtitle'] == "A calm, dedicated space to keep your daily reflections and academic task notes organized.", f"pageSubtitle EN mismatch: {en_populated['pageSubtitle']}"
    assert en_populated['createHeading'] == "Create Notes", f"createHeading EN mismatch: {en_populated['createHeading']}"
    assert "Day Note" in en_populated['pillDay'], f"pillDay EN mismatch: {en_populated['pillDay']}"
    assert "Task Note" in en_populated['pillTask'], f"pillTask EN mismatch: {en_populated['pillTask']}"
    assert en_populated['titleLabel'] == "Note Title (optional)", f"titleLabel EN mismatch: {en_populated['titleLabel']}"
    assert en_populated['dateLabel'] == "Calendar Date", f"dateLabel EN mismatch: {en_populated['dateLabel']}"
    assert en_populated['dateHelper'] == "Defaults to today's local date. You can select another date if needed.", f"dateHelper EN mismatch: {en_populated['dateHelper']}"
    assert en_populated['contentLabel'] == "Note Content", f"contentLabel EN mismatch: {en_populated['contentLabel']}"
    assert en_populated['contentPlaceholder'] == "Write reflections, reminders, or general observations for the day...", f"contentPlaceholder EN mismatch: {en_populated['contentPlaceholder']}"
    assert en_populated['cancelBtn'] == "Cancel", f"cancelBtn EN mismatch: {en_populated['cancelBtn']}"
    assert en_populated['saveBtn'] == "Save Note", f"saveBtn EN mismatch: {en_populated['saveBtn']}"
    assert en_populated['dayPanelHeading'] == "Day Notes", f"dayPanelHeading EN mismatch: {en_populated['dayPanelHeading']}"
    assert en_populated['dayGroupedBy'] == "Grouped by date", f"dayGroupedBy EN mismatch: {en_populated['dayGroupedBy']}"
    assert "day note" in en_populated['dayCardBadge'].lower(), f"dayCardBadge EN mismatch: {en_populated['dayCardBadge']}"
    assert en_populated['dayViewDetails'] == "View details →", f"dayViewDetails EN mismatch: {en_populated['dayViewDetails']}"
    assert en_populated['dayClickExpand'] == "Click to expand", f"dayClickExpand EN mismatch: {en_populated['dayClickExpand']}"
    assert en_populated['taskPanelHeading'] == "Task Notes", f"taskPanelHeading EN mismatch: {en_populated['taskPanelHeading']}"
    assert en_populated['taskAttachedTo'] == "Attached to tasks", f"taskAttachedTo EN mismatch: {en_populated['taskAttachedTo']}"
    assert en_populated['taskCardBadge'] == "TASK NOTE", f"taskCardBadge EN mismatch: {en_populated['taskCardBadge']}"
    assert en_populated['taskCardTitle'] == f"Note for {task_name}", f"taskCardTitle EN mismatch: {en_populated['taskCardTitle']}"
    assert en_populated['taskViewDetails'] == "View details →", f"taskViewDetails EN mismatch: {en_populated['taskViewDetails']}"
    assert en_populated['taskClickExpand'] == "Click to expand", f"taskClickExpand EN mismatch: {en_populated['taskClickExpand']}"

    capture_screenshot("notes_tool_page_en.png")

    # -------------------------------------------------------------------------
    # TEST 5: Card click opens Detail Modal
    # -------------------------------------------------------------------------
    print("\n--- TEST 5: Card Click Opens Detail Modal ---")
    eval_js("document.querySelector('[data-tempo-ui=\"tool-notes-task-panel\"] [data-task-note-id]').click()")
    time.sleep(0.5)

    modal_open = eval_js("document.getElementById('note-detail-backdrop') !== null")
    assert modal_open, "Note detail modal did not open on card click!"
    modal_title = eval_js("document.getElementById('note-detail-title')?.innerText.trim()")
    print(f"Detail Modal Title: '{modal_title}'")
    assert task_name in modal_title, f"Task name missing from detail modal title: {modal_title}"

    # Close detail modal
    eval_js("window.TempoToolNotes.closeModal()")
    time.sleep(0.3)
    modal_closed = eval_js("document.getElementById('tool-notes-modal-root')?.innerHTML === ''")
    assert modal_closed, "Detail modal failed to close!"
    print("Detail modal opened and closed cleanly.")

    # -------------------------------------------------------------------------
    # TEST 6: Page Reload Persistence
    # -------------------------------------------------------------------------
    print("\n--- TEST 6: Page Reload Persistence ---")
    send_cmd("Page.reload")
    time.sleep(2)
    reloaded_count = eval_js("window.TempoToolNotes.getNotes().length")
    print(f"Notes count after reload: {reloaded_count}")
    assert reloaded_count == 2, f"Notes lost after reload! Got: {reloaded_count}"

    print("\n=======================================================")
    print("ALL TESTS & FUNCTIONAL REGRESSION CHECKS PASSED 100%!")
    print("=======================================================")

finally:
    if ws:
        ws.close()
    proc.terminate()
