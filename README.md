# EDS Data Platform

Custom EDS-owned platform to ingest depth, velocity, and flow data from DetectData and serve it through a secure web application.

## Current Target Source
- DetectData URL: https://www.detecdata-en.com

## Stack
- Backend: FastAPI + SQLAlchemy + APScheduler + Playwright
- Database: PostgreSQL
- Frontend: React + Vite + Recharts
- Local deployment: Docker Compose

## Repository Layout
- docs/technical-spec.md: end-to-end technical specification
- docs/maintenance-guide.md: operational and maintenance procedures
- backend/: API, ingestion adapter, scheduler, ORM schema
- frontend/: dashboard and data visualization shell
- docker-compose.yml: local multi-service runtime

## Key Features Implemented
- User authentication with JWT tokens
- Password hashing with bcrypt
- Core data model:
  - sites
  - devices
  - channels
  - timeseries_data
  - users
  - permissions
  - polling_configs
  - ingestion_job_logs
- Endpoints for:
  - auth login/me
  - site list/create
  - latest data, timeseries, CSV export
  - admin user creation and polling config
  - manual sync and scheduler start/stop
- DetectData integration adapter with Playwright scaffold and configurable base URL

## Important Integration Note
The DetectData adapter is scaffolded and points to https://www.detecdata-en.com, but production selectors and authenticated extraction flows still need to be mapped against live pages and credentials.

## Run with Docker
1. Optional: export credentials
	- DETECTDATA_USERNAME=your_username
	- DETECTDATA_PASSWORD=your_password
2. Start services:
	- docker compose up --build
3. API health:
	- http://localhost:8000/health
4. Frontend:
	- http://localhost:5173

## Local Development (without Docker)
### Backend
1. cd backend
2. python -m venv .venv
3. source .venv/bin/activate
4. pip install -r requirements.txt
5. playwright install chromium
6. cp .env.example .env
7. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Bootstrap default admin user:
- python scripts/bootstrap_admin.py
- default credentials: admin / admin123

### Frontend
1. cd frontend
2. npm install
3. cp .env.example .env
4. npm run dev

## API Summary
- POST /api/v1/auth/login
- GET /api/v1/auth/me
- GET /api/v1/sites
- POST /api/v1/sites
- GET /api/v1/data/latest
- GET /api/v1/data/timeseries
- GET /api/v1/data/export.csv
- POST /api/v1/admin/users
- POST /api/v1/admin/polling-configs
- POST /api/v1/control/sync-now
- POST /api/v1/control/start
- POST /api/v1/control/stop

## Next Implementation Steps
1. Implement DetectData login form selectors and data parsing logic in backend/app/services/detectdata_client.py
2. Add complete CRUD for devices/channels/permissions
3. Add map interface (Leaflet) in frontend
4. Add audit logging endpoints and alerting hooks
5. Add migration scripts and automated tests