@echo off
cd /d "C:\Users\KEMBOI\THE WORKING MAN"

echo Checking Python...
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo Python 3.12 not found! Trying 3.11...
    py -3.11 --version >nul 2>&1
    if errorlevel 1 (
        echo Python 3.12/3.11 not found!
        echo Please download Python 3.12 from https://www.python.org/downloads/
        pause
        exit /b
    ) else (
        set PYVER=3.11
    )
) else (
    set PYVER=3.12
)

echo Using Python %PYVER%

echo Deleting old venv...
rmdir /s /q venv 2>nul

echo Creating new venv...
py -%PYVER% -m venv venv

echo Activating...
call venv\Scripts\activate.bat

echo Installing packages...
pip install Flask==2.3.3 Flask-SQLAlchemy==3.0.5 Flask-Login==0.6.2 Flask-Bcrypt==1.0.1 python-dotenv==1.0.0 Pillow==10.1.0 Werkzeug==2.3.7 SQLAlchemy==2.0.23 bcrypt==4.1.1 --quiet

echo.
echo ============================================
echo   The Working Man Platform
echo   http://localhost:5000
echo ============================================
echo.
python app.py
pause
