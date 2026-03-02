from flask import Blueprint, request, jsonify
from backend.models import Trip
from backend.extensions import db
from .auth import auth


trip_bp = Blueprint('trips', __name__)


@trip_bp.route('/', methods=['GET'])
@auth.login_required
def list_trips():
    user = auth.current_user()
    # supervisors see all, drivers only their own
    if user.role == 'supervisor':
        trips = Trip.query.all()
    else:
        if not user.verified:
            return jsonify({'error': 'user not verified'}), 403
        trips = Trip.query.filter_by(driver_id=user.id).all()
    return jsonify([{
        'id': t.id,
        'driver_id': t.driver_id,
        'start_time': t.start_time.isoformat() if t.start_time else None,
        'end_time': t.end_time.isoformat() if t.end_time else None,
        'distance': t.distance(),
        'duration': str(t.duration()) if t.duration() else None
    } for t in trips])


@trip_bp.route('/', methods=['POST'])
@auth.login_required
def create_trip():
    user = auth.current_user()
    if user.role != 'supervisor' and not user.verified:
        return jsonify({'error': 'user not verified'}), 403
    data = request.get_json() or {}
    # drivers can only create their own trips
    data['driver_id'] = user.id
    trip = Trip(**data)
    db.session.add(trip)
    db.session.commit()
    return jsonify({'id': trip.id}), 201
