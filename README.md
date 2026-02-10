# CA CRM System

A lightweight CRM system for CA associates with admin and user roles.

## Features
- Admin portal for user management
- Client management
- Task assignment system
- Role-based access control
- Compatible with local and AWS deployment

## Quick Start (WSL)

1. Install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Access at: http://localhost:5000
   - Default login: admin / admin123

## AWS Deployment

Set environment variables:
```bash
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
export SECRET_KEY=your-production-secret-key
```

Run with Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
