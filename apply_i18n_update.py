import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update vi posts
old_vi_posts = '''            posts: {
                title: "Tempo Posts",
                returnToDashboard: "Return to Dashboard",
                returnToDashboardWithArrow: "← Return to Dashboard",
                returnToDashboard: "Về Dashboard",
                returnToDashboardWithArrow: "← Về Dashboard",
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
            },'''

new_vi_posts = '''            community: {
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
            },'''

# 2. Update en posts
old_en_posts = '''            posts: {
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
            },'''

new_en_posts = '''            community: {
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
            },'''

# 3. Update formatTimeAgo regex
old_regex = "const match = str.match(/^(\\d+)\\s*(hour|hr|minute|min|day|month|year|giờ|phút|ngày|tháng|năm)s?\\s*(ago|trước)?$/i);"
new_regex = "const match = str.match(/^(\\d+)\\s*(hours?|hrs?|h|minutes?|mins?|m|days?|d|months?|years?|giờ|phút|ngày|tháng|năm)\\s*(ago|trước)?$/i);"

# 4. Update updateStaticHtml
old_back_label = '''        const communityBackBtn = document.getElementById('btn-community-back');
        const communityBackLabel = document.getElementById('community-back-label');
        if (communityBackLabel) {
            communityBackLabel.textContent = currentLang === 'vi' ? 'Về Dashboard' : 'Return to Dashboard';
        }
        if (communityBackBtn) {
            const commBackText = currentLang === 'vi' ? '← Về Dashboard' : '← Return to Dashboard';
            communityBackBtn.setAttribute('title', commBackText);
            communityBackBtn.setAttribute('aria-label', commBackText);
        }'''

new_back_label = '''        const communityBackBtn = document.getElementById('btn-community-back');
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
            learn: 'Learn',
            posts: currentLang === 'vi' ? 'Bài viết' : 'Posts',
            messages: currentLang === 'vi' ? 'Tin nhắn riêng' : 'Direct Message'
        };
        document.querySelectorAll('.community-nav-item, .community-mobile-tab-btn').forEach(btn => {
            const tabKey = btn.getAttribute('data-community-tab');
            if (tabKey && commTabLabels[tabKey]) {
                btn.textContent = commTabLabels[tabKey];
            }
        });

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
        }'''

# Check if target blocks exist
assert old_vi_posts.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_vi_posts not found"
assert old_en_posts.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_en_posts not found"
assert old_regex in content, "old_regex not found"
assert old_back_label.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_back_label not found"

# Perform CRLF-preserving replacements
# Normalize to \r\n
content = content.replace('\r\n', '\n')
content = content.replace(old_vi_posts.replace('\r\n', '\n'), new_vi_posts.replace('\r\n', '\n'))
content = content.replace(old_en_posts.replace('\r\n', '\n'), new_en_posts.replace('\r\n', '\n'))
content = content.replace(old_regex, new_regex)
content = content.replace(old_back_label.replace('\r\n', '\n'), new_back_label.replace('\r\n', '\n'))

# Ensure strictly CRLF
content_crlf = content.replace('\r\n', '\n').replace('\n', '\r\n')

with open('i18n.js', 'wb') as f:
    f.write(content_crlf.encode('utf-8'))

print("i18n.js updated successfully with strict CRLF.")
