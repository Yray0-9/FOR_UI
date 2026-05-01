# SafeBooks Dashboard To Analytics Real-Data Plan

## Goal
Build real backend-driven data for Clients, Financial Records, and Dashboard first, then start Analytics on top of reliable data.

This plan is based on the current implementation already in your system as of 2026-04-20.

## Execution Status Update (2026-04-21)
- Phase 1 completed: server-side session auth guard + real logout endpoint.
- Phase 2 completed: real Clients table + CRUD API + clients page API integration.
- Phase 3 completed: real Period + FinancialRecord + FinancialRecordLine tables, financial records APIs, and both financial pages migrated from preview data to backend data.
- Phase 4 completed: dashboard now uses real backend summary data API (no hardcoded dashboard datasets).
- Phase 4.1 completed: dashboard API hardening tests added (auth, metrics payload, ownership isolation, recent-ordering limit).
- Phase 5.1 completed: analytics backend summary API implemented with bookkeeper scoping and client filtering (`/api/analytics/summary/`).
- Phase 5.2 completed: analytics UI is now connected to real API data (client selector, summary cards, trend, risk insight, forecast, comparison, empty state).
- Phase 5.3 baseline completed: analytics API regression tests added (auth requirement, totals correctness, ownership isolation, empty payload behavior).
- Phase 5.4 completed: analytics timeframe/scope clarity polish added (dynamic labels now clarify that totals/comparison use all recorded entries in selected scope while trend chart is limited to a 6-month window).
- Phase 5.5 completed: analytics now supports safer client targeting using TIN disambiguation in UI (TIN search + TIN-visible client options) to avoid wrong-client selection when names are duplicated.
- Next recommended work: evaluate advanced analytics ideas from user feedback (for example deeper forecasting or period-over-period drilldowns) as a scoped Phase 5.6 increment.

---

## 1. Current State Audit

### 1.1 Completed and Working
- Login and Sign Up backend is implemented with SQLite persistence.
- Password hashing and validation rules are implemented.
- Auth API endpoints are live:
  - `POST /api/auth/login/`
  - `POST /api/auth/register/`
- Auth UI is connected to backend and shows proper success/error messages.
- Dashboard header profile is now functional in UI:
  - reads logged-in user from browser storage
  - has dropdown actions for Profile (placeholder) and Log out
- Welcome toast after login is implemented.
- Favicon 404 issue was addressed through routing.

### 1.2 Partially Implemented (UI Works, Backend Not Yet Real)
- Dashboard data blocks currently use hard-coded in-page datasets (not backend API data).
- Clients page add/edit/delete operations are currently frontend-only preview logic.
- Financial Records list and client detail pages are currently frontend-only preview logic.
- Profile action exists in dropdown but no Profile page yet (intentionally deferred).

### 1.3 Not Yet Implemented (Important for Production)
- No server-side session-based route protection is enforced yet for dashboard pages.
- No backend models yet for:
  - Clients
  - Periods
  - Financial Records
  - Financial Record Line Items
- No CRUD API layer yet for clients and financial records.
- No dashboard summary API yet.
- No analytics backend endpoints yet.

---

## 2. Why Real Data Must Come Before Analytics
- Analytics built on sample arrays will need major rewrite later.
- Real dashboard metrics depend on normalized persisted records.
- Risk classification and compliance summaries are only meaningful with real transaction history.

Decision: continue with backend data foundation now, then build Analytics.

---

## 2.1 Database Table File Standard (Requested)

To keep migration preparation clean and predictable, use this standard for every new table:

1. One table model per file inside `safebooks/models/`.
2. Keep a central model registry in `safebooks/models/table_registry.py`.
3. Update `safebooks/models/__init__.py` whenever a new table model is added.
4. Never mix multiple unrelated table models in one file.

Example for future additions:
- `client_model.py` -> `Client`
- `period_model.py` -> `Period`
- `financial_record_model.py` -> `FinancialRecord`
- `financial_record_line_model.py` -> `FinancialRecordLine`

---

## 3. Execution Strategy (Step-By-Step, Low Risk)

## Phase 1 - Access Control and Auth Hardening (Before Data CRUD)
Purpose: make sure only authenticated users can access and modify data routes.

### Tasks
1. Add server-side login session creation on successful login.
2. Add server-side logout endpoint.
3. Add auth guard decorator/helper for protected pages and APIs.
4. Replace open TemplateView routes for protected pages with guarded views.
5. Keep current UI dropdown logout, but connect it to real logout endpoint.

### Target Files
- `safebooks/views.py`
- `safebooks/urls.py`
- `templates/base/dashboard.html`
- `templates/base/clients.html`
- `templates/base/financial_records.html`
- `templates/base/financial_records_client.html`

### Acceptance Criteria
- Unauthenticated user visiting `/dashboard/` is redirected to login.
- Log out clears both server session and client storage.
- Existing login UX still works.

---

## Phase 2 - Clients Backend (First Real Domain Feature)
Purpose: replace frontend-only clients preview with real SQLite-backed CRUD.

### Data Model
Create `Client` model owned by logged-in bookkeeper.
Recommended fields:
- id
- bookkeeper (FK -> BookkeeperAccount)
- client_name
- tin_number (unique)
- trade_name (optional)
- location
- permit_number
- birthday (optional)
- email (optional)
- risk_level (default medium)
- created_at
- updated_at

### Tasks
1. Create model and migration.
2. Create clients service layer (list/create/update/delete + ownership filtering).
3. Create clients API endpoints.
4. Connect `clients.html` JS actions to API calls.
5. Keep current UI behavior but replace in-memory mutations with backend responses.

### Target Files
- `safebooks/models/client_model.py`
- `safebooks/models/__init__.py`
- `safebooks/services/client_service.py`
- `safebooks/views.py`
- `safebooks/urls.py`
- `templates/base/clients.html`

### Acceptance Criteria
- Added client persists after refresh.
- Edit/delete is persisted.
- User only sees own clients.

---

## Phase 3 - Financial Records Backend
Purpose: make financial records and line items fully persistent and client-scoped.

### Data Models
1. `Period` (month/year grouping)
2. `FinancialRecord` (header)
3. `FinancialRecordLine` (line items)

### Tasks
1. Add models and migrations.
2. Build service layer for record and line item operations.
3. Add APIs for:
   - list clients with record activity
   - list records by client + period
   - create/update/delete record
   - create/update/delete line items
4. Replace `financial_records.html` static rows with API data.
5. Replace `financial_records_client.html` in-memory `recordsByPeriod` logic with backend API.

### Target Files
- `safebooks/models/period_model.py`
- `safebooks/models/financial_record_model.py`
- `safebooks/models/financial_record_line_model.py`
- `safebooks/models/__init__.py`
- `safebooks/services/financial_record_service.py`
- `safebooks/views.py`
- `safebooks/urls.py`
- `templates/base/financial_records.html`
- `templates/base/financial_records_client.html`

### Acceptance Criteria
- Records persist and reload correctly by client and period.
- Line item totals are consistent after refresh.
- No cross-user data leakage.

---

## Phase 4 - Dashboard Real Data Integration
Purpose: remove hard-coded arrays and render real metrics from backend.

### Tasks
1. Create dashboard summary/read APIs:
   - total clients
   - total entries this month
   - pending compliance count
   - high-risk clients count
   - recent client activity
   - recent entries
   - risk summary
   - compliance percentages
2. Replace `CLIENT_ACTIVITY_DATA` and `RECENT_ENTRIES_DATA` in dashboard JS.
3. Keep same UI components and interactions, only swap data source.

### Target Files
- `safebooks/services/dashboard_service.py`
- `safebooks/views.py`
- `safebooks/urls.py`
- `templates/base/dashboard.html`

### Acceptance Criteria
- Dashboard values change based on real DB records.
- Filters/search still work with real data.
- Empty states display correctly with no data.

---

## Phase 5 - Analytics (Only After Phases 1-4)
Purpose: implement analytics using trusted, persisted data.

### Suggested First Analytics Scope
1. Revenue trend by month.
2. Expense trend by month.
3. Compliance trend by period.
4. Risk distribution over time.

### Acceptance Criteria
- Analytics page renders from backend endpoints.
- Numbers match dashboard and record totals.

---

## 4. Recommended Implementation Order (Practical)
1. Phase 1 (auth hardening/session guard)
2. Phase 2 (clients backend)
3. Phase 3 (financial records backend)
4. Phase 4 (dashboard real data)
5. Phase 5 (analytics)

This order minimizes rework and keeps your current UI valuable while backend becomes real.

---

## 5. Testing Checklist Per Phase
- Run `python manage.py check`
- Run migrations and verify schema
- Create data manually and verify page refresh persistence
- Verify ownership isolation (user A cannot read user B data)
- Verify invalid payload handling returns clean errors

---

## 6. Immediate Next Task (Start Here)
Start Phase 1 first:
- implement server-side session login/logout
- protect dashboard, clients, and financial-record routes

After that, move immediately to Phase 2 (Clients backend CRUD), one file/table at a time.

This gives you the cleanest foundation for everything after, including Analytics.
