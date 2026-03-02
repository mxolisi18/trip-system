from flask_httpauth import HTTPBasicAuth
from backend.models import User

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    if not username or not password:
        return False
    user = User.query.filter_by(username=username).first()
    if not user:
        return False
    if user.check_password(password):
        return user
    return False


@auth.error_handler
def unauthorized():
    return ("Unauthorized", 401)
