import sys, json

sys.stdout.reconfigure(encoding='utf-8')

# -----------------------------------------------------------------------------
# 1. UPDATE i18n.js
# -----------------------------------------------------------------------------
with open('i18n.js', 'r', encoding='utf-8') as f:
    i18n_content = f.read()

# We need all 19 items in vi.community.tips.items and en.community.tips.items
vi_items_json = '''                        deadline_pileup: {
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
                            title: "Cảm giác \\"mình chưa đủ tốt\\"",
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
                        }'''

en_items_json = '''                        deadline_pileup: {
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
                            title: "Feeling \\"not good enough\\"",
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
                        }'''

# Replace vi tips items
import re

# Match `items: { ... }` inside vi community tips
old_vi_items_pattern = r'(community:\s*\{[\s\S]*?tips:\s*\{[\s\S]*?items:\s*\{)[\s\S]*?(\n\s*\}\s*\n\s*\}\s*\n\s*\},[\s\S]*?posts:)'
m = re.search(old_vi_items_pattern, i18n_content)
if m:
    replacement = m.group(1) + '\n' + vi_items_json + m.group(2)
    i18n_content = i18n_content[:m.start()] + replacement + i18n_content[m.end():]
    print("Updated vi tips items in i18n.js")
else:
    print("Warning: could not regex replace vi tips items in i18n.js")

# Match `items: { ... }` inside en community tips
old_en_items_pattern = r'(community:\s*\{[\s\S]*?tips:\s*\{[\s\S]*?items:\s*\{)[\s\S]*?(\n\s*\}\s*\n\s*\}\s*\n\s*\},[\s\S]*?posts:)'
# Second occurrence is EN
matches = list(re.finditer(old_en_items_pattern, i18n_content))
if len(matches) >= 2:
    m_en = matches[1]
    replacement_en = m_en.group(1) + '\n' + en_items_json + m_en.group(2)
    i18n_content = i18n_content[:m_en.start()] + replacement_en + i18n_content[m_en.end():]
    print("Updated en tips items in i18n.js")
else:
    print("Warning: could not regex replace en tips items in i18n.js")

i18n_crlf = i18n_content.replace('\r\n', '\n').replace('\n', '\r\n')
with open('i18n.js', 'wb') as f:
    f.write(i18n_crlf.encode('utf-8'))
print("Wrote i18n.js with CRLF.")


# -----------------------------------------------------------------------------
# 2. UPDATE communityPosts.js
# -----------------------------------------------------------------------------
with open('communityPosts.js', 'r', encoding='utf-8') as f:
    cp_content = f.read()

# 1. Restore original INITIAL_TIPS (6 items)
old_cp_tips = '''    // Reference 2: Tips (Solve) Situations
    const INITIAL_TIPS = [
        {
            id: 'deadline_pileup',
            title: 'The 5-Minute Starter Rule for Paralyzing Deadlines',
            usage: 'Try it when you have a lot to do that makes you not want to do anything at all.'
        },
        {
            id: 'presentation_dread',
            title: 'Presentation anxiety',
            usage: 'Try it when you have a presentation ahead and you feel anxious about it.'
        },
        {
            id: 'brain_fog_reset',
            title: 'Brain Fog Reset & Mental Momentum',
            usage: 'Try it when mental fatigue blocks focus and simple tasks feel impossible.'
        },
        {
            id: 'exam_panic_surge',
            title: 'Exam panic & physiological sigh reset',
            usage: 'Try it when sudden panic spikes right before or during a major test.'
        },
        {
            id: 'email_paralysis',
            title: 'Professor extension email template',
            usage: 'Try it when severe stress requires requesting an urgent assignment extension.'
        },
        {
            id: 'sleep_runaway',
            title: 'Racing night thoughts wind-down',
            usage: 'Try it when academic worries keep you awake well past 2 AM.'
        },
        {
            id: 'falling_behind',
            title: 'Falling behind / not keeping up',
            usage: 'Struggling to keep pace with lecture material, required readings, or lab work.'
        },
        {
            id: 'teamwork',
            title: 'Teamwork problems',
            usage: 'Unbalanced workload, unresponsive group members, or communication friction.'
        },
        {
            id: 'grades',
            title: 'Grades didn’t go as expected',
            usage: 'Coping with academic disappointment and extracting constructive next steps.'
        }
    ];'''

restored_cp_tips = '''    // Reference 2: Tips (Solve) Situations
    const INITIAL_TIPS = [
        {
            id: 'deadline_pileup',
            title: 'The 5-Minute Starter Rule for Paralyzing Deadlines',
            usage: 'Try it when you have a lot to do that makes you not want to do anything at all'
        },
        {
            id: 'presentation_dread',
            title: 'Presentation anxiety',
            usage: 'Try it when you have a presentation ahead and you feel anxious about it'
        },
        {
            id: 'brain_fog_reset',
            title: 'Brain Fog Reset & Mental Momentum',
            usage: 'Try it when mental fatigue blocks focus and simple tasks feel impossible'
        },
        {
            id: 'exam_panic_surge',
            title: 'Exam panic & physiological sigh reset',
            usage: 'Try it when sudden panic spikes right before or during a major test'
        },
        {
            id: 'email_paralysis',
            title: 'Professor extension email template',
            usage: 'Try it when severe stress requires requesting an urgent assignment extension'
        },
        {
            id: 'sleep_runaway',
            title: 'Racing night thoughts wind-down',
            usage: 'Try it when academic worries keep you awake well past 2 AM'
        }
    ];'''

# 2. Update getTipDisplay with all 19 translations
full_tips_translations = '''    function getTipDisplay(item) {
        const isVi = isViLocale();
        if (window.TempoI18n && typeof window.TempoI18n.t === 'function') {
            const locTitle = window.TempoI18n.t(`community.tips.items.${item.id}.title`);
            const locUsage = window.TempoI18n.t(`community.tips.items.${item.id}.usage`);
            if (locTitle && locTitle !== `community.tips.items.${item.id}.title`) {
                return {
                    title: locTitle,
                    usage: locUsage || item.usage
                };
            }
        }
        const tipsTranslations = {
            deadline_pileup: {
                vi: {
                    title: 'Quy tắc bắt đầu 5 phút khi deadline khiến bạn tê liệt',
                    usage: 'Thử áp dụng khi bạn có quá nhiều việc phải làm đến mức không biết bắt đầu từ đâu.'
                },
                en: {
                    title: 'The 5-Minute Starter Rule for Paralyzing Deadlines',
                    usage: 'Try it when you have a lot to do that makes you not want to do anything at all'
                }
            },
            presentation_dread: {
                vi: {
                    title: 'Lo lắng khi thuyết trình',
                    usage: 'Áp dụng khi bạn sắp có một buổi thuyết trình và cảm thấy lo lắng về điều đó.'
                },
                en: {
                    title: 'Presentation anxiety',
                    usage: 'Try it when you have a presentation ahead and you feel anxious about it'
                }
            },
            brain_fog_reset: {
                vi: {
                    title: 'Xua tan sương mù tinh thần và lấy lại đà tập trung',
                    usage: 'Thử áp dụng khi sự mệt mỏi về tinh thần khiến bạn khó tập trung và ngay cả những việc đơn giản cũng trở nên khó khăn.'
                },
                en: {
                    title: 'Brain Fog Reset & Mental Momentum',
                    usage: 'Try it when mental fatigue blocks focus and simple tasks feel impossible'
                }
            },
            exam_panic_surge: {
                vi: {
                    title: 'Giảm hoảng loạn trước kỳ thi bằng kỹ thuật thở dài sinh lý',
                    usage: 'Áp dụng khi bạn đột nhiên cảm thấy hoảng loạn ngay trước hoặc trong một bài kiểm tra quan trọng.'
                },
                en: {
                    title: 'Exam panic & physiological sigh reset',
                    usage: 'Try it when sudden panic spikes right before or during a major test'
                }
            },
            email_paralysis: {
                vi: {
                    title: 'Mẫu email xin gia hạn deadline với giảng viên',
                    usage: 'Sử dụng khi bạn đang chịu áp lực lớn và cần xin gia hạn deadline bài tập một cách khẩn cấp.'
                },
                en: {
                    title: 'Professor extension email template',
                    usage: 'Try it when severe stress requires requesting an urgent assignment extension'
                }
            },
            sleep_runaway: {
                vi: {
                    title: 'Thư giãn khi những suy nghĩ cứ tiếp diễn vào ban đêm',
                    usage: 'Thử áp dụng khi những lo lắng về học tập khiến bạn trằn trọc và không thể ngủ dù đã qua 2 giờ sáng.'
                },
                en: {
                    title: 'Racing night thoughts wind-down',
                    usage: 'Try it when academic worries keep you awake well past 2 AM'
                }
            },
            falling_behind: {
                vi: {
                    title: 'Cảm thấy bị tụt lại phía sau trong học tập',
                    usage: 'Khi bạn gặp khó khăn trong việc theo kịp bài giảng, tài liệu đọc bắt buộc hoặc các bài thực hành.'
                },
                en: {
                    title: 'Falling behind / not keeping up',
                    usage: 'Struggling to keep pace with lecture material, required readings, or lab work.'
                }
            },
            teamwork: {
                vi: {
                    title: 'Khó khăn khi làm việc nhóm',
                    usage: 'Khi khối lượng công việc không được phân chia đồng đều, thành viên nhóm thiếu phản hồi hoặc giao tiếp gặp nhiều trở ngại.'
                },
                en: {
                    title: 'Teamwork problems',
                    usage: 'Unbalanced workload, unresponsive group members, or communication friction.'
                }
            },
            teamwork_problems: {
                vi: {
                    title: 'Khó khăn khi làm việc nhóm',
                    usage: 'Khi khối lượng công việc không được phân chia đồng đều, thành viên nhóm thiếu phản hồi hoặc giao tiếp gặp nhiều trở ngại.'
                },
                en: {
                    title: 'Teamwork problems',
                    usage: 'Unbalanced workload, unresponsive group members, or communication friction.'
                }
            },
            grades: {
                vi: {
                    title: 'Kết quả học tập không như mong đợi',
                    usage: 'Khi bạn cảm thấy thất vọng về kết quả học tập và cần tìm ra những bước tiếp theo mang tính xây dựng.'
                },
                en: {
                    title: 'Grades didn’t go as expected',
                    usage: 'Coping with academic disappointment and extracting constructive next steps.'
                }
            },
            grades_disappointment: {
                vi: {
                    title: 'Kết quả học tập không như mong đợi',
                    usage: 'Khi bạn cảm thấy thất vọng về kết quả học tập và cần tìm ra những bước tiếp theo mang tính xây dựng.'
                },
                en: {
                    title: 'Grades didn’t go as expected',
                    usage: 'Coping with academic disappointment and extracting constructive next steps.'
                }
            },
            presentation_anxiety: {
                vi: {
                    title: 'Lo lắng khi thuyết trình',
                    usage: 'Cảm giác hồi hộp tột độ, tim đập nhanh hoặc lo sợ trước khi phát biểu trước lớp hoặc thuyết trình.'
                },
                en: {
                    title: 'Presentation anxiety',
                    usage: 'Intense nervousness, racing heartbeat, or dread before speaking in class or giving a presentation.'
                }
            },
            cant_focus: {
                vi: {
                    title: 'Không thể tập trung / khó bắt đầu',
                    usage: 'Nhìn vào màn hình trống rỗng, cảm giác sương mù tinh thần hoặc bị tê liệt khi cố gắng bắt đầu học tập.'
                },
                en: {
                    title: 'Can’t focus / can’t get started',
                    usage: 'Staring at a blank screen, experiencing brain fog, or feeling frozen when trying to begin study tasks.'
                }
            },
            future_uncertainty: {
                vi: {
                    title: 'Mơ hồ về định hướng / tương lai',
                    usage: 'Lo lắng về lựa chọn nghề nghiệp, chọn ngành hoặc cảm thấy mất phương hướng so với bạn bè đồng trang lứa.'
                },
                en: {
                    title: 'Unsure about direction / future',
                    usage: 'Worrying about career choices, major selection, or feeling aimless compared to peers.'
                }
            },
            not_good_enough: {
                vi: {
                    title: 'Cảm giác "mình chưa đủ tốt"',
                    usage: 'Tự nghi ngờ bản thân kéo dài, hội chứng kẻ mạo danh và cảm thấy mọi người xung quanh đều hiểu bài trừ mình.'
                },
                en: {
                    title: 'Feeling "not good enough"',
                    usage: 'Persistent self-doubt, imposter syndrome, and feeling like everyone else understands while you don\\'t.'
                }
            },
            expectations_pressure: {
                vi: {
                    title: 'Áp lực từ kỳ vọng của bản thân',
                    usage: 'Chủ nghĩa hoàn hảo, tiêu chuẩn nội tâm khắt khe và nỗi sợ mắc lỗi trong quá trình học tập.'
                },
                en: {
                    title: 'Pressure from expectations of myself',
                    usage: 'Perfectionism, harsh internal standards, and fear of making mistakes in coursework.'
                }
            },
            comparing_others: {
                vi: {
                    title: 'So sánh bản thân với người khác',
                    usage: 'Cảm thấy kém cỏi khi nhìn vào kỳ thực tập, tiến độ học tập hoặc thành tích xã hội của bạn bè.'
                },
                en: {
                    title: 'Comparing myself with other people',
                    usage: 'Feeling inadequate when observing peers’ internships, study pace, or social achievements.'
                }
            },
            too_many_responsibilities: {
                vi: {
                    title: 'Quá nhiều trách nhiệm cùng một lúc',
                    usage: 'Bị quá tải với việc học, công việc làm thêm, câu lạc bộ và các trách nhiệm gia đình diễn ra cùng lúc.'
                },
                en: {
                    title: 'Too many responsibilities at once',
                    usage: 'Overloaded with study, part-time jobs, student clubs, and family commitments simultaneously.'
                }
            },
            relationship_conflict: {
                vi: {
                    title: 'Xung đột với người quan trọng',
                    usage: 'Mâu thuẫn với bạn cùng phòng, người yêu, bạn bè hoặc người thân ảnh hưởng đến khả năng học tập của bạn.'
                },
                en: {
                    title: 'Conflict with someone important',
                    usage: 'Friction with a roommate, partner, friend, or family member impacting your ability to study.'
                }
            },
            loneliness: {
                vi: {
                    title: 'Cô đơn / cảm giác mất kết nối',
                    usage: 'Cảm thấy bị cô lập trong trường học, thiếu cảm giác thuộc về nơi này hoặc không có ai để tâm sự trong những tuần khó khăn.'
                },
                en: {
                    title: 'Loneliness / feeling disconnected',
                    usage: 'Feeling isolated on campus, lacking belonging, or having nobody to confide in during tough weeks.'
                }
            },
            disrupted_routine: {
                vi: {
                    title: 'Lối sống hằng ngày bị xáo trộn kéo dài',
                    usage: 'Lịch ngủ bị đảo lộn, ăn uống thất thường và các thói quen hằng ngày bị xói mòn bởi căng thẳng liên miên.'
                },
                en: {
                    title: 'Daily routine has been disrupted for a while',
                    usage: 'Sleep schedule inverted, meals irregular, and everyday habits eroded by ongoing stress.'
                }
            }
        };

        const t = tipsTranslations[item.id];
        if (t) {
            const loc = isVi ? t.vi : t.en;
            return {
                title: loc.title || item.title,
                usage: loc.usage || item.usage
            };
        }
        return {
            title: item.title,
            usage: item.usage
        };
    }'''

# 3. Restore merging of TempoLearnSolve.getSituations() in renderTips()
old_render_tips_start = '''        let filtered = [...tips];

        if (currentTipsSearch) {'''

restored_render_tips_start = '''        let filtered = [...tips];

        // Also merge situations from TempoLearnSolve if not present (Preserve full 19-card dataset)
        if (window.TempoLearnSolve && typeof window.TempoLearnSolve.getSituations === 'function') {
            const extra = window.TempoLearnSolve.getSituations();
            extra.forEach(s => {
                if (!filtered.some(f => f.id === s.id)) {
                    filtered.push({
                        id: s.id,
                        title: s.title,
                        usage: s.shortDescription || 'Actionable coping guide'
                    });
                }
            });
        }

        if (currentTipsSearch) {'''

# Find and replace getTipDisplay in cp_content
old_get_tip_display_pattern = r'    function getTipDisplay\(item\) \{[\s\S]*?\n    \}'
m_tip = re.search(old_get_tip_display_pattern, cp_content)
assert m_tip, "old getTipDisplay not found in communityPosts.js"

cp_norm = cp_content.replace('\r\n', '\n')
cp_norm = cp_norm.replace(old_cp_tips.replace('\r\n', '\n'), restored_cp_tips.replace('\r\n', '\n'))
cp_norm = cp_norm.replace(m_tip.group(0).replace('\r\n', '\n'), full_tips_translations.replace('\r\n', '\n'))
cp_norm = cp_norm.replace(old_render_tips_start.replace('\r\n', '\n'), restored_render_tips_start.replace('\r\n', '\n'))

cp_crlf = cp_norm.replace('\n', '\r\n')
with open('communityPosts.js', 'wb') as f:
    f.write(cp_crlf.encode('utf-8'))
print("Wrote communityPosts.js with restored Tips content (CRLF).")


# -----------------------------------------------------------------------------
# 3. UPDATE index.html (bump cache version)
# -----------------------------------------------------------------------------
with open('index.html', 'r', encoding='utf-8') as f:
    idx_content = f.read()

idx_content = idx_content.replace('i18n.js?v=20261101.26', 'i18n.js?v=20261101.27')
idx_content = idx_content.replace('communityPosts.js?v=20261101.6', 'communityPosts.js?v=20261101.7')

idx_lf = idx_content.replace('\r\n', '\n')
with open('index.html', 'wb') as f:
    f.write(idx_lf.encode('utf-8'))
print("Wrote index.html with strict LF.")
