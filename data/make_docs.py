"""Generates the synthetic enterprise knowledge base (all invented, no real company data)."""
from pathlib import Path

OUT = Path(__file__).parent / "synthetic"
OUT.mkdir(exist_ok=True)

DOCS = [
    ("DOC-001", "vpn_runbook.md", "VPN Authentication Troubleshooting Runbook", "VPN", "Network Operations", "RUNBOOK", "2026-06-10", """
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
"""),
    ("DOC-002", "vpn_remote_access_standard_2021.md", "Remote Access Standard (2021 edition)", "VPN", "Network Operations", "POLICY", "2021-03-02", """
## Status
This document is the 2021 edition and has not been formally retired.

## Standard
- All remote access uses the corporate SSL VPN.
- The VPN idle timeout is 30 minutes.
- Split tunnelling is not permitted.

## Note
Later runbooks may describe different timeout values. Where documents disagree, a human owner must confirm which applies.
"""),
    ("DOC-003", "password_policy.md", "Password and Account Policy", "IT Policies", "Information Security", "POLICY", "2026-04-18", """
## Password requirements
- Minimum length: 14 characters.
- Passwords must not reuse the last 12 passwords.
- Passwords expire only after a suspected compromise; routine expiry is not enforced.

## Password reset policy
- Employees reset their own password using the self-service reset portal after verifying with MFA.
- If self-service is unavailable, the service desk verifies identity using the approved identity verification procedure before any reset.
- The service desk never asks users to disclose their current password and never sends passwords by email or chat.
- Temporary passwords must be changed at first sign-in.

## Account lockout
Accounts lock after 10 failed attempts and unlock automatically after 15 minutes, or earlier through the service desk.
"""),
    ("DOC-004", "active_directory_login_failures.md", "Active Directory Login Failure Troubleshooting", "Active Directory", "Identity Team", "RUNBOOK", "2026-05-22", """
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
"""),
    ("DOC-005", "active_directory_replication.md", "Active Directory Replication Failure Runbook", "Active Directory", "Identity Team", "RUNBOOK", "2026-03-30", """
## Symptoms
New accounts or password changes are visible on one domain controller but not another. Event ID 1988 or replication errors in the Directory Service log.

## Checks
1. Run a replication summary and review failing partners and error codes.
2. Check network connectivity and DNS between the affected domain controllers.
3. Check the site link schedule and interval.
4. Look for evidence of a restore from an unsupported snapshot (USN rollback).

## Actions
- For lagging replication, force a sync after fixing the cause.
- For suspected USN rollback, isolate the domain controller and escalate to the Identity Team. Do not attempt demotion without approval.

## Prevention
Do not restore domain controllers from VM snapshots. Use AD-aware backup tooling.
"""),
    ("DOC-006", "dns_resolution_issues.md", "Internal DNS Resolution Troubleshooting", "Networking", "Network Operations", "RUNBOOK", "2026-02-14", """
## Symptoms
Internal hostnames fail to resolve while external websites work.

## Checks
1. Compare resolution against each internal DNS server.
2. Confirm the DNS service is running on every internal DNS server.
3. Confirm clients list a healthy server first.
4. Verify zone data and forwarders.

## Resolution notes
Restarting a stopped DNS service and correcting the client DNS server order resolved a past incident.
"""),
    ("DOC-007", "network_outage_runbook.md", "Site Network Outage Runbook", "Networking", "Network Operations", "RUNBOOK", "2026-01-25", """
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
"""),
    ("DOC-008", "windows_update_boot_loop.md", "Windows Update Boot Loop Recovery", "Windows", "Endpoint Engineering", "RUNBOOK", "2026-07-02", """
## Symptoms
Devices restart repeatedly after a monthly Windows update.

## Actions
1. Boot into the Windows Recovery Environment.
2. Uninstall the latest quality update.
3. Pause the update ring for the affected hardware model.
4. Report affected models to Endpoint Engineering.

## Prevention
Release updates to a pilot ring before broad deployment.
"""),
    ("DOC-009", "mfa_enrollment_troubleshooting.md", "MFA Enrollment and Sign-in Troubleshooting", "Identity", "Identity Team", "RUNBOOK", "2026-05-05", """
## Symptoms
Users cannot sign in after enrolling in multi-factor authentication, or authenticator codes are rejected.

## Checks
1. Confirm the device clock is synchronised; time drift invalidates one-time codes.
2. Check the sign-in log to see whether MFA was requested and why it failed.
3. Check for legacy per-user MFA settings conflicting with Conditional Access policy.
4. If registration is corrupted, reset the user's MFA registration and ask them to re-enrol.

## Notes
Never ask users to read out their one-time codes or approve prompts they did not initiate.
"""),
    ("DOC-010", "linux_disk_space.md", "Linux Server Disk Space Troubleshooting", "Linux", "Platform Engineering", "RUNBOOK", "2026-04-02", """
## Symptoms
Services fail with "no space left on device"; disk usage above 95%.

## Checks
1. Identify the full filesystem and largest directories.
2. Check log directories and confirm log rotation is configured.
3. Check for deleted files still held open by running processes.

## Actions
Archive old logs, fix log rotation, and add a disk-space alert at 80%. Do not delete application data without owner approval.
"""),
    ("DOC-011", "database_connection_failures.md", "Database Connection Failure Troubleshooting", "Database", "Database Team", "RUNBOOK", "2026-06-20", """
## Symptoms
Applications report connection timeouts to the database; intermittent success.

## Checks
1. Check whether the database service is up and accepting connections.
2. Check for blocking sessions and long-running transactions.
3. Check application connection pool settings and connection leaks.
4. Check recent deployments or configuration changes.

## Actions
Identify and resolve the head blocker with the Database Team. Do not terminate sessions on production databases without Database Team approval.
"""),
    ("DOC-012", "database_backup_restore.md", "Database Backup and Restore Procedure", "Database", "Database Team", "RUNBOOK", "2026-03-11", """
## Backups
Full backups run nightly; transaction log backups run every 15 minutes for production databases.

## Restore
Restores to production require a change request and Database Team approval. Test restores are performed quarterly.
"""),
    ("DOC-013", "application_deployment_rollback.md", "Application Deployment and Rollback Runbook", "Application", "Application Support", "RUNBOOK", "2026-05-29", """
## Symptoms
Errors or slowness immediately after a release.

## Checks
1. Compare error rates before and after the deployment.
2. Review application and dependency health checks.
3. Check for new database queries missing indexes.

## Rollback
Application Support may roll back to the previous release when error rate exceeds the agreed threshold. Document the rollback in the change record.
"""),
    ("DOC-014", "azure_vm_unreachable.md", "Cloud: Azure Virtual Machine Unreachable", "Cloud", "Cloud Platform Team", "RUNBOOK", "2026-06-15", """
## Symptoms
A cloud virtual machine does not respond to RDP, SSH or application traffic.

## Checks
1. Check VM power state and platform health in the cloud portal.
2. Check network security group rules and effective routes.
3. Check boot diagnostics output.
4. Check recent configuration changes in the activity log.

## Actions
Restarting a production VM requires confirming the owning application team's approval. Escalate to the Cloud Platform Team for platform health events.
"""),
    ("DOC-015", "security_incident_response.md", "Security Incident Response Procedure", "Security", "Security Operations", "RUNBOOK", "2026-07-08", """
## Scope
Suspected account compromise, malware, data exposure or unauthorised access.

## Immediate actions
1. Report to Security Operations immediately.
2. Do not delete evidence or reboot affected systems unless Security Operations instructs.
3. Preserve logs and note the time of discovery.

## Containment
Containment actions such as disabling accounts or isolating devices are performed or approved by Security Operations.
"""),
    ("DOC-016", "change_management_policy.md", "Change Management Policy", "IT Policies", "IT Governance", "POLICY", "2026-02-03", """
## Principles
All changes to production systems require an approved change request.

## Security controls
Security controls, including firewalls, endpoint protection, MFA and logging, must never be disabled, bypassed or weakened to resolve an incident. If a security control is believed to be causing an incident, raise it with Security Operations, who may authorise a documented, time-limited exception through the emergency change process.

## Emergency changes
Emergency changes require approval from the on-call incident manager and must be reviewed afterwards.
"""),
    ("DOC-017", "acceptable_use_and_data_handling.md", "Acceptable Use and Data Handling Policy", "IT Policies", "Information Security", "POLICY", "2026-01-12", """
## Rules
- Do not share passwords, tokens, recovery keys or other credentials in tickets, chat or email.
- Classify data as Public, Internal, Confidential or Restricted. Do not place Confidential or Restricted data in unapproved tools.
- Report suspected data exposure to Security Operations immediately.
"""),
    ("DOC-018", "m365_signin_problems.md", "Microsoft 365 Sign-in Problems", "Identity", "Messaging Team", "RUNBOOK", "2026-04-25", """
## Symptoms
Outlook or Teams repeatedly prompts for credentials while browser sign-in works.

## Actions
1. Sign out of Office applications.
2. Clear cached Office credentials in Credential Manager.
3. Sign in again and confirm modern authentication is enabled for the user.
"""),
    ("DOC-019", "bitlocker_recovery.md", "BitLocker Recovery Key Request Procedure", "Windows", "Endpoint Engineering", "RUNBOOK", "2026-03-19", """
## Procedure
Recovery keys are released only after the service desk verifies the user's identity using the approved procedure and logs the request.

## Rules
Recovery keys must never be sent by email or chat. Read the key to the verified user over the phone only, or use the self-service portal.
"""),
    ("DOC-020", "oncall_escalation_matrix.md", "On-call and Escalation Matrix", "Runbooks", "Service Delivery", "RUNBOOK", "2026-07-20", """
## Severity
- P1: major outage or security incident. Escalate immediately to the on-call incident manager.
- P2: significant degradation affecting many users. Escalate within 30 minutes.
- P3: limited impact. Handle within the normal queue.

## Contacts by area
Network Operations, Identity Team, Database Team, Cloud Platform Team, Security Operations and Application Support each maintain their own on-call rota in the service management tool.
"""),
]

for doc_id, fname, title, category, owner, kind, reviewed, body in DOCS:
    front = (
        f"---\nid: {doc_id}\ntitle: {title}\ncategory: {category}\ntype: {kind}\n"
        f"owner: {owner}\nlast_reviewed: {reviewed}\nsynthetic: true\n---\n\n# {title}\n"
    )
    (OUT / fname).write_text(front + body.strip() + "\n", encoding="utf-8")

print(f"Wrote {len(DOCS)} synthetic documents to {OUT}")
