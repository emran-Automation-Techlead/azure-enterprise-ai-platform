---
id: DOC-006
title: Internal DNS Resolution Troubleshooting
category: Networking
type: RUNBOOK
owner: Network Operations
last_reviewed: 2026-02-14
synthetic: true
---

# Internal DNS Resolution Troubleshooting
## Symptoms
Internal hostnames fail to resolve while external websites work.

## Checks
1. Compare resolution against each internal DNS server.
2. Confirm the DNS service is running on every internal DNS server.
3. Confirm clients list a healthy server first.
4. Verify zone data and forwarders.

## Resolution notes
Restarting a stopped DNS service and correcting the client DNS server order resolved a past incident.
