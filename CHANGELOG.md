# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-01-14

### Added
- **REST API Layer** — Full Django REST Framework implementation
  - JWT authentication with token refresh
  - Multi-tenant permission system (IsCustomerMember)
  - ViewSets for all core models
  - OpenAPI documentation (Swagger/ReDoc) at `/api/v1/docs/`
  - Dashboard endpoint with aggregate statistics
  - Health check endpoint
- **Security & Compliance**
  - django-auditlog for HIPAA-compliant audit trails
  - django-encrypted-model-fields for PHI encryption
  - Enhanced session security (1-hour timeout, secure cookies)
  - 12-character minimum password requirement
  - Rate limiting on API endpoints
- **Demo Data Fixture** — `python manage.py loaddata demo_data` for onboarding
- **Enhanced Configuration**
  - Comprehensive `.env.example` with all settings documented
  - PostgreSQL configuration ready (commented for production)
  - CORS settings for frontend clients
  - Email configuration via Anymail

### Changed
- Renamed project from 'DriftWatch' to 'Payrixa' across codebase
- Reorganized settings.py with clear section headers
- README polished with brand voice, tech stack rationale, and roadmap
- Minimum password length increased to 12 characters

### Technical
- Added packages: djangorestframework, djangorestframework-simplejwt, django-cors-headers, drf-spectacular, django-auditlog, django-encrypted-model-fields, django-anymail, weasyprint, psycopg2-binary, django-q2

## [0.1.0] - 2026-01-12

### Added
- Initial project structure with Django 5.x
- Multi-tenant Customer model
- ClaimRecord model with CSV upload processing
- Payer name normalization (PayerMapping)
- CPT code grouping (CPTGroupMapping)
- Weekly payer drift detection algorithm
- ReportRun and DriftEvent models
- Management command: `run_weekly_payer_drift`
- Basic web portal templates

---

## Roadmap

### Phase 2 (Planned)
- Trend visualization charts
- Custom date range analysis
- Email alert delivery with PDF attachments
- CPT group-level drift detection

### Phase 3 (Planned)
- Electron desktop application
- Offline capability with sync
- Native OS notifications

### Phase 4 (Planned)
- SSO/SAML authentication
- Role-based access control
- Webhook integrations
- API rate limit dashboard
