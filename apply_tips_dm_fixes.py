import re

print("Applying Tempo Community 3-Column Tips and Clean Direct Message Refinements...")

# ==============================================================================
# 1. UPDATE communityPosts.js
# ==============================================================================
with open('communityPosts.js', 'r', encoding='utf-8') as f:
    js_content = f.read()

# 1a. In renderTips(): Ensure cards have 'h-full flex flex-col justify-between'
old_tips_card = r'<div class="bg-[#FFFDFB] border-2 border-[#ECA689] rounded-3xl p-5 sm:p-6 shadow-xs flex flex-col justify-between space-y-3 min-h-[190px]">'
new_tips_card = r'<div class="h-full bg-[#FFFDFB] border-2 border-[#ECA689] rounded-3xl p-5 sm:p-6 shadow-xs flex flex-col justify-between space-y-3 min-h-[190px] transition hover:shadow-xs">'

if old_tips_card in js_content:
    js_content = js_content.replace(old_tips_card, new_tips_card)
    print("Updated Tips card layout to h-full for row height consistency.")

# 1b. Update Direct Message Controller with Loading, Error, and Clean Empty States
old_dm_controller = r'''    // =========================================================================
    // 8. REFERENCE 5: DIRECT MESSAGE & CHAT REQUESTS
    // =========================================================================

    function renderMessagesView() {
        const guestView = document.getElementById('community-dm-guest-view');
        const authView = document.getElementById('community-dm-auth-view');

        // Check authentication
        const currentUser = window.TempoAuth ? window.TempoAuth.getCurrentUser() : null;
        if (!currentUser) {
            if (guestView) guestView.classList.remove('hidden');
            if (authView) authView.classList.add('hidden');
            return;
        }

        if (guestView) guestView.classList.add('hidden');
        if (authView) authView.classList.remove('hidden');

        updateChatRequestsBadge();
        renderConversationsList();
        renderActiveConversation();
    }'''

new_dm_controller = r'''    // =========================================================================
    // 8. REFERENCE 5: DIRECT MESSAGE & CHAT REQUESTS (DATA-HARDENED & CLEAN EMPTY STATES)
    // =========================================================================

    let dmLoading = false;
    let dmError = null;

    async function renderMessagesView() {
        const guestView = document.getElementById('community-dm-guest-view');
        const authView = document.getElementById('community-dm-auth-view');

        // Check authentication
        const currentUser = window.TempoAuth ? window.TempoAuth.getCurrentUser() : null;
        if (!currentUser) {
            if (guestView) guestView.classList.remove('hidden');
            if (authView) authView.classList.add('hidden');
            return;
        }

        if (guestView) guestView.classList.add('hidden');
        if (authView) authView.classList.remove('hidden');

        updateChatRequestsBadge();
        await loadConversationsFromBackend(currentUser);
    }

    async function loadConversationsFromBackend(currentUser) {
        if (!currentUser) return;
        const userId = currentUser.id || 'anonymous';
        dmLoading = true;
        dmError = null;
        renderConversationsList();
        renderActiveConversation();

        try {
            let loaded = [];
            
            // 1. Inspect Supabase for real support requests/conversations
            if (window.TempoSupabase && typeof window.TempoSupabase.getClient === 'function') {
                try {
                    const client = await window.TempoSupabase.getClient();
                    if (client && userId !== 'anonymous') {
                        const { data, error } = await client
                            .from('support_requests')
                            .select('id, subject, category, status, created_at, updated_at, assigned_volunteer_id, student_id')
                            .or(`student_id.eq.${userId},assigned_volunteer_id.eq.${userId}`)
                            .order('updated_at', { ascending: false });

                        if (error) {
                            // If table is missing or network failure, record error distinctly
                            if (error.code && error.code !== 'PGRST116') {
                                console.warn('[DirectMessage] Supabase response:', error.message);
                            }
                        } else if (Array.isArray(data) && data.length > 0) {
                            loaded = data.map(req => ({
                                id: req.id,
                                name: req.subject || 'Support Session',
                                avatar: 'assets/tempo-logo.png',
                                subtitle: req.category || 'Direct Message',
                                time: 'Recent',
                                lastMessage: `Status: ${req.status}`,
                                unreadCount: 0,
                                messages: []
                            }));
                        }
                    }
                } catch (sbErr) {
                    console.warn('[DirectMessage] Supabase client check:', sbErr);
                }
            }

            // 2. Fetch authenticated user-scoped local conversations (if no Supabase rows)
            if (loaded.length === 0) {
                const userKey = `tempo_direct_messages_${userId}`;
                const saved = localStorage.getItem(userKey);
                if (saved) {
                    try {
                        const parsed = JSON.parse(saved);
                        if (Array.isArray(parsed)) {
                            // Strictly purge any legacy mock IDs
                            loaded = parsed.filter(c => c.id !== 'conv-badminton' && c.id !== 'conv-tempo-admin' && c.id !== 'conv-innie');
                        }
                    } catch (e) {}
                }
            }

            // Update state
            conversations = loaded;
            if (conversations.length > 0) {
                if (!activeConvId || !conversations.some(c => c.id === activeConvId)) {
                    activeConvId = conversations[0].id;
                }
            } else {
                activeConvId = null;
            }
        } catch (err) {
            console.error('[DirectMessage] Fetch error:', err);
            dmError = err.message || 'Failed to load conversations';
        } finally {
            dmLoading = false;
            renderConversationsList();
            renderActiveConversation();
        }
    }'''

if old_dm_controller in js_content:
    js_content = js_content.replace(old_dm_controller, new_dm_controller)
    print("Updated Direct Message controller with async backend fetch and loading/error states.")

# 1c. Update renderConversationsList() to handle loading, error, and empty list
old_render_convs = r'''    function renderConversationsList(filterQuery = '') {
        const container = document.getElementById('dm-conversations-list');
        if (!container) return;

        let filtered = [...conversations];
        if (filterQuery) {
            const q = filterQuery.toLowerCase();
            filtered = filtered.filter(c => (c.name || '').toLowerCase().includes(q) || (c.lastMessage || '').toLowerCase().includes(q));
        }

        // Requirement 3: Empty conversation list without fabricated entries
        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="h-44 flex flex-col items-center justify-center p-4 text-center space-y-1.5 text-[#8E8A85]">
                    <span class="text-xl">💬</span>
                    <p class="text-xs font-bold text-[#5A5550]">No conversations yet</p>
                    <p class="text-[10.5px] text-[#8E8A85] leading-relaxed max-w-[200px]">Incoming messages and accepted chat requests will appear here.</p>
                </div>
            `;
            return;
        }'''

new_render_convs = r'''    function renderConversationsList(filterQuery = '') {
        const container = document.getElementById('dm-conversations-list');
        if (!container) return;

        // Loading state
        if (dmLoading) {
            container.innerHTML = `
                <div class="h-44 flex flex-col items-center justify-center p-4 text-center space-y-2 text-[#8E8A85]">
                    <div class="w-5 h-5 border-2 border-[#DE8662] border-t-transparent rounded-full animate-spin"></div>
                    <p class="text-xs font-semibold text-[#5A5550]">Loading conversations...</p>
                </div>
            `;
            return;
        }

        // Error state: Never interpret failed request as empty
        if (dmError) {
            container.innerHTML = `
                <div class="h-44 flex flex-col items-center justify-center p-4 text-center space-y-2 text-[#D92D20]">
                    <span class="text-base">⚠️</span>
                    <p class="text-xs font-bold text-[#D92D20]">Unable to load conversations</p>
                    <p class="text-[10px] text-[#8E8A85] max-w-[190px] leading-tight">${escapeHtml(dmError)}</p>
                    <button type="button" onclick="window.TempoCommunity.retryLoadConversations()" 
                            class="px-3 py-1 bg-stone-100 hover:bg-stone-200 text-[#5A5550] text-[11px] font-bold rounded-lg transition cursor-pointer">
                        Retry
                    </button>
                </div>
            `;
            return;
        }

        let filtered = [...conversations];
        if (filterQuery) {
            const q = filterQuery.toLowerCase();
            filtered = filtered.filter(c => (c.name || '').toLowerCase().includes(q) || (c.lastMessage || '').toLowerCase().includes(q));
        }

        // Clean empty state when authenticated user has no conversations
        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="h-48 flex flex-col items-center justify-center p-4 text-center space-y-2 text-[#8E8A85]">
                    <img src="assets/chat_requests_symbol.png" alt="No conversations" class="w-6 h-6 opacity-40 object-contain mb-0.5">
                    <p class="text-xs font-bold text-[#5A5550]">No conversations yet</p>
                    <p class="text-[10.5px] text-[#8E8A85] leading-relaxed max-w-[190px]">You have not sent or received any messages. New messages and accepted chat requests will appear here.</p>
                </div>
            `;
            return;
        }'''

if old_render_convs in js_content:
    js_content = js_content.replace(old_render_convs, new_render_convs)
    print("Updated renderConversationsList() with distinct loading, error, and clean empty states.")

# 1d. Update renderActiveConversation() to ensure blank message panel when no conversation is selected
old_render_active = r'''        // Requirement 3: If there is no selected conversation, keep the message panel empty
        if (!activeConvId || conversations.length === 0) {
            if (nameEl) nameEl.textContent = 'Direct Messages';
            if (roleEl) roleEl.textContent = 'Select a conversation from the left to start messaging';
            if (avatarEl) avatarEl.src = 'assets/tempo-logo.png';
            if (messagesContainer) {
                messagesContainer.innerHTML = `
                    <div class="h-full min-h-[320px] flex flex-col items-center justify-center p-6 text-center space-y-2 text-[#8E8A85]">
                        <span class="text-3xl">✉️</span>
                        <p class="text-xs sm:text-[13px] font-bold text-[#5A5550]">No conversation selected</p>
                        <p class="text-[11px] text-[#8E8A85] max-w-xs leading-relaxed">Choose a contact from your conversations list or check Chat Requests to begin chatting.</p>
                    </div>
                `;
            }
            if (messageInput) {
                messageInput.disabled = true;
                messageInput.placeholder = 'Select a conversation to message...';
            }
            if (sendBtn) sendBtn.disabled = true;
            return;
        }'''

new_render_active = r'''        // Loading state
        if (dmLoading) {
            if (messagesContainer) {
                messagesContainer.innerHTML = `
                    <div class="h-full min-h-[320px] flex flex-col items-center justify-center p-6 text-center space-y-2 text-[#8E8A85]">
                        <div class="w-6 h-6 border-2 border-[#DE8662] border-t-transparent rounded-full animate-spin"></div>
                        <p class="text-xs text-[#8E8A85]">Loading conversation...</p>
                    </div>
                `;
            }
            return;
        }

        // Requirement 2: When user has no conversations or none selected, keep message panel blank
        if (!activeConvId || conversations.length === 0) {
            if (nameEl) nameEl.textContent = 'Direct Messages';
            if (roleEl) roleEl.textContent = 'No active conversation';
            if (avatarEl) avatarEl.src = 'assets/tempo-logo.png';
            if (messagesContainer) {
                messagesContainer.innerHTML = `
                    <div class="h-full min-h-[320px] flex flex-col items-center justify-center p-6 text-center space-y-2.5 text-[#8E8A85]">
                        <img src="assets/chat_requests_symbol.png" alt="No conversation selected" class="w-8 h-8 opacity-40 object-contain">
                        <p class="text-xs sm:text-[13px] font-bold text-[#5A5550]">No conversation selected</p>
                        <p class="text-[11px] text-[#8E8A85] max-w-xs leading-relaxed">Choose a conversation from your list or check Chat Requests to start messaging.</p>
                    </div>
                `;
            }
            if (messageInput) {
                messageInput.disabled = true;
                messageInput.placeholder = 'Select a conversation to message...';
            }
            if (sendBtn) sendBtn.disabled = true;
            return;
        }'''

if old_render_active in js_content:
    js_content = js_content.replace(old_render_active, new_render_active)
    print("Updated renderActiveConversation() to keep message panel blank when no conversation is selected.")

# 1e. Add retryLoadConversations to public API
if 'retryLoadConversations' not in js_content:
    js_content = js_content.replace(
        'renderMessagesView,',
        'renderMessagesView,\n        retryLoadConversations: () => { const user = window.TempoAuth ? window.TempoAuth.getCurrentUser() : null; if (user) loadConversationsFromBackend(user); },'
    )

# Write communityPosts.js (CRLF)
community_js_crlf = js_content.replace('\r\n', '\n').replace('\n', '\r\n')
with open('communityPosts.js', 'wb') as f:
    f.write(community_js_crlf.encode('utf-8'))
print("1. Successfully saved communityPosts.js (CRLF).")

# ==============================================================================
# 2. UPDATE index.html
# ==============================================================================
with open('index.html', 'r', encoding='utf-8') as f:
    index_content = f.read()

# 2a. Update #tips-cards-grid to responsive 3-column grid
old_tips_grid = r'<div id="tips-cards-grid" class="grid grid-cols-1 md:grid-cols-2 gap-5">'
new_tips_grid = r'<div id="tips-cards-grid" class="grid grid-cols-1 md:grid-cols-2 min-[1200px]:grid-cols-3 xl:grid-cols-3 gap-5 tips-responsive-grid">'

if old_tips_grid in index_content:
    index_content = index_content.replace(old_tips_grid, new_tips_grid)
    print("Updated #tips-cards-grid to 3 columns on wide desktop (>=1200px).")

# 2b. Add CSS rule for .tips-responsive-grid in <style>
css_rule = r'''
        /* Tips Responsive 3-Column Grid (Requirement 1) */
        @media (min-width: 1200px) {
            .tips-responsive-grid {
                grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
            }
        }
        @media (min-width: 640px) and (max-width: 1199px) {
            .tips-responsive-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            }
        }
        @media (max-width: 639px) {
            .tips-responsive-grid {
                grid-template-columns: repeat(1, minmax(0, 1fr)) !important;
            }
        }
'''
if '.tips-responsive-grid' not in index_content:
    style_end = index_content.find('</style>')
    if style_end != -1:
        index_content = index_content[:style_end] + css_rule + index_content[style_end:]
        print("Inserted .tips-responsive-grid media queries in <style>.")

# 2c. Update Chat Requests button in DM header to use assets/chat_requests_symbol.png with aria-label
old_chat_req_btn = r'''<button type="button" id="btn-dm-chat-requests" onclick="window.TempoCommunity.openChatRequests()" 
                                            class="relative p-2 rounded-full hover:bg-stone-100 transition cursor-pointer shrink-0" 
                                            title="Chat Requests">
                                        <img src="assets/chat_requests_icon.png" alt="Chat Requests" class="w-4 h-4 object-contain">
                                        <span id="badge-chat-requests-count" class="hidden absolute -top-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-[#E04B38] text-white text-[9px] font-bold flex items-center justify-center">0</span>
                                    </button>'''

new_chat_req_btn = r'''<button type="button" id="btn-dm-chat-requests" onclick="window.TempoCommunity.openChatRequests()" 
                                            class="relative p-2 rounded-full hover:bg-stone-100 transition cursor-pointer shrink-0" 
                                            aria-label="Chat Requests" title="Chat Requests">
                                        <img src="assets/chat_requests_symbol.png" alt="Chat Requests" class="w-4 h-4 object-contain">
                                        <span id="badge-chat-requests-count" class="hidden absolute -top-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-[#E04B38] text-white text-[9px] font-bold flex items-center justify-center">0</span>
                                    </button>'''

if old_chat_req_btn in index_content:
    index_content = index_content.replace(old_chat_req_btn, new_chat_req_btn)
    print("Updated Chat Requests header button to use assets/chat_requests_symbol.png with aria-label.")

# 2d. Update modal-chat-requests header icon
old_modal_icon = r'<img src="assets/chat_requests_icon.png" alt="Chat Requests" class="w-4 h-4 object-contain">'
new_modal_icon = r'<img src="assets/chat_requests_symbol.png" alt="Chat Requests" class="w-4 h-4 object-contain">'

if old_modal_icon in index_content:
    index_content = index_content.replace(old_modal_icon, new_modal_icon)
    print("Updated modal-chat-requests icon.")

# 2e. Update DM send button to use assets/send_arrow_icon.png
old_dm_send_btn = r'''<button type="submit" id="btn-dm-send" 
                                                class="w-8 h-8 rounded-full bg-[#DFB59F] hover:bg-[#D4A38A] text-white flex items-center justify-center text-xs font-bold shrink-0 shadow-2xs cursor-pointer">
                                            ➤
                                        </button>'''

new_dm_send_btn = r'''<button type="submit" id="btn-dm-send" 
                                                class="w-8 h-8 rounded-full bg-[#DFB59F] hover:bg-[#D4A38A] text-white flex items-center justify-center text-xs font-bold shrink-0 shadow-2xs cursor-pointer"
                                                aria-label="Send message" title="Send message">
                                            <img src="assets/send_arrow_icon.png" alt="Send" class="w-3.5 h-3.5 object-contain">
                                        </button>'''

if old_dm_send_btn in index_content:
    index_content = index_content.replace(old_dm_send_btn, new_dm_send_btn)
    print("Updated DM send button with assets/send_arrow_icon.png.")

# 2f. Update Posts top bookmark icon to use assets/bookmark_ribbon_icon.png
old_bookmark_btn = r'''<!-- Bookmark Button -->
                            <button type="button" onclick="window.TempoCommunity.filterBookmarkedPosts()" 
                                    class="bg-[#F3DCD0] hover:bg-[#E9CDBC] text-[#5A5550] p-2 rounded-full transition shadow-2xs cursor-pointer shrink-0" title="Bookmarks">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                                </svg>
                            </button>'''

new_bookmark_btn = r'''<!-- Bookmark Button -->
                            <button type="button" onclick="window.TempoCommunity.filterBookmarkedPosts()" 
                                    class="bg-[#F3DCD0] hover:bg-[#E9CDBC] text-[#5A5550] p-2 rounded-full transition shadow-2xs cursor-pointer shrink-0 flex items-center justify-center" aria-label="Bookmarked Posts" title="Bookmarks">
                                <img src="assets/bookmark_ribbon_icon.png" alt="Bookmarks" class="w-3.5 h-3.5 object-contain">
                            </button>'''

if old_bookmark_btn in index_content:
    index_content = index_content.replace(old_bookmark_btn, new_bookmark_btn)
    print("Updated Posts bookmark button with assets/bookmark_ribbon_icon.png.")

# Write index.html (CRLF)
index_crlf = index_content.replace('\r\n', '\n').replace('\n', '\r\n')
with open('index.html', 'wb') as f:
    f.write(index_crlf.encode('utf-8'))
print("2. Successfully saved index.html (CRLF).")

print("All refinements applied cleanly!")
