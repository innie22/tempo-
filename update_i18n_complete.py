import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

assert '\r\n' in content, "CRLF not found in i18n.js!"
assert content.count('\n') == content.count('\r\n'), "Lone LF found before updating i18n.js!"

# Target vi block
vi_target = """            toolNotes: {
                createNotesTitle: "Tạo Notes",
                tabDayNote: "Note theo ngày",
                tabTaskNote: "Note theo task",
                noteTitleLabel: "Tiêu đề (không bắt buộc)",
                noteTitlePlaceholder: "VD: Suy nghĩ hôm nay, Tóm tắt bài giảng...",
                calendarDateLabel: "Ngày ghi chú",
                dateHelperText: "Ngày được tự động điền theo hôm nay. Bạn có thể thay đổi nếu muốn tạo ghi chú cho ngày khác.",
                associatedTaskLabel: "Công việc Học tập liên kết",
                selectTaskPlaceholder: "-- Chọn một task từ kế hoạch --",
                noActiveTasks: "Chưa có task nào trong kế hoạch",
                noteContentLabel: "Nội dung ghi chú",
                contentPlaceholderDay: "Viết những suy nghĩ, lời nhắc hoặc điều bạn muốn ghi lại trong ngày...",
                contentPlaceholderTask: "Viết ghi chú, dàn ý hoặc các bước hành động tiếp theo cho task này...",
                cancelAction: "Hủy",
                saveNoteAction: "Lưu ghi chú",
                validationContentMissing: "Vui lòng nhập nội dung ghi chú.",
                validationDateMissing: "Vui lòng chọn ngày hợp lệ.",
                validationTaskMissing: "Vui lòng chọn một công việc."
            }"""

vi_replacement = """            toolNotes: {
                createNotesTitle: "Tạo Notes",
                tabDayNote: "Note theo ngày",
                tabTaskNote: "Note theo task",
                noteTitleLabel: "Tiêu đề (không bắt buộc)",
                noteTitlePlaceholder: "VD: Suy nghĩ hôm nay, Tóm tắt bài giảng...",
                calendarDateLabel: "Ngày ghi chú",
                dateHelperText: "Ngày được tự động điền theo hôm nay. Bạn có thể thay đổi nếu muốn tạo ghi chú cho ngày khác.",
                associatedTaskLabel: "Công việc Học tập liên kết",
                selectTaskPlaceholder: "-- Chọn một task từ kế hoạch --",
                noActiveTasks: "Chưa có task nào trong kế hoạch",
                associatedTaskHelper: "Được điền từ kế hoạch làm việc và các công việc hiện tại của bạn.",
                noteContentLabel: "Nội dung ghi chú",
                contentPlaceholderDay: "Viết những suy nghĩ, lời nhắc hoặc điều bạn muốn ghi lại trong ngày...",
                contentPlaceholderTask: "Viết ghi chú, dàn ý hoặc các bước hành động tiếp theo cho task này...",
                cancelAction: "Hủy",
                saveNoteAction: "Lưu ghi chú",
                validationContentMissing: "Vui lòng nhập nội dung ghi chú.",
                validationDateMissing: "Vui lòng chọn ngày hợp lệ.",
                validationTaskMissing: "Vui lòng chọn một công việc.",
                saving: "Đang lưu...",

                // Page Header
                backToDashboard: "← Trở về Dashboard",
                pageTitle: "Notes Tools",
                pageSubtitle: "Không gian riêng để lưu giữ những suy nghĩ hằng ngày và ghi chú cho các task học tập của bạn.",

                // Page Create Notes Section
                sectionCreateNotes: "Tạo ghi chú",
                pageDateHelper: "Ngày mặc định là hôm nay. Bạn có thể chọn ngày khác nếu cần.",
                pageContentPlaceholderDay: "Ghi lại suy nghĩ, lời nhắc hoặc những điều bạn muốn lưu giữ trong ngày...",

                // Day Notes Section
                headingDayNotes: "Note theo ngày",
                groupedByDate: "Nhóm theo ngày",
                emptyDayNotesTitle: "Chưa có ghi chú theo ngày nào.",
                emptyDayNotesDesc: "Ghi lại suy nghĩ, mức năng lượng hoặc những cảm nhận của bạn mỗi ngày.",
                addDayNoteBtn: "+ Thêm note theo ngày",

                // Task Notes Section
                headingTaskNotes: "Note theo task",
                attachedToTasks: "Được liên kết với task",
                badgeTaskNote: "NOTE THEO TASK",
                noteForTask: "Note cho {taskName}",
                viewDetails: "Xem chi tiết →",
                clickToExpand: "Nhấn để mở rộng",
                emptyTaskNotesTitle: "Chưa có ghi chú công việc nào.",
                emptyTaskNotesDesc: "Liên kết ghi chú nghiên cứu, công thức hoặc các bước thực hiện với kế hoạch làm việc.",
                addTaskNoteBtn: "+ Thêm note theo task",

                // Detail and Edit Modals
                fullContent: "Nội dung đầy đủ",
                editNote: "Chỉnh sửa Ghi chú",
                saveChanges: "Lưu thay đổi",
                delete: "Xóa",
                close: "Đóng"
            }"""

# Target en block
en_target = """            toolNotes: {
                createNotesTitle: "Create Notes",
                tabDayNote: "Day Note",
                tabTaskNote: "Task Note",
                noteTitleLabel: "Note Title (optional)",
                noteTitlePlaceholder: "e.g. Daily reflection, Lecture summary...",
                calendarDateLabel: "Calendar Date",
                dateHelperText: "Prefilled with today's date. You can change it if creating for another day.",
                associatedTaskLabel: "Associated Study Task",
                selectTaskPlaceholder: "-- Select a task from your plan --",
                noActiveTasks: "No active tasks in your plan",
                noteContentLabel: "Note Content",
                contentPlaceholderDay: "Write reflections, reminders, or general observations for the day...",
                contentPlaceholderTask: "Write research notes, outlines, or next action steps for this task...",
                cancelAction: "Cancel",
                saveNoteAction: "Save Note",
                validationContentMissing: "Please enter note content.",
                validationDateMissing: "Please select a date.",
                validationTaskMissing: "Please select an associated task."
            }"""

en_replacement = """            toolNotes: {
                createNotesTitle: "Create Notes",
                tabDayNote: "Day Note",
                tabTaskNote: "Task Note",
                noteTitleLabel: "Note Title (optional)",
                noteTitlePlaceholder: "e.g. Daily reflection, Lecture summary...",
                calendarDateLabel: "Calendar Date",
                dateHelperText: "Prefilled with today's date. You can change it if creating for another day.",
                associatedTaskLabel: "Associated Study Task",
                selectTaskPlaceholder: "-- Select a task from your plan --",
                noActiveTasks: "No active tasks in your plan",
                associatedTaskHelper: "Populated from your working plan and current tasks.",
                noteContentLabel: "Note Content",
                contentPlaceholderDay: "Write reflections, reminders, or general observations for the day...",
                contentPlaceholderTask: "Write research notes, outlines, or next action steps for this task...",
                cancelAction: "Cancel",
                saveNoteAction: "Save Note",
                validationContentMissing: "Please enter note content.",
                validationDateMissing: "Please select a date.",
                validationTaskMissing: "Please select an associated task.",
                saving: "Saving...",

                // Page Header
                backToDashboard: "← Back to Dashboard",
                pageTitle: "Notes Tool",
                pageSubtitle: "A calm, dedicated space to keep your daily reflections and academic task notes organized.",

                // Page Create Notes Section
                sectionCreateNotes: "Create Notes",
                pageDateHelper: "Defaults to today's local date. You can select another date if needed.",
                pageContentPlaceholderDay: "Write reflections, reminders, or general observations for the day...",

                // Day Notes Section
                headingDayNotes: "Day Notes",
                groupedByDate: "Grouped by date",
                emptyDayNotesTitle: "No day notes yet.",
                emptyDayNotesDesc: "Track thoughts, energy levels, or gentle reflections for any day.",
                addDayNoteBtn: "+ Add a Day Note",

                // Task Notes Section
                headingTaskNotes: "Task Notes",
                attachedToTasks: "Attached to tasks",
                badgeTaskNote: "TASK NOTE",
                noteForTask: "Note for {taskName}",
                viewDetails: "View details →",
                clickToExpand: "Click to expand",
                emptyTaskNotesTitle: "No task notes yet.",
                emptyTaskNotesDesc: "Attach specific research notes, formulas, or steps to your working plan tasks.",
                addTaskNoteBtn: "+ Add a Task Note",

                // Detail and Edit Modals
                fullContent: "Full Content",
                editNote: "Edit Note",
                saveChanges: "Save Changes",
                delete: "Delete",
                close: "Close"
            }"""

vi_target_crlf = vi_target.replace('\n', '\r\n')
vi_replacement_crlf = vi_replacement.replace('\n', '\r\n')
en_target_crlf = en_target.replace('\n', '\r\n')
en_replacement_crlf = en_replacement.replace('\n', '\r\n')

assert vi_target_crlf in content, "vi_target_crlf not found!"
assert en_target_crlf in content, "en_target_crlf not found!"

content = content.replace(vi_target_crlf, vi_replacement_crlf, 1)
content = content.replace(en_target_crlf, en_replacement_crlf, 1)

lone_lfs = content.count('\n') - content.count('\r\n')
assert lone_lfs == 0, f"Found {lone_lfs} lone LFs!"

with open('i18n.js', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print(f"Updated i18n.js successfully! CRLF lines: {content.count(chr(10))}")
