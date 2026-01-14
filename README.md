# Payrixa

**Early-warning intelligence for healthcare revenue operations.**

---

> Healthcare doesn't fail all at once. It fails quietly.
>
> Payers change behavior. Processes slip. Revenue leaks.
> And most teams only find out after the damage is done.
>
> **Payrixa is your early-warning system.**

---

## What Payrixa Does

Payrixa watches operational and payer behavior patterns to flag what's starting to break—**before it hits revenue**.

We don't automate decisions. We tell you **where to look first**, while there's still time to act.

### Core Features

- **Payer Drift Detection** — Week-over-week analysis identifies when payer denial rates shift beyond normal variance
- **Claim Upload & Normalization** — CSV upload with automatic payer name and CPT code mapping
- **Threshold-Based Alerts** — Customizable sensitivity to flag statistically significant changes
- **Weekly Report Runs** — Scheduled analysis with historical tracking

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.12, Django 5.x |
| **Database** | SQLite (dev), PostgreSQL (production) |
| **Frontend** | Django Templates, HTML5, CSS3 |
| **Task Scheduling** | Django Management Commands |
| **Hosting** | GitHub Codespaces (dev), Cloud-ready |
| **Version Control** | Git, GitHub |

---

## Getting Started

### Prerequisites

- Python 3.12+
- pip

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Create a superuser (optional, for admin access)
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

### Running Payer Drift Analysis

```bash
# Run weekly payer drift detection for all customers
python manage.py run_weekly_payer_drift
```

---

## Project Structure

```
payrixa/
├── models.py          # Customer, ClaimRecord, ReportRun, DriftResult
├── views.py           # Upload, Settings, Drift Feed, Reports, Mappings
├── services/
│   └── payer_drift.py # Core drift detection algorithm
├── management/
│   └── commands/      # CLI commands for scheduled tasks
├── templates/         # Django HTML templates
└── static/            # CSS, images
```

---

## Roadmap

### Phase 1: Web Application (Current)
- [x] Multi-tenant customer architecture
- [x] CSV claim data upload & processing
- [x] Payer name normalization mapping
- [x] CPT code grouping
- [x] Weekly payer drift detection
- [x] Report history & results dashboard
- [ ] Email alert delivery
- [ ] PDF report generation

### Phase 2: Enhanced Analytics
- [ ] Trend visualization charts
- [ ] Custom date range analysis
- [ ] CPT group-level drift detection
- [ ] Comparative payer benchmarking
- [ ] Export functionality (CSV, Excel)

### Phase 3: Desktop Application
- [ ] Electron-based desktop client
- [ ] Local data processing option
- [ ] Offline capability with sync
- [ ] Native OS notifications

### Phase 4: Enterprise Features
- [ ] SSO / SAML authentication
- [ ] Role-based access control
- [ ] API access for integrations
- [ ] Webhook notifications
- [ ] Audit logging

---

## Understanding the Risk

Healthcare revenue cycle management operates on thin margins. A 2% shift in denial rates from a major payer can represent hundreds of thousands in delayed or lost revenue—compounded weekly.

Traditional approaches catch these problems in monthly or quarterly reviews. By then:
- Appeal windows may have closed
- Staff has moved on to new issues  
- The pattern has already repeated

Payrixa's value is **time**. Early detection means early intervention.

---

## Contributing

This project is in active development. See [CHANGELOG.md](CHANGELOG.md) for recent updates.

---

## License

Proprietary — © 2026 Byteworthy. All rights reserved.
