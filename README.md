# ECU Analytics — Python Backend

## 🌍 Live Project Link : https://fuel-consumption-prediction-and-driving.onrender.com/

## Overview
ECU Analytics is a comprehensive platform for vehicle telemetry analysis, featuring machine learning-based fuel prediction, driving profile classification, and a real-time dashboard. The backend is powered by Python (Flask) and **SQLite**, utilizing machine learning models (XGBoost, Ridge Regression, SVR) for predictive analytics.

## Features
- **Real-Time Dashboard**: Monitor vehicle telemetry data visually.
- **Machine Learning Predictions**: XGBoost, Ridge, and SVR models to predict fuel consumption and classify driving behavior.
- **Admin Panel**: Manage users, APIs, and overall system configuration.
- **Secure Authentication**: Bcrypt password hashing and robust user session management.
- **Health Endpoint**: Simple `/health` endpoint configured to prevent Render downtime via cron-job pinging.

## Prerequisites
To run this project in a new environment, ensure you have the following installed:
- **Python 3.8+**
- **Git** (optional, for cloning the repository)

## Setup Instructions

### 1. Navigate to the Project Directory
Ensure you are in the project root directory:
```bash
cd "Fuel Consuption Prediction"
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
1. Create or update the `.env` file in the root directory. You can use the following default template:
   ```env
   PORT=8080
   SECRET_KEY=ecu-analytics-secret-key-2025
   ```
2. The database setup is entirely automated! The application will create a local `ecu_analytics.db` SQLite database file and initialize all necessary tables when you start the server.

### 5. Run the Application
Start the backend server using the provided one-click launcher:
```bash
python3 start.py
```
You can also specify a custom port if the default is in use:
```bash
python3 start.py --port 5000
```

### 6. Access the Dashboards
Once the server is running, open a web browser and access the following:
- **Main Dashboard:** `http://localhost:8080`
- **Admin Dashboard:** `http://localhost:8080/admin_login.html`
- **API Health Check:** `http://localhost:8080/api/health`
- **Root Health Check:** `http://localhost:8080/health` (Useful for Render keeping instance awake)

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
- **Port already in use**: If port 8080 is occupied, try running with a different port (e.g., `python3 start.py --port 5000`) or stop the conflicting service.
- **ML Models fail to load**: If you get pickling or version errors (e.g., `_loss` module missing), delete the `backend/ml/saved_models/models.pkl` file and run `start.py` again to automatically retrain fresh models.

## Screenshots

| User Interface | Admin Interface |
|:---:|:---:|
| **User Registration**<br>![Register Page](Screenshots/Register%20page.png) | **Admin Login**<br>![Admin Login](Screenshots/admin%20login.png) |
| **User Login**<br>![Login Page](Screenshots/login%20Page.png) | **Admin Dashboard Overview**<br>![Admin Dashboard](Screenshots/admin%20dashboard.png) |
| **Live User Dashboard**<br>![Live Dashboard](Screenshots/live%20dashboard.png) | **User Management**<br>![User Handling](Screenshots/user%20handling%20page.png) |
| **Driving Simulator**<br>![Driving Simulation](Screenshots/Driving%20Simulation%20page.png) | **System Alerts View**<br>![Alerts Page](Screenshots/alerts%20page.png) |
| **Post-Drive Report**<br>![Drive Report](Screenshots/drive%20report.png) | **User-Specific Alerts**<br>![User Alerts](Screenshots/user%20alerts%20in%20admin%20pannel.png) |
| | **ML Model Metrics**<br>![ML Metrics](Screenshots/ML%20metrics.png) |
