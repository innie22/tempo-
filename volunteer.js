/**
 * Tempo Volunteer Dashboard Controller
 * Enforces strict access control: Only APPROVED volunteers can access support functionality.
 * Pending volunteers see an under-review notice with no access to student conversations.
 */

window.TempoVolunteer = (function() {
    let availableRequests = [];
    let assignedRequests = [];
    let isOnline = false;

    function init() {
        bindEvents();
    }

    function bindEvents() {
        const toggleOnlineBtn = document.getElementById('btn-volunteer-toggle-online');
        if (toggleOnlineBtn) {
            toggleOnlineBtn.addEventListener('click', toggleOnlineStatus);
        }
    }

    async function render() {
        const vProfile = window.TempoAuth ? window.TempoAuth.getCurrentVolunteerProfile() : null;
        const status = vProfile?.application_status || 'PENDING';

        const pendingView = document.getElementById('volunteer-view-pending');
        const approvedView = document.getElementById('volunteer-view-approved');
        const restrictedView = document.getElementById('volunteer-view-restricted');

        if (status === 'PENDING') {
            if (pendingView) pendingView.classList.remove('hidden');
            if (approvedView) approvedView.classList.add('hidden');
            if (restrictedView) restrictedView.classList.add('hidden');
        } else if (status === 'APPROVED') {
            if (pendingView) pendingView.classList.add('hidden');
            if (approvedView) approvedView.classList.remove('hidden');
            if (restrictedView) restrictedView.classList.add('hidden');
            loadVolunteerData();
        } else {
            // REJECTED or SUSPENDED
            if (pendingView) pendingView.classList.add('hidden');
            if (approvedView) approvedView.classList.add('hidden');
            if (restrictedView) restrictedView.classList.remove('hidden');
        }
    }

    async function loadVolunteerData() {
        const supabase = window.TempoSupabase ? window.TempoSupabase.getClient() : null;
        if (!supabase) return;

        try {
            // Load open support requests
            const { data: openReqs } = await supabase
                .from('support_requests')
                .select('*')
                .eq('status', 'OPEN')
                .order('created_at', { ascending: false });

            availableRequests = openReqs || [];

            // Load assigned requests
            const user = window.TempoAuth.getCurrentUser();
            if (user) {
                const { data: myReqs } = await supabase
                    .from('support_requests')
                    .select('*')
                    .eq('assigned_volunteer_id', user.id);
                assignedRequests = myReqs || [];
            }

            renderRequestsUI();

        } catch (e) {
            console.error("Error loading volunteer data:", e);
        }
    }

    function renderRequestsUI() {
        const queueContainer = document.getElementById('volunteer-available-queue');
        const assignedContainer = document.getElementById('volunteer-assigned-queue');

        if (queueContainer) {
            if (availableRequests.length === 0) {
                queueContainer.innerHTML = `
                    <div class="p-6 text-center text-gray-500 bg-stone-50 rounded-2xl border border-stone-200">
                        <p class="text-xs">No pending peer-support requests right now. Thank you for your readiness!</p>
                    </div>
                `;
            } else {
                queueContainer.innerHTML = availableRequests.map(r => `
                    <div class="p-4 bg-white border border-gray-200 rounded-xl space-y-2 hover:border-[#FF6B2C] transition">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-semibold text-[#B83D08] bg-[#FFE9DC] px-2 py-0.5 rounded border border-[#FFD2BA]">${r.category}</span>
                            <span class="text-[10px] text-gray-400 font-mono">Urgency: ${r.urgency}</span>
                        </div>
                        <h5 class="text-sm font-bold text-gray-900">${r.subject}</h5>
                        <div class="flex justify-end pt-2">
                            <button onclick="window.TempoVolunteer.claimRequest('${r.id}')" 
                                class="btn-primary px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-sm">
                                Accept & Respond
                            </button>
                        </div>
                    </div>
                `).join('');
            }
        }

        if (assignedContainer) {
            if (assignedRequests.length === 0) {
                assignedContainer.innerHTML = `
                    <div class="p-6 text-center text-gray-500 bg-stone-50 rounded-2xl border border-stone-200">
                        <p class="text-xs">You currently have no active assigned conversations.</p>
                    </div>
                `;
            } else {
                assignedContainer.innerHTML = assignedRequests.map(r => `
                    <div class="p-4 bg-white border border-[#FFD2BA] rounded-xl space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold text-gray-900">${r.subject}</span>
                            <span class="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-100 text-emerald-800">${r.status}</span>
                        </div>
                        <p class="text-xs text-gray-500">${r.category}</p>
                    </div>
                `).join('');
            }
        }
    }

    async function claimRequest(requestId) {
        // Strict Authorization Gate: Must be verified APPROVED volunteer
        const vProfile = window.TempoAuth ? window.TempoAuth.getCurrentVolunteerProfile() : null;
        if (!vProfile || vProfile.application_status !== 'APPROVED') {
            window.TempoApp.showToast("Security violation: Only approved volunteers can claim student support requests.");
            return;
        }

        const supabase = window.TempoSupabase ? window.TempoSupabase.getClient() : null;
        const user = window.TempoAuth.getCurrentUser();
        if (!supabase || !user) return;

        try {
            const { error } = await supabase
                .from('support_requests')
                .update({
                    assigned_volunteer_id: user.id,
                    status: 'ASSIGNED',
                    updated_at: new Date().toISOString()
                })
                .eq('id', requestId);

            if (error) {
                window.TempoApp.showToast("Could not claim request: " + error.message);
                return;
            }

            window.TempoApp.showToast("Request assigned to you! You can now send peer support.");
            loadVolunteerData();

        } catch (err) {
            console.error(err);
        }
    }

    async function toggleOnlineStatus() {
        // Strict Authorization Gate: Must be verified APPROVED volunteer
        const vProfile = window.TempoAuth ? window.TempoAuth.getCurrentVolunteerProfile() : null;
        if (!vProfile || vProfile.application_status !== 'APPROVED') {
            window.TempoApp.showToast("Security violation: Only approved volunteers can broadcast online availability.");
            return;
        }

        const supabase = window.TempoSupabase ? window.TempoSupabase.getClient() : null;
        const user = window.TempoAuth.getCurrentUser();
        if (!supabase || !user) return;

        const newStatus = !isOnline;

        const { error } = await supabase
            .from('volunteer_profiles')
            .update({ is_online: newStatus })
            .eq('user_id', user.id);

        if (error) {
            window.TempoApp.showToast("Failed to update status: " + error.message);
            return;
        }

        isOnline = newStatus;
        const btn = document.getElementById('btn-volunteer-toggle-online');
        if (btn) {
            btn.textContent = isOnline ? "Status: Online (Active)" : "Status: Offline";
            btn.className = isOnline 
                ? "px-3.5 py-1.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300"
                : "px-3.5 py-1.5 rounded-full text-xs font-bold bg-stone-100 text-stone-600 border border-stone-300";
        }

        window.TempoApp.showToast(`Your availability updated to: ${isOnline ? 'Online' : 'Offline'}`);
    }

    return {
        init,
        render,
        claimRequest,
        toggleOnlineStatus
    };
})();
