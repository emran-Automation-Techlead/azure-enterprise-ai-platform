---
id: DOC-009
title: MFA Enrollment and Sign-in Troubleshooting
category: Identity
type: RUNBOOK
owner: Identity Team
last_reviewed: 2026-05-05
synthetic: true
---

# MFA Enrollment and Sign-in Troubleshooting
## Symptoms
Users cannot sign in after enrolling in multi-factor authentication, or authenticator codes are rejected.

## Checks
1. Confirm the device clock is synchronised; time drift invalidates one-time codes.
2. Check the sign-in log to see whether MFA was requested and why it failed.
3. Check for legacy per-user MFA settings conflicting with Conditional Access policy.
4. If registration is corrupted, reset the user's MFA registration and ask them to re-enrol.

## Notes
Never ask users to read out their one-time codes or approve prompts they did not initiate.
