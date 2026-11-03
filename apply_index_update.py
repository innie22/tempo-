import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Back button & Sidebar
old_sidebar_section = '''                    <!-- Return Home Navigation Button (Typography reduced to 12-13px) -->
                    <div class="mb-5">
                        <button type="button" id="btn-community-back" onclick="window.TempoCommunity.handleReturnNavigation()" 
                                class="inline-flex items-center space-x-1.5 text-[12px] sm:text-[13px] font-bold text-[#5A5550] hover:text-[#DE8662] transition cursor-pointer"
                                aria-label="← Về Dashboard" title="← Về Dashboard">
                            <span class="text-base leading-none">←</span> <span id="community-back-label">Về Dashboard</span>
                        </button>
                    </div>

                    <!-- Mobile Horizontal Tab Strip (shown on mobile, hidden on lg) -->
                    <div class="lg:hidden flex items-center space-x-1.5 overflow-x-auto pb-4 scrollbar-none" role="tablist">
                        <button type="button" role="tab" data-community-tab="announcement" onclick="window.TempoCommunity.selectTab('announcement')" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-bold transition whitespace-nowrap bg-[#F7ECE1] text-[#DE8662]">
                            Announcement
                        </button>
                        <button type="button" role="tab" data-community-tab="tips" onclick="window.TempoCommunity.selectTab('tips')" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Tips
                        </button>
                        <button type="button" role="tab" data-community-tab="learn" onclick="window.TempoCommunity.selectTab('learn')" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Learn
                        </button>
                        <button type="button" role="tab" data-community-tab="posts" onclick="window.TempoCommunity.navigateToPostsFeed()" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Posts
                        </button>
                        <button type="button" role="tab" data-community-tab="messages" onclick="window.TempoCommunity.selectTab('messages')" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Direct Message
                        </button>
                    </div>

                    <!-- Desktop Vertical Tab Navigation (Typography reduced to 14-15px) -->
                    <nav class="hidden lg:flex flex-col space-y-1.5" role="tablist" id="community-sidebar-nav">
                        <button type="button" role="tab" data-community-tab="announcement" onclick="window.TempoCommunity.selectTab('announcement')" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer bg-[#F7ECE1] text-[#DE8662]">
                            Announcement
                        </button>

                        <button type="button" role="tab" data-community-tab="tips" onclick="window.TempoCommunity.selectTab('tips')" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Tips
                        </button>

                        <button type="button" role="tab" data-community-tab="learn" onclick="window.TempoCommunity.selectTab('learn')" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Learn
                        </button>

                        <!-- Requirement 5: Posts button always navigates to main Posts newsfeed -->
                        <button type="button" role="tab" data-community-tab="posts" onclick="window.TempoCommunity.navigateToPostsFeed()" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Posts
                        </button>

                        <button type="button" role="tab" data-community-tab="messages" onclick="window.TempoCommunity.selectTab('messages')" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Direct Message
                        </button>
                    </nav>'''

new_sidebar_section = '''                    <!-- Return Home Navigation Button (Typography reduced to 12-13px) -->
                    <div class="mb-5">
                        <button type="button" id="btn-community-back" onclick="window.TempoCommunity.handleReturnNavigation()" 
                                class="inline-flex items-center space-x-1.5 text-[12px] sm:text-[13px] font-bold text-[#5A5550] hover:text-[#DE8662] transition cursor-pointer"
                                aria-label="← Quay lại Dashboard" title="← Quay lại Dashboard">
                            <span class="text-base leading-none">←</span> <span id="community-back-label">Quay lại Dashboard</span>
                        </button>
                    </div>

                    <!-- Mobile Horizontal Tab Strip (shown on mobile, hidden on lg) -->
                    <div class="lg:hidden flex items-center space-x-1.5 overflow-x-auto pb-4 scrollbar-none" role="tablist">
                        <button type="button" role="tab" data-community-tab="announcement" onclick="window.TempoCommunity.selectTab('announcement')" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-bold transition whitespace-nowrap bg-[#F7ECE1] text-[#DE8662]">
                            Thông báo
                        </button>
                        <button type="button" role="tab" data-community-tab="tips" onclick="window.TempoCommunity.selectTab('tips')" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Tips
                        </button>
                        <button type="button" role="tab" data-community-tab="learn" onclick="window.TempoCommunity.selectTab('learn')" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Learn
                        </button>
                        <button type="button" role="tab" data-community-tab="posts" onclick="window.TempoCommunity.navigateToPostsFeed()" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Bài viết
                        </button>
                        <button type="button" role="tab" data-community-tab="messages" onclick="window.TempoCommunity.selectTab('messages')" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Tin nhắn riêng
                        </button>
                    </div>

                    <!-- Desktop Vertical Tab Navigation (Typography reduced to 14-15px) -->
                    <nav class="hidden lg:flex flex-col space-y-1.5" role="tablist" id="community-sidebar-nav">
                        <button type="button" role="tab" data-community-tab="announcement" onclick="window.TempoCommunity.selectTab('announcement')" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer bg-[#F7ECE1] text-[#DE8662]">
                            Thông báo
                        </button>

                        <button type="button" role="tab" data-community-tab="tips" onclick="window.TempoCommunity.selectTab('tips')" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Tips
                        </button>

                        <button type="button" role="tab" data-community-tab="learn" onclick="window.TempoCommunity.selectTab('learn')" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Learn
                        </button>

                        <!-- Requirement 5: Posts button always navigates to main Posts newsfeed -->
                        <button type="button" role="tab" data-community-tab="posts" onclick="window.TempoCommunity.navigateToPostsFeed()" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Bài viết
                        </button>

                        <button type="button" role="tab" data-community-tab="messages" onclick="window.TempoCommunity.selectTab('messages')" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Tin nhắn riêng
                        </button>
                    </nav>'''

# 2. Posts top action bar
old_toolbar = '''                        <!-- Top Action Bar (Reference 4) -->
                        <div class="flex items-center space-x-2.5">
                            <!-- New Post Button -->
                            <button type="button" onclick="window.TempoCommunity.openCreatePostModal()" 
                                    class="bg-[#DCE7EB] hover:bg-[#CAD9DF] text-[#2D2A26] px-4 py-2 rounded-full font-bold text-xs transition shadow-2xs cursor-pointer flex items-center space-x-1.5 shrink-0">
                                <span>New post</span>
                            </button>

                            <!-- Stable Flex Search Input (Zero Overlap, Requirement 1) -->
                            <div class="relative flex items-center flex-1 bg-[#F2EAE3] rounded-full px-3.5 py-2 space-x-2.5 transition shadow-2xs">
                                <svg class="w-3.5 h-3.5 text-[#736F68] shrink-0 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                                <input type="text" id="posts-search-input" 
                                       oninput="window.TempoCommunity.handlePostsSearch(this.value)"
                                       placeholder="Search..." 
                                       class="w-full bg-transparent border-none text-[13px] text-[#2D2A26] placeholder-[#8E8A85] focus:outline-none p-0 leading-normal">
                            </div>

                            <!-- Your Posts Button -->
                            <button type="button" onclick="window.TempoCommunity.filterMyPosts()" 
                                    class="bg-[#DFB59F] hover:bg-[#D4A38A] text-[#2D2A26] px-3.5 py-2 rounded-full font-bold text-xs transition shadow-2xs cursor-pointer shrink-0">
                                <span>Your posts</span>
                            </button>

                            <!-- Bell Notifications Button -->
                            <button type="button" onclick="if(window.TempoApp) window.TempoApp.showToast('No new notifications');" 
                                    class="bg-[#F3DCD0] hover:bg-[#E9CDBC] text-[#5A5550] p-2 rounded-full transition shadow-2xs cursor-pointer shrink-0" title="Notifications">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                                </svg>
                            </button>

                            <!-- Bookmark Button -->
                            <button type="button" onclick="window.TempoCommunity.filterBookmarkedPosts()" 
                                    class="bg-[#F3DCD0] hover:bg-[#E9CDBC] text-[#5A5550] p-2 rounded-full transition shadow-2xs cursor-pointer shrink-0 flex items-center justify-center" aria-label="Bookmarked Posts" title="Bookmarks">
                                <img src="assets/bookmark_ribbon_icon.png" alt="Bookmarks" class="w-3.5 h-3.5 object-contain">
                            </button>
                        </div>'''

new_toolbar = '''                        <!-- Top Action Bar (Reference 4) -->
                        <div class="flex items-center space-x-2.5">
                            <!-- New Post Button -->
                            <button type="button" id="btn-posts-new" onclick="window.TempoCommunity.openCreatePostModal()" 
                                    class="bg-[#DCE7EB] hover:bg-[#CAD9DF] text-[#2D2A26] px-4 py-2 rounded-full font-bold text-xs transition shadow-2xs cursor-pointer flex items-center space-x-1.5 shrink-0">
                                <span id="label-posts-new">Đăng bài mới</span>
                            </button>

                            <!-- Stable Flex Search Input (Zero Overlap, Requirement 1) -->
                            <div class="relative flex items-center flex-1 bg-[#F2EAE3] rounded-full px-3.5 py-2 space-x-2.5 transition shadow-2xs">
                                <svg class="w-3.5 h-3.5 text-[#736F68] shrink-0 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                                <input type="text" id="posts-search-input" 
                                       oninput="window.TempoCommunity.handlePostsSearch(this.value)"
                                       placeholder="Tìm kiếm..." 
                                       class="w-full bg-transparent border-none text-[13px] text-[#2D2A26] placeholder-[#8E8A85] focus:outline-none p-0 leading-normal">
                            </div>

                            <!-- Your Posts Button -->
                            <button type="button" id="btn-posts-filter-my" onclick="window.TempoCommunity.filterMyPosts()" 
                                    class="bg-[#DFB59F] hover:bg-[#D4A38A] text-[#2D2A26] px-3.5 py-2 rounded-full font-bold text-xs transition shadow-2xs cursor-pointer shrink-0">
                                <span id="label-posts-filter-my">Bài viết của tôi</span>
                            </button>

                            <!-- Bell Notifications Button -->
                            <button type="button" id="btn-posts-notifications" onclick="if(window.TempoApp) window.TempoApp.showToast(window.TempoI18n && window.TempoI18n.getLocale() === 'vi' ? 'Không có thông báo mới' : 'No new notifications');" 
                                    class="bg-[#F3DCD0] hover:bg-[#E9CDBC] text-[#5A5550] p-2 rounded-full transition shadow-2xs cursor-pointer shrink-0" title="Thông báo" aria-label="Thông báo">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                                </svg>
                            </button>

                            <!-- Bookmark Button -->
                            <button type="button" id="btn-posts-filter-bookmarks" onclick="window.TempoCommunity.filterBookmarkedPosts()" 
                                    class="bg-[#F3DCD0] hover:bg-[#E9CDBC] text-[#5A5550] p-2 rounded-full transition shadow-2xs cursor-pointer shrink-0 flex items-center justify-center" aria-label="Bài viết đã lưu" title="Bài viết đã lưu">
                                <img src="assets/bookmark_ribbon_icon.png" alt="Bookmarks" class="w-3.5 h-3.5 object-contain">
                            </button>
                        </div>'''

# 3. Script version tags
old_scripts = '''    <script src="i18n.js?v=20261101.23"></script>
    <script src="auth.js?v=20261031.1"></script>
    <script src="volunteer.js"></script>

    <!-- Core App Controllers -->
    <script src="data.js"></script>
    <script src="triage.js"></script>
    <script src="stress.js"></script>
    <script src="routine.js"></script>
    <script src="knowledge.js"></script>
    <script src="support.js"></script>
    <script src="admin.js"></script>
    <script src="emergencySupport.js"></script>
    <script src="communityPosts.js?v=20261101.3"></script>'''

new_scripts = '''    <script src="i18n.js?v=20261101.25"></script>
    <script src="auth.js?v=20261031.1"></script>
    <script src="volunteer.js"></script>

    <!-- Core App Controllers -->
    <script src="data.js"></script>
    <script src="triage.js"></script>
    <script src="stress.js"></script>
    <script src="routine.js"></script>
    <script src="knowledge.js"></script>
    <script src="support.js"></script>
    <script src="admin.js"></script>
    <script src="emergencySupport.js"></script>
    <script src="communityPosts.js?v=20261101.5"></script>'''

assert old_sidebar_section in content, "old_sidebar_section not found"
assert old_toolbar in content, "old_toolbar not found"
assert old_scripts in content, "old_scripts not found"

content = content.replace(old_sidebar_section, new_sidebar_section)
content = content.replace(old_toolbar, new_toolbar)
content = content.replace(old_scripts, new_scripts)

# Strictly preserve LF line endings (0 CRLFs)
content_lf = content.replace('\r\n', '\n')

with open('index.html', 'wb') as f:
    f.write(content_lf.encode('utf-8'))

print("index.html updated successfully with strict LF.")
