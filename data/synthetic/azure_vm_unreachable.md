---
id: DOC-014
title: Cloud: Azure Virtual Machine Unreachable
category: Cloud
type: RUNBOOK
owner: Cloud Platform Team
last_reviewed: 2026-06-15
synthetic: true
---

# Cloud: Azure Virtual Machine Unreachable
## Symptoms
A cloud virtual machine does not respond to RDP, SSH or application traffic.

## Checks
1. Check VM power state and platform health in the cloud portal.
2. Check network security group rules and effective routes.
3. Check boot diagnostics output.
4. Check recent configuration changes in the activity log.

## Actions
Restarting a production VM requires confirming the owning application team's approval. Escalate to the Cloud Platform Team for platform health events.
