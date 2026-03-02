from datetime import datetime

from . import db


class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    start_odometer = db.Column(db.Float)
    end_odometer = db.Column(db.Float)
    notes = db.Column(db.Text)

    def duration(self):
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return None

    def distance(self):
        if self.end_odometer is not None and self.start_odometer is not None:
            return self.end_odometer - self.start_odometer
        return None
