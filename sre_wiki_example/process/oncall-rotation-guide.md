# On-Call Rotation Guide

> **Category:** Process & Workflow  |  **Owner:** SRE Leadership  |  **Last Updated:** 2024-11-15

## Overview

This document defines the on-call rotation structure, responsibilities, escalation procedures, and compensation for SRE team members. The on-call rotation ensures 24/7 coverage for production incidents while maintaining sustainable work-life balance for the team.

## Rotation Structure

### Coverage Model
- **Primary On-Call**: First responder for all alerts
- **Secondary On-Call**: Backup if primary doesn't respond within 15 minutes
- **Manager On-Call**: Escalation point for SEV1 incidents requiring leadership decisions

### Rotation Schedule
- **Shift Duration**: 7 days (Monday 9:00 AM to following Monday 9:00 AM, local time)
- **Rotation Cycle**: All team members rotate through primary and secondary roles
- **Handoff**: Mondays at 9:00 AM local time
- **Advance Notice**: Schedule published 8 weeks in advance

### Team Members in Rotation
Current rotation includes 8 SRE engineers:
- Alex Rivera (US-East timezone)
- Jamie Chen (US-Pacific timezone)
- Morgan Taylor (US-Central timezone)
- Casey Anderson (US-East timezone)
- Sam Park (EU-London timezone)
- Jordan Matthews (EU-Amsterdam timezone)
- Riley Singh (APAC-Singapore timezone)
- Dakota Johnson (US-Pacific timezone)

**Coverage**: 24/7 global coverage with at least one engineer in reasonable timezone for incident response.

## On-Call Responsibilities

### Primary On-Call Engineer

#### During Business Hours (9 AM - 5 PM Local Time)
- Monitor PagerDuty for incoming alerts
- Respond to alerts within **5 minutes**
- Triage incidents and determine severity (SEV1, SEV2, SEV3)
- Execute runbooks for common issues
- Escalate to secondary or specialist teams as needed
- Update status page for customer-impacting incidents
- Document actions taken in incident ticket

#### Outside Business Hours (5 PM - 9 AM Local Time, Weekends, Holidays)
- Respond to **critical alerts only** (SEV1, SEV2)
- Response time: **15 minutes** for critical alerts
- SEV3 alerts queued for business hours unless they auto-escalate
- Focus on service restoration; detailed RCA can wait until business hours
- Page secondary on-call if issue requires specialized expertise

### Secondary On-Call Engineer

- Monitor PagerDuty for missed acknowledgments
- Step in if primary doesn't acknowledge within **15 minutes**
- Available for consultation on complex incidents
- Take over incident if primary is overwhelmed or multiple incidents occur
- Response expectation: Within **20 minutes** of escalation

### Shared Responsibilities

1. **Pre-Shift Preparation**:
   - Review recent incidents and ongoing issues
   - Attend handoff meeting with outgoing on-call
   - Test PagerDuty alerts (send test page to yourself)
   - Ensure laptop and VPN access functional
   - Review any scheduled maintenance or deployments

2. **During Shift**:
   - Keep laptop and phone accessible at all times
   - Maintain reliable internet connection
   - Update PagerDuty status if temporarily unavailable (>30 minutes)
   - Document all incidents in incident management system
   - Communicate in #oncall-updates Slack channel

3. **Post-Shift**:
   - Conduct handoff meeting with incoming on-call
   - Complete any pending incident documentation
   - File tickets for unresolved issues
   - Provide feedback on runbook gaps or alert noise

## Alert Triage and Response

### Severity Definitions

| Severity | Description | Response Time | Escalation |
|----------|-------------|---------------|------------|
| **SEV1** | Complete service outage, data loss, security breach | 5 minutes | Immediate bridge with leadership |
| **SEV2** | Significant degradation, affecting >10% of users | 15 minutes | Page secondary after 30 min |
| **SEV3** | Minor issue, affecting <10% of users, workaround exists | 1 hour (business hours only) | Ticket for follow-up |
| **Informational** | FYI alerts, no action required | No response required | None |

### Response Workflow

```
Alert Received
    ↓
Acknowledge in PagerDuty (<5 min)
    ↓
Assess severity (check dashboards, logs)
    ↓
├─ SEV1: Open incident bridge immediately
├─ SEV2: Start investigation, open ticket
└─ SEV3: Create ticket, address during business hours
    ↓
Execute runbook (if exists)
    ↓
├─ Issue Resolved → Update ticket, close alert
└─ Issue Unresolved → Escalate to specialist or secondary
    ↓
Post-incident: Document actions, update runbooks if needed
```

### Escalation Paths

#### Database Issues
- **Primary escalation**: Database SRE team (PD escalation policy: `SRE-Database`)
- **Contact**: Jamie Chen (primary DB expert)
- **Slack channel**: #team-database-sre

#### Network/Infrastructure Issues
- **Primary escalation**: Infrastructure team (PD escalation policy: `SRE-Infra`)
- **Contact**: Alex Rivera
- **Slack channel**: #team-infra-sre

#### Application-Specific Issues
- **Auth Service**: `@oncall-auth-team` in Slack, PD policy: `Team-Auth`
- **Payment Service**: `@oncall-payments` in Slack, PD policy: `Team-Payments`
- **Search Service**: `@oncall-search` in Slack, PD policy: `Team-Search`

#### Security Incidents
- **Immediate escalation**: Security Operations Center (SOC)
- **Contact**: security-oncall@company.com
- **Phone**: +1-555-SOC-ALERT (24/7)
- **Slack channel**: #security-incidents (private)

#### Leadership Escalation
- **When to escalate**: SEV1 lasting >1 hour, data loss, legal/compliance issues, PR/communications needed
- **Manager On-Call**: Via PD escalation policy `SRE-Management`
- **VP Engineering**: Only for business-critical decisions (e.g., approving emergency rollback that breaks contract SLA)

## Communication Expectations

### Internal Communication

**#oncall-updates Slack Channel**:
- Post when you take over an incident
- Provide status updates every 30 minutes for SEV1, hourly for SEV2
- Announce when incident is resolved
- Use thread replies to keep channel organized

**Incident Bridge** (Zoom):
- SEV1: Open bridge within 5 minutes of detection
- SEV2: Open bridge if incident lasts >30 minutes
- Post bridge link in #oncall-updates
- Assign roles: Incident Commander, Technical Lead, Communications Lead

### External Communication

**Status Page** (status.company.com):
- Update within 10 minutes of SEV1 detection
- Provide honest, clear updates (avoid jargon)
- Update every 30 minutes during active SEV1
- Post resolution notice and brief RCA after incident

**Customer Support**:
- Notify #customer-support channel for all customer-impacting incidents
- Provide 2-3 sentence summary they can use with customers
- Update when resolution ETA changes
- Provide final resolution message when incident is closed

## Compensation and Benefits

### On-Call Pay
- **Weekday on-call** (Monday 5 PM - Friday 5 PM): $100/day stipend
- **Weekend on-call** (Friday 5 PM - Monday 9 AM): $200/day stipend
- **Holiday on-call**: $300/day stipend

### Incident Response Pay
- **After-hours response** (outside 9 AM - 5 PM local time): 1.5x hourly rate for time spent responding
- **Minimum billing**: 1 hour per incident
- **Multiple incidents**: Clock continues across all incident work in a 4-hour window

### Compensation Cap
- Maximum 10 hours/week of after-hours incident response billable at 1.5x rate
- Additional hours are salaried (no extra pay but tracked for workload balancing)

### Time Off In Lieu (TOIL)
If on-call shift includes:
- **>5 hours of after-hours incident work**: 1 day TOIL
- **>10 hours of after-hours incident work**: 2 days TOIL
- **TOIL must be used within 30 days** of accrual

## Workload Balancing

### Skip Rotation Eligibility
Team members can skip rotation (no penalty) if:
- Recently completed >2 weeks of on-call in past month
- Responded to >15 hours of incidents in previous shift
- Upcoming PTO (vacation starts within 5 days of shift end)
- Significant personal life event (new child, family emergency)

**Process**: Notify SRE manager at least 2 weeks in advance (1 week for emergencies). Manager will find coverage.

### Alert Noise Reduction
If on-call shift includes:
- **>20 pages**: Schedule postmortem to review alert quality
- **>10 false positives**: Priority tickets filed to fix alerting
- **>5 SEV3 alerts outside business hours**: Alerts should be downgraded to informational

**Goal**: High-signal alerts only. On-call should not be firefighting constant noise.

## Tools and Access

### Required Access
Before your first on-call shift, verify you have:
- [ ] PagerDuty account with mobile app installed
- [ ] VPN access configured and tested
- [ ] kubectl access to all production clusters
- [ ] AWS Console access (read-only minimum, admin for senior SREs)
- [ ] Datadog/Grafana dashboard access
- [ ] Slack mobile app with notifications enabled for #oncall-updates
- [ ] Zoom desktop app (for incident bridges)
- [ ] 1Password access to SRE team vaults

### PagerDuty Configuration
- **High-urgency notifications**: Phone call + SMS + push notification
- **Low-urgency notifications**: Push notification only (no phone call)
- **Notification rules**: Retry every 5 minutes up to 3 times before escalating
- **Test your alerts**: Send yourself a test page before shift starts

### Laptop and Connectivity
- **Company-issued laptop**: Must be available during entire shift
- **Internet backup**: Have backup internet (mobile hotspot) in case primary fails
- **Phone battery**: Keep phone charged; have portable charger available
- **Travel during on-call**: Notify team, ensure reliable internet at destination

## On-Call Shift Handoff

### Outgoing On-Call Responsibilities
- Schedule 30-minute handoff meeting with incoming on-call
- Prepare handoff document covering:
  - Ongoing incidents (status, ETA, who's involved)
  - Recently resolved incidents (potential for recurrence)
  - Known issues or degradations (even if not alerting)
  - Scheduled maintenance or deployments this week
  - High-value customers having issues (context for support tickets)

### Incoming On-Call Responsibilities
- Attend handoff meeting (mandatory, not optional)
- Ask questions about anything unclear
- Review dashboards for current system state
- Test PagerDuty alert delivery
- Acknowledge taking over shift in #oncall-updates

### Handoff Document Template
```
## On-Call Handoff: [Date]
**Outgoing**: [Name]
**Incoming**: [Name]

### Ongoing Incidents
- [INC-123] Database replication lag - monitoring, DB team engaged

### Recent Incidents (last 7 days)
- [INC-120] Redis OOM - resolved, but watch memory usage
- [INC-118] Auth service crash loop - resolved with config change

### Known Issues
- Payment service seeing elevated latency (p99 = 500ms, threshold = 300ms)
- Increased API 429 rate limit errors (Marketing campaign launched yesterday)

### Scheduled Activities This Week
- Tuesday 2 PM: Deploy payment service v3.1.2
- Thursday 10 AM: Database maintenance window (read-only 15 min)

### Notes
- Black Friday preparation next week, expect higher traffic
- New runbook added for Redis cache eviction: [link]
```

## Training and Onboarding

### New Team Member Onboarding
Before joining on-call rotation:
1. **Shadow 2 full shifts**: Observe experienced on-call engineer
2. **Reverse shadow 1 shift**: Lead incident response with mentor observing
3. **Complete runbook drills**: Execute 5 common runbooks in staging
4. **Pass on-call quiz**: 20 question quiz on escalation, severity, procedures
5. **Manager sign-off**: Manager approves readiness for solo on-call

**Typical timeline**: 6-8 weeks for new SRE hire to join rotation.

### Continuous Training
- **Monthly runbook review**: Team reviews 2-3 runbooks together
- **Quarterly disaster recovery drill**: Simulate major outage scenarios
- **Incident retrospectives**: Learn from real incidents (no blame, learning focus)
- **Runbook updates**: On-call engineer responsible for documenting gaps found during shift

## Burnout Prevention

### Team Health Metrics
SRE leadership monitors:
- Average hours of after-hours incident response per person per month
- Distribution of on-call shifts (ensure fairness)
- Feedback from on-call shifts (survey after each shift)
- TOIL accrual and usage rates

**Targets**:
- <10 hours/month average after-hours incident time per person
- <3 consecutive weeks of on-call for any individual
- >80% positive feedback on on-call experience
- >90% of TOIL used within 30 days (not accumulating)

### Red Flags
If any team member shows:
- >20 hours after-hours incident work in a month
- Multiple skipped rotations due to burnout
- Negative feedback on multiple consecutive shifts

**Action**: Manager schedules 1:1 to discuss workload, consider temporary rotation exemption, address root cause (alert noise, tooling gaps, staffing).

### Vacation Policy During On-Call
- **Vacation overrides on-call**: Scheduled PTO takes precedence
- **Notify manager 2+ weeks before vacation** to arrange coverage
- **Emergency PTO**: Notify on-call secondary immediately, they cover until manager finds replacement

## Feedback and Continuous Improvement

### Post-Shift Survey
After each on-call shift, complete 5-minute survey:
- Alert quality (too many false positives?)
- Runbook coverage (gaps you encountered?)
- Tooling issues (access problems, slow dashboards?)
- Overall experience rating (1-5 scale)
- Suggestions for improvement

**Survey link**: [Google Form](https://forms.google.com/oncall-feedback) (internal)

### Monthly On-Call Retrospective
- **When**: First Monday of each month, 2:00 PM ET
- **Who**: All SRE team members
- **Agenda**:
  - Review alert noise trends
  - Discuss recurring incidents
  - Celebrate wins (good incident response, helpful runbook updates)
  - Prioritize improvements for next month

## Related Documentation

- [Incident Response Process](./incident-response.md)
- [Incident Escalation Guide](./incident-escalation.md)
- [Alert Tuning Best Practices](../how-to/alert-tuning.md)
- [Runbook Index](../runbooks/README.md)
- [PagerDuty Configuration Guide](../how-to/pagerduty-setup.md)

## Appendix: FAQ

**Q: What if I'm on vacation during my scheduled on-call week?**
A: Vacation takes precedence. Notify manager 2+ weeks in advance. Manager will arrange coverage.

**Q: Can I swap on-call shifts with a teammate?**
A: Yes, coordinate with teammate and notify manager. Both parties must agree, and swap must be recorded in PagerDuty.

**Q: What if I miss an alert?**
A: Secondary will be paged after 15 minutes. After incident is resolved, discuss with manager. Occasional misses due to technical issues are understandable; repeated misses may require training or process adjustment.

**Q: Do I get compensated for false positive alerts that wake me up?**
A: Yes, after-hours incident response time includes investigation of false positives. Also, please file ticket to fix the false positive so it doesn't happen again.

**Q: What if multiple SEV1 incidents happen simultaneously?**
A: Secondary automatically joins. Incident Commander role coordinates both incidents. Additional engineers can be paged via "all hands" escalation policy if needed.

**Q: Can I work remotely during on-call?**
A: Yes, as long as you have reliable internet, laptop access, and are in a timezone where you can reasonably respond to alerts.

---

**Document Owner**: SRE Leadership Team
**Review Cadence**: Quarterly
**Last Review**: 2024-11-15
**Next Review**: 2025-02-15
