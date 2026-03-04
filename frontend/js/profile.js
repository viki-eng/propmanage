/**
 * Profile module – view and edit user profile, upload avatar.
 */
const Profile = (() => {
    const form = document.getElementById('profile-form');
    const avatarInput = document.getElementById('profile-avatar-input');
    const avatarDisplay = document.getElementById('profile-avatar-display');
    const avatarImg = document.getElementById('profile-avatar-img');
    const errorDiv = document.getElementById('profile-error');

    // ── Load Profile Data ─────────────────────────────────────────────

    async function load() {
        try {
            const user = await API.get('/auth/me');
            // Update stored user
            API.setUser(user);
            populateForm(user);
        } catch (err) {
            // Fall back to cached user
            const user = API.getUser();
            if (user) populateForm(user);
        }
    }

    function populateForm(user) {
        const initials = user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);

        // Avatar section
        if (user.avatar_url) {
            avatarImg.src = user.avatar_url;
            avatarImg.classList.remove('hidden');
            avatarDisplay.style.visibility = 'hidden';
        } else {
            avatarDisplay.textContent = initials;
            avatarDisplay.style.visibility = 'visible';
            avatarImg.classList.add('hidden');
        }

        // Meta display
        document.getElementById('profile-display-name').textContent = user.name;
        document.getElementById('profile-display-role').textContent =
            user.role.charAt(0).toUpperCase() + user.role.slice(1);
        document.getElementById('profile-display-email').textContent = user.email;

        // Form fields
        document.getElementById('profile-name').value = user.name || '';
        document.getElementById('profile-phone').value = user.phone || '';
        document.getElementById('profile-bio').value = user.bio || '';
    }

    // ── Avatar Upload ─────────────────────────────────────────────────

    async function handleAvatarUpload() {
        const file = avatarInput.files[0];
        if (!file) return;

        const fd = new FormData();
        fd.append('file', file);

        try {
            const user = await API.upload('/auth/profile/avatar', fd);
            API.setUser(user);
            populateForm(user);
            // Update top bar and sidebar avatars
            App.onLogin(user);
            App.toast('Profile photo updated!', 'success');
        } catch (err) {
            App.toast(err.message || 'Failed to upload photo', 'error');
        }

        // Reset input so same file can be selected again
        avatarInput.value = '';
    }

    // ── Save Profile ──────────────────────────────────────────────────

    async function handleSave(e) {
        e.preventDefault();
        errorDiv.classList.add('hidden');

        const name = document.getElementById('profile-name').value.trim();
        const phone = document.getElementById('profile-phone').value.trim();
        const bio = document.getElementById('profile-bio').value.trim();

        if (!name) {
            errorDiv.textContent = 'Name is required';
            errorDiv.classList.remove('hidden');
            return;
        }

        const btn = form.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Saving...';

        try {
            const user = await API.patch('/auth/profile', { name, phone, bio });
            API.setUser(user);
            populateForm(user);
            // Update top bar and sidebar
            App.onLogin(user);
            App.toast('Profile updated!', 'success');
        } catch (err) {
            errorDiv.textContent = err.message || 'Failed to update profile';
            errorDiv.classList.remove('hidden');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Save Changes';
        }
    }

    // ── Init ──────────────────────────────────────────────────────────

    function init() {
        form.addEventListener('submit', handleSave);
        avatarInput.addEventListener('change', handleAvatarUpload);

        // Profile-page logout button
        document.getElementById('profile-logout-btn').addEventListener('click', () => {
            API.clearToken();
            const appScreen = document.getElementById('app-screen');
            const authScreen = document.getElementById('auth-screen');
            if (appScreen) appScreen.classList.remove('active');
            if (authScreen) authScreen.classList.add('active');
        });
    }

    return { init, load };
})();
