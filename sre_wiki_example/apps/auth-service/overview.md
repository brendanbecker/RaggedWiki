# Auth Service Knowledge Base

## Architecture Overview
- Stateless Go service behind Envoy gateways
- Depends on Redis session cache + PostgreSQL user store
- Lucidchart: `../assets/lucid-auth-architecture.md`

## Key Runbooks
- `../../runbooks/auth-service-restart.md`
- `../../how-to/zero-downtime-deployments.md`

## Institutional Knowledge
- Token refresh bug (2023): issue tracker `AUTH-4321`
- Vendor contact for MFA provider: see `../../stakeholders/contacts.md`
- Deployment cadence: weekly Wednesday 18:00 UTC

## Metrics & Dashboards
| Metric | Source | Threshold |
|--------|--------|-----------|
| Auth latency p95 | Datadog `auth.latency` | < 250ms |
| Login error rate | Grafana panel `Auth Errors` | < 0.3% |
| Token refresh failures | Custom query | < 100 / hour |

## Links
- Source repo: `git@github.com:company/auth-service`
- PagerDuty service: `PD-SVC-AUTH`
- Lucid diagram: `https://lucid.co/documents/auth-architecture`
