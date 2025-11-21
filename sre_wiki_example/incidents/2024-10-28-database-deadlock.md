# Incident Postmortem: Database Deadlock Cascade

> **Incident ID:** INC-2024-1028-001  |  **Severity:** SEV1  |  **Duration:** 2h 15m  |  **Date:** 2024-10-28

## Executive Summary

On October 28, 2024, between 14:30 and 16:45 UTC, the production PostgreSQL database experienced a cascade of deadlocks that rendered the payment processing service unavailable. Approximately 3,200 payment transactions were delayed, and 47 transactions failed completely requiring manual intervention. The root cause was a combination of a newly deployed query pattern and an existing database schema design flaw that created circular lock dependencies.

**Impact**: $12,400 in delayed revenue, 47 failed transactions, 2.5 hours of complete payment processing downtime.

## Timeline (All Times UTC)

| Time | Event |
|------|-------|
| 14:30 | Payment service v2.8.0 deployed to production |
| 14:32 | First deadlock errors appear in application logs |
| 14:34 | Error rate climbs to 5%, PagerDuty alert fires |
| 14:37 | On-call engineer investigates, sees deadlock errors |
| 14:40 | Database team paged for assistance |
| 14:45 | Second wave of deadlocks, error rate hits 25% |
| 14:50 | Decision made to rollback payment service to v2.7.5 |
| 14:55 | Rollback initiated, Kubernetes rolling update begins |
| 15:02 | Rollback complete, but deadlocks continue |
| 15:10 | Database team identifies query pattern causing locks |
| 15:15 | Manual intervention: Kill blocking sessions |
| 15:18 | Deadlocks stop, but backlog of 3,200 pending transactions |
| 15:30 | Transaction processing resumes |
| 16:15 | Backlog cleared |
| 16:45 | Incident declared resolved, monitoring continues |

## Root Cause Analysis

### The Problematic Query Pattern

The v2.8.0 deployment introduced a new transaction processing flow that updated three tables in this order:

```sql
BEGIN;
-- Step 1: Update user balance
UPDATE user_accounts SET balance = balance - 100 WHERE user_id = 12345;

-- Step 2: Create transaction record
INSERT INTO transactions (user_id, amount, status) VALUES (12345, 100, 'pending');

-- Step 3: Update merchant balance
UPDATE merchant_accounts SET balance = balance + 100 WHERE merchant_id = 789;
COMMIT;
```

### The Existing Schema Flaw

The `transactions` table had foreign key constraints to both `user_accounts` and `merchant_accounts`:

```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user_accounts(id),
    merchant_id INTEGER REFERENCES merchant_accounts(id),
    amount DECIMAL,
    status VARCHAR(20)
);
```

### The Deadlock Scenario

When two concurrent transactions involved the same user and merchant (common for recurring subscriptions):

**Transaction A**:
1. Locks `user_accounts` row (user_id=12345)
2. Attempts to insert into `transactions` (requires lock check on `merchant_accounts`)
3. Waits for `merchant_accounts` lock held by Transaction B

**Transaction B** (processing different order for same merchant):
1. Locks `merchant_accounts` row (merchant_id=789)
2. Attempts to insert into `transactions` (requires lock check on `user_accounts`)
3. Waits for `user_accounts` lock held by Transaction A

**Result**: Classic deadlock. PostgreSQL kills one transaction, but high volume causes cascade of deadlocks across hundreds of concurrent transactions.

### Why This Didn't Occur in Staging

Staging environment had:
- 100x less transaction volume (deadlocks are volume-dependent)
- Different transaction mix (fewer recurring subscriptions to same merchants)
- No load testing of concurrent same-user-same-merchant scenarios

## Impact Details

### Customer Impact
- **3,200 customers**: Experienced 15-60 minute payment processing delays
- **47 customers**: Payment failed completely, required manual retry
- **12 customers**: Submitted support tickets during incident
- **Customer satisfaction**: 4 one-star app reviews citing payment issues

### Business Impact
- **Revenue**: $12,400 in delayed payment processing (all eventually recovered)
- **Transaction fees**: $340 in additional fees from payment processor retries
- **Support cost**: Estimated 8 hours of customer support time

### Service Level Impact
- **Payment Processing SLO**: 99.9% availability target
  - Actual: 96.2% (2h 15m downtime in 30-day window)
  - **SLO breached**: Error budget exhausted for the month
- **Transaction Success Rate SLO**: 99.5% success target
  - Actual: 98.7% (47 failures in 3,200 attempts)
  - **SLO maintained**: Within acceptable error budget

## What Went Well

1. **Fast detection**: Monitoring detected the issue within 2 minutes of first deployment
2. **Clear alerts**: PagerDuty alert included deadlock error text, giving immediate context
3. **Database expertise**: Database team responded quickly with query analysis tools
4. **Communication**: Status page updated within 10 minutes, customer support notified
5. **Backlog recovery**: Transaction retry logic successfully processed all delayed payments

## What Went Wrong

1. **Insufficient testing**: Load tests didn't simulate concurrent same-merchant scenarios
2. **Rollback ineffective**: We assumed application rollback would resolve database state issues
3. **Schema design**: Foreign key constraints enabled, but lock ordering not considered
4. **No circuit breaker**: Payment service didn't stop retrying during database deadlocks
5. **Documentation gap**: Database lock ordering best practices not documented for developers

## Corrective Actions

### Immediate (Completed within 24 hours)

| Action | Owner | Status | Completion Date |
|--------|-------|--------|-----------------|
| Revert to v2.7.5 permanently | Platform SRE | ✅ Complete | 2024-10-28 |
| Document database lock ordering requirements | Database SRE | ✅ Complete | 2024-10-29 |
| Add deadlock monitoring to Grafana | Monitoring SRE | ✅ Complete | 2024-10-29 |
| Process failed transactions manually | Payment Team | ✅ Complete | 2024-10-28 |

### Short-term (Completed within 1 week)

| Action | Owner | Status | Target Date |
|--------|-------|--------|-------------|
| Redesign transaction flow with consistent lock ordering | Payment Team | ✅ Complete | 2024-11-01 |
| Add load test for concurrent same-merchant transactions | QA Team | ✅ Complete | 2024-10-30 |
| Implement circuit breaker for payment service database calls | Payment Team | ✅ Complete | 2024-11-02 |
| Review all foreign key constraints for deadlock potential | Database SRE | ✅ Complete | 2024-11-04 |
| Create runbook for database deadlock incidents | SRE Team | ✅ Complete | 2024-10-31 |

### Long-term (Completed within 1 month)

| Action | Owner | Status | Target Date |
|--------|-------|--------|-------------|
| Refactor schema to minimize foreign key constraints | Database Team | ✅ Complete | 2024-11-15 |
| Implement optimistic locking where possible | Payment Team | ✅ Complete | 2024-11-20 |
| Add pre-deployment deadlock analysis tool | Platform SRE | ✅ Complete | 2024-11-25 |
| Update deployment checklist with concurrency testing requirement | SRE Team | ✅ Complete | 2024-11-05 |
| Conduct training on database lock patterns | Database SRE | ✅ Complete | 2024-11-12 |

## Lessons Learned

### Technical Lessons

1. **Lock ordering matters**: Always acquire locks in a consistent order across all transactions
   - Best practice: Order by table name alphabetically, or by primary key value
   - Document lock ordering requirements in database schema documentation

2. **Foreign keys have hidden costs**: Foreign key constraints require shared locks during validation
   - Consider application-level referential integrity for high-throughput tables
   - Document trade-offs between data integrity and lock contention

3. **Staging must mirror production load**: Volume-dependent issues require realistic load testing
   - Implement continuous load testing with production-like traffic patterns
   - Include worst-case scenarios (concurrent updates to hot rows)

4. **Circuit breakers are essential**: Don't retry blindly during database issues
   - Implement circuit breakers on all database-dependent services
   - Fast failure is better than cascade of retries

### Process Lessons

1. **Rollback assumptions**: Don't assume application rollback fixes database state
   - Database state persists after application changes
   - Have separate runbooks for application vs. database issues

2. **Deployment validation**: Current deployment validation only checks for crashes, not concurrency issues
   - Add synthetic load tests that run for 10 minutes post-deployment
   - Include concurrent transaction scenarios in smoke tests

3. **Documentation accessibility**: Developers didn't have easy access to database best practices
   - Create developer-focused database guide
   - Include lock ordering patterns in code review checklist

## Detection and Monitoring Improvements

### New Dashboards
- **Database Deadlock Dashboard**: Real-time deadlock count, affected queries, duration
- **Payment Transaction Health**: Success rate, latency, retry count

### New Alerts
```yaml
- alert: DatabaseDeadlocksIncreasing
  expr: rate(postgres_deadlocks_total[5m]) > 1
  for: 1m
  severity: warning
  description: "Database is experiencing {{ $value }} deadlocks/sec"

- alert: HighPaymentTransactionRetries
  expr: rate(payment_transaction_retries_total[5m]) > 10
  for: 2m
  severity: warning
  description: "Payment transactions retrying at {{ $value }}/sec"
```

### Query Performance Logging
Added slow query logging for transactions holding locks >500ms:
```sql
ALTER DATABASE payments SET log_lock_waits = on;
ALTER DATABASE payments SET deadlock_timeout = '500ms';
```

## Cost of Incident

| Category | Cost |
|----------|------|
| Engineering time (6 engineers × 3 hours) | $5,400 |
| Customer support time (4 agents × 2 hours) | $800 |
| Payment processor retry fees | $340 |
| Estimated customer goodwill (refunds, credits) | $2,000 |
| **Total estimated cost** | **$8,540** |

**Note**: Does not include opportunity cost of delayed feature development or potential customer churn.

## References

- [Database Failover Runbook](../runbooks/database-failover.md)
- [Payment Service Architecture](../apps/payment-service/architecture.md)
- [Incident Response Process](../process/incident-response.md)
- [PostgreSQL Lock Monitoring Guide](../how-to/postgres-lock-monitoring.md)

## Postmortem Meeting

- **Date**: 2024-10-30
- **Attendees**: SRE team, Database team, Payment team, Engineering leadership
- **Recording**: [Zoom recording](https://company.zoom.us/rec/share/xxx) (internal only)
- **Action item tracker**: [Jira board](https://company.atlassian.net/browse/INC-2024-1028) (internal only)

## Sign-off

| Role | Name | Date |
|------|------|------|
| Incident Commander | Alex Rivera | 2024-10-31 |
| Database SRE Lead | Jamie Chen | 2024-10-31 |
| Payment Service Lead | Morgan Taylor | 2024-10-31 |
| VP Engineering | Casey Anderson | 2024-11-01 |
