# Example 1B: Runbook with Layout-Aware Hierarchical Chunking

**Strategy**: Section-based chunking respecting H2 boundaries
**Source**: Database failover runbook

This demonstrates the **CORRECT** approach - preserving complete semantic units.

---

## Chunk 1: Prerequisites and Context [420 tokens] ✅

**Section**: Title, metadata, prerequisites

```markdown
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
```

[End of chunk - tokens: 420/900 - 47% utilization - COMPLETE SEMANTIC UNIT] ✅

**Why this works**:
- Complete prerequisite list (nothing missing)
- Clear trigger conditions (when to use this runbook)
- Self-contained: Can answer "When should I failover?" without needing other chunks

---

## Chunk 2: Impact Assessment [485 tokens] ✅

**Section**: Impact assessment

```markdown
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
- `analytics-pipeline`: No impact (reads from replica)

### Data Consistency
- Zero data loss if replication lag < 1 second at failover initiation
- Potential loss of up to 5 seconds of writes if lag is elevated
- All replicas will resync automatically post-failover
```

[End of chunk - tokens: 485/900 - 54% utilization - COMPLETE SEMANTIC UNIT] ✅

**Why this works**:
- Complete impact analysis in one place
- Answers "What are the consequences?" fully
- All related information grouped together (downtime, dependencies, data consistency)

---

## Chunk 3: Pre-Failover Validation [590 tokens] ✅

**Section**: Pre-failover validation steps

```markdown
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
```
🚨 Database failover initiated for PostgreSQL prod-us-east
Primary: db-primary-us-east-1.aws.com
Target replica: db-replica-us-east-1.aws.com
Expected downtime: 2-5 minutes
Incident ticket: INC-XXXXX
```
```

[End of chunk - tokens: 590/900 - 66% utilization - COMPLETE PROCEDURE] ✅

**Why this works**:
- All validation steps together (1, 2, 3 complete)
- Each step has: command + expected output + interpretation
- Semantic completeness: "What do I check before failover?" fully answered

---

## Chunk 4: Failover Procedure [680 tokens] ✅

**Section**: Core failover procedure

```markdown
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

### Step 6: Restart Application Connection Pools
```bash
# Cycle application pods to reset DB connections
kubectl rollout restart deployment/auth-service -n prod
kubectl rollout restart deployment/payment-service -n prod
kubectl rollout restart deployment/user-profile-service -n prod
```

**Note**: Modern connection pools should detect the failover automatically, but restart ensures clean state.
```

[End of chunk - tokens: 680/900 - 76% utilization - COMPLETE PROCEDURE] ✅

**Why this works**:
- **Complete failover flow**: Steps 4-6 execute sequentially, all present
- **Both approaches**: RDS and self-managed commands together
- **Timing information**: Duration and expected outcomes included
- Answers "How do I fail over?" completely

---

## Chunk 5: Post-Failover Validation [750 tokens] ✅

**Section**: Validation and verification

```markdown
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

### Step 9: Validate Application Health
- Check Datadog dashboard: `PostgreSQL / Query Throughput`
- Confirm error rate < 0.1% in `Auth Service Errors` dashboard
- Run synthetic transaction test: `make test-db-connectivity`

**Success criteria**:
- Write latency p99 < 50ms
- Read latency p99 < 10ms
- Zero `connection refused` errors in application logs
```

[End of chunk - tokens: 750/900 - 83% utilization - COMPLETE VALIDATION] ✅

**Why this works**:
- All validation steps (7-9) in one chunk
- Success criteria clearly defined
- Monitoring commands and expected outcomes included
- Answers "How do I know the failover worked?" completely

---

## Chunk 6: Rollback and Common Failures [820 tokens] ✅

**Section**: Rollback procedure and troubleshooting

```markdown
## Rollback Procedure

If the failover causes unexpected issues:

### Immediate Rollback (within 10 minutes)
```bash
# Promote original primary back (if still healthy)
aws rds promote-read-replica \
  --db-instance-identifier prod-postgres-primary-original

# Revert DNS
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234EXAMPLE \
  --change-batch file://rollback-dns-change.json
```

**Risk**: May result in split-brain scenario if writes occurred on both instances. Requires manual data reconciliation.

### Clean Rollback (after 10 minutes)
Do NOT attempt automatic rollback. Open SEV1 incident and engage database engineering team for manual recovery.

## Common Failure Scenarios

### Scenario 1: Replica Promotion Fails
**Symptom**: `pg_ctl promote` command hangs or fails
**Resolution**:
1. Check replication slot status: `SELECT * FROM pg_replication_slots;`
2. If slot is inactive, restart PostgreSQL: `systemctl restart postgresql`
3. Retry promotion
4. If fails again, promote secondary replica (replica-2)

### Scenario 2: Split-Brain After Failover
**Symptom**: Both old and new primary accept writes
**Resolution**:
1. Immediately fence old primary: `systemctl stop postgresql`
2. Identify conflicting writes in both databases
3. Engage database team for manual reconciliation
4. Do NOT automate this - data loss risk is high

### Scenario 3: DNS Not Propagating
**Symptom**: Applications still connecting to old primary after 2 minutes
**Resolution**:
1. Force application pod restarts (breaks existing connections)
2. Update application ConfigMaps with direct IP if DNS continues to fail
3. File ticket with networking team for DNS investigation
```

[End of chunk - tokens: 820/900 - 91% utilization - COMPLETE ROLLBACK + TROUBLESHOOTING] ✅

**Why this works**:
- Rollback procedure complete (both immediate and delayed)
- Common failure scenarios grouped together
- Each scenario: symptom + resolution
- Answers "What if it goes wrong?" fully

---

## Analysis of Layout-Aware Chunking

### Advantages Over Naive Chunking

1. **Semantic completeness**: Each chunk answers a specific question completely
2. **No fragmentation**: Procedures not split mid-step
3. **Optimal token usage**: 420-820 tokens per chunk (all in sweet spot)
4. **Hierarchical structure**: Section headers preserved, easier to index
5. **Zero overlap**: No wasted tokens on redundant content

### Retrieval Simulation

**Query**: "How do I promote the replica to primary in a database failover?"

**Result**: Chunk 4 retrieved (similarity score: 0.94)

**Content retrieved**: Complete failover procedure (Steps 4-6)
- Promotion commands (both RDS and self-managed)
- DNS update commands
- Connection pool restart
- All expected outcomes and timing

**Follow-up context available**:
- Prerequisites: Chunk 1
- Pre-validation: Chunk 3
- Post-validation: Chunk 5
- Rollback if needed: Chunk 6

**User experience**: Single chunk provides complete answer. Adjacent chunks available for deeper context.

### Token Distribution

| Chunk | Tokens | Utilization | Contains | Semantic Completeness |
|-------|--------|-------------|----------|----------------------|
| 1 | 420 | 47% | Prerequisites, When to Execute | ✅ Complete |
| 2 | 485 | 54% | Impact Assessment | ✅ Complete |
| 3 | 590 | 66% | Pre-Failover Validation | ✅ Complete |
| 4 | 680 | 76% | Failover Procedure | ✅ Complete |
| 5 | 750 | 83% | Post-Failover Validation | ✅ Complete |
| 6 | 820 | 91% | Rollback and Failures | ✅ Complete |

**Observation**: Lower token utilization per chunk BUT **100% semantic utilization**. Each chunk is a complete thought/procedure.

### Why This Approach Succeeds

1. **Respects document structure**: H2 sections are natural semantic boundaries
2. **Aligned with user queries**: People ask "How do I failover?" not "Give me tokens 1024-1536"
3. **Complete context**: Each chunk can stand alone or work with related chunks
4. **Hierarchical indexing**: Can index by section type (Prerequisites, Procedure, Validation)
5. **Metadata-rich**: Section headers become metadata tags for filtering

### Chunking Algorithm

```python
def chunk_by_h2_sections(markdown_content):
    """
    Split markdown document into chunks at H2 (##) boundaries.
    Each chunk includes the H2 header and all content until next H2.
    """
    sections = []
    current_section = []

    for line in markdown_content.split('\n'):
        if line.startswith('## ') and current_section:
            # New H2 found, save previous section
            sections.append('\n'.join(current_section))
            current_section = [line]
        else:
            current_section.append(line)

    # Save last section
    if current_section:
        sections.append('\n'.join(current_section))

    return sections
```

**Result**: Chunks naturally fall into 400-900 token range because well-structured documents have sections sized for human readability, which aligns with LLM context windows.

**Conclusion**: Layout-aware chunking produces **semantically complete, contextually rich chunks** that dramatically improve retrieval quality for procedural content.
