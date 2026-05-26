# System Architecture

The SafeBooks system follows a three-tier, web-based client-server architecture that separates presentation, application, and data responsibilities to keep the system organized and maintainable [16]. The platform is built on Django and provides centralized handling of authentication, business logic, and financial record processing.

The presentation layer is the Web Browser UI used by bookkeepers and administrators. It renders the main pages (login, dashboard, clients, financial records, analytics, reports, settings, and the admin area) and communicates with the application server using HTTP/REST for both page loads and JSON-based updates [18].

The application layer is the Django application server. It manages authentication and approvals, client management, financial records, analytics and reports, and settings, and it triggers email verification and login alerts through the email backend [17].

The data layer is a relational database accessed through the Django ORM. The current implementation uses SQLite for local development and supports PostgreSQL for production via environment configuration, with only one database engine active at a time.

```mermaid
flowchart TB
	subgraph Presentation Layer
		User[Bookkeeper / Admin]
		UI[Web Browser UI]
		User <--> UI
	end

	subgraph Application Layer (Django)
		App[Application Server\nAuth and Approvals\nClient Management\nFinancial Records\nAnalytics and Reports\nSettings]
	end

	subgraph Data Layer
		DB[(PostgreSQL (production) / SQLite (dev))]
	end

	subgraph Supporting Services
		Email[Email Backend\nSMTP / Console]
	end

	UI -->|HTTP / REST| App
	App -->|Django ORM| DB
	App --> Email
```

**Figure 5: SafeBooks System Architecture (Current Implementation)**

In the operational flow, users interact with the Web Browser UI to manage client profiles and financial records. Requests are routed to the Django application server, which validates the input, applies business rules, and persists data through the ORM before returning HTML pages or JSON responses. When required, the email backend sends verification or login alert messages to the user.

## References

[16] A. Hussain and P. K. Sharma, "Deployment of Web Application in LAN based 3 Tier Architecture," International Journal of Scientific Research in Computer Science, Engineering and Information Technology (IJSRCSEIT), vol. 5, no. 6, pp. 341-345, Nov.-Dec. 2019. [Online]. Available: https://doi.org/10.32628/CSEIT195661. [Accessed: May 2026].

[17] H. Zhang, "Architecture of Network and Client-Server model," arXiv:1307.6665 [cs.NI], Jul. 2013. [Online]. Available: https://arxiv.org/abs/1307.6665. [Accessed: May 2026].

[18] M. Varga, "Web Programming and Multi-Tier Architecture of Web Applications," TEM Journal, vol. 13, no. 4, pp. 3286-3294, 2024. [Online]. Available: https://www.temjournal.com/content/134/TEMJournalNovember2024_3286_3294.pdf. [Accessed: May 2026].


## Diagram Prompt (Image Only)

Create a clean, professional system architecture diagram for the SafeBooks web application. Output image only, no text outside the diagram. Title at the top: "SafeBooks System Architecture". Use a white background, thin gray borders, and a simple color palette (soft blue for presentation, soft green for application, soft gray for data, light orange for supporting services). Use rounded rectangles for components and arrows for flow.

Layout:
- Presentation Layer on the left.
- Application Layer centered.
- Data Layer at the bottom.
- Supporting Services on the right.

Presentation Layer:
- User icons labeled "Bookkeeper" and "Admin".
- A "Web Browser UI" box.
- A double-headed arrow between the users and the Web Browser UI.

Application Layer (Django):
- One inner box labeled "Application Server" with a short list inside: "Auth and Approvals", "Client Management", "Financial Records", "Analytics and Reports", "Settings".

Data Layer:
- A database cylinder labeled "PostgreSQL (production) / SQLite (dev)".

Supporting Services:
- An "Email Backend" box with subtext "SMTP / Console".

Connections:
- Arrow labeled "HTTP / REST" from Web Browser UI to Application Server.
- Arrow labeled "Django ORM" from Application Server to the database.
- Arrow from Application Server to Email Backend.

Rules:
- Keep spacing aligned and avoid crossing lines.
- Do not add extra request or response boxes.
- Do not include any external services not in the current SafeBooks project.


## Next Section


# Functional and Non-Functional Requirements

The SafeBooks system supports core bookkeeping tasks centered on client profiles, financial records, analytics, and reporting. Users can capture period-based records with line items, compute totals, and review summaries through dashboards and analytics views. Search by client name or TIN helps locate records quickly, while reports provide printable outputs for review and handover.

Quality attributes focus on usability, security, data integrity, and consistent performance. The system uses authenticated access with email verification and an approval flow, validates user input, and keeps data scoped to each bookkeeper. It is designed to run reliably in standard web browsers and remain maintainable through modular services and ORM-based data access.

## Functional Requirements

1. Provide user authentication with email verification, session management, and admin approval for new bookkeeper accounts.
2. Allow admins to approve, reject, deactivate, and reactivate bookkeeper accounts.
3. Manage client profiles with BIR-related fields (TIN, trade name, location, permit) and a risk level.
4. Enforce unique TIN values and validate required client fields and email formats.
5. Record financial entries by period (monthly, quarterly, annually) with line items and totals.
6. Support line-item calculations (percent, add, subtract, multiply, divide) and store computed results.
7. Enable search and filtering by client name or TIN across client lists and analytics views.
8. Provide dashboard summaries with recent entries, compliance status (filed, pending, late), and risk counts.
9. Generate analytics summaries with sales, expenses, tax totals, monthly trends, and a forecast trend indicator.
10. Produce client reports and printable layouts for selected date ranges.

## Non-Functional Requirements

1. Usability: provide clear navigation and consistent forms for data entry and review.
2. Security: protect data through authentication, session handling, and email verification, with access scoped per bookkeeper.
3. Data integrity: validate required fields, dates, and numeric amounts, and enforce unique TIN constraints.
4. Performance: return dashboard and analytics summaries with minimal delay under typical workloads.
5. Reliability: maintain stable operation for routine data entry, updates, and reporting.
6. Compatibility: run on modern desktop or laptop web browsers without special plugins.
7. Maintainability: keep business logic in modular services with ORM-managed models for easier updates.
8. Scalability: handle growing numbers of clients and records without major performance degradation.


## Next section

# Use Case Diagram

The Use Case Diagram, shown in Figure 6, summarizes how the Bookkeeper and the System Administrator interact with the SafeBooks system and defines the system boundary for core tasks. The Bookkeeper is the primary user who performs day-to-day bookkeeping operations, while the System Administrator oversees access and account governance.

Bookkeeper use cases focus on account access and record management: register/login/logout with email verification, manage client profiles, manage financial records by period with line items and calculations, search clients by name or TIN, review dashboard compliance status, view analytics with trend and forecast summaries, generate reports, and update account settings. Include relationships are shown only for mandatory sub-steps in financial records (selecting a period and recording line items) and for the core administrative actions under account management (approve, reject, deactivate, reactivate, delete).

Administrator use cases cover governance and oversight: review and approve registrations, manage bookkeeper accounts (approve, reject, deactivate, reactivate, delete), view the admin dashboard, and maintain system settings.

**Actual Use Case Diagram (Attached image)**

Figure 6: Use Case Diagram

In operational use, bookkeepers log in, maintain client profiles, encode periodic financial records, and review dashboard and analytics results before generating reports. Administrators review registrations, manage bookkeeper account status, and maintain system settings to keep access controlled and data processing consistent.

## Use Case Diagram Layout (Text Guide)

```
Bookkeeper                                  SafeBooks System                                System Administrator
	|                                             |                                                |
	|----> (Authenticate Account)                 |                                                |
	|----> (Manage Client Profiles)               |                                                |
	|----> (Manage Financial Records)             |                                                |
	|            |--<<include>> (Select Period)   |                                                |
	|            |--<<include>> (Record Line Items)|                                               |
	|----> (Search Clients by TIN)                |                                                |
	|----> (View Dashboard)                       |                                                |
	|----> (View Analytics)                       |                                                |
	|----> (Generate Reports)                     |                                                |
	|----> (Manage Account Settings)              |                                                |
	|                                             |----> (Review Bookkeeper Registrations) <-------|
	|                                             |----> (Manage Bookkeeper Accounts)      <-------|
	|                                             |            |--<<include>> (Approve Bookkeeper)  |
	|                                             |            |--<<include>> (Reject Bookkeeper)   |
	|                                             |            |--<<include>> (Deactivate Bookkeeper)|
	|                                             |            |--<<include>> (Reactivate Bookkeeper)|
	|                                             |            |--<<include>> (Delete Bookkeeper)    |
	|                                             |----> (View Admin Dashboard)            <-------|
	|                                             |----> (Manage System Settings)          <-------|

System boundary: "SafeBooks System" encloses all use cases listed above.
Include relationships appear under financial records and admin account management. No extend relationships are used.
```

## Use Case Diagram Prompt (Image Only)

Create a clean UML use case diagram for the SafeBooks system. Output image only, no text outside the diagram. Title at the top: "SafeBooks Use Case Diagram". Use a white background, thin black or gray lines, and standard UML use case styling (stick-figure actors, system boundary rectangle, oval use cases). Use <<include>> only for mandatory sub-steps and do not use <<extend>>.

Actors:
- Bookkeeper (left side).
- System Administrator (right side).

System boundary label: "SafeBooks System".

Use cases connected to Bookkeeper:
- Authenticate Account
- Manage Client Profiles
- Manage Financial Records
- Search Clients by TIN
- View Dashboard
- View Analytics
- Generate Reports
- Manage Account Settings

Included use cases (dashed arrows with <<include>>):
- Manage Financial Records includes Select Period.
- Manage Financial Records includes Record Line Items.
- Manage Bookkeeper Accounts includes Approve Bookkeeper.
- Manage Bookkeeper Accounts includes Reject Bookkeeper.
- Manage Bookkeeper Accounts includes Deactivate Bookkeeper.
- Manage Bookkeeper Accounts includes Reactivate Bookkeeper.
- Manage Bookkeeper Accounts includes Delete Bookkeeper.

Use cases connected to System Administrator:
- Review Bookkeeper Registrations
- Manage Bookkeeper Accounts
- View Admin Dashboard
- Manage System Settings

Layout rules:
- Place Bookkeeper on the left and System Administrator on the right.
- Place use cases inside the system boundary and group bookkeeper-related use cases on the left half, admin use cases on the right half.
- Use straight association lines from each actor to their use cases.
- Keep spacing even and avoid crossing lines.


# Next Section

# Context Flow Diagram

The Context Flow Diagram, shown in Figure 7, presents a high-level view of the SafeBooks system as a single process and shows how data flows between the system and external entities. The primary entities are the Bookkeeper and the System Administrator, who provide inputs and receive outputs through the system boundary.

At the context level, the Bookkeeper sends login credentials, client profile data (TIN, trade name, location, permit), financial record entries by period with line items and amounts, and report requests. The system returns an authentication result, combined dashboard/analytics summaries, and report or printable outputs. This keeps the diagram focused on the core exchanges without listing every screen-level response.

The System Administrator sends login credentials, account actions (approve/reject, deactivate, reactivate, delete), and system settings updates. The system returns bookkeeper registration lists and admin dashboard metrics for monitoring and oversight.

**Actual Context Flow Diagram (Attached image)**

Figure 7: Context Flow Diagram

In operational use, the system receives data inputs from both roles, processes and stores them through validated workflows, and provides summarized outputs for decision support, reporting, and account governance.

## Context Flow Diagram Layout (Text Guide)

```
Bookkeeper                       SafeBooks System                        System Administrator
	|                                   |                                       |
	|-- Login Credentials ------------->|                                       |
	|-- Client Profile Data ----------->|                                       |
	|-- Financial Record Entries ------>|                                       |
	|-- Report Request ---------------->|                                       |
	|                                   |<------------- Login Credentials ------|
	|                                   |<------------- Account Actions --------|
	|                                   |<------------- System Settings Updates |
	|<------------- Auth Result --------|                                       |
	|<------------- Dashboard/Analytics Summary -------------------------------|
	|<------------- Reports/Printouts --|                                       |
	|                                   |------------- Bookkeeper Lists ------->|
	|                                   |------------- Admin Metrics ---------->|

System boundary: "SafeBooks System" is a single process with external entities on both sides.
```

## Context Flow Diagram Prompt (Image Only)

Create a clean DFD Level 0 (Context Flow Diagram) for the SafeBooks system. Output image only, no text outside the diagram. Title at the top: "SafeBooks Context Flow Diagram". Use a white background, thin black or gray lines, and simple boxes with clear labels. Place a single central process labeled "SafeBooks System" and two external entities: "Bookkeeper" on the left and "System Administrator" on the right.

Data flows from Bookkeeper to SafeBooks System:
- Login Credentials
- Client Profile Data (TIN, trade name, location, permit)
- Financial Record Entries (period, line items, amounts)
- Report Request

Data flows from SafeBooks System to Bookkeeper:
- Authentication Result
- Dashboard/Analytics Summary
- Reports / Printable Outputs

Data flows from System Administrator to SafeBooks System:
- Login Credentials
- Account Actions (approve/reject, deactivate/reactivate/delete)
- System Settings Updates

Data flows from SafeBooks System to System Administrator:
- Bookkeeper Registration List
- Admin Dashboard Metrics

Layout rules:
- Keep the system process centered with balanced spacing.
- Use straight arrows with labels for each data flow.
- Avoid crossing lines and keep labels readable.


# Next Section

# Level 1 Data Flow Diagram
The Level 1 Data Flow Diagram, shown in Figure 8, decomposes the SafeBooks system into internal processes and data stores for client profiles, financial records, analytics, reporting, and administrative governance. It details how data moves between processes and stores within the system boundary while keeping external entities as the Bookkeeper and the System Administrator.

**Actual Level 1 Data Flow Diagram (Attached image)**

Figure 8: Level 1 Data Flow Diagram

This diagram emphasizes the three core data stores of the application architecture: user accounts (D1), client profiles (D2), and financial ledgers and transactions (D3), which is the largest data structure containing ledgers, periods, and line items. System configurations are treated as internal settings and omitted at Level 1 to keep the DFD focused and readable.

## Level 1 Data Flow Diagram Layout (Text Guide)

```
External Entities:
- Bookkeeper (left)
- System Administrator (right)

Processes (center):
1.0 Authenticate and Route User
2.0 Manage Client Directories
3.0 Process Financial Transactions
4.0 Generate Dashboard Analytics
5.0 Generate Financial Reports
6.0 Administer User Accounts

Data Stores (right side or bottom):
D1 User Accounts
D2 Client Profiles
D3 Financial Ledgers & Records

Core Data Flows (Every directional arrow MUST have a label):
- Bookkeeper -> 1.0: "Login Credentials"
- 1.0 -> Bookkeeper: "Authentication Result"
- System Administrator -> 1.0: "Login Credentials"
- 1.0 -> System Administrator: "Authentication Result"

- Bookkeeper -> 2.0: "Client Profile Data"
- 2.0 -> D2: "Store New/Updated Profiles"
- D2 -> 2.0: "Retrieve Client Profiles"

- Bookkeeper -> 3.0: "Financial Entries (Periods, Lines)"
- 3.0 -> D3: "Store Records & Ledgers"
- D3 -> 3.0: "Retrieve Financial Data"

- Bookkeeper -> 4.0: "Dashboard/Analytics Request"
- 4.0 -> Bookkeeper: "Dashboard/Analytics Summary"
- D2 -> 4.0: "Client Risk & Status Data"
- D3 -> 4.0: "Aggregated Financial Totals"

- Bookkeeper -> 5.0: "Report Request"
- 5.0 -> Bookkeeper: "Reports & Print Layouts"
- D2 -> 5.0: "Client Details for Report"
- D3 -> 5.0: "Financial Data for Report"

- System Administrator -> 6.0: "Account Governance Actions"
- 6.0 -> System Administrator: "Account Status Results"
- 6.0 -> D1: "Save Account Updates"
- D1 -> 6.0: "Retrieve User Accounts"

System boundary: "SafeBooks System" encloses all processes and data stores.
```

## Level 1 Data Flow Diagram Prompt (Image Only)

Create a clean DFD Level 1 diagram for the SafeBooks system. Output image only, no text outside the diagram. Title at the top: "SafeBooks Level 1 Data Flow Diagram". Use a white background, thin black or gray lines, and classic DFD notation: external entities as rectangles, processes as numbered rounded rectangles, and data stores as open-ended rectangles labeled D1 to D3. Use clear, horizontal labels for data flows.

External Entities:
- Bookkeeper (left)
- System Administrator (right)

Processes (center):
1.0 Authenticate and Route User
2.0 Manage Client Directories
3.0 Process Financial Transactions
4.0 Generate Dashboard Analytics
5.0 Generate Financial Reports
6.0 Administer User Accounts

Data Stores:
D1 User Accounts
D2 Client Profiles
D3 Financial Ledgers & Records

Required Data Flows (CRITICAL: Every single arrow must have exactly this label text attached to it. Do not draw any unlabelled lines. Use separate unidirectional arrows instead of double-headed arrows for data store operations):

- Bookkeeper -> 1.0: "Login Credentials"
- 1.0 -> Bookkeeper: "Authentication Result"
- System Administrator -> 1.0: "Login Credentials"
- 1.0 -> System Administrator: "Authentication Result"

- Bookkeeper -> 2.0: "Client Profile Data"
- 2.0 -> D2: "Store New/Updated Profiles"
- D2 -> 2.0: "Retrieve Client Profiles"

- Bookkeeper -> 3.0: "Financial Entries"
- 3.0 -> D3: "Store Records & Ledgers"
- D3 -> 3.0: "Retrieve Financial Data"

- Bookkeeper -> 4.0: "Dashboard/Analytics Request"
- 4.0 -> Bookkeeper: "Dashboard/Analytics Summary"
- D2 -> 4.0: "Client Risk Data"
- D3 -> 4.0: "Aggregated Totals"

- Bookkeeper -> 5.0: "Report Request"
- 5.0 -> Bookkeeper: "Reports / Print Layout"
- D2 -> 5.0: "Client Details"
- D3 -> 5.0: "Financial Details"

- System Administrator -> 6.0: "Account Governance Actions"
- 6.0 -> System Administrator: "Account Status Results"
- 6.0 -> D1: "Save Account Updates"
- D1 -> 6.0: "Retrieve User Accounts"

Layout rules:
- Keep processes centered, entities on far left/right, and data stores aligned to the right.
- Use only one Bookkeeper entity and one System Administrator entity.
- Avoid crossing lines and keep labels readable.
- Keep spacing consistent and uncluttered.

# Next section is this

# System Design
This section outlines the SafeBooks system design and maps the requirements to the actual workflow. The design organizes the application into modules for authentication and approvals, client profile management, financial record entry by period with line items, analytics and reporting, and administrative account governance. It reflects the two user roles and the sequence from login to data capture, analysis, and report outputs.

It documents the database schema and relationships that support accounts, clients, and financial records, along with the validation rules that protect data quality such as unique TIN values, required fields, and numeric calculations. Implementation relies on Django services and the ORM with SQLite for development and PostgreSQL for production, plus the email backend for verification and alerts. These design choices define how data is stored, processed, and presented while keeping the system consistent and maintainable.

# Next section

# Entity Relationship Diagram (ERD)

The Entity-Relationship Diagram (ERD) illustrates the SafeBooks data model based on the Django models and the current SQLite schema. It focuses on core bookkeeping data for accounts, client profiles, reporting periods, financial records, and record line items. If a table or field does not appear in the SQLite file yet, it indicates pending migrations rather than a missing design requirement.

BookkeeperAccount is the parent entity for clients and financial records, while AdminAccount is used for approvals. Each Client belongs to one BookkeeperAccount and stores taxpayer details such as TIN, trade name, location, permit number, and risk level. Each Client can have multiple Period entries that define reporting months and years.

FinancialRecord links a BookkeeperAccount, Client, and Period and stores entry date, frequency, notes, and total amount. FinancialRecordLine holds the detailed line items for each record. AuditLog is added as a governance requirement to capture administrative and bookkeeping actions such as approvals, profile updates, and record edits. Reports and analytics are generated at runtime rather than stored as separate tables. Default Django authentication tables are excluded to keep the ERD focused on project specific entities.

**Actual Entity Relationship Diagram (ERD) (Attached image)**

Figure 9: Entity Relationship Diagram (ERD)

## ERD Layout (Text Guide)

```
Entities and fields (show PK and FK):

AdminAccount (admin_accounts)
- id (PK)
- full_name
- email
- password_hash
- is_active
- created_at
- last_login

BookkeeperAccount (bookkeeper_accounts)
- id (PK)
- full_name
- username
- email
- location
- email_verified
- login_alerts_enabled
- password_hash
- approved_at
- approved_by_admin_id (FK -> admin_accounts.id, nullable)
- rejected_at
- rejection_reason
- last_login
- created_at

Client (clients)
- id (PK)
- bookkeeper_id (FK -> bookkeeper_accounts.id)
- client_name
- tin_number (unique)
- trade_name
- location
- permit_number
- birthday
- email
- custom_fields (JSON)
- risk_level
- date_registered
- created_at
- updated_at

Period (periods)
- id (PK)
- client_id (FK -> clients.id)
- year
- month
- created_at
- updated_at
- unique: (client_id, year, month)

FinancialRecord (financial_records)
- id (PK)
- bookkeeper_id (FK -> bookkeeper_accounts.id)
- client_id (FK -> clients.id)
- period_id (FK -> periods.id)
- entry_date
- frequency
- notes
- total_amount
- created_at
- updated_at

FinancialRecordLine (financial_record_lines)
- id (PK)
- record_id (FK -> financial_records.id)
- type_code
- description
- amount
- sort_order
- created_at
- updated_at

AuditLog (audit_logs)
- id (PK)
- actor_type
- admin_id (FK -> admin_accounts.id, nullable)
- bookkeeper_id (FK -> bookkeeper_accounts.id, nullable)
- action
- target_type
- target_id
- created_at

Relationships (label each connector):
- AdminAccount 1 to 0..many BookkeeperAccount: approves
- BookkeeperAccount 0..1 to 1 AdminAccount: approved by
- BookkeeperAccount 1 to many Client: manages
- Client 1 to many Period: has periods
- BookkeeperAccount 1 to many FinancialRecord: records
- Client 1 to many FinancialRecord: records
- Period 1 to many FinancialRecord: covers
- FinancialRecord 1 to many FinancialRecordLine: line items
- AdminAccount 1 to 0..many AuditLog: creates
- BookkeeperAccount 1 to 0..many AuditLog: creates
- AuditLog 0..1 to 1 AdminAccount: performed by
- AuditLog 0..1 to 1 BookkeeperAccount: performed by
```

## ERD Diagram Prompt (Image Only)

Create a clean ERD for the SafeBooks database. Output image only, no text outside the diagram. Title at the top: "SafeBooks Entity Relationship Diagram". Use a white background, thin black or gray lines, and standard crow's foot notation with optionality markers. Represent entities as tables with field lists, and mark PK and FK fields. Use clear labels on relationship lines that match the relationship verbs below.

Entities and fields:
- AdminAccount (admin_accounts): id (PK), full_name, email, password_hash, is_active, created_at, last_login
- BookkeeperAccount (bookkeeper_accounts): id (PK), full_name, username, email, location, email_verified, login_alerts_enabled, password_hash, approved_at, approved_by_admin_id (FK, nullable), rejected_at, rejection_reason, last_login, created_at
- Client (clients): id (PK), bookkeeper_id (FK), client_name, tin_number (unique), trade_name, location, permit_number, birthday, email, custom_fields, risk_level, date_registered, created_at, updated_at
- Period (periods): id (PK), client_id (FK), year, month, created_at, updated_at
- FinancialRecord (financial_records): id (PK), bookkeeper_id (FK), client_id (FK), period_id (FK), entry_date, frequency, notes, total_amount, created_at, updated_at
- FinancialRecordLine (financial_record_lines): id (PK), record_id (FK), type_code, description, amount, sort_order, created_at, updated_at
- AuditLog (audit_logs): id (PK), actor_type, admin_id (FK, nullable), bookkeeper_id (FK, nullable), action, target_type, target_id, created_at

Relationships (label each connector):
- AdminAccount 1 to 0..many BookkeeperAccount: approves
- BookkeeperAccount 0..1 to 1 AdminAccount: approved by
- BookkeeperAccount 1 to many Client: manages
- Client 1 to many Period: has periods
- BookkeeperAccount 1 to many FinancialRecord: records
- Client 1 to many FinancialRecord: records
- Period 1 to many FinancialRecord: covers
- FinancialRecord 1 to many FinancialRecordLine: line items
- AdminAccount 1 to 0..many AuditLog: creates
- BookkeeperAccount 1 to 0..many AuditLog: creates
- AuditLog 0..1 to 1 AdminAccount: performed by
- AuditLog 0..1 to 1 BookkeeperAccount: performed by

Layout rules:
- Place BookkeeperAccount on the left.
- Place AdminAccount above BookkeeperAccount.
- Place Client next to BookkeeperAccount, then Period, then FinancialRecord, then FinancialRecordLine on the right.
- Place AuditLog below AdminAccount.
- Avoid crossing lines and keep labels readable.
- Do not include Django auth tables.


# Next Section

# JSON Schema Diagram

JSON Schema defines the structure and validation rules for data exchanged by SafeBooks. It standardizes payload formats across authentication, client management, financial records, analytics, reporting, and audit logging. This improves interoperability between client interfaces and backend services.

The schema centers on the FinancialRecord document, which nests a Period object and a line_items array for detailed entries. Supporting documents such as AuthRequest, ClientProfile, ReportRequest, AnalyticsSummary, and AuditLogEntry capture credentials, client identity, report filters, summary outputs, and governance events. Together, these schemas provide consistent naming and typing conventions for API communication.

**Actual JSON Schema Diagram (Attached image)**

Figure 10: JSON Schema Diagram

This diagram presents the structured payload hierarchy used by SafeBooks and highlights where nested objects and arrays occur. It serves as a reference for validation and documentation, helping ensure that data exchange remains accurate and predictable. The schema view also supports future maintenance by making payload changes easier to track.

# Next Section

# Data Dictionary

The data dictionary summarizes the SafeBooks database tables and their attributes. It provides a clear reference for field names, data types, and key roles used across the system.

Table 2. List of SafeBooks Database Tables

| Table Name | Description |
| --- | --- |
| admin_accounts | Stores administrator account profiles and access status. |
| bookkeeper_accounts | Stores bookkeeper account profiles and approval metadata. |
| clients | Stores client business profiles and taxpayer details. |
| periods | Stores reporting periods linked to clients. |
| financial_records | Stores financial record headers by client and period. |
| financial_record_lines | Stores line items for each financial record. |
| audit_logs | Stores audit events for approvals and record actions. |

Table 2.1 Data Dictionary for admin_accounts

| Attribute | Data Type | Key Type | Description |
| --- | --- | --- | --- |
| id | INTEGER | PK | Unique identifier of the admin account. |
| full_name | VARCHAR(120) | - | Admin full name. |
| email | VARCHAR(254) | UK | Admin email address. |
| password_hash | VARCHAR(255) | - | Hashed password value. |
| is_active | BOOLEAN | - | Account status flag. |
| created_at | DATETIME | - | Account creation timestamp. |
| last_login | DATETIME | - | Last login timestamp. |

Table 2.2 Data Dictionary for bookkeeper_accounts

| Attribute | Data Type | Key Type | Description |
| --- | --- | --- | --- |
| id | INTEGER | PK | Unique identifier of the bookkeeper account. |
| full_name | VARCHAR(120) | - | Bookkeeper full name. |
| username | VARCHAR(50) | UK | Unique login username. |
| email | VARCHAR(254) | UK | Unique login email address. |
| location | VARCHAR(180) | - | Primary location or address. |
| email_verified | BOOLEAN | - | Email verification status. |
| login_alerts_enabled | BOOLEAN | - | Login alert preference flag. |
| password_hash | VARCHAR(255) | - | Hashed password value. |
| approved_at | DATETIME | - | Approval timestamp. |
| approved_by_admin_id | INTEGER | FK | References admin_accounts.id. |
| rejected_at | DATETIME | - | Rejection timestamp. |
| rejection_reason | VARCHAR(255) | - | Rejection reason text. |
| last_login | DATETIME | - | Last login timestamp. |
| created_at | DATETIME | - | Account creation timestamp. |

Table 2.3 Data Dictionary for clients

| Attribute | Data Type | Key Type | Description |
| --- | --- | --- | --- |
| id | INTEGER | PK | Unique identifier of the client. |
| bookkeeper_id | INTEGER | FK | References bookkeeper_accounts.id. |
| client_name | VARCHAR(160) | - | Registered business name. |
| tin_number | VARCHAR(40) | UK | Unique taxpayer identification number. |
| trade_name | VARCHAR(180) | - | Optional trade name. |
| location | VARCHAR(180) | - | Business location. |
| permit_number | VARCHAR(80) | - | Business permit number. |
| birthday | DATE | - | Client birth date or registration date. |
| email | VARCHAR(254) | - | Contact email address. |
| custom_fields | JSON | - | Custom profile fields. |
| risk_level | ENUM | - | Client risk level classification. |
| date_registered | DATE | - | Date the client was registered. |
| created_at | DATETIME | - | Record creation timestamp. |
| updated_at | DATETIME | - | Record update timestamp. |

Table 2.4 Data Dictionary for periods

| Attribute | Data Type | Key Type | Description |
| --- | --- | --- | --- |
| id | INTEGER | PK | Unique identifier of the period. |
| client_id | INTEGER | FK | References clients.id. |
| year | INTEGER | - | Reporting year. |
| month | SMALLINT | - | Reporting month. |
| created_at | DATETIME | - | Record creation timestamp. |
| updated_at | DATETIME | - | Record update timestamp. |

Unique constraint: (client_id, year, month)

Table 2.5 Data Dictionary for financial_records

| Attribute | Data Type | Key Type | Description |
| --- | --- | --- | --- |
| id | INTEGER | PK | Unique identifier of the financial record. |
| bookkeeper_id | INTEGER | FK | References bookkeeper_accounts.id. |
| client_id | INTEGER | FK | References clients.id. |
| period_id | INTEGER | FK | References periods.id. |
| entry_date | DATE | - | Record entry date. |
| frequency | ENUM | - | Reporting frequency. |
| notes | TEXT | - | Notes or remarks. |
| total_amount | DECIMAL(14,2) | - | Total amount for the record. |
| created_at | DATETIME | - | Record creation timestamp. |
| updated_at | DATETIME | - | Record update timestamp. |

Table 2.6 Data Dictionary for financial_record_lines

| Attribute | Data Type | Key Type | Description |
| --- | --- | --- | --- |
| id | INTEGER | PK | Unique identifier of the line item. |
| record_id | INTEGER | FK | References financial_records.id. |
| type_code | VARCHAR(80) | - | Line item category or code. |
| description | VARCHAR(255) | - | Line item description. |
| amount | DECIMAL(14,2) | - | Line item amount. |
| sort_order | INTEGER | - | Sort order for display. |
| created_at | DATETIME | - | Record creation timestamp. |
| updated_at | DATETIME | - | Record update timestamp. |

Table 2.7 Data Dictionary for audit_logs

| Attribute | Data Type | Key Type | Description |
| --- | --- | --- | --- |
| id | INTEGER | PK | Unique identifier of the audit log entry. |
| actor_type | ENUM | - | Actor type that performed the action. |
| admin_id | INTEGER | FK | References admin_accounts.id. |
| bookkeeper_id | INTEGER | FK | References bookkeeper_accounts.id. |
| action | VARCHAR(160) | - | Action performed. |
| target_type | VARCHAR(120) | - | Target entity type. |
| target_id | VARCHAR(64) | - | Target entity identifier. |
| created_at | DATETIME | - | Event timestamp. |

# Next Section

# Technologies, Concepts, and Theories

This section describes the system model and process flow of SafeBooks and summarizes the technologies used for implementation. The discussion focuses on how data is captured, validated, stored, and analyzed to support bookkeeping operations.

## The System Model and Process Flow

### Account Onboarding and Approval

Bookkeepers register accounts through the web interface and submit required credentials for review. Administrators validate the request and approve or reject access based on policy and verification status. Approved accounts gain access to core features and audit entries are recorded for governance.

### Client Profile Management

Bookkeepers create and maintain client profiles that include TIN, trade name, location, and permit details. The system enforces unique TIN values and required fields to protect data quality. Each client profile is linked to its owner for secure data scoping.

### Financial Record Entry and Computation

Financial records are entered by period with detailed line items that describe revenue, expenses, and tax related values. The system computes totals, stores the record header, and preserves line items for traceability. These entries become the basis for analytics and reporting workflows.

### Analytics and Reporting

SafeBooks aggregates records to generate dashboard summaries, compliance status counts, and risk level views. Reports are produced using selected date ranges and client filters to support reviews and submissions. Output formats are optimized for on screen review and printable handover.

### Audit Logging

Administrative actions such as approvals and account updates, along with key record changes, are recorded in AuditLog. This provides traceable evidence of who performed an action and when it occurred. The audit trail supports accountability and operational review.

## Technical Stack and Utilization

Table 3. Technical Stack and Utilization of SafeBooks

| Technology | Definition | Utilization |
| --- | --- | --- |
| Python | General purpose programming language. | Implements the core business logic and services. |
| Django | Web framework for Python applications. | Provides routing, views, templates, authentication, and admin workflows. |
| PostgreSQL | Relational database management system. | Stores accounts, clients, periods, financial records, line items, and audit logs. |
| Django ORM | Object relational mapping layer. | Handles database queries and model relationships. |
| Django Templates, HTML, CSS, JavaScript | Server rendered UI layer. | Renders pages for login, dashboard, clients, records, analytics, and reports. |
| SMTP Email Backend | Email delivery service. | Sends verification emails and login alerts. |
| PyOTP | One time password library. | Supports time based authentication codes for account security. |

# System Testing and Implementation

This section outlines the proposed testing approach for SafeBooks to verify correctness, stability, and usability before deployment. Testing focuses on authentication, client management, financial record entry, analytics and reporting, and audit logging.

## System Test Plan

The team will perform systematic tests across the core modules and measure results using the following metrics:

### Account Access and Approval

Verify that only approved bookkeeper accounts can access protected pages and that admin approvals and rejections are recorded in audit logs.

### Client Profile Validation

Confirm that required fields are enforced and duplicate TIN values are rejected to maintain data integrity.

### Financial Record Entry Accuracy

Check that record headers and line items are saved correctly, and that totals match the computed sum of line items.

### Analytics and Reporting Consistency

Ensure dashboard summaries and report outputs match stored financial records for selected periods and clients.

### Audit Log Completeness

Verify that administrative actions and key record updates create audit log entries with the correct actor and target details.

## Summary of Proposed Testing Findings

**Table 4. Summary of Proposed Testing Findings**

| Test Case | Performance Metric | Expected Result |
| --- | --- | --- |
| Account Access | Access Control Accuracy | Unapproved accounts blocked in 100% of test cases. |
| Client Profiles | TIN Uniqueness Enforcement | Duplicate TIN submissions rejected in all attempts. |
| Financial Records | Data Completeness | Records stored with all line items and matching totals. |
| Analytics and Reports | Summary Accuracy | Dashboard and report totals match stored records. |
| Audit Logging | Log Coverage | Audit entries created for all tracked actions. |



