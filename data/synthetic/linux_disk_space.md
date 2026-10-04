---
id: DOC-010
title: Linux Server Disk Space Troubleshooting
category: Linux
type: RUNBOOK
owner: Platform Engineering
last_reviewed: 2026-04-02
synthetic: true
---

# Linux Server Disk Space Troubleshooting
## Symptoms
Services fail with "no space left on device"; disk usage above 95%.

## Checks
1. Identify the full filesystem and largest directories.
2. Check log directories and confirm log rotation is configured.
3. Check for deleted files still held open by running processes.

## Actions
Archive old logs, fix log rotation, and add a disk-space alert at 80%. Do not delete application data without owner approval.
