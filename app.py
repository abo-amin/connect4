from __init__ import create_app

# Create the Flask application instance
app = create_app()

# Initialize database if run directly
if __name__ == '__main__':
    with app.app_context():
        from models import db
        db.create_all()
    app.run(debug=True)