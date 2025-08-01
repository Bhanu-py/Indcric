# PostgreSQL Alpine setup script for Indcric

Write-Host "Fixing PostgreSQL configuration..." -ForegroundColor Green

# Stop any running PostgreSQL containers
docker-compose down -v

# Remove any PostgreSQL data
docker volume rm indcric_postgres_data -f

# Pull the latest PostgreSQL image
docker pull postgres:15-alpine

# Start a fresh container
docker-compose up -d db

# Wait for PostgreSQL to initialize
Write-Host "Waiting for PostgreSQL to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# For Alpine PostgreSQL, the default user is the POSTGRES_USER (indcric_user), not postgres
Write-Host "Setting up database schema and permissions..." -ForegroundColor Green
docker exec indcric-db-1 psql -U indcric_user -d indcric_db -c "CREATE SCHEMA IF NOT EXISTS django_schema;"
docker exec indcric-db-1 psql -U indcric_user -d indcric_db -c "ALTER ROLE indcric_user SET search_path TO django_schema,public;"

Write-Host "PostgreSQL setup complete!" -ForegroundColor Green
Write-Host "Now run: python manage.py setup_dev" -ForegroundColor Cyan
