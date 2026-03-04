/**
 * API module – handles all HTTP requests to the backend.
 */
const API = (() => {
    const BASE = '/api';

    function getToken() {
        return localStorage.getItem('token');
    }

    function setToken(token) {
        localStorage.setItem('token', token);
    }

    function clearToken() {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
    }

    function getUser() {
        try {
            return JSON.parse(localStorage.getItem('user'));
        } catch {
            return null;
        }
    }

    function setUser(user) {
        localStorage.setItem('user', JSON.stringify(user));
    }

    async function request(method, path, body = null, isFormData = false) {
        const headers = {};
        const token = getToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;
        if (!isFormData && body) headers['Content-Type'] = 'application/json';

        const opts = { method, headers };
        if (body) {
            opts.body = isFormData ? body : JSON.stringify(body);
        }

        const res = await fetch(`${BASE}${path}`, opts);

        if (res.status === 401) {
            clearToken();
            // Gracefully show login screen instead of hard reload
            const appScreen = document.getElementById('app-screen');
            const authScreen = document.getElementById('auth-screen');
            if (appScreen) appScreen.classList.remove('active');
            if (authScreen) authScreen.classList.add('active');
            throw new Error('Session expired. Please log in again.');
        }

        if (res.status === 204) return null;

        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || 'Something went wrong');
        }
        return data;
    }

    return {
        getToken,
        setToken,
        clearToken,
        getUser,
        setUser,
        get: (path) => request('GET', path),
        post: (path, body) => request('POST', path, body),
        patch: (path, body) => request('PATCH', path, body),
        delete: (path) => request('DELETE', path),
        upload: (path, formData) => request('POST', path, formData, true),
    };
})();
