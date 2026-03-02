from app import create_app, db
from flask_migrate import Migrate
from flask.cli import FlaskGroup

app = create_app()
migrate = Migrate(app, db)

def create_cli():
    cli = FlaskGroup(create_app=create_app)
    return cli

cli = create_cli()

if __name__ == '__main__':
    cli()
