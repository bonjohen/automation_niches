# YAML Niche Configuration Schema

This document defines the schema for YAML configuration files that define industry-specific "niches" for the SMB Compliance Platform.

## Overview

Each niche configuration file defines:
- Entity types (what objects you track: Vendors, Vehicles, Properties, etc.)
- Requirement types (compliance tasks: COI verification, registration renewal, etc.)
- Document types (files processed: Certificates of Insurance, Registrations, etc.)
- Workflow rules (automation triggers and actions)
- Notification rules (when and how to alert users)

## File Location

Niche configuration files are stored in `configs/niches/` with the naming convention:
```
{niche_id}.yaml
```

Example: `configs/niches/coi_tracking.yaml`

---

## Schema Definition

### Root Structure

```yaml
niche:
  id: string          # Unique identifier (snake_case)
  name: string        # Display name
  description: string # Brief description
  version: string     # Schema version (semver)

entity_types:
  - ...               # List of entity type definitions

requirement_types:
  - ...               # List of requirement type definitions

document_types:
  - ...               # List of document type definitions

workflow_rules:
  - ...               # List of automation rules

notification_templates:
  - ...               # Email/notification templates
```

---

### Entity Types

Defines the primary objects tracked in this niche.

```yaml
entity_types:
  - code: string              # Unique code (snake_case, max 50 chars)
    name: string              # Display name
    description: string       # Optional description
    icon: string              # Icon name (e.g., "building", "truck", "user")

    fields:                   # Custom fields for this entity type
      - name: string          # Field name (snake_case)
        label: string         # Display label
        type: string          # Field type (see below)
        required: boolean     # Is field required?
        default: any          # Default value (optional)
        options: array        # For select/multi-select types
        validation:           # Optional validation rules
          min: number
          max: number
          pattern: string     # Regex pattern

    # Field types: string, text, number, currency, date, boolean,
    #              email, phone, url, select, multi-select, address
```

**Example:**
```yaml
entity_types:
  - code: vendor
    name: Vendor
    description: Third-party vendor or contractor
    icon: building
    fields:
      - name: tax_id
        label: Tax ID / EIN
        type: string
        required: false
      - name: vendor_type
        label: Vendor Type
        type: select
        options:
          - Contractor
          - Supplier
          - Service Provider
      - name: contract_value
        label: Annual Contract Value
        type: currency
        required: false
```

---

### Requirement Types

Defines compliance tasks that must be tracked.

```yaml
requirement_types:
  - code: string              # Unique code (snake_case)
    name: string              # Display name
    description: string       # Description

    frequency: string         # once, daily, weekly, monthly, quarterly, annually
    default_priority: string  # low, medium, high, critical

    applicable_entity_types:  # Which entity types this applies to
      - string                # Entity type codes

    required_document_types:  # Which documents satisfy this requirement
      - string                # Document type codes

    notification_rules:
      days_before:            # When to send reminders
        - number              # Days before due date
      escalation:
        enabled: boolean
        days_overdue: number  # Days overdue before escalation
        escalate_to: string   # Role to escalate to (manager, admin)

    fields:                   # Custom fields for this requirement type
      - name: string
        label: string
        type: string
        required: boolean
```

**Example:**
```yaml
requirement_types:
  - code: coi_verification
    name: COI Verification
    description: Verify vendor's Certificate of Insurance is current and meets requirements
    frequency: annually
    default_priority: high
    applicable_entity_types:
      - vendor
    required_document_types:
      - certificate_of_insurance
    notification_rules:
      days_before: [30, 14, 7, 1]
      escalation:
        enabled: true
        days_overdue: 7
        escalate_to: manager
    fields:
      - name: minimum_coverage
        label: Minimum Coverage Amount
        type: currency
        required: true
        default: 1000000
```

---

### Document Types

Defines documents that can be uploaded and processed.

```yaml
document_types:
  - code: string              # Unique code (snake_case)
    name: string              # Display name
    description: string       # Description

    accepted_mime_types:      # Allowed file types
      - string                # MIME types

    extraction_prompt: string # LLM prompt for data extraction (multi-line)

    extraction_schema:        # Expected fields to extract
      fields:
        - name: string        # Field name in extracted data
          label: string       # Human-readable label
          type: string        # Data type
          required: boolean   # Is extraction required?

    validation_rules:         # Rules to validate extracted data
      - field: string         # Field name
        rule: string          # Validation rule type
        value: any            # Rule parameters
        message: string       # Error message if validation fails
```

**Example:**
```yaml
document_types:
  - code: certificate_of_insurance
    name: Certificate of Insurance (COI)
    description: Standard ACORD certificate of liability insurance
    accepted_mime_types:
      - application/pdf
      - image/png
      - image/jpeg
    extraction_prompt: |
      Extract the following information from this Certificate of Insurance:
      1. Named Insured (company name)
      2. Policy Number
      3. Insurance Company/Carrier name
      4. Policy Effective Date (start date)
      5. Policy Expiration Date (end date)
      6. General Liability Coverage Amount
      7. Auto Liability Coverage Amount
      8. Workers Compensation Coverage (Yes/No and limit if applicable)
      9. Umbrella/Excess Liability Amount
      10. Certificate Holder name and address

      Return the data as a JSON object with these exact field names:
      named_insured, policy_number, carrier_name, effective_date,
      expiration_date, general_liability_limit, auto_liability_limit,
      workers_comp_coverage, umbrella_limit, certificate_holder

      Use ISO date format (YYYY-MM-DD) for dates.
      Use numeric values for coverage amounts (no currency symbols).

    extraction_schema:
      fields:
        - name: named_insured
          label: Named Insured
          type: string
          required: true
        - name: policy_number
          label: Policy Number
          type: string
          required: true
        - name: carrier_name
          label: Insurance Carrier
          type: string
          required: true
        - name: effective_date
          label: Effective Date
          type: date
          required: true
        - name: expiration_date
          label: Expiration Date
          type: date
          required: true
        - name: general_liability_limit
          label: General Liability Limit
          type: number
          required: true
        - name: auto_liability_limit
          label: Auto Liability Limit
          type: number
          required: false
        - name: workers_comp_coverage
          label: Workers Comp Coverage
          type: boolean
          required: false
        - name: umbrella_limit
          label: Umbrella/Excess Limit
          type: number
          required: false
        - name: certificate_holder
          label: Certificate Holder
          type: string
          required: false

    validation_rules:
      - field: expiration_date
        rule: date_after
        value: effective_date
        message: Expiration date must be after effective date
      - field: general_liability_limit
        rule: min_value
        value: 0
        message: General liability limit must be positive
```

---

### Workflow Rules

Defines automated actions triggered by events.

```yaml
workflow_rules:
  - code: string              # Unique rule identifier
    name: string              # Display name
    description: string       # Description
    enabled: boolean          # Is rule active?

    trigger:
      event: string           # Event type (see below)
      conditions:             # Optional conditions
        - field: string
          operator: string    # equals, not_equals, greater_than, less_than, contains
          value: any

    actions:                  # Actions to perform
      - type: string          # Action type (see below)
        params: object        # Action-specific parameters
```

**Trigger Events:**
- `document.uploaded` - Document uploaded
- `document.processed` - Document extraction complete
- `requirement.created` - New requirement created
- `requirement.expiring` - Requirement approaching due date
- `requirement.expired` - Requirement past due date
- `entity.created` - New entity created
- `entity.updated` - Entity modified

**Action Types:**
- `create_requirement` - Create a new requirement
- `update_requirement` - Update existing requirement
- `send_notification` - Send email/notification
- `link_document` - Link document to requirement
- `update_status` - Change requirement status
- `assign_user` - Assign requirement to user

**Example:**
```yaml
workflow_rules:
  - code: auto_create_coi_requirement
    name: Auto-create COI requirement for new vendors
    description: When a new vendor is created, automatically create a COI verification requirement
    enabled: true
    trigger:
      event: entity.created
      conditions:
        - field: entity_type
          operator: equals
          value: vendor
    actions:
      - type: create_requirement
        params:
          requirement_type: coi_verification
          name: "COI Verification - {{entity.name}}"
          due_date_offset: 30  # Days from now
          priority: high

  - code: link_coi_to_requirement
    name: Auto-link processed COI to requirement
    description: When a COI is processed, automatically link it to the vendor's COI requirement
    enabled: true
    trigger:
      event: document.processed
      conditions:
        - field: document_type
          operator: equals
          value: certificate_of_insurance
    actions:
      - type: link_document
        params:
          requirement_type: coi_verification
      - type: update_requirement
        params:
          status: compliant
          due_date: "{{document.extracted_data.expiration_date}}"
```

---

### Notification Templates

Defines email and notification templates.

```yaml
notification_templates:
  - code: string              # Template identifier
    name: string              # Template name
    notification_type: string # reminder, expiring, overdue, escalation
    channel: string           # email, in_app, sms

    subject: string           # Email subject (Jinja2 template)
    body: string              # Email body (Jinja2 template, HTML supported)

    # Available template variables:
    # - {{user.first_name}}, {{user.email}}
    # - {{entity.name}}, {{entity.custom_fields.*}}
    # - {{requirement.name}}, {{requirement.due_date}}, {{requirement.status}}
    # - {{document.filename}}, {{document.extracted_data.*}}
    # - {{account.name}}, {{account.branding.logo_url}}
```

**Example:**
```yaml
notification_templates:
  - code: coi_expiring_reminder
    name: COI Expiring Reminder
    notification_type: expiring
    channel: email
    subject: "Action Required: COI expiring for {{entity.name}}"
    body: |
      <p>Hello {{user.first_name}},</p>

      <p>The Certificate of Insurance for <strong>{{entity.name}}</strong>
      is expiring on <strong>{{requirement.due_date | date('%B %d, %Y')}}</strong>.</p>

      <p>Please request an updated COI from the vendor to maintain compliance.</p>

      <p><a href="{{app_url}}/requirements/{{requirement.id}}">View Requirement</a></p>

      <p>Thank you,<br>
      {{account.name}} Compliance Team</p>
```

---

## Complete Example

See `configs/niches/coi_tracking.yaml` for a complete example of a niche configuration.

---

## Validation

All YAML configurations are validated on load against this schema. The validation script checks:

1. Required fields are present
2. Field types are valid
3. References to other types exist (e.g., entity_type codes in requirement_types)
4. Notification rules have valid day values
5. Workflow rules reference valid events and actions
6. Templates use valid Jinja2 syntax

Run validation with:
```bash
python -m app.config.yaml_validator configs/niches/coi_tracking.yaml
```
