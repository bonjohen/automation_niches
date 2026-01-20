# Static Marketing Website - Design Plan

## Purpose

A marketing/landing site to attract customers and explain the SMB Compliance Automation Platform's value proposition. Features modern professional design with demo request forms.

## Content Sources

- **docs/AutomationPainPointSolutions.pdf** - 15 automation niches with detailed pain points, workflows, and solutions
- **docs/SMB Compliance Automation Platform.pdf** - Platform capabilities and technology overview

---

## Site Structure

```
static_site/
├── index.html                    # Home/landing page
├── platform.html                 # Platform features & technology
├── contact.html                  # Demo request form
├── solutions/
│   ├── index.html               # Solutions overview grid
│   ├── fleet-compliance.html    # 1. Fleet Compliance Document Management
│   ├── lease-management.html    # 2. Commercial Lease Abstraction
│   ├── lien-waiver.html         # 3. Lien Waiver & Pay Application
│   ├── workers-comp.html        # 4. Workers' Comp Audit Prep
│   ├── permit-inspection.html   # 5. Permit & Inspection Coordination
│   ├── coi-tracking.html        # 6. Vendor COI Tracking
│   ├── utility-audit.html       # 7. Utility Bill Audit & Recovery
│   ├── environmental-compliance.html  # 8. Environmental Compliance Logs
│   ├── contract-renewal.html    # 9. Customer Contract Renewal
│   ├── equipment-maintenance.html # 10. Equipment Maintenance & Warranty
│   ├── payroll-exception.html   # 11. Payroll Exception Detection
│   ├── regulatory-mail.html     # 12. Regulatory Mail Intake
│   ├── business-license.html    # 13. Business License Tracking
│   ├── supplier-compliance.html # 14. Supplier Contract Compliance
│   └── grant-management.html    # 15. Grant & Rebate Deadlines
├── css/
│   └── styles.css               # Main stylesheet
├── js/
│   └── main.js                  # Mobile menu, smooth scroll
└── assets/
    └── icons/                   # SVG icons for solutions
```

---

## Page Designs

### Home Page (index.html)
| Section | Content |
|---------|---------|
| Hero | Headline, subheadline, "Request Demo" CTA |
| Problem | SMB compliance pain points overview |
| Solutions Grid | 15 cards linking to solution pages |
| Platform Highlights | AI processing, alerts, dashboards |
| Social Proof | Testimonials/stats placeholder |
| Footer CTA | Inline demo request form |

### Platform Page (platform.html)
| Section | Content |
|---------|---------|
| Hero | Platform value proposition |
| Features | AI OCR, automated alerts, dashboards, YAML config, CRM, white-label |
| How It Works | 3-4 step visual flow |
| Technology | Modern stack highlights |
| CTA | Demo request |

### Contact Page (contact.html)
Form fields:
- Name (required)
- Email (required)
- Company Name
- Company Size (dropdown)
- Interest Area (which solution)
- Message (optional)

Form backend: Formspree or mailto: fallback

### Solutions Overview (solutions/index.html)
- Header with intro text
- Filterable card grid (optional JS)
- Each card: icon, title, description, "Learn More" link

### Individual Solution Pages (15 pages)
Each page structure:
1. **Hero** - Solution title, icon, brief description
2. **Pain Points** - Bulleted challenges from PDF
3. **Typical Workflow Today** - How businesses handle it manually
4. **Why It's Hard** - Specific difficulties
5. **How Automation Helps** - Key benefits and features
6. **CTA** - Demo request button
7. **Related Solutions** - Links to 2-3 related niches

---

## Design System

### Colors
```css
:root {
  --primary: #2563eb;        /* Blue - trust */
  --primary-dark: #1d4ed8;
  --secondary: #059669;      /* Green - compliance */
  --text: #1f2937;
  --text-light: #6b7280;
  --bg: #ffffff;
  --bg-alt: #f9fafb;
  --border: #e5e7eb;
}
```

### Typography
- Font: System sans-serif stack
- Body: 16px, line-height 1.6
- H1: 2.5rem, H2: 2rem, H3: 1.5rem

### Components
- Cards with box-shadow
- Primary/secondary buttons
- Form inputs with focus states
- Section containers with max-width
- Responsive navigation

### Breakpoints
- Mobile: < 640px (single column)
- Tablet: 640-1024px (2 columns)
- Desktop: > 1024px (3+ columns)

---

## Files Summary

| Count | Type | Description |
|-------|------|-------------|
| 19 | HTML | Landing, platform, contact, solutions index, 15 solution pages |
| 1 | CSS | Complete stylesheet |
| 1 | JS | Mobile menu, smooth scroll, form validation |

**Total: 21 files**

---

## Verification

1. Open `static_site/index.html` in browser
2. Test all navigation links
3. Verify responsive design at 320px, 768px, 1280px widths
4. Test demo request form submission
5. Validate HTML with W3C validator
