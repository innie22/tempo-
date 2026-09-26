/**
 * Tempo Admin / Advisor Portal (Dr. Elena Vance)
 * Streamlined support inbox triage, 1-click empathetic templates, and micro-tip publishing.
 */

window.TempoAdmin = (function() {
    let currentFilter = 'all';
    let selectedTicketId = null;
    let tips = [];

    // Pre-written Empathetic Advisor Templates
    const templates = {
        extension: `Hi Alex, thank you for reaching out. First, please know that taking a pause to protect your health is the right decision. 

I strongly encourage you to send an extension request for the Marketing Report right now. Most professors are very accommodating if you write before the deadline. You can use the template from our Knowledge Hub (under 'Asking for Help'). 

Propose a concrete alternative time, such as Sunday at 5:00 PM. Let me know if you would like me to review your email draft before you send it.`,
        deescalate: `Hi Alex, take a slow breath. When three deadlines converge, your nervous system is in full emergency mode. 

Tonight, let's focus exclusively on ONE task: the 9:00 AM report. Give yourself full permission to ignore the Friday slides until tomorrow afternoon. Getting 6 hours of sleep tonight will make you twice as productive tomorrow. I am here if you need more support.`,
        dropin: `Hi Alex, I can see how much pressure you have been carrying this week. 

I have an open drop-in wellbeing slot tomorrow at 11:30 AM (virtual or in Student Center 304). Would you like me to hold that for you? We can sit down together and map out a gentle plan for the rest of your semester.`
    };

    function init() {
        tips = [...(window.TEMPO_DATA.tips || [])];
        bindEvents();
        renderTickets();
        renderTips();
    }

    function bindEvents() {
        // Filter Buttons
        document.querySelectorAll('.admin-ticket-filter').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.admin-ticket-filter').forEach(b => {
                    b.className = "admin-ticket-filter px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition";
                });
                e.currentTarget.className = "admin-ticket-filter px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-700 text-white transition";
                currentFilter = e.currentTarget.dataset.filter;
                renderTickets();
            });
        });

        // Template Quick Buttons
        document.querySelectorAll('.btn-use-template').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tplKey = e.currentTarget.dataset.template;
                const replyTextarea = document.getElementById('admin-reply-textarea');
                if (replyTextarea && templates[tplKey]) {
                    replyTextarea.value = templates[tplKey];
                    window.TempoApp.showToast("Empathetic template inserted into reply box.");
                }
            });
        });

        // Send Reply Button
        const sendReplyBtn = document.getElementById('btn-admin-send-reply');
        if (sendReplyBtn) {
            sendReplyBtn.addEventListener('click', handleSendAdminReply);
        }

        // Resolve Ticket Button
        const resolveBtn = document.getElementById('btn-admin-resolve-ticket');
        if (resolveBtn) {
            resolveBtn.addEventListener('click', handleResolveTicket);
        }

        // New Tip Form
        const newTipForm = document.getElementById('form-create-tip');
        if (newTipForm) {
            newTipForm.addEventListener('submit', handleCreateTip);
        }
    }

    function renderTickets() {
        const ticketList = window.TempoSupport ? window.TempoSupport.getTickets() : [];
        const container = document.getElementById('admin-tickets-table');
        if (!container) return;

        const filtered = ticketList.filter(t => {
            if (currentFilter === 'all') return true;
            if (currentFilter === 'awaiting') return t.status === 'Awaiting Advisor';
            if (currentFilter === 'resolved') return t.status === 'Resolved';
            return true;
        });

        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="p-8 text-center text-gray-400">
                    <p class="text-xs">No tickets match this filter.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = filtered.map(t => {
            const isSelected = t.id === selectedTicketId;
            const statusClass = t.status === 'Awaiting Advisor' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800';

            return `
                <div class="p-4 border-b border-gray-100 hover:bg-stone-50 cursor-pointer transition ${isSelected ? 'bg-emerald-50/50' : ''}" 
                    onclick="window.TempoAdmin.selectTicket('${t.id}')">
                    <div class="flex items-center justify-between mb-1">
                        <span class="text-xs font-bold text-gray-900">${t.studentName}</span>
                        <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold ${statusClass}">${t.status}</span>
                    </div>
                    <h5 class="text-xs font-semibold text-gray-800 truncate">${t.subject}</h5>
                    <p class="text-[11px] text-gray-500 mt-1">${t.category} • ${t.createdAt}</p>
                </div>
            `;
        }).join('');

        // If none selected, auto-select first
        if (!selectedTicketId && filtered.length > 0) {
            selectTicket(filtered[0].id);
        }
    }

    function selectTicket(id) {
        selectedTicketId = id;
        renderTickets();

        const tickets = window.TempoSupport ? window.TempoSupport.getTickets() : [];
        const ticket = tickets.find(t => t.id === id);
        const detailPane = document.getElementById('admin-ticket-detail-pane');
        if (!detailPane || !ticket) return;

        detailPane.classList.remove('hidden');
        document.getElementById('admin-detail-student-name').textContent = ticket.studentName;
        document.getElementById('admin-detail-student-email').textContent = ticket.studentEmail;
        document.getElementById('admin-detail-subject').textContent = ticket.subject;
        document.getElementById('admin-detail-category').textContent = `${ticket.category} • Urgency: ${ticket.urgency}`;

        // Render Conversation
        const threadEl = document.getElementById('admin-detail-messages-thread');
        threadEl.innerHTML = ticket.messages.map(m => `
            <div class="p-3.5 rounded-xl ${m.sender === 'student' ? 'bg-stone-100 text-gray-800 mr-8' : 'bg-emerald-700 text-white ml-8'}">
                <div class="flex items-center justify-between text-[11px] mb-1 opacity-80">
                    <span class="font-bold">${m.senderName}</span>
                    <span>${m.timestamp}</span>
                </div>
                <p class="text-xs leading-relaxed whitespace-pre-line">${m.text}</p>
            </div>
        `).join('');

        // Clear reply textarea
        document.getElementById('admin-reply-textarea').value = '';
    }

    function handleSendAdminReply() {
        if (!selectedTicketId) return;
        const textarea = document.getElementById('admin-reply-textarea');
        const text = textarea ? textarea.value.trim() : '';

        if (!text) {
            window.TempoApp.showToast("Please write a response message first.");
            return;
        }

        const tickets = window.TempoSupport ? window.TempoSupport.getTickets() : [];
        const ticket = tickets.find(t => t.id === selectedTicketId);
        if (ticket) {
            ticket.messages.push({
                id: `msg-${Date.now()}`,
                sender: 'admin',
                senderName: 'Dr. Elena Vance (Wellbeing Advisor)',
                text: text,
                timestamp: 'Just now'
            });
            ticket.status = 'Advisor Replied';
            window.TempoSupport.updateTicketFromAdmin(ticket);
            selectTicket(ticket.id);
            window.TempoApp.showToast("Empathetic response sent to student.");
        }
    }

    function handleResolveTicket() {
        if (!selectedTicketId) return;
        const tickets = window.TempoSupport ? window.TempoSupport.getTickets() : [];
        const ticket = tickets.find(t => t.id === selectedTicketId);
        if (ticket) {
            ticket.status = 'Resolved';
            window.TempoSupport.updateTicketFromAdmin(ticket);
            renderTickets();
            selectTicket(ticket.id);
            window.TempoApp.showToast("Ticket marked as Resolved.");
        }
    }

    function renderTips() {
        const container = document.getElementById('admin-tips-table');
        if (!container) return;

        container.innerHTML = tips.map(tip => `
            <div class="p-4 bg-white border border-gray-200 rounded-xl flex items-center justify-between">
                <div class="space-y-1">
                    <div class="flex items-center space-x-2">
                        <span class="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">${tip.category}</span>
                        <span class="text-xs text-gray-400 font-medium">${tip.readMinutes} min read</span>
                    </div>
                    <h4 class="text-sm font-bold text-gray-900">${tip.title}</h4>
                    <p class="text-xs text-gray-600 line-clamp-2 max-w-xl">${tip.content}</p>
                </div>
                <div class="flex items-center space-x-2">
                    <button onclick="window.TempoAdmin.toggleTipPublish('${tip.id}')" 
                        class="px-3 py-1.5 rounded-lg text-xs font-medium border ${tip.isPublished ? 'border-emerald-600 text-emerald-700 bg-emerald-50' : 'border-gray-300 text-gray-600'}">
                        ${tip.isPublished ? 'Published' : 'Draft'}
                    </button>
                </div>
            </div>
        `).join('');

        // Also update the dashboard daily tip with the first published tip
        const firstPublished = tips.find(t => t.isPublished);
        if (firstPublished) {
            const tipTitle = document.getElementById('dashboard-tip-title');
            const tipContent = document.getElementById('dashboard-tip-content');
            const tipAuthor = document.getElementById('dashboard-tip-author');
            if (tipTitle) tipTitle.textContent = firstPublished.title;
            if (tipContent) tipContent.textContent = firstPublished.content;
            if (tipAuthor) tipAuthor.textContent = `${firstPublished.author} (${firstPublished.readMinutes}m read)`;
        }
    }

    function toggleTipPublish(id) {
        const tip = tips.find(t => t.id === id);
        if (tip) {
            tip.isPublished = !tip.isPublished;
            renderTips();
            window.TempoApp.showToast(`Tip status updated to: ${tip.isPublished ? 'Published' : 'Draft'}`);
        }
    }

    function handleCreateTip(e) {
        e.preventDefault();
        const title = document.getElementById('input-tip-title').value.trim();
        const category = document.getElementById('select-tip-category').value;
        const readMins = parseInt(document.getElementById('input-tip-readtime').value, 10) || 2;
        const content = document.getElementById('textarea-tip-content').value.trim();

        if (!title || !content) {
            window.TempoApp.showToast("Please provide both title and content for the tip.");
            return;
        }

        const newTip = {
            id: `tip-${Date.now()}`,
            author: 'Dr. Elena Vance',
            role: 'Campus Wellbeing Advisor',
            title: title,
            category: category,
            readMinutes: readMins,
            content: content,
            publishedAt: 'Just now',
            isPublished: true
        };

        tips.unshift(newTip);
        renderTips();
        e.target.reset();
        window.TempoApp.showToast("New micro-tip published successfully!");
    }

    return {
        init,
        renderTickets,
        selectTicket,
        toggleTipPublish
    };
})();
