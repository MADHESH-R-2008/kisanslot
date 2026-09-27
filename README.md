# KisanSlot

KisanSlot is a farmer procurement and queue-management system consisting of a Flutter farmer application, React operator/admin dashboard, and FastAPI backend.

## Architecture

- `lib/`: Flutter farmer application
- `admin_dashboard/`: React/Vite dashboard
- `backend/`: FastAPI, SQLAlchemy services, routes, seed data, tests, and Alembic migrations
- `backend/migrations/`: incremental database migrations

The backend is the authoritative source for authentication, authorization, slot capacity, tokens, queue transitions, procurement totals, payment amounts, notifications, and analytics.

## Prerequisites

- Python 3.12+
- MySQL 8.0+ (Turbify MySQL is the production target)
- Node.js 20+
- Flutter 3.44+

## Environment

Copy `backend/.env.example` to `.env` in the repository root for local development. Set:

```text
DATABASE_URL=mysql+pymysql://YOUR_USERNAME:YOUR_PASSWORD@YOUR_MYSQL_HOST:3306/YOUR_DATABASE?charset=utf8mb4
TEST_DATABASE_URL=mysql+pymysql://YOUR_TEST_USERNAME:YOUR_TEST_PASSWORD@YOUR_MYSQL_HOST:3306/YOUR_TEST_DATABASE?charset=utf8mb4
SECRET_KEY=a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
ENVIRONMENT=development
```

Never commit real credentials. Use `ENVIRONMENT=production` in deployed environments.

For Turbify, create the database and assign its user in the hosting control panel, then verify it in phpMyAdmin. Use `localhost` as `YOUR_MYSQL_HOST` only when FastAPI runs in the same Turbify hosting environment; a backend running on a PC or another host needs the actual remotely reachable hostname supplied by Turbify. Back up an existing database before running migrations. Do not use a production database for tests.

### Turbify production setup

1. Create/select the MySQL database in the Turbify control panel.
2. Create a database user and grant it access to that database.
3. Open phpMyAdmin and confirm the selected database is reachable.
4. Back up any existing database before applying migrations.
5. Put `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`, and `ENVIRONMENT=production` in the backend host's environment (not Git).
6. Run `backend\venv\Scripts\python.exe -m alembic upgrade head` from the repository root.
7. Run `backend\venv\Scripts\python.exe backend\seed.py`; the seed is idempotent.
8. Start FastAPI with `backend\venv\Scripts\python.exe -m uvicorn main:app` from `backend`.
9. Configure `VITE_API_URL`/`VITE_WS_URL`, then build or start the React dashboard.
10. Configure the Flutter API base URL for the deployed backend, then build or run Flutter.

## Backend

```powershell
backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
backend\venv\Scripts\python.exe -m alembic upgrade head
Set-Location backend
venv\Scripts\python.exe seed.py
venv\Scripts\python.exe -m uvicorn main:app --reload
```

Swagger documentation is available at `http://127.0.0.1:8000/docs`.

## Admin dashboard

```powershell
Set-Location admin_dashboard
npm install
npm run dev
```

Set `VITE_API_URL` and `VITE_WS_URL` for non-local environments.

## Flutter application

```powershell
flutter pub get
flutter run
```

Android emulators use `http://10.0.2.2:8000`; desktop/web development uses `http://127.0.0.1:8000`. Configure the base URL through the existing API service/environment mechanism.

## Development accounts

- Farmer: `9999999999` / `farmer123`
- Centre operator: `operator1` / `op123`, assigned to Centre 3
- Admin: `admin` / `admin123`
- Super admin: `super` / `super123`

These accounts are development fixtures. Passwords are stored as hashes.

## Tests

```powershell
backend\venv\Scripts\python.exe -m compileall -q backend
backend\venv\Scripts\python.exe -m pytest backend\tests -q -p no:cacheprovider

Set-Location admin_dashboard
npm run build

Set-Location ..
flutter analyze --no-pub
flutter test
```

The backend tests use an isolated SQLite database by default. SQLite is useful for fast checks but does not prove MySQL locking behavior. For authoritative MySQL migration and concurrency validation, create an empty, disposable MySQL database and run:

```powershell
$env:TEST_DATABASE_URL="mysql+pymysql://TEST_USER:TEST_PASSWORD@MYSQL_HOST:3306/TEST_DATABASE?charset=utf8mb4"
$env:ALLOW_DESTRUCTIVE_TEST_DATABASE="true"
$env:DATABASE_URL=$env:TEST_DATABASE_URL
backend\venv\Scripts\python.exe -m alembic upgrade head
backend\venv\Scripts\python.exe -m pytest backend\tests -q -p no:cacheprovider
```

The suite drops and recreates tables. Never set `TEST_DATABASE_URL` to the Turbify production database. The explicit confirmation variable is required whenever `TEST_DATABASE_URL` is used.

## Database behavior

Run `alembic upgrade head` before starting production deployments. Production startup does not use `Base.metadata.create_all()` as its migration strategy. Booking creation uses an atomic capacity update and per-centre/day database token counter. Critical state transitions return `409 Conflict` when invalid.

Queue state currently uses the booking aggregate as its single source of truth. This intentionally avoids duplicated queue and booking status rows becoming inconsistent.

## Deployment

`render.yaml` installs backend dependencies, runs Alembic, starts FastAPI, and builds the React dashboard. Configure `DATABASE_URL`, `SECRET_KEY`, and `CORS_ORIGINS` in the deployment environment. The deployment host must be able to reach the Turbify MySQL host; Turbify's `localhost` database address is not reachable as `localhost` from Render or a developer PC.

## Known local limitation

An actual MySQL server and a separate test database are required for authoritative MySQL integration tests. Flutter commands may require stale Flutter tool processes to be stopped if a previous command was interrupted.
