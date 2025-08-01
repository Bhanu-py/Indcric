import os
import time
import subprocess
from django.core.management.base import BaseCommand
from django.db import connections, OperationalError
from django.db.migrations.executor import MigrationExecutor

class Command(BaseCommand):
    help = 'Sets up the development environment'

    def handle(self, *args, **options):
        # Check if we're using remote or local database
        using_remote = all([
            os.getenv("hostname"),
            os.getenv("databasename"),
            os.getenv("username"),
            os.getenv("password")
        ])
        
        self.stdout.write(f"Using {'remote' if using_remote else 'local'} database")
        
        # If using local database, ensure Docker is running
        if not using_remote:
            self.setup_local_database()
            # Wait for database to be ready
            self.wait_for_database(max_attempts=15, delay=5)  # Increased wait time
        
        # Check database connection
        try:
            self.check_connection()
            self.stdout.write(self.style.SUCCESS("✓ Database connection successful"))
        except OperationalError as e:
            if using_remote:
                self.stdout.write(self.style.ERROR(f"× Cannot connect to remote database: {str(e)}"))
                return
            else:
                self.stdout.write(self.style.ERROR(f"× Cannot connect to local database: {str(e)}"))
                self.stdout.write("Database troubleshooting steps:")
                self.stdout.write("1. Run 'docker-compose down -v' to remove all containers and volumes")
                self.stdout.write("2. Run 'docker ps' to ensure no PostgreSQL containers are running")
                self.stdout.write("3. Run 'setup_dev' again")
                return
        
        # For remote database, validate schema
        if using_remote:
            if not self.validate_schema():
                self.stdout.write(self.style.ERROR("× Remote database schema is not up-to-date"))
                self.stdout.write("Please run migrations on the remote database or check schema configuration")
                return
            self.stdout.write(self.style.SUCCESS("✓ Remote database schema is valid"))
        else:
            # For local database, create schema and apply migrations
            self.create_schema()
            self.apply_migrations()
        
        # Seed initial data
        self.seed_data()
        
        self.stdout.write(self.style.SUCCESS("✓ Development environment setup complete!"))
    
    def check_connection(self):
        """Test database connection"""
        conn = connections['default']
        conn.cursor()
    
    def setup_local_database(self):
        """Start the local Docker database if not running"""
        self.stdout.write("Starting local database with Docker...")
        try:
            # First, check if any PostgreSQL containers are running
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", "ancestor=postgres:15-alpine"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if "indcric-db" in result.stdout or "postgres" in result.stdout:
                self.stdout.write("Found existing database container, removing it first...")
                # Stop and remove existing container
                subprocess.run(["docker-compose", "down", "-v"], check=False)
            
            # Create and start a fresh container with a simpler configuration
            self.stdout.write("Creating and starting a fresh database container...")
            subprocess.run(["docker-compose", "up", "-d", "db"], check=True)
                
            self.stdout.write(self.style.SUCCESS("✓ Local database started"))
            self.stdout.write("Waiting for PostgreSQL to initialize (this may take a moment)...")
            time.sleep(10)  # Give PostgreSQL more time to initialize
            
            # Get actual container name to make commands more robust
            result = subprocess.run(
                ["docker", "ps", "--filter", "ancestor=postgres:15-alpine", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=False
            )
            container_name = result.stdout.strip() or "indcric-db-1"
            self.stdout.write(f"Using container name: {container_name}")
            
            # Create schema directly through Docker with the correct user
            self.stdout.write("Configuring database with direct SQL commands...")
            try:
                # In PostgreSQL Alpine, indcric_user is the default superuser
                subprocess.run([
                    "docker", "exec", container_name, 
                    "psql", "-U", "indcric_user", "-d", "indcric_db", 
                    "-c", "CREATE SCHEMA IF NOT EXISTS django_schema;"
                ], check=True)
                
                # Set up search path for our user
                subprocess.run([
                    "docker", "exec", container_name, 
                    "psql", "-U", "indcric_user", "-d", "indcric_db", 
                    "-c", "ALTER ROLE indcric_user SET search_path TO django_schema,public;"
                ], check=True)
                
                self.stdout.write(self.style.SUCCESS("✓ Schema and permissions configured"))
            except subprocess.CalledProcessError as e:
                self.stdout.write(self.style.ERROR(f"× Failed to configure database: {str(e)}"))
                self.stdout.write("Will attempt to continue anyway...")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"× Failed to start database: {str(e)}"))
            self.stdout.write("Make sure Docker is running and docker-compose is installed")
    
    def wait_for_database(self, max_attempts=15, delay=5):
        """Wait for database to be ready for connections"""
        self.stdout.write("Waiting for database to be ready...")
        attempts = 0
        
        # Get actual container name for logs
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "ancestor=postgres:15-alpine", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=False
            )
            container_name = result.stdout.strip() or "indcric-db-1"
        except:
            container_name = "indcric-db-1"  # Default fallback
            
        while attempts < max_attempts:
            # Try to connect using psycopg2 directly for better error diagnostics
            try:
                import psycopg2
                self.stdout.write("Attempting direct connection to PostgreSQL...")
                conn = psycopg2.connect(
                    dbname="indcric_db",
                    user="indcric_user",
                    password="indcric_password",
                    host="localhost",
                    port="5432"
                )
                conn.close()
                self.stdout.write(self.style.SUCCESS("✓ Direct connection successful"))
                
                # Now try Django's connection mechanism
                self.check_connection()
                self.stdout.write(self.style.SUCCESS("✓ Django database connection is ready"))
                return True
                
            except psycopg2.OperationalError as e:
                attempts += 1
                self.stdout.write(f"Direct PostgreSQL connection failed: {str(e)}")
                
                # Get container logs for debugging
                if attempts % 3 == 0:  # Only check logs every few attempts
                    self.stdout.write("Checking PostgreSQL container logs...")
                    try:
                        logs = subprocess.run(
                            ["docker", "logs", "--tail", "20", container_name],
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        self.stdout.write(f"Recent logs:\n{logs.stdout}")
                    except Exception:
                        pass
                
                if attempts < max_attempts:
                    self.stdout.write(f"Waiting {delay} seconds... (attempt {attempts}/{max_attempts})")
                    time.sleep(delay)
            
            except OperationalError as e:
                attempts += 1
                if attempts < max_attempts:
                    self.stdout.write(f"Django connection not ready yet: {str(e)}")
                    self.stdout.write(f"Waiting {delay} seconds... (attempt {attempts}/{max_attempts})")
                    time.sleep(delay)
        
        self.stdout.write(self.style.WARNING("× Maximum attempts reached waiting for database"))
        return False
    
    def validate_schema(self):
        """Check if the remote schema has all migrations applied"""
        executor = MigrationExecutor(connections['default'])
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        return len(plan) == 0  # No migrations pending
    
    def create_schema(self):
        """Create the django_schema if it doesn't exist"""
        self.stdout.write("Creating database schema...")
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute("CREATE SCHEMA IF NOT EXISTS django_schema;")
            self.stdout.write(self.style.SUCCESS("✓ Schema created"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"× Failed to create schema: {str(e)}"))
    
    def apply_migrations(self):
        """Apply all migrations"""
        self.stdout.write("Applying migrations...")
        try:
            subprocess.run(["python", "manage.py", "migrate"], check=True)
            self.stdout.write(self.style.SUCCESS("✓ Migrations applied"))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"× Failed to apply migrations: {str(e)}"))
    
    def seed_data(self):
        """Seed initial data with existing management commands"""
        self.stdout.write("Loading initial data...")
        commands = [
            # Add your existing data loading commands here
            # For example:
            # "load_initial_data",
            # "create_wallets",
        ]
        
        for command in commands:
            self.stdout.write(f"Running {command}...")
            try:
                subprocess.run(["python", "manage.py", command], check=True)
            except subprocess.CalledProcessError as e:
                self.stdout.write(self.style.ERROR(f"× Failed to run {command}: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS("✓ Initial data loaded"))
