# How To: Set Up Prometheus Monitoring for New Services

> **Category:** Monitoring & Observability  |  **Difficulty:** Intermediate  |  **Time:** 45-60 minutes

## Overview

This guide walks through instrumenting a new service with Prometheus metrics, configuring scrape targets, and creating initial dashboards. You'll learn the standard metrics to expose, naming conventions, and integration with our existing Grafana dashboards.

## Prerequisites

- Service deployed in Kubernetes
- kubectl access to the target namespace
- Access to Grafana (https://grafana.company.com)
- Prometheus deployment in `monitoring` namespace
- Basic understanding of your service's architecture

## Prometheus Architecture Overview

Our Prometheus setup:
- **Prometheus Server**: Deployed as StatefulSet in `monitoring` namespace
- **Service Discovery**: Kubernetes service discovery via annotations
- **Storage**: 30-day retention, backed by persistent volumes
- **Federation**: Metrics federated to central Prometheus for long-term storage
- **Alerting**: AlertManager handles notification routing

## Step 1: Instrument Your Application

### For Go Applications

```go
package main

import (
    "net/http"
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
    // Counter: Monotonically increasing value
    requestsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "myapp_http_requests_total",
            Help: "Total number of HTTP requests",
        },
        []string{"method", "endpoint", "status"},
    )

    // Histogram: Observations bucketed by value
    requestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "myapp_http_request_duration_seconds",
            Help:    "HTTP request latency in seconds",
            Buckets: prometheus.DefBuckets, // 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10
        },
        []string{"method", "endpoint"},
    )

    // Gauge: Value that can go up or down
    activeConnections = promauto.NewGauge(
        prometheus.GaugeOpts{
            Name: "myapp_active_connections",
            Help: "Number of active database connections",
        },
    )
)

func main() {
    // Expose metrics endpoint
    http.Handle("/metrics", promhttp.Handler())

    // Your application handlers
    http.HandleFunc("/api", handleAPI)

    http.ListenAndServe(":8080", nil)
}

func handleAPI(w http.ResponseWriter, r *http.Request) {
    timer := prometheus.NewTimer(requestDuration.WithLabelValues(r.Method, r.URL.Path))
    defer timer.ObserveDuration()

    // Your business logic here

    requestsTotal.WithLabelValues(r.Method, r.URL.Path, "200").Inc()
    w.WriteHeader(http.StatusOK)
}
```

### For Python Applications (Flask)

```python
from flask import Flask, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

app = Flask(__name__)

# Define metrics
requests_total = Counter(
    'myapp_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'myapp_http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'myapp_active_connections',
    'Number of active database connections'
)

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    request_duration.labels(
        method=request.method,
        endpoint=request.endpoint
    ).observe(time.time() - request.start_time)

    requests_total.labels(
        method=request.method,
        endpoint=request.endpoint,
        status=response.status_code
    ).inc()

    return response

@app.route('/metrics')
def metrics():
    return generate_latest()

@app.route('/api/data')
def get_data():
    # Your business logic
    return {"data": "value"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

## Step 2: Define Standard Metrics

Every service should expose these core metrics:

### RED Metrics (Request-focused)
1. **Rate**: Requests per second
   - Metric: `myapp_http_requests_total` (counter)
   - Labels: `method`, `endpoint`, `status`

2. **Errors**: Error rate
   - Derived from `myapp_http_requests_total{status=~"5.."}`

3. **Duration**: Request latency
   - Metric: `myapp_http_request_duration_seconds` (histogram)
   - Labels: `method`, `endpoint`

### USE Metrics (Resource-focused)
1. **Utilization**: % of resource in use
   - Examples: CPU usage, memory usage, connection pool utilization
   - Metric type: Gauge

2. **Saturation**: Queue depth, backlog
   - Examples: Request queue length, pending jobs
   - Metric type: Gauge

3. **Errors**: Error count
   - Examples: Failed DB queries, timeout errors
   - Metric type: Counter

### Business Metrics
Service-specific metrics that matter to your domain:
- `payment_transactions_total` (counter)
- `user_signups_total` (counter)
- `cache_hit_rate` (gauge, derived from cache_hits / cache_total)
- `background_job_duration_seconds` (histogram)

## Step 3: Configure Kubernetes Service for Scraping

Add Prometheus annotations to your Kubernetes Service:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
  namespace: production
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
  labels:
    app: myapp
    tier: backend
spec:
  selector:
    app: myapp
  ports:
  - name: http
    port: 8080
    targetPort: 8080
  - name: metrics
    port: 8080
    targetPort: 8080
```

**Key annotations**:
- `prometheus.io/scrape: "true"` → Tells Prometheus to scrape this service
- `prometheus.io/port: "8080"` → Port where metrics are exposed
- `prometheus.io/path: "/metrics"` → Endpoint path (default is `/metrics`)

## Step 4: Verify Scraping Configuration

```bash
# Check if Prometheus discovered your service
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Open browser: http://localhost:9090/targets
# Search for your service name - should show status "UP"

# Or use kubectl to check from terminal
kubectl exec -n monitoring deployment/prometheus -- \
  wget -qO- http://localhost:9090/api/v1/targets | \
  jq '.data.activeTargets[] | select(.labels.job | contains("myapp"))'
```

**Expected output**:
```json
{
  "discoveredLabels": {...},
  "labels": {
    "job": "kubernetes-service-endpoints",
    "kubernetes_name": "myapp-service",
    "kubernetes_namespace": "production"
  },
  "scrapeUrl": "http://10.244.1.15:8080/metrics",
  "health": "up",
  "lastScrape": "2024-11-20T10:30:45Z"
}
```

## Step 5: Test Metrics Endpoint

```bash
# Port-forward to your application pod
kubectl port-forward -n production pod/myapp-xxxxx 8080:8080

# Curl the metrics endpoint
curl http://localhost:8080/metrics
```

**Expected output**:
```
# HELP myapp_http_requests_total Total number of HTTP requests
# TYPE myapp_http_requests_total counter
myapp_http_requests_total{method="GET",endpoint="/api/data",status="200"} 1523
myapp_http_requests_total{method="POST",endpoint="/api/data",status="201"} 342

# HELP myapp_http_request_duration_seconds HTTP request latency in seconds
# TYPE myapp_http_request_duration_seconds histogram
myapp_http_request_duration_seconds_bucket{method="GET",endpoint="/api/data",le="0.005"} 1200
myapp_http_request_duration_seconds_bucket{method="GET",endpoint="/api/data",le="0.01"} 1450
myapp_http_request_duration_seconds_bucket{method="GET",endpoint="/api/data",le="0.025"} 1500
...
```

## Step 6: Create Grafana Dashboard

### Option A: Use Dashboard Template

```bash
# Import our standard service dashboard template
# In Grafana: Dashboards > Import > ID: 12345 (internal template)

# Customize variables:
# - namespace: production
# - service: myapp-service
# - instance: All
```

### Option B: Create Custom Dashboard

1. **Create dashboard in Grafana**:
   - Navigate to Grafana → Dashboards → New Dashboard
   - Add Panel

2. **Request Rate Panel**:
```promql
# Requests per second by endpoint
sum(rate(myapp_http_requests_total[5m])) by (endpoint)
```

3. **Error Rate Panel**:
```promql
# Percentage of 5xx errors
sum(rate(myapp_http_requests_total{status=~"5.."}[5m]))
/
sum(rate(myapp_http_requests_total[5m])) * 100
```

4. **Latency Panel** (p50, p95, p99):
```promql
# p50 latency
histogram_quantile(0.50,
  sum(rate(myapp_http_request_duration_seconds_bucket[5m])) by (le, endpoint)
)

# p95 latency
histogram_quantile(0.95,
  sum(rate(myapp_http_request_duration_seconds_bucket[5m])) by (le, endpoint)
)

# p99 latency
histogram_quantile(0.99,
  sum(rate(myapp_http_request_duration_seconds_bucket[5m])) by (le, endpoint)
)
```

5. **Active Connections Panel**:
```promql
myapp_active_connections
```

## Step 7: Set Up Alerts

Create PrometheusRule resource:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: myapp-alerts
  namespace: production
spec:
  groups:
  - name: myapp
    interval: 30s
    rules:
    - alert: HighErrorRate
      expr: |
        sum(rate(myapp_http_requests_total{status=~"5.."}[5m]))
        /
        sum(rate(myapp_http_requests_total[5m])) > 0.05
      for: 5m
      labels:
        severity: warning
        service: myapp
      annotations:
        summary: "High error rate on {{ $labels.instance }}"
        description: "Error rate is {{ $value | humanizePercentage }} over the last 5 minutes"

    - alert: HighLatency
      expr: |
        histogram_quantile(0.95,
          sum(rate(myapp_http_request_duration_seconds_bucket[5m])) by (le)
        ) > 1.0
      for: 10m
      labels:
        severity: warning
        service: myapp
      annotations:
        summary: "High latency detected"
        description: "p95 latency is {{ $value }}s (threshold: 1s)"

    - alert: ServiceDown
      expr: up{job="kubernetes-service-endpoints", kubernetes_name="myapp-service"} == 0
      for: 2m
      labels:
        severity: critical
        service: myapp
      annotations:
        summary: "Service is down"
        description: "Prometheus cannot scrape myapp-service"
```

Apply the alert:
```bash
kubectl apply -f myapp-alerts.yaml
```

## Step 8: Validate End-to-End

### Generate Traffic
```bash
# Generate test traffic to create metrics
for i in {1..100}; do
  curl http://myapp-service.production.svc.cluster.local:8080/api/data
  sleep 0.1
done
```

### Check Metrics in Prometheus
```bash
# Query Prometheus directly
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Open browser: http://localhost:9090/graph
# Run query: rate(myapp_http_requests_total[1m])
```

**Expected**: Graph shows increasing request rate.

### Verify Dashboard
- Open Grafana dashboard
- Confirm panels populate with data
- Check that metrics update in real-time

### Test Alerts
```bash
# Verify alert rules are loaded
kubectl get prometheusrules -n production myapp-alerts

# Check AlertManager for firing alerts (if any)
kubectl port-forward -n monitoring svc/alertmanager 9093:9093
# Browse to: http://localhost:9093
```

## Metric Naming Best Practices

Follow Prometheus naming conventions:

### Format: `<namespace>_<subsystem>_<metric>_<unit>`

Examples:
- `myapp_http_requests_total` (no unit for counters ending in _total)
- `myapp_http_request_duration_seconds` (histogram with unit)
- `myapp_database_connections_active` (gauge describing state)
- `myapp_cache_hits_total` (counter)

### Rules:
1. Use snake_case, not camelCase
2. Counters should end in `_total`
3. Histograms/summaries should include unit (`_seconds`, `_bytes`)
4. Gauges should describe current state (`_active`, `_utilization`, `_percentage`)
5. Don't include `_count` suffix (it's redundant with counter)

### Label Cardinality
**Keep label cardinality low**. Avoid high-cardinality labels like:
- User IDs
- Request IDs
- Timestamps
- IP addresses (except in specific use cases)

**Good labels** (low cardinality):
- HTTP method (GET, POST, PUT, DELETE) → ~7 values
- HTTP status code (200, 404, 500) → ~20 values
- Endpoint group (/api/users, /api/orders) → <100 values

**Bad labels** (high cardinality):
- User ID → millions of values
- Full URL path with IDs (/api/users/123456) → unbounded

## Troubleshooting

### Metrics Not Appearing in Prometheus

**Check 1**: Service annotation correct?
```bash
kubectl get svc myapp-service -n production -o yaml | grep prometheus
```

**Check 2**: Metrics endpoint accessible?
```bash
kubectl run curl-test --image=curlimages/curl -it --rm -- \
  curl http://myapp-service.production.svc.cluster.local:8080/metrics
```

**Check 3**: Prometheus config reload?
```bash
# Trigger config reload
kubectl exec -n monitoring deployment/prometheus -- \
  curl -X POST http://localhost:9090/-/reload
```

### High Memory Usage in Prometheus

**Cause**: Too many metrics or high label cardinality.

**Solution**:
1. Check cardinality: `http://localhost:9090/api/v1/status/tsdb`
2. Identify high-cardinality metrics
3. Reduce labels in application code
4. Increase Prometheus memory limits if needed

### Alerts Not Firing

**Check 1**: PrometheusRule loaded?
```bash
kubectl get prometheusrules -n production
kubectl describe prometheusrule myapp-alerts -n production
```

**Check 2**: AlertManager receiving alerts?
```bash
kubectl logs -n monitoring deployment/alertmanager
```

## Related Documentation

- [Prometheus Query Language (PromQL)](../how-to/promql-guide.md)
- [Alerting Best Practices](../process/alerting-philosophy.md)
- [Grafana Dashboard Standards](../process/dashboard-standards.md)
- [Metric Naming Conventions](../process/metric-naming.md)

## Next Steps

After monitoring is set up:
1. Create SLOs (Service Level Objectives) based on your metrics
2. Set up recording rules for frequently-queried metrics
3. Configure AlertManager notification channels (PagerDuty, Slack)
4. Add custom business metrics specific to your service
5. Document your metrics in service README
