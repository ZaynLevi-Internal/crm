#!/bin/bash

echo "=== CA CRM Setup Script ==="

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run the application
echo "Starting application..."
echo "Access at: http://localhost:5000"
echo "Default login: admin / admin123"
python app.py
