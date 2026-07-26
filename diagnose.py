# diagnose.py - Quick diagnostic tool for The Working Man
import sys
import os

def run_diagnostics():
    """Run comprehensive diagnostics"""
    print("=" * 60)
    print("🔍 The Working Man - Diagnostic Tool")
    print("=" * 60)
    
    # 1. Check Python Version
    print("\n1. PYTHON VERSION")
    print(f"   Python: {sys.version}")
    print(f"   Version Info: {sys.version_info}")
    if sys.version_info.minor >= 13:
        print("   ⚠️  Python 3.13+ may have compatibility issues")
        print("   Consider using Python 3.11 or 3.12")
    
    # 2. Check Current Directory
    print("\n2. PROJECT DIRECTORY")
    current_dir = os.getcwd()
    print(f"   Current: {current_dir}")
    print(f"   Contents: {os.listdir('.')}")
    
    # 3. Check Virtual Environment
    print("\n3. VIRTUAL ENVIRONMENT")
    venv_path = os.path.join(current_dir, 'venv')
    if os.path.exists(venv_path):
        print("   ✅ Virtual environment found")
        if sys.platform == 'win32':
            python_path = os.path.join(venv_path, 'Scripts', 'python.exe')
        else:
            python_path = os.path.join(venv_path, 'bin', 'python')
        print(f"   Python path: {python_path}")
        print(f"   Exists: {os.path.exists(python_path)}")
    else:
        print("   ❌ Virtual environment NOT found")
        print("   Run: python -m venv venv")
    
    # 4. Check Required Files
    print("\n4. REQUIRED FILES")
    required_files = [
        'app.py',
        'config.py',
        '.env',
        'requirements.txt',
        os.path.join('database', 'models.py'),
        os.path.join('database', '__init__.py'),
        os.path.join('utils', 'helpers.py'),
        os.path.join('utils', '__init__.py'),
    ]
    
    for file in required_files:
        exists = os.path.exists(file)
        status = "✅" if exists else "❌"
        print(f"   {status} {file}")
    
    # 5. Check Template Files
    print("\n5. TEMPLATE FILES")
    template_files = [
        os.path.join('templates', 'base.html'),
        os.path.join('templates', 'index.html'),
        os.path.join('templates', 'auth', 'login.html'),
        os.path.join('templates', 'worker', 'register.html'),
        os.path.join('templates', 'worker', 'dashboard.html'),
        os.path.join('templates', 'employer', 'register.html'),
        os.path.join('templates', 'employer', 'dashboard.html'),
    ]
    
    for file in template_files:
        exists = os.path.exists(file)
        status = "✅" if exists else "❌"
        print(f"   {status} {file}")
    
    # 6. Test Imports
    print("\n6. TESTING IMPORTS")
    
    # Test Flask
    try:
        import flask
        print(f"   ✅ Flask {flask.__version__}")
    except ImportError:
        print("   ❌ Flask not installed")
        print("   Run: pip install Flask")
    
    # Test Flask-SQLAlchemy
    try:
        import flask_sqlalchemy
        print(f"   ✅ Flask-SQLAlchemy")
    except ImportError:
        print("   ❌ Flask-SQLAlchemy not installed")
        print("   Run: pip install Flask-SQLAlchemy")
    
    # Test Flask-Login
    try:
        import flask_login
        print(f"   ✅ Flask-Login")
    except ImportError:
        print("   ❌ Flask-Login not installed")
        print("   Run: pip install Flask-Login")
    
    # Test Flask-Bcrypt
    try:
        import flask_bcrypt
        print(f"   ✅ Flask-Bcrypt")
    except ImportError:
        print("   ❌ Flask-Bcrypt not installed")
        print("   Run: pip install Flask-Bcrypt")
    
    # Test python-dotenv
    try:
        import dotenv
        print(f"   ✅ python-dotenv")
    except ImportError:
        print("   ❌ python-dotenv not installed")
        print("   Run: pip install python-dotenv")
    
    # Test Custom Modules
    try:
        from config import config_by_name
        print(f"   ✅ config.py")
    except ImportError as e:
        print(f"   ❌ config.py import failed: {e}")
    
    try:
        from database.models import db, User
        print(f"   ✅ database.models")
    except ImportError as e:
        print(f"   ❌ database.models import failed: {e}")
    
    # 7. Check .env file
    print("\n7. ENVIRONMENT CONFIGURATION")
    if os.path.exists('.env'):
        print("   ✅ .env file found")
        with open('.env', 'r') as f:
            content = f.read()
            if 'SECRET_KEY' in content:
                print("   ✅ SECRET_KEY configured")
            else:
                print("   ❌ SECRET_KEY missing")
            if 'DATABASE_URL' in content:
                print("   ✅ DATABASE_URL configured")
            else:
                print("   ❌ DATABASE_URL missing")
    else:
        print("   ❌ .env file NOT found")
    
    # 8. Test Database Creation
    print("\n8. DATABASE TEST")
    try:
        from flask import Flask
        from config import DevelopmentConfig
        
        app = Flask(__name__)
        app.config.from_object(DevelopmentConfig)
        
        from database.models import db
        db.init_app(app)
        
        with app.app_context():
            db.create_all()
            print("   ✅ Database tables created successfully")
            # List tables
            tables = db.engine.table_names()
            print(f"   Tables: {tables}")
    except Exception as e:
        print(f"   ❌ Database error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Diagnostic complete!")
    print("\n📋 If there are issues, follow these steps:")
    print("1. Install Python 3.11 or 3.12 if using 3.13+")
    print("2. Delete the 'venv' folder")
    print("3. Create new virtual environment:")
    print("   python -m venv venv")
    print("4. Activate it:")
    print("   Windows: venv\\Scripts\\activate")
    print("   Mac/Linux: source venv/bin/activate")
    print("5. Install dependencies:")
    print("   pip install -r requirements.txt")
    print("6. Run the app:")
    print("   python app.py")

if __name__ == '__main__':
    run_diagnostics()   