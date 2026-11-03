import sys

def main():
    with open('communityPosts.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add getPostTimeAgoDisplay helper right before renderPreviewPostCardHTML
    target_helper = """    function renderPreviewPostCardHTML(post) {"""
    repl_helper = """    function getPostTimeAgoDisplay(timeVal) {
        if (window.TempoI18n && typeof window.TempoI18n.formatTimeAgo === 'function') {
            return window.TempoI18n.formatTimeAgo(timeVal);
        }
        return timeVal || 'Recent';
    }

    function renderPreviewPostCardHTML(post) {"""

    # 2. Update line 2045 in renderPreviewPostCardHTML
    target_card_time = """<span class="text-xs text-[#8E8A85] whitespace-nowrap">${escapeHtml(post.timeAgo || 'Recent')}</span>"""
    repl_card_time = """<span class="text-xs text-[#8E8A85] whitespace-nowrap">${escapeHtml(getPostTimeAgoDisplay(post.timeAgo || 'Recent'))}</span>"""

    # 3. Update line 2022 for comment time
    target_comm_time = """<span class="text-[9px] text-[#8E8A85]">${escapeHtml(c.time || 'Recent')}</span>"""
    repl_comm_time = """<span class="text-[9px] text-[#8E8A85]">${escapeHtml(getPostTimeAgoDisplay(c.time || 'Recent'))}</span>"""

    # 4. Update line 1916 in renderTwoColumnPostHTML
    target_two_col = """<span class="text-xs text-[#8E8A85]">${escapeHtml(post.timeAgo || 'Recent')}</span>"""
    repl_two_col = """<span class="text-xs text-[#8E8A85]">${escapeHtml(getPostTimeAgoDisplay(post.timeAgo || 'Recent'))}</span>"""

    # 5. Update lines 915 and 1024
    target_915 = """<span class="text-[10px] text-[#8E8A85] italic">${escapeHtml(post.timeAgo)}</span>"""
    repl_915 = """<span class="text-[10px] text-[#8E8A85] italic">${escapeHtml(getPostTimeAgoDisplay(post.timeAgo))}</span>"""

    target_1024 = """<span class="text-[10px] text-[#8E8A85]">${escapeHtml(post.timeAgo)}</span>"""
    repl_1024 = """<span class="text-[10px] text-[#8E8A85]">${escapeHtml(getPostTimeAgoDisplay(post.timeAgo))}</span>"""

    # 6. Add language change listener before return
    target_listener = """    // Public API
    return {"""
    repl_listener = """    if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
        window.TempoI18n.onLanguageChange(() => {
            renderUrgentPreview();
            renderRecoveryPreview();
            const homeList = document.getElementById('homepage-community-posts-list');
            if (homeList) {
                const distinctPosts = getDistinctPosts(posts, 2);
                homeList.innerHTML = distinctPosts.map(p => renderPreviewPostCardHTML(p)).join('');
            }
        });
    }

    // Public API
    return {"""

    c_lf = content.replace('\r\n', '\n')
    assert target_helper in c_lf, 'target_helper not found'
    assert target_card_time in c_lf, 'target_card_time not found'
    assert target_comm_time in c_lf, 'target_comm_time not found'
    assert target_two_col in c_lf, 'target_two_col not found'
    assert target_915 in c_lf, 'target_915 not found'
    assert target_1024 in c_lf, 'target_1024 not found'
    assert target_listener in c_lf, 'target_listener not found'

    c_lf = c_lf.replace(target_helper, repl_helper, 1)
    c_lf = c_lf.replace(target_card_time, repl_card_time, 1)
    c_lf = c_lf.replace(target_comm_time, repl_comm_time, 1)
    c_lf = c_lf.replace(target_two_col, repl_two_col, 1)
    c_lf = c_lf.replace(target_915, repl_915, 1)
    c_lf = c_lf.replace(target_1024, repl_1024, 1)
    c_lf = c_lf.replace(target_listener, repl_listener, 1)

    final_content = c_lf.replace('\n', '\r\n')
    with open('communityPosts.js', 'wb') as f:
        f.write(final_content.encode('utf-8'))
    print('Successfully updated communityPosts.js with CRLF line endings!')

if __name__ == '__main__':
    main()
