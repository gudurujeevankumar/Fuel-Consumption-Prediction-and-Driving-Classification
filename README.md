# ECU Analytics — Python Backend

## Overview
ECU Analytics is a comprehensive platform for vehicle telemetry analysis, featuring machine learning-based fuel prediction, driving profile classification, and a real-time dashboard. The backend is powered by Python (Flask) and MySQL, utilizing machine learning models (XGBoost, Ridge Regression, SVR) for predictive analytics.

## Features
- **Real-Time Dashboard**: Monitor vehicle telemetry data visually.
- **Machine Learning Predictions**: XGBoost, Ridge, and SVR models to predict fuel consumption and classify driving behavior.
- **Admin Panel**: Manage users, APIs, and overall system configuration.
- **Secure Authentication**: Bcrypt password hashing and robust user session management.

## Prerequisites
To run this project in a new environment, ensure you have the following installed:
- **Python 3.8+**
- **MySQL Server** (Running locally or remotely)
- **Git** (optional, for cloning the repository)

## Setup Instructions

### 1. Navigate to the Project Directory
Ensure you are in the project root directory:
```bash
cd ecu_py
```

### 2. Set Up a Virtual Environment (Recommended)
It is highly recommended to use a virtual environment to manage dependencies cleanly.
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
```

### 3. Install Dependencies
Install the required Python packages using pip:
```bash
pip install -r requirements.txt
```

### 4. Database Configuration
1. Ensure your MySQL server is running.
2. Create or update the `.env` file in the root directory. You can use the following default template:
   ```env
   PORT=5000
   SECRET_KEY=ecu-analytics-secret-key-2025
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=ecu_analytics
   ```
3. Initialize the database by running the setup SQL script:
   ```bash
   mysql -u root -p < database/setup.sql
   ```
   *(Note: Enter your MySQL root password when prompted. The application's launch script will automatically verify and create missing tables on startup.)*

### 5. Run the Application
Start the backend server using the provided one-click launcher:
```bash
python3 start.py
```
You can also specify a custom port if the default is in use:
```bash
python3 start.py --port 8080
```

### 6. Access the Dashboards
Once the server is running, open a web browser and access the following:
- **Main Dashboard:** `http://localhost:5000`
- **Admin Dashboard:** `http://localhost:5000/admin_login.html`
- **API Health Check:** `http://localhost:5000/api/health`

**Default Admin Credentials:**
- Email: `admin@ecu.com`
- Password: `admin123`

## Project Structure
- `backend/` - Flask application, configuration, and API routes
- `backend/ml/` - Machine learning models and predictors
- `database/` - SQL schema setup files (`setup.sql`)
- `frontend/` - HTML, JS, and CSS files for the dashboards
- `logs/` - Application logs generated during runtime
- `scripts/` - Utility and helper scripts
- `start.py` - Main launch script

## Troubleshooting
- **Port already in use**: If port 5000 is occupied, try running with a different port (e.g., `python3 start.py --port 8080`) or stop the conflicting service. On macOS, port 5000 can sometimes be used by the AirPlay Receiver.
- **MySQL Connection Failed**: Double-check your `.env` credentials (`DB_USER`, `DB_PASSWORD`), ensure the MySQL service is actively running on the specified `DB_PORT`, and that the `ecu_analytics` database exists.
