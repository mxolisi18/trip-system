from datetime import datetime

from backend.extensions import db


class RegistrationAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50))
    company = db.Column(db.String(100))
    success = db.Column(db.Boolean, nullable=False, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<RegistrationAttempt {self.employee_id}@{self.company} success={self.success}>"  
