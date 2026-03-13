#!/bin/bash
# Nepal Voting System - Complete Setup Script
# Run this script to initialize the voting system with all features

echo "================================================"
echo "Nepal Election Voting System - Setup Script"
echo "================================================"
echo ""

# Check if manage.py exists
if [ ! -f "manage.py" ]; then
    echo "ERROR: manage.py not found. Please run this script from the project root directory."
    exit 1
fi

echo "Step 1: Applying migrations..."
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "ERROR: Migration failed. Please check your database configuration."
    exit 1
fi
echo "✓ Migrations applied successfully"
echo ""

echo "Step 2: Loading constituencies from CSV..."
python manage.py seed_constituencies_csv --csv data/nepal_constituencies_165.csv --election "Nepal Parliamentary Election 2024"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to load constituencies. Check the CSV file path."
    exit 1
fi
echo "✓ Constituencies loaded successfully"
echo ""

echo "Step 3: Collecting static files..."
python manage.py collectstatic --noinput
echo "✓ Static files collected"
echo ""

echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Create a superuser: python manage.py createsuperuser"
echo "2. Start the server: python manage.py runserver"
echo "3. Login to admin panel: http://localhost:8000/admin/"
echo "4. Create parties and candidates in the admin panel"
echo "5. Users can register at: http://localhost:8000/web/register/"
echo ""
echo "For detailed instructions, see SETUP_GUIDE.md"
echo ""
