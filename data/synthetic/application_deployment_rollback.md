---
id: DOC-013
title: Application Deployment and Rollback Runbook
category: Application
type: RUNBOOK
owner: Application Support
last_reviewed: 2026-05-29
synthetic: true
---

# Application Deployment and Rollback Runbook
## Symptoms
Errors or slowness immediately after a release.

## Checks
1. Compare error rates before and after the deployment.
2. Review application and dependency health checks.
3. Check for new database queries missing indexes.

## Rollback
Application Support may roll back to the previous release when error rate exceeds the agreed threshold. Document the rollback in the change record.
