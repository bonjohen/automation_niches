# User Stories & Acceptance Criteria - Vendor COI Tracking

## Target Users

### Primary Personas

1. **Office Manager (Sarah)**
   - Works at a property management company (25 employees)
   - Manages 50-100 vendors (HVAC, landscaping, cleaning, etc.)
   - Currently tracks COIs in spreadsheets
   - Pain: Spends 4-6 hours/week chasing expired certificates

2. **Operations Director (Mike)**
   - Works at a general contractor (40 employees)
   - Manages 30-60 subcontractors
   - Needs to verify insurance before allowing work on site
   - Pain: Liability exposure when subcontractors have lapsed coverage

3. **Risk Manager (Jennifer)**
   - Works at a mid-size business (50 employees)
   - Responsible for vendor compliance across departments
   - Needs audit trail and reporting
   - Pain: No visibility into compliance status company-wide

---

## Epic 1: Account & User Management

### US-1.1: Account Registration
**As a** new user
**I want to** create an account for my company
**So that** I can start tracking vendor insurance certificates

**Acceptance Criteria:**
- [ ] User can register with email, password, and company name
- [ ] Email verification is sent
- [ ] Account is created with user as Owner role
- [ ] User is redirected to onboarding flow after registration
- [ ] Duplicate email addresses are rejected with clear error message

### US-1.2: User Login
**As a** registered user
**I want to** log in to my account
**So that** I can access my vendor compliance dashboard

**Acceptance Criteria:**
- [ ] User can log in with email and password
- [ ] Invalid credentials show appropriate error message
- [ ] Session persists across browser refresh (JWT token)
- [ ] "Forgot password" link is available
- [ ] User is redirected to dashboard after login

### US-1.3: Invite Team Members
**As an** account owner
**I want to** invite team members to my account
**So that** they can help manage vendor compliance

**Acceptance Criteria:**
- [ ] Owner can invite users by email
- [ ] Owner can assign roles (Admin, Manager, Viewer)
- [ ] Invited user receives email with signup link
- [ ] Invited user's account is linked to the organization
- [ ] Owner can see list of pending invitations

### US-1.4: Role-Based Access
**As an** account owner
**I want to** control what team members can do
**So that** sensitive operations are restricted appropriately

**Acceptance Criteria:**
- [ ] Viewer: Can view vendors, requirements, documents (read-only)
- [ ] Manager: Can add/edit vendors, upload documents, update requirements
- [ ] Admin: Can manage users, change settings
- [ ] Owner: Full access including billing and account deletion

---

## Epic 2: Vendor Management

### US-2.1: Add New Vendor
**As a** manager
**I want to** add a new vendor to the system
**So that** I can track their insurance compliance

**Acceptance Criteria:**
- [ ] User can enter vendor name (required)
- [ ] User can enter contact info (email, phone, address)
- [ ] User can select vendor type (Contractor, Supplier, Service Provider, etc.)
- [ ] User can set risk level (Low, Medium, High, Critical)
- [ ] User can add custom notes
- [ ] Vendor is created with "Pending" COI requirement automatically
- [ ] User sees confirmation and can add another vendor

### US-2.2: View Vendor List
**As a** user
**I want to** see all my vendors in a list
**So that** I can quickly find and manage them

**Acceptance Criteria:**
- [ ] List shows vendor name, type, compliance status, next due date
- [ ] List can be sorted by name, status, due date
- [ ] List can be filtered by status (Compliant, Expiring Soon, Expired, Pending)
- [ ] List can be filtered by vendor type
- [ ] Search box filters by vendor name
- [ ] Pagination or infinite scroll for large lists (20+ vendors)
- [ ] Compliance status is color-coded (green/yellow/red)

### US-2.3: View Vendor Details
**As a** user
**I want to** see detailed information about a vendor
**So that** I can review their compliance status and history

**Acceptance Criteria:**
- [ ] Page shows all vendor information
- [ ] Page shows current compliance status with visual indicator
- [ ] Page shows list of requirements and their status
- [ ] Page shows list of uploaded documents
- [ ] Page shows compliance history (timeline of status changes)
- [ ] User can navigate to edit vendor or upload document

### US-2.4: Edit Vendor
**As a** manager
**I want to** update vendor information
**So that** I can keep records accurate

**Acceptance Criteria:**
- [ ] User can edit all vendor fields
- [ ] User can change vendor status (Active, Inactive, Archived)
- [ ] Changes are saved and confirmed
- [ ] Audit log records who made changes and when

### US-2.5: Delete Vendor
**As an** admin
**I want to** remove a vendor from the system
**So that** I can clean up outdated records

**Acceptance Criteria:**
- [ ] User is prompted to confirm deletion
- [ ] Warning shows that all documents and requirements will be deleted
- [ ] Deleted vendor is removed from all lists
- [ ] Audit log records deletion

### US-2.6: Import Vendors from CSV
**As a** manager
**I want to** import vendors from a spreadsheet
**So that** I can quickly onboard my existing vendor list

**Acceptance Criteria:**
- [ ] User can download CSV template
- [ ] User can upload CSV file
- [ ] System validates data and shows preview
- [ ] System shows errors for invalid rows
- [ ] User can proceed with valid rows only
- [ ] Imported vendors have COI requirements auto-created

---

## Epic 3: Document Upload & Processing

### US-3.1: Upload COI Document
**As a** manager
**I want to** upload a Certificate of Insurance
**So that** I can verify a vendor's coverage

**Acceptance Criteria:**
- [ ] User can drag-and-drop or click to upload
- [ ] Accepted formats: PDF, PNG, JPG
- [ ] Maximum file size: 10MB
- [ ] User can select which vendor the document belongs to
- [ ] User can select document type (COI, Workers Comp, etc.)
- [ ] Upload progress is shown
- [ ] Success message confirms upload and triggers processing

### US-3.2: Automatic Data Extraction
**As a** manager
**I want** the system to automatically extract data from uploaded COIs
**So that** I don't have to manually enter certificate details

**Acceptance Criteria:**
- [ ] System extracts: Named Insured, Policy Number, Carrier, Effective Date, Expiration Date
- [ ] System extracts coverage limits: General Liability, Auto, Workers Comp, Umbrella
- [ ] System extracts: Additional Insured status, Waiver of Subrogation
- [ ] Extraction completes within 30 seconds
- [ ] Processing status is visible to user
- [ ] Extracted data is displayed for review

### US-3.3: Review & Edit Extracted Data
**As a** manager
**I want to** review and correct AI-extracted data
**So that** I can ensure accuracy before it's used for compliance

**Acceptance Criteria:**
- [ ] Extracted data is shown in editable form
- [ ] Low-confidence fields are highlighted for review
- [ ] User can edit any extracted field
- [ ] User can approve data to finalize
- [ ] Approved data updates the requirement's due date
- [ ] System learns from corrections (future enhancement)

### US-3.4: View Document
**As a** user
**I want to** view an uploaded document
**So that** I can verify the extracted information

**Acceptance Criteria:**
- [ ] User can preview document in browser (PDF viewer)
- [ ] User can download original document
- [ ] User can see extracted data alongside document
- [ ] User can zoom in/out on document

### US-3.5: Delete Document
**As a** manager
**I want to** delete an incorrectly uploaded document
**So that** I can upload the correct one

**Acceptance Criteria:**
- [ ] User is prompted to confirm deletion
- [ ] If document was linked to requirement, requirement status reverts
- [ ] Document is removed from storage
- [ ] Audit log records deletion

---

## Epic 4: Compliance Tracking

### US-4.1: View Compliance Dashboard
**As a** user
**I want to** see an overview of my compliance status
**So that** I can quickly identify issues that need attention

**Acceptance Criteria:**
- [ ] Dashboard shows summary stats: Total vendors, Compliant, Expiring Soon, Expired, Pending
- [ ] Stats are displayed as cards with counts and percentages
- [ ] Dashboard shows list of vendors needing attention (sorted by urgency)
- [ ] Dashboard shows upcoming expirations (next 30 days)
- [ ] Dashboard shows recent activity
- [ ] User can click through to vendor details

### US-4.2: View Requirements List
**As a** user
**I want to** see all compliance requirements across vendors
**So that** I can manage them in one place

**Acceptance Criteria:**
- [ ] List shows requirement name, vendor, status, due date
- [ ] List can be sorted by due date, status, vendor name
- [ ] List can be filtered by status
- [ ] List can be filtered by date range
- [ ] Overdue items are highlighted in red
- [ ] Expiring soon items are highlighted in yellow

### US-4.3: Mark Requirement Complete
**As a** manager
**I want to** manually mark a requirement as complete
**So that** I can update status when I've verified compliance offline

**Acceptance Criteria:**
- [ ] User can mark requirement as Compliant
- [ ] User can optionally add notes
- [ ] Status change is recorded with timestamp
- [ ] Notification emails are cancelled if pending

### US-4.4: View Compliance Calendar
**As a** user
**I want to** see compliance deadlines on a calendar
**So that** I can plan ahead for renewals

**Acceptance Criteria:**
- [ ] Calendar shows monthly view
- [ ] Expiration dates are shown on calendar
- [ ] Items are color-coded by status
- [ ] User can click date to see all items due
- [ ] User can navigate between months

---

## Epic 5: Notifications & Alerts

### US-5.1: Receive Expiration Reminders
**As a** user
**I want to** receive email reminders before certificates expire
**So that** I can request renewals in time

**Acceptance Criteria:**
- [ ] System sends reminders at 60, 30, 14, 7, 3, 1 days before expiration
- [ ] Email includes vendor name, current expiration date, coverage details
- [ ] Email includes link to view requirement in app
- [ ] Email includes link to upload new document
- [ ] User can configure which reminders they receive

### US-5.2: Receive Overdue Alerts
**As a** user
**I want to** be alerted when a certificate has expired
**So that** I can take immediate action

**Acceptance Criteria:**
- [ ] System sends alert on expiration date
- [ ] System sends escalation after 7 days overdue
- [ ] Email clearly indicates EXPIRED status
- [ ] Email suggests actions to take

### US-5.3: Configure Notification Preferences
**As a** user
**I want to** control which notifications I receive
**So that** I'm not overwhelmed with emails

**Acceptance Criteria:**
- [ ] User can enable/disable email notifications
- [ ] User can choose which reminder intervals to receive
- [ ] User can set up digest mode (daily summary instead of individual emails)
- [ ] Settings are saved per user

### US-5.4: View In-App Notifications
**As a** user
**I want to** see notifications in the app
**So that** I can catch up on activity when logged in

**Acceptance Criteria:**
- [ ] Notification bell icon shows unread count
- [ ] Dropdown shows recent notifications
- [ ] User can click to navigate to related item
- [ ] User can mark notifications as read
- [ ] User can mark all as read

---

## Epic 6: Reporting

### US-6.1: Export Compliance Report
**As a** user
**I want to** export a compliance report
**So that** I can share it with stakeholders or auditors

**Acceptance Criteria:**
- [ ] User can generate report for all vendors or filtered subset
- [ ] Report includes vendor name, compliance status, expiration dates, coverage amounts
- [ ] Report can be exported as PDF or CSV
- [ ] Report includes generation date and user name

### US-6.2: View Compliance History
**As a** user
**I want to** see historical compliance data
**So that** I can demonstrate ongoing compliance for audits

**Acceptance Criteria:**
- [ ] User can view compliance status over time for a vendor
- [ ] Timeline shows when COIs were uploaded and when they expired
- [ ] User can filter by date range
- [ ] Data can be exported

---

## Epic 7: Settings & Administration

### US-7.1: Configure Coverage Requirements
**As an** admin
**I want to** set minimum coverage requirements
**So that** the system can flag COIs that don't meet our standards

**Acceptance Criteria:**
- [ ] Admin can set minimum General Liability amount
- [ ] Admin can set minimum Auto Liability amount
- [ ] Admin can require Workers Comp coverage
- [ ] Admin can require Additional Insured endorsement
- [ ] System flags documents that don't meet requirements
- [ ] Requirements can vary by vendor risk level

### US-7.2: Customize Email Templates
**As an** admin
**I want to** customize notification emails
**So that** they match our company's tone and branding

**Acceptance Criteria:**
- [ ] Admin can edit email subject lines
- [ ] Admin can edit email body text
- [ ] Preview shows how email will look
- [ ] Default templates can be restored

### US-7.3: View Audit Log
**As an** admin
**I want to** see an audit trail of all actions
**So that** I can track changes for compliance purposes

**Acceptance Criteria:**
- [ ] Log shows timestamp, user, action, resource
- [ ] Log can be filtered by user, action type, date range
- [ ] Log can be exported
- [ ] Log is immutable (cannot be edited or deleted)

### US-7.4: Configure Branding
**As an** account owner
**I want to** add my company logo and colors
**So that** the platform matches our brand

**Acceptance Criteria:**
- [ ] Owner can upload company logo
- [ ] Owner can set primary brand color
- [ ] Logo appears in header and emails
- [ ] Colors are applied to buttons and accents
- [ ] Preview shows changes before saving

---

## MVP Scope Definition

### Must Have (MVP)
- US-1.1, US-1.2: Account registration and login
- US-2.1, US-2.2, US-2.3, US-2.4: Basic vendor CRUD
- US-3.1, US-3.2, US-3.3: Document upload and AI extraction
- US-4.1, US-4.2, US-4.3: Compliance dashboard and tracking
- US-5.1, US-5.2: Email notifications for expirations

### Should Have (Post-MVP)
- US-1.3, US-1.4: Team invitations and roles
- US-2.5, US-2.6: Delete vendor, CSV import
- US-3.4, US-3.5: Document preview and delete
- US-4.4: Calendar view
- US-5.3, US-5.4: Notification preferences, in-app notifications
- US-6.1, US-6.2: Reporting
- US-7.1, US-7.2: Coverage requirements, email customization

### Nice to Have (Future)
- US-7.3, US-7.4: Audit log, branding customization
- Vendor self-service portal
- CRM integration
- API access

---

## Definition of Done

A user story is complete when:
- [ ] All acceptance criteria are met
- [ ] Code is reviewed and merged
- [ ] Unit tests pass
- [ ] Feature works in staging environment
- [ ] Documentation is updated if needed

---

*Last Updated: 2024-01-15*
