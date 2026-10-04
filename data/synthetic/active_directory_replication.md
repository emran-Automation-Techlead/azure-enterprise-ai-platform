---
id: DOC-005
title: Active Directory Replication Failure Runbook
category: Active Directory
type: RUNBOOK
owner: Identity Team
last_reviewed: 2026-03-30
synthetic: true
---

# Active Directory Replication Failure Runbook
## Symptoms
New accounts or password changes are visible on one domain controller but not another. Event ID 1988 or replication errors in the Directory Service log.

## Checks
1. Run a replication summary and review failing partners and error codes.
2. Check network connectivity and DNS between the affected domain controllers.
3. Check the site link schedule and interval.
4. Look for evidence of a restore from an unsupported snapshot (USN rollback).

## Actions
- For lagging replication, force a sync after fixing the cause.
- For suspected USN rollback, isolate the domain controller and escalate to the Identity Team. Do not attempt demotion without approval.

## Prevention
Do not restore domain controllers from VM snapshots. Use AD-aware backup tooling.
