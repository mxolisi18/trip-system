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
    const idRegex = /^[A-Za-z0-9]{10,16}$/;
    if (employeeId && !idRegex.test(employeeId)) {
        alert('Employee ID must be 10-16 alphanumeric characters');
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
        } else {
            window.location.href = 'login.html';
        }
    }
});