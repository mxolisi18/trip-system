from . import db
from flask import current_app


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="driver")
    employee_id = db.Column(db.String(50))
    company = db.Column(db.String(100))
    verified = db.Column(db.Boolean, default=False)

    trips = db.relationship('Trip', backref='driver', lazy=True)

    def set_password(self, password: str):
        # import here to avoid circular imports
        from extensions import bcrypt
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        from extensions import bcrypt
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'employee_id': self.employee_id,
            'company': self.company,
            'verified': self.verified,
        }
