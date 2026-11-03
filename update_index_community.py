import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Locate section #screen-community
start_pattern = r'<section id="screen-community"[\s\S]*?</section>'
match = re.search(start_pattern, content)

if not match:
    print("Could not find screen-community!")
    exit(1)

print("Found screen-community from index", match.start(), "to", match.end())

new_screen_community = r'''<section id="screen-community" class="screen-container hidden space-y-6 bg-[#FEFAF4] -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8 py-6 sm:py-8 min-h-[calc(100vh-140px)]">
            <!-- Two-Column Layout (Desktop Sidebar + Content Area) -->
            <div class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                
                <!-- Left Sidebar Navigation (Matching References 1-5) -->
                <aside class="lg:col-span-3 xl:col-span-3 w-full">
                    <!-- Return Home Navigation Button -->
                    <div class="mb-6">
                        <button type="button" id="btn-community-back" onclick="window.TempoCommunity.handleReturnNavigation()" 
                                class="inline-flex items-center space-x-2 text-[17px] font-bold text-[#5A5550] hover:text-[#DE8662] transition cursor-pointer">
                            <span class="text-xl">←</span>
                            <span id="community-back-label">Return Home</span>
                        </button>
                    </div>

                    <!-- Mobile Horizontal Tab Strip (shown on mobile, hidden on lg) -->
                    <div class="lg:hidden flex items-center space-x-2 overflow-x-auto pb-4 scrollbar-none" role="tablist">
                        <button type="button" role="tab" data-community-tab="announcement" onclick="window.TempoCommunity.selectTab('announcement')" 
                                class="community-mobile-tab-btn px-4 py-2 rounded-full text-xs font-bold transition whitespace-nowrap bg-[#F7ECE1] text-[#DE8662]">
                            Announcement
                        </button>
                        <button type="button" role="tab" data-community-tab="tips" onclick="window.TempoCommunity.selectTab('tips')" 
                                class="community-mobile-tab-btn px-4 py-2 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Tips
                        </button>
                        <button type="button" role="tab" data-community-tab="learn" onclick="window.TempoCommunity.selectTab('learn')" 
                                class="community-mobile-tab-btn px-4 py-2 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Learn
                        </button>
                        <button type="button" role="tab" data-community-tab="posts" onclick="window.TempoCommunity.selectTab('posts')" 
                                class="community-mobile-tab-btn px-4 py-2 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Posts
                        </button>
                        <button type="button" role="tab" data-community-tab="messages" onclick="window.TempoCommunity.selectTab('messages')" 
                                class="community-mobile-tab-btn px-4 py-2 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Direct Message
                        </button>
                    </div>

                    <!-- Desktop Vertical Tab Navigation (Matching References 1-5) -->
                    <nav class="hidden lg:flex flex-col space-y-2" role="tablist" id="community-sidebar-nav">
                        <button type="button" role="tab" data-community-tab="announcement" onclick="window.TempoCommunity.selectTab('announcement')" 
                                class="community-nav-item w-full flex items-center px-5 py-3 rounded-2xl text-[19px] sm:text-[20px] font-bold transition text-left cursor-pointer bg-[#F7ECE1] text-[#DE8662]">
                            Announcement
                        </button>

                        <button type="button" role="tab" data-community-tab="tips" onclick="window.TempoCommunity.selectTab('tips')" 
                                class="community-nav-item w-full flex items-center px-5 py-3 rounded-2xl text-[19px] sm:text-[20px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Tips
                        </button>

                        <button type="button" role="tab" data-community-tab="learn" onclick="window.TempoCommunity.selectTab('learn')" 
                                class="community-nav-item w-full flex items-center px-5 py-3 rounded-2xl text-[19px] sm:text-[20px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Learn
                        </button>

                        <button type="button" role="tab" data-community-tab="posts" onclick="window.TempoCommunity.selectTab('posts')" 
                                class="community-nav-item w-full flex items-center px-5 py-3 rounded-2xl text-[19px] sm:text-[20px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Posts
                        </button>

                        <button type="button" role="tab" data-community-tab="messages" onclick="window.TempoCommunity.selectTab('messages')" 
                                class="community-nav-item w-full flex items-center px-5 py-3 rounded-2xl text-[19px] sm:text-[20px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Direct Message
                        </button>
                    </nav>

                    <!-- Optional Admin Button if admin -->
                    <div class="pt-6 hidden" id="admin-actions-container">
                        <button type="button" id="btn-admin-new-announcement" onclick="window.TempoCommunity.openNewAnnouncementModal()" 
                                class="hidden px-4 py-2 rounded-xl bg-[#DE8662] hover:bg-[#C9724F] text-white font-bold text-xs flex items-center space-x-1.5 shadow-xs transition cursor-pointer">
                            <span>📢</span>
                            <span>+ New Announcement</span>
                        </button>
                    </div>
                </aside>

                <!-- Right Main Content Area -->
                <main class="lg:col-span-9 xl:col-span-9 w-full min-w-0">
                    
                    <!-- PANEL 1: ANNOUNCEMENT (Reference 1) -->
                    <div id="community-panel-announcement" class="community-panel space-y-6">
                        <!-- Announcements Stacked List -->
                        <div id="community-announcements-list" class="space-y-6 flex flex-col">
                            <!-- Populated dynamically by communityPosts.js -->
                        </div>

                        <!-- Empty State -->
                        <div id="community-announcements-empty" class="hidden text-center py-12 px-4 bg-white border border-[#ECA689] rounded-3xl space-y-3">
                            <h3 class="font-heading text-lg font-bold text-[#4A4541]">No announcements at this time</h3>
                            <p class="text-xs text-[#6E6964]">Check back soon for system updates and new feature releases.</p>
                        </div>
                    </div>

                    <!-- PANEL 2: TIPS (SOLVE) (Reference 2) -->
                    <div id="community-panel-tips" class="community-panel space-y-6 hidden">
                        <!-- Capsule Search Bar (Reference 2) -->
                        <div class="relative w-full">
                            <div class="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none text-[#736F68]">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            </div>
                            <input type="text" id="tips-search-input" 
                                   oninput="window.TempoCommunity.handleTipsSearch(this.value)"
                                   placeholder="Search..." 
                                   class="w-full pl-13 pr-6 py-3.5 text-base bg-[#F2EAE3] border-none rounded-full text-[#2D2A26] placeholder-[#8E8A85] focus:outline-none focus:ring-2 focus:ring-[#DE8662]/30 transition shadow-2xs">
                        </div>

                        <!-- Tips Cards Grid (2 columns, Reference 2) -->
                        <div id="tips-cards-grid" class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <!-- Populated dynamically by communityPosts.js -->
                        </div>

                        <!-- Empty State -->
                        <div id="tips-empty-state" class="hidden text-center py-12 px-4 bg-white border border-[#ECA689] rounded-3xl space-y-3">
                            <h3 class="font-heading text-base font-bold text-[#4A4541]">No matching solutions found</h3>
                            <p class="text-xs text-[#6E6964]">Try searching with different terms.</p>
                            <button type="button" onclick="window.TempoCommunity.clearTipsSearch();" 
                                    class="px-4 py-2 rounded-xl bg-[#F7ECE1] text-[#DE8662] font-bold text-xs">
                                Reset Search
                            </button>
                        </div>
                    </div>

                    <!-- PANEL 3: LEARN (Reference 3) -->
                    <div id="community-panel-learn" class="community-panel space-y-6 hidden">
                        <!-- Capsule Search Bar (Reference 3) -->
                        <div class="relative w-full">
                            <div class="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none text-[#736F68]">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            </div>
                            <input type="text" id="learn-search-input" 
                                   oninput="window.TempoCommunity.handleLearnSearch(this.value)"
                                   placeholder="Search..." 
                                   class="w-full pl-13 pr-6 py-3.5 text-base bg-[#F2EAE3] border-none rounded-full text-[#2D2A26] placeholder-[#8E8A85] focus:outline-none focus:ring-2 focus:ring-[#DE8662]/30 transition shadow-2xs">
                        </div>

                        <!-- Learn Cards Stacked (Reference 3) -->
                        <div id="learn-cards-grid" class="space-y-6 flex flex-col">
                            <!-- Populated dynamically by communityPosts.js -->
                        </div>

                        <!-- Empty State -->
                        <div id="learn-empty-state" class="hidden text-center py-12 px-4 bg-white border border-[#ECA689] rounded-3xl space-y-3">
                            <h3 class="font-heading text-base font-bold text-[#4A4541]">No educational topics found</h3>
                            <p class="text-xs text-[#6E6964]">Try searching with a broader keyword or clearing your search.</p>
                            <button type="button" onclick="window.TempoCommunity.clearLearnSearch();" 
                                    class="px-4 py-2 rounded-xl bg-[#F7ECE1] text-[#DE8662] font-bold text-xs">
                                Reset Search
                            </button>
                        </div>
                    </div>

                    <!-- PANEL 4: POSTS (Reference 4) -->
                    <div id="community-panel-posts" class="community-panel space-y-6 hidden">
                        <!-- Top Action Bar (Reference 4) -->
                        <div class="flex items-center space-x-3">
                            <!-- New Post Pill Button -->
                            <button type="button" onclick="window.TempoCommunity.openCreatePostModal()" 
                                    class="bg-[#DCE7EB] hover:bg-[#CAD9DF] text-[#2D2A26] px-5 py-2.5 rounded-full font-bold text-sm transition shadow-2xs cursor-pointer flex items-center space-x-1.5 shrink-0">
                                <span>New post</span>
                            </button>

                            <!-- Capsule Search Input -->
                            <div class="relative flex-1">
                                <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-[#736F68]">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                    </svg>
                                </div>
                                <input type="text" id="posts-search-input" 
                                       oninput="window.TempoCommunity.handlePostsSearch(this.value)"
                                       placeholder="Search..." 
                                       class="w-full pl-11 pr-4 py-2.5 text-sm bg-[#F2EAE3] border-none rounded-full text-[#2D2A26] placeholder-[#8E8A85] focus:outline-none focus:ring-2 focus:ring-[#DE8662]/30 transition shadow-2xs">
                            </div>

                            <!-- Your Posts Button -->
                            <button type="button" onclick="window.TempoCommunity.filterMyPosts()" 
                                    class="bg-[#DFB59F] hover:bg-[#D4A38A] text-[#2D2A26] px-4 py-2.5 rounded-full font-bold text-sm transition shadow-2xs cursor-pointer shrink-0">
                                <span>Your posts</span>
                            </button>

                            <!-- Bell Notifications Button -->
                            <button type="button" onclick="if(window.TempoApp) window.TempoApp.showToast('No new notifications');" 
                                    class="bg-[#F3DCD0] hover:bg-[#E9CDBC] text-[#5A5550] p-2.5 rounded-full transition shadow-2xs cursor-pointer shrink-0" title="Notifications">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                                </svg>
                            </button>

                            <!-- Bookmark Button -->
                            <button type="button" onclick="window.TempoCommunity.filterBookmarkedPosts()" 
                                    class="bg-[#F3DCD0] hover:bg-[#E9CDBC] text-[#5A5550] p-2.5 rounded-full transition shadow-2xs cursor-pointer shrink-0" title="Bookmarks">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                                </svg>
                            </button>
                        </div>

                        <!-- Posts Feed List (Reference 4) -->
                        <div id="community-feed-posts-list" class="space-y-6">
                            <!-- Populated dynamically by communityPosts.js -->
                        </div>

                        <!-- Empty State -->
                        <div id="community-posts-empty" class="hidden text-center py-12 px-4 bg-white border border-[#4A4541] rounded-3xl space-y-3">
                            <h3 class="font-heading text-base font-bold text-[#4A4541]">No posts found</h3>
                            <p class="text-xs text-[#6E6964]">Be the first to share your thoughts or questions.</p>
                        </div>
                    </div>

                    <!-- PANEL 5: DIRECT MESSAGE (Reference 5) -->
                    <div id="community-panel-messages" class="community-panel space-y-6 hidden">
                        <!-- Guest Unauthenticated View (if any) -->
                        <div id="community-dm-guest-view" class="p-8 sm:p-12 text-center bg-white border border-[#EAE4DF] rounded-3xl space-y-4 max-w-xl mx-auto shadow-xs hidden">
                            <div class="w-14 h-14 rounded-2xl bg-[#F7ECE1] text-[#DE8662] flex items-center justify-center mx-auto text-2xl font-bold">
                                ✉️
                            </div>
                            <div class="space-y-1.5">
                                <h3 class="font-heading text-lg font-bold text-[#202124]">Sign in for Direct Mentorship</h3>
                                <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                                    Direct messaging allows private, confidential conversations between you and mentors.
                                </p>
                            </div>
                            <div>
                                <button type="button" 
                                        onclick="if(window.TempoAuth && typeof window.TempoAuth.openSignInModal === 'function') window.TempoAuth.openSignInModal();"
                                        class="bg-[#DFB59F] text-white px-6 py-2.5 rounded-full font-bold text-xs shadow-xs transition cursor-pointer">
                                    Sign In to Access Messages
                                </button>
                            </div>
                        </div>

                        <!-- Unified Direct Message Card (Reference 5) -->
                        <div id="community-dm-auth-view" class="bg-white border border-[#EAE4DF] rounded-3xl overflow-hidden shadow-xs grid grid-cols-1 md:grid-cols-12 min-h-[620px]">
                            
                            <!-- Left Column: Conversations List -->
                            <div id="dm-conversations-column" class="md:col-span-5 lg:col-span-5 border-r border-[#EAE4DF] flex flex-col bg-white">
                                <!-- Search & Action Icons -->
                                <div class="p-4 border-b border-[#EAE4DF] flex items-center space-x-2">
                                    <div class="relative flex-1">
                                        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#736F68]">
                                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                            </svg>
                                        </div>
                                        <input type="text" id="dm-search-conversations" 
                                               oninput="window.TempoCommunity.handleDMSearch(this.value)"
                                               placeholder="Search..." 
                                               class="w-full pl-9 pr-3 py-2 text-xs sm:text-sm bg-[#F2EAE3] border-none rounded-full text-[#2D2A26] placeholder-[#8E8A85] focus:outline-none focus:ring-1 focus:ring-[#DE8662]">
                                    </div>
                                    <button type="button" onclick="if(window.TempoApp) window.TempoApp.showToast('Messages');" class="p-2 rounded-full hover:bg-stone-100 text-[#5A5550] text-sm cursor-pointer" title="Messages">💬</button>
                                    <button type="button" onclick="if(window.TempoApp) window.TempoApp.showToast('Create Group');" class="p-2 rounded-full hover:bg-stone-100 text-[#5A5550] text-sm cursor-pointer" title="New Group">👥</button>
                                </div>

                                <!-- Conversations Scrollable List -->
                                <div id="dm-conversations-list" class="flex-1 overflow-y-auto p-3 space-y-1.5 max-h-[540px]">
                                    <!-- Populated dynamically by communityPosts.js -->
                                </div>
                            </div>

                            <!-- Right Column: Active Chat Thread -->
                            <div id="dm-chat-column" class="md:col-span-7 lg:col-span-7 flex flex-col bg-[#FAF8F5] hidden md:flex">
                                <!-- Chat Header -->
                                <div class="p-4 border-b border-[#EAE4DF] bg-white flex items-center justify-between">
                                    <div class="flex items-center space-x-3">
                                        <button type="button" id="btn-dm-mobile-back" onclick="window.TempoCommunity.mobileToggleConversation(false)" 
                                                class="md:hidden text-[#736F68] hover:text-[#202124] p-1 font-bold text-sm">
                                            ← Back
                                        </button>
                                        <img id="dm-active-avatar" src="assets/avatar_koala.jpg" 
                                             alt="Group Avatar" class="w-10 h-10 rounded-full object-cover border border-stone-200">
                                        <div>
                                            <h4 id="dm-active-name" class="text-sm sm:text-base font-bold text-[#202124]">Go Badmintonnnn</h4>
                                            <p id="dm-active-role" class="text-xs text-[#8E8A85]">You, Innie, FPT Bá Khí and 3 others</p>
                                        </div>
                                    </div>
                                </div>

                                <!-- Messages Container -->
                                <div id="dm-messages-container" class="flex-1 p-5 sm:p-6 overflow-y-auto space-y-4 max-h-[460px]">
                                    <!-- Populated dynamically by communityPosts.js -->
                                </div>

                                <!-- Message Input Row (Reference 5) -->
                                <div class="p-4 bg-white border-t border-[#EAE4DF]">
                                    <form id="dm-message-form" onsubmit="window.TempoCommunity.handleSendMessage(event)" class="flex items-center space-x-2.5">
                                        <button type="button" onclick="if(window.TempoApp) window.TempoApp.showToast('Attach media');" 
                                                class="w-9 h-9 rounded-full bg-[#F2EAE3] hover:bg-[#EAE1D9] text-[#5A5550] flex items-center justify-center text-lg font-bold shrink-0 cursor-pointer">+</button>
                                        <input type="text" id="dm-message-input" 
                                               placeholder="Type a message..." 
                                               class="flex-1 px-4 py-2.5 text-xs sm:text-sm bg-[#F2EAE3] border-none rounded-full text-[#2D2A26] placeholder-[#8E8A85] focus:outline-none focus:ring-1 focus:ring-[#DE8662]">
                                        <button type="submit" id="btn-dm-send" 
                                                class="w-9 h-9 rounded-full bg-[#DFB59F] hover:bg-[#D4A38A] text-white flex items-center justify-center text-sm font-bold shrink-0 shadow-2xs cursor-pointer">
                                            ➤
                                        </button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>

                </main>
            </div>
        </section>'''

content = content[:match.start()] + new_screen_community + content[match.end():]

# Check if modal-create-post already exists
if 'id="modal-create-post"' not in content:
    # Add modal-create-post right after modal-announcement-create
    modal_post_html = r'''
    <!-- 4d. CREATE POST MODAL (Reference 4) -->
    <div id="modal-create-post" class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-3 sm:p-6 overflow-y-auto hidden">
        <div class="tempo-card max-w-lg w-full max-h-[90vh] overflow-y-auto bg-white rounded-3xl p-6 sm:p-8 space-y-5 relative shadow-2xl">
            <div class="flex items-center justify-between pb-3 border-b border-gray-100">
                <h3 class="font-heading text-lg font-bold text-[#202124]">Create a Post</h3>
                <button type="button" onclick="window.TempoCommunity.closeCreatePostModal()" class="text-gray-400 hover:text-gray-700 p-1.5 rounded-lg text-lg transition cursor-pointer">✕</button>
            </div>
            <form id="form-modal-create-post" onsubmit="window.TempoCommunity.handleCreateCommunityPost(event)" class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold text-[#202124] mb-1">Your Thoughts / Question</label>
                    <textarea id="input-modal-post-content" rows="4" placeholder="What's on your mind? Share study wins, questions, or encouragement..." required
                              class="w-full p-3.5 text-xs sm:text-sm bg-[#FAF8F5] border border-[#EAE4DF] rounded-2xl focus:outline-none focus:border-[#DE8662] resize-none"></textarea>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 items-center">
                    <div>
                        <label class="block text-xs font-semibold text-[#202124] mb-1">Category Tag</label>
                        <select id="select-modal-post-tag" class="w-full px-3 py-2 text-xs bg-[#FAF8F5] border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#DE8662]">
                            <option value="#mental health">#mental health</option>
                            <option value="#Deadline">#Deadline</option>
                            <option value="#Focus zone">#Focus zone</option>
                            <option value="#Background">#Background</option>
                            <option value="#Recovery">#Recovery</option>
                        </select>
                    </div>
                    <div class="pt-5 flex items-center space-x-2">
                        <input type="checkbox" id="checkbox-modal-post-anon" checked class="text-[#DE8662] focus:ring-[#DE8662] rounded">
                        <label for="checkbox-modal-post-anon" class="text-xs font-medium text-[#5A5550] cursor-pointer">Post anonymously</label>
                    </div>
                </div>
                <div class="pt-3 border-t border-gray-100 flex items-center justify-end space-x-2">
                    <button type="button" onclick="window.TempoCommunity.closeCreatePostModal()" 
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-[#736F68] hover:bg-stone-100 transition cursor-pointer">
                        Cancel
                    </button>
                    <button type="submit" class="bg-[#DFB59F] hover:bg-[#D4A38A] text-white px-5 py-2 rounded-xl text-xs font-bold transition shadow-2xs cursor-pointer">
                        Publish Post
                    </button>
                </div>
            </form>
        </div>
    </div>
'''
    ann_create_end = content.find('</div>', content.find('id="modal-announcement-create"'))
    # Find the closing </div> of modal-announcement-create (which has 2 nested divs)
    # Better: find `<!-- 4c. ADMIN: CREATE ANNOUNCEMENT MODAL -->` closing div:
    # Look for the next modal or next comment after modal-announcement-create
    ann_create_idx = content.find('id="modal-announcement-create"')
    # Find the closing </form> then the 2 </div>s
    form_end = content.find('</form>', ann_create_idx)
    div1 = content.find('</div>', form_end)
    div2 = content.find('</div>', div1 + 6)
    insert_pos = div2 + 6
    content = content[:insert_pos] + '\n' + modal_post_html + content[insert_pos:]
    print("Inserted modal-create-post at index", insert_pos)

# Write back preserving CRLF
content_crlf = content.replace('\r\n', '\n').replace('\n', '\r\n')
with open('index.html', 'wb') as f:
    f.write(content_crlf.encode('utf-8'))

print("Updated index.html successfully with CRLF.")
