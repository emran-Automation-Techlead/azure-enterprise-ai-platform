---
id: DOC-008
title: Windows Update Boot Loop Recovery
category: Windows
type: RUNBOOK
owner: Endpoint Engineering
last_reviewed: 2026-07-02
synthetic: true
---

# Windows Update Boot Loop Recovery
## Symptoms
Devices restart repeatedly after a monthly Windows update.

## Actions
1. Boot into the Windows Recovery Environment.
2. Uninstall the latest quality update.
3. Pause the update ring for the affected hardware model.
4. Report affected models to Endpoint Engineering.

## Prevention
Release updates to a pilot ring before broad deployment.
