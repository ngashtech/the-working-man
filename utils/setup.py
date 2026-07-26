# setup.py
import os
import sys
import subprocess
import shutil

def setup_environment():
    """Set up The Working Man project environment"""
    print("=" * 60)
    print("🔧 The Working Man - Environment Setup")
    print("=" * 60)
    
    # Create directories
    directories = [
        'database',
        'templates/worker',
        'templates/employer',
        'templates/auth',
        'templates/errors',
        'templates/job',
        'templates/search',
        'templates/review',
        'static/css',
        'static/js',
        'static/uploads/documents',
        'static/uploads/selfies',
        'utils'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        if directory in ['database', 'utils']:
            init_file = os.path.join(directory, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write(f"# {directory} package\n")
    
    # Create .env file
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("""FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=change-this-in-production-key-2024
DATABASE_URL=sqlite:///workingman.db
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216
""")
    
    print("\n✅ Setup complete!")
    print("\n📋 Next steps:")
    if sys.platform == 'win32':
        print("   python -m venv venv")
        print("   venv\\Scripts\\activate")
    else:
        print("   python3 -m venv venv")
        print("   source venv/bin/activate")
    print("   pip install -r requirements.txt")
    print("   python app.py")
    print("\n🌐 Visit http://localhost:5000")

if __name__ == '__main__':
    setup_environment()