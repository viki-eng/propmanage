/**
 * Tickets module – list, detail, create, update.
 */
const Tickets = (() => {
    let currentTicketId = null;

    // ── Helpers ───────────────────────────────────────────────────────

    function statusLabel(s) {
        const map = { open: 'Open', assigned: 'Assigned', in_progress: 'In Progress', done: 'Done' };
        return map[s] || s;
    }

    function priorityLabel(p) {
        const map = { low: 'Low', medium: 'Medium', high: 'High', urgent: 'Urgent' };
        return map[p] || p;
    }

    function timeAgo(dateStr) {
        const diff = Date.now() - new Date(dateStr).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 1) return 'just now';
        if (mins < 60) return `${mins}m ago`;
        const hrs = Math.floor(mins / 60);
        if (hrs < 24) return `${hrs}h ago`;
        const days = Math.floor(hrs / 24);
        if (days < 30) return `${days}d ago`;
        return new Date(dateStr).toLocaleDateString();
    }

    function formatDate(dateStr) {
        return new Date(dateStr).toLocaleString(undefined, {
            year: 'numeric', month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit',
        });
    }

    // ── Render Ticket Card ────────────────────────────────────────────

    function renderCard(ticket) {
        const user = API.getUser();
        const div = document.createElement('div');
        div.className = 'ticket-card';
        div.dataset.id = ticket.id;

        let meta = `
            <span class="status-badge status-${ticket.status}">${statusLabel(ticket.status)}</span>
            <span class="priority-badge priority-${ticket.priority}">${priorityLabel(ticket.priority)}</span>
        `;

        if (user.role === 'manager' && ticket.tenant) {
            meta += `<span class="ticket-card-info">👤 ${ticket.tenant.name}</span>`;
        }
        if (ticket.technician) {
            meta += `<span class="ticket-card-info">🔧 ${ticket.technician.name}</span>`;
        }

        div.innerHTML = `
            <div class="ticket-card-header">
                <span class="ticket-card-title">${escapeHtml(ticket.title)}</span>
                <span class="ticket-card-id">#${ticket.id}</span>
            </div>
            <div class="ticket-card-desc">${escapeHtml(ticket.description)}</div>
            <div class="ticket-card-meta">
                ${meta}
                <span class="ticket-card-info">${timeAgo(ticket.created_at)}</span>
            </div>
        `;

        div.addEventListener('click', () => showDetail(ticket.id));
        return div;
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // ── Load Stats ────────────────────────────────────────────────────

    async function loadStats() {
        try {
            const stats = await API.get('/tickets/stats');
            document.getElementById('stat-total').textContent = stats.total_tickets;
            document.getElementById('stat-open').textContent = stats.open_tickets;
            document.getElementById('stat-assigned').textContent = stats.assigned_tickets;
            document.getElementById('stat-progress').textContent = stats.in_progress_tickets;
            document.getElementById('stat-done').textContent = stats.done_tickets;

            // Update notification badge
            const badge = document.getElementById('notif-badge');
            const sidebarCount = document.getElementById('sidebar-notif-count');
            if (stats.unread_notifications > 0) {
                badge.textContent = stats.unread_notifications;
                badge.classList.remove('hidden');
                sidebarCount.textContent = stats.unread_notifications;
                sidebarCount.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
                sidebarCount.classList.add('hidden');
            }
        } catch (err) {
            console.error('Failed to load stats:', err);
        }
    }

    // ── Load Ticket List ──────────────────────────────────────────────

    async function loadTickets(containerId = 'tickets-list', filters = {}) {
        const container = document.getElementById(containerId);
        container.innerHTML = '<div class="empty-state">Loading...</div>';

        try {
            let params = new URLSearchParams();
            if (filters.status) params.set('status', filters.status);
            if (filters.priority) params.set('priority', filters.priority);
            if (filters.search) params.set('search', filters.search);

            const qs = params.toString() ? `?${params}` : '';
            const tickets = await API.get(`/tickets/${qs}`);

            if (tickets.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📋</div>
                        <p>No tickets found</p>
                    </div>`;
                return;
            }

            container.innerHTML = '';
            tickets.forEach(t => container.appendChild(renderCard(t)));
        } catch (err) {
            container.innerHTML = `<div class="empty-state">Failed to load tickets</div>`;
        }
    }

    // ── Load Dashboard ────────────────────────────────────────────────

    async function loadDashboard() {
        await loadStats();
        await loadTickets('dashboard-tickets');
    }

    // ── Ticket Detail ─────────────────────────────────────────────────

    async function showDetail(ticketId) {
        currentTicketId = ticketId;
        App.showPage('ticket-detail');

        const content = document.getElementById('ticket-detail-content');
        content.innerHTML = '<div class="empty-state">Loading...</div>';

        try {
            const t = await API.get(`/tickets/${ticketId}`);
            const user = API.getUser();

            let imagesHtml = '';
            if (t.images && t.images.length > 0) {
                imagesHtml = `
                    <div class="ticket-images">
                        <div class="ticket-images-title">📎 Attached Images (${t.images.length})</div>
                        <div class="images-grid">
                            ${t.images.map(img => `<img src="${img.filepath}" alt="${escapeHtml(img.filename)}" loading="lazy" onclick="window.open('${img.filepath}','_blank')">`).join('')}
                        </div>
                    </div>`;
            }

            let activityHtml = '';
            if (t.activity_logs && t.activity_logs.length > 0) {
                activityHtml = `
                    <div class="activity-log">
                        <div class="activity-log-title">📋 Activity Log</div>
                        <ul class="activity-list">
                            ${t.activity_logs.map(log => `
                                <li class="activity-item">
                                    <div class="activity-dot"></div>
                                    <div class="activity-content">
                                        <div class="activity-text"><strong>${escapeHtml(log.user.name)}</strong> – ${escapeHtml(log.details || log.action)}</div>
                                        <div class="activity-time">${formatDate(log.created_at)}</div>
                                    </div>
                                </li>
                            `).join('')}
                        </ul>
                    </div>`;
            }

            content.innerHTML = `
                <div class="ticket-detail">
                    <div class="ticket-detail-header">
                        <div class="ticket-detail-title">${escapeHtml(t.title)} <span class="ticket-card-id">#${t.id}</span></div>
                        <div class="ticket-detail-badges">
                            <span class="status-badge status-${t.status}">${statusLabel(t.status)}</span>
                            <span class="priority-badge priority-${t.priority}">${priorityLabel(t.priority)}</span>
                        </div>
                        <div class="ticket-detail-info">
                            <div class="detail-info-item">
                                <div class="detail-info-label">Tenant</div>
                                <div class="detail-info-value">${t.tenant ? escapeHtml(t.tenant.name) : 'N/A'}</div>
                            </div>
                            <div class="detail-info-item">
                                <div class="detail-info-label">Technician</div>
                                <div class="detail-info-value">${t.technician ? escapeHtml(t.technician.name) : 'Unassigned'}</div>
                            </div>
                            <div class="detail-info-item">
                                <div class="detail-info-label">Created</div>
                                <div class="detail-info-value">${formatDate(t.created_at)}</div>
                            </div>
                            <div class="detail-info-item">
                                <div class="detail-info-label">Location</div>
                                <div class="detail-info-value">${t.property_address ? escapeHtml(t.property_address) : '—'}${t.unit_number ? ', Unit ' + escapeHtml(t.unit_number) : ''}</div>
                            </div>
                        </div>
                    </div>
                    <div class="ticket-detail-body">
                        <div class="ticket-detail-desc">${escapeHtml(t.description)}</div>
                        ${imagesHtml}
                    </div>
                    ${activityHtml}
                </div>
            `;

            // Build actions
            renderActions(t, user);
        } catch (err) {
            content.innerHTML = `<div class="empty-state">Failed to load ticket</div>`;
        }
    }

    function renderActions(ticket, user) {
        const container = document.getElementById('ticket-actions');
        container.innerHTML = '';

        if (user.role === 'manager') {
            // Assign button
            const assignBtn = document.createElement('button');
            assignBtn.className = 'btn btn-primary btn-sm';
            assignBtn.textContent = ticket.technician ? 'Reassign' : 'Assign';
            assignBtn.addEventListener('click', () => openAssignModal(ticket));
            container.appendChild(assignBtn);

            // Delete button
            const delBtn = document.createElement('button');
            delBtn.className = 'btn btn-danger btn-sm';
            delBtn.textContent = 'Delete';
            delBtn.addEventListener('click', () => deleteTicket(ticket.id));
            container.appendChild(delBtn);
        }

        if (user.role === 'technician') {
            if (ticket.status === 'assigned') {
                const startBtn = document.createElement('button');
                startBtn.className = 'btn btn-primary btn-sm';
                startBtn.textContent = 'Start Work';
                startBtn.addEventListener('click', () => updateStatus(ticket.id, 'in_progress'));
                container.appendChild(startBtn);
            }
            if (ticket.status === 'in_progress') {
                const doneBtn = document.createElement('button');
                doneBtn.className = 'btn btn-success btn-sm';
                doneBtn.textContent = 'Mark Done';
                doneBtn.addEventListener('click', () => updateStatus(ticket.id, 'done'));
                container.appendChild(doneBtn);
            }
        }
    }

    // ── Status Update ─────────────────────────────────────────────────

    async function updateStatus(ticketId, status) {
        try {
            await API.patch(`/tickets/${ticketId}`, { status });
            App.toast('Status updated', 'success');
            showDetail(ticketId);
            loadStats();
        } catch (err) {
            App.toast(err.message, 'error');
        }
    }

    // ── Assign Modal ──────────────────────────────────────────────────

    async function openAssignModal(ticket) {
        const modal = document.getElementById('assign-modal');
        const select = document.getElementById('assign-tech-select');
        const prioritySelect = document.getElementById('assign-priority-select');

        // Load technicians
        try {
            const techs = await API.get('/users/technicians');
            select.innerHTML = '<option value="">-- Select Technician --</option>';
            techs.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t.id;
                opt.textContent = t.name;
                if (ticket.technician_id === t.id) opt.selected = true;
                select.appendChild(opt);
            });
        } catch {
            select.innerHTML = '<option value="">No technicians found</option>';
        }

        prioritySelect.value = ticket.priority;
        modal.classList.remove('hidden');

        // Handle confirm
        const confirmBtn = document.getElementById('assign-confirm');
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

        newConfirmBtn.addEventListener('click', async () => {
            const techId = parseInt(select.value);
            const priority = prioritySelect.value;

            if (!techId) {
                App.toast('Please select a technician', 'error');
                return;
            }

            try {
                await API.patch(`/tickets/${ticket.id}`, {
                    technician_id: techId,
                    priority: priority,
                });
                modal.classList.add('hidden');
                App.toast('Technician assigned', 'success');
                showDetail(ticket.id);
                loadStats();
            } catch (err) {
                App.toast(err.message, 'error');
            }
        });
    }

    // ── Delete Ticket ─────────────────────────────────────────────────

    async function deleteTicket(ticketId) {
        if (!confirm('Are you sure you want to delete this ticket?')) return;
        try {
            await API.delete(`/tickets/${ticketId}`);
            App.toast('Ticket deleted', 'success');
            App.showPage('tickets');
            loadTickets();
            loadStats();
        } catch (err) {
            App.toast(err.message, 'error');
        }
    }

    // ── Create Ticket ─────────────────────────────────────────────────

    function initCreateForm() {
        const form = document.getElementById('create-ticket-form');
        const imageInput = document.getElementById('ticket-images');
        const preview = document.getElementById('image-preview');
        const errorDiv = document.getElementById('create-error');

        imageInput.addEventListener('change', () => {
            preview.innerHTML = '';
            Array.from(imageInput.files).forEach(file => {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    preview.appendChild(img);
                };
                reader.readAsDataURL(file);
            });
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorDiv.classList.add('hidden');
            const btn = form.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span> Submitting...';

            try {
                const ticket = await API.post('/tickets/', {
                    title: document.getElementById('ticket-title').value.trim(),
                    description: document.getElementById('ticket-desc').value.trim(),
                    property_address: document.getElementById('ticket-address').value.trim() || null,
                    unit_number: document.getElementById('ticket-unit').value.trim() || null,
                    priority: document.getElementById('ticket-priority').value,
                });

                // Upload images if any
                if (imageInput.files.length > 0) {
                    const fd = new FormData();
                    Array.from(imageInput.files).forEach(f => fd.append('files', f));
                    await API.upload(`/tickets/${ticket.id}/images`, fd);
                }

                App.toast('Request submitted!', 'success');
                form.reset();
                preview.innerHTML = '';
                App.showPage('tickets');
                loadTickets();
                loadStats();
            } catch (err) {
                errorDiv.textContent = err.message;
                errorDiv.classList.remove('hidden');
            } finally {
                btn.disabled = false;
                btn.textContent = 'Submit Request';
            }
        });
    }

    // ── Filters ───────────────────────────────────────────────────────

    function initFilters() {
        const statusFilter = document.getElementById('filter-status');
        const priorityFilter = document.getElementById('filter-priority');
        const searchInput = document.getElementById('search-input');
        let searchTimeout;

        function applyFilters() {
            loadTickets('tickets-list', {
                status: statusFilter.value,
                priority: priorityFilter.value,
                search: searchInput.value.trim(),
            });
        }

        statusFilter.addEventListener('change', applyFilters);
        priorityFilter.addEventListener('change', applyFilters);
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(applyFilters, 300);
        });
    }

    // ── Init ──────────────────────────────────────────────────────────

    function init() {
        initCreateForm();
        initFilters();

        // Close assign modal
        document.getElementById('assign-modal-close').addEventListener('click', () => {
            document.getElementById('assign-modal').classList.add('hidden');
        });
        document.getElementById('assign-cancel').addEventListener('click', () => {
            document.getElementById('assign-modal').classList.add('hidden');
        });
        document.querySelector('#assign-modal .modal-overlay').addEventListener('click', () => {
            document.getElementById('assign-modal').classList.add('hidden');
        });
    }

    return {
        init,
        loadDashboard,
        loadTickets,
        loadStats,
        showDetail,
    };
})();
