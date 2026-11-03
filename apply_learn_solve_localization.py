import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('learnSolve.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Verify existing markers
assert 'const LEARN_TOPICS = [' in content, "LEARN_TOPICS marker missing"
assert 'function renderModalContent() {' in content, "renderModalContent marker missing"
assert 'function renderTipCalloutHTML(tipId) {' in content, "renderTipCalloutHTML marker missing"

# We will insert LEARN_TOPICS_VI, TEMPO_TIPS_VI, SOLVE_SITUATIONS_TITLES_VI, isViLocale, getTopicDisplay right before LEARN_TOPICS
helper_and_data = '''    function isViLocale() {
        if (window.TempoI18n && typeof window.TempoI18n.getCurrentLanguage === 'function') {
            return window.TempoI18n.getCurrentLanguage() === 'vi';
        }
        return (localStorage.getItem('tempo_locale') || 'vi') === 'vi';
    }

    const TEMPO_TIPS_VI = {
        startSmall: {
            title: 'Bắt đầu nhỏ hơn bạn nghĩ',
            text: 'Gặp khó khăn khi bắt đầu? Hãy hạ thấp tiêu chuẩn. Cam kết chỉ làm trong 5 phút hoặc viết một câu duy nhất. Vượt qua sức ỳ ban đầu là tất cả những gì quan trọng.'
        },
        goodEnoughBeforePerfect: {
            title: 'Đủ tốt trước khi hoàn hảo',
            text: "Bị mắc kẹt vì muốn mọi thứ phải hoàn hảo? Hãy nhắm đến mức 'đủ tốt để nộp' trước. Chỉnh sửa luôn dễ dàng hơn nhiều so với việc bắt đầu từ một trang giấy trắng."
        },
        containTheWorry: {
            title: 'Khoanh vùng vòng lặp lo âu',
            text: 'Suy nghĩ cứ xoay quanh một mối lo hay mâu thuẫn? Hãy viết vấn đề cốt lõi ra giấy, lên lịch một giờ cụ thể vào ngày mai để giải quyết, và nhẹ nhàng gác nó lại lúc này.'
        },
        interruptTheLoop: {
            title: 'Ngắt chỉ một mắt xích',
            text: 'Bị kẹt trong vòng lặp căng thẳng? Bạn không cần phải sửa chữa mọi thứ ngay hôm nay. Chỉ cần thay đổi một mắt xích duy nhất — như ngủ thêm 1 tiếng hoặc thư giãn 5 phút.'
        },
        selfCheckSigns: {
            title: 'Nhận biết tín hiệu sớm',
            text: 'Nhận ra các dấu hiệu căng thẳng sớm của cơ thể? Theo dõi các dấu hiệu lặp lại trong Self-check giúp bạn phát hiện quá tải trước khi kiệt sức ập đến.'
        },
        breathingBeforeAction: {
            title: 'Làm dịu cơn tăng adrenaline',
            text: 'Tim đập nhanh trước khi phát biểu hoặc thuyết trình? Hai phút thở hộp sẽ kích hoạt trực tiếp phản xạ phó giao cảm giúp cơ thể bạn dịu lại.'
        },
        pauseBeforeSnack: {
            title: 'Tạo khoảng dừng 60 giây',
            text: 'Tìm đến đồ ăn khi căng thẳng? Hãy dừng lại 60 giây cùng một ly nước để nhận biết cơ thể bạn đang cần nạp năng lượng, cần nghỉ ngơi, hay cần xoa dịu cảm xúc.'
        },
        stabilizeOneThing: {
            title: 'Neo giữ một thói quen duy nhất',
            text: 'Sinh hoạt cảm thấy hỗn loạn? Đừng cố gắng thay đổi toàn bộ cuộc sống cùng lúc. Hãy neo giữ một thói quen đơn giản — như giờ thức dậy cố định hoặc uống một ly nước mỗi sáng.'
        }
    };

    const SOLVE_SITUATIONS_TITLES_VI = {
        deadline_pileup: 'Dồn dập deadline',
        falling_behind: 'Bị tụt lại phía sau',
        cant_focus: 'Không thể tập trung',
        perfectionism_paralysis: 'Tê liệt vì cầu toàn',
        disrupted_routine: 'Xáo trộn sinh hoạt',
        grades: 'Áp lực điểm số',
        too_many_responsibilities: 'Quá nhiều trách nhiệm',
        loneliness: 'Cảm giác cô đơn',
        teamwork_conflict: 'Mâu thuẫn bài tập nhóm',
        exam_anxiety: 'Lo âu trước kỳ thi'
    };

    const LEARN_TOPICS_VI = {
        what_is_stress: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Stress là gì?',
            shortDescription: 'Căng thẳng là trạng thái lo lắng hoặc áp lực tinh thần xuất phát từ một tình huống khó khăn. Đây là phản ứng tự nhiên của con người, giúp chúng ta đối mặt với những thử thách và mối đe dọa trong cuộc sống. Mỗi người đều trải qua căng thẳng ở một mức độ nhất định.',
            contentParagraphs: [
                'Stress không phải là bệnh lý, sự yếu đuối cá nhân hay khiếm khuyết tính cách. Đây là cơ chế sinh lý tiến hóa giúp tâm trí và cơ thể bạn chuẩn bị sẵn sàng đối mặt với thử thách và thích ứng với các yêu cầu.',
                'Khi bạn đối mặt với deadline căng thẳng, câu hỏi thi bất ngờ hoặc xung đột trong giao tiếp, não bộ sẽ kích hoạt hệ thần kinh giao cảm và trục HPA, giải phóng các hormone như adrenaline và cortisol. Tim bạn đập nhanh hơn, nhịp thở tăng lên và sự chú ý tập trung dồn vào nhiệm vụ trước mắt.',
                'Ở mức độ vừa phải và kiểm soát được, căng thẳng cấp tính rất hữu ích: nó huy động năng lượng, mài sắc sự tập trung và nâng cao trạng thái sẵn sàng. Mối lo ngại chỉ phát sinh khi căng thẳng trở nên quá mức, kéo dài liên tục hoặc thiếu cơ hội phục hồi phù hợp.'
            ],
            relatedToolLabel: 'Mở Giải tỏa nhanh'
        },
        stress_problem: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Khi nào căng thẳng trở thành vấn đề?',
            shortDescription: 'Sự khác biệt giữa chu kỳ căng thẳng lành mạnh và tình trạng quá tải mãn tính không dứt.',
            contentParagraphs: [
                'Trong điều kiện lành mạnh, căng thẳng diễn ra theo một chu kỳ tự nhiên: Áp lực → Căng thẳng → Hoàn thành → Nghỉ ngơi → Phục hồi. Khi điểm gây áp lực được giải quyết, hệ thần kinh sẽ tự điều hòa giảm xuống và trở về mức cân bằng ban đầu.',
                'Trong đời sống sinh viên, căng thẳng thường trở thành một vòng lặp không ngừng nghỉ: Deadline → Căng thẳng → Deadline tiếp theo → Căng thẳng → Dự án nhóm → Căng thẳng → Thi cử... Không có khoảng dừng để phục hồi, hệ thần kinh luôn ở trạng thái báo động cao liên tục.',
                'Điều quan trọng là thời gian kéo dài và việc thiếu phục hồi cũng đáng lo ngại tương đương với cường độ căng thẳng tức thời. Khi căng thẳng tiếp diễn mà không được giải tỏa, nó dần bào mòn 5 khía cạnh sinh hoạt hàng ngày:'
            ],
            descriptiveList: [
                { title: 'Giấc ngủ', detail: 'Khó đi vào giấc ngủ, hay giật mình thức giấc giữa đêm hoặc thức dậy cảm thấy không sảng khoái.' },
                { title: 'Khả năng tập trung', detail: 'Trí nhớ làm việc suy giảm, khiến việc đọc tài liệu và giải quyết bài toán cảm thấy khó gấp đôi.' },
                { title: 'Cảm xúc', detail: 'Dễ cáu gắt hơn, đột ngột rơi nước mắt hoặc cảm thấy tê liệt, mất cảm xúc.' },
                { title: 'Năng lượng', detail: 'Sự kiệt sức sâu sắc về thể chất và tinh thần mà cà phê liên tục cũng không thể bù đắp.' },
                { title: 'Thói quen hằng ngày', detail: 'Các bữa ăn đều đặn, vệ sinh cá nhân và việc giữ gọn gàng không gian sống bắt đầu bị bỏ bê.' }
            ],
            relatedToolLabel: 'Mở Giải tỏa nhanh',
            relatedModeLabel: 'Vào Chế độ phục hồi'
        },
        stress_signs: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Cách căng thẳng biểu hiện ra ngoài',
            shortDescription: '4 nhóm dấu hiệu căng thẳng: Suy nghĩ, Cảm xúc, Cơ thể và Hành vi.',
            contentParagraphs: [
                'Căng thẳng không đơn thuần là một trải nghiệm trong suy nghĩ. Nó biểu hiện qua 4 khía cạnh gắn kết chặt chẽ trong đời sống hàng ngày của bạn:',
                'Những dấu hiệu lặp đi lặp lại có thể trở thành tín hiệu cảnh báo sớm của riêng bạn. Nếu nhận thấy bản thân bỏ bữa sáng hay nghiến chặt quai hàm, việc chăm sóc những dấu hiệu đó sớm sẽ giúp bạn điều chỉnh trước khi chạm ngưỡng kiệt sức.'
            ],
            fourGroups: [
                {
                    name: '🧠 Suy nghĩ',
                    items: ['Khó tập trung', 'Suy nghĩ chạy đua liên tục không dứt', 'Khó đưa ra quyết định', 'Thường xuyên trống rỗng đầu óc']
                },
                {
                    name: '💭 Cảm xúc',
                    items: ['Lo lắng dai dẳng', 'Dễ cáu gắt / gắt gỏng với bạn bè', 'Cảm giác buồn bã hoặc bất an', 'Cảm thấy choáng ngợp trước những việc nhỏ nhặt']
                },
                {
                    name: '💤 Cơ thể',
                    items: ['Mệt mỏi mãn tính', 'Khó đi vào giấc ngủ', 'Đau đầu do căng thẳng', 'Căng cứng cơ vùng cổ và vai']
                },
                {
                    name: '🔄 Hành vi & Sinh hoạt',
                    items: ['Trì hoãn các hành động đơn giản', 'Thu mình khỏi bạn bè và các mối quan hệ', 'Ăn uống thất thường / chán ăn', 'Bỏ bê các thói quen sinh hoạt hằng ngày']
                }
            ],
            relatedToolLabel: 'Mở Self-check'
        },
        stress_loop: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Vòng lặp căng thẳng ở sinh viên',
            shortDescription: 'Cách những deadline dồn dập kích hoạt trạng thái tê liệt tinh thần, tạo ra các vòng lặp né tránh làm tăng thêm mức độ căng thẳng.',
            contentParagraphs: [
                'Căng thẳng thường xuyên giữ chân sinh viên trong những vòng lặp hành vi tự củng cố. Khối lượng công việc nặng nề gây lo lắng, dẫn đến việc thức khuya cày bài. Thiếu ngủ gây mệt mỏi, làm suy giảm khả năng tập trung vào ngày hôm sau, khiến tốc độ hoàn thành công việc chậm lại và sinh ra thêm nhiều căng thẳng hơn nữa.'
            ],
            loopNodes: [
                { label: 'Dồn dập deadline', icon: '⏰' },
                { label: 'Căng thẳng / Hoảng loạn', icon: '⚡' },
                { label: 'Thức khuya làm bài', icon: '🌙' },
                { label: 'Mệt mỏi & khó tập trung', icon: '😴' },
                { label: 'Tiến độ chậm lại', icon: '⏳' },
                { label: 'Căng thẳng tăng thêm', icon: '💥' }
            ],
            keyTakeaway: 'Bạn không cần phải thay đổi tất cả mọi thứ cùng một lúc. Nhận diện vòng lặp và ngắt quãng nó chỉ tại MỘT mắt xích (ví dụ: đi ngủ đúng giờ hoặc đi bộ 10 phút) sẽ bẻ gãy đà tích tụ căng thẳng.',
            relatedToolLabel: 'Mở Giải tỏa nhanh',
            relatedModeLabel: 'Vào Chế độ phục hồi'
        },
        recovery: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Phục hồi là một phần của quản lý căng thẳng',
            shortDescription: 'Tại sao căng thẳng không kết thúc ngay khi deadline vừa qua, và tại sao phục hồi lại thiết yếu.',
            contentParagraphs: [
                'Bạn đã bao giờ nộp xong một bài tập lớn hoặc hoàn thành kỳ thi cuối kỳ, chỉ để cảm thấy cạn kiệt năng lượng, dễ cáu gắt, hoặc bị cảm lạnh ngay sau đó chưa?',
                'Việc kết thúc tình huống gây căng thẳng không đồng nghĩa với phản ứng căng thẳng của cơ thể sẽ tắt đi như một công tắc đèn. Lượng cortisol và adrenaline tăng cao cần thời gian để chuyển hóa hết, và hệ thần kinh tự chủ của bạn đòi hỏi sự nghỉ ngơi có chủ đích để tái lập trạng thái cân bằng nội môi.',
                'Phục hồi không phải là lãng phí thời gian, lười biếng hay trì hoãn. Đó là một quá trình sinh học và tâm lý chủ động, nơi các kết nối thần kinh được củng cố, khả năng phục hồi cảm xúc được tái tạo và sự sáng suốt tinh thần quay trở lại.',
                'Chế độ phục hồi trong Tempo được thiết kế chuyên biệt cho giai đoạn này: mang lại cho bạn không gian để sống chậm lại, check-in với chính mình và nhận ra điều gì thực sự hữu ích.'
            ],
            relatedToolLabel: 'Bắt đầu Tập thở',
            relatedModeLabel: 'Vào Chế độ phục hồi'
        },
        academic_burnout: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Kiệt sức học đường (Academic burnout)',
            shortDescription: 'Hiểu về tình trạng kiệt quệ kéo dài, thái độ tiêu cực và suy giảm hiệu quả học tập.',
            contentParagraphs: [
                'Kiệt sức học đường không phải là sự mệt mỏi thông thường sau một đêm thức khuya. Đó là trạng thái cạn kiệt thể chất và cảm xúc mãn tính do áp lực học tập kéo dài mà thiếu cơ hội phục hồi thích đáng.',
                'Các nghiên cứu thường mô tả kiệt sức học đường qua 3 khía cạnh rõ rệt:'
            ],
            burnoutDimensions: [
                {
                    icon: '🪫',
                    name: 'Kiệt quệ',
                    detail: 'Trạng thái mệt mỏi mãn tính về thể chất, nhận thức và cảm xúc, nơi giấc ngủ thông thường không còn giúp bạn hồi phục năng lượng.'
                },
                {
                    icon: '📚',
                    name: 'Xa lánh & Hoài nghi',
                    detail: 'Hình thành thái độ thờ ơ, hoài nghi hoặc chán chường đối với bài vở, giảng viên và các mục tiêu học tập từng rất quan trọng với bạn.'
                },
                {
                    icon: '📉',
                    name: 'Cảm giác suy giảm hiệu quả',
                    detail: 'Cảm giác dai dẳng rằng nỗ lực của mình là vô nghĩa, bản thân làm việc không hiệu quả và không có thành tựu nào thực sự đáng kể.'
                }
            ],
            nonDiagnosticNote: 'Bạn không cần phải phân định rạch ròi liệu mình "chỉ đang căng thẳng" hay "đã bị kiệt sức" trước khi bắt đầu quan tâm đến sức khỏe tinh thần của mình. Nhận ra các dấu hiệu này là lời nhắc bạn tạm dừng, điều chỉnh khối lượng công việc và tìm kiếm sự hỗ trợ.',
            relatedModeLabel: 'Vào Chế độ phục hồi'
        },
        stress_eating: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Ăn uống do căng thẳng',
            shortDescription: 'Ăn uống do căng thẳng, hay còn gọi là ăn uống theo cảm xúc, là việc sử dụng thức ăn để cải thiện cảm xúc hoặc khiến bản thân cảm thấy dễ chịu hơn, thay vì đáp ứng nhu cầu đói về mặt thể chất.',
            contentParagraphs: [
                'Tìm đến thức ăn khi căng thẳng là một phản xạ sinh lý và cảm xúc hoàn toàn dễ hiểu. Khi căng thẳng mãn tính, cortisol kích thích cảm giác thèm các loại tinh bột giàu năng lượng, trong khi việc ăn uống kích hoạt giải phóng dopamine tạm thời giúp xoa dịu nỗi bất an cảm xúc.',
                'Dưới đây là cách tiếp cận thấu hiểu, không tự phán xét đối với việc ăn uống do căng thẳng:'
            ],
            steps: [
                {
                    heading: 'Kiểm tra xem bạn đang đói, căng thẳng hay cả hai',
                    detail: 'Nếu bạn thực sự đói về mặt thể chất, cơ thể bạn cần dinh dưỡng. Hãy thưởng thức một bữa ăn đàng hoàng mà không tự trách mình.'
                },
                {
                    heading: 'Tạo khoảng dừng ngắn 60 giây',
                    detail: 'Uống một cốc nước, hít thở sâu 5 nhịp hoặc rời khỏi bàn học trong một phút. Khoảng dừng ngắn tạo ra không gian để bạn nhận biết cảm xúc thực sự của mình.'
                },
                {
                    heading: 'Không phán xét đạo đức hay xem đó là thất bại',
                    detail: 'Nếu bạn vẫn chọn ăn, hãy đối xử với bản thân bằng sự dịu dàng. Ép buộc ăn kiêng và cảm giác tội lỗi chỉ tạo ra thêm căng thẳng, tiếp thêm nhiên liệu cho chính vòng lặp mà bạn đang muốn thoát ra.'
                },
                {
                    heading: 'Quay lại nhiệm vụ khi tâm trí đã lắng dịu',
                    detail: 'Khi bạn đã cảm thấy vững vàng và tĩnh tâm hơn một chút, hãy quay lại công việc với một bước đầu tiên thật nhỏ.'
                }
            ],
            relatedToolLabel: 'Mở Giải tỏa nhanh'
        },
        what_do_i_need: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Tôi cần gì khi bị căng thẳng?',
            shortDescription: 'Kết nối trải nghiệm căng thẳng hiện tại của bạn với không gian phù hợp trong Tempo.',
            contentParagraphs: [
                'Căng thẳng biểu hiện theo nhiều cách khác nhau, và điều bạn cần phụ thuộc vào trạng thái bạn đang trải qua ngay lúc này:'
            ],
            routingOptions: [
                {
                    condition: 'Quá choáng ngợp hoặc hoảng loạn không thể nghĩ thông suốt?',
                    actionText: 'Hãy xoa dịu hệ thần kinh trước tiên với Giải tỏa nhanh hoặc Tập thở hộp 2 phút.',
                    btnLabel: 'Mở Giải tỏa nhanh',
                    actionKey: 'quick_relief'
                },
                {
                    condition: 'Biết chính xác tình huống nào đang gây ra căng thẳng?',
                    actionText: 'Khám phá mục Giải quyết tình huống để nhận kế hoạch hành động từng bước thực tế.',
                    btnLabel: 'Khám phá Tình huống',
                    actionKey: 'switch_to_solve'
                },
                {
                    condition: 'Vấn đề đã qua đi nhưng bạn vẫn cảm thấy chưa ổn?',
                    actionText: 'Vào Chế độ phục hồi để giải tỏa áp lực, theo dõi thể trạng mỗi ngày và nghỉ ngơi.',
                    btnLabel: 'Vào Chế độ phục hồi',
                    actionKey: 'mode_recovery'
                },
                {
                    condition: 'Thấy có gì đó bất ổn nhưng không rõ lý do cụ thể?',
                    actionText: 'Sử dụng Chế độ mơ hồ để check-in và suy ngẫm theo hướng dẫn nhẹ nhàng.',
                    btnLabel: 'Vào Chế độ mơ hồ',
                    actionKey: 'mode_unclear'
                },
                {
                    condition: 'Có một vấn đề cấp bách cần giải quyết dứt điểm ngay?',
                    actionText: 'Vào Chế độ khẩn cấp để phân loại các task gấp và tạo timeline khả thi.',
                    btnLabel: 'Vào Chế độ khẩn cấp',
                    actionKey: 'mode_emergency'
                }
            ],
            relatedToolLabel: 'Mở Giải tỏa nhanh',
            relatedModeLabel: 'Vào Chế độ khẩn cấp'
        },
        support_seeking: {
            badge: '🧠 Giáo dục Căng thẳng · Chủ đề',
            title: 'Khi nào tôi nên tìm kiếm thêm sự hỗ trợ?',
            shortDescription: 'Các chỉ số mô tả cho thấy việc tìm kiếm thêm hỗ trợ phù hợp là rất đáng cân nhắc.',
            contentParagraphs: [
                'Các công cụ tự quản lý và chiến lược cá nhân rất có giá trị, nhưng những thử thách ở đại học không phải là điều bạn bắt buộc phải vượt qua trong sự đơn độc hoàn toàn.',
                'Các dấu hiệu mô tả cho thấy sự hỗ trợ bổ sung có thể rất đáng để bạn cân nhắc:'
            ],
            descriptiveList: [
                { title: 'Căng thẳng kéo dài không thuyên giảm', detail: 'Căng thẳng dai dẳng qua nhiều tuần và những ngày cuối tuần nghỉ ngơi bình thường cũng không giúp xoa dịu.' },
                { title: 'Ảnh hưởng đến sức khỏe thể chất', detail: 'Chất lượng ăn uống, giấc ngủ hoặc mức năng lượng mỗi ngày bị xáo trộn rõ rệt và liên tục.' },
                { title: 'Hiệu quả sinh hoạt suy giảm', detail: 'Việc học tập, lên lớp hoặc các công việc thường nhật cảm thấy ngày càng khó duy trì.' },
                { title: 'Các cách quen thuộc không còn hiệu quả', detail: 'Những phương pháp và thói quen trước đây từng giúp bạn ứng phó nay dường như không còn tác dụng.' }
            ],
            supportConclusion: 'Liên hệ với điều phối viên chăm sóc sức khỏe tinh thần trong trường, cố vấn học tập hoặc các bạn tư vấn đồng đẳng là một dấu hiệu chủ động bảo vệ bản thân. (Lưu ý: Đối với các tình huống khẩn cấp về an toàn tức thời, nút SOS toàn cầu của Tempo luôn sẵn sàng bất cứ lúc nào).',
            relatedToolLabel: 'Khám phá các lựa chọn hỗ trợ'
        }
    };

    function getTopicDisplay(item) {
        if (!item) return item;
        const isVi = isViLocale();
        if (!isVi) return item;
        const viData = LEARN_TOPICS_VI[item.id];
        if (!viData) {
            if (SOLVE_SITUATIONS_TITLES_VI[item.id]) {
                return {
                    ...item,
                    title: SOLVE_SITUATIONS_TITLES_VI[item.id]
                };
            }
            return item;
        }
        return {
            ...item,
            title: viData.title || item.title,
            badge: viData.badge || (item.type === 'solve' ? '🧩 Tình huống & Giải pháp' : '🧠 Giáo dục Căng thẳng · Chủ đề'),
            shortDescription: viData.shortDescription || item.shortDescription,
            context: viData.context || item.context,
            contentParagraphs: viData.contentParagraphs || item.contentParagraphs,
            descriptiveList: viData.descriptiveList || item.descriptiveList,
            fourGroups: viData.fourGroups || item.fourGroups,
            loopNodes: viData.loopNodes || item.loopNodes,
            keyTakeaway: viData.keyTakeaway || item.keyTakeaway,
            burnoutDimensions: viData.burnoutDimensions || item.burnoutDimensions,
            nonDiagnosticNote: viData.nonDiagnosticNote || item.nonDiagnosticNote,
            steps: viData.steps || item.steps,
            routingOptions: viData.routingOptions || item.routingOptions,
            supportConclusion: viData.supportConclusion || item.supportConclusion,
            relatedTool: item.relatedTool ? {
                ...item.relatedTool,
                label: viData.relatedToolLabel || item.relatedTool.label
            } : null,
            relatedMode: item.relatedMode ? {
                ...item.relatedMode,
                label: viData.relatedModeLabel || item.relatedMode.label
            } : null
        };
    }
'''

norm = content.replace('\r\n', '\n')

# 1. Insert helper_and_data before `    const LEARN_TOPICS = [`
marker = '    const LEARN_TOPICS = ['
assert marker in norm, "Marker LEARN_TOPICS not found"
norm = norm.replace(marker, helper_and_data + '\n' + marker, 1)

# 2. Update renderTipCalloutHTML to support TEMPO_TIPS_VI
old_tip_callout = '''    function renderTipCalloutHTML(tipId) {
        const tip = TEMPO_TIPS[tipId];
        if (!tip) return '';
        return `
            <div class="tempo-tip-callout p-4 sm:p-5 rounded-2xl bg-[#FFF8F3] border border-[#FFD2BA] space-y-1.5 shadow-2xs text-left">
                <div class="flex items-center space-x-1.5 text-[10px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">
                    <span>💡</span>
                    <span>TEMPO TIP</span>
                </div>
                <h5 class="text-xs sm:text-sm font-bold text-[#202124] leading-snug">${escapeHTML(tip.title)}</h5>
                <p class="text-xs text-[#6F6B68] leading-relaxed">${escapeHTML(tip.text)}</p>
            </div>
        `;
    }'''

new_tip_callout = '''    function renderTipCalloutHTML(tipId) {
        const tip = TEMPO_TIPS[tipId];
        if (!tip) return '';
        const isVi = isViLocale();
        const tipDisplay = (isVi && TEMPO_TIPS_VI[tipId]) ? TEMPO_TIPS_VI[tipId] : tip;
        return `
            <div class="tempo-tip-callout p-4 sm:p-5 rounded-2xl bg-[#FFF8F3] border border-[#FFD2BA] space-y-1.5 shadow-2xs text-left">
                <div class="flex items-center space-x-1.5 text-[10px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">
                    <span>💡</span>
                    <span>TEMPO TIP</span>
                </div>
                <h5 class="text-xs sm:text-sm font-bold text-[#202124] leading-snug">${escapeHTML(tipDisplay.title)}</h5>
                <p class="text-xs text-[#6F6B68] leading-relaxed">${escapeHTML(tipDisplay.text)}</p>
            </div>
        `;
    }'''

assert old_tip_callout in norm, "old_tip_callout not found"
norm = norm.replace(old_tip_callout, new_tip_callout, 1)

# 3. Update renderModalContent to use getTopicDisplay and localized UI strings
old_rmc_start = '''    function renderModalContent() {
        const card = document.getElementById('tempo-learn-solve-modal-card');
        if (!card) return;

        const currentId = modalNavStack[modalNavStack.length - 1];
        const item = getItemById(currentId);
        if (!item) {
            closeModal();
            return;
        }

        const hasBack = modalNavStack.length > 1;
        const prevId = hasBack ? modalNavStack[modalNavStack.length - 2] : null;
        const prevItem = prevId ? getItemById(prevId) : null;'''

new_rmc_start = '''    function renderModalContent() {
        const card = document.getElementById('tempo-learn-solve-modal-card');
        if (!card) return;

        const currentId = modalNavStack[modalNavStack.length - 1];
        const rawItem = getItemById(currentId);
        if (!rawItem) {
            closeModal();
            return;
        }

        const isVi = isViLocale();
        const item = getTopicDisplay(rawItem);

        const hasBack = modalNavStack.length > 1;
        const prevId = hasBack ? modalNavStack[modalNavStack.length - 2] : null;
        const rawPrevItem = prevId ? getItemById(prevId) : null;
        const prevItem = rawPrevItem ? getTopicDisplay(rawPrevItem) : null;'''

assert old_rmc_start in norm, "old_rmc_start not found"
norm = norm.replace(old_rmc_start, new_rmc_start, 1)

# In renderModalContent:
# Update Back button label: 'Back' -> (isVi ? 'Quay lại' : 'Back')
old_back_str = "<span>${prevItem ? escapeHTML(prevItem.title) : 'Back'}</span>"
new_back_str = "<span>${prevItem ? escapeHTML(prevItem.title) : (isVi ? 'Quay lại' : 'Back')}</span>"
assert old_back_str in norm, "old_back_str not found"
norm = norm.replace(old_back_str, new_back_str, 1)

# Update Close dialog aria-label
old_aria = 'aria-label="Close dialog"'
new_aria = 'aria-label="${isVi ? \'Đóng cửa sổ\' : \'Close dialog\'}"'
assert old_aria in norm, "old_aria not found"
norm = norm.replace(old_aria, new_aria, 1)

# Update Section Headings:
# ACTION STEPS
old_act_steps = '<span class="text-xs font-extrabold uppercase tracking-wider text-stone-500">ACTION STEPS</span>'
new_act_steps = '<span class="text-xs font-extrabold uppercase tracking-wider text-stone-500">${isVi ? \'CÁC BƯỚC THỰC HIỆN\' : \'ACTION STEPS\'}</span>'
assert old_act_steps in norm, "old_act_steps not found"
norm = norm.replace(old_act_steps, new_act_steps, 1)

# DIFFERENT CONTEXTS / CASES
old_diff_ctx = '<span class="text-xs font-extrabold uppercase tracking-wider text-stone-500">DIFFERENT CONTEXTS / CASES</span>'
new_diff_ctx = '<span class="text-xs font-extrabold uppercase tracking-wider text-stone-500">${isVi ? \'CÁC BỐI CẢNH / TÌNH HUỐNG KHÁC NHAU\' : \'DIFFERENT CONTEXTS / CASES\'}</span>'
assert old_diff_ctx in norm, "old_diff_ctx not found"
norm = norm.replace(old_diff_ctx, new_diff_ctx, 1)

# VISUAL STRESS CYCLE
old_v_cycle = '<span class="text-[10px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">VISUAL STRESS CYCLE</span>'
new_v_cycle = '<span class="text-[10px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">${isVi ? \'VÒNG LẶP CĂNG THẲNG TRỰC QUAN\' : \'VISUAL STRESS CYCLE\'}</span>'
assert old_v_cycle in norm, "old_v_cycle not found"
norm = norm.replace(old_v_cycle, new_v_cycle, 1)

# Key Insight:
old_key_ins = '<strong class="text-[#202124]">Key Insight:</strong>'
new_key_ins = '<strong class="text-[#202124]">${isVi ? \'Điểm mấu chốt:\' : \'Key Insight:\'}</strong>'
assert old_key_ins in norm, "old_key_ins not found"
norm = norm.replace(old_key_ins, new_key_ins, 1)

# FINDING YOUR NEXT STEP
old_find_step = '<span class="text-xs font-extrabold uppercase tracking-wider text-stone-500">FINDING YOUR NEXT STEP</span>'
new_find_step = '<span class="text-xs font-extrabold uppercase tracking-wider text-stone-500">${isVi ? \'TÌM BƯỚC TIẾP THEO CỦA BẠN\' : \'FINDING YOUR NEXT STEP\'}</span>'
assert old_find_step in norm, "old_find_step not found"
norm = norm.replace(old_find_step, new_find_step, 1)

# RELATED GUIDES & ACTIONS
old_rel_guides = 'RELATED GUIDES &amp; ACTIONS'
new_rel_guides = '${isVi ? \'HƯỚNG DẪN &amp; HÀNH ĐỘNG LIÊN QUAN\' : \'RELATED GUIDES &amp; ACTIONS\'}'
assert old_rel_guides in norm, "old_rel_guides not found"
norm = norm.replace(old_rel_guides, new_rel_guides, 1)

# Update Related items title lookup to use getTopicDisplay
old_r_learn = '''                        ${hasRelatedLearn ? item.relatedLearnIds.map(rid => {
                            const rItem = getItemById(rid);
                            if (!rItem) return '';
                            return `
                                <button type="button" onclick="window.TempoLearnSolve.openModal('${rItem.id}')"
                                        class="px-3 py-1.5 rounded-xl bg-purple-50 text-[#7E22CE] border border-purple-200 text-xs font-bold hover:bg-purple-100 transition cursor-pointer flex items-center space-x-1">
                                    <span>🧠</span>
                                    <span>${escapeHTML(rItem.title)} →</span>
                                </button>
                            `;
                        }).join('') : ''}'''

new_r_learn = '''                        ${hasRelatedLearn ? item.relatedLearnIds.map(rid => {
                            const rItem = getItemById(rid);
                            if (!rItem) return '';
                            const disp = getTopicDisplay(rItem);
                            return `
                                <button type="button" onclick="window.TempoLearnSolve.openModal('${rItem.id}')"
                                        class="px-3 py-1.5 rounded-xl bg-purple-50 text-[#7E22CE] border border-purple-200 text-xs font-bold hover:bg-purple-100 transition cursor-pointer flex items-center space-x-1">
                                    <span>🧠</span>
                                    <span>${escapeHTML(disp.title)} →</span>
                                </button>
                            `;
                        }).join('') : ''}'''
assert old_r_learn in norm, "old_r_learn not found"
norm = norm.replace(old_r_learn, new_r_learn, 1)

old_r_solve = '''                        ${hasRelatedSolve ? item.relatedSolveIds.map(rid => {
                            const rItem = getItemById(rid);
                            if (!rItem) return '';
                            return `
                                <button type="button" onclick="window.TempoLearnSolve.openModal('${rItem.id}')"
                                        class="px-3 py-1.5 rounded-xl bg-[#FFF5EC] text-[#B83D08] border border-[#FFD2BA] text-xs font-bold hover:bg-[#FFE9DC] transition cursor-pointer flex items-center space-x-1">
                                    <span>🧩</span>
                                    <span>${escapeHTML(rItem.title)} →</span>
                                </button>
                            `;
                        }).join('') : ''}'''

new_r_solve = '''                        ${hasRelatedSolve ? item.relatedSolveIds.map(rid => {
                            const rItem = getItemById(rid);
                            if (!rItem) return '';
                            const disp = getTopicDisplay(rItem);
                            return `
                                <button type="button" onclick="window.TempoLearnSolve.openModal('${rItem.id}')"
                                        class="px-3 py-1.5 rounded-xl bg-[#FFF5EC] text-[#B83D08] border border-[#FFD2BA] text-xs font-bold hover:bg-[#FFE9DC] transition cursor-pointer flex items-center space-x-1">
                                    <span>🧩</span>
                                    <span>${escapeHTML(disp.title)} →</span>
                                </button>
                            `;
                        }).join('') : ''}'''
assert old_r_solve in norm, "old_r_solve not found"
norm = norm.replace(old_r_solve, new_r_solve, 1)

# Close button at bottom of modal
old_close_btn = '''                <button type="button" onclick="window.TempoLearnSolve.closeModal()"
                        class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                    Close
                </button>'''

new_close_btn = '''                <button type="button" onclick="window.TempoLearnSolve.closeModal()"
                        class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                    ${isVi ? 'Đóng' : 'Close'}
                </button>'''
assert old_close_btn in norm, "old_close_btn not found"
norm = norm.replace(old_close_btn, new_close_btn, 1)

# 4. Add onLanguageChange hook in init()
old_init = '''    function init() {
        ensureModalMounted();
    }'''

new_init = '''    function init() {
        ensureModalMounted();
        if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
            window.TempoI18n.onLanguageChange(() => {
                const modal = document.getElementById('tempo-learn-solve-modal');
                if (modal && !modal.classList.contains('hidden') && modalNavStack.length > 0) {
                    renderModalContent();
                }
                updateDOM();
            });
        }
    }'''
assert old_init in norm, "old_init not found"
norm = norm.replace(old_init, new_init, 1)

# 5. Export getTopicDisplay and isViLocale
old_return = '''        getActiveCategory: () => activeCategory,
        getNavStack: () => [...modalNavStack]
    };'''

new_return = '''        getActiveCategory: () => activeCategory,
        getNavStack: () => [...modalNavStack],
        isViLocale,
        getTopicDisplay
    };'''
assert old_return in norm, "old_return not found"
norm = norm.replace(old_return, new_return, 1)

# Write back with CRLF
content_crlf = norm.replace('\n', '\r\n')
with open('learnSolve.js', 'wb') as f:
    f.write(content_crlf.encode('utf-8'))

print("Successfully updated learnSolve.js with complete localization!")
