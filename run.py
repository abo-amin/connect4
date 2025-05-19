import os
import sys

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from __init__ import create_app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        from models import db
        db.create_all()
    app.run(debug=True)
