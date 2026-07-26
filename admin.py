# create_admin.py
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app import app, db
from database.models import User

def create_admin():
    with app.app_context():
        if User.query.filter_by(email='admin@workingman.com').first():
            print("Admin already exists.")
            return
        admin = User(email='admin@workingman.com', phone='+254700000000', full_name='System Admin', role='admin', is_verified=True, is_active=True)
        admin.set_password('Admin@123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin created: admin@workingman.com / Admin@123")

if __name__ == '__main__':
    create_admin()