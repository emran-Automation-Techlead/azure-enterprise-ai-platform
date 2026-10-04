---
id: DOC-001
title: VPN Authentication Troubleshooting Runbook
category: VPN
type: RUNBOOK
owner: Network Operations
last_reviewed: 2026-06-10
synthetic: true
---

# VPN Authentication Troubleshooting Runbook
## Purpose
Steps for service-desk engineers when users cannot authenticate to the corporate SSL VPN.

## Symptoms
- Users see "authentication failed" or the VPN client loops back to the login prompt.
- Several users fail at the same time, often after a change window.

## Checks (in order)
1. Confirm whether one user or many are affected. Many users usually indicates a shared dependency, not a user error.
2. Check the VPN concentrator authentication log for RADIUS timeouts or rejects.
3. Verify the RADIUS/NPS server is running and reachable from the concentrator.
4. Confirm the identity provider and MFA service are healthy (see DOC-009).
5. Check that the VPN server certificate has not expired.
6. Check for recent changes to VPN, firewall or identity configuration.

## Resolution notes
- Restarting the NPS service resolved a past outage caused by a hung authentication process.
- An expired VPN server certificate must be renewed by Network Operations.

## Idle timeout
The current standard VPN idle timeout is 45 minutes with a client keep-alive of 5 minutes.

## Escalation
Escalate to Network Operations (tier 2) if the RADIUS server is healthy and failures persist after 30 minutes.
