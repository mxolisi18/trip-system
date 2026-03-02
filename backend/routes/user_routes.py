from flask import Blueprint, request, jsonify
from backend.models import User
from backend.extensions import db
from .auth import auth


user_bp = Blueprint('users', __name__)


@user_bp.route('/', methods=['GET'])
@auth.login_required
def list_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])


@user_bp.route('/verify/<int:user_id>', methods=['POST'])
@auth.login_required
def verify_user(user_id):
    current = auth.current_user()
    # only supervisors (admins) may verify
    if current.role != 'supervisor':
        return jsonify({'error': 'forbidden'}), 403
    user = User.query.get_or_404(user_id)
    user.verified = True
    db.session.commit()
    return jsonify({'id': user.id, 'verified': user.verified})


@user_bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    # expect fields like username/email, password, employee_id, company, etc.
    employee_id = data.get('employee_id')
    company = data.get('company')
    # require both ID and company together, otherwise treat as missing
    if (employee_id and not company) or (company and not employee_id):
        return jsonify({'error': 'employee_id and company must be provided together'}), 400

    # only validate when both fields are provided; supervisors or other roles
    # may register without being in the registry table
    valid = True
    if employee_id and company:
        from backend.models import EmployeeRegistry
        valid = EmployeeRegistry.query.filter_by(company=company, employee_id=employee_id).first()
        if not valid:
            # log attempt for auditing
            from flask import current_app
            current_app.logger.warning(f"Failed registration attempt: {employee_id}@{company}")
            return jsonify({'error': 'invalid employee ID or company'}), 400

    password = data.pop('password', None)
    # new users start unverified; verification process based on id/company later
    data['verified'] = False
    user = User(**data)
    if password:
        user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'id': user.id}), 201
