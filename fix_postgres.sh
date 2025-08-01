#!/bin/bash
# This script fixes common PostgreSQL authentication issues

echo "Fixing PostgreSQL configuration..."

# Stop any running PostgreSQL containers
docker-compose down -v

# Remove any PostgreSQL data
docker volume rm indcric_postgres_data

# Pull the latest PostgreSQL image
docker pull postgres:15-alpine

# Start a fresh container
docker-compose up -d db

# Wait for PostgreSQL to initialize
echo "Waiting for PostgreSQL to initialize..."
sleep 10

# Create schema and configure permissions
echo "Setting up database schema and permissions..."
docker exec indcric-db-1 psql -U postgres -d indcric_db -c "CREATE SCHEMA IF NOT EXISTS django_schema;"
docker exec indcric-db-1 psql -U postgres -d indcric_db -c "GRANT ALL PRIVILEGES ON SCHEMA django_schema TO indcric_user;"
docker exec indcric-db-1 psql -U postgres -d indcric_db -c "ALTER ROLE indcric_user SET search_path TO django_schema,public;"

echo "PostgreSQL setup complete!"
echo "Now run: python manage.py setup_dev"
