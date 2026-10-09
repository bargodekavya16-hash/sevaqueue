 HEAD
# sevaqueue

# SevaQueue Version 2 — CEP Project

A full-stack, dark-dashboard prototype for a Smart Queue & Appointment Management system for public-service offices.

## Features

- Citizen registration and sign-in with hashed passwords
- Role-based access: citizen, staff, admin
- Appointment creation with unique token generation
- Appointment listing, search, status filtering, and cancellation
- Staff/admin status updates (Waiting, Serving, Completed, Cancelled, Skipped)
- Dashboard KPI cards and charts
- Staff/admin analytics reports, including service and status breakdowns
- Admin user management and role assignment
- CSRF protection for forms, server-side validation, responsive dark UI
- CSV-free print-to-PDF option from the Reports page

## Tech stack

- Python + Flask
- Flask-Login, Flask-SQLAlchemy, Flask-WTF CSRF protection
- MySQL with PyMySQL
- Chart.js from jsDelivr CDN for charts
- HTML, CSS, JavaScript, Jinja templates

## Requirements

- Python 3.10+
- MySQL Server 8.x (or compatible MySQL/MariaDB)
- A terminal / command prompt
- Internet access to load Google Fonts and Chart.js CDN (layout and core pages still render without fonts; charts require Chart.js)

## Setup on Windows

### 1. Extract the project

Extract `sevaqueue_v2.zip` to a folder, for example `C:\Projects\sevaqueue_v2`, then open Command Prompt or PowerShell in that folder.

### 2. Create and activate a virtual environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:
```bat
.venv\Scripts\activate.bat
```

### 3. Install Python dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create the MySQL database and database user

Open MySQL Workbench or the MySQL command-line client and run the commands from `schema.sql`.

**Important:** Replace `CHANGE_THIS_DB_PASSWORD` in `schema.sql` with a strong password before running it. Use the same password in your `.env` file in the next step. Do not commit `.env` or share the password.

### 5. Configure environment variables

Copy `.env.example` to `.env`:

PowerShell:
```powershell
Copy-Item .env.example .env
```

Edit `.env` and set:
```env
SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=mysql+pymysql://sevaqueue:YOUR_DB_PASSWORD@localhost/sevaqueue
FLASK_DEBUG=0
```

If your database password contains characters such as `@`, `:`, `/`, `#`, or `%`, URL-encode those characters in `DATABASE_URL` or choose a development password that avoids them.

Create a random secret key with:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

### 6. Create the tables

```powershell
flask --app app init-db
```

### 7. Start the website

```powershell
flask --app app run
```

Open this URL in your browser:
`http://127.0.0.1:5000`

Stop the local server with `Ctrl+C`.

## Create the first administrator

In a second terminal (with the same virtual environment activated and inside the project directory), run:

```powershell
flask --app app create-admin
```

Enter the admin name, email, and a strong password when prompted. Then sign in using that account. Admins can visit **User management** to promote trusted accounts to `staff` or `admin`.

To create a staff account:
1. Register that person as a normal citizen through the site.
2. Sign in as an admin.
3. Open **User management**.
4. Change the user's role to `staff`.

## Typical demo flow for a college presentation

1. Register a citizen account.
2. Create an appointment for a future date and show its generated token.
3. Open the dashboard and show KPI cards and charts.
4. Use the appointment filters to find a token.
5. Sign in as a staff account and update the appointment status.
6. Open Reports & analytics to show daily activity, service breakdown, and status distribution.
7. Sign in as admin to demonstrate user role management.
8. Use **Export / Print report** on the reports page and choose “Save as PDF” in the browser print dialog.

## Database design

### `user`
- `id` — primary key
- `full_name` — account display name
- `email` — unique login email
- `password_hash` — hashed password (never store plain text)
- `role` — citizen / staff / admin
- `created_at` — account creation timestamp

### `appointment`
- `id` — primary key
- `token` — unique appointment token
- `user_id` — citizen foreign key
- `service` — service category
- `appointment_date`, `appointment_time` — appointment schedule
- `status` — current workflow status
- `notes` — optional note
- `created_at` — creation timestamp

## Important notes

- This is a student CEP prototype. It is not an official government website and is not connected to a live government queue, SMS, email, or payment system.
- This version uses local database persistence, but it is not production-hardened. Before public deployment, use HTTPS, a strong secret, secure cookie settings, database backups, rate limiting, audit logs, stronger validation, and a production WSGI server.
- Role-based access is implemented in Flask route handlers. Do not expose the development server publicly.
- Analytics are based on the records in your own database. Empty charts are expected before appointments have been created.
- The UI uses Chart.js and Google Fonts CDNs. For a fully offline demo, download and serve those assets locally.
e8e3ddd (Initial commit)
