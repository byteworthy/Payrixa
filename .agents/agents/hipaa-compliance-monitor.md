# HIPAA Compliance Monitor Agent

**Agent Type**: hipaa_compliance
**Purpose**: Scan for PHI exposure, audit logging gaps, compliance violations
**Trigger Points**: pre-deploy, weekly scheduled check

---

## What This Agent Does

1. **PHI Exposure Scan**: Detects PHI in code, logs, database schema
2. **Encryption Check**: Validates sensitive fields are encrypted
3. **Audit Logging**: Ensures all models have audit trails
4. **Data Retention**: Verifies 7-year retention policies
5. **Session Security**: Validates 30-minute timeout and HTTPOnly cookies

---

## Critical Violations (Block Deployment)

### 1. PHI in Database Schema
- Table/column names contain "patient", "ssn", "dob"
- Test fixtures contain real PHI

### 2. Missing Audit Logging
- Customer-scoped models without `AuditlogHistoryField`
- Critical operations not logged

### 3. Unencrypted Sensitive Fields
- Fields that should be encrypted aren't using `EncryptedCharField`

### 4. Session Security Issues
- Session timeout > 30 minutes
- HTTPOnly cookies disabled
- HTTPS not enforced

---

## Usage

```bash
# Full compliance check
python manage.py check_hipaa_compliance

# Check specific area
python manage.py check_hipaa_compliance --check phi-exposure

# Generate compliance report
python manage.py check_hipaa_compliance --report compliance_report.json

# Pre-deploy gate
python manage.py check_hipaa_compliance --fail-on critical
```

---

## Output

```
🔍 HIPAA Compliance Monitor
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Running compliance checks...

✅ Technical Safeguards (§164.312)
   ✅ Access Control: Session timeout configured
   ✅ Audit Controls: Audit logging enabled
   ✅ Integrity: PHI detection active
   ✅ Transmission Security: HTTPS enforced

❌ VIOLATIONS (2)
   upstream/models.py:45 - Missing audit logging on Settings model
   upstream/fixtures/test_data.json - Contains potential PHI

━━━━━━━━━━━━━━━━━━━━━━━━━━━
Compliance Status: 95% (2 issues)
❌ FIX VIOLATIONS BEFORE DEPLOYMENT
```

---

## Compliance Checklist

- [ ] All customer-scoped models have audit logging
- [ ] Session timeout = 30 minutes
- [ ] HTTPOnly cookies enabled
- [ ] HTTPS enforced in production
- [ ] PHI detection on all user inputs
- [ ] Test data contains no real PHI
- [ ] Sensitive fields encrypted
- [ ] 7-year data retention configured
