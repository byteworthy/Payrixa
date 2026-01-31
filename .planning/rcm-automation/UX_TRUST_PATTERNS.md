# UX Patterns for Building Trust in Autonomous RCM

**Transparency, Reversibility, and Gradual Autonomy**

## Executive Summary

Autonomous billing automation faces a fundamental trust challenge: customers must believe the system won't create compliance liability or revenue loss. This guide defines UX patterns that build trust through transparency (show AI reasoning), reversibility (allow undo), and gradual autonomy (Stage 1 → 4 progression).

**Key Principles:**
1. **Post-Action Transparency:** Every autonomous action includes what/why/result/undo
2. **Undo by Action Impact:** Match recovery to risk (session vs. time-windowed vs. manual)
3. **Trust Calibration:** 4-stage progression from observe → full autonomy
4. **Clear Visual Hierarchy:** Auto/Review/Escalate status immediately visible

---

## Post-Action Notifications

### Three-Tier Severity Classification

#### High Attention (Modal + Push + Email)
**When to Use:**
- Denials received
- Payment failures
- Compliance escalations
- Large dollar actions (>$10K)
- Red-line violations attempted

**Implementation:**
```typescript
interface HighAttentionNotification {
  severity: 'high';
  delivery: ['modal', 'push', 'email'];
  title: string;
  message: string;
  actionButton?: {
    label: string;
    action: () => void;
  };
  dismissButton?: {
    label: string;
  };
}

const exampleDenialNotification: HighAttentionNotification = {
  severity: 'high',
  delivery: ['modal', 'push', 'email'],
  title: 'Claim Denied - Action Required',
  message: 'Claim #12345 was denied by Medicare. AI recommends submitting appeal (87% success probability based on similar cases).',
  actionButton: {
    label: 'Review Appeal',
    action: () => navigate('/appeals/12345'),
  },
  dismissButton: {
    label: 'Review Later',
  },
};
```

#### Medium Attention (In-App Toast)
**When to Use:**
- Claims submitted successfully
- Status updates received
- Authorizations expiring soon (>7 days)
- Queue assignments

**Implementation:**
```typescript
interface MediumAttentionNotification {
  severity: 'medium';
  delivery: ['toast'];
  title: string;
  message: string;
  duration: number; // milliseconds
  action?: {
    label: string;
    href: string;
  };
}

const exampleSubmissionNotification: MediumAttentionNotification = {
  severity: 'medium',
  delivery: ['toast'],
  title: 'Claim Submitted',
  message: 'Claim #12346 submitted to Anthem BCBS (96% confidence)',
  duration: 5000,
  action: {
    label: 'View Details',
    href: '/claims/12346',
  },
};
```

#### Low Attention (Daily/Weekly Digest)
**When to Use:**
- Summary of autonomous actions
- Performance metrics
- Routine status checks
- Bulk updates

**Implementation:**
```typescript
interface DigestNotification {
  severity: 'low';
  delivery: ['email_digest'];
  frequency: 'daily' | 'weekly';
  sections: DigestSection[];
}

interface DigestSection {
  title: string;
  metrics: Metric[];
  highlights?: string[];
}

const exampleWeeklyDigest: DigestNotification = {
  severity: 'low',
  delivery: ['email_digest'],
  frequency: 'weekly',
  sections: [
    {
      title: 'Autonomous Actions This Week',
      metrics: [
        { label: 'Claims Submitted', value: '1,247', change: '+8%' },
        { label: 'Average Confidence', value: '96.2%', change: '+1.2%' },
        { label: 'Total Submitted', value: '$2.4M', change: '+12%' },
      ],
      highlights: [
        '98% of claims submitted without human review',
        'Zero compliance escalations this week',
        'Average submission time: 2.3 hours (vs 18 hours industry avg)',
      ],
    },
  ],
};
```

### Required Information in Every Notification

**The 5 W's of Automation Transparency:**

1. **What** action was taken
   - "Claim #12345 submitted to Medicare"
   - "CPT code corrected from 99213 to 99214"

2. **Why** (AI reasoning + confidence)
   - "96% confidence based on documentation completeness and payer history"
   - "Similar claims from this payer approved 94% of the time"

3. **Result** (success/failure)
   - "Successfully submitted at 2:34 PM"
   - "Submission failed: payer portal unavailable (will retry in 1 hour)"

4. **Undo window** (if applicable)
   - "You can undo this action for the next 2 hours"
   - "Claim still in clearinghouse - undo available until 5:00 PM"

5. **Link to audit log** (full details)
   - "View complete audit trail →"

**Example Notification:**
```
🟢 Claim Submitted Automatically

Claim #12345 submitted to Medicare Part B

WHY: 96% confidence
- Complete documentation (ICD-10 Z00.00)
- CPT 99213 matches clinical notes
- Similar claims approved 94% of time

RESULT: Successfully submitted at 2:34 PM
Expected payment in 14-18 days

UNDO: Available for next 2 hours (until 4:34 PM)
[Undo Submission] [View Audit Trail →]
```

---

## Undo Functionality by Action Impact

### Session-Based Undo (Immediate)
**Use For:**
- Status checks (no external impact)
- Eligibility queries (read-only)
- Internal data updates (not submitted externally)

**Implementation:**
```python
def undo_status_check(execution_log_id: int, user: User):
    """Immediate undo for read-only actions"""
    log = ExecutionLog.objects.get(id=execution_log_id)

    # Verify action is undo-able
    if log.action_taken not in ['status_check', 'eligibility_query']:
        raise ValueError("Action cannot be undone")

    # Mark as reversed
    log.was_reversed = True
    log.reversal_timestamp = timezone.now()
    log.reversal_reason = "User requested immediate undo"
    log.reversed_by = user
    log.save()

    # No external action needed (read-only)
    return {'success': True, 'message': 'Action undone'}
```

### Time-Windowed Undo (2-24 Hours)
**Use For:**
- Claim submissions (while in clearinghouse)
- Code changes (before payer submission)
- Prior auth requests (before payer receipt)

**Implementation:**
```python
def undo_claim_submission(execution_log_id: int, user: User):
    """Time-windowed undo for claims still in clearinghouse"""
    log = ExecutionLog.objects.get(id=execution_log_id)
    claim = log.details['claim_id']

    # Check if still in undo window
    undo_deadline = log.executed_at + timedelta(hours=2)
    if timezone.now() > undo_deadline:
        raise ValueError(f"Undo window expired at {undo_deadline}")

    # Check if claim already sent to payer
    clearinghouse_status = check_clearinghouse_status(claim)
    if clearinghouse_status == 'sent_to_payer':
        raise ValueError("Claim already sent to payer - cannot undo")

    # Cancel submission in clearinghouse
    cancel_clearinghouse_submission(claim)

    # Mark as reversed
    log.was_reversed = True
    log.reversal_timestamp = timezone.now()
    log.reversal_reason = "User cancelled submission within undo window"
    log.reversed_by = user
    log.save()

    # Update claim status
    claim_record = ClaimRecord.objects.get(id=claim)
    claim_record.status = 'cancelled'
    claim_record.save()

    return {'success': True, 'message': 'Claim submission cancelled'}
```

### Soft-Delete + Recovery (30 Days)
**Use For:**
- Actions before external submission
- Internal database changes
- Draft appeals/letters

**Implementation:**
```python
class SoftDeletedAction(models.Model):
    """Recoverable actions with 30-day retention"""

    execution_log = models.ForeignKey(ExecutionLog, on_delete=models.CASCADE)
    original_data = models.JSONField()  # Full state backup
    deleted_at = models.DateTimeField(auto_now_add=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    permanent_delete_at = models.DateTimeField()  # deleted_at + 30 days

    class Meta:
        indexes = [
            models.Index(fields=['permanent_delete_at']),
        ]

def soft_delete_action(execution_log_id: int, user: User):
    """Soft delete with 30-day recovery window"""
    log = ExecutionLog.objects.get(id=execution_log_id)

    # Backup current state
    SoftDeletedAction.objects.create(
        execution_log=log,
        original_data=log.details,
        deleted_by=user,
        permanent_delete_at=timezone.now() + timedelta(days=30),
    )

    # Mark as deleted (but keep in DB)
    log.was_reversed = True
    log.reversal_timestamp = timezone.now()
    log.reversal_reason = "Soft deleted - recoverable for 30 days"
    log.reversed_by = user
    log.save()

def recover_soft_deleted_action(execution_log_id: int, user: User):
    """Recover action within 30-day window"""
    soft_deleted = SoftDeletedAction.objects.get(
        execution_log_id=execution_log_id
    )

    if timezone.now() > soft_deleted.permanent_delete_at:
        raise ValueError("Recovery window expired")

    # Restore original data
    log = soft_deleted.execution_log
    log.details = soft_deleted.original_data
    log.was_reversed = False
    log.save()

    # Delete soft delete record
    soft_deleted.delete()

    return {'success': True, 'message': 'Action recovered'}
```

### Cannot Be Reversed (Manual Intervention Required)
**Applies To:**
- Claims adjudicated by payers
- Appeals submitted to payers
- Actions with external legal implications
- Payments already received

**Implementation:**
```python
def attempt_undo(execution_log_id: int, user: User):
    """Check if action can be undone"""
    log = ExecutionLog.objects.get(id=execution_log_id)

    # Check if already adjudicated
    if log.action_taken == 'submit_claim':
        claim = ClaimRecord.objects.get(id=log.details['claim_id'])
        if claim.status in ['paid', 'denied', 'adjudicated']:
            return {
                'can_undo': False,
                'reason': 'Claim already adjudicated by payer',
                'manual_steps': [
                    'Contact payer to request correction',
                    'File corrected claim if necessary',
                    'Document reason for correction in notes',
                ],
            }

    # Check if appeal submitted
    if log.action_taken == 'submit_appeal':
        return {
            'can_undo': False,
            'reason': 'Appeal already submitted to payer',
            'manual_steps': [
                'Contact payer appeals department',
                'Request withdrawal of appeal in writing',
                'Document withdrawal reason for compliance',
            ],
        }

    # Action is undo-able
    return {'can_undo': True}
```

---

## Trust Calibration Framework: 4-Stage Progression

### Stage 1: Observe (Weeks 1-2)
**Philosophy:** AI recommends, human takes all actions

**UX Pattern:**
```
┌─────────────────────────────────────────────────┐
│  🤖 AI Recommendation                           │
├─────────────────────────────────────────────────┤
│  We recommend submitting this claim:            │
│                                                 │
│  Claim #12345 - Medicare Part B                │
│  Amount: $285.00                                │
│  Confidence: 96%                                │
│                                                 │
│  ✓ Documentation complete                      │
│  ✓ CPT code matches notes                     │
│  ✓ Similar claims approved 94% of time        │
│                                                 │
│  [Submit Claim] [Reject] [View Details]       │
└─────────────────────────────────────────────────┘
```

**Implementation:**
```python
def stage1_recommend_action(claim: ClaimRecord):
    """Stage 1: Show recommendation, wait for human decision"""
    score = claim.score

    recommendation = {
        'claim_id': claim.id,
        'recommended_action': score.recommended_action,
        'confidence': score.overall_confidence,
        'reasoning': score.prediction_reasoning,
        'supporting_evidence': [
            {'label': 'Documentation complete', 'status': 'pass'},
            {'label': 'CPT code matches notes', 'status': 'pass'},
            {'label': 'Similar claims approved 94% of time', 'status': 'info'},
        ],
        'actions': [
            {'label': 'Submit Claim', 'action': 'submit'},
            {'label': 'Reject', 'action': 'reject'},
            {'label': 'View Details', 'action': 'details'},
        ],
    }

    # Log recommendation (but don't execute)
    ExecutionLog.objects.create(
        customer=claim.customer,
        action_taken='recommend_only',  # Stage 1 marker
        result='awaiting_human_decision',
        details=recommendation,
    )

    return recommendation
```

### Stage 2: Suggest (Weeks 3-4)
**Philosophy:** AI pre-fills actions, human confirms with one click

**UX Pattern:**
```
┌─────────────────────────────────────────────────┐
│  Ready to Submit?                               │
├─────────────────────────────────────────────────┤
│  Claim #12345 - Medicare Part B                │
│  Amount: $285.00                                │
│  Confidence: 96%                                │
│                                                 │
│  ✓ Pre-filled with AI recommendation           │
│  ✓ One-click confirmation                      │
│                                                 │
│  [✓ Confirm & Submit] [Edit] [Cancel]         │
└─────────────────────────────────────────────────┘
```

**Implementation:**
```python
def stage2_suggest_action(claim: ClaimRecord):
    """Stage 2: Pre-fill action, require confirmation"""
    score = claim.score

    # Pre-populate submission form
    submission_form = {
        'claim_id': claim.id,
        'payer': claim.payer,
        'amount': claim.allowed_amount,
        'cpt_codes': claim.cpt,
        'diagnosis_codes': claim.diagnosis_codes,
        'pre_filled': True,  # Indicate AI pre-filled
        'confidence': score.overall_confidence,
    }

    # Show one-click confirmation
    return {
        'form': submission_form,
        'confirmation_required': True,
        'message': 'AI has pre-filled this submission. Review and confirm.',
    }

def stage2_confirm_action(claim_id: int, user: User):
    """User confirmed AI suggestion"""
    claim = ClaimRecord.objects.get(id=claim_id)

    # Execute action
    submit_claim_to_payer(claim)

    # Log with human confirmation
    ExecutionLog.objects.create(
        customer=claim.customer,
        action_taken='submit_claim',
        result='success',
        user_id=user.username,
        user_role=user.role,
        business_justification='User confirmed AI pre-filled submission',
        details={'claim_id': claim_id, 'stage': 'suggest'},
    )
```

### Stage 3: Act + Notify (Weeks 5-8)
**Philosophy:** AI executes automatically, human notified after with undo

**UX Pattern:**
```
┌─────────────────────────────────────────────────┐
│  🟢 Claim Submitted                             │
├─────────────────────────────────────────────────┤
│  Claim #12345 submitted to Medicare at 2:34 PM │
│                                                 │
│  Confidence: 96%                                │
│  Expected payment: 14-18 days                  │
│                                                 │
│  ⏱️  Undo available for 2 hours (until 4:34 PM)│
│                                                 │
│  [Undo Submission] [View Audit Trail →]       │
└─────────────────────────────────────────────────┘
```

**Implementation:**
```python
def stage3_execute_and_notify(claim: ClaimRecord):
    """Stage 3: Execute autonomously, notify user after"""
    score = claim.score
    profile = claim.customer.automation_profile

    # Execute action autonomously
    result = submit_claim_to_payer(claim)

    # Log execution
    log = ExecutionLog.objects.create(
        customer=claim.customer,
        action_taken='submit_claim',
        result='success',
        user_id='SYSTEM',  # Autonomous
        user_role='automation_agent',
        business_justification=f'Autonomous execution (confidence {score.overall_confidence:.1%})',
        confidence_score=score.overall_confidence,
        details={
            'claim_id': claim.id,
            'stage': 'act_notify',
            'undo_deadline': timezone.now() + timedelta(hours=profile.undo_window_hours),
        },
    )

    # Send post-action notification
    send_notification(
        customer=claim.customer,
        severity='medium',
        title='Claim Submitted',
        message=f'Claim #{claim.id} submitted to {claim.payer} at {timezone.now():%I:%M %p}',
        actions=[
            {'label': 'Undo Submission', 'action': f'/undo/{log.id}'},
            {'label': 'View Audit Trail', 'action': f'/audit/{log.id}'},
        ],
    )

    return {'success': True, 'execution_log_id': log.id}
```

### Stage 4: Full Autonomy (Week 9+)
**Philosophy:** AI executes silently, exceptions escalated, summary reports only

**UX Pattern:**
```
┌─────────────────────────────────────────────────┐
│  📊 Daily Automation Summary                    │
├─────────────────────────────────────────────────┤
│  347 claims submitted automatically today       │
│  Average confidence: 95.2%                      │
│  Total submitted: $428,320                      │
│                                                 │
│  🔴 3 escalations require your review           │
│                                                 │
│  [View Activity Feed] [Review Escalations →]   │
└─────────────────────────────────────────────────┘
```

**Implementation:**
```python
def stage4_silent_execution(claim: ClaimRecord):
    """Stage 4: Execute silently, only notify on exceptions"""
    score = claim.score

    # Execute without notification (unless escalation)
    result = submit_claim_to_payer(claim)

    # Log execution
    ExecutionLog.objects.create(
        customer=claim.customer,
        action_taken='submit_claim',
        result='success',
        user_id='SYSTEM',
        user_role='automation_agent',
        business_justification=f'Silent autonomous execution (Stage 4)',
        confidence_score=score.overall_confidence,
        details={'claim_id': claim.id, 'stage': 'full_autonomy'},
    )

    # Only notify if exception
    if score.automation_tier == 3:  # Escalation
        send_notification(
            customer=claim.customer,
            severity='high',
            title='Escalation Required',
            message=f'Claim #{claim.id} requires human review: {score.red_line_reason}',
        )

    # Otherwise, include in daily summary (no immediate notification)
    return {'success': True, 'notification': 'summary_only'}

def generate_daily_summary(customer: Customer):
    """Generate end-of-day summary for Stage 4 customers"""
    today = timezone.now().date()
    logs = ExecutionLog.objects.filter(
        customer=customer,
        executed_at__date=today,
        action_taken='submit_claim',
    )

    summary = {
        'total_claims': logs.count(),
        'avg_confidence': logs.aggregate(Avg('confidence_score'))['confidence_score__avg'],
        'total_amount': logs.aggregate(Sum('details__amount'))['details__amount__sum'],
        'escalations': logs.filter(result='escalated').count(),
    }

    # Send end-of-day digest
    send_notification(
        customer=customer,
        severity='low',
        delivery='email_digest',
        title='Daily Automation Summary',
        message=render_template('daily_summary.html', summary),
    )
```

---

## Dashboard Design Principles

### Clear Visual Hierarchy

**Three-Status Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  🟢 AUTOMATED ACTIONS (No Action Needed)                │
│  ─────────────────────────────────────────────────────  │
│  347 claims submitted automatically today               │
│  95.2% average confidence                               │
│  $428,320 total submitted                               │
│  [View Activity Feed →]                                 │
├─────────────────────────────────────────────────────────┤
│  🟡 NEEDS REVIEW (AI Recommends)                        │
│  ─────────────────────────────────────────────────────  │
│  23 claims queued for your review                       │
│  Average confidence: 82%                                │
│  Total value: $89,450                                   │
│  [Review Queue →]                                       │
├─────────────────────────────────────────────────────────┤
│  🔴 REQUIRES ACTION (Human Only)                        │
│  ─────────────────────────────────────────────────────  │
│  8 escalations awaiting assignment                      │
│  3 appeals need clinical justification                  │
│  2 fraud alerts                                         │
│  [View Escalations →]                                   │
└─────────────────────────────────────────────────────────┘
```

### Real-Time Activity Feed

**Component Structure:**
```typescript
interface ActivityFeedItem {
  id: string;
  timestamp: Date;
  action: string;
  claim_id: string;
  confidence: number;
  automation_tier: 1 | 2 | 3;
  status: 'success' | 'pending' | 'failed' | 'escalated';
  amount: number;
  undo_available: boolean;
  undo_deadline?: Date;
}

const ActivityFeed: React.FC = () => {
  const [filter, setFilter] = useState<'all' | 'auto' | 'review' | 'escalate'>('all');

  return (
    <div className="activity-feed">
      <div className="filters">
        <button onClick={() => setFilter('all')}>All Actions</button>
        <button onClick={() => setFilter('auto')}>Automated</button>
        <button onClick={() => setFilter('review')}>Needs Review</button>
        <button onClick={() => setFilter('escalate')}>Escalated</button>
      </div>

      <div className="feed-items">
        {items.map(item => (
          <ActivityFeedItem
            key={item.id}
            {...item}
            onUndo={() => undoAction(item.id)}
            onViewDetails={() => navigate(`/audit/${item.id}`)}
          />
        ))}
      </div>
    </div>
  );
};
```

### Automation Performance Metrics

**Dashboard Cards:**
```typescript
interface PerformanceMetrics {
  throughput: {
    today: number;
    week: number;
    change_percent: number;
  };
  accuracy: {
    human_agreement_rate: number;
    false_positive_rate: number;
  };
  time_saved: {
    hours_today: number;
    hours_week: number;
  };
  financial_impact: {
    faster_collection: number;
    denial_reduction: number;
  };
}

const PerformanceCard: React.FC<{ metric: Metric }> = ({ metric }) => (
  <div className="performance-card">
    <div className="metric-value">
      {metric.value}
      <span className={metric.change > 0 ? 'positive' : 'negative'}>
        {metric.change > 0 ? '↑' : '↓'} {Math.abs(metric.change)}%
      </span>
    </div>
    <div className="metric-label">{metric.label}</div>
    <div className="metric-trend">
      <SparklineChart data={metric.history} />
    </div>
  </div>
);
```

---

## Implementation Checklist

### Phase 1: Notification System (Weeks 1-2)
- [ ] Build three-tier notification delivery system
- [ ] Implement modal/push/email/toast components
- [ ] Create daily/weekly digest email templates
- [ ] Add 5 W's (what/why/result/undo/audit) to all notifications

### Phase 2: Undo Functionality (Weeks 3-4)
- [ ] Implement session-based undo (immediate)
- [ ] Build time-windowed undo with deadline tracking
- [ ] Create soft-delete recovery system
- [ ] Document cannot-be-reversed actions with manual steps

### Phase 3: Trust Calibration UI (Weeks 5-8)
- [ ] Build Stage 1 recommendation UI
- [ ] Create Stage 2 one-click confirmation flow
- [ ] Implement Stage 3 post-action notification
- [ ] Design Stage 4 silent execution with summaries

### Phase 4: Dashboard (Weeks 9-12)
- [ ] Build three-status hierarchy layout
- [ ] Create real-time activity feed with filters
- [ ] Implement exception queue UI
- [ ] Add automation performance metrics

---

**Document Version:** 1.0
**Last Updated:** 2026-01-31
**Owner:** Product Design Team
**Status:** Ready for Implementation
