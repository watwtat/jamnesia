#!/bin/bash

# Render deployment script for Jamnesia
# This script is executed during Render build process

set -e

echo "🚀 Starting Jamnesia deployment on Render..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

# Install gunicorn for production
echo "🔧 Installing gunicorn..."
pip install --no-cache-dir gunicorn

# Create data directory for SQLite (if not exists)
echo "🗃️ Setting up database directory..."
mkdir -p data

# Set proper permissions
chmod 755 data

echo "✅ Build completed successfully!"
echo "🌐 Starting application with gunicorn..."

# Start the application with gunicorn
exec gunicorn --config gunicorn.conf.py app:app