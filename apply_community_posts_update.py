import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('communityPosts.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update init()
old_init = '''    function init() {
        loadAnnouncements();
        loadPosts();
        loadConversations();
        loadChatRequests();
        renderHomepagePreview();
        renderUrgentPreview();
        renderRecoveryPreview();
        updateReturnButton();
        bindEvents();
    }'''

new_init = '''    function init() {
        loadAnnouncements();
        loadPosts();
        loadConversations();
        loadChatRequests();
        renderHomepagePreview();
        renderUrgentPreview();
        renderRecoveryPreview();
        updateCommunityStaticUI();
        bindEvents();
    }'''

# 2. Update updateReturnButton and add updateCommunitySidebar, updatePostsToolbar, updateCommunityStaticUI
old_return = '''    function updateReturnButton() {
        const backBtn = document.getElementById('btn-community-back');
        const backLabel = document.getElementById('community-back-label');
        if (!backLabel) return;

        const isVi = isViLocale();
        const textLabel = isVi ? 'Về Dashboard' : 'Return to Dashboard';
        const fullLabel = isVi ? '← Về Dashboard' : '← Return to Dashboard';

        backLabel.textContent = textLabel;

        if (backBtn) {
            backBtn.setAttribute('title', fullLabel);
            backBtn.setAttribute('aria-label', fullLabel);
        }
    }'''

new_return = '''    function updateReturnButton() {
        const backBtn = document.getElementById('btn-community-back');
        const backLabel = document.getElementById('community-back-label');
        if (!backLabel) return;

        const isVi = isViLocale();
        const textLabel = isVi ? 'Quay lại Dashboard' : 'Return to Dashboard';
        const fullLabel = isVi ? '← Quay lại Dashboard' : '← Return to Dashboard';

        backLabel.textContent = textLabel;

        if (backBtn) {
            backBtn.setAttribute('title', fullLabel);
            backBtn.setAttribute('aria-label', fullLabel);
        }
    }

    function updateCommunitySidebar() {
        const isVi = isViLocale();
        const tabLabels = {
            announcement: isVi ? 'Thông báo' : 'Announcement',
            tips: 'Tips',
            learn: 'Learn',
            posts: isVi ? 'Bài viết' : 'Posts',
            messages: isVi ? 'Tin nhắn riêng' : 'Direct Message'
        };
        document.querySelectorAll('.community-nav-item, .community-mobile-tab-btn').forEach(btn => {
            const tabKey = btn.getAttribute('data-community-tab');
            if (tabKey && tabLabels[tabKey]) {
                btn.textContent = tabLabels[tabKey];
            }
        });
    }

    function updatePostsToolbar() {
        const isVi = isViLocale();
        const labelNew = document.getElementById('label-posts-new');
        if (labelNew) labelNew.textContent = isVi ? 'Đăng bài mới' : 'New post';

        const searchInput = document.getElementById('posts-search-input');
        if (searchInput) searchInput.placeholder = isVi ? 'Tìm kiếm...' : 'Search...';

        const labelMy = document.getElementById('label-posts-filter-my');
        if (labelMy) labelMy.textContent = isVi ? 'Bài viết của tôi' : 'Your posts';

        const notifBtn = document.getElementById('btn-posts-notifications');
        if (notifBtn) {
            const notifText = isVi ? 'Thông báo' : 'Notifications';
            notifBtn.setAttribute('title', notifText);
            notifBtn.setAttribute('aria-label', notifText);
        }

        const bookmarksBtn = document.getElementById('btn-posts-filter-bookmarks');
        if (bookmarksBtn) {
            const bookmarksText = isVi ? 'Bài viết đã lưu' : 'Saved posts';
            bookmarksBtn.setAttribute('title', bookmarksText);
            bookmarksBtn.setAttribute('aria-label', bookmarksText);
        }
    }

    function updateCommunityStaticUI() {
        updateReturnButton();
        updateCommunitySidebar();
        updatePostsToolbar();
    }'''

# 3. Update selectTab to call updateCommunityStaticUI()
old_select_tab_update = '''        updateReturnButton();
        syncAdminUI();'''

new_select_tab_update = '''        updateCommunityStaticUI();
        syncAdminUI();'''

# 4. Update comment timestamp and reply form in renderTwoColumnPostHTML
old_two_col_comment = '''                                        <span class="text-[9.5px] text-[#8E8A85]">${escapeHtml(c.time || '')}</span>
                                    </div>
                                    <button type="button" class="text-xs text-stone-400 hover:text-[#DE8662]">♡</button>
                                </div>
                                <p class="text-[11px] text-[#4A4541] leading-relaxed pl-6.5">
                                    ${escapeHtml(c.text)}
                                </p>
                            </div>
                        `).join('')}
                    </div>

                    <!-- Add Comment input -->
                    <form onsubmit="window.TempoCommunity.handleInlineCommentSubmit(event, '${post.id}')" class="flex items-center space-x-1.5 pt-2 border-t border-[#EAE4DF]">
                        <input type="text" id="input-comment-${post.id}" 
                               placeholder="Reply..." 
                               class="flex-1 px-3 py-1.5 text-xs bg-[#FAF8F5] border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#DE8662]">
                        <button type="submit" class="bg-[#DFB59F] hover:bg-[#D4A38A] text-white px-3 py-1.5 rounded-xl text-xs font-bold shrink-0 transition">
                            Post
                        </button>
                    </form>'''

new_two_col_comment = '''                                        <span class="text-[9.5px] text-[#8E8A85]">${escapeHtml(getPostTimeAgoDisplay(c.time || ''))}</span>
                                    </div>
                                    <button type="button" class="text-xs text-stone-400 hover:text-[#DE8662]">♡</button>
                                </div>
                                <p class="text-[11px] text-[#4A4541] leading-relaxed pl-6.5">
                                    ${escapeHtml(c.text)}
                                </p>
                            </div>
                        `).join('')}
                    </div>

                    <!-- Add Comment input -->
                    <form onsubmit="window.TempoCommunity.handleInlineCommentSubmit(event, '${post.id}')" class="flex items-center space-x-1.5 pt-2 border-t border-[#EAE4DF]">
                        <input type="text" id="input-comment-${post.id}" 
                               placeholder="${isViLocale() ? 'Trả lời...' : 'Reply...'}" 
                               class="flex-1 px-3 py-1.5 text-xs bg-[#FAF8F5] border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#DE8662]">
                        <button type="submit" class="bg-[#DFB59F] hover:bg-[#D4A38A] text-white px-3 py-1.5 rounded-xl text-xs font-bold shrink-0 transition">
                            ${isViLocale() ? 'Gửi' : 'Post'}
                        </button>
                    </form>'''

# 5. Update comment timestamp and reply form in renderFullWidthPostHTML
old_full_col_comment = '''                                        <span class="text-[9.5px] text-[#8E8A85]">${escapeHtml(c.time || '')}</span>
                                    </div>
                                    <p class="text-[11px] text-[#4A4541] leading-relaxed pl-6.5">
                                        ${escapeHtml(c.text)}
                                    </p>
                                </div>
                            `).join('') : `
                                <p class="text-[11px] text-[#8E8A85] italic py-1">No comments yet. Start the conversation!</p>
                            `}
                        </div>
                        <!-- Add comment form -->
                        <form onsubmit="window.TempoCommunity.handleInlineCommentSubmit(event, '${post.id}')" class="flex items-center space-x-1.5 pt-2 border-t border-[#EAE4DF]">
                            <input type="text" id="input-comment-${post.id}" 
                                   placeholder="${isViLocale() ? 'Viết bình luận...' : 'Write a comment...'}" 
                                   class="flex-1 px-3 py-1.5 text-xs bg-[#FAF8F5] border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#DE8662]">
                            <button type="submit" class="bg-[#DFB59F] hover:bg-[#D4A38A] text-white px-3 py-1.5 rounded-xl text-xs font-bold shrink-0 transition">
                                Post
                            </button>
                        </form>'''

new_full_col_comment = '''                                        <span class="text-[9.5px] text-[#8E8A85]">${escapeHtml(getPostTimeAgoDisplay(c.time || ''))}</span>
                                    </div>
                                    <p class="text-[11px] text-[#4A4541] leading-relaxed pl-6.5">
                                        ${escapeHtml(c.text)}
                                    </p>
                                </div>
                            `).join('') : `
                                <p class="text-[11px] text-[#8E8A85] italic py-1">No comments yet. Start the conversation!</p>
                            `}
                        </div>
                        <!-- Add comment form -->
                        <form onsubmit="window.TempoCommunity.handleInlineCommentSubmit(event, '${post.id}')" class="flex items-center space-x-1.5 pt-2 border-t border-[#EAE4DF]">
                            <input type="text" id="input-comment-${post.id}" 
                                   placeholder="${isViLocale() ? 'Trả lời...' : 'Reply...'}" 
                                   class="flex-1 px-3 py-1.5 text-xs bg-[#FAF8F5] border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#DE8662]">
                            <button type="submit" class="bg-[#DFB59F] hover:bg-[#D4A38A] text-white px-3 py-1.5 rounded-xl text-xs font-bold shrink-0 transition">
                                ${isViLocale() ? 'Gửi' : 'Post'}
                            </button>
                        </form>'''

# 6. Update onLanguageChange
old_lang_change = '''    if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
        window.TempoI18n.onLanguageChange(() => {
            updateReturnButton();
            renderUrgentPreview();
            renderRecoveryPreview();
            const homeList = document.getElementById('homepage-community-posts-list');
            if (homeList) {
                const distinctPosts = getDistinctPosts(posts, 2);
                homeList.innerHTML = distinctPosts.map(p => renderPreviewPostCardHTML(p)).join('');
            }
        });
    }'''

new_lang_change = '''    if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
        window.TempoI18n.onLanguageChange(() => {
            updateCommunityStaticUI();
            const postsPanel = document.getElementById('community-panel-posts');
            if (postsPanel && !postsPanel.classList.contains('hidden')) {
                renderCommunityPosts();
            }
            renderUrgentPreview();
            renderRecoveryPreview();
            const homeList = document.getElementById('homepage-community-posts-list');
            if (homeList) {
                const distinctPosts = getDistinctPosts(posts, 2);
                homeList.innerHTML = distinctPosts.map(p => renderPreviewPostCardHTML(p)).join('');
            }
        });
    }'''

# 7. Update return object to expose updateCommunityStaticUI
old_return_obj = '''        handleReturnNavigation,
        updateReturnButton,'''

new_return_obj = '''        handleReturnNavigation,
        updateReturnButton,
        updateCommunitySidebar,
        updatePostsToolbar,
        updateCommunityStaticUI,'''

# Check presence
assert old_init.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_init not found"
assert old_return.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_return not found"
assert old_select_tab_update.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_select_tab_update not found"
assert old_two_col_comment.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_two_col_comment not found"
assert old_full_col_comment.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_full_col_comment not found"
assert old_lang_change.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_lang_change not found"
assert old_return_obj.replace('\r\n', '\n') in content.replace('\r\n', '\n'), "old_return_obj not found"

content_norm = content.replace('\r\n', '\n')
content_norm = content_norm.replace(old_init.replace('\r\n', '\n'), new_init.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_return.replace('\r\n', '\n'), new_return.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_select_tab_update.replace('\r\n', '\n'), new_select_tab_update.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_two_col_comment.replace('\r\n', '\n'), new_two_col_comment.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_full_col_comment.replace('\r\n', '\n'), new_full_col_comment.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_lang_change.replace('\r\n', '\n'), new_lang_change.replace('\r\n', '\n'))
content_norm = content_norm.replace(old_return_obj.replace('\r\n', '\n'), new_return_obj.replace('\r\n', '\n'))

content_crlf = content_norm.replace('\n', '\r\n')

with open('communityPosts.js', 'wb') as f:
    f.write(content_crlf.encode('utf-8'))

print("communityPosts.js updated successfully with strict CRLF.")
