# Architecture Decision Records

For each service: **problem it solves · why chosen · alternative · why not the alternative · what changes in production.**
Pricing is deliberately not quoted; verify current Azure pricing.

## 1. Why RAG?
- **Problem:** the model knows nothing about the company's runbooks and policies, and will invent plausible ones.
- **Why:** retrieve the company's own documents and make the model answer only from them, with citations. Knowledge changes by re-indexing, not retraining.
- **Alternative:** rely on the model's built-in knowledge.
- **Why not:** unverifiable, uncitable, wrong for enterprise-specific facts.
- **Production:** per-document access control (security trimming) so users only retrieve what they may read.

## 2. Why Azure AI Search?
- **Problem:** find the right documents fast, by exact terms and by meaning.
- **Why:** managed service with keyword, vector and hybrid search in one index, plus filters on metadata.
- **Alternative:** self-managed vector database.
- **Why not:** more to patch, secure, scale and back up for no portfolio benefit. See #15.
- **Production:** semantic ranker, replicas/partitions for availability, private endpoint.

## 3. Why hybrid search?
- Keyword search catches exact tokens ("Event ID 1988"); vector search catches meaning ("can't sign in" ≈ "authentication failing"). Hybrid uses both. In testing, keyword alone ranked the AD document above the VPN runbook for a VPN question, while vector ranked it correctly; hybrid sat between. Honest takeaway: hybrid is a good default, not perfect.

## 4. Why Azure OpenAI?
- **Why:** model hosting inside the same Azure tenant, with Azure identity, networking and content filtering options; the deployment name is configuration, so models can be swapped.
- **Chosen model:** `gpt-4.1-mini`, small and low-cost for retrieval-grounded answers. `gpt-4o-mini` was retired by Azure, which is why model availability is checked, never assumed.
- **Alternative:** a larger model. **Why not:** the task is grounded summarisation, not open-ended reasoning.

## 5. Why Blob Storage?
- **Problem:** source documents need a home separate from the search index.
- **Why:** the index is a searchable copy; Blob holds the originals so the index can always be rebuilt. Public access and shared-key access are disabled; access is via Azure roles only.
- **Alternative:** files in the repo or on the app's disk. **Why not:** no access control, lost on restart.
- **Production:** blob indexer + change detection, soft delete, versioning, private endpoint.

## 6. Why Key Vault?
- **Problem:** secrets must not live in code, images or app settings.
- **Why:** one audited store; the Container App references secrets and never holds them in its definition.
- **Alternative:** plain environment variables. **Why not:** visible to anyone who can read the app configuration.
- **Production:** rotation policy, purge protection, private endpoint, alerts on secret access.

## 7. Why Managed Identity?
- **Problem:** the app needs to authenticate to Azure without a stored password.
- **Why:** Azure issues the credentials; nothing to leak or rotate. The user-assigned identity holds three single-resource roles: Key Vault Secrets User, Storage Blob Data Reader, AcrPull.
- **Alternative:** service principal with a client secret. **Why not:** that is another secret.
- **Honest limit:** Azure OpenAI, Search and Content Safety still use keys (delivered through Key Vault). Moving them to token authentication with role assignments is a **PRODUCTION ENHANCEMENT**.

## 8. Why Container Apps?
- **Why:** runs a container with HTTPS ingress and scaling without managing a cluster.
- **Alternative:** AKS. See #13.

## 9. Why FastAPI?
- Typed request/response validation with Pydantic, automatic OpenAPI docs, simple testing with `TestClient`.
- **Alternative:** Flask. **Why not:** less built-in validation for the same effort.

## 10. Why Streamlit?
- A working, readable interface in one file; ideal for a portfolio MVP.
- **Production:** a proper front end with authentication, SSO and accessibility testing.

## 11. Why a Responsible AI layer?
- **Problem:** a model call alone has no memory of policy; safety added "in the prompt" can be talked around.
- **Why:** deterministic controls around the model: routing, safety checks, grounding gate, output scan, risk level, human-review decision and an audit-friendly response object. Rules run before and after the model and cannot be argued with.
- **Alternative:** a long system prompt only. **Why not:** prompts can be overridden by prompt injection.

## 12. Why human oversight?
- The assistant gives advice, not decisions. Medium risk or above, conflicting sources, insufficient evidence, sensitive input, or security-sensitive requests set `human_review_required` and show "Human review recommended".

## 13. Why not AKS?
- Kubernetes adds cluster operations, upgrades and networking that this single-container app doesn't need. Container Apps is built on Kubernetes already. Choose AKS if you need custom controllers, sidecars at scale, or strict network control.

## 14. Why not fine-tuning?
- Fine-tuning teaches style, not facts; facts go stale and can't be cited or access-controlled. RAG gives sources and instant updates.

## 15. Why not a self-managed vector database?
- It would trade a managed, secure, hybrid-capable service for operational burden (patching, scaling, backups, security) with no gain for a 20-document corpus.
