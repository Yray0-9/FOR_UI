# SafeBooks Bookkeeper Usability Feature Proposal

## Purpose

This document lists practical improvements for the bookkeeper side of SafeBooks. The goal is not to add more complicated features, but to make the system easier, clearer, and less stressful for bookkeepers who may not be technical users.

This proposal is meant for user feedback first. Each item should be discussed with real bookkeepers before implementation.

## Current Observation

The major bookkeeper features are already present:

- Client directory
- Client details
- Financial record entry
- Client-specific analytics and forecasting
- Client-specific report preview
- Dashboard work queue
- Profile and settings
- Security controls for client details access
- Client email notification after adding a financial record

The remaining opportunity is not simply "more features." The better direction is to make the existing workflow feel more guided, familiar, and safer for daily bookkeeping work.

## Main Usability Direction

SafeBooks should guide bookkeepers through a normal workday:

1. See which clients need attention.
2. Open one client.
3. Add or review records for the correct period.
4. Confirm that records were saved.
5. Generate or preview a client-specific report if needed.
6. Notify or follow up with the client when appropriate.

The system should avoid broad all-client views that may overwhelm the user unless the page is clearly designed as an overview.

## Recommended Improvements

### 1. Client Work Checklist

Priority: High

Problem:
Bookkeepers may know that a client needs attention, but may not immediately know what the next action should be.

Suggested feature:
Add a simple checklist panel inside Client Details or the Financial Records Client page.

Example checklist:

- Client details complete
- Email available for notifications
- Current period record added
- Tax line items checked
- Report ready for preview

Why this helps:
It gives bookkeepers a clear sense of progress without forcing them to understand system logic.

Implementation caution:
Keep this as guidance only at first. Do not block the user from saving records.

User feedback question:
Would this checklist help you know what to do next, or would it feel unnecessary?

### 2. Missing Client Information Reminder

Priority: High

Problem:
Some features depend on client details, especially email notification. If the client email is missing, SafeBooks correctly skips the email, but the bookkeeper may not notice.

Suggested feature:
Show a small non-intrusive reminder on Client Details when useful fields are missing.

Examples:

- Email not provided, client notifications will be skipped.
- Permit number not provided.
- ORUS account not provided.

Why this helps:
It prevents confusion later when a feature behaves correctly but silently skips missing information.

Implementation caution:
Do not show this as an error. Missing email or ORUS account may be normal.

User feedback question:
Which missing information should SafeBooks remind you about, and which ones should it ignore?

### 3. Record Save Confirmation Summary

Priority: High

Problem:
After saving a financial entry, bookkeepers may want quick confirmation of what was saved without reopening the record.

Suggested feature:
After adding or editing a record, show a small confirmation summary.

Example:

- Record saved for July 2026
- Schedule: Monthly
- Total: PHP 5,936.13
- Client email notification: Sent / Skipped

Why this helps:
It makes the system feel reliable and reduces doubt.

Implementation caution:
Keep this as a toast or compact panel, not a large modal.

User feedback question:
Would a short save summary be useful after adding records?

### 4. Period Readiness Indicator

Priority: Medium

Problem:
Bookkeepers may need to quickly know whether a client has records for the current month, quarter, or year.

Suggested feature:
Use a simple readiness indicator on Client Details and Financial Records:

- Current period filed
- No entry this period
- Quarterly schedule expected later
- Annual record pending

Why this helps:
It makes the system closer to a work tracker instead of only a data table.

Implementation caution:
Do not overpromise legal/tax compliance. Use wording like "record status" instead of "tax compliant."

User feedback question:
Do bookkeepers think by month only, or by monthly/quarterly/annual schedules?

### 5. Client-Specific Report Shortcut

Priority: Medium

Problem:
The standalone Reports page is still a remove-candidate because broad reports can confuse users with many clients.

Suggested feature:
Keep report generation inside Client Details only, with a clear client-specific report preview.

Possible label:
Preview Client Report

Why this helps:
Bookkeepers stay in one client context and avoid accidentally generating the wrong scope.

Implementation caution:
Do not delete report APIs until the final page decision is confirmed.

User feedback question:
Do users need a separate Reports page, or is client-specific reporting enough?

### 6. Notification Preference for Client Emails

Priority: Medium

Problem:
Automatic client email notifications are useful, but some bookkeepers may want control over when clients are notified.

Suggested feature:
Add a setting:

- Automatically email client when a financial record is added

Optional later version:
Allow bookkeeper to choose per record:

- Save only
- Save and notify client

Why this helps:
It keeps the feature helpful without surprising users.

Implementation caution:
The backend already has a global deployment toggle. A user-facing preference would need a model field and tests.

User feedback question:
Should client notification be automatic, optional per record, or controlled in settings?

### 7. Friendly Empty States

Priority: Medium

Problem:
Some pages already have empty states, but the wording can still be more task-based.

Suggested feature:
Use empty states that tell the bookkeeper what to do next.

Examples:

- No records yet for this period. Add the first entry when this client's record is ready.
- No client selected. Choose a client to review records.
- No forecast yet. Add more records to improve projections.

Why this helps:
It reduces pressure when the system has no data.

Implementation caution:
Keep text short. Avoid long explanations.

User feedback question:
Which empty screens feel confusing during daily use?

### 8. Profile and Settings Completion

Priority: Medium

Problem:
Some Profile and Settings areas still include planned/preview-only controls. These can make users think something is broken.

Suggested feature:
Finish or remove planned controls that are not ready.

Observed areas:

- Profile planned buttons
- Notification settings preview-only controls
- Appearance save behavior should remain clear

Why this helps:
Users should not see controls that appear available but do not fully work.

Implementation caution:
If the feature is not ready, hide it or clearly mark it as unavailable without making the page feel incomplete.

User feedback question:
Which settings do bookkeepers actually want to control?

### 9. Record Entry Templates

Priority: Future

Problem:
Many clients may use similar transaction details each month or quarter.

Suggested feature:
Allow a bookkeeper to save a small template for repeated Sales or Expenses details.

Example:

- Monthly sales detail
- Quarterly expense detail

Why this helps:
It reduces repeated typing and lowers the chance of missing common transaction details.

Implementation caution:
This should come after current record entry remains stable. Tax details should remain manually selected from the proper type/code list.

User feedback question:
Do users repeat the same line items often enough for templates to be worth it?

### 10. Gentle Error Prevention

Priority: Future

Problem:
Bookkeepers may accidentally enter the wrong period, duplicate records, or forget a line item.

Suggested feature:
Add soft warnings before saving.

Examples:

- A record already exists for this period.
- This client usually has quarterly tax entries, but none were added.
- Amount is unusually high compared with the last entry.

Why this helps:
It catches mistakes without blocking legitimate work.

Implementation caution:
Warnings must be soft and dismissible. Do not prevent saving unless the data is invalid.

User feedback question:
Which mistakes happen most often during manual record entry?

## Recommended Implementation Order

### Phase 1: Low-Risk Guidance Improvements

Do first because these mostly improve clarity:

1. Missing Client Information Reminder
2. Record Save Confirmation Summary
3. Friendly Empty States

Status: Implemented and checked.

Implementation notes:

- Client Details now shows a quiet reminder when email, permit number, or ORUS account is missing.
- Financial Records now shows a compact save summary after adding or editing an entry.
- Empty states now explain the next useful action in friendlier bookkeeping language.

Verification:

- `python manage.py check`
- `python manage.py test safebooks.tests.test_financial_records_api safebooks.tests.test_clients_api safebooks.tests.test_dashboard_summary_api`

### Phase 2: Workflow Support

Do after user feedback:

1. Client Work Checklist
2. Period Readiness Indicator
3. Client-specific report shortcut refinement

Status: Implemented and revised after UI review.

Implementation notes:

- Client Details now has a smaller Record Schedule Status panel that shows the next expected record period from the client's saved record history.
- The status uses the analytics API instead of guessing from the UI.
- The status now follows all saved record frequencies for the client: monthly, quarterly, and annual records are checked separately so mixed schedules do not overwrite each other.
- The status does not jump straight to the current month if older records are being encoded. For example, a January monthly record points to February as the next expected monthly record.
- Quarterly records use the quarter-end month as the expected checkpoint. For example, a January or February quarterly record points to March, while a March quarterly record points to June.
- Duplicate Records and Preview Report shortcuts were removed from this panel because those actions already exist in the client action bar.
- Missing client detail reminders stay in Client Overview only, so the same warning is not repeated in two places.

Verification:

- `python manage.py check`
- `python manage.py test safebooks.tests.test_analytics_summary_api`

### Phase 3: User-Controlled Behavior

Do after the workflow is accepted:

1. Notification preference for client emails
2. Finish or remove preview-only profile/settings controls

Status: Started.

Implementation notes:

- Settings now includes a real Client Record Emails toggle instead of preview-only notification controls.
- When enabled, SafeBooks emails the client's saved email address after a new financial record is added.
- When disabled, the record still saves normally and the save summary reports that the client email was skipped.
- This setting does not use ORUS account data. It only affects the client's saved email address.

Verification:

- `python manage.py check`
- `python manage.py test safebooks.tests.test_financial_records_api safebooks.tests.test_client_details_access_security`

### Phase 4: Productivity Features

Do later because they need more testing:

1. Record Entry Templates
2. Gentle Error Prevention

Status: Started.

Implementation notes:

- Financial record Add/Edit modals now include small common transaction detail starters.
- The starters only add editable rows for Sales and Expenses.
- Sales and Expenses starters leave the description and amount blank so the bookkeeper still writes the exact transaction wording.
- Tax starters were intentionally not added because tax records should use the specific BIR form/type selected by the bookkeeper.
- The feature does not auto-save or change calculations. Bookkeepers still review the type/code, description, and amount before saving.
- If the modal only has one blank transaction detail row, the starter replaces that blank row to avoid clutter.
- Add/Edit entry forms now show a gentle warning when the selected date and frequency already match another saved record for the client.
- The duplicate warning does not block saving because some clients may intentionally have multiple entries in the same period.

Verification:

- `python manage.py check`
- `python manage.py test safebooks.tests.test_financial_records_api`

### Phase 5: Client-Specific Reporting Flow

Do after the record entry workflow is stable:

1. Keep report preview inside Client Details
2. Reduce access to the broad standalone Reports page
3. Keep report APIs available for the client report modal

Status: Implemented and checked.

Implementation notes:

- Client Details now uses a direct Preview Report button that opens the client-specific report modal.
- The old `/reports/` page now redirects authenticated bookkeepers back to Clients with guidance to open a client first.
- The report print-layout API was not removed because the Client Details report preview still depends on it.
- The old Reports template is left in the codebase for now until the final page-removal decision is confirmed.

Example:

- If a bookkeeper wants a report for ROBISO, they open ROBISO in Client Details and click Preview Report.
- If they manually visit `/reports/`, SafeBooks sends them back to Clients instead of showing an all-client report workspace.

Verification:

- `python manage.py check`
- `python manage.py test safebooks.tests.test_reports_page safebooks.tests.test_reports_print_layout_api safebooks.tests.test_client_details_access_security`

### Phase 6: Profile And Settings Cleanup

Do after the client-specific report flow is stable:

1. Remove Profile controls that only show "planned soon"
2. Route account actions to working Settings sections
3. Replace fake Profile activity with real account status information

Status: Implemented, simplified, and checked.

Implementation notes:

- Profile is focused on the signed-in bookkeeper's identity and editable personal details.
- A single Account Settings link replaces repeated password, notification, preference, and account-request controls.
- Password, notification, security, appearance, and deactivation controls remain available in their proper Settings sections.
- The duplicated profile completion, account-status snapshot, preference snapshot, and account-request panels were removed.
- Unused Profile JavaScript for deleted snapshots and completion calculations was removed.

Example:

- A bookkeeper uses Profile to update their name, username, email, or location. For password or notification changes, they use the single Account Settings button.

Verification:

- `python manage.py check`
- `python manage.py test safebooks.tests.test_auth_api safebooks.tests.test_google_auth_flow`

### Phase 7: Contextual Empty States

Do after Profile and Settings are no longer showing placeholder controls:

1. Review empty states that still feel unclear
2. Make the message explain the next useful action
3. Avoid extra recovery buttons when the existing search or filter controls already handle clearing

Status: Implemented and checked.

Implementation notes:

- Financial Records now explains what to do when there are no clients ready for records.
- When search or filters hide all rows, the page now explains which control to clear without adding a duplicate button.
- The change is UI-only and does not alter record, client, or report data.

Example:

- If a bookkeeper searches for a TIN and nothing appears, SafeBooks now says no client matches that name or TIN and reminds them to clear the search field.

Verification:

- `python manage.py check`
- `python manage.py test safebooks.tests.test_financial_records_api`

### Phase 8: Bookkeeper Audit Log

Added after adviser feedback about database accountability.

Status: Implemented and checked.

Implementation notes:

- Added a dedicated `bookkeeper_audit_logs` database table owned by each bookkeeper account.
- Added an Audit Log page to the bookkeeper navigation with search, sorting, and filters for Clients, Financial Records, Account, and Security.
- Successful client add/update/close and financial record add/update/delete actions are recorded.
- Successful profile, password, login-alert, client-details-lock, client-email preference, and account-deactivation request changes are recorded.
- Page visits, searches, failed validation, and report previews are not recorded, keeping the history focused on meaningful changes.
- Passwords, ORUS credentials, email passwords, authenticator codes, and complete request payloads are never saved in audit metadata.
- Every API query is restricted to the signed-in bookkeeper, so one bookkeeper cannot view another bookkeeper's activity.

Example:

- If a bookkeeper updates a client's July monthly record, the Audit Log shows when the record was updated and which client it belonged to. It does not expose the client's passwords or private account credentials.

Verification:

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test safebooks.tests.test_bookkeeper_audit_log_api safebooks.tests.test_clients_api safebooks.tests.test_financial_records_api safebooks.tests.test_client_details_access_security safebooks.tests.test_auth_api`

## What Not To Do Yet

Avoid these unless users clearly ask for them:

- Large all-client analytics dashboards
- Complex tax compliance scoring
- Too many charts
- Too many required fields
- Mandatory step-by-step wizards for every action
- Blocking users from saving because of incomplete optional details

## Questions To Ask Bookkeepers

Use these questions when proposing improvements:

1. When you open SafeBooks, what do you want to see first?
2. Do you prefer a checklist, or do you prefer only tables and buttons?
3. Should SafeBooks remind you when a client has no email address?
4. Should client email notifications be automatic or optional?
5. What information do you always check before saving a monthly or quarterly record?
6. Which part of adding a financial entry feels easiest to make a mistake?
7. Do you need a separate Reports page, or is reporting inside Client Details enough?
8. What words feel too technical or confusing in the current system?

## Success Criteria

These improvements are successful if:

- Bookkeepers know the next action without asking for help.
- Optional missing data is visible but not alarming.
- Record saving feels confirmed and trustworthy.
- Client email behavior is understandable.
- Reports and analytics remain client-specific.
- The system avoids redundant pages and repeated text.
- New features reduce work instead of adding pressure.
