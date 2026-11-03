import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update vi community
old_vi_community = '''            community: {
                title: "Cộng đồng Tempo",
                returnToDashboard: "Quay lại Dashboard",
                returnToDashboardWithArrow: "← Quay lại Dashboard",
                tabs: {
                    announcement: "Thông báo",
                    tips: "Tips",
                    learn: "Learn",
                    posts: "Bài viết",
                    messages: "Tin nhắn riêng"
                }
            },'''

new_vi_community = '''            community: {
                title: "Cộng đồng Tempo",
                returnToDashboard: "Quay lại Dashboard",
                returnToDashboardWithArrow: "← Quay lại Dashboard",
                tabs: {
                    announcement: "Thông báo",
                    tips: "Tips",
                    learn: "Learn",
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
                        }
                    }
                }
            },'''

# 2. Update en community
old_en_community = '''            community: {
                title: "Tempo Community",
                returnToDashboard: "Return to Dashboard",
                returnToDashboardWithArrow: "← Return to Dashboard",
                tabs: {
                    announcement: "Announcement",
                    tips: "Tips",
                    learn: "Learn",
                    posts: "Posts",
                    messages: "Direct Message"
                }
            },'''

new_en_community = '''            community: {
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
                            usage: "Try it when you have a lot to do that makes you not want to do anything at all."
                        },
                        presentation_dread: {
                            title: "Presentation anxiety",
                            usage: "Try it when you have a presentation ahead and you feel anxious about it."
                        },
                        brain_fog_reset: {
                            title: "Brain Fog Reset & Mental Momentum",
                            usage: "Try it when mental fatigue blocks focus and simple tasks feel impossible."
                        },
                        exam_panic_surge: {
                            title: "Exam panic & physiological sigh reset",
                            usage: "Try it when sudden panic spikes right before or during a major test."
                        },
                        email_paralysis: {
                            title: "Professor extension email template",
                            usage: "Try it when severe stress requires requesting an urgent assignment extension."
                        },
                        sleep_runaway: {
                            title: "Racing night thoughts wind-down",
                            usage: "Try it when academic worries keep you awake well past 2 AM."
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
                        }
                    }
                }
            },'''

# 3. Update updateStaticHtml
old_static_html = '''        // Community Posts Toolbar
        const labelPostsNew = document.getElementById('label-posts-new');'''

new_static_html = '''        // Community Tips
        const tipsSearchInput = document.getElementById('tips-search-input');
        if (tipsSearchInput) {
            tipsSearchInput.placeholder = currentLang === 'vi' ? 'Tìm kiếm...' : 'Search...';
        }

        // Community Posts Toolbar
        const labelPostsNew = document.getElementById('label-posts-new');'''

assert old_vi_community.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_vi_community not found"
assert old_en_community.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_en_community not found"
assert old_static_html.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_static_html not found"

content_norm = content.replace('\r\n', '\n')
content_norm = content_norm.replace(old_vi_community.replace('\r\n', '\n'), new_vi_community.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_en_community.replace('\r\n', '\n'), new_en_community.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_static_html.replace('\r\n', '\n'), new_static_html.replace('\r\n', '\n'))

content_crlf = content_norm.replace('\n', '\r\n')

with open('i18n.js', 'wb') as f:
    f.write(content_crlf.encode('utf-8'))

print("i18n.js updated successfully with tips translations (strict CRLF).")
