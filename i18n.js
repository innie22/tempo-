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
                register: "Đăng ký",
                signOut: "Đăng xuất",
                loading: "Đang tải...",
                user: "Người dùng",
                notEstimated: "Chưa ước tính",
                date: "Ngày",
                time: "Giờ",
                from: "Từ",
                to: "Đến"
            },
            nav: {
                home: "Trang chủ",
                tempoPosts: "Tempo Posts",
                peerVolunteer: "Hỗ trợ tình nguyện",
                advisorDesk: "Bàn Cố vấn",
                sos: "SOS",
                language: "Ngôn ngữ",
                search: "Tìm kiếm",
                currentLang: "VI"
            },
            modes: {
                default: {
                    name: "Tempo",
                    greeting: "Chào {name} 👋",
                    greetingFallback: "Chào bạn 👋",
                    welcomeEyebrow: "CHÀO MỪNG ĐẾN TEMPO",
                    whatDoYouNeed: "Lúc này bạn cần gì?",
                    explainCopy: "Bạn không cần tự tìm cách một mình. Hãy cho Tempo biết tình huống hiện tại, mình sẽ cùng bạn tìm bước tiếp theo.",
                    helpMeStart: "Giúp tôi tìm điểm bắt đầu",
                    takesLessOneMin: "Chưa đến 1 phút",
                    personalizedGuidance: "Hướng dẫn phù hợp với bạn",
                    fromCommunity: "Từ cộng đồng Tempo",
                    seeAll: "Xem tất cả",
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
                    addTask: "+ Thêm công việc",
                    flexible: "Linh hoạt",
                    continue: "Tiếp tục",
                    focus: "Tập trung",
                    steps: "bước",
                    todayComplete: "Bạn đã hoàn thành xong kế hoạch của hôm nay.",
                    needDifferentSupport: "Bạn cần dạng hỗ trợ khác?",
                    chooseMode: "Chọn chế độ"
                },
                urgent: {
                    name: "Chế độ Khẩn",
                    shortName: "Khẩn cấp",
                    tagline: "Xử lý hạn chót gấp & giải tỏa áp lực tức thì",
                    taskForNow: "VIỆC CẦN LÀM NGAY",
                    taskForNowDesc: "Mình xử lý việc gấp trước nhé. Từng bước nhỏ một sẽ ổn thôi.",
                    due: "Hạn chót:",
                    est: "Dự tính:",
                    actionSteps: "bước hành động",
                    focusOnTask: "Tập trung vào việc này →",
                    viewTask: "Xem công việc →",
                    planForToday: "Kế hoạch hôm nay",
                    planForTodayUpper: "KẾ HOẠCH HÔM NAY",
                    yourUrgentPlanUpper: "KẾ HOẠCH KHẨN CỦA BẠN",
                    completedOf: "{completed}/{total} đã hoàn thành",
                    viewPlan: "Xem kế hoạch →",
                    viewEditPlan: "Xem / Chỉnh sửa kế hoạch",
                    editPlan: "Chỉnh sửa kế hoạch",
                    completed: "ĐÃ XONG",
                    completedBadge: "Đã xong",
                    now: "ĐANG LÀM",
                    upNext: "TIẾP THEO",
                    overwhelmed: "Cảm thấy quá tải?",
                    overwhelmedDesc: "Dành 2 phút thở sâu hoặc giải tỏa căng thẳng trước khi làm tiếp.",
                    quickStressRelief: "Giảm căng thẳng nhanh",
                    breathing: "Bài tập thở",
                    focusNow: "Tập trung ngay",
                    focusNowDesc: "Bắt đầu phiên tập trung tính giờ để bảo vệ đà làm việc.",
                    startFocus: "Bắt đầu tập trung →",
                    statePlanIncomplete: "Bạn vẫn đang thiết lập kế hoạch của mình.",
                    statePlanIncompleteDesc: "Bạn vẫn đang trong quá trình thiết lập kế hoạch.",
                    continueBuilding: "Tiếp tục tạo kế hoạch của tôi",
                    stateTodayComplete: "Bạn đã hoàn thành công việc hôm nay.",
                    stateTodayCompleteDesc: "Nghỉ ngơi để nạp lại năng lượng nhé. Công việc ngày mai cứ để ngày mai.",
                    todaysWorkDone: "ĐÃ XONG VIỆC HÔM NAY",
                    nextScheduledWork: "Công việc tiếp theo được lên lịch vào ngày mai.",
                    stateNoWork: "Hôm nay không có việc cần làm.",
                    stateNoWorkDesc: "Bạn có thể nghỉ ngơi, xem lại kế hoạch hoặc bắt đầu một phiên tập trung tự do.",
                    stateTimeEnded: "Đã hết thời gian theo kế hoạch.",
                    stateTimeEndedDesc: "Bạn đã nỗ lực rất nhiều hôm nay. Những việc còn lại có thể điều chỉnh sang ngày mai.",
                    statePlanStale: "Kế hoạch của bạn cần được cập nhật.",
                    statePlanStaleDesc: "Một số công việc đã quá thời gian dự kiến. Hãy cập nhật lại lịch trình để tiếp tục nhé.",
                    updateSchedule: "Cập nhật lịch trình",
                    statePlanComplete: "Kế hoạch Khẩn của bạn đã hoàn thành.",
                    statePlanCompleteDesc: "Tất cả các việc trong kế hoạch đã xong. Hãy tự thưởng cho bản thân một khoảng nghỉ nhé.",
                    shiftToRecovery: "Chuyển sang Chế độ Hồi phục",
                    stayInUrgent: "Ở lại Chế độ Khẩn",
                    taskCompletedToast: "Đã hoàn thành công việc! Từng bước nhỏ giúp giữ vững đà làm việc."
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
                    recoveryNote: "GHI CHÚ HỒI PHỤC",
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
                    posts: "Tempo Posts"
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
                    goToUrgent: "Đến Chế độ Khẩn",
                    goToRecovery: "Đến Chế độ Hồi phục",
                    returnToTempo: "Trở về Tempo",
                    exploreSupport: "Tìm kiếm sự hỗ trợ",
                    stayUnclear: "Ở lại Chế độ Chưa rõ lúc này",
                    whatOnMind: "Điều gì đang quanh quẩn trong tâm trí bạn?",
                    whatHeaviest: "Điều gì đang tạo áp lực lớn nhất lúc này?",
                    whatNoticed: "Bạn nhận thấy cơ thể hoặc tâm trạng mình gần đây thế nào?",
                    whatNeedNow: "Lúc này bạn cần gì nhất?"
                },
                selector: {
                    switchMode: "Chuyển chế độ",
                    takeBreak: "Tạm nghỉ các chế độ",
                    takeBreakDesc: "Trở về trải nghiệm Tempo mặc định",
                    activeBadge: "Đang bật"
                }
            },
            workspace: {
                title: "Không gian Kế hoạch",
                home: "Trang chủ",
                returnToHome: "Trở về Trang chủ",
                focus: "Tập trung",
                startFocus: "Bắt đầu tập trung",
                timeline: "Lịch trình thực hiện",
                unscheduled: "Chưa lên lịch",
                notScheduledYet: "CHƯA LÊN LỊCH",
                addTask: "+ Thêm công việc",
                taskDetails: "Chi tiết công việc",
                scheduledFor: "Đã lên lịch:",
                deadline: "Hạn chót:",
                editDeadline: "Sửa hạn chót",
                noDeadline: "Không có hạn chót",
                duration: "Thời lượng:",
                editEstimate: "Sửa thời lượng",
                actionSteps: "Các bước hành động",
                addSubtask: "+ Thêm bước nhỏ",
                subtaskPlaceholder: "Nhập bước hành động nhỏ tiếp theo...",
                markCompleted: "Đánh dấu hoàn thành",
                markIncomplete: "Đánh dấu chưa xong",
                deleteTask: "Xóa công việc",
                doThis: "LÀM VIỆC NÀY",
                then: "SAU ĐÓ",
                later: "SAU NỮA",
                noPlanTitle: "Không tìm thấy Kế hoạch Khẩn đang hoạt động",
                noPlanDesc: "Hiện tại bạn chưa có Kế hoạch Khẩn nào đang hoạt động. Hãy tạo kế hoạch để nhận được chỉ dẫn rõ ràng, thực tế.",
                createUrgentPlan: "Tạo Kế hoạch Khẩn →",
                headerSubtitle: "Đây là những việc bạn đang xử lý lúc này.",
                durationSummary: "~{duration} thời gian tập trung{unestimated}",
                unestimatedCount: " (+{count} chưa ước tính)",
                tasksCount: "{count} công việc",
                completedCount: "đã hoàn thành",
                startFocusNow: "Bắt đầu tập trung ngay",
                adjustAvailability: "Điều chỉnh thời gian rảnh",
                allPlannedWorkDone: "Đã xong tất cả việc đã lên lịch ✓",
                activeTasksCount: "{count} việc đang làm",
                estimate: "Dự tính:",
                due: "Hạn chót:",
                mayFinishAfterDeadline: "Có thể hoàn thành sau hạn chót",
                completed: "Đã hoàn thành",
                inProgress: "Đang làm",
                notStarted: "Chưa bắt đầu",
                start: "Bắt đầu",
                continueFocus: "Tiếp tục tập trung",
                addAnotherTask: "+ Thêm công việc khác vào kế hoạch này",
                allActiveScheduled: "Tất cả công việc đã được xếp vào lịch của bạn.",
                scheduleTask: "Xếp lịch công việc →",
                undo: "Hoàn tác",
                editTask: "Chỉnh sửa công việc",
                scheduledUpper: "LỊCH THỰC HIỆN",
                reschedule: "Xếp lại lịch",
                deadlineUpper: "HẠN CHÓT",
                noFixedDeadline: "Không có hạn chót cố định",
                saveDeadline: "Lưu hạn chót",
                estimateUpper: "DỰ TÍNH",
                flexibleFocusedWork: "Thời gian tập trung linh hoạt",
                actionStepsUpper: "CÁC BƯỚC HÀNH ĐỘNG",
                addNextStep: "Thêm bước tiếp theo...",
                add: "+ Thêm",
                startFocusOnTask: "▶ Bắt đầu tập trung vào việc này",
                removeFromPlan: "Xóa khỏi kế hoạch",
                addTaskModalTitle: "Thêm công việc",
                taskName: "Tên công việc",
                taskNamePlaceholder: "VD: Đọc tài liệu tham khảo",
                focusedEstimate: "Dự tính thời gian tập trung",
                notSureYet: "Chưa chắc chắn",
                addTaskBtn: "Thêm công việc",
                taskAdded: "Đã thêm công việc",
                taskReadyDesc: "\"{name}\" đã sẵn sàng.",
                fitIntoPlan: "Xếp vào kế hoạch của tôi",
                leaveUnscheduled: "Để chưa lên lịch lúc này",
                rescheduleTaskModalTitle: "Xếp lại lịch công việc",
                yourAvailableTime: "THỜI GIAN RẢNH CỦA BẠN",
                noTimeBlocks: "Chưa có khung giờ nào",
                figureOutLater: "Sắp xếp sau (Chuyển vào Chưa lên lịch)",
                schedule: "Lên lịch",
                yourAvailableTimeTitle: "Thời gian rảnh của bạn",
                addTimeWindow: "+ Thêm khung giờ rảnh",
                addWindowBtn: "Thêm khung giờ"
            },
            sos: {
                title: "SOS · Hỗ trợ khẩn cấp",
                subtitle: "Luôn có sự hỗ trợ dành cho bạn 24/7. Bạn không phải vượt qua điều này một mình.",
                groundingHeader: "HÃY CHẬM LẠI MỘT CHÚT",
                groundingDesc: "Hít một hơi thật sâu. Giữ trong 4 giây. Thở ra từ từ.",
                actionHeader: "KHI BẠN ĐANG CHỜ ĐƯỢC HỖ TRỢ",
                action1: "Ở cùng người bạn tin cậy",
                action2: "Đến nơi an toàn hơn",
                action3: "Tạo khoảng cách với những thứ có thể gây hại",
                reassurance: "Bạn không cần giải quyết mọi thứ ngay lúc này. Lúc này, chỉ cần tập trung giữ an toàn cho bản thân.",
                emergencyNumbers: "ĐƯỜNG DÂY NÓNG HỖ TRỢ KHẨN CẤP",
                getSupportNow: "Nhận hỗ trợ ngay",
                closeSOS: "Đóng cửa sổ hỗ trợ"
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
            posts: {
                title: "Tempo Posts",
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
                filterPopular: "Nổi bật"
            },
            auth: {
                regHeading: "TẠO TÀI KHOẢN TEMPO",
                regTitle: "Chào mừng đến với Tempo",
                regSubtitle: "Quản lý căng thẳng học tập, sắp xếp hạn chót và tìm lại nhịp điệu của bạn.",
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
            }
        },
        en: {
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
                signOut: "Sign Out",
                loading: "Loading...",
                user: "User",
                notEstimated: "Not estimated",
                date: "Date",
                time: "Time",
                from: "From",
                to: "To"
            },
            nav: {
                home: "Home",
                tempoPosts: "Tempo Posts",
                peerVolunteer: "Peer Volunteer",
                advisorDesk: "Advisor Desk",
                sos: "SOS",
                language: "Language",
                search: "Search",
                currentLang: "EN"
            },
            modes: {
                default: {
                    name: "Tempo",
                    greeting: "Hi, {name} 👋",
                    greetingFallback: "Hi there 👋",
                    welcomeEyebrow: "WELCOME TO TEMPO",
                    whatDoYouNeed: "What do you need right now?",
                    explainCopy: "You don’t need to figure it out alone. Tell Tempo your current situation, and we’ll help you find the next step.",
                    helpMeStart: "Help me figure out where to start",
                    takesLessOneMin: "Takes less than 1 minute",
                    personalizedGuidance: "Personalized guidance",
                    fromCommunity: "From the Tempo community",
                    seeAll: "See all",
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
                    taskForNow: "YOUR TASK FOR NOW",
                    taskForNowDesc: "Let's handle what's urgent first. You can do it one step at a time.",
                    due: "Due:",
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
                    editPlan: "Edit Plan",
                    completed: "COMPLETED",
                    completedBadge: "Completed",
                    now: "NOW",
                    upNext: "UP NEXT",
                    overwhelmed: "Feeling overwhelmed?",
                    overwhelmedDesc: "Take a few minutes to calm things down and clear your head.",
                    quickStressRelief: "Quick Stress Relief",
                    breathing: "Breathing",
                    focusNow: "Focus now",
                    focusNowDesc: "Launch a timed, distraction-free focus session.",
                    startFocus: "Start Focus →",
                    statePlanIncomplete: "You're still setting up your plan.",
                    statePlanIncompleteDesc: "You're still setting up your plan.",
                    continueBuilding: "Continue building my plan",
                    stateTodayComplete: "You're done for today.",
                    stateTodayCompleteDesc: "Rest up to protect your momentum. Tomorrow's work stays in tomorrow.",
                    todaysWorkDone: "TODAY'S WORK DONE",
                    nextScheduledWork: "Next scheduled work tomorrow.",
                    stateNoWork: "Nothing planned for today.",
                    stateNoWorkDesc: "You can rest, review your plan, or start focus without a task.",
                    stateTimeEnded: "Time ended for today.",
                    stateTimeEndedDesc: "You've worked hard today. Remaining tasks can be adjusted for tomorrow.",
                    statePlanStale: "Your plan needs an update.",
                    statePlanStaleDesc: "Some scheduled tasks are overdue. Update your schedule to continue.",
                    updateSchedule: "Update schedule",
                    statePlanComplete: "Your Urgent Plan is complete.",
                    statePlanCompleteDesc: "All tasks in this urgent plan are finished. Great job pushing through.",
                    shiftToRecovery: "Shift to Recovery Mode",
                    stayInUrgent: "Stay in Urgent Mode",
                    taskCompletedToast: "Task completed! Taking small steps protects your momentum."
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
                    recoveryNote: "RECOVERY NOTE",
                    noteTitle: "A note to myself",
                    noteEmptyTitle: "Keep what helps in one place",
                    noteEmptyDesc: "If you notice something you'd like your future self to remember when things feel heavy, you can keep it here.",
                    addNoteItem: "+ Add something to your note",
                    viewNote: "View Recovery Note",
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
                    posts: "Tempo Posts"
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
                    whatNeedNow: "What you need right now?"
                },
                selector: {
                    switchMode: "Switch Mode",
                    takeBreak: "Take a break from modes",
                    takeBreakDesc: "Return to the default experience",
                    activeBadge: "Active"
                }
            },
            workspace: {
                title: "Plan Workspace",
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
                noDeadline: "No fixed deadline",
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
                due: "Due:",
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
                noFixedDeadline: "No fixed deadline",
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
                subtitle: "Support is available 24/7. You don't have to carry this alone.",
                groundingHeader: "SLOW DOWN FOR A MOMENT",
                groundingDesc: "Take a slow, deep breath. Hold for 4 seconds. Exhale slowly.",
                actionHeader: "WHILE YOU'RE WAITING FOR SUPPORT",
                action1: "Stay with someone you trust",
                action2: "Move somewhere safer",
                action3: "Create distance from anything that could hurt you",
                reassurance: "You don't need to solve everything right now. For now, just focus on staying safe.",
                emergencyNumbers: "EMERGENCY LIFELINES",
                getSupportNow: "Get support now",
                closeSOS: "Close Support"
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
            posts: {
                title: "Tempo Posts",
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
                filterPopular: "Popular"
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

    function formatDeadline(dateStr, timeStr) {
        if (!dateStr) return t('workspace.noDeadline', {}, 'No fixed deadline');
        if (dateStr.includes(' ') && !timeStr) {
            const parts = dateStr.split(' ');
            dateStr = parts[0];
            timeStr = parts[1];
        }
        try {
            const [y, m, d] = dateStr.split('-').map(Number);
            const date = new Date(y, m - 1, d);
            const monthDay = formatDate(date, { month: 'short', day: 'numeric' });
            if (timeStr) {
                return `${monthDay} · ${formatTime12H(timeStr)}`;
            }
            return monthDay;
        } catch (e) {
            return `${dateStr}${timeStr ? ' · ' + timeStr : ''}`;
        }
    }

    // -------------------------------------------------------------------------
    // NAVBAR SWITCHER & STATIC HTML UPDATER
    // -------------------------------------------------------------------------
    function updateNavbarSwitcher() {
        const btnLabel = document.getElementById('nav-current-lang-label');
        if (btnLabel) {
            btnLabel.textContent = currentLang.toUpperCase();
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
        // Nav tabs
        const navTabToday = document.getElementById('nav-tab-today');
        if (navTabToday) navTabToday.textContent = t('nav.home');
        const navTabPosts = document.getElementById('nav-tab-community');
        if (navTabPosts) navTabPosts.textContent = t('nav.tempoPosts');
        const navTabVolunteer = document.getElementById('nav-tab-volunteer');
        if (navTabVolunteer) navTabVolunteer.textContent = t('nav.peerVolunteer');
        const navTabAdmin = document.getElementById('nav-tab-admin');
        if (navTabAdmin) navTabAdmin.textContent = t('nav.advisorDesk');

        // Global search placeholder
        const searchInput = document.getElementById('global-search-input');
        if (searchInput) searchInput.placeholder = t('common.searchPlaceholder');

        // Auth buttons in header
        const btnSignIn = document.getElementById('btn-header-signin');
        if (btnSignIn) btnSignIn.textContent = t('common.signIn');
        const btnRegister = document.getElementById('btn-header-register');
        if (btnRegister) btnRegister.textContent = t('common.register');
        const btnSignOut = document.getElementById('btn-header-signout');
        if (btnSignOut) btnSignOut.textContent = t('common.signOut');

        // Footer
        const footerSos = document.querySelector('footer button[onclick*="openSOS"]');
        if (footerSos) footerSos.textContent = t('sos.title');
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
        formatDate,
        formatTime12H,
        formatDeadline,
        toggleNavbarDropdown,
        closeNavbarDropdown,
        updateStaticHtml,
        DICTIONARY
    };

    // Global shorthand helper
    window.t = (path, params, fallback) => t(path, params, fallback);

})();
