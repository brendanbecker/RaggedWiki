# API Gateway Rate Limit Tuning Runbook

> **Service:** Kong API Gateway  |  **Environment:** prod-us-west  |  **Severity:** SEV3  |  **Owner:** sre-api

## Prerequisites

- Kong Admin API access: `https://kong-admin.prod.company.com`
- API key for Kong management: Stored in 1Password vault `SRE-Production`
- Grafana dashboard: `Kong / Rate Limiting & Traffic`
- kubectl access to `api-gateway` namespace

## When to Execute This Runbook

Execute when you observe:
1. Legitimate traffic being rate-limited (HTTP 429 responses increasing)
2. Customer reports of "Too Many Requests" errors
3. Alert fires: `Kong rate limit hit ratio > 5%`
4. After a new service launch that changes traffic patterns
5. During special events (product launches, marketing campaigns)

**Note**: Do NOT adjust rate limits during an active DDoS attack. Use the [DDoS Mitigation Runbook](./ddos-mitigation.md) instead.

## Current Rate Limit Configuration

### Default Global Limits
- **Per IP**: 100 requests/second
- **Per API Key**: 500 requests/second
- **Per Route**: Varies by endpoint (see table below)

### Endpoint-Specific Limits

| Route | Rate Limit | Burst Allowance | Business Justification |
|-------|------------|-----------------|------------------------|
| `/api/v1/auth/login` | 5 req/min per IP | 10 req/5min | Prevent credential stuffing |
| `/api/v1/search` | 50 req/sec per user | 100 req/10sec | High-frequency UI interaction |
| `/api/v1/checkout` | 10 req/min per user | 15 req/min | Payment processing constraint |
| `/api/v1/analytics` | 100 req/sec per key | 200 req/10sec | Partner integration endpoint |

## Diagnosis

### Step 1: Identify Which Limit Is Being Hit
```bash
curl -s https://kong-admin.prod.company.com/status | jq '.plugins.rate_limiting'
```

**Key metrics**:
- `total_requests`: Total requests processed
- `requests_exceeded`: Requests that exceeded rate limit
- `exceeded_percentage`: Should be <5% under normal conditions

### Step 2: Check Rate Limit by Route
```bash
curl -s https://kong-admin.prod.company.com/routes | \
  jq '.data[] | {route: .paths[], plugins: .plugins}'
```

Look for routes with rate-limiting plugin enabled. Note their current limits.

### Step 3: Analyze Traffic Patterns
```bash
# View recent 429 responses by client IP
kubectl logs -n api-gateway deployment/kong --since=10m | \
  grep 'HTTP/1.1" 429' | \
  awk '{print $1}' | sort | uniq -c | sort -rn | head -10
```

**Analysis**:
- Single IP with many 429s → Possible malicious actor
- Many IPs with few 429s each → Legitimate traffic spike, consider increasing limits
- Specific endpoint concentrated 429s → Route-specific limit needs adjustment

### Step 4: Verify Legitimate Traffic Pattern
```bash
# Check Datadog for traffic surge correlation
# Navigate to: Dashboards > Kong > Request Volume by Route

# Look for:
# - Time of day patterns (legitimate traffic has daily cycles)
# - User agent distribution (bots typically use same user agent)
# - Geographic distribution (DDoS often comes from specific regions)
```

## Adjustment Procedures

### Scenario A: Increase Global Rate Limit (Temporary)

Use this when legitimate traffic universally increased (e.g., successful product launch):

```bash
# Update global rate limit via Kong Admin API
curl -X PATCH https://kong-admin.prod.company.com/plugins/global-rate-limiting \
  -H "Kong-Admin-Token: $(cat ~/.kong-admin-token)" \
  -d "config.second=150" \
  -d "config.hour=500000"
```

**Effect**: Increases per-IP limit from 100 req/sec to 150 req/sec.

**Duration**: Temporary increase. Schedule follow-up review in 7 days to assess if permanent change needed.

### Scenario B: Increase Route-Specific Limit

Use when a specific endpoint is seeing legitimate growth:

```bash
# Example: Increase /api/v1/search limit
ROUTE_ID=$(curl -s https://kong-admin.prod.company.com/routes | \
  jq -r '.data[] | select(.paths[] | contains("/api/v1/search")) | .id')

curl -X POST https://kong-admin.prod.company.com/routes/$ROUTE_ID/plugins \
  -H "Kong-Admin-Token: $(cat ~/.kong-admin-token)" \
  -d "name=rate-limiting" \
  -d "config.second=75" \
  -d "config.policy=redis"
```

**Effect**: Increases `/api/v1/search` limit from 50 req/sec to 75 req/sec.

### Scenario C: Add IP Whitelist Exception

Use when a trusted partner or internal system is being rate-limited:

```bash
# Add IP to whitelist
curl -X POST https://kong-admin.prod.company.com/consumers/partner-acme/acls \
  -H "Kong-Admin-Token: $(cat ~/.kong-admin-token)" \
  -d "group=rate-limit-exempt"

# Apply exemption to rate-limiting plugin
curl -X PATCH https://kong-admin.prod.company.com/plugins/global-rate-limiting \
  -H "Kong-Admin-Token: $(cat ~/.kong-admin-token)" \
  -d "config.whitelist=rate-limit-exempt"
```

**Effect**: IP addresses in `rate-limit-exempt` group bypass all rate limits.

**Approval required**: Must get sign-off from Security team before adding any IP to whitelist (Slack: #security-approvals).

### Scenario D: Implement Gradual Increase

Use when you're unsure of the optimal new limit:

```bash
# Increase by 25% initially
CURRENT_LIMIT=100
NEW_LIMIT=$((CURRENT_LIMIT * 125 / 100))

curl -X PATCH https://kong-admin.prod.company.com/plugins/global-rate-limiting \
  -H "Kong-Admin-Token: $(cat ~/.kong-admin-token)" \
  -d "config.second=$NEW_LIMIT"

# Monitor for 30 minutes, then assess if further increase needed
```

**Best practice**: Increase in 25% increments with 30-minute monitoring intervals. Avoid doubling limits without data to support it.

## Validation

### Step 5: Monitor 429 Response Rate
```bash
# Wait 5 minutes after change, then check
curl -s https://kong-admin.prod.company.com/status | jq '.plugins.rate_limiting.exceeded_percentage'
```

**Success criteria**: Exceeded percentage should drop below 2%.

### Step 6: Check Application Error Rate
```bash
# Verify downstream services are healthy
kubectl top pods -n api-gateway
```

Ensure CPU/memory usage hasn't spiked. If increased limits cause resource exhaustion, roll back change and scale gateway first.

### Step 7: Validate Customer Impact
- Check support ticket queue for "429 error" mentions (should decrease)
- Monitor Datadog: `API Gateway / Response Codes` (429s should trend downward)
- Run synthetic test: `make test-api-gateway-smoke`

## Rollback Procedure

If increased limits cause instability:

```bash
# Revert to previous limit value
curl -X PATCH https://kong-admin.prod.company.com/plugins/global-rate-limiting \
  -H "Kong-Admin-Token: $(cat ~/.kong-admin-token)" \
  -d "config.second=100"

# Restart Kong pods to clear any cached state
kubectl rollout restart deployment/kong -n api-gateway
```

**Downtime**: <30 seconds during rolling restart. Requests are queued and replay automatically.

## Common Issues

### Issue 1: Change Not Taking Effect
**Symptom**: Rate limit adjustment made but 429s continue at same rate.

**Cause**: Kong caches rate limit configuration for 60 seconds.

**Resolution**: Wait 90 seconds after change, or force restart: `kubectl rollout restart deployment/kong -n api-gateway`

### Issue 2: Redis Connection Errors After Limit Increase
**Symptom**: Kong logs show `failed to connect to redis` after increasing limits.

**Cause**: Rate limiting plugin stores counters in Redis. Higher limits = more Redis operations.

**Resolution**: Scale Redis cluster before further limit increases:
```bash
kubectl scale statefulset/redis-rate-limit --replicas=5 -n api-gateway
```

### Issue 3: Legitimate Traffic Still Blocked
**Symptom**: After increasing limits, some users still get 429s.

**Cause**: Rate limiting is based on sliding window. Users who hit old limit are still in penalty box.

**Resolution**: Clear rate limit counters for affected IPs:
```bash
redis-cli -h redis-rate-limit.api-gateway.svc.cluster.local FLUSHDB
```

**Warning**: This resets ALL rate limit counters. Use only during incidents.

## Post-Change Actions

After any rate limit adjustment:
1. Document the change in incident ticket or change request
2. Update the rate limit table in this runbook with new values
3. Schedule review meeting with product team if change is >50% increase
4. Add metric to dashboard: Before/after comparison of 429 rate
5. Notify customer success team if customer-reported issue triggered the change

## Capacity Planning

### When to Scale Gateway (Instead of Increasing Limits)

Increase rate limits when:
- Legitimate traffic patterns changed
- New feature launched
- Customer tier upgraded

Scale gateway infrastructure when:
- Gateway CPU >70% sustained
- Gateway memory >80%
- Request latency p95 >200ms
- Redis rate-limit store CPU >60%

**Rule of thumb**: If you're increasing limits by >2x, consider scaling infrastructure first to maintain headroom.

## Related Documentation

- [Kong Architecture Overview](../apps/api-gateway/overview.md)
- [DDoS Mitigation Runbook](./ddos-mitigation.md)
- [API Gateway Scaling Guide](../how-to/scale-api-gateway.md)
- [Rate Limiting Strategy](../process/api-rate-limiting-policy.md)

## Runbook Metadata

| Field | Value |
|-------|-------|
| Last Updated | 2024-11-12 |
| Last Executed | 2024-11-08 (Black Friday prep) |
| Average Execution Time | 8 minutes |
| Success Rate | 95% (19/20 executions) |
| Approval Required | Yes (for whitelist changes only) |
