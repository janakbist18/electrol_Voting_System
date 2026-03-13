@echo off
REM Nepal Voting System - Complete Setup Script (Windows)
REM Run this script to initialize the voting system with all features

echo.
echo ================================================
echo Nepal Election Voting System - Setup Script
echo ================================================
echo.

REM Check if manage.py exists
if not exist "manage.py" (
    echo ERROR: manage.py not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

echo Step 1: Applying migrations...
python manage.py migrate
if %errorlevel% neq 0 (
    echo ERROR: Migration failed. Please check your database configuration.
    pause
    exit /b 1
)
echo [OK] Migrations applied successfully
echo.

echo Step 2: Loading constituencies from CSV...
python manage.py seed_constituencies_csv --csv data/nepal_constituencies_165.csv --election "Nepal Parliamentary Election 2024"
if %errorlevel% neq 0 (
    echo ERROR: Failed to load constituencies. Check the CSV file path.
    pause
    exit /b 1
)
echo [OK] Constituencies loaded successfully
echo.

echo Step 3: Collecting static files...
python manage.py collectstatic --noinput
if %errorlevel% neq 0 (
    echo WARNING: Static files collection encountered an issue (non-critical)
)
echo [OK] Static files collected
echo.

echo ================================================
echo Setup Complete!
echo ================================================
echo.
echo Next steps:
echo 1. Create a superuser: python manage.py createsuperuser
echo 2. Start the server: python manage.py runserver
echo 3. Login to admin panel: http://localhost:8000/admin/
echo 4. Create parties and candidates in the admin panel
echo 5. Users can register at: http://localhost:8000/web/register/
echo.
echo For detailed instructions, see SETUP_GUIDE.md
echo.
pause
