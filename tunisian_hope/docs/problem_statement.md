# Problem Statement

## Platform Name
**Tunisian Hope & Future** — A social-impact platform for youth support.

## Population
Children and young people aged 6–18 in Tunisia (synthetic data only).

## Problem
Early detection of disengagement and health risks
among Tunisian youth, using structured workflows and data-driven indicators.

## Decision Makers
- **Schools**: Teachers, school counselors — identify at-risk students early
- **Health Teams**: Community health workers — track follow-up adherence
- **Supervisors**: NGO coordinators — validate interventions and escalate

## Operational Workflow
1. **Field Operator** creates a Case record (intake)
2. **Supervisor** assesses the case using indicators (scoring, thresholds)
3. **Supervisor** plans and executes an intervention
4. Case moves through: INTAKE → ASSESSMENT → ACTIVE → FOLLOW-UP → CLOSED

## Expected Value
- Faster identification of at-risk youth (reduce response time from weeks to days)
- Better follow-up adherence (automated reminders, tracked appointments)
- Transparent decision-making (audit trail for every action)

## Validation Rules
- A case is "successfully handled" if it reaches CLOSED status with documented intervention
- A case is "at-risk" if it stays in INTAKE for more than 7 days without assessment
- Unauthorized actions are blocked and logged with reason

## Data & Ethics Boundary
- **Synthetic data only** — no real personal, medical, or confidential records
- All student IDs are randomly generated (STU-2026-XXX format)
- No real names, addresses, or identifiable information
- Access is role-controlled: operators see only their cases, supervisors see all cases
