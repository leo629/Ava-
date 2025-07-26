#!/usr/bin/env bash

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Optional: collect static files if needed
python manage.py collectstatic --noinput
