const BASE_URL = 'http://localhost:8000';

const API = {
    async get(endpoint, params = {}) {
        const token = localStorage.getItem('token');
        const url = new URL(`${BASE_URL}${endpoint}`);
        Object.keys(params).forEach(key => {
            if (params[key]) url.searchParams.append(key, params[key]);
        });

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) {
            if (response.status === 401) this.logout();
            return [];
        }
        return await response.json();
    },

    async post(endpoint, data) {
        const token = localStorage.getItem('token');
        const response = await fetch(`${BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        return await response.json();
    },

    async put(endpoint, data) {
        const token = localStorage.getItem('token');
        const response = await fetch(`${BASE_URL}${endpoint}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        return await response.json();
    },

    async del(endpoint) {
        const token = localStorage.getItem('token');
        const response = await fetch(`${BASE_URL}${endpoint}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        return await response.json();
    },

    async postStudentLogin(roll_no, password) {
        const url = new URL(`${BASE_URL}/login/student`);
        url.searchParams.append('roll_no', roll_no);
        url.searchParams.append('password', password);
        const response = await fetch(url.toString(), { method: 'POST' });
        return await response.json();
    },

    logout() {
        localStorage.clear();
        window.location.href = 'index.html';
    }
};
