# Security and Threat Model

## Threat model

| Threat | Risk | Mitigation (built) | PRODUCTION ENHANCEMENT |
|---|---|---|---|
| **Prompt injection** ("ignore your instructions…") | Model leaks instructions or ignores policy | Router rules block before any search or model call; documents are treated as data in the grounded prompt; output scan withholds leaked instruction text | Azure AI Content Safety Prompt Shields; red-team suite |
| **Data leakage** | Answer reveals documents the user shouldn't see | Answers limited to retrieved documents; sources always shown | Per-user security trimming in the index |
| **Credential leakage** | Secrets pasted into chat, echoed back, or logged | Input redaction before model/logs; output scan for credential-like values; privacy notice; telemetry never logs text | DLP integration; secret scanning in CI |
| **Excessive permissions** | A compromised app can do too much | Managed identity with three single-resource roles; storage public/shared-key access off; registry admin user off | Permissions review; Azure Policy |
| **Insecure APIs** | Anyone can call `/chat` | Input validation (Pydantic, length limits); friendly errors without internals; CORS currently `*` | Authentication (Entra ID), API Management throttling, restrictive CORS |
| **Malicious documents** | A poisoned document carries instructions | Prompt rule: documents are data, not instructions; citation validation | Content scanning at ingestion; document provenance and approval |
| **Unsafe output** | Harmful or secret-like text reaches the user | Output scan; Content Safety on input | Content Safety on output; groundedness detection |
| **Logging sensitive data** | Questions/answers stored in telemetry | Only counts, latency, type, risk, flags are logged | Retention policy, access review of the workspace |

## Secrets handling
- Local: `.env`, git-ignored and docker-ignored; `.env.example` has blank values only.
- Cloud: three secrets in **Azure Key Vault** (RBAC mode, soft delete on); the Container App references them with its managed identity. Secret values never appear in the app definition, the image or the repository.
- A secret scan of the files and git history is run before any push.

## Real RBAC for the app identity (`id-entai-app`)
Output of `az role assignment list --assignee <identity> --all` (subscription ID masked):

| Role | Scope |
|---|---|
| Key Vault Secrets User | `…/vaults/entai-kv-9494` |
| Storage Blob Data Reader | `…/storageAccounts/entaikb97240` |
| AcrPull | `…/registries/entaiacr9494` |

## Hardening applied (verified by CLI)
- Storage account: public blob access **off**, shared-key access **off**, TLS 1.2 minimum.
- Container Registry: admin user **off**; image pulled via managed identity.
- Container image: runs as non-root user (uid 10001), HEALTHCHECK enabled, no `.env` inside.

## Honest gaps
- Azure OpenAI, Search and Content Safety still authenticate with **keys** (stored in Key Vault, delivered via the identity). Token authentication with role assignments is the production target.
- No private networking: services are reachable on public endpoints with keys/RBAC.
- The Container App has a public URL with no user authentication. It is a short-lived demo deployment and is intended to be deleted once the evidence is captured.
- Content Safety **fails open** if unavailable (router and local rules still apply).
- API Management, WAF, rate limiting: not built.
