# Indcric - Cricket Management App

This is a Django-based web application for managing cricket matches, teams, players, and payments.

## Prerequisites

*   [Python 3.10+](https://www.python.org/downloads/)
*   [Docker Desktop](https://www.docker.com/products/docker-desktop/)
*   [Git](https://git-scm.com/downloads/)

## First-Time Setup

These steps are only necessary the first time you set up the project.

### 1. Clone the Repository

```bash
git clone https://github.com/Bhanu-py/Indcric.git
cd Indcric
```

### 2. Create and Activate a Virtual Environment

It's recommended to use a virtual environment to manage project dependencies.

**On Windows:**

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On macOS and Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

### 4. Set Up the Database

This project uses Docker to run a PostgreSQL database.

1.  **Start Docker Desktop**: Make sure Docker Desktop is running on your machine.
2.  **Run the setup script**: This script will start the database container and configure it for the application.

    **On Windows:**

    ```powershell
    .\fix_postgres.ps1
    ```

    **On macOS and Linux:**

    ```bash
    ./fix_postgres.sh
    ```

### 5. Run Database Migrations

Apply the database migrations to create the necessary tables:

```bash
python manage.py migrate
```

### 6. Create a Superuser

Create a superuser account to access the Django admin interface:

```bash
python manage.py createsuperuser
```

Follow the prompts to set a username, email, and password.

### 7. Seed the Database (Optional)

If you have an `initial_users.csv` file, you can seed the database with initial user data by running the following command:

```bash
python manage.py seed_users
```

## Running the Development Server

Once you've completed the first-time setup, you can run the development server with these steps.

### 1. Activate the Virtual Environment

**On Windows:**

```bash
.\.venv\Scripts\Activate.ps1
```

**On macOS and Linux:**

```bash
source .venv/bin/activate
```

### 2. Start the Database

If your Docker container is not already running, start it with:

```bash
docker-compose up -d
```

### 3. Run the Server

Start the Django development server:

```bash
python manage.py runserver
```

You can now access the application in your web browser at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## Stopping the Application

To stop the development server, press `Ctrl+C` in the terminal where it's running.

To stop the database container, run:

```bash
docker-compose down
```
