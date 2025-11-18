# Event Prep: Holiday Traffic Readiness

> **Event Window:** Nov 20 – Jan 5  |  **Primary Services:** Checkout, Auth, Inventory  |  **Prepared By:** SRE Program Office

## Objective
Ensure critical services survive 3x baseline load during holiday promotions by pre-scaling infrastructure, validating failover drills, and coordinating with vendors.

## Checklist
### Capacity
- [ ] Increase checkout cluster replicas from 20 -> 60.
- [ ] Validate autoscaling policies (HPA + Karpenter) with load test.
- [ ] Confirm DB connection pool tuning per service.

### Resiliency Drills
- [ ] Run chaos experiment `chaos/checkout-node-failure`.
- [ ] Conduct failover to secondary region for Auth.
- [ ] Validate inventory cache eviction strategy.

### Communications
- [ ] Share readiness plan with stakeholders from `../stakeholders/contacts.md`.
- [ ] Schedule daily standups during peak week.
- [ ] Publish status updates in #event-holiday.

## Validation Criteria
- Load test demonstrates < 300ms p95 for checkout under 3x load.
- Failover rehearsals complete without manual interventions.
- Vendor SLAs confirmed and logged in stakeholder sheet.

## References
- Runbooks: `../runbooks/auth-service-restart.md`
- How-To: `../how-to/zero-downtime-deployments.md`
- Assets: `../assets/lucid-platform-traffic-shift.md`
