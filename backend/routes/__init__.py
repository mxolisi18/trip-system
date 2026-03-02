def register_routes(app):
    from .trip_routes import trip_bp
    from .user_routes import user_bp
    from .admin_routes import admin_bp

    app.register_blueprint(trip_bp, url_prefix="/api/trips")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
