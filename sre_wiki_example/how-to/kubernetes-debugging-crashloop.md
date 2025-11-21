# How To: Debug Kubernetes CrashLoopBackOff

> **Category:** Kubernetes Troubleshooting  |  **Difficulty:** Intermediate  |  **Time:** 15-30 minutes

## Overview

This guide covers systematic debugging of pods stuck in `CrashLoopBackOff` state—one of the most common Kubernetes issues. You'll learn how to identify root causes ranging from application errors to resource constraints to configuration problems.

## Prerequisites

- kubectl access to the affected cluster
- Basic understanding of Kubernetes pod lifecycle
- Access to application logs (Datadog, CloudWatch, or kubectl logs)
- Familiarity with your application's startup process

## Understanding CrashLoopBackOff

`CrashLoopBackOff` means:
1. Pod started successfully (container runtime launched the process)
2. Application crashed or exited (exit code ≠ 0)
3. Kubernetes restarted the pod
4. Crash happened again
5. Kubernetes now waits increasing intervals before retrying (exponential backoff)

**Key insight**: The crash is happening *after* the container starts, not during image pull or container creation.

## Diagnostic Steps

### Step 1: Identify the Crashing Pod

```bash
# List pods with CrashLoopBackOff status
kubectl get pods -n <namespace> | grep CrashLoopBackOff

# Get detailed pod status
kubectl describe pod <pod-name> -n <namespace>
```

**What to look for**:
- `Restart Count`: How many times has the pod crashed? (High count indicates recurring issue)
- `Last State`: Shows exit code and reason for previous crash
- `Events`: Recent Kubernetes events related to this pod

### Step 2: Check Application Logs

```bash
# View current container logs
kubectl logs <pod-name> -n <namespace>

# View logs from previous crashed container
kubectl logs <pod-name> -n <namespace> --previous

# Follow logs in real-time
kubectl logs <pod-name> -n <namespace> -f
```

**Common log patterns indicating root cause**:

| Log Pattern | Likely Cause | Next Step |
|-------------|--------------|-----------|
| `Connection refused: database:5432` | Cannot reach dependency | Check network policies, service DNS |
| `Out of memory` or `OOMKilled` | Memory limit too low | Increase memory limits |
| `FATAL: password authentication failed` | Wrong credentials | Check secrets, environment variables |
| `Address already in use: port 8080` | Port conflict | Check pod spec for duplicate ports |
| `File not found: /config/app.yaml` | Missing config file | Check ConfigMap mounting |

### Step 3: Inspect Exit Code

```bash
# Extract exit code from pod status
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'
```

**Common exit codes**:

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Clean exit (shouldn't cause crash loop) | Check liveness probe configuration |
| 1 | Generic application error | Review application logs |
| 137 | SIGKILL (OOMKilled) | Increase memory limits |
| 139 | SIGSEGV (segmentation fault) | Application bug, check core dumps |
| 143 | SIGTERM (graceful shutdown) | Check if pod is shutting down too quickly |
| 255 | Exit status out of range | Check application error handling |

### Step 4: Check Resource Constraints

```bash
# Check if pod is being OOMKilled
kubectl describe pod <pod-name> -n <namespace> | grep -i "OOMKilled"

# Check current resource usage
kubectl top pod <pod-name> -n <namespace>

# View resource requests and limits
kubectl get pod <pod-name> -n <namespace> -o yaml | grep -A 6 resources:
```

**Red flags**:
- Memory usage approaching limit (e.g., 450Mi used, 512Mi limit)
- CPU throttling (visible in Datadog/Prometheus metrics)
- No resource requests defined (pod can be killed during node pressure)

### Step 5: Verify Dependencies

```bash
# Check if service dependencies are reachable
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh

# Inside the pod:
nslookup database-service
curl -v database-service:5432
env | grep DATABASE  # Check environment variables
```

**Common dependency issues**:
- DNS resolution fails → Service doesn't exist or wrong namespace
- Connection timeout → Network policy blocking traffic
- Connection refused → Service is down or wrong port

### Step 6: Examine ConfigMaps and Secrets

```bash
# List ConfigMaps mounted in pod
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.volumes[*].configMap.name}'

# Verify ConfigMap exists and contains expected data
kubectl get configmap <configmap-name> -n <namespace> -o yaml

# Check Secret mounting
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.volumes[*].secret.secretName}'
```

**Common issues**:
- ConfigMap/Secret referenced but doesn't exist
- Key mismatch (pod expects `config.yaml` but ConfigMap has `app-config.yaml`)
- Secret not base64 decoded properly in application code

### Step 7: Review Liveness and Readiness Probes

```bash
# Check probe configuration
kubectl get pod <pod-name> -n <namespace> -o yaml | grep -A 10 livenessProbe
kubectl get pod <pod-name> -n <namespace> -o yaml | grep -A 10 readinessProbe
```

**Problematic probe configurations**:
- `initialDelaySeconds` too short → App killed before it finishes starting
- `periodSeconds` too frequent → App can't handle health check load
- Liveness probe checking external dependency → App killed when dependency is slow
- Wrong endpoint → Health check always fails

## Resolution Procedures

### Fix 1: Increase Resource Limits

```bash
# Edit deployment to increase memory
kubectl edit deployment <deployment-name> -n <namespace>

# Modify resources section:
# resources:
#   requests:
#     memory: "256Mi"
#     cpu: "100m"
#   limits:
#     memory: "1Gi"      # Increased from 512Mi
#     cpu: "500m"

# Or use kubectl set resources
kubectl set resources deployment <deployment-name> -n <namespace> \
  --limits=memory=1Gi,cpu=500m \
  --requests=memory=256Mi,cpu=100m
```

### Fix 2: Adjust Startup Timing

```bash
# Increase initialDelaySeconds for liveness probe
kubectl patch deployment <deployment-name> -n <namespace> --type=json \
  -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/livenessProbe/initialDelaySeconds", "value":60}]'
```

### Fix 3: Fix Missing ConfigMap

```bash
# Create missing ConfigMap
kubectl create configmap app-config -n <namespace> \
  --from-file=config.yaml=./local-config.yaml

# Or from literal values
kubectl create configmap app-config -n <namespace> \
  --from-literal=database_url=postgres://db.example.com:5432/mydb
```

### Fix 4: Update Environment Variables

```bash
# Patch deployment with correct environment variable
kubectl set env deployment/<deployment-name> -n <namespace> \
  DATABASE_HOST=postgres-service.database.svc.cluster.local
```

### Fix 5: Debug with Ephemeral Container (Kubernetes 1.23+)

If pod crashes too quickly to debug:

```bash
# Add debug container to running pod
kubectl debug <pod-name> -n <namespace> -it --image=busybox --share-processes

# Now you can inspect the crashed container's environment
ps aux  # See all processes including crashed app
cat /proc/1/environ  # View environment variables of main process
```

## Validation

After applying fixes:

```bash
# Watch pod status
watch kubectl get pods -n <namespace>

# Should transition: Pending → Running (and stay Running)

# Verify no restarts occurring
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[0].restartCount}'

# Check application health
kubectl exec <pod-name> -n <namespace> -- curl localhost:8080/health
```

**Success criteria**:
- Pod status is `Running` for >5 minutes
- Restart count stops increasing
- Application health endpoint returns 200 OK
- Application logs show successful startup

## Prevention Best Practices

### 1. Set Appropriate Resource Requests and Limits
Always define both requests and limits. Use historical metrics to inform values:
```yaml
resources:
  requests:
    memory: "256Mi"  # Based on average usage + 20% buffer
    cpu: "100m"
  limits:
    memory: "512Mi"  # Based on p95 usage + 50% buffer
    cpu: "500m"
```

### 2. Configure Probes Correctly
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30  # Allow time for app startup
  periodSeconds: 10        # Check every 10 seconds
  timeoutSeconds: 5        # 5 seconds to respond
  failureThreshold: 3      # 3 failures = restart

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 2
```

### 3. Use Init Containers for Dependencies
If your app needs a database to be ready before starting:
```yaml
initContainers:
- name: wait-for-db
  image: busybox
  command: ['sh', '-c', 'until nc -z postgres-service 5432; do sleep 2; done']
```

### 4. Implement Graceful Degradation
Don't crash if a non-critical dependency is unavailable. Log errors and retry:
```python
# Instead of this:
db = connect_to_database()  # Crashes if DB unavailable

# Do this:
try:
    db = connect_to_database()
except ConnectionError:
    logger.error("Database unavailable, will retry")
    db = None  # App starts, retries connection in background
```

## Troubleshooting Decision Tree

```
Is restart count increasing?
├─ NO → Not a crash loop, check other issues
└─ YES → Check exit code
    ├─ 137 (OOMKilled) → Increase memory limits
    ├─ 1 or 2 → Check application logs for errors
    │   ├─ Connection errors → Verify dependencies (Step 5)
    │   ├─ Config errors → Check ConfigMaps (Step 6)
    │   └─ Other app errors → Fix application code
    └─ 143 (SIGTERM) → Check if liveness probe is too aggressive
```

## Related Documentation

- [Kubernetes Resource Management](./kubernetes-resource-management.md)
- [Health Check Best Practices](./health-check-patterns.md)
- [ConfigMap and Secret Management](./kubernetes-config-management.md)
- [Monitoring Pod Restarts](./monitoring-setup-kubernetes.md)

## Common Scenarios

### Scenario: Database Connection Failure
**Symptoms**: Logs show `connection refused` to database service
**Solution**: Check NetworkPolicy allows traffic, verify service exists, confirm credentials in Secret

### Scenario: OOMKilled During Startup
**Symptoms**: Exit code 137, high memory usage in logs
**Solution**: Increase memory limits, optimize application memory usage, consider using init containers to pre-load data

### Scenario: Probe Killing Healthy App
**Symptoms**: App logs show successful startup, then sudden termination
**Solution**: Increase `initialDelaySeconds` and `timeoutSeconds` on liveness probe

## Quick Reference

```bash
# Essential debugging commands
kubectl get pod <pod> -n <ns>              # Check status
kubectl describe pod <pod> -n <ns>         # Detailed info + events
kubectl logs <pod> -n <ns> --previous      # Logs from crashed container
kubectl exec -it <pod> -n <ns> -- /bin/sh  # Shell into container (if running)
kubectl debug <pod> -n <ns> --image=busybox # Debug crashed pod
```
