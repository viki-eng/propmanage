/**
 * App module – orchestrates navigation, initialization, and UI state.
 */
const App = (() => {
    const authScreen = document.getElementById('auth-screen');
    const appScreen = document.getElementById('app-screen');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const menuToggle = document.getElementById('menu-toggle');

    let currentPage = 'dashboard';

    // ── Navigation ────────────────────────────────────────────────────

    function showPage(page) {
        currentPage = page;
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        const target = document.getElementById(`page-${page}`);
        if (target) target.classList.add('active');

        // Update sidebar active state
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.toggle('active', link.dataset.page === page);
        });

        // Close sidebar on mobile
        sidebar.classList.remove('open');

        // Load page data
        switch (page) {
            case 'dashboard':
                Tickets.loadDashboard();
                break;
            case 'tickets':
                Tickets.loadTickets();
                break;
            case 'notifications':
                Notifications.load();
                break;
            case 'profile':
                Profile.load();
                break;
        }
    }

    // ── Sidebar Toggle ────────────────────────────────────────────────

    function initSidebar() {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });

        sidebarOverlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
        });

        // Sidebar nav links
        document.querySelectorAll('.nav-link[data-page]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                showPage(link.dataset.page);
            });
        });
    }

    // ── Login Handler ─────────────────────────────────────────────────

    function onLogin(user) {
        authScreen.classList.remove('active');
        appScreen.classList.add('active');
        setupUserUI(user);
        showPage('dashboard');
    }

    function setupUserUI(user) {
        const initials = user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);

        // Top-bar avatar
        const topAvatar = document.getElementById('user-avatar');
        if (user.avatar_url) {
            topAvatar.innerHTML = `<img src="${user.avatar_url}" alt="Avatar">`;
            topAvatar.classList.add('avatar-has-img');
        } else {
            topAvatar.textContent = initials;
            topAvatar.classList.remove('avatar-has-img');
        }

        // Sidebar avatar
        const sideAvatar = document.getElementById('sidebar-avatar');
        if (user.avatar_url) {
            sideAvatar.innerHTML = `<img src="${user.avatar_url}" alt="Avatar">`;
            sideAvatar.classList.add('avatar-has-img');
        } else {
            sideAvatar.textContent = initials;
            sideAvatar.classList.remove('avatar-has-img');
        }

        document.getElementById('sidebar-name').textContent = user.name;
        document.getElementById('sidebar-role').textContent = user.role.charAt(0).toUpperCase() + user.role.slice(1);

        // Show/hide "New Request" button based on role
        const canCreate = user.role === 'tenant' || user.role === 'manager';
        document.getElementById('new-ticket-btn').style.display = canCreate ? '' : 'none';
        document.getElementById('new-ticket-btn-2').style.display = canCreate ? '' : 'none';
    }

    // ── Logout ────────────────────────────────────────────────────────

    function logout() {
        API.clearToken();
        appScreen.classList.remove('active');
        authScreen.classList.add('active');
        document.getElementById('login-form').classList.add('active');
        document.getElementById('register-form').classList.remove('active');
        document.getElementById('login-email').value = '';
        document.getElementById('login-password').value = '';
    }

    // ── Toast ─────────────────────────────────────────────────────────

    function toast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const div = document.createElement('div');
        div.className = `toast toast-${type}`;
        div.textContent = message;
        container.appendChild(div);
        setTimeout(() => div.remove(), 3000);
    }

    // ── Init ──────────────────────────────────────────────────────────

    function init() {
        Auth.init();
        Tickets.init();
        Notifications.init();
        Profile.init();
        initSidebar();

        // New ticket buttons
        document.getElementById('new-ticket-btn').addEventListener('click', () => showPage('create-ticket'));
        document.getElementById('new-ticket-btn-2').addEventListener('click', () => showPage('create-ticket'));

        // Back buttons
        document.getElementById('back-to-tickets').addEventListener('click', () => showPage('tickets'));
        document.getElementById('back-from-create').addEventListener('click', () => showPage('tickets'));

        // Notification bell
        document.getElementById('notif-btn').addEventListener('click', () => showPage('notifications'));

        // User avatar -> profile page
        document.getElementById('user-avatar').addEventListener('click', () => showPage('profile'));

        // Logout link in sidebar
        document.getElementById('logout-btn').addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });

        // Check if already logged in
        const token = API.getToken();
        const user = API.getUser();
        if (token && user) {
            onLogin(user);
        }
    }

    // Boot
    document.addEventListener('DOMContentLoaded', init);

    return { showPage, onLogin, toast };
})();
