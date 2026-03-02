from backend.models import User, Trip, db, RegistrationAttempt

import logging
from base64 import b64encode

def test_user_creation_and_auth(client, caplog):
    # seed registry entries
    from backend.models import EmployeeRegistry, db, User
    with client.application.app_context():
        db.session.add(EmployeeRegistry(company='Acme Corp', employee_id='E123'))
        db.session.commit()
        # default seeded account should already be present
        assert User.query.filter_by(username='mxolisimazwi16@gmail.com').first() is not None

    # confirm we can authenticate with the seeded credentials
    auth_header_seed = {'Authorization': 'Basic ' + b64encode(b'mxolisimazwi16@gmail.com:123456').decode()}
    resp = client.get('/api/users/', headers=auth_header_seed)
    assert resp.status_code == 200

    # valid registration should succeed
    resp = client.post('/api/users/', json={
        'username': 'alice',
        'password': 'secret',
        'employee_id': 'E123',
        'company': 'Acme Corp'
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert 'id' in data

    # check registration attempts persisted
    from backend.models import RegistrationAttempt
    with client.application.app_context():
        attempts = RegistrationAttempt.query.all()
        assert len(attempts) == 1
        assert attempts[0].success is True

    # invalid combination should be rejected and logged
    caplog.set_level(logging.WARNING)
    resp = client.post('/api/users/', json={
        'username': 'bob',
        'password': 'pw',
        'employee_id': 'UNKNOWN',
        'company': 'Acme Corp'
    })
    assert resp.status_code == 400
    assert 'Failed registration attempt' in caplog.text
    with client.application.app_context():
        attempts = RegistrationAttempt.query.order_by(RegistrationAttempt.id).all()
        assert len(attempts) == 2
        assert attempts[-1].success is False

    # attempt to list users without auth should fail
    resp = client.get('/api/users/')
    assert resp.status_code == 401

    # missing pair of employee/company should be rejected
    resp = client.post('/api/users/', json={
        'username': 'charlie',
        'password': 'pw',
        'employee_id': 'C1'
    })
    assert resp.status_code == 400
    resp = client.post('/api/users/', json={
        'username': 'delta',
        'password': 'pw',
        'company': 'Acme'
    })
    assert resp.status_code == 400

    # list users with basic auth
    resp = client.get('/api/users/', headers={'Authorization': 'Basic YWxpY2U6c2VjcmV0'})  # alice:secret
    assert resp.status_code == 200
    users = resp.get_json()
    assert any(u['username'] == 'alice' for u in users)

    # password reset flow
    caplog.set_level(logging.INFO)
    resp = client.post('/api/users/reset-request', json={'username': 'alice'})
    assert resp.status_code == 200
    # token should have been generated
    with client.application.app_context():
        user = User.query.filter_by(username='alice').first()
        assert user.reset_token is not None
        token = user.reset_token
    assert 'SEND EMAIL' in caplog.text

    resp = client.post(f'/api/users/reset/{token}', json={'password': 'newpass'})
    assert resp.status_code == 200
    # now login with new password (alice:newpass)
    auth_header2 = {'Authorization': 'Basic ' + b64encode(b"alice:newpass").decode()}
    resp = client.get('/api/users/', headers=auth_header2)
    assert resp.status_code == 200


def test_trip_records(client):
    # make sure registry contains the driver's ID
    from backend.models import EmployeeRegistry, db
    with client.application.app_context():
        db.session.add(EmployeeRegistry(company='Acme', employee_id='D1'))
        db.session.commit()

    # set up users
    resp = client.post('/api/users/', json={'username': 'driv', 'password': 'pw', 'employee_id': 'D1', 'company': 'Acme'})
    assert resp.status_code == 201
    resp = client.post('/api/users/', json={'username': 'sup', 'password': 'pw', 'role': 'supervisor'})
    assert resp.status_code == 201

    # try to create a trip before verification -> should be forbidden
    resp = client.post('/api/trips/', json={'start_odometer': 0.0, 'end_odometer': 10.0}, headers={'Authorization': 'Basic ZHJpdjpwdw=='})
    assert resp.status_code == 403

    # verify driver as supervisor
    # supervisor auth header c3VwOnB3
    resp = client.post('/api/users/verify/1', headers={'Authorization': 'Basic c3VwOnB3'})
    assert resp.status_code == 200
    assert resp.get_json()['verified'] is True

    # invalid odometer range should be rejected
    resp = client.post('/api/trips/', json={'start_odometer': 50.0, 'end_odometer': 10.0}, headers={'Authorization': 'Basic ZHJpdjpwdw=='})
    assert resp.status_code == 400

    # now driver creates a trip
    resp = client.post('/api/trips/', json={'start_odometer': 0.0, 'end_odometer': 10.0}, headers={'Authorization': 'Basic ZHJpdjpwdw=='})
    assert resp.status_code == 201
    trip_id = resp.get_json()['id']

    # overlapping odometer (start < last end) should be blocked
    resp = client.post('/api/trips/', json={'start_odometer': 5.0, 'end_odometer': 15.0}, headers={'Authorization': 'Basic ZHJpdjpwdw=='})
    assert resp.status_code == 400

    # driver lists own trips
    resp = client.get('/api/trips/', headers={'Authorization': 'Basic ZHJpdjpwdw=='})
    trips = resp.get_json()
    assert len(trips) == 1
    assert trips[0]['distance'] == 10.0

    # supervisor lists all trips with pagination
    resp = client.get('/api/trips/?page=1&per_page=1', headers={'Authorization': 'Basic c3VwOnB3'})
    data = resp.get_json()
    assert data['page'] == 1
    assert data['per_page'] == 1
    assert data['total'] >= 1
    assert len(data['trips']) == 1

    # create additional trip for pagination
    resp = client.post('/api/trips/', json={'start_odometer': 20.0, 'end_odometer': 30.0}, headers={'Authorization': 'Basic ZHJpdjpwdw=='})
    assert resp.status_code == 201
    # now request second page
    resp = client.get('/api/trips/?page=2&per_page=1', headers={'Authorization': 'Basic c3VwOnB3'})
    data = resp.get_json()
    assert data['page'] == 2
    assert len(data['trips']) == 1


# admin functionality tests

def test_admin_registry_and_stats(client):
    # create supervisor user
    resp = client.post('/api/users/', json={'username': 'admin', 'password': 'pw', 'role': 'supervisor'})
    assert resp.status_code == 201

    auth_header = {'Authorization': 'Basic YWRtaW46cHc='}  # admin:pw

    # initially no registry entries
    resp = client.get('/api/admin/registry', headers=auth_header)
    assert resp.status_code == 200
    assert resp.get_json() == []

    # add an entry
    resp = client.post('/api/admin/registry', json={'company': 'TestCo', 'employee_id': 'T1'}, headers=auth_header)
    assert resp.status_code == 201
    entry_id = resp.get_json()['id']

    # list should now include it
    resp = client.get('/api/admin/registry', headers=auth_header)
    regs = resp.get_json()
    assert any(r['id'] == entry_id for r in regs)

    # stats endpoint should work
    resp = client.get('/api/admin/stats', headers=auth_header)
    stats = resp.get_json()
    assert stats['users'] >= 1
    assert 'trips' in stats
    assert 'pending_verifications' in stats

    # before deleting registry entry, create a normal driver (uses entry)
    resp = client.post('/api/users/', json={'username': 'driv', 'password': 'pw', 'employee_id': 'T1', 'company': 'TestCo'})
    assert resp.status_code == 201

    # attempts endpoint should reflect past registrations (should at least include the driver we just added)
    resp = client.get('/api/admin/attempts', headers=auth_header)
    assert resp.status_code == 200
    attempts = resp.get_json()
    assert isinstance(attempts, list)
    assert any(a.get('employee_id') == 'T1' for a in attempts)

    # delete the entry
    resp = client.delete(f'/api/admin/registry/{entry_id}', headers=auth_header)
    assert resp.status_code == 200

    # non-supervisor cannot access admin routes
    resp = client.get('/api/admin/registry', headers={'Authorization': 'Basic ZHJpdjpwdw=='})
    assert resp.status_code == 403
