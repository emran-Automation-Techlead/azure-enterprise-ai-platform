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

---

# Multi-agent questions

**M1. Why multi-agent?** One pipeline could only follow one path per request and could not review itself independently. Specialised agents have focused roles, their own tools and tests, can be combined for mixed requests ("VPN is failing, should we disable MFA?"), and the Responsible AI reviewer is separate from the agents producing the answer. It costs more latency, tokens and complexity.

**M2. Why not a single agent?** For one narrow path a single agent is simpler, cheaper and faster, and I'd choose it. Here, mixed requests, an independent reviewer and separately testable behaviours justified the extra cost. I kept `AGENT_MODE=single` to restore the original pipeline.

**M3. What does the orchestrator do?** It never answers. Hard rules run first and block injection, credential requests and bypass attempts with no model call. Otherwise one model call classifies the request into one or more types, and code maps those to agents, with overrides the model can't undo (for example proposing to disable a security control always adds the Knowledge agent).

**M4. How do agents communicate?** Through typed Pydantic messages (`AgentMessage`, `OrchestratorPlan`, `ReviewVerdict`), not free text. Invalid values are rejected. The pipeline runs the agents in the planned order; agents never call each other.

**M5. How do you prevent agent hallucination?** Retrieval gates the model (weak match means `NO_RELEVANT_KNOWLEDGE` and no model call). Incident findings are labelled From sources / Inference / Unknown, and code downgrades any "sourced" claim whose document wasn't actually retrieved. The General agent is labelled and can never carry enterprise sources. This reduces hallucination; it doesn't remove it.

**M6. How does the Responsible AI agent work?** A deterministic floor (rules, Azure AI Content Safety, output scan, conflicts, missing knowledge, outages) plus one model call that checks unsupported claims, risk and privacy. The model can only raise risk. It returns a structured verdict with a short reason, no chain-of-thought. It sees claims and source IDs, not full source text, which is a known limit.

**M7. How do you prevent prompt injection?** Rules block override attempts before any worker agent or model runs. Document text and agent output are treated as data. A test checks that an injection hidden inside agent output can't lower the risk. Azure AI Content Safety doesn't detect injection (I observed that), so Prompt Shields would be my production step.

**M8. How do you manage multi-agent cost?** Rules and the grounding gate run before models, a blocked request makes 0 model calls, the reviewer skips its call when there is nothing to review, and I use a small model with short prompts. A normal request makes about 3 calls (4 for a two-agent request) versus about 2 originally. I haven't measured real token costs yet.

**M9. How do you manage latency?** Today agents run sequentially, so latency adds up. Independent agents (Incident and Knowledge) could run in parallel, and routing could use a smaller model or caching. Not built yet.

**M10. How would you scale the agents?** They are stateless inside the FastAPI container, so Container Apps scales horizontally. If one agent became a bottleneck I could split it into its own service. Search replicas and OpenAI quota management matter more than agent count.

**M11. How would you evaluate agent routing?** Each evaluation case lists acceptable worker-agent sets (`expected_agents`), and a routing score checks the orchestrator ran first, the reviewer last and the workers matched. There are 12 cases, so it demonstrates the method and doesn't prove reliability. In my live run it routed 12 of 12 cases correctly; the two failures were a model-dependent conflict flag (TC09) and a keyword gap in my own test (TC11).

**M12. What happens if one agent fails?** A worker that can't reach Search or the model returns an `error` result instead of raising, so the request continues. The reviewer sees the gap and requires human review. If the reviewer's own model call fails, the verdict falls back to the deterministic checks and requires human review. If the orchestrator's model fails it routes to the Knowledge agent.

## "Tell me about your multi-agent Azure AI project" (60 to 90 seconds)
"IT teams keep their knowledge in runbooks and policies, and a generic chatbot will confidently invent fixes. I built an enterprise assistant on Azure that answers only from company documents. I started with a RAG pipeline on Azure AI Search and Azure OpenAI, then upgraded it to a multi-agent design.

An orchestrator agent classifies each request and decides who handles it. An incident agent analyses failures, a knowledge agent answers policy questions through hybrid search, and a general agent handles generic technology questions, clearly labelled as not from company documents. They pass structured messages, and every finding is marked as from sources, inference or unknown.

A separate Responsible AI review agent checks the combined result for grounding, safety, privacy and unsupported claims, and assigns a risk level. For something like 'VPN is failing, should we disable MFA?', both the incident and knowledge agents run, the risk comes back HIGH, and the answer requires human review, because the system shouldn't decide that alone. Prompt injection is blocked by rules before any model runs.

For security, secrets sit in Key Vault behind a managed identity, and telemetry never logs question text. The trade-off is cost and latency: about three or four model calls per request instead of two. Agents run sequentially today, so parallelising them is my next step. I've also been clear about the limits: it's synthetic data, a small evaluation, and token authentication to the AI services and API Management are future work."
