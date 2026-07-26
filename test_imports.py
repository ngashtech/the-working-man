# test_imports.py
print("Testing imports for The Working Man...")

try:
    print("1. Testing Flask...")
    from flask import Flask
    print("   ✅ Flask imported successfully")
except Exception as e:
    print(f"   ❌ Flask import failed: {e}")

try:
    print("2. Testing Flask-SQLAlchemy...")
    from flask_sqlalchemy import SQLAlchemy
    print("   ✅ Flask-SQLAlchemy imported successfully")
except Exception as e:
    print(f"   ❌ Flask-SQLAlchemy import failed: {e}")

try:
    print("3. Testing Flask-Login...")
    from flask_login import LoginManager
    print("   ✅ Flask-Login imported successfully")
except Exception as e:
    print(f"   ❌ Flask-Login import failed: {e}")

try:
    print("4. Testing Flask-Bcrypt...")
    from flask_bcrypt import Bcrypt
    print("   ✅ Flask-Bcrypt imported successfully")
except Exception as e:
    print(f"   ❌ Flask-Bcrypt import failed: {e}")

try:
    print("5. Testing WTForms...")
    from wtforms import Form
    print("   ✅ WTForms imported successfully")
except Exception as e:
    print(f"   ❌ WTForms import failed: {e}")

try:
    print("6. Testing PIL (Pillow)...")
    from PIL import Image
    print("   ✅ Pillow imported successfully")
except Exception as e:
    print(f"   ❌ Pillow import failed: {e}")

print("\n✅ Import test complete!")