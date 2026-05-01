# SafeBooks SQLite To PostgreSQL Migration Runbook

## Decision
Yes, this is a great idea.

For your current and future scale, moving from SQLite to PostgreSQL is the right long-term decision for reliability, concurrent usage, and production readiness.

We will execute this in a staged, low-risk way.

## Scope
This runbook is only for database migration.
It is separate from refinement work in [PromptUI/Plan_phases/phase6_refinement_efficiency_plan.md](PromptUI/Plan_phases/phase6_refinement_efficiency_plan.md).

## Collaboration Model
- You: infrastructure, credentials, and go/no-go approvals.
- Me: code changes, migration commands, validation scripts, and safety checks.
- Rule: we do not move to the next phase until the current checkpoint is green.

---

## Phase 0 - Pre-Migration Safety Gate
### Goal
Freeze risky changes and prepare rollback safety.

### You do
1. Confirm a short migration window for final cutover.
2. Confirm where PostgreSQL will run first:
- local PostgreSQL
- Docker PostgreSQL
- cloud provider PostgreSQL
3. Approve temporary code freeze on schema-related changes during migration.

### I do
1. Re-check current migrations state.
2. Re-check test baseline before any migration work.
3. Prepare command checklist for repeatable execution.

### Checkpoint (must pass)
- Current tests pass.
- No pending migration conflicts.
- Cutover window agreed.

---

## Phase 1 - Add PostgreSQL Compatibility In Codebase
### Goal
Make project able to run on either SQLite or PostgreSQL using environment configuration.

### You do
1. Provide preferred environment variable names.
2. Confirm if you want one URL variable or split DB variables.

### I do
1. Update settings to support dual database mode:
- SQLite fallback for local/dev
- PostgreSQL when env variables are provided
2. Add PostgreSQL dependency to requirements.
3. Create .env example guidance for safe setup.
4. Keep all existing app logic unchanged.

### Checkpoint (must pass)
- Project still runs on SQLite after changes.
- Project can start with PostgreSQL env config.
- No functional regression in current pages and APIs.

---

## Phase 2 - Provision PostgreSQL Instance
### Goal
Prepare a clean PostgreSQL target database.

### You do
1. Create PostgreSQL database and user.
2. Share connection values securely (host, port, db name, user, password, ssl mode).
3. Confirm network access from your app environment.

### I do
1. Validate connection using Django with PostgreSQL settings.
2. Run migrate on PostgreSQL target.
3. Confirm schema creation success.

### Checkpoint (must pass)
- Django migrate succeeds on PostgreSQL.
- Admin and app tables exist.

---

## Phase 3 - Data Export From SQLite
### Goal
Take a safe, restorable snapshot from current SQLite data.

### You do
1. Keep a safe copy of db.sqlite3 before any import.
2. Confirm whether to migrate all data or application data only.

### I do
1. Export data from SQLite to fixture(s).
2. Prefer app-scoped export first (safebooks app data) to reduce noise.
3. Document exact export command and artifact path.

### Recommended default export mode
- Primary export: safebooks app data only.
- Optional export: include selected framework tables if needed.

### Checkpoint (must pass)
- Export file created.
- Export file opens and validates as JSON.
- Row count snapshot recorded before import.

---

## Phase 4 - Data Import To PostgreSQL (Dry Run First)
### Goal
Load exported data into PostgreSQL and validate parity.

### You do
1. Approve dry-run import first (non-production target).
2. Confirm if any test users or seed data must be excluded.

### I do
1. Import fixture into PostgreSQL.
2. Run parity checks:
- per-table counts (core app tables)
- sample records by client and period
- API smoke calls for dashboard and analytics
3. Fix ordering/dependency issues if import warnings appear.

### Checkpoint (must pass)
- Core table counts are acceptable.
- Dashboard and analytics endpoints return expected data.
- Critical flows work:
- login
- clients list
- financial records list/detail
- analytics load and client scope

---

## Phase 5 - Switch Default Runtime To PostgreSQL
### Goal
Promote PostgreSQL from optional to primary runtime.

### You do
1. Update deployment/runtime environment variables.
2. Confirm secret management is in place.
3. Approve go-live switch.

### I do
1. Verify app boots with PostgreSQL-only configuration.
2. Re-run migrations to ensure final schema sync.
3. Run targeted regression tests.

### Checkpoint (must pass)
- App starts and runs on PostgreSQL.
- Tests and smoke checks pass.
- No critical error in logs after initial traffic.

---

## Phase 6 - Post-Cutover Stabilization
### Goal
Observe behavior and keep rollback readiness for a short period.

### You do
1. Monitor performance and usage.
2. Confirm user-reported behavior is normal.

### I do
1. Run quick health checks daily during stabilization window.
2. Keep migration notes updated with any issue and fix.
3. Prepare closeout summary once stable.

### Exit condition
- Stable operations for agreed observation window.
- No unresolved data integrity issues.

---

## Rollback Plan
If a critical issue appears after cutover:
1. Stop write operations if needed.
2. Switch runtime config back to SQLite.
3. Restore last known stable SQLite backup if required.
4. Record root cause and patch before reattempt.

Rollback safety assets to keep:
- original db.sqlite3 backup
- exported fixtures
- PostgreSQL migration/import logs
- environment config history

---

## Command Checklist (Template)
Use this section as a controlled execution checklist during implementation.

1. Baseline checks
- python manage.py check
- python manage.py test safebooks.tests.test_dashboard_summary_api safebooks.tests.test_analytics_summary_api

2. Export from SQLite
- Windows PowerShell (UTF-8 without BOM):
- $json = python manage.py dumpdata safebooks --indent 2 | Out-String
- [System.IO.File]::WriteAllText((Resolve-Path backups/safebooks_data.json), $json, (New-Object System.Text.UTF8Encoding($false)))
- Validate fixture:
- python -m json.tool backups/safebooks_data.json > $null

3. Migrate on PostgreSQL target
- python manage.py migrate

4. Import to PostgreSQL target
- python manage.py loaddata backups/safebooks_data.json

5. Post-import verification
- python manage.py check
- python manage.py test safebooks.tests.test_dashboard_summary_api safebooks.tests.test_analytics_summary_api

Note
- Exact commands may be adjusted for your terminal path style and environment activation method.
- On Windows PowerShell, avoid using `>` for dumpdata export because it may produce UTF-16 output that breaks `loaddata`.

---

## First Step To Start Now
Start Phase 0 and Phase 1 only.

Once you confirm your preferred PostgreSQL host setup and env variable format, I will implement the dual-database settings and dependency updates immediately.