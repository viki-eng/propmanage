/**
 * Notifications module.
 */
const Notifications = (() => {

    async function load() {
        const container = document.getElementById('notifications-list');
        container.innerHTML = '<div class="empty-state">Loading...</div>';

        try {
            const notifs = await API.get('/notifications/');

            if (notifs.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">🔔</div>
                        <p>No notifications yet</p>
                    </div>`;
                return;
            }

            container.innerHTML = '';
            notifs.forEach(n => {
                const div = document.createElement('div');
                div.className = `notification-item ${n.is_read ? '' : 'unread'}`;
                div.innerHTML = `
                    <div class="notification-title">${escapeHtml(n.title)}</div>
                    <div class="notification-message">${escapeHtml(n.message)}</div>
                    <div class="notification-time">${timeAgo(n.created_at)}</div>
                `;
                div.addEventListener('click', async () => {
                    if (!n.is_read) {
                        await API.patch(`/notifications/${n.id}/read`);
                        div.classList.remove('unread');
                        Tickets.loadStats();
                    }
                    if (n.link && n.link.startsWith('/tickets/')) {
                        const ticketId = n.link.split('/').pop();
                        Tickets.showDetail(parseInt(ticketId));
                    }
                });
                container.appendChild(div);
            });
        } catch (err) {
            container.innerHTML = `<div class="empty-state">Failed to load notifications</div>`;
        }
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
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

    async function markAllRead() {
        try {
            await API.patch('/notifications/read-all');
            load();
            Tickets.loadStats();
            App.toast('All marked as read', 'success');
        } catch (err) {
            App.toast(err.message, 'error');
        }
    }

    function init() {
        document.getElementById('mark-all-read-btn').addEventListener('click', markAllRead);
    }

    return { init, load };
})();
