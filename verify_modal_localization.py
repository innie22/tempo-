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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_modal_loc_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9524

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

    # 1. Switch language to Vietnamese
    eval_js("window.TempoI18n.setLanguage('vi')")
    time.sleep(0.5)

    # 2. Open Create Notes Modal
    eval_js("window.TempoToolNotes.openCreateNoteModal()")
    time.sleep(0.5)

    # 3. Read Vietnamese texts from modal
    vi_data = eval_js("""
    (() => {
        return {
            title: document.getElementById('modal-heading-title')?.innerText || '',
            pillDay: document.getElementById('modal-pill-day')?.innerText || '',
            pillTask: document.getElementById('modal-pill-task')?.innerText || '',
            titleLabel: document.querySelector("label[for='modal-input-title']")?.innerText || '',
            titlePlaceholder: document.getElementById('modal-input-title')?.getAttribute('placeholder') || '',
            dateLabel: document.querySelector("label[for='modal-input-date']")?.innerText || '',
            dateHelper: document.querySelector("#modal-group-date p")?.innerText || '',
            contentLabel: document.querySelector("label[for='modal-textarea-content']")?.innerText || '',
            contentPlaceholder: document.getElementById('modal-textarea-content')?.getAttribute('placeholder') || '',
            cancelBtn: document.getElementById('modal-btn-cancel')?.innerText || '',
            saveBtn: document.getElementById('modal-btn-submit')?.innerText || ''
        };
    })()
    """)

    print("\n--- VIETNAMESE MODAL DATA ---")
    for k, v in vi_data.items():
        print(f"  {k}: '{v}'")

    assert vi_data['title'] == "Tạo Notes", f"Modal title mismatch: {vi_data['title']}"
    assert "Note theo ngày" in vi_data['pillDay'], f"Pill day mismatch: {vi_data['pillDay']}"
    assert "Note theo task" in vi_data['pillTask'], f"Pill task mismatch: {vi_data['pillTask']}"
    assert vi_data['titleLabel'] == "Tiêu đề (không bắt buộc)", f"Title label mismatch: {vi_data['titleLabel']}"
    assert vi_data['dateLabel'] == "Ngày ghi chú", f"Date label mismatch: {vi_data['dateLabel']}"
    assert vi_data['dateHelper'] == "Ngày được tự động điền theo hôm nay. Bạn có thể thay đổi nếu muốn tạo ghi chú cho ngày khác.", f"Date helper mismatch: {vi_data['dateHelper']}"
    assert vi_data['contentLabel'] == "Nội dung ghi chú", f"Content label mismatch: {vi_data['contentLabel']}"
    assert vi_data['contentPlaceholder'] == "Viết những suy nghĩ, lời nhắc hoặc điều bạn muốn ghi lại trong ngày...", f"Content placeholder mismatch: {vi_data['contentPlaceholder']}"
    assert vi_data['cancelBtn'] == "Hủy", f"Cancel button mismatch: {vi_data['cancelBtn']}"
    assert vi_data['saveBtn'] == "Lưu ghi chú", f"Save button mismatch: {vi_data['saveBtn']}"

    # 4. Fill in title & content
    test_title = "Ghi chú buổi chiều"
    test_content = "Cần chuẩn bị kế hoạch ôn tập cho tuần tới."
    eval_js(f"""
    (() => {{
        const titleEl = document.getElementById('modal-input-title');
        if (titleEl) titleEl.value = {json.dumps(test_title)};
        const contentEl = document.getElementById('modal-textarea-content');
        if (contentEl) contentEl.value = {json.dumps(test_content)};
    }})()
    """)
    time.sleep(0.3)

    capture_screenshot("create_notes_modal_vi.png")

    # 5. Switch language dynamically to English while modal is open
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(0.5)

    # 6. Verify input preservation
    preserved_data = eval_js("""
    (() => {
        return {
            titleVal: document.getElementById('modal-input-title')?.value || '',
            contentVal: document.getElementById('modal-textarea-content')?.value || ''
        };
    })()
    """)

    print("\n--- PRESERVED USER INPUT AFTER LANGUAGE SWITCH ---")
    print(f"  Title: '{preserved_data['titleVal']}' (Expected: '{test_title}')")
    print(f"  Content: '{preserved_data['contentVal']}' (Expected: '{test_content}')")
    assert preserved_data['titleVal'] == test_title, f"Preserved title mismatch: {preserved_data['titleVal']}"
    assert preserved_data['contentVal'] == test_content, f"Preserved content mismatch: {preserved_data['contentVal']}"

    # 7. Read English texts from modal
    en_data = eval_js("""
    (() => {
        return {
            title: document.getElementById('modal-heading-title')?.innerText || '',
            pillDay: document.getElementById('modal-pill-day')?.innerText || '',
            pillTask: document.getElementById('modal-pill-task')?.innerText || '',
            titleLabel: document.querySelector("label[for='modal-input-title']")?.innerText || '',
            titlePlaceholder: document.getElementById('modal-input-title')?.getAttribute('placeholder') || '',
            dateLabel: document.querySelector("label[for='modal-input-date']")?.innerText || '',
            dateHelper: document.querySelector("#modal-group-date p")?.innerText || '',
            contentLabel: document.querySelector("label[for='modal-textarea-content']")?.innerText || '',
            contentPlaceholder: document.getElementById('modal-textarea-content')?.getAttribute('placeholder') || '',
            cancelBtn: document.getElementById('modal-btn-cancel')?.innerText || '',
            saveBtn: document.getElementById('modal-btn-submit')?.innerText || ''
        };
    })()
    """)

    print("\n--- ENGLISH MODAL DATA ---")
    for k, v in en_data.items():
        print(f"  {k}: '{v}'")

    assert en_data['title'] == "Create Notes", f"Modal title EN mismatch: {en_data['title']}"
    assert "Day Note" in en_data['pillDay'], f"Pill day EN mismatch: {en_data['pillDay']}"
    assert "Task Note" in en_data['pillTask'], f"Pill task EN mismatch: {en_data['pillTask']}"
    assert en_data['titleLabel'] == "Note Title (optional)", f"Title label EN mismatch: {en_data['titleLabel']}"
    assert en_data['dateLabel'] == "Calendar Date", f"Date label EN mismatch: {en_data['dateLabel']}"
    assert en_data['dateHelper'] == "Prefilled with today's date. You can change it if creating for another day.", f"Date helper EN mismatch: {en_data['dateHelper']}"
    assert en_data['contentLabel'] == "Note Content", f"Content label EN mismatch: {en_data['contentLabel']}"
    assert en_data['contentPlaceholder'] == "Write reflections, reminders, or general observations for the day...", f"Content placeholder EN mismatch: {en_data['contentPlaceholder']}"
    assert en_data['cancelBtn'] == "Cancel", f"Cancel button EN mismatch: {en_data['cancelBtn']}"
    assert en_data['saveBtn'] == "Save Note", f"Save button EN mismatch: {en_data['saveBtn']}"

    capture_screenshot("create_notes_modal_en.png")

    # 8. Save the note
    initial_count = eval_js("window.TempoToolNotes.getNotes().length")
    eval_js("document.getElementById('modal-btn-submit').click()")
    time.sleep(0.5)

    new_count = eval_js("window.TempoToolNotes.getNotes().length")
    print(f"\nInitial count: {initial_count}, new count: {new_count}")
    assert new_count == initial_count + 1, "Note count did not increment!"

    latest_saved = eval_js("window.TempoToolNotes.getNotes()[0]")
    print(f"Latest saved note: id={latest_saved.get('id')}, title='{latest_saved.get('title')}', text='{latest_saved.get('text')}'")
    assert latest_saved.get('title') == test_title, "Saved title mismatch"
    assert latest_saved.get('text') == test_content, "Saved content mismatch"

    # 9. Test Task Note tab workflow
    print("\n--- TASK NOTE WORKFLOW TEST ---")
    eval_js("window.TempoToolNotes.openCreateNoteModal('task')")
    time.sleep(0.5)

    task_en_label = eval_js("document.querySelector(\"label[for='modal-select-task']\")?.innerText")
    print(f"Task Note Selector Label (EN): '{task_en_label}'")
    assert task_en_label == "Associated Study Task"

    eval_js("window.TempoI18n.setLanguage('vi')")
    time.sleep(0.5)

    task_vi_label = eval_js("document.querySelector(\"label[for='modal-select-task']\")?.innerText")
    print(f"Task Note Selector Label (VI): '{task_vi_label}'")
    assert task_vi_label == "Công việc Học tập liên kết"

    # Close modal
    eval_js("document.getElementById('modal-btn-cancel').click()")
    time.sleep(0.3)
    modal_closed = eval_js("document.getElementById('tool-notes-modal-root')?.innerHTML === ''")
    assert modal_closed, "Modal did not close on cancel"
    print("Modal closed successfully.")

    print("\n==========================================")
    print("ALL TESTS AND VERIFICATIONS PASSED 100%!")
    print("==========================================")

finally:
    if ws:
        ws.close()
    proc.terminate()
