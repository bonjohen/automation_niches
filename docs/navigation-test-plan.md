# Plan: Static Site Navigation Test Pass

## Objective
Comprehensive verification of all page navigation links in the static_site marketing website.

## Site Inventory

### Pages (25 total)
**Root Level (3):**
- `index.html` - Homepage
- `platform.html` - Platform Features
- `contact.html` - Contact/Demo Request

**Features (3):**
- `features/ai-document-processing.html`
- `features/smart-alerts.html`
- `features/dashboard.html`

**Solutions (16):**
- `solutions/index.html` - Solutions Hub
- `solutions/business-license.html`
- `solutions/coi-tracking.html`
- `solutions/contract-renewal.html`
- `solutions/environmental-compliance.html`
- `solutions/equipment-maintenance.html`
- `solutions/fleet-compliance.html`
- `solutions/grant-management.html`
- `solutions/lease-management.html`
- `solutions/lien-waiver.html`
- `solutions/payroll-exception.html`
- `solutions/permit-inspection.html`
- `solutions/regulatory-mail.html`
- `solutions/supplier-compliance.html`
- `solutions/utility-audit.html`
- `solutions/workers-comp.html`

---

## Test Categories

### 1. Header Navigation (all pages)
Each page should have consistent header with working links:
- [ ] Logo → `index.html`
- [ ] Home → `index.html`
- [ ] Platform → `platform.html`
- [ ] Solutions → `solutions/index.html`
- [ ] Contact → `contact.html`

### 2. Footer Navigation (all pages)
- [ ] Footer logo → `index.html`
- [ ] Platform section links (Features, AI Doc Processing, Smart Alerts, Dashboard)
- [ ] Solutions section links (All Solutions, COI Tracking, Fleet Compliance)
- [ ] Company section links (Contact Us, Request Demo)

### 3. Homepage Content Links
**Feature Cards (3):**
- [ ] AI Document Processing → `features/ai-document-processing.html`
- [ ] Smart Alerts → `features/smart-alerts.html`
- [ ] Real-Time Dashboard → `features/dashboard.html`

**Solution Cards (15):**
- [ ] Fleet Compliance → `solutions/fleet-compliance.html`
- [ ] Lease Management → `solutions/lease-management.html`
- [ ] Lien Waiver → `solutions/lien-waiver.html`
- [ ] Workers' Comp → `solutions/workers-comp.html`
- [ ] Permit & Inspection → `solutions/permit-inspection.html`
- [ ] COI Tracking → `solutions/coi-tracking.html`
- [ ] Utility Bill Audit → `solutions/utility-audit.html`
- [ ] Environmental Logs → `solutions/environmental-compliance.html`
- [ ] Contract Renewal → `solutions/contract-renewal.html`
- [ ] Equipment Maintenance → `solutions/equipment-maintenance.html`
- [ ] Payroll Exception → `solutions/payroll-exception.html`
- [ ] Regulatory Mail → `solutions/regulatory-mail.html`
- [ ] Business License → `solutions/business-license.html`
- [ ] Supplier Compliance → `solutions/supplier-compliance.html`
- [ ] Grant & Rebate → `solutions/grant-management.html`

**CTA Buttons:**
- [ ] "Request a Demo" buttons → `contact.html`
- [ ] "Explore Solutions" → `solutions/index.html`
- [ ] "View All Solutions" → `solutions/index.html`

### 4. Platform Page Links
- [ ] CTA buttons → `contact.html`
- [ ] Related solutions cards (3 links)
- [ ] Anchor links: `#features`, `#how-it-works`

### 5. Feature Page Links (each of 3 pages)
- [ ] Related solutions section (3 cards per page)
- [ ] CTA buttons → `../contact.html`
- [ ] Footer links use correct `../` paths

### 6. Solutions Index Links
- [ ] All 15 solution cards link to correct pages
- [ ] CTA button → `../contact.html`

### 7. Individual Solution Page Links (each of 15 pages)
- [ ] Related solutions section (3 cards per page)
- [ ] CTA buttons → `../contact.html`
- [ ] Header/footer use correct `../` paths

### 8. Anchor Links
- [ ] `index.html#solutions` - jumps to solutions section
- [ ] `platform.html#features` - jumps to features section
- [ ] `platform.html#how-it-works` - jumps to how it works section

---

## Test Execution Method

Using browser automation (MCP Chrome tools):
1. Open each page
2. Verify page loads without errors
3. Click each navigation link
4. Verify destination page loads correctly
5. Use browser back to return
6. Repeat for all links on page

---

## Verification Checklist

### Phase 1: Page Load Test
Verify all 25 pages load without 404 errors.

### Phase 2: Header/Footer Consistency
Spot-check header/footer links from:
- Root page (`index.html`)
- Feature page (`features/smart-alerts.html`)
- Solution page (`solutions/coi-tracking.html`)

### Phase 3: Content Links
Test all internal content links from homepage and solutions index.

### Phase 4: Related Solutions Cross-Links
Verify related solutions sections link correctly.

---

## Known Issues to Investigate
1. Form endpoint uses placeholder: `https://formspree.io/f/your-form-id`
2. Email link: `demo@complianceauto.com` - verify correctness
3. Verify all solution pages referenced actually exist
