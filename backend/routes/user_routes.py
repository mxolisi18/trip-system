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
    # notify user of verification
    from backend.mailer import send_email
    send_email(user.username, "Account Verified", "Your Trip Sheet account has been verified.")
    return jsonify({'id': user.id, 'verified': user.verified})


@user_bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    # expect fields like username/email, password, employee_id, company, etc.
    employee_id = data.get('employee_id')
    company = data.get('company')

    from backend.models import RegistrationAttempt
    # default attempt record (not yet persisted)
    attempt = RegistrationAttempt(employee_id=employee_id, company=company, success=False)

    # require both ID and company together, otherwise treat as missing
    if (employee_id and not company) or (company and not employee_id):
        db.session.add(attempt)
        db.session.commit()
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
            db.session.add(attempt)
            db.session.commit()
            return jsonify({'error': 'invalid employee ID or company'}), 400

    password = data.pop('password', None)
    # new users start unverified; verification process based on id/company later
    data['verified'] = False
    user = User(**data)
    if password:
        user.set_password(password)

    # mark the earlier attempt as successful before persisting
    attempt.success = bool(valid)
    db.session.add(attempt)

    db.session.add(user)
    db.session.commit()

    # send notification email (stubbed)
    from backend.mailer import send_email
    send_email(user.username, "Welcome to Trip Sheet System", "Your account has been created and is pending verification.")

    return jsonify({'id': user.id}), 201


@user_bp.route('/reset-request', methods=['POST'])
def reset_request():
    data = request.get_json() or {}
    username = data.get('username')
    if not username:
        return jsonify({'error': 'username required'}), 400
    user = User.query.filter_by(username=username).first()
    if not user:
        # do not reveal user existence
        return jsonify({'status': 'ok'}), 200
    import uuid
    from datetime import datetime
    token = uuid.uuid4().hex
    user.reset_token = token
    user.reset_sent_at = datetime.utcnow()
    db.session.commit()
    from backend.mailer import send_email
    send_email(user.username, 'Password reset', f'Use this token to reset: {token}')
    return jsonify({'status': 'ok'}), 200


@user_bp.route('/reset/<token>', methods=['POST'])
def reset_password(token):
    data = request.get_json() or {}
    newpass = data.get('password')
    if not newpass:
        return jsonify({'error': 'password required'}), 400
    user = User.query.filter_by(reset_token=token).first()
    if not user:
        return jsonify({'error': 'invalid token'}), 400
    # optionally check expiry here
    user.set_password(newpass)
    user.reset_token = None
    user.reset_sent_at = None
    db.session.commit()
    from backend.mailer import send_email
    send_email(user.username, 'Password changed', 'Your password has been reset.')
    return jsonify({'status': 'ok'}), 200
