from flask import Flask

# import using package path so module resolution works when running as a module
from backend.routes import register_routes
from backend.extensions import db, migrate, bcrypt


def create_app(config_object=None):
    # serve frontend directory as static files at application root
    app = Flask(__name__, static_folder="../frontend", static_url_path="")
    # allow tests or callers to override configuration
    if config_object is not None:
        app.config.from_object(config_object)
    else:
        # backend.config is where configuration lives when running as package
        app.config.from_object("backend.config.Config")

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    # import models so Alembic can detect them
    with app.app_context():
        # ensure models imported via package path to avoid duplicate metadata
        from backend.models import User, Trip  # noqa: F401

    register_routes(app)

    # simple root route serves login page by default
    @app.route("/")
    def index():
        return app.send_static_file("login.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
