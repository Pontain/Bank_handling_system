# Bank Handling System

An educational banking application built with Flask. It brings together customer and account management, role-based staff access, transaction workflows, reporting, and a small AML module.

## Features

- Customer and account management
- Role-based staff access for cashier and administrator workflows
- Transaction processing and account services
- Dashboard statistics and customer summaries
- Flask API endpoints for accounts and customers
- Database migrations, seed data, and service-level tests

## Technology

Python, Flask, SQLAlchemy, Flask-Migrate, MySQL-compatible database support, and pytest.

## Run locally

Create and activate a virtual environment, then install the dependencies:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Configure the required database and Flask security settings in environment variables before starting the application. Keep credentials in a local `.env` file and do not commit it.

```bash
python app.py
```

The app is intended for development and learning. Use synthetic data; it is not connected to a real bank or payment network.
