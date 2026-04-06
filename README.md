# AI Study Planner MVP

Django-based prototype for managing subjects, assessments, deadlines, study sessions, analytics, and simulated in-app reminders.

## Stack

- Django 5
- Bootstrap 5
- Chart.js
- FullCalendar
- PostgreSQL via environment variables, with SQLite fallback for local bootstrap/testing

## Quick Start

1. Install dependencies:
   `python -m pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and adjust values if you want PostgreSQL.
3. Run migrations:
   `python manage.py migrate`
4. Seed demo data:
   `python manage.py seed_demo_data`
5. Start the server:
   `python manage.py runserver`

Demo login:

- Username: `demo_student`
- Password: `demo12345`

## Management Commands

- `python manage.py seed_demo_data`
- `python manage.py refresh_daily_plans`
- `python manage.py run_notification_checks`

## Key Modules

- `accounts`: auth, profile, preferences
- `subjects`: subject management
- `assessments`: assessments and deadlines
- `planner`: scoring engine, study plans, study sessions, planner logs, settings
- `progress`: progress snapshots and metrics
- `notifications`: in-app reminder simulation
- `dashboard`: student overview and notifications UI
- `reports`: analytics and charts
