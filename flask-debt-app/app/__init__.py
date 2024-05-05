from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from instance.config import Config
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin


db = SQLAlchemy()  # Initialize SQLAlchemy here
login_manager = LoginManager()
login_manager.login_view = 'login'  # The route name for your login view

def create_app():
    """
    Factory function to create the Flask application.

    Returns:
        Flask: The Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'  # Specify the login view

    from app.routes import init_routes  # Ensure routes are imported after initialization
    init_routes(app)

    return app

@login_manager.user_loader
def load_user(user_id):
    """
    Callback function to reload the user object from the user ID stored in the session.

    Args:
        user_id (str): The user ID.

    Returns:
        UserMixin: The User object corresponding to the user ID.
    """
    from app.models import User  # Move this import inside the user_loader function
    return User.query.get(int(user_id))