from . import db


class EmployeeRegistry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100), nullable=False)
    employee_id = db.Column(db.String(50), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('company', 'employee_id', name='uq_company_employee'),
    )

    def __repr__(self):
        return f"<EmployeeRegistry {self.company}:{self.employee_id}>"
