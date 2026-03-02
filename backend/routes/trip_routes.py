from flask import Blueprint, request, jsonify
from backend.models import Trip
from backend.extensions import db
from .auth import auth


trip_bp = Blueprint('trips', __name__)


@trip_bp.route('/', methods=['GET'])
@auth.login_required
def list_trips():
    user = auth.current_user()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    query = Trip.query
    # supervisors see all, drivers only their own
    if user.role != 'supervisor':
        if not user.verified:
            return jsonify({'error': 'user not verified'}), 403
        query = query.filter_by(driver_id=user.id)

    # optional filtering
    driver_filter = request.args.get('driver_id')
    if driver_filter and user.role == 'supervisor':
        query = query.filter_by(driver_id=int(driver_filter))

    paginated = query.order_by(Trip.id).paginate(page=page, per_page=per_page, error_out=False)
    trips = paginated.items
    return jsonify({
        'page': page,
        'per_page': per_page,
        'total': paginated.total,
        'trips': [{
            'id': t.id,
            'driver_id': t.driver_id,
            'start_time': t.start_time.isoformat() if t.start_time else None,
            'end_time': t.end_time.isoformat() if t.end_time else None,
            'distance': t.distance(),
            'duration': str(t.duration()) if t.duration() else None,
        } for t in trips]
    })


@trip_bp.route('/', methods=['POST'])
@auth.login_required
def create_trip():
    user = auth.current_user()
    if user.role != 'supervisor' and not user.verified:
        return jsonify({'error': 'user not verified'}), 403
    data = request.get_json() or {}
    # drivers can only create their own trips
    data['driver_id'] = user.id

    # basic validation: odometer values must make sense
    start = data.get('start_odometer')
    end = data.get('end_odometer')
    if start is not None and end is not None:
        try:
            if float(end) < float(start):
                return jsonify({'error': 'end odometer must be >= start'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'invalid odometer values'}), 400

    # prevent overlapping trips by odometer for this driver
    if start is not None:
        last = Trip.query.filter_by(driver_id=user.id).order_by(Trip.id.desc()).first()
        if last and last.end_odometer is not None and start < last.end_odometer:
            return jsonify({'error': 'trip overlaps previous one'}), 400

    trip = Trip(**data)
    db.session.add(trip)
    db.session.commit()
    return jsonify({'id': trip.id}), 201
