#!/usr/bin/env bash
set -o errexit

# Go to backend folder
cd backend

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migratee
