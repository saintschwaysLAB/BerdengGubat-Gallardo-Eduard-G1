# Berdeng Gubat

Berdeng Gubat is a Django web application that connects donors with reforestation
fundraising campaigns created by organizations and their NGO/LGU partners.

## Core feature: reforestation fundraising

- Organization leaders and admins can create and manage organization listings.
- Organization leaders and admins can create fundraising campaigns for an
  organization, set a PHP fundraising goal and optional deadline, and activate
  or deactivate campaigns.
- Donors can browse active campaigns, see their recorded fundraising progress,
  and save, review, edit, or delete their own donation records.
- Organization leaders can review donation records for their own organizations.
- Donation records are stored for project tracking; this application does not
  process payments.

## Roles

- **Donor**: browse active campaigns and manage personal donation records.
- **Organization leader**: manage owned organizations, campaigns, and their
  organizations' donation records.
- **Admin**: manage and review organizations, campaigns, and donation records.

## Requirements

- Python installed and available from the command line.
- PostgreSQL database. The application is configured to read its connection
  URI from `DATABASE_URL` (for example, a Supabase PostgreSQL connection URI).

## Setup on a new computer

1. Clone the repository and open a CMD terminal in the project folder (the
   folder containing `manage.py`):

   ```bat
   git clone https://github.com/saintschwaysLAB/BerdengGubat-Gallardo-Eduard-G1.git
   cd BerdengGubat-Gallardo-Eduard-G1
   ```

2. Create and activate a virtual environment:

   ```bat
   py -m venv .venv
   .venv\Scripts\activate.bat
   ```

3. Install dependencies:

   ```bat
   python -m pip install -r requirements.txt
   ```

4. Create the local environment file:

   ```bat
   notepad .env
   ```

   Add your database connection URI on one line:

   ```env
   DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=require
   ```

   Replace the example values with the connection details from your PostgreSQL
   provider. Keep `.env` private; it is ignored by Git and must never be
   committed or shared.

5. Apply database migrations and start the development server:

   ```bat
   python manage.py migrate
   python manage.py runserver
   ```

6. Visit <http://127.0.0.1:8000/> and create an account. Each computer needs its
   own `.venv`; do not copy the virtual environment between computers.

## Tests

Run the Django test suite with:

```bat
python manage.py test
```

The test runner creates a temporary test database. Configure `DATABASE_URL`
with a PostgreSQL connection that permits creating and dropping test databases,
or use a local test-only database URL.

## Main project files

- `accounts/`: custom user model, registration, login, and profile.
- `dashboard/`: organizations, campaigns, donations, views, and migrations.
- `templates/`: Django pages for account, organization, campaign, and donation
  flows.
- `requirements.txt`: Python dependencies.
