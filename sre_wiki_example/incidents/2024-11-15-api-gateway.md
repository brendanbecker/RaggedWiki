# Postmortem: API Gateway Outage (2024-11-15)

> **Severity:** SEV1  |  **Duration:** 47 minutes  |  **Services Impacted:** API Gateway, Mobile API  |  **IC:** J. Nguyen  |  **Scribe:** M. Ortiz

## Executive Summary
On 2024-11-15, the API Gateway began returning 5xx responses after a certificate rotation failed. Roughly 23% of customer traffic experienced auth failures. Service was restored by rolling back to the previous certificate bundle and purging edge caches.

## Timeline
- **14:32 UTC** – Synthetic monitor detects spike in 5xx.
- **14:34 UTC** – PagerDuty pages on-call API engineer.
- **14:38 UTC** – IC + CL assigned; incident channel created.
- **14:45 UTC** – Root cause narrowed to invalid cert chain.
- **14:58 UTC** – Certificate rollback initiated.
- **15:07 UTC** – Gateways return 200 OK across regions.
- **15:19 UTC** – Post-incident validation completed; status page updated.

## Root Cause Analysis
### Primary Cause
Certificate rotation script pushed a bundle missing the intermediate cert. TLS handshakes failed under specific clients, causing retries and saturation.

### Contributing Factors
1. Monitoring gap: cert expiry alerts disabled during migration.
2. Runbook outdated: missing cert rotation validation step.
3. Lack of automated smoke tests for gateway TLS.

## Mitigations
- Immediate rollback to previous cert bundle.
- Purged CDN caches to ensure clients re-downloaded certificates.
- Added manual validation step to runbook (`../runbooks/api-gateway-cert-rotation.md`).

## Action Items
| ID | Description | Owner | Due |
|----|-------------|-------|-----|
| AI-1 | Reinstate cert expiry alerts with redundancy | Platform Observability | 2024-11-30 |
| AI-2 | Automate TLS smoke tests in CI | API Engineering | 2024-12-15 |
| AI-3 | Update cert rotation runbook with validation checklist | SRE Oncall | 2024-11-20 |

## References
- Incident ticket: `INC-2024-11-15-API`
- Status page updates: link
- Related documents: `../event-prep/holiday-traffic-readiness.md`
