# EDS Data Platform Technical Specification

## 1. Purpose
This document translates the EDS program brief into an implementable architecture and starter implementation for an EDS-owned data platform that ingests DetectData measurements and serves them through a secure web application.

## 2. Goals
- Authenticate against DetectData with credential-based login.
- Collect depth, velocity, and flow from all available sites, devices, and channels.
- Normalize and store measurements in an EDS-managed PostgreSQL database.
- Provide role-based, secure, browser-based access to monitoring data.
- Support configurable polling intervals, site/device mapping, and access permissions.

## 3. Architecture

### 3.1 High-Level Components
- Ingestion service (FastAPI service + scheduler + scraper adapter)
- PostgreSQL data store
- REST API (FastAPI)
- Frontend web app (React + Vite)
- Background polling scheduler (APScheduler in-app worker)

### 3.2 Data Flow
1. Scheduler triggers polling jobs by site/device according to configured intervals.
2. DetectData adapter performs login, maintains session, and retrieves raw readings.
3. Ingestion service maps remote entities to local Site/Device/Channel records.
4. Measurements are normalized and inserted into TimeSeriesData.
5. API serves latest values and history with RBAC filtering.
6. Frontend renders dashboard, trend views, and management pages.

## 4. DetectData Integration Strategy
Because no public API is available:
- Primary approach: Playwright browser automation for login and data capture.
- Secondary optimization: request interception/replay if authenticated endpoints are discovered.
- Fallback and resilience:
  - DOM selectors centralized in one adapter module.
  - Retries with exponential backoff for login or transient fetch failures.
  - Structured logs for extraction success and failure diagnostics.

## 5. Data Model
The implementation uses the following core entities:
- Site: metadata and geographic coordinates.
- Device: meter/sensor linked to site.
- Channel: parameter stream (depth, velocity, flow) and units.
- TimeSeriesData: timestamped measurement values.
- User: local identity with bcrypt password hash.
- Permission: user-to-site access plus channel-level access map.
- PollingConfig: per-site or per-device ingestion cadence and enable/disable state.
- IngestionJobLog: operational audit of scheduler runs and outcomes.

## 6. Security Model
- Authentication: username + password, JWT access token.
- Password storage: bcrypt hashes only.
- Authorization: role-based access control with site/channel constraints.
- Transport: HTTPS required in deployment.
- Optional hardening:
  - audit log endpoint and immutable log sink
  - rate limiting and lockout thresholds

## 7. API Surface (Initial)
- Auth
  - POST /api/v1/auth/login
  - GET /api/v1/auth/me
- Sites/Devices/Channels
  - GET /api/v1/sites
  - POST /api/v1/sites (admin)
  - GET /api/v1/sites/{site_id}/devices
- Data
  - GET /api/v1/data/latest
  - GET /api/v1/data/timeseries
  - GET /api/v1/data/export.csv
- Admin
  - CRUD users
  - CRUD permissions
  - CRUD polling configs
- Control
  - POST /api/v1/control/sync-now
  - POST /api/v1/control/start
  - POST /api/v1/control/stop

## 8. Scheduling and Reliability
- APScheduler executes polling jobs per active PollingConfig.
- Retry behavior:
  - Login retries
  - Per-device polling retries
- Job execution logging includes status, started/finished timestamps, and error text.

## 9. Scalability Path
- Indexes on (channel_id, timestamp) and timestamp.
- Partitioning or migration to TimescaleDB for higher-volume workloads.
- Horizontal scale by moving scheduler and ingestion to worker containers.

## 10. Deliverables in This Repository
- Backend API and ingestion skeleton (FastAPI).
- PostgreSQL-ready ORM schema.
- Frontend React application skeleton.
- Docker Compose local environment.
- Deployment and maintenance documentation.

## 11. Open Integration Tasks
- Implement production DetectData selectors and extraction logic.
- Validate session/token behavior against live DetectData workflow.
- Complete full CRUD and map UI.
- Add alerting integrations and advanced observability.
