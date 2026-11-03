import re

# Read current index.html
with open('index.html', 'rb') as f:
    raw = f.read().decode('utf-8')

# Ensure CRLF
is_crlf = '\r\n' in raw

# 1. Update Desktop Navbar: Remove Learn and rename Post to Community
old_nav_pattern = r'''<a id="nav-link-learn" href="#learn" data-nav="learn" onclick="window\.TempoApp\.navigateTo\('learn'\); return false;" class="text-\[#736F68\] hover:text-\[#FF6B2C\] transition whitespace-nowrap">\s*Learn\s*</a>\s*<a id="nav-link-posts" href="#posts" onclick="[^"]*" class="text-\[#736F68\] hover:text-\[#FF6B2C\] transition whitespace-nowrap">\s*Post\s*</a>'''

new_nav_item = '''<a id="nav-link-community" href="#community" data-nav="community" onclick="window.TempoApp.navigateTo('community'); return false;" class="text-[#736F68] hover:text-[#FF6B2C] transition whitespace-nowrap">
                    Community
                </a>'''

if not re.search(old_nav_pattern, raw):
    print("Warning: old nav pattern not found with regex! Searching manually...")
    # Find manually
    target_nav = '<a id="nav-link-learn"'
    idx = raw.find(target_nav)
    if idx != -1:
        end_idx = raw.find('</a>', raw.find('<a id="nav-link-posts"', idx)) + 4
        print(f"Replacing nav region from {idx} to {end_idx}")
        raw = raw[:idx] + new_nav_item + raw[end_idx:]
    else:
        print("Could not find nav-link-learn")
else:
    raw = re.sub(old_nav_pattern, new_nav_item, raw, count=1)
    print("Successfully replaced desktop navbar links.")

# 2. Update Mobile Bottom Navbar: Replace Learn with Community
old_mobile_learn = r'''<a href="#learn" data-nav="learn" onclick="window\.TempoApp\.navigateTo\('learn'\); return false;" class="flex flex-col items-center text-\[10px\] text-gray-500">\s*<span class="text-base">📚</span>\s*<span>Learn</span>\s*</a>'''

new_mobile_community = '''<a href="#community" data-nav="community" onclick="window.TempoApp.navigateTo('community'); return false;" class="flex flex-col items-center text-[10px] text-gray-500">
            <span class="text-base">👥</span>
            <span>Community</span>
        </a>'''

if re.search(old_mobile_learn, raw):
    raw = re.sub(old_mobile_learn, new_mobile_community, raw, count=1)
    print("Successfully replaced mobile bottom navbar Learn link with Community.")
else:
    print("Warning: old mobile learn pattern not matched with regex, finding manually...")
    idx = raw.find('data-nav="learn"')
    if idx != -1:
        start_a = raw.rfind('<a', 0, idx)
        end_a = raw.find('</a>', idx) + 4
        raw = raw[:start_a] + new_mobile_community + raw[end_a:]
        print("Manually replaced mobile bottom navbar.")

# 3. Insert screen-community right before screen-learn
community_screen_html = '''        <!-- ===================================================================
             SCREEN: TEMPO COMMUNITY (UNIFIED HUB)
             =================================================================== -->
        <section id="screen-community" class="screen-container hidden space-y-6 bg-[#FEFAF4] -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8 py-6 sm:py-8 min-h-[calc(100vh-140px)]">
            <!-- 1. Header with Return Navigation & Admin Trigger -->
            <div class="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-[#EAE4DF]">
                <div class="space-y-1.5">
                    <div class="flex items-center space-x-2.5">
                        <button type="button" id="btn-community-back" onclick="window.TempoCommunity.handleReturnNavigation()" 
                                class="inline-flex items-center space-x-1.5 text-xs font-bold text-[#736F68] hover:text-[#FF6B2C] bg-white border border-[#EAE4DF] hover:border-[#FF6B2C] px-3 py-1.5 rounded-full transition shadow-2xs cursor-pointer">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                            <span id="community-back-label">Back to Today</span>
                        </button>
                        <span class="text-xs font-bold uppercase tracking-wider text-[#FF6B2C] bg-[#FFE9DC] px-2.5 py-0.5 rounded-full">Community Hub</span>
                    </div>
                    <h1 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">Tempo Community</h1>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">Official updates, actionable tips, stress education, peer discussions, and direct mentorship.</p>
                </div>

                <!-- Admin Action Button -->
                <div class="flex items-center space-x-2">
                    <button type="button" id="btn-admin-new-announcement" onclick="window.TempoCommunity.openNewAnnouncementModal()" 
                            class="hidden px-4 py-2 rounded-xl bg-[#FF6B2C] hover:bg-[#E55A1F] text-white font-bold text-xs flex items-center space-x-1.5 shadow-xs transition cursor-pointer">
                        <span>📢</span>
                        <span>+ New Announcement</span>
                    </button>
                </div>
            </div>

            <!-- Mobile Horizontal Tab Strip -->
            <div class="lg:hidden flex items-center space-x-2 overflow-x-auto pb-2 scrollbar-none max-w-7xl mx-auto" role="tablist">
                <button type="button" role="tab" data-community-tab="announcement" onclick="window.TempoCommunity.selectTab('announcement')" 
                        class="community-mobile-tab-btn px-4 py-2 rounded-full text-xs font-bold transition whitespace-nowrap bg-[#FF6B2C] text-white shadow-2xs">
                    📢 Announcement
                </button>
                <button type="button" role="tab" data-community-tab="tips" onclick="window.TempoCommunity.selectTab('tips')" 
                        class="community-mobile-tab-btn px-4 py-2 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]">
                    💡 Tips (Solve)
                </button>
                <button type="button" role="tab" data-community-tab="learn" onclick="window.TempoCommunity.selectTab('learn')" 
                        class="community-mobile-tab-btn px-4 py-2 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]">
                    🧠 Learn
                </button>
                <button type="button" role="tab" data-community-tab="posts" onclick="window.TempoCommunity.selectTab('posts')" 
                        class="community-mobile-tab-btn px-4 py-2 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]">
                    💬 Posts
                </button>
                <button type="button" role="tab" data-community-tab="messages" onclick="window.TempoCommunity.selectTab('messages')" 
                        class="community-mobile-tab-btn px-4 py-2 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]">
                    ✉️ Direct Message
                </button>
            </div>

            <!-- 2. Two-Column Layout (Desktop Sidebar + Content Area) -->
            <div class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                <!-- Left Sidebar Navigation (Desktop) -->
                <aside class="hidden lg:block lg:col-span-3 xl:col-span-3 w-full">
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-3 sm:p-4 shadow-xs space-y-1.5 sticky top-20">
                        <div class="px-3 py-1.5 text-[11px] font-bold text-[#8E8A85] uppercase tracking-wider">
                            Community Categories
                        </div>
                        <nav class="space-y-1" role="tablist" id="community-sidebar-nav">
                            <button type="button" role="tab" data-community-tab="announcement" onclick="window.TempoCommunity.selectTab('announcement')" 
                                    class="community-nav-item w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs font-bold transition text-left cursor-pointer bg-[#FFE9DC] text-[#B83D08] shadow-2xs">
                                <div class="flex items-center space-x-2.5">
                                    <span class="text-base select-none">📢</span>
                                    <span>Announcement</span>
                                </div>
                                <span id="badge-announcements-count" class="text-[10px] px-2 py-0.5 rounded-full bg-[#FF6B2C] text-white font-bold">3</span>
                            </button>

                            <button type="button" role="tab" data-community-tab="tips" onclick="window.TempoCommunity.selectTab('tips')" 
                                    class="community-nav-item w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs font-medium transition text-left cursor-pointer text-[#6F6B68] hover:bg-[#F8F6F4] hover:text-[#202124]">
                                <div class="flex items-center space-x-2.5">
                                    <span class="text-base select-none">💡</span>
                                    <span>Tips (Solve)</span>
                                </div>
                                <span class="text-[10px] px-2 py-0.5 rounded-full bg-[#F3F1EF] text-[#6F6B68] font-medium">Action</span>
                            </button>

                            <button type="button" role="tab" data-community-tab="learn" onclick="window.TempoCommunity.selectTab('learn')" 
                                    class="community-nav-item w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs font-medium transition text-left cursor-pointer text-[#6F6B68] hover:bg-[#F8F6F4] hover:text-[#202124]">
                                <div class="flex items-center space-x-2.5">
                                    <span class="text-base select-none">🧠</span>
                                    <span>Learn</span>
                                </div>
                                <span class="text-[10px] px-2 py-0.5 rounded-full bg-[#F3F1EF] text-[#6F6B68] font-medium">Concepts</span>
                            </button>

                            <button type="button" role="tab" data-community-tab="posts" onclick="window.TempoCommunity.selectTab('posts')" 
                                    class="community-nav-item w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs font-medium transition text-left cursor-pointer text-[#6F6B68] hover:bg-[#F8F6F4] hover:text-[#202124]">
                                <div class="flex items-center space-x-2.5">
                                    <span class="text-base select-none">💬</span>
                                    <span>Posts</span>
                                </div>
                                <span class="text-[10px] px-2 py-0.5 rounded-full bg-[#F3F1EF] text-[#6F6B68] font-medium">Feed</span>
                            </button>

                            <button type="button" role="tab" data-community-tab="messages" onclick="window.TempoCommunity.selectTab('messages')" 
                                    class="community-nav-item w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs font-medium transition text-left cursor-pointer text-[#6F6B68] hover:bg-[#F8F6F4] hover:text-[#202124]">
                                <div class="flex items-center space-x-2.5">
                                    <span class="text-base select-none">✉️</span>
                                    <span>Direct Message</span>
                                </div>
                                <span class="text-[10px] px-2 py-0.5 rounded-full bg-[#F3F1EF] text-[#6F6B68] font-medium">Mentors</span>
                            </button>
                        </nav>
                    </div>
                </aside>

                <!-- Right Main Content Area -->
                <main class="lg:col-span-9 xl:col-span-9 w-full min-w-0">
                    <!-- ==========================================
                         PANEL 1: ANNOUNCEMENT
                         ========================================== -->
                    <div id="community-panel-announcement" class="community-panel space-y-5">
                        <div class="flex items-center justify-between">
                            <div>
                                <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Official Announcements</h2>
                                <p class="text-xs sm:text-sm text-[#6F6B68]">Product updates, new features, and community news from the Tempo team.</p>
                            </div>
                        </div>

                        <!-- Announcements Grid -->
                        <div id="community-announcements-list" class="grid grid-cols-1 md:grid-cols-2 gap-5 sm:gap-6">
                            <!-- Populated dynamically by communityPosts.js -->
                        </div>

                        <!-- Empty State -->
                        <div id="community-announcements-empty" class="hidden text-center py-12 px-4 bg-white border border-[#EAE4DF] rounded-3xl space-y-3">
                            <span class="text-3xl">📢</span>
                            <h3 class="font-heading text-base font-bold text-[#202124]">No announcements at this time</h3>
                            <p class="text-xs text-[#6F6B68]">Check back soon for system updates and new feature releases.</p>
                        </div>
                    </div>

                    <!-- ==========================================
                         PANEL 2: TIPS (SOLVE)
                         ========================================== -->
                    <div id="community-panel-tips" class="community-panel space-y-5 hidden">
                        <div>
                            <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Tips &amp; Solutions</h2>
                            <p class="text-xs sm:text-sm text-[#6F6B68]">Actionable, step-by-step strategies to resolve deadlines, study blocks, and academic overwhelm.</p>
                        </div>

                        <!-- Search Bar -->
                        <div class="relative max-w-xl">
                            <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#9E9B97]">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            </div>
                            <input type="text" id="tips-search-input" 
                                   oninput="window.TempoCommunity.handleTipsSearch(this.value)"
                                   placeholder="Search actionable tips, guides, or situations (e.g. deadline, sleep, email)..." 
                                   class="w-full pl-10 pr-10 py-2.5 text-xs sm:text-sm bg-white border border-[#EAE4DF] rounded-2xl text-[#202124] placeholder-[#A09D9A] shadow-xs focus:outline-none focus:border-[#FF6B2C] focus:ring-2 focus:ring-[#FF6B2C]/20 transition">
                            <button type="button" id="btn-clear-tips-search" onclick="window.TempoCommunity.clearTipsSearch()" 
                                    class="hidden absolute inset-y-0 right-0 pr-3.5 flex items-center text-[#9E9B97] hover:text-[#202124] transition text-sm cursor-pointer"
                                    title="Clear search">✕</button>
                        </div>

                        <!-- Category Filter Pills -->
                        <div class="flex items-center space-x-2 overflow-x-auto pb-1 scrollbar-none" id="tips-categories-container">
                            <button type="button" data-tips-category="all" onclick="window.TempoCommunity.filterTipsCategory('all')" 
                                    class="tips-category-pill px-3.5 py-1.5 rounded-full text-xs font-bold transition whitespace-nowrap bg-[#FF6B2C] text-white shadow-2xs">
                                All Solutions
                            </button>
                            <button type="button" data-tips-category="study" onclick="window.TempoCommunity.filterTipsCategory('study')" 
                                    class="tips-category-pill px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]">
                                📚 Study
                            </button>
                            <button type="button" data-tips-category="future" onclick="window.TempoCommunity.filterTipsCategory('future')" 
                                    class="tips-category-pill px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]">
                                💭 Myself &amp; Future
                            </button>
                            <button type="button" data-tips-category="work" onclick="window.TempoCommunity.filterTipsCategory('work')" 
                                    class="tips-category-pill px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]">
                                💼 Work &amp; Activities
                            </button>
                            <button type="button" data-tips-category="relationships" onclick="window.TempoCommunity.filterTipsCategory('relationships')" 
                                    class="tips-category-pill px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]">
                                🤝 Relationships
                            </button>
                            <button type="button" data-tips-category="life" onclick="window.TempoCommunity.filterTipsCategory('life')" 
                                    class="tips-category-pill px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]">
                                🌿 Life
                            </button>
                        </div>

                        <!-- Tips Cards Grid -->
                        <div id="tips-cards-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                            <!-- Populated dynamically by communityPosts.js -->
                        </div>

                        <!-- Empty State -->
                        <div id="tips-empty-state" class="hidden text-center py-12 px-4 bg-white border border-[#EAE4DF] rounded-3xl space-y-3">
                            <span class="text-3xl">🔍</span>
                            <h3 class="font-heading text-base font-bold text-[#202124]">No matching solutions found</h3>
                            <p class="text-xs text-[#6F6B68]">Try searching with different terms or selecting another category.</p>
                            <button type="button" onclick="window.TempoCommunity.clearTipsSearch(); window.TempoCommunity.filterTipsCategory('all');" 
                                    class="px-4 py-2 rounded-xl bg-[#FFE9DC] text-[#B83D08] font-bold text-xs">
                                Reset Filters
                            </button>
                        </div>
                    </div>

                    <!-- ==========================================
                         PANEL 3: LEARN (KNOWLEDGE LIBRARY)
                         ========================================== -->
                    <div id="community-panel-learn" class="community-panel space-y-5 hidden">
                        <div>
                            <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Learn About Stress</h2>
                            <p class="text-xs sm:text-sm text-[#6F6B68]">Foundational, non-diagnostic concepts explaining bodily stress signals, loops, and nervous system recovery.</p>
                        </div>

                        <!-- Search Bar -->
                        <div class="relative max-w-xl">
                            <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#9E9B97]">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            </div>
                            <input type="text" id="learn-search-input" 
                                   oninput="window.TempoCommunity.handleLearnSearch(this.value)"
                                   placeholder="Search educational stress concepts (e.g. loop, burnout, recovery)..." 
                                   class="w-full pl-10 pr-10 py-2.5 text-xs sm:text-sm bg-white border border-[#EAE4DF] rounded-2xl text-[#202124] placeholder-[#A09D9A] shadow-xs focus:outline-none focus:border-[#FF6B2C] focus:ring-2 focus:ring-[#FF6B2C]/20 transition">
                            <button type="button" id="btn-clear-learn-search" onclick="window.TempoCommunity.clearLearnSearch()" 
                                    class="hidden absolute inset-y-0 right-0 pr-3.5 flex items-center text-[#9E9B97] hover:text-[#202124] transition text-sm cursor-pointer"
                                    title="Clear search">✕</button>
                        </div>

                        <!-- Learn Cards Grid -->
                        <div id="learn-cards-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                            <!-- Populated dynamically by communityPosts.js -->
                        </div>

                        <!-- Empty State -->
                        <div id="learn-empty-state" class="hidden text-center py-12 px-4 bg-white border border-[#EAE4DF] rounded-3xl space-y-3">
                            <span class="text-3xl">🔍</span>
                            <h3 class="font-heading text-base font-bold text-[#202124]">No educational topics found</h3>
                            <p class="text-xs text-[#6F6B68]">Try searching with a broader keyword or clearing your search.</p>
                            <button type="button" onclick="window.TempoCommunity.clearLearnSearch();" 
                                    class="px-4 py-2 rounded-xl bg-[#FFE9DC] text-[#B83D08] font-bold text-xs">
                                Reset Search
                            </button>
                        </div>
                    </div>

                    <!-- ==========================================
                         PANEL 4: POSTS (COMMUNITY FEED)
                         ========================================== -->
                    <div id="community-panel-posts" class="community-panel space-y-5 hidden">
                        <div>
                            <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Peer Discussions &amp; Posts</h2>
                            <p class="text-xs sm:text-sm text-[#6F6B68]">Supportive, honest thoughts, study wins, and peer advice from university students.</p>
                        </div>

                        <!-- Share a Thought Box -->
                        <form id="community-create-post-form" class="p-5 bg-[#FFF8F2] border border-[#FFD2BA]/80 rounded-3xl space-y-3.5 shadow-xs">
                            <textarea id="community-post-content" rows="3" 
                                      placeholder="Share an encouraging thought, a deadline win, or ask fellow students for advice..." 
                                      class="w-full p-3.5 text-xs sm:text-sm bg-white border border-[#EAE4DF] rounded-2xl focus:outline-none focus:ring-2 focus:ring-[#FF6B2C]/20 focus:border-[#FF6B2C] placeholder-[#9E9B97] resize-none"></textarea>
                            
                            <div class="flex flex-wrap items-center justify-between gap-3 pt-1">
                                <div class="flex items-center space-x-3 text-xs flex-wrap gap-y-2">
                                    <div class="flex items-center space-x-1.5">
                                        <span class="text-[#736F68] font-semibold">Tag:</span>
                                        <select id="community-post-tag" class="text-xs bg-white border border-[#EAE4DF] rounded-xl px-2.5 py-1.5 text-[#202124] focus:outline-none focus:border-[#FF6B2C]">
                                            <option value="#Deadline">#Deadline</option>
                                            <option value="#MentalHealth">#MentalHealth</option>
                                            <option value="#Focus">#Focus</option>
                                            <option value="#Recovery">#Recovery</option>
                                            <option value="#General">#General</option>
                                        </select>
                                    </div>

                                    <label class="flex items-center space-x-1.5 text-[#6F6B68] cursor-pointer">
                                        <input id="community-post-anon" type="checkbox" checked class="text-[#FF6B2C] focus:ring-[#FF6B2C] rounded">
                                        <span class="font-medium">Post Anonymously</span>
                                    </label>
                                </div>

                                <button type="submit" class="btn-primary px-5 py-2 rounded-xl font-bold text-xs shadow-xs transition cursor-pointer">
                                    Post to Community
                                </button>
                            </div>
                        </form>

                        <!-- Tag Filter Pills -->
                        <div class="flex items-center space-x-2 overflow-x-auto pb-1 scrollbar-none">
                            <button type="button" data-posts-tag="all" onclick="window.TempoCommunity.filterPostsTag('all')" 
                                    class="posts-tag-pill px-3.5 py-1.5 rounded-full text-xs font-bold transition whitespace-nowrap bg-[#FF6B2C] text-white shadow-2xs">
                                All Posts
                            </button>
                            <button type="button" data-posts-tag="#deadline" onclick="window.TempoCommunity.filterPostsTag('#deadline')" 
                                    class="posts-tag-pill px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]">
                                #Deadline
                            </button>
                            <button type="button" data-posts-tag="#mentalhealth" onclick="window.TempoCommunity.filterPostsTag('#mentalhealth')" 
                                    class="posts-tag-pill px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]">
                                #MentalHealth
                            </button>
                            <button type="button" data-posts-tag="#focus" onclick="window.TempoCommunity.filterPostsTag('#focus')" 
                                    class="posts-tag-pill px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]">
                                #Focus
                            </button>
                            <button type="button" data-posts-tag="#recovery" onclick="window.TempoCommunity.filterPostsTag('#recovery')" 
                                    class="posts-tag-pill px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]">
                                #Recovery
                            </button>
                            <button type="button" data-posts-tag="#general" onclick="window.TempoCommunity.filterPostsTag('#general')" 
                                    class="posts-tag-pill px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#736F68] border border-[#EAE4DF] hover:border-[#FF6B2C]">
                                #General
                            </button>
                        </div>

                        <!-- Posts Feed List -->
                        <div id="community-feed-posts-list" class="space-y-4">
                            <!-- Populated dynamically by communityPosts.js -->
                        </div>

                        <!-- Empty State -->
                        <div id="community-posts-empty" class="hidden text-center py-12 px-4 bg-white border border-[#EAE4DF] rounded-3xl space-y-3">
                            <span class="text-3xl">💬</span>
                            <h3 class="font-heading text-base font-bold text-[#202124]">No community posts found</h3>
                            <p class="text-xs text-[#6F6B68]">Be the first to share an encouraging note or advice with other students.</p>
                        </div>
                    </div>

                    <!-- ==========================================
                         PANEL 5: DIRECT MESSAGE
                         ========================================== -->
                    <div id="community-panel-messages" class="community-panel space-y-5 hidden">
                        <div>
                            <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Direct Mentorship &amp; Messages</h2>
                            <p class="text-xs sm:text-sm text-[#6F6B68]">Private, 1-on-1 conversations with peer supporters and campus wellbeing advisors.</p>
                        </div>

                        <!-- Guest Unauthenticated View -->
                        <div id="community-dm-guest-view" class="p-8 sm:p-12 text-center bg-white border border-[#EAE4DF] rounded-3xl space-y-4 max-w-xl mx-auto shadow-xs">
                            <div class="w-14 h-14 rounded-2xl bg-[#FFE9DC] text-[#FF6B2C] flex items-center justify-center mx-auto text-2xl font-bold">
                                ✉️
                            </div>
                            <div class="space-y-1.5">
                                <h3 class="font-heading text-lg font-bold text-[#202124]">Sign in for Direct Mentorship</h3>
                                <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                                    Direct messaging allows private, confidential conversations between you and certified student peer mentors or wellbeing advisors. Please sign in to access your conversations.
                                </p>
                            </div>
                            <div>
                                <button type="button" 
                                        onclick="if(window.TempoAuth && typeof window.TempoAuth.openSignInModal === 'function') window.TempoAuth.openSignInModal();"
                                        class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs shadow-xs transition cursor-pointer">
                                    Sign In to Access Messages
                                </button>
                            </div>
                        </div>

                        <!-- Authenticated 2-Column Messaging Interface -->
                        <div id="community-dm-auth-view" class="hidden bg-white border border-[#EAE4DF] rounded-3xl overflow-hidden shadow-xs grid grid-cols-1 md:grid-cols-12 min-h-[580px]">
                            <!-- Left Column: Conversations List -->
                            <div id="dm-conversations-column" class="md:col-span-5 border-r border-[#EAE4DF] flex flex-col bg-white">
                                <!-- Search & New DM bar -->
                                <div class="p-3.5 border-b border-[#EAE4DF] space-y-2.5">
                                    <div class="relative">
                                        <svg class="w-3.5 h-3.5 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                        </svg>
                                        <input type="text" id="dm-search-conversations" 
                                               oninput="window.TempoCommunity.handleDMSearch(this.value)"
                                               placeholder="Search mentors..." 
                                               class="w-full pl-8 pr-3 py-1.5 text-xs bg-[#FAF8F5] border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#FF6B2C]">
                                    </div>
                                </div>

                                <!-- Conversations Scrollable List -->
                                <div id="dm-conversations-list" class="flex-1 overflow-y-auto p-2 space-y-1 divide-y divide-[#EAE4DF]/40 max-h-[500px]">
                                    <!-- Populated dynamically by communityPosts.js -->
                                </div>
                            </div>

                            <!-- Right Column: Active Conversation Thread -->
                            <div id="dm-chat-column" class="md:col-span-7 flex flex-col bg-[#FAF8F5] hidden md:flex">
                                <!-- Header -->
                                <div class="p-4 border-b border-[#EAE4DF] bg-white flex items-center justify-between">
                                    <div class="flex items-center space-x-3">
                                        <button type="button" id="btn-dm-mobile-back" onclick="window.TempoCommunity.mobileToggleConversation(false)" 
                                                class="md:hidden text-[#736F68] hover:text-[#202124] p-1 font-bold text-sm">
                                            ← Back
                                        </button>
                                        <img id="dm-active-avatar" src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=120&h=120&q=80" 
                                             alt="Contact" class="w-9 h-9 rounded-full object-cover border border-stone-200">
                                        <div>
                                            <h4 id="dm-active-name" class="text-xs sm:text-sm font-bold text-[#202124]">Dr. Elena Vance</h4>
                                            <div class="flex items-center space-x-1.5 text-[10px]">
                                                <span id="dm-active-role" class="text-[#8E8A85]">Campus Wellbeing Advisor</span>
                                                <span>•</span>
                                                <span id="dm-active-status" class="text-emerald-600 font-bold">Online</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Messages Bubble Scroll Container -->
                                <div id="dm-messages-container" class="flex-1 p-4 sm:p-5 overflow-y-auto space-y-3.5 max-h-[420px]">
                                    <!-- Populated dynamically by communityPosts.js -->
                                </div>

                                <!-- Message Input Box -->
                                <div class="p-3.5 bg-white border-t border-[#EAE4DF]">
                                    <form id="dm-message-form" class="flex items-center space-x-2">
                                        <input type="text" id="dm-message-input" 
                                               placeholder="Write a supportive message or question..." 
                                               class="flex-1 px-3.5 py-2.5 text-xs sm:text-sm bg-[#FAF8F5] border border-[#EAE4DF] rounded-2xl focus:outline-none focus:border-[#FF6B2C] focus:bg-white transition">
                                        <button type="submit" id="btn-dm-send" 
                                                class="btn-primary px-4 py-2.5 rounded-2xl font-bold text-xs shrink-0 flex items-center space-x-1 shadow-xs transition cursor-pointer">
                                            <span>Send</span>
                                            <span>➤</span>
                                        </button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </section>

'''

# Find insertion point before SCREEN 5
learn_screen_marker = '<!-- ===================================================================\r\n             SCREEN 5: DEDICATED LEARN & SOLVE STANDALONE PAGE'
if learn_screen_marker not in raw:
    learn_screen_marker = '<!-- ===================================================================\n             SCREEN 5: DEDICATED LEARN & SOLVE STANDALONE PAGE'

if learn_screen_marker in raw:
    raw = raw.replace(learn_screen_marker, community_screen_html + learn_screen_marker, 1)
    print("Successfully inserted screen-community into index.html.")
else:
    print("Error: Could not find screen-learn marker in index.html!")

# 4. Insert Modals for Announcement Detail & Admin Announcement Create
announcement_modals_html = '''
    <!-- 4b. ANNOUNCEMENT DETAIL MODAL -->
    <div id="modal-announcement-detail" class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-3 sm:p-6 overflow-y-auto hidden">
        <div class="tempo-card max-w-xl w-full max-h-[90vh] overflow-y-auto bg-white rounded-3xl p-6 sm:p-8 space-y-5 relative shadow-2xl">
            <div class="flex items-center justify-between pb-3 border-b border-gray-100">
                <span id="announcement-modal-badge" class="px-3 py-1 rounded-full text-xs font-extrabold bg-[#FFE9DC] text-[#B83D08]">
                    Official Update
                </span>
                <button type="button" onclick="window.TempoCommunity.closeAnnouncementDetail()" class="text-gray-400 hover:text-gray-700 p-1.5 rounded-lg text-lg transition cursor-pointer">✕</button>
            </div>

            <div class="space-y-4">
                <img id="announcement-modal-image" src="" alt="Announcement" class="w-full h-52 object-cover rounded-2xl hidden">
                <div class="space-y-1">
                    <p id="announcement-modal-meta" class="text-xs text-[#8E8A85]"></p>
                    <h3 id="announcement-modal-title" class="font-heading text-xl sm:text-2xl font-bold text-[#202124] leading-tight"></h3>
                </div>
                <div id="announcement-modal-content" class="space-y-3 text-xs sm:text-sm text-[#42413F] leading-relaxed"></div>
            </div>

            <div class="pt-3 border-t border-gray-100 flex items-center justify-end space-x-3">
                <button type="button" onclick="window.TempoCommunity.closeAnnouncementDetail()" class="px-4 py-2 rounded-xl text-xs font-semibold text-[#736F68] hover:bg-stone-100 transition cursor-pointer">
                    Close
                </button>
                <button type="button" id="announcement-modal-action" class="btn-primary px-4 py-2 rounded-xl text-xs font-bold transition hidden cursor-pointer">
                    Try it now ↗
                </button>
            </div>
        </div>
    </div>

    <!-- 4c. ADMIN: CREATE ANNOUNCEMENT MODAL -->
    <div id="modal-announcement-create" class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-3 sm:p-6 overflow-y-auto hidden">
        <div class="tempo-card max-w-lg w-full max-h-[90vh] overflow-y-auto bg-white rounded-3xl p-6 sm:p-8 space-y-5 relative shadow-2xl">
            <div class="flex items-center justify-between pb-3 border-b border-gray-100">
                <div class="flex items-center space-x-2">
                    <span class="text-xl">📢</span>
                    <h3 class="font-heading text-lg font-bold text-[#202124]">New Official Announcement</h3>
                </div>
                <button type="button" onclick="window.TempoCommunity.closeNewAnnouncementModal()" class="text-gray-400 hover:text-gray-700 p-1.5 rounded-lg text-lg transition cursor-pointer">✕</button>
            </div>

            <form id="form-create-announcement" class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold text-[#202124] mb-1">Title *</label>
                    <input type="text" id="input-announcement-title" placeholder="e.g. Focus Zone Background Expansion" required
                           class="w-full px-3 py-2 text-xs bg-[#FAF8F5] border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#FF6B2C]">
                </div>

                <div>
                    <label class="block text-xs font-semibold text-[#202124] mb-1">Short Summary *</label>
                    <input type="text" id="input-announcement-summary" placeholder="Brief 1-2 sentence description..." required
                           class="w-full px-3 py-2 text-xs bg-[#FAF8F5] border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#FF6B2C]">
                </div>

                <div>
                    <label class="block text-xs font-semibold text-[#202124] mb-1">Full Announcement Body</label>
                    <textarea id="input-announcement-content" rows="4" placeholder="Detailed announcement content..." 
                              class="w-full p-3 text-xs bg-[#FAF8F5] border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#FF6B2C] resize-none"></textarea>
                </div>

                <div>
                    <label class="block text-xs font-semibold text-[#202124] mb-1">Cover Image URL (optional)</label>
                    <input type="url" id="input-announcement-image" placeholder="https://..." 
                           class="w-full px-3 py-2 text-xs bg-[#FAF8F5] border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#FF6B2C]">
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-semibold text-[#202124] mb-1">Action Button Label</label>
                        <input type="text" id="input-announcement-action-label" placeholder="e.g. Try Focus Zone" 
                               class="w-full px-3 py-2 text-xs bg-[#FAF8F5] border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#FF6B2C]">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-[#202124] mb-1">Action Route</label>
                        <select id="select-announcement-action-route" class="w-full px-3 py-2 text-xs bg-[#FAF8F5] border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#FF6B2C]">
                            <option value="">None</option>
                            <option value="focus-zone">Focus Zone</option>
                            <option value="explore-mental-health-tests">UCheck Assessments</option>
                            <option value="stress-check">Daily Self-Check</option>
                            <option value="plan-workspace">Plan Workspace</option>
                        </select>
                    </div>
                </div>

                <div class="pt-3 border-t border-gray-100 flex items-center justify-end space-x-2">
                    <button type="button" onclick="window.TempoCommunity.closeNewAnnouncementModal()" 
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-[#736F68] hover:bg-stone-100 transition cursor-pointer">
                        Cancel
                    </button>
                    <button type="submit" class="btn-primary px-5 py-2 rounded-xl text-xs font-bold transition cursor-pointer">
                        Publish Announcement
                    </button>
                </div>
            </form>
        </div>
    </div>
'''

modal_marker = '</div>\r\n    </div>\r\n\r\n    <!-- ===================================================================\r\n         AUTHENTICATION & ROLE SELECTION MODALS'
if modal_marker not in raw:
    modal_marker = '</div>\n    </div>\n\n    <!-- ===================================================================\n         AUTHENTICATION & ROLE SELECTION MODALS'

if modal_marker in raw:
    raw = raw.replace(modal_marker, '</div>\r\n    </div>\r\n' + announcement_modals_html + '\r\n\r\n    <!-- ===================================================================\r\n         AUTHENTICATION & ROLE SELECTION MODALS', 1)
    print("Successfully inserted announcement modals into index.html.")
else:
    print("Warning: Could not find modal marker, trying fallback search...")
    idx = raw.find('id="modal-community-posts"')
    if idx != -1:
        end_m = raw.find('<!-- ===================================================================\n         AUTHENTICATION', idx)
        if end_m == -1:
            end_m = raw.find('<!-- ===================================================================\r\n         AUTHENTICATION', idx)
        if end_m != -1:
            raw = raw[:end_m] + announcement_modals_html + '\r\n\r\n    ' + raw[end_m:]
            print("Successfully inserted announcement modals via fallback.")

# Ensure CRLF line endings
raw_crlf = raw.replace('\r\n', '\n').replace('\n', '\r\n')
with open('index.html', 'wb') as f:
    f.write(raw_crlf.encode('utf-8'))

print("Completed patching index.html successfully.")
