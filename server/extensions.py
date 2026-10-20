from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

# Created here without an app. app.py connects them with init_app().
# Keeping them in their own file lets routes.py import them
# without importing app.py (which would be a circular import).
bcrypt = Bcrypt()
jwt = JWTManager()
migrate = Migrate()