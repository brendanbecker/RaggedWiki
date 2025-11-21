# Redis Cache Eviction Runbook: Session Store

> **Service:** Redis Session Cache  |  **Environment:** prod-global  |  **Severity:** SEV2  |  **Owner:** sre-platform

## Prerequisites

- Access to Redis CLI: `redis-cli -h session-cache.prod.company.com`
- Grafana dashboard: `Redis / Memory & Evictions`
- kubectl access to `prod` namespace
- Datadog access for application metrics
- PagerDuty escalation: `PD-SRE-PLATFORM`

## When to Execute This Runbook

Execute this runbook when you observe:
1. Redis memory usage > 85% of max memory
2. Eviction rate > 100 keys/second
3. Cache hit ratio drops below 75%
4. Application latency increases with error logs mentioning "cache miss"
5. Alert fires: `Redis memory pressure - prod`

## Impact Assessment

### Service Impact
- **Session cache**: Users may need to re-authenticate if sessions are evicted
- **API response time**: Increased by 200-500ms for cache misses (database fallback)
- **Database load**: Increases by 40-60% during cache pressure

### User Experience
- Minor: Most users won't notice if evictions are gradual
- Moderate: If 10%+ of sessions evicted, users see unexpected logouts
- Severe: If cache completely fills, new sessions cannot be created

## Diagnosis

### Step 1: Check Current Memory Usage
```bash
redis-cli -h session-cache.prod.company.com INFO memory
```

**Key metrics to examine**:
- `used_memory_human`: Should be <85% of `maxmemory`
- `used_memory_rss_human`: RSS should not exceed `used_memory` by >20%
- `mem_fragmentation_ratio`: Should be between 1.0 and 1.5

### Step 2: Identify Eviction Policy
```bash
redis-cli -h session-cache.prod.company.com CONFIG GET maxmemory-policy
```

**Expected**: Should return `allkeys-lru` (evict least recently used keys when memory full).

If returns `noeviction`, this is a **critical misconfiguration** - Redis will reject new writes when full.

### Step 3: Analyze Key Distribution
```bash
redis-cli -h session-cache.prod.company.com --bigkeys
```

This scans the keyspace to find abnormally large keys. Look for:
- Keys with >1MB size
- Unexpected key patterns (possible memory leak in application)
- Large hash or list structures

### Step 4: Check Eviction Rate
```bash
redis-cli -h session-cache.prod.company.com INFO stats | grep evicted
```

**Normal**: `evicted_keys` should be <50/second during steady state.
**Warning**: >100/second indicates memory pressure.
**Critical**: >500/second means aggressive eviction, service degradation likely.

## Resolution Procedures

### Quick Fix: Flush Expired Keys
```bash
# Force scan and removal of expired keys (safe operation)
redis-cli -h session-cache.prod.company.com MEMORY PURGE
```

**Expected**: Frees 5-15% of memory occupied by expired but not yet deleted keys.

### Tactical Fix: Scale Redis Cluster
```bash
# Increase Redis memory limit (requires restart)
kubectl edit statefulset redis-session-cache -n prod

# Modify container resources:
# resources:
#   requests:
#     memory: "8Gi"  # Increase from 6Gi
#   limits:
#     memory: "8Gi"

# Apply changes
kubectl rollout restart statefulset/redis-session-cache -n prod
```

**Downtime**: 2-3 minutes during rolling restart. Application will fallback to database during this window.

### Strategic Fix: Implement Key Expiration
If keys lack proper TTL, they accumulate indefinitely:

```bash
# Audit keys without expiration
redis-cli -h session-cache.prod.company.com --scan --pattern '*' | \
  while read key; do
    ttl=$(redis-cli -h session-cache.prod.company.com TTL "$key")
    if [ "$ttl" -eq "-1" ]; then
      echo "Key without TTL: $key"
    fi
  done
```

**Action**: File ticket with application team to set TTL on all session keys (recommend 24 hours for user sessions).

### Emergency Fix: Targeted Key Deletion
If specific key patterns are causing the issue:

```bash
# Delete keys matching pattern (CAUTION: destructive operation)
redis-cli -h session-cache.prod.company.com --scan --pattern 'temp:*' | \
  xargs redis-cli -h session-cache.prod.company.com DEL
```

**Use only when**: You've identified non-critical keys (like temporary tokens, preview data) that can be safely deleted.

## Validation

### Step 5: Verify Memory Recovery
```bash
redis-cli -h session-cache.prod.company.com INFO memory | grep used_memory_human
```

**Success criteria**: Memory usage should drop below 75% of max memory within 10 minutes.

### Step 6: Check Application Health
- Monitor Datadog: `Auth Service / Cache Hit Rate`
- Confirm cache hit ratio returns to >85%
- Verify application error rate returns to baseline (<0.1%)

### Step 7: Validate Session Persistence
```bash
# Test session creation and retrieval
curl -X POST https://api.company.com/v1/auth/login \
  -d '{"username":"test@company.com","password":"test"}' | jq .token

# Use returned token to verify session retrieval
curl -H "Authorization: Bearer <token>" https://api.company.com/v1/auth/verify
```

**Expected**: Both operations should succeed with <100ms latency.

## Prevention

### Configure Proper TTLs
All cache keys should have appropriate expiration:
- User sessions: 24 hours
- API tokens: 1 hour
- Temporary data: 5 minutes
- Rate limit counters: 1 minute

### Monitor Key Growth Rate
Set up alert: "Redis key count increasing >10% per hour"

This detects:
- Memory leaks in application code
- Missing TTL on new key types
- Runaway background jobs

### Implement Cache Warming Strategy
During deployment, pre-populate cache with critical data to avoid thundering herd:

```bash
# Example: Pre-warm user session cache
kubectl exec -it app-deployment-xxx -n prod -- \
  python scripts/cache_warmup.py --keys=active_users
```

### Regular Memory Profiling
Schedule monthly analysis:
1. Run `redis-cli --bigkeys` and save output
2. Compare month-over-month key distribution
3. Identify growing key patterns
4. Work with application teams to optimize storage

## Escalation Path

If resolution procedures fail:

1. **Immediate** (within 5 minutes): Page SRE-platform on-call via PagerDuty
2. **Within 15 minutes**: Escalate to Redis subject matter expert (see contacts below)
3. **Within 30 minutes**: Open bridge with application teams if identified as app-side issue

### Key Contacts
- Redis SME: Sarah Chen (schen@company.com, Slack: @sarah.chen)
- SRE Platform Lead: Marcus Rodriguez (mrodriguez@company.com)
- Auth Service Team: `#team-auth-service`

## Related Documentation

- [Redis Architecture Overview](../apps/redis-cluster/overview.md)
- [Application Caching Best Practices](../how-to/application-caching.md)
- [Monitoring Setup: Redis](../how-to/monitoring-redis.md)

## Runbook Metadata

| Field | Value |
|-------|-------|
| Last Updated | 2024-11-18 |
| Last Executed | 2024-11-10 |
| Average Resolution Time | 12 minutes |
| Success Rate | 100% (8/8 executions) |
| Common Root Cause | Missing TTL on session keys (60% of incidents) |
