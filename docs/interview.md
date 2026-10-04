# Interview Preparation

## 60 to 90 second pitch: "Tell me about your Enterprise Azure AI project"

"IT teams keep their knowledge in runbooks and policies, and a plain chatbot will happily invent fixes that sound right. I built an enterprise IT assistant on Azure where the safety controls are part of the architecture, not an afterthought.

A question first goes through an AI router that classifies it and applies hard safety rules, so injection attempts, credential requests and attempts to bypass security are stopped before any model call. Enterprise questions go to Azure AI Search, which runs hybrid keyword and vector retrieval over documents that live in Blob Storage. A grounding gate checks how well the best document matches; if it's weak the model isn't called and the user is told there isn't enough information. Otherwise Azure OpenAI answers only from the retrieved documents and cites them.

A Responsible AI layer then checks the result: Content Safety, an output scan, citation validation and conflict detection, and it decides whether a human should review. Every response carries its sources, risk level and review status.

It's deployed as one container on Azure Container Apps, with secrets in Key Vault, delivered through a managed identity that holds three single-resource roles, and with Application Insights for safe telemetry. I evaluated it with a 10-case Responsible AI suite and 35 automated tests, and I report the one case it fails and why. For production I'd add private networking, token-based authentication to the AI services, API Management, per-user access control, and a larger evaluation set in CI."

## 25 questions

**1. Why RAG?** The model doesn't know our documents and will invent them. RAG grounds answers in retrieved text, gives citations, and updates by re-indexing.

**2. Why Azure AI Search?** Managed keyword + vector + hybrid search with metadata filters in one service; no vector database to operate.

**3. Why hybrid search?** Keyword catches exact terms like event IDs; vector catches meaning. In my testing neither was always best, so hybrid is the robust default.

**4. Why Azure OpenAI?** Models inside our Azure tenant with Azure identity and governance options, and swappable by deployment name. I used `gpt-4.1-mini` because the task is grounded summarisation, and I verified availability because `gpt-4o-mini` had been retired.

**5. Why Blob Storage?** It holds the originals so the index is always rebuildable; public and shared-key access are off.

**6. Why Container Apps?** Container hosting with ingress and scaling, without running a cluster.

**7. Why not AKS?** Cluster operations I don't need for one container. I'd choose AKS for custom controllers or strict network control.

**8. Why Managed Identity?** No stored password to leak or rotate. Mine has three roles, each on a single resource.

**9. Why Key Vault?** One audited place for secrets; the app references them and never holds them in its definition.

**10. How do you prevent hallucinations?** A grounding gate (no relevant documents means no model call), a prompt that allows only retrieved documents, citation validation, and an honest "not enough information" answer. It reduces hallucination; it doesn't make it impossible.

**11. How do you detect prompt injection?** Deterministic rules in the router run before the model. Content Safety doesn't detect injection (I tested it), so Prompt Shields would be my production addition.

**12. How do you implement Responsible AI?** As code around the model: router, safety layers, grounding gate, output scan, risk level, human review and a traceable response object, plus documentation and an evaluation suite.

**13. How do you implement human oversight?** `human_review_required` with reasons: risk MEDIUM or above, conflicting sources, insufficient evidence, sensitive input, security-sensitive requests.

**14. How do you evaluate grounding?** Cases state whether an answer should be grounded and which document must be cited; the script checks both. The grounding score is a retrieval-match metric, not proof of truth.

**15. How do you evaluate safety?** Cases for injection, credential requests, sensitive input and high-risk requests check flags, refusal, no leakage and review. It's a small portfolio set and doesn't prove production safety.

**16. How do you scale?** Container Apps scaling on concurrency; Search replicas/partitions; OpenAI quota management with retry and back-off; caching.

**17. How do you reduce token costs?** Refuse and gate before the model (0 tokens), small model, only relevant chunks, caching, shorter prompts.

**18. What happens if Search fails?** `/chat` returns a clear 502; no answer is produced because nothing can be grounded.

**19. What happens if OpenAI fails?** A clear 502. The router falls back to treating the question as KNOWLEDGE, and nothing is invented.

**20. How would you productionize this?** Private endpoints, token auth to AI services, API Management with authentication and throttling, CI/CD, IaC, per-user document access, larger evaluation in CI, alerting on telemetry.

**21. How would you implement private networking?** VNet-integrated Container Apps environment, private endpoints for Search, OpenAI, Storage and Key Vault, private DNS, public access disabled.

**22. How would you support multiple tenants?** Tenant ID on every document and filter in every query (or an index per tenant), identity-scoped access, per-tenant quotas and telemetry separation.

**23. How would you implement disaster recovery?** Infrastructure as code, a second region with replicated index and storage (GRS), tested restore of the index from Blob, and a failover runbook.

**24. How would you govern AI models?** Approved model list, versioned deployments, change control, evaluation gates before promotion, content-filter policy, usage monitoring and an owner for each model.

**25. How would you monitor AI quality?** Track grounding rate, refusal rate, human-review rate, conflict flags, user feedback and latency; run the evaluation suite on a schedule and on every change; alert on drift.

## Be ready to say honestly
- Evaluation is 10 cases; one fails (TC09, model-dependent conflict surfacing).
- The 0.65 threshold is a small calibration, and one high-risk question scored 0.66.
- Content Safety missed a calmly worded harmful request and doesn't detect injection.
- AI services still use keys (held in Key Vault); token auth is the production step.
