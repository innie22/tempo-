/**
 * Tempo Human Support ("Talk to Someone")
 * Empathetic messaging portal for campus wellbeing coordinators and urgent helpline modal.
 */

window.TempoSupport = (function() {
    let tickets = [];

    function init() {
        // Load tickets from LocalStorage or seed data
        const saved = localStorage.getItem('tempo_tickets');
        if (saved) {
            try {
                tickets = JSON.parse(saved);
            } catch (e) {
                tickets = [...window.TEMPO_DATA.supportTickets];
            }
        } else {
            tickets = [...window.TEMPO_DATA.supportTickets];
        }

        bindEvents();
        renderMyTickets();
    }

    function bindEvents() {
        const form = document.getElementById('support-request-form');
        if (form) {
            form.addEventListener('submit', handleTicketSubmit);
        }

        // Crisis helpline buttons
        document.querySelectorAll('.btn-open-crisis-helpline').forEach(btn => {
            btn.addEventListener('click', openCrisisModal);
        });

        const closeCrisisBtn = document.getElementById('btn-close-crisis-modal');
        if (closeCrisisBtn) {
            closeCrisisBtn.addEventListener('click', closeCrisisModal);
        }
    }

    function handleTicketSubmit(e) {
        e.preventDefault();
        const category = document.getElementById('support-category').value;
        const urgency = document.getElementById('support-urgency').value;
        const subject = document.getElementById('support-subject').value.trim();
        const message = document.getElementById('support-message').value.trim();

        if (!subject || !message) {
            window.TempoApp.showToast("Please include both a brief subject and your message.");
            return;
        }

        const newTicket = {
            id: `TCK-${Math.floor(1000 + Math.random() * 9000)}`,
            studentName: 'Alex Rivera (You)',
            studentEmail: 'a.rivera@university.edu',
            category: category,
            urgency: urgency,
            status: 'Awaiting Advisor',
            subject: subject,
            createdAt: 'Just now',
            messages: [
                {
                    id: `msg-${Date.now()}`,
                    sender: 'student',
                    senderName: 'Alex Rivera',
                    text: message,
                    timestamp: 'Just now'
                }
            ]
        };

        tickets.unshift(newTicket);
        saveTickets();
        renderMyTickets();

        // Reset form
        e.target.reset();
        window.TempoApp.showToast("Your support request has been submitted. An advisor will respond shortly.");

        // Also notify admin view if open
        if (window.TempoAdmin) {
            window.TempoAdmin.renderTickets();
        }
    }

    function renderMyTickets() {
        const container = document.getElementById('my-support-conversations');
        if (!container) return;

        if (tickets.length === 0) {
            container.innerHTML = `
                <div class="p-6 text-center text-gray-500 bg-white rounded-xl border border-gray-200">
                    <p class="text-sm">You haven't submitted any support requests yet.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = tickets.map(t => {
            const statusClass = t.status === 'Resolved' 
                ? 'bg-gray-100 text-gray-700' 
                : (t.status === 'Advisor Replied' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800');

            return `
                <div class="tempo-card p-5 space-y-4">
                    <div class="flex items-start justify-between">
                        <div>
                            <span class="text-xs font-mono text-gray-400 font-semibold">${t.id}</span>
                            <h4 class="text-base font-bold text-gray-900 mt-0.5">${t.subject}</h4>
                            <p class="text-xs text-gray-500 mt-0.5">${t.category} • Submitted ${t.createdAt}</p>
                        </div>
                        <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${statusClass}">${t.status}</span>
                    </div>

                    <!-- Conversation Thread -->
                    <div class="space-y-3 pt-3 border-t border-gray-100">
                        ${t.messages.map(m => `
                            <div class="p-3.5 rounded-xl ${m.sender === 'student' ? 'bg-stone-50 border border-stone-200 ml-4' : 'bg-emerald-50 border border-emerald-200 mr-4'}">
                                <div class="flex items-center justify-between mb-1.5">
                                    <span class="text-xs font-bold ${m.sender === 'student' ? 'text-gray-700' : 'text-emerald-900'}">${m.senderName}</span>
                                    <span class="text-[10px] text-gray-400">${m.timestamp}</span>
                                </div>
                                <p class="text-xs text-gray-800 leading-relaxed whitespace-pre-line">${m.text}</p>
                            </div>
                        `).join('')}
                    </div>

                    <!-- Student Follow-up Reply Input -->
                    <div class="pt-2 flex items-center space-x-2">
                        <input type="text" id="reply-input-${t.id}" placeholder="Type a follow-up response to the advisor..." 
                            class="flex-1 px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:border-emerald-600">
                        <button onclick="window.TempoSupport.sendFollowUp('${t.id}')" 
                            class="px-4 py-2 bg-emerald-700 text-white rounded-lg text-xs font-medium hover:bg-emerald-800 transition">
                            Reply
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    function sendFollowUp(ticketId) {
        const input = document.getElementById(`reply-input-${ticketId}`);
        const text = input ? input.value.trim() : '';
        if (!text) return;

        const ticket = tickets.find(t => t.id === ticketId);
        if (ticket) {
            ticket.messages.push({
                id: `msg-${Date.now()}`,
                sender: 'student',
                senderName: 'Alex Rivera (You)',
                text: text,
                timestamp: 'Just now'
            });
            ticket.status = 'Awaiting Advisor';
            saveTickets();
            renderMyTickets();
            window.TempoApp.showToast("Follow-up message sent.");
            if (window.TempoAdmin) {
                window.TempoAdmin.renderTickets();
            }
        }
    }

    function openCrisisModal() {
        if (window.TempoEmergencySupport) {
            window.TempoEmergencySupport.openModal();
            return;
        }
        const modal = document.getElementById('progressive-emergency-modal');
        if (modal) modal.classList.remove('hidden');
    }

    function closeCrisisModal() {
        if (window.TempoEmergencySupport) {
            window.TempoEmergencySupport.closeModal();
            return;
        }
        const modal = document.getElementById('progressive-emergency-modal');
        if (modal) modal.classList.add('hidden');
    }

    function saveTickets() {
        localStorage.setItem('tempo_tickets', JSON.stringify(tickets));
    }

    function getTickets() {
        return tickets;
    }

    function updateTicketFromAdmin(updatedTicket) {
        const idx = tickets.findIndex(t => t.id === updatedTicket.id);
        if (idx !== -1) {
            tickets[idx] = updatedTicket;
            saveTickets();
            renderMyTickets();
        }
    }

    return {
        init,
        sendFollowUp,
        getTickets,
        updateTicketFromAdmin,
        openCrisisModal
    };
})();
