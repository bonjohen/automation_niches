# DataJinn - Data Operations Platform Summary

## Overview

A unified AI-driven data operations platform for small businesses (10-50 employees) featuring:

- **Canonical core schema** - Common data model + workflow engine
- **YAML-configurable vertical templates** - Industry-specific configurations
- **AI-powered document processing** - OCR + LLM extraction
- **CRM connectivity** - Integration with existing systems
- **White-label capability** - Customer branding support

**Initial Vertical:** Compliance tracking (COI, licenses, permits, certifications)

---

## Project Phases (12 Weeks Total)

### Phase 1: Foundation & Architecture (Weeks 1-2)

#### 1.1 Requirements & Niche Selection
| Human Tasks | AI Agent Tasks |
|-------------|----------------|
| Select initial target niche | Research competitors |
| Define MVP feature set | Generate user stories |
| Identify 2-3 beta users | Draft sample test documents |

#### 1.2 Core Schema Design
**Database Entities:**
- Account/Organization (multi-tenant)
- User (auth, roles)
- Entity (generic: Vendor, Vehicle, Property, Contract)
- Task (tracked items with due dates and statuses)
- Document (metadata + extracted data JSON)
- Notification (scheduled alerts)
- AuditLog (change tracking)
- TaskType/DocumentType (lookup tables from YAML)

#### 1.3 YAML Template Structure
**Sections to define:**
- `vertical` - name and description
- `entity_types` - primary objects with custom fields
- `task_types` - tracked items, frequencies, notification rules
- `document_types` - expected fields, AI extraction prompts
- `workflow_rules` - conditional automations

#### 1.4 Tech Stack Setup
- Python backend (FastAPI)
- React/Next.js frontend
- PostgreSQL database
- Authentication (Firebase Auth or Auth0)
- Cloud storage (S3/GCS)
- CI/CD (GitHub Actions)

---

### Phase 2: Backend Core Development (Weeks 3-4)

#### 2.1 Database & Models
- ORM models matching schema
- Database migrations
- Seeding scripts for lookup tables

#### 2.2 Core API Endpoints
- `/api/entities` - generic entity management
- `/api/requirements` - task management (aliased as `/api/tasks`)
- `/api/documents` - upload, list, retrieve
- `/api/notifications` - alert management
- Authentication middleware
- Multi-tenant data isolation
- OpenAPI/Swagger documentation

#### 2.3 YAML Config Loader
- YAML parser loading niche config at startup
- Dynamic lookup table population
- Config validation
- Custom fields via JSONB columns

---

### Phase 3: AI Integration Pipeline (Weeks 5-6)

#### 3.1 Document Processing
- File upload endpoint with S3 storage
- OCR integration (Tesseract for MVP, Google Vision API option)
- Text extraction pipeline for PDFs

#### 3.2 LLM Data Extraction
- OpenAI API (GPT-4) integration
- Prompt templates per document type (from YAML)
- Structured JSON output parsing
- Confidence scoring and validation
- Graceful failure handling

#### 3.3 Workflow Automation
- Link extracted data to Requirements (e.g., expiry_date → due_date)
- Auto-create/update Requirements on document processing
- Notification scheduler (daily cron)
- Email service integration (SendGrid/Mailgun)
- Jinja2 notification templating

---

### Phase 4: Frontend Development (Weeks 6-8)

#### 4.1 Core UI Components
- Login/signup pages
- Dashboard with operations overview
- Entity list and detail views
- Dynamic forms based on YAML entity_type fields

#### 4.2 Document Management UI
- Document upload component
- Processing status indicator
- Extracted data review/edit interface
- Document preview

#### 4.3 Task Tracking UI
- Tasks list with status filters
- Calendar/timeline view of deadlines
- Overdue alerts display
- Mark complete functionality

#### 4.4 White-Label Support
- Theme configuration (colors, logo)
- Per-tenant branding storage
- CSS variable-based theming

---

### Phase 5: CRM Integration (Weeks 7-8)

#### 5.1 Integration Architecture
- Webhooks + API connectors
- Abstract CRM interface

#### 5.2 Initial Connectors (pick 1-2 for MVP)
- HubSpot integration
- Salesforce integration
- Zapier webhook support (fallback)

#### 5.3 Data Sync
- Bidirectional entity sync (Vendors/Contacts)
- Push task status to CRM
- Pull contact updates from CRM

---

### Phase 6: Testing & Hardening (Week 9)

#### 6.1 Automated Testing
- Unit tests for business logic
- Integration tests for API endpoints
- E2E tests for critical flows
- AI extraction accuracy tests

#### 6.2 Security Review
- Auth/authorization audit
- Data isolation verification
- Input validation review
- Secrets management check

#### 6.3 Performance Testing
- Load test (50+ entities, 100+ documents)
- Query optimization
- AI API usage cost review

---

### Phase 7: Beta Launch & Feedback (Week 10)

#### 7.1 Beta Deployment
| Human Tasks | AI Agent Tasks |
|-------------|----------------|
| Identify 3-5 beta users | Deploy to production |
| Conduct onboarding calls | Set up monitoring (Sentry) |
| Gather feedback | Create onboarding guide |

#### 7.2 Iteration
- Fix critical bugs from feedback
- Improve AI prompts based on real documents
- UX improvements for friction points

---

### Phase 8: Polish & Launch Prep (Week 11)

#### 8.1 Production Readiness
- Final bug fixes
- Performance optimization
- Error handling improvements
- Email template refinement

#### 8.2 Marketing Preparation
| Human Tasks | AI Agent Tasks |
|-------------|----------------|
| Approve marketing copy | Generate landing page copy |
| Record demo video | Create FAQ/help docs |
| | Draft launch announcements |

---

### Phase 9: Public Launch (Week 12)

#### 9.1 Launch Activities
| Human Tasks | AI Agent Tasks |
|-------------|----------------|
| Post on Product Hunt/HN | Monitor server health |
| Social media announcements | Track API usage/costs |
| Direct outreach | Support requests (with review) |

#### 9.2 Post-Launch Planning
- Review metrics and feedback
- Decide next niche to add
- Compile feedback analysis
- Draft next 90-day plan

---

## Parallel/Ongoing Work Streams

### Documentation (Throughout)
- API documentation
- YAML config documentation
- User guides
- Developer setup guide

### DevOps (Throughout)
- CI/CD maintenance
- Backup configuration
- Monitoring dashboards

---

## Vertical Expansion Template (Post-MVP)

For each new vertical (Fleet Compliance, Lease Management, Workers Comp, etc.):

1. **Research Phase** - Analyze pain points, research requirements, gather sample documents
2. **Configuration Phase** - Write YAML template, create AI extraction prompts, define notification rules
3. **Testing Phase** - Test with samples, validate extraction accuracy, user acceptance testing
4. **Launch Phase** - Enable in production, market to vertical-specific audience

---

## Key Decision Points for Human

| Decision | Recommendation |
|----------|----------------|
| Which vertical to start with? | Vendor COI Tracking (clear scope, high demand) |
| Pricing model? | Free beta → subscription |
| CRM integrations priority? | HubSpot + Zapier (decided) |
| Self-service vs. managed onboarding? | TBD |

---

## Project Structure

```
/backend
  /app
    /models      # SQLAlchemy models
    /api         # FastAPI routes
    /services    # Business logic
    /ai          # OCR + LLM pipeline
    /config      # YAML loader
  /migrations    # Alembic migrations
  /tests
  main.py

/frontend
  /src
    /components  # React components
    /pages       # Route pages
    /hooks       # Custom hooks
    /services    # API client
    /theme       # Branding/theming

/configs
  /niches
    coi_tracking.yaml
    fleet_compliance.yaml
    lease_management.yaml

/docs
  api.md
  yaml_schema.md
  user_guide.md
```

---

## Phase Completion Checklist

Before completing each phase, verify:
- [ ] All tests pass
- [ ] API endpoints documented
- [ ] No security vulnerabilities
- [ ] Performance acceptable
- [ ] User can complete core workflow end-to-end
