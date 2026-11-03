/**
 * TEMPO WELLBEING — CENTRALIZED LOCALIZATION SYSTEM (VIETNAMESE-FIRST)
 * File: i18n.js
 *
 * Core Principles:
 * 1. Default locale is Vietnamese ('vi'). Secondary locale is English ('en').
 * 2. Precedence on first visit / anonymous: saved preference -> 'vi' (Never defaults to browser locale).
 * 3. Centralized t("namespace.key", params, fallback) conceptual API.
 * 4. Internal identifiers (mode IDs, plan_types, status enums, DB fields, storage keys) are NEVER translated.
 * 5. Parameterized interpolation: t("modes.urgent.completedOf", { completed: 1, total: 3 })
 * 6. Dynamic locale-aware date & time formatting.
 * 7. Safe fallback on missing keys (returns secondary language or fallback text, never undefined/null).
 */

(function() {
    'use strict';

    const SUPPORTED_LANGS = ['vi', 'en'];
    const DEFAULT_LANG = 'vi';

    // -------------------------------------------------------------------------
    // TRANSLATION DICTIONARIES
    // -------------------------------------------------------------------------
    const DICTIONARY = {
        vi: {
            common: {
                appName: "Tempo",
                returnToDashboard: "Return to Dashboard",
                returnToDashboardWithArrow: "← Return to Dashboard",
                returnToDashboard: "Về Dashboard",
                returnToDashboardWithArrow: "← Về Dashboard",
                today: "Hôm nay",
                yesterday: "Hôm qua",
                tomorrow: "Ngày mai",
                minutes: "phút",
                hours: "giờ",
                minShort: "phút",
                hrShort: "giờ",
                completed: "Đã xong",
                now: "Đang làm",
                upNext: "Tiếp theo",
                doThis: "LÀM VIỆC NÀY",
                then: "SAU ĐÓ",
                later: "SAU NỮA",
                notStarted: "Chưa bắt đầu",
                inProgress: "Đang làm",
                save: "Lưu",
                skip: "Bỏ qua",
                cancel: "Hủy",
                edit: "Chỉnh sửa",
                delete: "Xóa",
                close: "Đóng",
                back: "Quay lại",
                continue: "Tiếp tục",
                done: "Xong",
                confirm: "Xác nhận",
                yes: "Có",
                no: "Không",
                all: "Tất cả",
                or: "hoặc",
                searchPlaceholder: "Tìm kiếm trên Tempo...",
                signIn: "Đăng nhập",
                register: "Đăng kí",
                signOut: "Đăng xuất",
                directMessages: "Tin nhắn trực tiếp",
                saved: "Đã lưu",
                myLibrary: "Thư viện của tôi",
                account: "Tài khoản",
                myData: "Dữ liệu của tôi",
                settings: "Cài đặt",
                loading: "Đang tải...",
                user: "Người dùng",
                notEstimated: "Chưa ước tính",
                date: "Ngày",
                time: "Giờ",
                from: "Từ",
                to: "Đến"
            },
            appearance: {
                sectionHeading: "GIAO DIỆN",
                title: "Màu nền",
                description: "Lựa chọn màu nền phù hợp với trải nghiệm Tempo của bạn.",
                preview: "Xem trước",
                apply: "Áp dụng",
                resetDefault: "Đặt lại mặc định",
                selected: "Đang chọn",
                activeLabel: "Đang dùng:",
                defaultBadge: "Mặc định",
                previewCardTitle: "Xem trước giao diện",
                previewCardBadge: "Mẫu",
                previewCardDesc: "Tông màu nền dịu mắt, giúp giảm căng thẳng và tăng khả năng tập trung.",
                previewSurfaceLabel: "Thẻ nội dung mẫu",
                previewSampleBtn: "Nút bấm mẫu",
                appliedToast: "Đã áp dụng màu nền mới.",
                resetToast: "Đã đặt lại màu nền mặc định (#EAEEE8)."
            },
            nav: {
                home: "Trang chủ",
                tempoPosts: "Tempo Posts",
                peerVolunteer: "Hỗ trợ tình nguyện",
                advisorDesk: "Bàn Cố vấn",
                sos: "SOS",
                language: "Ngôn ngữ",
                search: "Tìm kiếm",
                currentLang: "VI",
                about: "Giới thiệu",
                community: "Cộng đồng",
                check: "Check",
                test: "Test",
                assessment: "Test",
                selfCheck: "Check",
                plan: "Plan",
                tools: "Công cụ"
            },
            modes: {
                default: {
                    name: "Tempo",
                    greeting: "Chào {name} 👋",
                    greetingFallback: "Chào bạn 👋",
                    welcomeEyebrow: "Chào mừng đến với Tempo",
                    whatDoYouNeed: "Bạn cần gì ngay lúc này?",
                    explainCopy: "Bạn không cần tự tìm cách một mình. Hãy cho Tempo biết tình huống hiện tại, mình sẽ cùng bạn tìm bước tiếp theo.",
                    helpMeStart: "Giúp tôi tìm hướng bắt đầu",
                    takesLessOneMin: "Chưa đến 1 phút",
                    personalizedGuidance: "Hướng dẫn phù hợp với bạn",
                    fromCommunity: "Cộng đồng Tempo",
                    seeAll: "Xem tất cả",
                    viewAll: "Xem tất cả",
                    quickRelief: "Thư giãn",
                    focusNow: "Tập trung",
                    quickTools: "Công cụ nhanh",
                    quickToolsSubtitle: "Những công cụ đơn giản giúp bạn cảm thấy nhẹ nhõm hơn và bước qua ngày hôm nay.",
                    viewAllTools: "Xem tất cả công cụ",
                    focusZone: "Focus Zone",
                    focusZoneDesc: "Tập trung với các quãng nghỉ chủ động. Mặc định 45 phút tập trung / 15 phút nghỉ.",
                    breathing: "Bài tập thở",
                    breathingDesc: "Bài tập thở nhanh giúp làm dịu tâm trí.",
                    quickStressRelief: "Giảm căng thẳng nhanh",
                    quickStressReliefDesc: "Cảm thấy quá tải? Thử một hành động đơn giản để giảm bớt căng thẳng trong vài phút.",
                    selfCheck: "Tự kiểm tra",
                    selfCheckDesc: "Theo dõi các tín hiệu căng thẳng và thói quen thể chất, tinh thần của bạn.",
                    notSureSubtitle: "Chưa biết bắt đầu từ đâu? Hãy cho Tempo biết bạn đang cảm thấy thế nào.",
                    communityPreview: "Những chia sẻ thật từ các sinh viên khác.",
                    activeWork: "Công việc đang tiến hành",
                    completedWork: "Đã hoàn thành hôm nay",
                    noWorkToday: "Hôm nay chưa có việc nào",
                    lowDataGuest: "Tạo kế hoạch hoặc khám phá các công cụ hỗ trợ.",
                    yourDay: "Hôm nay của bạn",
                    todaysPlannedWork: "Công việc đã lên lịch hôm nay",
                    viewMyPlan: "Xem kế hoạch của tôi",
                    nothingPlannedToday: "Hôm nay chưa có lịch làm việc nào.",
                    nothingPlannedSubtitle: "Bạn không nhất thiết phải lấp đầy thời gian. Hãy bắt đầu với điều gì quan trọng nhất hôm nay.",
                    addTask: "+ Thêm task",
                    flexible: "Linh hoạt",
                    continue: "Tiếp tục",
                    focus: "Tập trung",
                    steps: "bước",
                    todayComplete: "Bạn đã hoàn thành xong kế hoạch của hôm nay.",
                    needDifferentSupport: "Bạn cần dạng hỗ trợ khác?",
                    chooseMode: "Chọn chế độ"
                },
                urgent: {
                    name: "Chế độ khẩn cấp",
                    shortName: "Khẩn cấp",
                    tagline: "Xử lý deadline gấp & giải tỏa áp lực tức thì",
                    welcomeHeading: "Chào {name}, cùng bắt đầu nhé?",
                    welcomeHeadingFallback: "Chào bạn, cùng bắt đầu nhé?",
                    createNotes: "Tạo Notes",
                    viewMyNotes: "Xem ghi chú",
                    createNoteForToday: "Tạo ghi chú cho hôm nay",
                    taskForNow: "VIỆC CẦN LÀM NGAY",
                    taskForNowDesc: "Mình xử lý việc gấp trước nhé. Từng bước nhỏ một sẽ ổn thôi.",
                    due: "Deadline:",
                    est: "Dự tính:",
                    actionSteps: "bước hành động",
                    focusOnTask: "Tập trung vào việc này →",
                    viewTask: "Xem task →",
                    planForToday: "Kế hoạch hôm nay",
                    planForTodayUpper: "KẾ HOẠCH HÔM NAY",
                    yourUrgentPlanUpper: "KẾ HOẠCH KHẨN CỦA BẠN",
                    completedOf: "{completed}/{total} đã hoàn thành",
                    viewPlan: "Xem kế hoạch →",
                    viewEditPlan: "Xem / Chỉnh sửa kế hoạch",
                    workingPlan: "Working Plan",
                    workingPlanTitle: "Working Plan",
                    workingPlanFull: "Kế hoạch làm việc của bạn",
                    editPlan: "Sửa plan",
                    quickRelief: "Thư giãn",
                    completed: "ĐÃ XONG",
                    completedBadge: "Đã xong",
                    now: "ĐANG LÀM",
                    upNext: "TIẾP THEO",
                    overwhelmed: "Cảm thấy quá tải?",
                    overwhelmedDesc: "Dành 2 phút thở sâu hoặc giải tỏa căng thẳng trước khi làm tiếp.",
                    quickStressRelief: "Giảm căng thẳng nhanh",
                    breathing: "Bài tập thở",
                    focusNow: "Tập trung",
                    transitionQuestion: "Mọi thứ đã đỡ gấp gáp hơn?",
                    changeMyMode: "Chuyển chế độ",
                    streakHeading: "Chuỗi Self-check 🔥",
                    skip: "Bỏ qua",
                    save: "Lưu",
                    checkinSummary: "Bạn đã check-in {completed}/{total} mục hôm nay.",
                    viewTodayCheckin: "Xem check-in hôm nay",
                    editTrackingSystem: "Sửa tracking",
                    editTracking: "Sửa tracking",
                    greeting: "Chào {name}, hôm nay bạn thế nào?",
                    dailyCheckinBadge: "CHECK-IN HẰNG NGÀY",
                    todaySelfCheckTitle: "Self-check cho hôm nay",
                    streakDays: "Chuỗi {count} ngày",
                    selectLevel: "Chọn mức độ:",
                    recentlyTitle: "Gần đây",
                    adjustTracking: "Chỉnh sửa tracking",
                    methodPercentage: "Mức trung bình",
                    methodScale: "Điểm trung bình",
                    methodQuantity: "Tổng lượng ghi nhận",
                    methodOptions: "Tỷ lệ lựa chọn",
                    methodYesNo: "Tỷ lệ phản hồi",
                    avgTensionLevel: "Mức căng thẳng trung bình",
                    nightsQualitySleep: "Số đêm ngủ ngon",
                    walkedFor: "Thời gian đi bộ",
                    loggedCount: "Số lần ghi nhận",
                    weeklyReportCountdown: "Báo cáo tuần sẽ sẵn sàng trong {days} ngày nữa.",
                    weeklyReportReadyToday: "Báo cáo tuần của bạn đã sẵn sàng hôm nay.",
                    fromCommunity: "Cộng đồng Tempo",
                    seeAll: "Xem tất cả",
                    viewAll: "Xem tất cả",
                    focusNowDesc: "Bắt đầu phiên tập trung tính giờ để bảo vệ đà làm việc.",
                    startFocus: "Bắt đầu tập trung →",
                    statePlanIncomplete: "Bạn vẫn đang thiết lập kế hoạch của mình.",
                    statePlanIncompleteDesc: "Bạn vẫn đang trong quá trình thiết lập kế hoạch.",
                    continueBuilding: "Tiếp tục tạo kế hoạch của tôi",
                    stateTodayComplete: "Bạn đã hoàn thành các task hôm nay.",
                    stateTodayCompleteDesc: "Nghỉ ngơi để nạp lại năng lượng nhé. Công việc ngày mai cứ để ngày mai.",
                    todaysWorkDone: "ĐÃ HOÀN THÀNH CÔNG VIỆC HÔM NAY",
                    allDoneTodayHeading: "Vậy là hôm nay bạn đã hoàn thành mọi việc! 🎉",
                    allDoneTodayDesc: "Bạn đã hoàn thành các công việc hôm nay. Bạn có muốn bắt đầu trước một chút cho ngày mai hay nghỉ ngơi tại đây?",
                    nextPlannedWorkLabel: "CÔNG VIỆC TIẾP THEO:",
                    tomorrow: "Ngày mai",
                    previewTomorrow: "Xem trước kế hoạch ngày mai →",
                    doTomorrowTask: "Bắt đầu công việc ngày mai →",
                    restForNow: "Tôi sẽ nghỉ ngơi lúc này",
                    restingDesc: "Đã xong mọi việc. Bạn xứng đáng được nghỉ ngơi. Cứ thư giãn nhé!",
                    backToOverview: "Quay lại tổng quan",
                    nextScheduledWork: "Công việc tiếp theo được lên lịch vào ngày mai.",
                    stateNoWork: "Hôm nay không có việc cần làm.",
                    stateNoWorkDesc: "Bạn có thể nghỉ ngơi, xem lại kế hoạch hoặc bắt đầu một phiên tập trung tự do.",
                    stateTimeEnded: "Đã hết thời gian theo kế hoạch.",
                    stateTimeEndedDesc: "Bạn đã nỗ lực rất nhiều hôm nay. Những việc còn lại có thể điều chỉnh sang ngày mai.",
                    statePlanStale: "Kế hoạch của bạn cần được cập nhật.",
                    statePlanStaleDesc: "Một số task đã quá thời gian dự kiến. Hãy cập nhật lại lịch trình để tiếp tục nhé.",
                    updateSchedule: "Cập nhật lịch trình",
                    taskOverdue: "TASK TRỄ DEADLINE",
                    thisTaskIsOverdue: "Task này đã trễ Deadline",
                    taskOverdueDesc: "Task này đã trễ deadline. Bạn muốn xóa, đánh dấu hoàn thành hay cập nhật lại?",
                    overdueBadge: "TRỄ DEADLINE",
                    scheduledLabel: "Ngày lên lịch:",
                    deadlineLabel: "Deadline:",
                    clearThisTask: "Xóa task này",
                    markAsDone: "Hoàn thành",
                    editTask: "Chỉnh sửa task",
                    statePlanComplete: "Kế hoạch Khẩn của bạn đã hoàn thành.",
                    statePlanCompleteDesc: "Tất cả các việc trong kế hoạch đã xong. Hãy tự thưởng cho bản thân một khoảng nghỉ nhé.",
                    shiftToRecovery: "Chuyển sang Chế độ Hồi phục",
                    stayInUrgent: "Ở lại Chế độ khẩn cấp",
                    taskCompletedToast: "Đã hoàn thành task! Từng bước nhỏ giúp giữ vững đà làm việc.",
                    realityCheck: {
                        backToHome: "Về trang chủ",
                        reset: "Thư giãn",
                        organize: "Sắp xếp",
                        plan: "Lên kế hoạch",
                        ready: "Sẵn sàng",
                        sosSupport: "Hỗ trợ SOS",
                        urgentMode: "Chế độ Khẩn cấp",
                        realityCheck: "Trút bỏ suy nghĩ",
                        subtitle: "Đưa mọi điều đang khiến bạn bận tâm ra khỏi đầu.",
                        description: "Liệt kê những việc bạn cần hoàn thành. Tempo sẽ giúp bạn sắp xếp chúng.",
                        inputLabel: "Bạn cần hoàn thành những việc gì?",
                        inputPlaceholder: "VD: Báo cáo Marketing, Bài tập Thống kê, Đọc chương 4...",
                        deadline: "Deadline",
                        noFixedDeadline: "Chưa có deadline",
                        addTask: "+ Thêm task",
                        loadSamples: "+ Thêm 3 task mẫu",
                        addedTasks: "Task đã thêm",
                        emptyState: "Chưa có task nào. Hãy nhập những task cần làm ở phía trên nhé.",
                        backToReset: "← Quay lại Thư giãn",
                        iveAddedEverything: "Tôi đã thêm tất cả",
                        due: "Deadline",
                        edit: "Sửa",
                        remove: "Xóa",
                        taskName: "Tên task",
                        cancel: "Hủy",
                        save: "Lưu"
                    },
                    prioritize: {
                        backToRealityCheck: "← Quay lại Trút bỏ suy nghĩ",
                        previousTask: "← Task trước",
                        badge: "ƯU TIÊN & ƯỚC LƯỢNG",
                        title: "Hãy xác định những việc cần được ưu tiên trước.",
                        subtitle: "Chúng ta sẽ xem xét từng task một.",
                        taskProgress: "Task {current}/{total}",
                        evaluated: "Đã đánh giá {percent}%",
                        currentTask: "TASK HIỆN TẠI",
                        deadlinePassed: "Đã quá Deadline",
                        editDeadline: "Sửa Deadline",
                        q1Title: "1. TASK NÀY QUAN TRỌNG NHƯ THẾ NÀO?",
                        importance: {
                            high: "Cao",
                            medium: "Trung bình",
                            low: "Thấp"
                        },
                        q2Title: "2. ĐIỀU GÌ XẢY RA NẾU TASK BỊ TRỄ HOẶC CHƯA HOÀN THÀNH?",
                        consequences: {
                            big: "Hậu quả nghiêm trọng",
                            some: "Có một số hậu quả",
                            notMuch: "Không đáng kể",
                            notSure: "Không chắc"
                        },
                        q3Title: "3. CÓ ĐIỀU GÌ Ở TASK NÀY CÓ THỂ THAY ĐỔI ĐƯỢC KHÔNG?",
                        selectAllApply: "CHỌN TẤT CẢ ĐÁP ÁN PHÙ HỢP",
                        flexibility: {
                            reduce: "Giảm bớt khối lượng việc cần làm",
                            help: "Nhờ người khác hỗ trợ",
                            move: "Dời / thương lượng lại Deadline",
                            probablyNot: "Hầu như không thể thay đổi",
                            notSure: "Không chắc"
                        },
                        q4Title: "4. Bạn nghĩ mình sẽ cần bao nhiêu thời gian?",
                        q4Subtitle: "Chỉ cần ước lượng gần đúng. Bạn có thể điều chỉnh sau.",
                        saveAndNext: "Lưu & task tiếp theo →",
                        reviewCategories: "Xem các nhóm ưu tiên →"
                    },
                    priorityReview: {
                        backToAssessment: "← Quay lại phần đánh giá",
                        badge: "XEM LẠI MỨC ĐỘ ƯU TIÊN",
                        title: "Cách sắp xếp được đề xuất",
                        subtitle: "Đây là cách Tempo phân nhóm các task dựa trên câu trả lời của bạn. Bạn có thể thay đổi nhóm nếu cảm thấy chưa phù hợp.",
                        categoryLabel: "PHÂN LOẠI:",
                        editDeadline: "Sửa Deadline",
                        noTasks: "Chưa có task nào trong nhóm này.",
                        taskCount: "{count} task",
                        categories: {
                            doFirst: {
                                label: "LÀM TRƯỚC",
                                desc: "Áp lực cấp bách và có ảnh hưởng lớn. Cần được ưu tiên ngay."
                            },
                            plan: {
                                label: "LÊN KẾ HOẠCH",
                                desc: "Công việc quan trọng. Hãy dành thời gian cụ thể để hoàn thành trước Deadline."
                            },
                            reduceHelp: {
                                label: "GIẢM BỚT / NHỜ HỖ TRỢ",
                                desc: "Phạm vi việc có thể thu gọn, đơn giản hóa hoặc nhờ người khác hỗ trợ."
                            },
                            later: {
                                label: "LÀM SAU",
                                desc: "Ít cấp bách hơn ở thời điểm này. Có thể xử lý an tâm sau khi vượt qua giai đoạn cao điểm."
                            }
                        },
                        continueBtn: "Tiếp tục đến Thời gian làm việc →"
                    },
                    availableTime: {
                        backToPriorityReview: "← Quay lại phần phân loại ưu tiên",
                        badge: "THỜI GIAN CÓ THỂ SẮP XẾP",
                        title: "Bạn thực sự có thể dành thời gian làm việc khi nào?",
                        subtitle: "Cho Tempo biết thời gian bạn có thể làm việc. Chúng tôi sẽ xây dựng kế hoạch dựa trên lịch trình của bạn — không phải ngược lại.",
                        shortcuts: "Thao tác nhanh",
                        shortcutsColon: "Thao tác nhanh:",
                        freeRestOfToday: "Rảnh trong thời gian còn lại hôm nay",
                        copyTodayToTomorrow: "Sao chép lịch hôm nay sang ngày mai",
                        today: "HÔM NAY",
                        tomorrow: "NGÀY MAI",
                        total: "tổng thời gian",
                        markNotAvailable: "Đánh dấu ngày không thể làm việc",
                        removeDay: "Xóa ngày",
                        removeDayTooltip: "Xóa ngày này khỏi khung thời gian lập kế hoạch",
                        from: "Từ",
                        to: "đến",
                        addAnotherBlock: "+ Thêm khung giờ khác",
                        addAnotherDay: "+ Thêm ngày khác",
                        addAvailabilityFor: "Thêm thời gian làm việc cho ngày",
                        selectDate: "Chọn ngày:",
                        cancel: "Hủy",
                        addDay: "Thêm ngày",
                        totalAvailableTime: "Tổng thời gian có thể làm việc:",
                        estimatedWorkload: "Ước lượng thời lượng task:",
                        notAvailableBadge: "KHÔNG THỂ LÀM VIỆC",
                        dayUnavailableDesc: "Bạn đã đánh dấu ngày này không thể làm việc. Tempo sẽ không sắp xếp task vào ngày này.",
                        addAvailabilityForDay: "+ Thêm thời gian làm việc cho ngày này",
                        allUnavailableTitle: "Bạn chưa thêm thời gian làm việc nào.",
                        allUnavailableDesc: "Hãy thêm ít nhất một khung giờ để Tempo có thể sắp xếp các task hiệu quả.",
                        resetDefaultAvailability: "Khôi phục thời gian mặc định",
                        overlaps: "Trùng giờ",
                        overlapsTooltip: "Thời gian trùng nhau sẽ được tự động gộp",
                        removeDayTitle: "Xóa ngày này?",
                        continueBtn: "Kiểm tra tính khả thi & Tạo kế hoạch →"
                    },
                    workingPlan: {
                        backToAvailability: "← Quay lại phần thời gian có thể sắp xếp",
                        backToPlanOverview: "← Quay lại tổng quan kế hoạch",
                        badge: "WORKING PLAN",
                        title: "Working Plan của bạn",
                        subtitle: "Đây là kế hoạch gợi ý dựa trên thông tin bạn cung cấp. Bạn có thể sắp xếp lại thứ tự, chuyển task giữa các ngày hoặc điều chỉnh thời lượng bất cứ lúc nào.",
                        today: "HÔM NAY",
                        tomorrow: "NGÀY MAI",
                        availabilityConflict: "Xung đột thời gian",
                        conflictMessageToday: "Các task được lên lịch hôm nay vượt quá tổng thời gian bạn có thể dành ra.",
                        conflictMessageDay: "Các task được lên lịch {day} vượt quá tổng thời gian bạn có thể dành ra.",
                        upNext: "TIẾP THEO",
                        then: "SAU ĐÓ",
                        doLater: "LÀM SAU",
                        doThisTaskLater: "Để task này làm sau",
                        estimate: "Thời lượng dự kiến",
                        estimateColon: "Thời lượng dự kiến:",
                        editEstimate: "Sửa thời lượng",
                        deadline: "Deadline",
                        deadlineColon: "Deadline:",
                        editDeadline: "Sửa Deadline",
                        cadence: "Nhịp làm việc",
                        focus: "tập trung",
                        breakWord: "nghỉ ngơi",
                        recovery: "hồi phục",
                        recoverySeparator: "{duration} hồi phục",
                        flexibleUntimed: "Linh hoạt / Chưa xếp giờ",
                        scheduledBeyondBlocks: "Đã lên lịch (Vượt quá khung giờ)",
                        flexible: "Linh hoạt",
                        unallocatedTitle: "{count} task cần thêm thời gian làm việc",
                        unallocatedDesc: "Chúng tôi đã ưu tiên sắp xếp những việc vừa với khung giờ. Các việc sau vẫn cần thêm thời gian: <strong>{tasks}</strong>.",
                        addMoreAvailability: "+ Thêm thời gian làm việc để xếp hết các task",
                        unarrangedTitle: "Tasks chưa xếp lịch ({count})",
                        unarrangedDesc: "Các task này chưa được ấn định khung giờ cụ thể. Bạn có thể xếp lịch cho chúng bất cứ lúc nào.",
                        scheduleTask: "Xếp lịch task",
                        emptyPlan: "Không có task nào trong kế hoạch. Hãy quay lại phần Trút bỏ suy nghĩ để thêm task.",
                        planUpdatedTitle: "Kế hoạch đã được cập nhật và lưu",
                        planUpdatedDesc: "Mọi thay đổi bạn thực hiện đều được tự động lưu lại.",
                        returnToPlanOverview: "Quay lại Tổng quan Kế hoạch →",
                        startFocusZone: "Bắt đầu Focus Zone →",
                        confirmWorkableTitle: "Bạn thấy kế hoạch này đã ổn chưa?",
                        confirmWorkableDesc: "Bạn có thể điều chỉnh lại bất cứ lúc nào trong quá trình làm việc.",
                        useThisPlan: "Sử dụng kế hoạch này →",
                        taskOrderConflict: "Thứ tự này cần nhiều thời gian hơn quỹ thời gian hiện có của bạn trong ngày này.",
                        deadlineRiskTitle: "Rủi ro Deadline:",
                        deadlineRiskDesc: "Với thứ tự này, {name} có Deadline vào {deadline} và có thể hoàn thành sau Deadline.",
                        keepMyOrder: "Giữ nguyên thứ tự của tôi"
                    }
                },
                recovery: {
                    name: "Chế độ Hồi phục",
                    shortName: "Hồi phục",
                    tagline: "Nghỉ ngơi, lấy lại năng lượng và thiết lập nhịp điệu bền vững",
                    introBanner: "Bạn đang ở Chế độ Hồi phục. Hãy giảm nhịp độ, lắng nghe bản thân và tái tạo năng lượng.",
                    dismissBanner: "Đã hiểu",
                    selfCheck: "TỰ KIỂM TRA",
                    selfCheckTitle: "Tự kiểm tra",
                    selfCheckDesc: "Theo dõi những gì bạn muốn quan sát.",
                    setupSelfCheck: "Thiết lập Tự kiểm tra",
                    setupMySelfCheck: "Thiết lập Tự kiểm tra của tôi",
                    checkInToday: "Điểm danh hôm nay",
                    viewToday: "Xem lại hôm nay",
                    manageSelfCheck: "Quản lý Tự kiểm tra",
                    streakCount: "{count} ngày liên tiếp",
                    streakHelp: "Duy trì thói quen để nhận diện nhịp điệu của bạn.",
                    signsOfStress: "Dấu hiệu căng thẳng",
                    supportiveHabits: "Thói quen hỗ trợ",
                    generalHabits: "Chung",
                    recoveryNote: "LỜI NHẮN PHỤC HỒI",
                    noticeModalHeader: "LỜI NHẮN PHỤC HỒI",
                    noticeModalTitle: "Lời nhắn dành cho tôi",
                    noticeModalSubtitle: "Những điều bạn muốn nhắc nhở bản thân khi mọi thứ trở nên khó khăn.",
                    noticeModalEditBtn: "Chỉnh sửa lời nhắn",
                    noticeModalCloseBtn: "Đóng",
                    noteTitle: "Lời nhắc nhở cho bản thân",
                    noteEmptyTitle: "Lưu lại những điều hữu ích khi cảm thấy quá tải",
                    noteEmptyDesc: "Nếu nhận thấy điều gì giúp bạn cảm thấy nhẹ nhàng hơn, hãy lưu lại đây để đọc khi cần.",
                    addNoteItem: "+ Thêm điều bạn muốn nhớ",
                    viewNote: "Xem Ghi chú hồi phục",
                    editNote: "Chỉnh sửa",
                    itemsSaved: "{count} điều đã lưu",
                    recently: "GẦN ĐÂY",
                    recentlyEmpty: "Chưa có dữ liệu nào.",
                    recentlyEmptyDesc: "Khi bạn bắt đầu điểm danh, không gian này sẽ giúp bạn nhìn lại những quan sát theo thời gian.",
                    recentlyJustStarted: "Bạn mới chỉ bắt đầu.",
                    recentlyJustStartedDesc: "Chưa đủ lịch sử để so sánh. Hãy tiếp tục điểm danh theo nhịp độ của riêng bạn nhé.",
                    nothingNeedsRecorded: "Không cần ghi nhận điều gì nếu bạn chưa sẵn sàng.",
                    viewHistory: "Xem lịch sử →",
                    somethingToNotice: "ĐIỀU ĐÁNG CHÚ Ý",
                    youWantedToRemember: "BẠN TỪNG MUỐN NHỚ ĐIỀU NÀY",
                    remindMeLater: "Nhắc tôi sau",
                    dismiss: "Bỏ qua",
                    weeklyReview: "NHÌN LẠI TUẦN",
                    weeklyReviewReady: "Bản nhìn lại tuần đã sẵn sàng.",
                    startWeeklyReview: "Bắt đầu nhìn lại tuần →",
                    todaySection: "Hôm nay",
                    nothingPlannedToday: "Không có việc gì lên lịch hôm nay",
                    nothingPlannedDesc: "Tận hưởng ngày nghỉ này hoặc làm những điều bạn yêu thích.",
                    recoveryTools: "Công cụ phục hồi",
                    learnSolve: "Tìm hiểu & Tháo gỡ",
                    posts: "Tempo Posts",
                    workingPlan: "Working Plan",
                    workingPlanTitle: "Working Plan",
                    workingPlanFull: "Kế hoạch làm việc của bạn",
                    editPlan: "Sửa plan",
                    quickRelief: "Thư giãn",
                    focusNow: "Tập trung",
                    transitionQuestion: "Bạn đang cảm thấy quá tải hơn?",
                    changeMyMode: "Chuyển chế độ",
                    streakHeading: "Chuỗi Self-check 🔥",
                    skip: "Bỏ qua",
                    save: "Lưu",
                    checkinSummary: "Bạn đã check-in {completed}/{total} mục hôm nay.",
                    viewTodayCheckin: "Xem check-in hôm nay",
                    editTrackingSystem: "Sửa tracking",
                    editTracking: "Sửa tracking",
                    greeting: "Chào {name}, hôm nay bạn thế nào?",
                    dailyCheckinBadge: "CHECK-IN HẰNG NGÀY",
                    todaySelfCheckTitle: "Self-check cho hôm nay",
                    streakDays: "Chuỗi {count} ngày",
                    selectLevel: "Chọn mức độ:",
                    recentlyTitle: "Gần đây",
                    adjustTracking: "Chỉnh sửa tracking",
                    methodPercentage: "Mức trung bình",
                    methodScale: "Điểm trung bình",
                    methodQuantity: "Tổng lượng ghi nhận",
                    methodOptions: "Tỷ lệ lựa chọn",
                    methodYesNo: "Tỷ lệ phản hồi",
                    avgTensionLevel: "Mức căng thẳng trung bình",
                    nightsQualitySleep: "Số đêm ngủ ngon",
                    walkedFor: "Thời gian đi bộ",
                    loggedCount: "Số lần ghi nhận",
                    weeklyReportCountdown: "Báo cáo tuần sẽ sẵn sàng trong {days} ngày nữa.",
                    weeklyReportReadyToday: "Báo cáo tuần của bạn đã sẵn sàng hôm nay.",
                    fromCommunity: "Cộng đồng Tempo",
                    seeAll: "Xem tất cả",
                    viewAll: "Xem tất cả",
                    onboarding: {
                        badge: "CHẾ ĐỘ HỒI PHỤC",
                        badgeReturning: "CHẾ ĐỘ HỒI PHỤC · CHÀO MỪNG QUAY LẠI",
                        badgeReview: "CHẾ ĐỘ HỒI PHỤC · XEM LẠI HỆ THỐNG TRACKING",
                        case1Title: "Chào mừng bạn đến với Chế độ Hồi phục",
                        case1Purpose: "Dành cho bản thân không gian để xả hơi và phục hồi.",
                        case1Benefits: "Chế độ Hồi phục giúp bạn giảm bớt áp lực, nhận diện những điều hữu ích và tái tạo lại nhịp điệu sinh hoạt bền vững.",
                        case1Question: "Bạn đã sẵn sàng thiết lập Hệ thống tracking của mình chưa?",
                        case1QuestionSub: "Chọn một vài điều bạn muốn quan sát mỗi ngày. Bạn có thể thay đổi bất cứ lúc nào.",
                        case1Yes: "Có, hãy thiết lập ngay →",
                        case1Later: "Để sau",
                        case2Title: "Chào mừng bạn quay lại!",
                        case2Question: "Bạn có muốn xem lại Hệ thống tracking của mình không?",
                        case2Summary: "Bạn hiện có {count} mục đang tracking.",
                        case2SummaryEmpty: "Bạn hiện không có mục tracking nào. Lịch sử tracking trước đây được lưu trữ an toàn trong kho lưu trữ.",
                        case2TrackingStatus: "TRACKING HIỆN TẠI",
                        case2Yes: "Có, xem lại hệ thống →",
                        case2No: "Không, về Dashboard",
                        reviewTitle: "Hệ thống tracking của bạn",
                        reviewSubtitle: "Xem lại các mục tracking hiện tại của bạn bên dưới. Bạn có thể giữ nguyên hệ thống hoặc điều chỉnh từng mục.",
                        reviewActiveItems: "CÁC MỤC TRACKING HIỆN TẠI ({count})",
                        reviewNoActive: "Hiện chưa có mục tracking nào đang hoạt động.",
                        reviewHistoricalPreserved: "Lịch sử điểm danh và các mục đã lưu trữ vẫn được bảo toàn an toàn trong kho lưu trữ.",
                        optionATitle: "Giữ nguyên hệ thống",
                        optionADesc: "Giữ nguyên tất cả các mục tracking và cấu hình hiện có. Không ghi đè hay đặt lại lịch sử. Tiếp tục vào Tự kiểm tra.",
                        optionABtn: "Giữ nguyên hệ thống",
                        optionBTitle: "Điều chỉnh hệ thống",
                        optionBDesc: "Giữ hoặc bỏ bớt mục, thay đổi cách tracking hoặc thêm mục mới. Dữ liệu lịch sử của các mục không đổi được giữ nguyên an toàn.",
                        optionBBtn: "Điều chỉnh hệ thống",
                        backToDashboard: "Quay lại Dashboard",
                        back: "← Quay lại",
                        toastKeepSuccess: "Đã giữ nguyên hệ thống tracking.",
                        toastSaveSuccess: "Đã lưu thay đổi hệ thống tracking.",
                        adjustStep1Badge: "BƯỚC 1/3 · HỆ THỐNG TRACKING",
                        adjustStep1Tag: "Thiết lập điều chỉnh",
                        adjustStep1Title: "Điều chỉnh các mục tracking",
                        adjustStep1Desc: "Chọn các mục bạn muốn giữ lại, thay đổi cách tracking hoặc ngừng tracking. Các mục đã ngừng sẽ được lưu trữ và dữ liệu trước đó vẫn được giữ nguyên.",
                        adjustActiveBadge: "Đang tracking",
                        adjustEditBtn: "Chỉnh sửa",
                        adjustStopBtn: "Ngừng tracking",
                        adjustKeepBtn: "Tiếp tục tracking",
                        adjustAddBtn: "+ Thêm mục tracking mới",
                        adjustBackBtn: "← Quay lại Dashboard",
                        adjustContinueBtn: "Tiếp tục đến Lời nhắn phục hồi →"
                    }
                },
                unclear: {
                    name: "Chế độ Chưa rõ",
                    shortName: "Chưa rõ",
                    tagline: "Làm rõ cảm xúc, gỡ rối suy nghĩ từng bước",
                    subtitle: "Khi mọi thứ dường như quá nhiều và bạn chưa biết bắt đầu từ đâu.",
                    stepOf: "Bước {step} trên {total}",
                    startClarifying: "Bắt đầu gỡ rối",
                    thingsAreClearer: "Mọi thứ đã rõ ràng hơn một chút rồi.",
                    thingsAreClearerDesc: "Dưới đây là những gì bạn vừa chia sẻ. Hãy chọn hướng đi phù hợp nhất với bạn lúc này.",
                    goToUrgent: "Đến Chế độ khẩn cấp",
                    goToRecovery: "Đến Chế độ Hồi phục",
                    returnToTempo: "Trở về Tempo",
                    exploreSupport: "Tìm kiếm sự hỗ trợ",
                    stayUnclear: "Ở lại Chế độ Chưa rõ lúc này",
                    whatOnMind: "Điều gì đang quanh quẩn trong tâm trí bạn?",
                    whatHeaviest: "Điều gì đang tạo áp lực lớn nhất lúc này?",
                    whatNoticed: "Bạn nhận thấy cơ thể hoặc tâm trạng mình gần đây thế nào?",
                    whatNeedNow: "Lúc này bạn cần gì nhất?",
                    landing: {
                        greeting: "Xin chào {name},",
                        heading1: "Bạn chưa biết nên bắt đầu từ đâu?",
                        heading2: "Hãy cùng tìm hiểu nhé.",
                        subtitle: "Hãy thực hiện một vài câu hỏi ngắn để tìm hiểu điều bạn đang cần.",
                        doTempoTest: "Làm bài đánh giá Tempo",
                        viewMyResults: "Xem kết quả của tôi",
                        exploreHeading: "Khám phá các bài đánh giá sức khỏe tinh thần",
                        depressionAssessments: "Đánh giá mức độ trầm cảm",
                        stressAssessments: "Đánh giá mức độ căng thẳng",
                        anxietyAssessments: "Đánh giá mức độ lo âu",
                        otherAssessments: "Các bài đánh giá khác",
                        backToDashboard: "Quay lại Dashboard"
                    }
                },
                selector: {
                    switchMode: "Chuyển chế độ",
                    activeBadge: "Đang bật"
                }
            },
            workspace: {
                title: "Không gian Kế hoạch",
                returnHome: "← Về trang chủ",
                returnHomeText: "Về trang chủ",
                addTask: "Thêm task",
                addAvailability: "Thêm thời gian làm việc",
                adjustPlan: "Điều chỉnh plan",
                deletePlan: "Xóa plan",
                deleteMyPlan: "Xóa plan",
                taskProgress: "{completed}/{total} task",
                taskUnit: "task",
                tomorrow: "Ngày mai",
                completed: "Đã hoàn thành",
                deadline: "Deadline",
                deadlinePrefix: "Deadline:",
                noDeadline: "Chưa có deadline",
                subtasks: "subtask",
                doNow: "Làm ngay",
                done: "Hoàn thành",
                editDeadline: "Sửa deadline",
                breakDownTask: "+ Chia nhỏ task",
                addNote: "+ Thêm ghi chú",
                markAsDone: "Hoàn thành",
                focusNow: "Làm task",
                reschedule: "Đổi lịch",
                clearThisTask: "Xóa task này",
                availability: "Thời gian làm việc",
                addAvailability: "Thêm thời gian làm việc",
                addAvailabilityBtn: "+ Thêm thời gian làm việc",
                copyToTomorrow: "Sao chép sang ngày mai",
                repeatWeekly: "Lặp lại hàng tuần",
                repeatEveryWeek: "Lặp lại mỗi tuần",
                startDate: "Ngày bắt đầu",
                endDate: "Ngày kết thúc (không bắt buộc)",
                confirm: "Xác nhận",
                cancel: "Hủy",
                copiedSuccessfully: "Đã sao chép thời gian làm việc thành công.",
                noWorkingHours: "Không có thời gian làm việc để sao chép.",
                adjustPlanStep1: "BƯỚC 1/3 · ĐIỀU CHỈNH PLAN",
                chooseTasksToKeep: "Chọn các task muốn giữ lại",
                chooseTasksToKeepDesc: "Chọn những task bạn vẫn cần hoàn thành. Bạn có thể giữ lại hoặc loại bỏ các task đã quá hạn hoặc hoàn thành.",
                cancelAdjustment: "Hủy điều chỉnh",
                nextAdjustAddTasks: "Tiếp theo: Điều chỉnh & thêm task →",
                adjustPlanStep2: "BƯỚC 2/3 · ĐIỀU CHỈNH PLAN",
                adjustEstimatesAndAddTasks: "Điều chỉnh thời lượng & thêm task mới",
                retainedTasksCount: "CÁC TASK ĐƯỢC GIỮ LẠI ({count}):",
                duePrefixLabel: "Deadline:",
                addNewTaskUpper: "+ THÊM TASK MỚI:",
                taskNamePlaceholderEllipsis: "Tên task...",
                addPlain: "Thêm",
                datePlaceholderStep2: "dd/mm/yyyy",
                adjustPlanStep3: "BƯỚC 3/3 · XÁC NHẬN PLAN MỚI",
                proposedUpdatedPlan: "Plan mới được đề xuất",
                adjustPlanStep3Desc: "Đây là kế hoạch làm việc đã được điều chỉnh. Kế hoạch ban đầu sẽ được giữ nguyên cho đến khi bạn xác nhận và lưu thay đổi.",
                doThisFirstUpper: "LÀM ĐẦU TIÊN",
                upNextUpper: "TIẾP THEO",
                noFixedDeadlineStep3: "Chưa có deadline cố định",
                saveUpdatedPlan: "Lưu Plan mới →",
                planConfirmedAndSavedUpper: "PLAN ĐÃ ĐƯỢC XÁC NHẬN & LƯU",
                yourTaskForNow: "Task tiếp theo của bạn",
                doThisFirstPriority: "ƯU TIÊN LÀM TRƯỚC",
                dueNoFixedDeadline: "Deadline: Chưa có deadline",
                dueWithDeadlinePrefix: "Deadline:",
                breakDownQuestion: "Bạn có muốn chia nhỏ task này thành các bước dễ thực hiện hơn không?",
                breakDownDesc: "Chia task lớn thành những bước nhỏ từ 10–15 phút giúp bạn dễ bắt đầu hơn và tránh cảm giác quá tải.",
                noStartWorking: "Không, bắt đầu làm",
                breakDownTaskBtn: "Chia nhỏ task →",
                readyToWorkUpper: "SẴN SÀNG BẮT ĐẦU",
                startWorkingOnPlanTitle: "Bắt đầu làm việc nhé?",
                startWorkingOnPlanDesc: "Kế hoạch làm việc của bạn đã sẵn sàng. Bạn muốn bắt đầu với task đầu tiên ngay bây giờ không?",
                firstTaskPrefix: "Task đầu tiên:",
                laterBtn: "Để sau",
                breakMoreTasksBtn: "Chia nhỏ thêm task",
                yesStartWorkingBtn: "Có, bắt đầu thôi →",
                firstTaskExecutionUpper: "BẮT ĐẦU TASK ĐẦU TIÊN",
                yourFirstTaskIs: "Task đầu tiên của bạn là…",
                readyNowBadge: "SẴN SÀNG THỰC HIỆN",
                chooseAnotherTaskBtn: "Chọn task khác",
                doThisTaskBtn: "Bắt đầu task này →",
                taskSelectionUpper: "CHỌN TASK",
                selectTaskToWorkOn: "Chọn task bạn muốn thực hiện",
                selectTaskWithArrow: "Chọn →",
                breakdownEmptyState: "Chưa có bước thực hiện nào. Hãy thêm bước đầu tiên bên dưới hoặc chọn ✨ AI hỗ trợ.",
                workingPlanActiveBadge: "PLAN ĐANG HOẠT ĐỘNG",
                workingPlanActiveBody: "Bạn đã có một plan đang hoạt động. Hãy dành 2 phút tập thở để lấy lại sự tập trung, hoặc xem lại và tiếp tục kế hoạch hiện tại của bạn.",
                groundedStartBadge: "KHỞI ĐẦU ĐIỀM TĨNH",
                groundedStartTitle: "Dành một chút thời gian để lấy lại bình tĩnh?",
                groundedStartBody: "Những tình huống khẩn cấp sẽ nhẹ nhàng hơn rất nhiều khi bạn tạm dừng lại một chút. Bạn có muốn dành 2 phút tập thở để làm dịu thần kinh trước khi sắp xếp các task không?",
                buildMyPlanBtn: "Lên plan của tôi",
                groundedCheckpointBadge: "ĐIỂM DỪNG ĐIỀM TĨNH",
                areYouReadyTitle: "Bạn đã sẵn sàng chưa?",
                areYouReadyBody: "Bạn vừa dành thời gian để thở và lấy lại bình tĩnh. Bạn cảm thấy thế nào về việc bắt đầu với Kế hoạch Làm việc bây giờ?",
                areYouReadySub: "Nếu bạn vẫn cảm thấy quá tải, bạn có thể quay lại nghỉ ngơi thêm bất cứ lúc nào.",
                notYetReturnResetBtn: "Chưa, quay lại tập thở",
                yesImReadyBtn: "Có, tôi đã sẵn sàng →",
                planUpdateNeededBadge: "PLAN CẦN ĐƯỢC CẬP NHẬT",
                reviewAndResetWorkingPlanTitle: "Xem lại và điều chỉnh plan của bạn",
                planUpdateNeededBody: "Bạn có một số task đã quá deadline cần được xem lại. Hãy dành chút thời gian để lấy lại bình tĩnh, hoặc xem lại các task và điều chỉnh lịch trình của mình nhé.",
                boxBreathingFeature: "Tập thở trong 2 phút",
                groundsFocusFeature: "Giúp bạn lấy lại sự tập trung",
                noRushFeature: "Không cần vội",
                reviewYourPlanBtn: "Xem lại plan",
                yesTakeQuickResetBtn: "Có, tôi muốn lấy lại bình tĩnh một chút →",
                workingPlanReviewBadge: "XEM LẠI PLAN",
                workingPlanSummaryTitle: "Tổng quan kế hoạch làm việc",
                tasksOverdueCount: "{count} task đã quá hạn:",
                overdueWarningDesc: "Một số task đã quá ngày lên lịch hoặc deadline. Bạn có thể giữ lại hoặc điều chỉnh lịch trình.",
                badgeOverdue: "QUÁ HẠN",
                badgeUpNext: "TIẾP THEO",
                badgeThen: "SAU ĐÓ",
                badgeLater: "ĐỂ SAU",
                noFixedDeadlineLabel: "Chưa có deadline",
                adjustMyPlanBtn: "Điều chỉnh plan",
                keepThePlanBtn: "Giữ nguyên plan →",
                yourTaskForNowBadge: "TASK HIỆN TẠI CỦA BẠN",
                yourTaskForNowHeading: "Task bạn nên thực hiện lúc này là…",
                focusNowBtn: "Tập trung ngay →",
                nextProposePlan: "Tiếp theo: Đề xuất plan →",
                saveAvailability: "Lưu thời gian làm việc",
                dateLabel: "Ngày",
                startTimeLabel: "Thời gian bắt đầu",
                endTimeLabel: "Thời gian kết thúc",
                cancelAction: "Hủy",
                errorFillAllAvailabilityFields: "Vui lòng nhập đầy đủ ngày, thời gian bắt đầu và thời gian kết thúc.",
                errorEndTimeAfterStartTime: "Thời gian kết thúc phải sau thời gian bắt đầu.",
                errorPastAvailabilityDate: "Không thể thêm thời gian làm việc cho ngày đã qua.",
                errorPastAvailabilityTime: "Không thể thêm thời gian làm việc trong quá khứ.",
                errorOverlapAvailability: "Khung giờ này bị trùng lặp với thời gian làm việc đã có ({start} – {end}).",
                errorConflictScheduledTask: "Khung giờ này trùng với task đã lên lịch: \"{name}\" ({start} – {end}).",
                priorityNow: "Làm ngay",
                priorityLater: "Để sau",
                priorityDone: "Hoàn thành",
                priorityOverdue: "Trễ Deadline",
                priorityOverdueUpper: "TRỄ DEADLINE",
                scheduledDateLabel: "Ngày lên lịch",
                dueDateLabel: "Deadline",
                duePrefix: "Deadline:",
                subtasksLabel: "Subtasks",
                notesLabel: "Ghi chú",
                notePrefix: "Ghi chú:",
                markAsDone: "Hoàn thành",
                markAsActive: "Đang thực hiện",
                focusNowAction: "Làm ngay",
                rescheduleAction: "Đổi lịch",
                clearThisTaskAction: "Xóa task này",
                missedSchedule: "Task quá lịch",
                missedScheduleUpper: "TASK QUÁ LỊCH",
                deadlineConflict: "Trùng Deadline",
                stepBreakdown: "Chia nhỏ task",
                stepBreakdownUpper: "CHIA NHỎ TASK",
                noteEditor: "Chỉnh sửa ghi chú",
                clearTaskConfirmation: "Xác nhận gỡ task",
                deadlineReorder: "Sắp xếp lại Deadline",
                home: "Trang chủ",
                returnToHome: "Trở về Trang chủ",
                focus: "Tập trung",
                startFocus: "Bắt đầu tập trung",
                timeline: "Lịch trình thực hiện",
                unscheduled: "Chưa lên lịch",
                notScheduledYet: "CHƯA LÊN LỊCH",
                addTask: "Thêm task",
                taskDetails: "Chi tiết task",
                scheduledFor: "Đã lên lịch:",
                deadline: "Deadline:",
                editDeadline: "Sửa deadline",
                noDeadline: "Chưa có deadline",
                duration: "Thời lượng:",
                editEstimate: "Sửa thời lượng",
                actionSteps: "Các bước hành động",
                addSubtask: "+ Thêm bước nhỏ",
                subtaskPlaceholder: "Nhập bước hành động nhỏ tiếp theo...",
                markCompleted: "Đánh dấu hoàn thành",
                markIncomplete: "Đánh dấu chưa xong",
                deleteTask: "Xóa task",
                doThis: "LÀM VIỆC NÀY",
                then: "SAU ĐÓ",
                later: "SAU NỮA",
                noPlanTitle: "Không tìm thấy Kế hoạch Khẩn đang hoạt động",
                noPlanDesc: "Hiện tại bạn chưa có Kế hoạch Khẩn nào đang hoạt động. Hãy tạo kế hoạch để nhận được chỉ dẫn rõ ràng, thực tế.",
                createUrgentPlan: "Tạo Kế hoạch Khẩn →",
                headerSubtitle: "Đây là những việc bạn đang xử lý lúc này.",
                durationSummary: "~{duration} thời gian tập trung{unestimated}",
                unestimatedCount: " (+{count} chưa ước tính)",
                tasksCount: "{count} task",
                completedCount: "đã hoàn thành",
                startFocusNow: "Bắt đầu tập trung ngay",
                adjustAvailability: "Điều chỉnh thời gian làm việc",
                allPlannedWorkDone: "Đã xong tất cả việc đã lên lịch ✓",
                activeTasksCount: "{count} task đang làm",
                estimate: "Dự tính:",
                due: "Deadline:",
                mayFinishAfterDeadline: "Có thể hoàn thành sau deadline",
                completed: "Đã hoàn thành",
                inProgress: "Đang làm",
                notStarted: "Chưa bắt đầu",
                start: "Bắt đầu",
                continueFocus: "Tiếp tục tập trung",
                addAnotherTask: "+ Thêm task khác vào kế hoạch này",
                allActiveScheduled: "Tất cả task đã được xếp vào lịch của bạn.",
                scheduleTask: "Xếp lịch task →",
                undo: "Hoàn tác",
                editTask: "Chỉnh sửa task",
                scheduledUpper: "LỊCH THỰC HIỆN",
                reschedule: "Đổi lịch",
                deadlineUpper: "DEADLINE",
                noFixedDeadline: "Chưa có deadline",
                saveDeadline: "Lưu deadline",
                estimateUpper: "DỰ TÍNH",
                flexibleFocusedWork: "Thời gian tập trung linh hoạt",
                actionStepsUpper: "CÁC BƯỚC HÀNH ĐỘNG",
                addNextStep: "Thêm bước tiếp theo...",
                add: "+ Thêm",
                startFocusOnTask: "▶ Bắt đầu tập trung vào việc này",
                removeFromPlan: "Xóa khỏi kế hoạch",
                addTaskModalTitle: "Thêm task",
                taskName: "Tên task",
                taskNamePlaceholder: "VD: Đọc tài liệu tham khảo",
                focusedEstimate: "Dự tính thời gian tập trung",
                notSureYet: "Chưa chắc chắn",
                addTaskBtn: "Thêm task",
                taskAdded: "Đã thêm task",
                taskReadyDesc: "\"{name}\" đã sẵn sàng.",
                fitIntoPlan: "Xếp vào kế hoạch của tôi",
                leaveUnscheduled: "Để chưa lên lịch lúc này",
                rescheduleTaskModalTitle: "Đổi lịch",
                yourAvailableTime: "THỜI GIAN LÀM VIỆC CỦA BẠN",
                noTimeBlocks: "Chưa có khung giờ nào",
                figureOutLater: "Để sau (Chuyển sang chưa lên lịch)",
                schedule: "Lên lịch",
                yourAvailableTimeTitle: "Thời gian làm việc của bạn",
                addTimeWindow: "+ THÊM KHUNG GIỜ LÀM VIỆC",
                addWindowBtn: "Thêm khung giờ làm việc"
            },
            sos: {
                title: "SOS · Hỗ trợ khẩn cấp",
                subtitle: "An toàn của bạn là ưu tiên hàng đầu",
                pillSupport: "Nhận hỗ trợ ngay →",
                safetyBannerHeading: "Chế độ an toàn đang bật",
                safetyBannerDesc: "Bạn không cần phải trải qua điều này một mình. Hãy để chúng tôi giúp bạn.",
                eyebrow: "SOS · Hỗ trợ khẩn cấp",
                mainHeading: "Tôi không cảm thấy an toàn lúc này",
                situationIntro: "Nếu ngay lúc này bạn đang:",
                situation1: "Hoảng loạn và cảm thấy mất kiểm soát",
                situation2: "Có suy nghĩ hoặc thôi thúc làm tổn thương bản thân",
                situation3: "Cảm thấy không an toàn khi ở một mình",
                reassuranceTitle: "An toàn của bạn là ưu tiên hàng đầu.",
                reassuranceBody: "Bạn không cần phải tự mình vượt qua tất cả.",
                getSupportNow: "Nhận hỗ trợ ngay →",
                altOptionsHeading: "Hoặc chọn điều bạn cần lúc này",
                optionABadge: "Lựa chọn A",
                optionATitle: "Lựa chọn A · Quá tải hoặc hoảng loạn",
                optionADesc: "Tôi cảm thấy căng thẳng, quá tải hoặc không thể suy nghĩ rõ ràng.",
                optionBBadge: "Lựa chọn B",
                optionBTitle: "Lựa chọn B · Khủng hoảng cảm xúc",
                optionBDesc: "Tôi đang trải qua trạng thái cảm xúc rất tiêu cực và cần được hỗ trợ ngay.",
                optionCBadge: "Lựa chọn C",
                optionCTitle: "Lựa chọn C · Cần hỗ trợ khẩn cấp",
                optionCDesc: "Tôi đang nghĩ đến việc làm tổn thương bản thân hoặc tự tử.",
                optionDLabel: "Tôi không chắc — đầu óc tôi đang rối bời và tôi chỉ muốn được giúp bình tĩnh lại.",
                drawerTitle: "Nhận hỗ trợ ngay",
                drawerSubtitle: "Nếu bạn cảm thấy không an toàn, đừng ở một mình.",
                drawerSubtitleDesc: "Hãy ở cùng người bạn tin cậy và tìm kiếm sự hỗ trợ ngay bây giờ.",
                medicalTitle: "Hỗ trợ Y tế Khẩn cấp",
                medicalBadge: "Khẩn cấp",
                medicalDesc: "Nếu bạn có nguy cơ tự làm hại bản thân ngay lập tức hoặc đang trong tình huống nguy hiểm.",
                medicalCall: "Gọi 115 ngay",
                hotlineTitle: "Đường dây nóng Khủng hoảng & Hỗ trợ Tâm lý HOPE",
                hotlineBadge: "Hỗ trợ khủng hoảng",
                hotlineDesc: "Nếu bạn đang trong cơn khủng hoảng, có suy nghĩ tự hại hoặc cần người lắng nghe ngay bây giờ.",
                hotlineCall: "Gọi 0865 044 400",
                ngayMaiTitle: "ĐƯỜNG DÂY NÓNG NGÀY MAI",
                ngayMaiBadge: "Hỗ trợ tâm lý",
                ngayMaiPhone: "096 306 1414",
                ngayMaiDesc: "Hỗ trợ tâm lý miễn phí qua điện thoại cho người đang gặp khủng hoảng tâm lý, trầm cảm và người thân của họ. Lắng nghe không phán xét, bảo mật thông tin.",
                ngayMaiHours: "13:00 – 20:30, Thứ Tư – Chủ Nhật",
                ngayMaiCall: "Gọi 096 306 1414",
                waitingHeader: "KHI BẠN ĐANG CHỜ ĐƯỢC HỖ TRỢ",
                action1: "Ở cùng một người bạn tin tưởng.",
                action2: "Di chuyển đến một nơi an toàn hơn.",
                action3: "Tạo khoảng cách với những vật có thể gây tổn thương cho bạn.",
                waitingReassTitle: "Bạn không cần giải quyết mọi thứ ngay lúc này.",
                reassurance: "Lúc này, chỉ cần tập trung giữ an toàn cho bản thân.",
                trustedTitle: "Liên hệ với người bạn tin tưởng",
                trustedDesc: "Bạn có thể sao chép tin nhắn này để gửi cho bạn bè hoặc người thân:",
                trustedQuote: "Chào bạn, mình đang trải qua một khoảng thời gian rất khó khăn và cảm thấy quá tải. Bạn có thể trò chuyện hoặc ngồi cùng mình một lúc được không?",
                copyTrustedBtn: "Sao chép tin nhắn",
                campusTitle: "HỖ TRỢ SỨC KHỎE TINH THẦN SINH VIÊN",
                campusBadge: "Hỗ trợ trong giờ làm việc",
                campusDesc: "Trong trường hợp khẩn cấp hoặc nguy hiểm tức thời, hãy gọi 115 hoặc 0865 044 400. Nếu bạn cần trao đổi về các vấn đề tâm lý không khẩn cấp, bạn có thể liên hệ với bộ phận hỗ trợ sinh viên trong giờ làm việc.",
                fptTitle: "Phòng Tư vấn tâm lý – Đại học FPT",
                fptDesc: "Dịch vụ tư vấn tâm lý miễn phí và bảo mật dành cho sinh viên Đại học FPT.",
                fptEmail: "tuvansinhvien@fpt.edu.vn",
                fptCta: "Gửi email tư vấn",
                offlineContactPlaceholder: "Họ tên hoặc email sinh viên (không bắt buộc)",
                offlineMsgPlaceholder: "Mô tả vấn đề hoặc nội dung bạn muốn gửi đến phòng tư vấn",
                offlineSubmitBtn: "Gửi tin nhắn cho bộ phận hỗ trợ",
                offlineSuccessMsg: "Tin nhắn đã được lưu. Bộ phận hỗ trợ sẽ phản hồi trong giờ làm việc. Nếu cần giúp đỡ ngay lập tức, hãy gọi 115 hoặc 0865 044 400.",
                closeSOS: "Đóng cửa sổ hỗ trợ",
                copySuccessToast: "Đã sao chép tin nhắn! Bạn có thể dán và gửi cho bạn bè hoặc người thân."
            },
            tools: {
                focusZone: "Focus Zone",
                focusZoneDesc: "Không gian làm việc tập trung, không phân tâm.",
                quickStressRelief: "Giảm căng thẳng nhanh",
                quickStressReliefDesc: "Các bài tập ngắn 2-3 phút giúp hạ nhiệt hệ thần kinh.",
                boxBreathing: "Bài tập thở",
                boxBreathingDesc: "Kỹ thuật thở 4-4-4-4 giúp lấy lại bình tĩnh nhanh chóng.",
                tempoBreak: "Tạm nghỉ",
                tempoBreakDesc: "Tạm dừng công việc một lúc để nạp lại năng lượng."
            },
            community: {
                title: "Cộng đồng Tempo",
                returnToDashboard: "Quay lại Dashboard",
                returnToDashboardWithArrow: "← Quay lại Dashboard",
                tabs: {
                    announcement: "Thông báo",
                    tips: "Tips",
                    learn: "Kiến thức",
                    posts: "Bài viết",
                    messages: "Tin nhắn riêng"
                },
                tips: {
                    searchPlaceholder: "Tìm kiếm...",
                    usage: "Cách sử dụng:",
                    seeMore: "Xem thêm →",
                    seeMoreLabel: "Xem thêm",
                    noSolutionsFound: "Không tìm thấy giải pháp phù hợp",
                    tryDifferentTerms: "Hãy thử tìm kiếm bằng các từ khóa khác.",
                    resetSearch: "Đặt lại tìm kiếm",
                    items: {
                        deadline_pileup: {
                            title: "Quy tắc bắt đầu 5 phút khi deadline khiến bạn tê liệt",
                            usage: "Thử áp dụng khi bạn có quá nhiều việc phải làm đến mức không biết bắt đầu từ đâu."
                        },
                        presentation_dread: {
                            title: "Lo lắng khi thuyết trình",
                            usage: "Áp dụng khi bạn sắp có một buổi thuyết trình và cảm thấy lo lắng về điều đó."
                        },
                        brain_fog_reset: {
                            title: "Xua tan sương mù tinh thần và lấy lại đà tập trung",
                            usage: "Thử áp dụng khi sự mệt mỏi về tinh thần khiến bạn khó tập trung và ngay cả những việc đơn giản cũng trở nên khó khăn."
                        },
                        exam_panic_surge: {
                            title: "Giảm hoảng loạn trước kỳ thi bằng kỹ thuật thở dài sinh lý",
                            usage: "Áp dụng khi bạn đột nhiên cảm thấy hoảng loạn ngay trước hoặc trong một bài kiểm tra quan trọng."
                        },
                        email_paralysis: {
                            title: "Mẫu email xin gia hạn deadline với giảng viên",
                            usage: "Sử dụng khi bạn đang chịu áp lực lớn và cần xin gia hạn deadline bài tập một cách khẩn cấp."
                        },
                        sleep_runaway: {
                            title: "Thư giãn khi những suy nghĩ cứ tiếp diễn vào ban đêm",
                            usage: "Thử áp dụng khi những lo lắng về học tập khiến bạn trằn trọc và không thể ngủ dù đã qua 2 giờ sáng."
                        },
                        falling_behind: {
                            title: "Cảm thấy bị tụt lại phía sau trong học tập",
                            usage: "Khi bạn gặp khó khăn trong việc theo kịp bài giảng, tài liệu đọc bắt buộc hoặc các bài thực hành."
                        },
                        teamwork: {
                            title: "Khó khăn khi làm việc nhóm",
                            usage: "Khi khối lượng công việc không được phân chia đồng đều, thành viên nhóm thiếu phản hồi hoặc giao tiếp gặp nhiều trở ngại."
                        },
                        teamwork_problems: {
                            title: "Khó khăn khi làm việc nhóm",
                            usage: "Khi khối lượng công việc không được phân chia đồng đều, thành viên nhóm thiếu phản hồi hoặc giao tiếp gặp nhiều trở ngại."
                        },
                        grades: {
                            title: "Kết quả học tập không như mong đợi",
                            usage: "Khi bạn cảm thấy thất vọng về kết quả học tập và cần tìm ra những bước tiếp theo mang tính xây dựng."
                        },
                        grades_disappointment: {
                            title: "Kết quả học tập không như mong đợi",
                            usage: "Khi bạn cảm thấy thất vọng về kết quả học tập và cần tìm ra những bước tiếp theo mang tính xây dựng."
                        },
                        presentation_anxiety: {
                            title: "Lo lắng khi thuyết trình",
                            usage: "Cảm giác hồi hộp tột độ, tim đập nhanh hoặc lo sợ trước khi phát biểu trước lớp hoặc thuyết trình."
                        },
                        cant_focus: {
                            title: "Không thể tập trung / khó bắt đầu",
                            usage: "Nhìn vào màn hình trống rỗng, cảm giác sương mù tinh thần hoặc bị tê liệt khi cố gắng bắt đầu học tập."
                        },
                        future_uncertainty: {
                            title: "Mơ hồ về định hướng / tương lai",
                            usage: "Lo lắng về lựa chọn nghề nghiệp, chọn ngành hoặc cảm thấy mất phương hướng so với bạn bè đồng trang lứa."
                        },
                        not_good_enough: {
                            title: "Cảm giác \"mình chưa đủ tốt\"",
                            usage: "Tự nghi ngờ bản thân kéo dài, hội chứng kẻ mạo danh và cảm thấy mọi người xung quanh đều hiểu bài trừ mình."
                        },
                        expectations_pressure: {
                            title: "Áp lực từ kỳ vọng của bản thân",
                            usage: "Chủ nghĩa hoàn hảo, tiêu chuẩn nội tâm khắt khe và nỗi sợ mắc lỗi trong quá trình học tập."
                        },
                        comparing_others: {
                            title: "So sánh bản thân với người khác",
                            usage: "Cảm thấy kém cỏi khi nhìn vào kỳ thực tập, tiến độ học tập hoặc thành tích xã hội của bạn bè."
                        },
                        too_many_responsibilities: {
                            title: "Quá nhiều trách nhiệm cùng một lúc",
                            usage: "Bị quá tải với việc học, công việc làm thêm, câu lạc bộ và các trách nhiệm gia đình diễn ra cùng lúc."
                        },
                        relationship_conflict: {
                            title: "Xung đột với người quan trọng",
                            usage: "Mâu thuẫn với bạn cùng phòng, người yêu, bạn bè hoặc người thân ảnh hưởng đến khả năng học tập của bạn."
                        },
                        loneliness: {
                            title: "Cô đơn / cảm giác mất kết nối",
                            usage: "Cảm thấy bị cô lập trong trường học, thiếu cảm giác thuộc về nơi này hoặc không có ai để tâm sự trong những tuần khó khăn."
                        },
                        disrupted_routine: {
                            title: "Lối sống hằng ngày bị xáo trộn kéo dài",
                            usage: "Lịch ngủ bị đảo lộn, ăn uống thất thường và các thói quen hằng ngày bị xói mòn bởi căng thẳng liên miên."
                        }
                    }
                }
            },
                learn: {
                    searchPlaceholder: "Tìm kiếm...",
                    seeMore: "Xem thêm →",
                    seeMoreLabel: "Xem thêm",
                    noTopicsFound: "Không tìm thấy chủ đề kiến thức nào",
                    tryDifferentTerms: "Hãy thử tìm kiếm với từ khóa khác hoặc đặt lại tìm kiếm.",
                    resetSearch: "Đặt lại tìm kiếm",
                    cards: {
                        what_is_stress: {
                            title: "Stress là gì?",
                            summary: "Căng thẳng là trạng thái lo lắng hoặc áp lực tinh thần xuất phát từ một tình huống khó khăn. Đây là phản ứng tự nhiên của con người, giúp chúng ta đối mặt với những thử thách và mối đe dọa trong cuộc sống. Mỗi người đều trải qua căng thẳng ở một mức độ nhất định."
                        },
                        stress_eating: {
                            title: "Ăn uống do căng thẳng",
                            summary: "Ăn uống do căng thẳng, hay còn gọi là ăn uống theo cảm xúc, là việc sử dụng thức ăn để cải thiện cảm xúc hoặc khiến bản thân cảm thấy dễ chịu hơn, thay vì đáp ứng nhu cầu đói về mặt thể chất."
                        },
                        stress_loop: {
                            title: "Vòng lặp căng thẳng ở sinh viên",
                            summary: "Cách những deadline dồn dập kích hoạt trạng thái tê liệt tinh thần, tạo ra các vòng lặp né tránh làm tăng thêm mức độ căng thẳng."
                        }
                    }
                },
            posts: {
                title: "Tempo Posts",
                returnToDashboard: "Quay lại Dashboard",
                returnToDashboardWithArrow: "← Quay lại Dashboard",
                subtitle: "Những chia sẻ thật từ các sinh viên đang cùng nỗ lực như bạn.",
                like: "Thích",
                relate: "Đồng cảm",
                support: "Ủng hộ",
                comment: "Bình luận",
                commentsCount: "{count} bình luận",
                save: "Lưu",
                saved: "Đã lưu",
                share: "Chia sẻ",
                seeAllPosts: "Xem tất cả bài viết →",
                writeComment: "Viết bình luận động viên...",
                filterLatest: "Mới nhất",
                filterPopular: "Nổi bật",
                newPost: "Đăng bài mới",
                searchPlaceholder: "Tìm kiếm...",
                yourPosts: "Bài viết của tôi",
                notifications: "Thông báo",
                savedPosts: "Bài viết đã lưu",
                replyPlaceholder: "Trả lời...",
                postSubmit: "Gửi"
            },
            auth: {
                regHeading: "TẠO TÀI KHOẢN TEMPO",
                regTitle: "Chào mừng đến với Tempo",
                regSubtitle: "Quản lý căng thẳng học tập, sắp xếp deadline và tìm lại nhịp điệu của bạn.",
                regNameLabel: 'Tên hiển thị <span class="text-rose-500">*</span>',
                regNamePlaceholder: "VD: Alex hoặc Nguyễn Yến Nhi",
                regEmailLabel: 'Email <span class="text-rose-500">*</span>',
                regEmailPlaceholder: "ban@example.com",
                regPasswordLabel: 'Mật khẩu <span class="text-rose-500">*</span>',
                regPasswordPlaceholder: "Tối thiểu 6 ký tự",
                regSubmitBtn: "Tạo tài khoản",
                regFooterText: 'Đã có tài khoản? <button type="button" onclick="window.TempoAuth.openSignInModal()" class="text-[#FF6B2C] font-bold hover:underline ml-1 cursor-pointer">Đăng nhập</button>',
                loginHeading: "CHÀO MỪNG TRỞ LẠI",
                loginTitle: "Chào mừng trở lại",
                loginSubtitle: "Đăng nhập vào tài khoản Tempo của bạn.",
                loginEmailLabel: "Email",
                loginPasswordLabel: "Mật khẩu",
                loginForgotLink: "Quên mật khẩu?",
                loginSubmitBtn: "Đăng nhập",
                loginFooterText: 'Chưa có tài khoản? <button type="button" onclick="window.TempoAuth.openRegisterModal()" class="text-[#FF6B2C] font-bold hover:underline ml-1 cursor-pointer">Tạo tài khoản</button>',
                forgotPrompt: "Nhập địa chỉ email đã đăng ký để nhận hướng dẫn đặt lại mật khẩu:",
                forgotSent: "Liên kết đặt lại mật khẩu đã được gửi đến email của bạn.",
                fillRequired: "Vui lòng điền đầy đủ các thông tin bắt buộc.",
                passTooShort: "Mật khẩu phải có ít nhất 6 ký tự."
            },
            footer: {
                descriptor: "Hỗ trợ áp lực học tập & deadline",
                disclaimer: "Hỗ trợ sức khỏe tinh thần bảo mật từ cộng đồng. Không thay thế dịch vụ cấp cứu hoặc chăm sóc tâm thần chuyên môn.",
                terms: "Điều khoản sử dụng",
                privacy: "Chính sách quyền riêng tư",
                sos: "SOS · Hỗ trợ khẩn cấp",
                copyright: "© 2026 Tempo"
            },
            routing: {
                eyebrow: "BƯỚC TIẾP THEO",
                title: "Điều gì phù hợp nhất với trạng thái hiện tại của bạn?",
                desc: "Mỗi tình huống cần một cách hỗ trợ khác nhau. Hãy chọn hướng phù hợp với bạn nhé.",
                urgent: {
                    badge: "CẦN XỬ LÝ NGAY",
                    title: "Deadline đang gấp",
                    desc: "Công việc cần được giải quyết ngay, nhưng căng thẳng khiến bạn khó tập trung, bắt đầu hoặc sắp xếp thứ tự ưu tiên.",
                    cta: "Vào chế độ khẩn cấp"
                },
                recovery: {
                    badge: "PHỤC HỒI & NẠP LẠI NĂNG LƯỢNG",
                    title: "Đang hồi phục sau căng thẳng",
                    desc: "Áp lực đã qua, nhưng bạn vẫn cảm thấy mệt mỏi, lo âu hoặc kiệt sức về tinh thần.",
                    cta: "Vào chế độ phục hồi"
                },
                unclear: {
                    badge: "CHƯA RÕ",
                    title: "Chưa biết mình đang gặp vấn đề gì",
                    desc: "Bạn cảm thấy không ổn nhưng chưa rõ nguyên nhân hoặc chưa biết mình cần gì lúc này.",
                    cta: "Tìm hiểu bản thân"
                },
                support: {
                    badge: "CẦN HỖ TRỢ NGAY",
                    title: "Bạn không cảm thấy an toàn",
                    desc: "Bạn đang hoảng loạn, mất kiểm soát, có ý nghĩ tự làm đau bản thân hoặc cảm thấy không an toàn khi ở một mình.",
                    cta: "Nhận hỗ trợ ngay"
                }
            },
            selfCheckWorkspace: {
                title: "Tempo Self-check",
                returnUrgent: "Quay lại Chế độ khẩn cấp",
                returnRecovery: "Quay lại Dashboard",
                returnUnclear: "Quay lại Chế độ mơ hồ",
                returnHome: "Quay lại trang chủ",
                returnUrgentWithArrow: "← Quay lại Chế độ khẩn cấp",
                returnRecoveryWithArrow: "← Quay lại Dashboard",
                dailyCheckinUpper: "CHECK-IN HẰNG NGÀY",
                todaysCheckin: "Check-in hôm nay",
                streakDays: "Chuỗi {count} ngày",
                sleepQuestion: "Bạn ngủ thế nào vào tối qua?",
                good: "Tốt",
                notGood: "Chưa tốt",
                walkQuestion: "Hôm nay bạn có đi bộ không?",
                yes: "Có",
                noIdidnt: "Không",
                createNoteForToday: "Tạo ghi chú hôm nay",
                checkedInCount: "Bạn đã check-in {completed}/{total} mục hôm nay.",
                yourTrackingSystem: "Các mục tracking của bạn",
                addTracking: "Thêm mục tracking",
                clearAll: "Xóa tất cả",
                adjust: "Chỉnh sửa",
                tension: "Căng thẳng",
                sleep: "Giấc ngủ",
                walk: "Đi bộ",
                avgTensionLevel: "Mức căng thẳng trung bình",
                methodPercentage: "Mức trung bình",
                methodScale: "Điểm trung bình",
                methodQuantity: "Tổng lượng ghi nhận",
                methodOptions: "Tỷ lệ lựa chọn",
                methodYesNo: "Tỷ lệ phản hồi",
                nightsQualitySleep: "Số đêm có giấc ngủ tốt",
                totalLoggedThisWeek: "Tổng ghi nhận tuần này",
                avgRating: "Đánh giá trung bình",
                viewMyFullCheck: "Xem full-check",
                yourFullCheck: "Full-check",
                monthlyOverview: "Tổng quan tháng",
                backToCalendar: "Quay lại lịch",
                currentMonthPill: "Tháng hiện tại",
                fullCheckMon: "T2",
                fullCheckTue: "T3",
                fullCheckWed: "T4",
                fullCheckThu: "T5",
                fullCheckFri: "T6",
                fullCheckSat: "T7",
                fullCheckSun: "CN",
                myWeeklyReport: "Báo cáo tuần của tôi",
                myRecoveryNotice: "Lời nhắn phục hồi",
                mon: "Thứ 2",
                tue: "Thứ 3",
                wed: "Thứ 4",
                thu: "Thứ 5",
                fri: "Thứ 6",
                sat: "Thứ 7",
                sun: "Chủ nhật",
                emptyTitle: "Chưa có mục theo dõi nào",
                emptyDesc: "Thêm mục theo dõi để bắt đầu ghi nhận check-in hằng ngày."
            },
            toolNotes: {
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
                viewTask: "Xem task",
                taskUnavailable: "Task này hiện không còn tồn tại.",
                emptyTaskNotesTitle: "Chưa có ghi chú công việc nào.",
                emptyTaskNotesDesc: "Liên kết ghi chú nghiên cứu, công thức hoặc các bước thực hiện với kế hoạch làm việc.",
                addTaskNoteBtn: "+ Thêm note theo task",

                // Detail and Edit Modals
                fullContent: "Nội dung đầy đủ",
                editNote: "Chỉnh sửa Ghi chú",
                saveChanges: "Lưu thay đổi",
                delete: "Xóa",
                close: "Đóng"
            },
            about: {
                // 1. Hero
                heroBadge: "GẶP GỠ TEMPO",
                heroTitle: "Không gian đồng hành cùng bạn trên hành trình sinh viên.",
                heroDesc: "Được thiết kế dành cho sinh viên Đại học FPT, Tempo mang đến sự hỗ trợ phù hợp với nhu cầu cá nhân, giúp bạn chăm sóc sức khỏe tinh thần và quản lý căng thẳng — từ việc vượt qua áp lực học tập hiện tại đến xây dựng nhận thức và kỹ năng hữu ích cho tương lai.",
                heroCta: "Khám phá Tempo",
                previewBadge: "TEMPO · KHÔNG GIAN SỨC KHỎE TINH THẦN FPT",
                card1Title: "Chế độ Khẩn cấp",
                card1Badge: "Hỗ trợ xử lý Deadline",
                card1Desc: "Chia nhỏ sự bế tắc thành MỘT bước khả thi.",
                card2Title: "Self-check",
                card2Badge: "6 khía cạnh",
                card2Desc: "Tự nhìn nhận bản thân nhẹ nhàng, không áp lực hay phán xét.",
                card3Title: "Luyện tập hít thở",
                card3Badge: "2 phút thư giãn",
                card3Desc: "Giúp cơ thể và tâm trí tạm dừng, thả lỏng.",
                previewFooter: "Luôn bảo mật và có sự đồng hành từ cộng đồng đồng trang lứa.",

                // 2. When Things Feel Like Too Much
                s02Eyebrow: "KHI MỌI THỨ TRỞ NÊN QUÁ SỨC",
                s02Title: "Khi mọi thứ trở nên quá sức",
                s02Desc: "Cuộc sống sinh viên đôi khi mang đến những thời điểm mọi thứ đều trở nên cấp bách, căng thẳng khó kiểm soát hoặc bạn không biết mình thực sự cần gì. Tempo mang đến sự hỗ trợ phù hợp với trạng thái hiện tại, đồng thời giúp bạn xây dựng nhận thức và kỹ năng cần thiết cho tương lai.",

                // Scenario 1
                s02C1Eyebrow: "KHI MỌI THỨ DỒN DẬP",
                s02C1Title: "Khi mọi thứ dồn dập, bạn không biết nên bắt đầu từ đâu?",
                s02C1Desc: "Khi Deadline và những trách nhiệm liên tục chồng chất, bạn có thể khó xác định điều gì cần được ưu tiên trước.",
                s02C1HelpEyebrow: "TEMPO GIÚP BẠN THẾ NÀO?",
                s02C1HelpTitle: "Tìm ra điều cần ưu tiên và bước tiếp theo.",
                s02C1HelpDesc: "Tempo giúp bạn xác định những việc cần được chú ý trước, sau đó chia nhỏ chúng thành các bước vừa sức để bạn có thể tiếp tục với tâm thế rõ ràng và chủ động hơn.",

                // Scenario 2
                s02C2Eyebrow: "KHI CĂNG THẲNG LẤN ÁT",
                s02C2Title: "Khi căng thẳng lấn át, bạn cần chậm lại một chút?",
                s02C2Desc: "Đôi khi áp lực khiến bạn khó suy nghĩ rõ ràng, khó tập trung hoặc không biết nên bắt đầu bước tiếp theo như thế nào.",
                s02C2HelpEyebrow: "TEMPO GIÚP BẠN THẾ NÀO?",
                s02C2HelpTitle: "Lấy lại cân bằng lúc này. Xây dựng kỹ năng cho tương lai.",
                s02C2HelpDesc: "Tempo mang đến những cách giúp bạn tạm dừng và giảm bớt căng thẳng trước mắt, đồng thời hỗ trợ bạn hiểu rõ hơn về trạng thái căng thẳng và phát triển những phương pháp quản lý phù hợp theo thời gian.",

                // Scenario 3
                s02C3Eyebrow: "KHI BẠN CHƯA BIẾT MÌNH CẦN GÌ",
                s02C3Title: "Khi chưa rõ mình đang cảm thấy thế nào hoặc nên bắt đầu từ đâu?",
                s02C3Desc: "Không phải lúc nào bạn cũng dễ dàng nhận ra trạng thái hiện tại của bản thân hay biết loại hỗ trợ nào sẽ thực sự hữu ích.",
                s02C3HelpEyebrow: "TEMPO GIÚP BẠN THẾ NÀO?",
                s02C3HelpTitle: "Hiểu bản thân trước, tìm kiếm sự hỗ trợ phù hợp sau.",
                s02C3HelpDesc: "Tempo giúp bạn nhìn nhận trạng thái hiện tại và khám phá hướng đi phù hợp khi bạn chưa biết phải làm gì tiếp theo.",

                // 3. Explore Tempo
                s03Eyebrow: "KHÁM PHÁ TEMPO",
                s03Title: "Một không gian, nhiều cách tìm lại nhịp độ của riêng bạn.",
                s03Desc: "Từ việc tìm kiếm sự hỗ trợ phù hợp đến xây dựng thói quen tích cực và kết nối với mọi người, hãy khám phá những cách khác nhau để đồng hành cùng cuộc sống sinh viên với Tempo.",

                // 3.1 Modes & SOS
                modesEyebrow: "CÁC CHẾ ĐỘ & SOS",
                modesTitle: "Tìm kiếm sự hỗ trợ bạn cần",
                modesSubtitle: "Mỗi tình huống đều cần một cách hỗ trợ khác nhau.",
                modesDesc: "Khám phá các chế độ của Tempo để tìm ra hướng đi phù hợp với nhu cầu hiện tại, hoặc truy cập SOS khi bạn cần một quy trình hỗ trợ riêng biệt.",
                modeUrgent: "Khẩn cấp",
                modeRecovery: "Hồi phục",
                modeUnclear: "Chưa rõ",
                sosTitle: "SOS – Hỗ trợ khẩn cấp",
                sosFlow: "Quy trình hỗ trợ riêng",
                sosNote: "Lưu ý: SOS là quy trình hỗ trợ riêng biệt, không phải một chế độ.",

                // 3.2 Personal Tools
                toolsEyebrow: "CÔNG CỤ CÁ NHÂN",
                toolsTitle: "Công cụ phù hợp với nhu cầu của bạn",
                toolsSubtitle: "Dành không gian cho sự tập trung, tự nhìn nhận và những tiến bộ mỗi ngày.",
                toolsDesc: "Sử dụng các công cụ của Tempo để sắp xếp công việc, check-in với bản thân, duy trì thói quen và theo dõi tiến trình theo nhịp độ phù hợp với bạn.",
                toolFocusZone: "Focus Zone",
                toolWorkingPlan: "Working Plan",
                toolSelfCheck: "Self-check",
                toolBreathing: "Hít thở",
                toolNotes: "Ghi chú",

                // 3.3 Quick Relief & Learning
                reliefEyebrow: "THƯ GIÃN & HỌC HỎI",
                reliefTitle: "Thư giãn, học hỏi và phát triển",
                reliefSubtitle: "Tạm dừng khi bạn cần. Học hỏi trên từng chặng đường.",
                reliefDesc: "Khám phá các hoạt động giúp bạn thư giãn ngay lúc này, cùng những tài nguyên giúp bạn hiểu hơn về căng thẳng và tìm ra cách ứng phó phù hợp.",
                reliefCard1Title: "Thư giãn",
                reliefCard1Desc: "Những hoạt động thư giãn thể chất và tinh thần chỉ trong 2 phút.",
                reliefCard2Title: "Learn & Solve",
                reliefCard2Desc: "Những phương pháp thiết thực giúp bạn ứng phó với áp lực đại học.",

                // 3.4 Community
                communityEyebrow: "CỘNG ĐỒNG",
                communityTitle: "Bạn không đơn độc",
                communitySubtitle: "Cuộc sống sinh viên sẽ trở nên dễ chia sẻ hơn khi chúng ta có thể kết nối và thấu hiểu trải nghiệm của nhau.",
                communityDesc: "Khám phá các bài viết từ cộng đồng Tempo, lắng nghe những góc nhìn khác nhau và chia sẻ trải nghiệm cùng các bạn sinh viên.",
                communityCard1Title: "Cộng đồng Tempo",
                communityCard1Desc: "Những câu chuyện chân thực, suy nghĩ chân thành và sự động viên từ cộng đồng sinh viên.",
                communityCard2Title: "Tempo Post",
                communityCard2Desc: "Tự do chia sẻ ẩn danh hoặc sử dụng hồ sơ sinh viên của bạn.",

                // 4. Your Journey, Your Pace
                s04Eyebrow: "HÀNH TRÌNH CỦA BẠN, NHỊP ĐIỆU CỦA RIÊNG BẠN",
                s04Title: "Sử dụng Tempo theo cách của bạn",
                s04Desc: "Không có một cách duy nhất để sử dụng Tempo. Hãy bắt đầu từ điều bạn cảm thấy cần thiết, khám phá những gì thực sự hữu ích và điều chỉnh bất cứ khi nào nhu cầu của bạn thay đổi.",
                step1Title: "01 — Bắt đầu từ chính bạn",
                step1Desc: "Chưa biết mình cần gì? Hãy dành một chút thời gian check-in với bản thân hoặc lựa chọn hình thức hỗ trợ phù hợp với tình huống hiện tại.",
                step2Title: "02 — Tìm ra điều phù hợp với bạn",
                step2Desc: "Khám phá các chế độ, công cụ cá nhân, hoạt động thư giãn nhanh và tài nguyên học hỏi của Tempo. Bạn không cần sử dụng tất cả — chỉ cần tập trung vào những gì phù hợp với mình.",
                step3Title: "03 — Tiến bước theo nhịp độ riêng",
                step3Desc: "Từng bước nhỏ một. Hãy quay lại với Tempo bất cứ khi nào bạn cần tạm dừng, nhìn nhận bản thân hoặc điều chỉnh kế hoạch khi cuộc sống thay đổi.",

                // 5. Final CTA
                s05Eyebrow: "TEMPO · CHƯƠNG TIẾP THEO CỦA BẠN",
                s05Title: "Sẵn sàng tìm lại nhịp điệu của riêng mình?",
                s05Desc: "Không có một cách duy nhất để vượt qua cuộc sống sinh viên. Hãy bắt đầu từ điều bạn cần hôm nay và tiến từng bước nhỏ một.",
                s05Cta: "Bắt đầu ngay"
            }
        },
        en: {
            selfCheckWorkspace: {
                title: "Tempo Self-check",
                returnUrgent: "Return to Urgent Mode",
                returnRecovery: "Return to Recovery Mode",
                returnUnclear: "Return to Unclear Mode",
                returnHome: "Return Home",
                returnUrgentWithArrow: "Return to Urgent Mode",
                returnRecoveryWithArrow: "Return to Recovery Mode",
                dailyCheckinUpper: "YOUR DAILY CHECK-IN",
                todaysCheckin: "Today's Check-in",
                streakDays: "{count}-day streak",
                sleepQuestion: "How was your sleep last night?",
                good: "Good",
                notGood: "Not good",
                walkQuestion: "Did you go for a walk today?",
                yes: "Yes",
                noIdidnt: "No, I didn't",
                createNoteForToday: "Create a note for today",
                checkedInCount: "You checked in on {completed} of {total} things.",
                yourTrackingSystem: "Your Tracking System",
                addTracking: "Add Tracking",
                clearAll: "Clear all",
                adjust: "Adjust",
                tension: "Tension",
                sleep: "Sleep",
                walk: "Walk",
                avgTensionLevel: "Your average tension level is",
                methodPercentage: "Average level",
                methodScale: "Average score",
                methodQuantity: "Total recorded",
                methodOptions: "Option distribution",
                methodYesNo: "Response distribution",
                nightsQualitySleep: "Nights of Quality Sleep",
                totalLoggedThisWeek: "Total logged this week",
                avgRating: "Average rating",
                viewMyFullCheck: "View my full check",
                yourFullCheck: "Your full check",
                monthlyOverview: "Monthly Overview",
                backToCalendar: "Back to calendar",
                currentMonthPill: "Current month",
                fullCheckMon: "Mon",
                fullCheckTue: "Tue",
                fullCheckWed: "Wed",
                fullCheckThu: "Thurs",
                fullCheckFri: "Fri",
                fullCheckSat: "Sat",
                fullCheckSun: "Sun",
                myWeeklyReport: "My weekly report",
                myRecoveryNotice: "My Recovery notice",
                mon: "Mon",
                tue: "Tue",
                wed: "Wed",
                thu: "Thu",
                fri: "Fri",
                sat: "Sat",
                sun: "Sun",
                emptyTitle: "No tracking items yet",
                emptyDesc: "Add a tracking item to start recording your daily check-ins."
            },
            common: {
                appName: "Tempo",
                today: "Today",
                yesterday: "Yesterday",
                tomorrow: "Tomorrow",
                minutes: "min",
                hours: "hr",
                minShort: "min",
                hrShort: "hr",
                completed: "Completed",
                now: "Now",
                upNext: "Up Next",
                doThis: "DO THIS",
                then: "THEN",
                later: "LATER",
                notStarted: "Not started",
                inProgress: "In progress",
                save: "Save",
                skip: "Skip",
                cancel: "Cancel",
                edit: "Edit",
                delete: "Delete",
                close: "Close",
                back: "Back",
                continue: "Continue",
                done: "Done",
                confirm: "Confirm",
                yes: "Yes",
                no: "No",
                all: "All",
                or: "or",
                searchPlaceholder: "Search Tempo...",
                signIn: "Sign In",
                register: "Register",
                signOut: "Sign out",
                directMessages: "Direct Messages",
                saved: "Saved",
                myLibrary: "My Library",
                account: "Account",
                myData: "My Data",
                settings: "Settings",
                loading: "Loading...",
                user: "User",
                notEstimated: "Not estimated",
                date: "Date",
                time: "Time",
                from: "From",
                to: "To"
            },
            appearance: {
                sectionHeading: "APPEARANCE",
                title: "Background Color",
                description: "Choose a background color for your Tempo experience.",
                preview: "Preview",
                apply: "Apply",
                resetDefault: "Reset to default",
                selected: "Selected",
                activeLabel: "Active:",
                defaultBadge: "Default",
                previewCardTitle: "Tempo Preview",
                previewCardBadge: "Sample",
                previewCardDesc: "Soft, calming background tones designed to reduce stress and improve focus.",
                previewSurfaceLabel: "Card Surface",
                previewSampleBtn: "Sample Button",
                appliedToast: "Background color applied successfully.",
                resetToast: "Reset to default background (#EAEEE8)."
            },
            nav: {
                home: "Home",
                tempoPosts: "Tempo Posts",
                peerVolunteer: "Peer Volunteer",
                advisorDesk: "Advisor Desk",
                sos: "SOS",
                language: "Language",
                search: "Search",
                currentLang: "EN",
                about: "About",
                community: "Community",
                check: "Check",
                test: "Test",
                assessment: "Assessment",
                selfCheck: "Check",
                plan: "Plan",
                tools: "Tools"
            },
            modes: {
                default: {
                    name: "Tempo",
                    greeting: "Hi, {name} 👋",
                    greetingFallback: "Hi there 👋",
                    welcomeEyebrow: "Welcome to Tempo",
                    whatDoYouNeed: "What do you need right now?",
                    explainCopy: "You don’t need to figure it out alone. Tell Tempo your current situation, and we’ll help you find the next step.",
                    helpMeStart: "Help me figure out where to start",
                    takesLessOneMin: "Takes less than 1 minute",
                    personalizedGuidance: "Personalized guidance",
                    fromCommunity: "From the Tempo Community",
                    seeAll: "View all",
                    viewAll: "View all",
                    quickRelief: "Quick Relief",
                    focusNow: "Focus Now",
                    quickTools: "Quick Tools",
                    quickToolsSubtitle: "Simple tools to help you feel better and get through your day.",
                    viewAllTools: "View all tools",
                    focusZone: "Focus Zone",
                    focusZoneDesc: "Focus with intentional breaks. Default 45 min focus / 15 min rest.",
                    breathing: "Breathing",
                    breathingDesc: "A quick breathing exercise to calm your mind.",
                    quickStressRelief: "Quick Stress Relief",
                    quickStressReliefDesc: "Feel overwhelmed? Try a simple action to ease stress in a few minutes.",
                    selfCheck: "Self-check",
                    selfCheckDesc: "Track your stress signals and wellbeing habits.",
                    notSureSubtitle: "Not sure where to start? Tell us how you're feeling and we'll guide you.",
                    communityPreview: "Real experiences from students like you.",
                    activeWork: "Active work",
                    completedWork: "Completed today",
                    noWorkToday: "No work scheduled for today",
                    lowDataGuest: "Create a plan or explore support tools.",
                    yourDay: "Your Day",
                    todaysPlannedWork: "Today's planned work",
                    viewMyPlan: "View my plan",
                    nothingPlannedToday: "Nothing planned for today.",
                    nothingPlannedSubtitle: "You don't need to fill the space. Start with whatever matters today.",
                    addTask: "+ Add a task",
                    flexible: "Flexible",
                    continue: "Continue",
                    focus: "Focus",
                    steps: "steps",
                    todayComplete: "You're done with what was planned for today.",
                    needDifferentSupport: "Need a different kind of support?",
                    chooseMode: "Choose mode"
                },
                urgent: {
                    name: "Urgent Mode",
                    shortName: "Urgent",
                    tagline: "Acute academic deadline triage & high-direction execution",
                    welcomeHeading: "Hi, {name}, ready to get things done?",
                    welcomeHeadingFallback: "Hi, ready to get things done?",
                    createNotes: "Create Notes",
                    viewMyNotes: "View my notes",
                    createNoteForToday: "Create a note for today",
                    taskForNow: "YOUR TASK FOR NOW",
                    taskForNowDesc: "Let's handle what's urgent first. You can do it one step at a time.",
                    due: "Deadline:",
                    est: "Est:",
                    actionSteps: "action steps",
                    focusOnTask: "Focus on this task →",
                    viewTask: "View task →",
                    planForToday: "Your plan for today",
                    planForTodayUpper: "YOUR PLAN FOR TODAY",
                    yourUrgentPlanUpper: "YOUR URGENT PLAN",
                    completedOf: "{completed} of {total} completed",
                    viewPlan: "View Plan →",
                    viewEditPlan: "View / Edit Plan",
                    workingPlan: "Working Plan",
                    workingPlanTitle: "Working Plan",
                    editPlan: "Edit Plan",
                    quickRelief: "Quick Relief",
                    completed: "COMPLETED",
                    completedBadge: "Completed",
                    now: "NOW",
                    upNext: "UP NEXT",
                    overwhelmed: "Feeling overwhelmed?",
                    overwhelmedDesc: "Take a few minutes to calm things down and clear your head.",
                    quickStressRelief: "Quick Stress Relief",
                    breathing: "Breathing",
                    focusNow: "Focus Now",
                    transitionQuestion: "Are things feeling less urgent now?",
                    changeMyMode: "Change my mode",
                    streakHeading: "Your Self-check Streak 🔥",
                    skip: "Skip",
                    save: "Save",
                    checkinSummary: "You checked in on {completed} of {total} things.",
                    viewTodayCheckin: "View today's checkin",
                    editTrackingSystem: "Edit tracking system",
                    fromCommunity: "From the Tempo Community",
                    seeAll: "View all",
                    viewAll: "View all",
                    focusNowDesc: "Launch a timed, distraction-free focus session.",
                    startFocus: "Start Focus →",
                    statePlanIncomplete: "You're still setting up your plan.",
                    statePlanIncompleteDesc: "You're still setting up your plan.",
                    continueBuilding: "Continue building my plan",
                    stateTodayComplete: "You're done for today.",
                    stateTodayCompleteDesc: "Rest up to protect your momentum. Tomorrow's work stays in tomorrow.",
                    todaysWorkDone: "TODAY'S WORK DONE",
                    allDoneTodayHeading: "You're all done for today! 🎉",
                    allDoneTodayDesc: "You've made it through today's tasks. Want to get a head start on tomorrow, or call it a day?",
                    nextPlannedWorkLabel: "NEXT PLANNED WORK:",
                    tomorrow: "Tomorrow",
                    previewTomorrow: "Preview tomorrow →",
                    doTomorrowTask: "Let's do tomorrow's task →",
                    restForNow: "I'll rest for now",
                    restingDesc: "All done. You've earned some rest. Take it easy!",
                    backToOverview: "Back to overview",
                    nextScheduledWork: "Next scheduled work tomorrow.",
                    stateNoWork: "Nothing planned for today.",
                    stateNoWorkDesc: "You can rest, review your plan, or start focus without a task.",
                    stateTimeEnded: "Time ended for today.",
                    stateTimeEndedDesc: "You've worked hard today. Remaining tasks can be adjusted for tomorrow.",
                    statePlanStale: "Your plan needs an update.",
                    statePlanStaleDesc: "Some scheduled tasks are overdue. Update your schedule to continue.",
                    updateSchedule: "Update schedule",
                    taskOverdue: "TASK OVERDUE",
                    thisTaskIsOverdue: "This task is overdue",
                    taskOverdueDesc: "Looks like this task has passed its due date. Would you like to clear it, mark it as done, or update it?",
                    overdueBadge: "OVERDUE",
                    scheduledLabel: "Scheduled:",
                    deadlineLabel: "Deadline:",
                    clearThisTask: "Clear this task",
                    markAsDone: "Mark as done",
                    editTask: "Edit task",
                    statePlanComplete: "Your Urgent Plan is complete.",
                    statePlanCompleteDesc: "All tasks in this urgent plan are finished. Great job pushing through.",
                    shiftToRecovery: "Shift to Recovery Mode",
                    stayInUrgent: "Stay in Urgent Mode",
                    taskCompletedToast: "Task completed! Taking small steps protects your momentum.",
                    realityCheck: {
                        backToHome: "Back to Home",
                        reset: "Reset",
                        organize: "Organize",
                        plan: "Plan",
                        ready: "Ready",
                        sosSupport: "SOS Support",
                        urgentMode: "Urgent Mode",
                        realityCheck: "Reality Check",
                        subtitle: "Get everything out of your head.",
                        description: "Add what you need to get done. We'll organize it next.",
                        inputLabel: "What do you need to get done?",
                        inputPlaceholder: "e.g. Marketing Report, Statistics Lab, Chapter 4 Reading...",
                        deadline: "Deadline",
                        noFixedDeadline: "No fixed deadline",
                        addTask: "+ Add task",
                        loadSamples: "+ Load 3 sample tasks",
                        addedTasks: "Added Tasks",
                        emptyState: "No tasks added yet. Enter your tasks above to get them out of your head.",
                        backToReset: "← Back to Reset",
                        iveAddedEverything: "I've added everything",
                        due: "Deadline",
                        edit: "Edit",
                        remove: "Remove",
                        taskName: "Task Name",
                        cancel: "Cancel",
                        save: "Save"
                    },
                    prioritize: {
                        backToRealityCheck: "← Back to Reality Check",
                        previousTask: "← Previous task",
                        badge: "PRIORITIZE & ESTIMATE",
                        title: "Let's figure out what needs your attention first.",
                        subtitle: "We'll look at one task at a time.",
                        taskProgress: "Task {current} of {total}",
                        evaluated: "{percent}% evaluated",
                        currentTask: "CURRENT TASK",
                        deadlinePassed: "Deadline passed",
                        editDeadline: "Edit deadline",
                        q1Title: "1. HOW IMPORTANT IS THIS TASK?",
                        importance: {
                            high: "High",
                            medium: "Medium",
                            low: "Low"
                        },
                        q2Title: "2. WHAT HAPPENS IF IT'S LATE OR UNFINISHED?",
                        consequences: {
                            big: "Big consequences",
                            some: "Some consequences",
                            notMuch: "Not much",
                            notSure: "Not sure"
                        },
                        q3Title: "3. CAN ANYTHING ABOUT THIS TASK CHANGE?",
                        selectAllApply: "SELECT ALL THAT APPLY",
                        flexibility: {
                            reduce: "Reduce what I need to do",
                            help: "Ask someone for help",
                            move: "Move / negotiate the deadline",
                            probablyNot: "Probably not",
                            notSure: "Not sure"
                        },
                        q4Title: "4. How long do you think you'll need?",
                        q4Subtitle: "A rough estimate is enough. You can adjust this later.",
                        saveAndNext: "Save & next task →",
                        reviewCategories: "Review Priority Categories →"
                    },
                    priorityReview: {
                        backToAssessment: "← Back to Assessment",
                        badge: "PRIORITY REVIEW",
                        title: "Suggested Organization",
                        subtitle: "Here is how Tempo grouped your tasks based on your answers. You can change any category if something feels off.",
                        categoryLabel: "CATEGORY:",
                        editDeadline: "Edit",
                        noTasks: "No tasks in this category.",
                        taskCount: "{count} task{plural}",
                        categories: {
                            doFirst: {
                                label: "DO FIRST",
                                desc: "Urgent pressure with high impact. Needs immediate focus."
                            },
                            plan: {
                                label: "PLAN",
                                desc: "Important work. Schedule dedicated blocks before deadlines."
                            },
                            reduceHelp: {
                                label: "REDUCE / GET HELP",
                                desc: "Scope can be trimmed, simplified, or delegated with peer help."
                            },
                            later: {
                                label: "LATER",
                                desc: "Lower immediate stakes. Can be safely addressed after the crunch."
                            }
                        },
                        continueBtn: "Continue to Available Time →"
                    },
                    availableTime: {
                        backToPriorityReview: "← Back to Priority Review",
                        badge: "AVAILABLE TIME",
                        title: "When can you actually work on this?",
                        subtitle: "Tell Tempo when you're available. We'll build the plan around your time — not the other way around.",
                        shortcuts: "Quick shortcuts",
                        shortcutsColon: "Quick shortcuts:",
                        freeRestOfToday: "Free for rest of today",
                        copyTodayToTomorrow: "Copy today to tomorrow",
                        today: "TODAY",
                        tomorrow: "TOMORROW",
                        total: "total",
                        markNotAvailable: "Mark day as not available",
                        removeDay: "Remove day",
                        removeDayTooltip: "Remove this day from planning window",
                        from: "From",
                        to: "to",
                        addAnotherBlock: "+ Add another time block",
                        addAnotherDay: "+ Add another day",
                        addAvailabilityFor: "Add availability for",
                        selectDate: "Select date:",
                        cancel: "Cancel",
                        addDay: "Add day",
                        totalAvailableTime: "Total Available Time:",
                        estimatedWorkload: "Estimated Tasks Workload:",
                        notAvailableBadge: "NOT AVAILABLE",
                        dayUnavailableDesc: "You marked this day as unavailable. No tasks will be scheduled here.",
                        addAvailabilityForDay: "+ Add availability for this day",
                        allUnavailableTitle: "You haven't added any available work time yet.",
                        allUnavailableDesc: "Add at least one time block so Tempo can organize your tasks effectively.",
                        resetDefaultAvailability: "Reset default availability",
                        overlaps: "Overlaps",
                        overlapsTooltip: "Overlapping minutes are deduplicated automatically",
                        removeDayTitle: "Remove this day?",
                        continueBtn: "Check Feasibility & Build Plan →"
                    },
                    workingPlan: {
                        backToAvailability: "← Back to availability",
                        backToPlanOverview: "← Back to plan overview",
                        badge: "WORKING PLAN",
                        title: "Your Working Plan",
                        subtitle: "Here's a starting point based on what you told us. You can reorder, move between days, or adjust estimates anytime.",
                        today: "TODAY",
                        tomorrow: "TOMORROW",
                        availabilityConflict: "Availability conflict",
                        conflictMessageToday: "Tasks scheduled for TODAY exceed available capacity.",
                        conflictMessageDay: "Tasks scheduled for {day} exceed available capacity.",
                        upNext: "UP NEXT",
                        then: "THEN",
                        doLater: "LATER",
                        doThisTaskLater: "Do this task later",
                        estimate: "Estimate",
                        estimateColon: "Estimate:",
                        editEstimate: "Edit estimate",
                        deadline: "Deadline",
                        deadlineColon: "Deadline:",
                        editDeadline: "Edit deadline",
                        cadence: "Cadence",
                        focus: "focus",
                        breakWord: "break",
                        recovery: "recovery",
                        recoverySeparator: "{duration} recovery",
                        flexibleUntimed: "Flexible / Untimed",
                        scheduledBeyondBlocks: "Scheduled (Beyond available blocks)",
                        flexible: "Flexible",
                        unallocatedTitle: "{count} task{plural} need more available working blocks",
                        unallocatedDesc: "We scheduled what fits first. The following work still needs dedicated time: <strong>{tasks}</strong>.",
                        addMoreAvailability: "+ Add more availability to fit everything",
                        unarrangedTitle: "Unarranged Tasks ({count})",
                        unarrangedDesc: "These tasks are not currently scheduled into a specific time window. You can schedule them whenever you're ready.",
                        scheduleTask: "Schedule task",
                        emptyPlan: "No tasks scheduled in plan. Return to Reality Check to add tasks.",
                        planUpdatedTitle: "Plan is updated and saved",
                        planUpdatedDesc: "Any adjustments you make are automatically saved.",
                        returnToPlanOverview: "Return to Plan Overview →",
                        startFocusZone: "Start Focus Zone →",
                        confirmWorkableTitle: "Does this plan feel workable?",
                        confirmWorkableDesc: "You can change it again later as you make progress.",
                        useThisPlan: "Use this plan →",
                        taskOrderConflict: "This order needs more time than your current availability on this day.",
                        deadlineRiskTitle: "Deadline risk:",
                        deadlineRiskDesc: "With this order, {name} is due on {deadline} and may finish after its deadline.",
                        keepMyOrder: "Keep my order"
                    }
                },
                recovery: {
                    name: "Recovery Mode",
                    shortName: "Recovery",
                    tagline: "Nervous system decompression & sustainable rhythm rebuild",
                    introBanner: "You're in Recovery Mode. Take your time, listen to yourself, and rebuild your energy.",
                    dismissBanner: "Got it",
                    selfCheck: "SELF-CHECK",
                    selfCheckTitle: "Self-check",
                    selfCheckDesc: "What would you like to keep an eye on?",
                    setupSelfCheck: "Set up Self-check",
                    setupMySelfCheck: "Set up my Self-check",
                    checkInToday: "Check in today",
                    viewToday: "View today's check-in",
                    manageSelfCheck: "Manage Self-check",
                    streakCount: "{count}-day streak",
                    streakHelp: "Consistent presence helps you notice your rhythm.",
                    signsOfStress: "Signs of stress",
                    supportiveHabits: "Supportive habits",
                    generalHabits: "General",
                    recoveryNote: "RECOVERY NOTICE",
                    noticeModalHeader: "RECOVERY NOTICE",
                    noticeModalTitle: "My Recovery Notice",
                    noticeModalSubtitle: "Things you wanted to remember when things feel heavy.",
                    noticeModalEditBtn: "Edit note",
                    noticeModalCloseBtn: "Close",
                    noteTitle: "A note to myself",
                    noteEmptyTitle: "Keep what helps in one place",
                    noteEmptyDesc: "If you notice something you'd like your future self to remember when things feel heavy, you can keep it here.",
                    addNoteItem: "+ Add something to your note",
                    viewNote: "View Recovery Notice",
                    editNote: "Edit",
                    itemsSaved: "{count} items saved",
                    recently: "RECENTLY",
                    recentlyEmpty: "Nothing here yet.",
                    recentlyEmptyDesc: "Once you start checking in, this space can help you look back at what you've been noticing over time.",
                    recentlyJustStarted: "You're just getting started.",
                    recentlyJustStartedDesc: "There's not enough history to compare yet. Keep checking in at your own pace.",
                    nothingNeedsRecorded: "Nothing needs to be recorded until you're ready.",
                    viewHistory: "View history →",
                    somethingToNotice: "SOMETHING TO NOTICE",
                    youWantedToRemember: "YOU WANTED TO REMEMBER",
                    remindMeLater: "Remind me later",
                    dismiss: "Dismiss",
                    weeklyReview: "WEEKLY REVIEW",
                    weeklyReviewReady: "Your weekly review is ready.",
                    startWeeklyReview: "Start weekly review →",
                    todaySection: "Today",
                    nothingPlannedToday: "Nothing planned for today",
                    nothingPlannedDesc: "Take advantage of a clear day to rest or do something you enjoy.",
                    recoveryTools: "Recovery Tools",
                    learnSolve: "Learn & Solve",
                    posts: "Tempo Posts",
                    workingPlan: "Working Plan",
                    workingPlanTitle: "Working Plan",
                    editPlan: "Edit Plan",
                    quickRelief: "Quick Relief",
                    focusNow: "Focus Now",
                    transitionQuestion: "Are things feeling more overwhelming now?",
                    changeMyMode: "Change my mode",
                    streakHeading: "Your Self-check Streak 🔥",
                    skip: "Skip",
                    save: "Save",
                    checkinSummary: "You checked on {completed}/{total} things today.",
                    viewTodayCheckin: "View today's check-in",
                    editTrackingSystem: "Edit tracking",
                    editTracking: "Edit tracking",
                    greeting: "Hi {name}, how are you today?",
                    dailyCheckinBadge: "YOUR DAILY CHECK-IN",
                    todaySelfCheckTitle: "Today’s self-check",
                    streakDays: "{count}-day streak",
                    selectLevel: "Select level:",
                    recentlyTitle: "Recently",
                    adjustTracking: "Adjust Tracking",
                    methodPercentage: "Average level",
                    methodScale: "Average score",
                    methodQuantity: "Total recorded",
                    methodOptions: "Option distribution",
                    methodYesNo: "Response distribution",
                    avgTensionLevel: "Your average tension level is",
                    nightsQualitySleep: "Nights of Quality Sleep",
                    walkedFor: "You have walked for",
                    loggedCount: "You have logged",
                    weeklyReportCountdown: "{days} day{s} until your weekly report.",
                    weeklyReportReadyToday: "Your weekly report is ready today.",
                    fromCommunity: "From the Tempo Community",
                    seeAll: "View all",
                    viewAll: "View all",
                    onboarding: {
                        badge: "RECOVERY MODE",
                        badgeReturning: "RECOVERY MODE · WELCOME BACK",
                        badgeReview: "RECOVERY MODE · TRACKING SYSTEM REVIEW",
                        case1Title: "Welcome to Rmode",
                        case1Purpose: "Give yourself some space to decompress and recover.",
                        case1Benefits: "Rmode helps you slow down, notice what supports your nervous system, and rebuild a sustainable daily rhythm.",
                        case1Question: "Are you ready to set up your Tracking System?",
                        case1QuestionSub: "Choose a few things that feel useful to observe. You can adjust them anytime.",
                        case1Yes: "Yes, let's set it up →",
                        case1Later: "Later",
                        case2Title: "Welcome back!",
                        case2Question: "Would you like to review your Tracking System?",
                        case2Summary: "You currently have {count} active tracking item{s}.",
                        case2SummaryEmpty: "You currently have 0 active items. Your past tracking records are safely preserved in archive.",
                        case2TrackingStatus: "CURRENT TRACKING",
                        case2Yes: "Yes, review my system →",
                        case2No: "No, go to dashboard",
                        reviewTitle: "Your Tracking System",
                        reviewSubtitle: "Review your active tracking items below. You can keep your system as is, or adjust individual items.",
                        reviewActiveItems: "Active Tracking Items ({count})",
                        reviewNoActive: "No tracking items are currently active.",
                        reviewHistoricalPreserved: "Past check-in records and archived items remain safe in your archive.",
                        optionATitle: "Option A – Keep current system",
                        optionADesc: "Keep all existing tracking items and configurations. Does not overwrite or reset history. Continue to Self-check tool.",
                        optionABtn: "Keep current system",
                        optionBTitle: "Option B – Adjust my system",
                        optionBDesc: "Keep or remove items, update tracking methods, or add new items. Historical records for unchanged items are safely preserved.",
                        optionBBtn: "Adjust my system",
                        backToDashboard: "Return to Dashboard",
                        back: "← Back",
                        toastKeepSuccess: "Current tracking system preserved.",
                        toastSaveSuccess: "Tracking system updated successfully.",
                        adjustStep1Badge: "STEP 1 OF 3 · TRACKING SYSTEM",
                        adjustStep1Tag: "Setup Adjustment",
                        adjustStep1Title: "Adjust your tracking items",
                        adjustStep1Desc: "Choose which items to keep, update tracking methods, or stop tracking items. Stopped items are archived and past data is preserved.",
                        adjustActiveBadge: "Active",
                        adjustEditBtn: "Edit",
                        adjustStopBtn: "Stop tracking",
                        adjustKeepBtn: "Keep tracking",
                        adjustAddBtn: "+ Add new tracking item",
                        adjustBackBtn: "← Back to Hub",
                        adjustContinueBtn: "Continue to Recovery Notice →"
                    }
                },
                unclear: {
                    name: "Unclear Mode",
                    shortName: "Unclear",
                    tagline: "Guided unpack & reflective clarity",
                    subtitle: "When everything feels like a lot and you don't know where to start.",
                    stepOf: "Step {step} of {total}",
                    startClarifying: "Start clarifying",
                    thingsAreClearer: "Things are a little clearer.",
                    thingsAreClearerDesc: "Here is what you noticed. Choose what feels most supportive right now.",
                    goToUrgent: "Go to Urgent Mode",
                    goToRecovery: "Go to Recovery Mode",
                    returnToTempo: "Return to Tempo",
                    exploreSupport: "Explore support options",
                    stayUnclear: "Stay in Unclear Mode for now",
                    whatOnMind: "What's been on your mind?",
                    whatHeaviest: "What feels heaviest right now?",
                    whatNoticed: "What you've noticed lately?",
                    whatNeedNow: "What you need right now?",
                    landing: {
                        greeting: "Hi {name},",
                        heading1: "Not sure where to start?",
                        heading2: "Let’s figure it out together.",
                        subtitle: "Let’s try a few quick check-ins to understand what you need.",
                        doTempoTest: "Do Tempo Test",
                        viewMyResults: "View my results",
                        exploreHeading: "Explore Mental<br />Health Tests",
                        depressionAssessments: "Depression Assessments",
                        stressAssessments: "Stress Assessments",
                        anxietyAssessments: "Anxiety Assessments",
                        otherAssessments: "Other Assessments",
                        backToDashboard: "Back to Dashboard"
                    }
                },
                selector: {
                    switchMode: "Switch Mode",
                    activeBadge: "Active"
                }
            },
            workspace: {
                title: "Plan Workspace",
                returnHome: "Return Home",
                returnHomeText: "Return Home",
                addTask: "Add task",
                addAvailability: "Add availability",
                adjustPlan: "Adjust Plan",
                deletePlan: "Delete my plan",
                deleteMyPlan: "Delete my plan",
                taskProgress: "{completed}/{total} Tasks",
                taskUnit: "Tasks",
                tomorrow: "Tomorrow",
                completed: "Completed",
                deadline: "Deadline",
                deadlinePrefix: "Deadline:",
                noDeadline: "No deadline",
                subtasks: "Subtasks",
                doNow: "Do now",
                done: "Done",
                editDeadline: "Edit deadline",
                breakDownTask: "+ Break down task",
                addNote: "+ Add note",
                markAsDone: "Mark as done",
                focusNow: "Focus now",
                reschedule: "Reschedule",
                clearThisTask: "Clear this task",
                availability: "Availability",
                addAvailability: "Add availability",
                addAvailabilityBtn: "+ Add availability",
                copyToTomorrow: "Copy to Tomorrow",
                repeatWeekly: "Repeat Weekly",
                repeatEveryWeek: "Repeat every week",
                startDate: "Start date",
                endDate: "End date (optional)",
                confirm: "Confirm",
                cancel: "Cancel",
                copiedSuccessfully: "Working hours copied successfully.",
                noWorkingHours: "No working hours available to copy.",
                adjustPlanStep1: "STEP 1 OF 3 · ADJUST PLAN",
                chooseTasksToKeep: "Choose tasks to keep",
                chooseTasksToKeepDesc: "Select the tasks you still need to complete. Overdue or completed tasks can be removed or kept.",
                cancelAdjustment: "Cancel adjustment",
                nextAdjustAddTasks: "Next: Adjust & add tasks →",
                adjustPlanStep2: "STEP 2 OF 3 · ADJUST PLAN",
                adjustEstimatesAndAddTasks: "Adjust estimates & add new tasks",
                retainedTasksCount: "RETAINED TASKS ({count}):",
                duePrefixLabel: "Deadline:",
                addNewTaskUpper: "+ ADD NEW TASK:",
                taskNamePlaceholderEllipsis: "Task name...",
                addPlain: "Add",
                datePlaceholderStep2: "MMM DD, YYYY",
                adjustPlanStep3: "STEP 3 OF 3 · CONFIRM UPDATED PLAN",
                proposedUpdatedPlan: "Proposed Updated Plan",
                adjustPlanStep3Desc: "Here is your updated working plan. Your original plan is preserved until you confirm and save.",
                doThisFirstUpper: "DO THIS FIRST",
                upNextUpper: "UP NEXT",
                noFixedDeadlineStep3: "No fixed deadline",
                saveUpdatedPlan: "Save updated plan →",
                planConfirmedAndSavedUpper: "PLAN CONFIRMED & SAVED",
                yourTaskForNow: "Your task for now",
                doThisFirstPriority: "DO THIS FIRST",
                dueNoFixedDeadline: "Deadline: No fixed deadline",
                dueWithDeadlinePrefix: "Deadline:",
                breakDownQuestion: "Would you like to break down this task into smaller steps?",
                breakDownDesc: "Breaking big tasks into 10–15 min steps prevents freeze and makes starting effortless.",
                noStartWorking: "No, start working",
                breakDownTaskBtn: "Break down task →",
                readyToWorkUpper: "READY TO WORK",
                startWorkingOnPlanTitle: "Start working on your plan?",
                startWorkingOnPlanDesc: "Your working plan is ready. Would you like to start right away on your first task?",
                firstTaskPrefix: "First task:",
                laterBtn: "Later",
                breakMoreTasksBtn: "Break more tasks",
                yesStartWorkingBtn: "Yes, start working →",
                firstTaskExecutionUpper: "FIRST TASK EXECUTION",
                yourFirstTaskIs: "Your first task is…",
                readyNowBadge: "READY NOW",
                chooseAnotherTaskBtn: "Choose another task",
                doThisTaskBtn: "Do this task →",
                taskSelectionUpper: "TASK SELECTION",
                selectTaskToWorkOn: "Select a task to work on",
                selectTaskWithArrow: "Select →",
                breakdownEmptyState: "No action steps added yet. Add your first step below or click ✨ AI Help.",
                workingPlanActiveBadge: "WORKING PLAN ACTIVE",
                workingPlanActiveBody: "You already have an active Working Plan saved. Take a 2-minute reset to ground your focus, or review and keep your existing plan.",
                groundedStartBadge: "GROUNDED START",
                groundedStartTitle: "Take a moment to reset?",
                groundedStartBody: "Urgent situations feel much lighter when you pause first. Would you like a 2-minute reset to calm your nervous system before organizing your tasks?",
                buildMyPlanBtn: "Build my plan",
                groundedCheckpointBadge: "GROUNDED CHECKPOINT",
                areYouReadyTitle: "Are you ready?",
                areYouReadyBody: "You took a moment to breathe and reset. How do you feel about moving into your Working Plan now?",
                areYouReadySub: "If you still feel overwhelmed, you can return to take another pause or rest anytime.",
                notYetReturnResetBtn: "Not yet, return to reset",
                yesImReadyBtn: "Yes, I'm ready →",
                planUpdateNeededBadge: "PLAN UPDATE NEEDED",
                reviewAndResetWorkingPlanTitle: "Review and reset your Working Plan",
                planUpdateNeededBody: "You have tasks with overdue deadlines that need your attention. Take a quick reset to calm down, or review your tasks and adjust your schedule.",
                boxBreathingFeature: "2 min box breathing",
                groundsFocusFeature: "Grounds focus",
                noRushFeature: "No rush",
                reviewYourPlanBtn: "Review your plan",
                yesTakeQuickResetBtn: "Yes, take a quick reset →",
                workingPlanReviewBadge: "WORKING PLAN REVIEW",
                workingPlanSummaryTitle: "Your Working Plan Summary",
                tasksOverdueCount: "{count} tasks overdue:",
                taskOverdueSingleCount: "{count} task overdue:",
                overdueWarningDesc: "Some tasks passed their planned date or deadline. You can keep them or adjust your schedule.",
                badgeOverdue: "OVERDUE",
                badgeUpNext: "UP NEXT",
                badgeThen: "THEN",
                badgeLater: "LATER",
                noFixedDeadlineLabel: "No fixed deadline",
                adjustMyPlanBtn: "Adjust my plan",
                keepThePlanBtn: "Keep the plan →",
                yourTaskForNowBadge: "YOUR TASK FOR NOW",
                yourTaskForNowHeading: "Your task for now is…",
                focusNowBtn: "Focus now →",
                nextProposePlan: "Next: Propose plan →",
                saveAvailability: "Save availability",
                dateLabel: "Date",
                startTimeLabel: "Start time",
                endTimeLabel: "End time",
                cancelAction: "Cancel",
                errorFillAllAvailabilityFields: "Please enter date, start time, and end time.",
                errorEndTimeAfterStartTime: "End time must be later than start time.",
                errorPastAvailabilityDate: "Cannot add availability for a past date.",
                errorPastAvailabilityTime: "Cannot add availability for past time.",
                errorOverlapAvailability: "This slot overlaps with existing availability ({start} – {end}).",
                errorConflictScheduledTask: "This time slot conflicts with an already scheduled task: \"{name}\" ({start} – {end}).",
                priorityNow: "Now",
                priorityLater: "Later",
                priorityDone: "Done",
                priorityOverdue: "Overdue",
                priorityOverdueUpper: "OVERDUE",
                scheduledDateLabel: "Scheduled date",
                dueDateLabel: "Deadline",
                duePrefix: "Deadline:",
                subtasksLabel: "Subtasks",
                notesLabel: "Notes",
                notePrefix: "Note:",
                markAsDone: "Mark as done",
                markAsActive: "Mark as active",
                focusNowAction: "Focus now",
                rescheduleAction: "Reschedule",
                clearThisTaskAction: "Clear this task",
                missedSchedule: "Missed Schedule",
                missedScheduleUpper: "MISSED SCHEDULE",
                deadlineConflict: "Deadline Conflict",
                stepBreakdown: "Step Breakdown",
                stepBreakdownUpper: "STEP BREAKDOWN",
                noteEditor: "Note Editor",
                clearTaskConfirmation: "Clear Task Confirmation",
                deadlineReorder: "Deadline Reorder",
                home: "Home",
                returnToHome: "Return to Home",
                focus: "Focus",
                startFocus: "Start Focus",
                timeline: "Timeline",
                unscheduled: "Not Scheduled Yet",
                notScheduledYet: "NOT SCHEDULED YET",
                addTask: "+ Add Task",
                taskDetails: "Task Details",
                scheduledFor: "Scheduled for:",
                deadline: "Deadline:",
                editDeadline: "Edit deadline",
                noDeadline: "No deadline",
                duration: "Duration:",
                editEstimate: "Edit duration",
                actionSteps: "Action Steps",
                addSubtask: "+ Add subtask",
                subtaskPlaceholder: "Add a small next action...",
                markCompleted: "Mark Complete",
                markIncomplete: "Mark Incomplete",
                deleteTask: "Delete task",
                doThis: "DO THIS",
                then: "THEN",
                later: "LATER",
                noPlanTitle: "No active Urgent Plan found",
                noPlanDesc: "You don't have an active Urgent Plan right now. Create one to get clear, realistic guidance.",
                createUrgentPlan: "Create an Urgent Plan →",
                headerSubtitle: "Here's what you're working through right now.",
                durationSummary: "~{duration} focused work{unestimated}",
                unestimatedCount: " (+{count} unestimated)",
                tasksCount: "{count} tasks",
                completedCount: "completed",
                startFocusNow: "Start Focus Now",
                adjustAvailability: "Adjust availability",
                allPlannedWorkDone: "All planned work done ✓",
                activeTasksCount: "{count} active tasks",
                estimate: "Estimate:",
                due: "Deadline:",
                mayFinishAfterDeadline: "May finish after deadline",
                completed: "Completed",
                inProgress: "In progress",
                notStarted: "Not started",
                start: "Start",
                continueFocus: "Continue Focus",
                addAnotherTask: "+ Add another task to this plan",
                allActiveScheduled: "All active tasks have been placed into your schedule.",
                scheduleTask: "Schedule task →",
                undo: "Undo",
                editTask: "Edit Task",
                scheduledUpper: "SCHEDULED",
                reschedule: "Reschedule",
                deadlineUpper: "DEADLINE",
                noFixedDeadline: "No deadline",
                saveDeadline: "Save deadline",
                estimateUpper: "ESTIMATE",
                flexibleFocusedWork: "Flexible focused work",
                actionStepsUpper: "ACTION STEPS",
                addNextStep: "Add next step...",
                add: "+ Add",
                startFocusOnTask: "▶ Start Focus on this task",
                removeFromPlan: "Remove from plan",
                addTaskModalTitle: "Add a task",
                taskName: "Task Name",
                taskNamePlaceholder: "e.g. Research Literature Review",
                focusedEstimate: "Focused-work Estimate",
                notSureYet: "Not sure yet",
                addTaskBtn: "Add task",
                taskAdded: "Task added",
                taskReadyDesc: "\"{name}\" is ready.",
                fitIntoPlan: "Fit it into my plan",
                leaveUnscheduled: "Leave it unscheduled for now",
                rescheduleTaskModalTitle: "Reschedule task",
                yourAvailableTime: "YOUR AVAILABLE TIME",
                noTimeBlocks: "No time blocks defined",
                figureOutLater: "I'll figure it out later (Move to Unscheduled)",
                schedule: "Schedule",
                yourAvailableTimeTitle: "Your available time",
                addTimeWindow: "+ Add Available Time Window",
                addWindowBtn: "Add window"
            },
            sos: {
                title: "SOS · Immediate Support",
                subtitle: "Your safety comes first",
                pillSupport: "Get support now →",
                safetyBannerHeading: "Safety Mode Active — Immediate human support is right here.",
                safetyBannerDesc: "You don't need to finish any exercises to speak with someone. You can tap \"Get support now →\" at any second.",
                eyebrow: "SOS · IMMEDIATE SUPPORT",
                mainHeading: "I don't feel safe right now",
                situationIntro: "If right now you're:",
                situation1: "panicking and feel out of control",
                situation2: "having thoughts or urges to hurt yourself",
                situation3: "not feeling safe being alone",
                reassuranceTitle: "Your safety comes first.",
                reassuranceBody: "You don't need to handle everything by yourself right now.",
                getSupportNow: "Get support now →",
                altOptionsHeading: "Or choose what you need right now",
                optionABadge: "Option A",
                optionATitle: "I'm overwhelmed or panicking",
                optionADesc: "I feel stressed, overwhelmed, or unable to think clearly.",
                optionBBadge: "Option B • Immediate Support",
                optionBTitle: "I'm in an emotional crisis or don't feel safe",
                optionBDesc: "I'm experiencing intense emotional distress and need immediate support.",
                optionCBadge: "Option C • Urgent Care",
                optionCTitle: "I'm thinking about hurting myself or suicide",
                optionCDesc: "I'm having thoughts about harming myself or ending my life.",
                optionDLabel: "I'm not sure — my mind is racing and I just need help slowing down",
                drawerTitle: "Get Support Now",
                drawerSubtitle: "If you don't feel safe, don't stay alone.",
                drawerSubtitleDesc: "Stay with someone you trust and reach out for support now.",
                medicalTitle: "Emergency Medical Support",
                medicalBadge: "Emergency",
                medicalDesc: "If you're at immediate risk of hurting yourself or you're in immediate danger.",
                medicalCall: "Call 115 Now",
                hotlineTitle: "HOPE — Suicide Prevention Hotline",
                hotlineBadge: "Crisis Support",
                hotlineDesc: "If you're in crisis, having thoughts of hurting yourself, or need someone to support you right now.",
                hotlineCall: "Call 0865 044 400",
                ngayMaiTitle: "NGÀY MAI SUPPORT HOTLINE",
                ngayMaiBadge: "Mental Health Support",
                ngayMaiPhone: "096 306 1414",
                ngayMaiDesc: "Free psychological first aid by phone for people experiencing emotional distress or depression, and their loved ones. Confidential and non-judgmental support.",
                ngayMaiHours: "1:00 PM – 8:30 PM, Wednesday – Sunday",
                ngayMaiCall: "Call 096 306 1414",
                waitingHeader: "While you're waiting for support",
                action1: "Stay with someone you trust.",
                action2: "Move somewhere safer.",
                action3: "Create distance from anything that could hurt you.",
                waitingReassTitle: "You don't need to solve everything right now.",
                reassurance: "For now, just focus on staying safe.",
                trustedTitle: "Reach Out to Someone You Trust:",
                trustedDesc: "Copy this simple message to reach out to a friend or family member:",
                trustedQuote: "Hey, I'm having a really difficult time right now and feeling overwhelmed. Are you free to talk or sit with me for a few minutes?",
                copyTrustedBtn: "Copy Message",
                campusTitle: "Campus Student Wellbeing",
                campusBadge: "Office Hours Support",
                campusDesc: "For immediate crisis or danger, call 115 or 0865 044 400. For non-urgent campus advising questions during office hours:",
                fptTitle: "FPT University Psychological Counseling Office",
                fptDesc: "Free and confidential psychological counseling services for FPT University students.",
                fptEmail: "tuvansinhvien@fpt.edu.vn",
                fptCta: "Send counseling email",
                offlineContactPlaceholder: "Your name or student email (optional)",
                offlineMsgPlaceholder: "Describe your question or message for office hours...",
                offlineSubmitBtn: "Leave Message for Campus Staff",
                offlineSuccessMsg: "Message saved. Staff will respond during normal hours. For immediate help, call 115 or 0865 044 400.",
                closeSOS: "Close Support Drawer"
            },
            tools: {
                focusZone: "Focus Zone",
                focusZoneDesc: "Distraction-free focus workspace.",
                quickStressRelief: "Quick Stress Relief",
                quickStressReliefDesc: "2-3 minute exercises to decompress your nervous system.",
                boxBreathing: "Breathing",
                boxBreathingDesc: "Box breathing technique to quickly regain calm.",
                tempoBreak: "Tempo Break",
                tempoBreakDesc: "Take a pause to reset and recharge."
            },
            community: {
                title: "Tempo Community",
                returnToDashboard: "Return to Dashboard",
                returnToDashboardWithArrow: "← Return to Dashboard",
                tabs: {
                    announcement: "Announcement",
                    tips: "Tips",
                    learn: "Learn",
                    posts: "Posts",
                    messages: "Direct Message"
                },
                tips: {
                    searchPlaceholder: "Search...",
                    usage: "Usage:",
                    seeMore: "See more →",
                    seeMoreLabel: "See more",
                    noSolutionsFound: "No matching solutions found",
                    tryDifferentTerms: "Try searching with different terms.",
                    resetSearch: "Reset Search",
                    items: {
                        deadline_pileup: {
                            title: "The 5-Minute Starter Rule for Paralyzing Deadlines",
                            usage: "Try it when you have a lot to do that makes you not want to do anything at all"
                        },
                        presentation_dread: {
                            title: "Presentation anxiety",
                            usage: "Try it when you have a presentation ahead and you feel anxious about it"
                        },
                        brain_fog_reset: {
                            title: "Brain Fog Reset & Mental Momentum",
                            usage: "Try it when mental fatigue blocks focus and simple tasks feel impossible"
                        },
                        exam_panic_surge: {
                            title: "Exam panic & physiological sigh reset",
                            usage: "Try it when sudden panic spikes right before or during a major test"
                        },
                        email_paralysis: {
                            title: "Professor extension email template",
                            usage: "Try it when severe stress requires requesting an urgent assignment extension"
                        },
                        sleep_runaway: {
                            title: "Racing night thoughts wind-down",
                            usage: "Try it when academic worries keep you awake well past 2 AM"
                        },
                        falling_behind: {
                            title: "Falling behind / not keeping up",
                            usage: "Struggling to keep pace with lecture material, required readings, or lab work."
                        },
                        teamwork: {
                            title: "Teamwork problems",
                            usage: "Unbalanced workload, unresponsive group members, or communication friction."
                        },
                        teamwork_problems: {
                            title: "Teamwork problems",
                            usage: "Unbalanced workload, unresponsive group members, or communication friction."
                        },
                        grades: {
                            title: "Grades didn’t go as expected",
                            usage: "Coping with academic disappointment and extracting constructive next steps."
                        },
                        grades_disappointment: {
                            title: "Grades didn’t go as expected",
                            usage: "Coping with academic disappointment and extracting constructive next steps."
                        },
                        presentation_anxiety: {
                            title: "Presentation anxiety",
                            usage: "Intense nervousness, racing heartbeat, or dread before speaking in class or giving a presentation."
                        },
                        cant_focus: {
                            title: "Can’t focus / can’t get started",
                            usage: "Staring at a blank screen, experiencing brain fog, or feeling frozen when trying to begin study tasks."
                        },
                        future_uncertainty: {
                            title: "Unsure about direction / future",
                            usage: "Worrying about career choices, major selection, or feeling aimless compared to peers."
                        },
                        not_good_enough: {
                            title: "Feeling \"not good enough\"",
                            usage: "Persistent self-doubt, imposter syndrome, and feeling like everyone else understands while you don't."
                        },
                        expectations_pressure: {
                            title: "Pressure from expectations of myself",
                            usage: "Perfectionism, harsh internal standards, and fear of making mistakes in coursework."
                        },
                        comparing_others: {
                            title: "Comparing myself with other people",
                            usage: "Feeling inadequate when observing peers’ internships, study pace, or social achievements."
                        },
                        too_many_responsibilities: {
                            title: "Too many responsibilities at once",
                            usage: "Overloaded with study, part-time jobs, student clubs, and family commitments simultaneously."
                        },
                        relationship_conflict: {
                            title: "Conflict with someone important",
                            usage: "Friction with a roommate, partner, friend, or family member impacting your ability to study."
                        },
                        loneliness: {
                            title: "Loneliness / feeling disconnected",
                            usage: "Feeling isolated on campus, lacking belonging, or having nobody to confide in during tough weeks."
                        },
                        disrupted_routine: {
                            title: "Daily routine has been disrupted for a while",
                            usage: "Sleep schedule inverted, meals irregular, and everyday habits eroded by ongoing stress."
                        }
                    }
                }
            },
                learn: {
                    searchPlaceholder: "Search...",
                    seeMore: "See more →",
                    seeMoreLabel: "See more",
                    noTopicsFound: "No educational topics found",
                    tryDifferentTerms: "Try searching with a broader keyword or clearing your search.",
                    resetSearch: "Reset Search",
                    cards: {
                        what_is_stress: {
                            title: "What is stress?",
                            summary: "Stress is a state of worry or mental tension caused by a difficult situation. Stress is a natural human response that prompts us to address challenges and threats in our lives. Everyone experiences stress to some degree."
                        },
                        stress_eating: {
                            title: "Stress eating",
                            summary: "Stress eating, or emotional eating, is using food to make yourself feel better—eating to satisfy emotional needs, rather than to satisfy physical hunger."
                        },
                        stress_loop: {
                            title: "The Student Stress Loop",
                            summary: "How acute deadlines trigger mental paralysis, creating avoidance loops that multiply stress levels."
                        }
                    }
                },
            posts: {
                title: "Tempo Posts",
                returnToDashboard: "Return to Dashboard",
                returnToDashboardWithArrow: "← Return to Dashboard",
                subtitle: "Real experiences from students navigating the same challenges.",
                like: "Like",
                relate: "Relate",
                support: "Support",
                comment: "Comment",
                commentsCount: "{count} comments",
                save: "Save",
                saved: "Saved",
                share: "Share",
                seeAllPosts: "See all posts →",
                writeComment: "Write a supportive comment...",
                filterLatest: "Latest",
                filterPopular: "Popular",
                newPost: "New post",
                searchPlaceholder: "Search...",
                yourPosts: "Your posts",
                notifications: "Notifications",
                savedPosts: "Saved posts",
                replyPlaceholder: "Reply...",
                postSubmit: "Post"
            },
            auth: {
                regHeading: "CREATE YOUR TEMPO ACCOUNT",
                regTitle: "Welcome to Tempo",
                regSubtitle: "Manage academic stress, organize deadlines, and find your rhythm.",
                regNameLabel: 'Display name <span class="text-rose-500">*</span>',
                regNamePlaceholder: "e.g. Alex or Nguyễn Yến Nhi",
                regEmailLabel: 'Email <span class="text-rose-500">*</span>',
                regEmailPlaceholder: "you@example.com",
                regPasswordLabel: 'Password <span class="text-rose-500">*</span>',
                regPasswordPlaceholder: "Min. 6 characters",
                regSubmitBtn: "Create account",
                regFooterText: 'Already have an account? <button type="button" onclick="window.TempoAuth.openSignInModal()" class="text-[#FF6B2C] font-bold hover:underline ml-1 cursor-pointer">Log in</button>',
                loginHeading: "WELCOME BACK",
                loginTitle: "Welcome Back",
                loginSubtitle: "Sign in to your Tempo account.",
                loginEmailLabel: "Email",
                loginPasswordLabel: "Password",
                loginForgotLink: "Forgot password?",
                loginSubmitBtn: "Log in",
                loginFooterText: 'Don\'t have an account? <button type="button" onclick="window.TempoAuth.openRegisterModal()" class="text-[#FF6B2C] font-bold hover:underline ml-1 cursor-pointer">Create account</button>',
                forgotPrompt: "Enter your registered email address to receive password reset instructions:",
                forgotSent: "Password reset link has been sent to your email.",
                fillRequired: "Please fill in all required fields.",
                passTooShort: "Password must be at least 6 characters long."
            },
            footer: {
                descriptor: "Academic Stress & Deadline Triage",
                disclaimer: "Confidential peer wellbeing support. Not a replacement for emergency or psychiatric services.",
                terms: "Terms of Service",
                privacy: "Privacy Policy",
                sos: "SOS · Immediate Support",
                copyright: "© 2026 Tempo"
            },
            routing: {
                eyebrow: "FIND YOUR NEXT STEP",
                title: "What best describes where you are right now?",
                desc: "Different situations need different approaches. Choose the path that matches what you're experiencing:",
                urgent: {
                    badge: "ACUTE ACTION",
                    title: "Deadline is Urgent",
                    desc: "Urgent work needs attention, but stress is making it hard to focus, start, or prioritize.",
                    cta: "Go to Urgent Mode"
                },
                recovery: {
                    badge: "RECOVER & RECHARGE",
                    title: "Recovering from Heavy Stress",
                    desc: "The urgent pressure has passed, but you still feel tired, anxious, or mentally drained.",
                    cta: "Go to Recovery Mode"
                },
                unclear: {
                    badge: "UNCLEAR",
                    title: "Not Sure What's Wrong",
                    desc: "You feel off, but you're not sure why or what you need right now.",
                    cta: "Go to Unclear Mode"
                },
                support: {
                    badge: "IMMEDIATE SUPPORT",
                    title: "I Don't Feel Safe",
                    desc: "You feel panicked or out of control, have thoughts of self-harm, or don't feel safe being alone right now.",
                    cta: "Get Immediate Support"
                }
            },
            toolNotes: {
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
                viewTask: "View Task",
                taskUnavailable: "This task is no longer available.",
                emptyTaskNotesTitle: "No task notes yet.",
                emptyTaskNotesDesc: "Attach specific research notes, formulas, or steps to your working plan tasks.",
                addTaskNoteBtn: "+ Add a Task Note",

                // Detail and Edit Modals
                fullContent: "Full Content",
                editNote: "Edit Note",
                saveChanges: "Save Changes",
                delete: "Delete",
                close: "Close"
            },
            about: {
                // 1. Hero
                heroBadge: "MEET TEMPO",
                heroTitle: "Your space to navigate student life.",
                heroDesc: "Designed with FPT University students in mind, Tempo offers personalized support for mental well-being and stress management — helping you navigate academic pressure today while building awareness and practical skills for the future.",
                heroCta: "Explore Tempo",
                previewBadge: "TEMPO · FPT WELLBEING SPACE",
                card1Title: "Urgent Mode",
                card1Badge: "Deadline triage",
                card1Desc: "Break paralysis into ONE doable step.",
                card2Title: "Self-check",
                card2Badge: "6 dimensions",
                card2Desc: "Gentle reflections, no toxic pressure.",
                card3Title: "Breathing Practice",
                card3Badge: "2-minute reset",
                card3Desc: "Give your mind and body a moment to pause and relax.",
                previewFooter: "Confidential peer support from the community.",

                // 2. When Things Feel Like Too Much
                s02Eyebrow: "WHEN THINGS FEEL LIKE TOO MUCH",
                s02Title: "When things feel like too much",
                s02Desc: "Student life can sometimes bring moments when everything feels urgent, stress becomes difficult to manage, or you are unsure what you really need. Tempo offers support that fits your current state while helping you build awareness and skills for the future.",

                // Scenario 1
                s02C1Eyebrow: "WHEN EVERYTHING PILES UP",
                s02C1Title: "Not sure where to start when everything piles up?",
                s02C1Desc: "When deadlines and responsibilities keep piling up, it can be difficult to identify what needs your attention first.",
                s02C1HelpEyebrow: "HOW TEMPO HELPS",
                s02C1HelpTitle: "Find what needs attention first and identify your next step.",
                s02C1HelpDesc: "Tempo helps you identify what needs attention first, then break it down into manageable steps so you can move forward with greater clarity and confidence.",

                // Scenario 2
                s02C2Eyebrow: "WHEN STRESS TAKES OVER",
                s02C2Title: "Feeling overwhelmed by stress and need a moment to slow down?",
                s02C2Desc: "Sometimes pressure makes it difficult to think clearly, concentrate, or figure out what to do next.",
                s02C2HelpEyebrow: "HOW TEMPO HELPS",
                s02C2HelpTitle: "Regain balance now. Build skills for the future.",
                s02C2HelpDesc: "Tempo offers ways to pause and ease immediate stress while helping you better understand your stress responses and develop suitable coping strategies over time.",

                // Scenario 3
                s02C3Eyebrow: "WHEN YOU'RE NOT SURE WHAT YOU NEED",
                s02C3Title: "Not sure how you're feeling or where to begin?",
                s02C3Desc: "It's not always easy to recognize your current state or know what kind of support would actually help.",
                s02C3HelpEyebrow: "HOW TEMPO HELPS",
                s02C3HelpTitle: "Understand yourself first. Find the support that fits.",
                s02C3HelpDesc: "Tempo helps you reflect on your current state and explore a suitable direction when you're unsure what to do next.",

                // 3. Explore Tempo
                s03Eyebrow: "EXPLORE TEMPO",
                s03Title: "One space, many ways to find your own rhythm.",
                s03Desc: "From finding the right support to building positive habits and connecting with others, explore different ways to navigate student life with Tempo.",

                // 3.1 Modes & SOS
                modesEyebrow: "MODES & SOS",
                modesTitle: "Find the support you need.",
                modesSubtitle: "Every situation calls for a different kind of support.",
                modesDesc: "Explore Tempo's modes to find the direction that fits your current needs, or access SOS when you need a dedicated support flow.",
                modeUrgent: "Urgent",
                modeRecovery: "Recovery",
                modeUnclear: "Unclear",
                sosTitle: "SOS Immediate Support",
                sosFlow: "Dedicated Flow",
                sosNote: "Important: SOS is a dedicated support flow, not a separate mode.",

                // 3.2 Personal Tools
                toolsEyebrow: "PERSONAL TOOLS",
                toolsTitle: "Tools that fit your needs.",
                toolsSubtitle: "Make space for focus, self-reflection, and everyday progress.",
                toolsDesc: "Use Tempo's tools to organize tasks, check in with yourself, build habits, and track your progress at your own pace.",
                toolFocusZone: "Focus Zone",
                toolWorkingPlan: "Working Plan",
                toolSelfCheck: "Self-check",
                toolBreathing: "Breathing",
                toolNotes: "Notes",

                // 3.3 Quick Relief & Learning
                reliefEyebrow: "QUICK RELIEF & LEARNING",
                reliefTitle: "Relax, learn, and grow.",
                reliefSubtitle: "Pause when you need to. Learn along the way.",
                reliefDesc: "Explore activities that help you relax in the moment, alongside resources that help you understand stress and discover suitable coping strategies.",
                reliefCard1Title: "Quick Relief",
                reliefCard1Desc: "Two-minute physical and mental relaxation activities.",
                reliefCard2Title: "Learn & Solve",
                reliefCard2Desc: "Practical approaches to help you navigate university pressure.",

                // 3.4 Community
                communityEyebrow: "COMMUNITY",
                communityTitle: "You are not alone.",
                communitySubtitle: "Student life becomes easier to share when we can connect and understand one another's experiences.",
                communityDesc: "Explore posts from the Tempo Community, listen to different perspectives, and share experiences with fellow students.",
                communityCard1Title: "Tempo Community",
                communityCard1Desc: "Real student stories, honest thoughts & peer encouragement.",
                communityCard2Title: "Tempo Post",
                communityCard2Desc: "Express yourself anonymously or with your student profile.",

                // 4. Your Journey, Your Pace
                s04Eyebrow: "YOUR JOURNEY, YOUR PACE",
                s04Title: "Use Tempo your way.",
                s04Desc: "There is no single way to use Tempo. Start with what feels necessary, explore what genuinely helps, and adjust whenever your needs change.",
                step1Title: "01 — Start with yourself",
                step1Desc: "Not sure what you need? Take a moment to check in with yourself or choose the type of support that fits your current situation.",
                step2Title: "02 — Find what works for you",
                step2Desc: "Explore Tempo's modes, personal tools, quick relief activities, and learning resources. You don't need to use everything — just focus on what works for you.",
                step3Title: "03 — Move at your own pace",
                step3Desc: "One small step at a time. Return to Tempo whenever you need to pause, reflect, or adjust your plan as life changes.",

                // 5. Final CTA
                s05Eyebrow: "TEMPO · YOUR NEXT CHAPTER",
                s05Title: "Ready to find your own rhythm again?",
                s05Desc: "There is no single way to navigate student life. Start with what you need today and take one small step at a time.",
                s05Cta: "Get Started"
            }
        }
    };

    // -------------------------------------------------------------------------
    // LOCALIZATION CONTROLLER
    // -------------------------------------------------------------------------
    let currentLang = DEFAULT_LANG;
    const listeners = new Set();

    function initLanguage() {
        try {
            const saved = localStorage.getItem('tempo_language') || localStorage.getItem('tempo_auth_lang');
            if (saved && SUPPORTED_LANGS.includes(saved)) {
                currentLang = saved;
            } else {
                // Vietnamese-first: first visit defaults to 'vi'
                currentLang = DEFAULT_LANG;
            }
        } catch (e) {
            currentLang = DEFAULT_LANG;
        }
    }

    initLanguage();

    function getLanguage() {
        return currentLang;
    }

    function setLanguage(lang) {
        if (!SUPPORTED_LANGS.includes(lang)) return;
        currentLang = lang;
        try {
            localStorage.setItem('tempo_language', lang);
            localStorage.setItem('tempo_auth_lang', lang);
        } catch (e) {}

        updateNavbarSwitcher();
        updateStaticHtml();
        closeNavbarDropdown();

        // Notify subscribers
        listeners.forEach(fn => {
            try { fn(lang); } catch (e) { console.warn("[TempoI18n] listener error:", e); }
        });

        // Update active modes if present
        if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
            window.TempoMode.renderActiveModeHome();
        }
        if (window.TempoAuth && typeof window.TempoAuth.setAuthLanguage === 'function') {
            window.TempoAuth.setAuthLanguage(lang, false);
        }
    }

    function onLanguageChange(fn) {
        if (typeof fn === 'function') {
            listeners.add(fn);
            return () => listeners.delete(fn);
        }
        return () => {};
    }

    /**
     * Centralized t(key, params, fallback)
     * e.g. t('modes.urgent.taskForNow')
     * e.g. t('modes.urgent.completedOf', { completed: 1, total: 3 })
     */
    function t(path, params = {}, fallback = '') {
        if (!path || typeof path !== 'string') return '';
        if (typeof params === 'string') {
            fallback = params;
            params = {};
        }
        const keys = path.split('.');

        // 1. Try active language
        let val = resolvePath(DICTIONARY[currentLang], keys);

        // 2. Try secondary fallback language ('en' if 'vi', 'vi' if 'en')
        if (val === null || val === undefined) {
            const secondaryLang = currentLang === 'vi' ? 'en' : 'vi';
            val = resolvePath(DICTIONARY[secondaryLang], keys);
        }

        // 3. Fallback to provided fallback string
        if (val === null || val === undefined) {
            if (fallback) {
                val = fallback;
            } else {
                // Safe dev fallback: return readable last segment rather than undefined/null
                val = keys[keys.length - 1];
            }
        }

        // Parameter interpolation: {param}
        if (typeof val === 'string') {
            return val.replace(/\{(\w+)\}/g, (match, pName) => {
                return (params && params[pName] !== undefined) ? String(params[pName]) : match;
            });
        }

        return val;
    }

    function resolvePath(obj, keys) {
        if (!obj) return null;
        let curr = obj;
        for (const k of keys) {
            if (curr && typeof curr === 'object' && k in curr) {
                curr = curr[k];
            } else {
                return null;
            }
        }
        return curr;
    }

    function formatDate(d, options) {
        const date = (d instanceof Date) ? d : new Date(d);
        if (isNaN(date.getTime())) return '';
        const locale = currentLang === 'vi' ? 'vi-VN' : 'en-US';
        return date.toLocaleDateString(locale, options);
    }

    function formatTime12H(timeStr) {
        if (!timeStr) return '';
        if (timeStr.toLowerCase().includes('am') || timeStr.toLowerCase().includes('pm')) return timeStr;
        const parts = timeStr.split(':');
        if (parts.length < 2) return timeStr;
        let h = parseInt(parts[0], 10);
        const m = parts[1];
        if (isNaN(h)) return timeStr;
        const ampm = h >= 12 ? 'PM' : 'AM';
        h = h % 12;
        if (h === 0) h = 12;
        return `${h}:${m} ${ampm}`;
    }

    function getLocalDateParts(d) {
        if (!d) return null;
        if (typeof d === 'string') {
            const clean = d.split(/[T ]/)[0].trim();
            const p = clean.split('-').map(Number);
            if (p.length === 3 && !isNaN(p[0]) && !isNaN(p[1]) && !isNaN(p[2])) {
                return { y: p[0], m: p[1], d: p[2] };
            }
        }
        const dateObj = (d instanceof Date) ? d : new Date(d);
        if (isNaN(dateObj.getTime())) return null;
        try {
            const formatter = new Intl.DateTimeFormat('en-CA', {
                timeZone: 'Asia/Ho_Chi_Minh',
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            });
            const [y, m, day] = formatter.format(dateObj).split('-').map(Number);
            return { y, m, d: day };
        } catch (e) {
            return { y: dateObj.getFullYear(), m: dateObj.getMonth() + 1, d: dateObj.getDate() };
        }
    }

    function formatCalendarDate(d, lang) {
        const targetLang = lang || currentLang || 'vi';
        const parts = getLocalDateParts(d);
        if (!parts) return '';
        const pad = n => String(n).padStart(2, '0');
        if (targetLang === 'vi') {
            // DD/MM/YYYY: e.g. 18/10/2026, 31/10/2026, 25/11/2026
            return `${pad(parts.d)}/${pad(parts.m)}/${parts.y}`;
        } else {
            // MMM DD, YYYY: e.g. Oct 18, 2026, Oct 31, 2026, Nov 25, 2026
            const enMonths = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const monthName = enMonths[parts.m - 1] || '';
            return `${monthName} ${pad(parts.d)}, ${parts.y}`;
        }
    }

    function getLocalTodayISO() {
        try {
            return new Intl.DateTimeFormat('en-CA', {
                timeZone: 'Asia/Ho_Chi_Minh',
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            }).format(new Date());
        } catch (e) {
            const d = new Date();
            const pad = n => String(n).padStart(2, '0');
            return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
        }
    }

    function getLocalTomorrowISO() {
        const todayStr = getLocalTodayISO();
        const parts = todayStr.split('-').map(Number);
        if (parts.length === 3 && !isNaN(parts[0]) && !isNaN(parts[1]) && !isNaN(parts[2])) {
            const nextDate = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2] + 1));
            const pad = n => String(n).padStart(2, '0');
            return `${nextDate.getUTCFullYear()}-${pad(nextDate.getUTCMonth() + 1)}-${pad(nextDate.getUTCDate())}`;
        }
        const d = new Date();
        d.setDate(d.getDate() + 1);
        const pad = n => String(n).padStart(2, '0');
        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    }

    function formatScheduledDateLabel(dateStr, lang) {
        if (!dateStr || typeof dateStr !== 'string') return '';
        const cleanDate = dateStr.split(/[T ]/)[0].trim();
        if (!cleanDate || cleanDate === 'unscheduled') return '';

        const targetLang = (lang === 'vi' || lang === true) ? 'vi' : ((lang === 'en' || lang === false) ? 'en' : (currentLang || 'vi'));
        const calDate = formatCalendarDate(cleanDate, targetLang);
        if (!calDate) return cleanDate;

        const todayStr = getLocalTodayISO();
        const tomorrowStr = getLocalTomorrowISO();

        if (cleanDate === todayStr) {
            return targetLang === 'vi' ? `Hôm nay · ${calDate}` : `Today · ${calDate}`;
        }
        if (cleanDate === tomorrowStr) {
            return targetLang === 'vi' ? `Ngày mai · ${calDate}` : `Tomorrow · ${calDate}`;
        }

        return calDate;
    }

    function formatDeadline(dateStr, timeStr) {
        if (!dateStr) return t('workspace.noDeadline', {}, 'No fixed deadline');
        if (dateStr.includes(' ') && !timeStr) {
            const parts = dateStr.split(' ');
            dateStr = parts[0];
            timeStr = parts[1];
        }
        try {
            const calDate = formatCalendarDate(dateStr, currentLang);
            if (!calDate) return `${dateStr}${timeStr ? ' · ' + timeStr : ''}`;
            if (timeStr) {
                return `${calDate} · ${formatTime12H(timeStr)}`;
            }
            return calDate;
        } catch (e) {
            return `${dateStr}${timeStr ? ' · ' + timeStr : ''}`;
        }
    }

    function formatTimeAgo(timeInput, lang) {
        const targetLang = (lang && SUPPORTED_LANGS.includes(lang)) ? lang : currentLang;
        const isVi = targetLang === 'vi';

        if (!timeInput) return isVi ? 'Gần đây' : 'Recent';

        if (typeof timeInput === 'string') {
            const str = timeInput.trim();
            if (/^(just now|vừa xong)$/i.test(str)) {
                return isVi ? 'Vừa xong' : 'Just now';
            }
            if (/^(recent|gần đây)$/i.test(str)) {
                return isVi ? 'Gần đây' : 'Recent';
            }

            const match = str.match(/^(\d+)\s*(hours?|hrs?|h|minutes?|mins?|m|days?|d|months?|years?|giờ|phút|ngày|tháng|năm)\s*(ago|trước)?$/i);
            if (match) {
                const count = parseInt(match[1], 10);
                const unit = match[2].toLowerCase();

                if (unit.startsWith('h') || unit.startsWith('giờ')) {
                    const s = count === 1 ? '' : 's';
                    return isVi ? `${count} giờ trước` : `${count} hour${s} ago`;
                }
                if (unit.startsWith('m') || unit.startsWith('phút')) {
                    const s = count === 1 ? '' : 's';
                    return isVi ? `${count} phút trước` : `${count} minute${s} ago`;
                }
                if (unit.startsWith('d') || unit.startsWith('ngày')) {
                    const s = count === 1 ? '' : 's';
                    return isVi ? `${count} ngày trước` : `${count} day${s} ago`;
                }
                if (unit.startsWith('tháng') || unit.startsWith('month')) {
                    const s = count === 1 ? '' : 's';
                    return isVi ? `${count} tháng trước` : `${count} month${s} ago`;
                }
                if (unit.startsWith('y') || unit.startsWith('năm')) {
                    const s = count === 1 ? '' : 's';
                    return isVi ? `${count} năm trước` : `${count} year${s} ago`;
                }
            }
        }

        let dateObj = null;
        if (timeInput instanceof Date) {
            dateObj = timeInput;
        } else if (typeof timeInput === 'number' && !isNaN(timeInput)) {
            dateObj = new Date(timeInput);
        } else if (typeof timeInput === 'string' && /^\d{4}-\d{2}-\d{2}/.test(timeInput)) {
            const parsed = new Date(timeInput);
            if (!isNaN(parsed.getTime())) {
                dateObj = parsed;
            }
        }

        if (dateObj && !isNaN(dateObj.getTime())) {
            const diffSeconds = Math.max(0, Math.floor((Date.now() - dateObj.getTime()) / 1000));
            if (diffSeconds < 60) {
                return isVi ? 'Vừa xong' : 'Just now';
            }
            const diffMinutes = Math.floor(diffSeconds / 60);
            if (diffMinutes < 60) {
                const s = diffMinutes === 1 ? '' : 's';
                return isVi ? `${diffMinutes} phút trước` : `${diffMinutes} minute${s} ago`;
            }
            const diffHours = Math.floor(diffMinutes / 60);
            if (diffHours < 24) {
                const s = diffHours === 1 ? '' : 's';
                return isVi ? `${diffHours} giờ trước` : `${diffHours} hour${s} ago`;
            }
            const diffDays = Math.floor(diffHours / 24);
            if (diffDays < 30) {
                const s = diffDays === 1 ? '' : 's';
                return isVi ? `${diffDays} ngày trước` : `${diffDays} day${s} ago`;
            }
            const diffMonths = Math.floor(diffDays / 30);
            if (diffMonths < 12) {
                const s = diffMonths === 1 ? '' : 's';
                return isVi ? `${diffMonths} tháng trước` : `${diffMonths} month${s} ago`;
            }
            const diffYears = Math.floor(diffDays / 365);
            const s = diffYears === 1 ? '' : 's';
            return isVi ? `${diffYears} năm trước` : `${diffYears} year${s} ago`;
        }

        return String(timeInput);
    }

    // -------------------------------------------------------------------------
    // NAVBAR SWITCHER & STATIC HTML UPDATER
    // -------------------------------------------------------------------------
    function updateNavbarSwitcher() {
        const wrapper = document.getElementById('nav-language-wrapper');
        if (wrapper) {
            wrapper.classList.remove('hidden');
            wrapper.style.display = '';
        }
        const btnLabel = document.getElementById('nav-current-lang-label');
        if (btnLabel) {
            btnLabel.textContent = currentLang.toUpperCase();
        }

        const flagImg = document.getElementById('nav-current-lang-flag');
        if (flagImg) {
            if (currentLang === 'vi') {
                flagImg.src = 'assets/flag-vn.png';
                flagImg.alt = 'Tiếng Việt';
            } else {
                flagImg.src = 'assets/flag-us.png';
                flagImg.alt = 'English';
            }
        }

        const checkVi = document.getElementById('lang-check-vi');
        const checkEn = document.getElementById('lang-check-en');
        if (checkVi && checkEn) {
            if (currentLang === 'vi') {
                checkVi.classList.remove('hidden');
                checkEn.classList.add('hidden');
            } else {
                checkVi.classList.add('hidden');
                checkEn.classList.remove('hidden');
            }
        }
    }

    function updateStaticHtml() {
        // Nav tabs & links
        const navTabToday = document.getElementById('nav-tab-today');
        if (navTabToday) navTabToday.textContent = t('nav.home');
        const navTabPosts = document.getElementById('nav-tab-community');
        if (navTabPosts) navTabPosts.textContent = t('nav.tempoPosts');
        const navTabVolunteer = document.getElementById('nav-tab-volunteer');
        if (navTabVolunteer) navTabVolunteer.textContent = t('nav.peerVolunteer');
        const navTabAdmin = document.getElementById('nav-tab-admin');
        if (navTabAdmin) navTabAdmin.textContent = t('nav.advisorDesk');
        const navLinkAbout = document.getElementById('nav-link-what-is-tempo');
        if (navLinkAbout) navLinkAbout.textContent = t('nav.about', {}, currentLang === 'vi' ? 'Giới thiệu' : 'About');
        const navLinkCommunity = document.getElementById('nav-link-community');
        if (navLinkCommunity) navLinkCommunity.textContent = t('nav.community', {}, currentLang === 'vi' ? 'Cộng đồng' : 'Community');
        const communityBackBtn = document.getElementById('btn-community-back');
        const communityBackLabel = document.getElementById('community-back-label');
        if (communityBackLabel) {
            communityBackLabel.textContent = currentLang === 'vi' ? 'Quay lại Dashboard' : 'Return to Dashboard';
        }
        if (communityBackBtn) {
            const commBackText = currentLang === 'vi' ? '← Quay lại Dashboard' : '← Return to Dashboard';
            communityBackBtn.setAttribute('title', commBackText);
            communityBackBtn.setAttribute('aria-label', commBackText);
        }

        // Community sidebar navigation tabs (desktop and mobile)
        const commTabLabels = {
            announcement: currentLang === 'vi' ? 'Thông báo' : 'Announcement',
            tips: 'Tips',
            learn: currentLang === 'vi' ? 'Kiến thức' : 'Learn',
            posts: currentLang === 'vi' ? 'Bài viết' : 'Posts',
            messages: currentLang === 'vi' ? 'Tin nhắn riêng' : 'Direct Message'
        };
        document.querySelectorAll('.community-nav-item, .community-mobile-tab-btn').forEach(btn => {
            const tabKey = btn.getAttribute('data-community-tab');
            if (tabKey && commTabLabels[tabKey]) {
                btn.textContent = commTabLabels[tabKey];
            }
        });

        // Community Tips
        const tipsSearchInput = document.getElementById('tips-search-input');
        if (tipsSearchInput) {
            tipsSearchInput.placeholder = currentLang === 'vi' ? 'Tìm kiếm...' : 'Search...';
        }

        // Community Learn
        const learnSearchInput = document.getElementById('learn-search-input');
        if (learnSearchInput) {
            learnSearchInput.placeholder = currentLang === 'vi' ? 'Tìm kiếm...' : 'Search...';
        }

        // Community Posts Toolbar
        const labelPostsNew = document.getElementById('label-posts-new');
        if (labelPostsNew) labelPostsNew.textContent = currentLang === 'vi' ? 'Đăng bài mới' : 'New post';
        const postsSearchInput = document.getElementById('posts-search-input');
        if (postsSearchInput) postsSearchInput.placeholder = currentLang === 'vi' ? 'Tìm kiếm...' : 'Search...';
        const labelPostsFilterMy = document.getElementById('label-posts-filter-my');
        if (labelPostsFilterMy) labelPostsFilterMy.textContent = currentLang === 'vi' ? 'Bài viết của tôi' : 'Your posts';
        const btnPostsNotif = document.getElementById('btn-posts-notifications');
        if (btnPostsNotif) {
            const notifTitle = currentLang === 'vi' ? 'Thông báo' : 'Notifications';
            btnPostsNotif.setAttribute('title', notifTitle);
            btnPostsNotif.setAttribute('aria-label', notifTitle);
        }
        const btnPostsBookmarks = document.getElementById('btn-posts-filter-bookmarks');
        if (btnPostsBookmarks) {
            const bmTitle = currentLang === 'vi' ? 'Bài viết đã lưu' : 'Saved posts';
            btnPostsBookmarks.setAttribute('title', bmTitle);
            btnPostsBookmarks.setAttribute('aria-label', bmTitle);
        }
        if (window.TempoCommunity && typeof window.TempoCommunity.updateCommunityStaticUI === 'function') {
            window.TempoCommunity.updateCommunityStaticUI();
        }
        const seeAllBtns = [
            document.getElementById('btn-see-all-posts'),
            document.getElementById('btn-see-all-posts-urgent'),
            document.getElementById('btn-see-all-posts-recovery')
        ];
        const seeAllLabel = currentLang === 'vi' ? 'Xem tất cả' : 'View all';
        const seeAllFull = currentLang === 'vi' ? 'Xem tất cả →' : 'View all →';
        seeAllBtns.forEach(btn => {
            if (btn) {
                const textSpan = btn.querySelector('span:first-child');
                if (textSpan) textSpan.textContent = seeAllLabel;
                btn.setAttribute('title', seeAllFull);
                btn.setAttribute('aria-label', seeAllFull);
            }
        });
        const commHeadings = document.querySelectorAll('[data-tempo-ui="entry-community-panel"] h3, [data-tempo-ui="urgent-community-panel"] h3, [data-tempo-ui="recovery-community-panel"] h3');
        commHeadings.forEach(h => {
            h.textContent = currentLang === 'vi' ? 'Cộng đồng Tempo' : 'From the Tempo Community';
        });
        const btnSearchToggle = document.getElementById('btn-header-search-toggle');
        if (btnSearchToggle) btnSearchToggle.title = currentLang === 'vi' ? 'Tìm kiếm trên Tempo' : 'Search Tempo';
        const btnModeTrigger = document.getElementById('btn-mode-indicator-trigger');
        if (btnModeTrigger) btnModeTrigger.title = currentLang === 'vi' ? 'Chuyển Chế độ Tempo' : 'Switch Tempo Mode';

        // Global search placeholder
        const searchInput = document.getElementById('global-search-input');
        if (searchInput) searchInput.placeholder = t('common.searchPlaceholder');

        // Auth buttons in header & avatar dropdown items
        const btnSignIn = document.getElementById('btn-header-signin');
        if (btnSignIn) btnSignIn.textContent = t('common.signIn');
        const btnRegister = document.getElementById('btn-header-register');
        if (btnRegister) btnRegister.textContent = t('common.register');
        const labelMessages = document.getElementById('label-menu-messages');
        if (labelMessages) labelMessages.textContent = t('common.directMessages');
        const labelSaved = document.getElementById('label-menu-saved');
        if (labelSaved) labelSaved.textContent = t('common.saved');
        const labelLibrary = document.getElementById('label-menu-library');
        if (labelLibrary) labelLibrary.textContent = t('common.myLibrary');
        const labelAccount = document.getElementById('label-menu-account');
        if (labelAccount) labelAccount.textContent = t('common.account');
        const labelMyData = document.getElementById('label-menu-my-data');
        if (labelMyData) labelMyData.textContent = t('common.myData');
        const labelSettings = document.getElementById('label-menu-settings');
        if (labelSettings) labelSettings.textContent = t('common.settings');
        const labelSignOut = document.getElementById('label-menu-signout');
        if (labelSignOut) {
            labelSignOut.textContent = t('common.signOut');
        } else {
            const btnSignOut = document.getElementById('btn-header-signout');
            if (btnSignOut) btnSignOut.textContent = t('common.signOut');
        }

        if (window.TempoMode && typeof window.TempoMode.updateNavbarForMode === 'function') {
            window.TempoMode.updateNavbarForMode();
        }

        // Footer
        const footerTagline = document.getElementById('footer-tagline');
        if (footerTagline) {
            footerTagline.textContent = `| ${t('footer.descriptor', {}, currentLang === 'vi' ? 'Hỗ trợ áp lực học tập & deadline' : 'Academic Stress & Deadline Triage')}`;
        }
        const footerDisclaimer = document.getElementById('footer-disclaimer-text');
        if (footerDisclaimer) {
            footerDisclaimer.textContent = t('footer.disclaimer', {}, currentLang === 'vi'
                ? 'Hỗ trợ sức khỏe tinh thần bảo mật từ cộng đồng. Không thay thế dịch vụ cấp cứu hoặc chăm sóc tâm thần chuyên môn.'
                : 'Confidential peer wellbeing support. Not a replacement for emergency or psychiatric services.');
        }
        const footerTerms = document.getElementById('footer-terms-link');
        if (footerTerms) {
            footerTerms.textContent = t('footer.terms', {}, currentLang === 'vi' ? 'Điều khoản sử dụng' : 'Terms of Service');
        }
        const footerPrivacy = document.getElementById('footer-privacy-link');
        if (footerPrivacy) {
            footerPrivacy.textContent = t('footer.privacy', {}, currentLang === 'vi' ? 'Chính sách quyền riêng tư' : 'Privacy Policy');
        }
        const footerSos = document.querySelector('footer button[onclick*="openSOS"]');
        if (footerSos) {
            footerSos.textContent = currentLang === 'vi' ? 'SOS · Hỗ trợ khẩn cấp' : (t('sos.title') || 'SOS · Immediate Support');
        }

        // SOS Modal & Human Drawer Reactive Localization
        const sosHeaderTitle = document.getElementById('sos-header-title');
        if (sosHeaderTitle) sosHeaderTitle.textContent = t('sos.title');
        const sosHeaderSubtitle = document.getElementById('sos-header-subtitle');
        if (sosHeaderSubtitle) sosHeaderSubtitle.textContent = t('sos.subtitle');
        const sosPillSupport = document.getElementById('sos-pill-get-support');
        if (sosPillSupport) sosPillSupport.textContent = t('sos.pillSupport');

        const sosSafetyHeading = document.getElementById('sos-safety-mode-active-heading');
        if (sosSafetyHeading) sosSafetyHeading.textContent = t('sos.safetyBannerHeading');
        const sosSafetyDesc = document.getElementById('sos-safety-mode-active-desc');
        if (sosSafetyDesc) sosSafetyDesc.textContent = t('sos.safetyBannerDesc');

        const sosEyebrow = document.getElementById('sos-eyebrow');
        if (sosEyebrow) sosEyebrow.textContent = t('sos.eyebrow');
        const sosMainHeading = document.getElementById('sos-main-heading');
        if (sosMainHeading) sosMainHeading.textContent = t('sos.mainHeading');

        const sosSituationIntro = document.getElementById('sos-card-situation-intro');
        if (sosSituationIntro) sosSituationIntro.textContent = t('sos.situationIntro');
        const sosSit1 = document.getElementById('sos-situation-1');
        if (sosSit1) sosSit1.textContent = t('sos.situation1');
        const sosSit2 = document.getElementById('sos-situation-2');
        if (sosSit2) sosSit2.textContent = t('sos.situation2');
        const sosSit3 = document.getElementById('sos-situation-3');
        if (sosSit3) sosSit3.textContent = t('sos.situation3');

        const sosReassTitle = document.getElementById('sos-reassurance-title');
        if (sosReassTitle) sosReassTitle.textContent = t('sos.reassuranceTitle');
        const sosReassBody = document.getElementById('sos-reassurance-body');
        if (sosReassBody) sosReassBody.textContent = t('sos.reassuranceBody');

        const sosCtaLabel = document.getElementById('sos-cta-label');
        if (sosCtaLabel) sosCtaLabel.textContent = t('sos.getSupportNow');

        const sosAltHeading = document.getElementById('sos-alt-options-heading');
        if (sosAltHeading) sosAltHeading.textContent = t('sos.altOptionsHeading');

        const sosOptABadge = document.getElementById('sos-option-a-badge');
        if (sosOptABadge) {
            if (currentLang === 'vi') {
                sosOptABadge.textContent = '';
                sosOptABadge.style.display = 'none';
            } else {
                sosOptABadge.style.display = '';
                sosOptABadge.textContent = t('sos.optionABadge');
            }
        }
        const sosOptATitle = document.getElementById('sos-option-a-title');
        if (sosOptATitle) sosOptATitle.textContent = t('sos.optionATitle');
        const sosOptADesc = document.getElementById('sos-option-a-desc');
        if (sosOptADesc) sosOptADesc.textContent = t('sos.optionADesc');

        const sosOptBBadge = document.getElementById('sos-option-b-badge');
        if (sosOptBBadge) {
            if (currentLang === 'vi') {
                sosOptBBadge.textContent = '';
                sosOptBBadge.style.display = 'none';
            } else {
                sosOptBBadge.style.display = '';
                sosOptBBadge.textContent = t('sos.optionBBadge');
            }
        }
        const sosOptBTitle = document.getElementById('sos-option-b-title');
        if (sosOptBTitle) sosOptBTitle.textContent = t('sos.optionBTitle');
        const sosOptBDesc = document.getElementById('sos-option-b-desc');
        if (sosOptBDesc) sosOptBDesc.textContent = t('sos.optionBDesc');

        const sosOptCBadge = document.getElementById('sos-option-c-badge');
        if (sosOptCBadge) {
            if (currentLang === 'vi') {
                sosOptCBadge.textContent = '';
                sosOptCBadge.style.display = 'none';
            } else {
                sosOptCBadge.style.display = '';
                sosOptCBadge.textContent = t('sos.optionCBadge');
            }
        }
        const sosOptCTitle = document.getElementById('sos-option-c-title');
        if (sosOptCTitle) sosOptCTitle.textContent = t('sos.optionCTitle');
        const sosOptCDesc = document.getElementById('sos-option-c-desc');
        if (sosOptCDesc) sosOptCDesc.textContent = t('sos.optionCDesc');

        const sosOptDLabel = document.getElementById('sos-option-d-label');
        if (sosOptDLabel) sosOptDLabel.textContent = t('sos.optionDLabel');

        const btnCloseEmergency = document.getElementById('btn-close-emergency-flow');
        if (btnCloseEmergency) {
            const closeText = currentLang === 'vi' ? 'Đóng cửa sổ hỗ trợ' : 'Close dialog';
            btnCloseEmergency.setAttribute('aria-label', closeText);
            btnCloseEmergency.setAttribute('title', closeText);
        }

        // Support Drawer Reactive Texts
        const drawerTitle = document.getElementById('drawer-title');
        if (drawerTitle) drawerTitle.textContent = t('sos.drawerTitle');
        const drawerSubtitle = document.getElementById('drawer-subtitle');
        if (drawerSubtitle) drawerSubtitle.textContent = t('sos.drawerSubtitle');
        const drawerSubtitleDesc = document.getElementById('drawer-subtitle-desc');
        if (drawerSubtitleDesc) drawerSubtitleDesc.textContent = t('sos.drawerSubtitleDesc');

        const drawerMedTitle = document.getElementById('drawer-medical-title');
        if (drawerMedTitle) drawerMedTitle.textContent = t('sos.medicalTitle');
        const drawerMedBadge = document.getElementById('drawer-medical-badge');
        if (drawerMedBadge) drawerMedBadge.textContent = t('sos.medicalBadge');
        const drawerMedDesc = document.getElementById('drawer-medical-desc');
        if (drawerMedDesc) drawerMedDesc.textContent = t('sos.medicalDesc');
        const drawerMedCall = document.getElementById('drawer-medical-call');
        if (drawerMedCall) drawerMedCall.textContent = t('sos.medicalCall');

        const drawerHotlineTitle = document.getElementById('drawer-hotline-title');
        if (drawerHotlineTitle) drawerHotlineTitle.textContent = t('sos.hotlineTitle');
        const drawerHotlineBadge = document.getElementById('drawer-hotline-badge');
        if (drawerHotlineBadge) drawerHotlineBadge.textContent = t('sos.hotlineBadge');
        const drawerHotlineDesc = document.getElementById('drawer-hotline-desc');
        if (drawerHotlineDesc) drawerHotlineDesc.textContent = t('sos.hotlineDesc');
        const drawerHotlineCall = document.getElementById('drawer-hotline-call');
        if (drawerHotlineCall) drawerHotlineCall.textContent = t('sos.hotlineCall');

        const drawerNgayMaiTitle = document.getElementById('drawer-ngaymai-title');
        if (drawerNgayMaiTitle) drawerNgayMaiTitle.textContent = t('sos.ngayMaiTitle');
        const drawerNgayMaiBadge = document.getElementById('drawer-ngaymai-badge');
        if (drawerNgayMaiBadge) drawerNgayMaiBadge.textContent = t('sos.ngayMaiBadge');
        const drawerNgayMaiDesc = document.getElementById('drawer-ngaymai-desc');
        if (drawerNgayMaiDesc) drawerNgayMaiDesc.textContent = t('sos.ngayMaiDesc');
        const drawerNgayMaiHours = document.getElementById('drawer-ngaymai-hours');
        if (drawerNgayMaiHours) drawerNgayMaiHours.textContent = t('sos.ngayMaiHours');
        const drawerNgayMaiCall = document.getElementById('drawer-ngaymai-call');
        if (drawerNgayMaiCall) drawerNgayMaiCall.textContent = t('sos.ngayMaiCall');

        const step5aNgayMaiTitle = document.getElementById('step5a-ngaymai-title');
        if (step5aNgayMaiTitle) step5aNgayMaiTitle.textContent = t('sos.ngayMaiTitle');
        const step5aNgayMaiBadge = document.getElementById('step5a-ngaymai-badge');
        if (step5aNgayMaiBadge) step5aNgayMaiBadge.textContent = t('sos.ngayMaiBadge');
        const step5aNgayMaiDesc = document.getElementById('step5a-ngaymai-desc');
        if (step5aNgayMaiDesc) step5aNgayMaiDesc.textContent = t('sos.ngayMaiDesc');
        const step5aNgayMaiHours = document.getElementById('step5a-ngaymai-hours');
        if (step5aNgayMaiHours) step5aNgayMaiHours.textContent = t('sos.ngayMaiHours');
        const step5aNgayMaiCall = document.getElementById('step5a-ngaymai-call');
        if (step5aNgayMaiCall) step5aNgayMaiCall.textContent = t('sos.ngayMaiCall');

        const drawerWaitHeader = document.getElementById('drawer-waiting-header');
        if (drawerWaitHeader) drawerWaitHeader.textContent = t('sos.waitingHeader');
        const drawerWait1 = document.getElementById('drawer-waiting-action-1');
        if (drawerWait1) drawerWait1.textContent = t('sos.action1');
        const drawerWait2 = document.getElementById('drawer-waiting-action-2');
        if (drawerWait2) drawerWait2.textContent = t('sos.action2');
        const drawerWait3 = document.getElementById('drawer-waiting-action-3');
        if (drawerWait3) drawerWait3.textContent = t('sos.action3');
        const drawerWaitReassTitle = document.getElementById('drawer-waiting-reass-title');
        if (drawerWaitReassTitle) drawerWaitReassTitle.textContent = t('sos.waitingReassTitle');
        const drawerWaitReass = document.getElementById('drawer-waiting-reassurance');
        if (drawerWaitReass) drawerWaitReass.textContent = t('sos.reassurance');

        // Step 5A waiting guidance
        const step5aWaitHeader = document.getElementById('step5a-waiting-header');
        if (step5aWaitHeader) step5aWaitHeader.textContent = t('sos.waitingHeader');
        const step5aWait1 = document.getElementById('step5a-waiting-action-1');
        if (step5aWait1) step5aWait1.textContent = t('sos.action1');
        const step5aWait2 = document.getElementById('step5a-waiting-action-2');
        if (step5aWait2) step5aWait2.textContent = t('sos.action2');
        const step5aWait3 = document.getElementById('step5a-waiting-action-3');
        if (step5aWait3) step5aWait3.textContent = t('sos.action3');
        const step5aWaitReassTitle = document.getElementById('step5a-waiting-reass-title');
        if (step5aWaitReassTitle) step5aWaitReassTitle.textContent = t('sos.waitingReassTitle');
        const step5aWaitReass = document.getElementById('step5a-waiting-reassurance');
        if (step5aWaitReass) step5aWaitReass.textContent = t('sos.reassurance');

        // Trusted Contact Card
        const drawerTrustedTitle = document.getElementById('drawer-trusted-title');
        if (drawerTrustedTitle) drawerTrustedTitle.textContent = t('sos.trustedTitle');
        const drawerTrustedDesc = document.getElementById('drawer-trusted-desc');
        if (drawerTrustedDesc) drawerTrustedDesc.textContent = t('sos.trustedDesc');
        const drawerCopyBtn = document.getElementById('drawer-copy-btn-text');
        if (drawerCopyBtn) drawerCopyBtn.textContent = t('sos.copyTrustedBtn');
        const drawerQuote = document.getElementById('drawer-trusted-quote');
        if (drawerQuote) {
            drawerQuote.textContent = '"' + t('sos.trustedQuote') + '"';
        }

        // Campus Student Wellbeing Card & FPT Counseling Office
        const drawerCampusTitle = document.getElementById('drawer-campus-title');
        if (drawerCampusTitle) drawerCampusTitle.textContent = t('sos.campusTitle');
        const drawerCampusBadge = document.getElementById('drawer-campus-badge');
        if (drawerCampusBadge) drawerCampusBadge.textContent = t('sos.campusBadge');
        const drawerCampusDesc = document.getElementById('drawer-campus-desc');
        if (drawerCampusDesc) {
            drawerCampusDesc.innerHTML = currentLang === 'vi'
                ? 'Trong trường hợp khẩn cấp hoặc nguy hiểm tức thời, hãy gọi <strong>115</strong> hoặc <strong>0865 044 400</strong>. Nếu bạn cần trao đổi về các vấn đề tâm lý không khẩn cấp, bạn có thể liên hệ với bộ phận hỗ trợ sinh viên trong giờ làm việc.'
                : 'For immediate crisis or danger, call <strong>115</strong> or <strong>0865 044 400</strong>. For non-urgent campus advising questions during office hours:';
        }

        const drawerFptTitle = document.getElementById('drawer-fpt-title');
        if (drawerFptTitle) drawerFptTitle.textContent = t('sos.fptTitle');
        const drawerFptDesc = document.getElementById('drawer-fpt-desc');
        if (drawerFptDesc) drawerFptDesc.textContent = t('sos.fptDesc');
        const drawerFptCtaText = document.getElementById('drawer-fpt-cta-text');
        if (drawerFptCtaText) drawerFptCtaText.textContent = t('sos.fptCta');

        const drawerOfflineContact = document.getElementById('drawer-offline-contact');
        if (drawerOfflineContact) drawerOfflineContact.setAttribute('placeholder', t('sos.offlineContactPlaceholder'));
        const drawerOfflineMessage = document.getElementById('drawer-offline-message');
        if (drawerOfflineMessage) drawerOfflineMessage.setAttribute('placeholder', t('sos.offlineMsgPlaceholder'));
        const drawerOfflineBtnText = document.getElementById('drawer-offline-btn-text');
        if (drawerOfflineBtnText) drawerOfflineBtnText.textContent = t('sos.offlineSubmitBtn');
        const drawerOfflineSuccess = document.getElementById('drawer-offline-success');
        if (drawerOfflineSuccess) drawerOfflineSuccess.textContent = t('sos.offlineSuccessMsg');

        // Step 5A Campus & FPT
        const step5aCampusTitle = document.getElementById('step5a-campus-title');
        if (step5aCampusTitle) step5aCampusTitle.textContent = t('sos.campusTitle');
        const step5aCampusBadge = document.getElementById('step5a-campus-badge');
        if (step5aCampusBadge) step5aCampusBadge.textContent = t('sos.campusBadge');
        const step5aCampusDesc = document.getElementById('step5a-campus-desc');
        if (step5aCampusDesc) {
            step5aCampusDesc.innerHTML = currentLang === 'vi'
                ? 'Trong trường hợp khẩn cấp hoặc nguy hiểm tức thời, hãy gọi <strong>115</strong> hoặc <strong>0865 044 400</strong>. Nếu bạn cần trao đổi về các vấn đề tâm lý không khẩn cấp, bạn có thể liên hệ với bộ phận hỗ trợ sinh viên trong giờ làm việc.'
                : 'For immediate crisis or danger, call <strong>115</strong> or <strong>0865 044 400</strong>. For non-urgent campus advising questions during office hours:';
        }

        const step5aFptTitle = document.getElementById('step5a-fpt-title');
        if (step5aFptTitle) step5aFptTitle.textContent = t('sos.fptTitle');
        const step5aFptDesc = document.getElementById('step5a-fpt-desc');
        if (step5aFptDesc) step5aFptDesc.textContent = t('sos.fptDesc');
        const step5aFptCtaText = document.getElementById('step5a-fpt-cta-text');
        if (step5aFptCtaText) step5aFptCtaText.textContent = t('sos.fptCta');

        const step5aOfflineContact = document.getElementById('step5a-offline-contact');
        if (step5aOfflineContact) step5aOfflineContact.setAttribute('placeholder', t('sos.offlineContactPlaceholder'));
        const step5aOfflineMessage = document.getElementById('step5a-offline-message');
        if (step5aOfflineMessage) step5aOfflineMessage.setAttribute('placeholder', t('sos.offlineMsgPlaceholder'));
        const step5aOfflineBtnText = document.getElementById('step5a-offline-btn-text');
        if (step5aOfflineBtnText) step5aOfflineBtnText.textContent = t('sos.offlineSubmitBtn');
        const step5aOfflineSuccess = document.getElementById('step5a-offline-success');
        if (step5aOfflineSuccess) step5aOfflineSuccess.textContent = t('sos.offlineSuccessMsg');

        const drawerCloseBtn = document.getElementById('drawer-close-btn-text');
        if (drawerCloseBtn) drawerCloseBtn.textContent = t('sos.closeSOS');

        // Routing modal (Find Your Next Step)
        const routingEyebrow = document.getElementById('routing-modal-eyebrow');
        if (routingEyebrow) routingEyebrow.textContent = t('routing.eyebrow');
        const routingTitle = document.getElementById('routing-modal-title');
        if (routingTitle) routingTitle.textContent = t('routing.title');
        const routingDesc = document.getElementById('routing-modal-desc');
        if (routingDesc) routingDesc.textContent = t('routing.desc');

        const btnCloseRouting = document.getElementById('btn-close-routing-modal');
        if (btnCloseRouting) {
            const closeText = currentLang === 'vi' ? 'Đóng' : 'Close dialog';
            btnCloseRouting.setAttribute('aria-label', closeText);
            btnCloseRouting.setAttribute('title', closeText);
        }

        const badgeUrgent = document.getElementById('routing-card-urgent-badge');
        if (badgeUrgent) badgeUrgent.textContent = t('routing.urgent.badge');
        const titleUrgent = document.getElementById('routing-card-urgent-title');
        if (titleUrgent) titleUrgent.textContent = t('routing.urgent.title');
        const descUrgent = document.getElementById('routing-card-urgent-desc');
        if (descUrgent) descUrgent.textContent = t('routing.urgent.desc');
        const ctaUrgent = document.getElementById('routing-card-urgent-cta');
        if (ctaUrgent) ctaUrgent.textContent = t('routing.urgent.cta');

        const badgeRecovery = document.getElementById('routing-card-recovery-badge');
        if (badgeRecovery) badgeRecovery.textContent = t('routing.recovery.badge');
        const titleRecovery = document.getElementById('routing-card-recovery-title');
        if (titleRecovery) titleRecovery.textContent = t('routing.recovery.title');
        const descRecovery = document.getElementById('routing-card-recovery-desc');
        if (descRecovery) descRecovery.textContent = t('routing.recovery.desc');
        const ctaRecovery = document.getElementById('routing-card-recovery-cta');
        if (ctaRecovery) ctaRecovery.textContent = t('routing.recovery.cta');

        const badgeUnclear = document.getElementById('routing-card-unclear-badge');
        if (badgeUnclear) badgeUnclear.textContent = t('routing.unclear.badge');
        const titleUnclear = document.getElementById('routing-card-unclear-title');
        if (titleUnclear) titleUnclear.textContent = t('routing.unclear.title');
        const descUnclear = document.getElementById('routing-card-unclear-desc');
        if (descUnclear) descUnclear.textContent = t('routing.unclear.desc');
        const ctaUnclear = document.getElementById('routing-card-unclear-cta');
        if (ctaUnclear) ctaUnclear.textContent = t('routing.unclear.cta');

        const badgeSupport = document.getElementById('routing-card-support-badge');
        if (badgeSupport) badgeSupport.textContent = t('routing.support.badge');
        const titleSupport = document.getElementById('routing-card-support-title');
        if (titleSupport) titleSupport.textContent = t('routing.support.title');
        const descSupport = document.getElementById('routing-card-support-desc');
        if (descSupport) descSupport.textContent = t('routing.support.desc');
        const ctaSupport = document.getElementById('routing-card-support-cta');
        if (ctaSupport) ctaSupport.textContent = t('routing.support.cta');

        updateAboutPageStaticHtml();
    }

    function updateAboutPageStaticHtml() {
        const setEl = (id, text) => {
            const el = document.getElementById(id);
            if (el && text !== undefined && text !== null) {
                el.textContent = text;
            }
        };

        // 1. Hero Section
        setEl('about-hero-badge', t('about.heroBadge'));
        setEl('about-hero-title', t('about.heroTitle'));
        setEl('about-hero-desc', t('about.heroDesc'));
        setEl('about-hero-cta-text', t('about.heroCta'));
        setEl('about-preview-badge', t('about.previewBadge'));
        setEl('about-card1-title', t('about.card1Title'));
        setEl('about-card1-badge', t('about.card1Badge'));
        setEl('about-card1-desc', t('about.card1Desc'));
        setEl('about-card2-title', t('about.card2Title'));
        setEl('about-card2-badge', t('about.card2Badge'));
        setEl('about-card2-desc', t('about.card2Desc'));
        setEl('about-card3-title', t('about.card3Title'));
        setEl('about-card3-badge', t('about.card3Badge'));
        setEl('about-card3-desc', t('about.card3Desc'));
        setEl('about-preview-footer', t('about.previewFooter'));

        // 2. When Things Feel Like Too Much
        setEl('about-s02-eyebrow', t('about.s02Eyebrow'));
        setEl('about-s02-title', t('about.s02Title'));
        setEl('about-s02-desc', t('about.s02Desc'));

        // Scenario 1
        setEl('about-s02-c1-eyebrow', t('about.s02C1Eyebrow'));
        setEl('about-s02-c1-title', t('about.s02C1Title'));
        setEl('about-s02-c1-desc', t('about.s02C1Desc'));
        setEl('about-s02-c1-help-eyebrow', t('about.s02C1HelpEyebrow'));
        setEl('about-s02-c1-help-title', t('about.s02C1HelpTitle'));
        setEl('about-s02-c1-help-desc', t('about.s02C1HelpDesc'));

        // Scenario 2
        setEl('about-s02-c2-eyebrow', t('about.s02C2Eyebrow'));
        setEl('about-s02-c2-title', t('about.s02C2Title'));
        setEl('about-s02-c2-desc', t('about.s02C2Desc'));
        setEl('about-s02-c2-help-eyebrow', t('about.s02C2HelpEyebrow'));
        setEl('about-s02-c2-help-title', t('about.s02C2HelpTitle'));
        setEl('about-s02-c2-help-desc', t('about.s02C2HelpDesc'));

        // Scenario 3
        setEl('about-s02-c3-eyebrow', t('about.s02C3Eyebrow'));
        setEl('about-s02-c3-title', t('about.s02C3Title'));
        setEl('about-s02-c3-desc', t('about.s02C3Desc'));
        setEl('about-s02-c3-help-eyebrow', t('about.s02C3HelpEyebrow'));
        setEl('about-s02-c3-help-title', t('about.s02C3HelpTitle'));
        setEl('about-s02-c3-help-desc', t('about.s02C3HelpDesc'));

        // 3. Explore Tempo
        setEl('about-s03-eyebrow', t('about.s03Eyebrow'));
        setEl('about-s03-title', t('about.s03Title'));
        setEl('about-s03-desc', t('about.s03Desc'));

        // 3.1 Modes & SOS
        setEl('about-modes-eyebrow', t('about.modesEyebrow'));
        setEl('about-modes-title', t('about.modesTitle'));
        setEl('about-modes-subtitle', t('about.modesSubtitle'));
        setEl('about-modes-desc', t('about.modesDesc'));
        setEl('about-mode-urgent', t('about.modeUrgent'));
        setEl('about-mode-recovery', t('about.modeRecovery'));
        setEl('about-mode-unclear', t('about.modeUnclear'));
        setEl('about-sos-title', t('about.sosTitle'));
        setEl('about-sos-flow', t('about.sosFlow'));
        setEl('about-sos-note', t('about.sosNote'));

        // 3.2 Personal Tools
        setEl('about-tools-eyebrow', t('about.toolsEyebrow'));
        setEl('about-tools-title', t('about.toolsTitle'));
        setEl('about-tools-subtitle', t('about.toolsSubtitle'));
        setEl('about-tools-desc', t('about.toolsDesc'));
        setEl('about-tool-focus-zone', t('about.toolFocusZone'));
        setEl('about-tool-working-plan', t('about.toolWorkingPlan'));
        setEl('about-tool-self-check', t('about.toolSelfCheck'));
        setEl('about-tool-breathing', t('about.toolBreathing'));
        setEl('about-tool-notes', t('about.toolNotes'));

        // 3.3 Quick Relief & Learning
        setEl('about-relief-eyebrow', t('about.reliefEyebrow'));
        setEl('about-relief-title', t('about.reliefTitle'));
        setEl('about-relief-subtitle', t('about.reliefSubtitle'));
        setEl('about-relief-desc', t('about.reliefDesc'));
        setEl('about-relief-c1-title', t('about.reliefCard1Title'));
        setEl('about-relief-c1-desc', t('about.reliefCard1Desc'));
        setEl('about-relief-c2-title', t('about.reliefCard2Title'));
        setEl('about-relief-c2-desc', t('about.reliefCard2Desc'));

        // 3.4 Community
        setEl('about-comm-eyebrow', t('about.communityEyebrow'));
        setEl('about-comm-title', t('about.communityTitle'));
        setEl('about-comm-subtitle', t('about.communitySubtitle'));
        setEl('about-comm-desc', t('about.communityDesc'));
        setEl('about-comm-c1-title', t('about.communityCard1Title'));
        setEl('about-comm-c1-desc', t('about.communityCard1Desc'));
        setEl('about-comm-c2-title', t('about.communityCard2Title'));
        setEl('about-comm-c2-desc', t('about.communityCard2Desc'));

        // 4. Your Journey, Your Pace
        setEl('about-s04-eyebrow', t('about.s04Eyebrow'));
        setEl('about-s04-title', t('about.s04Title'));
        setEl('about-s04-desc', t('about.s04Desc'));
        setEl('about-step1-title', t('about.step1Title'));
        setEl('about-step1-desc', t('about.step1Desc'));
        setEl('about-step2-title', t('about.step2Title'));
        setEl('about-step2-desc', t('about.step2Desc'));
        setEl('about-step3-title', t('about.step3Title'));
        setEl('about-step3-desc', t('about.step3Desc'));

        // 5. Final CTA
        setEl('about-s05-eyebrow', t('about.s05Eyebrow'));
        setEl('about-s05-title', t('about.s05Title'));
        setEl('about-s05-desc', t('about.s05Desc'));
        setEl('about-s05-cta-text', t('about.s05Cta'));

        // Urgent Mode Emergency Flow Header
        setEl('em-header-back-home', currentLang === 'vi' ? 'Về trang chủ' : 'Back to Home');
        setEl('em-header-sos-label', currentLang === 'vi' ? 'Hỗ trợ SOS' : 'SOS Support');
        setEl('em-phase-reset', currentLang === 'vi' ? 'THƯ GIÃN' : 'RESET');
        setEl('em-phase-organize', currentLang === 'vi' ? 'SẮP XẾP' : 'ORGANIZE');
        setEl('em-phase-plan', currentLang === 'vi' ? 'LÊN KẾ HOẠCH' : 'PLAN');
        setEl('em-phase-ready', currentLang === 'vi' ? 'SẴN SÀNG' : 'READY');

        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.onLanguageChange === 'function') {
            window.TempoEmergencyFlow.onLanguageChange(currentLang);
        }

        if (window.TempoTheme && typeof window.TempoTheme.syncSettingsUI === 'function') {
            window.TempoTheme.syncSettingsUI();
        }
    }

    function toggleNavbarDropdown(e) {
        if (e) {
            e.stopPropagation();
            e.preventDefault();
        }
        const dropdown = document.getElementById('nav-language-dropdown');
        if (!dropdown) return;
        dropdown.classList.toggle('hidden');
    }

    function closeNavbarDropdown() {
        const dropdown = document.getElementById('nav-language-dropdown');
        if (dropdown && !dropdown.classList.contains('hidden')) {
            dropdown.classList.add('hidden');
        }
    }

    function initNavbarSwitcher() {
        const btn = document.getElementById('nav-btn-language');
        if (btn) {
            btn.onclick = toggleNavbarDropdown;
        }

        document.addEventListener('click', (e) => {
            if (!e.target.closest('#nav-language-wrapper')) {
                closeNavbarDropdown();
            }
        });

        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeNavbarDropdown();
            }
        });

        updateNavbarSwitcher();
        updateStaticHtml();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNavbarSwitcher);
    } else {
        initNavbarSwitcher();
    }

    // -------------------------------------------------------------------------
    // EXPORTS
    // -------------------------------------------------------------------------
    window.TempoI18n = {
        getLanguage,
        setLanguage,
        t,
        onLanguageChange,
        subscribe: onLanguageChange,
        formatDate,
        formatCalendarDate,
        formatScheduledDateLabel,
        getLocalTodayISO,
        getLocalTomorrowISO,
        formatTime12H,
        formatDeadline,
        formatTimeAgo,
        toggleNavbarDropdown,
        closeNavbarDropdown,
        updateStaticHtml,
        updateAboutPageStaticHtml,
        DICTIONARY
    };

    // Global shorthand helper
    window.t = (path, params, fallback) => t(path, params, fallback);

})();
