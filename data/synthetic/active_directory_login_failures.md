---
id: DOC-004
title: Active Directory Login Failure Troubleshooting
category: Active Directory
type: RUNBOOK
owner: Identity Team
last_reviewed: 2026-05-22
synthetic: true
---

# Active Directory Login Failure Troubleshooting
## Symptoms
Users cannot sign in to domain-joined Windows devices, or see "The trust relationship between this workstation and the primary domain failed".

## Checks
1. Confirm the user account is not locked out or disabled.
2. Verify the device can reach a domain controller (network and DNS).
3. Check that the device clock is within 5 minutes of the domain controller (Kerberos requirement).
4. Check domain controller health and replication status (see DOC-005).
5. For a broken trust relationship, rejoin the device to the domain using an approved administrator account.

## Common causes
- Time drift causing Kerberos failures.
- DNS pointing at the wrong server.
- Account lockouts from stale cached credentials on mobile devices or mapped drives.

## Escalation
Escalate to the Identity Team if multiple users on different devices cannot authenticate.
