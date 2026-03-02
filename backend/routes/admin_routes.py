from flask import Blueprint, request, jsonify
from backend.extensions import db
from backend.models import User, Trip, EmployeeRegistry, RegistrationAttempt
from .auth import auth

admin_bp = Blueprint('admin', __name__)


def supervisor_required(f):
    @auth.login_required
    def wrapper(*args, **kwargs):
        current = auth.current_user()
        if current.role != 'supervisor':
            return jsonify({'error': 'forbidden'}), 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


@admin_bp.route('/users', methods=['GET'])
@supervisor_required
def list_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])


@admin_bp.route('/registry', methods=['GET'])
@supervisor_required
def list_registry():
    regs = EmployeeRegistry.query.all()
    return jsonify(
        [{'id': r.id, 'company': r.company, 'employee_id': r.employee_id} for r in regs]
    )


@admin_bp.route('/registry', methods=['POST'])
@supervisor_required
def add_registry():
    data = request.get_json() or {}
    comp = data.get('company')
    eid = data.get('employee_id')
    if not comp or not eid:
        return jsonify({'error': 'company and employee_id required'}), 400
    entry = EmployeeRegistry(company=comp, employee_id=eid)
    db.session.add(entry)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'duplicate or db error'}), 400
    return jsonify({'id': entry.id}), 201


@admin_bp.route('/registry/<int:entry_id>', methods=['DELETE'])
@supervisor_required
def delete_registry(entry_id):
    entry = EmployeeRegistry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'status': 'deleted'})


@admin_bp.route('/attempts', methods=['GET'])
@supervisor_required
def list_attempts():
    # simple list all attempts (could add filters later)
    attempts = RegistrationAttempt.query.order_by(RegistrationAttempt.timestamp.desc()).all()
    return jsonify([
        {
            'id': a.id,
            'employee_id': a.employee_id,
            'company': a.company,
            'success': a.success,
            'timestamp': a.timestamp.isoformat() if a.timestamp else None,
        }
        for a in attempts
    ])

@admin_bp.route('/stats', methods=['GET'])
@supervisor_required
def stats():
    return jsonify({
        'users': User.query.count(),
        'trips': Trip.query.count(),
        'pending_verifications': User.query.filter_by(verified=False).count(),
    })
