---
id: DOC-011
title: Database Connection Failure Troubleshooting
category: Database
type: RUNBOOK
owner: Database Team
last_reviewed: 2026-06-20
synthetic: true
---

# Database Connection Failure Troubleshooting
## Symptoms
Applications report connection timeouts to the database; intermittent success.

## Checks
1. Check whether the database service is up and accepting connections.
2. Check for blocking sessions and long-running transactions.
3. Check application connection pool settings and connection leaks.
4. Check recent deployments or configuration changes.

## Actions
Identify and resolve the head blocker with the Database Team. Do not terminate sessions on production databases without Database Team approval.
