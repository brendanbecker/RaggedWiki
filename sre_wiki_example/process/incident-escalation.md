# Process: Incident Escalation Workflow

> **Applies To:** All production services  |  **Audience:** On-call SREs & Engineering Managers  |  **Version:** 2025.02

## Purpose
Define the repeatable steps for escalating incidents across engineering, product, and vendor partners.

## Roles & Responsibilities
- **Incident Commander (IC):** Owns overall response.
- **Communications Lead (CL):** Handles stakeholder updates every 30 minutes.
- **Scribe:** Captures timeline in real time.

## Workflow
### Stage 1: Detection
1. Pager triggers to on-call engineer.
2. On-call acknowledges within 5 minutes.
3. Determine severity using runbook severity table.

### Stage 2: Mobilization
1. Assign IC + CL in PagerDuty.
2. Create incident Slack channel `#inc-<date>-<slug>`.
3. Invite product lead + relevant vendors.

### Stage 3: Communication Cadence
- Internal updates every 15 minutes (Slack + status doc).
- External updates (customers) every 30 minutes for SEV2+.
- Maintain stakeholder list from `../stakeholders/contacts.md`.

## Closure Criteria
- Mitigation verified (runbook reference recorded).
- Postmortem scheduled within 48 hours.
- Action items tracked in incident ticket.

## References
- Template: `../incidents/postmortem-template.md`
- Stakeholders: `../stakeholders/contacts.md`
