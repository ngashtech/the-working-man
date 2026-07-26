@echo off
echo ============================================
echo The Working Man - Environment Reset
echo ============================================
echo.

echo 1. Checking Python versions...
py --list
echo.

echo 2. Deleting old virtual environment...
rmdir /s /q venv
echo.

echo 3. Available Python versions:
py -3.12 --version 2>nul && echo Python 3.12 found && goto :use312
py -3.11 --version 2>nul && echo Python 3.11 found && goto :use311
py -3.10 --version 2>nul && echo Python 3.10 found && goto :use310

echo ERROR: No compatible Python version found!
echo Please install Python 3.10, 3.11, or 3.12
echo Download: https://www.python.org/downloads/
pause
exit /b

:use312
echo Creating virtual environment with Python 3.12...
py -3.12 -m venv venv
goto :install

:use311
echo Creating virtual environment with Python 3.11...
py -3.11 -m venv venv
goto :install

:use310
echo Creating virtual environment with Python 3.10...
py -3.10 -m venv venv
goto :install

:install
echo.
echo 4. Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo 5. Checking Python version...
python --version

echo.
echo 6. Upgrading pip...
python -m pip install --upgrade pip

echo.
echo 7. Installing Flask...
pip install Flask==2.3.3

echo.
echo 8. Testing Flask import...
python -c "from flask import Flask; print('SUCCESS: Flask works!')"

echo.
echo 9. Installing remaining dependencies...
pip install Flask-SQLAlchemy==3.0.5
pip install Flask-Login==0.6.2
pip install Flask-Bcrypt==1.0.1
pip install python-dotenv==1.0.0
pip install Pillow==10.1.0
pip install Werkzeug==2.3.7
pip install SQLAlchemy==2.0.23
pip install bcrypt==4.1.1

echo.
echo ============================================
echo SETUP COMPLETE!
echo ============================================
echo.
echo To run the application:
echo   venv\Scripts\activate
echo   python app.py
echo.
pause