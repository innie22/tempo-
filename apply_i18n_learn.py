import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update vi community.tabs.learn to "Kiến thức"
old_vi_tab = 'learn: "Learn",'
new_vi_tab = 'learn: "Kiến thức",'
assert old_vi_tab in content, "old_vi_tab not found"
content = content.replace(old_vi_tab, new_vi_tab, 1) # Only first occurrence is VI

# 2. Add learn under vi community
vi_learn_dict = '''                learn: {
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
                },'''

# Insert vi_learn_dict before vi posts: {
old_vi_posts_anchor = '            posts: {'
assert old_vi_posts_anchor in content, "old_vi_posts_anchor not found"
# First occurrence of 'posts: {' is VI
content = content.replace(old_vi_posts_anchor, vi_learn_dict + '\n' + old_vi_posts_anchor, 1)

# 3. Add learn under en community
en_learn_dict = '''                learn: {
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
                },'''

# Second occurrence of 'posts: {' is EN
parts = content.split('            posts: {')
assert len(parts) >= 3, "Did not find at least two 'posts: {' anchors"
content = parts[0] + '            posts: {' + parts[1] + en_learn_dict + '\n            posts: {' + parts[2]

# 4. Update updateStaticHtml() in i18n.js
old_comm_tab_labels = '''        const commTabLabels = {
            announcement: currentLang === 'vi' ? 'Thông báo' : 'Announcement',
            tips: 'Tips',
            learn: 'Learn',
            posts: currentLang === 'vi' ? 'Bài viết' : 'Posts',
            messages: currentLang === 'vi' ? 'Tin nhắn riêng' : 'Direct Message'
        };'''

new_comm_tab_labels = '''        const commTabLabels = {
            announcement: currentLang === 'vi' ? 'Thông báo' : 'Announcement',
            tips: 'Tips',
            learn: currentLang === 'vi' ? 'Kiến thức' : 'Learn',
            posts: currentLang === 'vi' ? 'Bài viết' : 'Posts',
            messages: currentLang === 'vi' ? 'Tin nhắn riêng' : 'Direct Message'
        };'''

old_tips_search = '''        // Community Tips
        const tipsSearchInput = document.getElementById('tips-search-input');
        if (tipsSearchInput) {
            tipsSearchInput.placeholder = currentLang === 'vi' ? 'Tìm kiếm...' : 'Search...';
        }'''

new_tips_and_learn_search = '''        // Community Tips
        const tipsSearchInput = document.getElementById('tips-search-input');
        if (tipsSearchInput) {
            tipsSearchInput.placeholder = currentLang === 'vi' ? 'Tìm kiếm...' : 'Search...';
        }

        // Community Learn
        const learnSearchInput = document.getElementById('learn-search-input');
        if (learnSearchInput) {
            learnSearchInput.placeholder = currentLang === 'vi' ? 'Tìm kiếm...' : 'Search...';
        }'''

content_norm = content.replace('\r\n', '\n')
assert old_comm_tab_labels.replace('\r\n', '\n') in content_norm, "old_comm_tab_labels not found"
assert old_tips_search.replace('\r\n', '\n') in content_norm, "old_tips_search not found"

content_norm = content_norm.replace(old_comm_tab_labels.replace('\r\n', '\n'), new_comm_tab_labels.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_tips_search.replace('\r\n', '\n'), new_tips_and_learn_search.replace('\r\n', '\n'))

content_crlf = content_norm.replace('\n', '\r\n')
with open('i18n.js', 'wb') as f:
    f.write(content_crlf.encode('utf-8'))

print("Updated i18n.js with Learn localization (CRLF).")
