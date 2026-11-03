import os

path = "communityPosts.js"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

target1 = """    function renderRecoveryPreview() {
        const container = document.getElementById('recovery-community-posts-list');
        if (!container) return;
        const mentalPosts = posts.filter(p => (p.tags || []).some(t => t.label.toLowerCase().includes('mental'))).slice(0, 2);
        container.innerHTML = mentalPosts.map(p => `
            <div class="p-3 bg-white border border-[#EAE4DF] rounded-2xl space-y-1">
                <span class="font-bold text-xs text-[#202124]">${escapeHtml(p.authorName)}</span>
                <p class="text-xs text-[#5A5550] line-clamp-2">${escapeHtml(p.content)}</p>
            </div>
        `).join('');
    }"""

repl1 = """    function renderRecoveryPreview() {
        const container = document.getElementById('recovery-community-posts-list');
        if (!container) return;
        const distinctPosts = getDistinctPosts(posts, 2);
        if (distinctPosts.length === 0) {
            container.innerHTML = renderPreviewEmptyStateHTML();
            return;
        }
        container.innerHTML = distinctPosts.map(p => renderPreviewPostCardHTML(p)).join('');
    }"""

# Normalize CRLF for matching
target1_crlf = target1.replace("\r\n", "\n").replace("\n", "\r\n")
repl1_crlf = repl1.replace("\r\n", "\n").replace("\n", "\r\n")

if target1_crlf not in content:
    print("Error: target1 not found")
    exit(1)

content = content.replace(target1_crlf, repl1_crlf, 1)

target2 = """        savePosts();
        renderCommunityPosts();
    }"""
repl2 = """        savePosts();
        renderCommunityPosts();
        renderHomepagePreview();
        renderUrgentPreview();
        renderRecoveryPreview();
    }"""

target2_crlf = target2.replace("\r\n", "\n").replace("\n", "\r\n")
repl2_crlf = repl2.replace("\r\n", "\n").replace("\n", "\r\n")

if target2_crlf not in content:
    print("Error: target2 not found")
    exit(1)

content = content.replace(target2_crlf, repl2_crlf, 1)

target3 = """        saveUserBookmarks(userBookmarks);
        savePosts();
        renderCommunityPosts();"""
repl3 = """        saveUserBookmarks(userBookmarks);
        savePosts();
        renderCommunityPosts();
        renderHomepagePreview();
        renderUrgentPreview();
        renderRecoveryPreview();"""

target3_crlf = target3.replace("\r\n", "\n").replace("\n", "\r\n")
repl3_crlf = repl3.replace("\r\n", "\n").replace("\n", "\r\n")

if target3_crlf not in content:
    print("Error: target3 not found")
    exit(1)

content = content.replace(target3_crlf, repl3_crlf, 1)

with open(path, "wb") as f:
    f.write(content.encode("utf-8"))

print("communityPosts.js updated successfully!")
