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

### Step 9: Validate Application Health
- Check Datadog dashboard: `PostgreSQL / Query Throughput`
- Confirm error rate < 0.1% in `Auth Service Errors` dashboard
- Run synthetic transaction test: `make test-db-connectivity`

**Success criteria**:
- Write latency p99 < 50ms
- Read latency p99 < 10ms
- Zero `connection refused` errors in application logs

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

## Post-Incident Actions

After successful failover:
1. Update incident ticket with all timestamps and commands executed
2. Capture PostgreSQL logs from old primary: `/var/log/postgresql/*.log`
3. Generate replication lag graph from Grafana for incident timeline
4. Schedule post-mortem meeting within 48 hours
5. Document any deviations from this runbook in incident ticket
6. If failover was due to hardware failure, schedule old primary replacement

## Related Documentation

- [Database Architecture Overview](../apps/database-cluster/overview.md)
- [Replication Monitoring Setup](../how-to/database-replication-monitoring.md)
- [Post-Mortem Template](../incidents/postmortem-template.md)
- [Incident Escalation Process](../process/incident-escalation.md)

## Runbook Metadata

| Field | Value |
|-------|-------|
| Last Updated | 2024-11-15 |
| Last Tested | 2024-10-22 (DR drill) |
| Success Rate | 94% (17/18 executions) |
| Avg Execution Time | 4 minutes 30 seconds |
| Owner | sre-data team |
| On-call Rotation | PagerDuty schedule `SRE-Data-Primary` |
