# Example 1A: Runbook with Naive Fixed-Size Chunking

**Strategy**: Fixed 512-token chunks with 50-token overlap
**Source**: Database failover runbook

This demonstrates the **WRONG** approach - breaking content at arbitrary boundaries.

---

## Chunk 1/12 [512 tokens] ⚠️

# Database Failover Runbook: PostgreSQL Primary

> **Service:** PostgreSQL Cluster  |  **Environment:** prod-us-east  |  **Severity:** SEV1  |  **Owner:** sre-data

## Prerequisites

Before initiating a failover, ensure you have:
- Access to `psql` client with superuser credentials
- Replication monitoring dashboard: Grafana `PostgreSQL / Replication Lag`
- PagerDuty escalation: `PD-SRE-DATA`
- AWS Console access for RDS management
- Communication channel open: `#incident-response`

## When to Execute This Runbook

Execute database failover when:
1. Primary database is unresponsive for >60 seconds
2. Replication lag exceeds 30 seconds and is growing
3. CPU utilization sustains >95% for >5 minutes
4. Disk I/O wait time exceeds 80%
5. Planned maintenance window requires primary switchover

**Critical**: Do NOT failover during active write-heavy transactions (e.g., end-of-day batch jobs) unless primary is completely unavailable.

## Impact Assessment

### Expected Downtime
- **Automated failover**: 15-45 seconds of write unavailability
- **Manual failover**: 2-5 minutes total
- Read replicas continue serving traffic during failover

### Service Dependencies
Services affected during failover window:
- `auth-service`: Login writes will queue (60s buffer)
- `payment-service`: Transaction processing pauses (retry logic handles this)
- `user-profile-service`: Profile updates will fail (requires manual retry)

[End of chunk - tokens: 512/512 - 100% utilization - OVERLAP NEXT]

---

## Chunk 2/12 [512 tokens] ⚠️

[Overlap from previous chunk]
- `user-profile-service`: Profile updates will fail (requires manual retry)
- `analytics-pipeline`: No impact (reads from replica)

### Data Consistency
- Zero data loss if replication lag < 1 second at failover initiation
- Potential loss of up to 5 seconds of writes if lag is elevated
- All replicas will resync automatically post-failover

## Pre-Failover Validation

### Step 1: Assess Replication Health
```bash
# Check current replication lag on all replicas
psql -h replica-1.prod.aws.com -U admin -c "SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag;"
psql -h replica-2.prod.aws.com -U admin -c "SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag;"
```

**Expected**: Lag should be <1 second on at least one replica. If all replicas show >10 second lag, investigate replication issues before proceeding.

### Step 2: Verify Replica Readiness
```bash
# Confirm replica is in hot standby mode
psql -h replica-1.prod.aws.com -U admin -c "SELECT pg_is_in_recovery();"
```

**Expected**: Should return `t` (true). If returns `f`, the replica is not in recovery mode and cannot be promoted.

### Step 3: Notify Stakeholders
Post in `#incident-response`:

[End of chunk - tokens: 512/512 - 100% utilization - OVERLAP NEXT]
[**PROBLEM**: Step 3 cut off mid-instruction]

---

## Chunk 3/12 [512 tokens] ⚠️

[Overlap from previous chunk]
### Step 3: Notify Stakeholders
Post in `#incident-response`:
```
🚨 Database failover initiated for PostgreSQL prod-us-east
Primary: db-primary-us-east-1.aws.com
Target replica: db-replica-us-east-1.aws.com
Expected downtime: 2-5 minutes
Incident ticket: INC-XXXXX
```

## Failover Procedure

### Step 4: Promote Replica to Primary
```bash
# AWS RDS approach
aws rds promote-read-replica \
  --db-instance-identifier prod-postgres-replica-1 \
  --region us-east-1

# Self-managed approach
ssh postgres-replica-1.prod.aws.com
sudo -u postgres /usr/lib/postgresql/14/bin/pg_ctl promote -D /var/lib/postgresql/14/main/
```

**Duration**: 30-90 seconds for promotion to complete.

### Step 5: Update DNS and Connection Pools
```bash
# Update Route53 DNS record to point to new primary
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234EXAMPLE \
  --change-batch file://failover-dns-change.json

# Verify DNS propagation
dig db-primary.prod.company.com +short
```

**Expected**: DNS should resolve to new primary IP within 30 seconds (TTL=30s).

[End of chunk - tokens: 512/512 - 100% utilization - OVERLAP NEXT]
[**PROBLEM**: Step 5 continues in next chunk, incomplete context]

---

## Chunk 4/12 [512 tokens] ⚠️

[Overlap from previous chunk]
**Expected**: DNS should resolve to new primary IP within 30 seconds (TTL=30s).

### Step 6: Restart Application Connection Pools
```bash
# Cycle application pods to reset DB connections
kubectl rollout restart deployment/auth-service -n prod
kubectl rollout restart deployment/payment-service -n prod
kubectl rollout restart deployment/user-profile-service -n prod
```

**Note**: Modern connection pools should detect the failover automatically, but restart ensures clean state.

## Post-Failover Validation

### Step 7: Verify Write Capability
```bash
# Execute test write on new primary
psql -h db-primary.prod.company.com -U admin -c \
  "INSERT INTO health_check (timestamp, status) VALUES (NOW(), 'post-failover-test');"
```

**Expected**: Write should succeed with `INSERT 0 1` response.

### Step 8: Monitor Replication Re-establishment
```bash
# Check that old primary (now replica) is replicating from new primary
psql -h db-replica-us-east-2.aws.com -U admin -c \
  "SELECT status, sender_host FROM pg_stat_wal_receiver;"
```

**Expected**: Status should show `streaming` within 5 minutes.

[End of chunk - tokens: 512/512 - 100% utilization - OVERLAP NEXT]

---

## Analysis of Naive Chunking

### Problems Identified

1. **Procedure fragmentation**: Step 3 is split across chunks 2 and 3
2. **Context loss**: Step 5 starts in chunk 3 but validation is in chunk 4
3. **Incomplete information**: User searching for "DNS update" gets chunk 3, but validation steps are in chunk 4 (may not be retrieved)
4. **Poor semantic boundaries**: Chunks break mid-procedure, mid-code block
5. **Overlap waste**: 50 tokens repeated in each chunk (10% overhead)

### Retrieval Simulation

**Query**: "How do I promote the replica to primary in a database failover?"

**Result**: Chunk 3/12 retrieved (highest similarity score: 0.87)

**Content retrieved**:
```
Step 4: Promote Replica to Primary
[commands shown]
Duration: 30-90 seconds for promotion to complete.
Step 5: Update DNS and Connection Pools
[partial commands shown, cut off]
```

**What's missing**:
- Prerequisites (in chunk 1-2)
- Post-promotion validation (in chunk 4)
- Expected outcomes (in chunk 4)

**User experience**: Partial answer, requires multiple follow-up queries or retrieval of adjacent chunks.

### Token Distribution

| Chunk | Tokens | Utilization | Contains |
|-------|--------|-------------|----------|
| 1 | 512 | 100% | Prerequisites, When to Execute, partial Impact |
| 2 | 512 | 100% | Impact continuation, Step 1-2, partial Step 3 |
| 3 | 512 | 100% | Step 3-5 partial |
| 4 | 512 | 100% | Step 6-8 partial |
| ... | ... | ... | ... |

**Observation**: High token utilization but **terrible semantic utilization**. Chunks are full of text but not full of *meaning*.

### Why This Approach Fails

1. **Ignores document structure**: Headers, code blocks, lists are treated as plain text
2. **Arbitrary boundaries**: 512-token limit doesn't align with semantic units
3. **Overlap inefficiency**: Repeated content doesn't improve retrieval, just wastes storage
4. **No hierarchy**: All chunks treated equally, no abstract/summary layer
5. **Query mismatch**: User queries align with *concepts* (procedures, steps), not arbitrary byte offsets

**Conclusion**: Fixed-size chunking is **incompatible** with procedural content like runbooks. Retrieval quality is poor despite 100% token utilization.
