# Admin System Settings Plan (v2)

## 1) Context Review (Current Admin Features)
- Admin Home: KPI counts (total, pending, active, high load), approval readiness buckets, load snapshot (top 5), quick actions. Data comes from `admin_dashboard_service` with high load threshold = 150.
- Approvals: list/search/sort/filter, approve/reject with modal and optional rejection note, summary counts and today counts.
- Bookkeepers: directory list/search/sort/filter, status summary, client load summary, actions (deactivate/reactivate toggle, delete).
- Audit Log: removed from admin navigation and routes.

## 2) Objective
Provide a lean, admin-focused settings page that supports approvals, bookkeeper monitoring, and admin security without exposing client data or confusing controls.

## 3) Guiding Principles
- Only show settings that map to real admin workflows.
- Avoid auto-suspension or punitive automation.
- Keep defaults safe and reversible.
- Use clear labels; no jargon (e.g., remove IP allowlist).
- Use email notifications only; in-app notifications are out of scope for now.

## 4) Recommended Settings Sections

### 4.1 Approval Governance
Purpose: control approval workflow behavior.
- Default approval mode: Manual (fixed).
- Approval SLA target: 24/48/72 hours.
- Auto-approve: planned but disabled until policy and testing are ready.

### 4.2 Bookkeeper Monitoring
Purpose: highlight accounts that need attention.
- Flag inactive accounts: toggle (flag only, no auto-deactivate).
- Inactivity reminder window: 30/60/90 days.
- Client load alert threshold: 50/100/150 clients.
  - Note: Admin Home high load KPI should use this threshold (default 150).

### 4.3 Notification Policy (Admin Controlled)
Purpose: define when bookkeepers receive status updates.
- Notify on approval: toggle (email only).
- Notify on rejection: toggle (email only).
- Notification channel: Email only (remove in-app).
- Admin login alerts: toggle (email to admin).

### 4.4 Admin Security
Purpose: reduce risk during sensitive actions.
- Admin session timeout: 30/60/120 minutes.
- Re-auth for critical actions: toggle (approve, reject, delete).
- Remove IP allowlist (too advanced for current scope).

### 4.5 Save and Reset
Purpose: controlled rollout.
- Save settings: enabled once backend wiring is ready.
- Reset to defaults: available after settings persistence exists.

## 5) Data Model Proposal (Future)
Create a `SystemSetting` table (single row) or `AdminSetting` JSON table.
Suggested fields:
- approval_mode (manual)
- approval_sla_hours (24/48/72)
- flag_inactive (bool)
- inactivity_window_days (30/60/90)
- client_load_threshold (50/100/150)
- notify_on_approval (bool)
- notify_on_rejection (bool)
- notify_channel_email (bool)
- admin_login_alerts (bool)
- admin_session_timeout_minutes (30/60/120)
- reauth_for_critical (bool)

## 6) API Plan (Future)
- GET `/api/admin/settings/` -> current settings
- PUT `/api/admin/settings/` -> update settings
- Validation: only allow supported values; reject anything else

## 7) UI Plan (Admin System Settings)
- Remove IP allowlist field.
- Replace in-app channel with Email only.
- Rename "Suspend after inactivity" to "Flag inactive accounts".
- Add helper copy (short, one line max) where needed.
- Keep controls disabled until backend is ready.

## 8) Integration Points
- Admin Home KPI (high load) should read `client_load_threshold`.
- Approvals page could show SLA target in a small hint.
- Bookkeepers page can highlight rows that exceed `client_load_threshold`.
- Email notifications (approval/rejection) will be wired later.

## 9) Non-Goals (For Now)
- No audit log.
- No in-app notification system.
- No auto-suspension or auto-approval.
- No client data exposure in settings.

## 10) Acceptance Criteria
1. Settings page shows only admin-relevant controls.
2. No confusing or unused items (IP allowlist, in-app notifications).
3. Labels match admin workflows (flag vs suspend).
4. Settings can map to existing admin dashboards when wired.

## 11) Collaboration Checkpoint (You Do / I Do)
- You: Confirm section list and default values.
- I do: Update UI labels and wire backend when approved.

## 12) Status
- Draft (ready for review)
