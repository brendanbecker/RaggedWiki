# Payment Service Overview

> **Service Name:** payment-service  |  **Team:** Payments Platform  |  **Criticality:** Tier 1 (Revenue-Critical)

## Service Purpose

The Payment Service handles all financial transactions in the platform including:
- Credit card and ACH payment processing
- Subscription billing and recurring charges
- Refunds and chargebacks
- Payment method storage and tokenization
- Transaction history and reporting
- Fraud detection integration

**Business Impact**: Directly responsible for 100% of company revenue ($240M ARR). Any downtime immediately impacts revenue generation and customer trust.

## Architecture

### Technology Stack
- **Language**: Go 1.21
- **Framework**: Gin HTTP framework
- **Database**: PostgreSQL 15 (primary), Redis 7 (cache)
- **Message Queue**: RabbitMQ (async payment processing)
- **Payment Gateway Integration**: Stripe API v2023-10-16
- **Container Runtime**: Docker, deployed on Kubernetes

### Infrastructure
- **Kubernetes Cluster**: prod-us-central (GKE)
- **Namespace**: payments
- **Replicas**: 12 pods (autoscaling 6-20 based on CPU)
- **Resource Allocation**:
  - CPU: 500m request, 2000m limit
  - Memory: 1Gi request, 2Gi limit
- **Storage**:
  - PostgreSQL: 500GB SSD, daily backups
  - Redis: 16GB memory, AOF persistence enabled

### Network
- **Internal Port**: 8080 (HTTP)
- **External Endpoint**: https://api.company.com/v1/payments
- **Ingress**: Kong API Gateway (rate-limited, authenticated)
- **Egress**: Stripe API (api.stripe.com:443)

## Key Components

### Transaction Processor
Handles synchronous payment processing requests:
- Validates payment information
- Calls Stripe API to process charge
- Records transaction in database
- Returns success/failure to client

**SLO**: 95% of transactions complete within 2 seconds

### Subscription Manager
Manages recurring billing:
- Cron job runs every hour
- Identifies subscriptions due for renewal
- Queues renewal tasks to RabbitMQ
- Worker processes queue asynchronously

**SLO**: 99% of subscription renewals processed within 24 hours of due date

### Fraud Detection Integration
Real-time fraud scoring:
- Sends transaction metadata to fraud detection service (internal)
- Receives risk score (0-100)
- Blocks transactions with score >80
- Flags transactions with score 60-80 for manual review

**SLO**: Fraud detection adds <200ms latency to transaction

### Webhook Handler
Receives notifications from Stripe:
- Payment succeeded/failed
- Refund processed
- Chargeback initiated
- Updates internal transaction status accordingly

**Webhook Endpoint**: https://api.company.com/v1/payments/webhooks/stripe

## Data Model

### Core Tables

**transactions**
```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL,
    merchant_id INTEGER,
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) NOT NULL, -- pending, succeeded, failed, refunded
    stripe_payment_intent_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
```

**payment_methods**
```sql
CREATE TABLE payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL,
    stripe_payment_method_id VARCHAR(255) NOT NULL,
    type VARCHAR(50), -- card, bank_account
    last4 VARCHAR(4),
    brand VARCHAR(50), -- visa, mastercard, amex
    exp_month INTEGER,
    exp_year INTEGER,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_payment_methods_user_id ON payment_methods(user_id);
```

**subscriptions**
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL,
    plan_id INTEGER NOT NULL,
    status VARCHAR(20), -- active, canceled, past_due
    current_period_start DATE NOT NULL,
    current_period_end DATE NOT NULL,
    stripe_subscription_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
```

### Cache Keys (Redis)
- `payment_method:{user_id}` → User's default payment method (TTL: 1 hour)
- `transaction:{transaction_id}` → Recent transaction details (TTL: 24 hours)
- `rate_limit:user:{user_id}` → Rate limit counter (TTL: 1 minute)

## API Endpoints

### POST /v1/payments/charge
Process a one-time payment.

**Request**:
```json
{
  "user_id": 12345,
  "amount": 29.99,
  "currency": "USD",
  "payment_method_id": "pm_abc123",
  "idempotency_key": "unique-client-key"
}
```

**Response** (200 OK):
```json
{
  "transaction_id": "txn_xyz789",
  "status": "succeeded",
  "amount": 29.99,
  "created_at": "2024-11-20T14:30:00Z"
}
```

**Rate Limit**: 10 requests/minute per user

### POST /v1/payments/methods
Save a payment method for future use.

**Request**:
```json
{
  "user_id": 12345,
  "stripe_payment_method_id": "pm_abc123",
  "set_as_default": true
}
```

**Response** (201 Created):
```json
{
  "payment_method_id": "pm_internal_xyz",
  "last4": "4242",
  "brand": "visa",
  "exp_month": 12,
  "exp_year": 2025
}
```

### GET /v1/payments/transactions
List user's payment history.

**Query Parameters**:
- `user_id` (required): User ID
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)
- `status` (optional): Filter by status (succeeded, failed, refunded)

**Response** (200 OK):
```json
{
  "transactions": [
    {
      "id": "txn_xyz789",
      "amount": 29.99,
      "status": "succeeded",
      "created_at": "2024-11-20T14:30:00Z"
    }
  ],
  "total": 156,
  "limit": 20,
  "offset": 0
}
```

### POST /v1/payments/refund
Process a refund for a transaction.

**Request**:
```json
{
  "transaction_id": "txn_xyz789",
  "amount": 29.99,
  "reason": "customer_request"
}
```

**Response** (200 OK):
```json
{
  "refund_id": "rfnd_abc123",
  "status": "succeeded",
  "amount": 29.99
}
```

**Authorization**: Requires admin role or customer-support role.

## Monitoring and Observability

### Key Metrics

**Transaction Success Rate**:
```promql
sum(rate(payment_transactions_total{status="succeeded"}[5m]))
/
sum(rate(payment_transactions_total[5m])) * 100
```
**SLO**: >99.5% success rate

**Transaction Latency**:
```promql
histogram_quantile(0.95,
  sum(rate(payment_transaction_duration_seconds_bucket[5m])) by (le)
)
```
**SLO**: p95 < 2 seconds

**Stripe API Error Rate**:
```promql
sum(rate(payment_stripe_api_errors_total[5m]))
```
**Alert threshold**: >5 errors/minute

### Dashboards
- **Grafana**: [Payment Service Overview](https://grafana.company.com/d/payments-overview)
- **Datadog**: [Payment Transaction Health](https://app.datadoghq.com/dashboard/payments-health)

### Alerts

| Alert Name | Condition | Severity | Escalation |
|------------|-----------|----------|------------|
| Payment Service Down | `up{job="payment-service"} == 0` for 2min | SEV1 | Page SRE + Payments team |
| High Transaction Failure Rate | Failure rate >5% for 5min | SEV2 | Page Payments team |
| Stripe API Degraded | Stripe API errors >10/min for 5min | SEV2 | Page Payments team + notify Stripe support |
| Database Connection Pool Exhausted | Active connections >90% for 5min | SEV2 | Page SRE + Database team |
| Subscription Processing Backlog | Pending renewals >500 for 1 hour | SEV3 | Ticket to Payments team |

### Logs
- **Application Logs**: Shipped to Datadog via Fluentd
- **Audit Logs**: All financial transactions logged to separate audit table (7-year retention for compliance)
- **Stripe Webhook Logs**: Stored in `stripe_webhook_events` table for debugging

## Dependencies

### Critical Dependencies (Tier 1)
- **Stripe API**: Payment processing gateway
  - **Status Page**: https://status.stripe.com
  - **Fallback**: No fallback - we queue failed requests for retry
  - **Impact if down**: Cannot process new payments, existing payments unaffected

- **PostgreSQL Database**: Transaction records and payment methods
  - **Runbook**: [Database Failover](../../runbooks/database-failover.md)
  - **Impact if down**: Complete service outage

### Important Dependencies (Tier 2)
- **Redis Cache**: Performance optimization
  - **Runbook**: [Redis Cache Eviction](../../runbooks/redis-cache-eviction.md)
  - **Impact if down**: Increased database load, slower responses (2-5x latency), but service remains operational

- **RabbitMQ**: Async subscription processing
  - **Impact if down**: Subscription renewals delayed but queued for processing when restored

- **Fraud Detection Service**: Real-time fraud scoring
  - **Fallback**: If unavailable, allow transactions through (fail-open for availability)
  - **Impact if down**: Increased fraud risk, but no customer-facing impact

### Non-Critical Dependencies (Tier 3)
- **Analytics Service**: Transaction reporting
  - **Impact if down**: No impact on payment processing

## Incident Response

### Common Issues

#### Issue: High Transaction Failure Rate
**Symptoms**: Alert fires, Stripe API returning errors
**Likely Causes**:
1. Stripe API degradation (check https://status.stripe.com)
2. Database deadlocks (check PostgreSQL logs)
3. Invalid payment methods (increased card declines)

**Immediate Actions**:
1. Check Stripe status page
2. Review Datadog: Payment Service / Error Breakdown
3. If Stripe is down: Communicate to customers via status page
4. If database issue: Engage database team

**Runbook**: [Payment Service High Error Rate](../../runbooks/payment-high-error-rate.md) *(todo)*

#### Issue: Subscription Renewal Backlog
**Symptoms**: Alert fires, `pending_renewals` metric increasing
**Likely Causes**:
1. RabbitMQ worker pods scaled down or crashed
2. Database slow queries blocking workers
3. Spike in subscription renewals (end of month)

**Immediate Actions**:
1. Check worker pod count: `kubectl get pods -n payments -l component=subscription-worker`
2. Scale workers if needed: `kubectl scale deployment payment-subscription-workers --replicas=10`
3. Monitor queue depth: Should decrease within 30 minutes

**Runbook**: [Subscription Processing Backlog](../../runbooks/subscription-backlog.md) *(todo)*

### Escalation Contacts
- **Primary On-Call**: PagerDuty policy `Team-Payments`
- **Team Lead**: Sarah Chen (schen@company.com, Slack: @sarah.chen)
- **Slack Channel**: #team-payments
- **Engineering Manager**: Marcus Rodriguez (mrodriguez@company.com)

## Deployment

### CI/CD Pipeline
1. **Build**: GitHub Actions builds Docker image on merge to `main`
2. **Test**: Unit tests + integration tests run in CI
3. **Deploy to Staging**: Automatic deploy to staging environment
4. **Smoke Tests**: Automated tests run against staging
5. **Deploy to Production**: Manual approval required, rolling update

### Deployment Process
```bash
# Deployment is automated via ArgoCD
# To check deployment status:
kubectl rollout status deployment/payment-service -n payments

# To manually rollback:
kubectl rollout undo deployment/payment-service -n payments
```

### Database Migrations
- **Tool**: golang-migrate
- **Process**: Migrations run as Kubernetes Job before application deployment
- **Rollback**: Migrations include both `up` and `down` SQL

### Feature Flags
Service uses LaunchDarkly for feature flags:
- `enable-fraud-detection`: Toggle fraud detection on/off
- `enable-subscription-retries`: Enable automatic retry of failed renewals
- `new-payment-flow-v2`: A/B test new payment UI integration

## Security

### PCI Compliance
- **Scope**: Payment service handles cardholder data (CHD) via Stripe tokenization
- **Compliance**: PCI DSS Level 1 (SAQ-A)
- **Audit**: Annual PCI audit conducted by third-party QSA

### Authentication
- **API Key**: All requests require valid API key in header: `Authorization: Bearer <api_key>`
- **User Context**: API key tied to user account, enforces user-level permissions
- **Internal Services**: mTLS for service-to-service communication

### Secrets Management
- **Stripe API Keys**: Stored in Kubernetes Secrets (sealed with SealedSecrets)
- **Database Credentials**: Injected via environment variables from Vault
- **Rotation**: Secrets rotated quarterly

### Audit Trail
All payment actions logged:
- User ID
- Action (charge, refund, payment method added)
- Timestamp
- IP address
- API key used

**Retention**: 7 years (financial compliance requirement)

## Disaster Recovery

### Backup Strategy
- **Database**: Daily full backup, 15-minute WAL (write-ahead log) shipping
- **Recovery Point Objective (RPO)**: 15 minutes
- **Recovery Time Objective (RTO)**: 1 hour

### Failover Plan
1. **Database Failover**: Promote read replica to primary ([runbook](../../runbooks/database-failover.md))
2. **Application Failover**: Deploy to secondary region (manual process, 30-60 minutes)
3. **DNS Switchover**: Update Route53 to point to secondary region

### DR Testing
- **Quarterly**: Database failover drill
- **Annually**: Full multi-region failover test

## Performance Optimization

### Caching Strategy
- User payment methods cached in Redis (1 hour TTL)
- Recent transactions cached (24 hour TTL)
- Cache hit rate: ~75% (target >70%)

### Database Optimization
- Indexes on high-query columns (user_id, status, created_at)
- Connection pooling: 50 max connections per pod
- Query timeout: 5 seconds

### Rate Limiting
- Per-user rate limits: 10 transactions/minute
- Per-IP rate limits: 100 requests/minute
- Prevents abuse and protects against payment fraud

## Cost Analysis

### Monthly Operational Cost
- **Infrastructure**: $4,500/month
  - Kubernetes pods: $2,000
  - PostgreSQL RDS: $1,800
  - Redis ElastiCache: $400
  - Network egress: $300

- **External Services**: $8,200/month
  - Stripe transaction fees: 2.9% + $0.30 per transaction (~$8,000)
  - Fraud detection service: $200

**Total**: ~$12,700/month operational cost
**Revenue Generated**: $20M/month ($240M ARR)
**Cost as % of Revenue**: 0.06%

## Related Documentation

- [Payment Transaction Flow Diagram](./payment-flow.md) *(todo)*
- [Stripe Integration Guide](../../how-to/stripe-integration.md) *(todo)*
- [Payment Service High Error Rate Runbook](../../runbooks/payment-high-error-rate.md) *(todo)*
- [PCI Compliance Documentation](./pci-compliance.md) *(todo)*
- [Database Schema Documentation](./database-schema.md) *(todo)*

---

**Last Updated**: 2024-11-18
**Document Owner**: Payments Platform Team
**Review Cadence**: Quarterly
