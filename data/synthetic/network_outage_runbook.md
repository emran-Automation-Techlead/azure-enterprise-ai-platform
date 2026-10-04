---
id: DOC-007
title: Site Network Outage Runbook
category: Networking
type: RUNBOOK
owner: Network Operations
last_reviewed: 2026-01-25
synthetic: true
---

# Site Network Outage Runbook
## Symptoms
Users at a site lose connectivity to internal systems or the internet.

## Checks
1. Determine scope: one device, one switch, one site, or all sites.
2. Check the site uplink and WAN circuit status.
3. Check the core switch and firewall health dashboards.
4. Check for recent network changes.

## Communication
Open a major incident if more than 50 users are affected. Update stakeholders every 30 minutes.

## Escalation
Escalate to Network Operations on-call for any site-wide outage.
