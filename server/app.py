import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from extensions import bcrypt, jwt, migrate
from models import db
from routes import api

load_dotenv()


def create_app(test_config=None):
    """Create and configure the Flask application.

    Tests pass their own config (an in-memory database and a test
    secret key) so they never touch productivity.db.
    """
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///productivity.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)

    if test_config:
        app.config.update(test_config)

    if not app.config["JWT_SECRET_KEY"]:
        raise RuntimeError(
            "JWT_SECRET_KEY is not set. Add it to your .env file."
        )

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Allow the separate frontend to call this API directly.
    # During development the React proxy (package.json) already forwards
    # requests to Flask, so this only matters if you call port 5555 directly.
    CORS(app, origins=["http://localhost:4000"])

    app.register_blueprint(api)

    return app


# Kept at module level so seed.py and `flask db` commands keep working.
app = create_app()


if __name__ == "__main__":
    app.run(port=5555, debug=os.environ.get("FLASK_DEBUG") == "1")