from backend.models import User, Trip, db


import logging

def test_user_creation_and_auth(client, caplog):
    # seed registry entries
    from backend.models import EmployeeRegistry, db
    with client.application.app_context():
        db.session.add(EmployeeRegistry(company='Acme Corp', employee_id='E123'))
        db.session.commit()

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

    # now driver creates a trip
    resp = client.post('/api/trips/', json={'start_odometer': 0.0, 'end_odometer': 10.0}, headers={'Authorization': 'Basic ZHJpdjpwdw=='})
    assert resp.status_code == 201
    trip_id = resp.get_json()['id']

    # driver lists own trips
    resp = client.get('/api/trips/', headers={'Authorization': 'Basic ZHJpdjpwdw=='})
    trips = resp.get_json()
    assert len(trips) == 1
    assert trips[0]['distance'] == 10.0

    # supervisor lists all trips
    resp = client.get('/api/trips/', headers={'Authorization': 'Basic c3VwOnB3'})
    trips = resp.get_json()
    assert len(trips) == 1
