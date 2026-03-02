let authHeader = null;
let currentUser = null;

function persistAuth(user, pass) {
    authHeader = 'Basic ' + btoa(user + ':' + pass);
    currentUser = user;
    localStorage.setItem('auth', JSON.stringify({ user, pass }));
}

function loadPersistedAuth() {
    const v = localStorage.getItem('auth');
    if (v) {
        const { user, pass } = JSON.parse(v);
        persistAuth(user, pass);
    }
}

function login() {
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    persistAuth(user, pass);
    window.location.href = 'landing.html';
}

function signup() {
    const fullName = document.getElementById('full_name').value;
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    const employeeId = document.getElementById('employee_id').value;
    const company = document.getElementById('company').value;
    const pass = document.getElementById('new_password').value;
    const confirm = document.getElementById('confirm_password').value;

    if (!company) {
        alert('Company is required');
        return;
    }

    if (pass !== confirm) {
        alert('Passwords do not match');
        return;
    }

    // enforce simple employee ID format: alphanumeric 2-10 characters
    const idRegex = /^[A-Za-z0-9]{2,10}$/;
    if (employeeId && !idRegex.test(employeeId)) {
        alert('Employee ID must be 2-10 alphanumeric characters');
        return;
    }

    const payload = {
        username: email, // use email as username
        password: pass,
        full_name: fullName,
        phone,
        employee_id: employeeId,
        company
    };

    fetch('/api/users/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    }).then(async r => {
        if (r.status === 201) {
            alert('Account registered, please login.');
            window.location.href = 'login.html';
        } else {
            let msg = 'Failed to register';
            try {
                const data = await r.json();
                if (data && data.error) msg += ': ' + data.error;
            } catch {}
            alert(msg);
        }
    });
}

function createTrip() {
    const start = parseFloat(document.getElementById('start_odometer').value);
    const end = parseFloat(document.getElementById('end_odometer').value);
    fetch('/api/trips/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': authHeader
        },
        body: JSON.stringify({ start_odometer: start, end_odometer: end })
    }).then(r => r.json()).then(console.log);
}

function loadTrips() {
    fetch('/api/trips/', { headers: { 'Authorization': authHeader } })
        .then(r => r.json())
        .then(trips => {
            const ul = document.getElementById('trips');
            if (!ul) return;
            ul.innerHTML = '';
            trips.forEach(t => {
                const li = document.createElement('li');
                li.textContent = `Trip ${t.id}: ${t.distance} km (${t.duration})`;
                ul.appendChild(li);
            });
        });
}

function gotoTrips() {
    window.location.href = 'trips.html';
}

function gotoNewTrip() {
    window.location.href = 'newtrip.html';
}

function logout() {
    localStorage.removeItem('auth');
    window.location.href = 'login.html';
}

// on landing page load, populate greeting and ensure auth
window.addEventListener('DOMContentLoaded', () => {
    loadPersistedAuth();
    if (window.location.pathname.endsWith('landing.html')) {
        if (currentUser) {
            const greet = document.getElementById('greeting');
            if (greet) greet.textContent = `Welcome, ${currentUser}!`;
            const adminBtn = document.getElementById('admin_button');
            if (adminBtn) adminBtn.style.display = 'inline-block';
        } else {
            window.location.href = 'login.html';
        }
    }

    if (window.location.pathname.endsWith('admin.html')) {
        loadPersistedAuth();
        if (!currentUser) {
            window.location.href = 'login.html';
            return;
        }
        loadRegistry();
        loadStats();
        loadAttempts();
    }
});

// navigation helpers
function gotoAdmin() {
    window.location.href = 'admin.html';
}
function gotoLanding() {
    window.location.href = 'landing.html';
}

// admin helpers
function loadRegistry() {
    fetch('/api/admin/registry', { headers: { 'Authorization': authHeader } })
        .then(r => r.json())
        .then(regs => {
            const ul = document.getElementById('registry_list');
            if (!ul) return;
            ul.innerHTML = '';
            regs.forEach(r => {
                const li = document.createElement('li');
                li.textContent = `${r.company}: ${r.employee_id}`;
                const btn = document.createElement('button');
                btn.textContent = 'Delete';
                btn.onclick = () => deleteRegistryEntry(r.id);
                li.appendChild(btn);
                ul.appendChild(li);
            });
        });
}

function addRegistryEntry() {
    const company = document.getElementById('admin_company').value;
    const employeeId = document.getElementById('admin_employee_id').value;
    fetch('/api/admin/registry', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: authHeader
        },
        body: JSON.stringify({ company, employee_id: employeeId })
    }).then(r => {
        if (r.status === 201) {
            loadRegistry();
        } else {
            alert('Failed to add entry');
        }
    });
}

function deleteRegistryEntry(id) {
    fetch(`/api/admin/registry/${id}`, {
        method: 'DELETE',
        headers: { Authorization: authHeader }
    }).then(r => {
        if (r.status === 200) loadRegistry();
    });
}

function loadStats() {
    fetch('/api/admin/stats', { headers: { 'Authorization': authHeader } })
        .then(r => r.json())
        .then(s => {
            const ul = document.getElementById('admin_stats');
            if (!ul) return;
            ul.innerHTML = '';
            Object.entries(s).forEach(([k, v]) => {
                const li = document.createElement('li');
                li.textContent = `${k}: ${v}`;
                ul.appendChild(li);
            });
        });
}

function loadAttempts() {
    fetch('/api/admin/attempts', { headers: { 'Authorization': authHeader } })
        .then(r => r.json())
        .then(attempts => {
            const ul = document.getElementById('attempts_list');
            if (!ul) return;
            ul.innerHTML = '';
            attempts.forEach(a => {
                const li = document.createElement('li');
                li.textContent = `${a.timestamp || ''} ${a.company || ''}:${a.employee_id || ''} success=${a.success}`;
                ul.appendChild(li);
            });
        });
}
