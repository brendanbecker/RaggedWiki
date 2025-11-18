# How-To Guide: Zero-Downtime Deployments

> **Content Type:** how-to  |  **Service:** Core Platform  |  **Environment:** prod/stage  |  **Last Updated:** 2025-01-12

## Objective
Deliver application updates without interrupting user traffic by combining canary releases, traffic shifting, and automated rollback triggers.

## Prerequisites
- Feature flags managed in LaunchDarkly (`flag: platform.deploy.canary`)
- CI/CD pipeline with staged artifacts
- Observability dashboards bookmarked (Latency, Error Rate, Saturation)

## Procedure
### Step 1: Prep Canary Release
1. Merge approved changes to `main`.
2. Generate release artifact via `./ci/publish.sh --env prod`.
3. Enable canary flag at 5% traffic slice.

### Step 2: Monitor Canary
1. Datadog monitor `deploy-canary-latency` must stay < 200ms p95.
2. Compare error budget burn vs baseline (Grafana dashboard `Deploy Canary`).
3. If metrics exceed thresholds, disable flag and run rollback script.

### Step 3: Full Rollout
1. Increase `platform.deploy.canary` to 50%, then 100% if stable for 10 minutes.
2. Confirm new pods registered in service mesh.
3. Announce completion in #deployments with dashboard link.

## Validation
- `kubectl rollout status deploy/platform-api` reports success.
- Observability KPIs match pre-deploy baselines within 5%.
- Run synthetic check: `./scripts/smoke/platform_smoke.sh`.

## References
- Runbook: `../runbooks/platform-api-rollback.md`
- Pattern: `../patterns/async-incident-comms.md`
- Asset: `../assets/lucid-platform-traffic-shift.md`
