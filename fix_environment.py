# fix_environment.py
import os
import sys
import subprocess
import shutil

def fix_environment():
    """Fix the virtual environment and reinstall dependencies"""
    
    print("🔧 Fixing 'The Working Man' environment...")
    
    # 1. Remove existing virtual environment
    if os.path.exists('venv'):
        print("🗑️  Removing old virtual environment...")
        try:
            shutil.rmtree('venv')
        except Exception as e:
            print(f"⚠️  Could not remove venv: {e}")
            print("Please close any programs using the venv folder and try again.")
            return
    
    # 2. Remove __pycache__ directories
    print("🧹 Cleaning Python cache...")
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
            except:
                pass
    
    # 3. Check Python version
    python_version = sys.version_info
    print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.minor >= 13:
        print("⚠️  Python 3.13+ detected. This might cause issues with some packages.")
        print("   Consider using Python 3.11 or 3.12 for better compatibility.")
    
    # 4. Create new virtual environment
    print("📦 Creating new virtual environment...")
    try:
        subprocess.run([sys.executable, '-m', 'venv', 'venv', '--clear'], 
                      check=True, capture_output=True)
        print("✅ Virtual environment created successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return
    
    # 5. Determine pip path
    if sys.platform == 'win32':
        pip_path = os.path.join('venv', 'Scripts', 'pip.exe')
        python_path = os.path.join('venv', 'Scripts', 'python.exe')
    else:
        pip_path = os.path.join('venv', 'bin', 'pip')
        python_path = os.path.join('venv', 'bin', 'python')
    
    # 6. Upgrade pip
    print("⬆️  Upgrading pip...")
    try:
        subprocess.run([pip_path, 'install', '--upgrade', 'pip'], 
                      check=True, capture_output=True)
    except:
        print("⚠️  Could not upgrade pip, continuing...")
    
    # 7. Install dependencies one by one to identify problem packages
    dependencies = [
        'python-dotenv',
        'Flask==2.3.3',
        'Flask-SQLAlchemy==3.1.1',
        'Flask-Login==0.6.2',
        'Flask-WTF==1.2.1',
        'Flask-Bcrypt==1.0.1',
        'WTForms==3.1.1',
        'email-validator==2.1.0',
        'Pillow==10.1.0',
        'gunicorn==21.2.0',
    ]
    
    print("📥 Installing dependencies...")
    for package in dependencies:
        print(f"   Installing {package}...")
        try:
            subprocess.run([pip_path, 'install', package], 
                          check=True, capture_output=True, text=True)
            print(f"   ✅ {package}")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to install {package}")
            print(f"      Error: {e.stderr}")
    
    # 8. Update requirements.txt with working versions
    requirements_content = """# The Working Man - Dependencies (Stable Versions)
python-dotenv==1.0.0
Flask==2.3.3
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.2
Flask-WTF==1.2.1
Flask-Bcrypt==1.0.1
Flask-Mail==0.9.1
WTForms==3.1.1
email-validator==2.1.0
Pillow==10.1.0
gunicorn==21.2.0
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements_content)
    
    print("\n✅ Environment fix complete!")
    print("\n📋 To run the application:")
    if sys.platform == 'win32':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("   python app.py")

if __name__ == '__main__':
    fix_environment()