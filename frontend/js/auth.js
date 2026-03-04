/**
 * Auth module – handles login, register, and session management.
 */
const Auth = (() => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const showRegisterLink = document.getElementById('show-register');
    const showLoginLink = document.getElementById('show-login');
    const loginError = document.getElementById('login-error');
    const registerError = document.getElementById('register-error');

    function init() {
        // Toggle between forms
        showRegisterLink.addEventListener('click', (e) => {
            e.preventDefault();
            loginForm.classList.remove('active');
            registerForm.classList.add('active');
            loginError.classList.add('hidden');
        });

        showLoginLink.addEventListener('click', (e) => {
            e.preventDefault();
            registerForm.classList.remove('active');
            loginForm.classList.add('active');
            registerError.classList.add('hidden');
        });

        // Login
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            loginError.classList.add('hidden');
            const btn = loginForm.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span> Signing in...';

            try {
                const data = await API.post('/auth/login', {
                    email: document.getElementById('login-email').value.trim(),
                    password: document.getElementById('login-password').value,
                });
                API.setToken(data.access_token);
                API.setUser(data.user);
                App.onLogin(data.user);
            } catch (err) {
                loginError.textContent = err.message;
                loginError.classList.remove('hidden');
            } finally {
                btn.disabled = false;
                btn.textContent = 'Sign In';
            }
        });

        // Register
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            registerError.classList.add('hidden');
            const btn = registerForm.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span> Creating...';

            try {
                const data = await API.post('/auth/register', {
                    name: document.getElementById('reg-name').value.trim(),
                    email: document.getElementById('reg-email').value.trim(),
                    phone: document.getElementById('reg-phone').value.trim() || null,
                    password: document.getElementById('reg-password').value,
                    role: document.getElementById('reg-role').value,
                });
                API.setToken(data.access_token);
                API.setUser(data.user);
                App.onLogin(data.user);
            } catch (err) {
                registerError.textContent = err.message;
                registerError.classList.remove('hidden');
            } finally {
                btn.disabled = false;
                btn.textContent = 'Create Account';
            }
        });

        // Demo credential buttons
        document.querySelectorAll('.demo-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.getElementById('login-email').value = btn.dataset.email;
                document.getElementById('login-password').value = btn.dataset.pass;
            });
        });
    }

    return { init };
})();
