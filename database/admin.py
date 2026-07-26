# create_admin.py
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from database.models import User

def create_admin():
    """Create an admin user"""
    with app.app_context():
        # Check if admin already exists
        existing = User.query.filter_by(email='admin@workingman.com').first()
        if existing:
            print("Admin user already exists.")
            return
        
        # Create admin user
        admin = User(
            email='admin@workingman.com',
            phone='+254700000000',
            full_name='System Admin',
            role='admin',
            is_verified=True,
            is_active=True
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        print("=" * 50)
        print("✅ Admin user created successfully!")
        print("=" * 50)
        print("Email: admin@workingman.com")
        print("Password: admin123")
        print("=" * 50)
        print("⚠️  CHANGE THIS PASSWORD IMMEDIATELY IN PRODUCTION!")
        print("=" * 50)

if __name__ == '__main__':
    create_admin()
    