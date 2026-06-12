# Indcric - Cricket Management App

This is a Django-based web application for managing cricket matches, teams, players, and payments.

## Features

- **Sessions & attendance** — create sessions, poll availability, confirm attendance, split the cost per head
- **Teams & scoring** — assign teams and run ball-by-ball live scoring with full scorecards
- **Payments & wallet** — per-session payments, wallet balances, and settlement
- **Donations** — a public "Support the club" page at `/support/` to fundraise for club costs (see [Donations](#donations--support-the-club) below)

## Prerequisites

*   [Python 3.10+](https://www.python.org/downloads/)
*   [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for local database option)
*   [Git](https://git-scm.com/downloads/)
*   PostgreSQL database (if using your own server)

---

## Project Setup

Choose the setup path that matches your environment:

### **A. If You Already Have a PostgreSQL Database Server**

1. **Clone the Repository**
    ```bash
    git clone https://github.com/Bhanu-py/Indcric.git
    cd Indcric
    ```
2. **Create and Activate a Virtual Environment**
    - **Windows:**
      ```powershell
      python -m venv .venv
      .\.venv\Scripts\Activate.ps1
      ```
    - **macOS/Linux:**
      ```bash
      python3 -m venv .venv
      source .venv/bin/activate
      ```
3. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
4. **Configure Database Connection**
    - Update your `cric_core/settings.py` or use environment variables to point to your PostgreSQL server (host, port, user, password, db name).
5. **Run Database Migrations**
    ```bash
    python manage.py migrate
    ```
6. **(Optional) Seed the Database**
    - If you have an `initial_users.csv` file:
      ```bash
      python manage.py seed_users
      ```
7. **Create a Superuser**
    ```bash
    python manage.py createsuperuser
    ```
8. **Run the Development Server**
    ```bash
    python manage.py runserver
    ```
    - Access at [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

### **B. If You Do NOT Have a Database Server (Local Development with Docker Compose)**

1. **Clone the Repository**
    ```bash
    git clone https://github.com/Bhanu-py/Indcric.git
    cd Indcric
    ```
2. **Create and Activate a Virtual Environment**
    - **Windows:**
      ```powershell
      python -m venv .venv
      .\.venv\Scripts\Activate.ps1
      ```
    - **macOS/Linux:**
      ```bash
      python3 -m venv .venv
      source .venv/bin/activate
      ```
3. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
4. **Start the Database with Docker Compose**
    - Make sure Docker Desktop is running.
    - **Windows:**
      ```powershell
      .\fix_postgres.ps1
      ```
    - **macOS/Linux:**
      ```bash
      ./fix_postgres.sh
      ```
    - Or manually:
      ```bash
      docker-compose up -d
      ```
5. **Run Database Migrations**
    ```bash
    python manage.py migrate
    ```
6. **(Optional) Seed the Database**
    - If you have an `initial_users.csv` file:
      ```bash
      python manage.py seed_users
      ```
7. **Create a Superuser**
    ```bash
    python manage.py createsuperuser
    ```
8. **Run the Development Server**
    ```bash
    python manage.py runserver
    ```
    - Access at [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## Donations / Support the club

A public page at `/support/` lets members and visitors fund club costs (hosting, a
bigger database, drinks, equipment). Money is collected **off-app** by SEPA transfer
to the club's single bank account; the app tracks a transparent goal bar and a
contributor wall.

**One-time admin setup:**

1. `/admin/donations/donationsettings/` → **Add** → enter the club's **account holder**,
   **IBAN**, and a payment **reference**. (Held in the DB, never hardcoded in source.)
2. `/admin/donations/donationcampaign/` → **Add** a campaign (title, blurb, goal). Add
   **Fund items** inline for campaign-specific cause tiles. Untick **is active** to retire it.

Logged-in members self-log their own donations (auto-attributed); staff can log on
behalf of anyone — a member, an external name, or anonymous.

## Stopping the Application

- To stop the development server: Press `Ctrl+C` in the terminal.
- To stop the database container (if using Docker Compose):
  ```bash
  docker-compose down
  ```

---

## Notes
- Ensure your database connection settings match your environment.
- For production, use secure credentials and proper environment variable management.
- For troubleshooting, check `debug.log` and Docker logs if using containers.
