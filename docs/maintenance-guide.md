# EDS Data Platform Maintenance Guide

## 1. Routine Operations
- Review ingestion job logs daily.
- Verify latest readings update for representative sites every shift.
- Review API and worker container health.

## 2. DetectData Break/Fix Procedure
1. Confirm login credentials are valid.
2. Check scraper logs for selector or navigation failures.
3. Update selector constants in the DetectData adapter.
4. Run manual sync endpoint to validate fix.
5. Record change reason and impacted entities.

## 3. Database Maintenance
- Monitor storage growth in TimeSeriesData.
- Add retention/archive policy if required by contract.
- Reindex periodically for high-write deployments.
- Backup schedule: daily snapshot + point-in-time recovery.

## 4. Security Maintenance
- Rotate secrets quarterly or after personnel changes.
- Force password reset for compromised accounts.
- Review admin role assignments monthly.
- Keep TLS certificates valid and renewed.

## 5. Upgrade Strategy
- Pin dependencies and update monthly.
- Validate in staging before production rollout.
- Run smoke checks:
  - authentication
  - manual sync
  - latest and historical data queries
  - CSV export

## 6. Incident Response Minimums
- Track incident start time, impact, and root cause.
- Preserve relevant logs.
- Apply rollback if an update causes ingestion outage.
- Publish short post-incident summary with preventive actions.
