from flask_app import app, db

# Use the app context
with app.app_context():
    # Create all database tables
    db.create_all()