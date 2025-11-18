# Service Restart Runbook: Authentication API

> **Service:** Auth API  |  **Environment:** prod-us-central  |  **Severity:** SEV2 potential  |  **Owner:** sre-auth

## Prerequisites
- PagerDuty escalation: `PD-SRE-AUTH`
- Access: `kubectl` context `prod-us-central`
- Dashboards: Datadog `Auth / Latency`, Grafana `Auth Errors`

## Impact Assessment
Restarting the deployment causes up to 60 seconds of degraded login throughput. Session cache survives across restarts; no data loss expected.

## Procedure
### Step 1: Validate Current Health
1. `kubectl get pods -n auth | grep auth-api`
2. `curl -sf https://auth.company.com/health`
3. Confirm Datadog error rate < 0.5%

### Step 2: Drain Traffic
1. Shift 90% traffic to secondary region using the traffic manager UI.
2. Scale deployment to zero: `kubectl scale deploy/auth-api --replicas=0 -n auth`
3. Monitor login backlog; keep < 200 pending requests.

### Step 3: Restart Pods
1. `kubectl rollout restart deploy/auth-api -n auth`
2. Watch rollout: `kubectl rollout status deploy/auth-api -n auth`
3. Re-enable traffic and confirm 200 OK plateau for 10 minutes.

## Validation
- Latency p95 < 250ms
- Error budget burn remains < 1%
- Synthetic login pipeline returns STATUS=PASS

## Post-Run Actions
- Update incident ticket with timestamps
- Attach tail logs under `logs/auth-service/auth-restart-YYYYMMDD.log`
- Notify #oncall-summary with validation screenshot
