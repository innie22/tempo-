/**
 * Tempo Admin / Advisor Portal (Dr. Elena Vance)
 * Streamlined support inbox triage, 1-click empathetic templates, and micro-tip publishing.
 */

window.TempoAdmin = (function() {
    let currentFilter = 'all';
    let selectedTicketId = null;
    let tips = [];

    // Pre-written Empathetic Advisor Templates
    function getTemplate(tplKey, studentName) {
        const name = studentName || 'there';
        const templates = {
            extension: `Hi ${name}, thank you for reaching out. First, please know that taking a pause to protect your health is the right decision. \n\nI strongly encourage you to send an extension request for the Marketing Report right now. Most professors are very accommodating if you write before the deadline. You can use the template from our Knowledge Hub (under 'Asking for Help'). \n\nPropose a concrete alternative time, such as Sunday at 5:00 PM. Let me know if you would like me to review your email draft before you send it.`,
            deescalate: `Hi ${name}, take a slow breath. When three deadlines converge, your nervous system is in full emergency mode. \n\nTonight, let's focus exclusively on ONE task: the 9:00 AM report. Give yourself full permission to ignore the Friday slides until tomorrow afternoon. Getting 6 hours of sleep tonight will make you twice as productive tomorrow. I am here if you need more support.`,
            dropin: `Hi ${name}, I can see how much pressure you have been carrying this week. \n\nI have an open drop-in wellbeing slot tomorrow at 11:30 AM (virtual or in Student Center 304). Would you like me to hold that for you? We can sit down together and map out a gentle plan for the rest of your semester.`
        };
        return templates[tplKey] || '';
    }

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
                e.currentTarget.className = "admin-ticket-filter px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#FF6B2C] text-white transition";
                currentFilter = e.currentTarget.dataset.filter;
                renderTickets();
            });
        });

        // Template Quick Buttons
        document.querySelectorAll('.btn-use-template').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tplKey = e.currentTarget.dataset.template;
                const replyTextarea = document.getElementById('admin-reply-textarea');
                const tickets = window.TempoSupport ? window.TempoSupport.getTickets() : [];
                const currentTicket = tickets.find(t => t.id === selectedTicketId);
                let studentGreetingName = 'there';
                if (currentTicket && currentTicket.studentName) {
                    const rawName = currentTicket.studentName.replace(/\s*\(You\)$/, '');
                    if (window.TempoAuth && typeof window.TempoAuth.extractGreetingName === 'function') {
                        studentGreetingName = window.TempoAuth.extractGreetingName(rawName) || 'there';
                    } else {
                        studentGreetingName = rawName.split(' ')[0] || 'there';
                    }
                }
                const templateContent = getTemplate(tplKey, studentGreetingName);
                if (replyTextarea && templateContent) {
                    replyTextarea.value = templateContent;
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
                <div class="p-4 border-b border-gray-100 hover:bg-stone-50 cursor-pointer transition ${isSelected ? 'bg-[#FFE9DC]/50' : ''}" 
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
            <div class="p-3.5 rounded-xl ${m.sender === 'student' ? 'bg-stone-100 text-gray-800 mr-8' : 'bg-[#FFF9F4] border border-[#FFD2BA] text-gray-900 ml-8'}">
                <div class="flex items-center justify-between text-[11px] mb-1 opacity-80">
                    <span class="font-bold ${m.sender === 'student' ? 'text-gray-700' : 'text-[#FF6B2C]'}">${m.senderName}</span>
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
                        <span class="text-xs font-semibold px-2 py-0.5 rounded bg-[#FFE9DC] text-[#B83D08] border border-[#FFD2BA]">${tip.category}</span>
                        <span class="text-xs text-gray-400 font-medium">${tip.readMinutes} min read</span>
                    </div>
                    <h4 class="text-sm font-bold text-gray-900">${tip.title}</h4>
                    <p class="text-xs text-gray-600 line-clamp-2 max-w-xl">${tip.content}</p>
                </div>
                <div class="flex items-center space-x-2">
                    <button onclick="window.TempoAdmin.toggleTipPublish('${tip.id}')" 
                        class="px-3 py-1.5 rounded-lg text-xs font-medium border ${tip.isPublished ? 'border-[#FF6B2C] text-[#FF6B2C] bg-[#FFE9DC]/50' : 'border-gray-300 text-gray-600'}">
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

    // =========================================================================
    // VOLUNTEER APPLICATIONS MANAGEMENT (US04)
    // =========================================================================
    let volunteerApplications = [];
    let currentVolFilter = 'all';

    async function loadVolunteerApplications() {
        const supabase = window.TempoSupabase ? window.TempoSupabase.getClient() : null;
        if (supabase) {
            try {
                // Fetch profiles with volunteer role
                const { data, error } = await supabase
                    .from('volunteer_profiles')
                    .select('*, profiles(full_name, email)');

                if (!error && data) {
                    volunteerApplications = data.map(v => ({
                        userId: v.user_id,
                        fullName: v.profiles?.full_name || 'Volunteer Applicant',
                        email: v.profiles?.email || 'N/A',
                        universityOrOrg: v.university_or_organization,
                        background: v.background,
                        studyYear: v.study_year_or_qualification,
                        experience: v.experience,
                        motivation: v.motivation,
                        availability: v.availability,
                        applicationStatus: v.application_status,
                        reviewedAt: v.reviewed_at,
                        createdAt: v.created_at
                    }));
                }
            } catch (e) {
                console.error("Error loading volunteer applications:", e);
            }
        }

        // If no remote apps yet, populate with realistic demo applications
        if (volunteerApplications.length === 0) {
            volunteerApplications = [
                {
                    userId: 'vol-demo-1',
                    fullName: 'Maya Lin',
                    email: 'm.lin@university.edu',
                    universityOrOrg: 'Faculty of Psychology & Neuroscience',
                    background: 'Psychology student',
                    studyYear: 'Year 3 (BSc Psychology)',
                    experience: 'Completed 40 hours of active listening peer mentorship training; campus wellbeing volunteer last semester.',
                    motivation: 'I know how isolating exam crunch periods can be. I want to offer an empathetic, non-judgmental presence to fellow students.',
                    availability: 'Weekday evenings (6:00 PM – 9:00 PM)',
                    applicationStatus: 'PENDING',
                    createdAt: '2 hours ago'
                },
                {
                    userId: 'vol-demo-2',
                    fullName: 'Samuel Chen',
                    email: 's.chen@university.edu',
                    universityOrOrg: 'School of Education & Counseling',
                    background: 'Counseling-related field',
                    studyYear: 'Master of Education (Guidance & Counseling)',
                    experience: 'Certified in Youth Mental Health First Aid (YMHFA); 2 years volunteer at community youth hotline.',
                    motivation: 'Passionate about helping students unfreeze academic paralysis without clinical stigmatization.',
                    availability: 'Weekends & Friday afternoons',
                    applicationStatus: 'APPROVED',
                    createdAt: '3 days ago'
                }
            ];
        }

        renderVolunteerApplications();
    }

    function renderVolunteerApplications() {
        const container = document.getElementById('admin-volunteer-applications-list');
        if (!container) return;

        const pendingCount = volunteerApplications.filter(a => a.applicationStatus === 'PENDING').length;
        const countBadge = document.getElementById('admin-vol-pending-count');
        if (countBadge) countBadge.textContent = pendingCount;

        const filtered = volunteerApplications.filter(app => {
            if (currentVolFilter === 'all') return true;
            return app.applicationStatus === currentVolFilter;
        });

        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="p-8 text-center text-gray-500 bg-stone-50 rounded-2xl border border-stone-200">
                    <p class="text-xs">No volunteer applications in this status filter.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = filtered.map(app => {
            let statusBadgeClass = 'bg-amber-100 text-amber-800';
            if (app.applicationStatus === 'APPROVED') statusBadgeClass = 'bg-emerald-100 text-emerald-800';
            if (app.applicationStatus === 'REJECTED') statusBadgeClass = 'bg-rose-100 text-rose-800';
            if (app.applicationStatus === 'SUSPENDED') statusBadgeClass = 'bg-purple-100 text-purple-800';

            return `
                <div class="tempo-card p-5 space-y-4 border-gray-200 hover:border-[#FF6B2C] transition">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-gray-100">
                        <div>
                            <div class="flex items-center space-x-2">
                                <h4 class="font-heading text-base font-bold text-gray-900">${app.fullName}</h4>
                                <span class="px-2.5 py-0.5 rounded-full text-xs font-bold ${statusBadgeClass}">
                                    ${app.applicationStatus}
                                </span>
                            </div>
                            <p class="text-xs text-gray-500">${app.email} • ${app.universityOrOrg}</p>
                        </div>
                        <span class="text-[11px] text-gray-400 font-medium">${app.background}</span>
                    </div>

                    <!-- Details Grid -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-gray-700">
                        <div class="space-y-1">
                            <span class="font-bold text-gray-500 uppercase tracking-wider text-[10px]">Study Year / Qualification:</span>
                            <p class="font-medium text-gray-900">${app.studyYear}</p>
                        </div>
                        <div class="space-y-1">
                            <span class="font-bold text-gray-500 uppercase tracking-wider text-[10px]">General Availability:</span>
                            <p class="font-medium text-gray-900">${app.availability}</p>
                        </div>
                        <div class="space-y-1 col-span-full">
                            <span class="font-bold text-gray-500 uppercase tracking-wider text-[10px]">Relevant Background & Experience:</span>
                            <p class="leading-relaxed bg-stone-50 p-2.5 rounded-xl border border-stone-200">${app.experience}</p>
                        </div>
                        <div class="space-y-1 col-span-full">
                            <span class="font-bold text-gray-500 uppercase tracking-wider text-[10px]">Motivation to Volunteer:</span>
                            <p class="leading-relaxed bg-stone-50 p-2.5 rounded-xl border border-stone-200">${app.motivation}</p>
                        </div>
                    </div>

                    <!-- Decision Controls -->
                    <div class="pt-3 border-t border-gray-100 flex flex-wrap items-center justify-between gap-2">
                        <span class="text-[11px] text-gray-500 italic">Peer Support Agreement: Acknowledged ✓</span>
                        <div class="flex items-center space-x-2">
                            <button onclick="window.TempoAdmin.setApplicationStatus('${app.userId}', 'APPROVED')" 
                                class="px-3.5 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-bold transition shadow-sm">
                                ✓ Approve
                            </button>
                            <button onclick="window.TempoAdmin.setApplicationStatus('${app.userId}', 'REJECTED')" 
                                class="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-xs font-semibold transition">
                                Reject
                            </button>
                            <button onclick="window.TempoAdmin.setApplicationStatus('${app.userId}', 'SUSPENDED')" 
                                class="px-3 py-1.5 bg-stone-100 hover:bg-stone-200 text-stone-600 rounded-lg text-xs font-medium transition">
                                Suspend
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    async function setApplicationStatus(userId, newStatus) {
        // 1. Strict Authorization Gate: Caller must be an authenticated administrator
        const currentProfile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
        if (!currentProfile || currentProfile.role !== 'admin') {
            window.TempoApp.showToast("Security violation: Only verified administrators can review volunteer applications.");
            return;
        }

        const app = volunteerApplications.find(a => a.userId === userId);
        if (!app) return;

        const supabase = window.TempoSupabase ? window.TempoSupabase.getClient() : null;
        if (supabase) {
            try {
                const currentUser = window.TempoAuth.getCurrentUser();
                const { error } = await supabase
                    .from('volunteer_profiles')
                    .update({
                        application_status: newStatus,
                        reviewed_at: new Date().toISOString(),
                        reviewed_by: currentUser?.id || null
                    })
                    .eq('user_id', userId);

                if (error) {
                    console.error("[TempoAdmin] Review action rejected by database:", error.message);
                    window.TempoApp.showToast(`Action rejected by database security: ${error.message}`);
                    return; // Strictly abort: do NOT mutate client-side state
                }
            } catch (e) {
                console.error("[TempoAdmin] Network or database error:", e);
                window.TempoApp.showToast("Failed to contact database. Client state unchanged.");
                return; // Strictly abort
            }
        }

        // 2. Only mutate client state AFTER database confirms success
        app.applicationStatus = newStatus;
        renderVolunteerApplications();
        window.TempoApp.showToast(`Volunteer application for ${app.fullName} is now ${newStatus}.`);

        // If currently viewing as that volunteer, refresh their view
        if (window.TempoAuth?.getCurrentUser()?.id === userId) {
            window.TempoAuth.loadUserProfile(userId);
        }
    }

    function filterVolunteerApplications(status) {
        currentVolFilter = status;
        document.querySelectorAll('.admin-vol-filter').forEach(btn => {
            btn.className = "admin-vol-filter px-2.5 py-1 rounded-lg text-xs font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition";
        });
        const activeBtn = document.getElementById(`btn-vol-filter-${status.toLowerCase()}`);
        if (activeBtn) activeBtn.className = "admin-vol-filter px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#FF6B2C] text-white transition";
        renderVolunteerApplications();
    }

    function switchTab(tab) {
        document.querySelectorAll('.admin-main-tab').forEach(btn => {
            btn.className = "admin-main-tab px-4 py-2 rounded-xl text-xs font-semibold bg-stone-100 text-gray-700 hover:bg-stone-200 transition";
        });
        document.querySelectorAll('.admin-tab-pane').forEach(pane => {
            pane.classList.add('hidden');
        });

        const activeBtn = document.getElementById(`btn-admin-tab-${tab}`);
        if (activeBtn) activeBtn.className = "admin-main-tab px-4 py-2 rounded-xl text-xs font-bold bg-[#FF6B2C] text-white transition shadow-sm";

        const activePane = document.getElementById(`admin-tab-${tab}-pane`);
        if (activePane) activePane.classList.remove('hidden');

        if (tab === 'volunteers') {
            loadVolunteerApplications();
        }
    }

    return {
        init,
        renderTickets,
        selectTicket,
        toggleTipPublish,
        loadVolunteerApplications,
        renderVolunteerApplications,
        setApplicationStatus,
        filterVolunteerApplications,
        switchTab
    };
})();


